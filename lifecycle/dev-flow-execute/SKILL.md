---
name: dev-flow-execute
description: 'Use when implementing, executing, or delivering a staged plan on a feature/* or fix/* branch in .agents/plans/. Invoke after dev-flow-plan has committed and pushed the plan to the branch. Triggers on dev-flow-execute, execute plan, implement plan, resume plan, execute tasks, deliver feature, run plan runner.'
---

# dev-flow-execute — Plan-Ausführung & PR

Repo-Spezifika stehen nicht hier, sondern in `repo.yaml` im Consumer-Repo-Root:
Vor Beginn `repo.main_branch`, `repo.scopes`, `repo.tickets`,
`repo.generated_artifacts` und `repo.task_runner` aus `repo.yaml` lesen.
Fehlt ein Schlüssel, die Annahme explizit nennen (Annahmen unten in Klammern).
`scripts/...`- und `task ...`-Aufrufe beziehen sich auf das Quell-Layout;
im Consumer das dortige Äquivalent verwenden.

Rollen- und Übergabevertrag: [dev-flow-lifecycle](references/dev-flow-lifecycle.md).
Diese Skill enthält nur die Execute-Gates, die Mechanik steht in den verlinkten
Referenzen. Interaktive Ausführung über die Slash-Commands `dev-flow-exe.md`
und `dev-flow-execute.md`.

> **cwd-Regel (PFLICHT):** Git-Aufrufe immer als `git -C <worktree>` bzw. mit
> explizitem cd+guard — **nie auf implizites cwd vertrauen**. `cd` wirkt nur auf den aktuellen
> Bash-Call, ein bare `git commit` landet sonst im Haupt-Checkout.

## Wann diese Skill greift

Feature/Fix-Branch mit committiertem, gepushtem Plan → PR gemergt zu
`<repo.main_branch>` (Annahme: `main`), Plan als `completed` markiert,
Worktree/Branch aufgeräumt. Nur wenn `repo.tickets` ein Backend nennt
(only-if-tickets): zusätzlich Ticket `done/shipped` und Plan-Archivierung.

## Pre-Flight (Schritte −1 bis 1.7)

Befehlsfolgen: [dev-flow-execute-phases](references/dev-flow-execute-phases.md).
Hier nur Leistung und Abbruchbedingung:

| Schritt | Leistet | Bricht ab, wenn |
|---|---|---|
| **−1 Pre-Flight-Lock** | Branch claimen (`agent-lock claim branch` — kein ticket-Scope), Broadcast an andere Sessions | eine lebende Session den Branch schon hält |
| **0 Main-Sync** | Reaper, ungelesene Agent-Nachrichten, `git pull --rebase` im Haupt-Repo | — |
| **0 Worktree-Konsistenz** | Branch-Guard: gültiger Branch ausgecheckt **und** unter `.worktrees/*` gearbeitet; legt sonst einen an | detached HEAD, oder Worktree-Erstellung schlägt fehl |
| **0.5 Rebase** | `git fetch origin <repo.main_branch> && git rebase origin/<repo.main_branch>` | Konflikt — dann manuell lösen |
| **1 Plan-Pfad laden** | Plan-Datei **im Git-Tree** prüfen — only-if-tickets: `FACTORY-PLAN-REF` aus der DB (`stage-plan` setzt sie); sonst: Slug aus dem Branch-Namen, `.agents/plans/<slug>/tasks.md` (Slug = Branch-Name ohne `feature/`- bzw. `fix/`-Präfix) | Pfad fehlt, Datei nicht in `HEAD` (only-if-tickets: kein `plan_ref`) |
| **1.4–1.7** | Doppelarbeit-Guard, Pipeline-Modus (`slot_count`), Claim gehört noch dieser Session (only-if-tickets: zusätzlich Ticket auf `in_progress`, `touched_files`, Ticket-Anhänge laden) | Claim gehört nicht mehr dieser Session |

> **Der Plan-Pfad kommt nie aus einem Glob** — aus der DB (only-if-tickets)
> bzw. aus der Branch-Konvention (sonst).

