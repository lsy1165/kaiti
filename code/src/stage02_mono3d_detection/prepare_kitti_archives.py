"""Extract KITTI object detection archives into the expected stage 02 layout."""

from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path
from typing import Iterable, List


EXPECTED_ARCHIVES = [
    "data_object_velodyne.zip",
    "data_object_image_2.zip",
    "data_object_calib.zip",
    "data_object_label_2.zip",
]


def find_archives(download_dir: Path) -> List[Path]:
    return [download_dir / name for name in EXPECTED_ARCHIVES if (download_dir / name).exists()]


def extract_archives(archives: Iterable[Path], output_root: Path) -> List[str]:
    output_root.mkdir(parents=True, exist_ok=True)
    extracted: List[str] = []
    for archive in archives:
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(output_root)
        extracted.append(archive.name)
    return extracted


def copy_if_needed(source_root: Path, target_root: Path) -> None:
    """Handle archives that contain an extra object/ wrapper directory."""
    wrapper = source_root / "object"
    if not wrapper.exists():
        return

    for child in wrapper.iterdir():
        target = target_root / child.name
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        elif child.is_file():
            shutil.copy2(child, target)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare KITTI archives for stage 02.")
    parser.add_argument(
        "--download-dir",
        type=Path,
        default=Path("code/data/stage02_mono3d_detection/downloads"),
        help="Directory containing KITTI zip archives.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("code/data/stage02_mono3d_detection/kitti"),
        help="Expected KITTI dataset root.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    archives = find_archives(args.download_dir)
    missing = sorted(set(EXPECTED_ARCHIVES) - {archive.name for archive in archives})

    if not archives:
        print(f"No KITTI archives found in: {args.download_dir}")
        print("Expected archive names:")
        for name in EXPECTED_ARCHIVES:
            print(f"- {name}")
        raise SystemExit(1)

    extracted = extract_archives(archives, args.output_root)
    copy_if_needed(args.output_root, args.output_root)

    print("Extracted archives:")
    for name in extracted:
        print(f"- {name}")

    if missing:
        print("Missing archives:")
        for name in missing:
            print(f"- {name}")

    print(f"KITTI data prepared under: {args.output_root}")


if __name__ == "__main__":
    main()
