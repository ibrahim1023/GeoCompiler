"""Atomic, typed Workflow IR patch artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from geocompiler.workflow.errors import WorkflowError
from geocompiler.workflow.models import WorkflowIR, WorkflowParameter, WorkflowStep
from geocompiler.workflow.serialization import (
    ArtifactValidationError,
    FrozenArtifact,
    JsonValue,
    require_mapping,
    require_string,
    validate_json_value,
)


@dataclass(frozen=True)
class PatchOperation(FrozenArtifact):
    """One deterministic change to a Workflow IR artifact."""

    type: Literal[
        "add_parameter",
        "update_parameter",
        "insert_step",
        "remove_step",
        "update_step",
    ]
    target_id: str | None = None
    payload: dict[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        allowed = {"add_parameter", "update_parameter", "insert_step", "remove_step", "update_step"}
        if self.type not in allowed:
            raise ArtifactValidationError("unsupported patch operation")
        if self.target_id is not None:
            require_string(self.target_id, "patch target ID")
        payload = require_mapping(self.payload, "patch payload")
        normalized = {
            key: validate_json_value(value, "patch payload") for key, value in payload.items()
        }
        object.__setattr__(self, "payload", normalized)


@dataclass(frozen=True)
class WorkflowPatch(FrozenArtifact):
    """A versioned sequence of typed changes for one workflow."""

    workflow_id: str
    base_version: str
    operations: tuple[PatchOperation, ...]
    summary: str

    def __post_init__(self) -> None:
        require_string(self.workflow_id, "patch workflow ID")
        require_string(self.base_version, "patch base version")
        require_string(self.summary, "patch summary")
        operations = tuple(
            item if isinstance(item, PatchOperation) else PatchOperation.from_dict(item)
            for item in self.operations
        )
        object.__setattr__(self, "operations", operations)


@dataclass(frozen=True)
class PatchResult(FrozenArtifact):
    """The replacement workflow and a concise deterministic change list."""

    workflow: WorkflowIR
    changes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.workflow, WorkflowIR):
            object.__setattr__(self, "workflow", WorkflowIR.from_dict(self.workflow))
        if not all(isinstance(change, str) for change in self.changes):
            raise ArtifactValidationError("patch changes must be strings")


def apply_patch(workflow: WorkflowIR, patch: WorkflowPatch) -> PatchResult:
    """Apply all patch operations or leave the original workflow unchanged."""

    if patch.workflow_id != workflow.id:
        raise WorkflowError("patch targets a different workflow")
    if patch.base_version != workflow.schema_version:
        raise WorkflowError("patch base version does not match workflow schema version")

    parameters = [parameter.to_dict() for parameter in workflow.parameters]
    steps = [step.to_dict() for step in workflow.steps]
    changes: list[str] = []

    for operation in patch.operations:
        if operation.type == "add_parameter":
            parameter = _parse_parameter(operation.payload)
            if any(candidate["id"] == parameter.id for candidate in parameters):
                raise WorkflowError(f"duplicate parameter: {parameter.id}")
            parameters.append(parameter.to_dict())
            changes.append(f"add_parameter:{parameter.id}")
        elif operation.type == "update_parameter":
            target = _target(parameters, operation.target_id, "parameter")
            parameters[target] = _update_item(
                parameters[target],
                operation.payload,
                operation.target_id,
                WorkflowParameter,
                "parameter",
            )
            changes.append(f"update_parameter:{operation.target_id}")
        elif operation.type == "insert_step":
            step = _parse_step(operation.payload)
            if any(candidate["id"] == step.id for candidate in steps):
                raise WorkflowError(f"duplicate step: {step.id}")
            position = (
                len(steps)
                if operation.target_id is None
                else _target(steps, operation.target_id, "step") + 1
            )
            steps.insert(position, step.to_dict())
            changes.append(f"insert_step:{step.id}")
        elif operation.type == "remove_step":
            target = _target(steps, operation.target_id, "step")
            steps.pop(target)
            changes.append(f"remove_step:{operation.target_id}")
        else:
            target = _target(steps, operation.target_id, "step")
            steps[target] = _update_item(
                steps[target], operation.payload, operation.target_id, WorkflowStep, "step"
            )
            changes.append(f"update_step:{operation.target_id}")

    try:
        candidate = WorkflowIR.model_validate(
            {
                **workflow.to_dict(),
                "parameters": parameters,
                "steps": steps,
            }
        )
    except (ArtifactValidationError, WorkflowError) as error:
        raise WorkflowError(f"patch produces an invalid workflow: {error}") from error
    return PatchResult(workflow=candidate, changes=tuple(changes))


def _parse_parameter(payload: dict[str, JsonValue]) -> WorkflowParameter:
    try:
        return WorkflowParameter.model_validate(payload)
    except ArtifactValidationError as error:
        raise WorkflowError(f"invalid parameter payload: {error}") from error


def _parse_step(payload: dict[str, JsonValue]) -> WorkflowStep:
    try:
        return WorkflowStep.model_validate(payload)
    except ArtifactValidationError as error:
        raise WorkflowError(f"invalid step payload: {error}") from error


def _target(items: list[dict[str, JsonValue]], target_id: str | None, label: str) -> int:
    if target_id is None:
        raise WorkflowError(f"{label} operation requires a target ID")
    for index, item in enumerate(items):
        if item["id"] == target_id:
            return index
    raise WorkflowError(f"unknown {label}: {target_id}")


def _update_item(
    existing: dict[str, JsonValue],
    payload: dict[str, JsonValue],
    target_id: str | None,
    model_type: type[WorkflowParameter] | type[WorkflowStep],
    label: str,
) -> dict[str, JsonValue]:
    if "id" in payload and payload["id"] != target_id:
        raise WorkflowError(f"{label} ID cannot change")
    try:
        return model_type.model_validate({**existing, **payload}).to_dict()
    except ArtifactValidationError as error:
        raise WorkflowError(f"invalid {label} payload: {error}") from error
