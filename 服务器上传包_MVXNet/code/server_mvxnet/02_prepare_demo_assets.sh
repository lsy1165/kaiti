#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/server_config.env"

eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

mkdir -p "$CKPT_DIR" "$DEMO_DATA_DIR" "$OUTPUT_DIR"

for path in "$DEMO_IMAGE" "$DEMO_PCD" "$DEMO_INFO"; do
  if [[ ! -f "$path" ]]; then
    echo "ERROR: required demo file not found: $path"
    exit 1
  fi
done

if [[ ! -f "$MVXNET_CONFIG" ]]; then
  echo "ERROR: MVX-Net config not found: $MVXNET_CONFIG"
  echo "Run 01_install_mmdetection3d.sh first."
  exit 1
fi

if [[ -f "$MVXNET_CKPT" ]]; then
  echo "Checkpoint already exists: $MVXNET_CKPT"
else
  echo "Downloading MVX-Net checkpoint to: $MVXNET_CKPT"
  python "$SCRIPT_DIR/tools/download_url.py" "$MVXNET_CKPT_URL" "$MVXNET_CKPT"
fi

python "$SCRIPT_DIR/tools/check_demo_assets.py" \
  --image "$DEMO_IMAGE" \
  --point-cloud "$DEMO_PCD" \
  --info "$DEMO_INFO" \
  --output "$OUTPUT_DIR/demo_assets_check.md"

echo "Demo assets are ready."
