# WhistleLock

Local immutable drop + dead-man packet

**Paper ID:** WL-WP-0.1
**Product:** WhistleLock v0
**Author:** Aziel Eliab
**Date:** 2 September 2026
**License:** Apache-2.0
**DOI:** [10.5281/zenodo.22257762](https://doi.org/10.5281/zenodo.22257762)

The Zenodo preprint also covers FoldLock. **This document is the
WhistleLock parts only.** FoldLock lives in a separate product.

Store the record. Chain the row. Release the packet locally. The operator carries it.

## Abstract

WhistleLock is a local vault for materials the operator already holds:
whistle records, investigative files, journalist correspondence saved as
files, and databases in the operator’s possession. Drops are copied into
the store, hashed, and written to an append-only ledger. A dead-man
switch watches a check-in clock. If the clock lapses, the pre-placed
packet is copied into `released/`.

WhistleLock does not mail. It does not rotate sender addresses. It does
not mask IP. It does not scrape inboxes at boot. Those would be an
untraceable-origin send path. That path is refused.

Runtime: `whistlelock.py`. Spec string: `whistlelock-v0`.

## 1. Purpose

Whistle material dies in three ordinary ways: the file is deleted, the
story is renamed until it has no owner, or the holder is silenced before
the packet moves.

WhistleLock answers those with three local acts:

1. **Drop** — copy a file the operator already has. Hash it. Ledger it.
2. **Chain** — each ledger row names the previous row’s hash. Delete is not a command.
3. **Dead-man** — if check-in stops, copy the packet the operator pre-placed into `released/`.

Accuracy is re-hashing what is already in the store. It is not a search
of other people’s mail.

## 2. What this is / is not

**This is**

- a directory store with `HEADER.json`, `ledger.jsonl`, `drops/`, `deadman/packet/`, `deadman/released/`;
- TemporalLock-shaped rows;
- a local dead-man copy;
- optional refresh of an operator-supplied `source_url` at verify time.

**This is not**

- a rotating encrypted identity mailbox;
- an IP-masking or proxy stack;
- a mixnet, drop box in the sky, or anonymous relay;
- a boot scraper of journalist or source inboxes;
- a public website;
- UL, FoldLock, EmployeeLock, or GodLock;
- legal advice. Filing, reporting, and source protection remain the operator’s work outside this tool.

Refused on purpose. Do not build an untraceable-origin upload path. The
operator moves the released packet on a channel they already control.

## 3. Store layout

```
STORE/
  HEADER.json
  ledger.jsonl
  drops/
    DR-<digest12>/
      meta.json
      <original filename>
  deadman/
    state.json
    packet/          # operator places files here
    released/
      <UTC stamp>/   # tick copies packet here when overdue
```

`HEADER.spec` = `whistlelock-v0`.

Drop meta: `drop_id`, `original_name`, `stored_path`, `size_bytes`,
`payload_sha256`, `source_note`, `source_url`, `imported`.

## 4. Ledger

JSONL, append-only. Genesis `prev_hash` = 64 ASCII zeros.

Hashed fields only:

`entry_id`, `timestamp`, `kind`, `summary`, `drop_id`,
`payload_sha256`, `source_note`, `prev_hash`

Canonical form: UTF-8 JSON, sorted keys, compact separators.
`row_hash` = SHA-256 hex of that string.

kind: `drop` | `checkin` | `arm` | `release` | `verify` | `note`.

A correction is a new row. The old line stays.

## 5. Drop

```
python3 whistlelock.py drop STORE FILE --summary TEXT [--source NOTE] [--url URL]
```

Copies FILE into `drops/DR-<first12 of sha256>/`. Writes `meta.json`.
Appends a drop row with the payload digest.

`--url` is a locator the operator already knows (a public page they
saved from). It is not a hunt instruction. `verify --refresh` may fetch
that exact URL and compare hashes. Failure is logged. The local copy is
not deleted.

Email: store a `.eml` or export the operator already possesses.
WhistleLock does not collect mail.

## 6. Dead-man

```
python3 whistlelock.py arm STORE --hours N
python3 whistlelock.py checkin STORE
python3 whistlelock.py tick STORE
```

Arm sets interval and stamps check-in. Check-in resets the clock. Tick
does nothing inside the window. Past the window, tick copies
`deadman/packet/` to `deadman/released/<UTC>/`, writes
`RELEASE_NOTICE.txt`, ledgers `release`, and will not copy again until
the operator arms again.

Boot / cron is the operator’s. Example local unit only:

```
# every 15 minutes, this machine, this store
*/15 * * * * python3 /path/whistlelock.py tick /path/STORE
```

No mailer in that line. No IP flag. No rotating From:.

If the packet directory is empty, release still happens and the notice
file is the whole payload. Put the real files in `packet/` before you arm.

## 7. Verify

```
python3 whistlelock.py verify STORE [--refresh]
```

Walks the ledger (hash + `prev_hash`). Re-hashes each stored drop.
Reports missing files. `--refresh` only hits URLs written at ingest. It
does not discover new sources.

A verify row is itself appended (so the check is in the chain).

## 8. CLI

```
python3 whistlelock.py init STORE
python3 whistlelock.py drop STORE FILE --summary TEXT [--source NOTE] [--url URL]
python3 whistlelock.py checkin STORE
python3 whistlelock.py arm STORE --hours N
python3 whistlelock.py tick STORE
python3 whistlelock.py verify STORE [--refresh]
python3 whistlelock.py list STORE
```

Package also: `whistlelock ui` (127.0.0.1:8873), `whistlelock doctor`.

## 9. Files to reproduce

| File | Role |
|------|------|
| `whistlelock.py` | runtime |
| `whistlelock/engine.py` | store, ledger, dead-man |
| `docs/whitepaper.md` | this paper |
| Python 3 stdlib | hashlib, json, shutil, urllib.request |

Smoke:

```
python3 whistlelock.py init /tmp/wl
echo test > /tmp/wl_sample.txt
python3 whistlelock.py drop /tmp/wl /tmp/wl_sample.txt --summary "sample drop"
python3 whistlelock.py arm /tmp/wl --hours 1
python3 whistlelock.py checkin /tmp/wl
python3 whistlelock.py verify /tmp/wl
python3 whistlelock.py list /tmp/wl
```

## 10. Relation

| Sibling | Boundary |
|---------|----------|
| FoldLock | May fold a text drop. Not this ledger. Separate product. |
| EmployeeLock | Workplace event rows. Not a whistle store. |
| TemporalLock | Ethic borrowed. Product stays separate. |
| UL / BAL | Issue cluster. Do not file WhistleLock under UL-CAT. |

## 11. Limits

WhistleLock v0 does not encrypt the store, does not set exhibit numbers,
does not decide whether a record should be published, does not contact
journalists, and does not hide the operator’s network identity.

## 12. Status

| Item | State |
|------|-------|
| Structure | WhistleLock v0 |
| Paper | WL-WP-0.1 |
| Runtime | whistlelock.py |
| DOI | 10.5281/zenodo.22257762 (preprint also covers FoldLock) |
| License | Apache-2.0 |
| Author | Aziel Eliab |

A fork that adds hidden From: rotation or IP masking and keeps this name
is no longer this spec.
