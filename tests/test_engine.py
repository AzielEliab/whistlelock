"""Engine contract: init, drop, chain, verify, dead-man, tamper, missing file."""

from __future__ import annotations

import json
from pathlib import Path

from whistlelock.engine import (
    GENESIS,
    arm,
    checkin,
    drop,
    force_overdue,
    init,
    place_packet,
    read_ledger,
    row_hash,
    tick,
    verify,
)


def test_init_drop_chain_verify(tmp_path: Path) -> None:
    store = tmp_path / "wl"
    rec = init(store)
    assert rec["spec"] == "whistlelock-v0"
    assert (store / "HEADER.json").is_file()
    assert (store / "ledger.jsonl").is_file()
    assert (store / "drops").is_dir()
    assert (store / "deadman" / "packet").is_dir()
    assert (store / "deadman" / "released").is_dir()
    assert (store / "deadman" / "state.json").is_file()
    sample = tmp_path / "sample.txt"
    sample.write_text("sample drop\n", encoding="utf-8")
    dropped = drop(store, sample, "sample drop")
    assert dropped["drop_id"].startswith("DR-")
    assert len(dropped["payload_sha256"]) == 64
    assert (store / "drops" / dropped["drop_id"] / "sample.txt").is_file()
    rows = read_ledger(store)
    assert rows[0]["kind"] == "note"
    assert rows[0]["prev_hash"] == GENESIS
    assert rows[1]["kind"] == "drop"
    assert rows[1]["prev_hash"] == rows[0]["row_hash"]
    fields = {k: rows[1][k] for k in (
        "entry_id", "timestamp", "kind", "summary", "drop_id",
        "payload_sha256", "source_note", "prev_hash",
    )}
    assert row_hash(fields) == rows[1]["row_hash"]
    report = verify(store)
    assert report["ok"] is True
    assert report["missing_files"] == []


def test_arm_checkin_tick_inside_window(tmp_path: Path) -> None:
    store = tmp_path / "wl"
    init(store)
    arm(store, 1)
    checkin(store)
    result = tick(store)
    assert result["released"] is False
    assert result["reason"] == "inside window"
    released = list((store / "deadman" / "released").iterdir())
    assert released == []


def test_overdue_tick_copies_and_notice_does_not_mail(tmp_path: Path) -> None:
    store = tmp_path / "wl"
    init(store)
    packet = tmp_path / "packet.txt"
    packet.write_text("operator packet\n", encoding="utf-8")
    place_packet(store, packet)
    arm(store, 1)
    force_overdue(store)
    result = tick(store)
    assert result["released"] is True
    dest = Path(result["dest"])
    assert dest.is_dir()
    notice = (dest / "RELEASE_NOTICE.txt").read_text(encoding="utf-8")
    assert "did not mail" in notice.lower()
    assert (dest / "packet.txt").is_file()
    second = tick(store)
    assert second.get("reason") == "already released"
    stamps = [p.name for p in (store / "deadman" / "released").iterdir() if p.is_dir()]
    assert len(stamps) == 1
    arm(store, 1)
    force_overdue(store)
    third = tick(store)
    assert third["released"] is True
    stamps = [p.name for p in (store / "deadman" / "released").iterdir() if p.is_dir()]
    assert len(stamps) == 2


def test_empty_packet_still_releases_notice(tmp_path: Path) -> None:
    store = tmp_path / "wl"
    init(store)
    arm(store, 1)
    force_overdue(store)
    result = tick(store)
    dest = Path(result["dest"])
    notice = (dest / "RELEASE_NOTICE.txt").read_text(encoding="utf-8")
    assert "did not mail" in notice.lower()


def test_tamper_ledger_verify_fails(tmp_path: Path) -> None:
    store = tmp_path / "wl"
    init(store)
    ledger = store / "ledger.jsonl"
    lines = ledger.read_text(encoding="utf-8").splitlines(True)
    rec = json.loads(lines[0])
    rec["summary"] = "tampered"
    lines[0] = json.dumps(rec, separators=(",", ":"), ensure_ascii=False) + "\n"
    ledger.write_text("".join(lines), encoding="utf-8")
    report = verify(store)
    assert report["ok"] is False
    assert report["errors"]


def test_missing_drop_file_reported(tmp_path: Path) -> None:
    store = tmp_path / "wl"
    init(store)
    sample = tmp_path / "sample.txt"
    sample.write_text("sample drop\n", encoding="utf-8")
    dropped = drop(store, sample, "sample drop")
    dest = store / "drops" / dropped["drop_id"] / "sample.txt"
    dest.unlink()
    report = verify(store)
    assert dropped["drop_id"] in report["missing_files"]
    assert report["ok"] is False
