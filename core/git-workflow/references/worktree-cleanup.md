# Worktree-Cleanup (git-workflow Schritt 7 — Detail)

Nur wenn in einem Worktree gearbeitet wurde:

```bash
WORKTREE_PATH="$(git rev-parse --show-toplevel)"
BRANCH_NAME="$(git rev-parse --abbrev-ref HEAD)"
MAIN_REPO=$(git worktree list --porcelain | awk '/^worktree/{print $2; exit}')

cd "$MAIN_REPO"
# Repo-eigene Branch-Sperre (falls vorhanden) erst im Haupt-Repo freigeben —
# aus dem Worktree heraus verweigern viele Wrapper den Release.
git worktree unlock "$WORKTREE_PATH" 2>/dev/null || true   # falls Worktrees gesperrt angelegt werden — sonst Exit 128 beim Remove
git worktree remove "$WORKTREE_PATH"
git worktree prune

# Der Merge löscht den Remote-Branch nicht automatisch — erst hier, NACH
# einem nötigen Post-Merge-Archiv, löschen.
git push origin --delete "$BRANCH_NAME"
# Squash-Commit ist ein neuer Commit, `git branch -d` würde fehlschlagen; `-D` ist nötig.
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME" 2>/dev/null; then
  git branch -D "$BRANCH_NAME"
fi
```

## Worktree-Erstellung — nur das git-crypt-sichere Verfahren

Worktrees immer über das repo-eigene Verfahren anlegen, das den git-crypt-Key
mitkopiert und smudge/clean-Filter neutralisiert. Ein plaines `git worktree
add` scheitert auf verschlüsselten Pfaden (exit 128) oder hinterlässt sie
unbrauchbar — nur für Branches sicher, die keine git-crypt-Pfade berühren.
Nie direkt in einem fremden Worktree oder auf `<main_branch>`
(`repo.main_branch` aus `repo.yaml`) arbeiten.
