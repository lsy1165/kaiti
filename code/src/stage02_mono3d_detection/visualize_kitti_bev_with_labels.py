"""Visualize KITTI point cloud BEV with 3D boxes projected to BEV."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import yaml


@dataclass
class KittiObject:
    name: str
    h: float
    w: float
    l: float
    x: float
    y: float
    z: float
    ry: float


def load_config(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def pick_sample_id(dataset_root: Path, sample_id: str | None) -> str:
    if sample_id:
        return sample_id
    velodyne_dir = dataset_root / "training" / "velodyne"
    files = sorted(velodyne_dir.glob("*.bin")) if velodyne_dir.exists() else []
    if not files:
        raise FileNotFoundError(f"No KITTI point cloud files found in: {velodyne_dir}")
    return files[0].stem


def load_points(path: Path):
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Missing dependency: numpy.") from exc

    points = np.fromfile(path, dtype=np.float32)
    if points.size % 4 != 0:
        raise ValueError(f"Invalid KITTI point cloud file: {path}")
    return points.reshape(-1, 4)


def parse_labels(path: Path, allowed_classes: List[str]) -> List[KittiObject]:
    if not path.exists():
        raise FileNotFoundError(f"KITTI label file not found: {path}")

    allowed = set(allowed_classes)
    objects: List[KittiObject] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < 15:
            continue
        name = parts[0]
        if allowed and name not in allowed:
            continue
        h, w, l = map(float, parts[8:11])
        x, y, z = map(float, parts[11:14])
        ry = float(parts[14])
        objects.append(KittiObject(name=name, h=h, w=w, l=l, x=x, y=y, z=z, ry=ry))
    return objects


def parse_calib(path: Path):
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Missing dependency: numpy.") from exc

    if not path.exists():
        raise FileNotFoundError(f"KITTI calibration file not found: {path}")

    values: Dict[str, List[float]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        values[key] = [float(item) for item in raw.strip().split()]

    if "R0_rect" not in values or "Tr_velo_to_cam" not in values:
        raise ValueError(f"Missing R0_rect or Tr_velo_to_cam in calibration file: {path}")

    r0 = np.eye(4, dtype=np.float32)
    r0[:3, :3] = np.array(values["R0_rect"], dtype=np.float32).reshape(3, 3)

    tr = np.eye(4, dtype=np.float32)
    tr[:3, :4] = np.array(values["Tr_velo_to_cam"], dtype=np.float32).reshape(3, 4)

    velo_to_rect = r0 @ tr
    rect_to_velo = np.linalg.inv(velo_to_rect)
    return rect_to_velo


def range_tuple(values) -> Tuple[float, float]:
    return float(values[0]), float(values[1])


def lidar_box_corners(obj: KittiObject):
    import numpy as np

    dx = obj.l
    dy = obj.w
    corners = np.array(
        [
            [dx / 2, dy / 2],
            [dx / 2, -dy / 2],
            [-dx / 2, -dy / 2],
            [-dx / 2, dy / 2],
            [dx / 2, dy / 2],
        ],
        dtype=np.float32,
    )
    c = np.cos(obj.ry)
    s = np.sin(obj.ry)
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    rotated = corners @ rot.T
    rotated[:, 0] += obj.x
    rotated[:, 1] += obj.y
    return rotated


def camera_box_corners_in_lidar(obj: KittiObject, rect_to_velo):
    import numpy as np

    x_corners = np.array([obj.l / 2, obj.l / 2, -obj.l / 2, -obj.l / 2], dtype=np.float32)
    y_corners = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)
    z_corners = np.array([obj.w / 2, -obj.w / 2, -obj.w / 2, obj.w / 2], dtype=np.float32)

    c = np.cos(obj.ry)
    s = np.sin(obj.ry)
    rot_y = np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float32)
    corners_rect = rot_y @ np.vstack([x_corners, y_corners, z_corners])
    corners_rect += np.array([[obj.x], [obj.y], [obj.z]], dtype=np.float32)
    corners_rect_h = np.vstack([corners_rect, np.ones((1, 4), dtype=np.float32)])
    corners_velo = rect_to_velo @ corners_rect_h
    xy = corners_velo[:2, :].T
    return np.vstack([xy, xy[0]])


def save_bev_with_labels(
    points,
    objects: List[KittiObject],
    output_path: Path,
    config: Dict,
    title: str,
    rect_to_velo=None,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Missing dependency: matplotlib.") from exc

    x_min, x_max = range_tuple(config["bev"]["x_range"])
    y_min, y_max = range_tuple(config["bev"]["y_range"])
    z_min, z_max = range_tuple(config["bev"]["z_range"])
    coordinate = config.get("labels", {}).get("coordinate", "kitti_camera")

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

    colors = {"Car": "#ff2d55", "Pedestrian": "#ffd60a", "Cyclist": "#32d74b"}
    for obj in objects:
        if coordinate == "lidar":
            corners = lidar_box_corners(obj)
        else:
            if rect_to_velo is None:
                raise ValueError("Calibration is required for KITTI camera-coordinate labels.")
            corners = camera_box_corners_in_lidar(obj, rect_to_velo)
        color = colors.get(obj.name, "#ff9500")
        plt.plot(corners[:, 1], corners[:, 0], color=color, linewidth=1.8, label=obj.name)

    handles, labels = plt.gca().get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    if unique:
        plt.legend(unique.values(), unique.keys(), loc="upper right")

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
    parser = argparse.ArgumentParser(description="Create KITTI BEV visualization with labels.")
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
        sample_id = pick_sample_id(dataset_root, args.sample_id)

        training_root = dataset_root / "training"
        point_cloud = training_root / "velodyne" / f"{sample_id}.bin"
        label_file = training_root / "label_2" / f"{sample_id}.txt"
        calib_file = training_root / "calib" / f"{sample_id}.txt"

        points = load_points(point_cloud)
        objects = parse_labels(label_file, config.get("labels", {}).get("classes", []))
        coordinate = config.get("labels", {}).get("coordinate", "kitti_camera")
        rect_to_velo = None if coordinate == "lidar" else parse_calib(calib_file)

        output_path = output_dir / f"{sample_id}_bev_labels.png"
        save_bev_with_labels(
            points,
            objects,
            output_path,
            config,
            title=f"KITTI BEV with labels {sample_id}",
            rect_to_velo=rect_to_velo,
        )
        print(f"BEV label visualization saved to: {output_path}")
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc


if __name__ == "__main__":
    main()
