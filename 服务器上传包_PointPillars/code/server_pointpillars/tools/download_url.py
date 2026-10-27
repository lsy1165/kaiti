"""Download a URL to a local file with basic validation."""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download a URL to a local file.")
    parser.add_argument("url")
    parser.add_argument("output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(args.url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    if len(data) < 1024:
        raise SystemExit(f"ERROR: downloaded file is unexpectedly small: {len(data)} bytes")
    args.output.write_bytes(data)
    print(f"Downloaded {len(data)} bytes to {args.output}")


if __name__ == "__main__":
    main()
