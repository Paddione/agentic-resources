# dev-flow Gotchas

Sammlung bekannter Probleme und Workarounds der dev-flow-Pipeline. Der [Lifecycle-Vertrag](dev-flow-lifecycle.md) besitzt Transitionen und Rollen; ausführbare Git-, Verifikations- und Merge-Mechanik bleibt in den referenzierten SSOTs.

Repo-Konfiguration: `repo.yaml` (`repo.main_branch`, `repo.scopes`, `repo.tickets`, `repo.generated_artifacts`, `repo.task_runner`). Main-Branch, Scope-Allowlist, Ticket-Regeln, generierte Artefakte und Task-Runner-Namen unten kommen aus diesen Keys. Ticket-Einträge gelten nur bei `repo.tickets: true` — sonst sind sie retiriert.

### [T000321] Main Branch Guard
Nie direkt auf den Main-Branch (`repo.main_branch`) committen oder pushen. Immer Feature-, Fix- oder Chore-Worktree/Branch anlegen. `dev-flow-plan` und `dev-flow-execute` verifizieren vor Commit/Push, dass der aktive Branch nicht der Main-Branch ist.

### [T000343] Brainstorm Port Selection
Visual-Companion-Port immer dynamisch aus dem Rückgabewert von `start-server.sh` ableiten. Fest codierte oder geratene Ports aus früheren Sessions geben 502 Bad Gateway.

### [T000298] Git Auto-Merge in Worktrees
`gh pr merge --auto` in `.worktrees/*` kann still scheitern, weil Git den Main-Branch durch den Haupt-Worktree als belegt sieht. Merge entweder mit explizitem `--repo` aus dem Haupt-Repo-Verzeichnis oder Checks sequenziell pollen (ohne `--auto`) und dann mergen.

### [T000346] K8s Object verification before Planning
Vor einem Deployment-Patch Objektnamen per `kubectl kustomize` oder `kubectl get` verifizieren, keine Namen annehmen.

### [T000244] JSON Patch duplicate keys in Env variables
Existiert die Variable im Basis-Deployment, `op: replace` statt `op: add` verwenden — sonst Duplikat-Fehler bei der API-Validierung im Dry-Run.

### [T000218] task test:all exit 128
Intermittierender Exit 128 beim ersten Lauf im frischen Worktree (Race zwischen `npm install` und Submodul-Checks; Task-Runner-Name aus `repo.task_runner`). Zweiter Lauf gelingt.

### [T000245] fresh worktree node_modules missing
Node-Module sind nicht eingecheckt; im frischen Worktree erst installieren, dann testen/kompilieren.

### [T000214] openclaw approvals get JSON parsing
`openclaw approvals get` liefert tab-separierten Text, kein JSON. Stdout nicht an JSON-Parser pipen; ggf. `.openclaw/exec-approvals.json` direkt lesen.

### [T000335] Commitlint body-max-line-length
Body-Zeilen unter 100 Zeichen umbrechen; Raw-Output/Logs kürzen oder manuell umbrechen.

### [T000342] gh pr checks parsing
Kein `gh pr view --json state` für Build-Ergebnisse; textbasiert aus der Checks-Liste parsen. `gh pr checks` unterstützt kein `--json` (installierte CLI 2.45.0) — stilles Failen darf nie als Pass gewertet werden; neue CI-Watch-Tools prüfen echte Conclusions via `gh pr view --json statusCheckRollup` und fallen laut statt default-pass um.

### [T001395] Freshness-Auto-Regen race → PR flips to CONFLICTING mid-flow
Auto-Regen generierter Artefakte (`repo.generated_artifacts`) committet selbständig auf den Main-Branch. Bleibt ein PR über einen Zyklus offen, meldet GitHub `CONFLICTING` ohne menschliche Änderung. Regel: PRs kurzlebig halten. Bei rein generiertem Diff sofort `git fetch origin <MAIN> && git rebase origin/<MAIN> && <task_runner> freshness:regenerate && git add <regenerierte Dateien> && git rebase --continue && git push --force-with-lease`. Ein bare Rebase ohne Regenerate reicht nicht.

### [T001395] Check the commit-scope SSOT allowlist BEFORE the first commit
Scope-Allowlist aus `repo.scopes` (SSOT: `namedScopes` in `commitlint.config.cjs`, gedruckt via `scripts/validate-commit-msg.sh scopes`, enforced pre-push). Vor dem ersten `git commit -m "<type>(<scope>): ..."` eines Plans/Chores Allowlist lesen und Scope wählen (oder vorher via `register-scope.sh` registrieren). Post-Commit-Preflight bleibt harter Backstop; Pre-Commit-Check spart Soft-Reset/Recommit.

