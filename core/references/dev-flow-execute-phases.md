# dev-flow-execute — Phasen im Detail

Referenz zu `dev-flow-execute` und dem [Lifecycle-Vertrag](dev-flow-lifecycle.md). Der Skill-Body führt Ablauf, Delegation und Gates; hier stehen die Befehlsfolgen der mechanischen Schritte.

Repo-Konfiguration: `repo.yaml` (`repo.main_branch`, `repo.tickets`, `repo.generated_artifacts`, `repo.task_runner`). `MAIN` unten = `repo.main_branch`. Ticket-Blöcke gelten nur bei `repo.tickets: true`; sonst entfällt alles mit Ticket-ID, `ticket.sh`, DB-Reads — Fortschritt lebt in Commits und `phase-events.log`.

---

## Plan-Slug ermitteln

Slug aus dem Branch-Namen (ohne `feature/`- bzw. `fix/`-Präfix):

```bash
CURRENT_BRANCH=$(git branch --show-current)
SLUG=$(echo "$CURRENT_BRANCH" | sed 's#^[a-z]*/##')
PLAN_FILE=".agents/plans/$SLUG/tasks.md"
git cat-file -e "HEAD:$PLAN_FILE" || { echo "Plan nicht im Git-Tree." >&2; exit 1; }
```

Bei mehreren Plan-Branches den User nach dem gewünschten Branch fragen.

Nur bei `repo.tickets: true`: `TICKET_ID` ersatzweise aus DB holen (MCP-first `mcp-postgres`, Fallback `kubectl exec ... psql`), bei mehreren staged plans User fragen.

---

## Schritt −1 bis 0.5 — Pre-Flight, Sync, Worktree-Konsistenz, Rebase

Branch vor der ersten Git-Operation claimen:

```bash
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")
bash scripts/agent-lock.sh claim branch "$CURRENT_BRANCH" --worktree "$(pwd)" --label dev-flow-execute
RET=$?
case $RET in
  0) echo "Branch $CURRENT_BRANCH geclaimed." ;;
  1) echo "Branch $CURRENT_BRANCH wird bereits bearbeitet." >&2
     echo "  bash scripts/agent-msg.sh read --mine --unread" >&2
     exit 1 ;;
  2) echo "Branch $CURRENT_BRANCH geclaimed — Status-Check verweigert." >&2
     exit 1 ;;
esac
```

Ankündigung broadcasten:

```bash
bash scripts/agent-msg.sh post "dev-flow-execute startet Arbeit an Branch $CURRENT_BRANCH" --to all
```

Nur bei `repo.tickets: true` zusätzlich: Ticket-Status prüfen (`plan_staged` = fortfahren, `done`/`archived` = abbrechen) und ggf. separaten Ticket-Claim setzen.

## Schritt 0: Main-Branch im Haupt-Repo synchronisieren (Pull-First)

```bash
MAIN=$(grep -oP 'main_branch:\s*\K.*' repo.yaml 2>/dev/null || echo main)
bash scripts/agent-lock.sh reap
bash scripts/agent-msg.sh read --unread
MAIN_REPO=$(git worktree list --porcelain | awk '/^worktree/{print $2; exit}')
if [[ -n "$MAIN_REPO" && -d "$MAIN_REPO" ]]; then
  (cd "$MAIN_REPO" && git fetch origin "$MAIN" && git pull --rebase origin "$MAIN")
else
  git fetch origin "$MAIN" && git pull --rebase origin "$MAIN"
fi
```

Lock-Lebenszyklus: siehe session-coordination (SSOT).

## Schritt 0: Worktree-Konsistenz prüfen

```bash
CURRENT_BRANCH=$(git branch --show-current)
EXPECTED_BRANCH="$CURRENT_BRANCH"
if [[ -z "$CURRENT_BRANCH" || "$CURRENT_BRANCH" == "HEAD" ]]; then
  echo "HALT: Kein gueltiger Branch (detached HEAD)." >&2
  exit 1
fi
```

Läuft die Phase versehentlich im Haupt-Checkout, schreibt der Implementer ins Haupt-Repo statt in eine isolierte Kopie:

