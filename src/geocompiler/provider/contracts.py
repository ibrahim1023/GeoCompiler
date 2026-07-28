"""Strict provider-facing artifact contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from geocompiler.workflow.serialization import (
    ArtifactValidationError,
    FrozenArtifact,
    JsonValue,
    require_mapping,
    require_string,
    validate_json_value,
)


@dataclass(frozen=True)
class ProviderRequest(FrozenArtifact):
    """A metadata-only request sent to a configured workflow provider."""

    intent: str
    context: dict[str, JsonValue]

    def __post_init__(self) -> None:
        require_string(self.intent, "provider intent")
        context = require_mapping(self.context, "provider context")
        normalized = {
            key: validate_json_value(value, "provider context") for key, value in context.items()
        }
        object.__setattr__(self, "context", normalized)


@dataclass(frozen=True)
class ProviderResponse(FrozenArtifact):
    """A strict envelope around one proposed workflow artifact."""

    artifact: Literal["workflow", "patch"]
    payload: dict[str, JsonValue]

    def __post_init__(self) -> None:
        if self.artifact not in {"workflow", "patch"}:
            raise ArtifactValidationError("provider artifact must be workflow or patch")
        payload = require_mapping(self.payload, "provider payload")
        normalized = {
            key: validate_json_value(value, "provider payload") for key, value in payload.items()
        }
        object.__setattr__(self, "payload", normalized)


def provider_response_schema() -> dict[str, JsonValue]:
    """Return the strict JSON Schema used for structured provider responses."""

    non_empty_string: dict[str, JsonValue] = {"type": "string", "minLength": 1}
    workflow = {
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "id", "name", "inputs", "parameters", "steps", "outputs"],
        "properties": {
            "schema_version": non_empty_string,
            "id": non_empty_string,
            "name": non_empty_string,
            "inputs": {"type": "array"},
            "parameters": {"type": "array"},
            "steps": {"type": "array"},
            "outputs": {"type": "object", "minProperties": 1},
        },
    }
    patch = {
        "type": "object",
        "additionalProperties": False,
        "required": ["workflow_id", "base_version", "operations", "summary"],
        "properties": {
            "workflow_id": non_empty_string,
            "base_version": non_empty_string,
            "summary": non_empty_string,
            "operations": {"type": "array"},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["artifact", "payload"],
        "properties": {
            "artifact": {"enum": ["workflow", "patch"]},
            "payload": {"oneOf": [workflow, patch]},
        },
    }


class LLMProvider(Protocol):
    """A provider may propose artifacts but never receives execution access."""

    def generate(self, request: ProviderRequest) -> ProviderResponse: ...


class ProviderError(Exception):
    """Raised when a provider cannot return a usable proposed artifact."""
