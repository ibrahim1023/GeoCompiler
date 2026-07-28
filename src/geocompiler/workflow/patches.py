"""Atomic, typed Workflow IR patch artifacts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError

from geocompiler.workflow.errors import WorkflowError
from geocompiler.workflow.models import WorkflowIR, WorkflowParameter, WorkflowStep


class PatchOperation(BaseModel):
    """One deterministic change to a Workflow IR artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    type: Literal[
        "add_parameter",
        "update_parameter",
        "insert_step",
        "remove_step",
        "update_step",
    ]
    target_id: str | None = None
    payload: dict[str, JsonValue] = Field(default_factory=dict)


class WorkflowPatch(BaseModel):
    """A versioned sequence of typed changes for one workflow."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_id: str = Field(min_length=1)
    base_version: str = Field(min_length=1)
    operations: list[PatchOperation]
    summary: str = Field(min_length=1)


class PatchResult(BaseModel):
    """The replacement workflow and a concise deterministic change list."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow: WorkflowIR
    changes: tuple[str, ...]


def apply_patch(workflow: WorkflowIR, patch: WorkflowPatch) -> PatchResult:
    """Apply all patch operations or leave the original workflow unchanged."""

    if patch.workflow_id != workflow.id:
        raise WorkflowError("patch targets a different workflow")
    if patch.base_version != workflow.schema_version:
        raise WorkflowError("patch base version does not match workflow schema version")

    parameters = [parameter.model_dump(mode="json") for parameter in workflow.parameters]
    steps = [step.model_dump(mode="json") for step in workflow.steps]
    changes: list[str] = []

    for operation in patch.operations:
        if operation.type == "add_parameter":
            parameter = _parse_parameter(operation.payload)
            if any(candidate["id"] == parameter.id for candidate in parameters):
                raise WorkflowError(f"duplicate parameter: {parameter.id}")
            parameters.append(parameter.model_dump(mode="json"))
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
            steps.insert(position, step.model_dump(mode="json"))
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
                **workflow.model_dump(mode="json"),
                "parameters": parameters,
                "steps": steps,
            }
        )
    except ValidationError as error:
        raise WorkflowError(f"patch produces an invalid workflow: {error}") from error
    return PatchResult(workflow=candidate, changes=tuple(changes))


def _parse_parameter(payload: dict[str, JsonValue]) -> WorkflowParameter:
    try:
        return WorkflowParameter.model_validate(payload)
    except ValidationError as error:
        raise WorkflowError(f"invalid parameter payload: {error}") from error


def _parse_step(payload: dict[str, JsonValue]) -> WorkflowStep:
    try:
        return WorkflowStep.model_validate(payload)
    except ValidationError as error:
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
        return model_type.model_validate({**existing, **payload}).model_dump(mode="json")
    except ValidationError as error:
        raise WorkflowError(f"invalid {label} payload: {error}") from error
