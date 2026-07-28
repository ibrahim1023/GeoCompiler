# Testing Strategy

## Principle

Most GeoCompiler correctness belongs in deterministic tests. LLM-dependent
behavior is evaluated separately and must not be the only evidence that the
compiler is safe.

## Test Layers

| Layer | Purpose | Required | Planned command |
| --- | --- | --- | --- |
| Unit and schema | Workflow IR, JSON round trips, graph and parameter validation | Yes | `python3 -m pytest tests/unit -q` |
| Contract | Registry definitions and compatibility validation | Yes | `python3 -m pytest tests/contract -q` |
| PyQGIS integration | Project inspection, CRS/geometry checks, compiler generation | Yes once adapter exists | Not established; target `pytest tests/integration -q` in supported QGIS |
| Processing workflow | Run generated vector workflows against fixtures | Yes for supported operations | Not established; target `pytest tests/workflow -q` |
| UI smoke | Dock widget loads, approval gates execution, and opens Model Designer | Required for UI milestones | `scripts/qgis_dock_widget_smoke.py` in the supported QGIS runtime |
| Security/privacy | Provider payload minimization and blocked arbitrary execution | Yes | Not established; target `pytest tests/security -q` |
| End-to-end | Intent to approved executable workflow | Required before release | Not established; target documented QGIS fixture run |

## Required Deterministic Coverage

- Workflow IDs, references, acyclicity, declared outputs, parameters, and JSON serialization.
- Geometry and CRS compatibility before metric operations.
- Registry allow-list resolution and unsupported-operation failure.
- Patch atomicity, semantic diff, and version/base checks.
- Provider request normalization, schema parsing, context limits, retry/timeout policy, termination, and error propagation.
- Compiler mapping, execution node/error attribution, and portability rules.

## Local and CI Policy

The established local commands are `python3 -m pytest -q`,
`python3 -m ruff check .`, `python3 -m ruff format --check .`, and
`python3 -m compileall -q src`. Type checking, packaging builds, evaluations,
security checks, CI, and a reproducible QGIS runtime are not established yet.
The Phase 5 plugin archive is built and checked with:

```sh
python3 scripts/build_plugin_archive.py
python3 scripts/validate_plugin_archive.py dist/geocompiler-0.1.0.zip
```

It contains the `geocompiler` plugin root, metadata, GPL-3.0 license, icon,
and user README, while excluding Python dependencies, tests, caches, and
development-only files.
Later CI must run deterministic unit and contract checks on every change; QGIS
integration and workflow tests run where a version-pinned runtime is available.
The TASK-003 adapter has deterministic fake-project coverage for its privacy and
normalization boundary. TASK-003/TASK-004 live coverage is collected from
`tests/integration/test_qgis_vertical_slice.py` only in a QGIS Python runtime;
it creates an in-memory projected line layer and runs `native:buffer` through
the approved compiler and runner. The equivalent QGIS 4.2.0 smoke passed on
2026-07-27. Its cask Python lacks pytest, so the automated integration test
requires a separately provisioned QGIS test environment.

The supported local smoke command for QGIS 4.2.0 on macOS is:

```sh
PYTHONHOME=/Applications/QGIS-final-4_2_0.app/Contents/Frameworks \
PYTHONPATH="$PWD/src:/Applications/QGIS-final-4_2_0.app/Contents/Resources/python3.12/site-packages:/Applications/QGIS-final-4_2_0.app/Contents/Resources/qgis/python/plugins" \
PROJ_DATA=/Applications/QGIS-final-4_2_0.app/Contents/Resources/qgis/proj \
QGIS_PREFIX_PATH=/Applications/QGIS-final-4_2_0.app/Contents/Resources \
/Applications/QGIS-final-4_2_0.app/Contents/MacOS/python3.12 scripts/qgis_vertical_slice_smoke.py
```
UI verification includes manual QGIS evidence until a reliable automated harness
exists.

The same environment runs `scripts/qgis_dock_widget_smoke.py` with
`QT_QPA_PLATFORM=offscreen`; it verifies dock lifecycle, explicit approval, and
the QGIS Processing Model Designer entry point. Provider response evaluation is
fixture replay in `tests/fixtures/provider/`, exercised by the unit suite. It
does not contact a provider, compiler, or QGIS runtime.

Run the provider evaluator directly with:

```sh
python3 scripts/evaluate_provider_fixtures.py --fixtures tests/fixtures/provider
```

## Failure Handling

Do not skip a required test because a QGIS runtime is absent. Mark it blocked,
run all independent checks, record the missing environment in `docs/progress.md`,
and route according to the assigned task's failure handoff.
