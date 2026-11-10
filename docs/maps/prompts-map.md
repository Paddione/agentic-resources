# prompts-map — generiert aus runtimes/prompts/manifest.yaml (P1).
Generator: `python3 -c "..."` bzw. Manifest editieren, dann Tabelle neu erzeugen.
Kein Task-Eintrag: AR hat `task_runner: none` (repo.yaml.schema) — Checks laufen via pytest.

| id | Datei | Rolle | Harness | Version |
|---|---|---|---|---|
| bp-build | `runtimes/prompts/bp-build.md` | bp-build | bachelorprojekt | 1 |
| bp-run | `runtimes/prompts/bp-run.md` | bp-run | bachelorprojekt | 1 |
| bp-ship | `runtimes/prompts/bp-ship.md` | bp-ship | bachelorprojekt | 1 |
| local-subagent | `runtimes/prompts/local-subagent.md` | local-subagent | local | 1 |
| orchestrator | `runtimes/prompts/orchestrator.md` | orchestrator | all | 1 |
| primary-agent | `runtimes/prompts/primary-agent.md` | primary-agent | bachelorprojekt | 1 |
| qwen35-worker | `runtimes/prompts/qwen35-worker.md` | worker | local | 1 |
| vllm-worker | `runtimes/prompts/vllm-worker.md` | worker | local | 1 |

Rollen-Vokabular `bp-build/bp-run/bp-ship/orchestrator/...`: SSOT Bachelorprojekt
`scripts/toolset/lib/roles.mjs` (extern, dort fail-closed geprüft); AR-lokale Rollen
(`primary-agent`, `local-subagent`, `worker`) nur hier dokumentiert.
