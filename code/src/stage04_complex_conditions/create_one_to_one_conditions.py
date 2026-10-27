"""Create paired clean/complex samples for stage-04 complex-condition tests.

The script enforces the stage-04 rule:
one clean base sample can produce at most one complex-condition sample.
It also writes a paired folder for direct before/after comparison.
"""

from __future__ import annotations

import argparse
import json
import pickle
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


@dataclass(frozen=True)
class BaseSample:
    stem: str
    image: Path
    point_cloud: Path
    info: Path


def load_config(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def find_base_samples(base_dir: Path) -> List[BaseSample]:
    samples: List[BaseSample] = []
    for info_path in sorted(base_dir.glob("*.pkl")):
        stem = info_path.stem
        image_path = base_dir / f"{stem}.png"
        point_cloud_path = base_dir / f"{stem}.bin"
        if image_path.exists() and point_cloud_path.exists():
            samples.append(
                BaseSample(
                    stem=stem,
                    image=image_path,
                    point_cloud=point_cloud_path,
                    info=info_path,
                )
            )
    return samples


def read_points(path: Path) -> np.ndarray:
    points = np.fromfile(path, dtype=np.float32)
    if points.size % 4 != 0:
        raise ValueError(f"Invalid KITTI point cloud file: {path}")
    return points.reshape(-1, 4)


def write_points(path: Path, points: np.ndarray) -> None:
    points.astype(np.float32).tofile(path)


def apply_image_condition(image: Image.Image, spec: Dict[str, Any], rng: np.random.Generator) -> Image.Image:
    condition_type = spec.get("type", "none")
    if condition_type == "none":
        return image.copy()
    if condition_type == "low_light":
        brightness = float(spec.get("brightness", 0.4))
        contrast = float(spec.get("contrast", 0.9))
        out = ImageEnhance.Brightness(image).enhance(brightness)
        return ImageEnhance.Contrast(out).enhance(contrast)
    if condition_type == "fog":
        density = float(spec.get("density", 0.4))
        blur_radius = float(spec.get("blur_radius", 1.0))
        fog = Image.new("RGB", image.size, (235, 235, 235))
        out = Image.blend(image.convert("RGB"), fog, density)
        return out.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    if condition_type == "motion_blur":
        kernel_size = int(spec.get("kernel_size", 15))
        return horizontal_motion_blur(image.convert("RGB"), kernel_size)
    if condition_type == "gaussian_noise":
        sigma = float(spec.get("sigma", 15.0))
        arr = np.asarray(image.convert("RGB"), dtype=np.float32)
        noisy = arr + rng.normal(0.0, sigma, size=arr.shape)
        noisy = np.clip(noisy, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy, mode="RGB")
    raise ValueError(f"Unsupported image condition type: {condition_type}")


def horizontal_motion_blur(image: Image.Image, kernel_size: int) -> Image.Image:
    kernel_size = max(3, kernel_size)
    if kernel_size % 2 == 0:
        kernel_size += 1
    arr = np.asarray(image, dtype=np.float32)
    pad = kernel_size // 2
    padded = np.pad(arr, ((0, 0), (pad, pad), (0, 0)), mode="edge")
    out = np.zeros_like(arr, dtype=np.float32)
    for offset in range(kernel_size):
        out += padded[:, offset : offset + arr.shape[1], :]
    out /= float(kernel_size)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), mode="RGB")


def apply_lidar_condition(points: np.ndarray, spec: Dict[str, Any], rng: np.random.Generator) -> np.ndarray:
    condition_type = spec.get("type", "none")
    if condition_type == "none":
        return points.copy()
    if condition_type == "dropout":
        keep_ratio = float(spec.get("keep_ratio", 0.5))
        keep_ratio = min(max(keep_ratio, 0.05), 1.0)
        mask = rng.random(len(points)) < keep_ratio
        if not mask.any():
            mask[rng.integers(0, len(points))] = True
        return points[mask].copy()
    if condition_type == "jitter":
        xyz_sigma = float(spec.get("xyz_sigma", 0.05))
        out = points.copy()
        out[:, :3] += rng.normal(0.0, xyz_sigma, size=out[:, :3].shape).astype(np.float32)
        return out
    raise ValueError(f"Unsupported lidar condition type: {condition_type}")