> **Worktree-Isolation ist Pflicht.** Liegt auf dem Branch schon Arbeit oder hält ihn ein fremder Worktree, gilt der **Fortsetzungs-Kontrakt** — fortsetzen statt neu beginnen, zurückstellen statt `blocked`: [resume-contract](references/resume-contract.md).

### Schritt −1.1: Branch-Claim ist branch-scoped

Der Pre-Flight-Lock claimt **branch-scoped** — niemals über das Ticket:
`bash scripts/agent-lock.sh claim branch "$BRANCH"`. Verifikation:
`bash scripts/agent-lock.sh check branch "$(git branch --show-current)"`. Release nach
dem Merge (Schritt 6.4–7.5), ebenfalls branch-scoped.

## Schritt 1.8: Hold-Freigabe — nur only-if-tickets

Nur wenn `repo.tickets` ein Backend nennt: Nach `stage-plan --hold` ist
`readiness.execution_released=false`; ohne Hold ist die Freigabe ein No-op
(`|| true`), `false` bleibt der Default. Ohne Ticket-Backend entfällt dieser
Schritt ersatzlos.

## Schritt 2: Implementierung an frischen Implementer-Subagenten delegieren

> **Arbeitsteilung:** Implementer bis PR-Erstellung → **ENDE**, Bericht zurück, OHNE
> Auto-Merge-Anforderung. Orchestrator: Merge-Gate (3.8), CI-Watch (5.5); Exit 3/4 per
> `SendMessage` an den Implementer zurück, nicht neu spawnen.

Phasen-Telemetrie (best-effort): [phase-events](references/phase-events.md).

Delegiere die **gesamte Implementierung an EINEN frischen Subagenten**. Du behältst den Plan-Kontext und verifizierst danach unabhängig — kein Per-Task-Fan-out (verschachtelte Delegation sprengt den Kontext, 162k-Prompt-Lehre). Spawn-Matrix je Harness (opencode: `background-agents.ts`-Delegation; Worktree-`cd`-Pflicht und Effort-Formulierungen dort), Kontext-Injektion (Plan-Datei, Branch, Plan-Intel-Bundle aus `intel.json`; only-if-tickets: zusätzlich Ticket-ID und `$ATTACHMENT_DIR`), Test-Pflicht (pytest) und Auftrag (Ein-Ebenen-Regel, SID-Propagation T006365, Freshness-Pflicht vor PR-Erstellung, ENDE T002365): [implementer-handoff](references/implementer-handoff.md) — den Auftrag wörtlich in den Subagenten-Prompt übernehmen.

### Wenn keine Delegation möglich ist

Ohne Subagent (Session-Policy, Harness ohne Agent-Tool, Offline) **implementiert der Orchestrator
in-context** und führt die Schritte 3 bis 7.5 selbst aus. Die Ein-Ebenen-Regel entfällt. Rote
Checks und Rebase-Konflikte löst der Orchestrator selbst, weiter ohne
Hintergrund-Monitore. Weil derselbe Kontext Implementierung und Prüfung trägt,
sorgfältiger verifizieren.

## Schritt 2.5 — Lokaler Self-Correcting-Loop (optional)

`bash scripts/devflow-build-loop.sh` (only-if-tickets: mit `"$TICKET_ID"`) — läuft lokal
**vor** Verifikation und Push, entlastet die CI-Retry-Schleife (5.5), ersetzt sie nicht.
Default `MAX_LOOP=3`. Bei `abort:escalate-gate|no-progress|max-iterations`
eskalieren (only-if-tickets: als Ticket-Kommentar, sonst Mishap-Eintrag) —
**kein** blindes Weiter-Pushen.

## Schritt 3: Lokale Verifikation

Rufe das Skill **`verification-before-completion`** auf.
Phasen-Telemetrie (PFLICHT für verify — Schritt 6 prüft `verify:done` fail-closed): [phase-events](references/phase-events.md).
Verifikation: die vier Befehle + Manifest-Runner bei Manifest-Änderungen.
**SSOT:** [verification-block](references/verification-block.md).

