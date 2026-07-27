"""Domain errors exposed by the deterministic workflow boundary."""


class WorkflowError(Exception):
    """Base class for errors that prevent workflow execution."""


class WorkflowGraphError(WorkflowError):
    """Raised when Workflow IR graph invariants are violated."""


class UnsupportedOperationError(WorkflowError):
    """Raised when an operation is absent from the approved registry."""


class CompatibilityError(WorkflowError):
    """Raised when validated IR is incompatible with an algorithm definition."""


class CompilerError(WorkflowError):
    """Raised when a validated workflow cannot form an executable plan."""


class ExecutionError(WorkflowError):
    """Raised when QGIS Processing fails for a mapped workflow step."""

    def __init__(self, step_id: str, algorithm_id: str, reason: str) -> None:
        self.step_id = step_id
        self.algorithm_id = algorithm_id
        self.reason = reason
        super().__init__(f"step {step_id} ({algorithm_id}) failed: {reason}")
