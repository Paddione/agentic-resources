---
name: goal
description: Dateibasierter Ziel-Polyfill für Harness ohne natives Goal-Tracking; legt GOAL.md und PROGRESS.md an, prüft und schließt sie ab.
---

# Goal

Ein Ziel pro Ordner als Datei-Polyfill pflegen. Auf Muse mit nativem Goal das native Goal bevorzugen; der Datei-Spiegel entsteht nur auf Wunsch. Auf allen anderen Harnessen diesen Datei-Vertrag nutzen.

## Ablage

`.agents/goals/<slug>/GOAL.md` und `.agents/goals/<slug>/PROGRESS.md` im Ziel-Repo. Slug kleingeschrieben mit Bindestrichen. Keine Home-Pfade, keine fremden Dateien.

`GOAL.md` enthält Objective, Erfolgskriterien, Nicht-Ziele, Abhängigkeiten. `PROGRESS.md` enthält Prozent, Erledigt, nächste Schritte, offene Punkte.

## Operationen

Anlegen: Ordner und beide Dateien schreiben; Erfolgskriterien messbar formulieren. Prüfen: beide Dateien lesen; Prozent und nächste Schritte nennen. Fortschreiben: Erledigtes nach tragen; Prozent ehrlich anpassen. Abschließen: erst bei belegten Erfolgskriterien; `PROGRESS.md` auf 100 Prozent setzen.

## Regeln

Genau ein Ziel je Ordner. Erfolg ohne Beleg gilt nicht als Erfolg. Annahmen als Annahmen markieren. Kein Code und keine fremden Dateien als Nebeneffekt.
