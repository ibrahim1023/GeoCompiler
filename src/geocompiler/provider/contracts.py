"""Strict provider-facing artifact contracts."""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class ProviderRequest(BaseModel):
    """A metadata-only request sent to a configured workflow provider."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    intent: str = Field(min_length=1)
    context: dict[str, JsonValue]


class ProviderResponse(BaseModel):
    """A strict envelope around one proposed workflow artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact: Literal["workflow", "patch"]
    payload: dict[str, JsonValue]


class LLMProvider(Protocol):
    """A provider may propose artifacts but never receives execution access."""

    def generate(self, request: ProviderRequest) -> ProviderResponse: ...


class ProviderError(Exception):
    """Raised when a provider cannot return a usable proposed artifact."""
