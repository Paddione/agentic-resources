---
name: vitest-testing
description: Vitest-Runner konfigurieren, prüfen, laufen lassen und debuggen — Config, vi-API, Pools, Coverage, Browser Mode, hängefreier Agent-Betrieb. Trigger: vitest.config, vi.mock, vi.useFakeTimers, expect.poll, toMatchInlineSnapshot, test.extend, projects, pool, browser.instances, toMatchScreenshot, "*.test-d.ts", import.meta.vitest, veraltete Config-Keys. Testinhalt gehört zu vitest, strategieübergreifende Qualität zu sota-testing, Journeys und Server-Lebenszyklus zu e2e.
user-invocable: false
---

# Vitest Testing

Vitest-Suite konfigurieren, starten, debuggen, reviewen: Config-Datei, vi-API, Pools, Reporter, Coverage-Provider, Browser Mode. Dazu Regeln für hängefreie, kontextsparsamer Runs.

Runner-Schicht, keine Inhaltsschicht: Was zu prüfen ist, Spec-Namen, Fixture-Qualität gehören zu `vitest` bzw. `sota-testing`. Journeys, Locator-Hierarchie, Server-Lebenszyklus gehören zu e2e, Test-Hook-Konventionen (z. B. data-testid) zur Component-Fähigkeit. Anderer Runner heißt andere Fähigkeit.

Versionshaltung lookup-first: verifiziert gegen Vitest 4.1.10 (Node >= 20, Vite >= 6). Vitest 4 hat ca. zwei Dutzend Optionen verschoben/entfernt und ignoriert alte Namen still — v3-Antworten aus dem Netz laufen grün und wirken nicht. Maßgeblich ist die Doku der installierten Version unter <https://vitest.dev>; jede Referenz unten nennt ihre Upstream-Seite.

Falls references/stable-version-policy.md vorhanden: vor jeder Runner-Empfehlung lesen, neueste stabile Version über npm-`latest`-Dist-Tag auflösen und deren Doku konsultieren; die 4.1.10-Baseline unten gilt dann nicht als aktuell.

Repo-Anpassung per repo.yaml: Main-Branch (repo.main_branch), Scopes (repo.scopes), Tickets (repo.tickets), Task-Runner (repo.task_runner), generierte Artefakte (repo.generated_artifacts). Skill-Verweise (vitest, sota-testing) per Name auflösen, keine festen Pfade voraussetzen.

Schlüsselwörter MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, MAY, OPTIONAL nach [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.html).

## Agent-Betrieb

Siehe [running-as-an-agent.md](./references/running-as-an-agent.md):

- jeder nicht-interaktive Run mit `vitest run` oder `--no-watch`; nacktes `vitest` ist Watch Mode und kehrt nie zurück
- Projekt-`test`-Script als `vitest` oder `vitest --watch` vererbt diesen Hang
- Eingrenzen per Pfad, `-t`, `file.test.ts:42`, `--project`, `--changed`, `--related`
- `minimal`-Reporter für Token-Kosten; eigenes `reporters`-Array schaltet dessen Auto-Wahl ab
- Diff und Stackframe lesen statt Suite erneut laufen lassen
- Vitest-MCP-Server von Dritten nur mit Freigabe

## Versionsdisziplin

Siehe [version-discipline.md](./references/version-discipline.md):

- Vitest 4 ignoriert unbekannte `test`-Keys statt zu fehlen; v3-Option läuft grün und tut nichts
- `workspace` zu `projects`, `maxThreads`/`maxForks` zu `maxWorkers`, `singleThread` zu `maxWorkers: 1` plus `isolate: false`
- `poolOptions.*` auf Top-Level abgeflacht, `deps.external`/`inline` zu `server.deps.*`
- entfernt: `coverage.all`, `environmentMatchGlobs`, `poolMatchGlobs`, `minWorkers`, `basic`-Reporter
- `getMockName()` liefert `"vi.fn()"`; Snapshots mit Mocks neu schreiben
- Feature-Grenzen 4.1.0, 4.1.1, 4.1.3, 4.1.4: Tags, Fixture-Builder, eigene Snapshot-Matcher, ARIA-Snapshots

## Konfiguration

Siehe [configuration.md](./references/configuration.md):

