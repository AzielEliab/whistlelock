"""Local UI: loopback only, Simple buttons, no CDN, does not mail."""

from __future__ import annotations

import json
import threading
import urllib.request

import pytest

from whistlelock.ui import LOOPBACK, make_server


def test_ui_rejects_non_loopback() -> None:
    with pytest.raises(ValueError, match="loopback"):
        make_server("0.0.0.0", 9)
    assert "127.0.0.1" in LOOPBACK


def _serve():
    httpd = make_server("127.0.0.1", 0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


def test_ui_get_root_honest_scope() -> None:
    httpd = _serve()
    port = httpd.server_address[1]
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5) as resp:
            html = resp.read().decode("utf-8")
        assert "WhistleLock" in html
        assert "THIS IS" in html
        assert "THIS IS NOT" in html
        assert "does not mail" in html.lower() or "did not mail" in html.lower()
        assert "Init" in html
        assert "Drop" in html
        assert "Check in" in html
        assert "Arm" in html
        assert "Tick" in html
        assert "Verify" in html
        assert "cdnjs" not in html.lower()
        assert "unpkg" not in html.lower()
        assert "jsdelivr" not in html.lower()
        assert "GodLock.AZ" not in html
        assert "Horton" not in html
        assert "Madelyn" not in html
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/style.css", timeout=3) as resp:
            css = resp.read().decode("utf-8")
        assert "--gold" in css or "c9a227" in css
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=3) as resp:
            health = json.loads(resp.read().decode("utf-8"))
        assert health["ok"] is True
        assert health["loopback"] is True
        assert health["telemetry"] is False
        assert health["mails"] is False
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/sample",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            state = json.loads(resp.read().decode("utf-8"))
        assert state["verify"]["ok"] is True
        assert state["counts"]["drops"] >= 1
        assert state["mails"] is False
        assert state["deadman_local"] is True
    finally:
        httpd.shutdown()
        httpd.server_close()