> Nur wenn `repo.generated_artifacts` true ist: **`freshness:check` wird erst NACH dem Commit der regenerierten Artefakte grün**, weil es auch prüft, ob sie committet sind. Reihenfolge: `regenerate` → Artefakte **committen** → `check`. Der Implementierungs-Commit bleibt in Schritt 5.

Nach grünen Tests das `verify done`-Event schreiben (Aufrufe: [phase-events](references/phase-events.md)).

## Schritt 3.5: Admin-Menu Placement Gate

Falls neue Admin-Seiten hinzugefügt wurden:
```bash
bash scripts/admin-menu-gate.sh
```

## Schritt 3.8: Merge-Gate, Code-Review optional (Orchestrator)

**Orchestrator-Schritt, nicht Implementer** — Self-Attestation ist kein Review.

Merge-Kriterium: grüne Required Checks plus bestandener fail-closed Phase-Chain-Gate (Befehle: [phase-events](references/phase-events.md), KEIN `|| true`). Ein
Code-Review ist **keine** Merge-Voraussetzung.

1. Auto-Merge-Zustand des PRs prüfen. **Den Branch immer explizit übergeben**:
   ohne `--branch` leitet `gh` den PR aus dem ausgecheckten Branch ab und meldet im Haupt-Checkout
   `OK: Kein PR gefunden` (rc=0), obwohl ein PR offen ist.
   ```bash
   bash scripts/check-pr-automerge.sh --branch "$BRANCH"
   ```
   Semantik: `rc=0` noch nicht aktiv → weiter; `rc=1` bereits aktiv → weder abbrechen noch deaktivieren, der Merge läuft bei grünen Required Checks; `rc=2` Abbruch als Umgebungsfehler.
2. Optionales Review: nur wenn der Operator in der laufenden Session ausdrücklich ein Review
   verlangt. Dann rufe das Skill **`requesting-code-review`** auf. Findings vor dem
   Merge gehen per `SendMessage` an den **bereits gespawnten** Implementer (kein neuer Spawn);
   nach dessen Push erneut reviewen. Findings, die erst nach dem Merge eintreffen, werden zum
   Folge-PR (only-if-tickets: mit eigenem Folge-Ticket bei Defekten). Ohne ausdrücklichen Zuruf wird
   kein Review-Subagent gestartet.
3. Fail-closed den Phase-Chain-Gate prüfen, dann Auto-Merge anfordern:
```bash
bash scripts/devflow-phase.sh check
```
```bash
# GitHub merged selbstständig, sobald Required Checks grün sind.
# KEIN --delete-branch: die Archivierung braucht den Branch noch (Löschung in 7.5).
# Die Anforderung ist idempotent, wenn Auto-Merge bereits aktiv ist.
(cd "$MAIN_REPO" && gh pr merge --auto --squash)
```

## Schritt 3.9: Finalisierung delegieren

> **Härtung:** Nach dem Auto-Merge-Request endet der Orchestrator. Die Schritte 6.4–7.5
> laufen in einem frischen Finalizer, weil ein Executor nach dem Merge an Kontext-Erschöpfung
> starb und Closure, Archiv und Cleanup liegen blieben.

Spawne einen **frischen Finalizer-Subagenten** (nativer Dispatch, `general-purpose`) und gib ihm alles explizit: PR-Nummer `$PR_NUM`, Branch
`$BRANCH`, Worktree-Pfad `$MAIN_REPO/.worktrees/<slug>`, Plan-Pfad `$PLAN_FILE`
(only-if-tickets: zusätzlich Ticket-ID `$TICKET_ID` und Resolution `shipped`/`fixed`).

