---
name: dev-flow-chore
description: 'Use for maintenance with NO behavior change — documentation, dependency bumps, config edits, renames, CI tweaks, dead-code and file cleanup. Triggers on chore, docs update, bump dependency, rename, tidy up, remove unused, CI config tweak. Executes and merges inline in one pass — no spec, no plan, no dev-flow-execute handoff. If the change alters what the software does, stop and use dev-flow-plan instead; that boundary decides the path, not the size of the diff.'
---
# dev-flow-chore — Wartung direkt ausführen & mergen

> **Repo-Profil (PFLICHT):** Vor Schritt 0 `repo.yaml` im Consumer-Repo-Root lesen:
> `repo.main_branch`, `repo.scopes` (`free` oder Allowlist-Quelle), `repo.task_runner`,
> `repo.generated_artifacts`. Fehlender Schlüssel → Annahme explizit nennen. Unten steht
> `MAIN` für den gelesenen `repo.main_branch`.

> **cwd-Regel (PFLICHT, T006367/T002357):** Git-Aufrufe immer als `git -C <worktree>` bzw. mit
> explizitem cd+guard — **nie auf implizites cwd vertrauen**. Nach dem Worktree-Wechsel tragen
> alle Read/Write/Edit-Pfade den Worktree-Präfix. Gilt für das ganze Dokument.

Der gemeinsame Lifecycle-Vertrag besitzt hier den No-Behavior-Change-Einstieg und delegiert Git-,
Verifikations- und Cleanup-Mechanik an `git-workflow` bzw. `verification-block`. Reine
Playwright-Änderungen laufen als spezialisierter test-only Chore über `dev-flow-e2e`.

Chores brauchen kein Ticket (Branch + squash-gemergte Commits sind die Audit-Spur) — unabhängig
von `repo.tickets`.

**Sage zu Beginn:** "Ich nutze dev-flow-chore und führe die Wartung direkt aus."

---

## Wann diese Skill greift

Eine **Chore**: Wartung ohne Verhaltensänderung — Doku, Dependency-Bumps, Config/Rename, CI-Tweaks,
Aufräumen. Chores brauchen **keinen** Plan und **keinen** `dev-flow-execute`-Handoff: sie werden in
einem Rutsch erledigt und gemergt. Für Features/Fixes stattdessen `dev-flow-plan` nutzen.

---

## Position im Git-Kreislauf

```
    ┌────────────────────────────────────────────────────┐
    ▼                                                    │
[ MAIN ]                                                 │
    │                                                    │
    └──► [branch] ──► [ändern + testen] ──► [PR+merge] ──► AUSSTIEG
              DIESER SKILL (Kurzschluss — kein Plan-Handoff)   │
                                                               │
                                    zurück zu [ MAIN ] ────────┘
```

**EINSTIEG:** `MAIN` — synchronisiert, sauberer Stand
**AUSSTIEG:** PR gemergt zu `MAIN`, Worktree bereinigt, Kreislauf geschlossen
**Kurzschluss:** kein Zwischenstopp bei `dev-flow-execute` — Chores sind einzügig

---

## Schritt 0: Reaper & Pull-First

Läuft nach **`git-workflow` Schritt 0** (SSOT — dort die vollständige Sequenz inkl.
`git-stash-net.sh pop --by-message` und der Stash-Pop-Verifikation; hier keine eigene
Kopie pflegen). Nur chore-spezifisch: Bei fremder Aktivität im Haupt-Checkout wird der
lokale `MAIN`-Sync übersprungen — `mc_foreign_activity_detected` aus
`scripts/lib/main-checkout-foreign-guard.sh` entscheidet das (T003078/T003097). Der
lokale `MAIN`-Sync ist Hygiene, keine Korrektheitsvoraussetzung für den nachfolgenden
Worktree-Aufruf, der ohnehin von `origin/MAIN` aus anlegt.

## Schritt 0.5: Wiederkehrend oder einmalig?

Frage den User, ob die Chore regelmäßig laufen soll. Falls ja, rufe `/schedule` auf und richte
einen Cron-Job ein. **STOPP hier.**

## Schritt 1: Worktree anlegen & claimen

