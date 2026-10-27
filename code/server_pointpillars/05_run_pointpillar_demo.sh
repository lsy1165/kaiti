#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/server_config.env"

eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

if [[ ! -f "$CKPT_PATH" ]]; then
  echo "ERROR: checkpoint not found: $CKPT_PATH"
  echo "Run 03_prepare_demo_assets.sh first, put a KITTI PointPillars checkpoint there, or override CKPT_PATH."
  exit 1
fi

if [[ ! -e "$DEMO_DATA_PATH" ]]; then
  echo "ERROR: demo point cloud not found: $DEMO_DATA_PATH"
  echo "Run 03_prepare_demo_assets.sh first, or override DEMO_DATA_PATH."
  exit 1
fi

if [[ -d "$DEMO_DATA_PATH" ]] && ! compgen -G "$DEMO_DATA_PATH/*.bin" >/dev/null; then
  echo "ERROR: no .bin point cloud found in demo directory: $DEMO_DATA_PATH"
  echo "Run 03_prepare_demo_assets.sh first, or put KITTI-format .bin files there."
  exit 1
fi

mkdir -p "$DEMO_OUTPUT_DIR"

python "$SCRIPT_DIR/tools/run_openpcdet_inference.py" \
  --openpcdet-dir "$OPENPCDET_DIR" \
  --cfg-file "$OPENPCDET_DIR/tools/cfgs/kitti_models/pointpillar.yaml" \
  --ckpt "$CKPT_PATH" \
  --data-path "$DEMO_DATA_PATH" \
  --output-dir "$DEMO_OUTPUT_DIR"

echo "Demo outputs saved to: $DEMO_OUTPUT_DIR"