def update_info_file(source_info: Path, target_info: Path, image_name: str, point_cloud_name: str) -> None:
    info_obj = pickle.loads(source_info.read_bytes())
    data_list = info_obj.get("data_list", [])
    if not data_list:
        raise ValueError(f"Invalid info pkl without data_list: {source_info}")

    item = data_list[0]
    images = item.get("images", {})
    if "CAM2" in images:
        images["CAM2"]["img_path"] = image_name
    else:
        for image_info in images.values():
            if isinstance(image_info, dict) and "img_path" in image_info:
                image_info["img_path"] = image_name
                break

    lidar_points = item.get("lidar_points", {})
    lidar_points["lidar_path"] = point_cloud_name
    target_info.write_bytes(pickle.dumps(info_obj))


def draw_bev(points: np.ndarray, output_path: Path) -> None:
    width, height = 900, 520
    x_min, x_max = 0.0, 70.4
    y_min, y_max = -40.0, 40.0
    valid = (
        (points[:, 0] >= x_min)
        & (points[:, 0] <= x_max)
        & (points[:, 1] >= y_min)
        & (points[:, 1] <= y_max)
    )
    pts = points[valid]
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    if len(pts):
        px = ((pts[:, 1] - y_min) / (y_max - y_min) * (width - 1)).astype(np.int32)
        py = (height - 1 - (pts[:, 0] - x_min) / (x_max - x_min) * (height - 1)).astype(np.int32)
        intensity = np.clip(pts[:, 3], 0.0, 1.0)
        values = (80 + intensity * 175).astype(np.uint8)
        canvas[py, px, :] = np.stack([values, values, values], axis=1)
    Image.fromarray(canvas, mode="RGB").save(output_path)


def copy_base_sample_once(source_dir: Path, base_dir: Path) -> bool:
    expected = ["000008.png", "000008.bin", "000008.pkl"]
    if not all((source_dir / name).exists() for name in expected):
        return False
    base_dir.mkdir(parents=True, exist_ok=True)
    copied = False
    for name in expected:
        src = source_dir / name
        dst = base_dir / name
        if not dst.exists():
            shutil.copy2(src, dst)
            copied = True
    return copied


