"""Summarize stage 01 detection JSON into a small Markdown report."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def summarize(payload: Dict[str, Any]) -> List[str]:
    results = payload.get("results", [])
    lines: List[str] = [
        "# 阶段 1 二维目标检测结果汇总",
        "",
        "## 总体结果",
        "",
        f"- 图片数量：{len(results)}",
    ]

    total_detections = sum(len(item.get("detections", [])) for item in results)
    lines.append(f"- 检测目标总数：{total_detections}")
    lines.append("")

    class_counter: Counter[str] = Counter()
    for item in results:
        for detection in item.get("detections", []):
            class_counter[detection.get("class_name", "unknown")] += 1

    lines.extend(["## 类别统计", "", "| 类别 | 数量 |", "|---|---:|"])
    for class_name, count in class_counter.most_common():
        lines.append(f"| {class_name} | {count} |")

    lines.extend(
        [
            "",
            "## 按图片统计",
            "",
            "| 图片 | 检测数量 | 主要类别 |",
            "|---|---:|---|",
        ]
    )

    for item in results:
        image = item.get("image", "")
        detections = item.get("detections", [])
        per_image_counter = Counter(
            detection.get("class_name", "unknown") for detection in detections
        )
        main_classes = ", ".join(
            f"{class_name}({count})"
            for class_name, count in per_image_counter.most_common()
        )
        lines.append(f"| {image} | {len(detections)} | {main_classes} |")

    lines.extend(
        [
            "",
            "## 说明",
            "",
            "该汇总仅用于第一阶段二维目标检测流程验证，说明当前基础检测流程已经能够完成图像输入、模型推理、结果可视化和结构化结果统计。",
            "后续将替换为自动驾驶公开数据集图像，并继续推进单模态三维目标检测和图像+雷达多模态三维目标检测基础系统复现。",
        ]
    )
    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize stage 01 results.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("code/outputs/stage01_2d_detection/detections.json"),
        help="Path to detections.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("code/outputs/stage01_2d_detection/summary.md"),
        help="Path to the Markdown summary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = load_json(args.input)
    lines = summarize(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Summary saved to: {args.output}")


if __name__ == "__main__":
    main()
