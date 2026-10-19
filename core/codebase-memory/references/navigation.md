# Navigate and explain

| Question | First structural operation |
|---|---|
| Who calls X? | exact symbol -> trace inbound |
| What does X call? | exact symbol -> trace outbound |
| Call context or service impact | relevant both directions |
| Changed code -> impacted tests | diff seeds -> inbound with tests |
| Architecture | scoped overview + actual schema |
| Failure | supplied stack frame/test id -> exact path/symbol |
| Intent search | lexical+dense candidates -> source -> graph |

Use `search_graph` to resolve ambiguous names. Keep qualified name, path, kind, total/has_more and selected generation. Confirm source at the returned span. Keyword `query` can override `name_pattern`; inspect schema. `trace_path` directions are `inbound`, `outbound`, `both` in the locally inspected tool. Historical `callers`/`callees` strings yielded misleading empty results; never substitute them without schema support.

Start depth 1-2 and bounded scope. Retain seed, direction, edge kinds, hop depth and truncation. `query_graph` was inspected with snapshot cursor support and a 99,998 visible-row maximum in CLI 0.11.0; do not reuse the old 100k claim. Consult live help. Use cursor pagination where available and exhaust every relevant page. Offset pagination requires generation stability. Preserve errors/omitted fields as errors, not empty answers.

## Evidence tiers and source

Scout finds provisional positive anchors. Verify confirms material anchors/relationships with targeted source and complete relevant pages. Auditor bounds the exhaustive claim, establishes a fresh generation, checks every claimed scope and resolves all recorded gaps. No tier guarantees runtime completeness.

After candidate paths are known, check coverage once for all paths (page if necessary). Add scopes for absence or exhaustive analysis. Read reported skipped ranges or unsupported scopes. Avoid re-reading every node; verify material relationships. Cross-service explanations require both source endpoints and route/config evidence.

## Impact, tests and absence

Deduplicate changed-symbol seeds by qualified id. Union inbound results retaining reasons, add outbound context where useful, distinguish direct and transitive candidates. Nodes are inspection candidates, not guaranteed breakages or business severity.

Tests may be excluded by default. Explicitly include tests for test impact and inspect schema for `TESTS`/`TESTS_FILE`; do not presume those edge types exist. Runtime E2E route coverage needs test/helper source evidence. Graph-based selection supplements required repository checks; it does not prove exhaustive test coverage.

Zero degree is an unused-code heuristic, not a deletion certificate: check exports, framework registration and dynamic uses. Total degree includes definitions/imports, not just callers. Neither bounded traversal nor arbitrary Cypher proves global shortest paths.

On empty results validate project, identity, freshness, direction, test flags, limits, response shape and coverage. Report explicit results, bounds, source checks and remaining hypotheses. An absence report should contain project/generation, seed, query, direction, depth, test inclusion, pagination, coverage and exact source fallback. Retry only after fixing parameters or changing a hypothesis.

## UI and agent handoff

Offer exact-name search, intent search, breadcrumbs/backtracking, focus neighborhood, expand inbound/outbound, edge-kind and test/generated filters, route/service views and source links at the indexed revision. Show receipt and coverage gaps prominently. Use lazy loading and node/edge budgets; never silently truncate. Explain why a result was retrieved and why an edge exists. Preserve state in shareable snapshot-bound links.

Render repository text as text, not executable HTML. Use relative source locations and an explicitly configured source-link adapter. A self-contained widget should need no backend credentials or absolute local paths. Large graphs need chunked data/worker indexing, not an unbounded force-layout on every load.

For delegation or compaction pass tier, project/root/generation, scope, exact symbols, queries, pages/cursors, relationships, coverage gaps, source checks and unresolved questions. A child without graph access uses supplied evidence and targeted reads; never claim inherited MCP access.
