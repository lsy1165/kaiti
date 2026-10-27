#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/server_config.env"

eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

python - <<'PY'
import torch
print("torch:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
print("cuda:", torch.version.cuda)
print("gpu count:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("gpu:", torch.cuda.get_device_name(0))
PY

python -m pip install -U pip wheel
python -m pip install -U openmim
python -m mim install "mmengine>=0.7.1"
python -m mim install "mmcv>=2.0.0,<2.2.0"
python -m mim install "mmdet>=3.0.0,<3.3.0"
python -m pip install --force-reinstall "setuptools==68.2.2" "numpy==1.26.4"

mkdir -p "$(dirname "$MMDET3D_DIR")"
SOURCE_ZIP="$PROJECT_ROOT/external/mmdetection3d_source.zip"
if [[ -f "$MMDET3D_DIR/setup.py" ]] || [[ -f "$MMDET3D_DIR/pyproject.toml" ]]; then
  echo "MMDetection3D source already exists: $MMDET3D_DIR"
elif [[ -f "$SOURCE_ZIP" ]]; then
  echo "Found local MMDetection3D source zip: $SOURCE_ZIP"
  python - <<PY
from pathlib import Path
from zipfile import ZipFile
import shutil

zip_path = Path("$SOURCE_ZIP")
target = Path("$MMDET3D_DIR")
if target.exists():
    shutil.rmtree(target)
with ZipFile(zip_path) as zf:
    zf.extractall(target.parent)
extracted = target.parent / "mmdetection3d"
if not (extracted / "setup.py").exists():
    raise SystemExit(f"ERROR: extracted source missing setup.py: {extracted}")
print(f"Extracted MMDetection3D source to: {extracted}")
PY
elif [[ ! -d "$MMDET3D_DIR/.git" ]]; then
  git clone -b "$MMDET3D_BRANCH" https://github.com/open-mmlab/mmdetection3d.git "$MMDET3D_DIR"
else
  echo "MMDetection3D already exists: $MMDET3D_DIR"
fi

cd "$MMDET3D_DIR"
python - <<'PY'
import torch
print("torch is available for MMDetection3D build:", torch.__version__)
PY
python -m pip install -v -e . --no-build-isolation

python - <<'PY'
import mmdet3d
print("mmdet3d import ok:", mmdet3d.__version__)
PY
