---
name: goal
description: Dateibasierter Ziel-Polyfill für Harness ohne natives Goal-Tracking; legt GOAL.md und PROGRESS.md lint-konform an, schreibt belegten Fortschritt fort und schließt Goals erst bei belegten Kriterien ab. Trigger auf Goal anlegen, Goal-Stand prüfen, Fortschritt nachtragen, Goal abschließen, Übergabe von setgoal.
---

# Goal

## Repo-Graph zuerst (nur bei Code-Suche)

Suchst oder navigierst du Repo-Code, beginne am zentralen MCP-Hub `fleet-workspace`: `search_graph` → `trace_path` → `get_code_snippet`; Übersicht via `get_architecture`/`query_graph`/`search_code`. Nicht indiziertes Projekt zuerst mit `index_repository` indizieren. Belegpfade mit `check_index_coverage` prüfen und Lücken benennen. `grep`/`rg` nur für nicht-indizierte Nicht-Code-Dateien oder als belegten Fallback. Details: SSOT-Skill `codebase-memory`.

Ein Ziel pro Ordner als Datei-Polyfill pflegen. Auf Muse mit nativem Goal das native Goal bevorzugen; der Datei-Spiegel entsteht nur auf Wunsch. Auf allen anderen Harnessen diesen Datei-Vertrag nutzen.

## Ablage

`.agents/goals/<slug>/GOAL.md` und `.agents/goals/<slug>/PROGRESS.md` im Repo, dessen Code das Goal ändert (z. B. Spiel-Goals in `unity-sandbox`, Tooling-Goals in `~`). Slug kleingeschrieben mit Bindestrichen. Keine fremden Dateien.

`GOAL.md` übernimmt das Prompt-Format aus `setgoal` (Objective, Ist-Befunde, Entscheidungen, Erfolgskriterien mit Nachweis, Nicht-Ziele, Abhängigkeiten). Pflicht ab `0 %` (`G6`): `health_goals: [G-...]`, `health_probe: {"id":"G-...","title":"...","cmd":"...","target":0}` oder `health_goals: none (<Begründung>)`. Nach der Planung kommt `plan_refs: [<pfad>/tasks.md]` dazu.

`PROGRESS.md` exakt so (der Parser liest nur diese Form):

```markdown
# Progress: <slug>

Prozent: <ganze Zahl> %

## Erledigt
- <Datum>: <Kriterium N> — Beleg: <Commit-SHA, CI-Run-ID, Befehl + Ergebnis, Bildpfad>

## Nächste Schritte
- <konkret> (bei 100 %: Keine.)

## Offene Punkte
- <im Scope offen> (bei 100 %: Keine.)
```

Genau eine Prozentzeile, am Zeilenanfang, ohne Fettdruck, Spiegelstrich oder Nachkommastelle.

## Operationen

- **Anlegen:** Vorher aktive Goals (`< 100 %`) auf Überschneidung prüfen und ggf. fortschreiben statt neu anlegen. Beide Dateien schreiben, `node ~/scripts/goal-lint.mjs --repo <repo>` ausführen (still = grün), committen und landen. Erst nach dem Landen auf dem Default-Branch sehen Board und andere Agenten das Goal; "für andere freigeben" heißt landen plus `plan_refs`.
- **Prüfen:** beide Dateien lesen; Prozent, nächste Schritte und unbelegte Kriterien nennen.
- **Fortschreiben:** Erledigtes je Kriterium mit Beleg nachtragen; Prozent = Anteil belegter Kriterien, ehrlich gerundet.
- **Abschließen:** erst wenn jedes Erfolgskriterium einen Beleg in `Erledigt` hat. Dann `Prozent: 100 %`, `Nächste Schritte` und `Offene Punkte` auf `Keine.`, Lint grün, landen.

## Regeln

- Erfolg ohne Beleg gilt nicht als Erfolg. Messen statt schätzen. Annahmen als Annahmen markieren.
- Nicht stehen bleiben: Mit Umsetzungsauftrag nach dem Anlegen direkt in `dev-flow-plan`/`dev-flow-execute`, ohne "Soll ich starten?". Kein Goal nach Code-Merge unter `100 %` lassen, außer bei echtem Blocker (fehlende Credentials, Hardware, Eigner-Stopp), der konkret unter `Offene Punkte` steht.
- Warte-blockierte Kriterien ("nächster Nightly", "nach einer Woche") in selbst auslösbare Nachweise umwandeln (Lauf per `workflow_dispatch` oder lokal starten, Probe ausführen) und die Umformulierung in `GOAL.md` vermerken.
- Scope-fremde Befunde gehören nicht in `Offene Punkte` (sie blockieren sonst `G7`): kleine Fixes direkt mitnehmen, wenn sie den Abschluss nicht verzögern, sonst in der Abschlussmeldung nennen oder als Folge-Goal vorschlagen.
- Kriterium nachträglich ändern nur mit Vermerk unter `## Entscheidungen` (Grund, Datum); Kriterien nie still streichen.

## Dev-flow-Anbindung (Modell B) & `/health`-Graduierung

Der Plan trägt das Goal: `dev-flow-plan` prüft aktive Goals und verlinkt bidirektional (`goal:` in `tasks.md`, `plan_refs:` in `GOAL.md`), `dev-flow-execute` schreibt belegte Fortschritte zurück. `goal-lint.mjs` erzwingt `G6` ab `0 %` (und `plan-goal-gate.py` bei jedem verlinkten Plan) sowie `G4`/`G7` bei `100 %`; das persistente `/health`-Goal `G-GOALS01` prüft alle Goals auf `G6` und führt `health_probe`-Kommandos abgeschlossener Goals dauerhaft aus. Chores und E2E bekommen kein eigenes Goal.
