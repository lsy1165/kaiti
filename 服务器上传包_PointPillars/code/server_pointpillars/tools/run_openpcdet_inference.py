"""Run OpenPCDet PointPillars inference and save non-GUI outputs."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import torch


def add_openpcdet_to_path(openpcdet_dir: Path) -> None:
    sys.path.insert(0, str(openpcdet_dir))
    sys.path.insert(0, str(openpcdet_dir / "tools"))


def patch_openpcdet_optional_dataset_imports(openpcdet_dir: Path) -> None:
    """Skip optional dataset imports that are not needed for KITTI demo inference."""
    init_file = openpcdet_dir / "pcdet" / "datasets" / "__init__.py"
    if not init_file.exists():
        return

    text = init_file.read_text(encoding="utf-8")
    original = text
    text = text.replace(
        "from .argo2.argo2_dataset import Argo2Dataset",
        "try:\n    from .argo2.argo2_dataset import Argo2Dataset\n"
        "except ModuleNotFoundError:\n    Argo2Dataset = None",
    )
    text = text.replace(
        "    'Argo2Dataset': Argo2Dataset\n}",
        "    **({'Argo2Dataset': Argo2Dataset} if Argo2Dataset is not None else {})\n}",
    )

    if text != original:
        init_file.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OpenPCDet inference without GUI.")
    parser.add_argument("--openpcdet-dir", type=Path, required=True)
    parser.add_argument("--cfg-file", type=Path, required=True)
    parser.add_argument("--ckpt", type=Path, required=True)
    parser.add_argument("--data-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--score-threshold", type=float, default=0.1)
    return parser.parse_args()


def load_raw_points(path: Path) -> np.ndarray:
    if path.suffix == ".npy":
        points = np.load(path)
    else:
        points = np.fromfile(path, dtype=np.float32).reshape(-1, 4)
    if points.ndim != 2 or points.shape[1] != 4:
        raise ValueError(f"Expected Nx4 point cloud, got {points.shape} from {path}")
    return points


def box_corners_bev(box: np.ndarray) -> np.ndarray:
    x, y, _z, dx, dy, _dz, heading = box[:7]
    local = np.array(
        [
            [dx / 2, dy / 2],
            [dx / 2, -dy / 2],
            [-dx / 2, -dy / 2],
            [-dx / 2, dy / 2],
            [dx / 2, dy / 2],
        ],
        dtype=np.float32,
    )
    c = math.cos(float(heading))
    s = math.sin(float(heading))
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    corners = local @ rot.T
    corners[:, 0] += x
    corners[:, 1] += y
    return corners


def save_bev(points: np.ndarray, predictions: List[Dict[str, Any]], output_path: Path) -> None:
    import matplotlib.pyplot as plt

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 10))
    mask = (
        (points[:, 0] >= 0)
        & (points[:, 0] <= 70.4)
        & (points[:, 1] >= -40)
        & (points[:, 1] <= 40)
        & (points[:, 2] >= -3)
        & (points[:, 2] <= 1)
    )
    selected = points[mask]
    plt.scatter(selected[:, 1], selected[:, 0], s=0.2, c=selected[:, 2], cmap="viridis", linewidths=0)

    colors = {1: "#ff2d55", 2: "#ffd60a", 3: "#32d74b"}
    names = {1: "Car", 2: "Pedestrian", 3: "Cyclist"}
    for pred in predictions:
        box = np.array(pred["box"], dtype=np.float32)
        corners = box_corners_bev(box)
        label = int(pred["label"])
        plt.plot(corners[:, 1], corners[:, 0], color=colors.get(label, "#ff9500"), linewidth=1.8)
        plt.text(corners[0, 1], corners[0, 0], f"{names.get(label, label)} {pred['score']:.2f}", fontsize=7)

    plt.xlabel("left-right y (m)")
    plt.ylabel("forward x (m)")
    plt.title("PointPillars detection BEV")
    plt.xlim(-40, 40)
    plt.ylim(0, 70.4)
    plt.grid(True, linewidth=0.2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=220)
    plt.close()


def main() -> None:
    args = parse_args()
    args.openpcdet_dir = args.openpcdet_dir.resolve()
    args.cfg_file = args.cfg_file.resolve()
    args.ckpt = args.ckpt.resolve()
    args.data_path = args.data_path.resolve()
    args.output_dir = args.output_dir.resolve()

    add_openpcdet_to_path(args.openpcdet_dir)
    patch_openpcdet_optional_dataset_imports(args.openpcdet_dir)
    os.chdir(args.openpcdet_dir / "tools")

    from pcdet.config import cfg, cfg_from_yaml_file
    from pcdet.datasets import DatasetTemplate
    from pcdet.models import build_network, load_data_to_gpu
    from pcdet.utils import common_utils

    class DemoDataset(DatasetTemplate):
        def __init__(self, dataset_cfg, class_names, root_path, logger, ext):
            super().__init__(
                dataset_cfg=dataset_cfg,
                class_names=class_names,
                training=False,
                root_path=root_path,
                logger=logger,
            )
            self.root_path = Path(root_path)
            self.ext = ext
            if self.root_path.is_dir():
                file_ext = self.ext if self.ext else ".bin"
                self.sample_file_list = sorted(self.root_path.glob(f"*{file_ext}"))
            else:
                self.sample_file_list = [self.root_path]

        def __len__(self):
            return len(self.sample_file_list)

        def __getitem__(self, index):
            path = self.sample_file_list[index]
            points = load_raw_points(path)
            input_dict = {"points": points, "frame_id": path.stem}
            return self.prepare_data(data_dict=input_dict)

    if not torch.cuda.is_available():
        raise SystemExit("ERROR: CUDA is not available. Use a GPU server for this demo.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    cfg_from_yaml_file(str(args.cfg_file), cfg)
    logger = common_utils.create_logger(log_file=str(args.output_dir / "inference.log"))
    dataset = DemoDataset(
        dataset_cfg=cfg.DATA_CONFIG,
        class_names=cfg.CLASS_NAMES,
        root_path=args.data_path,
        logger=logger,
        ext=args.data_path.suffix,
    )
    model = build_network(model_cfg=cfg.MODEL, num_class=len(cfg.CLASS_NAMES), dataset=dataset)
    model.load_params_from_file(filename=str(args.ckpt), logger=logger, to_cpu=True)
    model.cuda()
    model.eval()

    all_outputs = []
    with torch.no_grad():
        for idx, data_dict in enumerate(dataset):
            data_dict = dataset.collate_batch([data_dict])
            load_data_to_gpu(data_dict)
            pred_dicts, _ = model.forward(data_dict)
            pred = pred_dicts[0]
            boxes = pred["pred_boxes"].detach().cpu().numpy()
            scores = pred["pred_scores"].detach().cpu().numpy()
            labels = pred["pred_labels"].detach().cpu().numpy()

            kept = scores >= args.score_threshold
            outputs = [
                {
                    "box": boxes[i].round(5).tolist(),
                    "score": float(scores[i]),
                    "label": int(labels[i]),
                }
                for i in range(len(scores))
                if kept[i]
            ]
            sample_path = dataset.sample_file_list[idx]
            points = load_raw_points(sample_path)
            save_bev(points, outputs, args.output_dir / f"{sample_path.stem}_pred_bev.png")
            all_outputs.append({"sample": str(sample_path), "predictions": outputs})

    (args.output_dir / "predictions.json").write_text(
        json.dumps({"results": all_outputs}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved predictions to: {args.output_dir / 'predictions.json'}")
    print(f"Saved BEV visualizations to: {args.output_dir}")


if __name__ == "__main__":
    main()
