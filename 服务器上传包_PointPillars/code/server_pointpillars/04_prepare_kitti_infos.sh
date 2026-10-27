#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/server_config.env"

eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

cd "$OPENPCDET_DIR"

python -m pcdet.datasets.kitti.kitti_dataset create_kitti_infos \
  tools/cfgs/dataset_configs/kitti_dataset.yaml

echo "KITTI infos created under $OPENPCDET_DIR/data/kitti"
find "$OPENPCDET_DIR/data/kitti" -maxdepth 1 -type f | sort
