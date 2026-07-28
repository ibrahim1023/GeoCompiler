"""QGIS plugin lifecycle for the GeoCompiler dock."""

from __future__ import annotations

from typing import Any

from qgis.PyQt.QtCore import Qt

from geocompiler.ui.dock import GeoCompilerDockWidget
from geocompiler.ui.view_model import WorkflowViewModel
from geocompiler.workflow.models import WorkflowIR


class GeoCompilerPlugin:
    """Own the native dock lifecycle while keeping orchestration external."""

    def __init__(self, iface: Any) -> None:
        self._iface = iface
        self._view_model = WorkflowViewModel()
        self.dock: GeoCompilerDockWidget | None = None
        self._model_designer: Any | None = None

    def initGui(self) -> None:
        if self.dock is not None:
            return
        self.dock = GeoCompilerDockWidget(
            self._view_model,
            self._build_requested,
            self._run_requested,
            self._edit_requested,
            self._iface.mainWindow(),
        )
        self._iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)

    def unload(self) -> None:
        if self._model_designer is not None:
            self._model_designer.close()
            self._model_designer = None
        if self.dock is None:
            return
        self._iface.removeDockWidget(self.dock)
        self.dock.deleteLater()
        self.dock = None

    def _build_requested(self, _: str) -> None:
        if self.dock is not None:
            self.dock.set_execution_error("No workflow provider is configured.")

    def _run_requested(self, _: WorkflowIR) -> None:
        if self.dock is not None:
            self.dock.set_execution_error("Execution orchestration is not configured.")

    def _edit_requested(self, _: WorkflowIR) -> None:
        try:
            from processing.modeler.ModelerDialog import ModelerDialog

            self._model_designer = ModelerDialog.create()
            self._model_designer.show()
        except Exception as error:
            if self.dock is not None:
                self.dock.set_execution_error(
                    f"Unable to open QGIS Processing Model Designer: {error}"
                )


def classFactory(iface: Any) -> GeoCompilerPlugin:
    """QGIS plugin entry point."""

    return GeoCompilerPlugin(iface)
