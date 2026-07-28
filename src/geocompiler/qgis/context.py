"""Privacy-minimizing inspection of the active QGIS project."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from geocompiler.workflow.registry import SpatialContext
from geocompiler.workflow.serialization import (
    ArtifactValidationError,
    FrozenArtifact,
    require_string,
)


class LayerKind(StrEnum):
    """Supported QGIS layer families exposed to GeoCompiler."""

    VECTOR = "vector"
    RASTER = "raster"


@dataclass(frozen=True)
class FieldSummary(FrozenArtifact):
    """A field name and provider-declared type, without any field values."""

    name: str
    type_name: str

    def __post_init__(self) -> None:
        require_string(self.name, "field name")
        require_string(self.type_name, "field type name")


@dataclass(frozen=True)
class LayerSummary(FrozenArtifact):
    """Safe layer metadata suitable for deterministic validation or providers."""

    id: str
    name: str
    kind: LayerKind
    geometry_kind: str | None = None
    crs_auth_id: str | None = None
    is_projected: bool | None = None
    fields: tuple[FieldSummary, ...] = ()
    feature_count: int | None = None
    selected_feature_count: int | None = None

    def __post_init__(self) -> None:
        require_string(self.id, "layer id")
        require_string(self.name, "layer name")
        if not isinstance(self.kind, LayerKind):
            object.__setattr__(self, "kind", LayerKind(self.kind))
        fields = tuple(
            item if isinstance(item, FieldSummary) else FieldSummary.from_dict(item)
            for item in self.fields
        )
        object.__setattr__(self, "fields", fields)
        counts = (
            ("feature_count", self.feature_count),
            ("selected_feature_count", self.selected_feature_count),
        )
        for label, count in counts:
            invalid = not isinstance(count, int) or isinstance(count, bool) or count < 0
            if count is not None and invalid:
                raise ArtifactValidationError(f"{label} must be a non-negative integer")


@dataclass(frozen=True)
class ProcessingHistoryEntry(FrozenArtifact):
    """A safe summary of a Processing operation, never its Python command."""

    algorithm_id: str
    title: str

    def __post_init__(self) -> None:
        require_string(self.algorithm_id, "history algorithm id")
        require_string(self.title, "history title")


@dataclass(frozen=True)
class ProjectContext(FrozenArtifact):
    """The metadata-only project view used by GeoCompiler boundaries."""

    layers: tuple[LayerSummary, ...] = ()
    selected_layer_ids: tuple[str, ...] = ()
    processing_history: tuple[ProcessingHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        layers = tuple(
            item if isinstance(item, LayerSummary) else LayerSummary.from_dict(item)
            for item in self.layers
        )
        selected_layer_ids = tuple(
            require_string(item, "selected layer id") for item in self.selected_layer_ids
        )
        processing_history = tuple(
            item
            if isinstance(item, ProcessingHistoryEntry)
            else ProcessingHistoryEntry.from_dict(item)
            for item in self.processing_history
        )
        object.__setattr__(self, "layers", layers)
        object.__setattr__(self, "selected_layer_ids", selected_layer_ids)
        object.__setattr__(self, "processing_history", processing_history)

    def spatial_context(self) -> SpatialContext:
        """Return only CRS evidence needed by deterministic workflow validation."""

        return SpatialContext(
            projected_references={
                layer.id: layer.is_projected
                for layer in self.layers
                if layer.is_projected is not None
            }
        )


class QgisProjectContextAdapter:
    """Inspect loaded QGIS layers without reading features or data sources."""

    def inspect(
        self,
        project: Any | None = None,
        *,
        processing_history: Iterable[object] = (),
    ) -> ProjectContext:
        """Build a deterministic context from a ``QgsProject`` or its singleton."""

        if project is None:
            project = _active_project()
        layers_by_id = project.mapLayers()
        layers = tuple(
            summary
            for _, layer in sorted(layers_by_id.items())
            if (summary := _summarize_layer(layer)) is not None
        )
        selected_layer_ids = tuple(
            layer.id for layer in layers if (layer.selected_feature_count or 0) > 0
        )
        return ProjectContext(
            layers=layers,
            selected_layer_ids=selected_layer_ids,
            processing_history=tuple(_summarize_history(entry) for entry in processing_history),
        )


def _active_project() -> Any:
    try:
        from qgis.core import QgsProject
    except ImportError as error:  # pragma: no cover - only exercised outside QGIS.
        raise RuntimeError("PyQGIS is required to inspect the active QGIS project") from error
    return QgsProject.instance()


def _summarize_layer(layer: object) -> LayerSummary | None:
    kind = _layer_kind(layer)
    if kind is None:
        return None
    crs = layer.crs()
    is_projected = _is_projected(crs)
    fields = _field_summaries(layer) if kind is LayerKind.VECTOR else ()
    return LayerSummary(
        id=str(layer.id()),
        name=str(layer.name()),
        kind=kind,
        geometry_kind=_geometry_kind(layer) if kind is LayerKind.VECTOR else None,
        crs_auth_id=_value_or_none(crs, "authid"),
        is_projected=is_projected,
        fields=fields,
        feature_count=_optional_count(layer, "featureCount"),
        selected_feature_count=(
            _optional_count(layer, "selectedFeatureCount") if kind is LayerKind.VECTOR else None
        ),
    )


def _layer_kind(layer: object) -> LayerKind | None:
    type_name = _enum_name(layer.type())
    class_name = type(layer).__name__.lower()
    if "vector" in type_name or "vector" in class_name:
        return LayerKind.VECTOR
    if "raster" in type_name or "raster" in class_name:
        return LayerKind.RASTER
    return None


def _geometry_kind(layer: object) -> str | None:
    name = _enum_name(layer.geometryType())
    if "point" in name:
        return "vector_point"
    if "line" in name or "curve" in name:
        return "vector_line"
    if "polygon" in name or "surface" in name:
        return "vector_polygon"
    return None


def _is_projected(crs: object) -> bool | None:
    crs_type = _enum_name(_call_or_none(crs, "type"))
    if "projected" in crs_type:
        return True
    if "geographic" in crs_type or _bool_or_none(crs, "isGeographic") is True:
        return False
    return None


def _field_summaries(layer: object) -> tuple[FieldSummary, ...]:
    return tuple(
        FieldSummary(name=str(field.name()), type_name=str(field.typeName()))
        for field in layer.fields()
    )


def _summarize_history(entry: object) -> ProcessingHistoryEntry:
    return ProcessingHistoryEntry(
        algorithm_id=_history_value(entry, "algorithm_id", "algorithmId"),
        title=_history_value(entry, "title", "displayName"),
    )


def _history_value(entry: object, mapping_key: str, method_name: str) -> str:
    if isinstance(entry, Mapping):
        value = entry.get(mapping_key)
    else:
        value = _call_or_none(entry, method_name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"processing history entry requires {mapping_key}")
    return value


def _enum_name(value: object) -> str:
    return str(getattr(value, "name", value)).lower()


def _call_or_none(value: object, method_name: str) -> object | None:
    method = getattr(value, method_name, None)
    return method() if callable(method) else None


def _value_or_none(value: object, method_name: str) -> str | None:
    result = _call_or_none(value, method_name)
    return str(result) if result else None


def _bool_or_none(value: object, method_name: str) -> bool | None:
    result = _call_or_none(value, method_name)
    return result if isinstance(result, bool) else None


def _optional_count(layer: object, method_name: str) -> int | None:
    value = _call_or_none(layer, method_name)
    return value if isinstance(value, int) and value >= 0 else None
