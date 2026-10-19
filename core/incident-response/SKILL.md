---
name: incident-response
description: 'Production incident triage, scope, diagnose, fix/rollback, and post-mortem close. Time-critical — use when a core service is down or degraded. For plan triage see dev-flow-plan; for follow-up work or worker dispatch see operations-management; for repo hygiene or PR management see repo-hygiene.'
agent: bp-run
---

> **Mishap Tracking:** Führe während dieses Skills ein `MISHAP_LOG` und rufe am Ende
> `mishap-tracker` auf — Eintragsformat und Ablauf: siehe `mishap-tracker` §Input.

# incident-response

Production incident triage and recovery. Use when a core platform service is down or degraded. For plan triage, see `dev-flow-plan`; for follow-up work or worker dispatch, see `operations-management`; for repo hygiene or PR management, see `repo-hygiene`.

## Repo-Kontext (repo.yaml)

Lies vor Beginn aus `repo.yaml` im Consumer-Repo-Root:

- `repo.tickets`: `github` → Incidents als GitHub-Issues (Konvention unten); `none` → Incident nur im lokalen Log (`stderr` + `.mishaps.log`) festhalten, Steps 2 und 5 entfallen.
- `repo.task_runner`: `taskfile` → Diagnose-Kommandos über den Task-Runner des Consumer-Repos; `none` → direkte CLI-/MCP-Calls (Fallbacks unten).
- Fehlender Schlüssel → getroffene Annahme im Log nennen.

## Issue model (nur wenn `repo.tickets: github`)

Incidents als GitHub-Issues (interne Ticket-DB retiriert 2026-10-14):
Titel `Incident: <service> — <symptom>`, Labels `incident` + Schwere (`critical|major|minor`),
Body mit Service, Cluster, Onset, Blast-Radius, Root-Cause und Fix. Der Close-Kommentar
hält Dauer und PR-Referenz fest.

**DB-Zugriff:** Reads MCP-first via `mcp-postgres_query` (Nicht-Ticket-Tabellen);
der `psql()`-Fallback-Helper ist SSOT im
[`MCP-Tool-Guide`](.agents/skills/references/mcp-tool-guide.md) §mcp-postgres.

---

## Step 1 — Scope the Incident (< 2 min)

Determine:
1. **Affected Service:** Welcher Core-Service ist betroffen?
2. **Target Cluster:** Welches Zielcluster (Brand/Umgebung laut Deployment-Status)?
3. **Onset Time:** Since when has it been failing? Check git log or deployment status.
4. **Blast Radius:** All users or a subset of features?

## Step 2 — Open an Incident Issue

```bash
ISSUE_NUM=$(gh issue create --title "Incident: <service> — <symptom>" \
  --label "incident,<critical|major|minor>" \
  --body "Affected: <svc>
Cluster: <env>
Symptoms: <symptoms>" | grep -oE '[0-9]+$')
# → ISSUE_NUM merken (für Step 5 Close-Kommentar)
```

## Step 3 — Diagnose

Cluster-Status-Reads — **MCP-first** (`mcp-kubernetes`, read-only):

> Pod-Status: `mcp-kubernetes_pods_list_in_namespace({ namespace: "workspace" })` — CrashLoopBackOff, OOMKilled, Pending erkennen.
> Logs: `mcp-kubernetes_pods_log({ namespace: "workspace", name: "<pod>" })`
> Einzelnes Pod-Detail: `mcp-kubernetes_pods_get({ namespace: "workspace", name: "<pod>" })`

Fallback (mcp-kubernetes nicht erreichbar — Verfügbarkeits-Guard siehe [`MCP-Tool-Guide`](.agents/skills/references/mcp-tool-guide.md)):

* **Pod status** (nur wenn `repo.task_runner: taskfile`): Status-Task des Consumer-Repos (CrashLoopBackOff, OOMKilled, Pending).
* **Logs:** Log-Task des Consumer-Repos für `<service>`.
* Sonst: `kubectl` direkt gegen das Zielcluster.

**Recent Deploys** (kein Cluster-Read): `git log --oneline -10`.

## Step 4 — Fix or Rollback

* **Baseline remote clients before network changes [T002495-M6]:** Vor jeder Änderung an Netzwerkpfaden oder Firewall-Regeln (Hetzner, UFW, WireGuard, GPU-Host) zwingend die Erreichbarkeit von REMOTEN Clients (z. B. fleet-Cluster-Pods, external probes) messen und dokumentieren, nicht nur den lokalen Health-Endpunkt (`curl localhost`). Sonst lässt sich nach der Änderung ein Vorzustand nicht von einem selbst verursachten Ausfall unterscheiden.
* **Rollback** (no schema migration introduced): `kubectl set image deployment/<svc> <container>=<image>:<PREV_SHA> -n <ns> --context <ctx>`
* **Fix:** Open a `fix/<slug>` branch, implement, PR, merge, verify.

## Step 5 — Close & Write Post-Mortem

Capture the fix PR number (`PR_NUM=$(gh pr view <branch-or-num> --json number -q '.number')`); for rollback-only, omit the comment.

```bash
gh issue comment "$ISSUE_NUM" --body "[incident-response $(date +%Y-%m-%d)] Root cause: <cause>. Fix: <fix>. Duration: <X> min. Resolved by PR #$PR_NUM (or rollback to <PREV_SHA>)."
gh issue close "$ISSUE_NUM"
```

---

## Post-Execution: Mishap Report

Invoke `mishap-tracker` with your accumulated `MISHAP_LOG`.

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `operations-management` | Follow-up work via worker dispatch; PR management via `repo-hygiene` |
| `dev-flow-plan` | Follow-up: plan human-fixable items |
| `mishap-tracker` | Local mishap log (stderr + `.mishaps.log`, no ticket backend) |
| `infra-ops` | Cross-brand incident handling and infrastructure deployment (Phase 5) |

## Framework mapping

| Framework | Availability |
|-----------|--------------|
| **Claude Code** | Full — load via `load skill <name>` or matches on description triggers |
| **opencode** | Full — available as a listed skill. All tools (CLI, MCP) are framework-agnostic |
| **agy** | Full — treat the opencode path as authoritative. All CLI tools and MCP calls work identically |
