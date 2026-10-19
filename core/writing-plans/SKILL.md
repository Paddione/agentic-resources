---
name: writing-plans
description: Write concrete implementation plans with exact interfaces, files, verification commands and expected results. Use for plan content; retain the repository's dev-flow lifecycle where applicable.
---
# Writing executable plans

Curated from obra/superpowers writing-plans. Repository instructions and the
user's chosen execution method take precedence. This skill writes plan content;
it does not replace branch, review or release rules.

Read the spec and relevant code before planning. Record the repository revision,
working directory, global constraints and environmental assumptions. Retrieve
mutable interfaces from code or the code graph instead of guessing.

Store plans in the repository's established location (`.agents/plans/<slug>/`
in these dotfiles). Include:
- Goal and spec path; observable acceptance criteria.
- File structure and responsibilities; exact create/modify/test paths.
- Small independently verifiable tasks, ordered by their dependencies.
- Each task's consumed and produced interfaces: names, signatures and types.
- Checkable steps with an exact command and expected exit/result.
- A final verification task covering the integration boundaries.

## Target shape (ideal orchestration)

Write every plan so it passes the canonical gates without rework. Shape of `tasks.md`:
- YAML frontmatter first: non-empty `title`, `domains` (non-empty list), `status`.
- Then `# <slug> — Implementation Plan` (H1), followed by `## File Structure` (H2) listing created/modified files.
- At least one failing-test step with the literal phrase `expected: FAIL` plus a real runner call (`bats`, `vitest`, `pytest`, `jest`, `mocha`, `go test`, `playwright test`).
- Last task lists literally `task test:changed`, `task freshness:regenerate`, `task freshness:check`.
- Per touched file record the effective budget (baseline vs limit); never plan around a gate with a baseline exception. No `TBD`/`TODO`/`FIXME` in prose.
- Do not duplicate the gate rules here — `.agents/skills/references/plan-quality-gates.md` is canonical (S1–S4, CQ02, vitest, plan-lint hard rules F1/F2/STRUCT/P1/B1a/B1b).

For a local model executor, each task must also identify the permitted files,
interpreter/runtime, timeout, evidence location and retry/stop conditions.
Provide the decisions the executor cannot reasonably make from the code.
Avoid copying a complete implementation into the plan or leaving unresolved
names, “TBD”, “test appropriately” and unspecified dependencies.

For behavior changes, pin meaningful examples and failure cases with tests.
For documentation or similarly reversible low-impact work, use a proportionate
check rather than imposing TDD on every edit.

Self-review against the spec: coverage, interface consistency, environmental
assumptions, untested boundaries and excessive detail. Run the repository's
plan linter when one exists. Record unavailable checks explicitly.

When the user already authorized implementation, continue with the established
execution workflow. Otherwise present the concrete plan for review. Do not
introduce a second approval or delegation workflow.

Use sandbox-plan-executor for bounded local-model execution and
verification-planning for uncertain evidence paths when available.

Origin and revision: [skill-sources.json](../skill-sources.json).
