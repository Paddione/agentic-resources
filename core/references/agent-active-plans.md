# Active-plans-Injektion für Domain-Agenten

> Skript-Verweise gelten nur-wenn das Repo sie führt (Bachelorprojekt-Profil); sonst das Repo-Äquivalent aus `repo.yaml` bzw. `AGENTS.md` des Repos. Lifecycle-Mechanik immer über `python3 ~/scripts/agent-workspace.py`.

Geteilter Kontrakt für alle `.claude/agents/bp-*.md` (`bp-build`, `bp-run`, `bp-ship`). Die Agent-Dateien
verweisen hierher, statt diesen Text zu wiederholen.

## Wer injiziert

Der Orchestrator (siehe `CLAUDE.md` → „Agent Routing") baut vor dem Dispatch einen
`<active-plans>`-Block aus `scripts/plan-context.sh <rolle>` und stellt
ihn dem Agent-Prompt voran. Quelle sind die aktiven Proposals unter
`.agents/plans/*/proposal.md`.

**Der injizierte Block ist maßgeblich** — er ist der Arbeitskontext für das laufende Feature.

## Rollenname: immer die Langform

`plan-context.sh` erwartet einen der Namen aus `_role_allowlist()` im Skript selbst:
`bp-build`, `bp-run`, `bp-ship`, `orchestrator` (plus `openclaw-ops`). Die älteren Namen
`bachelorprojekt-{website,ops,infra,test,db,security}` bleiben dort nur noch als Legacy-Aliase
für historische Proposals erhalten.

Eine Kurzform (`build`, `infra`, …) schlägt **nicht** fehl. Sie fällt still auf `__ALL__`
zurück, schreibt nur ein `WARN: unknown role` nach stderr und liefert **alle** Proposals
ungefiltert — der Rollenfilter wirkt dann gar nicht (T002322). Das ist die eigentliche
Falle: der Aufruf sieht erfolgreich aus und der Agent bekommt fremden Kontext.

```bash
bash scripts/plan-context.sh bp-build   # richtig
bash scripts/plan-context.sh build      # still ungefiltert
```

Die Allowlist wird hier bewusst nicht dupliziert — maßgeblich ist die Funktion im Skript.

Der Schwesterbefehl `scripts/toolset-context.sh <rolle>` ist im Gegensatz dazu
**fail-closed**: eine unbekannte Rolle beendet ihn mit Exit ≠ 0 und gibt nichts aus.

## Kein Block injiziert

Dann ist für diese Rolle kein Plan in Arbeit. **Nicht** ersatzweise `superpowers.plans`
abfragen: die Tabelle ist eingefrorene Historie. Die Tracking-Pipeline wurde in PR #788
(`tracking-import` CronJob) und PR #993 (`track-pr.yml`) entfernt;
der letzte erfasste Eintrag ist PR #787.