Auftrag an den Finalizer (wörtlich Teil des Prompts):
- **Merge-Wait-Loop zuerst (T001149-M1):** [ci-fix-loop](references/ci-fix-loop.md) §"PR-Merge-Wait-Loop" lesen und von dort ausführen. Bei Timeout strukturiert berichten — keine Closure behaupten (only-if-tickets: bei Timeout KEIN Ticket schließen — Drift Ticket=done bei PR=OPEN vermeiden).
- **Abschluss über die manuelle Einheit,** keine freie Rekonstruktion der Einzelschritte: [plan-archive-steps](references/plan-archive-steps.md) der Reihe nach (Merge verifizieren → Plan `completed` → Claim freigeben → Worktree/Branch entfernen). Only-if-tickets: stattdessen die idempotente Einheit `bash scripts/devflow-post-merge-finalize.sh "$TICKET_ID" --pr "$PR_NUM"` (PR verlinken, Ticket `done`, `verify:done`-Event, Plan archivieren, Claims freigeben, Worktree/Branch entfernen).
- **Standing-Direktive bei Kontext-Überlauf:** stoppen und einen strukturierten Handoff-Report liefern (erledigte Schritte, Git-Zustand, offene Schritte).
- **Positiven Endzustand prüfen:** Zum tatsächlichen PR-Head müssen die Required Checks `SUCCESS` belegen; `SKIPPED` genügt nicht. Danach unabhängig prüfen, dass Plan-`completed` gesetzt ist (only-if-tickets: zusätzlich Ticket-Closure mit strukturiertem Receipt) und der eigene Worktree sowie lokaler und Remote-Branch tatsächlich fehlen; Exit 0 allein beweist keinen Abschluss. Bei verbleibenden Refs/Worktrees offen berichten.
- **Rückmeldung an den Auftraggeber (Pflicht):** Endzustand berichten — erledigt, offen.

**Der Orchestrator endet hier** und führt 6.4–7.5 NICHT im eigenen Kontext aus. Er bleibt nur für
die CI-Fix-Schleife (5.5) zuständig, solange sie läuft.

## Schritt 4: Dev-Iteration (optional)

Iteratives Testen im Dev-Namespace auf Fleet ([deploy-routing](references/deploy-routing.md)), setzt voraus, dass nach einem Push das `:dev`-Image per CI gebaut wurde.
Nur wenn `repo.generated_artifacts` true ist, gilt der **Freshness-Guard (vor dem Commit):** `git diff --name-only` darf keine generierten Indexdateien zeigen, sonst regenerate + `git add` nachholen.

## Schritt 5: PR erstellen

Commit → Push → PR läuft nach **`git-workflow` Schritt 2–4** (SSOT): Scope vorab gegen `repo.scopes` prüfen (Annahme: Allowlist mit Preflight), explizite Pathspecs statt `git add -A`, Commit-Verifikation `HEAD_SHA != BASE_SHA`, Scope-Preflight vor `gh pr create`, REST-Fallback für Titel-Edits. Only-if-tickets: Ticket-ID `[$TICKET_ID]` im Subject und `Closes T000XXX` im Body bei Fixes; sonst free-form Scope.
Rufe `commit-commands:commit-push-pr` auf oder führe `gh pr create` manuell aus.

> Auto-Merge **nicht** vor dem ersten Implementierungs-Push aktivieren — sonst mergen Proposal-Commits vorzeitig (only-if-tickets: sonst schließt das Ticket vorzeitig). Der Auto-Merge folgt erst im Merge-Gate (3.8).

## Schritt 5.5: CI/CD-Fix-Schleife (Orchestrator-Zuständigkeit)

**Orchestrator-Schritt, nie als Hintergrund-Monitor.** Auto-Merge ist seit 3.8 angefordert und greift bei grünen Required Checks. Details/Required-Check-Liste: [ci-fix-loop](references/ci-fix-loop.md).

