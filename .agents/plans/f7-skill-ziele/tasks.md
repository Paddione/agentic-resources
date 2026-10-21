---
title: F7 Skill-Ziele — Link-Matrix zwischen init.sh und Inventar abgleichen
domains: [runtimes, skills]
status: staged
branch: fix/f7-skill-ziele-20261021
---

# F7 Skill-Ziele — Plan

Ziel: Projekt- und Home-Ziele von `init.sh` widersprechen dem Inventar nicht mehr.

## File Structure

| Datei | Änderung (Worker-Output, unstaged) |
|---|---|
| `runtimes/init.sh` | Projekt 5 Dirs, Harness 9 Dirs, Kommentar mit Matrix-Begründung (`.opencode`-Ausnahme, Home-only-Roots) |
| `AGENTS.md`, `README.md`, `docs/follow-ups.md` | Matrix dokumentieren (73 Skills nachgezählt) |
| `tests/test_init_harness.py` | Harness-Matrix- und Dangling-Tests |

## Tasks

- [x] 1. Ziel-Listen angleichen und kommentieren.
- [x] 2. Doku (AGENTS/README/follow-ups) nachziehen.
- [x] 3. Verifikation im Worktree: `python3 -m pytest tests/test_init_harness.py -q` (Exit 0) und `bash -n runtimes/init.sh` (Exit 0).

## Abnahme

`init.sh`-Ziele und Inventar-Aussage stimmen überein; Ausnahmen sind begründet.
