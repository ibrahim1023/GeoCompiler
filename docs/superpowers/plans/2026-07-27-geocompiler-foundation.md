# GeoCompiler Engineering Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the smallest durable documentation, role, task, and verification foundation needed to begin GeoCompiler implementation safely.

**Architecture:** GeoCompiler is a conventional Python/PyQGIS plugin with a native PyQt dock widget. Workflow semantics cross a strict deterministic boundary from schema-valid AI output through Workflow IR validation and an approved algorithm registry before QGIS Processing execution.

**Tech Stack:** Markdown, Python, PyQGIS, PyQt, Pydantic, pytest, JSON, Mermaid.

## Global Constraints

- Do not implement product code, packaging, dependencies, CI, or a Git repository in this bootstrap.
- The product specification is authoritative for product behavior and scope.
- Use a native PyQt/PyQGIS dock widget; QGIS Processing tooling remains the full workflow-model editor.
- A model may produce only structured Workflow IR or Workflow Patch artifacts; it must never execute arbitrary Python.
- Remote providers receive only necessary metadata by default, never raw features, geometries, credentials, or connection strings.
- Treat all commands as planned unless they already exist in the repository.
- Persist durable state in repository artifacts and load only task-relevant context.

---

## Planned File Structure

| Path | Responsibility |
| --- | --- |
| `AGENTS.md` | Stable repository rules and default context order |
| `docs/architecture.md` | Plugin boundaries, trust/data flows, invariants, and UI decision |
| `docs/interfaces.md` | Workflow IR, patch, registry, provider, and adapter contracts |
| `docs/agent-system.md` | Roles, handoffs, graph transitions, and bounded loops |
| `docs/decisions/0001-typed-ir-registry-boundary.md` | ADR for the deterministic execution boundary |
| `docs/context-map.md` | Minimal context and checks by task type |
| `docs/progress.md` | Compact, current cross-thread project memory |
| `docs/testing-strategy.md` | Deterministic test layers and planned verification commands |
| `docs/evaluation-plan.md` | Fixture-driven probabilistic evaluation strategy |
| `task.md` | Dependency-aware, bounded first implementation roadmap |
| `.agents/skills/qgis-plugin-implementation/SKILL.md` | PyQGIS/PyQt implementation procedure |
| `.agents/skills/ai-workflow-change/SKILL.md` | AI boundary and eval procedure |

### Task 1: Establish Governance, Architecture, and Contracts

**Files:**
- Create: `AGENTS.md`
- Create: `docs/architecture.md`
- Create: `docs/interfaces.md`
- Create: `docs/decisions/0001-typed-ir-registry-boundary.md`

**Interfaces:**
- Consumes: `geocompiler-product-spec.md`; `docs/superpowers/specs/2026-07-27-geocompiler-foundation-design.md`
- Produces: authoritative architecture and contract constraints for all future implementation tasks.

- [ ] **Step 1: Write the repository constitution**

Write `AGENTS.md` with product purpose, source-of-truth map, default context order, scoped workflow rules, safety boundaries, and a commands table showing `Not established` for format, lint, typecheck, build, tests, evaluations, and security checks.

- [ ] **Step 2: Document component and data boundaries**

Write `docs/architecture.md` with UI, project context, AI boundary, workflow core, compiler/execution, and observability responsibilities. Include a Mermaid flow: `intent -> structured output -> schema validation -> Workflow IR validation -> approved registry -> QGIS Processing -> result layers`. State that PyQt is the plugin surface and QGIS Processing is the full model editor.

- [ ] **Step 3: Define contracts before components exist**

Write `docs/interfaces.md` with stable domain-level schemas for `WorkflowIR`, `WorkflowInput`, `WorkflowParameter`, `WorkflowStep`, `WorkflowPatch`, `AlgorithmDefinition`, `ProjectContext`, `LLMProvider`, and `QgisCompiler`. Distinguish model-generated, deterministically validated, and human-approved artifacts. Specify schema, graph, compatibility, unsupported-operation, compiler, and execution errors.

- [ ] **Step 4: Record the trust-boundary decision**

Write ADR `0001-typed-ir-registry-boundary.md` with Status, Context, Decision, Alternatives considered, Reasons, Tradeoffs, Consequences, and Reversal strategy. Select typed Workflow IR plus an approved registry; reject direct XML emission and arbitrary PyQGIS/Python execution.

- [ ] **Step 5: Verify authority and safety coverage**

Run:

```bash
rg -n "arbitrary Python|approved.*registry|PyQt|QGIS Processing|product specification" AGENTS.md docs/architecture.md docs/interfaces.md docs/decisions/0001-typed-ir-registry-boundary.md
```

Expected: each boundary appears in its owning document; no command claims an unavailable tool exists.

- [ ] **Step 6: Commit when Git is available**

After repository initialization, stage `AGENTS.md`, `docs/architecture.md`, `docs/interfaces.md`, and `docs/decisions/0001-typed-ir-registry-boundary.md`; commit with `docs: establish GeoCompiler architecture foundation`.

### Task 2: Establish Roles, Context Routing, and Progress Memory

**Files:**
- Create: `docs/agent-system.md`
- Create: `docs/context-map.md`
- Create: `docs/progress.md`

**Interfaces:**
- Consumes: `AGENTS.md`; `docs/architecture.md`; `docs/interfaces.md`
- Produces: explicit handoffs and selective context rules for implementer, reviewer, architect, and verifier sessions.

