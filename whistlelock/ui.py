"""Local WhistleLock UI. Bind 127.0.0.1:8873 only.

Simple: Init, Drop, Check in, Arm, Tick, Verify.
Advanced: List, Doctor, Export receipt, packet file, ledger JSON.
Dead-man copy is LOCAL. Banner: does not mail. No CDN, no telemetry.
"""

from __future__ import annotations

import base64
import io
import json
import tempfile
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlparse

from whistlelock.engine import (
    ENGINE_VERSION,
    LIMITATION,
    arm,
    checkin,
    drop,
    init,
    list_store,
    place_packet,
    read_ledger,
    tick,
    verify,
)

LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})
WEB = files("whistlelock") / "web"
MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}
MAX_BODY_BYTES = 8 * 1024 * 1024

_STATE: dict[str, Path | None] = {"store": None, "tmpdir": None}


def _ensure_store() -> Path:
    if _STATE["store"] is None or not (Path(str(_STATE["store"])) / "HEADER.json").is_file():
        tmp = Path(tempfile.mkdtemp(prefix="whistlelock-ui-"))
        _STATE["tmpdir"] = tmp
        dest = tmp / "store"
        init(dest)
        sample = tmp / "sample-drop.txt"
        sample.write_text("sample drop\n", encoding="utf-8")
        drop(dest, sample, "sample drop")
        _STATE["store"] = dest
    return Path(str(_STATE["store"]))


def _web_bytes(name: str) -> bytes:
    return (WEB / name).read_bytes()


def _receipt(store: Path) -> dict:
    listing = list_store(store)
    report = verify(store, refresh=False, record=False)
    dm = listing["deadman"]
    rows = read_ledger(store)
    released_dirs = []
    released_root = store / "deadman" / "released"
    if released_root.exists():
        released_dirs = sorted(p.name for p in released_root.iterdir() if p.is_dir())
    return {
        "product": "whistlelock",
        "version": ENGINE_VERSION,
        "store": str(store),
        "limitation": LIMITATION,
        "mails": False,
        "deadman_local": True,
        "verify": {
            "ok": report["ok"],
            "rows": report["rows"],
            "errors": report["errors"],
            "missing_files": report["missing_files"],
        },
        "counts": {
            "drops": len(listing["drops"]),
            "rows": listing["rows"],
            "armed": 1 if dm.get("armed") else 0,
            "released": 1 if dm.get("released") else 0,
            "packet": len(listing["packet_items"]),
            "chain_ok": 1 if report["ok"] else 0,
        },
        "deadman": dm,
        "released_dirs": released_dirs,
        "packet_items": listing["packet_items"],
        "drops": listing["drops"],
        "rows": [
            {
                "entry_id": r.get("entry_id"),
                "timestamp": r.get("timestamp"),
                "kind": r.get("kind"),
                "summary": r.get("summary"),
                "drop_id": r.get("drop_id"),
                "payload_sha256": r.get("payload_sha256"),
                "prev_hash": r.get("prev_hash"),
                "row_hash": r.get("row_hash"),
            }
            for r in rows
        ],
    }


