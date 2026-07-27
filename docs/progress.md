# Progress

## Current Phase

Phase 2 implementation and live verification are complete; independent review
of TASK-003 and TASK-004 remains pending.

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

## Important Decisions

- Workflow IR and patches are the sole model-to-engine boundary.
- Only an approved algorithm registry may reach QGIS Processing execution.
- Default provider context contains safe project metadata only.
- Initial implementation is vector-first and conventional Python/PyQGIS.

## Known Limits and Risks

- No PyQGIS plugin packaging, UI, provider adapter, CI, type checker, or
  evaluation suite exists yet.
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

## Blocker

Independent review is required for TASK-003 and TASK-004 before Phase 2 can be
closed.

## Next Task and Role

Assign an independent reviewer for TASK-003 and TASK-004. On approval, begin
Phase 3 TASK-005.
