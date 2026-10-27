#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/server_config.env"

eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

cd "$OPENPCDET_DIR/tools"

python train.py \
  --cfg_file "cfgs/kitti_models/pointpillar.yaml" \
  --batch_size "${BATCH_SIZE:-4}" \
  --epochs "${EPOCHS:-80}"
