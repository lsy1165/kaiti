"""Check KITTI object detection dataset structure for stage 02."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Set

import yaml


REQUIRED_TRAINING_DIRS = ["velodyne", "image_2", "calib", "label_2"]
OPTIONAL_TESTING_DIRS = ["velodyne", "image_2", "calib"]


def load_config(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def ids_in_dir(path: Path, suffix: str) -> Set[str]:
    if not path.exists():
        return set()
    return {item.stem for item in path.iterdir() if item.is_file() and item.suffix == suffix}


def count_files(path: Path, suffix: str) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.iterdir() if item.is_file() and item.suffix == suffix)


def read_first_point_cloud(velodyne_dir: Path) -> str:
    files = sorted(velodyne_dir.glob("*.bin")) if velodyne_dir.exists() else []
    if not files:
        return "未找到点云文件，暂不能读取点云样例。"

    try:
        import numpy as np
    except ImportError:
        return "未安装 numpy，暂不能读取点云样例。"

    sample = files[0]
    points = np.fromfile(sample, dtype=np.float32)
    if points.size % 4 != 0:
        return f"点云样例 {sample.name} 的数据长度不能被 4 整除，可能不是 KITTI velodyne 格式。"

    points = points.reshape(-1, 4)
    return f"点云样例 {sample.name} 可读取，点数：{len(points)}。"


def build_report(dataset_root: Path) -> List[str]:
    training_root = dataset_root / "training"
    testing_root = dataset_root / "testing"

    lines: List[str] = [
        "# 阶段 2 KITTI 数据检查报告",
        "",
        "## 数据根目录",
        "",
        f"`{dataset_root}`",
        "",
        "## training 目录检查",
        "",
        "| 子目录 | 是否存在 | 文件数量 |",
        "|---|---|---:|",
    ]

    suffix_map = {
        "velodyne": ".bin",
        "image_2": ".png",
        "calib": ".txt",
        "label_2": ".txt",
    }

    for dirname in REQUIRED_TRAINING_DIRS:
        path = training_root / dirname
        suffix = suffix_map[dirname]
        exists = "是" if path.exists() else "否"
        lines.append(f"| {dirname} | {exists} | {count_files(path, suffix)} |")

    lines.extend(["", "## 样本 ID 对齐检查", ""])
    velodyne_ids = ids_in_dir(training_root / "velodyne", ".bin")
    image_ids = ids_in_dir(training_root / "image_2", ".png")
    calib_ids = ids_in_dir(training_root / "calib", ".txt")
    label_ids = ids_in_dir(training_root / "label_2", ".txt")

    common_ids = velodyne_ids & image_ids & calib_ids & label_ids
    lines.extend(
        [
            f"- 点云样本数：{len(velodyne_ids)}",
            f"- 图像样本数：{len(image_ids)}",
            f"- 标定样本数：{len(calib_ids)}",
            f"- 标签样本数：{len(label_ids)}",
            f"- 四类文件均存在的训练样本数：{len(common_ids)}",
            "",
            read_first_point_cloud(training_root / "velodyne"),
            "",
            "## testing 目录检查",
            "",
            "| 子目录 | 是否存在 | 文件数量 |",
            "|---|---|---:|",
        ]
    )

    for dirname in OPTIONAL_TESTING_DIRS:
        path = testing_root / dirname
        suffix = suffix_map[dirname]
        exists = "是" if path.exists() else "否"
        lines.append(f"| {dirname} | {exists} | {count_files(path, suffix)} |")

    lines.extend(
        [
            "",
            "## 结论",
            "",
        ]
    )

    if common_ids:
        lines.append("KITTI training 数据结构基本可用，可以继续进行点云 BEV 可视化和三维检测模型复现。")
    else:
        lines.append("当前尚未检测到完整 KITTI training 样本。请先按说明整理 KITTI 数据，再继续三维检测模型复现。")

    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check KITTI dataset for stage 02.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("code/configs/stage02_mono3d_kitti.yaml"),
        help="Path to stage 02 config.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    dataset_root = Path(config["dataset"]["root"])
    output_dir = Path(config["output"]["dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    report = "\n".join(build_report(dataset_root)) + "\n"
    output_path = output_dir / "kitti_dataset_check.md"
    output_path.write_text(report, encoding="utf-8")
    print(f"Dataset check report saved to: {output_path}")


if __name__ == "__main__":
    main()
