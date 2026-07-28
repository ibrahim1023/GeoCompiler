"""Provider-independent safe request and structured-response boundary."""

from geocompiler.provider.contracts import (
    LLMProvider,
    ProviderError,
    ProviderRequest,
    ProviderResponse,
)
from geocompiler.provider.evaluation import (
    EvaluationReport,
    FixtureResult,
    evaluate_fixture,
    evaluate_fixture_directory,
)
from geocompiler.provider.normalization import (
    build_provider_request,
    parse_provider_response,
    request_artifact,
)

__all__ = [
    "LLMProvider",
    "EvaluationReport",
    "FixtureResult",
    "ProviderError",
    "ProviderRequest",
    "ProviderResponse",
    "build_provider_request",
    "evaluate_fixture",
    "evaluate_fixture_directory",
    "parse_provider_response",
    "request_artifact",
]
