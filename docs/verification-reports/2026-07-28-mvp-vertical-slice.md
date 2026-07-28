# MVP Vertical-Slice Verification Report

**Verifier scope:** TASK-007 narrow supported vector workflow slice

**Date:** 2026-07-28

**Verdict:** Component-level slice passes. Connected user-facing
intent-to-output flow is **no-go** until provider and execution orchestration
are integrated.

## Acceptance Evidence

| Requirement | Evidence | Verdict |
| --- | --- | --- |
| Inspectable reusable workflow | `WorkflowIR` graph validation, dock tree rendering, and approval-gate tests | Pass |
| Approved execution reaches QGIS | QGIS 4.2 `native:buffer` smoke created a valid one-feature output layer | Pass |
| Registry-only Processing | Source review found `processing.run` only in `qgis/compiler.py`; compiler tests reject unsupported operations | Pass |
| Privacy-minimizing provider context | Context adapter and tests reject data sources, raw features, coordinates, and raw Processing commands | Pass |
| Transparent failures | Provider, compiler, runner, and dock tests expose structured/mapped errors | Pass |
| Connected dock intent-to-output flow | Plugin callbacks report that no provider or execution orchestration is configured | No-go |

## Commands Run

```sh
python3 -m ruff check .
python3 -m ruff format --check .
python3 -m pytest -q
python3 scripts/evaluate_provider_fixtures.py --fixtures tests/fixtures/provider
python3 -m compileall -q src
```

Results: Ruff and formatting passed; Python compilation passed; pytest reported
`47 passed, 2 skipped` (the skips require a QGIS Python runtime); the provider
fixture evaluator reported `6/6` expected outcomes across golden, edge,
adversarial, failure, and regression categories.

The documented QGIS 4.2 environment also ran:

```sh
scripts/qgis_vertical_slice_smoke.py
scripts/qgis_dock_widget_smoke.py
```

Both passed. The first verified metadata inspection, compilation, and a real
`native:buffer` output layer. The second verified dock lifecycle, explicit
approval gating, transparent unavailable-provider/execution states, and QGIS
Processing Model Designer access.

## Boundary Review

- `provider/normalization.py` constructs metadata-only requests and validates
  structured Workflow IR or Patch artifacts. It neither compiles nor executes.
- `qgis/compiler.py` is the sole source location invoking `processing.run`.
  The runner receives only compiled registry-resolved algorithms.
- `qgis/context.py` summarizes layer metadata without reading sources or raw
  features. The adapter tests make such reads fail.
- `ui/dock.py` owns display and approval state only. Execution is an injected
  callback; it contains no QGIS Processing invocation.

## Bounded Finding

**Major: connected product path unavailable.**

Reproduction: open the dock, enter an intent, and select **Build Workflow**.
The plugin displays `No workflow provider is configured.` Injecting and
approving a workflow then selecting **Run** displays `Execution orchestration
is not configured.` Both messages are transparent and preserve the safety
boundary, but the user cannot yet create and execute a workflow through the
dock.

This verifier phase makes no implementation change. A follow-up phase must add
explicit provider and execution orchestration while preserving validation,
approval, registry, and privacy controls.

## Review Artifact

The accompanying self-contained HTML explanation is generated outside the
repository at `/tmp/2026-07-28-explanation-phase-4-mvp-verification.html`.
Its file size, inline-only asset policy, table-of-contents targets, five quiz
controls, and `<pre>` whitespace styling were statically validated. Automated
Chromium validation could not launch because the host sandbox denied its macOS
Mach-port registration; this report does not claim a browser automation pass.