```bash
if [[ "$PWD" != *".worktrees/"* ]]; then
  echo "Kein isolierter Worktree unter .worktrees/* (PWD=$PWD)."
  SLUG=$(echo "$CURRENT_BRANCH" | sed 's#^[a-z]*/##')
  WORKTREE_PATH=".worktrees/${SLUG}"
  bash scripts/worktree-create.sh "$CURRENT_BRANCH" "$WORKTREE_PATH"
  if [[ -d "$WORKTREE_PATH" ]]; then
    echo "Worktree bereit unter $WORKTREE_PATH — dort fortsetzen."
  else
    echo "Worktree-Erstellung fehlgeschlagen." >&2
    exit 1
  fi
  exit 1
fi
```

## Schritt 0.5: Sync mit Main-Branch und Rebase

```bash
MAIN=$(grep -oP 'main_branch:\s*\K.*' repo.yaml 2>/dev/null || echo main)
git fetch origin "$MAIN"
git rebase "origin/$MAIN"
# Falls push fehlschlaegt: --force-with-lease
```

---

## Schritt 1 — Plan-Pfad laden

Standard: Konvention `.agents/plans/<slug>/tasks.md`, immer gegen den Git-Tree verifizieren:

```bash
BRANCH=$(git branch --show-current)
SLUG=$(echo "$BRANCH" | sed 's#^[a-z]*/##')
PLAN_FILE=".agents/plans/$SLUG/tasks.md"
if ! git cat-file -e "HEAD:$PLAN_FILE" 2>/dev/null; then
  echo "Plan-Datei '$PLAN_FILE' nicht im Git-Tree (Branch: $BRANCH)."
  exit 1
fi
echo "Plan geladen: $PLAN_FILE (Branch: $BRANCH)"
PLAN_DIR=".agents/plans/$SLUG"
if [[ ! -d "$PLAN_DIR" ]]; then
  echo "$PLAN_DIR/ fehlt — nicht von dev-flow-plan angelegt."
fi
```

Nur bei `repo.tickets: true`: Pfad stattdessen aus DB (`FACTORY-PLAN-REF branch=<branch> plan=<plan_path>` via `vda.sh ticket get`), daraus `BRANCH`/`PLAN_FILE` parsen; zusätzlich `$PLAN_DIR/.ticket` prüfen.

---

## Schritt 1.4 / 1.4.5 / 1.4.6 — Doppelarbeit-Guard

Branch-Claim aus Schritt −1 nur verifizieren:

```bash
bash scripts/agent-lock.sh check branch "$CURRENT_BRANCH" | head -1 | grep -q '^mine$' \
  || { echo "Branch $CURRENT_BRANCH nicht mehr geclaimed — Abbruch." >&2; exit 1; }
```

Registry-Overlap für geteilte Hochfrequenz-Dateien prüfen (SSOT session-coordination).

Nur bei `repo.tickets: true`: zusätzlich Ticket-Claim verifizieren und Pipeline-Modus aus DB lesen (`slot_count` > 1 = Multi-Partial in Manifest-Reihenfolge, = 1 = Single-Shot). Sonst: Partials strikt in `tasks.md`-Manifest-Reihenfolge abarbeiten.

### Schritt 1.4.7: Auto-Merge-Zustand prüfen

```bash
bash scripts/check-pr-automerge.sh --branch "$BRANCH"
```

- `rc=1`: parallele Session oder User-PR mit Auto-Merge — koordinieren, nicht duplizieren.
- `rc=2`: Umgebungsfehler.

---

## Schritt 1.5 — Kollisions-Grundlage: File Structure

Kollisionserkennung läuft über Dateien: der `## File Structure`-Block des Plans ist plan-lint Hard Rule STRUCT1 und existiert zwingend. Berührt die Umsetzung nicht geplante Dateien, vor dem Commit `agent-collision.sh check --branch` laufen lassen und bei Treffern koordinieren.

Nur bei `repo.tickets: true`: Ticket auf `in_progress` setzen (MCP-first, Fallback `vda.sh ticket update-status` + `devflow-phase.sh plan entered`) und neue Pfade zu `touched_files` ergänzen (Liste ersetzen nur nach vorherigem Lesen, sonst gehen Stage-Pfade verloren). Phase-Events (`plan`/`implement`/`deploy`) entstehen aus Statuswechseln, Dedup macht Doppel-Emission harmlos; `verify:done` bleibt Pflicht.

