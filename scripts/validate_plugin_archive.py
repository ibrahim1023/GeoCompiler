"""Validate GeoCompiler's QGIS repository archive contract."""

from __future__ import annotations

import argparse
import configparser
import zipfile
from pathlib import Path

REQUIRED = {
    "geocompiler/__init__.py",
    "geocompiler/plugin.py",
    "geocompiler/metadata.txt",
    "geocompiler/LICENSE",
    "geocompiler/icon.svg",
}
FORBIDDEN = {"__pycache__", ".pyc", ".DS_Store", ".pytest_cache", ".ruff_cache", ".git"}


def validate(archive_path: Path) -> None:
    """Raise ``ValueError`` when an archive cannot be safely submitted."""

    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        missing = REQUIRED.difference(names)
        if missing:
            raise ValueError(f"archive is missing: {', '.join(sorted(missing))}")
        for name in names:
            if any(part in FORBIDDEN or part.endswith(".pyc") for part in Path(name).parts):
                raise ValueError(f"archive contains forbidden development artifact: {name}")
        metadata = configparser.ConfigParser()
        metadata.read_string(archive.read("geocompiler/metadata.txt").decode("utf-8"))
        general = metadata["general"]
        keys = (
            "name",
            "version",
            "qgisMinimumVersion",
            "author",
            "email",
            "homepage",
            "repository",
            "tracker",
            "icon",
        )
        for key in keys:
            if not general.get(key):
                raise ValueError(f"metadata is missing {key}")
        for key in ("homepage", "repository", "tracker"):
            if not general[key].startswith("https://"):
                raise ValueError(f"metadata {key} must be a public HTTPS URL")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    arguments = parser.parse_args()
    validate(arguments.archive)
    print(f"valid: {arguments.archive}")


if __name__ == "__main__":
    main()
