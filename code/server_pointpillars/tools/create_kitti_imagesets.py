"""Create KITTI ImageSets files when they are missing.

OpenPCDet expects data/kitti/ImageSets with train/val/trainval/test text files.
This helper creates a deterministic split from available KITTI labels.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List


def write_ids(path: Path, ids: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(ids) + "\n", encoding="utf-8")


def collect_ids(path: Path, suffix: str) -> List[str]:
    if not path.exists():
        return []
    return sorted(item.stem for item in path.iterdir() if item.is_file() and item.suffix == suffix)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create KITTI ImageSets.")
    parser.add_argument("--kitti-root", type=Path, required=True, help="OpenPCDet data/kitti root.")
    parser.add_argument("--val-ratio", type=float, default=0.2, help="Validation ratio.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    image_sets = args.kitti_root / "ImageSets"

    trainval_ids = collect_ids(args.kitti_root / "training" / "label_2", ".txt")
    test_ids = collect_ids(args.kitti_root / "testing" / "velodyne", ".bin")

    if not trainval_ids:
        raise SystemExit(f"ERROR: no training labels found under {args.kitti_root}")

    val_count = max(1, int(len(trainval_ids) * args.val_ratio)) if len(trainval_ids) > 1 else 0
    val_ids = trainval_ids[-val_count:] if val_count else []
    train_ids = trainval_ids[:-val_count] if val_count else trainval_ids

    write_ids(image_sets / "trainval.txt", trainval_ids)
    write_ids(image_sets / "train.txt", train_ids)
    write_ids(image_sets / "val.txt", val_ids)
    if test_ids:
        write_ids(image_sets / "test.txt", test_ids)

    print(f"ImageSets written to: {image_sets}")
    print(f"train: {len(train_ids)}")
    print(f"val: {len(val_ids)}")
    print(f"trainval: {len(trainval_ids)}")
    print(f"test: {len(test_ids)}")


if __name__ == "__main__":
    main()
