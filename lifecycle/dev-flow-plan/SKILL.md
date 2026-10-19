---
name: dev-flow-plan
description: 'Use to choose the development path for a work request in this repo — feature, fix, or chore. Triggers on work request, neue Funktion, feature request, bug fix, chore, dev-flow-plan, plan erstellen. Features/Fixes: brainstorming, spec, staged plan, then dev-flow-execute takes over. Chores route to dev-flow-chore.'
---
# dev-flow-plan — Pfad-Wahl, Brainstorming & Plan

> **Repo-Profil (PFLICHT):** Vor Schritt −3 `repo.yaml` im Consumer-Repo-Root lesen:
> `repo.main_branch`, `repo.tickets` (`none` oder `github`), `repo.task_runner`,
> `repo.generated_artifacts`, `repo.scopes`. Fehlender Schlüssel → Annahme explizit
> nennen. Unten steht `MAIN` für den gelesenen `repo.main_branch`.

> **cwd-Regel (PFLICHT, T006367/T002357):** Git-Aufrufe immer als `git -C "$WT"` bzw. mit
> explizitem cd+guard — **nie auf implizites cwd vertrauen**. Ab Phase B tragen **alle**
> Read/Write/Edit-Pfade den Worktree-Präfix. Gilt für das ganze Dokument.

Der Plan ist der behavior-change-Einstieg des gemeinsamen [Lifecycle-Vertrags](.agents/skills/references/dev-flow-lifecycle.md): Ausgang ist ein Request, Ausgang ein gestagter, gepushter Plan ohne PR; danach übernimmt `dev-flow-execute`. Proposal, Plan-Lint, staged-plan und No-Early-PR-Gates bleiben hier normativ.

Nur-wenn-Tickets (`repo.tickets != none`): „Gestagt" heißt Ticket-Status `plan_staged` (Claim ticket-scoped, `stage-plan --hold` nach dem Commit); `dev-flow-execute` liest den Plan aus der DB. Ohne Tickets (`repo.tickets == none`): kein `ticket.sh`, kein `ticket-mcp`, kein `stage-plan` — „gestagt" heißt Plan committiert und auf den Feature/Fix-Branch gepusht; `dev-flow-execute` liest ihn aus der Branch-Konvention `.agents/plans/<slug>/tasks.md`.

## Wann diese Skill greift
Bei jeder Anfrage in diesem Repo, die etwas verändern will.
**Sage zu Beginn:** "Ich nutze dev-flow-plan für Pfad-Wahl und Planung."

## Position im Git-Kreislauf
```
    ┌──────────────────────────────────────────────────────────┐
    ▼                                                          │
[ MAIN ]                                                       │
    │                                                          │
    ├─► [branch + spec + plan] ── DIESER SKILL ── AUSSTIEG ──►│
    │         (feature / fix)         pushed                   │
    │                                                          │
    └─► [chore direkt] ── dev-flow-chore ──────────────────────┘
```
**EINSTIEG:** `MAIN` — synchronisiert, sauberer Stand
**AUSSTIEG:** Feature/Fix-Branch mit committiertem, gepushtem Plan, kein PR (nur-wenn-Tickets: Ticket `plan_staged`)
**Nächster Schritt:** `dev-flow-execute` — liest den Plan aus der Branch-Konvention `.agents/plans/<slug>/tasks.md` (nur-wenn-Tickets: aus der DB, keine manuelle Pfad-Übergabe nötig)

## Schritt −3: Deep Grilling (optional)
Bei komplexem oder unklarem Feature den User nach einer Grilling-Session fragen. Fragenkatalog:
[dev-flow-gotchas](.agents/skills/references/dev-flow-gotchas.md). Q/A-Session über `lavish`
(`.lavish/<slug>-grilling.html`, Input-Playbook). Antworten in
`.agents/plans/<slug>/grill-answers.md` persistieren (nur-wenn-Tickets: zusätzlich
Ticket-Anlage und Attachments, siehe [grilling-to-ticket](.agents/skills/references/grilling-to-ticket.md)).