Only-if-tickets: `bash scripts/devflow-ci-watch.sh "$TICKET_ID" "$PR_URL"` (rebased bei `DIRTY` selbst, Exit 3/4 = Rebase-Konflikt/echter `CONFLICTING`-Status). Sonst manueller Watch:
```bash
# Checks + Merge-State pollen, bis MERGED oder Timeout:
gh pr checks <num> && gh pr view <num> --json mergeStateStatus,mergedAt -q '[.mergeStateStatus, .mergedAt]'
```
Bei roten Checks: Logs an einen Fix-Subagenten (Fix-Routine: Freshness → TS → pytest → Kustomize → Commitlint), nach dem Push Loop wiederholen.
`DIRTY` per Rebase gegen `origin/<repo.main_branch>` auflösen; bei echtem `CONFLICTING`-Mergestatus
gibt der **Orchestrator den Konflikt per `SendMessage` an den bereits gespawnten Implementer zurück** (kein neuer Spawn) und prüft nach dessen Push erneut.

## Schritt 6: Phase-Chain-Gate & Merge-Wait

> Schritt 6 läuft im Orchestrator; 6.4–7.5 hat der Finalizer (3.9). `E2E PR` ist kein required
> check. Required-Check-Liste: [ci-fix-loop](references/ci-fix-loop.md).
**Fail-closed Phase-Chain-Gate — PFLICHT vor dem Merge, KEIN `|| true`:**
prüft `plan:done`, `implement:entered` und `verify:done` (Befehle: [phase-events](references/phase-events.md)).
Bei FAIL zuerst die fehlende Zeile nachholen (insb. `verify done` nach grünen Tests).

## Schritte 6.4–7.5 — Merge-Wait, Abschluss, Cleanup

Zuständig ist der Finalizer, den Schritt 3.9 als frischen Subagenten spawnt. `gh pr merge --auto` kehrt sofort zurück; erst den
Merge abwarten ([ci-fix-loop](references/ci-fix-loop.md) §"PR-Merge-Wait-Loop"), dann abschließen ([plan-archive-steps](references/plan-archive-steps.md) bzw. only-if-tickets per Finalize-Skript, siehe 3.9).

> **Merge = Abschluss** — `qa_review`/`awaiting_deploy` nicht als Zwischenstatus setzen. **Reihenfolge:** Archivierung VOR der Branch-Löschung. **Claims vor dem Worktree-Remove freigeben.**

## Schritt 8: Post-Merge Deploy & Verify

Only-if-tickets: `bash scripts/devflow-post-merge-deploy.sh "$TICKET_ID"`. Sonst den Deploy-Pfad aus
[deploy-routing](references/deploy-routing.md) direkt ausführen (Single Source of Truth — nur dort pflegen).
Danach `dev-flow-e2e` ausführen, um E2E-Tests gegen die Live-Umgebung zu schreiben.
> **Mitten in der Umsetzung blockiert?** Nutzer grillen (Grill-HTML pro Slug),
> Antworten im Plan bzw. PR persistieren (only-if-tickets: zusätzlich ans Ticket).

## Übergabe — Kreislauf geschlossen

**Zustand nach Schritt 8:**
- `<repo.main_branch>` enthält die gemergten Änderungen (squash commit)
- Worktree `.worktrees/<slug>` gelöscht, Branch `feature/<slug>` gelöscht
- Plan-Status = `completed` (only-if-tickets: Ticket status = `done`)
- Branch-Lock freigegeben
- Deployed (falls Deploy-Routing Pfad-Treffer)
**Kreislauf zurück zu `<repo.main_branch>`** — nächste Arbeit startet mit `dev-flow-plan` von einem frischen `git pull`.

## Verwandte Skills

| Skill | Beziehung |
|-------|-----------|
| `dev-flow-plan` | **Vorgänger im Kreislauf** — liefert Branch + committiertem Plan |
| `dev-flow-e2e` | Folge — schreibt E2E-Tests nach Deploy |
| `mishap-tracker` | Abschluss — protokolliert Frictions (lokal) |

## Nachbereitung

Melde alle aufgetretenen Fehler oder Prozess-Frictionen über `mishap-tracker`.

## Framework mapping

| Framework | Availability |
|-----------|--------------|
| **Claude Code** | Full |
| **opencode** | Full |
| **agy** | Full |
