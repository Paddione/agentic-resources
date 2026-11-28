---
name: postgres-audit
description: "Evaluate existing PostgreSQL databases or clusters for schema integrity, normalization, query performance and maintenance. Use for database quality reviews, DB health checks and audits, normalization and business invariants (functional dependencies, candidate keys, tenant boundaries, 1NF/2NF/3NF/BCNF), and query cost, index design, locking, vacuum and EXPLAIN diagnosis. Produces evidence and recommendations without implementing fixes. Read-only diagnosis only; for sanctioned migrations, index changes or tuning use database-specialist."
---

# PostgreSQL audit

## Repo-Graph zuerst (nur bei Code-Suche)

Suchst oder navigierst du Repo-Code, beginne am zentralen MCP-Hub `fleet-workspace`: `search_graph` → `trace_path` → `get_code_snippet`; Übersicht via `get_architecture`/`query_graph`/`search_code`. Nicht indiziertes Projekt zuerst mit `index_repository` indizieren. Belegpfade mit `check_index_coverage` prüfen und Lücken benennen. `grep`/`rg` nur für nicht-indizierte Nicht-Code-Dateien oder als belegten Fallback. Details: SSOT-Skill `codebase-memory`.

Establish the actual target: cluster, namespace, instance, database, schemas, server
version, role, replica state and statistics window. Tool descriptions and topology
notes can be stale. Enumerate all databases when cluster scope is requested;
distinguish production, staging, development, restore copies and templates.

Use existing authorized access and prefer a restricted role. With psql use -X,
ON_ERROR_STOP=1, default_transaction_read_only=on and bounded statement/lock timeouts.
An audit runs no DDL, VACUUM, ANALYZE, statistics reset, extension installation or
application functions. Read-only transactions do not prevent external function effects.
Fetch schema and aggregate counts rather than secrets or personal row contents.

## Workflow

1. Read project database conventions, migration sources and existing authorization.
   Do not introduce approval gates for an already requested read-only analysis.
2. Inventory every scoped database. Use [collect.py](scripts/collect.py) with an
   explicit Kubernetes target and a restricted role
   (`--user audit_ro`; never add a `--password` flag — it would land in the
   output JSON under `target`). Requires Python 3, kubectl, authorized pod
   exec and psql inside the specified container. Writes local 0600 JSON
   evidence only (atomic temp-write, refuses to overwrite).
   Example: `python3 scripts/collect.py --context devmesh --namespace workspace --pod POD --container postgres --user audit_ro --output /tmp/audit.json`
   Non-Kubernetes fallback: run the same [queries.json](references/queries.json)
   keys in order over direct `psql "$DSN"` with `-X -v ON_ERROR_STOP=1` and
   `PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=15000 -c lock_timeout=2000"`;
   store results as 0600 JSON with timestamp, DSN host/database (never the
   password), server version and stats reset. `collect.py` auto-selects
   `top_queries_legacy` below PG13 and `duplicates_legacy` below PG15, and
   skips `stats_info` below PG14 / `sequences` below PG10 with a reason.
3. Check PKs, constraint validation, FK index candidates, invalid/duplicate indexes,
   maintenance, transaction/lock age, sequence headroom, extensions and query costs.
   Route constraint/dependency findings to [integrity](references/integrity.md)
   (step 4) and index/workload findings to [performance](references/performance.md)
   (step 5).
4. For functional dependencies and business integrity load
   [integrity](references/integrity.md). Check suspected violations
   with bounded aggregate probes and compare the actual application write paths.
5. For measured query tuning load [performance](references/performance.md).
6. Compare migration records with repo migrations when a ledger exists. Dynamic
   initialization limits parity claims. Vendor schemas follow the vendor migration
   system; do not propose unsupported manual normalization of third-party applications.

## Results

Each finding needs ID, priority, database/schema/table, measured evidence, consequence,
recommendation and validation/rollback approach. Distinguish confirmed anomalies,
missing enforcement, performance candidates and unknowns. Record timestamp, SQL,
source revision and statistics reset. Include positive checks and unreachable targets.
Do not claim 100% integrity or guaranteed speedups.

The FK-index detector finds missing full B-tree coverage, not proof an index is needed.
Inspect partial predicates before proposing redundant full indexes. Never remove indexes
solely because scan counts are zero. Duplicate candidates need constraint/dependency checks.
Keep raw schema/workload evidence local (0600) unless publication is authorized; redact literal secrets from DEFAULT expressions first. Executing fixes
is outside the audit request: to implement, load `database-specialist` with finding IDs plus the evidence path. See [sources.md](references/sources.md) for provenance.
