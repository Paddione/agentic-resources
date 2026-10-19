# Plan-Archiv nach Merge

Branch aus `repo.main_branch` auflösen (`MAIN=$(yq .repo.main_branch repo.yaml)`).

Mit Finalizer (nur wenn `scripts/devflow-post-merge-finalize.sh` ohne Ticket-Backend läuft):

```bash
bash scripts/devflow-post-merge-finalize.sh --pr "$PR_NUM"
```

Der Finalizer liest den Planpfad aus `FACTORY-PLAN-REF`, markiert Frontmatter `status: completed` und ist idempotent (nach Abbruch mit gemergter PR-Nummer erneut aufrufen).

Manuell (ohne ticket-freien Finalizer — ein Skript mit toter Ticket-Abhängigkeit NICHT aufrufen):

```bash
# 1. Merge verifizieren (Timestamp, nie Exit-Code):
m=$(gh pr view <num> --json mergedAt -q '.mergedAt')
[ -n "$m" ] && [ "$m" != "null" ] || { echo "FAIL: kein Merge"; exit 1; }

# 2. Plan als completed markieren (Frontmatter in tasks.md), committen.

# 3. Eigenen Branch-Claim freigeben, DANN Worktree + lokalen/Remote-Branch entfernen.
cd "$MAIN_REPO"
bash scripts/agent-lock.sh release branch "$BRANCH"
git worktree remove "$WORKTREE"
git branch -D "$BRANCH" && git push origin ":$BRANCH"
```

Reihenfolge: Archivierung VOR Branch-Löschung, Release aus `$MAIN_REPO`. Jede Session kann offene Schritte nachholen (idempotent: Erledigtes überspringen).

The staged plan remains a regular repository file until a later cleanup change removes it.
