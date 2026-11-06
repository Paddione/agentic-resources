# GOAL: OD-2 Inspector-Unifizierung (agentic-resources)

## Objective
Doppelte Dataset-Inspektoren und Format-Helper in eine geteilte
Bibliothek überführen, Validate-Graph in komponierbare Checks zerlegen.

## Erfolgskriterien
- [ ] `domains/ml-training/huggingface-vision-trainer/scripts/dataset_inspector.py:546 main` (c45/259 Zeilen) + `domains/ml-training/huggingface-llm-trainer/scripts/dataset_inspector.py:202 main` (c33/206) → ein Shared-Modul + dünne Wrapper (`SIMILAR_TO`-Query belegt Konvergenz).
- [ ] `core/codebase-memory/scripts/validate_graph.py:11 validate` (c43/175) → komponierbare Checks.
- [ ] `domains/mcp/google-workspace/scripts/slides_helper.py:297 cmd_build` (c39) + Format-Helper (`safe_extract` fan-in 18) mit Property-Tests.
- [ ] Betroffene Skript-Tests grün.

## Nicht-Ziele
- Keine Lifecycle-Core-Splits ohne vorherige `DelegationManager`-State-Machine-Doku.
- Kein `viewer.html:1114 renderBenchmark`-Inline-JS im selben Schritt (Folge-PR).

## Abhängigkeiten
- Graph-Receipt agentic-resources 2026-11-06 (10.621/18.658).
- Master-Regel: Änderungen landen hier (nicht in `~/.agents/skills`-Symlinks).
