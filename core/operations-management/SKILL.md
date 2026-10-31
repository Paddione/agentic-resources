---
name: operations-management
description: 'Routing hub for operational work — decides between incident-response (a service is down or degraded, time-critical), dev-flow-plan (plan or content work: feature, bug, chore), repo-hygiene (repository state: branches, worktrees, PRs) and worker dispatch (execution via worker sandboxes). Use this first when the operational request is ambiguous; it holds no runbook of its own and only delegates. If you already know which skill you need, invoke it directly.'
---

# operations-management

This skill routes to focused sub-skills. Use the decision tree below to route to the correct one. It dispatches no work itself.

## Repo-Kontext (repo.yaml)

Lies vor Beginn aus `repo.yaml` im Consumer-Repo-Root:

- `repo.tickets`: `github` → Bug-/Issue-Routen wie unten; `none` → keine Issue-Steps, nur lokales Log.
- `repo.task_runner`: `taskfile` → Sandbox-Dispatch über den Task-Runner des Consumer-Repos; `none` → direkter Dispatch-Call (Fallback unten).
- Fehlender Schlüssel → getroffene Annahme im Log nennen.

> Ticket-System-Historie: interne Ticket-DB retiriert 2026-10-14; `ticket-ops`, `ticket-triage` und `ticket-dispatch` existieren nicht mehr.

---

## Decision Tree

```
Is a core service DOWN or DEGRADED right now?
├── YES → Use incident-response
│          (production triage, diagnose, fix/rollback, post-mortem)
│
├── NO, PLAN or CONTENT work (feature, bug, chore)
│   ├── needs a plan first → Use dev-flow-plan
│   └── approved for execution → worker sandbox (contract below),
│        then dev-flow-execute — only after explicit approval
│
└── NO, repository STATE (branches, worktrees, PRs)
         → Use repo-hygiene
```

### Quick reference

| Situation | Route |
|-----------|-------|
| Service is down or crashing | `incident-response` |
| New feature, bug report, or chore needs a plan | `dev-flow-plan` |
| Approved work goes to execution sandboxes | worker sandbox (below), then `dev-flow-execute` |
| Clean up stale worktrees and branches | `repo-hygiene` |
| Review & merge open PRs | `repo-hygiene` |
| Funnel issues (dedupe against open issues) | `repo-hygiene` |
| Multi-repo, runtime drift, or GGUF/serving hygiene audit | `repo-hygiene` |
| File a bug found after merge (nur wenn `repo.tickets: github`) | GitHub issue (siehe AGENTS.md Bug-Triage-Konvention) |
| Run a task on the GPU workers | worker sandbox (below) |

---

## Worker dispatch contract

Execution dispatch casts a sandbox on the workers instead of claiming ticket waves.

- **Primary** (nur wenn `repo.task_runner: taskfile`): Sandbox-Task des Consumer-Repos mit
  `WORKTREE`, `SCOPE`, `ACTION`, `BRANCH`, `PLAN` — POSTet den JSON-Contract an den
  Dispatch-Endpunkt des Consumer-Repos (Pfad/Taskfile dort dokumentiert).
- **Fallback** (Runner fehlt oder Proxy offline): direkter Sandbox-Call mit demselben
  JSON-Contract (z. B. `PYTHONPATH=scripts python3 -m devflow sandbox`).
- **Substrat:** Worker-Inventory des Consumer-Repos (Cluster-/Host-Liste dort als SSOT).
- **Approval gate (preserved):** building a dispatch plan does not authorize
  dispatch. Only explicit user approval dispatches.

---

## Mishap Tracking

All sub-skills carry the mishap tracking preamble. After completing either, invoke `mishap-tracker` if any mishaps were accumulated (`mishap-tracker` is local-only: stderr + `.mishaps.log`, no ticket backend).

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `incident-response` | Production incident triage & recovery |
| `dev-flow-plan` | Plan work: specs, partials, plan-lint |
| `dev-flow-execute` | Execute approved plans in worker sandboxes |
| `repo-hygiene` | Repository state: branches, worktrees, PRs |
| `mishap-tracker` | Local friction log (no ticket backend) |

## Framework mapping

| Framework | Availability |
|-----------|--------------|
| **Claude Code** | Full — load via `load skill <name>` or matches on description triggers |
| **opencode** | Full — available as a listed skill. All tools (CLI, MCP) are framework-agnostic |
| **agy** | Full — treat the opencode path as authoritative. All CLI tools and MCP calls work identically |
