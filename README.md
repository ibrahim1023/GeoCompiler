# GeoCompiler

GeoCompiler is a QGIS plugin that turns spatial-analysis intent into reusable,
editable QGIS Processing workflows. It is not a generic GIS chat interface or
an autonomous desktop agent: models may propose typed workflow artifacts, while
QGIS performs spatial execution through an approved algorithm registry.

## Capabilities

- Defines a portable, JSON-serializable Workflow IR with directed-graph and
  parameter validation.
- Resolves a vector-first allow-list of 18 QGIS Processing operations.
- Inspects supported QGIS vector and raster layers as metadata-only project
  context, excluding data sources, feature values, geometry coordinates, and
  raw Processing commands.
- Compiles validated workflows only through the approved registry and runs them
  through QGIS Processing with explicit layer bindings and temporary outputs.
- Requires projected-CRS evidence for metric operations and maps Processing
  failures to the affected workflow step and approved algorithm.
- Provides a native QGIS dock for intent entry, structured workflow inspection,
  explicit approval before execution, and access to the QGIS Processing Model
  Designer.
- Accepts only strict, metadata-safe provider responses containing a Workflow IR
  or atomic Workflow Patch; unsupported operations and arbitrary-code-shaped
  payloads are rejected before compilation.

## Architecture

```text
Intent -> structured Workflow IR or Patch -> deterministic validation
       -> approved algorithm registry -> QGIS Processing -> result layers
```

Key boundaries:

- `src/geocompiler/workflow/`: portable Workflow IR and approved registry.
- `src/geocompiler/qgis/`: safe project context, compilation, and Processing
  execution adapters.
- `docs/architecture.md`: component responsibilities and trust boundaries.
- `docs/interfaces.md`: stable internal contracts.

## Technology

- Python 3.12+
- QGIS and PyQGIS, with PyQt supplied by the QGIS runtime
- Frozen standard-library dataclasses with deterministic JSON validation and
  JSON Schema output for provider artifacts
- QGIS Processing for spatial execution
- pytest and Ruff for deterministic verification

Ollama is an external local dependency for the planned connected workflow
provider. It is not bundled in the QGIS plugin archive.

## Metrics

| Measure | Current value |
| --- | --- |
| Approved vector Processing operations | 18 |
| Deterministic tests | 48 |
| Provider response fixtures | 6 across golden, edge, adversarial, failure, and regression sets |
| Live QGIS runtime validated | QGIS 4.2.0 on macOS |
| Verified live QGIS paths | `native:buffer` execution and dock/Model Designer lifecycle |

## Development

Use Python 3.12 or newer with the project dependencies installed.

```sh
python3 -m pytest -q
python3 -m ruff check .
python3 -m ruff format --check .
python3 -m compileall -q src
python3 scripts/evaluate_provider_fixtures.py --fixtures tests/fixtures/provider
```

The QGIS 4.2.0 macOS smoke command is documented in
`docs/testing-strategy.md`.

## Documentation

| Topic | Source |
| --- | --- |
| Product behavior | `geocompiler-product-spec.md` |
| Architecture | `docs/architecture.md` |
| Contracts | `docs/interfaces.md` |
| Testing | `docs/testing-strategy.md` |

See `AGENTS.md` for the repository workflow and non-negotiable safety
constraints.
