"""Deterministic replay of metadata-safe provider response fixtures."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from geocompiler.provider.normalization import parse_provider_response


@dataclass(frozen=True)
class FixtureResult:
    """The deterministic outcome for one recorded provider response."""

    name: str
    category: str
    expected: Literal["accept", "reject"]
    passed: bool
    detail: str


def evaluate_fixture(path: Path) -> FixtureResult:
    """Replay one fixture without calling a provider, compiler, or QGIS."""

    fixture = json.loads(path.read_text(encoding="utf-8"))
    expected = fixture["expected"]
    name = fixture["name"]
    category = fixture["category"]
    if expected not in {"accept", "reject"}:
        raise ValueError(f"fixture {path} has an unsupported expected result: {expected}")

    try:
        parse_provider_response(fixture["response"])
    except ValueError as error:
        if expected == "reject":
            return FixtureResult(name, category, expected, True, str(error))
        return FixtureResult(name, category, expected, False, str(error))

    if expected == "accept":
        return FixtureResult(name, category, expected, True, "accepted")
    return FixtureResult(name, category, expected, False, "response was accepted")


def evaluate_fixture_directory(directory: Path) -> tuple[FixtureResult, ...]:
    """Evaluate each JSON fixture in stable filename order."""

    return tuple(evaluate_fixture(path) for path in sorted(directory.glob("*.json")))
