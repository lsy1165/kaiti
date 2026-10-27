"""Check the paired image, point cloud, and metadata for stage 03."""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path
from typing import Any, Dict

import numpy as np
import yaml
from PIL import Image


def load_config(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_points(path: Path) -> np.ndarray:
    points = np.fromfile(path, dtype=np.float32)
    if points.size % 4 != 0:
        raise ValueError(f"Invalid KITTI point cloud: {path}")
    return points.reshape(-1, 4)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check multimodal demo assets.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("code/configs/stage03_multimodal3d_mvxnet.yaml"),
    )
    args = parser.parse_args()

    config = load_config(args.config)
    sample = config["demo_sample"]
    image_path = Path(sample["image"])
    point_cloud_path = Path(sample["point_cloud"])
    info_path = Path(sample["info"])
    output_dir = Path(config["output"]["dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    checks = []
    for label, path in [
        ("image", image_path),
        ("point_cloud", point_cloud_path),
        ("info", info_path),
    ]:
        checks.append((label, path, path.exists(), path.stat().st_size if path.exists() else 0))

    points = load_points(point_cloud_path)
    image = Image.open(image_path)
    info = pickle.loads(info_path.read_bytes())["data_list"][0]
    cam2 = info["images"]["CAM2"]
    lidar_points = info["lidar_points"]

    image_match = Path(cam2.get("img_path", "")).name == image_path.name
    lidar_match = Path(lidar_points.get("lidar_path", "")).name == point_cloud_path.name
    size_match = int(cam2["width"]) == image.size[0] and int(cam2["height"]) == image.size[1]

    report = [
        "# 阶段 3 多模态 demo 样例检查",
        "",
        "## 文件检查",
        "",
        "| 项目 | 路径 | 是否存在 | 大小 |",
        "| --- | --- | --- | ---: |",
    ]
    for label, path, exists, size in checks:
        report.append(f"| {label} | `{path}` | {exists} | {size} |")

    report.extend(
        [
            "",
            "## 元数据对应关系",
            "",
            f"- sample_id: `{info.get('sample_id')}`",
            f"- pkl image path: `{cam2.get('img_path')}`",
            f"- pkl lidar path: `{lidar_points.get('lidar_path')}`",
            f"- local image size: `{image.size[0]} x {image.size[1]}`",
            f"- pkl image size: `{int(cam2['width'])} x {int(cam2['height'])}`",
            f"- point count: `{len(points)}`",
            f"- image name matched: `{image_match}`",
            f"- lidar name matched: `{lidar_match}`",
            f"- image size matched: `{size_match}`",
            "",
            "## 结论",
            "",
        ]
    )

    if all(item[2] for item in checks) and image_match and lidar_match and size_match:
        report.append("阶段 3 demo 样例检查通过，可以作为图像+雷达多模态三维检测的基础样例。")
    else:
        report.append("阶段 3 demo 样例检查未通过，需要先修正文件对应关系。")

    output_path = output_dir / "demo_assets_check.md"
    output_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    main()
