---
name: repo-hygiene
description: 'Nutze diesen Skill für den Zustand des Repos und die Host-weite Multi-Repo-/Serving-Hygiene — stale Branches und Worktrees, offene PRs mergen und schließen, GitHub-Issue-Intake, Laufzeit-/Serving-Drift, proaktive Hygiene-Empfehlungen und Scheduling-Guidance. Trigger: "clean branches", "merge PRs", "prune worktrees", "stale worktrees", git worktree remove, gh pr merge, "repo health check", "hygiene recommendations", "what should I clean up", "repo-hygiene-audit", "undecided GGUF". Nicht für Task- oder Plan-Inhalte — Triage und Klärungsrunden gehören in dev-flow-plan, Ausführung in Worker-Sandboxes.'
---

> **Mishap Tracking:** Führe während dieses Skills ein `MISHAP_LOG` und rufe am Ende
> `mishap-tracker` auf — Eintragsformat und Ablauf: siehe `mishap-tracker` §Input.

# repo-hygiene

Day-to-day repository hygiene, PR merging, issue intake, and multi-repository / model-serving drift audit.

Lies vor Beginn aus `repo.yaml` im Consumer-Repo-Root:
- `repo.main_branch` (`main` oder `master`)
- `repo.tickets`: `github` → verknüpfte GitHub-Issues referenzieren/kommentieren (`closingIssuesReferences`); `none` → keine Issue-Steps (interne Ticket-DB retiriert am 2026-10-14; kein Ticket-Close).
- `repo.task_runner`: `taskfile` oder `none`.
- Nur-wenn das Repo tabellarische Nicht-Ticket-Daten mit DB-Zugriff hält: MCP-first vor direktem DB-Zugriff (siehe [`mcp-tool-guide.md`](../references/mcp-tool-guide.md)).

---

## Ablauf

> **Kollisionsschutz:** Zwischen **08:00 und 08:45 CET** laufen die automatischen Morgen-Routinen:
> - `08:00–08:15`: `repo-hygiene.timer` (`repo-hygiene-cron.sh standard`, Lock `/tmp/repo-hygiene-tick.lock`)
> - `08:15–08:30`: `repo-hygiene-audit.timer` (`~/scripts/repo-hygiene-audit.py --out ~/.cache/repo-hygiene-audit.json`)
> - `08:30–08:45`: `multi-repo-morning.timer` (`~/scripts/morning-health-brief.py` → `~/.cache/morning-brief.md`)
> Vor jedem manuellen Lauf prüfen, ob ein Dienst aktiv ist (`systemctl --user is-active repo-hygiene.service repo-hygiene-audit.service` oder `/tmp/repo-hygiene-tick.lock`).

Die gesamte Housekeeping-Mechanik ist **SSOT** in
[`repo-hygiene-ops.md`](../references/repo-hygiene-ops.md) —
die aktiven Abschnitte der Reihe nach ausführen (§5 entfiel mit T900399):

0. **Arbeitsbaum & Stashes** — §0 (inkl. `repo-hygiene-precheck.sh` + Snapshot-Verifikation)
1. **Stale Git Worktrees** — §1 (inkl. `worktree-git-op-guard.sh`, `git-worktree-health.sh`, `worktree-clean-check.sh`)
2. **Stale Branches** (Reaper vor `[gone]`-Prune, Archiv-Tag `refs/tags/reaped/<branch>`) — §2
3. **PR-Triage → mergen** (`gh pr merge --squash` ohne `--delete-branch`, Timestamp-Verifikation, `closingIssuesReferences` kommentieren; kein Ticket-Close) — §3
4. **GitHub-Issue-Intake** (nur bei `repo.tickets: github`; Dedupe-Guard gegen offene Issues + `.mishaps.log`) — §4
5. *(entfallen, T900399)* — §5
6. **Proactive Hygiene Recommendations** — §6 (nach jedem Lauf: Top-3-Empfehlungen, Aging-Report)
7. **Scheduling & Trigger Guidance** — §7 (Ausführungstiefe, systemd-Timer-Kollisionsmatrix, Gesundheitsampel)

Für Completeness-Triage und Klärungsrunden → `dev-flow-plan`. Für Ausführung:
Dispatch über Worker-Sandboxes (`operations-management`,
Worker-Dispatch-Contract), wo vorhanden.

