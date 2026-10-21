---
name: update-dependencies
description: 'Dependency update routine for the multi-repo ecosystem; invoke explicitly with /update-dependencies when manual audit or bump is required.'
archived: true
disable-model-invocation: true
---

# ARCHIVIERT → Multi-Repo Dependency Routine

Dieser Skill wird **nicht mehr auto-getriggert**, sondern läuft planmäßig als Cloud-Routine bzw. wird manuell mit `/update-dependencies` ausgeführt.

## Multi-Repo Matrix

| Repository / Pfad | Paketmanager | Typ | Primäre Verifikation |
|-------------------|--------------|-----|----------------------|
| `~/Bachelorprojekt` | `npm` | Node.js / Monorepo | `npm run typecheck`, `npm run test:unit`, `task test:changed` |
| `~/tests` (Dotfiles) | `npm` + `pip` | Node.js & Python | `npm test --prefix ~/tests`, `pytest ~/tests/unit` |
| `~/scripts` (Dotfiles) | `npm` | Node.js Tools | `python3 -m pytest ~/scripts/ -q` |
| `~/news-agent` | `npm` | Node.js / Vite / Vue | `npm test` / Build-Check |
| `~/unsloth-boxes/*` | `uv` / `pip` | Python (pyproject.toml) | `uv run pytest` / Einzelsuiten |
| `~/mcp-servers/*` | `npm` | Node.js MCP Services | `python3 ~/scripts/mcp_health.py` |

---

## Ablauf

### Phase 1: Audit & Status

```bash
# Bachelorprojekt (primäres App-Repo)
cd ~/Bachelorprojekt && npm outdated
npm audit --json > /tmp/audit-bachelorprojekt.json

# Dotfiles Tooling & Tests
cd ~/tests && npm outdated
cd ~/scripts && npm outdated

# News Agent
cd ~/news-agent && npm outdated

# Unsloth Boxes (Python)
for dir in ~/unsloth-boxes/*/; do
  if [ -f "$dir/pyproject.toml" ]; then
    echo "=== $dir ==="
    (cd "$dir" && uv pip list --outdated 2>/dev/null || true)
  fi
done
```

### Phase 2: Klassifizierung

| Typ | Aktion | Risiko | Vorgehen |
|-----|--------|--------|----------|
| Patch (`x.y.Z`) | Auto-Update + Tests | Niedrig | Direkt aktualisieren (`npm update`) |
| Minor (`x.Y.z`) | Auto-Update + Tests | Mittel | Direkt aktualisieren + Test-Suites |
| Major (`X.y.z`) | Manuelles Upgrade / Renovate | Hoch | Eigener Feature-Branch/Worktree + Migrations-Runbook |
| Security Advisory | Sofort patchen | Kritisch | Gezieltes `npm audit fix` oder version pinning |

> **Hinweis zu Bachelorprojekt:** Renovate läuft wöchentlich via `.github/workflows/renovate.yml` ([renovate.json5](file:///home/patrick/Bachelorprojekt/renovate.json5)) und erstellt isolierte PRs für Major-Bumps. Major-Updates nicht ungestagt im Live-Tree erzwingen.

### Phase 3: Update

```bash
# 1. Dotfiles (im Worktree oder Host-Checks)
cd ~/tests && npm update
cd ~/scripts && npm update

# 2. News Agent
cd ~/news-agent && npm update

# 3. Bachelorprojekt (Minor/Patch im Range)
cd ~/Bachelorprojekt && npm update
```

### Phase 4: Verifikation

```bash
# Dotfiles Suites
npm test --prefix ~/tests
npm run typecheck --prefix ~/tests
python3 -m pytest ~/tests/unit -q
python3 ~/scripts/agent-workspace.py check

# Bachelorprojekt Suites
cd ~/Bachelorprojekt
npm run typecheck
npm run test:unit
task test:changed
task workspace:validate

# MCP Health
python3 ~/scripts/mcp_health.py
```

### Phase 5: Rollback

```bash
# Bei Fehlschlag Lockfiles zurücksetzen:
git -C ~/Bachelorprojekt checkout package-lock.json
git -C ~/news-agent checkout package-lock.json
git -C ~ checkout ~/tests/package-lock.json ~/scripts/package-lock.json 2>/dev/null || true

# Abhängigkeiten wiederherstellen:
cd ~/Bachelorprojekt && npm ci
cd ~/news-agent && npm ci
cd ~/tests && npm ci
```

## EOL-Check

- **Node.js**: `node --version` → ≥22.x (aktive LTS)
- **npm**: `npm --version` → ≥10.x / 12.x
- **Python**: `python3 --version` → ≥3.12
- **PostgreSQL**: `SELECT version()` → ≥16.x
- **k3s**: innerhalb Support-Window

## Verwandte Skills

| Skill | Beziehung |
|-------|-----------|
| `infra-ops §1` | Folge — Test-Deploy nach Major-Bump |
| `mishap-tracker` | Abschluss / Friction-Log |
| `git-workflow` | Commit, Push und PR-Erstellung |
