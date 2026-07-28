from __future__ import annotations

from pathlib import Path

import pytest

from geocompiler.provider import (
    build_provider_request,
    evaluate_fixture_directory,
    parse_provider_response,
)
from geocompiler.qgis import LayerKind, LayerSummary, ProjectContext
from geocompiler.workflow import WorkflowIR, WorkflowPatch


def _context() -> ProjectContext:
    return ProjectContext(
        layers=(
            LayerSummary(
                id="roads",
                name="Roads",
                kind=LayerKind.VECTOR,
                geometry_kind="vector_line",
                crs_auth_id="EPSG:32640",
                is_projected=True,
            ),
        )
    )


def _workflow_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "id": "buffer-roads",
        "name": "Buffer roads",
        "inputs": [{"id": "roads", "title": "Roads", "kind": "vector_line"}],
        "parameters": [],
        "steps": [
            {
                "id": "buffer",
                "operation": "buffer",
                "inputs": {"INPUT": "roads"},
                "parameters": {"DISTANCE": 500},
                "outputs": {"OUTPUT": "buffered_roads"},
            }
        ],
        "outputs": {"result": "buffered_roads"},
    }


def test_provider_request_contains_only_safe_project_metadata() -> None:
    request = build_provider_request("Buffer roads", _context())

    assert request.intent == "Buffer roads"
    assert request.context["layers"][0]["id"] == "roads"
    serialized = request.model_dump_json()
    assert "source" not in serialized
    assert "coordinates" not in serialized
    assert "connection" not in serialized


def test_parse_provider_response_returns_valid_workflow_or_patch() -> None:
    workflow = parse_provider_response({"artifact": "workflow", "payload": _workflow_payload()})
    patch = parse_provider_response(
        {
            "artifact": "patch",
            "payload": {
                "workflow_id": "buffer-roads",
                "base_version": "1.0",
                "summary": "Change distance",
                "operations": [],
            },
        }
    )

    assert isinstance(workflow, WorkflowIR)
    assert isinstance(patch, WorkflowPatch)


def test_parse_provider_response_rejects_invalid_or_unsafe_artifacts() -> None:
    with pytest.raises(ValueError, match="extra"):
        parse_provider_response(
            {"artifact": "workflow", "payload": _workflow_payload(), "command": "import os"}
        )
    step = _workflow_payload()["steps"][0]
    unsafe = _workflow_payload() | {"steps": [step | {"operation": "exec"}]}
    with pytest.raises(ValueError, match="unsupported operation"):
        parse_provider_response({"artifact": "workflow", "payload": unsafe})
    with pytest.raises(ValueError, match="valid JSON"):
        parse_provider_response("not-json")


def test_provider_fixture_replay_has_expected_outcomes() -> None:
    fixture_directory = Path(__file__).parents[1] / "fixtures" / "provider"

    results = evaluate_fixture_directory(fixture_directory)

    assert len(results) == 4
    assert all(result.passed for result in results)
    assert {result.category for result in results} == {"golden", "adversarial", "failure"}
