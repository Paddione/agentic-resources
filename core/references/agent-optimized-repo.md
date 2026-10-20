# Agentenoptimierte Repo-Struktur (SSOT)

Startwerte für agentenlesbare Consumer-Repos, keine Konstanten. Jedes Repo misst
selbst und schärft die Werte nach. Änderung NUR in dieser Datei.

Repo-Variablen aus `repo.yaml` (alle optional): `MAIN` = `repo.main_branch`,
`task` = `repo.task_runner`, Limits = `repo.agent_max_module_loc` (500),
`repo.agent_max_function_loc` (50), `repo.agent_tier1_max_lines` (300).
Fehlt ein Schlüssel, gilt der Klammerwert. Lesebefehl:

```bash
yq '.repo.main_branch' repo.yaml 2>/dev/null || echo main
```

## 1. Kontext-Budget

Annahmen: Systemprompt plus Tool-Schemas belegen grob 10.000 Tokens, bevor eine
Repo-Zeile geladen ist. Root-Kontext konkurriert mit Quelldateien und Turn-Historie.
Folge: Root klein halten, Details per Pointer auslagern (§3), Rauschen per Ignore
filtern (§6), Ausgaben kompakt halten (§7).

## 2. Removal-Test

Jeder Satz in `AGENTS.md` muss eine Agentenentscheidung ändern oder einen nicht
ableitbaren Befehl liefern. Fällt der Satz weg und das Verhalten bleibt gleich,
fällt der Satz weg. Stilregeln gehören nicht in Prompts, sondern in Formatter.

## 3. Drei Stufen (harness-neutral)

- **Stufe 1 (Root):** `AGENTS.md` plus Tool-Notizen (`CLAUDE.md`). Ziel unter 300
  Zeilen, intern unter 60 anstreben. Inhalt nur Topologie, Befehle, Zeiger.
  Warnung: Manche Harnesses kappen große Root-Dateien still (Codex-Parameter
  `project_doc_max_bytes`, Default 64 KiB, ältere 32 KiB). Wer darüber liegt,
  driftet ohne Fehlermeldung.
- **Stufe 2 (scoped):** Verzeichnisregeln, die nur bei Bedarf laden
  (`src/api/AGENTS.md`, `.cursor/rules/*.mdc` mit `globs`, Copilot
  `.github/instructions/*.instructions.md` mit `applyTo`). Begrenzungen des
  jeweiligen Harnesses einhalten, Rest bleibt dormant.
- **Stufe 3 (on-demand):** Volltexte in `docs/`, referenziert als
  `Pfad:Zeile`. Pointer sind pullsicher zu halten: kein Snippet duplizieren, das
  veraltet. Hinweis: Pointer erweitern die Vertrauensgrenze. Nur eigene
  Repo-Pfade zeigen lassen, keine fremden URLs ausführen.

## 4. Größenlimits (Startwerte)

| Maß | Startwert | Bei Überschreitung |
|---|---|---|
| Modul | 150–500 LOC | Ab 300–500 aufteilen, hart 500 |
| Funktion | unter 50 LOC | Extrahieren, Komplexität per Lint |
| UI-/Service-Komponente | unter 200 LOC | Zustand und Lifecycle trennen |
| PR-Diff | um 200 Zeilen, 2–5 Dateien | Task splitten, Schnittstellen prüfen |
| Gelesene Dateien pro Task | bis 10 | Kopplung senken, Abstraktion prüfen |
| Root-Datei | unter 300 Zeilen | Stufe 2/3 auslagern (§3) |

Hintergrund: Search-Replace-Engines treffen bei 200–400 LOC am besten, bauen
über 400 LOC mit repetitiven Mustern ab. Monolithen über 700 LOC verlieren
Exporte und Signaturen. PR-Erfolgsraten fallen mit wachsendem Diff deutlich.

## 5. Navigation und Verträge

- Eindeutige Bezeichner (`initializeBillingSession` statt `init`), semantische
  Pfade (`services/billing/session-broker/`), damit Suche ohne Kontextläufe trifft.
- Exportgrenzen strikt typisieren. Jede untypisierte Grenze kostet zusätzliche
  Leseläufe zum Erschließen des Vertrags.
- Tests neben die Implementierung legen (`BillingEngine.ts`,
  `BillingEngine.test.ts`), Mocks eng kolokalisieren. Getrennte
  `/tests`-Spiegel kosten Suchläufe und verlangsamen TDD-Schleifen.

## 6. Ignore-Dateien

`.aiderignore` und `.claudeignore` im Root pflegen. Raus gehören Dependencies,
Build-Artefakte, Fixtures, generierte Stubs und die Migrationshistorie (nur
aktueller Schema-Stand zählt, Historie verleitet zu veralteten Spalten).
Effekt in der Praxis: bis zu 80 % weniger Rauschen in Maps und Suchen.

## 7. Deterministisch statt natürlichsprachlich

- Stil per Formatter und Hooks, nicht per Prompt (Post-Tool- und Stop-Hooks).
- Architektur per Test (`kein Modul über N LOC`, `kein untypisierter Export`),
  referenziert in [`taskfile-patterns.md`](../../runtimes/taskfile-patterns.md).
- Testreporter einzeilig (`ERROR: [Datei:Zeile] [Grund]`), Volllogs in Dateien,
  Agent liest selektiv.
- Lokal nur 1–10 % der betroffenen Suiten laufen lassen, Vollmatrix in CI.
  Hintergrund: volle Verbose-Läufe verdrängen Instruktionen und triggern
  verlustreiche Kompaktierungen; erschöpfte Sessions verlieren bis zu 98 %
  akkumulierten Zustands.

## 8. Bezug zu `repo.yaml`-Profilen

Profile unter `runtimes/profiles/` seeden die Schlüssel aus dem Kopf dieser
Datei. `init.sh --dry-run` zeigt vorab, was verlinkt und geseedet wird.
Harness-Besonderheiten stehen in den jeweiligen Skill-Dateien, nicht hier.
