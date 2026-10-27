#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/server_config.env"

eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

if [[ ! -f "$CKPT_PATH" ]]; then
  echo "ERROR: checkpoint not found: $CKPT_PATH"
  echo "Put a KITTI PointPillars checkpoint there or override CKPT_PATH before running."
  exit 1
fi

cd "$OPENPCDET_DIR/tools"

python test.py \
  --cfg_file "cfgs/kitti_models/pointpillar.yaml" \
  --batch_size "${BATCH_SIZE:-4}" \
  --ckpt "$CKPT_PATH"
