# Migrations

1. Draft in `scripts/migrations/XX-<description>.sql`.
   Website-owned migrations live separately in
   `components/website/src/db/migrations/`.
2. Assess with `EXPLAIN` first; `EXPLAIN ANALYZE` executes the statement,
   so run it only against a safe copy.
3. Take backup evidence for destructive changes
   (`docs/runbooks/db-audit-playbook.md`: cluster-context guard,
   backup-before-DROP).
4. Apply via `task workspace:psql ENV=<env> -- <db> -f <file>`.
   `korczewski` stays excluded while frozen (T002479).
