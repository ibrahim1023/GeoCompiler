from __future__ import annotations

import pytest

from geocompiler.ui.view_model import ExecutionState, WorkflowViewModel
from geocompiler.workflow import GeometryKind, WorkflowInput, WorkflowIR, WorkflowStep


def _workflow(name: str = "Buffer roads") -> WorkflowIR:
    return WorkflowIR(
        schema_version="1.0",
        id=name.lower().replace(" ", "-"),
        name=name,
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


def test_proposal_requires_explicit_approval_before_execution() -> None:
    model = WorkflowViewModel()
    model.set_proposal(_workflow())

    assert model.approved is False
    assert model.can_execute is False
    model.approve()
    assert model.approved is True
    assert model.can_execute is True


def test_replacement_clears_approval_and_execution_state() -> None:
    model = WorkflowViewModel()
    model.set_proposal(_workflow())
    model.approve()
    model.begin_execution()
    model.set_proposal(_workflow("Other workflow"))

    assert model.approved is False
    assert model.execution_state is ExecutionState.IDLE
    assert model.error_message is None


def test_execution_error_is_mapped_without_enabling_execution() -> None:
    model = WorkflowViewModel()
    model.set_proposal(_workflow())
    model.approve()
    model.begin_execution()
    model.set_execution_error("step buffer (native:buffer) failed: invalid geometry")

    assert model.execution_state is ExecutionState.FAILED
    assert model.error_message == "step buffer (native:buffer) failed: invalid geometry"
    assert model.can_execute is False


def test_cannot_approve_or_execute_without_proposal() -> None:
    model = WorkflowViewModel()

    with pytest.raises(ValueError, match="no workflow proposal"):
        model.approve()
    with pytest.raises(ValueError, match="approved workflow"):
        model.begin_execution()
