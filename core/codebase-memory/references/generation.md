# Generate an evidence-bearing graph

## Input contract

Record repository identity (portable slug, not host path), exact commit, tracked/untracked dirty-file hashes when included, scope, languages, parser/resolver versions, configuration digest and generated/vendor/test policy. Enumerate candidate files deterministically. Record excluded and failed files with reasons. Scope coverage includes files that produced zero symbols.

Use the existing backend. Inspect installed schemas/help before selecting indexing modes, persistence or cross-repo flags. A local 0.11.0 inspection exposed `index_repository` with full/moderate/fast/cross-repo-intelligence modes and optional native persistence; this is dated evidence, not a universal API. Native compressed persistence is not automatically a browser-portable graph.

## Parse and resolve

1. Parse definitions and imports into nodes with repository-relative paths and exact source spans. Include kind, qualified name, signature, language and test/generated flags.
2. Resolve lexical scope, aliases, imports and types where supported. Represent unresolved targets explicitly; do not invent a call edge because two names match. Separate external targets from source-addressable symbols.
3. Preserve edge kind and origin: parsed, inferred, semantic, historical or observed. Store method/strategy, source span and confidence where applicable. Similarity and co-change never become `CALLS`.
4. Resolve routes, configuration and service links using supported adapters. Verify both endpoints and route/config evidence for cross-service claims. Reflection, dynamic dispatch, callbacks, shell and unsupported syntax need explicit gaps/source checks.
5. Check coverage against the input inventory and inspect failures. File count, architecture size and node count do not measure recall.

## Refresh and publication

Acquire the established single-flight lock. Capture the input generation before work, recheck it afterward, and refuse to mix snapshots. Stage data in a temporary generation, validate it, then publish atomically with a successful receipt. Keep prior artifacts if parsing, extraction or validation fails.

Incrementally invalidate modified content, removed symbols/files, renamed paths, dependent resolution results and parser/config changes. A rename can legitimately change identity; store explicit verified lineage if required. Delete stale embedding keys. Hash the embedding text plus model/version and chunking config, not just the symbol name.

## Stable and snapshot identities

Use stable ids derived from repository identity + relative file path + kind + qualified name + signature/disambiguator; never line numbers alone. Overloads/nested functions need disambiguation. Snapshot ids additionally bind stable ids to commit/content hash. An id can persist through line insertion; arbitrary renames require explicit mapping. Emit deterministic sorting and content digests excluding timestamps to make repeated builds comparable.

## Export

Choose a bounded, useful view or a full artifact explicitly. Extract nodes, edges and coverage with supported paginated APIs. Inspect schema before writing Cypher; generic queries are not portable across engines. A `LIMIT` is a scope bound, not completeness proof. Preserve a snapshot cursor or lock/version-check the backend for the entire extraction. If node and edge queries lack a shared generation guarantee, freeze a verified backend snapshot or abort; do not fabricate one from current HEAD.

Record all relevant pagination state, exhaustion and limits. Reject cursor expiry or generation changes. Keep unresolved external endpoints as explicitly non-source nodes rather than dangling edges. Adapt raw fields to the portable contract; validate before publication.
