## PollinationsClient Checklist

- Use `curl_cffi.requests` for Pollinations HTTP calls.
- Do not reintroduce `urllib.request` or `urllib.error` in `backend/services/pollinations_client.py`.
- Preserve multi-endpoint failover and `_preferred_endpoint` caching.
- Cloudflare 1010/1020 style responses must map to `CLOUDFLARE_ACCESS_DENIED`.
- Keep non-retryable 4xx errors fail-fast; do not hide bad API keys behind endpoint failover.
DOCUMENTATION-ONLY task. Táº¡o DUY NHáº¤T 1 file Markdown á»Ÿ root repo: `CODEX_INSTRUCTIONS.md`.

Tuyá»‡t Ä‘á»‘i KHÃ”NG:

- Sá»­a báº¥t ká»³ file nguá»“n nÃ o (.py/.js/.css/.html/.ps1/.spec/.bat/.toml/.json/.yml/.txt/.env*).
- Táº¡o file khÃ¡c ngoÃ i `CODEX_INSTRUCTIONS.md`.
- CÃ i dependency, cháº¡y tests, táº¡o branch, commit.

Má»¥c tiÃªu: file `CODEX_INSTRUCTIONS.md` lÃ  self-contained handoff cho Codex/Cursor/Claude Code. Äá»c 1 file lÃ  code Ä‘Æ°á»£c toÃ n bá»™ roadmap nÃ¢ng cáº¥p, KHÃ”NG cáº§n truy cáº­p Epic.

# ================================================================  
NGUá»’N Ná»˜I DUNG (Ä‘á»c qua tool epic, Ä‘Ã£ cÃ³ sáºµn):

Master spec (APP_SKILL): spec:7fcfbced-af9c-43d4-80ee-76cb515a129a/ffd40db1-63d4-4001-8ebf-2d959327802b

Wave specs:

- Wave 1: spec:7fcfbced-af9c-43d4-80ee-76cb515a129a/0d38c00e-d93d-4cd9-8a91-453743d57e7d
- Wave 2: spec:7fcfbced-af9c-43d4-80ee-76cb515a129a/1d04c7b2-ce6b-4b70-86b4-22503d2d9abc
- Wave 3: spec:7fcfbced-af9c-43d4-80ee-76cb515a129a/614ac6db-8581-48bd-b70d-8f0b6b9c7125
- Wave 4: spec:7fcfbced-af9c-43d4-80ee-76cb515a129a/b847c677-dc8a-4d02-ad6e-d7788d804f39
- Wave 5: spec:7fcfbced-af9c-43d4-80ee-76cb515a129a/cb75df07-d3a6-4e8d-b3c0-e4bcf0551c00

Wave 1 tickets:

- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/dc647866-259d-4d14-a051-50793a68d04b  (W1.1)
- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/bf17768a-2844-4858-a8e5-e7f4df29c9b6  (W1.2)
- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/a9174391-8305-4340-9cce-79fa0e58e05a  (W1.3)

Wave 2 tickets:

- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/c297d857-86de-4baa-a941-9f377fe3a06b  (W2.1)
- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/ba3aabd3-c06d-437c-9afe-143bc56ac721  (W2.2)
- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/5ff4b602-2d9c-4f8b-999e-5af124da907e  (W2.3)
- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/3f548352-750b-4e07-9028-3617c75ee624  (W2.4)

Wave 3 tickets:

- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/30d31599-f6b1-452b-bcd3-60678c489146  (W3.1)
- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/63387ada-988a-4aab-a0bf-5a295f826983  (W3.2)
- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/c16afb4a-d9f5-4c3c-8046-25b5cf9423af  (W3.3)

Wave 4 tickets:

- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/92fcff0d-3220-4d23-9c67-7f087ccc816c  (W4.1)
- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/0cbab03f-4479-4613-8cbe-0dd1eafb48e8  (W4.2)
- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/7695687e-aceb-4acc-bfb3-10255e47b126  (W4.3)
- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/a522056f-6f17-405b-b9a9-5241baf30da2  (W4.4)

Wave 5 tickets:

- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/4c3bdbff-3005-4c64-9c67-3a0855d0dc54  (W5.1)
- ticket:7fcfbced-af9c-43d4-80ee-76cb515a729a/3d685a3e-8a1f-4854-9093-3588c75ba358  (W5.2)
- ticket:7fcfbced-af9c-43d4-80ee-76cb515a129a/ebbb9e51-1a08-4bf8-a79d-2d113aecac4e  (W5.3)

