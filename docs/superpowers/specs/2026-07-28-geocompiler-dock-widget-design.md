# GeoCompiler Dock Widget Design

## Scope

Implement TASK-005 as a native PyQt/PyQGIS dock widget. The initial surface has
only Build and Workflow views. History, Versions, and Experiments remain absent
until their backing capabilities exist.

## Goals

- Make the proposed Workflow IR more prominent than natural-language input.
- Require an explicit user approval before any execution route becomes enabled.
- Show workflow inputs, parameters, ordered steps, and declared outputs without
  recreating the QGIS Processing graph editor.
- Surface execution status and mapped failures without placing spatial semantics
  or direct Processing calls in the widget.

## Components

`WorkflowViewModel` is a pure-Python state container for a proposed
`WorkflowIR`, approval state, execution state, and mapped user-facing error.
It is the testable UI boundary: it accepts a schema-valid workflow, clears
approval when a replacement is proposed, and exposes whether execution is
allowed.

`GeoCompilerDockWidget` is a `QDockWidget` composed of two native tabs:

- **Build:** an intent field and a proposal-status action. TASK-006 will attach
  provider generation; TASK-005 exposes the command without claiming that a
  provider exists.
- **Workflow:** a compact, read-only workflow inspection tree and controls for
  approval, running a validated approved artifact, and opening QGIS Processing
  model tooling.

`GeoCompilerPlugin` owns the QGIS dock lifecycle. It adds the dock to the main
window, removes it on unload, and injects collaborators. The plugin boundary,
not the widget, will later connect approved workflows to the compiler and
runner.

## Data Flow

```text
provider or fixture -> WorkflowViewModel.set_proposal(workflow)
                    -> dock workflow inspector
user approval       -> WorkflowViewModel.approve()
approved artifact   -> future plugin execution coordinator
```

Only a `WorkflowIR` that has already passed its Pydantic graph validation can
enter the view model. The dock does not parse provider output, resolve QGIS
algorithm IDs, compile a workflow, or execute Processing directly.

## Interaction Rules

- Proposing a new workflow clears prior approval and any stale execution state.
- Run remains disabled until the current workflow is explicitly approved.
- Invalid or failed states are rendered as text associated with the workflow
  artifact; the UI does not infer a substitute operation.
- Edit opens QGIS-native Processing model tooling through an injected callback.
  It does not implement a graph editor.

## Verification

- Pure-Python view-model tests cover proposal rendering state, approval reset,
  disabled execution, progress, and mapped error state.
- QGIS/PyQt tests cover dock construction, control state, and injected action
  routing when the QGIS runtime is available.
- A QGIS 4.2.0 manual smoke creates and displays the dock, loads a fixture
  workflow, verifies approval gating, and unloads the plugin cleanly.

## Non-Goals

- Provider requests, Workflow Patch application, history conversion, version
  browsing, experiments, arbitrary code, and a custom Processing graph editor.
