---
name: git-workflow
description: Nutze diesen Skill bei Commit, Push, PR-Erstellung oder Branch-Abschluss auf beliebigem Branch. Deckt den kompletten Lifecycle ab: Pull-First, Commit-Konventionen, Scope-Preflight, Freshness-Guard, Commit-Verifikation, PR-Erstellung, CI-Fix-Loop, Squash-Merge und Worktree-Cleanup.
---

# Git Workflow — Commit → Push → PR → Merge → Cleanup

Sage zu Beginn: "Ich nutze git-workflow für den Commit/PR-Ablauf."

Dieser Skill ist die SSOT für Commit → Push → PR → Merge → Cleanup.
Repo-Spezifika stehen nicht hier, sondern in `repo.yaml` im Consumer-Repo-Root:
Vor Schritt 0 `repo.main_branch`, `repo.scopes`, `repo.tickets`,
`repo.generated_artifacts` und `repo.task_runner` aus `repo.yaml` lesen.
Fehlt ein Schlüssel, die Annahme explizit nennen.

## Schritt 0 — Pull-First

Vor jedem Commit `origin/<main_branch>` aktualisieren (bei dirty tree stashen
und zurückspielen):

```bash
git pull --rebase origin <main_branch>
```

Beispiel ausgerollt (`repo.main_branch: main`):

```bash
git pull --rebase origin main
```

Stash-Fallen (Pop-Verifikation, Disziplin, Branch-Switch-Race, Probe-Commit):
[stash-discipline](references/stash-discipline.md).

## Master-Diff in Branch übernehmen (git-crypt-Falle)

Liegengebliebene Branch-Basis-Änderungen per Patch-Datei in den Branch-Worktree
tragen — auf git-crypt-Dateien nicht per `git apply` (findet dort kein
Kontextfragment, obwohl die Datei entschlüsselt vorliegt):

```bash
git diff --binary -- <pfade...> > /tmp/change.patch
patch -p1 --dry-run < /tmp/change.patch   # erst prüfen …
patch -p1 < /tmp/change.patch             # … dann anwenden
git diff --stat   # Treffer verifizieren, keine .rej-Dateien übrig?
```

Betroffene Dateien erkennen: `git check-attr -a -- <pfad>` zeigt dann
`filter: git-crypt`.

## Schritt 1 — Verifikation (vor dem Commit)

Betroffene Suiten laufen lassen (Befehle aus `repo.task_runner`; bei
`task_runner: none` die repo-eigenen direkten Befehle, z. B. vitest/pytest).

Nur-wenn-`generated_artifacts`: Vor der Artefakt-Regeneration erneut auf
Divergenz zu `origin/<main_branch>` prüfen (seit Schritt 0 kann die Basis
weitergerückt sein) und erst danach regenerieren.

### Rebase-Preflight

Divergenz zählen (nötigenfalls Rebase vor dem Regen-Lauf):

```bash
git fetch origin <main_branch>
BEHIND=$(git rev-list --count HEAD..origin/<main_branch> 2>/dev/null || echo 0)
# Beispiel ausgerollt (repo.main_branch: main):
# BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
```

Erst danach regenerieren (`task freshness:regenerate` bzw. Repo-Äquivalent).

### Rebase-Freshness-Regel (T003105)

Nach JEDEM Rebase VOR dem Push den Freshness-Check erneut laufen lassen
(`task freshness:check`, bei `task_runner: none` das repo-eigene Äquivalent) —
ein konfliktfreier Rebase kann committete Artefakte durch `merge=ours` still
verlieren; ein grüner Rebase belegt die Artefakt-Vollständigkeit nicht. Rot?
`task freshness:regenerate` (bzw. Repo-Äquivalent) und Regen-Commit anhängen.

## Schritt 2 — Commit

### Conventional Commits — Pflichtformat

```
<type>(<scope>): <subject>
```

Header ≤ 100 Zeichen (besteht auch strengere Repo-Lints). Typen: `feat fix
chore docs refactor test build ci perf revert style`.

Nur-wenn-`scopes` eine Allowlist ist: Scope vor dem ersten Commit gegen die
SSOT-Liste prüfen (repo-eigener Preflight/Validator) und noch nicht
registrierte Scopes mitcommitten (Registrierungs-Skript + Lint-Config im
selben Commit). Bei `scopes: free` sind Scopes frei wählbar.

### Commit ausführen

