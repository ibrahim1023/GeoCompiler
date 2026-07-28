"""Public Workflow IR and approved-registry interfaces."""

from geocompiler.workflow.errors import (
    CompatibilityError,
    CompilerError,
    ExecutionError,
    UnsupportedOperationError,
    WorkflowError,
    WorkflowGraphError,
)
from geocompiler.workflow.models import (
    GeometryKind,
    ParameterKind,
    WorkflowInput,
    WorkflowIR,
    WorkflowParameter,
    WorkflowStep,
)
from geocompiler.workflow.patches import PatchOperation, PatchResult, WorkflowPatch, apply_patch
from geocompiler.workflow.registry import (
    AlgorithmDefinition,
    AlgorithmRegistry,
    ParameterDefinition,
    SpatialContext,
    default_algorithm_registry,
)

__all__ = [
    "AlgorithmDefinition",
    "AlgorithmRegistry",
    "CompilerError",
    "CompatibilityError",
    "ExecutionError",
    "GeometryKind",
    "ParameterDefinition",
    "ParameterKind",
    "SpatialContext",
    "UnsupportedOperationError",
    "WorkflowGraphError",
    "WorkflowError",
    "WorkflowIR",
    "WorkflowInput",
    "WorkflowParameter",
    "WorkflowStep",
    "PatchOperation",
    "PatchResult",
    "WorkflowPatch",
    "apply_patch",
    "default_algorithm_registry",
]
