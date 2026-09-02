#!/usr/bin/env python3
"""WhistleLock v0 — local immutable drop ledger + dead-man packet.

Not an anonymous mailer. Not an IP mask. Not an inbox scraper.
The operator moves anything that leaves this store.

Spec: whistlelock-v0. Paper: WL-WP-0.1. Author: Aziel Eliab.
Python 3 stdlib only (hashlib, json, shutil, urllib.request).
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ENGINE_VERSION = "0.1.0"
SPEC = "whistlelock-v0"
SPEC_STRING = SPEC
PAPER_ID = "WL-WP-0.1"
GENESIS = "0" * 64
GENESIS_PREV = GENESIS
KINDS = ("drop", "checkin", "arm", "release", "verify", "note")
HASHED_FIELDS = (
    "entry_id",
    "timestamp",
    "kind",
    "summary",
    "drop_id",
    "payload_sha256",
    "source_note",
    "prev_hash",
)
LIMITATION = (
    "THIS IS: local directory store + TemporalLock-shaped rows + local dead-man "
    "copy + optional refresh of an operator-supplied source_url at verify. "
    "THIS IS NOT: rotating encrypted identity mailbox; IP-masking/proxy; "
    "mixnet/anonymous relay; boot scraper of inboxes; a public website; UL; "
    "FoldLock; EmployeeLock; GodLock; legal advice. The operator moves released "
    "packets on a channel they already control. WhistleLock does not mail."
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def canon(fields: dict) -> str:
    body = {
        "entry_id": fields["entry_id"],
        "timestamp": fields["timestamp"],
        "kind": fields["kind"],
        "summary": fields["summary"],
        "drop_id": fields["drop_id"],
        "payload_sha256": fields["payload_sha256"],
        "source_note": fields["source_note"],
        "prev_hash": fields["prev_hash"],
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_json(fields: dict) -> str:
    return canon(fields)


def row_hash(fields: dict) -> str:
    return hashlib.sha256(canon(fields).encode("utf-8")).hexdigest()


def store_paths(root: Path) -> dict:
    root = Path(root)
    return {
        "root": root,
        "header": root / "HEADER.json",
        "ledger": root / "ledger.jsonl",
        "drops": root / "drops",
        "packet": root / "deadman" / "packet",
        "released": root / "deadman" / "released",
        "deadman": root / "deadman" / "state.json",
    }


def load_header(p: dict) -> dict:
    return json.loads(p["header"].read_text(encoding="utf-8"))


def write_header(p: dict, header: dict) -> None:
    p["header"].write_text(json.dumps(header, indent=2) + "\n", encoding="utf-8")


def last_hash(p: dict) -> str:
    if not p["ledger"].exists() or p["ledger"].stat().st_size == 0:
        return GENESIS
    last = ""
    with p["ledger"].open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last = line
    return json.loads(last)["row_hash"]


def next_id(p: dict, prefix: str) -> str:
    n = 0
    if p["ledger"].exists():
        with p["ledger"].open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    n += 1
    return f"{prefix}-{n+1:04d}"


def append(p: dict, kind: str, summary: str, drop_id: str = "", payload: str = "", source: str = "") -> dict:
    if kind not in KINDS:
        raise ValueError(f"bad kind {kind}")
    fields = {
        "entry_id": next_id(p, "WL"),
        "timestamp": utc_now(),
        "kind": kind,
        "summary": summary,
        "drop_id": drop_id,
        "payload_sha256": payload,
        "source_note": source,
        "prev_hash": last_hash(p),
    }
    digest = row_hash(fields)
    rec = dict(fields)
    rec["canonical"] = canon(fields)
    rec["row_hash"] = digest
    with p["ledger"].open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, separators=(",", ":"), ensure_ascii=False) + "\n")
    return rec


def read_ledger(root: Path) -> list[dict]:
    p = store_paths(root)
    rows: list[dict] = []
    if not p["ledger"].exists():
        return rows
    with p["ledger"].open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def init(root: Path) -> dict:
    p = store_paths(root)
    if p["header"].exists():
        raise ValueError(f"store already exists: {root}")
    p["drops"].mkdir(parents=True)
    p["packet"].mkdir(parents=True)
    p["released"].mkdir(parents=True)
    header = {
        "spec": SPEC,
        "created": utc_now(),
        "note": "Local drop ledger. Operator moves released packets. No anonymous send path.",
    }
    write_header(p, header)
    p["ledger"].write_text("", encoding="utf-8")
    p["deadman"].write_text(
        json.dumps(
            {
                "armed": False,
                "interval_hours": 0,
                "armed_at": "",
                "last_checkin": "",
                "released": False,
                "last_release": "",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    rec = append(p, "note", "store genesis")
    return {"store": str(root), "spec": SPEC, "genesis": rec["row_hash"]}


def drop(root: Path, src: Path, summary: str, source: str = "", url: str = "") -> dict:
    p = store_paths(root)
    if not p["header"].exists():
        raise ValueError("init the store first")
    src = Path(src)
    if not src.is_file():
        raise FileNotFoundError(src)
    digest, size = sha256_file(src)
    drop_id = f"DR-{digest[:12]}"
    dest_dir = p["drops"] / drop_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if not dest.exists():
        shutil.copy2(src, dest)
    meta = {
        "drop_id": drop_id,
        "original_name": src.name,
        "stored_path": str(dest),
        "size_bytes": size,
        "payload_sha256": digest,
        "source_note": source,
        "source_url": url,
        "imported": utc_now(),
    }
    (dest_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    rec = append(
        p,
        "drop",
        summary,
        drop_id=drop_id,
        payload=digest,
        source=source or url,
    )
    return {"drop_id": drop_id, "payload_sha256": digest, "size": size, "entry_id": rec["entry_id"]}


def load_deadman(p: dict) -> dict:
    return json.loads(p["deadman"].read_text(encoding="utf-8"))


def save_deadman(p: dict, state: dict) -> None:
    p["deadman"].write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def checkin(root: Path) -> dict:
    p = store_paths(root)
    state = load_deadman(p)
    state["last_checkin"] = utc_now()
    save_deadman(p, state)
    rec = append(p, "checkin", f"checkin at {state['last_checkin']}")
    return {"last_checkin": state["last_checkin"], "armed": state["armed"], "entry_id": rec["entry_id"]}


def arm(root: Path, hours: int) -> dict:
    if hours <= 0:
        raise ValueError("hours must be > 0")
    p = store_paths(root)
    state = load_deadman(p)
    state["armed"] = True
    state["interval_hours"] = hours
    state["armed_at"] = utc_now()
    state["last_checkin"] = state["armed_at"]
    state["released"] = False
    state["last_release"] = ""
    save_deadman(p, state)
    rec = append(p, "arm", f"armed {hours}h")
    return {"armed": True, "interval_hours": hours, "entry_id": rec["entry_id"]}


def parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def tick(root: Path) -> dict:
    p = store_paths(root)
    state = load_deadman(p)
    if not state.get("armed"):
        return {"released": False, "reason": "not armed"}
    if state.get("released"):
        return {"released": True, "reason": "already released", "at": state.get("last_release")}
    last = state.get("last_checkin") or state.get("armed_at")
    if not last:
        return {"released": False, "reason": "no checkin clock"}
    age_h = (datetime.now(timezone.utc) - parse_ts(last)).total_seconds() / 3600.0
    if age_h < float(state["interval_hours"]):
        return {
            "released": False,
            "reason": "inside window",
            "age_hours": round(age_h, 4),
            "interval_hours": state["interval_hours"],
        }
    stamp = utc_now().replace(":", "")
    dest = p["released"] / stamp
    n = 2
    while dest.exists():
        dest = p["released"] / f"{stamp}-{n}"
        n += 1
    dest.mkdir(parents=True)
    copied = []
    if p["packet"].exists():
        for item in p["packet"].iterdir():
            target = dest / item.name
            if item.is_file():
                shutil.copy2(item, target)
                copied.append(item.name)
            elif item.is_dir():
                shutil.copytree(item, target)
                copied.append(item.name + "/")
    notice = dest / "RELEASE_NOTICE.txt"
    notice.write_text(
        "WhistleLock dead-man release\n"
        f"released_at: {utc_now()}\n"
        f"last_checkin: {last}\n"
        f"interval_hours: {state['interval_hours']}\n"
        "This packet was copied locally. WhistleLock did not mail it.\n"
        "The operator moves the files.\n",
        encoding="utf-8",
    )
    state["released"] = True
    state["last_release"] = utc_now()
    save_deadman(p, state)
    rec = append(p, "release", f"dead-man copied {len(copied)} items to {dest.name}")
    return {
        "released": True,
        "dest": str(dest),
        "copied": copied,
        "entry_id": rec["entry_id"],
    }


def verify(root: Path, refresh: bool = False, record: bool = True) -> dict:
    import urllib.request

    p = store_paths(root)
    errors = []
    expected = GENESIS
    rows = 0
    if not p["ledger"].exists():
        raise ValueError("no ledger")
    with p["ledger"].open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            rec = json.loads(line)
            rows += 1
            fields = {k: rec[k] for k in HASHED_FIELDS}
            if row_hash(fields) != rec.get("row_hash"):
                errors.append(f"line {i} hash mismatch {rec.get('entry_id')}")
            if rec.get("prev_hash") != expected:
                errors.append(f"line {i} chain break {rec.get('entry_id')}")
            expected = rec.get("row_hash")
    missing = []
    url_mismatch = []
    for meta_path in p["drops"].glob("*/meta.json"):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        stored = Path(meta["stored_path"])
        if not stored.is_file():
            missing.append(meta["drop_id"])
            continue
        got, _n = sha256_file(stored)
        if got != meta["payload_sha256"]:
            errors.append(f"drop {meta['drop_id']} payload hash mismatch")
        if refresh and meta.get("source_url"):
            try:
                with urllib.request.urlopen(meta["source_url"], timeout=20) as resp:
                    remote = hashlib.sha256(resp.read()).hexdigest()
                if remote != meta["payload_sha256"]:
                    url_mismatch.append(meta["drop_id"])
            except Exception as e:  # noqa: BLE001 — verify must not crash the store
                errors.append(f"drop {meta['drop_id']} refresh failed: {e}")
    out = {
        "ok": not errors and not missing and not url_mismatch,
        "rows": rows,
        "errors": errors,
        "missing_files": missing,
        "url_mismatch": url_mismatch,
        "entry_id": "",
    }
    if record:
        rec = append(
            p,
            "verify",
            f"verify rows={rows} errors={len(errors)} missing={len(missing)} refresh={refresh}",
        )
        out["entry_id"] = rec["entry_id"]
    return out


def list_store(root: Path) -> dict:
    p = store_paths(root)
    drops = []
    for meta_path in sorted(p["drops"].glob("*/meta.json")):
        drops.append(json.loads(meta_path.read_text(encoding="utf-8")))
    rows = 0
    if p["ledger"].exists():
        with p["ledger"].open(encoding="utf-8") as f:
            rows = sum(1 for line in f if line.strip())
    return {
        "store": str(root),
        "spec": load_header(p)["spec"],
        "rows": rows,
        "drops": drops,
        "deadman": load_deadman(p),
        "packet_items": [x.name for x in p["packet"].iterdir()] if p["packet"].exists() else [],
    }


def place_packet(root: Path, src: Path) -> dict:
    """Copy a file the operator already has into deadman/packet/. Not a mailer."""
    p = store_paths(root)
    if not p["header"].exists():
        raise ValueError("init the store first")
    src = Path(src)
    if not src.is_file():
        raise FileNotFoundError(src)
    p["packet"].mkdir(parents=True, exist_ok=True)
    dest = p["packet"] / src.name
    shutil.copy2(src, dest)
    return {"packet": str(dest), "name": src.name}


def force_overdue(root: Path) -> dict:
    """Test helper: set last_checkin far in the past so the next tick is overdue."""
    p = store_paths(root)
    state = load_deadman(p)
    state["last_checkin"] = "2000-01-01T00:00:00Z"
    save_deadman(p, state)
    return {"last_checkin": state["last_checkin"], "armed": state.get("armed")}