## Schritt 1.7: Visual und Textual Assets

Design-Quellen sind Repo-Dateien (Mockups, Specs im Plan-Ordner `.agents/plans/<slug>/`). Pflicht für UI-Arbeiten: alle relevanten Bild- und Textdateien im Plan-Ordner einlesen, nicht auf Prose verlassen.

Nur bei `repo.tickets: true`: zusätzlich Ticket-Anhänge laden (MCP-first `node_get_attachments`, Fallback Ticket-CLI) und ebenfalls alle einlesen.

---

## Schritt 6.4 bis 7.5 — Merge-Wait, Abschluss, Archivierung, Cleanup

Diese Schritte laufen nicht im Orchestrator, sondern in einem frischen Finalizer-Subagenten. Jeder Schritt überspringt erledigte Arbeit; ein zweiter Lauf setzt an der ersten offenen Stelle fort.

Vor dem Abschluss: Merge-Wait-Loop aus `ci-fix-loop` §"PR-Merge-Wait-Loop" von dort ausführen, nicht rekonstruieren. Bei Timeout keinen Abschluss behaupten — strukturiert berichten, Schritte sind manuell nachholbar.

Nur bei `repo.tickets: true`: Finalizer ruft `bash scripts/devflow-post-merge-finalize.sh "$TICKET_ID" --pr "$PR_NUM"` (idempotent, Exit 0 = erledigt/übersprungen). Sonst manuelle Einheit aus plan-archive-steps: Merge verifizieren → Plan `completed` → Claim freigeben → Worktree/Branch entfernen.

## Schritt 6.5: Abschluss

```bash
: "${PR_NUM:=$(gh pr view --json number -q '.number' 2>/dev/null || echo "")}"
```

Merge = Abschluss: Schritt 6.4 hat den Merge bestätigt; Prod-Deploy (Schritt 8) ist entkoppelt und ändert den Status nicht. `verify:done`-Zeile in `phase-events.log` (Pflicht, Merge-Gate), Plan-Frontmatter `status: completed`, committen.

Nur bei `repo.tickets: true`: zusätzlich PR-Link, Statuswechsel nach `done` (`shipped`/`fixed`), `verify:done`- und `deploy:done`-Events und Kommentar (MCP-first, Fallback `vda.sh` + `devflow-phase.sh`).

## Schritt 7: Plan archivieren

Manuelles Archiv nach plan-archive-steps vor dem Branch-Cleanup (mit Tickets: zusätzlich Ablage in Ticket-Plan-Tabelle).

## Schritt 7.5: Worktree und Branch bereinigen

Läuft nach Schritt 7 — der Fix-PR-Merge löscht den Branch bewusst nicht (`delete_branch_on_merge=false`), damit die Archivierung ihn vorfindet. Claims vor dem Worktree-Remove freigeben, dann im Haupt-Repo:

```bash
git worktree unlock "$MAIN_REPO/.worktrees/<slug>" 2>/dev/null || true
git worktree remove "$MAIN_REPO/.worktrees/<slug>" --force
git branch -D "<branch>"
git push origin --delete "<branch>"
```

---

## Tests — ein pytest-Modul pro Vorgang

Neue Tests sind pytest-Funktionen in `tests/py/spec/<bereich>/test_<kurz_slug>.py` (Bereich aus Feature-/Ticket-Titel). BATS ist deinstalliert.

1. Bereich ermitteln (Verhalten beschreiben).
2. Modul prüfen/anlegen: existiert passendes Modul unter `tests/py/spec/` → ergänzen, sonst neu (Vorlage und Konventionen: `tests/CLAUDE.md`).
3. Fallback: übergreifende Tests ohne Bereich → Modul in `tests/py/unit/` erweitern.

```bash
ls tests/py/spec/native_ported/spec/
bash scripts/pytest-run.sh tests/py/spec/<pfad>/test_<slug>.py
```

Live-Tests mit Clusterbedarf nach `tests/py/local/test_<id>.py` (nur mit `PYTEST_LOCAL=1` gesammelt, via `tests/runner.sh local <ID>`). Ticket-nummerierte Dateinamen nicht neu anlegen.
