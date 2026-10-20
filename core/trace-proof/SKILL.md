---
name: trace-proof
description: Verifies AI tracing end to end and records or analyzes local telemetry when a remote observability plugin is empty or unavailable. Use when asked whether tracing works, to diagnose missing remote traces, or to capture AI errors, latency, and token usage without a hosted backend.
---

# Trace Proof

Deliver evidence of where telemetry goes and what can actually be read back. Support the existing backend; provide local SQLite telemetry when remote access is unavailable or a backend-independent recorder is requested. This skill is an agent workflow plus a local recorder, focused on recording telemetry and verifying ingestion.

## Installed WSL harness hooks

Installed hooks must be verified on the current host; historical installation statements are not evidence. Check the entrypoint, execute permission, configured hook wiring and report readability before claiming automatic collection. Use the host's existing configuration without replacing hook groups or weakening permissions.

On hosts with the WSL integration, discover `trace-proof` on PATH or inspect the configured local wrapper. Its `report` reads harness records, while `scripts/telemetry.py report` reads a separate spans table. A shell wrapper without execute permission may be inspected and invoked through its declared interpreter for read-only diagnostics; report the broken direct entrypoint separately. Do not silently chmod it during an audit.

Record query window and filters. If a report only returns lifetime aggregates, label them as such and do not infer recent rates or unique-request counts. Missing usage remains unknown. Local records do not establish remote ingestion or ordinary application instrumentation.

## Verify remote tracing

- Identify the intended app, environment, endpoint, and project. Distinguish the MCP plugin's configured project from the app's credentials. Do not print secrets or assume a cloud region.
- Discover available tools and their schemas. Check service health separately from authenticated reads and instrumentation. Use direct API or the installed SDK/CLI when MCP cannot answer; verify current official docs or the deployment's API schema before implementing requests.
- Query a bounded recent window, inspect pagination, and report that window and filters. Empty data means no matching records; it does not prove the app is down or the plugin broken. If project identity cannot be verified, say so.
- For an authorized tracing test, create one labeled synthetic event with a unique correlation ID, no user content, and no model call. Use an existing application path where practical. Flush the exporter and read that exact ID back, with a bounded polling deadline (default 30 seconds). An ingestion acknowledgement alone is insufficient. Do not send synthetic events to a live remote system for a read-only status request; request authorization if it is needed.
- Separate service health, project identity, export acceptance, stored read-back, and application instrumentation. A synthetic exporter test does not establish that ordinary app requests are instrumented. Verify a real app request or show precisely what remains unverified.
- Fix authorized local configuration/instrumentation issues and repeat the relevant check. Preserve remote deployment and credential-change authorization boundaries. Stop retries once the deadline expires and identify the failing layer.

## Local telemetry

Use `scripts/telemetry.py`, which requires only Python's standard library. It creates a SQLite database at the explicit `--db` path. Choose a persistent app-owned state directory or a task artifact directory; do not put telemetry into tracked source files.

```bash
python3 <skill-dir>/scripts/telemetry.py --db <state-dir>/telemetry.sqlite record --name smoke-test --status ok --latency-ms 12
python3 <skill-dir>/scripts/telemetry.py --db <state-dir>/telemetry.sqlite report
```

`record` accepts a trace ID, parent span ID, environment, measured latency, and measured input/output tokens; it returns trace and span IDs. Pass the returned span ID as `--parent-id` for child observations and reuse `--trace-id`. Omitted measurements remain unknown. The report summarizes recorded spans, not unique requests, and reports metric coverage. It does not infer cost from tokens.

For Python integration, load the helper as a module and call `record(db_path, name=..., status=..., latency_ms=..., trace_id=..., parent_id=..., environment=..., input_tokens=..., output_tokens=...)`. Measure duration with a monotonic timer around the actual operation. Obtain token usage from the provider response; do not estimate or invent it. Capture failed operations as error spans even when usage is absent. Use controlled operation names, not prompts, URLs with query strings, or exception messages.

The helper supports parent links but does not propagate context automatically. Wire the actual application boundary when asked to implement tracing. Do not claim continuous monitoring until the app integration has been exercised. Local read-back proves local persistence only; it says nothing about remote ingestion.

## Verify and report

Run `python3 <skill-dir>/scripts/telemetry.py self-test` before relying on this helper in a new environment. It verifies persistence, parent IDs, aggregation, missing metrics, and rejected invalid measurements using a temporary database.

For application changes, exercise one successful request and one controlled failure; check correlated records and measured fields. Report evidence, counts, latest timestamp, error rate, latency distribution, usage coverage, and the first unresolved failure. Keep local and remote findings separate. Do not expose raw payloads or credentials. Never present an untested skill, empty query, or successful health response as proof that tracing works.

## Zusammenspiel bei Flow-Analysen

Bei einer zusammenhängenden Repo-/Agent-Flow-Analyse dem [gemeinsamen Ablauf](../repo-flow-analysis/SKILL.md) folgen. Dieser Skill liefert seinen Fachbeitrag; seine Einzelanwendung bleibt eigenständig.
