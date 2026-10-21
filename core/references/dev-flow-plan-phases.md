# dev-flow-plan — Phasen im Detail

Referenz zum Skill `dev-flow-plan`. Der Skill-Body führt Pfad-Wahl und Guards; hier stehen die Phasen des Feature-Pfads, die Decompose-/Fan-out-Mechanik und die Schritte des Fix-Pfads.

Repo-Konfiguration: `repo.yaml` (`repo.main_branch`, `repo.scopes`, `repo.tickets`, `repo.task_runner`). `MAIN` unten = `repo.main_branch`. „Gestagt" heißt committiert + gepusht; Ticket-Blöcke (`TICKET_EXT_ID`, `stage-plan`, Ticket-Claims) gelten nur bei `repo.tickets: github`.

> cwd-Regel (Pflicht): Bash-Aufrufe immer mit `git -C <worktree>` bzw. explizitem cd+Guard — nie auf implizites cwd vertrauen. `cd` wirkt nur auf den aktuellen Bash-Call; ein bare `git commit` landet sonst im Haupt-Checkout.
>
> Der Guard vergleicht normalisiert, nicht als Zeichenkette: unter Git-Bash liefert `git rev-parse --show-toplevel` die Windows-Form, `$PWD` die POSIX-Form — deshalb steht die Toplevel-Seite in `cd … && pwd`.

---

### Phase A: Auf Main-Branch — Proposal-Phase

#### Schritt A.1: Asset-Sammlung + Codebase-Exploration
User aktiv nach Spec-Notizen, Mockups oder Screenshots fragen. Text- und Image-Dateien mit dem `Read` Tool einlesen. Code-Explorer-Subagent analysiert Code-Pfade und Architektur vor dem Brainstorming.

#### Schritt A.1.5: Intel-Gathering → Plan Intel Bundle
Nach der Exploration Generator laufen lassen — deterministisch, kein LLM:

```bash
bash scripts/plan-intel.sh <slug>
```

Befüllt `.agents/plans/<slug>/intel.json` (target_files), berechnet S1-Budgets via `plan-lint.sh`-Hooks, extrahiert Symbole per `grep`. Schema: plan-intel-bundle. `api_contracts`/`external_types` bleiben beim Planner; fehlende Quellen werden `risks[]`-Einträge. Ohne Change-Ordner: `mkdir -p .agents/plans/<slug> && bash scripts/plan-intel.sh <slug>` (Bundle wandert nach B.2).

#### Schritt A.2: Design-Bundle co-lokalisieren (nur Design-/UI-Anfragen)
Bei Design-Handoff (Bundle-ID vom User erfragen) Assets jetzt im Main-Checkout anlegen — wandern in B.2 in den Worktree:

```bash
SLUG="<slug>"
DESIGN_DIR=".agents/plans/${SLUG}/assets"
mkdir -p "${DESIGN_DIR}/new"
# Intent: cp <bundle>/chats/chat1.md "${DESIGN_DIR}/intent.md"
```

Qualitäts-Gate: jedes SVG prüfen, unpassende verwerfen (currentColor statt `<img>`, keine Stray-Hex-Werte, kein Root-`width/height`, Export-Vollständigkeit). Alt-Assets nicht mitkopieren — Abgleich in-place gegen die echte Repo-Datei erst beim Verbauen.

#### Schritt A.3: Lavish-Board anbieten — vor Brainstorming
`.lavish/<slug>-brainstorm.html` (Intent, Constraints, Trade-offs, Entscheidungen) mit `npx -y lavish-axi` öffnen. Anbieten, nicht erzwingen: ohne Zustimmung oder in nicht-interaktiver Sitzung läuft das Brainstorming über `AskUserQuestion` mit Previews — vollwertiger Ersatz.

#### Schritt A.4: Brainstorming — immer, kein Überspringen
`superpowers:brainstorming` aufrufen (oder inlined-Äquivalent ohne Skill-Load durcharbeiten). Ergebnis: Design-Spec in `.agents/plans/<slug>/design.md` (`mkdir -p` vorab). Danach Frontmatter setzen: `bash scripts/vda.sh frontmatter --spec .agents/plans/<slug>/design.md` (mit Tickets: `ticket_id`/`plan_ref` nachtragen).

Commit-Scope ist `plans`, nicht `specs` (Scopes aus `repo.scopes`): `docs(plans): …` oder `chore(plans): …`.