## Schritt −2: Main-Branch sync (Pull-First)
```bash
git fetch origin MAIN
if git diff --quiet HEAD; then
  git pull --rebase origin MAIN
else
  git stash && git pull --rebase origin MAIN && git stash pop
fi
```

## Schritt −1: Reaper & Stale-Worktree-Audit
Tote Sessions/Zombies/stale Worktrees räumen und sehen, wer gerade was bearbeitet —
Lock-Lebenszyklus-SSOT: [session-coordination](.agents/skills/references/session-coordination.md) [T000510]:
```bash
bash scripts/agent-lock.sh reap            # cwd-tote Prozesse killen, Worktrees prunen, tote Locks räumen
bash scripts/agent-lock.sh list            # "Wer macht was": laufende Claims anderer Sessions
bash scripts/agent-msg.sh read --unread    # offene Nachrichten paralleler Sessions sichten [T000882]
git worktree list && bash scripts/worktree-git-op-guard.sh
```
Stale Worktrees nur nach bestandenem Vorcheck löschen [T005115]:
`bash scripts/worktree-clean-check.sh <path>` lehnt dirty-Worktrees UND solche mit aktivem
fremden branch-Claim ab (`agent-lock.sh check branch <branch>` — laufende Lauf-/Batch-Session!).
Bei rc 1 den Worktree stehen lassen, sonst
`git worktree unlock <path> 2>/dev/null || true && git worktree remove <path> --force && git branch -D <branch>`.

## Schritt 0: Pfad bestimmen
Wähle einen Pfad und kläre ihn mit dem User ab:
- **feature**: Neue Funktionen oder UI-Elemente. → diese Skill (Feature-Pfad unten).
- **fix**: Fehlerbehebung (erfordert zwingend einen failing Test, Schritt Fix-Pfad; nur-wenn-Tickets: erfordert zusätzlich eine Ticket-ID). → diese Skill (Fix-Pfad unten).
- **chore**: Wartung, Doku, Dependency-Bumps (keine Verhaltensänderung). → **`dev-flow-chore`
  aufrufen und STOPP** — Chores werden dort direkt ausgeführt und gemergt, nicht hier geplant.

Diese Skill plant nur (Feature/Fix) und stoppt vor der Umsetzung; die übernimmt `dev-flow-execute`.

**Artefakt-Ebene:** Die feature/fix/chore-Wahl ist die *Pfad*-Wahl; davor steht die *Artefakt*-Wahl
(PRD vs. ADR vs. Change-Proposal vs. Chore ohne Plan — nur-wenn-Tickets: Chore-Ticket).
Entscheidungstabelle + PRD-Checkliste:
[plan-artifact-level](.agents/skills/references/plan-artifact-level.md).

## Schritt 0.7: Prior-Art-Suche vor der ersten Architekturfrage [T002829]
Bevor dem User eine **Architekturfrage** gestellt wird („gemeinsame Quelle oder duplizieren?",
„Bibliothek oder Inline?", „Hook oder Helper?"), MUSS geprüft sein, ob dieselbe Frage im Repo
schon einmal entschieden wurde. Gilt für **beide** Pfade, **vor** dem Brainstorming. Die Suche geht
über ADRs und Guards, nicht nur über den Code — eine verworfene Lösungsrichtung hinterlässt im
Code keine Spur:
```bash
grep -rn -e '<pfad/der/betroffenen/datei>' -e '<zweiter-pfad>' docs/adr/   # Architekturentscheidungen
grep -rln '<pfad/der/betroffenen/datei>' tests/spec/                      # absichernde Guards
```
Treffer werden zitiert (Datei + Zeilen); die Frage lautet dann „bestehende Entscheidung behalten
oder ersetzen?". Ersetzen geht über ein `RENAMED`/`MODIFIED`-Delta auf den SSOT-Spec. Begründung
und Fallbeispiel: T002817 in [dev-flow-gotchas](.agents/skills/references/dev-flow-gotchas.md).

