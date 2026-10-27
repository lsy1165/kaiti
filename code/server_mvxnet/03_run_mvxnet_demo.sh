#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/server_config.env"

eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

mkdir -p "$OUTPUT_DIR"

for path in "$DEMO_IMAGE" "$DEMO_PCD" "$DEMO_INFO" "$MVXNET_CONFIG" "$MVXNET_CKPT"; do
  if [[ ! -f "$path" ]]; then
    echo "ERROR: required file not found: $path"
    exit 1
  fi
done

cd "$MMDET3D_DIR"

python demo/multi_modality_demo.py \
  "$DEMO_PCD" \
  "$DEMO_IMAGE" \
  "$DEMO_INFO" \
  "$MVXNET_CONFIG" \
  "$MVXNET_CKPT" \
  --device "$DEVICE" \
  --pred-score-thr "$PRED_SCORE_THR" \
  --out-dir "$OUTPUT_DIR" \
  --cam-type CAM2 \
  2>&1 | tee "$OUTPUT_DIR/inference.log"

echo "MVX-Net demo outputs saved to: $OUTPUT_DIR"
