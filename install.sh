#!/usr/bin/env bash
# WhistleLock one-click install. Counted download via this project's Worker.
# Usage: curl -fsSL https://whistlelock-download-tracker.vibelock.workers.dev/install.sh | bash
set -euo pipefail

HOST="${WHISTLELOCK_HOST:-https://whistlelock-download-tracker.vibelock.workers.dev}"
ASSET="${WHISTLELOCK_ASSET:-whistlelock-0.1.0.tar.gz}"
WORKDIR="${WHISTLELOCK_HOME:-$HOME/whistlelock}"

mkdir -p "$WORKDIR"
cd "$WORKDIR"

echo "Downloading counted tarball from ${HOST}/download (User-Agent Mozilla/5.0)…"
curl -fsSL -A 'Mozilla/5.0' "${HOST}/download?asset=${ASSET}" -o "${ASSET}"

tar -xzf "${ASSET}"
DIR="$(find . -maxdepth 1 -type d -name 'whistlelock-*' | head -n 1)"
if [ -n "${DIR}" ]; then
  cd "${DIR}"
fi

python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .

echo
echo "Installed WhistleLock."
echo "Run:  whistlelock ui"
echo "Then open http://127.0.0.1:8873  (loopback only)"
echo "Does not mail. Dead-man copy is local. Author: Aziel Eliab."
