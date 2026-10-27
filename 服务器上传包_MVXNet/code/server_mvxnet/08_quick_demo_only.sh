#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$SCRIPT_DIR/00_check_server.sh"
bash "$SCRIPT_DIR/01_install_mmdetection3d.sh"
bash "$SCRIPT_DIR/02_prepare_demo_assets.sh"
bash "$SCRIPT_DIR/03_run_mvxnet_demo.sh"
