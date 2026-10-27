"""Check stage 03 multimodal demo assets on the server."""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import numpy as np
from PIL import Image


def load_points(path: Path) -> np.ndarray:
    points = np.fromfile(path, dtype=np.float32)
    if points.size % 4 != 0:
        raise ValueError(f"Invalid KITTI point cloud: {path}")
    return points.reshape(-1, 4)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check multimodal demo assets.")
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--point-cloud", type=Path, required=True)
    parser.add_argument("--info", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    image = Image.open(args.image)
    points = load_points(args.point_cloud)
    info = pickle.loads(args.info.read_bytes())["data_list"][0]
    cam2 = info["images"]["CAM2"]
    lidar = info["lidar_points"]

    image_match = Path(cam2.get("img_path", "")).name == args.image.name
    lidar_match = Path(lidar.get("lidar_path", "")).name == args.point_cloud.name
    size_match = int(cam2["width"]) == image.size[0] and int(cam2["height"]) == image.size[1]

    report = [
        "# MVX-Net demo assets check",
        "",
        f"- image: `{args.image}`",
        f"- point cloud: `{args.point_cloud}`",
        f"- info: `{args.info}`",
        f"- sample_id: `{info.get('sample_id')}`",
        f"- image size: `{image.size[0]} x {image.size[1]}`",
        f"- point count: `{len(points)}`",
        f"- image name matched: `{image_match}`",
        f"- lidar name matched: `{lidar_match}`",
        f"- image size matched: `{size_match}`",
        "",
    ]
    if image_match and lidar_match and size_match:
        report.append("Result: PASS")
    else:
        report.append("Result: FAIL")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Report saved to: {args.output}")


if __name__ == "__main__":
    main()
