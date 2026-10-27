"""Visualize a KITTI velodyne point cloud as a BEV scatter image."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Tuple

import yaml


def load_config(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def pick_point_cloud(dataset_root: Path, sample_id: str | None) -> Path:
    velodyne_dir = dataset_root / "training" / "velodyne"
    if sample_id:
        path = velodyne_dir / f"{sample_id}.bin"
        if not path.exists():
            raise FileNotFoundError(f"Point cloud not found: {path}")
        return path

    files = sorted(velodyne_dir.glob("*.bin")) if velodyne_dir.exists() else []
    if not files:
        raise FileNotFoundError(f"No KITTI point cloud files found in: {velodyne_dir}")
    return files[0]


def load_points(path: Path):
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Missing dependency: numpy.") from exc

    points = np.fromfile(path, dtype=np.float32)
    if points.size % 4 != 0:
        raise ValueError(f"Invalid KITTI point cloud file: {path}")
    return points.reshape(-1, 4)


def range_tuple(values) -> Tuple[float, float]:
    return float(values[0]), float(values[1])


def save_bev(points, output_path: Path, config: Dict, title: str) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Missing dependency: matplotlib.") from exc

    x_min, x_max = range_tuple(config["bev"]["x_range"])
    y_min, y_max = range_tuple(config["bev"]["y_range"])
    z_min, z_max = range_tuple(config["bev"]["z_range"])

    mask = (
        (points[:, 0] >= x_min)
        & (points[:, 0] <= x_max)
        & (points[:, 1] >= y_min)
        & (points[:, 1] <= y_max)
        & (points[:, 2] >= z_min)
        & (points[:, 2] <= z_max)
    )
    selected = points[mask]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 10))
    scatter = plt.scatter(
        selected[:, 1],
        selected[:, 0],
        c=selected[:, 2],
        s=float(config["bev"].get("point_size", 0.2)),
        cmap="viridis",
        linewidths=0,
    )
    plt.colorbar(scatter, label="height z")
    plt.xlabel("left-right y (m)")
    plt.ylabel("forward x (m)")
    plt.title(title)
    plt.xlim(y_min, y_max)
    plt.ylim(x_min, x_max)
    plt.grid(True, linewidth=0.2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=int(config["bev"].get("dpi", 220)))
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create KITTI BEV visualization.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("code/configs/stage02_mono3d_kitti.yaml"),
        help="Path to stage 02 config.",
    )
    parser.add_argument(
        "--sample-id",
        default=None,
        help="KITTI sample id such as 000000. If omitted, the first point cloud is used.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        config = load_config(args.config)
        dataset_root = Path(config["dataset"]["root"])
        output_dir = Path(config["output"]["dir"])

        point_cloud = pick_point_cloud(dataset_root, args.sample_id)
        points = load_points(point_cloud)
        output_path = output_dir / f"{point_cloud.stem}_bev.png"
        save_bev(points, output_path, config, title=f"KITTI BEV {point_cloud.stem}")
        print(f"BEV visualization saved to: {output_path}")
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc


if __name__ == "__main__":
    main()
