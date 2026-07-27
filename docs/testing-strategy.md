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
| UI smoke | Dock widget loads and routes approved actions | Required for UI milestones | Not established; target `pytest tests/ui -q` plus manual QGIS smoke test |
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
Later CI must run deterministic unit and contract checks on every change; QGIS
integration and workflow tests run where a version-pinned runtime is available.
The TASK-003 adapter has deterministic fake-project coverage for its privacy and
normalization boundary, but an installed QGIS runtime is still required to
validate the live PyQGIS API contract.
UI verification includes manual QGIS evidence until a reliable automated harness
exists.

## Failure Handling

Do not skip a required test because a QGIS runtime is absent. Mark it blocked,
run all independent checks, record the missing environment in `docs/progress.md`,
and route according to the assigned task's failure handoff.
