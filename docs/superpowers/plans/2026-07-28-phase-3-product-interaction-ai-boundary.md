# Phase 3 Product Interaction and AI Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the native QGIS dock widget and the provider-independent,
metadata-minimizing Workflow IR/Patch boundary required by Phase 3.

**Architecture:** The dock uses a pure-Python view model so approval and
execution gating are testable without QGIS. The provider layer accepts only safe
`ProjectContext` metadata and parses only schema-valid Workflow IR or Patch
envelopes. Providers, widgets, compilers, and runners remain separate.

**Tech Stack:** Python 3.12+, Pydantic, PyQGIS/PyQt6 from QGIS 4.2.0, pytest,
and Ruff.

## Global Constraints

- Use native PyQt/PyQGIS; QGIS Processing remains the graph editor.
- Reject model-generated Python, PyQGIS, shell, XML, provider algorithm IDs,
  raw geometry, feature values, credentials, connection strings, and source
  URIs.
- Only an explicitly approved valid Workflow IR may reach future execution.
- Work stays on `phase/phase-3-product-interaction-ai-boundary`; merge only to
  `development` after verification and review. Do not change `main`.

## File Structure

- `src/geocompiler/workflow/patches.py`: atomic typed Workflow Patch models.
- `src/geocompiler/provider/`: safe request/response contracts and parsing.
- `src/geocompiler/ui/view_model.py`: workflow proposal and approval state.
- `src/geocompiler/ui/dock.py`: Build and Workflow QDockWidget views.
- `src/geocompiler/plugin.py`: QGIS dock lifecycle.
- `tests/unit/`: deterministic patches, provider, and view-model tests.
- `tests/integration/` and `scripts/`: QGIS dock tests and manual smoke.
- `tests/fixtures/provider/` and `scripts/evaluate_provider_fixtures.py`:
  deterministic semantic fixture replay.

### Task 1: Add Atomic Workflow Patches

**Files:** Create `src/geocompiler/workflow/patches.py` and
`tests/unit/test_workflow_patches.py`; modify workflow exports and interfaces.

**Produces:**

```python
class PatchOperation(BaseModel):
    type: Literal["add_parameter", "update_parameter", "insert_step", "remove_step", "update_step"]
    target_id: str | None
    payload: dict[str, JsonValue]

class WorkflowPatch(BaseModel):
    workflow_id: str
    base_version: str
    operations: list[PatchOperation]
    summary: str

def apply_patch(workflow: WorkflowIR, patch: WorkflowPatch) -> PatchResult: ...
```

- [ ] Write tests for add/update/remove/insert operations, mismatched workflow
  ID or version, duplicate IDs, invalid graphs, and all-or-nothing rollback.
- [ ] Run `python3 -m pytest tests/unit/test_workflow_patches.py -q`; expect
  collection failure before implementation.
- [ ] Apply operations to a deep-copied workflow representation and construct a
  fresh `WorkflowIR` only after every operation succeeds.
- [ ] Run focused pytest and Ruff checks; commit `feat: add atomic workflow patches`.

### Task 2: Add Provider-Safe Contracts and Parsing

**Files:** Create `src/geocompiler/provider/{__init__,contracts,normalization}.py`
and `tests/unit/test_provider_normalization.py`; modify interfaces and eval plan.

**Produces:**

```python
class LLMProvider(Protocol):
    def generate(self, request: ProviderRequest) -> ProviderResponse: ...

def build_provider_request(intent: str, context: ProjectContext) -> ProviderRequest: ...
def parse_provider_response(payload: str | dict[str, JsonValue]) -> WorkflowIR | WorkflowPatch: ...
```

- [ ] Test that normalized context contains only `ProjectContext` fields, lacks
  raw layer/source data, and provider failure cannot trigger compilation.
- [ ] Test valid workflow and patch envelopes plus malformed JSON, extra keys,
  unsafe-code-shaped payloads, and invalid artifacts.
- [ ] Run the focused test first; expect collection failure before implementation.
- [ ] Implement frozen, `extra="forbid"` request/response envelopes and parse
  only `artifact="workflow"` or `artifact="patch"` payloads.
