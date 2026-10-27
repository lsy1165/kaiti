"""Create several point-cloud demo samples from one KITTI-format frame.

These variants are only for deployment demonstration and batch-output checks.
They are not independent KITTI scenes and should not be used as experiment data.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import numpy as np


def load_points(path: Path) -> np.ndarray:
    points = np.fromfile(path, dtype=np.float32)
    if points.size % 4 != 0:
        raise ValueError(f"Invalid KITTI-format point cloud: {path}")
    return points.reshape(-1, 4)


def save_points(path: Path, points: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    points.astype(np.float32).tofile(path)


def filter_range(points: np.ndarray) -> np.ndarray:
    mask = (
        (points[:, 0] >= 0.0)
        & (points[:, 0] <= 70.4)
        & (points[:, 1] >= -40.0)
        & (points[:, 1] <= 40.0)
        & (points[:, 2] >= -3.5)
        & (points[:, 2] <= 2.0)
    )
    return points[mask]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create demo point-cloud variants.")
    parser.add_argument("--source", type=Path, required=True, help="Source KITTI .bin point cloud.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    points = load_points(args.source)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    base_output = args.output_dir / args.source.name
    if args.source.resolve() != base_output.resolve():
        shutil.copy2(args.source, base_output)

    translations = {
        "000008_shift_left.bin": (0.0, 1.5, 0.0),
        "000008_shift_right.bin": (0.0, -1.5, 0.0),
        "000008_forward.bin": (2.0, 0.0, 0.0),
        "000008_backward.bin": (-2.0, 0.0, 0.0),
        "000008_forward_left.bin": (2.0, 1.2, 0.0),
        "000008_forward_right.bin": (2.0, -1.2, 0.0),
        "000008_near_left.bin": (-1.2, 0.8, 0.0),
        "000008_near_right.bin": (-1.2, -0.8, 0.0),
    }

    for name, offset in translations.items():
        variant = points.copy()
        variant[:, :3] += np.array(offset, dtype=np.float32)
        save_points(args.output_dir / name, filter_range(variant))

    note = (
        "These demo point clouds are generated from 000008.bin for deployment "
        "and batch-output checks only. They are not independent KITTI scenes "
        "and should not be used as experiment data.\n"
    )
    (args.output_dir / "DEMO_VARIANTS_NOTE.txt").write_text(note, encoding="utf-8")
    print(f"Demo variants written to: {args.output_dir}")
    print("Files:")
    names = [args.source.name, *sorted(translations)]
    for name in names:
        path = args.output_dir / name
        print(f"- {name}: {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
