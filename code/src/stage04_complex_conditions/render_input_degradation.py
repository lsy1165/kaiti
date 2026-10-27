"""Render existing paired inputs without running a detector or changing data."""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import shutil
from pathlib import Path

import numpy as np
from PIL import Image


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_points(path: Path) -> np.ndarray:
    raw = np.fromfile(path, dtype="<f4")
    if raw.size % 4:
        raise ValueError(f"Invalid XYZI point file: {path}")
    points = raw.reshape(-1, 4)
    if not len(points) or not np.isfinite(points).all():
        raise ValueError(f"Empty or nonfinite point file: {path}")
    return points


def camera_info(path: Path) -> dict:
    # Only load the project's trusted local KITTI metadata, never downloaded pickles.
    with path.open("rb") as stream:
        return pickle.load(stream)["data_list"][0]["images"]["CAM2"]


def render_camera_points(points: np.ndarray, camera: dict, output: Path) -> int:
    width, height = int(camera["width"]), int(camera["height"])
    transform = np.asarray(camera["lidar2img"], dtype=np.float64)
    homogeneous = np.column_stack((points[:, :3], np.ones(len(points))))
    projected = homogeneous @ transform.T
    in_front = projected[:, 2] > 0.1
    coordinates = projected[in_front, :2] / projected[in_front, 2, None]
    xyz = points[in_front, :3]
    visible = (
        (coordinates[:, 0] >= 0) & (coordinates[:, 0] < width)
        & (coordinates[:, 1] >= 0) & (coordinates[:, 1] < height)
    )
    coordinates, xyz = coordinates[visible], xyz[visible]
    distance = np.linalg.norm(xyz, axis=1)
    # A fixed distance scale prevents independent auto-coloring of the two inputs.
    stops = np.array([0.0, 10.0, 25.0, 45.0, 70.4])
    palette = np.array([[255, 211, 80], [77, 222, 171], [47, 187, 247],
                        [91, 117, 237], [178, 108, 216]], dtype=np.float64)
    colors = np.column_stack([
        np.interp(distance, stops, palette[:, channel]) for channel in range(3)
    ]).astype(np.uint8)
    pixels = np.floor(coordinates).astype(np.int32)
    order = np.argsort(-distance, kind="stable")
    pixels, colors = pixels[order], colors[order]
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        xx, yy = pixels[:, 0] + dx, pixels[:, 1] + dy
        valid = (xx < width) & (yy < height)
        # Resolve duplicate screen pixels deterministically, with the nearer point last.
        indices = np.flatnonzero(valid)
        flat = yy[indices] * width + xx[indices]
        _, reverse_positions = np.unique(flat[::-1], return_index=True)
        selected = indices[len(indices) - 1 - reverse_positions]
        canvas[yy[selected], xx[selected]] = colors[selected]
    Image.fromarray(canvas).save(output)
    return int(len(coordinates))