- [ ] Run focused pytest and Ruff checks; commit `feat: add safe provider boundary`.

### Task 3: Add Deterministic Provider Fixture Evaluation

**Files:** Create provider fixture JSON files, evaluator script, and tests;
modify evaluation/testing docs and README metrics.

**Produces:**

```python
def evaluate_fixture_directory(path: Path) -> EvaluationReport: ...
```

- [ ] Add golden valid-workflow/valid-patch fixtures and invalid-schema/unsafe
  adversarial fixtures, all containing metadata only.
- [ ] Test expected parse success or structured rejection per fixture category.
- [ ] Implement sorted fixture replay without any external model call.
- [ ] Run `python3 scripts/evaluate_provider_fixtures.py --fixtures tests/fixtures/provider`.
- [ ] Commit `test: add provider fixture evaluation`.

### Task 4: Build the Approval-Gated Native Dock

**Files:** Create `src/geocompiler/ui/{__init__,view_model,dock}.py`, unit and
QGIS integration tests; modify interfaces.

**Produces:**

```python
class WorkflowViewModel:
    def set_proposal(self, workflow: WorkflowIR) -> None: ...
    def approve(self) -> None: ...
    def begin_execution(self) -> None: ...
    def finish_execution(self) -> None: ...
    def set_execution_error(self, message: str) -> None: ...
    @property
    def can_execute(self) -> bool: ...

class GeoCompilerDockWidget(QDockWidget):
    def __init__(self, view_model: WorkflowViewModel, on_build, on_run, on_edit, parent=None) -> None: ...
```

- [ ] Test proposal state, approval reset on replacement, run gating, progress,
  error state, and approval without a workflow.
- [ ] Implement the pure view model without QGIS, PyQt, provider, compiler, or
  runner imports.
- [ ] Implement Build and Workflow tabs. Render inputs, parameters, ordered
  steps, and outputs in a read-only tree; use callbacks for Build, Run, Edit.
- [ ] Test dock construction/routing with `pytest.importorskip("qgis.PyQt")`.
- [ ] Run unit tests and commit `feat: add workflow approval dock`.

### Task 5: Add Plugin Lifecycle and QGIS UI Smoke

**Files:** Create `src/geocompiler/plugin.py` and
`scripts/qgis_dock_widget_smoke.py`; modify package exports, testing docs,
progress, README, and roadmap.

**Produces:**

```python
class GeoCompilerPlugin:
    def __init__(self, iface: QgisInterface) -> None: ...
    def initGui(self) -> None: ...
    def unload(self) -> None: ...

def classFactory(iface: QgisInterface) -> GeoCompilerPlugin: ...
```

- [ ] Test a fake QGIS interface receives exactly one added and removed dock.
- [ ] Implement lifecycle ownership and injected callbacks only; no widget
  method may call Processing directly.
- [ ] Write a QGIS 4.2.0 smoke that loads the dock, injects a fixture workflow,
  verifies approval gating and callbacks, then unloads cleanly.
- [ ] Run the documented QGIS command; commit `feat: add QGIS dock lifecycle`.

### Task 6: Verify, Document, and Review Phase 3

- [ ] Run `python3 -m pytest -q`, `python3 -m ruff check .`,
  `python3 -m ruff format --check .`, and `python3 -m compileall -q src`.
- [ ] Run both QGIS smoke scripts with the QGIS 4.2.0 bundle environment.
- [ ] Run the provider fixture evaluator and record category totals.
- [ ] Update README capabilities/metrics, testing/evaluation commands, progress,
  and roadmap evidence. Keep TASK-005 and TASK-006 unchecked until independent
  review approval, then merge the phase branch into `development`.

## Self-Review

TASK-005 is covered by Tasks 4-5: native dock construction, workflow
inspection, explicit approval, execution state, callbacks, lifecycle, unit
tests, and QGIS smoke. TASK-006 is covered by Tasks 1-3: Patch atomicity, safe
provider context, strict artifact parsing, provider failure behavior, and
fixture evaluation. No task creates a direct provider-to-execution path or a
custom QGIS graph editor.
