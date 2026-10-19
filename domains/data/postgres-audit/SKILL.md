---
name: postgres-audit
description: "Evaluate existing PostgreSQL databases or clusters for schema integrity, normalization, query performance and maintenance. Use for database quality reviews, DB health checks and audits, normalization and business invariants (functional dependencies, candidate keys, tenant boundaries, 1NF/2NF/3NF/BCNF), and query cost, index design, locking, vacuum and EXPLAIN diagnosis. Produces evidence and recommendations without implementing fixes."
---

# PostgreSQL audit

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
   explicit Kubernetes target, or adapt [queries.json](references/queries.json) to
   the available SQL connector. Requires Python 3, kubectl, authorized pod exec and
   psql inside the specified container. Writes local JSON evidence only.
   Example: `python3 scripts/collect.py --context fleet --namespace workspace --pod POD --container postgres --output /tmp/audit.json`
3. Check PKs, constraint validation, FK index candidates, invalid/duplicate indexes,
   maintenance, transaction/lock age, sequence headroom, extensions and query costs.
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
Keep raw schema/workload evidence local unless publication is authorized. Executing fixes
is outside the audit request. See [sources.md](references/sources.md) for provenance.
