# worktree plugins

> Skript-Verweise gelten nur-wenn das Repo sie führt (Bachelorprojekt-Profil); sonst das Repo-Äquivalent aus `repo.yaml` bzw. `AGENTS.md` des Repos. Lifecycle-Mechanik immer über `python3 ~/scripts/agent-workspace.py`.

Worktree management for OpenCode git isolation and temporary workspace creation. Enables feature branching via native git worktrees with automatic cleanup.

## Canonical path

All harnesses (opencode, agy) create worktrees at **`.worktrees/<slug>`** via `scripts/worktree-create.sh`. Config: `.opencode/worktree.jsonc` (`worktreePath: ".worktrees"`). (verboten, statt dessen `python3 ~/scripts/agent-workspace.py create --repo <repo> <branch>`)

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

- `createWorktree()` delegates to `scripts/worktree-create.sh` (canonical bash harness) (verboten, statt dessen `python3 ~/scripts/agent-workspace.py create --repo <repo> <branch>`)
- `TerminalPlugin` — Manages shell sessions and worktree creation
- State management via `state.ts` (14KB)
- Launch context injection in `launch-context.ts`

---

**Files:**
- `.opencode/skills/dev-flow/worktree.ts` → plugin entry, `createWorktree()` delegation
- `.opencode/skills/dev-flow/plugins/worktree/*.ts` → state, terminal, launch-context
- `.opencode/worktree.jsonc` → config
- `scripts/worktree-create.sh` → canonical bash harness (guards, git-crypt, agent-lock) (verboten, statt dessen `python3 ~/scripts/agent-workspace.py create --repo <repo> <branch>`)

**Related:** [dev-flow-execute](.claude/skills/dev-flow-execute/SKILL.md)
