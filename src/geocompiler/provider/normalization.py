"""Safe project-context normalization and structured provider response parsing."""

from __future__ import annotations

from pydantic import ValidationError

from geocompiler.provider.contracts import (
    LLMProvider,
    ProviderError,
    ProviderRequest,
    ProviderResponse,
)
from geocompiler.qgis.context import ProjectContext
from geocompiler.workflow.errors import WorkflowError
from geocompiler.workflow.models import WorkflowIR, WorkflowParameter, WorkflowStep
from geocompiler.workflow.patches import PatchOperation, WorkflowPatch
from geocompiler.workflow.registry import default_algorithm_registry


def build_provider_request(intent: str, context: ProjectContext) -> ProviderRequest:
    """Serialize only the existing metadata-only ProjectContext contract."""

    return ProviderRequest(intent=intent, context=context.model_dump(mode="json"))


def parse_provider_response(payload: str | dict[str, object]) -> WorkflowIR | WorkflowPatch:
    """Parse one strict provider envelope without compiling or executing it."""

    try:
        response = (
            ProviderResponse.model_validate_json(payload)
            if isinstance(payload, str)
            else ProviderResponse.model_validate(payload)
        )
    except ValidationError as error:
        raise ValueError(f"invalid provider response: {error}") from error

    try:
        if response.artifact == "patch":
            patch = WorkflowPatch.model_validate(response.payload)
            _validate_provider_patch(patch)
            return patch
        workflow = WorkflowIR.model_validate(response.payload)
    except (ValidationError, WorkflowError) as error:
        raise ValueError(f"invalid {response.artifact} artifact: {error}") from error

    registry = default_algorithm_registry()
    for step in workflow.steps:
        try:
            registry.resolve(step.operation)
        except Exception as error:
            raise ValueError(
                f"unsupported operation in provider workflow: {step.operation}"
            ) from error
    return workflow


def _validate_provider_patch(patch: WorkflowPatch) -> None:
    """Reject incomplete, unsafe, or unsupported provider patch operations."""

    registry = default_algorithm_registry()
    for operation in patch.operations:
        if operation.type == "add_parameter":
            WorkflowParameter.model_validate(operation.payload)
        elif operation.type == "insert_step":
            step = WorkflowStep.model_validate(operation.payload)
            registry.resolve(step.operation)
        elif operation.type == "remove_step":
            _require_target(operation)
            if operation.payload:
                raise ValueError("remove_step operation cannot contain a payload")
        elif operation.type == "update_parameter":
            _require_target(operation)
            _validate_update_payload(operation, WorkflowParameter)
        else:
            _require_target(operation)
            _validate_update_payload(operation, WorkflowStep)
            candidate_operation = operation.payload.get("operation")
            if candidate_operation is not None:
                registry.resolve(str(candidate_operation))


def _require_target(operation: PatchOperation) -> None:
    if operation.target_id is None:
        raise ValueError(f"{operation.type} operation requires a target ID")


def _validate_update_payload(
    operation: PatchOperation, model_type: type[WorkflowParameter] | type[WorkflowStep]
) -> None:
    unknown_keys = set(operation.payload).difference(model_type.model_fields)
    if unknown_keys:
        unknown = ", ".join(sorted(unknown_keys))
        raise ValueError(f"{operation.type} operation has unsupported fields: {unknown}")


def request_artifact(provider: LLMProvider, request: ProviderRequest) -> WorkflowIR | WorkflowPatch:
    """Request and validate one artifact without compiling or executing it."""

    try:
        response = provider.generate(request)
    except Exception as error:
        raise ProviderError(f"provider request failed: {error}") from error
    try:
        return parse_provider_response(response.model_dump(mode="json"))
    except (AttributeError, ValueError) as error:
        raise ProviderError(f"provider returned an invalid artifact: {error}") from error
