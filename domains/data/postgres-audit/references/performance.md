# PostgreSQL performance

On-demand reference for the [postgres-audit](../SKILL.md) workflow. Load this
file when step 5 of the audit applies: measured query tuning with workload evidence.

Start with version, workload, volume and latency/throughput targets. Separate high total
cost, frequent cheap calls and slow individual calls. Filter pg_stat_statements by current
database, recording reset and deallocation. Separate backups, migration/initialization
work and application traffic. Report query IDs and sanitized shapes; utility query text
can include secrets. Inspect repository callers as well as database statistics.

Use plain EXPLAIN first. EXPLAIN ANALYZE executes the statement. During a read-only audit
do not analyze DML or volatile application functions; rollback cannot undo sequence or
external effects. Benchmark changes in an authorized representative safe environment.

Choose indexes from predicates, joins, ordering, selectivity and existing coverage.
Account for write overhead, size, partial predicates, operator classes, INCLUDE,
expression keys and null semantics. FK indexes affect performance, not FK enforcement.
Seq scans can be optimal. Check vector operators, dimensions, filtering, planner choice
and recall requirements before changing ANN indexes or planner settings.

Repeated DDL/catalog initialization on request paths can dominate query costs. Confirm
callers and migrate initialization into the established deployment mechanism with rolling
version compatibility. Do not assume CREATE IF NOT EXISTS makes repeated DDL free.

## Interpretation safeguards

- Counters are cumulative. Use deltas for current behavior; restart is not necessarily
  reset. Deallocation limits coverage. Rollbacks include intentional rollbacks.
- Shared-buffer misses may hit OS cache; a low hit ratio alone does not prove low RAM.
- Dead tuple estimates do not measure physical bloat. Check vacuum thresholds, table
  options and long transactions. No current blocker does not exclude past incidents.
- Zero index scans requires checking reset windows, rare jobs and replicas. Constraint
  indexes enforce rules even without scans. Invalid unique indexes may still enforce.
- Duplicate comparison includes method, keys/INCLUDE, expressions, predicates, opclasses,
  collations, ordering, uniqueness, NULLS NOT DISTINCT and dependencies/replica identity.
- Missing full FK indexes are candidates; partial indexes may already cover all relevant
  non-null probes. Do not add a redundant index automatically. The audit checks full
  B-tree coverage first and inspects partial predicates before proposing anything.
- Sequence headroom depends on both sequence bounds and column bounds, increment and
  cycle policy. Check transaction ID age independently.