def make_image_comparison(clean_image: Path, complex_image: Path, output_path: Path, title: str) -> None:
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
    draw.text((14, 13), "clean before", fill=(255, 255, 255))
    safe_title = title.encode("ascii", errors="ignore").decode("ascii") or "complex"
    draw.text((left.width + gap + 14, 13), f"complex after: {safe_title}", fill=(255, 255, 255))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def copy_to_pair_dir(
    sample: BaseSample,
    condition: Dict[str, Any],
    output_stem: str,
    complex_image: Path,
    complex_points: Path,
    complex_info: Path,
    pair_root: Path,
    preview_dir: Path,
    source_point_count: int,
    output_point_count: int,
) -> Dict[str, Any]:
    pair_dir = pair_root / output_stem
    clean_dir = pair_dir / "clean"
    complex_dir = pair_dir / "complex"
    clean_dir.mkdir(parents=True, exist_ok=True)
    complex_dir.mkdir(parents=True, exist_ok=True)

    clean_image = clean_dir / sample.image.name
    clean_points = clean_dir / sample.point_cloud.name
    clean_info = clean_dir / sample.info.name
    pair_complex_image = complex_dir / complex_image.name
    pair_complex_points = complex_dir / complex_points.name
    pair_complex_info = complex_dir / complex_info.name

    shutil.copy2(sample.image, clean_image)
    shutil.copy2(sample.point_cloud, clean_points)
    shutil.copy2(sample.info, clean_info)
    shutil.copy2(complex_image, pair_complex_image)
    shutil.copy2(complex_points, pair_complex_points)
    shutil.copy2(complex_info, pair_complex_info)

    comparison_image = preview_dir / f"{output_stem}_clean_vs_complex.png"
    make_image_comparison(
        clean_image,
        pair_complex_image,
        comparison_image,
        condition["name"],
    )

    pair_info = {
        "pair_id": output_stem,
        "condition_name": condition["name"],
        "condition_title": condition.get("title", condition["name"]),
        "condition_description": condition.get("description", ""),
        "clean": {
            "sample_id": sample.stem,
            "image": str(clean_image),
            "point_cloud": str(clean_points),
            "info": str(clean_info),
        },
        "complex": {
            "sample_id": output_stem,
            "image": str(pair_complex_image),
            "point_cloud": str(pair_complex_points),
            "info": str(pair_complex_info),
        },
        "comparison_preview": str(comparison_image),
        "source_point_count": source_point_count,
        "output_point_count": output_point_count,
    }
    (pair_dir / "pair_info.json").write_text(
        json.dumps(pair_info, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return pair_info


def write_report(
    report_path: Path,
    manifest: List[Dict[str, Any]],
    base_count: int,
    condition_count: int,
    recommended_min: int,
    bootstrapped: bool,
    demo_all_conditions: bool,
) -> None:
    lines = [
        "# 阶段 4 复杂工况样例生成报告",
        "",
        "## 生成原则",
        "",
        "每个生成样例都同时保存改变前 clean 数据和改变后 complex 数据，便于后续检测结果对比。",
        "",
    ]
    if demo_all_conditions:
        lines.extend(
            [
                "当前为展示版数据准备：基于已经跑通的 MVX-Net 多模态样例生成多种复杂工况对比组。",
                "每个对比组都包含改变前 clean 数据和改变后 complex 数据，可直接接入已跑通的 MVX-Net 检测流程。",
                "该展示版用于说明复杂工况前后检测效果变化，不作为多帧正式评测结论。",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "本阶段采用“多个原始样例，一一对应多种复杂工况”的方式。",
                "每个原始样例最多生成一个复杂工况样例，不采用同一帧扩展多个工况的一对多方式。",
                "",
            ]
        )
    lines.extend(
        [
            "## 样例数量",
            "",
            f"- 原始样例数量：`{base_count}`",
            f"- 可用复杂工况类型数量：`{condition_count}`",
            f"- 建议最少原始样例数量：`{recommended_min}`",
            f"- 是否从阶段 3 自动补入 000008：`{bootstrapped}`",
            f"- 是否基于已跑通样例生成多工况展示版：`{demo_all_conditions}`",
            "",
            "## 已生成样例",
            "",
            "| 对比组 | 原始样例 | 复杂工况 | 改变前数据 | 改变后数据 | 点云点数变化 |",
            "| --- | --- | --- | --- | --- | ---: |",
        ]
    )
    for item in manifest:
        lines.append(
            "| "
            f"`{item['pair_id']}` | "
            f"`{item['base_stem']}` | "
            f"{item['condition_title']} (`{item['condition_name']}`) | "
            f"`{item['clean_dir']}` | "
            f"`{item['complex_dir']}` | "
            f"{item['source_point_count']} -> {item['output_point_count']} |"
        )

    lines.extend(
        [
            "",
            "## 检测结果建议保存结构",
            "",
            "服务器批量检测脚本会按照同样的一组一组方式保存结果：",
            "",
            "```text",
            "code/outputs/stage04_complex_conditions/mvxnet_comparison_results/",
            "  对比组ID/",
            "    clean/",
            "    complex/",
            "```",
            "",
            "`clean/` 是改变前原始样例的检测结果，`complex/` 是改变后复杂工况样例的检测结果。",
        ]
    )

    if base_count < recommended_min and not demo_all_conditions:
        lines.extend(
            [
                "",
                "## 后续补充",
                "",
                f"当前原始样例少于建议数量 `{recommended_min}`。如果要展示更多复杂工况，请继续向 `base_samples/` 放入更多真实多模态样例三件套：",
                "",
                "```text",
                "样例ID.png",
                "样例ID.bin",
                "样例ID.pkl",
                "```",
                "",
                "再次运行生成脚本后，会继续按“一帧对应一种工况”的规则生成复杂工况样例。",
            ]
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create paired clean/complex condition samples.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("code/configs/stage04_complex_conditions.yaml"),
    )
    parser.add_argument(
        "--bootstrap-stage03-sample",
        action="store_true",
        help="Copy the existing stage03 000008 sample into base_samples if base_samples is empty.",
    )
    parser.add_argument(
        "--demo-all-conditions-from-first-sample",
        action="store_true",
        help="Use the first available base sample to create all configured clean/complex condition pairs.",
    )
    parser.add_argument("--seed", type=int, default=20260924)
    args = parser.parse_args()

    config = load_config(args.config)
    base_dir = Path(config["data"]["base_dir"])
    output_dir = Path(config["data"]["output_dir"])
    paired_dir = Path(config["data"].get("paired_dir", "code/data/stage04_complex_conditions/paired_samples"))
    report_dir = Path(config["outputs"]["report_dir"])
    preview_dir = Path(config["outputs"]["preview_dir"])
    recommended_min = int(config["policy"].get("recommended_min_base_samples", 5))
    conditions = list(config.get("conditions", []))

    base_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    paired_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    bootstrapped = False
    if args.bootstrap_stage03_sample and not find_base_samples(base_dir):
        bootstrapped = copy_base_sample_once(
            Path("code/data/stage03_multimodal3d_detection/demo_samples"),
            base_dir,
        )

    base_samples = find_base_samples(base_dir)
    rng = np.random.default_rng(args.seed)
    manifest: List[Dict[str, Any]] = []

    if args.demo_all_conditions_from_first_sample and base_samples:
        generation_plan = [(base_samples[0], condition) for condition in conditions]
    else:
        generation_plan = list(zip(base_samples, conditions))

    for sample, condition in generation_plan:
        condition_name = condition["name"]
        output_stem = f"{sample.stem}_{condition_name}"
        output_image = output_dir / f"{output_stem}.png"
        output_points = output_dir / f"{output_stem}.bin"
        output_info = output_dir / f"{output_stem}.pkl"

        source_image = Image.open(sample.image).convert("RGB")
        source_points = read_points(sample.point_cloud)
        target_image = apply_image_condition(source_image, condition.get("image", {}), rng)
        target_points = apply_lidar_condition(source_points, condition.get("lidar", {}), rng)

        target_image.save(output_image)
        write_points(output_points, target_points)
        update_info_file(sample.info, output_info, output_image.name, output_points.name)
        draw_bev(source_points, preview_dir / f"{sample.stem}_clean_input_bev.png")
        draw_bev(target_points, preview_dir / f"{output_stem}_complex_input_bev.png")

        pair_info = copy_to_pair_dir(
            sample=sample,
            condition=condition,
            output_stem=output_stem,
            complex_image=output_image,
            complex_points=output_points,
            complex_info=output_info,
            pair_root=paired_dir,
            preview_dir=preview_dir,
            source_point_count=int(len(source_points)),
            output_point_count=int(len(target_points)),
        )

        manifest.append(
            {
                "pair_id": output_stem,
                "base_stem": sample.stem,
                "condition_name": condition_name,
                "condition_title": condition.get("title", condition_name),
                "condition_description": condition.get("description", ""),
                "clean_dir": str(paired_dir / output_stem / "clean"),
                "complex_dir": str(paired_dir / output_stem / "complex"),
                "image": str(output_image),
                "point_cloud": str(output_points),
                "info": str(output_info),
                "source_point_count": int(len(source_points)),
                "output_point_count": int(len(target_points)),
                "comparison_preview": pair_info["comparison_preview"],
            }
        )

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "policy": config.get("policy", {}),
                "paired_dir": str(paired_dir),
                "samples": manifest,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (paired_dir / "manifest.json").write_text(
        json.dumps(
            {
                "policy": config.get("policy", {}),
                "samples": manifest,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    write_report(
        report_dir / "complex_condition_samples_report.md",
        manifest,
        len(base_samples),
        len(conditions),
        recommended_min,
        bootstrapped,
        args.demo_all_conditions_from_first_sample,
    )

    print(f"Base samples: {len(base_samples)}")
    print(f"Generated condition samples: {len(manifest)}")
    print(f"Flat manifest: {manifest_path}")
    print(f"Paired samples: {paired_dir}")
    print(f"Report: {report_dir / 'complex_condition_samples_report.md'}")


if __name__ == "__main__":
    main()
