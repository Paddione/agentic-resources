# dev-flow-Lifecycle-Vertrag

Transition-SSOT für die vier Flow-Skills. Ausführbare Details bleiben in `git-workflow`, `verification-block`, `ci-fix-loop` und den Phasen-Referenzen.

Repo-Konfiguration: `repo.yaml` (`repo.main_branch`, `repo.tickets`, `repo.generated_artifacts`, `repo.task_runner`). Pläne leben als Dateien auf ihrem Branch; Dispatch läuft über Worker-Sandboxes; Abschluss heißt Merge + `completed`-Markierung. Ticket-Zeilen gelten nur bei `repo.tickets: true`.

| Skill | Auslöser | Eintritt | Owner | Mutation | Austritt | Nächster Handoff |
|---|---|---|---|---|---|---|
| dev-flow-plan | Verhaltensänderung | Anfrage, kein gestagter Plan | Planner | Proposal/Spec/Plan auf Feature- oder Fix-Worktree | Plan committet und gepusht (mit Tickets: staged), kein PR | dev-flow-execute |
| dev-flow-chore | keine Verhaltensänderung | Anfrage, kein Plan nötig | Chore-Implementer | Maintenance-Dateien auf Chore-Worktree (mit Tickets: ticketiert) | PR gemergt, Cleanup fertig | ggf. Deploy |
| dev-flow-execute | gestagter Feature-/Fix-Plan | Plan committet und gepusht | Implementer, Orchestrator, Finalizer | geplante Produkt- und Testdateien | PR gemergt, Plan completed, Cleanup fertig (mit Tickets: Ticket done) | Deploy, dann dev-flow-e2e |
| dev-flow-e2e | Post-Deploy-Abdeckung | gemergte und deployte Änderung | E2E-Chore-Implementer | nur Playwright-Specs und generiertes Inventar | Chore-PR gemergt, Cleanup fertig (mit Tickets: ticketiert) | Main-Branch (`repo.main_branch`) |

## Gemeinsame Invarianten

Jede Mutation hat einen isolierten Worktree, eine propagierte Session-SID und einen expliziten Branch-/PR-Owner. Mit Tickets: Ticket vor ticketiertem Branch. Nie direkt auf den Main-Branch (`repo.main_branch`) pushen. Pull-first, explizites Stagen (inkl. git-crypt-Guard), PR, Merge und Cleanup nach `git-workflow`; Tests und Freshness nach `verification-block`. Abschluss erst nach bestätigtem `MERGED`; der Finalizer archiviert manuell (mit Tickets: idempotenter Post-Merge-Finalizer) und gibt Claims erst nach Archiv/Cleanup-Reihenfolge frei.

## Execute-Swimlane und Exception-Loop

Der Implementer wendet den Plan an, verifiziert RED→GREEN, committet, pusht, erstellt den PR, berichtet und stoppt. Der Orchestrator reviewt nur auf Wunsch, prüft aber immer fail-closed das lokale Phase-Chain-Gate vor `gh pr merge --auto --squash`; bereits aktives Auto-Merge bleibt an. Danach hält er den CI-/Konflikt-Exception-Loop bis `MERGED`; spätere rote Checks, Ersatzläufe nach Korrektur-Push oder `DIRTY`/`CONFLICTING` nach Main-Branch-Vorsprung gehen an denselben Implementer. Jeder neue Commit tritt erneut in Phase-Chain-Gate und invalidierte CI-Gates ein (plus Review nur auf Wunsch).

Nach dem Merge-Request wartet ein frischer Finalizer per `ci-fix-loop` und behauptet bei Timeout, offenem/geschlossenem PR, spätem CI-Fehler oder Konflikt keinen Abschluss (mit Tickets: kein Ticket schließen). Erst nach `MERGED` läuft das manuelle Archiv; die Operation ist idempotent.

## E2E-Spezialisierung

Post-Deploy-E2E ist ein test-only Chore: `dev-flow-e2e` besitzt Live-Target-Discovery, Credentials, Playwright-Projekte, Tags und optionale Headed-/Vision-Verifikation. Repo-Mutationen laufen über `chore/*`-Branch (mit Tickets: ticketiert), PR, Merge und Cleanup nach diesem Vertrag.
