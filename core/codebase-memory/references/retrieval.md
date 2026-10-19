# Symbol embeddings and retrieval quality

Structural embedding means packaging a graph for a UI/agent. Vector embedding means representing source/intent numerically. They can share identity and provenance but are different artifacts.

## Durable vector contract

The existing Bachelorprojekt store uses `.codebase-memory/embed-index.jsonl` rows `{key, hash, model, dim, vector}` and `embed-manifest.json` with corpus hash, successful receipt, model/dimension and counts. Historic keys are `repo@commit:path:symbol`; these are snapshot identities. Content hashes bind model plus exact embedding input. Sync only deltas, prune stale keys, invalidate model/input changes and publish the pair as a consistent generation. Corrupt rows, duplicate keys, missing receipts, mixed dimensions and generation drift fail closed.

Include full qualified names, path, kind, signature, docstring and bounded body/context in embedding input. Handle long functions with source-aligned chunks carrying parent id and span. Deduplicate overlapping chunks at retrieval, retain test/generated flags and source provenance. Model/chunker/template changes invalidate vectors; verify finite values and dimension. Do not silently ignore symbols without docstrings. Report candidate, embedded, skipped and failed counts by language/kind.

Use the existing gateway endpoint/config; inspect its capabilities, budgets and retry contract. Batch with bounded concurrency, checkpoint and resume, then verify. Status and validation are read-only. Stale/unknown graph input does not become fresh vectors because an embedding call succeeded. An explicit stale diagnostic artifact must be marked stale throughout and not replace a fresh production store.

## Retrieval pipeline

Use exact/lexical lookup for known symbols. For intent, retrieve lexical and dense candidates independently, fuse with RRF, rerank with a supported cross-encoder, and then expose structural context with a bounded graph traversal. Keep source-backed results and explanations. Preserve K1 prose retrieval when K3 sections lack useful text.

The project evaluation dated 2026-10-04 measured Recall@10 0.469 fused, 0.828 with cross-encoder and 0.828 with post-rerank graph boost. Pre-rerank boost hurt recall by 0.250. These are historic observations, not portable performance guarantees. Do not attribute the cross-encoder gain to graph boost. Score boosts require calibration to the actual score scale and query-conditioned evidence.

## Evaluation

Create independently source-labelled queries, not labels inferred from the same graph being evaluated. Cover symbol names, intent, routes, docs, duplicate names, tests, unsupported syntax and deliberate absence. Hold out evaluation cases; freeze corpus/commit/receipt and model configs. Compare exact, lexical, dense, fused, cross-encoder and graph-context variants on the same cases. Report Recall@k, MRR/nDCG, latency, cost, token/tool budgets and per-kind misses. Graph edge precision and coverage require separate source-grounded samples. Release improvements only on measured benefit without hidden omissions.
