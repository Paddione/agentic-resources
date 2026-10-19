# Shared operations and repository adapter

## Central MCP hub

Use the existing central MCP hub beside the central gateway as the client-facing surface. The gateway owns transport/authentication; the hub owns tool aggregation and discovery; graph and embedding services remain backends. Server registries are configuration authorities, not necessarily aggregators. Inspect the actual deployed hub routes before naming an endpoint or asserting a migration is complete.

Never create direct graph, embedding or database registrations in individual harnesses as a workaround for a missing hub tool. Diagnose registry -> hub route -> gateway -> harness -> tool result. Distinguish disabled, stale and unreachable entries. Preserve credentials in their existing private sources and keep owner-scoped workspaces. An already-running session may retain its tool list until restart.

The central hub's existing Codebase Memory route also exposes Python resource
markers through `index_python_resources`, `python_resource_status`,
`python_resource_environment`, `search_python_resources` and
`trace_python_resources`. Discover their live schemas. These nodes bind the
native generation and exact Python source/environment state; native Cypher does
not include the extension. Resource traces return source spans and native symbol
identities. `EntrySet` represents logical records, not enumerated runtime rows.
Read `mcp-servers/remote-workspace/python-resources.md` in the dotfiles repository
for supported providers, publication and known resolution gaps. Native CLI
refreshes require a subsequent marker refresh through the hub.

If hub tools are absent, report that fact and use exact source reads for the question. A locally installed CLI may be used explicitly for diagnostics or offline artifact work, without installing or registering a second MCP. Do not silently use it to evade hub access controls.

## Bachelorprojekt

Repository rules override generic commands. Use `bash scripts/vda.sh oracle '<goal>'` to resolve task commands. Project id and root must be discovered, not assumed from the historical `home-patrick-Bachelorprojekt` name.

Freshness helper: `scripts/mcp/cbm-freshness.py status --repo PATH --project NAME --timeout SECONDS`. Refresh goes through the repository's single-flight wrapper (`scripts/mcp/cbm-single-flight.sh`), resolved via the task oracle. Historic task names are `codebase:index` and `codebase:refresh`. Never run concurrent raw indexers, kill another session's indexer, or delete someone else's lock.

The receipt records a successful generation. Compare checkout, root, graph DB identity and dirty paths; a missing receipt, failed probe, root mismatch or interrupted refresh cannot be fresh. Skip indexing when fresh. Keep successful receipts on failed attempts and expose the failed attempt separately.

Embedding adapter: `scripts/mcp/cbm-embed-store.py`, `cbm-embed-sync.py`, `cbm-graph-rerank.py`, `cbm-eval.py`. Inspect their current help before constructing commands. They use the existing LLM gateway, not newly provisioned API credentials. Do not add cloud credentials for a skill evaluation.

Keep K1 authored-prose/semantic discovery, K3 structural relationships and authored architectural doctrine distinct. A symbol vector store does not replace documents. Repository-local `code-graph-interpretation` is legacy project guidance; use the shared workflow here and retain project deployment details in the repo.
