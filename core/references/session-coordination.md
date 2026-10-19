# Session-Koordination — agent-lock-Lebenszyklus (SSOT)

Der komplette Claim/Release-Lebenszyklus für parallele Sessions. Skills verlinken hierher und zeigen nur skill-spezifische Parameter (`--label`, Scope). Worktree-*Erzeugung* ist SSOT in `scripts/worktree-create.sh`. Branch-Namen für Vergleiche aus `repo.main_branch` auflösen (`MAIN=$(yq .repo.main_branch repo.yaml)`).

Claims sind **branch-scoped**. Ticket-Claims nur bedingt, siehe unten.

## Sitzungsstart — Reaper & Nachrichten

```bash
bash scripts/agent-lock.sh reap           # Zombie-Prozesse, stale Worktrees & tote Locks räumen
bash scripts/agent-lock.sh list           # "Wer macht was": laufende Claims anderer Sessions
bash scripts/agent-msg.sh read --unread   # offene Nachrichten paralleler Sessions sichten
```

**Sichtbarkeitslücke:** `agent-lock.sh list` zeigt eine Session erst ab ihrem ersten Commit — der `main-checkout`-Claim entsteht im Pre-Commit-Hook, nicht beim Worktree-Anlegen. Leere `list`-Ausgabe beweist **nicht**, dass niemand arbeitet. Dafür `agent-lock.sh activity` verwenden (listet zusätzlich laufende Prozesse mit `cwd` in einem Worktree-Pfad).

## Claimen (vor der Arbeit)

```bash
# Branch-Claim (immer):
bash scripts/agent-lock.sh claim branch "<branch>" --worktree "<wt-pfad>" --label <skill-name> \
  || { echo "Branch wird bereits von einer lebenden Session bearbeitet — koordinieren, nicht duplizieren."; exit 1; }
```

- **Exit 1** = lebende Session hält den Claim (Halter-Info in Ausgabe) → koordinieren.
- **Re-Claim durch dieselbe Session** ist no-op-Refresh, kein Fehler.
- Lock-Dateien unter `.git/agent-locks/` (`branch__<name>.json`) — Guards lesen `branch`/`worktree` daraus (`jq -r '.branch' <lockfile>`).
- Bei Inline-Arbeit im main-Checkout: zusätzlich `claim main-checkout`, sonst sperrt `.githooks/pre-commit` konkurrierende Commits.

**Nur mit Ticket-Backend (`repo.tickets` gesetzt):** zusätzlich Ticket-Claim, sobald die ID bekannt ist:

```bash
bash scripts/agent-lock.sh claim ticket "<T00XXXX>" --branch "<branch>" --worktree "<wt-pfad>" --label <skill-name> \
  || { echo "Ticket wird bereits bearbeitet — koordinieren."; exit 1; }
```

## Registry-Overlap (geteilte Hochfrequenz-Dateien)

Vor Änderungen an geteilten Registry-Dateien (Liste aus `repo.scopes` bzw. Repo-Konvention, z. B. `fleet/configmap-domains.yaml environments/schema.yaml Taskfile.yml fleet/kustomization.yaml`) weiche Warnung + Claim:

```bash
for hf in <registry-dateien>; do
  git diff --name-only "origin/$MAIN" | grep -qx "$hf" || continue
  [ "$(bash scripts/agent-lock.sh check registry "$hf" | head -1)" = "held" ] \
    && echo "$hf wird parallel bearbeitet → Keep-both-Rebase erwarten."
  bash scripts/agent-lock.sh claim registry "$hf" --branch "$BRANCH" --label <skill-name> || true
done
```

## Guard Hooks (pre-commit & post-checkout)

`.githooks/pre-commit` ruft zwei agent-lock-Guards auf:

1. **`guard-precommit`** — blockiert Commits im main-Checkout, während eine ANDERE Session dort exklusiv arbeitet (erkannt am `main-checkout`-Lock mit fremdem Label). Fail-open: ohne Lock kein Block.
2. **`guard-postcheckout`** — prüft nach `git checkout`, ob der main-Checkout-Lock von einer ANDEREN lebenden Session gehalten wird; falls ja und kein Rebase/Merge/Cherry-Pick läuft, Reset auf den Lock-Branch.

