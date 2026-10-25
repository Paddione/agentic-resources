---
name: repo-hygiene
description: 'Nutze diesen Skill für den Zustand des Repos selbst — stale Branches und Worktrees, offene PRs mergen und schließen, GitHub-Issue-Intake, proaktive Hygiene-Empfehlungen und Scheduling-Guidance. Trigger: "clean branches", "merge PRs", "prune worktrees", "stale worktrees", git worktree remove, gh pr merge, "repo health check", "hygiene recommendations", "what should I clean up". Nicht für Task- oder Plan-Inhalte — Triage und Klärungsrunden gehören in dev-flow-plan, Ausführung in Worker-Sandboxes.'
---

> **Mishap Tracking:** Führe während dieses Skills ein `MISHAP_LOG` und rufe am Ende
> `mishap-tracker` auf — Eintragsformat und Ablauf: siehe `mishap-tracker` §Input.

# repo-hygiene

Day-to-day repository hygiene, PR merging and issue intake.

SSOT für Issues sind die GitHub-Issues des Repos (interne Ticket-DB
retiriert). Nur-wenn-`tickets` in `repo.yaml` (Consumer-Repo-Root) gesetzt
ist: Ticket-Close-Mechanik des Repos ausführen; bei `tickets: none` entfällt
jeglicher Ticket-Close. Nur-wenn das Repo tabellarische Nicht-Ticket-Daten mit
DB-Zugriff hält: MCP-first vor direktem DB-Zugriff.

---

## Ablauf

> **Kollisionsschutz:** Der Daily Sweep läuft automatisch täglich um 08:00 CET via `repo-hygiene.timer`.
> Vor jedem manuellen Lauf prüfen, ob der Timer/Service aktiv ist (`systemctl --user is-active repo-hygiene.service`
> oder `/tmp/repo-hygiene-tick.lock`). Zwischen 08:00 und 08:15 CET keine parallelen Sweeps starten.

Die gesamte Housekeeping-Mechanik ist **SSOT** in
[`repo-hygiene-ops`](.agents/skills/references/repo-hygiene-ops.md) —
die acht Abschnitte der Reihe nach ausführen:

0. **Arbeitsbaum & Stashes** — §0
1. **Stale Git Worktrees** — §1
2. **Stale Branches** (inkl. squash-`[gone]`-Prune) — §2
3. **PR-Triage → mergen** (verknüpfte GitHub-Issues referenzieren; Ticket-Close nur-wenn-`tickets`) — §3
4. **GitHub-Issue-Intake** (Dedupe-Guard: vor dem Anlegen gegen offene GitHub-Issues auf gleichen Titel/Duplikat prüfen) — §4
5. *(entfallen)* — §5
6. **Proactive Hygiene Recommendations** — §6 (nach jedem Lauf: Top-3-Empfehlungen, Aging-Report)
7. **Scheduling & Trigger Guidance** — §7 (wann und wie oft Hygiene laufen sollte)

Für Completeness-Triage und Klärungsrunden → `dev-flow-plan`. Für Ausführung:
Dispatch über Worker-Sandboxes (`operations-management`,
Worker-Dispatch-Contract), wo vorhanden.

---

## Laufzeit-Drift

Gemergte Fixes laufen nur, wenn sie auf dem laufenden System angekommen sind. Der Guard
`bash scripts/runtime-drift-check.sh` prüft das beim Hygiene-Lauf und listet seine
Befunde neben den Branch-, Worktree- und Queue-Befunden:

1. **MCP-Prozesse gegen ihre Binaries** — laufende stdio-Server, deren Binary ersetzt wurde
   (Prozess läuft mit der alten Inode, `/proc/<pid>/exe` zeigt `(deleted)` oder weicht im
   sha256 ab).
2. **DB-Funktionen gegen ihre Migrationen** — Funktionen, deren `pg_proc.prosrc` den in
   `scripts/one-shot/*.sql` deklarierten `RUNTIME-CHECK`-Marker nicht trägt.

Der Guard **meldet und greift nicht ein**: das Beenden eines driftenden Prozesses und das
Einspielen einer Migration bleiben Entscheidungen des Betreibers. Unerreichbare DB oder nicht
lesbare `/proc/<pid>/exe` (fremder Benutzer) gelten als übersprungen, nicht als Drift.

---

## Post-Execution: Mishap Report

After completing all steps in this skill, invoke `mishap-tracker` with your accumulated `MISHAP_LOG`. If no mishaps were found, `mishap-tracker` exits cleanly.

## Related Skills

- `operations-management` — Routing-Hub (Worker-Dispatch, Housekeeping)
- `dev-flow-plan` — Completeness-Triage und Klärungsrunden
- `mishap-tracker` — lokales Mishap-Log
