---
name: worktrees
description: Create, inspect, integrate, and clean up Git worktrees for isolated implementation or parallel work, respecting repository conventions and existing authorization.
---

# Git Worktrees

Use worktrees when isolation helps the requested work or the repository requires them. Follow project instructions for branch names, base revisions, locks, and creation helpers. Worktrees do not themselves authorize delegation, commits, publication, or integration.

## Inspect and choose

Use explicit repository paths (`git -C <repo> ...`). Inspect `status --short`, the current branch, and `worktree list --porcelain` before mutation. Identify ownership of existing worktrees; reuse a suitable task worktree instead of creating a duplicate. Preserve unrelated dirty changes in the main checkout.

Prefer the repository's worktree convention and helper. For Bachelorprojekt, consult its current `AGENTS.md`: `.worktrees/<slug>` and its creation helper take precedence over OMO defaults. Otherwise choose an appropriate path; `.slim/worktrees/<slug>` is an optional OMO convention, not a requirement. Verify that a nested worktree directory is ignored before creating it; use an existing ignore rule or a narrow local exclude rather than rewriting tracked ignore files unnecessarily.

Select the intended base explicitly. Check branch/path collisions, and determine whether a remote update is needed for this task. Do not reset or pull a dirty main checkout merely to create a separate worktree.

## Create and work

Routine creation of an isolated worktree and branch can proceed within an authorized implementation task. Do not request redundant confirmation. For an ordinary repository without a required helper:

```text
git -C <repo> worktree add -b <branch> <absolute-worktree-path> <base>
```

Set edit paths and command working directories to that worktree. Check prerequisites there; ignored dependencies, local environment files, submodules, and encrypted files may require repository-specific setup. Do not copy secrets or a dirty checkout wholesale.

If parallel agents are authorized and useful, give each clear ownership and an explicit worktree path. Otherwise work directly. Optional OMO metadata (`.slim/worktrees.json`) may be maintained when already in use; Git's worktree list remains authoritative. Do not create a second coordination system when repository locks already cover the need.

## Verify and integrate

Review the final diff against the intended base and run required project checks plus proportionate checks for the change. Commit, publish, or integrate only within existing authorization and project workflow. If approval is still required, prepare the concrete diff and verification results first. Do not repeatedly ask for an action already authorized.

## Clean up without losing work

Before removal, check tracked and untracked changes, ignored artifacts that may matter, and whether another process or agent still owns the worktree. Verify that intended changes are integrated or durably preserved; squash merges may need PR/commit evidence because ancestry alone will not establish preservation.

Remove an owned, clean, disposable worktree with ordinary `git worktree remove <path>` when cleanup is within scope. Stop if Git refuses; inspect the reason instead of retrying with `--force`. Do not discard dirty files, delete unpreserved branches, reset another checkout, or prune unavailable worktrees without specific authorization. Branch deletion is a separate action: inspect preservation and use the repository's cleanup workflow. Never assume removal of a worktree also deletes its branch.

Release task-owned locks and update existing metadata. Report the remaining branch/worktree when preserving unfinished work. Do not invent an integration or cleanup success that was not verified.
