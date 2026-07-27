"""QGIS-bound adapters with import-safe public contracts."""

from geocompiler.qgis.context import (
    FieldSummary,
    LayerSummary,
    ProcessingHistoryEntry,
    ProjectContext,
    QgisProjectContextAdapter,
)

__all__ = [
    "FieldSummary",
    "LayerSummary",
    "ProcessingHistoryEntry",
    "ProjectContext",
    "QgisProjectContextAdapter",
]
