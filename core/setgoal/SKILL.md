---
name: setgoal
description: Vage Anfrage in genau einer Fragerunde mit Empfehlungen klären und als idealen Goal-Prompt zur Ablage mit dem goal-Skill übergeben.
---

# Setgoal

Halbgare Anfrage in einen setzbaren Ziel-Prompt verwandeln. Danach nichts implementieren.

## Ablauf

Anfrage und governing Repo-Dateien lesen. Keine breite Suche nach hypothetischen Unklarheiten.

Genau eine Fragerunde stellen: alle Klärungspunkte (inkl. passender `/health`-Goals `health_goals: [G-...]` / `health_probe:` / `health_goals: none (<Begründung>)`) mit je Empfehlung und einem Satz Begründung, höchstens 3 Fragen pro Aufruf (Tool-Limit) — bei mehr als 3 Punkten hintereinander aufrufen (z. B. 3+1), bis alle gestellt sind; das zählt als eine Runde. Dann auf alle Antworten warten. Keine weitere Runde, außer eine Antwort öffnet einen neuen Sperrpunkt.

Danach den idealen Goal-Prompt ausgeben: Objective, Erfolgskriterien, Scope und Nicht-Ziele, Randbedingungen sowie das verbindliche `/health`-Feld (`health_goals: [G-...]`, `health_probe:` oder `health_goals: none (<Begründung>)` für `G6` ab `0 %`). Format so wählen, dass er direkt in den goal-Skill, ein natives Muse-Goal oder `dev-flow-plan` Schritt 0.5 passt.

## Regeln

Entdeckbare Fakten selbst recherchieren; nur Eigner-Entscheidungen fragen. Bereits genannte Fakten nie erneut fragen. Persistenz nur über den goal-Skill und nur auf Wunsch. Ohne Antwort keinen Prompt erfinden.