## Feature-Pfad

### Ablauf in drei Phasen
Die Planphase startet auf `MAIN`; danach entsteht der Worktree.

| Phase | Wo | Was |
|---|---|---|
| **A — Proposal** | `MAIN` | Assets sammeln, Codebase erkunden, Plan Intel Bundle (`intel.json`) füllen, Design-Bundle co-lokalisieren, Lavish-Board, **Brainstorming**, Plan in `.agents/plans/<slug>/` anlegen — Design-Spec-Frontmatter per Task-Runner/Helper des Repos (`scripts/vda.sh frontmatter` bzw. Repo-Äquivalent) |
| **B — Branch live** | Worktree | Worktree anlegen, agent-lock claimen, Artefakte verschieben, Scaffold-Commit + Push |
| **C — Partial-Pipeline** | Worktree | Decompose in Partials, pro Partial: Plan schreiben → committen (nur-wenn-Tickets: → stagen → enqueuen); danach plan-lint, Embedding, finaler Push |

Vollständige Schrittfolge samt Befehlen, Decompose-/Fan-out-Mechanik und Kontext-Injektion für
Plan-Subagenten: [dev-flow-plan-phases](.agents/skills/references/dev-flow-plan-phases.md).

**Intel-Quellen des Bundles** (Phase A.1.5) — jede Sektion ist an ihre Quelle gebunden: `symbols`/`signature`/`type_text`/`call_graph` aus **codebase-memory** + **LSP**-Hover; `db_tables` aus **mcp-postgres** (read-only); `external_types` aus **context7**; `impact_files`/`s1_*` aus `wc -l` + Baseline (`docs/code-quality/baseline.json` bzw. Repo-Äquivalent). Unerreichbare Quelle → `risks[]`-Eintrag statt leerer Sektion. Format: [plan-intel-bundle](.agents/skills/references/plan-intel-bundle.md).

### Guards des Feature-Pfads
- **Preflight: Check merged** (T002279) — beide Pfade, vor der Worktree-Anlage: prüfen, ob der
  Fix auf `MAIN` schon drin ist. Nur-wenn-Tickets: `bash scripts/agent-lock.sh check-merged "$TICKET_EXT_ID"` (`rc=1` = schon gefixt → Ticket `done`, abbrechen). Ohne Tickets: `git log origin/MAIN --grep='<slug|symptom>'` — Treffer → abbrechen.
- Alle weiteren Guards (Kollisions-Check T002444, Brainstorming-Pflicht, Ticket-vor-Branch nur-wenn-Tickets, disjunkte Partials, Plan-Mutation, Slot-Gating, Design-Asset-Qualität): [feature-path-guards](references/feature-path-guards.md).

### Schritt 3.7: Plan-Erstellung — Decompose, dann paralleler Fan-out (T002074)
Zweistufig aus `intel.json` (deterministisch via Plan-Intel-Helper des Repos, `scripts/plan-intel.sh` bzw. Repo-Äquivalent) in Partials mit disjunkten `target_files` decomposen (Tests separat, Obergrenze 9), dann schreiben **parallele Plan-Subagenten** je ihre `tasks.d/pX-<name>.md`; der Orchestrator schreibt den `tasks.md`-Index mit Partial-Manifest, `## File Structure` und finalem Verify-Task. Mechanik, Kontext-Injektion und Provisionierung: [dev-flow-plan-phases](.agents/skills/references/dev-flow-plan-phases.md).

**SID-Propagation (PFLICHT, T006365):** Ermittle deine Session-SID mit
`bash scripts/agent-lock.sh mine` und weise die Plan-Subagenten an, in jedem Bash-Call zuerst
`export AGENT_LOCK_SID=<deine-sid>` auszuführen — sonst blockiert der Worktree-Write-Guard ihre
Datei-Tools.

**Der Subagent-Prompt MUSS [plan-quality-gates](.agents/skills/references/plan-quality-gates.md) verbindlich einbinden** —
der Subagent liest die Datei und schreibt den Plan dagegen. Sie ist die kanonische Referenz für
alle plan-lint Hard Rules (Details dort, nicht hier dupliziert).

