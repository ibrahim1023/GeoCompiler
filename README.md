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
- Pydantic for typed, JSON-safe workflow artifacts
- QGIS Processing for spatial execution
- pytest and Ruff for deterministic verification

## Metrics

| Measure | Current value |
| --- | --- |
| Approved vector Processing operations | 18 |
| Deterministic tests | 31 |
| Live QGIS runtime validated | QGIS 4.2.0 on macOS |
| Verified live Processing path | `native:buffer` to a valid output layer |

## Development

Use Python 3.12 or newer with the project dependencies installed.

```sh
python3 -m pytest -q
python3 -m ruff check .
python3 -m ruff format --check .
python3 -m compileall -q src
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
