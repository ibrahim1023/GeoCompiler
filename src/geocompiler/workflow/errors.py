"""Domain errors exposed by the deterministic workflow boundary."""


class WorkflowError(Exception):
    """Base class for errors that prevent workflow execution."""


class WorkflowGraphError(WorkflowError):
    """Raised when Workflow IR graph invariants are violated."""


class UnsupportedOperationError(WorkflowError):
    """Raised when an operation is absent from the approved registry."""


class CompatibilityError(WorkflowError):
    """Raised when validated IR is incompatible with an algorithm definition."""