def verify_lidar_pair(clean: np.ndarray, degraded: np.ndarray, condition: str) -> dict:
    if condition == "lidar_sparse":
        rows = np.dtype((np.void, clean.dtype.itemsize * clean.shape[1]))
        original_rows = np.ascontiguousarray(clean).view(rows).ravel()
        degraded_rows = np.ascontiguousarray(degraded).view(rows).ravel()
        if len(degraded) >= len(clean) or not np.isin(degraded_rows, original_rows).all():
            raise ValueError("Sparse data must be an exact subset of original XYZI rows")
        return {"exact_subset": True, "retained_ratio": len(degraded) / len(clean)}
    if len(clean) != len(degraded) or not np.array_equal(clean[:, 3], degraded[:, 3]):
        raise ValueError("Jitter must preserve point count, order and reflectance")
    delta = degraded[:, :3] - clean[:, :3]
    if not np.any(delta):
        raise ValueError("Jitter input has no coordinate changes")
    return {
        "reflectance_unchanged": True,
        "xyz_delta_std_m": np.std(delta, axis=0).tolist(),
        "mean_displacement_m": float(np.linalg.norm(delta, axis=1).mean()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    project = args.project.resolve()
    paired = project / "code/data/stage04_complex_conditions/paired_samples"
    output = project / "code/outputs/stage04_complex_conditions/input_degradation_comparisons"
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((paired / "manifest.json").read_text(encoding="utf-8"))
    records = []
    for sample in manifest["samples"]:
        pair_id = sample["pair_id"]
        info = json.loads((paired / pair_id / "pair_info.json").read_text(encoding="utf-8"))
        condition = info["condition_name"]
        is_lidar = condition in ("lidar_sparse", "lidar_jitter")
        folder = output / pair_id
        folder.mkdir(exist_ok=True)
        sources = {}
        for side in ("clean", "complex"):
            sources[side] = {key: project / info[side][key]
                             for key in ("image", "point_cloud", "info")}
            for path in sources[side].values():
                if not path.is_file():
                    raise FileNotFoundError(path)
        cloud_before = load_points(sources["clean"]["point_cloud"])
        cloud_after = load_points(sources["complex"]["point_cloud"])
        if len(cloud_before) != info["source_point_count"] or len(cloud_after) != info["output_point_count"]:
            raise ValueError(f"Point counts differ from the paired manifest: {pair_id}")
        with Image.open(sources["clean"]["image"]) as original, Image.open(sources["complex"]["image"]) as changed:
            images_equal = np.array_equal(np.asarray(original.convert("RGB")), np.asarray(changed.convert("RGB")))
        clouds_equal = np.array_equal(cloud_before, cloud_after)
        if is_lidar:
            if not images_equal or clouds_equal:
                raise ValueError(f"Expected unchanged RGB and changed point cloud: {pair_id}")
            verification = verify_lidar_pair(cloud_before, cloud_after, condition)
            original_camera = camera_info(sources["clean"]["info"])
            degraded_camera = camera_info(sources["complex"]["info"])
            for key in ("width", "height", "lidar2img"):
                if not np.array_equal(original_camera[key], degraded_camera[key]):
                    raise ValueError(f"Camera projection changed: {pair_id}")
            visible_before = render_camera_points(cloud_before, original_camera, folder / "before.png")
            visible_after = render_camera_points(cloud_after, original_camera, folder / "after.png")
            verification["points_in_camera_view"] = [visible_before, visible_after]
            render_spec = {
                "type": "point_cloud_camera_projection_on_black",
                "image_size_px": [original_camera["width"], original_camera["height"]],
                "lidar2img": original_camera["lidar2img"],
                "point_footprint_px": [2, 2],
                "distance_color_stops_m": [0, 10, 25, 45, 70.4],
                "same_parameters_before_after": True,
                "rgb_background": False,
                "detection_boxes": False,
            }
        else:
            if images_equal or not clouds_equal:
                raise ValueError(f"Expected changed RGB and unchanged point cloud: {pair_id}")
            shutil.copyfile(sources["clean"]["image"], folder / "before.png")
            shutil.copyfile(sources["complex"]["image"], folder / "after.png")
            verification = {"point_cloud_unchanged": True, "image_changed": True}
            render_spec = {"type": "byte_identical_copy_of_input_rgb", "detection_boxes": False}
        record = {
            "pair_id": pair_id,
            "title": info["condition_title"],
            "input_type": "point_cloud" if is_lidar else "image",
            "source_point_count": len(cloud_before), "degraded_point_count": len(cloud_after),
            "verification": verification, "render": render_spec,
            "sources": {
                side: {key: {"path": str(path.relative_to(project)), "sha256": sha256(path)}
                       for key, path in paths.items()} for side, paths in sources.items()
            },
            "pictures": {
                side: {"path": str((folder / f"{side}.png").relative_to(project)),
                       "sha256": sha256(folder / f"{side}.png")} for side in ("before", "after")
            },
        }
        records.append(record)
        print(f"Verified {pair_id}: {len(cloud_before)} -> {len(cloud_after)} points")
    (output / "source_manifest.json").write_text(
        json.dumps({"existing_inputs_only": True, "pairs": records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved 12 input pictures and source hashes to {output}")


if __name__ == "__main__":
    main()
