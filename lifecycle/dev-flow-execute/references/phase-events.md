# Phase-Events — dev-flow-execute Telemetrie (Detail, lokal)

Phasen-Events sind Zeilen in `.agents/plans/<slug>/phase-events.log`
(Format: `<phase> <state> <utc-timestamp> <detail>`, Slug = Branch ohne Typ-Präfix).
Pflichtkette für den Merge: `plan done`, `implement entered`, `verify done`.
`verify`-Events sind PFLICHT — Schritt 6 prüft sie fail-closed.
Fehlt die Log-Datei ganz, ist das ebenfalls FAIL — eine leere Antwort ist kein Urteil.
(`plan done` schreibt `dev-flow-plan` beim Stagen.)

## Schreiben — nur wenn `repo.tickets` ein Backend nennt (only-if-tickets)

Alle Events schreibt `scripts/devflow-phase.sh` in die lokale, gitignorierte
`phase-events.log` des Worktrees. `devflow-ci-watch.sh` und
`devflow-post-merge-finalize.sh` lesen die Datei aus dem Worktree — beide deshalb
im selben Worktree aufrufen, in dem die Events entstanden sind. Fehlt ein Event
(etwa weil der Plan in einem anderen Worktree gestagt wurde), nach erfüllter
Bedingung nachtragen.

```bash
bash scripts/devflow-phase.sh implement entered --detail "Subagent gestartet"
bash scripts/devflow-phase.sh implement done --detail "Implementierung fertig"
bash scripts/devflow-phase.sh verify entered --detail "test:changed + freshness"
# erst nach grünen Tests:
bash scripts/devflow-phase.sh verify done --detail "Tests grün, freshness OK"
```

## Schreiben — ohne Ticket-Backend (Default, `repo.tickets: none`)

Kein Backend, kein MCP, kein `ticket.sh`: Events per `echo` anhängen.

```bash
echo "implement entered $(date -u +%FT%TZ) subagent-gestartet" >> .agents/plans/<slug>/phase-events.log
echo "implement done $(date -u +%FT%TZ) implementierung-fertig" >> .agents/plans/<slug>/phase-events.log
echo "verify entered $(date -u +%FT%TZ) tests-changed-freshness-ok" >> .agents/plans/<slug>/phase-events.log
# erst nach grünen Tests:
echo "verify done $(date -u +%FT%TZ) tests-gruen-freshness-ok" >> .agents/plans/<slug>/phase-events.log
```

## Gate (Schritt 6, PFLICHT — KEIN `|| true`)

Only-if-tickets: `bash scripts/devflow-phase.sh check` (Exit 6 = unvollständig).
Sonst fail-closed per grep:

```bash
grep -q '^plan done' .agents/plans/<slug>/phase-events.log \
&& grep -q '^implement entered' .agents/plans/<slug>/phase-events.log \
&& grep -q '^verify done' .agents/plans/<slug>/phase-events.log \
  || { echo "FAIL: phase-chain unvollständig"; exit 1; }
```
