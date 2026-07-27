from __future__ import annotations

import pytest

from geocompiler.qgis import (
    LayerKind,
    LayerSummary,
    ProjectContext,
    QgisCompiler,
    QgisWorkflowRunner,
)
from geocompiler.workflow import (
    CompatibilityError,
    GeometryKind,
    ParameterKind,
    UnsupportedOperationError,
    WorkflowInput,
    WorkflowIR,
    WorkflowParameter,
    WorkflowStep,
)
from geocompiler.workflow.errors import CompilerError, ExecutionError


def _context(*, projected: bool = True) -> ProjectContext:
    return ProjectContext(
        layers=(
            LayerSummary(
                id="roads",
                name="Roads",
                kind=LayerKind.VECTOR,
                geometry_kind="vector_line",
                crs_auth_id="EPSG:32640" if projected else "EPSG:4326",
                is_projected=projected,
            ),
        )
    )


def _workflow(*, operation: str = "buffer", kind: GeometryKind = GeometryKind.LINE) -> WorkflowIR:
    return WorkflowIR(
        schema_version="1.0",
        id="buffer-roads",
        name="Buffer roads",
        inputs=[WorkflowInput(id="roads", title="Roads", kind=kind)],
        parameters=[
            WorkflowParameter(
                id="distance",
                title="Distance",
                kind=ParameterKind.DISTANCE,
                default=500,
                unit="m",
            )
        ],
        steps=[
            WorkflowStep(
                id="buffer_roads",
                operation=operation,
                inputs={"INPUT": "roads"},
                parameters={"DISTANCE": "$distance"},
                outputs={"OUTPUT": "buffered_roads"},
            )
        ],
        outputs={"result": "buffered_roads"},
    )


def test_compiler_resolves_only_registry_approved_steps() -> None:
    compiled = QgisCompiler().compile(_workflow(), _context())

    assert compiled.steps[0].id == "buffer_roads"
    assert compiled.steps[0].qgis_algorithm_id == "native:buffer"
    assert compiled.steps[0].parameters == {"DISTANCE": "$distance"}


def test_compiler_rejects_unsupported_operations() -> None:
    with pytest.raises(UnsupportedOperationError, match="unsupported operation"):
        QgisCompiler().compile(_workflow(operation="unapproved"), _context())


def test_compiler_rejects_incompatible_geometry_and_crs() -> None:
    with pytest.raises(CompatibilityError, match="expects one of"):
        QgisCompiler().compile(_workflow(kind=GeometryKind.RASTER), _context())
    with pytest.raises(CompatibilityError, match="requires a projected CRS"):
        QgisCompiler().compile(_workflow(), _context(projected=False))


def test_runner_resolves_bound_inputs_defaults_and_temporary_outputs() -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def run_algorithm(algorithm_id: str, arguments: dict[str, object]) -> dict[str, object]:
        calls.append((algorithm_id, arguments))
        return {"OUTPUT": "generated-buffer-layer"}

    compiled = QgisCompiler().compile(_workflow(), _context())
    result = QgisWorkflowRunner(run_algorithm).execute(
        compiled,
        input_bindings={"roads": "roads-layer"},
        parameter_values={"distance": 750},
    )

    assert calls == [
        (
            "native:buffer",
            {"INPUT": "roads-layer", "DISTANCE": 750, "OUTPUT": "TEMPORARY_OUTPUT"},
        )
    ]
    assert result.outputs == {"result": "generated-buffer-layer"}
    assert result.step_outputs == {"buffer_roads": {"OUTPUT": "generated-buffer-layer"}}


def test_runner_rejects_unbound_inputs_and_invalid_parameter_overrides() -> None:
    compiled = QgisCompiler().compile(_workflow(), _context())
    runner = QgisWorkflowRunner(lambda *_: {"OUTPUT": "unused"})

    with pytest.raises(CompilerError, match="missing workflow input binding: roads"):
        runner.execute(compiled, input_bindings={})
    with pytest.raises(CompilerError, match="requires distance value"):
        runner.execute(
            compiled,
            input_bindings={"roads": "roads-layer"},
            parameter_values={"distance": "not a distance"},
        )


def test_runner_maps_qgis_failure_to_step_and_algorithm() -> None:
    compiled = QgisCompiler().compile(_workflow(), _context())

    def fail(_: str, __: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("invalid geometry")

    with pytest.raises(
        ExecutionError,
        match=r"step buffer_roads \(native:buffer\) failed: invalid geometry",
    ):
        QgisWorkflowRunner(fail).execute(compiled, input_bindings={"roads": "roads-layer"})


def test_runner_maps_invalid_field_failure_to_step_and_algorithm() -> None:
    compiled = QgisCompiler().compile(_workflow(), _context())

    def fail(_: str, __: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("field does_not_exist was not found")

    with pytest.raises(
        ExecutionError,
        match=r"step buffer_roads \(native:buffer\) failed: field does_not_exist was not found",
    ):
        QgisWorkflowRunner(fail).execute(compiled, input_bindings={"roads": "roads-layer"})