### Schritt 3.8: Plan-Qualitäts-Gate (deterministischer Linter + advisory LLM-QA)
Führe ZUERST den fail-closed Linter auf den vom Subagenten zurückgegebenen Plan-Pfad aus — das ist
das **harte Gate**:
```bash
bash scripts/plan-lint.sh .agents/plans/<slug>/tasks.md
```
- **PASS (Exit 0):** optional die advisory LLM-QA (bricht nie):
  `bash scripts/plan-qa-check.sh .agents/plans/<slug>/tasks.md || true` — dann Schritt 4.
- **FAIL (Exit 1):** der Linter listet die Hard-Fails (F1/F2/STRUCT/P1/B1a). Erneut an einen
  Plan-Subagenten delegieren (Schritt 3.7) mit den Hard-Fails als Korrektur-Hinweis, bis PASS.
  KEIN Weitergehen mit rotem Linter.
- **Retry-Cap (T901790):** nach dem **3. FAIL in Folge** für denselben Plan NICHT weiter
  delegieren, sondern an den Operator eskalieren (nur-wenn-Tickets: Ticket-Kommentar mit den
  Hard-Fails + `mishap-tracker`-Eintrag `plan-lint-retry-cap`; ohne Tickets:
  `mishap-tracker`-Eintrag `plan-lint-retry-cap`).

### Schritt 4: Plan prüfen & übernehmen
Du behältst deinen vollen Brainstorming-Kontext: lies den zurückgegebenen Plan und prüfe ihn gegen
die im Brainstorming getroffenen Entscheidungen. Zusätzlich die Gate-Konformität (Checkliste in
[plan-quality-gates](.agents/skills/references/plan-quality-gates.md)): S1-Budgets gegen die **wirksame Schwelle**
(Baseline-Wert falls gebaselined, sonst Limit) pro Datei notiert — und bei Budget≈0 ein echter
Verkleinerungs-/Split-Schritt statt kosmetischem Zusammenziehen? Finaler Verifikations-Task aus
`repo.task_runner` lesen (bei `taskfile`: `task test:changed`; Freshness-Teil nur-wenn-generated-artifacts: `+ task freshness:regenerate + task freshness:check`)? Keine
Brand-Domain-Literale in den Code-Snippets? Bei Lücken erneut delegieren (Schritt 3.7) mit
konkreten Korrektur-Hinweisen.

### Schritt 4.5: Claim (PFLICHT vor Commit)
Nur-wenn-Tickets — Ticket anlegen oder wiederverwenden (SSOT: [ticket-stage-procedure](.agents/skills/references/ticket-stage-procedure.md)), dann ticket-scoped claimen, bevor der Pre-Commit-Guard die Lock-Datei liest:
```bash
bash scripts/agent-lock.sh claim ticket "$TICKET_EXT_ID" \
  --branch "$(git -C "$WT" branch --show-current)" --worktree "$WT" --label dev-flow-plan
```
`stage-plan` läuft erst **nach** dem Commit.
Ohne Tickets — nur den Branch claimen:
```bash
bash scripts/agent-lock.sh claim branch "$(git -C "$WT" branch --show-current)" \
  --worktree "$WT" --label dev-flow-plan
```

### Schritt 5: Commit & Push (nur-wenn-Tickets: dann stagen) — dann STOPP
Nur-wenn-Tickets — ein Aufruf statt der Sequenz unten (T900985): devflow-mcp `plan_stage(ticket, slug,
branch_type, plan_markdown | plan_file, design_markdown?, partials)` legt Worktree + Branch von
`origin/MAIN` an, claimt, schreibt Plan und Design, lässt `plan-lint` laufen (rot = Abbruch mit
strukturierten Befunden, Worktree bleibt), dann Preflight, Commit, Push und
`stage-plan --hold`.

