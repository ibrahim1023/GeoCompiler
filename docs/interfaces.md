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
every step declares at least one input and output, parameter values match their
declared kind and unit, and metric operations receive CRS-safe inputs or an
explicit reproject step.
Defaults and step parameters are JSON values only, so a validated IR can always
cross the provider, persistence, and compiler boundaries without Python object
serialization.

Steps may be serialized in any order. Consumers must use the validated
dependency order rather than assuming the list order is executable order.

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
    output_kinds: dict[str, str]
    requires_projected_crs: bool = False

class QgisCompiler:
    def compile(self, workflow: WorkflowIR, context: ProjectContext) -> CompiledWorkflow: ...
```

The registry is the allow-list. `QgisCompiler` may compile only operations with
an `AlgorithmDefinition`; it never accepts provider-specific algorithm IDs or
model-generated QGIS XML as an execution request.

Compilation requires explicit semantic-workflow-input to active-project-layer
bindings when their IDs differ. It validates each bound layer's geometry and
CRS evidence before registry validation, so a metric operation cannot proceed
with unknown or geographic CRS evidence. `CompiledWorkflow` retains only registry-resolved algorithm IDs, symbolic input
and output references, and typed workflow defaults. `QgisWorkflowRunner`
requires explicit input bindings at execution time, maps every declared output
to `TEMPORARY_OUTPUT`, and calls only `processing.run`. It rejects unknown or
missing bindings and parameter overrides, and maps QGIS failures to the
workflow-step ID and approved algorithm ID.

`SpatialContext` supplies deterministic CRS properties keyed by workflow input
or intermediate-output reference. The Phase 1 registry rejects metric operations
when a referenced input is explicitly known to use a geographic CRS; the future
project-context adapter supplies that evidence.

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

The QGIS adapter exposes supported vector and raster layers only. Each
`LayerSummary` contains an ID, display name, layer family, optional vector
geometry kind, CRS auth ID, conservative projected-CRS evidence, field names
and provider-declared types, and aggregate feature/selection counts. It never
includes a data-source URI, connection string, feature attribute value,
geometry, coordinate, or Processing Python command. `ProcessingHistoryEntry`
contains only an algorithm ID and display title supplied through the safe
history interface; unknown history records are rejected rather than serialized.

## Error Contract

| Error kind | Meaning | Required response |
| --- | --- | --- |
| `schema_error` | Output cannot parse to a contract | Reject before workflow handling |
| `graph_error` | Duplicate IDs, unresolved refs, cycle, or missing output | Show node-level validation error |
| `compatibility_error` | Geometry, field, CRS, or parameter incompatibility | Explain expected and available values |
| `unsupported_operation` | No approved registry entry | Preserve semantic request and report unsupported capability |
| `compiler_error` | Model generation/resolution cannot proceed | Map to step and algorithm when known |
| `execution_error` | QGIS Processing failed | Preserve QGIS reason and affected node |
