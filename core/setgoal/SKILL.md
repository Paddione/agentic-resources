---
name: setgoal
description: Vage Anfrage in genau einer Fragerunde mit Empfehlungen zu einem oder mehreren lint-fertigen Goal-Prompts klären und je nach gewähltem Modus nur ausgeben, per goal-Skill anlegen oder anlegen und direkt umsetzen. Trigger auf /setgoal, "setz ein Ziel", "Ziele/Milestones vorschlagen", "mach daraus ein Goal".
---

# Setgoal

## Repo-Graph zuerst (nur bei Code-Suche)

Suchst oder navigierst du Repo-Code, beginne am zentralen MCP-Hub `fleet-workspace`: `search_graph` → `trace_path` → `get_code_snippet`; Übersicht via `get_architecture`/`query_graph`/`search_code`. Nicht indiziertes Projekt zuerst mit `index_repository` indizieren. Belegpfade mit `check_index_coverage` prüfen und Lücken benennen. `grep`/`rg` nur für nicht-indizierte Nicht-Code-Dateien oder als belegten Fallback. Details: SSOT-Skill `codebase-memory`.

Halbgare Anfrage in setzbare Goal-Prompts verwandeln. Vor der Freigabe nichts implementieren.

## Ablauf

1. **Lesen, nicht fragen.** Anfrage, governing Repo-Dateien (`AGENTS.md`, `repo.yaml`) und aktive Goals (`.agents/goals/*/PROGRESS.md` unter `100 %`, im Ziel-Repo und in `~/.agents/goals`) lesen. Überschneidet sich die Anfrage mit einem aktiven Goal, dessen Fortschreibung vorschlagen statt ein Parallel-Goal. Entdeckbare Fakten (Dateien, Ist-Zustand, vorhandene `G-*`-Health-Goals, Testbefehle) selbst erheben. Keine breite Suche nach hypothetischen Unklarheiten.
2. **Schneiden.** Ein Goal je unabhängig abnehmbarem Ergebnis. Sammelanfragen ("Ziele vorschlagen", "neue Milestones", "verbessere X substanziell") ergeben mehrere Goals mit Reihenfolge und Abhängigkeiten. Chores und reine E2E-Arbeit bekommen kein Goal.
3. **Eine Fragerunde, direkt im Chat.** Nur Eigner-Entscheidungen fragen (Umfang, Priorität, Geschmack, Abnahmeform), je mit Empfehlung (`(Empfohlen)` als erste Option) und einem Satz Begründung. Die Runde immer als genau eine Markdown-Nachricht im Chat stellen: nummerierte Fragen (Q1, Q2, …), je mit Optionen als Liste, erste Option ist die Empfehlung mit Suffix `(Empfohlen)`, letzte Option immer „Sonstiges – eigenen Text eingeben". Kein Tool-Aufruf dafür, kein Offloading über `hub_board_mcp__board_ask` oder ein anderes Board-/Walkie-Tool. Nach der Fragerunde den Turn beenden und auf alle Antworten warten.
   - Pflichtfrage **Modus**, außer die Anfrage legt ihn schon fest ("implementiere", "setz um", "leg an"): `Anlegen + planen + umsetzen (Empfohlen)` / `Nur anlegen` / `Nur Prompt`.
   - Nicht fragen, sondern selbst festlegen und im Prompt begründen: `/health`-Feld, Nachweisform je Kriterium, Slug, technische Umsetzung.
   - "du entscheidest", "wie du sagst" oder fehlende Präferenz heißt: Empfehlung übernehmen. "verklickt" oder "frag nochmal" heißt: dieselbe Runde erneut stellen. Eine neue Runde nur, wenn eine Antwort einen neuen Sperrpunkt öffnet.
4. **Prompt ausgeben** je Goal im Format unten. Bei mehreren Goals vorab eine Tabelle Slug, Ziel in einem Satz, Abhängigkeit.
5. **Übergabe nach Modus.**
   - `Nur Prompt`: Ende.
   - `Nur anlegen`: goal-Skill "Anlegen" ausführen, landen, Pfade melden.
   - `Anlegen + planen + umsetzen`: goal-Skill "Anlegen", dann `dev-flow-plan` und `dev-flow-execute` ohne weitere Rückfrage bis Merge und Goal auf `100 %`. Bei mehreren Goals in der Abhängigkeitsreihenfolge.

## Prompt-Format

Abschnittsnamen exakt so, damit der goal-Skill den Prompt 1:1 übernimmt und `goal-lint.mjs` (`G2`, `G6`) grün ist:

```markdown
# Goal: <slug>

health_goals: [G-...]

## Objective
<2–4 Sätze: Ergebnis aus Nutzersicht, nicht der Weg.>

## Ist-Befunde
- B1 <selbst erhobener Fakt mit Pfad/Befehl; Ausführende erheben ihn nicht erneut>

## Entscheidungen
- D1 <Eigner-Antwort oder begründete Eigenentscheidung>

## Erfolgskriterien
1. <Prüfbare Aussage> — Nachweis: <Befehl, Test, CI-Lauf, Screenshot, Messwert mit Schwelle>

## Nicht-Ziele
- <ausdrücklich ausgeschlossen>

## Abhängigkeiten
- <Goals, Dienste, Hardware; sonst "Keine.">
```

Statt `health_goals: [G-...]` geht `health_probe: {"id":"G-...","title":"...","cmd":"...","target":0}` (neue Dauerprüfung) oder `health_goals: none (<Begründung>)` (einmalige Migration). Vorhandene `G-*` vor einer neuen Probe prüfen.

Regeln für Erfolgskriterien:
- Jedes Kriterium nennt seinen Nachweis. Messen statt schätzen: Zahlen nur mit Messbefehl und Schwelle.
- Der Agent muss jedes Kriterium im selben Durchlauf selbst belegen können. Nicht "nächster Nightly grün" oder "eine Woche stabil", sondern den Lauf selbst auslösen (`workflow_dispatch`, lokaler Lauf, Probe). Echte Eigner-Abnahmen (Playtest, Geschmack) als solche markieren.
- Keine Kriterien, die außerhalb des Scopes liegen; Folgearbeit wird ein eigenes Goal.

## Regeln

Bereits genannte Fakten nie erneut fragen. Ohne Antworten keinen Prompt erfinden. Persistenz nur über den goal-Skill.
