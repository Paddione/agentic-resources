# PostgreSQL integrity and normalization

On-demand reference for the [postgres-audit](../SKILL.md) workflow. Load this
file when step 4 of the audit applies: suspected functional-dependency or
business-invariant violations.

Read tables, constraints, triggers and application write paths. Resolve the business
meaning of fields before declaring redundancy a defect. For central relations record
candidate keys, dependencies (A -> B), enforcement and counterexamples.

Check partial-key and transitive dependencies against all candidate keys, not only the
chosen primary key. Propose lossless decompositions and state whether dependencies
remain enforceable. Column count alone does not identify a normalization violation.

Historical snapshots (invoice addresses, audit actor names) may intentionally duplicate
mutable entities. Do not replace them with joins that rewrite history. Arrays/JSON are
not inherently defects; relationships needing per-element FKs, uniqueness or lifecycle
usually warrant junction tables. Opaque document payloads may remain JSON.

Check NOT NULL separately from CHECK, null uniqueness semantics, composite tenant FKs,
ON DELETE behavior, unvalidated constraints and disabled constraint triggers. UUIDs and
app filtering do not enforce tenant equality. Cross-table invariants need FKs, unique or
exclusion constraints, or concurrency-safe mechanisms, not table-reading CHECK functions.

For duplicated parent identifiers (chunk.document_id and chunk.collection_id), either
derive the latter or enforce the pair against a unique parent pair. Check cached counters
against source counts, accounting for subset filters and eventual-consistency semantics.
Check ID arrays for unresolvable or duplicate elements before proposing a junction table.

Probe with aggregate counts, separating fixtures and actual data. Zero current anomalies
does not prove enforcement. Review concurrent writes and all write paths. State business
assumptions explicitly. Money can legitimately be negative (refunds/cancellations).

Output current anomaly, future risk and proposed invariant separately. Migration proposals
include conflict policy, backfill, concurrent writes, validation, lock cost, deployment
order and rollback. Do not execute migrations during an audit. Respect vendor-managed
schemas and their supported upgrade path.
