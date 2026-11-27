# dev-flow skills

## Repo-Graph zuerst (nur bei Code-Suche)

Suchst oder navigierst du Repo-Code, beginne am zentralen MCP-Hub `fleet-workspace`: `search_graph` → `trace_path` → `get_code_snippet`; Übersicht via `get_architecture`/`query_graph`/`search_code`. Nicht indiziertes Projekt zuerst mit `index_repository` indizieren. Belegpfade mit `check_index_coverage` prüfen und Lücken benennen. `grep`/`rg` nur für nicht-indizierte Nicht-Code-Dateien oder als belegten Fallback. Details: SSOT-Skill `codebase-memory`.

The repository workflow runs `dev-flow-plan` to stage a plan in `.agents/plans/<slug>/`, then `dev-flow-execute` to implement, verify, and open a PR. With a ticket backend, the ticket's `FACTORY-PLAN-REF` locates the plan; without one, the branch convention does. Use an isolated worktree and verify via the consumer's own checks (when `repo.task_runner` is set, e.g. `task test:changed`; otherwise the repo-local suites) before the PR.

Use the `dev-flow-plan` and `dev-flow-execute` skills.
