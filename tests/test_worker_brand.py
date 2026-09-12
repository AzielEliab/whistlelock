"""Worker homepage rose-star brand mark.

Public mark is /sigil.png with empty alt and no words on the mark.
Do not put “everblooming sigil” on the public mark. Verify contracts
that require Everblooming header/skill strings stay unchanged elsewhere.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "workers/download-tracker/src/index.js").read_text(encoding="utf-8")
RUNTIME = (ROOT / "workers/download-tracker/src/runtime.js").read_text(encoding="utf-8")
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
SIGIL = ROOT / "workers/download-tracker/public/sigil.png"

BRAND_MARKUP = (
    '<div class="brandrow"><img class="brandmark" src="/sigil.png" '
    'width="40" height="40" alt="" decoding="async"></div>'
)


def test_homepage_brandrow_empty_alt() -> None:
    assert BRAND_MARKUP in INDEX
    assert 'class="brandrow"' in INDEX
    assert 'class="brandmark"' in INDEX
    assert 'src="/sigil.png"' in INDEX
    assert 'alt=""' in INDEX
    assert "alt=\"Everblooming" not in INDEX
    assert "alt='Everblooming" not in INDEX


def test_public_mark_has_no_everblooming_sigil_wording() -> None:
    home = INDEX[INDEX.index("return `<!doctype html>") : INDEX.index("</html>`;")]
    assert "everblooming sigil" not in home.lower()
    assert "everblooming" not in home.lower()
    assert 'class="stamp"' not in home


def test_official_rose_star_is_hosted() -> None:
    assert SIGIL.is_file()
    raw = SIGIL.read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    assert 70_000 <= len(raw) <= 80_000


def test_verify_skill_strings_untouched() -> None:
    assert "Author: **Aziel Eliab**" in SKILL
    assert "name: WhistleLock" in SKILL
    assert "Hosted /v1 never stores drops" in RUNTIME
    assert "GET /v1/skill" in RUNTIME