```bash
BASE_SHA="$(git rev-parse HEAD)"

git add <spezifische Dateien>   # explizite Pathspecs — NIEMALS git add -A
                                # (würde git-crypt-Artefakte und Secrets stagen)

# Secret-Guard: Secret-verdächtige oder git-crypt-geschützte Pfade dürfen
# nicht plaintext bzw. als Smudge-Artefakt im Index landen — bei Treffer
# abbrechen und git-crypt-Abdeckung prüfen
git commit -m "<type>(<scope>): <subject>"

# Commit-Verifikation — schlägt der Hook fehl, landet nichts
HEAD_SHA="$(git rev-parse HEAD)"
if [ "$HEAD_SHA" = "$BASE_SHA" ]; then
  echo "FATAL: Commit ist nicht gelandet (Hook hat abgelehnt?). Push abgebrochen." >&2
  exit 1
fi
```

Repo-eigene Commit-Hooks (Secret-Scan, Format-/Konsistenzprüfung) laufen bei
jedem Commit; nur im Notfall mit `SKIP_*=1` bypassen.

## Schritt 3 — Push

```bash
git push -u origin "$(git rev-parse --abbrev-ref HEAD)"
# Bei rejected (non-fast-forward im selben Feature-Branch):
# git push --force-with-lease   — NUR für eigene Feature-Branches, NIEMALS für <main_branch>
```

Push-Schutz des Repos (Wrapper/Hooks für inhalts-äquivalente Divergenz)
beachten. Direkte Pushes auf `<main_branch>` nur für Trivialitäten, sonst PR.

## Schritt 4 — PR-Erstellung

```bash
gh pr create --title "<type>(<scope>): <subject>" --body "..."
```

Body: Summary + Test Plan (welche Suiten liefen, mit Ergebnis). Nur-wenn-
`tickets` gesetzt: Ticket-/Issue-Referenz nach Repo-Konvention; sonst Issues
und PRs nur referenzieren, wenn sie existieren. Nur-wenn-`scopes` eine
Allowlist ist: Scope-Preflight vor `gh pr create` laufen lassen.

## Schritt 5 — CI Fix Loop

Nach dem Push CI- und Merge-Status überwachen: `bash scripts/pr-health-check.sh <n>`
(repo-eigenes Äquivalent, falls vorhanden) prüft CI-Rollup UND Git-Mergeability
(`DIRTY`/`CONFLICTING`/`BEHIND`); danach `gh pr checks <n> --watch` — warten bis
grün. Bei Fehlern: Log lesen, lokal fixen, committen, pushen, wiederholen.
Merge-Konflikte sofort per Rebase auflösen, nicht aussitzen:

```bash
git fetch origin <main_branch> && git rebase origin/<main_branch>
# Konflikte auflösen, Tests erneut laufen lassen, push --force-with-lease
# Nur-wenn-generated_artifacts: Freshness-Check/Regenerate vor dem Push
```

## Schritt 6 — Merge

```bash
MAIN_REPO=$(git worktree list --porcelain | awk '/^worktree/{print $2; exit}')
(cd "$MAIN_REPO" && gh pr merge --squash --auto <n>)
```

Immer `--squash` (saubere `<main_branch>`-History). `--auto` kehrt sofort
zurück; der Merge läuft asynchron nach grünen Checks. `--delete-branch` nur,
wenn kein Post-Merge-Archiv den Branch noch braucht — sonst erst im Cleanup
nach der Archivierung löschen. Verweigert GitHub `--auto`, Checks abwarten und
danach ohne `--auto` mergen.

## Schritt 7 — Cleanup (Worktrees)

Nur wenn in einem Worktree gearbeitet wurde: zurück in den Hauptcheckout,
Worktree entfernen, lokalen Branch löschen, Remote-Branch prüfen:

```bash
(cd "$MAIN_REPO" && git pull --ff-only origin <main_branch>)
git worktree remove --force <worktree-pfad>
git branch -D <branch>
git ls-remote --heads origin <branch>  # leer? sonst: git push origin --delete <branch>
```

Neue Worktrees immer über das repo-eigene git-crypt-sichere Verfahren
anlegen — nie direkt in einem fremden Worktree oder auf `<main_branch>`
arbeiten. Details: [worktree-cleanup](references/worktree-cleanup.md).

## Verwandte Skills

- `superpowers:using-git-worktrees` — Worktree korrekt anlegen
- `superpowers:finishing-a-development-branch` — Optionen nach Implementierung
- `dev-flow-chore`, `dev-flow-execute` — nutzen diesen Skill intern