#### Schritt A.5: Plan anlegen — auf Main-Branch
```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
mkdir -p .agents/plans/<slug>
```

Brainstorming-Output (WARUM + WAS) nach `.agents/plans/<slug>/proposal.md`; Implementierungsplan ausschließlich nach `.agents/plans/<slug>/tasks.md`.

#### Schritt A.6: Playwright-Projekt-Gate (optional)
Bei neuen E2E-Tests passendes Playwright-Projekt zuweisen (Zuordnungstabelle: dev-flow-gotchas).

### Phase B: Worktree anlegen + Branch pushen

Branch und Worktree werden jetzt angelegt und gepusht, damit jeder Partial-Plan sofort committet und gesichert werden kann. Branch-Name: `feature/<slug>`; nur bei `repo.tickets: github` mit Ticket-Suffix `feature/<slug>-T<id>` (sonst schlägt der PR-Scope-Preflight fehl).

#### Schritt B.1: Worktree anlegen (git-crypt-safe)

Ab hier trägt jeder Datei-Tool-Pfad den Worktree-Präfix: Read/Write/Edit haben keinen Bezug zum Bash-cwd; ohne Präfix trifft ein Pfad still den Hauptcheckout. Prüfbefehl im Hauptcheckout: `git -C <repo-root> status --porcelain` muss leer bleiben.

```bash
# Preflight: Fix schon auf Main-Branch? Treffer -> abbrechen.
# Standard: git log origin/<MAIN> --oneline --grep='<slug|symptom>' | head -5
# Nur bei repo.tickets: bash scripts/plan-preflight.sh pre-worktree --ticket "$TICKET_EXT_ID"
# (rc 0 = fortfahren, 1 = bereits gemergt + abbrechen, 2 = Umgebung reparieren)

bash scripts/worktree-create.sh feature/<slug> .worktrees/<slug>
# Mit Tickets: bash scripts/worktree-create.sh feature/<slug>-T<id> .worktrees/<slug>

bash scripts/agent-lock.sh claim branch "feature/<slug>" --worktree ".worktrees/<slug>" --label dev-flow-plan \
  || { echo "Branch wird bereits bearbeitet."; exit 1; }
# Mit Tickets zusaetzlich: agent-lock.sh claim ticket "$TICKET_EXT_ID" --branch ... --worktree ... --label dev-flow-plan
```

#### Schritt B.2: Artefakte in den Worktree verschieben

```bash
WT="${REPO_ROOT}/.worktrees/<slug>"
mkdir -p "${WT}/.agents/plans/"
mv "${REPO_ROOT}/.agents/plans/<slug>" "${WT}/.agents/plans/<slug>"
[ -f "${REPO_ROOT}/intel.json" ] && mv "${REPO_ROOT}/intel.json" "${WT}/.agents/plans/<slug>/intel.json"
[ -f "${REPO_ROOT}/.lavish/<slug>-brainstorm.html" ] && mv "${REPO_ROOT}/.lavish/<slug>-brainstorm.html" "${WT}/.lavish/" 2>/dev/null || true
cd "${WT}"
```

Danach muss `git -C "${REPO_ROOT}" status --porcelain` leer sein — Reste gehören in den Worktree oder werden verworfen.

#### Schritt B.3: Scaffold-Commit + Push

```bash
cd "$WT" && [ "$(cd "$(git rev-parse --show-toplevel)" && pwd)" = "$PWD" ] || { echo "FATAL: cwd != worktree"; exit 1; }
git add .agents/plans/<slug>/
git commit -m "chore(plans): scaffold <slug> branch"
# Mit Tickets: git commit -m "chore(plans): scaffold <slug> branch [$TICKET_EXT_ID]"
git push -u origin $(git branch --show-current)
```

### Phase C: Im Worktree — Partial-Pläne schreiben

#### Schritt C.1: Decompose — Partial-Manifest erstellen
Aus `intel.json` (`impact_files`) Partial-Manifest mit disjunkten `target_files` (`| id | tasks.d/pX-*.md | impl|tests | <target_files> | <depends_on> |`); letztes Partial immer Tests-Rolle mit STRUCT2-Failing-Test-Step. Keine Datei in zwei Partials (D1). Obergrenze 9. Format-SSOT: plan-quality-gates. Routing entscheidet der Orchestrator zur Dispatch-Zeit (subagent-provisioning) — keine Routing-Spalten.

