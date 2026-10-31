---
name: dev-flow-e2e
description: 'Use AFTER dev-flow-execute has merged and deployed, to write and run Playwright E2E tests against the live brand environments. Triggers on Playwright, E2E test, e2e/, playwright test, npx playwright, browser test against prod, "test the deployed change", nightly e2e workflow, Playwright project assignment. Not for unit or pytest tests during implementation — those belong in dev-flow-execute.'
agent: bp-ship
---

# dev-flow-e2e — Playwright E2E Tests schreiben & ausführen

Repo-Spezifika stehen nicht hier, sondern in `repo.yaml` im Consumer-Repo-Root:
Vor Beginn `repo.tickets` (`none` oder Ticket-Backend — Ticket-IDs in
Dateinamen/Titeln nur only-if-tickets), `repo.scopes` (Commit-Scope-Allowlist)
und `repo.task_runner` (`taskfile` oder `none` — `task ...`-Befehle nur dann)
aus `repo.yaml` lesen. Fehlt ein Schlüssel, die Annahme explizit nennen.
Live-URLs, Brand-Namen und Playwright-Projekte unten sind das Beispiel aus dem
Quell-Repo — im Consumer an die eigene Umgebung anpassen.

Der test-only Chore folgt dem gemeinsamen [dev-flow-lifecycle](references/dev-flow-lifecycle.md); diese Skill besitzt die Playwright-spezifischen Entscheidungen und Live-Gates.

## Wann diese Skill greift

`dev-flow-execute` hat fertig implementiert und gemergt. Jetzt soll die implementierte Funktion mit echten Browser-E2E-Tests abgesichert werden. Für die Live-Erkundung werden Standard-Browser/HTTP-Tools oder native Playwright-Mittel eingesetzt.

**Sage zu Beginn:** "Ich nutze dev-flow-e2e für Playwright E2E Tests."

---

## Position im Git-Kreislauf

```
    ┌──────────────────────────────────────────────────────────────────┐
    ▼                                                                  │
[ main ] ←── merge ←── PR ←── implement ←── [plan committed]          │
    │                                                                  │
    └──► [E2E Tests schreiben + committen] ──► [push] ──► AUSSTIEG ───┘
              DIESER SKILL (post-merge)
```

**EINSTIEG:** `<repo.main_branch>` nach Merge — Feature deployed auf Live-Umgebung
**AUSSTIEG:** E2E-Spec committed + gepusht auf `chore/*`-Branch (only-if-tickets: ticketed), als PR gemergt und bereinigt
> `test/*`-Branches sind nicht erlaubt — der Pre-Commit-Hook lässt nur `feature/ fix/ chore/ docs/ feat/batch-*` zu; test-only E2E-Branches nutzen `chore/`.
**Voraussetzung:** `dev-flow-execute` Schritt 8 (Post-Merge Deploy) abgeschlossen, Live-URL erreichbar

---

## Schritt 0: Kontext ermitteln

Finde heraus, was implementiert wurde:

```bash
# Letzten PR ansehen
gh pr list --state merged --limit 3 --json number,title,headRefName,mergedAt

# Geänderte Dateien des letzten PR
PR_NUM=$(gh pr list --state merged --limit 1 --json number -q '.[0].number')
gh pr view "$PR_NUM" --json files -q '.files[].path' | sort
```

Ermittle daraus:
- **Welche URLs/Endpunkte** wurden neu erstellt oder verändert?
- **Welches Playwright-Projekt** passt (Beispiel-Mapping siehe Schritt 1)?
- **Ticket-ID** aus dem PR-Titel (Format `T######`) — nur only-if-tickets.
- **Codegraph-Abgleich:** Bei unklaren Abhängigkeiten geänderte Routen oder Helper via `code-graph-interpretation` prüfen (`trace_path --include-tests true`).

---

## Schritt 1: Ziel-URL bestimmen

Beispiel-Mapping aus dem Quell-Repo (im Consumer ersetzen):

