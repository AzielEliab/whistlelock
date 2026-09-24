"""Command-line interface for WhistleLock.

Human text is the default. Pass --json for the same fields as JSON.

    whistlelock
    whistlelock ui
    whistlelock init STORE
    whistlelock drop STORE FILE --summary TEXT
    whistlelock --json list STORE
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Sequence

from whistlelock import __version__
from whistlelock.engine import arm, checkin, drop, init, list_store, tick, verify

HELP = """\
usage: whistlelock <command> [options]

WhistleLock keeps a local ledger of files you already have,
and copies a packet on this computer if you miss a check-in.

Start
  ui                         Open the local app
  doctor                     Check the engine on this machine

Common
  init STORE                 Create a store folder
  drop STORE FILE            Copy a file you already have into the store
                             (--summary TEXT is required)
  checkin STORE              Reset the check-in clock
  arm STORE --hours N        Set how many hours until a local copy
  tick STORE                 If the window has passed, copy the packet here
  verify STORE               Check the chain and the stored files
  list STORE                 Show drops and the check-in clock

Other
  version                    Print the version
  help                       Show this help

Advanced
  verify STORE --refresh     Re-fetch a source URL already stored on a drop
  ui --port PORT             Another loopback port (default 8873)
  ui --host HOST             Loopback only: 127.0.0.1, localhost, or ::1

Add --json to any command for the same fields as JSON.

Examples
  whistlelock ui
  whistlelock init ./STORE
  whistlelock drop ./STORE ./notes.txt --summary "sample drop"
  whistlelock doctor

Author: Aziel Eliab
"""

WELCOME = """\
WhistleLock keeps a local ledger of files you already have, and copies a packet on this computer if you miss a check-in.

Open the app:
  whistlelock ui

Or from the terminal:
  whistlelock init ./STORE
  whistlelock doctor
  whistlelock --help
