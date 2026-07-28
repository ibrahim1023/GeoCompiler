"""Replay recorded provider artifacts without calling an external provider."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from geocompiler.provider import evaluate_fixture_directory  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, required=True)
    arguments = parser.parse_args()
    report = evaluate_fixture_directory(arguments.fixtures)
    print(
        json.dumps(
            {
                "total": len(report.results),
                "passed": report.passed,
                "failed": report.failed,
                "categories": report.category_totals,
            },
            sort_keys=True,
        )
    )
    return 0 if report.succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
