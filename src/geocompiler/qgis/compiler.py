"""Deterministic compilation and controlled QGIS Processing execution."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from geocompiler.qgis.context import ProjectContext
from geocompiler.workflow.errors import CompatibilityError, CompilerError, ExecutionError
from geocompiler.workflow.models import ParameterKind, WorkflowIR, value_matches_parameter_kind
from geocompiler.workflow.registry import (
    AlgorithmRegistry,
    SpatialContext,
    default_algorithm_registry,
)


class CompiledParameter(BaseModel):
    """A workflow parameter available to the controlled execution boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    kind: ParameterKind
    default: JsonValue


class CompiledStep(BaseModel):
    """A registry-approved QGIS Processing call with symbolic references."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    qgis_algorithm_id: str = Field(min_length=1)
    inputs: dict[str, str]
    parameters: dict[str, JsonValue]
    outputs: dict[str, str]


class CompiledWorkflow(BaseModel):
    """An executable plan whose operations have passed the approved registry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_id: str = Field(min_length=1)
    input_ids: tuple[str, ...]
    parameters: tuple[CompiledParameter, ...]
    steps: tuple[CompiledStep, ...]
    outputs: dict[str, str]


class WorkflowExecutionResult(BaseModel):
    """References produced by the QGIS Processing runner."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    outputs: dict[str, Any]
    step_outputs: dict[str, dict[str, Any]]


class QgisCompiler:
    """Compile only registry-approved Workflow IR into symbolic Processing calls."""

    def __init__(self, registry: AlgorithmRegistry | None = None) -> None:
        self._registry = registry or default_algorithm_registry()

    def compile(
        self,
        workflow: WorkflowIR,
        context: ProjectContext,
        *,
        input_layer_ids: Mapping[str, str] | None = None,
    ) -> CompiledWorkflow:
        """Validate and map a workflow without importing or executing PyQGIS."""

        self._registry.validate(
            workflow,
            self._spatial_context(workflow, context, input_layer_ids),
        )
        return CompiledWorkflow(
            workflow_id=workflow.id,
            input_ids=tuple(input_.id for input_ in workflow.inputs),
            parameters=tuple(
                CompiledParameter(
                    id=parameter.id,
                    kind=parameter.kind,
                    default=parameter.default,
                )
                for parameter in workflow.parameters
            ),
            steps=tuple(
                CompiledStep(
                    id=step.id,
                    qgis_algorithm_id=self._registry.resolve(step.operation).qgis_algorithm_id,
                    inputs=step.inputs,
                    parameters=step.parameters,
                    outputs=step.outputs,
                )
                for step in workflow.steps_in_dependency_order
            ),
            outputs=workflow.outputs,
        )

    @staticmethod
    def _spatial_context(
        workflow: WorkflowIR,
        context: ProjectContext,
        input_layer_ids: Mapping[str, str] | None,
    ) -> SpatialContext:
        layers_by_id = {layer.id: layer for layer in context.layers}
        bindings = dict(input_layer_ids or {input_.id: input_.id for input_ in workflow.inputs})
        expected = {input_.id for input_ in workflow.inputs}
        unknown = set(bindings).difference(expected)
        if unknown:
            raise CompilerError(f"unknown workflow input layer binding: {sorted(unknown)[0]}")
        missing = expected.difference(bindings)
        if missing:
            raise CompilerError(f"missing workflow input layer binding: {sorted(missing)[0]}")

        projected_references: dict[str, bool] = {}
        for input_ in workflow.inputs:
            layer_id = bindings[input_.id]
            try:
                layer = layers_by_id[layer_id]
            except KeyError as error:
                raise CompilerError(
                    f"workflow input {input_.id} is bound to unavailable project layer: {layer_id}"
                ) from error
            if layer.geometry_kind != input_.kind.value:
                raise CompatibilityError(
                    f"workflow input {input_.id} expects {input_.kind.value}; "
                    f"got {layer.geometry_kind or layer.kind.value}"
                )
            if layer.is_projected is not None:
                projected_references[input_.id] = layer.is_projected
        return SpatialContext(projected_references=projected_references)


class QgisWorkflowRunner:
    """Execute compiled steps through QGIS Processing and map failures to steps."""

    def __init__(
        self,
        run_algorithm: Callable[[str, dict[str, Any]], Mapping[str, Any]] | None = None,
    ) -> None:
        self._run_algorithm = run_algorithm or _qgis_processing_run

    def execute(
        self,
        workflow: CompiledWorkflow,
        *,
        input_bindings: Mapping[str, Any],
        parameter_values: Mapping[str, JsonValue] | None = None,
    ) -> WorkflowExecutionResult:
        """Run a compiled workflow using explicit user-approved input bindings."""

        references = self._validate_bindings(workflow, input_bindings)
        values = self._parameter_values(workflow, parameter_values or {})
        step_outputs: dict[str, dict[str, Any]] = {}

        for step in workflow.steps:
            arguments = {
                port: self._reference_value(references, reference, step.id)
                for port, reference in step.inputs.items()
            }
            arguments.update(
                {
                    name: self._resolve_parameter(value, values, step.id)
                    for name, value in step.parameters.items()
                }
            )
            arguments.update({port: "TEMPORARY_OUTPUT" for port in step.outputs})
            try:
                result = self._run_algorithm(step.qgis_algorithm_id, arguments)
            except Exception as error:
                raise ExecutionError(step.id, step.qgis_algorithm_id, str(error)) from error

            recorded_outputs: dict[str, Any] = {}
            for port, reference in step.outputs.items():
                if port not in result:
                    raise ExecutionError(
                        step.id,
                        step.qgis_algorithm_id,
                        f"QGIS did not return required output: {port}",
                    )
                references[reference] = result[port]
                recorded_outputs[port] = result[port]
            step_outputs[step.id] = recorded_outputs

        return WorkflowExecutionResult(
            outputs={
                name: self._reference_value(references, reference, "workflow output")
                for name, reference in workflow.outputs.items()
            },
            step_outputs=step_outputs,
        )

    @staticmethod
    def _validate_bindings(
        workflow: CompiledWorkflow,
        input_bindings: Mapping[str, Any],
    ) -> dict[str, Any]:
        expected = set(workflow.input_ids)
        provided = set(input_bindings)
        unknown = provided.difference(expected)
        if unknown:
            raise CompilerError(f"unknown workflow input binding: {sorted(unknown)[0]}")
        missing = expected.difference(provided)
        if missing:
            raise CompilerError(f"missing workflow input binding: {sorted(missing)[0]}")
        return dict(input_bindings)

    @staticmethod
    def _parameter_values(
        workflow: CompiledWorkflow,
        overrides: Mapping[str, JsonValue],
    ) -> dict[str, JsonValue]:
        parameters = {parameter.id: parameter for parameter in workflow.parameters}
        unknown = set(overrides).difference(parameters)
        if unknown:
            raise CompilerError(f"unknown workflow parameter override: {sorted(unknown)[0]}")
        values = {parameter.id: parameter.default for parameter in workflow.parameters}
        for parameter_id, value in overrides.items():
            parameter = parameters[parameter_id]
            if not value_matches_parameter_kind(value, parameter.kind):
                raise CompilerError(
                    f"parameter {parameter_id} requires {parameter.kind.value} value"
                )
            values[parameter_id] = value
        return values

    @staticmethod
    def _reference_value(references: Mapping[str, Any], reference: str, step_id: str) -> Any:
        try:
            return references[reference]
        except KeyError as error:
            raise CompilerError(
                f"step {step_id} references unavailable input: {reference}"
            ) from error

    @staticmethod
    def _resolve_parameter(
        value: JsonValue,
        values: Mapping[str, JsonValue],
        step_id: str,
    ) -> JsonValue:
        if isinstance(value, str) and value.startswith("$"):
            parameter_id = value[1:]
            try:
                return values[parameter_id]
            except KeyError as error:
                raise CompilerError(
                    f"step {step_id} references unavailable parameter: {parameter_id}"
                ) from error
        return value


def _qgis_processing_run(algorithm_id: str, arguments: dict[str, Any]) -> Mapping[str, Any]:
    try:
        import processing
    except ImportError as error:  # pragma: no cover - only exercised outside QGIS.
        raise RuntimeError("PyQGIS Processing is required to execute workflows") from error
    return processing.run(algorithm_id, arguments)