#### Schritt C.2: Pro Partial — Plan schreiben, committen, pushen

```
FOR each partial pX (p1, p2, ..., zuletzt Tests):
  ├─ C.2a: tasks.d/pX-<name>.md schreiben
  ├─ C.2b: tasks.md-Index (Partial-Manifest + File Structure) aktualisieren
  └─ C.2c: Commit + Push (mit cwd-Guard wie B.3)
        git add .agents/plans/<slug>/
        git commit -m "chore(plans): add partial pX-<name> for <slug>"
        git push origin "$(git branch --show-current)"
```

#### Schritt C.3: Plan-Qualitäts-Gate
```bash
bash scripts/plan-lint.sh .agents/plans/<slug>/tasks.md
```

#### Schritt C.4: Stagen = Commit + Push
Kein separater Stage-Befehl ohne Tickets — der gepushte Plan ist der gestagte Plan. Danach `plan done` in `phase-events.log` (füttert den Phase-Chain-Gate in dev-flow-execute):

```bash
echo "plan done $(date -u +%FT%TZ) plan-gestagt" >> .agents/plans/<slug>/phase-events.log
```

Nur bei `repo.tickets: github`: `stage-plan` mit Hold (MCP-first, Fallback Ticket-CLI) — erst nach Commit/Push, weil es den Plan aus dem Branch-Commit liest. Ausgeführt wird der Plan danach von `dev-flow-execute` (gibt den Hold frei) oder lokal per plan-runner.

---

### Schritt 3.7: Plan-Erstellung — zweistufig: Decompose → paralleler Fan-out

(a) Decompose: Orchestrator erzeugt das Partial-Manifest (1 Partial je disjunktem Subsystem, Tests immer separat; mehr als 3 nur bei echt disjunkten Dateimengen; `depends_on` optional, plan-lint validiert Referenzen und Azyklizität).

(b) Fan-out: N parallele Plan-Subagenten. Kontext pro Subagent nur: `proposal.md`, sein Manifest-Eintrag, `bash scripts/plan-intel-filter.sh <slug> <target_files...>` und plan-quality-gates. Jeder schreibt seine `tasks.d/pX-<name>.md`; der Orchestrator schreibt den `tasks.md`-Index (Partials-Manifest, File Structure als Union, finaler Verify-Task STRUCT3). `plan-lint.sh` erkennt den Partial-Modus über `tasks.d/` automatisch.

Budget-Faustregel: (Summe `wc -l` der target_files + Testdateien) × 40, aufgerundet auf S/M/L-Bucket (32000/80000/100000). Über 100000: weiter aufteilen. Worker-Stufe nach Komplexitätsklasse (subagent-provisioning).

Single-Plan-Ablauf (1-Partial-Fall und Prompt-Kern je Fan-out-Subagent): Spec committen/pushen, frischen Subagenten mit passendem Modell/Effort spawnen ( reasoning-lastig: Default `opus`, trivial `sonnet`), Kontext explizit injizieren: Spec-Pfad, Design-Bundle (`intent.md` referenzieren, finale Asset-Zielpfade in target_files, Guardrails als Acceptance-Kriterien), Grilling-/Ticket-Kontext falls vorhanden, CI-/Quality-Gates (S1-Budget gegen wirksame Schwelle — bei gebaselineten Dateien oft 0, dann zeilenneutral planen oder verkleinern; S2/S3/S4 beachten), Plan Intel Bundle (nur reale Signaturen/Typen, `s1_budget`-Werte, DB-Spalten/API-Contracts zitieren), plan-lint Hard Rules (F1/F2/STRUCT1–3/P1/B1a/B1b, Datei lesen und danach schreiben).

---

## Fix-Pfad — Schritte im Detail

### Schritt 1: Symptom festhalten
Ausgangspunkt ist das beobachtete Symptom (User-Meldung, Log, failing Check). Symptom + Reproducer gehören ins Proposal, dann direkt weiter. Nur bei `repo.tickets: github`: Ticket-ID vom User erfragen oder Bug-Ticket anlegen (MCP-first, Fallback Ticket-CLI) und als `TICKET_EXT_ID` führen.

### Schritt 2: Worktree anlegen
```bash
# Preflight wie B.1 (Standard: git log auf Main-Branch; mit Tickets: plan-preflight.sh --ticket)
bash scripts/worktree-create.sh fix/<slug> .worktrees/<slug>
WT="$(pwd)/.worktrees/<slug>"
cd .worktrees/<slug>
```

