# CLAUDE.md

> **Leading SSOT:** [`AGENTS.md`](AGENTS.md) is the shared instruction base
> for every repository inheriting from `agentic-resources`. Tool-specific
> notes live here; shared doctrine lives there and is not mirrored.

## Claude notes

- Answer users in their language; repo docs and conventions stay German.
- Prefer native tools over shell for file operations; use `gh` directly for
  JSON output, polling, and mutations.
- Ground claims in files read or commands run; label the rest as inferred.
- Autonomous on routine reads and edits; ask before cross-system actions
  (publish, deploy, access changes) and before history rewrites.
