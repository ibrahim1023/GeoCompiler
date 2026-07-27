# Evaluation Plan

## Scope

Evaluate only probabilistic behavior: intent interpretation into Workflow IR and
natural-language editing into Workflow Patch. Compilation and execution retain
deterministic tests as their primary gate.

## Evaluation Cases

| Set | Purpose | Example expectation |
| --- | --- | --- |
| Golden | Representative supported vector analyses | Area threshold and highway distance become typed parameters and supported stages |
| Edge | Units, aliases, missing optional metadata, ambiguous layer names | Clarify or fail transparently; do not guess fields or CRS |
| Adversarial | Requests for code, unsupported routing, unsafe substitutions | No arbitrary code; preserve unsupported semantic request |
| Failure | Schema-invalid output, unavailable provider, incompatible geometry | Structured error and no compile attempt |
| Regression | Reproducible prior defect | Fixture prevents recurrence |

## Per-Case Contract

Each fixture records a safe `ProjectContext`, user instruction, expected
semantic requirements, forbidden operations, expected artifact class, and
deterministic structural assertions. Fixtures contain metadata only unless a
QGIS workflow test needs local non-sensitive data.

## Grading

Deterministic graders validate JSON/schema parsing, allowed registry operations,
required inputs/parameters, unit representation, graph connectivity, no raw
provider code path, and expected transparent failure. A human rubric assesses
semantic completeness only when multiple workflow shapes are valid.

Record pass rate by case category, schema failure rate, unsupported-operation
rate, request latency, response latency, token usage, and cost where an external
provider call is made. Provider calls are not performed by default in local
tests; fixture replay is the baseline.

## Threshold Ownership

Task owners propose fixture acceptance thresholds after a baseline exists.
Architecture or product owners approve threshold changes that could weaken CRS,
privacy, registry, or transparent-failure guarantees. Add a regression fixture
for repeatable real failures when practical.
