---
name: unity-testing
description: Run Unity EditMode and PlayMode tests via the Unity CLI or hardened batchmode wrappers, interpret exit codes, and fix headless test traps. Use whenever Unity tests are run, added, filtered, failing, flaky, or gated in CI — EditMode/PlayMode suites, run-unity-tests.sh, NUnit/JUnit reports, coverage, MonoScript rebinding, Time.timeScale leaks, AudioListener log spam, or shared PlayMode fixtures.
---

# Unity Testing

## Repo-Graph zuerst (nur bei Code-Suche)

Suchst oder navigierst du Repo-Code, beginne am zentralen MCP-Hub `fleet-workspace`: `search_graph` → `trace_path` → `get_code_snippet`; Übersicht via `get_architecture`/`query_graph`/`search_code`. Nicht indiziertes Projekt zuerst mit `index_repository` indizieren. Belegpfade mit `check_index_coverage` prüfen und Lücken benennen. `grep`/`rg` nur für nicht-indizierte Nicht-Code-Dateien oder als belegten Fallback. Details: SSOT-Skill `codebase-memory`.

Run Unity tests cheapest-first: EditMode before PlayMode, targeted filters while iterating, full unfiltered suites once per mode on final code. Never re-run a failing suite unchanged; branch on the exit code and (with `--format json`) `errors[0].code`.

## Run tests

If the project ships a hardened batchmode wrapper (e.g., `scripts/run-unity-tests.sh` with `PLATFORMS=EditMode TEST_FILTER=<Class>`), prefer it over raw `unity test` so Editor locking, service stop/restart, stall watchdogs, and MonoScript warm-up apply automatically. See [references/runner-hardening.md](references/runner-hardening.md) for the wrapper architecture.

```bash
# Targeted EditMode iteration via Unity CLI (default NUnit XML; supports --rerun-failed / --affected)
unity test /path/to/Project --mode EditMode --filter "MyNamespace.MyTests" -- -nographics

# Full PlayMode run emitting both NUnit and JUnit reports in one pass
unity test /path/to/Project --mode PlayMode \
  --report-format nunit,junit --junit-output ./artifacts/playmode-junit.xml -- -nographics

# Optional code coverage (requires com.unity.testtools.codecoverage in the project)
unity test /path/to/Project --mode EditMode --coverage --coverage-output ./coverage -- -nographics
```

Useful CLI flags: `--filter <pattern>`, `--affected`, `--rerun-failed`, `--retries <n>`, `--shard <n/m>`, and `--timeout <seconds>`.

- **Report formats:** `--report-format junit` alone produces a JUnit-only file that `--affected` and `--rerun-failed` cannot read. Keep the `nunit` default during iteration or pass `--report-format nunit,junit --junit-output <path>` to produce both from one run.
- **Editor lock discipline:** `unity test` refuses a project open in an Editor. Never kill a user's interactive Editor or run tests during Play Mode. Worktree runs must target the worktree checkout and leave any shared main-checkout warm-editor service untouched (see [references/runner-hardening.md](references/runner-hardening.md)).

## Exit codes

### `unity test` CLI

| Code | Name | Retry? | Meaning |
|---|---|---|---|
| `0` | `SUCCESS` | No | All tests passed |
| `8` | `TESTS_FAILED` | No | Tests ran, some failed — fix code/tests, never blind-retry |
| `6` | `COMMAND_FAILED` | Only after infra fix | Failed without a verdict (compile error, license, crash, bad platform); inspect `errors[0].code` (e.g., `TEST_RUN_ERROR`) |
| `10` | `READY_TIMEOUT` | Yes | Editor did not become ready in time |
| `12` | `EDITOR_UNREACHABLE` | Yes | No Editor answered |
| `14` | `TIMEOUT` | Yes | Hit `--timeout` (`TEST_TIMED_OUT`) |
| `17` | `UNAVAILABLE` | Yes | Editor is loading, compiling, or in Safe Mode — retry later |
| `18` | `AWAITING_INPUT` | Yes | Modal dialog blocks Editor — inspect/answer via `unity command editor dialog`, then retry |

