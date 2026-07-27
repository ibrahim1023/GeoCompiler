# Interfaces and Contracts

## Artifact Classes

| Class | Producer | Acceptance condition |
| --- | --- | --- |
| Model-generated | LLM provider | Strict structured-output schema parses |
| Deterministically validated | Workflow core and registry | Schema, graph, compatibility, CRS, and operation checks pass |
| Human-approved | UI user action | Proposed creation or patch is explicitly accepted |
| Executable | QGIS compiler | Validated IR resolves only to approved QGIS Processing algorithms |

## Workflow Domain

The first implementation defines these Pydantic-compatible models. The field
names are stable internal contracts; version changes require an ADR or a
contract-migration task.

```python
class WorkflowInput:
    id: str
    title: str
    kind: str  # vector_point | vector_line | vector_polygon | raster
    required: bool = True

class WorkflowParameter:
    id: str
    title: str
    kind: str  # number | integer | string | boolean | distance | area
    default: object
    unit: str | None = None

class WorkflowStep:
    id: str
    operation: str
    inputs: dict[str, str]
    parameters: dict[str, object]
    outputs: dict[str, str]

class WorkflowIR:
    schema_version: str
    id: str
    name: str
    inputs: list[WorkflowInput]
    parameters: list[WorkflowParameter]
    steps: list[WorkflowStep]
    outputs: dict[str, str]
```

`WorkflowIR` is a directed acyclic graph. IDs are unique, references resolve,
declared outputs exist, parameter values match their declared kind and unit,
and metric operations receive CRS-safe inputs or an explicit reproject step.

## Editing Contract

```python
class PatchOperation:
    type: str  # add_parameter | update_parameter | insert_step | remove_step | update_step
    target_id: str | None
    payload: dict[str, object]

class WorkflowPatch:
    workflow_id: str
    base_version: str
    operations: list[PatchOperation]
    summary: str
```

Patch application is deterministic, atomic, and produces either a validated new
Workflow IR plus a semantic diff or structured validation errors. The editor
does not silently regenerate an unrelated workflow.

## Compiler Contract

```python
class AlgorithmDefinition:
    operation: str
    qgis_algorithm_id: str
    input_kinds: dict[str, set[str]]
    parameters: dict[str, str]
    outputs: dict[str, str]
    requires_projected_crs: bool = False

class QgisCompiler:
    def compile(self, workflow: WorkflowIR, context: ProjectContext) -> CompiledWorkflow: ...
```

The registry is the allow-list. `QgisCompiler` may compile only operations with
an `AlgorithmDefinition`; it never accepts provider-specific algorithm IDs or
model-generated QGIS XML as an execution request.

## Project and Provider Contracts

```python
class ProjectContext:
    layers: list[LayerSummary]
    selected_layer_ids: list[str]
    processing_history: list[ProcessingHistoryEntry]

class LLMProvider:
    def generate_workflow(self, intent: str, context: ProjectContext) -> WorkflowIR: ...
    def modify_workflow(self, instruction: str, workflow: WorkflowIR, context: ProjectContext) -> WorkflowPatch: ...
```

`ProjectContext` contains metadata only by default: layer identity, geometry
type, CRS, fields, field types, and safe capability summaries. Provider adapters
must expose whether an external request is being made.

## Error Contract

| Error kind | Meaning | Required response |
| --- | --- | --- |
| `schema_error` | Output cannot parse to a contract | Reject before workflow handling |
| `graph_error` | Duplicate IDs, unresolved refs, cycle, or missing output | Show node-level validation error |
| `compatibility_error` | Geometry, field, CRS, or parameter incompatibility | Explain expected and available values |
| `unsupported_operation` | No approved registry entry | Preserve semantic request and report unsupported capability |
| `compiler_error` | Model generation/resolution cannot proceed | Map to step and algorithm when known |
| `execution_error` | QGIS Processing failed | Preserve QGIS reason and affected node |
