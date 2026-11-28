# Freeze (korczewski, T002479)

`korczewski` is frozen (`suspend: true`, no go-live, no scaling):
no migrations, writes, restores or password rotations there until thawed.

`Taskfile.yml` excludes it explicitly; apply all mutating ops to the live
ENV only and note the exclusion in the migration record.