"""

_CHOICE = re.compile(r"invalid choice: '([^']+)'")


class FriendlyParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        match = _CHOICE.search(message)
        if match:
            choice = match.group(1)
            self.exit(
                2,
                f'Unknown command "{choice}". Try: whistlelock ui   or   whistlelock --help\n',
            )
        self.exit(2, _usage_hint(self.prog, message) + "\n")


def _usage_hint(prog: str, message: str) -> str:
    if "invalid int value" in message and prog.endswith(" arm"):
        return 'Hours must be a whole number greater than 0.\nNext: whistlelock arm ./STORE --hours 24'
    if "invalid int value" in message and prog.endswith(" ui"):
        return "The port must be a number.\nNext: whistlelock ui --port 8873"
    hints = {
        "whistlelock init": "Init needs a folder for the store.\nNext: whistlelock init ./STORE",
        "whistlelock drop": (
            'Drop needs a store, a file, and a summary.\n'
            'Next: whistlelock drop ./STORE ./file.txt --summary "sample drop"'
        ),
        "whistlelock checkin": "Check-in needs a store.\nNext: whistlelock checkin ./STORE",
        "whistlelock arm": (
            "Arm needs a store and how many hours to wait.\n"
            "Next: whistlelock arm ./STORE --hours 24"
        ),
        "whistlelock tick": "Tick needs a store.\nNext: whistlelock tick ./STORE",
        "whistlelock verify": "Verify needs a store.\nNext: whistlelock verify ./STORE",
        "whistlelock list": "List needs a store.\nNext: whistlelock list ./STORE",
    }
    if prog in hints and ("required" in message or "invalid" in message):
        return hints[prog]
    if prog in hints and message.startswith("the following arguments"):
        return hints[prog]
    return f"{message}\nNext: whistlelock --help"


def _json_flag() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--json", action="store_true", help="Print JSON for scripts.")
    return parent


def _build_parser() -> FriendlyParser:
    parser = FriendlyParser(prog="whistlelock", description="WhistleLock local ledger.", add_help=True)
    sub = parser.add_subparsers(dest="cmd")
    machine = _json_flag()

    s = sub.add_parser("init", parents=[machine], help="Create a store folder.")
    s.add_argument("store")

    d = sub.add_parser("drop", parents=[machine], help="Copy a file you already have into the store.")
    d.add_argument("store")
    d.add_argument("file")
    d.add_argument("--summary", default=None)
    d.add_argument("--source", default="")
    d.add_argument("--url", default="")

    c = sub.add_parser("checkin", parents=[machine], help="Reset the check-in clock.")
    c.add_argument("store")

    a = sub.add_parser("arm", parents=[machine], help="Set how many hours until a local copy.")
    a.add_argument("store")
    a.add_argument("--hours", type=int, default=None)

    t = sub.add_parser("tick", parents=[machine], help="If the window has passed, copy the packet here.")
    t.add_argument("store")

    v = sub.add_parser("verify", parents=[machine], help="Check the chain and the stored files.")
    v.add_argument("store")
    v.add_argument("--refresh", action="store_true", help="Re-fetch a source URL already stored on a drop.")

    ls = sub.add_parser("list", parents=[machine], help="Show drops and the check-in clock.")
    ls.add_argument("store")

    p_ui = sub.add_parser("ui", help="Open the local app on this computer.")
    p_ui.add_argument("--host", default="127.0.0.1")
    p_ui.add_argument("--port", type=int, default=8873)

    sub.add_parser("doctor", parents=[machine], help="Check the engine on this machine.")
    sub.add_parser("version", parents=[machine], help="Print the version.")
    sub.add_parser("help", help="Show this help.")
    return parser


def _print_json(obj: object) -> None:
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def _emit(obj: object, as_json: bool, human: str) -> None:
    if as_json:
        _print_json(obj)
    else:
        sys.stdout.write(human if human.endswith("\n") else human + "\n")


def _explain(exc: BaseException, store: str) -> str:
    if isinstance(exc, FileNotFoundError):
        name = str(exc.filename or exc)
        if name.endswith(("state.json", "HEADER.json", "ledger.jsonl")):
            return f"No store at {store} yet.\nNext: whistlelock init {store}"
        return (
            f"File not found: {name}\n"
            f'Next: Check the path, then whistlelock drop {store} ./file.txt --summary "sample drop"'
        )
    text = str(exc)
    if "already exists" in text:
        return f"A store is already at {store}.\nNext: whistlelock list {store}"
    if "init the store first" in text or "no ledger" in text:
        return f"No store at {store} yet.\nNext: whistlelock init {store}"
    if "hours must be" in text:
        return f"Hours must be greater than 0.\nNext: whistlelock arm {store} --hours 24"
    return f"{text}\nNext: whistlelock --help"


def _fmt_list(data: dict) -> str:
    dead = data["deadman"]
    lines = [
        f"Store: {data['store']}",
        f"Spec: {data['spec']}",
        f"Rows: {data['rows']}",
        f"Drops: {len(data['drops'])}",
    ]
    for item in data["drops"]:
        lines.append(f"  {item.get('drop_id', '')}  {item.get('original_name', '')}")
    packet = data.get("packet_items") or []
    lines.append(f"Packet files: {len(packet)}")
    if dead.get("armed"):
        lines.append(
            f"Clock: armed for {dead.get('interval_hours')} hour(s). "
            f"Last check-in: {dead.get('last_checkin') or 'none'}."
        )
        if dead.get("released"):
            lines.append("A local copy was already made.")
    else:
        lines.append("Clock: not armed.")
        lines.append(f"Next: whistlelock arm {data['store']} --hours 24")
    return "\n".join(lines)


def _fmt_tick(rec: dict, store: str) -> str:
    reason = rec.get("reason")
    if reason == "not armed":
        return f"Not armed yet.\nNext: whistlelock arm {store} --hours 24"
    if reason == "inside window":
        return f"Inside the window. Nothing was copied.\nNext: whistlelock checkin {store}"
    if reason == "already released":
        return f"Already copied on this computer.\nNext: whistlelock arm {store} --hours 24"
    if reason == "no checkin clock":
        return f"There is no check-in clock yet.\nNext: whistlelock arm {store} --hours 24"
    if rec.get("released") and rec.get("dest"):
        copied = ", ".join(rec.get("copied") or []) or "notice only"
        return (
            f"Copied on this computer: {rec['dest']}\n"
            f"Files: {copied}\n"
            "The copy was not mailed.\n\n"
            f"Next: whistlelock list {store}"
        )
    return f"Tick finished.\nNext: whistlelock list {store}"


def _fmt_verify(rec: dict, store: str) -> str:
    if rec["ok"]:
        return f"Chain checks out.\nRows: {rec['rows']}\nMissing files: 0"
    lines = ["The chain needs a look."]
    for err in rec["errors"]:
        lines.append(f"- {err}")
    for missing in rec["missing_files"]:
        lines.append(f"- Missing file: {missing}")
    for mismatch in rec.get("url_mismatch") or []:
        lines.append(f"- Source URL differs: {mismatch}")
    lines.append(f"Next: whistlelock list {store}")
    return "\n".join(lines)


def _split_json(argv: Sequence[str]) -> tuple[list[str], bool]:
    return [arg for arg in argv if arg != "--json"], "--json" in argv


def main(argv: Sequence[str] | None = None) -> int:
    raw_in = list(sys.argv[1:] if argv is None else argv)
    raw, as_json = _split_json(raw_in)
    if not raw:
        sys.stdout.write(WELCOME)
        return 0
    if raw in (["-h"], ["--help"], ["help"]):
        sys.stdout.write(HELP)
        return 0

    parser = _build_parser()
    args = parser.parse_args(raw)
    as_json = as_json or bool(getattr(args, "json", False))

    if args.cmd in {None, "help"}:
        sys.stdout.write(HELP if args.cmd == "help" else WELCOME)
        return 0

    if args.cmd == "version":
        if as_json:
            _print_json({"version": __version__})
        else:
            print(f"whistlelock {__version__}")
        return 0

    if args.cmd == "doctor":
        from whistlelock.doctor import run_doctor

        return run_doctor(as_json=as_json)

    if args.cmd == "ui":
        from whistlelock.ui import serve

        try:
            serve(host=args.host, port=args.port)
        except ValueError as exc:
            print(f"{exc}\nNext: whistlelock ui", file=sys.stderr)
            return 1
        except OSError as exc:
            detail = exc.strerror or str(exc)
            print(
                f"Could not listen on {args.host}:{args.port} ({detail}).\n"
                "Next: whistlelock ui --port 8874",
                file=sys.stderr,
            )
            return 1
        return 0

    store = str(getattr(args, "store", "./STORE"))
    try:
        if args.cmd == "init":
            rec = init(Path(store))
            _emit(
                rec,
                as_json,
                f"Store ready: {rec['store']}\n"
                f"Spec: {rec['spec']}\n\n"
                f'Next: whistlelock drop {store} ./file.txt --summary "sample drop"',
            )
            return 0
        if args.cmd == "drop":
            if not args.summary:
                print(
                    'Drop needs a summary.\n'
                    f'Next: whistlelock drop {store} {args.file} --summary "sample drop"',
                    file=sys.stderr,
                )
                return 2
            rec = drop(Path(store), Path(args.file), args.summary, args.source, args.url)
            _emit(
                rec,
                as_json,
                f"Dropped {Path(args.file).name}\n"
                f"Drop: {rec['drop_id']}\n"
                f"SHA-256: {rec['payload_sha256']}\n"
                f"Size: {rec['size']} bytes\n\n"
                f"Next: whistlelock verify {store}",
            )
            return 0
        if args.cmd == "checkin":
            rec = checkin(Path(store))
            armed = "yes" if rec["armed"] else "no"
            nxt = (
                f"whistlelock tick {store}"
                if rec["armed"]
                else f"whistlelock arm {store} --hours 24"
            )
            _emit(
                rec,
                as_json,
                f"Checked in at {rec['last_checkin']}.\nArmed: {armed}\n\nNext: {nxt}",
            )
            return 0
        if args.cmd == "arm":
            if args.hours is None:
                print(
                    "Arm needs how many hours to wait.\n"
                    f"Next: whistlelock arm {store} --hours 24",
                    file=sys.stderr,
                )
                return 2
            rec = arm(Path(store), args.hours)
            _emit(
                rec,
                as_json,
                f"Armed for {rec['interval_hours']} hour(s).\n"
                "If that window passes with no check-in, tick copies the packet on this computer.\n\n"
                f"Next: whistlelock checkin {store}",
            )
            return 0
        if args.cmd == "tick":
            rec = tick(Path(store))
            _emit(rec, as_json, _fmt_tick(rec, store))
            return 0
        if args.cmd == "verify":
            rec = verify(Path(store), args.refresh)
            _emit(rec, as_json, _fmt_verify(rec, store))
            return 0 if rec["ok"] else 1
        if args.cmd == "list":
            rec = list_store(Path(store))
            _emit(rec, as_json, _fmt_list(rec))
            return 0
    except (ValueError, FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        if isinstance(exc, json.JSONDecodeError):
            print(
                "The store files could not be read.\nNext: whistlelock doctor",
                file=sys.stderr,
            )
            return 1
        print(_explain(exc, store), file=sys.stderr)
        return 1

    print(f'Unknown command "{args.cmd}". Try: whistlelock ui   or   whistlelock --help', file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
