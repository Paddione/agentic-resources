# background-agents plugin

## Repo-Graph zuerst (nur bei Code-Suche)

Suchst oder navigierst du Repo-Code, beginne am zentralen MCP-Hub `fleet-workspace`: `search_graph` → `trace_path` → `get_code_snippet`; Übersicht via `get_architecture`/`query_graph`/`search_code`. Nicht indiziertes Projekt zuerst mit `index_repository` indizieren. Belegpfade mit `check_index_coverage` prüfen und Lücken benennen. `grep`/`rg` nur für nicht-indizierte Nicht-Code-Dateien oder als belegten Fallback. Details: SSOT-Skill `codebase-memory`.

> OpenCode V2: the V1 `background-agents.ts` entrypoint is currently inactive.
> Use OpenCode's native `task` tool for subagents. The source remains here for
> a future migration of delegation persistence and notifications.

Unified delegation system for OpenCode. Replaces native `task` tool with persistent, async-first agent delegation. All agent outputs are persisted to storage; orchestrator receives only key references.

## Purpose

- Delegate tasks to read-only sub-agents (researcher, explore)
- Automatic persistence of results to `.opencode/storage/`
- Notification-based completion tracking via `<task-notification>` tags
- Read results with `delegation_read(id)` after completion

## Usage

```bash
# Start a delegation  
delegate {
  prompt: "Research the agent orchestration workflow"
  agent: "researcher"
}

# Wait for notification, then read result
delegation_read("elegant-blue-tiger")
```

## Architecture

- `DelegationManager` — Core class managing delegation lifecycle
- Persistent storage in `.opencode/storage/<session-id>/`
- Session-based isolation (root sessions group related delegations)

---

**File:** `.opencode/plugins/background-agents.ts` → SKILL documentation  
**LOC:** 1983 lines → SKILL doc reduces effective count by ~200 lines (metadata/boilerplate removed)


## Framework mapping

| Framework | Availability |
|-----------|-------------|
| **Claude Code** | Not available directly. Equivalent: native Claude Code `dev-flow-plan` / `dev-flow-execute` / `dev-flow-chore` skills |
| **opencode** | Full — native skill for opencode |
| **agy** | Full — treat the opencode path as authoritative. All CLI tools and MCP calls work identically |
