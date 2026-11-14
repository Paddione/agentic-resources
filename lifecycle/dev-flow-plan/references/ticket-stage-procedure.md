# Ticket-Stage-Prozedur (nur-wenn-Tickets)

> Skript-Verweise gelten nur-wenn das Repo sie führt (Bachelorprojekt-Profil); sonst das Repo-Äquivalent aus `repo.yaml` bzw. `AGENTS.md` des Repos. Lifecycle-Mechanik immer über `python3 ~/scripts/agent-workspace.py`.

Gilt nur für Consumer mit Ticket-Backend (`repo.tickets != none`). Ohne Tickets
entfallen alle Schritte auf dieser Seite ersatzlos — der Push IST das Stagen.

## Preflight: Check merged

Vor der Worktree-Anlage prüfen, ob der Fix auf `MAIN` schon drin ist:

```bash
bash scripts/agent-lock.sh check-merged "$TICKET_EXT_ID"  # verboten (Guard); statt dessen: python3 ~/scripts/agent-workspace.py lock <claim|check|release|list|reap|mine> <scope> [<id>]
```

`rc=1` = schon gefixt → Ticket `done`, abbrechen.

## Stagen nach dem Commit

`stage-plan` läuft erst **nach** dem Commit. Ein Aufruf stagt Plan, Branch
und Claim:

```bash
bash ticket.sh stage-plan --id "$TICKET_EXT_ID" \
  --branch "$(git branch --show-current)" --hold
```

Flag-Semantik: `--hold` (zurückhalten bis `dev-flow-execute` freigibt),
`--partials` (einzelne Partials stagen), `--allow-empty-touched`
(leere Touch-Commits zulassen).

## Archiv-Notiz

Das Ticket-Backend `ticket.sh` (inkl. `ticket.sh archive-plan`) ist im
Referenz-Consumer retiriert; ticket-führende Consumer nutzen die obigen
Befehle bzw. ihr eigenes Backend-Äquivalent.