# ================================================================  
Cáº¤U TRÃšC FILE `CODEX_INSTRUCTIONS.md` (theo thá»© tá»±, headings y nguyÃªn):

```
# CODEX INSTRUCTIONS â€” Img automation App

> File nÃ y lÃ  source of truth duy nháº¥t cho Codex/Cursor/Claude Code.
> Khi xung Ä‘á»™t vá»›i báº¥t ká»³ file Markdown nÃ o khÃ¡c trong repo (SKILL.md, outfit_swap_skill.md, REDESIGN_SPEC.md, README.md), file nÃ y tháº¯ng.

## 0. CÃ¡ch dÃ¹ng

1. Äá»c Háº¾T file nÃ y trÆ°á»›c khi sá»­a code.
2. Code theo thá»© tá»± Wave 1 â†’ Wave 2 â†’ Wave 3 â†’ Wave 4 â†’ Wave 5. KHÃ”NG nháº£y cÃ³c.
3. Má»—i wave: lÃ m háº¿t ticket trong wave, cháº¡y verify suite (Â§5), tick Acceptance Criteria, rá»“i má»›i sang wave káº¿ tiáº¿p.
4. Náº¿u user chá»‰ yÃªu cáº§u 1 wave cá»¥ thá»ƒ â†’ chá»‰ lÃ m wave Ä‘Ã³, khÃ´ng tá»± Ã½ lÃ m thÃªm.

## 1. Bá»‘i cáº£nh sáº£n pháº©m

<copy nguyÃªn Â§1 "Product Identity" cá»§a APP_SKILL spec, giá»¯ code block, giá»¯ list>

## 2. NguyÃªn táº¯c báº¥t biáº¿n (Non-Negotiables)

<copy nguyÃªn Â§2 cá»§a APP_SKILL spec, giá»¯ Ä‘Ã¡nh sá»‘ 1..11>

## 3. Kiáº¿n trÃºc target & module contracts

### 3.1 Repo layout sau khi xong toÃ n bá»™

<copy nguyÃªn Â§3 "Repository Layout" cá»§a APP_SKILL>

### 3.2 Runtime architecture

<copy nguyÃªn Â§4 cá»§a APP_SKILL, GIá»® NGUYÃŠN mermaid block, khÃ´ng escape>

### 3.3 Backend module contracts

<copy nguyÃªn Â§5 cá»§a APP_SKILL: Â§5.1 constants, Â§5.2 image_preprocess, Â§5.3 cache_service, Â§5.4 pollinations_client, Â§5.5 prompt_workflow, Â§5.6 chrome_profiles, Â§5.7 desktop_api>

### 3.4 Output format theo target_model_rule

<copy nguyÃªn Â§6 cá»§a APP_SKILL>

### 3.5 Identity / Outfit / Background / Pose / Negative rules

<copy nguyÃªn Â§7 cá»§a APP_SKILL>

### 3.6 Pollinations API contract

<copy nguyÃªn Â§8 cá»§a APP_SKILL, giá»¯ table>

### 3.7 Frontend contract

<copy nguyÃªn Â§9 cá»§a APP_SKILL>

### 3.8 Build & package

<copy nguyÃªn Â§10 cá»§a APP_SKILL>

### 3.9 Security & privacy

<copy nguyÃªn Â§12 cá»§a APP_SKILL>

## 4. Roadmap 5 Wave

Má»—i wave lÃ  1 mini-spec + danh sÃ¡ch ticket chi tiáº¿t. Äá»c ká»¹ trÆ°á»›c khi báº¯t Ä‘áº§u wave Ä‘Ã³.

### Wave 1 â€” Hardening & Single Source of Truth

#### Spec
<copy nguyÃªn body cá»§a Wave 1 spec: Scope, Bug list, Acceptance Criteria>

#### Ticket W1.1 â€” <title>
<copy nguyÃªn body W1.1 ticket>

#### Ticket W1.2 â€” <title>
<copy nguyÃªn body W1.2 ticket>

#### Ticket W1.3 â€” <title>
<copy nguyÃªn body W1.3 ticket>

### Wave 2 â€” Visionâ†’Builder Pipeline + Cache

#### Spec
<copy nguyÃªn body Wave 2 spec, giá»¯ mermaid flowchart>

#### Ticket W2.1 â€” ...
<copy>

#### Ticket W2.2 â€” ...
<copy>

#### Ticket W2.3 â€” ...
<copy>

#### Ticket W2.4 â€” ...
<copy>

### Wave 3 â€” Multi-target Output + Critic Mode

#### Spec
<copy>

#### Ticket W3.1 â€” ...
<copy>

#### Ticket W3.2 â€” ...
<copy>

#### Ticket W3.3 â€” ...
<copy>

### Wave 4 â€” UX Upgrade

#### Spec
<copy>

#### Ticket W4.1 â€” ...
<copy>

#### Ticket W4.2 â€” ...
<copy>

#### Ticket W4.3 â€” ...
<copy>

#### Ticket W4.4 â€” ...
<copy>

### Wave 5 â€” DevEx, CI, Build Cleanup

#### Spec
<copy>

#### Ticket W5.1 â€” ...
<copy>

#### Ticket W5.2 â€” ...
<copy>

#### Ticket W5.3 â€” ...
<copy>

## 5. Verify suite (cháº¡y local sau má»—i wave)

```powershell
# Backend tests
python -m pytest -q

