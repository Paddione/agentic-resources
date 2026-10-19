# Stash-Discipline (git-workflow Schritt 0 — Detail)

Pull-first vor jedem Commit / jeder Branch-Aktion: `origin/<main_branch>`
(`repo.main_branch` aus `repo.yaml`) muss aktuell sein.

```bash
git fetch origin <main_branch>
if git diff --quiet HEAD; then
  git pull --rebase origin <main_branch>
else
  git stash push -m "wip ${BRANCH}"
  git pull --rebase origin <main_branch>
  git stash pop  # per Nachricht auflösen, nie per Index (siehe Disziplin)
fi
```

> **Stash-Pop positive Verifikation.** Nach dem Pop MUSS der eigene Eintrag
> aus `git stash list` verschwunden sein. Ein verbliebener Eintrag ist ein
> **Befund, kein Erfolg**: Der post-rewrite-Hook hat ein gestashtes Artefakt
> schon neu erzeugt, der Pop wendet nur teilweise an. Wiederherstellung:
> `git stash show --stat "stash@{0}"` gegen den Arbeitsbaum halten, fehlende
> Datei mit `git checkout "stash@{0}" -- <pfad>` zurückholen, den Eintrag als
> Sicherungsnetz liegen lassen.

> **Stash-Disziplin.** Der Stash-Stack ist über ALLE Worktrees geteilt,
> `stash@{0}` verschiebt sich durch fremde pushes. Bei Parallelarbeit einen
> **Wegwerf-Commit auf dem eigenen Branch** verwenden (`git commit -m wip`,
> später `git reset --soft HEAD~1`). Wo ein Stash nötig bleibt: IMMER mit `-m`
> und Branch-Namen anlegen und über die Nachricht auflösen, NIE über den Index
> `stash@{0}`.

> **Branch-Switch + Stash Race.** `git checkout -b <branch> && git stash pop`
> nie in einer Pipeline verketten, sonst landet der Commit auf dem falschen
> Branch. Jeden Schritt einzeln absichern:
>
> ```bash
> git checkout -b fix/my-branch || exit 1   # Branch-Switch abwarten
> git stash pop || { echo "stash pop failed"; exit 1; }
> ```

> **Probe-Commit + `--hard` verwirft auch unstaged Dateien.**
> `git reset -q --hard HEAD~1` nach einem Probe-Commit reißt unstaged
> Arbeitsdateien mit. Sicher:
> ```bash
> git stash -u && git reset --hard HEAD~1 && git stash pop
> ```
> Oder den Probe in einem separaten Wegwerf-Worktree testen.
