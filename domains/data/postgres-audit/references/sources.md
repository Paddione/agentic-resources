# Sources and local ownership

Own maintained skill, curated 2026-10-12. No automatic upstream synchronization.

Inspiration reviewed at pinned source revisions:
- Audit workflow and evidence-based read-only audit; independently written implementation. Corrected index comparisons, rollback interpretation, target verification and authorization handling:
  https://github.com/mvdmakesthings/skills/tree/4b32961c99875cb78d0058b400801b8f40f15103/plugins/specialist/skills/dba
- Normalization and relationship review; independently written guidance. Removed universal UUID, financial-history and negative-value prescriptions; added tenant equality, snapshots and counterexample probes:
  https://github.com/jacob-balslev/skills/tree/bbec0f9f7481e6c01fb791a433479140c65f6231/skills/software-architecture/entity-relationship-modeling
- Workload-driven PostgreSQL rules; independently written guidance. Added safe EXPLAIN scope, exact index semantics, partial-FK coverage and measured validation:
  https://github.com/supabase/agent-skills/tree/1207767388a0ffb55f21fb4e6988fee96942431d/skills/supabase-postgres-best-practices

The former `postgres-integrity` and `postgres-performance` skills were merged into
this skill as on-demand references (`integrity.md`, `performance.md`) in 2026-10.

No upstream source text or executable scripts vendored.

Authoritative PostgreSQL references (match the deployed major version):
- https://www.postgresql.org/docs/16/ddl-constraints.html
- https://www.postgresql.org/docs/16/pgstatstatements.html
- https://www.postgresql.org/docs/16/sql-explain.html
- https://www.postgresql.org/docs/16/monitoring-stats.html