# Frontend static check (Wave 1+)
node tests/frontend-static-check.mjs

# Frontend render check (Wave 1+, cáº§n playwright)
node tests/frontend-render-check.mjs

```

Wave 5 thÃªm:

```powershell
ruff check .
mypy backend
node tests/frontend-unit.mjs

```

Smoke run sau má»—i wave:

```powershell
.\run_app.ps1

```

Má»Ÿ app, generate Ä‘Æ°á»£c prompt vá»›i 3 áº£nh tháº­t.

## 6. Ranh giá»›i Codex KHÃ”NG Ä‘Æ°á»£c vÆ°á»£t

- KHÃ”NG tá»± Ã½ refactor file ngoÃ i scope wave hiá»‡n táº¡i.
- KHÃ”NG thÃªm runtime dependency má»›i ngoÃ i: pywebview (cÃ³ sáºµn), Pillow (Wave 2).
- KHÃ”NG thay framework: cáº¥m Electron, React, Vue, bundler (vite/webpack/esbuild).
- KHÃ”NG táº¡o backend HTTP má»›i (Flask/FastAPI). App lÃ  pywebview pure.
- KHÃ”NG Ä‘á»•i DOM IDs Ä‘ang cÃ³ (xem Â§3.7).
- KHÃ”NG Ä‘á»•i shape payload `generate_prompt` cá»§a FEâ†’BE (chá»‰ THÃŠM field tÃ¹y chá»n, khÃ´ng xÃ³a/Ä‘á»•i tÃªn).
- KHÃ”NG xoÃ¡ file legacy SKILL.md / outfit_swap_skill.md / REDESIGN_SPEC.md trÆ°á»›c Wave 5.
- KHÃ”NG gá»i API tháº­t trong test (mock urlopen/urllib).
- KHÃ”NG commit `.env`, `dist/`, `build/`, file áº£nh chá»©a thÃ´ng tin nháº¡y cáº£m.
- KHÃ”NG thÃªm telemetry, analytics, auto-update.

## 7. Khi gáº·p ambiguity

Æ¯u tiÃªn (cao â†’ tháº¥p):

1. Â§2 (Non-Negotiables) cá»§a file nÃ y.
2. Â§3 (Architecture) cá»§a file nÃ y.
3. Spec wave hiá»‡n táº¡i (Â§4.&lt;wave&gt;).
4. Ticket trong wave Ä‘Ã³.
5. Source code hiá»‡n táº¡i trong repo.

Náº¿u váº«n khÃ´ng rÃµ: dá»«ng, há»i user. KHÃ”NG tá»± Ä‘oÃ¡n.

## 8. Convention commit

```
feat(waveN): W<N>.<X> <short description>
fix(waveN):  W<N>.<X> <short description>
test(waveN): W<N>.<X> <short description>
chore(waveN): ...

