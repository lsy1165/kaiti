"""Check whether required KITTI archive files are present."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List


EXPECTED_ARCHIVES = [
    "data_object_velodyne.zip",
    "data_object_calib.zip",
    "data_object_label_2.zip",
    "data_object_image_2.zip",
]


def size_text(path: Path) -> str:
    size = path.stat().st_size
    if size >= 1024**3:
        return f"{size / 1024**3:.2f} GB"
    if size >= 1024**2:
        return f"{size / 1024**2:.2f} MB"
    return f"{size / 1024:.2f} KB"


def build_report(download_dir: Path) -> List[str]:
    lines = [
        "# KITTI 压缩包状态检查",
        "",
        f"下载目录：`{download_dir}`",
        "",
        "| 文件 | 状态 | 大小 |",
        "|---|---|---:|",
    ]

    present_count = 0
    for archive_name in EXPECTED_ARCHIVES:
        archive = download_dir / archive_name
        if archive.exists():
            present_count += 1
            lines.append(f"| {archive_name} | 已存在 | {size_text(archive)} |")
        else:
            lines.append(f"| {archive_name} | 缺失 | - |")

    lines.extend(
        [
            "",
            "## 结论",
            "",
        ]
    )

    if present_count == len(EXPECTED_ARCHIVES):
        lines.append("所需 KITTI 压缩包已齐全，可以运行解压整理脚本。")
    else:
        lines.append(f"当前已找到 {present_count}/{len(EXPECTED_ARCHIVES)} 个压缩包，请继续补齐缺失文件。")

    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check KITTI downloaded archives.")
    parser.add_argument(
        "--download-dir",
        type=Path,
        default=Path("code/data/stage02_mono3d_detection/downloads"),
        help="Directory containing KITTI zip archives.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("code/outputs/stage02_mono3d_detection/kitti_archive_check.md"),
        help="Output Markdown report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.download_dir.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(build_report(args.download_dir)) + "\n", encoding="utf-8")
    print(f"KITTI archive check report saved to: {args.output}")


if __name__ == "__main__":
    main()