> **Test-only-Kurzpfad (kein Worktree):** Berührt die Chore **ausschließlich** Testdateien
> (z.B. `tests/py/**/*.py`, `*.test.ts`, Playwright-Specs — „schreib einen Test für X") — dann
> entfällt der Worktree als Standardfall, solange kein anderer Prozess konkurrierend im
> Haupt-Checkout schreibt. Prüfe das:
> ```bash
> bash scripts/agent-lock.sh activity   # Locks + laufende Prozesse in Worktree-Pfaden [T003098] — list allein zeigt Sessions erst nach ihrem ersten Commit
> ```
> Ist die Liste leer (solo, kein konkurrierender Prozess), arbeite **inline im Haupt-Checkout**:
> ```bash
> git checkout -b chore/<slug>
> bash scripts/agent-lock.sh claim main-checkout --branch "chore/<slug>" --label dev-flow-chore
> ```
> Der `.githooks/pre-commit`-Mutex blockt konkurrierende Commits anderer Sessions währenddessen.
> Zeigt `activity` fremde lebende Aktivität, oder berührt die Chore auch Nicht-Testdateien
> (Implementierung + Test zusammen) → regulärer Worktree-Pfad unten.

Regulärer Pfad (Default für alles außer dem Test-only-Kurzpfad oben):
```bash
# git-crypt-safe: creates the worktree, handles git-crypt
bash scripts/worktree-create.sh chore/<slug> <worktree-pfad-nach-Repo-Konvention>
cd <worktree-pfad>
bash scripts/agent-lock.sh claim branch "chore/<slug>" --worktree "$PWD" --label dev-flow-chore
```

> **Ab hier gilt die cwd-Regel oben:** Datei-Tool-Pfade tragen den Worktree-Präfix, sonst
> trifft ein alter Hauptcheckout-Pfad still die falsche Arbeitskopie (T002350).

Claim-Semantik, main-checkout-Sonderfall (`claim main-checkout`) und Release:
[session-coordination](.agents/skills/references/session-coordination.md) — ausschließlich
branch-scoped Claims, kein Ticket-Scope.

## Schritt 2: Änderungen vornehmen

Setze die Wartung um. Bei mechanischer Arbeit über mehrere Dateien kannst du an einen passend
provisionierten Subagenten delegieren (siehe [subagent-provisioning](.agents/skills/references/subagent-provisioning.md) — Chores sind i.d.R. `haiku`/`sonnet`, Effort low).

## Schritt 3: Verifizieren

Verify-Block ausführen (die vier Befehle, Freshness-Guard, S1-Ratchet-Erklärung) — **SSOT:**
[verification-block](.agents/skills/references/verification-block.md). Verifizierende Kommandos
aus `repo.task_runner` lesen; Freshness-Teil nur-wenn-generated-artifacts
(`repo.generated_artifacts == true`).

> **⚠ S1-Gate-Guard (Chores ohne Plan!):** Chores haben kein Zeilenbudget-Planungsschritt.
> Berührt die Chore Code-Dateien (`.ts/.svelte/.astro/.sh/.mjs/...`), vor dem Commit den
> **Restbudget-Check** aus dem verification-block laufen lassen (`plan-lint.sh residual_budget`-
> Schleife) — bei Restbudget ≤ 0 die Datei **echt verkleinern**, nicht kosmetisch zusammenziehen.

Siehe [dev-flow-gotchas](.agents/skills/references/dev-flow-gotchas.md) für TypeScript/pnpm-Gotchas in Worktrees.

## Schritt 4: Commit, Push & PR

Läuft nach **`git-workflow` Schritt 2–4** (SSOT): git-crypt-Staging-Guard [T001210]
(explizite Pathspecs, NIE `git add -A`, Secret-in-index-Guard), Commit-Verifikation
`HEAD_SHA != BASE_SHA` [T000925], `preflight-pr-scope.sh` vor `gh pr create`,
REST-Fallback für Titel-Edits.

Chore-spezifisch: Titelformat `chore(<scope>): <subject>`. Scope aus `repo.scopes` lesen —
bei `free` ein freies Scope-Wort wählen, bei Allowlist via
`bash scripts/validate-commit-msg.sh scopes` wählen (kein Ticket-Tag).

Rufe `commit-commands:commit-push-pr` auf (Claude Code slash-command) oder führe `gh pr create` manuell aus (beide Frameworks).

## Schritt 5: Merge wenn CI grün

**`git-workflow` Schritt 5–6** (SSOT): CI-Fix-Loop bis grün, dann aus dem Haupt-Repo
`gh pr merge --auto --squash` (kein `--delete-branch` — Löschung in Schritt 6, T004612).

## Schritt 6: Worktree & Branch bereinigen

Nach bestätigtem Merge und tatsächlich erfolgreichen Required Checks abschließen. Die bereits
etablierte eigene `AGENT_LOCK_SID` weitergeben; keine fremde Session-ID übernehmen.
Bevorzugt die idempotente Einheit (falls im Repo vorhanden):
```bash
export AGENT_LOCK_SID
bash scripts/devflow-post-merge-finalize.sh --branch "$BRANCH" --no-plan --pr "$PR_NUM"
```
Fallback (manuell, z.B. wenn das Script ein entferntes Ticket-Backend voraussetzt):
```bash
# Merge verifizieren (Timestamp, nie Exit-Code):
m=$(gh pr view <num> --json mergedAt -q '.mergedAt')
[ -n "$m" ] && [ "$m" != "null" ] || { echo "FAIL: kein Merge"; exit 1; }
# Eigenen Branch-Claim freigeben, DANN Worktree + lokalen/Remote-Branch entfernen:
cd "$MAIN_REPO"
bash scripts/agent-lock.sh release branch "$BRANCH"
git worktree remove "$WORKTREE"
git branch -D "$BRANCH" && git push origin ":$BRANCH"
```

Ein Chore ohne Plan hat keinen Plan-Receipt; keinen solchen Archiv-Beleg behaupten.
Den tatsächlichen Endzustand prüfen: eigener Worktree, lokaler und Remote-Branch
entfernt, eigene Claims freigegeben. Exit 0 allein reicht nicht. Die gemeinsame
[repo-hygiene-ops §2](../references/repo-hygiene-ops.md#2-stale-branches) beschreibt
die positive Prüfung und den Remote-Control-Ausnahmefall ohne Hook-Umgehung.

Beim Test-only-Kurzpfad gibt es keinen Worktree zu entfernen. Nur SID-eigene Claims
freigeben; einen fremd genutzten Hauptcheckout weder umschalten noch entfernen.
Solange der Chore-Branch dort ausgecheckt ist, den lokalen Branch erhalten und den
Cleanup als offen berichten. Für sichere Branch-/Remote-Nacharbeit dieselbe SSOT
anwenden; ein eigener Control-Worktree berechtigt nicht zum Wechseln fremder
Checkouts.

## Schritt 7: Deploy (falls nötig)

Nur wenn die Chore deploybare Pfade berührt — Mapping in
[deploy-routing](.agents/skills/references/deploy-routing.md) (Single Source of Truth).

---

## Übergabe — Kreislauf geschlossen

**Zustand nach Schritt 6:**
- `MAIN` enthält die gemergten Änderungen (squash commit)
- Worktree (Repo-Konvention) gelöscht, Branch `chore/<slug>` gelöscht
- Branch-Lock freigegeben

**Kreislauf zurück zu `MAIN`** — nächste Arbeit startet mit `dev-flow-plan` oder erneutem `dev-flow-chore`.

---

## Verwandte Skills

| Skill | Beziehung |
|-------|-----------|
| `dev-flow-plan` | Geschwister — Features/Fixes (mit Plan + Handoff) statt Chores |
| `git-workflow` | **SSOT für Schritt 4–6** — Commit/PR/Merge/Cleanup |
| `using-git-worktrees` | Hintergrund — wird hier durch Worktree-Helper des Repos (git-crypt-safe) ersetzt |
| `mishap-tracker` | Abschluss — protokolliert Frictions |

## Nachbereitung & Mishap Report

Melde alle aufgetretenen Fehler oder Prozess-Frictionen am Ende über `mishap-tracker`
(`Invoke mishap-tracker` bzw. `bash scripts/hooks/mishap-tracker.sh`).


## Framework mapping

| Framework | Availability |
|-----------|--------------|
| **Claude Code** | Full — load via `load skill <name>` or matches on description triggers |
| **opencode** | Full — available as a listed skill. All tools (CLI, MCP) are framework-agnostic |
| **agy** | Full — treat the opencode path as authoritative. All CLI tools and MCP calls work identically |
