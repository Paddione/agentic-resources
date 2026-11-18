# Session history review

## Locate and bound

Identify whether OpenCode runs on native Windows, WSL, or another host. Use that
runtime's `opencode debug paths` to locate its data; do not assume `$HOME` or a
Linux data directory from a different host. Inspect `opencode session --help`
and available list/export commands before use. Prefer supported read interfaces.

Start with session metadata and a bounded recent sample (for example 20 sessions
when no count was supplied), then select sessions relevant to the user's focus.
Cross-project analysis is appropriate only for a requested cross-project review.
Do not dump every message into context. Read relevant messages and tool outcomes
for a selected session, retaining only what supports a finding.

## Database fallback

If direct SQLite access is needed, open an existing database read-only with an
available SQLite client. Never let a missing path create an empty database. Inspect
`sqlite_master` and `PRAGMA table_info(...)` before constructing queries: versions
may put model, token, cost, and agent information in JSON or other tables rather
than in `session` columns. Inspect the actual message/part relation before reading
content; a metadata row is not necessarily the complete message.

Select only needed fields, parameterize session IDs, bound results, and order
messages using the actual schema's timestamp/ordering fields. Do not migrate,
repair, or write to the live history as part of reflection. If access fails, report
the limitation and continue with available evidence; missing history does not prove
OpenCode has never been used.

## Analyze without overstating

Record the task, observed outcome (including unknown), friction, evidence location,
and candidate improvement. Distinguish recurring behavior from one interrupted
session. Deduplicate sessions in frequency counts and report the denominator and
selection method; a recent selected sample is not evidence about all usage.

Persist summaries only when useful or requested, with minimal sensitive detail.
If caching, track session identity, last-update marker, review scope, and summary
version; invalidate when any changes. Exclude stale or out-of-scope cached records
from aggregation. Do not infer global applicability from an arbitrary percentage
of repositories or assign unsupported confidence decimals.
