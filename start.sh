#!/usr/bin/env bash
# ============================================================
# Ibosoft ACARS Backend - Start (Linux)
# ------------------------------------------------------------
# Path independent: can be run from any directory, directly or
# from a systemd unit (ExecStart=/path/to/start.sh).
# exec hands the process over to Python so that SIGTERM from
# systemd reaches the application directly.
# ============================================================
set -euo pipefail
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

if [ ! -x "venv/bin/python" ]; then
    echo "[ERROR] Virtual environment not found at ./venv" >&2
    echo "Run ./install-venv.sh first to set up the environment." >&2
    exit 1
fi

export PYTHONUNBUFFERED=1
export PYTHONIOENCODING=utf-8

exec venv/bin/python -u main.py
