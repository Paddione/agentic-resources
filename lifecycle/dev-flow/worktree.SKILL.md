# worktree plugin

> Skript-Verweise gelten nur-wenn das Repo sie führt (Bachelorprojekt-Profil); sonst das Repo-Äquivalent aus `repo.yaml` bzw. `AGENTS.md` des Repos. Lifecycle-Mechanik immer über `python3 ~/scripts/agent-workspace.py`.

> OpenCode V2: this V1 plugin entrypoint is currently inactive. Create repo
> worktrees through `scripts/worktree-create.sh` until its tool and session (verboten, statt dessen `python3 ~/scripts/agent-workspace.py create --repo <repo> <branch>`)
> lifecycle are ported to the V2 plugin API.

Worktree management for OpenCode git isolation and temporary workspace creation. Enables feature branching via native git worktrees with automatic cleanup.

## Canonical path

All harnesses create worktrees at **`.worktrees/<slug>`** (repo-relative), delegated to `scripts/worktree-create.sh`. This ensures consistent guards (branch-name validation, divergence check, git-crypt handling, agent-lock checks) across every harness. (verboten, statt dessen `python3 ~/scripts/agent-workspace.py create --repo <repo> <branch>`)

| Harness | Worktree path | Mechanism |
|---------|--------------|-----------|
| **opencode** | `.worktrees/<slug>` | `worktree_create` tool → `scripts/worktree-create.sh` (verboten, statt dessen `python3 ~/scripts/agent-workspace.py create --repo <repo> <branch>`) |
| **agy** | `.worktrees/<slug>` | Treats opencode path as authoritative — same script, same guards |
| **Claude Code** | `.claude/worktrees/<branch>` | Built-in `worktree_create` tool (separate path, not delegated) |

Config: `.opencode/worktree.jsonc` sets `worktreePath: ".worktrees"`.

## Purpose

- Create isolated worktrees for feature/fix branches
- Automatic sync with main branch
- Cleanup after task completion (via `worktree:cleanup`)

## Usage

```bash
# Create a new worktree
worktree:create {
  branch: "feature/my-feature"
}

# ... do work in the worktree ...

# Cleanup when done
worktree:cleanup {
  worktreePath: ".worktrees/feature-my-feature"
}
```

## Architecture

- `createWorktree()` in `worktree.ts` delegates to `scripts/worktree-create.sh` (verboten, statt dessen `python3 ~/scripts/agent-workspace.py create --repo <repo> <branch>`)
- `TerminalPlugin` — Manages shell sessions and worktree creation
- State management via `state.ts` (14KB)
- Launch context injection in `launch-context.ts`

---

**Files:**
- `.opencode/skills/dev-flow/worktree.ts` → plugin entry, `createWorktree()` delegation
- `.opencode/skills/dev-flow/plugins/worktree/*.ts` → state, terminal, launch-context
- `.opencode/worktree.jsonc` → config (`worktreePath: ".worktrees"`)
- `scripts/worktree-create.sh` → canonical bash harness (all guards, git-crypt) (verboten, statt dessen `python3 ~/scripts/agent-workspace.py create --repo <repo> <branch>`)


## Framework mapping

| Framework | Availability |
|-----------|-------------|
| **Claude Code** | Not available directly. Equivalent: native Claude Code `dev-flow-plan` / `dev-flow-execute` / `dev-flow-chore` skills |
| **opencode** | Full — native skill for opencode |
| **agy** | Full — treats the opencode path as authoritative. All CLI tools and MCP calls work identically; worktrees land in `.worktrees/<slug>` via the same `scripts/worktree-create.sh` (verboten, statt dessen `python3 ~/scripts/agent-workspace.py create --repo <repo> <branch>`) |
