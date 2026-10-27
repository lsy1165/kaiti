#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/server_config.env"

eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

mkdir -p "$(dirname "$CKPT_PATH")" "$DEMO_DATA_DIR"

if [[ -f "$CKPT_PATH" ]]; then
  echo "Checkpoint already exists: $CKPT_PATH"
else
  echo "Downloading PointPillars checkpoint to: $CKPT_PATH"
  python -m pip install -q gdown
  python -m gdown "https://drive.google.com/uc?id=${POINTPILLAR_GDRIVE_ID}" -O "$CKPT_PATH"
fi

if [[ -f "$DEMO_SOURCE_FILE" ]]; then
  echo "Demo point cloud already exists: $DEMO_SOURCE_FILE"
else
  echo "Downloading demo point cloud to: $DEMO_SOURCE_FILE"
  python "$SCRIPT_DIR/tools/download_url.py" "$DEMO_SAMPLE_URL" "$DEMO_SOURCE_FILE"
fi

python - <<PY
from pathlib import Path
import numpy as np

path = Path("$DEMO_SOURCE_FILE")
points = np.fromfile(path, dtype=np.float32)
if points.size % 4 != 0:
    raise SystemExit(f"ERROR: {path} is not a KITTI-format float32 Nx4 point cloud")
print("demo point cloud:", path)
print("points:", points.size // 4)
PY

python "$SCRIPT_DIR/tools/create_demo_variants.py" \
  --source "$DEMO_SOURCE_FILE" \
  --output-dir "$DEMO_DATA_DIR"

echo "Demo assets are ready."
