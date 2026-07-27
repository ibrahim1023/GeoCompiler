# ADR: Typed Workflow IR and Approved Registry Boundary

## Status

Accepted.

## Context

GeoCompiler turns model-assisted intent into executable spatial workflows. A
model can hallucinate algorithms, fields, file paths, and executable code; QGIS
model files and PyQGIS afford broad access to project data and local resources.

## Decision

Require all model output to parse as typed Workflow IR or Workflow Patch. Apply
deterministic schema, graph, geometry, field, parameter, and CRS validation.
Compile only operations present in an explicit approved algorithm registry to
QGIS Processing APIs. Require a user to approve proposed creation or editing
changes before execution.

## Alternatives Considered

- Direct model-generated QGIS model XML.
- Model-generated PyQGIS/Python code.
- A generic autonomous QGIS agent.

## Reasons

The chosen boundary preserves editable workflow artifacts, provider
independence, deterministic testing, transparent validation, and a constrained
execution surface.

## Tradeoffs

The initial feature set grows more slowly because each supported operation needs
an explicit registry definition and compiler mapping. Some valid user requests
will fail until their semantics are deliberately supported.

## Consequences

The workflow core can be tested without a provider or QGIS. Providers cannot
directly execute code. Unsupported or semantically ambiguous requests must be
reported, not silently approximated.

## Reversal Strategy

Adding an operation extends the registry and compiler with tests. Replacing the
IR or registry boundary requires a versioned migration, security review, and a
new ADR; no compatibility bypass is permitted.
