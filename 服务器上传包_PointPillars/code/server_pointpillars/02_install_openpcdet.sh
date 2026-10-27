#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/server_config.env"

eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

mkdir -p "$(dirname "$OPENPCDET_DIR")"

if [[ ! -d "$OPENPCDET_DIR/.git" ]]; then
  git clone https://github.com/open-mmlab/OpenPCDet.git "$OPENPCDET_DIR"
else
  echo "OpenPCDet already exists: $OPENPCDET_DIR"
fi

cd "$OPENPCDET_DIR"
python -m pip install --upgrade pip wheel
python -m pip install --force-reinstall "setuptools==68.2.2" "numpy==1.26.4"
python -m pip install pyyaml easydict tqdm tensorboardX scikit-image SharedArray \
  matplotlib pyquaternion "opencv-python<4.10" "numba<0.60" || true
python -m pip install -r requirements.txt --no-deps || true
python -m pip install --force-reinstall "setuptools==68.2.2" "numpy==1.26.4"
python setup.py develop

python - <<'PY'
import pcdet
print("pcdet import ok:", pcdet.__file__)
PY
