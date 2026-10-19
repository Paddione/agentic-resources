# Consolidation provenance

Consolidated on 2026-10-09 from local sources:

- Former global `.zcode/skills/codebase-memory/SKILL.md`: query routing, evidence tiers, coverage and child handoff. Its old fixed tool-count and 100k query ceiling were replaced with live schema inspection.
- `Bachelorprojekt/.opencode/skills/code-graph-interpretation/SKILL.md` and `references/test-impact-analysis.md`, `references/synthesis-and-goals.md`: snapshot checks, invalid-direction regression, failure/diff seeds, impact, absence, tests and evaluation goals.
- `Bachelorprojekt/docs/brain/k3-code-graph.md` and `docs/runbooks/cbm-index-stampede.md`: indexing, receipt freshness, serialized refresh and repository operations.
- `Bachelorprojekt/docs/brain/embed-store.md` and `embed-rerank-eval.md`: durable receipt-keyed vector artifacts and independently attributable retrieval evidence.

These paths belong to the original repositories, not this skill. The operational project docs remain authoritative for deployments; generic knowledge is maintained here. Do not duplicate current project fleet configuration into harness-specific skills.

Local CLI 0.11.0 `--help`, `cli index_repository --help`, `cli query_graph --help` and `cli check_index_coverage --help` were inspected. Verify installed schemas again when applying the skill.

Upstream primary source: https://github.com/DeusData/codebase-memory-mcp . Upstream features may differ from the locally installed binary. No language-count, timing or token-saving marketing claim is a quality acceptance criterion.
