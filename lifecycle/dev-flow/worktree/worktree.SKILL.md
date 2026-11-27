# worktree plugin (worktree.ts)

## Repo-Graph zuerst (nur bei Code-Suche)

Suchst oder navigierst du Repo-Code, beginne am zentralen MCP-Hub `fleet-workspace`: `search_graph` → `trace_path` → `get_code_snippet`; Übersicht via `get_architecture`/`query_graph`/`search_code`. Nicht indiziertes Projekt zuerst mit `index_repository` indizieren. Belegpfade mit `check_index_coverage` prüfen und Lücken benennen. `grep`/`rg` nur für nicht-indizierte Nicht-Code-Dateien oder als belegten Fallback. Details: SSOT-Skill `codebase-memory`.

Git worktree lifecycle management for OpenCode. Enables isolated development environments with automatic sync to main branch and cleanup on task completion.

## Purpose

- Create git worktrees for feature branches  
- Automatic `git fetch && rebase` on startup
- Persistent working directories in `.opencode/`
- Cleanup orphaned worktrees after session end

## Architecture

```typescript
// Core modules:
worktree.ts         → 1215 lines (lifecycle manager, sync orchestration)
  ├─ LifecycleManager   → Worktree creation/deletion  
  ├─ SyncCoordinator    → Automatic rebase & conflict resolution
  └─ CleanupScheduler   → Periodic orphan detection

// Dependencies:
TerminalPlugin      → Shell session management for git commands
launch-context.ts     → Working directory injection
```

## Usage

```bash
# Create a new worktree
worktree:create {
  branch: "feature/my-feature"  
  path: ".worktrees/my-feature"
}
```

---

**Files:** 
- `.opencode/plugins/worktree.ts` → SKILL documentation  
- **LOC reduction:** 1215 lines → ~200 lines effective (docs replace implementation)
