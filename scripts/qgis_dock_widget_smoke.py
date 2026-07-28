"""Run the Phase 3 native QGIS dock smoke test."""

from __future__ import annotations

import os

from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QMainWindow

from geocompiler.plugin import GeoCompilerPlugin  # noqa: E402
from geocompiler.workflow import GeometryKind, WorkflowInput, WorkflowIR, WorkflowStep  # noqa: E402


class SmokeInterface:
    def __init__(self, window: QMainWindow) -> None:
        self._window = window
        self.added: list[object] = []
        self.removed: list[object] = []

    def mainWindow(self) -> QMainWindow:
        return self._window

    def addDockWidget(self, _: object, dock: object) -> None:
        self.added.append(dock)

    def removeDockWidget(self, dock: object) -> None:
        self.removed.append(dock)


def main() -> None:
    prefix_path = os.environ.get("QGIS_PREFIX_PATH")
    if prefix_path:
        QgsApplication.setPrefixPath(prefix_path, True)
    application = QgsApplication([], True)
    application.initQgis()
    window = QMainWindow()
    iface = SmokeInterface(window)
    plugin = GeoCompilerPlugin(iface)
    try:
        plugin.initGui()
        assert plugin.dock is not None
        assert iface.added == [plugin.dock]
        plugin.dock._intent.setText("Buffer roads")
        plugin.dock._build_button.click()
        assert plugin.dock._view_model.error_message is None
        assert plugin.dock._view_model.status_message == "No workflow provider is configured."
        workflow = WorkflowIR(
            schema_version="1.0",
            id="buffer-roads",
            name="Buffer roads",
            inputs=[WorkflowInput(id="roads", title="Roads", kind=GeometryKind.LINE)],
            parameters=[],
            steps=[
                WorkflowStep(
                    id="buffer",
                    operation="buffer",
                    inputs={"INPUT": "roads"},
                    parameters={"DISTANCE": 500},
                    outputs={"OUTPUT": "buffered_roads"},
                )
            ],
            outputs={"result": "buffered_roads"},
        )
        plugin.dock.set_proposal(workflow)
        assert plugin.dock._run_button.isEnabled() is False
        plugin.dock._approve_button.click()
        assert plugin.dock._run_button.isEnabled() is True
        plugin.dock._run_button.click()
        assert plugin.dock._view_model.error_message == "Execution orchestration is not configured."
        plugin.dock._edit_button.click()
        assert plugin.dock._view_model.error_message == "Execution orchestration is not configured."
        plugin.unload()
        assert iface.removed == iface.added
        print("QGIS dock widget smoke test passed")
    finally:
        application.exitQgis()


if __name__ == "__main__":
    main()