- [ ] **Step 1: Define the smallest useful development graph**

Write `docs/agent-system.md` with role tables for implementer, reviewer, architect, and verifier. Define inputs, outputs, scope, completion evidence, transitions, and the three-attempt blocker stop condition. Include a Mermaid graph with deterministic failures and material review findings routing to the implementer.

- [ ] **Step 2: Define durable handoffs**

Add a YAML handoff template to `docs/agent-system.md` requiring `task_id`, `owner_role`, `objective`, `inputs`, `constraints`, `acceptance_criteria`, `verification`, `outputs`, `success_next`, and `failure_next`.

- [ ] **Step 3: Map minimal context**

Write `docs/context-map.md` entries for Workflow IR changes, PyQGIS compiler changes, AI provider/prompt changes, UI changes, and reviews. Each entry names required documents, relevant directories, required checks, optional context, and context normally unnecessary.

- [ ] **Step 4: Seed compact execution memory**

Write `docs/progress.md` with bootstrap phase, completed design, primary constraints, known limits, verification state, no blocker, and `TASK-001` as next work.

- [ ] **Step 5: Verify role boundaries and token discipline**

Run:

```bash
rg -n "three|stop|implementer|reviewer|verifier|normally unnecessary|TASK-001" docs/agent-system.md docs/context-map.md docs/progress.md
```

Expected: documents define bounded retries, role routing, selective context, and a clear next task.

- [ ] **Step 6: Commit when Git is available**

After repository initialization, stage `docs/agent-system.md`, `docs/context-map.md`, and `docs/progress.md`; commit with `docs: define GeoCompiler agent workflow`.

### Task 3: Establish Testing, Evaluation, Skills, and the Active Roadmap

**Files:**
- Create: `docs/testing-strategy.md`
- Create: `docs/evaluation-plan.md`
- Create: `task.md`
- Create: `.agents/skills/qgis-plugin-implementation/SKILL.md`
- Create: `.agents/skills/ai-workflow-change/SKILL.md`

**Interfaces:**
- Consumes: `docs/architecture.md`; `docs/interfaces.md`; `docs/agent-system.md`; `docs/context-map.md`
- Produces: future implementation tasks, planned checks, and narrowly reusable procedures.

- [ ] **Step 1: Define deterministic verification layers**

Write `docs/testing-strategy.md` covering pure-Python unit/schema tests, graph/contract tests, PyQGIS integration tests, Processing execution tests, UI smoke tests, and security checks. Mark commands `Not established` and name future commands only as planned after TASK-001 creates a Python scaffold.

- [ ] **Step 2: Define only the needed model evaluation plan**

Write `docs/evaluation-plan.md` for semantic Workflow IR generation and workflow patches. Include golden, edge, adversarial, failure, and regression fixtures; deterministic structural graders; semantic review criteria; threshold ownership; and cost/latency recording. State that provider calls are not performed by default.

- [ ] **Step 3: Create the dependency-aware active roadmap**

Write `task.md` with `TASK-001` through `TASK-006`: pure Workflow IR, algorithm registry/validator, QGIS context adapter, compiler/execution vertical slice, PyQt dock widget, and AI provider/eval integration. Make `TASK-001` executable by one implementer and keep later tasks at milestone detail. For each task include owner, dependencies, context, scope, out-of-scope, acceptance criteria, verification, outputs, review need, and success/failure routing.

- [ ] **Step 4: Create the QGIS implementation skill**

Write `.agents/skills/qgis-plugin-implementation/SKILL.md` with a precise trigger and scope. Require QGIS-version inspection, native Processing API use, focused tests, and explicit manual-QGIS verification when an automated runtime is unavailable. Exclude pure Workflow IR and provider-only changes.

- [ ] **Step 5: Create the AI workflow skill**

Write `.agents/skills/ai-workflow-change/SKILL.md` for provider, prompt, structured-output, evaluation, and patch changes. Require contract loading, metadata minimization, schema validation, approved registry constraints, deterministic tests, fixture evals, and transparent failure. Prohibit arbitrary code paths and unvalidated natural-language execution.

- [ ] **Step 6: Verify bootstrap completeness honestly**

Run:

```bash
rg -n -i "TO[D]O|TB[D]|implement[- ]later|fill[- ]in[- ]details" AGENTS.md docs task.md .agents/skills
rg -n "Not established|planned" AGENTS.md docs/testing-strategy.md
```

Expected: the first command returns no unfinished placeholders; the second confirms unavailable checks are represented honestly.

- [ ] **Step 7: Commit when Git is available**

After repository initialization, stage `docs/testing-strategy.md`, `docs/evaluation-plan.md`, `task.md`, and `.agents/skills`; commit with `docs: add GeoCompiler delivery roadmap`.

## Plan Self-Review

Coverage: architecture, contracts, source ownership, roles, handoffs, bounded loops, testing, model evaluation, selective context, progress, safe parallelism, and reusable procedures are included. Product code, packaging, dependencies, CI, and Git initialization are deliberately omitted.

Consistency: every authority is created before a dependent task consumes it. Stable terms are `Workflow IR`, `Workflow Patch`, `AlgorithmDefinition`, `ProjectContext`, `LLMProvider`, and `QgisCompiler` throughout.

Placeholder check: no unfinished implementation placeholders are allowed; planned commands are explicitly marked because no runtime exists yet.
