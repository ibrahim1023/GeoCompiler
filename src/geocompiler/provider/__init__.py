"""Provider-independent safe request and structured-response boundary."""

from geocompiler.provider.contracts import LLMProvider, ProviderRequest, ProviderResponse
from geocompiler.provider.evaluation import (
    FixtureResult,
    evaluate_fixture,
    evaluate_fixture_directory,
)
from geocompiler.provider.normalization import build_provider_request, parse_provider_response

__all__ = [
    "LLMProvider",
    "FixtureResult",
    "ProviderRequest",
    "ProviderResponse",
    "build_provider_request",
    "evaluate_fixture",
    "evaluate_fixture_directory",
    "parse_provider_response",
]
