# P1 — Ausführbare Partial

## Auftrag

F1: --harness wird beim ersten Argument-Parse konsumiert, danach bleibt HARNESS=0. Repariere nur die Flag-Verarbeitung. Ohne --harness ausschließlich Consumer-Verteilung, mit --harness zusätzlich Home-Harnesses. Bestehende Dateien und Symlinks erhalten. Keine Änderungen an Layer-Auflösung oder anderen bekannten Problemen.

## Dateien und Grenzen

FILES: runtimes/init.sh, tests/test_init_harness.py

Lies vor Änderungen die genannten bestehenden Quellen und den vorhandenen Teststil. Runtime: Python 3 / Bash. Repo-Hauptbranch ist main, task_runner=none, generated_artifacts=false. Kein Taskfile-Befehl und keine Freshness-Regeneration erforderlich. Keine vorhandene S1-Baseline/Gates im Zielrepo behaupten. Änderungen klein halten; bestehende Tools erweitern statt neue Infrastruktur bauen.

Nur diese Zielpfade schreiben. Niemals .git, Hook-Konfiguration, Secret-/git-crypt-Inhalte, lokale Konfigurationen, fremde Claims oder andere Worktrees lesen/ändern. Keine Commits, Pushes, PRs, Cloud-Modelle, Pakete installieren, Dienste starten oder GPU-Jobs konfigurieren. Bestehende Hook-Kette erhalten. Benutze keine git clean/reset --hard/add -A.

## Schritte

1. Relevante Quellen und den gestagten Test lesen. RED-Test ausführen: expected: FAIL (Reproduktion ist bereits gestagt). Danach minimale Korrektur und aussagekräftige weitere Fälle ergänzen.
2. Implementierung bzw. Report ausschließlich in FILES schreiben. Bei unklarer extern abhängiger Entscheidung nicht raten: im Report unverified markieren.
3. Exakt ausführen: `python3 -m pytest tests/test_init_harness.py -q`. Erwartung nach Umsetzung: Exit 0, keine zusätzlichen Skips als Ersatz für Assertions. Bei Testfehler Ursachen anhand realer Ausgabe prüfen, Tests nicht abschwächen.
4. Nur `git diff --stat -- <FILES>` ausführen. --check ist im bestehenden Worker-Tool nicht freigegeben und wird durch den Haupt-Orchestrator nachgeprüft. Git-Diffs immer explizit auf FILES begrenzen; Secret-Dateien sind in der Sandbox absichtlich ausgeblendet.
5. Mit Erfolg/Fehler, tatsächlich geprüften Befehlen, Ergebnis, geänderten Dateien und offenen Host-/CI-Nachprüfungen abschließen.

## Grenzen der Ausführung

Worker-Timeout 15 Minuten, höchstens zwei inhaltliche Wiederholungen durch den vorhandenen Runner. Evidence: .agents/plans/flow-p1-skill-distribution/.plan-runner/state.json plus Orchestrator-Log. Kein Netzwerk-/Live-Smoke aus Tests nachladen. Sandbox hält Git-Daten read-only; Commit/Push/Merge verbleiben beim Haupt-Orchestrator. Für Host-/Windows-/Remote-Checks ohne Zugriff ehrlich offen melden.

## Tatsächliche Worker-Sandbox

Host-HOME, git-crypt-Dateien und Git-Schlüssel sind ausgeblendet. Nur der Worktree ist schreibbar; Git-Daten sind read-only. Der bestehende Direct-Worker erlaubt Python-pytest sowie git diff/status, aber kein chmod/Commit/Push und kein git diff --check. Keine Umgehung bauen. Für Tests ausschließlich temporäre synthetische Fixtures verwenden. Live- oder Cluster-Servicechecks, Windows und echte Remote-Exports sind in diesem Worker nicht verfügbar. Ein Audit muss diese Grenzen im Ergebnis ausweisen. Der Haupt-Orchestrator führt Diff-Check und unabhängig dieselben Tests in der Sandbox aus.

## Review-Nachbesserung

Der erste Worker-Diff bricht ohne --harness ab: HARNESS ist durch set -u ungebunden. Der Review-Test parametrisiert jetzt beide Aufrufe. Beide müssen bestehen; Flag-Erkennung allein reicht nicht. Alle bereits genannten Nebenbedingungen und Schreibgrenzen bleiben gültig. Keine Tests entfernen oder abschwächen.
