from __future__ import annotations

import pytest

qgis_pyqt = pytest.importorskip("qgis.PyQt", reason="requires a QGIS PyQt runtime")

from geocompiler.plugin import GeoCompilerPlugin  # noqa: E402
from geocompiler.ui.dock import GeoCompilerDockWidget  # noqa: E402
from geocompiler.ui.view_model import ExecutionState, WorkflowViewModel  # noqa: E402
from geocompiler.workflow import GeometryKind, WorkflowInput, WorkflowIR, WorkflowStep  # noqa: E402

QApplication = qgis_pyqt.QtWidgets.QApplication
QMainWindow = qgis_pyqt.QtWidgets.QMainWindow


@pytest.fixture(scope="session", autouse=True)
def application() -> object:
    return QApplication.instance() or QApplication([])


def _workflow() -> WorkflowIR:
    return WorkflowIR(
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


def test_dock_renders_workflow_and_requires_approval_before_run() -> None:
    built: list[str] = []
    ran: list[str] = []
    edited: list[str] = []
    dock = GeoCompilerDockWidget(
        WorkflowViewModel(),
        built.append,
        lambda workflow: ran.append(workflow.id),
        lambda workflow: edited.append(workflow.id),
    )
    dock.set_proposal(_workflow())

    assert dock._workflow_tree.topLevelItem(0).text(0) == "Buffer roads"
    assert dock._run_button.isEnabled() is False
    dock._approve_button.click()
    assert dock._run_button.isEnabled() is True
    dock._run_button.click()
    dock._edit_button.click()
    dock._intent.setText("Buffer roads")
    dock._build_button.click()

    assert ran == ["buffer-roads"]
    assert edited == ["buffer-roads"]
    assert built == ["Buffer roads"]
    assert dock._view_model.execution_state is ExecutionState.SUCCEEDED


def test_dock_maps_build_callback_failure_without_changing_execution_state() -> None:
    def fail(_: str) -> None:
        raise RuntimeError("No workflow provider is configured.")

    dock = GeoCompilerDockWidget(WorkflowViewModel(), fail, lambda _: None, lambda _: None)
    dock._intent.setText("Buffer roads")
    dock._build_button.click()

    assert dock._status.text() == "No workflow provider is configured."
    assert dock._view_model.execution_state is ExecutionState.IDLE


class _Interface:
    def __init__(self) -> None:
        self.window = QMainWindow()
        self.added: list[object] = []
        self.removed: list[object] = []

    def mainWindow(self) -> object:
        return self.window

    def addDockWidget(self, _: object, dock: object) -> None:
        self.added.append(dock)

    def removeDockWidget(self, dock: object) -> None:
        self.removed.append(dock)


def test_plugin_owns_a_single_dock_and_unloads_it() -> None:
    iface = _Interface()
    plugin = GeoCompilerPlugin(iface)

    plugin.initGui()
    plugin.initGui()

    assert plugin.dock is not None
    assert iface.added == [plugin.dock]
    plugin.unload()
    assert iface.removed == iface.added
    assert plugin.dock is None
