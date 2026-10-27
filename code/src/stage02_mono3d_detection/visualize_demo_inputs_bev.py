"""Create input-only BEV images for the PointPillars demo point clouds."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def load_points(path: Path) -> np.ndarray:
    points = np.fromfile(path, dtype=np.float32)
    if points.size % 4 != 0:
        raise ValueError(f"Invalid KITTI point cloud file: {path}")
    return points.reshape(-1, 4)


def save_input_bev(points: np.ndarray, output_path: Path, title: str) -> None:
    import matplotlib.pyplot as plt

    mask = (
        (points[:, 0] >= 0.0)
        & (points[:, 0] <= 70.4)
        & (points[:, 1] >= -40.0)
        & (points[:, 1] <= 40.0)
        & (points[:, 2] >= -3.0)
        & (points[:, 2] <= 1.0)
    )
    selected = points[mask]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 10))
    scatter = plt.scatter(
        selected[:, 1],
        selected[:, 0],
        c=selected[:, 2],
        s=0.2,
        cmap="viridis",
        linewidths=0,
    )
    plt.colorbar(scatter, label="height z")
    plt.xlabel("left-right y (m)")
    plt.ylabel("forward x (m)")
    plt.title(title)
    plt.xlim(-40, 40)
    plt.ylim(0, 70.4)
    plt.grid(True, linewidth=0.2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=220)
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize demo point-cloud inputs as BEV images.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("code/data/stage02_mono3d_detection/demo_samples"),
        help="Directory containing KITTI-format .bin point clouds.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("code/outputs/stage02_mono3d_detection/demo_input_bev"),
        help="Output directory for input-only BEV images.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    files = sorted(args.input_dir.glob("*.bin"))
    if not files:
        raise SystemExit(f"ERROR: no .bin point clouds found in: {args.input_dir}")

    for point_cloud in files:
        points = load_points(point_cloud)
        output_path = args.output_dir / f"{point_cloud.stem}_input_bev.png"
        save_input_bev(points, output_path, title=f"Input point cloud BEV: {point_cloud.stem}")
        print(f"saved: {output_path}")


if __name__ == "__main__":
    main()
