# Plan-Status & Ausführungsoptionen (Feature- und Fix-Pfad)

Aus `dev-flow-plan` Schritt 6.5 (Feature-Pfad) und Schritt 6 (Fix-Pfad) extrahiert.

## 1. Status laden

Ohne Tickets (`repo.tickets == none`): Status aus Repo-Dateien, nicht aus der DB:

```bash
BRANCH=$(git branch --show-current)
SLUG=<slug>
git cat-file -e HEAD:.agents/plans/$SLUG/tasks.md \
  && echo "Plan committed" || echo "Plan NICHT committed"
git ls-remote --heads origin "$BRANCH" | grep -q . \
  && echo "Branch gepusht" || echo "Branch NICHT gepusht"
bash scripts/plan-lint.sh .agents/plans/$SLUG/tasks.md \
  && echo "Lint PASS" || echo "Lint FAIL"
```

Belege `PLAN_COMMITTED` / `BRANCH_PUSHED` / `LINT` aus dem Output.

Nur-wenn-Tickets (`repo.tickets != none`): Status aus den Ticket-Queues
(`plan_staged`/`planning`).

**MCP-Schnellweg (read-only).** Wenn `mcp-postgres` erreichbar (MCP-Tool direkt nutzbar — `SELECT 1`),
führe beide Reads via `mcp-postgres_query` aus:
> staged plans — `sql:` `SELECT external_id, title, priority, COALESCE(value_prop,'') FROM tickets.tickets WHERE status='plan_staged' ORDER BY planning_rank ASC NULLS LAST, created_at DESC;`
> planning-Count — `sql:` `SELECT COUNT(*) FROM tickets.tickets WHERE status='planning';`

Belege `STAGED_PLANS` bzw. `PLANNING_COUNT` aus den MCP-Ergebnissen. **Fallback:** der kubectl-Block unten. Siehe [`MCP-Tool-Guide`](.agents/skills/references/mcp-tool-guide.md).

_Fallback:_

```bash
STAGED_PLANS=$(kubectl exec -n workspace deploy/shared-db -- psql -U postgres -d website -t -A -F '|' -c \
  "SELECT external_id, title, priority, COALESCE(value_prop,''), COALESCE(effort,''),
   array_to_string(areas,','), COALESCE(depends_on::text,'{}')
   FROM tickets.tickets WHERE status='plan_staged'
   ORDER BY planning_rank ASC NULLS LAST, created_at DESC;" 2>/dev/null)
STAGED_COUNT=$(echo "$STAGED_PLANS" | grep -c '|' || echo 0)

PLANNING_COUNT=$(kubectl exec -n workspace deploy/shared-db -- psql -U postgres -t -A -c \
  "SELECT COUNT(*) FROM tickets.tickets WHERE status='planning';" 2>/dev/null)
```

## 2. Ausgabe-Format (identisch für Feature- und Fix-Pfad)

**STOPP.** Informiere den User:

```
✅ <Feature|Fix>-Plan bereit: <slug> (nur-wenn-Tickets: Ticket $TICKET_EXT_ID)
   Branch: <feature|fix>/<slug> (gepusht: ja/nein — nur-wenn-Tickets: ohne ja/nein)
   Plan: .agents/plans/<slug>/tasks.md (committed: ja/nein, lint: PASS/FAIL — nur-wenn-Tickets: ohne Klammerzusatz)

📋 Kommissionierung (status=plan_staged): $STAGED_COUNT Plan(s)   [nur-wenn-Tickets]
   • T000xxx [priorität] <titel> — <value_prop>
   • T000yyy [priorität] <titel> — <value_prop>
   ...

📝 Planungsbüro (status=planning): $PLANNING_COUNT Ticket(s) warten auf Planung   [nur-wenn-Tickets]

🚀 Ausführungsoptionen:

1. **Einzel-Ausführung:**
   dev-flow-execute auf <feature|fix>/<slug> aufrufen
   → Implementiert nur diesen einen Plan

2. **Lokal mit dem Plan-Runner:**
   node scripts/llm/plan-runner.mjs .agents/plans/<slug> --worktree <pfad>
   → Führt die Partials mit den lokalen Modellen aus (Runbook: docs/runbooks/plan-runner.md)

3. **Batch-Planung (mit dev-flow-batch):**   [nur-wenn-Tickets]
   Wenn weitere planning-Tickets existieren und du erst alle planen willst:
   dev-flow-batch aufrufen → plant alle status=planning Tickets parallel
   → Danach jeden fertigen Plan per Option 1 oder 2 ausführen
```

**Empfehlung:** Ein fertiger Plan → Option 1. Lokal ohne Cloud-Budget → Option 2. Nur-wenn-Tickets: wenn noch planning-Tickets warten → Option 3.

STOPP danach.
