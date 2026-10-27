"""Run a basic YOLO 2D object detection demo.

This script is intentionally small and focused. It is only responsible for
stage 01 in the action plan: load images, run a 2D detector, and save visual
and JSON results.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def load_config(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}
    return config


def collect_images(source: Path) -> List[Path]:
    if source.is_file():
        if source.suffix.lower() not in IMAGE_SUFFIXES:
            raise ValueError(f"Unsupported image file: {source}")
        return [source]

    if source.is_dir():
        images = [
            path
            for path in sorted(source.iterdir())
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        ]
        if not images:
            raise FileNotFoundError(f"No images found in directory: {source}")
        return images

    raise FileNotFoundError(f"Input source does not exist: {source}")


def ensure_dependency(ultralytics_config_dir: Path | None = None) -> Any:
    if ultralytics_config_dir is not None:
        ultralytics_config_dir.mkdir(parents=True, exist_ok=True)
        os.environ["YOLO_CONFIG_DIR"] = str(ultralytics_config_dir.resolve())

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency: ultralytics. Run "
            "`python -m pip install -r code/requirements.txt` first."
        ) from exc
    return YOLO


def result_to_records(result: Any) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    names = result.names

    for box in result.boxes:
        xyxy = box.xyxy[0].tolist()
        class_id = int(box.cls[0].item())
        confidence = float(box.conf[0].item())
        records.append(
            {
                "class_id": class_id,
                "class_name": names.get(class_id, str(class_id)),
                "confidence": round(confidence, 6),
                "bbox_xyxy": [round(float(value), 3) for value in xyxy],
            }
        )

    return records


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def run_detection(config: Dict[str, Any]) -> None:
    input_source = Path(config["input"]["source"])
    output_dir = Path(config["output"]["dir"])
    weights = config["model"]["weights"]
    conf = float(config["model"].get("confidence_threshold", 0.25))
    iou = float(config["model"].get("iou_threshold", 0.45))
    device = config["model"].get("device", "cpu")
    save_images = bool(config.get("save", {}).get("images", True))
    save_json_results = bool(config.get("save", {}).get("json", True))
    ultralytics_config = config.get("runtime", {}).get("ultralytics_config_dir")
    ultralytics_config_dir = Path(ultralytics_config) if ultralytics_config else None

    images = collect_images(input_source)
    YOLO = ensure_dependency(ultralytics_config_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model = YOLO(weights)
    all_records: List[Dict[str, Any]] = []

    for image_path in images:
        results: Iterable[Any] = model.predict(
            source=str(image_path),
            conf=conf,
            iou=iou,
            device=device,
            verbose=False,
        )

        for result in results:
            records = result_to_records(result)
            all_records.append(
                {
                    "image": str(image_path),
                    "detections": records,
                }
            )

            if save_images:
                output_image = output_dir / f"{image_path.stem}_detected.jpg"
                result.save(filename=str(output_image))

    if save_json_results:
        save_json(output_dir / "detections.json", {"results": all_records})

    print(f"Processed {len(images)} image(s).")
    print(f"Results saved to: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run stage 01 YOLO 2D demo.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("code/configs/stage01_2d_detection.yaml"),
        help="Path to the stage 01 config file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    try:
        run_detection(config)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc


if __name__ == "__main__":
    main()
