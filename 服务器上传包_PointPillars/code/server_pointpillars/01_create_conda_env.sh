#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/server_config.env"

if ! command -v conda >/dev/null 2>&1; then
  echo "ERROR: conda not found. Please install or load conda on the server first."
  exit 1
fi

eval "$(conda shell.bash hook)"

if conda env list | awk '{print $1}' | grep -qx "$CONDA_ENV_NAME"; then
  echo "Conda env already exists: $CONDA_ENV_NAME"
else
  conda create -n "$CONDA_ENV_NAME" python=3.8 -y
fi

conda activate "$CONDA_ENV_NAME"
python -m pip install --upgrade pip setuptools wheel

# Use env vars to adapt to the server CUDA driver.
python -m pip install $TORCH_PACKAGES --index-url "$TORCH_INDEX_URL"
python -m pip install "numpy<2" pyyaml easydict tqdm tensorboardX scikit-image \
  SharedArray open3d
python -m pip install "$SPCONV_PACKAGE"

python - <<'PY'
import torch
print("torch:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
print("cuda version:", torch.version.cuda)
print("gpu count:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("gpu:", torch.cuda.get_device_name(0))
PY
