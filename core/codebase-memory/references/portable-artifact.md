# Portable graph contract v1

This is a local interchange contract, not a claimed native Codebase Memory export format. A backend adapter must produce it. JSON is embeddable in a widget after validation; use safe text rendering and source links bound to the manifest revision.

Top-level fields:

- `schema_version`: integer `1`.
- `manifest`: `repo` portable identity, `commit` full Git hash, `generation` successful immutable receipt identifier, `tool_version`, `scope` nonempty relative roots (use `.` for repository), `dirty` boolean, `complete` boolean, `pagination_exhausted` boolean. Dirty snapshots require `dirty_digest` (SHA256 of inventoried dirty inputs). `complete` refers to the declared scope/export, never runtime completeness.
- `files`: one row per inventoried in-scope file with relative POSIX `path`, file-byte `sha256`, `coverage` (`indexed`, `partial`, `excluded`, `unsupported`, `failed`, `unknown`) and nonempty `reason` for anything other than indexed. Optional `missed_ranges` uses inclusive 1-based `{start_line,end_line}`.
- `nodes`: unique `id`, `kind`, `qualified_name`, `origin` (`source` or `external`). Source nodes require inventoried `path`, inclusive `start_line`/`end_line`. External nodes require `reason` and have no source path/span. Optional signature, language, generated and test flags are retained.
- `edges`: unique `id`, existing `source`/`target` ids, `kind`, `evidence` (`parsed`, `inferred`, `semantic`, `historical`, `observed`), nonempty `strategy`. Optional `confidence` is finite 0..1; optional `path` with inclusive `start_line`/`end_line` provides inventoried evidence location. Preserve unresolved relationships as external nodes with reasons.
- Optional `embeddings`: `model`, positive `dimension`, `generation` matching the graph, `items` with unique `node_id`, SHA256 `input_sha256`, finite vector of exact dimension. Chunked vector stores may use a separate documented sidecar contract instead.

All paths are portable, canonical and repository-relative: reject absolute/drive/UNC paths, backslashes, empty segments and `..`. Symbols outside manifest scope are invalid. Each file appears exactly once. IDs are strings, not backend integer rowids. Retain deterministic stable ids plus snapshot provenance.

`complete=true` requires exhausted pagination and no partial/failed/unknown file entries. Excluded and unsupported files remain visible with reasons even in a completed export. An intentionally partial export has `complete=false` and passes structural validation with a warning; it cannot support exhaustive claims.

Validate: `python3 scripts/validate_graph.py artifact.json [--repo EXACT_CHECKOUT]` from this skill directory. Exit 0 means contract/source checks passed, exit 1 validation errors, exit 2 unreadable/invalid JSON or arguments. Output contains counts, issues and completeness. `--repo` checks file hashes, safe resolved paths and all source spans against file line counts, but does not verify Git identity, edge semantics or source parser recall; obtain those independently. No writes, networking, dependencies or indexing occur.

For production publish a manifest plus content-addressed data (or bounded JSON) atomically. Verify snapshot identity at export, hash artifact bytes, preserve unknown edge properties in an adapter metadata field, and never mark an interrupted/capped export complete. Load large artifacts lazily. An offline UI stores no backend credentials.
