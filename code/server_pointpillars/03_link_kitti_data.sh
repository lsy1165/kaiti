#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/server_config.env"

if [[ ! -d "$OPENPCDET_DIR" ]]; then
  echo "ERROR: OpenPCDet not found: $OPENPCDET_DIR"
  exit 1
fi

if [[ ! -d "$KITTI_SRC" ]]; then
  echo "ERROR: KITTI source not found: $KITTI_SRC"
  echo "Please upload/extract KITTI to code/data/stage02_mono3d_detection/kitti first."
  exit 1
fi

mkdir -p "$OPENPCDET_DIR/data"
TARGET="$OPENPCDET_DIR/data/kitti"

if [[ -L "$TARGET" ]]; then
  echo "Existing symlink: $TARGET -> $(readlink "$TARGET")"
elif [[ -e "$TARGET" ]]; then
  echo "ERROR: $TARGET already exists and is not a symlink."
  echo "Move it away manually if you want this script to create a symlink."
  exit 1
else
  ln -s "$KITTI_SRC" "$TARGET"
  echo "Created symlink: $TARGET -> $KITTI_SRC"
fi

python "$SCRIPT_DIR/tools/create_kitti_imagesets.py" --kitti-root "$TARGET"

echo "KITTI linked for OpenPCDet."
find "$TARGET" -maxdepth 2 -type d | sort
