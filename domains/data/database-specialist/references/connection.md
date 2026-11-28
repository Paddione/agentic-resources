# Connection

All DB access goes through `taskfiles/Taskfile.workspace.yml`:

- `task workspace:psql ENV=<env> -- <database> [-c ... | -f ...]`
  resolves ENV via `env-resolve.sh` to context/namespace and execs
  `deploy/shared-db`.
- `task workspace:port-forward ENV=<env>` forwards `svc/shared-db`.
- `task workspace:backup`, `task workspace:backup:list`,
  `task workspace:db:restore ENV=<env> -- <db>|all <timestamp>`.

ENV is a task variable. Never substitute raw `kubectl --context fleet`;
it points at a decommissioned cluster.
