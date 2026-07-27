# AI Workflow Change

## Purpose

Implement and evaluate GeoCompiler behavior that converts user instructions into
structured Workflow IR or Workflow Patch artifacts through a provider boundary.

## When to Use

Use for provider adapters, prompts, structured outputs, context construction,
patch generation, model routing, AI-specific errors, or fixture evaluations.

## When Not to Use

Do not use for pure PyQGIS UI, compiler mapping, or registry implementation
unless the change also affects model-facing contracts.

## Required Context

Read `AGENTS.md`, the assigned task, `docs/interfaces.md`, relevant architecture
invariants, `docs/evaluation-plan.md`, provider source/tests, and
`docs/progress.md` when continuing work.

## Authoritative Documents

`geocompiler-product-spec.md` governs product behavior. `docs/interfaces.md`
governs Workflow IR, patches, provider methods, and errors. ADR 0001 prohibits
model-to-code execution without typed validation and registry resolution.

## Scope

Model behavior may interpret intent, select supported semantic stages, propose
portable parameters, and generate structured patches. Deterministic code owns
schema validation, registry resolution, CRS/geometry checks, compilation, and
execution.

## Project Conventions

- Send the minimum project metadata necessary for the task.
- Require strict structured output and reject text that cannot parse to the contract.
- Do not expose raw geometries, full feature data, credentials, or connection strings by default.
- Do not forward model-generated Python, shell commands, QGIS XML, or provider algorithm IDs to execution.
- Preserve unsupported semantics and fail transparently rather than substitute.

## Workflow

1. Load the relevant contract and fixture/evaluation context.
2. Define or update deterministic request normalization and output validation.
3. Add focused tests for valid, invalid, missing-data, and unsafe cases.
4. Update fixtures and deterministic graders for semantic behavior changes.
5. Run schema, contract, privacy, and fixture checks before provider calls.
6. When a provider call is authorized, record model, latency, token usage, cost, schema result, and termination reason without sensitive data.
7. Inspect the diff and update authorities/progress with evidence.

## Common Mistakes

- Using prompt instructions as the only safety control.
- Parsing natural-language prose instead of strict structured output.
- Selecting a field or layer not present in `ProjectContext`.
- Replacing unsupported routing or temporal semantics with a spatial buffer.
- Regenerating an entire workflow when a patch is sufficient.

## Required Tests

Run deterministic context-normalization, schema, forbidden-output, error, and
patch-application tests. Run the relevant fixture evaluation suite. Add a
regression fixture for a repeatable production failure when practical.

## Required Verification

Verify executable operations are registry-approved only after deterministic
validation, provider payloads are minimized, failures stop before compilation,
and no arbitrary-execution path exists.

## Completion Criteria

Required deterministic tests and fixture evaluations pass, model behavior meets
the documented rubric, privacy/safety conditions hold, and evidence is
persisted with the task or progress state.
