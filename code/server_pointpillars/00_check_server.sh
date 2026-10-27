#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/server_config.env"

echo "== Basic =="
echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "OPENPCDET_DIR=$OPENPCDET_DIR"
echo "KITTI_SRC=$KITTI_SRC"
echo

echo "== System =="
uname -a || true
df -h . || true
echo

echo "== GPU =="
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi
else
  echo "nvidia-smi not found. The server may not expose an NVIDIA GPU."
fi
echo

echo "== Conda =="
if command -v conda >/dev/null 2>&1; then
  conda --version
  conda env list
else
  echo "conda not found. Install Anaconda/Miniconda or load the server module first."
fi
echo

echo "== Data =="
if [[ -d "$KITTI_SRC" ]]; then
  find "$KITTI_SRC" -maxdepth 3 -type d | sort
else
  echo "KITTI_SRC does not exist: $KITTI_SRC"
fi
