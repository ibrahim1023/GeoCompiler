# Progress

## Current Phase

Phase 4 verification is complete and awaiting review approval.

## Completed

- Product specification and bootstrap instruction inspected.
- Foundation design approved: native PyQt/PyQGIS dock widget; QGIS Processing
  remains the full model editor.
- Architecture, interfaces, root agent rules, and typed-IR registry ADR created.
- TASK-001 implemented: pure-Python Pydantic Workflow IR, JSON serialization,
  graph invariants, and unit tests.
- TASK-002 implemented: 18-operation vector-first algorithm registry,
  deterministic geometry/parameter/CRS compatibility validation, and contract
  tests.
- Workflow IR defaults and step parameters are constrained to JSON values;
  non-serializable Python objects are rejected at schema validation.
- Workflow steps require at least one input and output; registry validation uses
  topological dependency order rather than serialized step order.
- TASK-003 implementation: a metadata-only project-context adapter summarizes
  supported vector/raster layers, field schemas, CRS evidence, selections, and
  explicitly supplied safe Processing-history metadata. It excludes source
  URIs, connection strings, feature values, geometries, coordinates, and raw
  Processing commands.
- TASK-004 implementation: the compiler maps validated Workflow IR only through
  the approved registry. The runner requires explicit bindings, uses temporary
  outputs, calls only QGIS Processing, and attributes failures to the workflow
  step and approved algorithm.
- Metric compilation requires an explicit semantic-workflow-input to project-layer
  binding, which verifies bound geometry and projected CRS evidence before an
  approved algorithm can run.
- TASK-005 implementation: a native PyQt dock supports intent entry, structured
  Workflow IR inspection, explicit approval before Run becomes available,
  mapped status/errors, plugin lifecycle ownership, and access to QGIS
  Processing Model Designer.
- TASK-006 implementation: provider requests remain metadata-only, provider
  responses accept only strict Workflow IR or atomic Workflow Patch envelopes,
  and fixture replay validates golden, adversarial, and schema-failure cases
  without a provider, compiler, or QGIS call.

## Important Decisions

- Workflow IR and patches are the sole model-to-engine boundary.
- Only an approved algorithm registry may reach QGIS Processing execution.
- Default provider context contains safe project metadata only.
- Initial implementation is vector-first and conventional Python/PyQGIS.

## Known Limits and Risks

- Plugin packaging metadata, a configured provider implementation, execution
  orchestration, CI, and a type checker are not established yet.
- QGIS 4.2.0 on macOS is the supported local Phase 2 smoke runtime. Its cask
  bundles a Pydantic source/core patch mismatch and no pytest package, so the
  documented smoke script contains a test-only compatibility bootstrap; a
  packaged plugin must pin its own runtime dependencies.

## Verification and Review

- Bootstrap Task 1 verification passed: architecture and safety authorities
  contain the required QGIS-native and no-arbitrary-execution constraints.
- Bootstrap Tasks 2 and 3 verification passed: bounded roles, selective context,
  planned checks, focused skills, and the dependency-aware roadmap are present.
- Phase 1 deterministic verification passed: Ruff, full pytest suite, and
  Python compilation. Human review approval was received on 2026-07-27.
- Phase 2 deterministic verification passed: 31 tests, 1 expected QGIS-runtime
  skip, Ruff, formatting, and Python compilation.
- QGIS 4.2.0 live verification passed on 2026-07-27: the metadata-only adapter
  inspected an in-memory projected line layer, and the approved
  `native:buffer` runner returned a valid one-feature output layer.
- Human review approval for TASK-003 and TASK-004 was received on 2026-07-27.
- Phase 3 deterministic verification passed: 47 tests with 2 expected
  QGIS-runtime skips, Ruff, formatting, and Python compilation.
- Phase 3 provider fixture evaluation passed on 2026-07-28: 6/6 fixtures across
  golden, edge, adversarial, failure, and regression categories produced the
  expected validated artifact or transparent rejection.
- QGIS 4.2.0 dock smoke passed on 2026-07-28: plugin lifecycle, workflow
  approval gate, and QGIS Processing Model Designer launch/cleanup were
  verified with `scripts/qgis_dock_widget_smoke.py`.
- Independent review approval for TASK-005 and TASK-006 was received on
  2026-07-28.
- Phase 4 narrow vertical-slice verification passed its deterministic, QGIS,
  privacy, and registry-boundary checks on 2026-07-28. The verifier report
  records a no-go for the connected dock flow because no provider or execution
  orchestration is configured.

## Blocker

The connected user-facing intent-to-output path is unavailable: the dock
transparently reports that no workflow provider or execution orchestration is
configured. This is a bounded product follow-up, not a safety bypass.

## Next Task and Role

Review the Phase 4 verifier report. If accepted, define a bounded follow-up
phase for provider/orchestration integration before claiming a connected MVP
intent-to-output workflow.