| Geänderte Dateien | Live-URL | Playwright project |
|---|---|---|
| `components/website/src/**` (öffentlich) | `https://web.mentolder.de` | `website` |
| `components/website/src/**` (authentifiziert) | `https://web.mentolder.de` | `mentolder` (nutzt `.auth/mentolder-website-admin.json`) |
| `fleet/nextcloud*.yaml` | `https://files.mentolder.de` | `services` |
| korczewski-spezifisch (fleet cluster) | `https://web.korczewski.de` | `korczewski` *(deaktiviert / frozen)* |
| Übergreifender Smoke-Test | — | `smoke` |
| Mobile/Responsive | — | `ios` |

Projekt- und Markennamen oben sind Consumer-Beispiele — die realen Namen stehen im Consumer-Repo (`playwright.config.ts`, `repo.yaml`).

> Pure-Function Unit-Tests laufen über Vitest (`npx vitest run`), nicht über Playwright.

```bash
# Live-URL für spätere Schritte festlegen (Default in configs ist http://localhost:4321)
BASE_URL="https://web.mentolder.de"   # anpassen falls nötig
```

### Credentials & Brand-Status

Im Quell-Repo gibt es **kein** separates E2E-Test-Passwort für den
eingefrorenen Zweit-Brand (Deployments stehen auf 0/0, die URL antwortet mit
503); E2E-Tests laufen ausschließlich gegen den Haupt-Brand, das
Zweit-Brand-Projekt ist deaktiviert. Im Consumer: denselben Status-Check
(läuft der Brand, existiert das Test-Passwort) vor dem Lauf durchführen.

---

## Schritt 2: Live-Erkundung & Endpunkt-Prüfung

Verschaffe dir ein vollständiges Bild der implementierten Funktion: welche Seiten, welche API-Endpunkte, welche Auth-Anforderungen und DOM-Elemente existieren.

```bash
# HTTP-Erreichbarkeit & Headers prüfen
curl -sI "$BASE_URL/<pfad>"

# Falls nötig HTML-Struktur / Selektoren sichten (data-testid, semantische Rollen)
curl -sL "$BASE_URL/<pfad>" | head -n 50
curl -sL "$BASE_URL/<pfad>" | grep -iE 'data-testid|role=|aria-label' | head -n 30
```

---

## Schritt 3: Test-Spec schreiben

### Dateiname

| Situation | Dateiname |
|---|---|
| Neue Feature-Tests (neuer FA-Block) | `fa-<NN>-<slug>.spec.ts` — nächste freie Nummer aus `tests/e2e/specs/` |
| Bug-Regression (only-if-tickets) | `fa-bug-t<TICKETID>.spec.ts` (z.B. `fa-bug-t000440.spec.ts`) |
| Bug-Regression (ohne Tickets) | `fa-bug-<slug>.spec.ts` |
| Ergänzung zu bestehendem Spec | In bestehende `fa-<NN>-*.spec.ts` einfügen |

Nächste freie FA-Nummer ermitteln:
```bash
ls tests/e2e/specs/fa-[0-9]*.spec.ts | grep -oP 'fa-\K[0-9]+' | sort -n | tail -1
```

### Test-Vorlage

Implementierte Features erfordern echte Interaktionstests (Happy Path, Validierung, Zustandsänderungen) statt reiner URL-Gating-Checks. Folge den Locator- und Assertions-Mustern aus `playwright-best-practices`:
- **Resistente Selektoren:** Nutzerorientierte Locators bevorzugen (`page.getByRole()`, `page.getByLabel()`, `page.getByTestId()`).
- **Web-First Assertions:** Immer auto-retrying Assertions nutzen (`await expect(locator).toBeVisible()`).
- **Keine harten Sleeps:** `page.waitForTimeout()` ist verboten; auf Web-Events oder Locator-Zustände warten.