---

## Laufzeit-Drift & Multi-Repo-Audit

Gemergte Fixes und Serving-Konfigurationen wirken nur, wenn sie auf dem laufenden System angekommen sind. Zwei komplementäre Prüfpfade decken Repo- und Host-Ebene ab:

### 1. Repo-lokaler Guard (`bash scripts/runtime-drift-check.sh`, falls im Repo vorhanden)
1. **MCP-Prozesse gegen ihre Binaries** — laufende stdio-Server aus `docs/agent-guide/registry/mcp.yaml`, deren Binary ersetzt wurde (`/proc/<pid>/exe` zeigt `(deleted)` oder weicht im sha256 ab).
2. **DB-Funktionen gegen ihre Migrationen** — Funktionen, deren `pg_proc.prosrc` den in `scripts/one-shot/*.sql` deklarierten `RUNTIME-CHECK`-Marker nicht trägt.

Der Guard **meldet standardmäßig und greift nicht ein** (im Daily-Cron heilt `--auto-kill` nur ersetzte stdio-Binaries per `SIGTERM`; HTTP-Server-Restarts und DB-Migrationen bleiben Betreiber-Entscheidung). Unerreichbare DB oder nicht lesbare `/proc/<pid>/exe` gelten als übersprungen, nicht als Drift.

### 2. Host-weiter Read-Only-Audit (`python3 ~/scripts/repo-hygiene-audit.py`)
Liest `~/.cache/repo-hygiene-audit.json` (täglich 08:15 via `repo-hygiene-audit.timer`) oder führt den Lauf ad-hoc read-only aus (`unknown` wird nie zu `pass`):
1. **Multi-Repo-Inventar** über `~` (dotfiles), `Bachelorprojekt`, `agentic-resources`, `news-agent`, `unsloth-boxes`: Porcelain-Status, Stashes, Ahead/Behind, `git fsck --connectivity-only`, Branches, Worktree-Alter & unterbrochene Git-Operationen, offene PRs.
2. **MCP-Config- & DB-Marker-Drift**: `python3 ~/scripts/render-mcp-configs.py --check` sowie read-only `RUNTIME-CHECK`-Prüfung über `~/scripts/repo_hygiene_db.py` (lokaler PostgreSQL-MCP `:13001`).
3. **Serving, Consumer & Modell-Inventar** (`~/scripts/repo_hygiene_serving.py`):
   - **Serving**: alle `llama-server`-Units unter `~/.config/systemd/user/` (direkt oder via `serve.sh` mit `DRY_RUN=1`) auf existierende Pfade (`model`, `mmproj`, `draft`, `binary`), Quant-Konsistenz in `Description=` und live gemeldeten `/v1/models`-Alias prüfen.
   - **Consumers**: Modell-IDs in `news-agent/.env` und `news-agent/k8s/dna-api.yaml` (`DNA_MODEL`, `DNA_HELPER_MODEL`) gegen den bedienten Port-Alias abgleichen.
   - **Models**: GGUF-Bestand unter `/mnt/f/models` in `referenced` (von Unit genutzt), `decided` (in `~/.config/repo-hygiene/model-decisions.json` dokumentiert; Rollen-Katalog in `~/.config/repo-hygiene/model-roles.json`) und `undecided` (Befund; Upstream-Vocab-Fixtures `ggml-vocab-*.gguf` werden ignoriert) klassifizieren.

---

## Post-Execution: Mishap Report

After completing all steps in this skill, invoke `mishap-tracker` with your accumulated `MISHAP_LOG`. If no mishaps were found, `mishap-tracker` exits cleanly.

## Related Skills

- `operations-management` — Routing-Hub (Worker-Dispatch, Housekeeping)
- `system-audit` — Voll-Audit über alle Subsysteme (delegiert Ziel `repo` hierher)
- `dev-flow-chore` — Einzügige Wartungs-Chores ohne Verhaltensänderung
- `dev-flow-plan` — Completeness-Triage und Klärungsrunden
- `morning` — Konsumiert `~/.cache/morning-brief.md` (gespeist aus `repo-hygiene-audit.json`)
- `mishap-tracker` — lokales Mishap-Log
