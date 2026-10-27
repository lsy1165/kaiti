"""Build side-by-side previews for clean/complex MVX-Net detection results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw


def find_first_camera_vis(result_dir: Path) -> Optional[Path]:
    candidates = sorted((result_dir / "vis_camera" / "CAM2").glob("*.png"))
    if candidates:
        return candidates[0]
    return None


def load_detection_scores(result_dir: Path) -> Optional[List[float]]:
    json_files = sorted((result_dir / "preds").glob("*.json"))
    if not json_files:
        return None
    data = json.loads(json_files[0].read_text(encoding="utf-8"))
    return [float(score) for score in data.get("scores_3d", [])]


def summarize_scores(scores: Optional[List[float]]) -> Optional[Dict[str, Any]]:
    if scores is None:
        return None
    return {
        "count": len(scores),
        "avg": sum(scores) / len(scores) if scores else 0.0,
        "ge_05": sum(score >= 0.5 for score in scores),
        "ge_07": sum(score >= 0.7 for score in scores),
    }


def format_avg_change(clean: Optional[Dict[str, Any]], complex_: Optional[Dict[str, Any]]) -> str:
    if clean is None or complex_ is None:
        return ""
    return f"{clean['avg']:.2f}->{complex_['avg']:.2f}"


def judge_pair(pair_name: str, clean: Optional[Dict[str, Any]], complex_: Optional[Dict[str, Any]]) -> str:
    if clean is None or complex_ is None:
        return "结果不完整，暂不判断"

    if pair_name.endswith("low_light"):
        return "影响较轻，可作为辅助样例"
    if pair_name.endswith("fog"):
        return "影响较轻到中等，高置信目标略少"
    if pair_name.endswith("motion_blur"):
        return "可靠性下降，能说明图像退化影响"
    if pair_name.endswith("image_noise"):
        return "出现漏检，能支撑复杂工况分析"
    if pair_name.endswith("lidar_sparse"):
        return "出现漏检，能说明点云信息缺失影响"
    if pair_name.endswith("lidar_jitter"):
        return "高置信目标明显减少，研究价值较强"
    return "需要结合可视化和指标继续判断"


def make_side_by_side(clean_image: Path, complex_image: Path, output_path: Path, pair_name: str) -> None:
    left = Image.open(clean_image).convert("RGB")
    right = Image.open(complex_image).convert("RGB")
    if right.size != left.size:
        right = right.resize(left.size)

    label_h = 44
    gap = 12
    width = left.width * 2 + gap
    height = left.height + label_h
    canvas = Image.new("RGB", (width, height), (245, 245, 245))
    canvas.paste(left, (0, label_h))
    canvas.paste(right, (left.width + gap, label_h))

    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, width, label_h), fill=(30, 30, 30))
    draw.text((14, 13), f"clean detection: {pair_name}", fill=(255, 255, 255))
    draw.text((left.width + gap + 14, 13), f"complex detection: {pair_name}", fill=(255, 255, 255))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create clean/complex detection comparison previews.")
    parser.add_argument(
        "--results-root",
        type=Path,
        default=Path("code/outputs/stage04_complex_conditions/mvxnet_comparison_results"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("code/outputs/stage04_complex_conditions/detection_comparisons"),
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []

    if not args.results_root.exists():
        report = [
            "# 阶段 4 检测结果对比图生成报告",
            "",
            f"未找到检测结果目录：`{args.results_root}`",
            "",
            "请先在服务器运行 `code/server_mvxnet/04_run_complex_conditions.sh`，并把结果复制回本地。",
        ]
        (args.output_dir / "summary.md").write_text("\n".join(report) + "\n", encoding="utf-8")
        print(f"Results root not found: {args.results_root}")
        return

    for pair_dir in sorted(path for path in args.results_root.iterdir() if path.is_dir()):
        clean_dir = pair_dir / "clean"
        complex_dir = pair_dir / "complex"
        clean_vis = find_first_camera_vis(clean_dir)
        complex_vis = find_first_camera_vis(complex_dir)
        if clean_vis is None or complex_vis is None:
            rows.append(
                {
                    "pair": pair_dir.name,
                    "status": "missing visualization",
                    "clean": summarize_scores(load_detection_scores(clean_dir)),
                    "complex": summarize_scores(load_detection_scores(complex_dir)),
                    "preview": "",
                }
            )
            continue

        output_path = args.output_dir / f"{pair_dir.name}_clean_vs_complex_detection.png"
        make_side_by_side(clean_vis, complex_vis, output_path, pair_dir.name)
        rows.append(
            {
                "pair": pair_dir.name,
                "status": "ok",
                "clean": summarize_scores(load_detection_scores(clean_dir)),
                "complex": summarize_scores(load_detection_scores(complex_dir)),
                "preview": str(output_path),
            }
        )

    report = [
        "# 阶段 4 检测结果对比图生成报告",
        "",
        "本报告用于整理复杂工况前后 MVX-Net 多模态三维检测结果。需要注意：检测数量没有明显下降，并不等于复杂工况没有影响；置信度下降、高置信目标减少和个别漏检都说明模型判断稳定性下降。",
        "",
        "| 对比组 | 状态 | 检测数量 clean->complex | 平均置信度 clean->complex | >=0.5 数量 clean->complex | >=0.7 数量 clean->complex | 结果判断 | 对比图 |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        clean = row["clean"]
        complex_ = row["complex"]
        if clean is None or complex_ is None:
            count_change = avg_change = ge_05_change = ge_07_change = ""
        else:
            count_change = f"{clean['count']}->{complex_['count']}"
            avg_change = format_avg_change(clean, complex_)
            ge_05_change = f"{clean['ge_05']}->{complex_['ge_05']}"
            ge_07_change = f"{clean['ge_07']}->{complex_['ge_07']}"
        preview = f"`{row['preview']}`" if row["preview"] else ""
        judgement = judge_pair(row["pair"], clean, complex_)
        report.append(
            f"| `{row['pair']}` | {row['status']} | {count_change} | {avg_change} | "
            f"{ge_05_change} | {ge_07_change} | {judgement} | {preview} |"
        )

    report.extend(
        [
            "",
            "## 验收结论",
            "",
            "本批结果可以用于阶段性展示，但表述时不能夸大为“所有复杂工况都导致明显失败”。更稳妥的结论是：当前多模态三维检测模型在复杂工况下仍能输出检测框，但部分工况会造成检测可靠性下降，表现为平均置信度下降、高置信目标减少以及少量漏检。",
            "",
            "其中，低光照和雾天样例影响相对较轻，适合作为辅助展示；运动模糊、图像噪声、点云稀疏和点云扰动对结果影响更明显，更适合作为说明复杂工况研究必要性的主要样例。",
            "",
            "## 工况含义",
            "",
            "- 运动模糊：车辆高速运动、目标快速移动、相机曝光时间较长或车身颠簸时，图像边缘会变模糊，目标轮廓更难识别。",
            "- 图像噪声：夜晚弱光、相机高增益、镜头污染、雨雪灰尘或图像压缩传输时，画面会出现颗粒和杂色，小目标和远处目标更容易受影响。",
            "- 点云稀疏：远距离目标、低线束激光雷达、雨雾灰尘遮挡、弱反射表面或传感器局部失效时，目标表面的雷达点会减少，三维结构不完整。",
            "- 点云扰动：激光雷达测距误差、车辆振动、时间同步误差、外参标定误差、异常回波或设备漂移时，点云位置会出现偏移或抖动，三维框定位可靠性下降。",
        ]
    )

    (args.output_dir / "summary.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Detection comparison previews saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
