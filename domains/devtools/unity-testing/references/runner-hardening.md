# Hardened Unity Test & Build Runners

Reference patterns for batchmode Unity test and build wrappers, derived from production CI and local multi-session setups (`run-unity-tests.sh`, `run-unity-build.sh`, `unity-editor-lock.sh`, `unity-warmup.sh`, `unity_test_report.py`).

## 1. Machine-Wide Editor Serialization (`flock`)

Every Editor-owning run (builds, warm-ups, EditMode/PlayMode suites across main and worktree checkouts) queues on a single machine-wide lock file (for example `/tmp/<project>-editor.lock`) via `flock`.

- Export a guard variable (e.g., `UNITY_EDITOR_LOCK_HELD=1`) once acquired so nested helper invocations (such as a pre-test warm-up script calling the build wrapper) skip re-acquiring the lock and avoid self-deadlock.
- Keep all lock acquisition/release and watchdog logic in one shared shell library sourced by both test and build wrappers.

## 2. Warm-Editor Service Discipline (Main vs. Worktree)

When a persistent headless Editor service (e.g., a `systemd --user` unit backing the project's MCP relay) holds the main checkout:

- **Main checkout runs:** Stop the service before launching the batchmode run and restart it in an `EXIT` trap so it cannot block the project lock or race over `Library/`. Always run `systemctl --user reset-failed <service>` before `systemctl --user start <service>` — a `KillSignal=SIGKILL` stop leaves the unit in `failed` state, which plain `start` will not revive.
- **Worktree runs:** Target the worktree's own project path and leave the shared main-checkout service untouched so active MCP sessions on the main checkout are not evicted.

## 3. Live-Holder vs. Stale Lockfile Gate

Before invoking Unity:

1. Check `<project>/Temp/UnityLockfile`.
2. Probe live processes (`pgrep -f "Unity.*-projectPath <project>"`, excluding the wrapper's own PID/PPID).
3. If a live holder exists, refuse immediately with exit `3` — never kill a user's interactive Editor or another active batch run.
4. If no live holder exists, delete the stale lockfile and proceed.

## 4. Never Pass `-quit` with `-runTests`

Direct batchmode test runs (`-batchmode -nographics -runTests -testPlatform <Mode> -testResults <xml>`) must omit `-quit`. Unity exits automatically once `-runTests` writes the result XML; passing `-quit` terminates the Editor before tests finish or write results.

## 5. CPU-Aware Stall Watchdog & Waiter Reaping

Log silence alone (e.g., `UNITY_STALL_S=600`) produces false positives when a healthy suite is CPU-bound under load without printing log lines.

- Record the active Unity PID and log path in `<lock>.owner`.
- Print a periodic heartbeat (every `60 s`) showing elapsed time, log silence duration, and the last log line.
- When log silence crosses `UNITY_STALL_S`, sample cumulative user+sys CPU time across the entire process tree (`/proc/<pid>/stat` + descendants) over a probe window (e.g., `15 s`):
  - Tree CPU `>= 3 s`: slow, not stuck — grant a fresh stall window (still bounded by the hard timeout, e.g., `1500 s`).
  - Tree CPU `< 3 s` (or unreadable): stalled — send `TERM` to the tree, `KILL` after `10 s`, remove the owner record, and exit `2`.
- Waiters polling `flock` (every `30 s`) inspect `<lock>.owner`, verify PID + cmdline match the log path against PID reuse, and reap an orphaned or stalled lock holder using the same CPU-aware check.

## 6. Shutdown Hang & Post-Success Crash Tolerance (Batch Builds)

Batchmode `-executeMethod` builds can hang indefinitely during Editor shutdown or exit with a signal (`>= 128`, e.g., `136` / `SIGFPE`) after writing all build artifacts. If the build log already contains both the explicit success marker and `Batchmode quit successfully invoked` (or hits the stall/hard timeout after the success marker), treat the build as succeeded (`exit 0`).

## 7. Pre-Test Compile & MonoScript Rebind Warm-Up

Copying `Library/` from the main checkout into a worktree can cause the first asset refresh to leave `MonoScript.GetClass()` returning `null` for scripts under `Assets/Scripts` — scenes and prefabs then load those components silently as `null` with no missing-script warning.

- Run a pre-test compile-check session before `EditMode`/`PlayMode` runs (skippable via an opt-out env like `UNITY_TESTS_SKIP_WARMUP=1`).
- Inspect `AssetDatabase.FindAssets("t:MonoScript", new[] { "Assets/Scripts" })`; if any `MonoBehaviour`/`NetworkBehaviour` script has `GetClass() == null`, run `AssetDatabase.ImportAsset("Assets/Scripts", ImportAssetOptions.ImportRecursive | ImportAssetOptions.ForceUpdate)`.
- Because the rebinding only takes effect on the next Editor launch, loop up to 2 warm-up sessions until the check logs `"scripts bound"`.

## 8. Filtered Runs & Readable NUnit XML Summary

- Expose fast iteration filters in the wrapper: `PLATFORMS=EditMode`, `TEST_FILTER=<ClassOrRegex>` (`-testFilter`), and `TEST_CATEGORY=<Category>` (`-testCategory`).
- Summarize the NUnit XML after each platform run with a small parser script (`unity_test_report.py`): print pass/total/failed/skipped counts, every failing test name + first `Assets/` stack frame + message lines, and the `N` slowest tests (append to `$GITHUB_STEP_SUMMARY` in CI). Use `--allow-empty` only when filters are active so an unfiltered empty run fails closed.
