"""Homepage Download is the primary control. /download is unchanged."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "workers/download-tracker/src/index.js").read_text(encoding="utf-8")
HOME = INDEX[INDEX.index("return `<!doctype html>") : INDEX.index("</html>`;")]


def test_primary_download_stays_on_the_counted_route() -> None:
    assert 'id="downloadBtn"' in HOME
    assert 'class="btn block primary"' in HOME
    assert 'href="/download?asset=${DEFAULT_ASSET}"' in HOME
    assert ">Download<" in HOME
    assert "<footer class=\"quiet\">" in HOME
    assert ":focus-visible" in HOME
    assert "prefers-color-scheme: light" in HOME
    assert "THIS IS NOT" not in HOME


def test_counters_and_mesh_strip_remain() -> None:
    assert "<span>Views</span>" in HOME
    assert "<span>Downloads</span>" in HOME
    assert 'id="install-btn"' in HOME
    assert 'id="meshStrip"' in HOME
    assert 'id="meshLiveCount"' in HOME
    assert "QNS-CD-1.0" in HOME
    assert "no public qnsd proxy" in HOME
