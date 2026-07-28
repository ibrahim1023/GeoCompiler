"""Pure state for the workflow proposal and approval UI boundary."""

from __future__ import annotations

from enum import StrEnum

from geocompiler.workflow.models import WorkflowIR


class ExecutionState(StrEnum):
    """Visible lifecycle states for the currently proposed workflow."""

    IDLE = "idle"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class WorkflowViewModel:
    """Own proposal, approval, and mapped execution state without UI imports."""

    def __init__(self) -> None:
        self._workflow: WorkflowIR | None = None
        self._approved = False
        self._execution_state = ExecutionState.IDLE
        self._error_message: str | None = None
        self._status_message: str | None = None

    @property
    def workflow(self) -> WorkflowIR | None:
        return self._workflow

    @property
    def approved(self) -> bool:
        return self._approved

    @property
    def execution_state(self) -> ExecutionState:
        return self._execution_state

    @property
    def error_message(self) -> str | None:
        return self._error_message

    @property
    def status_message(self) -> str | None:
        return self._status_message

    @property
    def can_execute(self) -> bool:
        return (
            self._workflow is not None
            and self._approved
            and self._execution_state is ExecutionState.IDLE
        )

    def set_proposal(self, workflow: WorkflowIR) -> None:
        self._workflow = workflow
        self._approved = False
        self._execution_state = ExecutionState.IDLE
        self._error_message = None
        self._status_message = None

    def approve(self) -> None:
        if self._workflow is None:
            raise ValueError("no workflow proposal is available for approval")
        self._approved = True

    def begin_execution(self) -> None:
        if not self.can_execute:
            raise ValueError("an approved workflow proposal is required for execution")
        self._execution_state = ExecutionState.RUNNING
        self._error_message = None
        self._status_message = None

    def finish_execution(self) -> None:
        if self._execution_state is not ExecutionState.RUNNING:
            raise ValueError("workflow execution is not running")
        self._execution_state = ExecutionState.SUCCEEDED

    def set_execution_error(self, message: str) -> None:
        if not message:
            raise ValueError("execution error message cannot be empty")
        self._execution_state = ExecutionState.FAILED
        self._error_message = message
        self._status_message = message

    def set_status_message(self, message: str) -> None:
        if not message:
            raise ValueError("status message cannot be empty")
        self._status_message = message