- `defineConfig` aus `vitest/config`, nicht aus `vite` (typisiert sonst `test`-Block nicht)
- v4-Default-Excludes nur `node_modules`, `.git`; `dist` ohne Exclude gescannt
- Haltung: `globals: false` mit expliziten Imports; `globals: true` braucht `vitest/globals`-Typen
- `clearMocks`, `mockReset`, `restoreMocks`, `unstubEnvs`, `unstubGlobals` als Config statt Hook-Disziplin
- `testTimeout` 5.000 ms; engste Ebene erhöhen (pro Test, `hookTimeout`)
- `dangerouslyIgnoreUnhandledErrors` schaltet echte Prüfung ab; `experimental`-Block eigene Risikoklasse

## Testprojekte

Siehe [test-projects.md](./references/test-projects.md):

- `projects` als einziger Mechanismus; ersetzt `workspace`, `poolMatchGlobs`, `environmentMatchGlobs`
- Glob-, Pfad- und Inline-Einträge, `!`-Negation, `packages/!(business)`-Idiom
- Namensregel `vitest.config.*` / `vitest.<name>.config.*` für Erkennung
- keine Root-Vererbung; `extends: true`, `mergeConfig` oder geteilte Setup-Files
- `coverage`, `reporters`, `resolveSnapshotPath` prozessweit, daher in Projekten unzulässig
- Trennung node/Browser oder Unit/Integration mit eigener Isolation

## Umgebung

Siehe [environments.md](./references/environments.md):

- `node`, `jsdom`, `happy-dom`, `edge-runtime`; DOM-Startkosten pro Datei
- `// @vitest-environment jsdom`-Docblock für einzelne Dateien statt Suite
- CSS-/Asset-Import unter DOM-Shim erst mit ganzer Kette in `server.deps.inline`
- `viteEnvironment` als v4-Ersatz für `transformMode`
- "läuft unter jsdom, bricht im Browser" heißt Browser Mode statt weiter stubben

## Run-Lebenszyklus

Siehe [run-lifecycle.md](./references/run-lifecycle.md):

- `globalSetup` im Hauptprozess mit eigenem Scope; nur `provide`/`inject` überquert ihn
- `setupFiles` im Worker; daher Mock-Registrierung und `expect.extend` dorthin
- Setup-Files unter `isolate: false` erneut laufend bei gecachten Modulen
- `globalSetup` im Watch Mode ohne Re-Run; Seed-State bleibt
- `forceRerunTriggers`, `watchTriggerPatterns` für nicht-importierte Dateien

## Test-API

Siehe [test-api.md](./references/test-api.md):

- Testoptionen im zweiten Argument; v3-Drittargument entfernt und ungelesen
- `skip`, `skipIf`, `runIf`, `only`, `todo`, `fails`, `concurrent`; `sequential` veraltet
- `test.each` spreizt Array-Fälle, `test.for` nicht und liefert Testkontext
- `aroundEach`/`aroundAll` brauchen `runTest`-Aufruf
- `onTestFinished`/`onTestFailed` als Cleanup pro Test, konkurrenzfest
- `retry` mit Fehlerprädikat für eine Fehlerart statt alle

## Fixtures und Kontext

Siehe [fixtures-and-context.md](./references/fixtures-and-context.md):

- `context.expect` für Snapshots in parallelen Tests Pflicht
- 4.1-`test.extend`-Builder mit Typinferenz; `onCleanup` einmal je Fixture
- Scopes Test, Datei, Worker; Zugriff nur gleich oder langlebiger
- nur destrukturierte Fixtures initialisiert (`{ database }` ungleich `context.database`)
- `test.override` für Suite-Werte, `injected`-Fixtures aus `config.provide` je Projekt

## Assertions und Async

Siehe [assertions-and-async.md](./references/assertions-and-async.md):

- `toEqual` vs. `toStrictEqual` nur bei present-`undefined`-Key und Sparse-Array verschieden
- `objectContaining`, `stringMatching`, `closeTo`, `schemaMatching` (Standard Schema)
- `.resolves`/`.rejects` ohne await scheitern in v4, in v3 still bestanden
- `vi.waitFor` vs. `vi.waitUntil` vs. `expect.poll`; `expect.poll` ohne Snapshots, `.rejects`, `toThrow`
- `expect.hasAssertions()` für Assertions in Callbacks
- `expect.extend`-`MatcherResult`; `pass`-Verzweigung auf `isNot` hebt sich auf

## Funktions-Mocks und Spies

Siehe [function-mocks.md](./references/function-mocks.md):

