# Pollinations Relay

## Prerequisites

- Node 20+
- `npm i -g wrangler`
- Cloudflare account

## Quick Deploy

```powershell
cd relay
wrangler deploy cloudflare-worker.js --name pollinations-relay
```

## Bind KV

Optional rate-limit storage:

```powershell
wrangler kv:namespace create RATE_LIMIT
```

Paste the returned namespace id into `wrangler.toml`.

## Custom Domain

Point `relay.your-domain.com` to the Worker route in Cloudflare.

## Update App

Set the relay first in `.env`:

```env
POLLINATIONS_ENDPOINTS=https://relay.your-domain.com/v1/chat/completions,https://text.pollinations.ai/openai,https://gen.pollinations.ai/v1/chat/completions
```

## Test

```powershell
curl -X POST https://<worker-url>/v1/chat/completions `
  -H "Authorization: Bearer sk_..." `
  -H "Content-Type: application/json" `
  -d "{\"model\":\"gpt-5.4-nano\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}],\"max_tokens\":8}"
```
