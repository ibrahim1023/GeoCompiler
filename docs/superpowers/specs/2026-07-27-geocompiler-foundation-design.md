# GeoCompiler Engineering Foundation Design

## Purpose

Create a lean, durable engineering foundation for GeoCompiler without
implementing product functionality. Future sessions must be able to take one
bounded task, load only the context it needs, verify its outcome, record
evidence, and stop.

## Product Constraints

GeoCompiler is a conventional QGIS Python plugin. Its primary artifact is an
editable QGIS Processing workflow, not a chat response or an autonomous QGIS
agent.

The foundation preserves these product invariants:

- The model interprets intent and proposes structured changes only.
- Typed Workflow IR, validation, algorithm resolution, compilation, and QGIS
  execution are deterministic components.
- Generated output can resolve only through an approved operation registry;
  it must never become arbitrary Python execution.
- Remote providers receive only the minimum necessary project metadata by
  default, never raw geometries or full feature data without explicit future
  product support.
- The MVP is vector-first and compiles a deliberately small supported set of
  QGIS Processing operations.

## Documentation Structure

The product specification remains the authority for product behavior. The
following focused artifacts supplement it:

| Artifact | Authority |
| --- | --- |
| `AGENTS.md` | Stable repository rules and context-loading order |
| `docs/architecture.md` | Component boundaries, data flow, invariants, trust boundaries |
| `docs/interfaces.md` | Stable internal contracts and validation boundaries |
| `docs/agent-system.md` | Development-role graph, handoffs, and bounded loops |
| `docs/testing-strategy.md` | Deterministic test layers and commands/status |
| `docs/evaluation-plan.md` | Future probabilistic workflow-planning evals |
| `docs/context-map.md` | Task-to-context and verification routing |
| `docs/progress.md` | Compact cross-thread execution memory |
| `docs/decisions/` | Material, reversible architecture decisions |
| `task.md` | Active dependency-aware implementation roadmap |

No separate data-model, security, reliability, or known-limitations documents
will be created. Their initial content is small and belongs respectively in
the architecture, interface, testing, evaluation, and progress documents.

## Architecture

The implementation will use six boundaries:

1. UI: a native PyQt/PyQGIS dock widget and workflow-facing screens. It
   presents proposals, previews, execution state, and QGIS-native model
   access; it does not own spatial semantics. QGIS Processing model tooling
   remains the full editor. Qt Designer may later define stable widget layouts,
   but QML, embedded web applications, and a standalone client are out of
   scope for the MVP.
2. Project context: deterministic PyQGIS inspection of loaded layers, schema,
   geometry, CRS, and processing history. It produces metadata safe to pass to
   an LLM provider.
3. AI boundary: provider-independent prompting and structured response parsing.
   Its only accepted results are schema-valid Workflow IR or Workflow Patch
   artifacts.
4. Workflow core: pure-Python Pydantic models, graph and semantic validation,
   patch application, diffs, and persistence metadata. It has no QGIS or
   provider dependency where practical.
5. Compiler and execution: an approved algorithm registry resolves valid IR
   operations into QGIS Processing model definitions and runs them through
   QGIS APIs. Unsupported or incompatible operations fail explicitly.
6. Observability: structured development events with no raw geographic feature
   data by default.

The decisive contract is:

`model output -> Pydantic schema -> workflow validation -> approved registry -> QGIS Processing`

This sequence keeps probabilistic interpretation outside deterministic
execution and makes the core independently testable without QGIS or a model
provider.

## Development Graph

The default task flow is intentionally small:

`task -> implementer -> deterministic checks -> reviewer when material -> final verification -> progress update`

An architect role is required only for material changes to the architecture,
contracts, persistence, public APIs, or trust boundaries. Specialist roles are
not created until recurring work justifies them. Parallel work is allowed only
when the task graph identifies independent files and settled contracts.

Every task defines owner, scope, authority, acceptance criteria, verification,
output artifacts, and success/failure routing. After three materially distinct
failed attempts at the same blocker, a worker preserves evidence in
`docs/progress.md` and stops for human direction.

## Verification and Evaluation

The first implementation milestones use deterministic tests before AI evals:

- unit and schema tests for Workflow IR, graph validation, patches, and the
  algorithm registry;
- QGIS integration tests for context inspection, compilation, and Processing
  execution once a reproducible QGIS test runtime exists;
- fixture-based semantic evaluations for model-produced Workflow IR only after
  the deterministic contract exists.

The bootstrap must not invent executable commands because there is no code,
test runner, CI configuration, or Git repository yet. Documents will mark
commands as planned until the first scaffold establishes them.

## First Implementation Task

`TASK-001` is a pure-Python Workflow IR foundation: establish package layout,
Pydantic schemas, JSON round trips, graph invariants, and focused tests. It is
the recommended first task because it locks the trusted deterministic boundary
before PyQGIS, providers, UI, or persistence expand the surface area.

It should use a normal Codex implementer session with a bounded inner
test/fix/verify loop. It does not need an isolated worktree or reviewer thread
unless the repository is initialized and the change becomes larger than the
defined task scope.

## Assumptions

- QGIS plugin conventions and PyQGIS runtime details will be selected during
  TASK-002, after inspecting the target QGIS version and packaging approach.
- The plugin uses Python, PyQGIS, PyQt, Pydantic, pytest, and JSON as stated in
  the product specification; no web backend or database is assumed.
- The repository will be initialized as Git before product implementation, but
  this bootstrap does not create a repository or make a commit.
