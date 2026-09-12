# Interleaved controller watchdog — EDIT-STOP — 2026-09-12

Owned only watchdog, test counterpart and this note. **26 CPU tests PASS, zero skips (0.256s); CLI help PASS.** Fake clock, proc and signaler; actual pidfd system-adapter calls are mocked. No actual signals, native execution, SSH/network/GPU/Git. Frozen driver remains `d100cb58296499c7cd6489d20e96528898f2e48b698147a97dae99fa38946bbe`; frozen tests remain `a87b76a9c49f2e5ed2159bf6b33da8663371a0e9ee294a3c81f362a4dfed494f`.

Files:
- `/tmp/astra_interleaved_controller_watchdog_20260912.py` — SHA256 `c9924b8ff09a046d8a5ec0b41a2cd57a6902650f84c3caab0942213ad93cdd96`
- `/tmp/test_astra_interleaved_controller_watchdog_20260912.py` — SHA256 `5dfc9d4e646acdb36bf45670947f7eec43f53592d27caa998b121c6b986f929d`
- `/tmp/astra_interleaved_controller_watchdog_handoff_20260912.md`

## Main launcher integration — before writing immutable launch.json

Fixed run: `/localhome/local-rohing/astra_diagnostics/astra_interleaved_memory_replay_20260912_attempt1/fits_root0_attempt1`; plan SHA `4cad487a53d0e992b896eb4324ff2de1adb24ccc176856de7043d1132c0ee388`, source `22b7e528f6f62358981ed2264d30ee7242926160`, device1. No alternative PID/run CLI exists.

Keep the existing launch receipt fields unchanged. Add these fields **before its exclusive first write**, not by updating a sealed receipt:

| Field | Actual source |
| --- | --- |
| `pgid` | `/proc/{controller_pid}/stat` field5; must equal PID |
| `proc_start_ticks` | Same stat field22, integer; capture immediately after spawn |
| `controller_started_unix` | `ROOT/run/reservation.json` → `started` |
| `effective_deadline` | Same reservation → `effective_deadline` |
| `reservation_sha256` | SHA256 of exact reservation.json bytes |

Use `start_new_session=True` for the controller. Before recording identity, compare actual `/proc/PID/cmdline` to the **exact** intended command list, retaining the venv executable path and every argument. Importing this standalone watchdog's `Proc().read(pid)`/`parse_stat(bytes)` helpers is safe for Main's launcher; no action runs on import. The watcher also checks UID equals its own UID.

The reservation is created at controller startup before verification or GPU workers. Main may wait for it with a short bounded launcher wait and controller-liveness check. If startup exits/fails before valid pins are available, report the failed launch and reconcile separately; never invent start ticks/deadlines, spawn a replacement automatically, or modify the frozen runner. This watchdog deliberately requires the actual reservation pin, not a guessed launch timestamp. Existing runner/collector accept extra launch metadata fields.

`effective_deadline` must equal actual `controller_started_unix + 1800`, be no later than the plan deadline (Main's22:30Z latest end), and precede the real lease boundary. Launcher wall-clock `started_utc` and reservation start may differ slightly: the watchdog uses the **actual controller reservation** end, not launch-return time or watcher-start time.

## Main commands (not executed here)

```bash
PY="$HOME/v2/venv/bin/python"
WATCH=/tmp/astra_interleaved_controller_watchdog_20260912.py
ROOT="$HOME/astra_diagnostics/astra_interleaved_memory_replay_20260912_attempt1/fits_root0_attempt1"
PYTHONDONTWRITEBYTECODE=1 "$PY" -B /tmp/test_astra_interleaved_controller_watchdog_20260912.py -v
# Main captures LAUNCH_SHA from the exclusive immutable launch.json write.
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 "$PY" -B "$WATCH" \
  --launch "$ROOT/launch/launch.json" --launch-sha256 "$LAUNCH_SHA" \
  --out /tmp/astra_interleaved_controller_watch_20260912_attempt1
```

Run asynchronously under Main's independent launcher/log supervision, outside the controller's process group, with `CUDA_VISIBLE_DEVICES` **absent** (even an empty variable is rejected). Watcher has no GPU reservation, GPU query, model import, worker ownership or cleanup authority. Linux/Python `os.pidfd_open` and `signal.pidfd_send_signal` are mandatory; unsupported runtimes fail closed without fallback. Do not resolve the controller's venv executable symlink when forming its command.

## Exact actions and evidence

- Check immutable launch/plan/runner/reservation bindings at startup and immediately before each possible signal. Recheck PID, process-group ID==PID, start ticks, UID and exact full cmdline before signaling. Opening a pidfd is followed by another identity check. The pidfd prevents PID reuse from redirecting a signal to a replacement process. No numeric `kill`, `killpg`, process-name search or foreign-PID signaling.
- TERM the **individual controller** at effective end−140 (start+1660). KILL that same pinned controller at effective end (start+1800) if it persists. No repeated TERM/KILL, retry, grace reset or budget extension. A late watchdog starts with the already-due action: immediately KILL if the hard end has passed.
- UTC deadlines are anchored to monotonic time at watcher startup; either due clock triggers the action. Backward wall-clock changes cannot postpone an already-anchored deadline; forward changes can trigger earlier. Polling is at most0.2s; actual OS scheduling/syscall latency is recorded, not claimed to be real-time zero latency. A clock error that occurred before startup cannot be independently reconstructed by this process.
- Absent PID, matching zombie (empty zombie cmdline allowed), or exited pinned pidfd yields a successful **controller-exit observation**. Wrong identity/cmdline/UID or changed custody inputs yields failure without further signals. If SIGKILL is sent but the controller remains observable, watch for at most5s then fail honestly; that is observation only, not an execution extension. SIGKILL cannot guarantee immediate death of an uninterruptible kernel task.
- Fresh external watch directory only; no overwrite/reuse/orphan repair. `watch.json` pins contract, watcher hash, clocks and mechanism. Exclusive `term-intent.json`/`kill-intent.json` precede signaling; corresponding result files distinguish sent, process-exited race and signal failure. `terminal.json` records exit observation/failure and attempted actions. Signal delivery is not conflated with exit. Intent/result gaps are partial evidence requiring Main reconciliation.
- Every receipt states `worker_cleanup_verified=False`, `gpu_release_verified=False`, `budget_extended=False`. Main retains the GPU reservation and performs independent worker/full-device release checks. Existing worker parent-loss guards are untouched. A controller death alone proves neither worker cleanup nor GPU vacancy. The watchdog's own liveness is Main's responsibility.

Coverage: exact TERM/KILL timing; early normal/zombie exit; late startup; no deadline reset; PID reuse before/after pidfd opening; PGID/UID/argv/start-tick mismatches; last-moment argv recheck; extra empty argv preservation; immutable receipt mutation; forward/backward clock jumps; failed/stuck KILL; permission/open-exit races; fresh paths/aliases; proc names with embedded parentheses; pidfd-only adapter; missing pidfd support; launch/reservation/plan pins and duplicate JSON rejection.

**EDIT-STOP — Main launches; no signals sent by this author.**
