"""Check environment readiness for monocular-free 3D detection reproduction."""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List


PACKAGES = [
    "torch",
    "torchvision",
    "numpy",
    "matplotlib",
    "spconv-cu120",
    "spconv-cu118",
    "spconv",
    "open3d",
    "mmdet",
    "mmcv",
    "mmdet3d",
    "pcdet",
]


def package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "未安装"


def run_nvidia_smi() -> List[str]:
    exe = shutil.which("nvidia-smi")
    if exe is None:
        return ["未在 PATH 中找到 nvidia-smi。"]

    try:
        result = subprocess.run(
            [exe],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
    except Exception as exc:  # pragma: no cover - system dependent
        return [f"运行 nvidia-smi 失败：{exc}"]

    if result.returncode != 0:
        return ["nvidia-smi 返回非零状态：", result.stderr.strip()]

    return result.stdout.strip().splitlines()[:20]


def torch_status() -> List[str]:
    try:
        import torch
    except ImportError:
        return ["PyTorch 未安装。"]

    lines = [
        f"torch 版本：{torch.__version__}",
        f"CUDA 是否可用：{torch.cuda.is_available()}",
        f"torch CUDA 版本：{torch.version.cuda}",
        f"CUDA 设备数量：{torch.cuda.device_count()}",
    ]
    if torch.cuda.is_available():
        lines.append(f"CUDA 设备名称：{torch.cuda.get_device_name(0)}")
    else:
        lines.append("当前 PyTorch 不能调用 CUDA，完整 3D 检测训练/推理可能需要重新配置 GPU 环境或使用服务器。")
    return lines


def build_report() -> List[str]:
    lines: List[str] = [
        "# 阶段 2 三维检测环境检查报告",
        "",
        "## 基本环境",
        "",
        f"- Python：{sys.version.split()[0]}",
        f"- Python 路径：`{sys.executable}`",
        f"- 操作系统：{platform.platform()}",
        "",
        "## PyTorch/CUDA 状态",
        "",
    ]
    lines.extend(f"- {line}" for line in torch_status())

    lines.extend(["", "## nvidia-smi 状态", ""])
    lines.extend(f"- {line}" for line in run_nvidia_smi())

    lines.extend(["", "## 关键 Python 包", "", "| 包 | 状态 |", "|---|---|"])
    for package in PACKAGES:
        lines.append(f"| {package} | {package_version(package)} |")

    lines.extend(
        [
            "",
            "## 判断",
            "",
            "当前环境可以继续进行 KITTI 数据检查、点云读取、BEV 可视化和标签框可视化。",
            "若要复现 PointPillars/CenterPoint 等三维检测模型，通常还需要：",
            "",
            "1. 可用的 NVIDIA GPU 与 CUDA 版 PyTorch；",
            "2. spconv 等稀疏卷积依赖；",
            "3. OpenPCDet 或 MMDetection3D 等三维检测框架；",
            "4. 完整 KITTI 数据集。",
            "",
            "按照老师意见，下一阶段应先完成单模态三维检测基础系统复现，再进入图像+雷达多模态三维检测基础系统。",
        ]
    )
    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check 3D detection environment.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("code/outputs/stage02_mono3d_detection/3d_detection_env_check.md"),
        help="Output Markdown report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(build_report()) + "\n", encoding="utf-8")
    print(f"3D detection environment report saved to: {args.output}")


if __name__ == "__main__":
    main()
