# QGIS Plugin Implementation

## Purpose

Implement and verify GeoCompiler changes that depend on PyQGIS, PyQt, QGIS
Processing, plugin packaging, or manual QGIS behavior.

## When to Use

Use for project-context inspection, algorithm registry integration, compiler or
execution adapters, dock-widget views, QGIS persistence, plugin metadata, and
QGIS integration tests.

## When Not to Use

Do not use for pure Workflow IR/Pydantic logic, fixture-only evaluations, or
provider-only changes without PyQGIS/PyQt behavior.

## Required Context

Read `AGENTS.md`, the assigned task, relevant `docs/architecture.md` and
`docs/interfaces.md` sections, `docs/testing-strategy.md`, target source/tests,
and `docs/progress.md` when continuing work.

## Authoritative Documents

`geocompiler-product-spec.md` governs product behavior. `docs/architecture.md`
governs boundaries; `docs/interfaces.md` governs contracts; ADR 0001 governs the
no-arbitrary-execution boundary.

## Scope

Keep QGIS-specific code at the project-context, compiler/execution, or UI
boundary. Do not make UI widgets own workflow semantics. Do not let a provider
or model bypass Workflow IR validation or the approved algorithm registry.

## Project Conventions

- Inspect target QGIS version and packaging convention before adding APIs.
- Prefer native QGIS Processing APIs and normal plugin conventions.
- Use the PyQt dock widget for GeoCompiler UI; QGIS Processing remains the full model editor.
- Map errors to workflow node and algorithm where possible.
- Never send raw features, geometry coordinates, credentials, or connection strings to a provider by default.

## Workflow

1. Load task-relevant context and inspect existing source/tests.
2. Identify the QGIS API contract and deterministic boundary affected.
3. Write or update focused tests before the behavior change where practical.
4. Implement the smallest adapter, widget, or registry mapping.
5. Run focused checks in a reproducible QGIS runtime when available.
6. Perform and record a manual QGIS smoke test when automation cannot exercise the behavior.
7. Inspect the diff, update authorities if needed, and persist evidence.

## Common Mistakes

- Treating geographic degrees as metres for distance or area operations.
- Recreating QGIS's full Processing model editor in the dock widget.
- Hard-coding project paths or layer names where model inputs are required.
- Calling arbitrary PyQGIS or accepting provider-specific algorithm IDs.
- Hiding an unsupported operation with a semantic approximation.

## Required Tests

Run focused registry/compatibility tests and relevant integration tests. For UI
or QGIS runtime behavior, perform a manual smoke test when no automated runtime
is established.

## Required Verification

Verify the approved registry remains the only path to execution, relevant
contracts remain valid, failure text identifies the affected node where known,
and no sensitive payload enters provider requests.

## Completion Criteria

Required checks pass or are explicitly blocked with evidence, manual QGIS
verification is recorded when required, documents match changed contracts, and
the task acceptance criteria are met.
