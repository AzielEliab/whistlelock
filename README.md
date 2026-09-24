# WhistleLock

Keep a local ledger of a file you already have. If you miss a check-in, a packet you placed is copied on this computer.

**Author:** Aziel Eliab
**License:** [Apache-2.0](LICENSE)
**Version:** 0.1.0

## Start

1. `python -m venv .venv && . .venv/bin/activate && pip install -e .`
2. `whistlelock ui`
3. Open http://127.0.0.1:8873/ and tap **Drop a file**.

`whistlelock doctor` checks this machine. `whistlelock --help` lists commands. Add `--json` when you need the same fields as JSON.

The same commands work as `python3 whistlelock.py`.

## Commands

| Command | What you get |
| --- | --- |
| `init STORE` | A new store folder |
| `drop STORE FILE --summary TEXT` | A copy of a file you already have |
| `checkin STORE` | The check-in clock reset |
| `arm STORE --hours N` | Hours until a local copy |
| `tick STORE` | A local copy, if the window has passed |
| `verify STORE` | A chain and file check |
| `list STORE` | Drops and the clock |
| `ui` | The local app at http://127.0.0.1:8873/ |
| `doctor` | A pass/fail check of this machine |

`drop` asks for `--summary`. `--source` and `--url` are optional. `verify --refresh` re-fetches a source URL you already stored. `ui --port` chooses another loopback port.

```bash
whistlelock init ./STORE
whistlelock drop ./STORE ./notes.txt --summary "sample drop"
whistlelock arm ./STORE --hours 24
whistlelock checkin ./STORE
whistlelock --json list ./STORE
```

## Store

```
STORE/
  HEADER.json
  ledger.jsonl
  drops/DR-<digest12>/
  deadman/state.json
  deadman/packet/
  deadman/released/<UTC>/
```

`tick` copies `deadman/packet/` to `deadman/released/<UTC>/` and writes `RELEASE_NOTICE.txt`. The copy stays in that folder. You move the files. An empty packet still writes the notice.

A check every 15 minutes, on this machine, for this store:

```
*/15 * * * * whistlelock tick /path/STORE
```

Python 3 stdlib only for the engine (`hashlib`, `json`, `shutil`, `urllib.request`).

## Phone

On-device preview: [mobile/README.md](mobile/README.md).

## Tests

```bash
python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
python -m pytest -q
```

## Notes

Author: Aziel Eliab. Forks are welcome and always allowed. Spec `whistlelock-v0`. Paper WL-WP-0.1 · [doi:10.5281/zenodo.22257762](https://doi.org/10.5281/zenodo.22257762) (that preprint also covers FoldLock; this product is WhistleLock).

Demo text is `sample drop`. Hosted `/v1` never stores drops or packets. `whistlelock doctor --json` includes the `limitation` field.

Counted download and preview API: https://whistlelock-download-tracker.vibelock.workers.dev/

Direct archive: [whistlelock-0.1.0.tar.gz](https://whistlelock-download-tracker.vibelock.workers.dev/download?asset=whistlelock-0.1.0.tar.gz)

```bash
curl -fsSL https://whistlelock-download-tracker.vibelock.workers.dev/install.sh | bash
```

- OpenAPI: https://whistlelock-download-tracker.vibelock.workers.dev/openapi.json
- Skill: https://whistlelock-download-tracker.vibelock.workers.dev/v1/skill
- Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json
- MCP: `POST https://whistlelock-download-tracker.vibelock.workers.dev/mcp`
- Catalog MCP: `POST https://aziel-runtime.vibelock.workers.dev/mcp`
- GitHub: https://github.com/AzielEliab/whistlelock

`/v1/mesh` proxies the suite mesh through `AZIEL_RUNTIME` (default off; QNM-BUILD-1.0 live / locked / isolated). QNS-CD-1.0 photon QNS1 packet transfer is a hub cite only (local qnsd in [qnm-node](https://github.com/AzielEliab/qnm-node); no public qnsd proxy). Send `User-Agent: Mozilla/5.0`.

## License

Apache License 2.0. Copyright 2026 Aziel Eliab.
