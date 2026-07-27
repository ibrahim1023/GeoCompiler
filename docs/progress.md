# Progress

## Current Phase

Phase 2 TASK-003 is in progress. The deterministic project-context adapter is
implemented; live PyQGIS verification and independent review remain pending.

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

## Important Decisions

- Workflow IR and patches are the sole model-to-engine boundary.
- Only an approved algorithm registry may reach QGIS Processing execution.
- Default provider context contains safe project metadata only.
- Initial implementation is vector-first and conventional Python/PyQGIS.

## Known Limits and Risks

- No PyQGIS plugin, QGIS runtime, UI, provider adapter, CI, type checker,
  evaluation suite, or reproducible QGIS integration runtime exists yet.
- Supported QGIS versions and plugin packaging convention remain a bounded
  discovery task before PyQGIS integration.
- On 2026-07-27, `qgis`, `qgis_process`, `import qgis`, and common macOS/local
  installation locations were unavailable. A live adapter smoke test cannot run
  until QGIS is installed and version-pinned.

## Verification and Review

- Bootstrap Task 1 verification passed: architecture and safety authorities
  contain the required QGIS-native and no-arbitrary-execution constraints.
- Bootstrap Tasks 2 and 3 verification passed: bounded roles, selective context,
  planned checks, focused skills, and the dependency-aware roadmap are present.
- Phase 1 deterministic verification passed: Ruff, full pytest suite, and
  Python compilation. Human review approval was received on 2026-07-27.
- TASK-003 deterministic verification passed: 23 tests, Ruff, formatting, and
  Python compilation. Live PyQGIS API verification is blocked by the absent
  QGIS runtime.

## Blocker

No version-pinned QGIS runtime is available for the required TASK-003 live
integration test and manual smoke test.

## Next Task and Role

Provision a version-pinned QGIS runtime, run the TASK-003 live integration and
manual smoke tests, then assign an independent reviewer for TASK-003.
