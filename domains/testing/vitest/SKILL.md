---
name: vitest
description: Tests mit Vitest schreiben, mocken, Coverage konfigurieren, filtern und Fixtures nutzen. Testinhalt und -struktur; Runner-Fragen (Config-Keys, vi-API, Pools, Coverage, Browser Mode) gehören zu vitest-testing.
metadata:
  author: Anthony Fu
  version: "2026.9.25"
  source: Generated from https://github.com/vitest-dev/vitest, scripts located at https://github.com/antfu/skills
---

Vitest ist ein Vite-natives Testframework mit Jest-kompatibler API, ESM-, TypeScript- und JSX-Support ohne Konfiguration. Nutzt Config, Transformer, Resolver und Plugins der Vite-App.

Stand: Vitest 5.0.1, generiert 2026-09-25. Runner-Themen (verschobene Config-Keys, vi-API, Pools, Coverage-Provider, Browser Mode, hängefreie Runs) gehören zu `vitest-testing`; dieser Skill besitzt Testinhalt und -struktur.

Repo-Anpassung per repo.yaml: Scopes (repo.scopes), Task-Runner (repo.task_runner), generierte Artefakte (repo.generated_artifacts). Falls ein Repo eigene Teststrategie- oder Setup-Skills definiert, gelten diese vorrangig; keine festen Skill-Pfade voraussetzen.

## Core

| Topic | Description | Reference |
|-------|-------------|-----------|
| Configuration | Vitest- und Vite-Config-Integration, defineConfig | [core-config](references/core-config.md) |
| CLI | CLI-Befehle und Optionen | [core-cli](references/core-cli.md) |
| Test API | test/it, Modifier skip, only, concurrent | [core-test-api](references/core-test-api.md) |
| Describe API | Gruppierung mit describe/suite | [core-describe](references/core-describe.md) |
| Expect API | Matcher toBe, toEqual, asymmetrische Matcher | [core-expect](references/core-expect.md) |
| Hooks | beforeEach, afterEach, beforeAll, afterAll, aroundEach | [core-hooks](references/core-hooks.md) |

## Features

| Topic | Description | Reference |
|-------|-------------|-----------|
| Mocking | Funktionen, Module, Timer, Daten mit vi | [features-mocking](references/features-mocking.md) |
| Snapshots | toMatchSnapshot, Inline-Snapshots | [features-snapshots](references/features-snapshots.md) |
| Coverage | Coverage mit V8 oder Istanbul | [features-coverage](references/features-coverage.md) |
| Test Context | Fixtures, context.expect, test.extend | [features-context](references/features-context.md) |
| Concurrency | Parallele Tests, Sharding | [features-concurrency](references/features-concurrency.md) |
| Filtering | Filter nach Name, Datei, Tags | [features-filtering](references/features-filtering.md) |
| Test Tags | Tests labeln, Runs filtern, Optionen teilen | [features-test-tags](references/features-test-tags.md) |
| Reporters | Reporter, Standardauswahl, CI-Ausgabe | [features-reporters](references/features-reporters.md) |
| Benchmarking | Benchmarks mit bench-Fixture (Tinybench) | [features-benchmarking](references/features-benchmarking.md) |

## Advanced

| Topic | Description | Reference |
|-------|-------------|-----------|
| Vi Utilities | mock, spyOn, Fake-Timer, hoisted, waitFor | [advanced-vi](references/advanced-vi.md) |
| Environments | node, jsdom, happy-dom, eigene | [advanced-environments](references/advanced-environments.md) |
| Type Testing | Typtests mit expectTypeOf, assertType | [advanced-type-testing](references/advanced-type-testing.md) |
| Projects | Multi-Projekt-Workspaces, Configs je Projekt | [advanced-projects](references/advanced-projects.md) |