- Spy sieht nur Calls nach Installation; Importzeit unsichtbar
- `mockClear` behält Implementierung, `mockReset` stellt Original wieder her, `mockRestore` Deskriptor
- `clearAllMocks`/`resetAllMocks`/`restoreAllMocks` erreichen Automocks nicht
- `mockThrow`/`mockThrowOnce`, `withImplementation`, `Once`-Varianten für Sequenzen
- `invocationCallOrder` ab 1 in v4; Mock-Matcher statt `mock.calls` lesen
- `vi.defineHelper` für Helfer mit Caller-Zeile

## Modul-Mocking

Siehe [module-mocking.md](./references/module-mocking.md):

- `vi.mock` gehoistet über Imports; `const` auf Modulebene beim Factory-Lauf undefined
- `vi.hoisted` für Factory-Closure-Werte; `importOriginal` mit await
- Automock leert Arrays, gibt undefined zurück; `{ spy: true }` behält Verhalten
- `__mocks__` inert bis `vi.mock`-Aufruf das Modul nennt
- Calls zwischen Funktionen derselben Datei nicht mockbar; Refactor Extrahieren/Injizieren
- `server.deps.inline` wenn `vi.mock` gegen externalisierte Dep wirkungslos

## Timer und Ambient State

Siehe [timers-and-ambient-state.md](./references/timers-and-ambient-state.md):

- installierte Fake-Clock leaked in spätere Files desselben Workers
- `*Async`-Advance-Varianten sobald Callback awaitet
- `runAllTimers` wirft bei `loopLimit` auf selbst-nachplanenden Code
- `vi.setSystemTime` friert driftende Snapshots ein; `TZ` steuert Format-Ausgabe
- `vi.stubGlobal`/`vi.stubEnv` persistent ohne `unstubGlobals`/`unstubEnvs`
- `memfs` über `__mocks__/fs.cjs` plus `__mocks__/fs/promises.cjs`, beide Specifier mocken

## Netzwerk-Mocking

Siehe [network-mocking.md](./references/network-mocking.md):

- mit MSW intercepten statt `fetch` ersetzen; Request-Pfad bleibt real
- `server.listen()` / `resetHandlers()` / `close()` über beforeAll, afterEach, afterAll
- `onUnhandledRequest: "error"` stoppt echte Netz-Calls bei unmatched Requests
- e2e will die echte Dependency

## Snapshots

Siehe [snapshots.md](./references/snapshots.md):

- inline für reviewbare Werte, `.snap` für größer, File-Snapshots für Markup, ARIA für Struktur
- Fehler als `[Error: message]`, nicht bloße Nachricht
- `-u` mit `new`, `all`, `none`; `--update=new` lässt bestehende in Ruhe
- CI schreibt keine Snapshots; fehlender schlägt fehl
- obsolete Snapshots schlagen in CI fehl; fängt gelöschte Tests mit Rest-Output

## Coverage

Siehe [coverage.md](./references/coverage.md):

- `@vitest/coverage-v8`, `@vitest/coverage-istanbul` in v4 explizit installieren
- nur importierte Files berichtet ohne `coverage.include`-Globs
- `autoUpdate` schreibt Thresholds neu; Drops recorded statt rejected
- Ignore-Hints mit `-- @preserve`, sonst entfernt esbuild sie
- `DEBUG=vitest:coverage` wenn Sammlung selbst langsam

## Performance und Parallelität

Siehe [performance-and-parallelism.md](./references/performance-and-parallelism.md):

- Files über Worker vs. Tests in File; Slowdown erst Achse zuordnen
- `forks` kompatibler Default; `threads` mit Worker-Abbrüchen und Segfaults
- `isolate: false` größter Gewinn; Überlebens-State beachten; `vmThreads` verbietet es
- Concurrency hilft nur wartenden Tests; sync Tests teilen einen Thread
- erst Transform-, Collect-, Setup-, Env-Timings lesen, dann drehen
- Sharding teilt Files statt Fälle; eine langsame Datei nicht shardbar

## Filter und Tags

Siehe [filtering-and-tags.md](./references/filtering-and-tags.md):

- Positions-Pfadfilter, `-t`, `file.test.ts:10` braucht vollen Dateinamen
- `allowOnly`-Default lässt CI mit `.only` scheitern
- Tags vor Nutzung in Config deklarieren; `timeout`, `retry`, `priority` je Tag
- `--tags-filter` mit `and`/`or`/`not`, Wildcards, Präzedenz `not` vor `and` vor `or`
- `@module-tag` für ganze Datei
- Filter je File; Vitest lädt dennoch alle Files zur Match-Suche

