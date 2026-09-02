"""Command-line interface for WhistleLock.

    python3 whistlelock.py init STORE
    python3 whistlelock.py drop STORE FILE --summary TEXT [--source NOTE] [--url URL]
    python3 whistlelock.py checkin STORE
    python3 whistlelock.py arm STORE --hours N
    python3 whistlelock.py tick STORE
    python3 whistlelock.py verify STORE [--refresh]
    python3 whistlelock.py list STORE
    whistlelock ui
    whistlelock doctor
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from whistlelock import __version__
from whistlelock.engine import (
    LIMITATION,
    arm,
    checkin,
    drop,
    init,
    list_store,
    tick,
    verify,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="whistlelock",
        description=(
            "WhistleLock v0 local drop ledger + dead-man. No anonymous send path. "
            "Local UI: `whistlelock ui` at http://127.0.0.1:8873."
        ),
        epilog=LIMITATION,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="Create a local store (HEADER, ledger, drops, deadman).")
    s.add_argument("store")

    d = sub.add_parser("drop", help="Copy a file the operator already has into the store.")
    d.add_argument("store")
    d.add_argument("file")
    d.add_argument("--summary", required=True)
    d.add_argument("--source", default="")
    d.add_argument("--url", default="")

    c = sub.add_parser("checkin", help="Reset the dead-man clock.")
    c.add_argument("store")

    a = sub.add_parser("arm", help="Arm the dead-man for N hours.")
    a.add_argument("store")
    a.add_argument("--hours", type=int, required=True)

    t = sub.add_parser("tick", help="If overdue, copy packet/ to released/<UTC>/ locally. Does not mail.")
    t.add_argument("store")

    v = sub.add_parser("verify", help="Walk the ledger. Re-hash stored drops. Report missing files.")
    v.add_argument("store")
    v.add_argument("--refresh", action="store_true", help="Fetch operator-supplied source_url only.")

    ls = sub.add_parser("list", help="List drops, rows, and dead-man state.")
    ls.add_argument("store")

    p_ui = sub.add_parser("ui", help="Serve the local UI on 127.0.0.1:8873 (loopback only).")
    p_ui.add_argument("--host", default="127.0.0.1")
    p_ui.add_argument("--port", type=int, default=8873)

    p_doc = sub.add_parser("doctor", help="Self-check: engine, chain, dead-man, loopback.")
    p_doc.add_argument("--json", action="store_true", dest="as_json")

    sub.add_parser("version", help="Print package version.")
    return parser


def _print_json(obj: object) -> None:
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "version":
        print(f"whistlelock {__version__}")
        return 0

    if args.cmd == "doctor":
        from whistlelock.doctor import run_doctor

        return run_doctor(as_json=args.as_json)

    if args.cmd == "ui":
        from whistlelock.ui import serve

        serve(host=args.host, port=args.port)
        return 0

    try:
        if args.cmd == "init":
            _print_json(init(Path(args.store)))
            return 0
        if args.cmd == "drop":
            _print_json(drop(Path(args.store), Path(args.file), args.summary, args.source, args.url))
            return 0
        if args.cmd == "checkin":
            _print_json(checkin(Path(args.store)))
            return 0
        if args.cmd == "arm":
            _print_json(arm(Path(args.store), args.hours))
            return 0
        if args.cmd == "tick":
            _print_json(tick(Path(args.store)))
            return 0
        if args.cmd == "verify":
            rec = verify(Path(args.store), args.refresh)
            _print_json(rec)
            return 0 if rec["ok"] else 1
        if args.cmd == "list":
            _print_json(list_store(Path(args.store)))
            return 0
    except (ValueError, FileNotFoundError) as e:
        print(f"whistlelock: {e}", file=sys.stderr)
        return 1

    parser.error(f"unknown command {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
