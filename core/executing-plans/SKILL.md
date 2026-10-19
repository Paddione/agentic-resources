---
name: executing-plans
description: Execute a supplied implementation plan incrementally, verify each result and retain a resumable evidence ledger. Use alongside repository lifecycle rules; use sandbox-plan-executor for bounded local models.
---
# Execute and verify a plan

Curated from obra/superpowers executing-plans. This skill covers execution
content, not branch/ticket/release policy. Use the repository's worktree helper
and git/dev-flow workflow. Do not create another delegation or merge process.

Read the committed plan, spec, repository rules and existing progress evidence.
Verify dependencies and consumed/produced interfaces before the first task.
Do not reimplement completed work: compare the ledger with commits and artifacts.

For each task:
1. Read its exact brief and affected code.
2. Follow its steps using the specified working directory and runtime.
3. Run the meaningful verification and inspect output, exit status and failures.
4. Record task ID, revision, command, environment, result and evidence path.
5. Mark complete only when the acceptance criteria have evidence.

Keep the ledger in the plan's evidence directory; preserve it across context
loss. Treat absent evidence as unknown. A test that was skipped did not pass.
A generated fixture result is not a measurement of the trained model.

If assumptions conflict with live code, record the conflict. Ordinary executors
may resolve routine details within the authorized scope; sandboxed local models
must follow their task's permitted files, commands and escalation conditions.
Neither executor should silently weaken acceptance criteria, tests or guards.

For behavior changes, verify the regression meaningfully. On failed commands,
diagnose the failure before retrying; obey task-specific budgets. Continue
through authorized tasks without asking whether to continue after each one.

At the end, check integration boundaries, inspect the final diff and execute the
repository-required checks. The final check is literally `task test:changed`,
`task freshness:regenerate`, `task freshness:check`. Report actual validation and
remaining limitations. Leave merge evidence to the repository's finalize flow (in this
repo: lifecycle receipt in the local evidence ledger); the ledger keeps per-task evidence.
Commit/push/review/merge only through the repository's established workflow.

For small local models, load sandbox-plan-executor rather than this longer
planning context unless the task explicitly requires it.