### Hardened batchmode wrapper (`run-unity-tests.sh`)

| Code | Meaning | Retry? |
|---|---|---|
| `0` | All requested suites passed | — |
| `1` | Test failures, missing/invalid XML report, compile error, or process failure | No — fix code/tests |
| `2` | Stall watchdog or hard timeout (infra hang) | Yes |
| `3` | Project locked by a live Unity process | Wait for holder, then retry |

## Headless traps (evidenced in Unity batchmode / `-nographics` suites)

1. **`m_AutoSyncTransforms=0`:** Setting `transform.position` while `CharacterController` is enabled never updates physics/triggers. Fix in the shared fixture: disable `CharacterController`, move, re-enable, then call `Physics.SyncTransforms()`.
2. **`Destroy` applies at frame end:** Kill assertions need `yield return null` before checking destruction (or `Object.DestroyImmediate` in `TearDown`).
3. **`Keyboard.current` is idle headless:** The device exists but receives no OS key events; drive movement/WASD tests via `InputTestFixture` synthetic input.
4. **`AddComponent` + `DontDestroyOnLoad` throws in EditMode:** Guard runtime persistence calls in production code with `Application.isPlaying`.
5. **`LogAssert.Expect` matches exact strings in order:** Keep expected error strings centralized in the shared fixture rather than scattered across test files.
6. **Headless audio (`nosound`) warns per frame & desktop runners beep:** Assert audio dispatch counters/clips instead of logs, and add a `[SetUpFixture]` that toggles a global playback-mute flag in `OneTimeSetUp` / `OneTimeTearDown` so desktop runs stay silent.
7. **Leaked `Time.timeScale = 0` between PlayMode tests:** A test failing between pause/hit-stop and restore leaves `Time.timeScale == 0`, stalling every subsequent game-time wait until the 180 s per-test timeout. Fix: use `[assembly: TestRunCallback(typeof(TestStateGuard))]` (NUnit `ITestAction` does **not** fire for `[UnityTest]` coroutines!) to reset `Time.timeScale = 1f` in `TestStarted`, and enforce a `Time.realtimeSinceStartup` deadline in the shared `WaitSeconds` helper so stalled clocks fail fast.
8. **Missing `AudioListener` floods PlayMode logs:** Test scenes without a listener log `"There are no audio listeners in the scene"` every frame (hundreds of MB). Fix: spawn a persistent `FallbackAudioListener` from `TestRunCallback.TestStarted` that disables its own `AudioListener` in `LateUpdate` whenever another active listener exists.
9. **Copied `Library/` in worktrees unbinds `MonoScript` references:** `MonoScript.GetClass()` silently returns `null` and scene/prefab components load as `null` without warnings. Fix: run a pre-test `LibraryRepair` warm-up session (see [references/runner-hardening.md](references/runner-hardening.md)).
10. **Passing `-quit` with `-runTests` aborts test runs:** Direct batchmode invocations using `-runTests` must omit `-quit`.

## Shared fixture architecture

Keep three small, centralized building blocks per test assembly instead of duplicating helpers across test files:

1. **Static test fixture** (e.g., `DiabloTestFixture`): `TeleportHero` (CC-toggle + `Physics.SyncTransforms`), real-time-bounded `WaitSeconds`, `DestroyAfterFrame`, `CleanupTestScene`, and central `LogAssert` helpers.
2. **Assembly-level `[assembly: TestRunCallback(...)]`** (`ITestRunCallback`): resets `Time.timeScale = 1f` and ensures a `FallbackAudioListener` before every `[Test]` and `[UnityTest]`.
3. **`[SetUpFixture]` audio mute**: disables sound playback in `OneTimeSetUp` and restores it in `OneTimeTearDown`.

Migrate legacy test files onto the shared fixture two files at a time, keeping EditMode and PlayMode suites green after each step.
