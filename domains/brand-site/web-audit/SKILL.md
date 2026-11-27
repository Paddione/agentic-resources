---
name: web-audit
description: "Semantische Pruefung und Triage der eigenen Brand-Seiten ueber axe, Lighthouse und LLM. Kombiniert a11y-Scan (axe), Performance-Audit (Lighthouse) und semantische LLM-Beurteilung (alt-Texte, Meta-Tags, Ueberschriften, Link-Labels). Kein Merge-Gate — laeuft manuell. Triggers on web-audit, web:audit, semantic audit, semantische Pruefung, axe triage, llm review, page audit."
agent: bp-ship
---

# web-audit

## Repo-Graph zuerst (nur bei Code-Suche)

Suchst oder navigierst du Repo-Code, beginne am zentralen MCP-Hub `fleet-workspace`: `search_graph` → `trace_path` → `get_code_snippet`; Übersicht via `get_architecture`/`query_graph`/`search_code`. Nicht indiziertes Projekt zuerst mit `index_repository` indizieren. Belegpfade mit `check_index_coverage` prüfen und Lücken benennen. `grep`/`rg` nur für nicht-indizierte Nicht-Code-Dateien oder als belegten Fallback. Details: SSOT-Skill `codebase-memory`.

Semantische Pruefung und Triage der Brand-Seiten: kombiniert die vorhandenen technischen Audits
(`a11y:axe`, Lighthouse) mit einer LLM-basierten semantischen Beurteilung und erstellt eine
priorisierte Rangliste der Befunde.

**Kein Merge-Gate.** Der Skill laeuft manuell gegen die Live-Brands und entscheidet nicht ueber
PRs. Die Ausgaben sind ein Bericht unter `tmp/claude-scratch/web-audit-<brand>-<datum>.md` und
eine Kurzfassung auf stdout.

## Aufruf

```bash
task web:audit ENV=mentolder     # Standard-Routen: /, /ueber-mich, /kontakt, /coaching
task web:audit ENV=mentolder WEB_AUDIT_ROUTES="/,/leistungen"  # Eigene Routen
```

## Drei Stufen

1. **axe a11y-Scan** — delegiert an `task a11y:axe ENV=<brand>`. Die vorhandenen
   axe-core-Regeln werden unveraendert genutzt; der Skill definiert keine eigenen.

2. **Lighthouse** — delegiert an die vorhandene `lighthouserc.json`. Performance-,
   Accessibility-, Best-Practices- und SEO-Scores.

3. **Semantische LLM-Pruefung** — Playwright rendert die Seiten, extrahiert
   `alt`-Texte, `<meta>`-Tags, Ueberschriften-Hierarchie und Link-Labels mit Ziel-URLs.
   Kein rohes HTML. Das Modell beurteilt:
   - ob `alt`-Texte den Bildinhalt beschreiben und nicht nur Dateinamen sind
   - ob die Meta-Description Marken- und Leistungsbezug hat
   - ob Link-Labels ausserhalb ihres Kontexts verstaendlich sind
   - die Ueberschriften-Hierarchie

   Zusaetzlich erstellt das Modell eine **Triage-Rangliste** der Roh-Befunde aus
   Stufe 1 und 2 — nach Auswirkung auf echte Nutzer sortiert, mit Begruendung.

## Ausfallsicherheit

Jede Stufe ist einzeln ausfallbar. Keine Stufe bricht den Lauf ab. Ausgefallene Stufen
werden im Bericht ausdruecklich mit `FAILED` gekennzeichnet. Exit-Code ist auch bei
Fehlern 0.

## Abgrenzung

- Nur eigene Brands — aktiv nur `mentolder`; korczewski ist seit 2026-07-23 eingefroren (T002479, 0 Replicas), `web.korczewski.de` antwortet mit 503
- Keine visuelle Pruefung (Screenshots/Vision gehoeren zum Headed-E2E-Vorgang)
- Kein CI-Job — manueller Lauf
