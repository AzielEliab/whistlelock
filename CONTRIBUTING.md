# Contributing to WhistleLock

**Forks are first-class.** This project is Apache-2.0; you do not need
permission to fork, patch, or redistribute.

**Forks are welcome and always allowed.**

## How to run tests

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q
```

Python 3.10+. Engine is stdlib only. pytest is the dev extra.
No network. No ML. No mailer.

## Ground rules

1. **Not a mailer.** Do not add From: rotation, SMTP, mixnet, IP masking,
   inbox scraping, or any untraceable-origin send path. Dead-man copy is
   local. The notice says WhistleLock did not mail it.
2. **`--url` is a locator the operator already knows.** Not a hunt.
3. **UI binds loopback only** (`127.0.0.1:8873`). Do not listen on
   `0.0.0.0`. No telemetry. No CDN.
4. **Do not mix the download tracker** with any other product's Worker
   or KV. Namespace `WHISTLELOCK_DOWNLOADS` only.
5. **Public identity is Aziel Eliab.** Do not add GodLock.AZ as an
   identity label.
6. **Do not put private case facts** (Horton, Madelyn, Hamilton Superior)
   in the repo. Demo drops stay generic (`sample drop`).
7. New behavior needs a test that fails without the change.
8. Canonical JSON: UTF-8, sorted keys, compact separators. Genesis
   `prev_hash` is 64 ASCII zeros. Correction = new row.

## Where to change things

- Store / ledger / dead-man: `whistlelock/engine.py`
- CLI: `whistlelock/cli.py`
- Doctor: `whistlelock/doctor.py`
- Local UI: `whistlelock/ui.py`, `whistlelock/web/`
- Spec: `docs/whitepaper.md`
- Skill: `SKILL.md` (same text at Worker `GET /v1/skill`)
- Flutter: `mobile/`
- Isolated counter: `workers/download-tracker/`

## License of contributions

By submitting a change you agree it is licensed under Apache-2.0, the
same license as the rest of the tree. Keep the copyright lines honest.
Ship as Aziel Eliab.
