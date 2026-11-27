---
name: code-graph-interpretation
description: 'Pointer to the codebase-memory SSOT for repository code graph analysis. Use codebase-memory for code graph inspection, call paths, blast radius, symbol relationships, and K3 queries.'
---

# code-graph-interpretation — Verweis auf die SSOT

## Repo-Graph zuerst (nur bei Code-Suche)

Suchst oder navigierst du Repo-Code, beginne am zentralen MCP-Hub `fleet-workspace`: `search_graph` → `trace_path` → `get_code_snippet`; Übersicht via `get_architecture`/`query_graph`/`search_code`. Nicht indiziertes Projekt zuerst mit `index_repository` indizieren. Belegpfade mit `check_index_coverage` prüfen und Lücken benennen. `grep`/`rg` nur für nicht-indizierte Nicht-Code-Dateien oder als belegten Fallback. Details: SSOT-Skill `codebase-memory`.

**Der Inhalt dieses Skills wurde vollständig in [`codebase-memory`](../../../core/codebase-memory/SKILL.md)
konsolidiert. Lies dort weiter und folge dem Ablauf von dort.**

## Warum hier ein Verweis steht

`codebase-memory` ist die SSOT für alle Belange rund um Repository-Codegraphen (K3-Graph-Inspektion,
Call-Paths, Blast-Radius, Symbol-Beziehungen, Freshness-Checks, Validierung und Einbettungen).
Um redundante Anleitungen und divergierende Tool-Aufrufe zu vermeiden, verweist dieser Skill
direkt auf die SSOT.
