#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/server_config.env"

echo "== Basic =="
pwd
python --version || true
conda --version || true
git --version || true

echo
echo "== GPU =="
nvidia-smi || true

echo
echo "== Conda envs =="
conda env list || true

echo
echo "== Demo files =="
ls -lh "$DEMO_DATA_DIR" || true
