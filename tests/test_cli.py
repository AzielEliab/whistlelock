"""CLI: init, drop, verify, ui, doctor, version."""

from __future__ import annotations

import json
from pathlib import Path

from whistlelock import __version__
from whistlelock.cli import main


def test_cli_version(capsys) -> None:
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == f"whistlelock {__version__}"
    assert __version__ == "0.1.0"


def test_help_lists_commands(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    out = capsys.readouterr().out
    for word in ("init", "drop", "checkin", "arm", "tick", "verify", "list", "ui", "doctor"):
        assert word in out


def test_cli_init_drop_verify(tmp_path: Path, capsys) -> None:
    store = tmp_path / "wl"
    sample = tmp_path / "sample.txt"
    sample.write_text("sample drop\n", encoding="utf-8")
    assert main(["init", str(store)]) == 0
    capsys.readouterr()
    assert main(["drop", str(store), str(sample), "--summary", "sample drop"]) == 0
    rec = json.loads(capsys.readouterr().out)
    assert rec["drop_id"].startswith("DR-")
    assert main(["verify", str(store)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is True
    assert main(["list", str(store)]) == 0
    listing = json.loads(capsys.readouterr().out)
    assert listing["spec"] == "whistlelock-v0"
    assert listing["drops"]
