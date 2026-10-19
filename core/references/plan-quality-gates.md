# Plan-Quality-Gates

Jeder Implementierungsplan muss gegen diese CI-Gates geschrieben werden. Quelle der Wahrheit ist `docs/code-quality/gates.yaml` (Limits/Scopes dort nachlesen, nicht hier raten — diese Datei ist eine Karte, kein Ersatz). Konkrete Runner, Scopes und Artefaktpfade aus `repo.yaml` auflösen (`repo.task_runner`, `repo.scopes`, `repo.generated_artifacts`, `repo.main_branch`); unten steht `task` für den Runner und `main` für `repo.main_branch`.

### S1 — Zeilenlimits pro Datei (Ratchet gegen BASELINE, nicht gegen das Limit)

`node scripts/code-quality/check.mjs` (lokal: `task quality:check`, in `task freshness:check` enthalten) ist ein **Ratchet** gegen die eingefrorenen Werte in `docs/code-quality/baseline.json`. Es blockiert CI, wenn:
- eine **neue / nicht gebaselinete** Datei über ihrem Extension-Limit liegt, **oder**
- eine **bereits gebaselinete** Datei *wächst*, d.h. `metric > baseline[datei].metric` (worsened).

> **Die Schwelle, die in der Praxis trifft, ist NICHT das statische Limit, sondern der Baseline-Wert.** Eine gebaselinete Datei liegt bereits *über* dem Limit und ist auf ihrem Ist-Wert eingefroren → Budget **0 oder negativ**: schon **+1 Zeile** macht CI rot. Das statische Limit gilt nur für *neue/kleine* Dateien.

Die statischen Limits stehen hier **bewusst nicht**. Jede Kopie driftet (Beispiel T002452: `.sh` 500 → 800 machte eine alte Tabelle falsch); deshalb Lesebefehl statt Werte:

```bash
yq '.s1.limits' docs/code-quality/gates.yaml     # oder: grep -A15 '  limits:' docs/code-quality/gates.yaml
```

**Pflicht beim Plan-Schreiben — pro zu ändernder Datei BEIDE Schwellen ermitteln:**
1. `wc -l <datei>` → Ist-Zeilen.
2. Baseline-Wert nachschlagen (die **wirksame** Schwelle):
   ```bash
   jq -r '."S1:<relativer/pfad>".metric // "nicht-baselined"' docs/code-quality/baseline.json
   ```
   - `nicht-baselined` → Schwelle = Extension-Limit aus `gates.yaml` → `s1.limits`, Budget = Limit − Ist.
   - eine Zahl → gebaselined (eingefroren). Schwelle = **dieser Baseline-Wert**, Budget = Baseline − Ist (**oft 0**).
3. Budget im Plan notieren — gegen die wirksame Schwelle, z.B. „`CoachingSettings.svelte` Ist 600 · Baseline 600 → **Budget 0**: Änderung MUSS zeilenneutral sein ODER die Datei echt verkleinern."
4. Liegt die Datei nach der Änderung voraussichtlich über ~80 % ihrer **wirksamen Schwelle**, Aufteilung in ein Modul gleich mit einplanen — **echter Split/Extraktion**, kein kosmetisches Zeilen-Zusammenziehen.
5. Neue Dateien mit Wachstumsreserve unter dem Limit schneiden.
6. **Niemals** eine Baseline-/Ignore-Ausnahme einplanen, um die Schwelle zu umgehen — die Baseline-Key-Count-Assertion in `freshness:check` failt ohnehin bei Baseline-Wachstum.

### S2 — Import-Zyklen

Keine neuen Zyklen in den tsconfig-basierten Graphen (Scopes aus `repo.scopes`, z. B. `website`, `e2e`). Helper-Module als **pure Module** ohne Rück-Import auf DB-/API-Schichten planen.

### S3 — Hardcodierte Hostnamen

In den cmd-seitigen Scopes (aus `repo.scopes`, z. B. `fleet/`, `prod*/`, `components/website/src/`) sind String-Literale der Brand-Domains verboten (Kommentarzeilen ausgenommen). Immer Env-/Config-basierte Auflösung vorsehen — nie Brand-Domains in Code-Snippets vorgeben.

### S4 — Orphan-Manifeste/-Skripte

Jedes neue Manifest muss in seiner Kustomization referenziert sein, jedes neue Skript (`scripts/*.sh`/`*.mjs`) von Taskfile/CI/Doku/anderem Skript erreichbar — sonst Orphan-Violation.

### CQ02 — Explizite `any`-Typen (Health-Goal)

**Limit:** ≤ 200 explizite `any`-Verwendungen global (Gate: `tests/py/spec/test_code_quality_and_gates.py`).

```bash
# Ist-Zählung vor der Änderung (Baseline für den Plan)
grep -rn ': any\|<any>\|as any' components/website/src --include='*.ts' --include='*.svelte' --include='*.astro' | wc -l
```

**Pflicht:** Kein Plan darf die `any`-Anzahl erhöhen. Neue exportierte Funktionen/API-Handler typisieren — kein `as any`, kein `catch (e: any)`. Unvermeidbare `any`-Typen (z.B. Drittanbieter-Interop) brauchen eigenen Task „CQ02: any-Typen eliminieren".

**Prüfbefehl für den Verify-Task:**
```bash
bash -c "count=\$(grep -rn ': any\|<any>\|as any' components/website/src --include='*.ts' --include='*.svelte' --include='*.astro' | wc -l | tr -d ' '); echo \"any count: \$count (limit: 200)\"; [ \$count -le 200 ]"
```

### Vitest-Abdeckung (Health-Goal)

