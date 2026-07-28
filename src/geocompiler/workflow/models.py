"""Portable, provider-independent Workflow IR models."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from geocompiler.workflow.errors import WorkflowGraphError
from geocompiler.workflow.serialization import (
    ArtifactValidationError,
    FrozenArtifact,
    JsonValue,
    require_mapping,
    require_string,
    validate_json_value,
)


class GeometryKind(StrEnum):
    POINT = "vector_point"
    LINE = "vector_line"
    POLYGON = "vector_polygon"
    RASTER = "raster"


class ParameterKind(StrEnum):
    NUMBER = "number"
    INTEGER = "integer"
    STRING = "string"
    BOOLEAN = "boolean"
    DISTANCE = "distance"
    AREA = "area"


@dataclass(frozen=True)
class WorkflowInput(FrozenArtifact):
    id: str
    title: str
    kind: GeometryKind
    required: bool = True

    def __post_init__(self) -> None:
        require_string(self.id, "input id")
        require_string(self.title, "input title")
        if not isinstance(self.kind, GeometryKind):
            object.__setattr__(self, "kind", GeometryKind(self.kind))
        if not isinstance(self.required, bool):
            raise ArtifactValidationError("input required must be a boolean")


@dataclass(frozen=True)
class WorkflowParameter(FrozenArtifact):
    id: str
    title: str
    kind: ParameterKind
    default: JsonValue
    unit: str | None = None

    def __post_init__(self) -> None:
        require_string(self.id, "parameter id")
        require_string(self.title, "parameter title")
        if not isinstance(self.kind, ParameterKind):
            object.__setattr__(self, "kind", ParameterKind(self.kind))
        object.__setattr__(self, "default", validate_json_value(self.default, "parameter default"))
        if self.unit is not None:
            require_string(self.unit, "parameter unit")
        if not _value_matches_kind(self.default, self.kind):
            raise ArtifactValidationError(f"default for {self.id} does not match {self.kind}")
        if self.kind in {ParameterKind.DISTANCE, ParameterKind.AREA} and not self.unit:
            raise ArtifactValidationError(f"{self.kind} parameter {self.id} requires a unit")
        if self.kind not in {ParameterKind.DISTANCE, ParameterKind.AREA} and self.unit:
            raise ArtifactValidationError(f"{self.kind} parameter {self.id} cannot declare a unit")


@dataclass(frozen=True)
class WorkflowStep(FrozenArtifact):
    id: str
    operation: str
    inputs: dict[str, str]
    parameters: dict[str, JsonValue]
    outputs: dict[str, str]

    def __post_init__(self) -> None:
        require_string(self.id, "step id")
        require_string(self.operation, "step operation")
        object.__setattr__(
            self, "inputs", _string_mapping(self.inputs, "step inputs", nonempty=True)
        )
        object.__setattr__(
            self, "outputs", _string_mapping(self.outputs, "step outputs", nonempty=True)
        )
        parameters = require_mapping(self.parameters, "step parameters")
        object.__setattr__(
            self,
            "parameters",
            {
                key: validate_json_value(value, "step parameters")
                for key, value in parameters.items()
            },
        )


@dataclass(frozen=True)
class WorkflowIR(FrozenArtifact):
    schema_version: str
    id: str
    name: str
    inputs: tuple[WorkflowInput, ...]
    parameters: tuple[WorkflowParameter, ...]
    steps: tuple[WorkflowStep, ...]
    outputs: dict[str, str]

    def __post_init__(self) -> None:
        require_string(self.schema_version, "workflow schema version")
        require_string(self.id, "workflow id")
        require_string(self.name, "workflow name")
        object.__setattr__(self, "inputs", tuple(_parse_input(item) for item in self.inputs))
        object.__setattr__(
            self, "parameters", tuple(_parse_parameter(item) for item in self.parameters)
        )
        object.__setattr__(self, "steps", tuple(_parse_step(item) for item in self.steps))
        object.__setattr__(self, "outputs", _string_mapping(self.outputs, "workflow outputs"))
        if not self.outputs:
            raise WorkflowGraphError("workflow requires at least one declared output")
        self._validate_graph()

    @classmethod
    def from_dict(cls, value: object) -> WorkflowIR:
        value = require_mapping(value, "WorkflowIR")
        allowed = {"schema_version", "id", "name", "inputs", "parameters", "steps", "outputs"}
        unknown = set(value).difference(allowed)
        if unknown:
            raise ArtifactValidationError(f"extra fields: {', '.join(sorted(unknown))}")
        try:
            return cls(**value)  # type: ignore[arg-type]
        except (TypeError, ValueError) as error:
            if isinstance(error, ArtifactValidationError | WorkflowGraphError):
                raise
            raise ArtifactValidationError(str(error)) from error

    def _validate_graph(self) -> None:
        _ensure_unique((input_.id for input_ in self.inputs), "input id")
        _ensure_unique((parameter.id for parameter in self.parameters), "parameter id")
        _ensure_unique((step.id for step in self.steps), "step id")
        input_ids = {input_.id for input_ in self.inputs}
        parameter_ids = {parameter.id for parameter in self.parameters}
        output_producers = _output_producers(self.steps)
        if input_ids.intersection(output_producers):
            conflict = sorted(input_ids.intersection(output_producers))[0]
            raise WorkflowGraphError(f"output conflicts with input reference: {conflict}")
        known_references = input_ids | set(output_producers)
        dependencies: dict[str, set[str]] = defaultdict(set)
        for step in self.steps:
            for reference in step.inputs.values():
                if reference not in known_references:
                    raise WorkflowGraphError(f"unknown reference: {reference}")
                if reference in output_producers:
                    dependencies[step.id].add(output_producers[reference])
            for item in step.parameters.values():
                _validate_parameter_references(item, parameter_ids)
        for reference in self.outputs.values():
            if reference not in known_references:
                raise WorkflowGraphError(f"unknown reference: {reference}")
        _ensure_acyclic((step.id for step in self.steps), dependencies)

    @property
    def step_ids(self) -> tuple[str, ...]:
        return tuple(step.id for step in self.steps)

    @property
    def parameters_by_id(self) -> dict[str, WorkflowParameter]:
        return {parameter.id: parameter for parameter in self.parameters}

    @property
    def steps_in_dependency_order(self) -> tuple[WorkflowStep, ...]:
        step_by_id = {step.id: step for step in self.steps}
        producers = _output_producers(self.steps)
        dependencies: dict[str, set[str]] = defaultdict(set)
        dependents: dict[str, set[str]] = defaultdict(set)
        for step in self.steps:
            for reference in step.inputs.values():
                producer = producers.get(reference)
                if producer:
                    dependencies[step.id].add(producer)
                    dependents[producer].add(step.id)
        ready = deque(step.id for step in self.steps if not dependencies[step.id])
        ordered: list[WorkflowStep] = []
        while ready:
            step_id = ready.popleft()
            ordered.append(step_by_id[step_id])
            for child in dependents[step_id]:
                dependencies[child].remove(step_id)
                if not dependencies[child]:
                    ready.append(child)
        return tuple(ordered)


def _parse_input(value: object) -> WorkflowInput:
    return value if isinstance(value, WorkflowInput) else WorkflowInput.from_dict(value)


def _parse_parameter(value: object) -> WorkflowParameter:
    return value if isinstance(value, WorkflowParameter) else WorkflowParameter.from_dict(value)


def _parse_step(value: object) -> WorkflowStep:
    return value if isinstance(value, WorkflowStep) else WorkflowStep.from_dict(value)


def _string_mapping(value: object, label: str, *, nonempty: bool = False) -> dict[str, str]:
    mapping = require_mapping(value, label)
    if nonempty and not mapping:
        raise ArtifactValidationError(f"{label} requires at least one item")
    return {
        require_string(key, label): require_string(item, label) for key, item in mapping.items()
    }


def _value_matches_kind(value: Any, kind: ParameterKind) -> bool:
    if kind is ParameterKind.BOOLEAN:
        return isinstance(value, bool)
    if kind is ParameterKind.STRING:
        return isinstance(value, str)
    if kind is ParameterKind.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, int | float) and not isinstance(value, bool)


def value_matches_parameter_kind(value: Any, kind: ParameterKind) -> bool:
    return _value_matches_kind(value, kind)


def _ensure_unique(values: Any, label: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise WorkflowGraphError(f"duplicate {label}: {value}")
        seen.add(value)


def _output_producers(steps: tuple[WorkflowStep, ...]) -> dict[str, str]:
    producers: dict[str, str] = {}
    for step in steps:
        for reference in step.outputs.values():
            if reference in producers:
                raise WorkflowGraphError(f"duplicate output reference: {reference}")
            producers[reference] = step.id
    return producers


def _validate_parameter_references(value: Any, parameter_ids: set[str]) -> None:
    if isinstance(value, str) and value.startswith("$") and value[1:] not in parameter_ids:
        raise WorkflowGraphError(f"unknown parameter: {value[1:]}")
    if isinstance(value, list):
        for item in value:
            _validate_parameter_references(item, parameter_ids)
    if isinstance(value, dict):
        for item in value.values():
            _validate_parameter_references(item, parameter_ids)


def _ensure_acyclic(step_ids: Any, dependencies: dict[str, set[str]]) -> None:
    remaining = {step_id: set(dependencies[step_id]) for step_id in step_ids}
    dependents: dict[str, set[str]] = defaultdict(set)
    for child, parents in remaining.items():
        for parent in parents:
            dependents[parent].add(child)
    ready = deque(step_id for step_id, parents in remaining.items() if not parents)
    visited = 0
    while ready:
        step_id = ready.popleft()
        visited += 1
        for child in dependents[step_id]:
            remaining[child].remove(step_id)
            if not remaining[child]:
                ready.append(child)
    if visited != len(remaining):
        raise WorkflowGraphError("dependency cycle detected")
