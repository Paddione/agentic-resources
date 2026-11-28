# Passwords

Canonical path is the secret source of truth:

```bash
task workspace:sync-db-passwords ENV=<env>
```

It syncs all DB passwords from `workspace-secrets` into PostgreSQL
(`Taskfile.workspace.yml:1176-1198`) and is auto-chained after
`db:restore`, `db:start` and restarts.

Never use raw `ALTER ROLE <user> PASSWORD '<literal>'`: the literal lands
in shell history and task logs and drifts from the sealed secret.