Jeder Plan mit neuen/wesentlich geänderten Dateien in `components/website/src/lib/**` oder `components/website/src/pages/api/**` MUSS einen Vitest-Test-Task enthalten:

- **Neue Lib-Datei** → Test in `components/website/src/lib/__tests__/<name>.test.ts` (oder nächstgelegene Test-Datei erweitern, bevorzugt).
- **Neuer API-Endpunkt** → Vitest-Test im zugehörigen Test-Bundle (`components/website/src/**/__tests__/`).
- **Keine Test-Datei anlegen** ohne `task test:inventory`-Schritt (CI-Inventar-Check).

**Abweichung begründen:** Ändert ein Plan `.ts`/`.svelte`-Dateien ohne neuen Test (konfigurativ, logikfreier Refactor), Kommentar `<!-- vitest: kein neuer Test nötig, weil … -->` einfügen.

### plan-lint Hard Rules (fail-closed Gate — `scripts/plan-lint.sh`)

Jede `tasks.md` muss diese Pflichten erfüllen. **Diese Datei ist die kanonische Referenz für das Plan-Format** (SSOT hier + `scripts/plan-lint.sh`; Skill und Phasen-Referenz verlinken hierher):

> Hinweis: Das `## Partials`-Manifest trägt KEINE per-partial Tier-/Kontext-Spalten — der Orchestrator routet nach Komplexitätsklasse.

- **F1 Frontmatter:** YAML-Frontmatter mit Pflicht-Keys `title`, `domains`, `status` (alle nicht-leer). Nur mit Ticket-Backend (`repo.tickets` gesetzt): zusätzlich `ticket_id`.
- **F2 domains:** `domains:` ist non-empty YAML-Liste (`[a, b, …]`), kein leerer String, kein `[]`.
- **STRUCT1 Plan-Shape:** Nach Frontmatter H1 `# <slug> — Implementation Plan`, gefolgt von H2 `## File Structure` mit geänderten/neuen Dateien.
- **STRUCT2 Failing-Test-Step:** Mindestens ein Task mit rot→grün-Step (Phrase `expected: FAIL`, regex `expected:? *fail`) UND echtem Testrunner-Aufruf (`bats`, `vitest`, `pytest`, `jest`, `mocha`, `go test`, `playwright test`). Phrase allein reicht NICHT. Der finale `task test:*`-Verify-Task (STRUCT3) zählt NICHT.
- **STRUCT3 Verify-Task:** Letzter Task listet `task test:changed`, `task freshness:regenerate`, `task freshness:check`.
- **P1 Placeholder-Verbot:** In Prosa (außer ```-Fences/`inline code`) kein `TBD`, `TODO`, `FIXME`, `???`, `<ausfüllen>`, `similar to Task <N>`.
- **B1a Budget-Integrität:** Behauptete Budget-Werte referenzierter existierender Dateien müssen exakt dem Linter-Budget (Baseline vs. Limit) entsprechen, sonst Hard-Fail.
- **B1b Split/Shrink bei Budget ≤ 0 (Warn):** Ohne Split-/Shrink-Stichwort (`split`, `extract`, `verkleiner`, `shrink`, `aufteil`) gibt der Linter eine Warnung aus.

### Gate-Messung & Ad-hoc-Skripte (Positiv-Anker-Pflicht)

Gate-Werte NIE mit ad-hoc Einzeilern prüfen, wenn ein autoritatives Messskript existiert (`scripts/health-goals-check.sh`). Falls unvermeidbar:
- IMMER Positiv-Anker mitmessen: `echo "Anker: claimed=$(echo "$claimed" | grep -c .) actual=$(echo "$actual" | grep -c .)"` — beide > 0.
- Stderr nicht nach `/dev/null` umleiten — leeres Stdin darf nicht als „0 Abweichungen" zählen.

### Weitere CI-Gates (Pflicht im finalen Verifikations-Task)

```bash
task test:changed          # gezielte Tests geänderter Domains
task freshness:regenerate  # generierte Artefakte aktualisieren (repo.generated_artifacts)
task freshness:check       # CI-Äquivalent: Freshness + quality:check (S1–S4-Ratchet) + Baseline-Assertion
```

Dazu:
- **Test-Inventar:** nach Test-Änderung `task test:inventory` regenerieren und Inventar-Datei (`repo.generated_artifacts`, z. B. `components/website/src/data/test-inventory.json`) mitcommitten.
- **Baseline darf nicht wachsen:** Key-Anzahl von `docs/code-quality/baseline.json` gegen `repo.main_branch` vergleichen — keine neuen Baseline-Einträge.
- **Bestehende Tests erweitern** statt neue Dateien anlegen (Vitest/Playwright/pytest zuerst suchen).
- **Manifest-Änderungen:** `task workspace:validate` + relevante `./tests/runner.sh local <TEST-ID>`.
- **Image-Pins:** CI warnt bei `:latest` (Ausnahmen dokumentiert).
- **Shell-Snippet Sanity:** CLI-Befehle auf Argument-Fallen prüfen (z.B. `jq --args` → Inputs via Stdin `< file`).

### Lifecycle Receipt + Delete

Jeder ausgeführte Plan endet mit Receipt UND Delete — kein `.md`-Überhang:

- **Receipt:** Frontmatter-`completed` + Check-Evidenz + Merge-SHA im Plan-File selbst; kein DB-Archiv (Ticket-Retirement).
- **Delete:** `branch-reaper.sh --sweep --plan-cleanup` entfernt Plan-Ordner per `git rm`, gebündelt als Sammel-Cleanup-PR — nie direkt nach main.
- **Fail-closed:** ohne verifizierten Record kein Delete.
- **Abgrenzung:** Generieren schreibt Pläne; Validieren (`plan-lint.sh`, Gates, Guards) prüft nur.
