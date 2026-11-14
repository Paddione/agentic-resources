---
name: goal
description: Dateibasierter Ziel-Polyfill für Harness ohne natives Goal-Tracking; legt GOAL.md und PROGRESS.md an, prüft und schließt sie ab.
---

# Goal

Ein Ziel pro Ordner als Datei-Polyfill pflegen. Auf Muse mit nativem Goal das native Goal bevorzugen; der Datei-Spiegel entsteht nur auf Wunsch. Auf allen anderen Harnessen diesen Datei-Vertrag nutzen.

## Ablage

`.agents/goals/<slug>/GOAL.md` und `.agents/goals/<slug>/PROGRESS.md` im Ziel-Repo. Slug kleingeschrieben mit Bindestrichen. Keine Home-Pfade, keine fremden Dateien.

`GOAL.md` enthält Objective, Erfolgskriterien, Nicht-Ziele, Abhängigkeiten. Jedes Goal (bereits ab `0 %` beim Anlegen) deklariert darin zwingend `health_goals: [G-...]` (oder `health_probe: {"id":"G-...","title":"...","cmd":"...","target":0}`, oder `health_goals: none (<Begründung>)` für einmalige Migrationen/Refactors). `PROGRESS.md` enthält Prozent, Erledigt, nächste Schritte, offene Punkte (`Keine.` bei `100 %`).

## Operationen

Anlegen: Ordner und beide Dateien schreiben; Erfolgskriterien messbar formulieren und `health_goals:`/`health_probe:`/`none (<Begründung>)` sofort in `GOAL.md` festlegen (`goal-lint.mjs` `G6` ab `0 %`). Prüfen: beide Dateien lesen; Prozent und nächste Schritte nennen. Fortschreiben: Erledigtes nachtragen; Prozent ehrlich anpassen. Abschließen: erst bei belegten Erfolgskriterien und deklariertem `health_goals:`/`health_probe:`/`none (<Begründung>)`; `PROGRESS.md` auf `100 %` und `Offene Punkte` auf `Keine.` setzen.

## Regeln

Genau ein Ziel je Ordner. Erfolg ohne Beleg gilt nicht als Erfolg. Annahmen als Annahmen markieren. Kein Code und keine fremden Dateien als Nebeneffekt.

## Dev-flow-Anbindung (Modell B) & `/health`-Graduierung

Der Plan trägt das Goal: `dev-flow-plan` prüft aktive Goals und verlinkt bidirektional (`goal:` in `tasks.md`, `plan_refs:` in `GOAL.md`), `dev-flow-execute` schreibt belegte Fortschritte zurück. `goal-lint.mjs` erzwingt `G6` bereits ab `0 %` (und `plan-goal-gate.py` bei jedem verlinkten Plan) sowie `G7` bei `100 %`; das persistente `/health`-Goal `G-GOALS01` prüft alle Goals (`0 %`–`100 %`) auf `G6` und führt definierte `health_probe`-Kommandos bei abgeschlossenen Goals (`100 %`) dauerhaft aus. Chores und E2E bekommen kein eigenes Goal.