Das `cd` wirkt nur auf Bash: Datei-Tool-Pfade ab hier explizit unter `.worktrees/<slug>/`, sonst treffen sie den Hauptcheckout.

### Schritt 2.5: Branch claimen
```bash
bash scripts/agent-lock.sh claim branch "fix/<slug>" --worktree "$PWD" --label dev-flow-plan
```
Exit 1 = lebende Session arbeitet schon daran → koordinieren. Nur bei `repo.tickets: github`: zusätzlich Ticket-Claim.

### Schritt 2.7: Lavish-Board anbieten — vor Brainstorming
`.lavish/<slug>-brainstorm.html` (Root-Cause, Fix-Ansatz, Subsysteme, Edge-Cases) anbieten, nicht erzwingen. Ohne Zustimmung über `AskUserQuestion`.

### Schritt 2.8: Brainstorming — immer, kein Überspringen
`superpowers:brainstorming` mit Fokus Root-Cause, Fix-Ansatz, Subsysteme, Edge-Cases. Ergebnis: `.agents/plans/<slug>/design.md`. Kein Test vor geklärter Root-Cause.

### Schritt 3: Failing Test schreiben
Automatisierter Test, der den Bug reproduziert und fehlschlägt (rot-grün, harte Voraussetzung). Als pytest-Funktion in `tests/py/spec/<bereich>/test_<kurz_slug>.py` (Bereich aus Symptom/Feature-Name, mit Tickets: Ticket-Titel). Modul ggf. anlegen (Konventionen: `tests/CLAUDE.md`). Ausführen: `bash scripts/pytest-run.sh <modul>`.

### Schritt 4: Plan schreiben
`superpowers:writing-plans` (oder inlined-Äquivalent) nach `.agents/plans/<slug>/tasks.md` gemäß plan-lint Hard Rules. Frontmatter setzen (mit Tickets: Ticket-ID eintragen). Erst committen und pushen — Ableitungen (`plan-touched-files.sh`, mit Tickets: `stage-plan`) lesen aus dem Branch-Commit, nicht aus dem Arbeitsbaum.

### Schritt 4.5: Stagen = Commit + Push
Der gepushte Plan ist der gestagte Plan; `plan done` in `phase-events.log`. Nur bei `repo.tickets: github`: `stage-plan --hold` nach Commit/Push (MCP-first, Fallback Ticket-CLI) — damit ist das Ticket `plan_staged` und für dev-flow-execute bereit.

### Schritt 5: Commit und Push
```bash
cd "$WT" && [ "$(cd "$(git rev-parse --show-toplevel)" && pwd)" = "$PWD" ] || { echo "FATAL: cwd != worktree"; exit 1; }
git add tests/ .agents/plans/<slug>/tasks.md
git commit -m "chore(plans): add failing test + stage plan"
# Mit Tickets: git commit -m "chore(plans): add failing test + stage plan [$TICKET_EXT_ID]"
git push -u origin $(git branch --show-current)
```

Stage-Commit enthält nur RED-Test und Plan-Artefakte, keinen Production-Code — deshalb immer `chore(plans):`, nie `fix(`/`feat(`/`refactor(`/`perf(` (sonst überspringt der Execute-Implementer den Fix; Guard: `check-commit-vs-diff.sh` + `commit-msg`-Hook, Notfall-Bypass `SKIP_COMMIT_VS_DIFF=1`). Echter Production-Code gehört in einen separaten Commit mit Implementierungs-Präfix.

Stopp: failing Test, Spec und Plan sind committet und gepusht. Nächster Schritt: `dev-flow-execute`.

## Preflight — Check merged

Gilt in beiden Pfaden vor der Worktree-Anlage: verhindert Recherche in bereits erledigte Bugs.

```bash
git log origin/<MAIN> --oneline --grep='<slug|symptom>' | head -5   # Treffer -> abbrechen
```

Nur bei `repo.tickets: github`: zusätzlich Ticket-Check (bereits gemergte Ticket-ID → Ticket `done` + abbrechen; rc-Tabelle des Preflight-Skripts bzw. check-merged beachten). Der Check ersetzt nicht den Post-Merge-Scan, sondern verhindert Doppelarbeit vorab.
