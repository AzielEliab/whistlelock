# WhistleLock

Local drop ledger + dead-man copy. **Not a mailer.** Author Aziel Eliab.

**Author:** Aziel Eliab
**Date:** 2 September 2026
**License:** [Apache-2.0](LICENSE)
**Version:** 0.1.0
**Spec:** `whistlelock-v0`
**Paper:** WL-WP-0.1 — [docs/whitepaper.md](docs/whitepaper.md) · DOI [10.5281/zenodo.22257762](https://doi.org/10.5281/zenodo.22257762)

That preprint also covers FoldLock. **This repo is WhistleLock only.**

> Store the record. Chain the row. Release the packet locally. The operator carries it.

**Forks are welcome and always allowed.**

## Honest scope

**THIS IS:** local directory store + TemporalLock-shaped rows + local dead-man copy + optional refresh of an operator-supplied `source_url` at verify.

**THIS IS NOT:** rotating encrypted identity mailbox; IP-masking/proxy; mixnet/anonymous relay; boot scraper of inboxes; a public website; UL; FoldLock; EmployeeLock; GodLock; legal advice.

The operator moves released packets on a channel they already control. Demo drops are generic (`sample drop`). Dead-man copy is **local**. WhistleLock **does not mail**.

## One-click install

```bash
curl -fsSL https://whistlelock-download-tracker.vibelock.workers.dev/install.sh | bash
```

The script curls the **counted** tarball from this project's Worker
(`/download`, User-Agent `Mozilla/5.0`), extracts, makes a venv, and
`pip install -e .`. Then run `whistlelock ui`.

Or tap **Download and install** on the Worker homepage — a 6th-grader
button, not curl-only.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
python3 whistlelock.py init ./STORE
echo "sample drop" > /tmp/sample.txt
python3 whistlelock.py drop ./STORE /tmp/sample.txt --summary "sample drop"
python3 whistlelock.py arm ./STORE --hours 1
python3 whistlelock.py checkin ./STORE
python3 whistlelock.py verify ./STORE
whistlelock ui
```

Open http://127.0.0.1:8873 (loopback only). Simple view: **Init / Drop /
Check in / Arm / Tick / Verify**. No CDN, no telemetry. Does not mail.

Self-check: `whistlelock doctor`.

## Counted download (Cloudflare Worker)

**This is the counted download.** GitHub releases exist as a mirror.
The Worker serves the gzip itself (HTTP 200, no 302 to GitHub).

# → [https://whistlelock-download-tracker.vibelock.workers.dev/](https://whistlelock-download-tracker.vibelock.workers.dev/) ←

Direct tarball (also counted):
[whistlelock-0.1.0.tar.gz](https://whistlelock-download-tracker.vibelock.workers.dev/download?asset=whistlelock-0.1.0.tar.gz)

- Live count JSON: [https://whistlelock-download-tracker.vibelock.workers.dev/stats](https://whistlelock-download-tracker.vibelock.workers.dev/stats)
- OpenAPI: [https://whistlelock-download-tracker.vibelock.workers.dev/openapi.json](https://whistlelock-download-tracker.vibelock.workers.dev/openapi.json)
- Skill: [https://whistlelock-download-tracker.vibelock.workers.dev/v1/skill](https://whistlelock-download-tracker.vibelock.workers.dev/v1/skill)
- GitHub: [https://github.com/AzielEliab/whistlelock](https://github.com/AzielEliab/whistlelock)

Isolated counter: Worker `whistlelock-download-tracker`, KV `WHISTLELOCK_DOWNLOADS`. Not mixed with any other product. `/v1` does not increment downloads. Hosted never holds whistle files.

Paper: [doi:10.5281/zenodo.22257762](https://doi.org/10.5281/zenodo.22257762) · [Zenodo record](https://zenodo.org/records/22257762) · `FoldLock_WhistleLock_FL-WP-0.3_WL-WP-0.1.pdf` · Apache-2.0 · Eliab, Aziel.

## CLI

```bash
python3 whistlelock.py init STORE
python3 whistlelock.py drop STORE FILE --summary TEXT [--source NOTE] [--url URL]
python3 whistlelock.py checkin STORE
python3 whistlelock.py arm STORE --hours N
python3 whistlelock.py tick STORE
python3 whistlelock.py verify STORE [--refresh]
python3 whistlelock.py list STORE
whistlelock ui
whistlelock doctor
```

`--url` is a locator the operator already knows. `verify --refresh`
fetches that exact URL only. `tick` copies `deadman/packet/` to
`deadman/released/<UTC>/` and writes `RELEASE_NOTICE.txt` saying
WhistleLock did not mail it. Empty packet still releases the notice.
Will not copy again until re-armed.

Python 3 stdlib only for the engine (`hashlib`, `json`, `shutil`,
`urllib.request`).

## Store

```
STORE/
  HEADER.json          spec = whistlelock-v0
  ledger.jsonl         append-only; genesis prev_hash = 64 ASCII zeros
  drops/DR-<digest12>/
  deadman/state.json
  deadman/packet/      operator places files here
  deadman/released/<UTC>/
```

Hashed fields only: `entry_id`, `timestamp`, `kind`, `summary`,
`drop_id`, `payload_sha256`, `source_note`, `prev_hash`. Canonical UTF-8
JSON, sorted keys, compact separators. kind: `drop|checkin|arm|release|verify|note`.
A correction is a new row.

Cron example (this machine, this store, **no mailer**):

```
*/15 * * * * python3 /path/whistlelock.py tick /path/STORE
```

## Use with AI assistants

Works with ChatGPT (GPT Actions / OpenAI), Grok (xAI), Venice, Claude (Anthropic), Cursor (MCP), Glama (MCP), Perplexity, Microsoft Copilot / Bing, Google Gemini / Vertex, Mistral, Meta AI, Apple Intelligence surfaces, Amazon Q tooling, DuckAssist, You.com, Cohere, and other MCP/OpenAPI-capable assistants.

Skill file: [SKILL.md](SKILL.md). Same markdown at
`GET /v1/skill` (does not increment downloads).

- Worker OpenAPI: https://whistlelock-download-tracker.vibelock.workers.dev/openapi.json
- Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json
- MCP: `POST https://whistlelock-download-tracker.vibelock.workers.dev/mcp`
- Catalog MCP: `POST https://aziel-runtime.vibelock.workers.dev/mcp`

Always send `User-Agent: Mozilla/5.0`. Hosted `/v1` never stores drops
or packets. Ops: `health`, `hash-preview`, `canon-preview`, `skill`.

ChatGPT: GPT Actions → Import from URL (no auth). Grok: import the
OpenAPI as a custom tool, or MCP. Venice: HTTP tools. Claude, Cursor,
Glama, and other MCP clients: `POST` the Worker or catalog MCP URL.
Other OpenAPI-capable assistants: import the same OpenAPI.

```bash
curl -A Mozilla/5.0 https://whistlelock-download-tracker.vibelock.workers.dev/v1/health
curl -A Mozilla/5.0 -X POST https://whistlelock-download-tracker.vibelock.workers.dev/v1/hash-preview \
  -H 'content-type: text/plain' --data-binary 'sample drop'
```

Paper DOI: [10.5281/zenodo.22257762](https://doi.org/10.5281/zenodo.22257762).

## Flutter (iOS + Android)

On-device preview under [mobile/](mobile/). Not a separate repo. Not a
store IPA. `flutter create --org com.azieeliab --project-name whistlelock .`

## Tests

```bash
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
python -m pytest -q
```

## Catalog and Worker import

Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json
Catalog MCP: `POST https://aziel-runtime.vibelock.workers.dev/mcp`
This Worker skill: https://whistlelock-download-tracker.vibelock.workers.dev/v1/skill
This Worker OpenAPI: https://whistlelock-download-tracker.vibelock.workers.dev/openapi.json

Same assistants as above: ChatGPT (GPT Actions / OpenAI), Grok (xAI), Venice, Claude (Anthropic), Cursor (MCP), Glama (MCP), Perplexity, Microsoft Copilot / Bing, Google Gemini / Vertex, Mistral, Meta AI, Apple Intelligence surfaces, Amazon Q tooling, DuckAssist, You.com, Cohere, and other MCP/OpenAPI-capable clients. ChatGPT: GPT Actions (no auth). Grok: import the catalog or Worker OpenAPI as a custom tool, or MCP. Venice: HTTP tools. Claude, Cursor, Glama, and other MCP clients: `POST` the catalog or Worker MCP URL. Always send `User-Agent: Mozilla/5.0`.

## Cite this

Aziel Eliab. WhistleLock. https://github.com/AzielEliab/whistlelock. https://whistlelock-download-tracker.vibelock.workers.dev. https://doi.org/10.5281/zenodo.22257762.

- Catalog: https://aziel-runtime.vibelock.workers.dev/
- Worker homepage: https://whistlelock-download-tracker.vibelock.workers.dev/
- Counted download (gzip HTTP 200, no 302): https://whistlelock-download-tracker.vibelock.workers.dev/download
- GitHub: https://github.com/AzielEliab/whistlelock
- Citation JSON: https://whistlelock-download-tracker.vibelock.workers.dev/cite.json
- DOI: https://doi.org/10.5281/zenodo.22257762

## License

Apache License 2.0. Copyright 2026 Aziel Eliab.
