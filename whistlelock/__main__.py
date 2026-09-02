"""Allow ``python -m whistlelock`` and ``python3 whistlelock.py``."""

from whistlelock.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
