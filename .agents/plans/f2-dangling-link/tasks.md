---
title: F2 Dangling-Link — init.sh repariert nur tote Symlinks
domains: [runtimes, skills]
status: staged
branch: fix/f2-dangling-link-20261021
---

# F2 Dangling-Link — Plan

Ziel: `link_skill` ersetzt tote Symlinks, fasst echte Dateien nie an.

## File Structure

| Datei | Änderung (Worker-Output, unstaged) |
|---|---|
| `runtimes/init.sh` | Dangling-Fall (`-L` und nicht `-e`) per `ln -sfn` neu verlinken, sonst unverändert abbrechen |
| `tests/test_init_harness.py` | 2 Tests: tote Links werden repariert, echte Dateien bleiben unangetastet |

## Tasks

- [x] 1. Dangling-Zweig in `link_skill` einbauen.
- [x] 2. Beide Tests schreiben.
- [x] 3. Verifikation im Worktree: `python3 -m pytest tests/test_init_harness.py -q` (Exit 0) und `bash -n runtimes/init.sh` (Exit 0).

## Abnahme

Toter Link zeigt danach auf die Quelle; echte Datei bleibt Byte-identisch.
