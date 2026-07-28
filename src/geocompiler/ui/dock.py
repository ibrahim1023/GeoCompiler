"""Native QGIS dock widget for workflow inspection and explicit approval."""

from __future__ import annotations

from collections.abc import Callable

from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from geocompiler.ui.view_model import ExecutionState, WorkflowViewModel
from geocompiler.workflow.models import WorkflowIR


class GeoCompilerDockWidget(QDockWidget):
    """A workflow-first dock that never invokes QGIS Processing directly."""

    def __init__(
        self,
        view_model: WorkflowViewModel,
        on_build: Callable[[str], None],
        on_run: Callable[[WorkflowIR], None],
        on_edit: Callable[[WorkflowIR], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("GeoCompiler", parent)
        self._view_model = view_model
        self._on_build = on_build
        self._on_run = on_run
        self._on_edit = on_edit
        self._intent = QLineEdit()
        self._build_button = QPushButton("Build Workflow")
        self._workflow_tree = QTreeWidget()
        self._status = QLabel()
        self._approve_button = QPushButton("Approve")
        self._run_button = QPushButton("Run")
        self._edit_button = QPushButton("Open in Processing")
        self._build_ui()
        self._refresh()

    def set_proposal(self, workflow: WorkflowIR) -> None:
        """Display a validated proposal and reset the explicit approval gate."""

        self._view_model.set_proposal(workflow)
        self._refresh()

    def set_execution_error(self, message: str) -> None:
        """Display a mapped execution error supplied by an external coordinator."""

        self._view_model.set_execution_error(message)
        self._refresh()

    def _build_ui(self) -> None:
        tabs = QTabWidget()
        tabs.addTab(self._build_tab(), "Build")
        tabs.addTab(self._workflow_tab(), "Workflow")
        self.setWidget(tabs)
        self.setObjectName("GeoCompilerDockWidget")

    def _build_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("Describe the spatial analysis to turn into a workflow."))
        self._intent.setPlaceholderText("Describe an analysis")
        layout.addWidget(self._intent)
        layout.addWidget(self._build_button)
        layout.addStretch(1)
        self._build_button.clicked.connect(self._build_requested)
        return tab

    def _workflow_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self._workflow_tree.setHeaderLabels(["Workflow", "Details"])
        self._workflow_tree.setRootIsDecorated(True)
        layout.addWidget(self._workflow_tree)
        layout.addWidget(self._status)
        controls = QHBoxLayout()
        controls.addWidget(self._approve_button)
        controls.addWidget(self._run_button)
        controls.addWidget(self._edit_button)
        layout.addLayout(controls)
        self._approve_button.clicked.connect(self._approve_requested)
        self._run_button.clicked.connect(self._run_requested)
        self._edit_button.clicked.connect(self._edit_requested)
        return tab

    def _build_requested(self) -> None:
        intent = self._intent.text().strip()
        if intent:
            self._on_build(intent)

    def _approve_requested(self) -> None:
        self._view_model.approve()
        self._refresh()

    def _run_requested(self) -> None:
        workflow = self._view_model.workflow
        if workflow is None:
            return
        self._view_model.begin_execution()
        self._refresh()
        try:
            self._on_run(workflow)
        except Exception as error:
            self._view_model.set_execution_error(str(error))
            self._refresh()

    def _edit_requested(self) -> None:
        workflow = self._view_model.workflow
        if workflow is not None:
            self._on_edit(workflow)

    def _refresh(self) -> None:
        workflow = self._view_model.workflow
        self._workflow_tree.clear()
        if workflow is not None:
            root = QTreeWidgetItem([workflow.name, workflow.id])
            self._workflow_tree.addTopLevelItem(root)
            self._add_inputs(root, workflow)
            self._add_parameters(root, workflow)
            self._add_steps(root, workflow)
            self._add_outputs(root, workflow)
            root.setExpanded(True)
        self._approve_button.setEnabled(workflow is not None and not self._view_model.approved)
        self._run_button.setEnabled(self._view_model.can_execute)
        self._edit_button.setEnabled(workflow is not None)
        self._status.setText(self._status_text())

    def _add_inputs(self, root: QTreeWidgetItem, workflow: WorkflowIR) -> None:
        group = QTreeWidgetItem(["Inputs", ""])
        root.addChild(group)
        for input_ in workflow.inputs:
            group.addChild(QTreeWidgetItem([input_.title, input_.kind.value]))

    def _add_parameters(self, root: QTreeWidgetItem, workflow: WorkflowIR) -> None:
        group = QTreeWidgetItem(["Parameters", ""])
        root.addChild(group)
        for parameter in workflow.parameters:
            group.addChild(QTreeWidgetItem([parameter.title, str(parameter.default)]))

    def _add_steps(self, root: QTreeWidgetItem, workflow: WorkflowIR) -> None:
        group = QTreeWidgetItem(["Steps", ""])
        root.addChild(group)
        for step in workflow.steps_in_dependency_order:
            group.addChild(QTreeWidgetItem([step.id, step.operation]))

    def _add_outputs(self, root: QTreeWidgetItem, workflow: WorkflowIR) -> None:
        group = QTreeWidgetItem(["Outputs", ""])
        root.addChild(group)
        for name, reference in workflow.outputs.items():
            group.addChild(QTreeWidgetItem([name, reference]))

    def _status_text(self) -> str:
        if self._view_model.error_message:
            return self._view_model.error_message
        if self._view_model.execution_state is ExecutionState.RUNNING:
            return "Running approved workflow"
        if self._view_model.execution_state is ExecutionState.SUCCEEDED:
            return "Workflow completed"
        if self._view_model.approved:
            return "Workflow approved"
        if self._view_model.workflow is not None:
            return "Review and approve the workflow before running it"
        return "No workflow proposal"
