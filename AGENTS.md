# AGENTS.md — Shared agent doctrine (agentic-resources SSOT)

This file is the shared instruction base for every repository that inherits
from `agentic-resources`. Repos with their own `AGENTS.md` keep it and point
here for the shared parts; repos without one symlink this file (and the
accompanying `CLAUDE.md`) to their root.

## What this repo is

Monorepo for all agent skills: harness-neutral base skills, lifecycle
workflows, opt-in domain packs, runtimes, and prompts. Follow-up projects
inherit via live symlink, never via fork.

- `core/` — harness-neutral base skills (`git-workflow`, hygiene, response,
  `references/` as shared hub).
- `lifecycle/` — `dev-flow-*`: plan, execute, chores, E2E.
- `domains/<pack>/` — opt-in domains (`testing`, `gitops`, `ml-training`,
  `brand-site`, `data`, `devtools`, `formats`, `research`, `mcp`, `web`,
  `misc`, `projects/` for project-specific examples).
- `runtimes/` — `init.sh`, `repo.yaml.schema`, profiles, scripts, prompts.
- `registry.json` — index of every skill with origin and upstream revision.
- `staging/` — merge working area, never inherited content.

## Inheriting (consumers)

```bash
./runtimes/init.sh --repo <pfad> --layers core,lifecycle,domains/testing --profile bachelorprojekt
```

Layers link skills as symlinks — additive, never overwriting real files — and
`repo.yaml` is created from the profile. `--layers all` for everything,
`--dry-run` for preview. Re-run after clones, renames, or skill moves.

## Consumer contract (`repo.yaml`)

Shared skills read repo specifics from `repo.yaml` in the consumer root —
main branch, scopes, task runner, generated artifacts, tickets — and never
hardcode them. No repo assumptions in shared files; parametrize, don't fork.

## Skill conventions

- Frontmatter (`name`, `description`) is Pflicht; third-person triggers.
- German, concise, no decoration. Facts over procedure in chat answers.
- External origin goes in `registry.json` under `upstream` with revision.
- One skill = one capability; route instead of duplicating.

## Workflows

- Change work: `dev-flow-plan` → `dev-flow-execute`; maintenance:
  `dev-flow-chore` (inline, then merge).
- Git lifecycle per `git-workflow`: pull-first, explicit pathspecs (never
  broad add), Conventional Commits, verify via the repo's own checks, PR,
  squash-merge, cleanup. No direct pushes to the main branch.
- Work in the target repo's checkout. This repo holds shared skills only;
  read-only questions work from anywhere, mutating work does not.

## Instruction inheritance

- This file + `CLAUDE.md` are the central pair. Light repos symlink both
  names to these files.
- Repos with their own `AGENTS.md` keep it (repo specifics win) and carry
  one pointer section here. Machine-global preferences live in
  `~/.claude/CLAUDE.md` / `~/AGENTS.md`, never shared doctrine.
