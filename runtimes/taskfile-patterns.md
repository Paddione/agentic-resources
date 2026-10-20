# Taskfile-Muster (extrahiert aus Bachelorprojekt)

Drei wiederverwendbare Task-Patterns für Folgeprojekte. Konvention: Root-
`Taskfile.yml` mit `includes:` je Bereich (`test`, `quality`, `workspace`),
`dir: .`.

## 1. test:changed — Smart Selection

Nur Tests zu geänderten Dateien laufen lassen:

```yaml
test:changed:
  cmds:
    - |
      CHANGED=$( (git diff --name-only --diff-filter=d origin/main 2>/dev/null \
        || git diff --name-only --diff-filter=d HEAD 2>/dev/null) | sort -u \
        | bash scripts/filter-generated.sh || true)
      # CHANGED per Pfadpräfix auf RUN_*-Flags mappen (Repo-Pfade einsetzen),
      # dann nur die fälligen Suiten starten.
```

Generierte Artefakte vorher herausfiltern (`filter-generated.sh`, via
`.gitattributes` als `linguist-generated` markiert), sonst starten teure
Suiten ohne Bezug.

## 2. freshness:regenerate + freshness:check

Generierte Artefakte deterministisch regenerieren; der Check regeneriert
ZUERST und prüft dann per Diff (T002252 — sonst ist der Gate auf frischem
Checkout strukturell grün). Neue Output-Artefakte brauchen einen
`.gitattributes`-Eintrag mit `merge=ours` (kein Rebase-Rauschen).

## 3. workspace:validate — Kustomize Dry-Run

```yaml
workspace:validate:
  cmds:
    - kubectl kustomize k3d/ --load-restrictor=LoadRestrictionsNone | kubectl apply --dry-run=client -f -
```

Manifest-Fehler vor Cluster-Kontakt finden. Für Nicht-K8s-Repos: analoger
Render-/Dry-Run des Deploy-Artefakts.

## 4. agent:guardrails — Größenlimits und kompakte Ausgabe

Limits aus `repo.yaml` lesen (`agent_max_module_loc`, `agent_max_function_loc`,
`agent_tier1_max_lines`), Details in
`core/references/agent-optimized-repo.md`:

```yaml
agent:lint:
  cmds:
    - |
      MAX_MOD=$(yq '.repo.agent_max_module_loc' repo.yaml 2>/dev/null || echo 500)
      fail=0
      for f in $(git diff --name-only --diff-filter=d origin/main 2>/dev/null \
        || git diff --name-only --diff-filter=d HEAD 2>/dev/null); do
        case "$f" in *.ts|*.py|*.md) ;;
          *) continue;; esac
        lines=$(wc -l < "$f" 2>/dev/null || echo 0)
        if [ "$lines" -gt "$MAX_MOD" ]; then echo "TOO-LONG $f ($lines > $MAX_MOD)"; fail=1; fi
      done
      # Funktionslänge per Sprach-Linter prüfen (ESLint max-lines-per-function,
      # Ruff C901/PLR0912), nicht per Shell-Heuristik.
      exit $fail
agent:test:
  cmds:
    # Nur betroffene Suiten (test:changed), einzeilige Reporter
    # (vitest --reporter=basic, pytest -q --tb=line), Volllogs in Dateien.
    - task test:changed TEST_ARGS="--reporter=basic"
```

Lokal nur 1–10 % der betroffenen Suiten laufen lassen, Vollmatrix in CI.
Verbose-Ausgaben verdrängen Instruktionen und triggern Kompaktierungen.
