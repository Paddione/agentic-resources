---
name: codebase-memory
description: Build, refresh, export, embed, validate, and navigate repository code graphs (repo-code-graph). Use for graph generation, portable graph artifacts, symbol embeddings, architecture exploration, callers/callees, failure-to-code navigation, test/change impact, coverage and graph freshness. Consolidates code-graph-interpretation and K3 graph/embedding expertise. Do not use for unrelated charting or a trivial known-file text lookup.
compatibility: Harness-independent. Use tools exposed by the central MCP hub; Python 3 for the bundled portable-artifact validator. Codebase Memory CLI is an explicit local diagnostic fallback, not a new MCP registration.
---

# Repository code graphs

Make navigation reproducible and source-grounded. A useful graph resolves the right symbol, explains its relationships, exposes gaps, and opens the exact source at the indexed revision. More nodes or attractive layouts alone do not establish quality.

This directory is the shared authority for generation, interpretation, portable exports, and symbol embeddings. Keep repository-specific deployment and task routing in the repository. Read [operations](references/operations.md) for the central hub and Bachelorprojekt adapter, [generation](references/generation.md) when building, [navigation](references/navigation.md) when exploring, [portable artifact](references/portable-artifact.md) when embedding in a UI, and [retrieval](references/retrieval.md) for vectors and evaluation. [Sources](references/sources.md) records consolidation provenance.

## Establish identity and scope

1. Discover the available graph tools through the central MCP hub. Do not install a duplicate backend or register a direct per-harness server to bypass it. Tool names may be hub-prefixed; map by the actual schema, not a fixed namespace.
2. Obtain `list_projects` and `index_status`. Record selected project, actual root/worktree, graph generation or successful receipt, tool/schema version, checkout SHA, dirty state and query scope. Missing or failed probes mean **unknown**, never fresh. Git HEAD in tool metadata alone is not proof of a successful index.
3. Choose the deliverable: read-only navigation, index/refresh, portable UI artifact, vector store, or a combination. Default to existing tooling and a bounded repository/subsystem. A request to improve a skill does not authorize indexing every repository or publishing its sources.
4. Choose an evidence tier: Scout for provisional positive discovery; Verify (default) for task-directed queries, complete relevant pages and source checks; Auditor for bounded exhaustive analysis with current receipt and source fallback for every coverage gap.

## Generate and package

For generation follow [generation](references/generation.md). Inventory inputs, parse and resolve with declared language support, record unresolved relationships, serialize writers, and publish only a complete validated generation. Handle deletions, renames, parser/config changes and vector invalidation. Retain the previous successful generation on failure.

For a portable graph follow [portable artifact](references/portable-artifact.md). Export from one immutable generation; preserve identities, edge evidence, file hashes, coverage and pagination evidence. Adapt backend rows to the documented JSON contract, then run:

```bash
python3 <this-skill>/scripts/validate_graph.py graph.json
python3 <this-skill>/scripts/validate_graph.py graph.json --repo /exact/indexed/checkout
```

The first verifies structure; the second verifies referenced file bytes and source spans. Neither proves parser completeness or runtime behavior. The script does not export or index a graph. No undocumented `export_graph` command is assumed. Native backend persistence is a separate format.

## Navigate with evidence

Use schema and compact architecture to orient, exact qualified symbols to anchor, then relevant relationships. Read [navigation](references/navigation.md), including pagination, invalid-direction regression, test inclusion, absence handling and handoff requirements.

Once candidate paths are known, call `check_index_coverage` for all evidence paths. Include the claimed scopes for negative/exhaustive conclusions. Page through diagnostics; a clean check means no recorded gap, not proof of completeness. Read the reported ranges/scopes for partial, excluded, unsupported, stale, pending or unknown coverage.

Prefer exact symbol and lexical lookup first for known names; hybrid lexical+dense retrieval for intent queries; graph traversal for relationships. Semantic similarity, observed traces, inferred routes and parsed calls remain distinct. Read [retrieval](references/retrieval.md) before changing embeddings or ranking.

## Derive code improvements

When the request asks what to improve in the underlying code, pair this skill with the installed `code-analyzer` skill. Supply verified graph/source evidence, scope, generation receipt and limitations. That skill adds change history, impact/effort prioritization, bounded changes and testable acceptance criteria. Degree, cycles and zero callers are investigation signals, not automatic refactoring or deletion decisions.

## Verify success

Compare the same source-grounded cases before and after. Include duplicate names, methods, route-to-handler, callers, test impact, cross-service boundaries, deleted/renamed symbols, dirty checkout, unsupported syntax, deliberately absent symbols, and pagination overflow. Measure resolution accuracy, edge precision, coverage by language, Recall@k/MRR, latency, artifact size and tokens/tool calls. Report misses and unsupported cases instead of dropping them. Separate retrieval ablations to attribute gains correctly.

Deliver artifact paths, indexed revision/receipt, exact scope, build and validator results, measured navigation quality, and unresolved gaps. A validated schema is not a perfect graph. Do not claim a full export from a truncated query or global shortest paths from bounded traversal.
