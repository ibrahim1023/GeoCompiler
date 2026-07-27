# Testing Strategy

## Principle

Most GeoCompiler correctness belongs in deterministic tests. LLM-dependent
behavior is evaluated separately and must not be the only evidence that the
compiler is safe.

## Test Layers

| Layer | Purpose | Required | Planned command |
| --- | --- | --- | --- |
| Unit and schema | Workflow IR, JSON round trips, patches, graph and parameter validation | Yes | Not established; target `pytest tests/unit -q` after TASK-001 |
| Contract | Registry definitions, compiler inputs/outputs, provider structured results | Yes | Not established; target `pytest tests/contract -q` |
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

No test, format, lint, typecheck, build, evaluation, or security command is
established yet. TASK-001 must add the Python scaffold and record exact commands
in `AGENTS.md` and this document. Later CI must run deterministic unit and
contract checks on every change; QGIS integration and workflow tests run where a
version-pinned runtime is available. UI verification includes manual QGIS
evidence until a reliable automated harness exists.

## Failure Handling

Do not skip a required test because a QGIS runtime is absent. Mark it blocked,
run all independent checks, record the missing environment in `docs/progress.md`,
and route according to the assigned task's failure handoff.