Beide via `git config core.hooksPath .githooks` aktiviert.

## Agent-Msg: tail & peers

```bash
bash scripts/agent-msg.sh tail -n 10              # letzte 10 Nachrichten (auch gelesene)
bash scripts/agent-msg.sh read --mine --unread    # nur an DICH adressiert (SID/Label)
bash scripts/agent-msg.sh read --since 1748822400 # nur ab Zeitstempel
bash scripts/agent-msg.sh peers                   # Live-Sessions (delegiert an lock list)
```

Nachrichten > 4096 Bytes werden gekürzt (Metrik im JSON erhalten).

## Agent-Collision (live edit collision)

`scripts/agent-collision.sh` warnt vor Dateien, die eine ANDERE lebende Session im Worktree ändert. Pre-Commit-Hook ruft `check --staged` auf; mit `AGENT_COLLISION_STRICT=1` wird bei Kollision abgelehnt.

| Modus | Prüft | Wann nutzen |
|-------|-------|-------------|
| `--staged` (default) | Nur `git add`-Dateien | Pre-Commit-Hook |
| `--all` | Staged + unstaged | Vor `git commit -a` |
| `--branch` | Alles seit Abzweigung (`<main>...HEAD`) | Präventiv, auch bei sauberem WT |

```bash
bash scripts/agent-collision.sh check --staged
bash scripts/agent-collision.sh check --all
bash scripts/agent-collision.sh check --branch
bash scripts/agent-collision.sh check --quiet   # still, nur Exit-Code
```

`--branch` erstellt/wechselt nie einen Branch — der Name kommt vom Drei-Punkt-Diff. Empfohlen: vor Plan-Schreiben und PR-Erstellung `--branch`, im Hook `--staged`. Lokale Bash, kein Cluster.

## Reap-Lifecycle

`agent-lock.sh reap` räumt stale Locks/Zombie-Prozesse. Reapable (eindeutig tot) bei:

1. **PID tot** + Alter > Grace (`AGENT_LOCK_GRACE`, default 120s).
2. **Worktree-Pfad gelöscht**.
3. **SID tot** (numerisch, per `pgrep -s`) + Alter > Grace.
4. **Heartbeat-TTL abgelaufen** (`AGENT_LOCK_TTL`, default 1800s) — für non-numeric SIDs.

Läuft in Step −1 der Execute-Pipeline und beim Sitzungsstart; Gelöschtes landet in `.reap.log`. Nach jedem Reap-Fenster eigene Claims verifizieren (`list`) — parallele Sessions können genutzte Claims löschen.

## Pre-Flight Claim-Pattern

Branch-Claim **vor** jeder Git-Operation in dediziertem Pre-Flight-Schritt (−1):

1. **Prüfen** — `agent-lock.sh check branch $BRANCH` → bei fremdem Halter koordinieren.
2. **Atomisch claimen** — `agent-lock.sh check-and-claim branch $BRANCH` (Check + Claim unter flock). Optional `--status-check <pfad>`: Exit non-zero verweigert den Claim (exit 2).
3. **Broadcasten** — `agent-msg.sh post "… startet Arbeit an Branch $BRANCH" --to all`.

Exit-Codes: 0=claimed, 1=held by other, 2=status-check refused. **Nur mit Ticket-Backend:** zusätzlich Ticket-Status prüfen (abbrechen bei done/archived/merged) und Ticket-Claim vorziehen.

## Freigeben (nach Merge, VOR dem Worktree-Remove)

Zuerst ins Haupt-Repo wechseln, DANN freigeben: aus dem Worktree verweigert `release branch` den Release (cwd würde zerstört). Ohne stderr-Unterdrückung.

```bash
cd "$MAIN_REPO"
bash scripts/agent-lock.sh release branch "<branch>"
# Nur mit Ticket-Backend: bash scripts/agent-lock.sh release ticket "<T00XXXX>"
```
