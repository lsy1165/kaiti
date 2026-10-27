"""Download a URL to a local file with a small progress message."""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a URL to a file.")
    parser.add_argument("url")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(args.url) as response, args.output.open("wb") as file:
        total = int(response.headers.get("Content-Length", "0") or 0)
        copied = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            file.write(chunk)
            copied += len(chunk)
            if total:
                print(f"\r{copied / total:.1%}", end="", flush=True)
    if total:
        print()
    print(f"Saved to: {args.output}")


if __name__ == "__main__":
    main()