**Pre-Commit-Vertrag (PFLICHT):** Nur-wenn-Tickets via `plan-preflight.sh pre-commit --ticket "$TICKET_EXT_ID"`
(`rc=0` grün, `rc=1` Guard verletzt, `rc=2` Umgebungsfehler). Ohne Tickets gilt der manuelle
Vertrag (kein `plan-preflight.sh` — verlangt eine Ticket-ID):

1. **Nicht auf MAIN committen:** Plan-Commits auf `MAIN` sind verboten, nur ein
   Worktree-Branch ist zulässig.
2. **Staged-Set-Pflicht [T005114]:** geprüft wird `git diff --cached --name-only`; erlaubt sind
   Pfade unter `tests/` und `.agents/plans/` (nur-wenn-generated-artifacts: plus exakt
   `components/website/src/data/test-inventory.json`). Andere gestagte Dateien brechen ab
   (Abhilfe: `git restore --staged <pfad>`). Unstaged/untracked wird nicht geprüft.
3. **Claim vorhanden [T003102]:** nur-wenn-Tickets `agent-locks/ticket__${TICKET_EXT_ID}.json`
   (Fallback `agent-locks/branch__${BRANCH_SLUG}.json`, beide Scopes akzeptiert); ohne Tickets
   `agent-locks/branch__${BRANCH_SLUG}.json` — fehlt die Lock-Datei, vorher claimen (Schritt 4.5).

```bash
git -C "$WT" add .agents/plans/<slug>/
git -C "$WT" commit -m "chore(plans): stage <slug> for execution"   # nur-wenn-Tickets: Suffix " [$TICKET_EXT_ID]"
git -C "$WT" push -u origin "$(git -C "$WT" branch --show-current)"
```
Nur-wenn-Tickets: ERST JETZT stagen — Flag-Semantik (`--hold`/`--partials`/`--allow-empty-touched`):
[ticket-stage-procedure](.agents/skills/references/ticket-stage-procedure.md) §Flag-Semantik.
Ohne Tickets: der Push IST das Stagen — `echo "plan done $(date -u +%FT%TZ) plan-gestagt" >> .agents/plans/<slug>/phase-events.log` nicht vergessen.

### Schritt 6: Optionaler Plan-Review (interaktiv)
Der Plan lässt sich annotierbar rendern und im Browser reviewen
(`bash scripts/plan-review/plan-review.sh render .agents/plans/<slug>/tasks.md`). Details:
[plan-review-ui](.agents/skills/references/plan-review-ui.md).

**STOPP.** Branch, Spec und Plan sind committed und gepusht (nur-wenn-Tickets: Ticket per
`execution_released=false` zurückgehalten, bis `dev-flow-execute` es mit `release-hold` freigibt).

## Fix-Pfad

Ein Fix braucht **zwingend einen failing Test**, bevor der Plan geschrieben wird. Der Test ist
eine pytest-Funktion in `tests/py/spec/<bereich>/test_<kurz_slug>.py` (Bereich aus
Feature-Name/Symptom — nur-wenn-Tickets: aus dem Ticket-Titel), nicht in einem
ticket-nummerierten Modul. Setzt er ein externes Binary oder
einen externen Dienst voraus, gehört
der Verfügbarkeits-Guard (`if shutil.which("<binary>") is None: pytest.skip("<binary> binary not installed")`)
schon in die **Rotphase**. Vorher prüfen: `grep -rn '<binary>' .github/workflows/`; **0 Treffer
heißt: in CI nicht vorhanden**. Begründung: T002820 in
[dev-flow-gotchas](.agents/skills/references/dev-flow-gotchas.md).

**Bug-Triage: Ursachen-Verifikation vor Brainstorming [T002448-M5]:** Beobachtetes Symptom (Fakt)
und angenommene Ursache (Hypothese) trennen. Die Ursache MUSS vor „Lösung entwerfen" mit einem
minimalen Reproducer oder Log-Evidenz belegt sein; die Trennung gehört ins Proposal.
English: verify the bug cause during triage — distinguish observed symptom from assumed root cause,
and validate the cause with evidence before designing the solution.

