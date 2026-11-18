---
name: unity-testing
description: Run Unity EditMode and PlayMode tests via the Unity CLI, harden the test runner, and fix headless test traps. Use whenever Unity tests are run, added, failing, or gated in CI — EditMode/PlayMode suites, test runner scripts, coverage reports, or flaky headless failures. Use for test loop discipline, exit-code semantics, and shared test fixtures.
---

# Unity Testing

Test Unity projects through the CLI, cheapest test first. All exit codes below were verified against the live CLI exit-code table this session — branch on the exit code, then on `errors[0].code` in JSON.

## Run tests

```bash
unity test /path/to/MyProject --mode EditMode --report-format junit --coverage
unity test /path/to/MyProject --mode PlayMode --report-format junit --coverage
```

Iterating on a change, not gating a pipeline? Run the cheapest test that can fail for the change. Try EditMode first. Use `--filter`, `--affected` or `--rerun-failed` while working. Run the full suite on the final code, once per mode. Never re-run a suite on unchanged code unless the run exited without a verdict.

`unity test` refuses a project that is open in an Editor: do not close the user's Editor to make room, and do not test while they are in Play Mode. Stop the warm-editor service for batch runs and restart it after (see `run-unity-build.sh` lock/stop/restart discipline).

## Exit codes (live table)

| Code | Meaning | Retry? |
|---|---|---|
| 0 | Success, all tests passed | — |
| 8 `TESTS_FAILED` | Tests ran, some failed — report to developers | Never re-run blindly |
| 6 `COMMAND_FAILED` | Failed without a verdict | Safe to retry after fixing infra |
| 10 `READY_TIMEOUT` | Editor did not become ready | Retry |
| 12 `EDITOR_UNREACHABLE` | No Editor answered | Retry |
| 14 `TIMEOUT` | Operation timed out | Retry |

`--report-format junit` makes `--output` a JUnit-schema report for CI ingestion; it is written even when tests fail. `--affected` and `--rerun-failed` cannot read the JUnit-only report — keep the NUnit default for those runs.

## Headless traps (all evidenced in unity-sandbox suites)

- `m_AutoSyncTransforms=0`: teleports via `transform.position` never reach physics. Fix in the test: disable `CharacterController`, move, `Physics.SyncTransforms()`, re-enable.
- `Destroy` applies at frame end: kill asserts need `yield` (a skipped wait once cost 6 s).
- `Keyboard.current` exists but is idle headless: WASD tests need synthetic input via `InputTestFixture`.
- `AddComponent` + `DontDestroyOnLoad` in EditMode throws immediately: guard production code with `Application.isPlaying`.
- `LogAssert.Expect` matches exactly, order included: keep expected strings central in the shared fixture.
- Headless audio (`nosound`) warns per frame: assert dispatch/counters, not logs.

## Shared fixture

Keep one shared fixture per project (teleport helper with CC-toggle + sync, destroy-yield helper, keyboard fixture, log-noise filter, LogAssert policy) instead of per-file duplicates. Migrate files onto it two at a time with suites green after each.