class Handler(BaseHTTPRequestHandler):
    server_version = f"WhistleLock/{ENGINE_VERSION}"

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _send(self, status: int, body: bytes, content_type: str, filename: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, obj: object) -> None:
        body = json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _read_body(self) -> bytes | None:
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            self._json(400, {"error": "invalid Content-Length"})
            return None
        if length < 0:
            self._json(400, {"error": "invalid Content-Length"})
            return None
        if length > MAX_BODY_BYTES:
            self._json(413, {"error": "payload too large", "limit": MAX_BODY_BYTES, "limitation": LIMITATION})
            return None
        return self.rfile.read(length) if length else b"{}"

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            self._send(200, _web_bytes("index.html"), MIME[".html"])
            return
        if path == "/style.css":
            self._send(200, _web_bytes("style.css"), MIME[".css"])
            return
        if path == "/app.js":
            self._send(200, _web_bytes("app.js"), MIME[".js"])
            return
        if path == "/api/health":
            store = _ensure_store()
            self._json(
                200,
                {
                    "ok": True,
                    "version": ENGINE_VERSION,
                    "loopback": True,
                    "telemetry": False,
                    "mails": False,
                    "store": str(store),
                    "limitation": LIMITATION,
                },
            )
            return
        if path == "/api/state":
            self._json(200, _receipt(_ensure_store()))
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        allowed = {
            "/api/init",
            "/api/drop",
            "/api/checkin",
            "/api/arm",
            "/api/tick",
            "/api/verify",
            "/api/list",
            "/api/doctor",
            "/api/export",
            "/api/packet",
            "/api/sample",
        }
        if path not in allowed:
            self._json(404, {"error": "not found"})
            return
        raw = self._read_body()
        if raw is None:
            return

        if path == "/api/init":
            tmp = Path(tempfile.mkdtemp(prefix="whistlelock-ui-"))
            dest = tmp / "store"
            init(dest)
            _STATE["tmpdir"] = tmp
            _STATE["store"] = dest
            self._json(200, _receipt(dest))
            return

        if path == "/api/sample":
            tmp = Path(tempfile.mkdtemp(prefix="whistlelock-ui-"))
            dest = tmp / "store"
            init(dest)
            sample = tmp / "sample-drop.txt"
            sample.write_text("sample drop\n", encoding="utf-8")
            drop(dest, sample, "sample drop")
            _STATE["tmpdir"] = tmp
            _STATE["store"] = dest
            self._json(200, _receipt(dest))
            return

        store = _ensure_store()

        if path == "/api/verify":
            rec = verify(store, refresh=False, record=True)
            out = _receipt(store)
            out["last"] = rec
            self._json(200, out)
            return

        if path == "/api/list":
            self._json(200, _receipt(store))
            return

        if path == "/api/checkin":
            rec = checkin(store)
            out = _receipt(store)
            out["last"] = rec
            self._json(200, out)
            return

        if path == "/api/tick":
            rec = tick(store)
            out = _receipt(store)
            out["last"] = rec
            self._json(200, out)
            return

        if path == "/api/export":
            receipt = _receipt(store)
            self._json(
                200,
                {
                    "receipt": receipt,
                    "filename": "whistlelock-receipt.json",
                    "limitation": LIMITATION,
                    "mails": False,
                },
            )
            return

        if path == "/api/doctor":
            buf = io.StringIO()
            with redirect_stdout(buf):
                from whistlelock.doctor import run_doctor

                code = run_doctor(as_json=True)
            text = buf.getvalue()
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                payload = {"ok": code == 0, "raw": text}
            payload["exit"] = code
            self._json(200, payload)
            return

        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "JSON body required"})
            return
        if not isinstance(payload, dict):
            self._json(400, {"error": "JSON object required"})
            return

        if path == "/api/arm":
            hours = int(payload.get("hours") or 1)
            rec = arm(store, hours)
            out = _receipt(store)
            out["last"] = rec
            self._json(200, out)
            return

        if path == "/api/drop":
            name = str(payload.get("name") or "upload.bin")
            data = payload.get("b64") or payload.get("bytes_b64") or ""
            try:
                blob = base64.b64decode(data)
            except Exception as exc:  # noqa: BLE001
                self._json(400, {"error": f"bad base64: {exc}"})
                return
            tmp = Path(str(_STATE["tmpdir"] or tempfile.mkdtemp(prefix="whistlelock-ui-")))
            src = tmp / name
            src.write_bytes(blob)
            rec = drop(
                store,
                src,
                str(payload.get("summary") or "sample drop"),
                str(payload.get("source") or ""),
                str(payload.get("url") or ""),
            )
            out = _receipt(store)
            out["last"] = rec
            self._json(200, out)
            return

        if path == "/api/packet":
            name = str(payload.get("name") or "packet.bin")
            data = payload.get("b64") or payload.get("bytes_b64") or ""
            try:
                blob = base64.b64decode(data)
            except Exception as exc:  # noqa: BLE001
                self._json(400, {"error": f"bad base64: {exc}"})
                return
            tmp = Path(str(_STATE["tmpdir"] or tempfile.mkdtemp(prefix="whistlelock-ui-")))
            src = tmp / name
            src.write_bytes(blob)
            rec = place_packet(store, src)
            out = _receipt(store)
            out["last"] = rec
            self._json(200, out)
            return

        self._json(404, {"error": "not found"})


def make_server(host: str = "127.0.0.1", port: int = 8873) -> ThreadingHTTPServer:
    if host not in LOOPBACK:
        raise ValueError("WhistleLock UI binds loopback only (127.0.0.1)")
    return ThreadingHTTPServer((host, port), Handler)


def serve(host: str = "127.0.0.1", port: int = 8873) -> None:
    httpd = make_server(host, port)
    bound_host, bound_port = httpd.server_address[:2]
    print(
        f"WhistleLock UI http://{bound_host}:{bound_port} "
        "(loopback only; does not mail; dead-man copy is local)"
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
