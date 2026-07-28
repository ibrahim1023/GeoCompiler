"""Dependency-free immutable artifact serialization and validation helpers."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, fields, is_dataclass, replace
from enum import Enum
from typing import ClassVar, Self

type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]


class ArtifactValidationError(ValueError):
    """Raised when an untrusted JSON artifact does not meet its contract."""


@dataclass(frozen=True)
class FrozenArtifact:
    """Common JSON codec for explicitly validated frozen dataclasses.

    ``model_*`` aliases intentionally keep provider and plugin callers stable
    while artifacts migrate to standard-library validation.
    """

    _field_names: ClassVar[frozenset[str] | None] = None

    @classmethod
    def from_dict(cls, value: object) -> Self:
        if not isinstance(value, dict):
            raise ArtifactValidationError(f"{cls.__name__} requires an object")
        allowed = cls._field_names or frozenset(field.name for field in fields(cls))
        unknown = set(value).difference(allowed)
        if unknown:
            raise ArtifactValidationError(f"extra fields: {', '.join(sorted(unknown))}")
        try:
            return cls(**value)  # type: ignore[arg-type,call-arg]
        except (TypeError, ValueError) as error:
            if isinstance(error, ArtifactValidationError):
                raise
            raise ArtifactValidationError(str(error)) from error

    @classmethod
    def from_json(cls, payload: str) -> Self:
        try:
            value = json.loads(payload)
        except json.JSONDecodeError as error:
            raise ArtifactValidationError(f"invalid JSON: {error.msg}") from error
        return cls.from_dict(value)

    @classmethod
    def model_validate(cls, value: object) -> Self:
        return cls.from_dict(value)

    @classmethod
    def model_validate_json(cls, payload: str) -> Self:
        return cls.from_json(payload)

    def to_dict(self) -> dict[str, JsonValue]:
        value = _to_json_value(asdict(self))
        assert isinstance(value, dict)
        return value

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)

    def model_dump(self, **_: object) -> dict[str, JsonValue]:
        return self.to_dict()

    def model_dump_json(self, **_: object) -> str:
        return self.to_json()

    def model_copy(self, *, update: dict[str, object] | None = None) -> Self:
        return replace(self, **(update or {}))


def require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ArtifactValidationError(f"{label} requires a non-empty string")
    return value


def require_mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ArtifactValidationError(f"{label} requires an object")
    return dict(value)


def validate_json_value(value: object, label: str = "value") -> JsonValue:
    if value is None or isinstance(value, bool | str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ArtifactValidationError(f"{label} cannot contain a non-finite number")
        return value
    if isinstance(value, list):
        return [validate_json_value(item, label) for item in value]
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise ArtifactValidationError(f"{label} object keys must be strings")
        return {key: validate_json_value(item, label) for key, item in value.items()}
    raise ArtifactValidationError(f"{label} must be JSON-serializable")


def _to_json_value(value: object) -> JsonValue:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _to_json_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple | list):
        return [_to_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_json_value(item) for key, item in value.items()}
    return validate_json_value(value)
