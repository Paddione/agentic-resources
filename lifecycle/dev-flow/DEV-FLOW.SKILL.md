# dev-flow skills

The repository workflow runs `dev-flow-plan` to stage a plan in `.agents/plans/<slug>/`, then `dev-flow-execute` to implement, verify, and open a PR. With a ticket backend, the ticket's `FACTORY-PLAN-REF` locates the plan; without one, the branch convention does. Use an isolated worktree and verify via the consumer's own checks (when `repo.task_runner` is set, e.g. `task test:changed`; otherwise the repo-local suites) before the PR.

Use the `dev-flow-plan` and `dev-flow-execute` skills.