```typescript
import { test, expect } from '@playwright/test';

const BASE = process.env.WEBSITE_URL ?? 'https://web.mentolder.de';

// PFLICHT: Tag-Annotation für den PR-E2E-Workflow (e2e-pr.yml).
// Der Tag steuert, welche Tests bei PRs mit diesem Feature-Scope laufen.
// Verfügbare Tags (Consumer-Beispiele): @smoke @website @content-hub @admin @factory @planungsbuero
//                  @booking @meeting @billing @messaging @fragebogen @crm
// Neue Feature-Tags können ergänzt werden (Branch-Mapping in e2e-pr.yml erweitern).
test.describe('FA-<NN>: <Feature-Name>', { tag: ['@<feature-tag>'] }, () => {
  // Muster 1: Interaktives Feature-Verhalten (Happy Path & Benutzerinteraktion)
  test('T1: <feature> performs intended action', async ({ page }) => {
    await page.goto(`${BASE}/<pfad>`);

    const submitBtn = page.getByRole('button', { name: /speichern|absenden/i });
    await expect(submitBtn).toBeVisible();

    await page.getByLabel('Titel').fill('Test-Eintrag');
    await submitBtn.click();

    await expect(page.getByText('Erfolgreich gespeichert')).toBeVisible();
  });

  // Muster 2: Auth-Gating & Absicherung
  test('T2: /<pfad> requires authentication', async ({ page }) => {
    await page.goto(`${BASE}/<pfad>`);
    await expect(page).not.toHaveURL(`${BASE}/<pfad>`);
  });
});
```

---

## Schritt 4: Spec registrieren

Trage die neue Datei in `tests/e2e/playwright.config.ts` ein falls nötig:

```typescript
// Im passenden project-Block (z.B. 'website' oder 'mentolder')
testMatch: [
  '**/fa-<NN>-<slug>.spec.ts',
],
```

---

## Schritt 5: Tests ausführen und verifizieren

> **Wichtig — Setup-Details:**
> - **Working directory:** alle Playwright-Aufrufe laufen aus `tests/e2e/` (dort liegen die Configs wie `playwright.config.ts`).
> - **node_modules:** frische Worktrees haben kein `tests/e2e/node_modules` — deshalb `[[ -x ./node_modules/.bin/playwright ]] || npm ci`.
> - **`WEBSITE_URL`:** Default in Configs ist `http://localhost:4321`. Bei Tests gegen Live zwingend `WEBSITE_URL="$BASE_URL"` mitgeben, sonst scheitern Tests an `net::ERR_CONNECTION_REFUSED`.
> - **`SKIP_DB_PURGE=1`:** überspringt den Prod-DB-Purge im globalen Setup/Teardown — nötig, wenn das Cron-Secret nicht gesetzt ist.
> - **Playwright-Projekt-Zuordnung:** siehe dev-flow-gotchas (Playwright Project Assignment).

```bash
# E2E Tests ausführen (Full Run)
cd tests/e2e/ && [[ -x ./node_modules/.bin/playwright ]] || npm ci
SKIP_DB_PURGE=1 WEBSITE_URL="$BASE_URL" ./node_modules/.bin/playwright test \
  specs/<neu>.spec.ts \
  --project "$PLAYWRIGHT_PROJECT"

# Schneller PR-E2E-Lauf (nur relevante getaggte Tests, ohne DB-Purge):
WEBSITE_URL="$BASE_URL" ./node_modules/.bin/playwright test \
  --config playwright.pr.config.ts \
  --grep "@<feature-tag>|@smoke"
```

---

## Schritt 6: Test-Inventory aktualisieren

Falls neue FA-Tests angelegt wurden (nur wenn `repo.task_runner` = `taskfile`, sonst das Consumer-Äquivalent):

```bash
task test:inventory
git diff components/website/src/data/test-inventory.json
```

### Lokaler Lauf für SDLC- und LLM/GPU-Specs

Zwei Spec-Klassen laufen bewusst **nicht** im Nightly (`e2e.yml` / `playwright.config.ts`),
sondern nur lokal über `playwright.local.config.ts`:

- **`sdlc-local`** — die `guardSdlc`-Specs (SDLC-Cockpit, dev-status, Factory-Ansichten).
  Die Routen sind im Prod-Build absichtlich entfernt; der Guard skippt dort weiterhin und
  wirft gegen eine Dev-/localhost-Instanz ohne SDLC-Routen einen Fehler (fail-loud).
  Benötigt Admin-Auth (`mentolder-setup` läuft als Dependency mit).
