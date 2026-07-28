from __future__ import annotations

import pytest

qgis_pyqt = pytest.importorskip("qgis.PyQt", reason="requires a QGIS PyQt runtime")

from geocompiler.ui.dock import GeoCompilerDockWidget  # noqa: E402
from geocompiler.ui.view_model import WorkflowViewModel  # noqa: E402
from geocompiler.workflow import GeometryKind, WorkflowInput, WorkflowIR, WorkflowStep  # noqa: E402

QApplication = qgis_pyqt.QtWidgets.QApplication


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