```

Má»—i ticket = 1 commit (hoáº·c 1 PR). Body commit liá»‡t kÃª file Ä‘Ã£ sá»­a.

## 9. Done definition

Wave Ä‘Æ°á»£c coi lÃ  done khi:

- [ ] Táº¥t cáº£ Acceptance Criteria cá»§a spec wave + ticket bÃªn trong Ä‘á»u check.
- [ ] ToÃ n bá»™ verify suite Â§5 xanh.
- [ ] Smoke run app thÃ nh cÃ´ng.
- [ ] KhÃ´ng cÃ³ file nÃ o bá»‹ sá»­a ngoÃ i scope wave (kiá»ƒm tra `git diff --name-only`).

## 10. Glossary

&lt;copy nguyÃªn Â§15 "Glossary" cá»§a APP_SKILL&gt;

```

================================================================
QUY Táº®C RENDER:
================================================================

1. UTF-8 khÃ´ng BOM. LF line endings.
2. Má»i mermaid code block giá»¯ nguyÃªn dáº¡ng ` ```mermaid `, KHÃ”NG escape.
3. Má»i code block giá»¯ nguyÃªn ngÃ´n ngá»¯ (text/json/python/powershell).
4. Má»i reference dáº¡ng `spec:.../...`, `ticket:.../...`, `epic:...`, `chat:...` xuáº¥t hiá»‡n trong ná»™i dung copy â†’ REPLACE báº±ng tham chiáº¿u ná»™i bá»™. VÃ­ dá»¥:
   - "spec:7fcfbced.../ffd40db1..." â†’ "Â§3 cá»§a file nÃ y" hoáº·c bá» háº³n náº¿u khÃ´ng cáº§n.
   - "ticket:.../W1.1..." â†’ "Ticket W1.1 trong Â§4.Wave 1".
   - KhÃ´ng Ä‘á»ƒ Codex tháº¥y uuid epic/spec/ticket â€” Codex khÃ´ng cÃ³ quyá»n truy cáº­p.
5. Má»i reference dáº¡ng backend/... â†’ Ä‘á»•i thÃ nh path thÆ°á»ng, vÃ­ dá»¥ "`backend/services/prompt_workflow.py`" (giá»¯ backtick).
6. Heading levels tuÃ¢n theo cáº¥u trÃºc trÃªn (## cho má»¥c 0..10, ### cho 3.1..3.9 vÃ  Wave 1..5, #### cho Spec / Ticket).
7. Acceptance Criteria pháº£i dáº¡ng `- [ ]` Ä‘á»ƒ Codex tick Ä‘Æ°á»£c.
8. Táº¥t cáº£ tiáº¿ng Viá»‡t, KHÃ”NG dá»‹ch.
9. KHÃ”NG thÃªm meta-comment kiá»ƒu "(copy from spec X)" vÃ o file output. File pháº£i sáº¡ch sáº½, Ä‘á»c tá»± nhiÃªn.
10. KHÃ”NG tÃ³m táº¯t ná»™i dung gá»‘c â€” copy Ä‘áº§y Ä‘á»§. File nÃ y cÃ³ thá»ƒ dÃ i (~3000-5000 dÃ²ng), Ä‘Ã³ lÃ  cháº¥p nháº­n Ä‘Æ°á»£c.

================================================================
VALIDATION CUá»I:
================================================================

- Chá»‰ táº¡o 1 file: `CODEX_INSTRUCTIONS.md` á»Ÿ root.
- File má»Ÿ Ä‘Æ°á»£c, cÃ³ Ä‘áº§y Ä‘á»§ heading tá»« ## 0 Ä‘áº¿n ## 10.
- CÃ³ heading `### Wave 1 â€” Hardening & Single Source of Truth` Ä‘áº¿n `### Wave 5 â€” DevEx, CI, Build Cleanup`.
- CÃ³ 17 ticket sub-section (W1.1, W1.2, W1.3, W2.1..W2.4, W3.1..W3.3, W4.1..W4.4, W5.1..W5.3).
- KhÃ´ng cÃ²n chuá»—i `spec:` hoáº·c `ticket:` hoáº·c `epic:` nÃ o trong file output (grep verify).
- File size > 30KB (Ä‘áº£m báº£o ná»™i dung Ä‘áº§y Ä‘á»§, khÃ´ng bá»‹ tÃ³m táº¯t).

BÃ¡o cÃ¡o cuá»‘i: in ra path file, size, sá»‘ dÃ²ng, vÃ  5 dÃ²ng Ä‘áº§u + 5 dÃ²ng cuá»‘i Ä‘á»ƒ xÃ¡c nháº­n.
```