- **`llm-local`** — LLM-Router- und GPU-VRAM-Specs. Der Router
  sitzt auf dem GPU-Host im wg-mesh; ohne `LLM_HOST_IP`/`LLM_ROUTER_URL` skippen die Specs
  selbständig.

```bash
cd tests/e2e/ && [[ -x ./node_modules/.bin/playwright ]] || npm ci
# SDLC-Cockpit-Specs gegen eine Dev-Instanz mit SDLC-Build:
SKIP_DB_PURGE=1 WEBSITE_URL=http://localhost:4321 ./node_modules/.bin/playwright test \
  --config playwright.local.config.ts --project sdlc-local
# LLM-Router/GPU-Specs aus dem wg-mesh:
SKIP_DB_PURGE=1 ./node_modules/.bin/playwright test \
  --config playwright.local.config.ts --project llm-local
```

---

## Schritt 7: Commit & Push

Läuft nach **`git-workflow` Schritt 2–4** (SSOT: Conventional Commits, git-crypt-Staging-Guard,
Commit-Verifikation, Scope-Preflight gegen `repo.scopes`).

E2E-spezifisch — zu stagende Pfade und Titelformat:

```bash
git add tests/e2e/specs/<neu>.spec.ts tests/e2e/playwright.config.ts components/website/src/data/test-inventory.json
# Titel (only-if-tickets): "test(test): add E2E tests for <feature> [$TICKET_ID]"
# Titel (ohne Tickets): "test(test): add E2E tests for <feature>"
# Scope 'test' verwenden — 'e2e' lehnt validate-commit-msg ab
# (konsolidiert; erlaubte Scopes: Scopes-Skript bzw. repo.scopes).
```

---

## Schritt 8: E2E Smoke auf Live optional anstoßen

```bash
cd tests/e2e/ && SKIP_DB_PURGE=1 WEBSITE_URL=https://web.mentolder.de ./node_modules/.bin/playwright test \
  --project website
```

---

Die Repository-Änderung folgt anschließend dem test-only Chore/Git-Lifecycle: PR erstellen,
CI abwarten, Merge über `git-workflow` anfordern und erst nach bestätigtem Merge Worktree und
Branch bereinigen. Kein direkter Push auf `<repo.main_branch>` und kein `feature/*`-Branch für diese reine
Teständerung.

## Schritt 8.5: Optionale Stufe `headed-verify`

**Explizit optional — kein Pflichtschritt, kein CI-Gate.** Headed-Läufe gegen die Live-Umgebung
sind langsam und flakeanfällig; als Merge-Gate würden sie den Durchsatz senken statt die Qualität
zu heben. Diese Stufe läuft **nur manuell/agentisch**, nie automatisiert in der CI oder als required check.

**Trigger:** `--headed` Flag beim Aufruf dieses Skills, oder Env `HEADED_VERIFY=true`.

**Ablauf:**
1. Der Agent parametrisiert `tests/e2e/specs/k8-headed-verify.spec.ts` (Ziel-URL, Selektoren,
   Assertions) passend zur gerade verifizierten Implementierung.
2. Ausführung **headed** (echter, sichtbarer Chrome — kein CI-Runner, kein Xvfb):
   ```bash
   cd tests/e2e/ && SKIP_DB_PURGE=1 WEBSITE_URL="$BASE_URL" ./node_modules/.bin/playwright test \
     specs/k8-headed-verify.spec.ts --headed --project website
   ```