## Reporter und CI-Ausgabe

Siehe [reporters-and-ci.md](./references/reporters-and-ci.md):

- `minimal` (Alias `agent`) nur Failures und Fehler
- Auto-Wahl bei `std-env`-Agent-Erkennung oder `AI_AGENT`-Variable
- eigenes `reporters`-Array umgeht Erkennung; `github-actions` dann explizit listen
- `blob` mit `--shard`, gemergt per `--merge-reports`, einzige korrekte Shard-Reportform
- `outputFile` als Pfad oder Map je Reporter
- `context.annotate`-Schweregrade; Default-Reporter nur bei failed Tests

## Browser Mode

Siehe [browser-mode.md](./references/browser-mode.md):

- CSS-Layout, Computed Styles, echte Events als DOM-Shim-blinde Bugklasse
- v4-Provider als Objekte aus `@vitest/browser-playwright`, `-webdriverio`, `-preview`, keine Strings
- Imports aus `vitest/browser`; `@vitest/browser/context` entfernt
- `await expect.element(...)` als retrying Assertion; sync-`expect` nicht
- `userEvent` aus `vitest/browser` für echten Input, nicht Testing-Library-Events
- `alert`/`confirm` blockieren Thread; versiegelte ESM-Namespaces brauchen `{ spy: true }`

## Visuelle Regression

Siehe [visual-regression.md](./references/visual-regression.md):

- `toMatchScreenshot` schreibt Referenz beim Erstlauf und scheitert; in `__screenshots__/` committen
- `allowedMismatchedPixelRatio` vs. `allowedMismatchedPixels`; strengeres Limit gewinnt
- Stable-Erkennung bis zwei Frames übereinstimmen
- Fonts, GPU, Headless lassen lokal vs. CI differieren
- `toMatchAriaSnapshot` für A11y-Baum statt Pixel; fontrobuster

## Typ- und In-Source-Tests

Siehe [types-and-in-source.md](./references/types-and-in-source.md):

- `*.test-d.ts` mit `expectTypeOf`/`assertType`, nur unter `--typecheck`
- Typtests analysiert statt ausgeführt; `test.each`-Name nie evaluiert
- `import.meta.vitest` mit `includeSource`; `"vitest/importMeta"` in tsconfig-Types
- Prod-Build mit `define: { "import.meta.vitest": "undefined" }`, sonst Tests im Ship
- In-Source nur für kleine Utilities, nicht Komponenten/e2e

## Debug und Fehlermodi

Siehe [debugging-and-failure-modes.md](./references/debugging-and-failure-modes.md):

- `--inspect-brk --no-file-parallelism --test-timeout=0` gemeinsam, je Flag eine Blockade weniger
- `--isolate false` hält Debugger über Watch-Reruns
- `hanging-process`-Reporter und `--detect-async-leaks` bei nicht endendem Run
- `Failed to Terminate Worker` durch Node-`fetch` unter `threads`; Fix `forks`
- Segfaults nativer Module unter `threads`; gleicher Fix
- `Cannot find module` bei unaufgelöstem Alias; `ssr.resolve.conditions` für Export-Conditions

## Suite-Hygiene

Siehe [suite-hygiene.md](./references/suite-hygiene.md):

- `expect-expect`, `no-focused-tests`, `valid-expect` aus `@vitest/eslint-plugin`
- `allowOnly` plus Obsolete-Snapshot-Failures als Guards gegen liegengebliebene Edits
- `restoreMocks`/`unstubEnvs`/`unstubGlobals` statt Autor-Disziplin
- `--detect-async-leaks` für Handles über Testende hinaus
- CI ruft `vitest run` ohne Watch-Form; geänderte Config-Keys gegen installierte Version prüfen

## Erweitern

Siehe [extending-vitest.md](./references/extending-vitest.md):

- entfernte v3-Reporter-Hooks (`onCollected`, `onTaskUpdate`, `onFinished`) still, kein Fehler
- `viteEnvironment` in eigener Umgebung; v4-Pool-Interface neu
- `startVitest`, `createVitest`, `vitest.state.getTestModules()` aus `vitest/node`
- `experimental.openTelemetry` braucht `sdkPath` mit ungestartetem SDK als Default-Export
- Tracing-Kosten pro Worker außer bei nicht-isoliertem Run
