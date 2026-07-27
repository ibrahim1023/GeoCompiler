# GeoCompiler

## Repository Context

GeoCompiler is a conventional Python QGIS plugin that turns spatial-analysis
intent into reusable QGIS Processing workflows. The workflow is the durable
artifact; AI proposes typed workflow changes, while QGIS performs geospatial
execution.

## Sources of Truth

| Concern | Authority |
| --- | --- |
| Product behavior and scope | `geocompiler-product-spec.md` |
| Architecture | `docs/architecture.md` |
| Contracts | `docs/interfaces.md` |
| Agent roles and handoffs | `docs/agent-system.md` |
| Current execution state | `docs/progress.md` |
| Active roadmap | `task.md` |
| Task context selection | `docs/context-map.md` |
| Tests and evaluations | `docs/testing-strategy.md`, `docs/evaluation-plan.md` |
| Material decisions | `docs/decisions/` |

## Default Context Order

1. `AGENTS.md`
2. Assigned task or plan
3. `docs/progress.md` when continuing work
4. Relevant architecture or contract section
5. Relevant project `SKILL.md`
6. Relevant source and tests
7. Extra context only when needed

## Required Workflow

Understand acceptance criteria, identify authorities, load only relevant
context, inspect existing patterns before editing, keep changes scoped, run
relevant checks, record material assumptions or deviations, update authorities
when contracts change, persist progress or blockers, and stop without claiming
success unless evidence exists.

## Stable Constraints

- Keep the plugin QGIS-native: Python, PyQGIS, PyQt, and QGIS Processing.
- Use a native PyQt dock widget. QGIS Processing tooling remains the full
  workflow-model editor.
- Keep Workflow IR, validation, registry resolution, compilation, and execution
  deterministic and independently testable.
- Models may output only schema-valid Workflow IR or Workflow Patch artifacts.
  Never route model text to arbitrary Python, PyQGIS, shell, XML, or execution.
- Resolve execution only through the approved algorithm registry and fail
  transparently for unsupported semantics or incompatible data.
- Default remote-provider context to layer metadata, schema, geometry type, and
  CRS. Do not send raw geometries, full feature data, credentials, or connection
  strings without an explicit product change.
- Add dependencies only when justified by a bounded task. Prefer QGIS and Python
  standard capabilities first.

## Commands

| Check | Command |
| --- | --- |
| Format | `python3 -m ruff format --check .` |
| Lint | `python3 -m ruff check .` |
| Typecheck | Not established |
| Build | `python3 -m compileall -q src` |
| Tests | `python3 -m pytest -q` |
| Evaluations | Not established |
| Security checks | Not established |

## Completion

Do not declare a task complete until its acceptance criteria, relevant checks,
documentation, and required review pass with no unresolved critical issue.
