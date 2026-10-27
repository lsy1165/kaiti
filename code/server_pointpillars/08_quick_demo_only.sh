#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$SCRIPT_DIR/00_check_server.sh"
bash "$SCRIPT_DIR/01_create_conda_env.sh"
bash "$SCRIPT_DIR/02_install_openpcdet.sh"
bash "$SCRIPT_DIR/03_prepare_demo_assets.sh"
bash "$SCRIPT_DIR/05_run_pointpillar_demo.sh"

echo "PointPillars detection-only demo is complete."
