#!/usr/bin/env bash
# ============================================================
# Ibosoft ACARS Backend - Virtual Environment Setup (Linux)
# ------------------------------------------------------------
# Creates a Python virtual environment in ./venv and installs
# all required packages from requirements.txt into it.
# Run this once after first checkout, and again whenever
# requirements.txt is updated.
# Requires: python3, python3-venv, zlib (libz.so.1, for libacars-2.so)
# ============================================================
set -euo pipefail
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 not found. Install it first: sudo apt install python3 python3-venv" >&2
    exit 1
fi

if [ ! -x "venv/bin/python" ]; then
    echo "Creating virtual environment in ./venv ..."
    if ! python3 -m venv venv; then
        echo "[ERROR] Failed to create virtual environment. Install venv support: sudo apt install python3-venv" >&2
        rm -rf venv
        exit 1
    fi
else
    echo "Virtual environment already exists at ./venv - reusing it."
fi

echo
echo "Upgrading pip inside the venv ..."
venv/bin/python -m pip install --upgrade pip

echo
echo "Installing requirements from requirements.txt ..."
venv/bin/python -m pip install -r requirements.txt

echo
echo "============================================================"
echo "Setup complete. You can now run ./start.sh to launch."
echo "============================================================"
