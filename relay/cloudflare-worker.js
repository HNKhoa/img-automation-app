const UPSTREAMS = [
  "https://text.pollinations.ai/openai",
  "https://gen.pollinations.ai/v1/chat/completions",
];

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }
    if (request.method !== "POST" || url.pathname !== "/v1/chat/completions") {
      return json({ error: "not_found" }, 404);
    }

    const authorization = request.headers.get("Authorization") || "";
    const limited = await rateLimit(env, authorization);
    if (limited) {
      return json({ error: "rate_limited" }, 429);
    }

    const body = await request.arrayBuffer();
    const headers = new Headers();
    for (const name of ["Authorization", "Content-Type", "Accept"]) {
      const value = request.headers.get(name);
      if (value) headers.set(name, value);
    }

    let lastStatus = 502;
    let lastBody = '{"error":"upstream_failed"}';
    for (const upstream of UPSTREAMS) {
      const started = Date.now();
      const response = await fetch(upstream, {
        method: "POST",
        headers,
        body,
        redirect: "follow",
        signal: AbortSignal.timeout(60000),
      });
      const text = await response.text();
      console.log(
        JSON.stringify({
          ts: new Date().toISOString(),
          upstream,
          status: response.status,
          latency_ms: Date.now() - started,
          ray_id: response.headers.get("cf-ray") || null,
        }),
      );

      if (response.status === 200) {
        return new Response(text, {
          status: response.status,
          headers: proxyHeaders(response.headers),
        });
      }
      lastStatus = response.status;
      lastBody = text;
      if (response.status === 403 && /cloudflare|access denied|error 10[12]0/i.test(text)) {
        continue;
      }
      return new Response(text, {
        status: response.status,
        headers: proxyHeaders(response.headers),
      });
    }

    const outHeaders = proxyHeaders(new Headers());
    outHeaders.set("x-relay-failover", "exhausted");
    return new Response(lastBody, { status: lastStatus, headers: outHeaders });
  },
};

async function rateLimit(env, authorization) {
  if (!env.RATE_LIMIT || !authorization) return false;
  const hash = await sha256(authorization);
  const key = `rl:${hash}`;
  const now = Math.floor(Date.now() / 1000);
  const windowStart = now - (now % 60);
  const payload = JSON.parse((await env.RATE_LIMIT.get(key)) || "null") || {
    windowStart,
    count: 0,
  };
  const next = payload.windowStart === windowStart ? payload : { windowStart, count: 0 };
  next.count += 1;
  await env.RATE_LIMIT.put(key, JSON.stringify(next), { expirationTtl: 90 });
  return next.count > 60;
}

async function sha256(text) {
  const bytes = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function proxyHeaders(headers) {
  const out = new Headers(CORS_HEADERS);
  out.set("Content-Type", headers.get("Content-Type") || "application/json");
  return out;
}

function json(payload, status) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}
