---
name: database-specialist
description: 'Use for sanctioned mutating PostgreSQL ops on the Bachelorprojekt platform (schema migrations, backup/restore, DB password sync, live tuning). Triggers on: schema migration, task workspace:psql/port-forward/backup/db:restore, workspace:sync-db-passwords, korczewski freeze T002479. Mutating fleet ops only; for read-only health/integrity evidence without changes use postgres-audit.'
---

# Database specialist (mutating ops)

Bachelorprojekt consumer overlay. Shared file carries no hardcoded
consumer-local behavior paths as normative requirements; repo specifics
resolve via the consumer repo (`repo.yaml`, `environments/*.yaml`,
`taskfiles/Taskfile.workspace.yml`). Routing to the `bp-run` role lives in
the consumer dispatch map, not in this frontmatter.

## Repo-Graph zuerst (nur bei Code-Suche)

Suchst oder navigierst du Repo-Code, beginne am zentralen MCP-Hub `fleet-workspace`: `search_graph` → `trace_path` → `get_code_snippet`; Übersicht via `get_architecture`/`query_graph`/`search_code`. Nicht indiziertes Projekt zuerst mit `index_repository` indizieren. Belegpfade mit `check_index_coverage` prüfen und Lücken benennen. `grep`/`rg` nur für nicht-indizierte Nicht-Code-Dateien oder als belegten Fallback. Details: SSOT-Skill `codebase-memory`.

## Library (Bachelorprojekt-consumer only)

At the start of every session in the Bachelorprojekt checkout, read these
consumer-local fragments before doing anything else:

- `.claude/lib/behaviors/never-push-main.md`
- `.claude/lib/behaviors/inject-plan-context.md`
- `.claude/lib/behaviors/tool-use-safety.md`

Outside that checkout these paths do not exist; do not treat them as
shared-skill requirements.

## Topology (verify before trusting)

- The `fleet` cluster context was decommissioned 2026-10-22. Treat any
  residual `fleet` reference as legacy until re-verified via
  `environments/*.yaml`. Live contexts are `devmesh`, `prodmesh`,
  `korczewski-prod` (see `environments/dev.yaml`, `environments/prodmesh-korczewski.yaml`).
- Namespaces `workspace` / `workspace-korczewski` remain valid.
- ENV values resolve via `env-resolve.sh` from `environments/*.yaml`
  (e.g. `dev`, `prodmesh-korczewski`). There is no `environments/mentolder*`
  file; `mentolder` is a standalone brand repo and not a valid ENV here.
- `korczewski` stays frozen (T002479, `suspend: true`): no migrations or
  writes while frozen. Detail: [freeze](references/freeze.md).

They share no data and have independent role passwords. Detail:
[references/topology.md](references/topology.md).

## Connection commands

```bash
# Interactive session (ENV from environments/*.yaml, e.g. ENV=dev)
task workspace:psql ENV=<env> -- <database>

# Port-forward for local tools (pgAdmin, DBeaver, etc.)
task workspace:port-forward ENV=<env>

# Schema introspection
task workspace:psql ENV=dev -- pocket_id -c "\d+"
```

Mechanism: `Taskfile.workspace.yml` resolves ENV to context/namespace and
execs `deploy/shared-db`. Never bypass the task wrapper with raw kubectl.
Detail: [references/connection.md](references/connection.md).

## Tracking schema (legacy, frozen)

The tracking pipeline was removed in PRs #788/#993. Historical tables exist but are frozen:

- `bachelorprojekt.features` — historical feature records
- `bachelorprojekt.v_timeline` — view joining features + bug fix counts
- `bugs.bug_tickets` — bug tickets; `fixed_in_pr` links back to features

## Backup & restore

```bash
task workspace:backup                              # trigger immediate backup
task workspace:backup:list                         # list available timestamps
task workspace:db:restore ENV=<env> -- <db> <timestamp>   # restore one DB
task workspace:db:restore ENV=<env> -- all <timestamp>    # restore all DBs
```

Restore chains `workspace:sync-db-passwords` automatically; do not skip it.
ENV is a task variable, not a `--` CLI flag.

## Schema migration pattern

1. Draft migration in `scripts/migrations/XX-<description>.sql`
   (Website-eigene DB-Migrationen liegen separat in `components/website/src/db/migrations/`)
2. Review impact with `EXPLAIN <query>` first; use `EXPLAIN ANALYZE` only
   against a safe non-production copy (it executes the statement).
3. Apply to the live ENV explicitly (korczewski stays excluded while
   frozen, T002479):

   ```bash
   task workspace:psql ENV=dev -- pocket_id -f scripts/migrations/XX-something.sql
   ```

Detail: [references/migrations.md](references/migrations.md).

## Passwords

ONLY via the secret source of truth:

```bash
task workspace:sync-db-passwords ENV=<env>
```

Never paste a literal password into `ALTER ROLE ... PASSWORD '...'` —
it leaks into shell history and task logs and bypasses `workspace-secrets`.
Detail: [references/passwords.md](references/passwords.md).

## Performance troubleshooting (live tuning)

```bash
# Slow-query shapes, not raw text (pg_stat_statements holds query text)
task workspace:psql ENV=dev -- pocket_id -c "SELECT queryid, calls, mean_exec_time FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;"

# Explain plan only against a safe copy for writes
EXPLAIN SELECT * FROM features WHERE id = $1;
```

`VACUUM`/`ANALYZE` and index changes are mutations: they belong to this
skill, never to a read-only audit. For diagnosis without changes load
`postgres-audit` instead.

## Guardrails

- Read-only probes are autonomous. Destructive or irreversible ops
  (DDL, DROP, restore, password sync, prod deploy) need explicit
  confirmation plus backup evidence first.
- `korczewski`: no writes while frozen (T002479).
- Redact literal secrets from `DEFAULT` expressions before publishing evidence.

## When stuck: Escalation Protocol (Bachelorprojekt-consumer only)

Blockiert (fehlender Kontext, Mehrdeutigkeit, unsichere Operation)? Sofort stoppen,
`bash scripts/agent-escalate.sh --agent "bp-run" --reason … --tried … --needs …`
aufrufen und einen ESCALATION-Block zurückgeben. Nie stumm scheitern, nie raten.
The skill name is never a valid `--agent` value; routing uses the
`bp-run` role. Vollständige Regel (Bachelorprojekt-Consumer):
`.claude/lib/behaviors/escalation-protocol.md`.
