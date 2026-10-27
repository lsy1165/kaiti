"""Create a tiny synthetic KITTI-like point cloud sample for pipeline checks.

The generated sample is not experimental data. It only verifies that the
stage 02 data checker and BEV visualizer can read KITTI-style files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def make_dirs(root: Path) -> None:
    for dirname in ["velodyne", "image_2", "calib", "label_2"]:
        (root / "training" / dirname).mkdir(parents=True, exist_ok=True)


def generate_points() -> np.ndarray:
    rng = np.random.default_rng(20260923)

    road_x = rng.uniform(0.0, 65.0, 9000)
    road_y = rng.uniform(-22.0, 22.0, 9000)
    road_z = rng.normal(-1.55, 0.04, 9000)
    road_i = rng.uniform(0.05, 0.4, 9000)
    road = np.column_stack([road_x, road_y, road_z, road_i])

    car_centers = [(18.0, -4.0, -0.8), (32.0, 5.5, -0.75), (48.0, -8.0, -0.85)]
    car_parts = []
    for cx, cy, cz in car_centers:
        car_x = rng.normal(cx, 1.7, 1200)
        car_y = rng.normal(cy, 0.8, 1200)
        car_z = rng.uniform(cz - 0.5, cz + 1.0, 1200)
        car_i = rng.uniform(0.45, 1.0, 1200)
        car_parts.append(np.column_stack([car_x, car_y, car_z, car_i]))

    pedestrian_x = rng.normal(25.0, 0.25, 350)
    pedestrian_y = rng.normal(1.8, 0.25, 350)
    pedestrian_z = rng.uniform(-1.4, 0.4, 350)
    pedestrian_i = rng.uniform(0.35, 0.9, 350)
    pedestrian = np.column_stack([pedestrian_x, pedestrian_y, pedestrian_z, pedestrian_i])

    points = np.vstack([road, *car_parts, pedestrian]).astype(np.float32)
    return points


def write_placeholder_png(path: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Missing dependency: matplotlib.") from exc

    image = np.full((180, 480, 3), 235, dtype=np.uint8)
    image[105:125, :, :] = 120
    image[125:, :, :] = 80
    image[:, 0:6, :] = 30
    image[:, -6:, :] = 30
    plt.imsave(path, image)


def write_calib(path: Path) -> None:
    calib_text = "\n".join(
        [
            "P0: 7.215377e+02 0.000000e+00 6.095593e+02 0.000000e+00 0.000000e+00 7.215377e+02 1.728540e+02 0.000000e+00 0.000000e+00 0.000000e+00 1.000000e+00 0.000000e+00",
            "P1: 7.215377e+02 0.000000e+00 6.095593e+02 -3.875744e+02 0.000000e+00 7.215377e+02 1.728540e+02 0.000000e+00 0.000000e+00 0.000000e+00 1.000000e+00 0.000000e+00",
            "P2: 7.215377e+02 0.000000e+00 6.095593e+02 4.485728e+01 0.000000e+00 7.215377e+02 1.728540e+02 2.163791e-01 0.000000e+00 0.000000e+00 1.000000e+00 2.745884e-03",
            "P3: 7.215377e+02 0.000000e+00 6.095593e+02 -3.395242e+02 0.000000e+00 7.215377e+02 1.728540e+02 2.199936e+00 0.000000e+00 0.000000e+00 1.000000e+00 2.729905e-03",
            "R0_rect: 9.999239e-01 9.837760e-03 -7.445048e-03 -9.869795e-03 9.999421e-01 -4.278459e-03 7.402527e-03 4.351614e-03 9.999631e-01",
            "Tr_velo_to_cam: 7.533745e-03 -9.999714e-01 -6.166020e-04 -4.069766e-03 1.480249e-02 7.280733e-04 -9.998902e-01 -7.631618e-02 9.998621e-01 7.523790e-03 1.480755e-02 -2.717806e-01",
            "Tr_imu_to_velo: 9.999976e-01 7.553071e-04 -2.035826e-03 -8.086759e-01 -7.854027e-04 9.998898e-01 -1.482298e-02 3.195559e-01 2.024406e-03 1.482454e-02 9.998881e-01 -7.997231e-01",
        ]
    )
    path.write_text(calib_text + "\n", encoding="utf-8")


def write_label(path: Path) -> None:
    label_text = "\n".join(
        [
            "Car 0.00 0 -1.57 50.00 60.00 120.00 120.00 1.50 1.60 3.90 18.00 -4.00 -0.80 -1.57",
            "Car 0.00 0 -1.57 160.00 55.00 240.00 118.00 1.50 1.60 3.90 32.00 5.50 -0.75 -1.57",
            "Pedestrian 0.00 0 0.00 250.00 65.00 275.00 135.00 1.70 0.60 0.80 25.00 1.80 -1.40 0.00",
        ]
    )
    path.write_text(label_text + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create synthetic KITTI-style sample.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("code/data/stage02_mono3d_detection/kitti_synthetic"),
        help="Synthetic KITTI root directory.",
    )
    parser.add_argument("--sample-id", default="000000", help="Sample id to create.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    make_dirs(args.root)

    sample_id = args.sample_id
    points = generate_points()
    points.tofile(args.root / "training" / "velodyne" / f"{sample_id}.bin")
    write_placeholder_png(args.root / "training" / "image_2" / f"{sample_id}.png")
    write_calib(args.root / "training" / "calib" / f"{sample_id}.txt")
    write_label(args.root / "training" / "label_2" / f"{sample_id}.txt")

    print(f"Synthetic KITTI-style sample created under: {args.root}")
    print("This sample is for pipeline checks only, not for experiments.")


if __name__ == "__main__":
    main()