### [T001914] Health-goal commits use scope `goals`, not `health`
Commits an Goals-Dateien, Baselines/Measurements oder `G-<ID>`-Gates gehören zu Scope `goals` (oder zur konkreten Goal-ID als Scope, z. B. `fix(G-SIZE02): ...`). Keinen generischen `health`-Scope einführen.

### [T000344] [RETIRIERT] Database row check before file deletion
Gilt nur bei `repo.tickets: true` (Plan-Zeile in Ticket-Plan-Tabelle prüfen, dann erst `rm`). Sonst: Plan-Commit im Git-Tree verifizieren (`git cat-file -e HEAD:<planfile>`), dann erst `rm`.

### [T000388] [RETIRIERT] tickets.ticket_plans Query Timeout
Gilt nur bei `repo.tickets: true`: nie `SELECT *`/Content-Spalte über die ganze Plan-Tabelle (Timeouts über den DB-Tunnel); nur Metadaten-Spalten oder gefiltert nach Ticket-ID/Slug. Sonst gegenstandslos (Tabelle gedroppt).

### [T000418] Playwright Project Assignment
Projektname in `playwright.config.ts` nach Service/Marke wählen:

| Projektname | Zweck / Ziel |
|-------------|--------------|
| `mentolder` | E2E-Tests für die Marke Mentolder |
| `korczewski` | E2E-Tests für die Marke Korczewski |
| `website` | Allgemeine Website E2E-Tests |
| `services` | Testen von Hintergrund-Diensten |
| `smoke` | Smoke-Tests für den Live-Cluster |
| `systemtest` | System-Integrationstests |

### [T001393] Lavish reload can discard in-flight form input
`npx -y lavish-axi <html-file>` lädt den Tab neu. Reload-Safety-Protokoll im lavish-Skill beachten — nie bei ausstehendem Poll reloaden, vorher letzten Poll-Status prüfen.

### [T002637-M5] Massenverschiebung: Referenzliste zuerst erheben, nicht aus CI ernten
Bei Massenverschiebung vor dem ersten Commit alle Referenzen auf alte Pfade per `git grep` über den ganzen Baum (inkl. tests/) erheben, nicht CI-Runde für CI-Runde abarbeiten.

### [T002673] [RETIRIERT] stage-plan läuft NACH dem Commit, nicht davor
Gilt nur bei `repo.tickets: true`: erst committen/pushen, dann stagen — der Stage liest den Plan aus dem Branch-Commit, sonst bleibt `touched_files` leer. Ohne Tickets entfällt der Eintrag (Ableitung per `plan-touched-files.sh` gegen die reale Datei, Commit zuerst).

### [T002820] Externe Abhängigkeiten schon in der Rotphase absichern
Verfügbarkeits-Guard in die Rotphase: `command -v <binary> >/dev/null 2>&1 || skip "<binary> binary not installed"`. Vorher prüfen, ob CI die Abhängigkeit einrichtet (`grep -rn '<binary>' .github/workflows/`; 0 Treffer = in CI nicht vorhanden). Beide Richtungen verifizieren (mit Binary läuft, mit Minimal-PATH skippt sauber).

### [T002816] Kein fertig aussehender PR aus dem Plan-Stand
Plan-Stand ist ein gepushter Branch ohne PR. Früh-PR nur als Draft mit `[plan-only]`-Präfix. Regulären PR eröffnet `dev-flow-execute` nach der Implementierung.

### [T002817] Prior-Art-Suche geht über die Requirements, nicht nur über den Code
Vor der ersten Architekturfrage Requirements zum selben Gegenstand suchen, Fundstellen zitieren (Datei + Zeilen) und fragen, ob die bestehende Entscheidung bleibt oder ersetzt wird. Ersetzen via `RENAMED`/`MODIFIED`-Delta auf den SSOT-Spec, nicht danebenschreiben.

### [T001434] Plan-Stage-Commits heißen `chore(plans):`, nie `fix(`/`feat(`
Stage-Commit enthält nur RED-Test und Plan-Artefakte, keinen Production-Code. Immer `chore(plans):` (Scopes aus `repo.scopes`). Guard: `scripts/check-commit-vs-diff.sh` + `.githooks/commit-msg`; Notfall-Bypass `SKIP_COMMIT_VS_DIFF=1`.

### [T001974] Detached-HEAD-Falle bei `git worktree add <remote-ref>`
`git worktree add <pfad> <remote-ref>` erzeugt detached HEAD — Commits landen unerreichbar, `git push` meldet fälschlich "up-to-date". Nach dem Create sofort Branch checken oder Projekt-Helper `scripts/worktree-create.sh <branch> <pfad>` verwenden (in dev-flow immer).

### [T000426] Bare `git worktree add` stirbt mit exit 128 (git-crypt)
Bare `git worktree add` scheitert am git-crypt-Smudge-Filter (exit 128). Immer `scripts/worktree-create.sh <branch> <pfad>` verwenden (behandelt Key-Copy und node_modules-Symlink).
