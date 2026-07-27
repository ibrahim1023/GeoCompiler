# Context Map

Load the smallest set of authorities needed for the assigned task. Search
symbols before opening large files and read relevant sections rather than full
documents. Conversation history is not durable project memory.

## Workflow IR, Patch, or Validation Change

**Required:** `AGENTS.md`, assigned task, `docs/interfaces.md`, relevant
`docs/architecture.md` invariants, Workflow IR source and tests.

**Skill:** none unless the task changes model interaction; then use
`.agents/skills/ai-workflow-change/SKILL.md`.

**Checks:** focused unit/schema tests; graph, reference, parameter, and CRS
validation tests when applicable.

**Optional:** relevant ADR, `docs/evaluation-plan.md` for model-facing output.

**Normally unnecessary:** full product specification, UI docs, processing
history details, unrelated provider integrations.

## PyQGIS Compiler or Processing Change

**Required:** `AGENTS.md`, assigned task, `docs/architecture.md`,
`docs/interfaces.md`, `docs/testing-strategy.md`, compiler source/tests, and
`.agents/skills/qgis-plugin-implementation/SKILL.md`.

**Checks:** registry/compatibility tests plus QGIS integration or explicit
manual-QGIS verification.

**Optional:** relevant `docs/decisions/`, `docs/progress.md`.

**Normally unnecessary:** provider prompt details, full evaluation fixtures,
unrelated UI behavior.

## AI Provider, Prompt, Structured Output, or Evaluation Change

**Required:** `AGENTS.md`, assigned task, `docs/interfaces.md`,
`docs/evaluation-plan.md`, provider source/tests, and
`.agents/skills/ai-workflow-change/SKILL.md`.

**Checks:** request-data minimization, schema parsing, deterministic
normalization tests, fixture evaluation, and cost/latency capture if a provider
call is part of the task.

**Optional:** registry source for capability-related prompts.

**Normally unnecessary:** full QGIS UI implementation, raw project data,
unrelated ADRs.

## PyQt/PyQGIS UI Change

**Required:** `AGENTS.md`, assigned task, UI section of
`docs/architecture.md`, relevant interface/view-model contract, target widget
source/tests, and `.agents/skills/qgis-plugin-implementation/SKILL.md`.

**Checks:** focused automated test where feasible and manual QGIS smoke test.

**Optional:** `docs/progress.md`, QGIS plugin packaging details.

**Normally unnecessary:** full product specification, provider implementation,
model evaluation fixtures.

## Review

**Required:** `AGENTS.md`, task acceptance criteria, relevant authority, diff,
and verification evidence.

**Checks:** requirements alignment, scope, contracts, failure behavior, tests,
security/privacy implications, and documentation changes.

**Normally unnecessary:** raw implementation history, unrelated source trees,
full progress history.
