import json

from whistlelock.doctor import run_doctor


def test_doctor_passes() -> None:
    assert run_doctor(as_json=True) == 0


def test_doctor_human_is_plain(capsys) -> None:
    assert run_doctor(as_json=False) == 0
    out = capsys.readouterr().out
    assert "doctor passed" in out
    assert "[ok] loopback" in out
    assert "THIS IS NOT" not in out


def test_doctor_json_keeps_limitation(capsys) -> None:
    assert run_doctor(as_json=True) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["mails"] is False
    assert payload["network"] is False
    assert payload["telemetry"] is False
    assert "THIS IS NOT" in payload["limitation"]
    assert isinstance(payload["checks"], list)
