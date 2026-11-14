---
name: goal
description: Dateibasierter Ziel-Polyfill für Harness ohne natives Goal-Tracking; legt GOAL.md und PROGRESS.md an, prüft und schließt sie ab.
---

# Goal

Ein Ziel pro Ordner als Datei-Polyfill pflegen. Auf Muse mit nativem Goal das native Goal bevorzugen; der Datei-Spiegel entsteht nur auf Wunsch. Auf allen anderen Harnessen diesen Datei-Vertrag nutzen.

## Ablage

`.agents/goals/<slug>/GOAL.md` und `.agents/goals/<slug>/PROGRESS.md` im Ziel-Repo. Slug kleingeschrieben mit Bindestrichen. Keine Home-Pfade, keine fremden Dateien.

`GOAL.md` enthält Objective, Erfolgskriterien, Nicht-Ziele, Abhängigkeiten. Abgeschlossene Goals (`100 %`) deklarieren darin zusätzlich `health_goals: [G-...]` (oder `health_probe: {"id":"G-...","title":"...","cmd":"...","target":0}`, oder `health_goals: none (<Begründung>)` für einmalige Migrationen/Refactors). `PROGRESS.md` enthält Prozent, Erledigt, nächste Schritte, offene Punkte (`Keine.` bei `100 %`).

## Operationen

Anlegen: Ordner und beide Dateien schreiben; Erfolgskriterien messbar formulieren. Prüfen: beide Dateien lesen; Prozent und nächste Schritte nennen. Fortschreiben: Erledigtes nachtragen; Prozent ehrlich anpassen. Abschließen: erst bei belegten Erfolgskriterien und deklariertem `health_goals:`/`health_probe:`/`none (<Begründung>)`; `PROGRESS.md` auf `100 %` und `Offene Punkte` auf `Keine.` setzen.

## Regeln

Genau ein Ziel je Ordner. Erfolg ohne Beleg gilt nicht als Erfolg. Annahmen als Annahmen markieren. Kein Code und keine fremden Dateien als Nebeneffekt.

## Dev-flow-Anbindung (Modell B) & `/health`-Graduierung

Der Plan trägt das Goal: `dev-flow-plan` prüft aktive Goals und verlinkt bidirektional (`goal:` in `tasks.md`, `plan_refs:` in `GOAL.md`), `dev-flow-execute` schreibt belegte Fortschritte zurück. `100 %` erst nach Merge plus Verifikation sowie bestandenen `goal-lint.mjs`-Regeln `G6`/`G7`; das persistente `/health`-Goal `G-GOALS01` überwacht alle umgesetzten Goals dauerhaft. Chores und E2E bekommen kein eigenes Goal.
