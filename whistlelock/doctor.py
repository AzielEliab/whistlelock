"""Self-check for WhistleLock. NASA-robust, no network, no telemetry.

    whistlelock doctor
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Callable

from whistlelock import __version__
from whistlelock.engine import (
    ENGINE_VERSION,
    GENESIS,
    LIMITATION,
    SPEC_STRING,
    arm,
    checkin,
    drop,
    force_overdue,
    init,
    place_packet,
    tick,
    verify,
)
from whistlelock.ui import LOOPBACK, make_server

Check = tuple[str, bool, str]


def _ok(name: str, detail: str = "") -> Check:
    return name, True, detail


def _fail(name: str, detail: str) -> Check:
    return name, False, detail


def _check_version() -> Check:
    if __version__ == ENGINE_VERSION == "0.1.0":
        return _ok("version", __version__)
    return _fail("version", f"{__version__} vs engine {ENGINE_VERSION}")


def _check_spec() -> Check:
    if SPEC_STRING == "whistlelock-v0":
        return _ok("spec", SPEC_STRING)
    return _fail("spec", SPEC_STRING)


def _check_genesis_and_drop() -> Check:
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp) / "wl"
        rec = init(store)
        if rec["spec"] != "whistlelock-v0":
            return _fail("init spec", rec["spec"])
        sample = Path(tmp) / "sample.txt"
        sample.write_text("sample drop\n", encoding="utf-8")
        dropped = drop(store, sample, "sample drop")
        if not dropped["drop_id"].startswith("DR-"):
            return _fail("drop id", dropped["drop_id"])
        report = verify(store)
        if not report["ok"]:
            return _fail("verify after drop", str(report["errors"]))
        ledger = (store / "ledger.jsonl").read_text(encoding="utf-8").strip().splitlines()
        first = json.loads(ledger[0])
        if first["prev_hash"] != GENESIS:
            return _fail("genesis prev_hash", first["prev_hash"])
        second = json.loads(ledger[1])
        if second["prev_hash"] != first["row_hash"]:
            return _fail("chain link", second["prev_hash"])
        return _ok("genesis+drop", dropped["drop_id"])


def _check_deadman_window() -> Check:
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp) / "wl"
        init(store)
        arm(store, 1)
        checkin(store)
        result = tick(store)
        if result.get("released"):
            return _fail("inside window released", str(result))
        if result.get("reason") != "inside window":
            return _fail("inside window reason", str(result))
        return _ok("inside window", "tick did not copy")


def _check_overdue_release() -> Check:
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp) / "wl"
        init(store)
        packet = Path(tmp) / "packet.txt"
        packet.write_text("operator packet\n", encoding="utf-8")
        place_packet(store, packet)
        arm(store, 1)
        force_overdue(store)
        result = tick(store)
        if not result.get("released"):
            return _fail("overdue did not release", str(result))
        dest = Path(result["dest"])
        notice = (dest / "RELEASE_NOTICE.txt").read_text(encoding="utf-8")
        if "did not mail" not in notice.lower():
            return _fail("notice mail claim", notice)
        if not (dest / "packet.txt").is_file():
            return _fail("packet not copied", str(list(dest.iterdir())))
        second = tick(store)
        if second.get("reason") != "already released":
            return _fail("second tick recopied", str(second))
        before = list((store / "deadman" / "released").iterdir())
        arm(store, 1)
        force_overdue(store)
        third = tick(store)
        if not third.get("released") or third.get("reason") == "already released":
            return _fail("re-arm did not allow release", str(third))
        after = list((store / "deadman" / "released").iterdir())
        if len(after) != len(before) + 1:
            return _fail("re-arm copy count", f"{len(before)} -> {len(after)}")
        return _ok("overdue+idempotent", result["dest"])


def _check_empty_packet_still_notices() -> Check:
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp) / "wl"
        init(store)
        arm(store, 1)
        force_overdue(store)
        result = tick(store)
        dest = Path(result["dest"])
        notice = dest / "RELEASE_NOTICE.txt"
        if not notice.is_file():
            return _fail("empty packet no notice", str(result))
        if "did not mail" not in notice.read_text(encoding="utf-8").lower():
            return _fail("empty packet notice text", notice.read_text(encoding="utf-8"))
        return _ok("empty packet", "notice only")


def _check_tamper() -> Check:
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp) / "wl"
        init(store)
        ledger = store / "ledger.jsonl"
        lines = ledger.read_text(encoding="utf-8").splitlines(True)
        rec = json.loads(lines[0])
        rec["summary"] = "tampered"
        lines[0] = json.dumps(rec, separators=(",", ":"), ensure_ascii=False) + "\n"
        ledger.write_text("".join(lines), encoding="utf-8")
        report = verify(store)
        if report["ok"]:
            return _fail("tamper", "verify did not fail")
        if not report["errors"]:
            return _fail("tamper", "no errors listed")
        return _ok("tamper", report["errors"][0][:80])


def _check_missing_drop() -> Check:
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp) / "wl"
        init(store)
        sample = Path(tmp) / "sample.txt"
        sample.write_text("sample drop\n", encoding="utf-8")
        dropped = drop(store, sample, "sample drop")
        dest = store / "drops" / dropped["drop_id"] / "sample.txt"
        dest.unlink()
        report = verify(store)
        if dropped["drop_id"] not in report["missing_files"]:
            return _fail("missing not reported", str(report))
        if report["ok"]:
            return _fail("missing still ok", str(report))
        return _ok("missing drop", dropped["drop_id"])


def _check_loopback() -> Check:
    try:
        make_server("0.0.0.0", 9)
    except ValueError as exc:
        if "loopback" in str(exc).lower() and "127.0.0.1" in LOOPBACK:
            return _ok("loopback", "rejects 0.0.0.0")
        return _fail("loopback", str(exc))
    return _fail("loopback", "accepted 0.0.0.0")


def _check_no_mailer() -> Check:
    text = Path(__file__).with_name("engine.py").read_text(encoding="utf-8")
    for banned in ("import smtplib", "import socks", "smtp.SMTP", "sendmail("):
        if banned in text:
            return _fail("no mailer", banned)
    if "did not mail" not in text:
        return _fail("no mailer", "release notice missing did-not-mail")
    return _ok("no mailer", "engine has no mailer")


CHECKS: tuple[Callable[[], Check], ...] = (
    _check_version,
    _check_spec,
    _check_genesis_and_drop,
    _check_deadman_window,
    _check_overdue_release,
    _check_empty_packet_still_notices,
    _check_tamper,
    _check_missing_drop,
    _check_loopback,
    _check_no_mailer,
)


def run_doctor(*, as_json: bool = False) -> int:
    results = []
    failed = 0
    for fn in CHECKS:
        name, ok, detail = fn()
        results.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            failed += 1
        mark = "ok" if ok else "FAIL"
        if not as_json:
            print(f"[{mark}] {name}" + (f" — {detail}" if detail else ""))
    payload = {
        "ok": failed == 0,
        "failed": failed,
        "checks": results,
        "version": __version__,
        "spec": SPEC_STRING,
        "limitation": LIMITATION,
        "network": False,
        "telemetry": False,
        "mails": False,
    }
    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        print("limitation:", LIMITATION)
        print("doctor", "passed" if failed == 0 else "failed")
    return 0 if failed == 0 else 1
