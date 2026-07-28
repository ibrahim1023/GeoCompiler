from __future__ import annotations

import pytest

from geocompiler.workflow import (
    GeometryKind,
    ParameterKind,
    WorkflowError,
    WorkflowInput,
    WorkflowIR,
    WorkflowStep,
)
from geocompiler.workflow.patches import PatchOperation, WorkflowPatch, apply_patch


def _workflow() -> WorkflowIR:
    return WorkflowIR(
        schema_version="1.0",
        id="buffer-roads",
        name="Buffer roads",
        inputs=[WorkflowInput(id="roads", title="Roads", kind=GeometryKind.LINE)],
        parameters=[],
        steps=[
            WorkflowStep(
                id="buffer",
                operation="buffer",
                inputs={"INPUT": "roads"},
                parameters={"DISTANCE": 500},
                outputs={"OUTPUT": "buffered_roads"},
            )
        ],
        outputs={"result": "buffered_roads"},
    )


def _patch(*operations: PatchOperation) -> WorkflowPatch:
    return WorkflowPatch(
        workflow_id="buffer-roads",
        base_version="1.0",
        summary="Update workflow",
        operations=list(operations),
    )


def test_apply_patch_adds_parameter_without_mutating_original() -> None:
    workflow = _workflow()

    result = apply_patch(
        workflow,
        _patch(
            PatchOperation(
                type="add_parameter",
                target_id=None,
                payload={
                    "id": "distance",
                    "title": "Distance",
                    "kind": ParameterKind.DISTANCE,
                    "default": 750,
                    "unit": "m",
                },
            )
        ),
    )

    assert result.workflow.parameters_by_id["distance"].default == 750
    assert workflow.parameters == []
    assert result.changes == ("add_parameter:distance",)


def test_apply_patch_updates_and_removes_steps() -> None:
    workflow = _workflow()

    result = apply_patch(
        workflow,
        _patch(
            PatchOperation(
                type="insert_step",
                target_id="buffer",
                payload={
                    "id": "centroid",
                    "operation": "centroid",
                    "inputs": {"INPUT": "buffered_roads"},
                    "parameters": {},
                    "outputs": {"OUTPUT": "centroid"},
                },
            ),
            PatchOperation(type="remove_step", target_id="centroid", payload={}),
        ),
    )

    assert result.workflow.step_ids == ("buffer",)
    assert result.changes == ("insert_step:centroid", "remove_step:centroid")


def test_apply_patch_is_atomic_when_a_later_operation_is_invalid() -> None:
    workflow = _workflow()
    patch = _patch(
        PatchOperation(
            type="add_parameter",
            target_id=None,
            payload={
                "id": "distance",
                "title": "Distance",
                "kind": ParameterKind.DISTANCE,
                "default": 500,
                "unit": "m",
            },
        ),
        PatchOperation(type="remove_step", target_id="missing", payload={}),
    )

    with pytest.raises(WorkflowError, match="unknown step: missing"):
        apply_patch(workflow, patch)

    assert workflow.parameters == []
    assert workflow.step_ids == ("buffer",)


def test_apply_patch_rejects_wrong_workflow_or_version() -> None:
    with pytest.raises(WorkflowError, match="different workflow"):
        apply_patch(
            _workflow(),
            WorkflowPatch(
                workflow_id="other",
                base_version="1.0",
                summary="Wrong workflow",
                operations=[],
            ),
        )
    with pytest.raises(WorkflowError, match="base version"):
        apply_patch(
            _workflow(),
            WorkflowPatch(
                workflow_id="buffer-roads",
                base_version="2.0",
                summary="Wrong version",
                operations=[],
            ),
        )
