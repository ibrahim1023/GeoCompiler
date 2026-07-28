"""Build a clean QGIS plugin archive without runtime dependency installation."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).parents[1]
PACKAGE = ROOT / "src" / "geocompiler"
ROOT_FILES = ("metadata.txt", "icon.svg", "LICENSE", "README.md")
EXCLUDED_PARTS = {"__pycache__", ".DS_Store", ".pytest_cache", ".ruff_cache"}


def build(output: Path) -> Path:
    """Create a deterministic archive with ``geocompiler`` as its plugin root."""

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(PACKAGE.rglob("*")):
            if source.is_dir() or EXCLUDED_PARTS.intersection(source.parts):
                continue
            archive.write(source, source.relative_to(ROOT / "src").as_posix())
        for name in ROOT_FILES:
            archive.write(ROOT / name, f"geocompiler/{name}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "geocompiler-0.1.0.zip")
    arguments = parser.parse_args()
    print(build(arguments.output))


if __name__ == "__main__":
    main()
