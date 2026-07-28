"""Safe project-context normalization and structured provider response parsing."""

from __future__ import annotations

from pydantic import ValidationError

from geocompiler.provider.contracts import ProviderRequest, ProviderResponse
from geocompiler.qgis.context import ProjectContext
from geocompiler.workflow.models import WorkflowIR
from geocompiler.workflow.patches import WorkflowPatch
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
            return WorkflowPatch.model_validate(response.payload)
        workflow = WorkflowIR.model_validate(response.payload)
    except ValidationError as error:
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
