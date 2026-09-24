"""CLI: human welcome, --json shapes, plain errors."""

from __future__ import annotations

import json
from pathlib import Path

from whistlelock import __version__
from whistlelock.cli import main


def _run(argv: list[str]) -> int:
    try:
        return main(argv)
    except SystemExit as exc:
        return int(exc.code or 0)


def test_cli_version(capsys) -> None:
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == f"whistlelock {__version__}"
    assert __version__ == "0.1.0"


def test_version_json(capsys) -> None:
    assert main(["version", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"version": __version__}


def test_bare_welcome(capsys) -> None:
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "whistlelock ui" in out
    assert "whistlelock --help" in out
    assert "required" not in out.lower()
    assert not out.lstrip().startswith("{")


def test_help_lists_commands(capsys) -> None:
    assert _run(["--help"]) == 0
    out = capsys.readouterr().out
    for word in ("init", "drop", "checkin", "arm", "tick", "verify", "list", "ui", "doctor"):
        assert word in out
    assert "--json" in out
    assert "Examples" in out
    assert "THIS IS NOT" not in out
    assert "arguments are required" not in out


def test_unknown_command(capsys) -> None:
    assert _run(["bogus"]) == 2
    err = capsys.readouterr().err
    assert 'Unknown command "bogus"' in err
    assert "whistlelock --help" in err
    assert "Traceback" not in err


def test_drop_needs_summary(tmp_path: Path, capsys) -> None:
    store = tmp_path / "wl"
    assert main(["--json", "init", str(store)]) == 0
    capsys.readouterr()
    sample = tmp_path / "sample.txt"
    sample.write_text("sample drop\n", encoding="utf-8")
    assert main(["drop", str(store), str(sample)]) == 2
    err = capsys.readouterr().err
    assert "summary" in err.lower()
    assert "Next:" in err


def test_missing_file_has_next_step(tmp_path: Path, capsys) -> None:
    store = tmp_path / "wl"
    assert main(["init", str(store)]) == 0
    capsys.readouterr()
    missing = tmp_path / "missing.txt"
    assert main(["drop", str(store), str(missing), "--summary", "sample drop"]) == 1
    err = capsys.readouterr().err
    assert "not found" in err.lower()
    assert "Next:" in err
    assert "Traceback" not in err


def test_cli_init_drop_verify(tmp_path: Path, capsys) -> None:
    store = tmp_path / "wl"
    sample = tmp_path / "sample.txt"
    sample.write_text("sample drop\n", encoding="utf-8")
    assert main(["--json", "init", str(store)]) == 0
    created = json.loads(capsys.readouterr().out)
    assert created["spec"] == "whistlelock-v0"
    assert main(["drop", str(store), str(sample), "--summary", "sample drop"]) == 0
    human = capsys.readouterr().out
    assert "Dropped" in human
    assert "DR-" in human
    assert not human.lstrip().startswith("{")
    assert main(["--json", "drop", str(store), str(sample), "--summary", "sample drop"]) == 0
    rec = json.loads(capsys.readouterr().out)
    assert rec["drop_id"].startswith("DR-")
    assert "payload_sha256" in rec
    assert main(["--json", "verify", str(store)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is True
    assert "missing_files" in report
    assert main(["--json", "list", str(store)]) == 0
    listing = json.loads(capsys.readouterr().out)
    assert listing["spec"] == "whistlelock-v0"
    assert listing["drops"]
    assert "deadman" in listing


def test_tick_human_and_json(tmp_path: Path, capsys) -> None:
    store = tmp_path / "wl"
    assert main(["init", str(store)]) == 0
    capsys.readouterr()
    assert main(["tick", str(store)]) == 0
    assert "Not armed" in capsys.readouterr().out
    assert main(["tick", str(store), "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"released": False, "reason": "not armed"}


def test_ui_rejects_public_host(capsys) -> None:
    assert _run(["ui", "--host", "0.0.0.0", "--port", "9"]) == 1
    err = capsys.readouterr().err
    assert "loopback" in err.lower()
    assert "Next:" in err
