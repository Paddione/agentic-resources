---
name: repo-scout
description: Parallel repository scouting for onboarding maps, repo-wide questions, and evidenced findings. Use for map/findings/ask runs over a whole repository. Not for single-file lookups.
---

# repo-scout

Scout any git repository with many agents at once and return one report.
Source of truth: dotfiles (`~/scripts/repo-scout.py`, `~/scripts/repo_scout/`).

> Skript-Verweise gelten nur-wenn das dotfiles-Repo mit scripts/repo-scout.py verfügbar ist.

## Prerequisites

- Local workers (OpenAI-compatible): Devmesh LLM Router `http://127.0.0.1:18235/v1`
  (models `worker`, `fast`, `default`), or primary direct on `http://127.0.0.1:1919/v1`.
- Deep backends on PATH (run read-only in a sanitized snapshot):
  `claude`, `codex`, `opencode`, `agy`.
- Config (optional): `~/.config/repo-scout/config.toml`.

## Commands

```bash
python3 ~/scripts/repo-scout.py <repo> --mode map [--deep 8] [--out DIR]
python3 ~/scripts/repo-scout.py <repo> --mode findings [--deep 8] [--no-crosscheck]
python3 ~/scripts/repo-scout.py <repo> --mode ask --question "..." [--deep 8]
```

## Outputs

`~/.cache/repo-scout/<repo>/<UTC>/` (or `--out`):
`digests.jsonl`, `findings.jsonl` (`maps.jsonl`/`answers.jsonl`),
`crosscheck.jsonl`, `report.md`, `run.json` (args, sha, dirty, backends, durations, failures).

Read `report.md` first, then `run.json` for coverage (area, digest status,
backend, outcome). Missing digests mean the run continued on size/churn
ranking; `not selected` areas were never deep-scouted.

## Rules

- Findings are hand-offs and do not authorize changes.
- Exit codes: 0 ok, 2 usage error (e.g. `ask` without `--question`),
  3 read-only violation (target changed during the run, report invalid).
