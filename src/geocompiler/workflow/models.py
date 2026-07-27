"""Portable, provider-independent Workflow IR models."""

from __future__ import annotations

from collections import defaultdict, deque
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from geocompiler.workflow.errors import WorkflowGraphError


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


class WorkflowInput(BaseModel):
    """A portable data input to a workflow."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    kind: GeometryKind
    required: bool = True


class WorkflowParameter(BaseModel):
    """A user-configurable, portable workflow value."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    kind: ParameterKind
    default: JsonValue
    unit: str | None = None

    @model_validator(mode="after")
    def validate_default(self) -> WorkflowParameter:
        if not _value_matches_kind(self.default, self.kind):
            raise ValueError(f"default for {self.id} does not match {self.kind}")
        if self.kind in {ParameterKind.DISTANCE, ParameterKind.AREA} and not self.unit:
            raise ValueError(f"{self.kind} parameter {self.id} requires a unit")
        if self.kind not in {ParameterKind.DISTANCE, ParameterKind.AREA} and self.unit:
            raise ValueError(f"{self.kind} parameter {self.id} cannot declare a unit")
        return self


class WorkflowStep(BaseModel):
    """One semantic operation in a Workflow IR directed acyclic graph."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    inputs: dict[str, str] = Field(min_length=1)
    parameters: dict[str, JsonValue]
    outputs: dict[str, str] = Field(min_length=1)


class WorkflowIR(BaseModel):
    """The trusted, serializable intermediate representation for a workflow."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = Field(min_length=1)
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    inputs: list[WorkflowInput]
    parameters: list[WorkflowParameter]
    steps: list[WorkflowStep]
    outputs: dict[str, str]

    @model_validator(mode="after")
    def validate_graph(self) -> WorkflowIR:
        if not self.outputs:
            raise WorkflowGraphError("workflow requires at least one declared output")
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
            for value in step.parameters.values():
                _validate_parameter_references(value, parameter_ids)

        for reference in self.outputs.values():
            if reference not in known_references:
                raise WorkflowGraphError(f"unknown reference: {reference}")

        _ensure_acyclic((step.id for step in self.steps), dependencies)
        return self

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
        for step in self.steps:
            for reference in step.inputs.values():
                producer = producers.get(reference)
                if producer:
                    dependencies[step.id].add(producer)

        ready = deque(step.id for step in self.steps if not dependencies[step.id])
        ordered: list[WorkflowStep] = []
        dependents: dict[str, set[str]] = defaultdict(set)
        for step_id, parents in dependencies.items():
            for parent in parents:
                dependents[parent].add(step_id)

        while ready:
            step_id = ready.popleft()
            ordered.append(step_by_id[step_id])
            for child in dependents[step_id]:
                dependencies[child].remove(step_id)
                if not dependencies[child]:
                    ready.append(child)
        return tuple(ordered)


def _value_matches_kind(value: Any, kind: ParameterKind) -> bool:
    if kind is ParameterKind.BOOLEAN:
        return isinstance(value, bool)
    if kind is ParameterKind.STRING:
        return isinstance(value, str)
    if kind is ParameterKind.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool)
    if kind in {ParameterKind.NUMBER, ParameterKind.DISTANCE, ParameterKind.AREA}:
        return isinstance(value, int | float) and not isinstance(value, bool)
    return False


def value_matches_parameter_kind(value: Any, kind: ParameterKind) -> bool:
    """Check literal values against a parameter definition."""

    return _value_matches_kind(value, kind)


def _ensure_unique(values: Any, label: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise WorkflowGraphError(f"duplicate {label}: {value}")
        seen.add(value)


def _output_producers(steps: list[WorkflowStep]) -> dict[str, str]:
    producers: dict[str, str] = {}
    for step in steps:
        for output_reference in step.outputs.values():
            if output_reference in producers:
                raise WorkflowGraphError(f"duplicate output reference: {output_reference}")
            producers[output_reference] = step.id
    return producers


def _validate_parameter_references(value: Any, parameter_ids: set[str]) -> None:
    if isinstance(value, str) and value.startswith("$"):
        parameter_id = value[1:]
        if parameter_id not in parameter_ids:
            raise WorkflowGraphError(f"unknown parameter: {parameter_id}")
    elif isinstance(value, list):
        for item in value:
            _validate_parameter_references(item, parameter_ids)
    elif isinstance(value, dict):
        for item in value.values():
            _validate_parameter_references(item, parameter_ids)


def _ensure_acyclic(step_ids: Any, dependencies: dict[str, set[str]]) -> None:
    all_step_ids = tuple(step_ids)
    remaining = {step_id: set(dependencies[step_id]) for step_id in all_step_ids}
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
    if visited != len(all_step_ids):
        raise WorkflowGraphError("dependency cycle detected")
