from __future__ import annotations

import pytest
from pydantic import ValidationError

from geocompiler.workflow import (
    GeometryKind,
    ParameterKind,
    WorkflowGraphError,
    WorkflowInput,
    WorkflowIR,
    WorkflowParameter,
    WorkflowStep,
)


def _workflow(**overrides: object) -> WorkflowIR:
    values: dict[str, object] = {
        "schema_version": "1.0",
        "id": "warehouse-suitability",
        "name": "Warehouse suitability",
        "inputs": [
            WorkflowInput(id="parcels", title="Parcels", kind=GeometryKind.POLYGON),
            WorkflowInput(id="roads", title="Roads", kind=GeometryKind.LINE),
        ],
        "parameters": [
            WorkflowParameter(
                id="buffer_distance",
                title="Highway distance",
                kind=ParameterKind.DISTANCE,
                default=5000,
                unit="m",
            )
        ],
        "steps": [
            WorkflowStep(
                id="buffer_roads",
                operation="buffer",
                inputs={"INPUT": "roads"},
                parameters={"DISTANCE": "$buffer_distance"},
                outputs={"OUTPUT": "road_buffer"},
            ),
            WorkflowStep(
                id="clip_parcels",
                operation="clip",
                inputs={"INPUT": "parcels", "OVERLAY": "road_buffer"},
                parameters={},
                outputs={"OUTPUT": "candidate_parcels"},
            ),
        ],
        "outputs": {"candidates": "candidate_parcels"},
    }
    values.update(overrides)
    return WorkflowIR.model_validate(values)


def test_workflow_round_trips_as_json() -> None:
    workflow = _workflow()

    restored = WorkflowIR.model_validate_json(workflow.model_dump_json())

    assert restored == workflow
    assert restored.step_ids == ("buffer_roads", "clip_parcels")


def test_workflow_rejects_duplicate_identifiers() -> None:
    duplicate = WorkflowStep(
        id="buffer_roads",
        operation="centroid",
        inputs={"INPUT": "parcels"},
        parameters={},
        outputs={"OUTPUT": "parcel_centroids"},
    )

    with pytest.raises(WorkflowGraphError, match="duplicate step id: buffer_roads"):
        _workflow(steps=[*_workflow().steps, duplicate])


def test_workflow_rejects_unknown_input_reference() -> None:
    invalid_step = WorkflowStep(
        id="buffer_roads",
        operation="buffer",
        inputs={"INPUT": "missing_roads"},
        parameters={"DISTANCE": "$buffer_distance"},
        outputs={"OUTPUT": "road_buffer"},
    )

    with pytest.raises(WorkflowGraphError, match="unknown reference: missing_roads"):
        _workflow(steps=[invalid_step])


def test_workflow_rejects_dependency_cycle() -> None:
    first = WorkflowStep(
        id="first",
        operation="field_calculator",
        inputs={"INPUT": "second_output"},
        parameters={},
        outputs={"OUTPUT": "first_output"},
    )
    second = WorkflowStep(
        id="second",
        operation="field_calculator",
        inputs={"INPUT": "first_output"},
        parameters={},
        outputs={"OUTPUT": "second_output"},
    )

    with pytest.raises(WorkflowGraphError, match="dependency cycle"):
        _workflow(steps=[first, second], outputs={"result": "first_output"})


def test_workflow_rejects_undeclared_output_reference() -> None:
    with pytest.raises(WorkflowGraphError, match="unknown reference: absent_output"):
        _workflow(outputs={"candidates": "absent_output"})


def test_workflow_requires_at_least_one_declared_output() -> None:
    with pytest.raises(WorkflowGraphError, match="at least one declared output"):
        _workflow(outputs={})


def test_workflow_rejects_unknown_parameter_reference() -> None:
    step = WorkflowStep(
        id="buffer_roads",
        operation="buffer",
        inputs={"INPUT": "roads"},
        parameters={"DISTANCE": "$unknown_parameter"},
        outputs={"OUTPUT": "road_buffer"},
    )

    with pytest.raises(WorkflowGraphError, match="unknown parameter: unknown_parameter"):
        _workflow(steps=[step], outputs={"result": "road_buffer"})


def test_workflow_rejects_non_json_parameter_values() -> None:
    with pytest.raises(ValidationError):
        WorkflowParameter(
            id="label",
            title="Label",
            kind=ParameterKind.STRING,
            default=object(),
        )

    with pytest.raises(ValidationError):
        WorkflowStep(
            id="buffer_roads",
            operation="buffer",
            inputs={"INPUT": "roads"},
            parameters={"DISTANCE": object()},
            outputs={"OUTPUT": "road_buffer"},
        )
