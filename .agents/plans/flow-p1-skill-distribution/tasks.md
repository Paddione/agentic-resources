---
title: "P1: flow-p1-skill-distribution"
domains: [agent-workflows]
status: staged
plan_id: P1
depends_on_plans: []
base_commit: 9aa82c6bf1d615ee40f5e5520f63fdd1ba583ed4
execution: existing-plan-runner-direct
---
# flow-p1-skill-distribution — Implementation Plan

## File Structure

- `runtimes/init.sh`
- `tests/test_init_harness.py`

## Ziel

Siehe design.md. Basis 9aa82c6bf1d615ee40f5e5520f63fdd1ba583ed4. Die sechs Pläne werden nacheinander gestagt und ausgeführt. Frühere Plan-Ausführung muss verifiziert sein; fehlende Voraussetzungen werden nicht still übersprungen. P1–P3 sind Fixes, P4–P6 explizit beauftragte Auditpläne ohne Produktänderungen. Die explizite Auditplanung ersetzt hier den generischen Chore-Kurzschluss.

## Partials

| id | plan | role | target_files | depends_on |
| --- | --- | --- | --- | --- |
| p1 | tasks.d/p1-work.md | orchestrator | runtimes/init.sh, tests/test_init_harness.py | |

## Task 1: Facharbeit

- [ ] Partial ausführen.
- [ ] RED-Verifikation: expected: FAIL; `python3 -m pytest tests/test_init_harness.py -q` vor Korrektur. Danach grün.

## Budgets

- `runtimes/init.sh`: aktuell 75 Zeilen; keine konfigurierte S1-Baseline im Zielrepo.
- `tests/test_init_harness.py`: neu; keine konfigurierte S1-Baseline im Zielrepo.

## Task 2: Finale Verifikation und Übergabe

- [ ] `python3 -m pytest tests/test_init_harness.py -q`: expected Exit 0.
- [ ] `git diff --check`: expected Exit 0.
- [ ] Alle Änderungen innerhalb FILES, keine Secrets, keine geschwächten Assertions.
- [ ] Orchestrator verifiziert Ergebnis unabhängig. Worker markiert keine eigene Implementierung als gemergt.
- [ ] Host-/Windows-/Live-Checks ohne belegten Zugriff bleiben offen. Keine auto-Deploys.

Kein `task test:changed`, `task freshness:regenerate` oder `task freshness:check` ausführen: task_runner=none, generated_artifacts=false; oben stehen die tatsächlichen Repo-Befehle. Lokales scripts/plan-lint.sh und agent-lock.sh existieren hier nicht; kein fremdes Bachelorprojekt-Gate als Zielrepo-Gate ausgeben. Ersatz: YAML-/Datei-/Referenzprüfung, reale Runner-Manifestprüfung und RED-Beleg für Fixes.