3. **Optional — Vision-gestützte Verifikation:** Screenshots aus dem Testlauf an das lokale
   vision-fähige Modell senden und die Antwort (UI-Elemente, Text, Positionierung korrekt?)
   ins Testergebnis einbetten. Der Weg führt über den **Devmesh Router auf `127.0.0.1:18235`**
   (oder direkt `:1919` Qwen3.8-27B mit mmproj-Vision):
   ```bash
   curl -sf -m 3 http://127.0.0.1:18235/v1/models | grep -qE 'chat_primary|default|qwen' \
     && echo "Vision/LLM verfuegbar" \
     || echo "kein Endpunkt — Punkt 3 ueberspringen"
   ```
   Anfrage-Parameter (Pflicht, sonst Denk-Blockade): `max_tokens` ≥ 800 und
   `reasoning_effort: "low"` — sonst verbrauchen die Modelle das komplette
   Fenster fürs Denken und liefern eine leere Antwort.

   > Frühere Aliase/Ports (`gemma12-vision` auf `:8089`, `gemma4-e4b-unsloth`, davor 8094 mit 8091 als
   > Rückfall) sind dekommissioniert. Immer die aktiven Modelle gegen `/v1/models` auf `:18235`
   > verifizieren statt historische Namen vorauszusetzen.

   Ist der Endpunkt nicht erreichbar, überspringe Punkt 3 — die Verifikation bleibt optional und
   blockiert den Ablauf nicht. Unterscheide dabei „Proxy antwortet nicht" (Proxy starten) von
   „Proxy antwortet, Alias fehlt" (Backend-Konfiguration prüfen) — die Abhilfe ist eine andere.
   Leere Antworten trotz erreichbarem Alias deuten auf die Denk-Blockade oben
   (Parameter prüfen) oder einen Proxy-Budget-Bug (Bild-Base64 wurde als
   Text tokenisiert und `max_tokens` gekappt) hin.

   Für einen **breiten** vision-geurteilten Durchgang über alle Routen statt einer Einzelprüfung:
   den Visual-Sweep-Task des Consumer-Repos (Quell-Repo: `task test:e2e:visual-sweep:vision`;
   nur wenn `repo.task_runner` = `taskfile`) — report-only, kein CI-Gate.
4. **Kein Abbruch bei Fehler:** Diese Stufe informiert den Agenten, blockiert aber nicht den
   Merge- oder Deploy-Flow — sie läuft grundsätzlich erst nach Merge/Deploy (Schritt 8).

---

## Schritt 9: Beendigung und Nachbereitung

1. **Mishap Report**: Melde am Ende dieses Skills alle aufgetretenen Frictions über `mishap-tracker`.
2. **Operations & Pipeline-Abschluss**: Fahre danach mit `operations-management` fort, um den Status des zugehörigen PRs / Tests zu überwachen (only-if-tickets: bzw. Locks per `agent-lock release` durchzuführen).

## Übergabe — Kreislauf geschlossen

**Zustand nach Schritt 9 (Endzustand des Skills):**
- E2E-Spec `tests/e2e/specs/<neu>.spec.ts` committed + gepusht
- `components/website/src/data/test-inventory.json` aktualisiert
- Tests laufen lokal grün gegen Live-URL

**Kreislauf zurück zu `<repo.main_branch>`** via normalem PR-Merge (oder direkter Push wenn Branch-Protection es erlaubt). Nächste Arbeit startet mit `dev-flow-plan`.

---

## Verwandte Skills

| Skill | Beziehung |
|-------|-----------|
| `playwright-best-practices` | Best Practices für robuste Locators, Fixtures & Anti-Flakiness |
| `code-graph-interpretation` | Test Impact Analysis: Endpunkte & Helper über den K3-Codegraphen tracen |
| `dev-flow-execute` | **Vorgänger im Kreislauf** — Feature muss deployt sein |
| `git-workflow` | Commit/Push-Konventionen für Schritt 7 (Freshness Guard, Scope-Preflight) |
| `infra-ops` | Querschnitt — Infrastruktur- und Service-Status |
| `mishap-tracker` | Abschluss — protokolliert Frictions |
| `operations-management` | Nachbereitung — PRs/Tickets/Locks aufräumen |

## Framework mapping

| Framework | Availability |
|-----------|--------------|
| **Claude Code** | Full — load via `load skill <name>` or matches on description triggers |
| **opencode** | Full — available as a listed skill. All tools (CLI, MCP) are framework-agnostic |
| **agy** | Full — treat the opencode path as authoritative. All CLI tools and MCP calls work identically |