Schritte 1–5 im Detail (nur-wenn-Tickets: Ticket, Worktree, Claims, Lavish-Board, Brainstorming mit
Root-Cause-Fokus, failing Test, Plan, `stage-plan`, Commit — ohne Tickets: ohne Ticket-Schritte):
[dev-flow-plan-phases](.agents/skills/references/dev-flow-plan-phases.md) §Fix-Pfad. Der abschließende Stage-Commit:

```bash
git -C "$WT" add tests/ .agents/plans/<slug>/tasks.md
(cd "$WT" && git commit -m "chore(plans): add failing test + stage plan")   # nur-wenn-Tickets: Suffix " [$TICKET_EXT_ID]"
git -C "$WT" push -u origin "$(git -C "$WT" branch --show-current)"
```
Der Commit enthält nur RED-Test und Plan-Artefakte, deshalb `chore(plans):` — nie `fix(`/`feat(`
(T001434 in den Gotchas; Guard blockiert).

## Chore-Pfad
Ausgelagert nach `dev-flow-chore` — Chores brauchen keinen Plan und werden dort direkt ausgeführt
und gemergt. In Schritt 0 für Chores sofort `dev-flow-chore` aufrufen und hier stoppen.

## Übergabe an dev-flow-execute
**Zustand bei STOPP:**
- Branch `feature/<slug>` oder `fix/<slug>` auf Remote gepusht
- Plan `.agents/plans/<slug>/tasks.md` committed (ohne Tickets: + `plan done` in `phase-events.log`)
- Nur-wenn-Tickets: Ticket status = `plan_staged`
- Branch-Lock aktiv (andere Sessions sehen diesen Branch als belegt)
- **Kein PR** — der Plan-Stand ist ein gepushter Branch, nichts weiter. Wird aus anderem Grund
  früh einer gebraucht: `--draft` + Titel-Präfix `[plan-only]` (T002816 in den Gotchas).

**Nächster Schritt:** `dev-flow-execute` aufrufen. Ohne Tickets liest es den Plan aus der
Branch-Konvention `.agents/plans/<slug>/tasks.md` — keine manuelle Pfad-Übergabe nötig.
Nur-wenn-Tickets liest es ihn aus der DB (`FACTORY-PLAN-REF`-Kommentar).

Status-Übersicht und Ausführungsoptionen: [plan-batch-status](references/plan-batch-status.md).

## Verwandte Skills
| Skill | Beziehung |
|-------|-----------|
| `using-git-worktrees` | Hintergrund — ersetzt durch Worktree-Helper des Repos (git-crypt-safe) |
| `superpowers:brainstorming` | **IMMER** aufgerufen — Feature-Pfad Schritt 3, Fix-Pfad Schritt 2.8 |
| `superpowers:writing-plans` | Aufgerufen vom Plan-Subagenten (Schritt 3.7) |
| `dev-flow-execute` | **Nachfolger im Kreislauf** — implementiert den erstellten Plan |
| `dev-flow-chore` | Geschwister — Chores statt Features/Fixes (direkter Kurzschluss) |
| `mishap-tracker` | Abschluss — protokolliert Frictions |

## Nachbereitung & Mishap Report
Melde alle aufgetretenen Fehler oder Prozess-Frictionen am Ende des Skills über `mishap-tracker`
(`Invoke mishap-tracker` bzw. `bash scripts/hooks/mishap-tracker.sh`).

## Framework mapping

| Framework | Availability |
|-----------|--------------|
| **Claude Code** | Full — load via `load skill <name>` or matches on description triggers |
| **opencode** | Full — geladen als `dev-flow-plan` (Directory-Symlink auf diese Shared Source). Sub-Delegation über `background-agents.ts` (`delegate` für read-only, native write-capable Delegation sonst); alle CLI-/MCP-Aufrufe sind framework-agnostisch |
| **agy** | Full — treat the opencode path as authoritative. All CLI tools and MCP calls work identically |
