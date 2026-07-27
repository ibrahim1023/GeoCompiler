from __future__ import annotations

import pytest

from geocompiler.workflow import (
    CompatibilityError,
    GeometryKind,
    ParameterKind,
    SpatialContext,
    UnsupportedOperationError,
    WorkflowInput,
    WorkflowIR,
    WorkflowParameter,
    WorkflowStep,
    default_algorithm_registry,
)


def _buffer_workflow(
    *,
    input_kind: GeometryKind = GeometryKind.LINE,
    parameter: WorkflowParameter | None = None,
    step_parameters: dict[str, object] | None = None,
) -> WorkflowIR:
    parameters = step_parameters if step_parameters is not None else {"DISTANCE": "$distance"}
    return WorkflowIR(
        schema_version="1.0",
        id="buffer-workflow",
        name="Buffer workflow",
        inputs=[WorkflowInput(id="roads", title="Roads", kind=input_kind)],
        parameters=[
            parameter
            or WorkflowParameter(
                id="distance",
                title="Distance",
                kind=ParameterKind.DISTANCE,
                default=5000,
                unit="m",
            )
        ],
        steps=[
            WorkflowStep(
                id="buffer",
                operation="buffer",
                inputs={"INPUT": "roads"},
                parameters=parameters,
                outputs={"OUTPUT": "buffered_roads"},
            )
        ],
        outputs={"result": "buffered_roads"},
    )


def test_default_registry_resolves_supported_operation() -> None:
    registry = default_algorithm_registry()
    definition = registry.resolve("buffer")

    assert definition.qgis_algorithm_id == "native:buffer"
    assert "DISTANCE" in definition.parameters
    assert 15 <= len(registry.operations) <= 25
    assert {"buffer", "clip", "difference", "field_calculator", "reproject"} <= registry.operations


def test_registry_rejects_unknown_operation() -> None:
    with pytest.raises(UnsupportedOperationError, match="unsupported operation: imaginary_tool"):
        default_algorithm_registry().resolve("imaginary_tool")


def test_registry_rejects_incompatible_geometry() -> None:
    workflow = _buffer_workflow(input_kind=GeometryKind.RASTER)

    with pytest.raises(CompatibilityError, match="expects one of"):
        default_algorithm_registry().validate(workflow, SpatialContext())


def test_registry_rejects_missing_required_parameter() -> None:
    workflow = _buffer_workflow(step_parameters={})

    with pytest.raises(CompatibilityError, match="missing required parameter: DISTANCE"):
        default_algorithm_registry().validate(workflow, SpatialContext())


def test_registry_rejects_unknown_model_parameter() -> None:
    workflow = _buffer_workflow(
        step_parameters={"DISTANCE": "$distance", "COMMAND": "arbitrary code"}
    )

    with pytest.raises(CompatibilityError, match="unsupported parameter: COMMAND"):
        default_algorithm_registry().validate(workflow, SpatialContext())


def test_registry_rejects_unknown_model_input_port() -> None:
    workflow = _buffer_workflow()
    step = workflow.steps[0].model_copy(update={"inputs": {"INPUT": "roads", "SHELL": "roads"}})
    workflow = workflow.model_copy(update={"steps": [step]})

    with pytest.raises(CompatibilityError, match="unsupported input port: SHELL"):
        default_algorithm_registry().validate(workflow, SpatialContext())


def test_registry_rejects_unknown_model_output_port() -> None:
    workflow = _buffer_workflow()
    step = workflow.steps[0].model_copy(
        update={"outputs": {"OUTPUT": "buffered_roads", "COMMAND": "unsafe_output"}}
    )
    workflow = workflow.model_copy(update={"steps": [step]})

    with pytest.raises(CompatibilityError, match="unsupported output port: COMMAND"):
        default_algorithm_registry().validate(workflow, SpatialContext())


def test_registry_rejects_parameter_with_wrong_kind() -> None:
    workflow = _buffer_workflow(
        parameter=WorkflowParameter(
            id="distance",
            title="Distance",
            kind=ParameterKind.STRING,
            default="five kilometres",
        )
    )

    with pytest.raises(CompatibilityError, match="requires distance"):
        default_algorithm_registry().validate(workflow, SpatialContext())


def test_registry_requires_projected_crs_for_metric_operation() -> None:
    workflow = _buffer_workflow()
    context = SpatialContext(projected_references={"roads": False})

    with pytest.raises(CompatibilityError, match="requires a projected CRS"):
        default_algorithm_registry().validate(workflow, context)


def test_registry_validates_workflow_in_dependency_order() -> None:
    workflow = WorkflowIR(
        schema_version="1.0",
        id="out-of-order",
        name="Out of order",
        inputs=[
            WorkflowInput(id="parcels", title="Parcels", kind=GeometryKind.POLYGON),
            WorkflowInput(id="roads", title="Roads", kind=GeometryKind.LINE),
        ],
        parameters=[
            WorkflowParameter(
                id="distance",
                title="Distance",
                kind=ParameterKind.DISTANCE,
                default=5000,
                unit="m",
            )
        ],
        steps=[
            WorkflowStep(
                id="clip_parcels",
                operation="clip",
                inputs={"INPUT": "parcels", "OVERLAY": "road_buffer"},
                parameters={},
                outputs={"OUTPUT": "candidates"},
            ),
            WorkflowStep(
                id="buffer_roads",
                operation="buffer",
                inputs={"INPUT": "roads"},
                parameters={"DISTANCE": "$distance"},
                outputs={"OUTPUT": "road_buffer"},
            ),
        ],
        outputs={"result": "candidates"},
    )

    default_algorithm_registry().validate(workflow, SpatialContext())

    assert tuple(step.id for step in workflow.steps_in_dependency_order) == (
        "buffer_roads",
        "clip_parcels",
    )
