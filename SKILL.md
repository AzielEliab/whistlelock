---
name: WhistleLock
description: Use this when someone already has a whistle file and needs a local hashed drop ledger plus a local dead-man copy. Not a mailer. Hosted /v1 never stores drops.
---

# WhistleLock skill

WhistleLock is a **local folder** that copies a file you already have, hashes it, and chains the row. If you stop checking in, it copies a packet you already placed into `released/`. **It does not mail.** It does not rotate From: addresses. It does not hide your IP. It does not scrape inboxes.

Call it when:

- the operator already holds a file (a `.eml` they saved, a PDF, a note) and wants a hashed drop;
- they want a dead-man **copy on this machine**, not a send path.

Do **not** call it to send anonymous mail, mask IP, hunt inboxes, or store whistle files on the hosted Worker.

Author: **Aziel Eliab**. Apache-2.0. Paper WL-WP-0.1. DOI [10.5281/zenodo.22257762](https://doi.org/10.5281/zenodo.22257762) (that preprint also covers FoldLock; this product is WhistleLock only).

## Hosted /v1 never stores drops

The Worker is a counted download + a preview API.

- `GET /v1/health` — liveness. Does not increment downloads.
- `POST /v1/hash-preview` — SHA-256 of posted bytes. **Not stored.**
- `POST /v1/canon-preview` — hash a proposed ledger row. **Not stored.**
- `GET /v1/skill` — this markdown. Does not increment downloads.

Hosted never holds whistle files. Hosted is not a mailer.

Always send `User-Agent: Mozilla/5.0`. Cloudflare Workers may 403 empty agents.

## OpenAPI and MCP

- This Worker OpenAPI: https://whistlelock-download-tracker.vibelock.workers.dev/openapi.json
- Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json
- MCP: `POST https://whistlelock-download-tracker.vibelock.workers.dev/mcp`
- Catalog MCP: `POST https://aziel-runtime.vibelock.workers.dev/mcp`

Grok: import the OpenAPI as a custom tool. ChatGPT: GPT Actions → Import from URL. Venice: HTTP tools.

Counted install (this Worker, HTTP 200 gzip, no 302 to GitHub):

```bash
curl -fsSL https://whistlelock-download-tracker.vibelock.workers.dev/install.sh | bash
```

Then `whistlelock ui` → http://127.0.0.1:8873 (loopback only). Tap **Init / Drop / Check in / Arm / Tick / Verify**. Dead-man copy is local. Does not mail.

## Honest one-liner

THIS IS a local vault + chained rows + local dead-man copy. THIS IS NOT a mailer, mixnet, IP mask, inbox scraper, UL, FoldLock, EmployeeLock, or GodLock.

Forks are welcome and always allowed.

## Catalog + local UI

Author: **Aziel Eliab**. Honest scope: Local drop ledger + dead-man copy. Not a mailer. Hosted never holds whistle files.

- Catalog product: https://aziel-runtime.vibelock.workers.dev/p/whistlelock/
- Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json
- Catalog MCP: `POST https://aziel-runtime.vibelock.workers.dev/mcp`
- This Worker skill: `GET https://whistlelock-download-tracker.vibelock.workers.dev/v1/skill`
- This Worker OpenAPI: https://whistlelock-download-tracker.vibelock.workers.dev/openapi.json
- Sample payload: `GET https://whistlelock-download-tracker.vibelock.workers.dev/v1/example`

Local UI: **Import JSON file** (`type=file`) and **Export JSON**. Then `whistlelock doctor`.

Grok: import catalog or Worker OpenAPI as a custom tool. ChatGPT: GPT Actions. Venice: HTTP tools.
