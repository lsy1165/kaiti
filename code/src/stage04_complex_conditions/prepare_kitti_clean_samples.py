"""Prepare KITTI clean samples as MVX-Net demo triplets."""

from __future__ import annotations

import argparse
import pickle
import shutil
from pathlib import Path
from typing import Dict, List

import numpy as np
from PIL import Image


CLASS_TO_LABEL = {
    "Pedestrian": 0,
    "Cyclist": 1,
    "Car": 2,
    "Van": 2,
}


def parse_calib(path: Path) -> Dict[str, np.ndarray]:
    values: Dict[str, np.ndarray] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, raw = line.split(":", 1)
        arr = np.array([float(x) for x in raw.strip().split()], dtype=np.float32)
        values[key] = arr
    return values


def to_4x4(matrix: np.ndarray, rows: int, cols: int) -> np.ndarray:
    out = np.eye(4, dtype=np.float32)
    out[:rows, :cols] = matrix.reshape(rows, cols)
    return out


def parse_labels(path: Path) -> List[dict]:
    instances: List[dict] = []
    if not path.exists():
        return instances
    group_id = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) < 15:
            continue
        class_name = parts[0]
        if class_name == "DontCare":
            continue
        label = CLASS_TO_LABEL.get(class_name, -1)
        truncated = float(parts[1])
        occluded = int(float(parts[2]))
        alpha = float(parts[3])
        bbox = [float(x) for x in parts[4:8]]
        h, w, l = [float(x) for x in parts[8:11]]
        x, y, z = [float(x) for x in parts[11:14]]
        rotation_y = float(parts[14])
        instances.append(
            {
                "bbox": bbox,
                "bbox_label": label,
                "bbox_3d": [x, y, z, l, w, h, rotation_y],
                "bbox_label_3d": label,
                "depth": z,
                "center_2d": [(bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0],
                "num_lidar_pts": -1,
                "difficulty": -1,
                "truncated": truncated,
                "occluded": occluded,
                "alpha": alpha,
                "score": 0.0,
                "index": group_id,
                "group_id": group_id,
            }
        )
        group_id += 1
    return instances


def create_info(sample_id: str, image_path: Path, point_path: Path, calib_path: Path, label_path: Path) -> dict:
    calib = parse_calib(calib_path)
    p2 = to_4x4(calib["P2"], 3, 4)
    r0 = to_4x4(calib.get("R0_rect", np.eye(3, dtype=np.float32).reshape(-1)), 3, 3)
    tr_velo_to_cam = to_4x4(calib["Tr_velo_to_cam"], 3, 4)
    tr_imu_to_velo = to_4x4(calib.get("Tr_imu_to_velo", np.eye(3, 4, dtype=np.float32).reshape(-1)), 3, 4)
    lidar2cam = r0 @ tr_velo_to_cam
    lidar2img = p2 @ lidar2cam
    image = Image.open(image_path)

    return {
        "metainfo": {"DATASET": "KITTI"},
        "data_list": [
            {
                "sample_id": int(sample_id),
                "sample_idx": int(sample_id),
                "images": {
                    "CAM2": {
                        "img_path": f"{sample_id}.png",
                        "height": image.height,
                        "width": image.width,
                        "cam2img": p2.tolist(),
                        "lidar2cam": lidar2cam.tolist(),
                        "lidar2img": lidar2img.tolist(),
                    }
                },
                "lidar_points": {
                    "num_pts_feats": 4,
                    "lidar_path": f"{sample_id}.bin",
                    "Tr_velo_to_cam": tr_velo_to_cam.tolist(),
                    "Tr_imu_to_velo": tr_imu_to_velo.tolist(),
                },
                "instances": parse_labels(label_path),
            }
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare KITTI clean samples for MVX-Net demo.")
    parser.add_argument(
        "--raw-training-dir",
        type=Path,
        default=Path("code/data/stage04_complex_conditions/downloads/supervisely_kitti_training/training"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("code/data/stage04_complex_conditions/base_samples"),
    )
    args = parser.parse_args()

    image_dir = args.raw_training_dir / "image_2"
    point_dir = args.raw_training_dir / "velodyne"
    calib_dir = args.raw_training_dir / "calib"
    label_dir = args.raw_training_dir / "label_2"
    args.output_dir.mkdir(parents=True, exist_ok=True)

    sample_ids = sorted(path.stem for path in image_dir.glob("*.png"))
    prepared = []
    for sample_id in sample_ids:
        image_path = image_dir / f"{sample_id}.png"
        point_path = point_dir / f"{sample_id}.bin"
        calib_path = calib_dir / f"{sample_id}.txt"
        label_path = label_dir / f"{sample_id}.txt"
        if not (image_path.exists() and point_path.exists() and calib_path.exists()):
            continue

        shutil.copy2(image_path, args.output_dir / f"{sample_id}.png")
        shutil.copy2(point_path, args.output_dir / f"{sample_id}.bin")
        info = create_info(sample_id, image_path, point_path, calib_path, label_path)
        (args.output_dir / f"{sample_id}.pkl").write_bytes(pickle.dumps(info))
        prepared.append(sample_id)

    report = [
        "# KITTI clean samples prepared for stage 04",
        "",
        "| sample | image | point cloud | info |",
        "| --- | --- | --- | --- |",
    ]
    for sample_id in prepared:
        report.append(f"| `{sample_id}` | `{sample_id}.png` | `{sample_id}.bin` | `{sample_id}.pkl` |")
    (args.output_dir / "prepared_clean_samples.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"Prepared {len(prepared)} clean samples: {', '.join(prepared)}")
    print(f"Output: {args.output_dir}")


if __name__ == "__main__":
    main()
