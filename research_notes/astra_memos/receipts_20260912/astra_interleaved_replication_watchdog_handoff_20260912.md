# Replication watchdog — CPU PASS / EDITSTOP — 2026-09-12

Only the new watcher, its tests, and this handoff are owned/changed. **45 CPU tests PASS, zero skips, 0.744s final run; CLI help PASS.** Mock clocks/processes/pidfds only; no real process read/signaling, native/model/GPU, SSH/network, Git, experiment launch, or repo edits. Short-lived synthetic fixture trees were removed by the tests. No root0 or replication runtime artifacts were inspected. This is author-side implementation validation, not independent raw/scientific review.

| File | SHA256 |
|---|---|
| `/tmp/astra_interleaved_replication_watchdog_20260912.py` | `a2f3bb6b8583994b845c38ea1fcf765c937f4230700f92bfebd512d8f569ac54` |
| `/tmp/test_astra_interleaved_replication_watchdog_20260912.py` | `4282ee39f2756670c3c010e1d0b3c9c333cf8cd710d368f590052affd043b18f` |

Frozen inputs remained unchanged: root0 watchdog `/tmp/astra_interleaved_controller_watchdog_20260912.py` = `c9924b8ff09a046d8a5ec0b41a2cd57a6902650f84c3caab0942213ad93cdd96`; replication driver `/tmp/astra_interleaved_memory_replication_20260912.py` = `dc92b9d18f1fc7e8b9907f304e366de34a5e12340223f8dd17506e007093065f`. The new file is an explicit versioned adaptation, not an import/monkeypatch of either driver. AST comparison verified unchanged pidfd, `/proc` identity/parser, exclusive receipt helpers, and monitor deadline/signaling body after the parameterized output-path preflight.

## CLI and Main integration

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_interleaved_replication_watchdog_20260912.py -v
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 "$WATCH_PY" -B \
  /tmp/astra_interleaved_replication_watchdog_20260912.py \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA256" --launch-sha256 "$LAUNCH_SHA256" \
  --out "$FRESH_WATCH_OUT"
```

`ROOT` is the exact absolute prepared replication root, **not** the material directory. `PLAN_SHA256` and `LAUNCH_SHA256` are Main's independently recorded final byte hashes, not hashes inferred by this watcher. `WATCH_PY` is Main's selected Linux Python with `os.pidfd_open` and `signal.pidfd_send_signal`; no guessed native interpreter path is supplied here. Preserve the controller's `plan.python` venv spelling, even when that executable is a symlink. Do not resolve it. The watcher can use any CWD; it imports only the standard library.

Main's proposed fresh outputs work unchanged: `/tmp/astra_interleaved_replication_watch_seed1_20260912_attempt1` and `/tmp/astra_interleaved_replication_watch_seed2_20260912_attempt1`. One invocation watches one seed/controller; no launcher, retry, automatic progression, or second-seed orchestration is added. Run under Main's independent supervision outside the controller process group, with `CUDA_VISIBLE_DEVICES` **absent**, not empty. An existing/orphan output directory is never reused or overwritten.

Before starting the watcher, Main must finish `ROOT/launch/launch.json`, `ROOT/launch/gpu.xml`, and `ROOT/run/reservation.json`. The launch retains the pinned driver's fields: `seed`, `parent_plan_sha256`, `seed0_gate_sha256`, `plan_sha256`, `script_sha256`, `root`, `source`, `device`, `controller_bound_seconds=1800`, `external_collection_margin_seconds=300`, `generation_calls=224`, `pid`, `gpu.gpu_uuid`, and exact `command`. **Additional watchdog identity fields required:** integer `pgid==pid>1`, positive integer `proc_start_ticks`, `controller_started_unix`, `effective_deadline`, and `reservation_sha256`. Do not hash the launch until these are final. Read start/deadline values from the bound controller reservation; do not substitute the outer launcher's start clock.

The controller command must be exactly `[plan.python, "-B", "/tmp/astra_interleaved_memory_replication_20260912.py", "run", "--source-root", plan.source_root, "--runroot", plan.root, "--allow-gpu"]`. Wrapper argv, additional empty arguments, foreign commands, and seed0/worker PIDs are not accepted. No default device, source pathname, parent pathname, or plan pin is invented.

## Boundaries enforced

- Plan schema `INTERLEAVED_MEMORY_REPLICATION_V1`, integer seed1/2, matching optimizer seed, driver hash, and source identity `22b7e528f6f62358981ed2264d30ee7242926160`. Source path comes from the pinned plan and must equal the launch source; its final directory name must match that identity. Actual device comes from the matching launch/plan single numeric device declaration; the single XML GPU UUID must equal `launch.gpu.gpu_uuid`. Device is not hardcoded or inferred from seed.
- Prepared run is beside material, not inside it, and disjoint from source, model, material, original selected parent, material's parent anchor, and seed0 root. The watch directory is fresh and external to all those roots and custody files. Aliased custody paths, parent traversal, duplicate JSON keys, missing/mismatched files, and invalid initial plan/launch/root fail before any output directory/receipt/stdout result or pidfd open/signal. Diagnostics may appear on stderr. Post-start failures preserve receipts; they do not remove earlier evidence.
- Original parent plan, `fit_teach/verified.json`, and original `readouts/teach/plan.json` hashes must equal the selected seed's frozen three pins, also matching plan provenance and launch parent-plan pin. Their seed, adapter path, adapter-file identity, and embedded readout must agree with the plan. Copied seed0/other-seed parents and replay-descendant adapter paths fail. Only these metadata files are read, not adapter weights.
- Main's explicit bound seed0 gate must say `ALLOW_SEEDS_1_2`, owner `Main`, independent raw-review `PASS`, eligible seeds `[1,2]`, and the pinned progression criteria. Gate file and referenced plan/terminal/validation/review evidence are byte-hashed, with gate root/path identity checked. This is receipt custody, **not a new reduction/gate decision**. The driver owns namespace semantics: habit = `counts.addition.adherence>=30`; ACT = `counts.addition.correct_action>=31`. Swapping progression thresholds is rejected; the watcher does not recompute scores. SINGLE scores do not become a gate.
- SINGLE_VIEW then FOUR_VIEW, panels48/16/48,112 calls/arm,224 total, zero confirmation calls, all captures before reduction, and no outcome-selective skips are checked. The watcher adds no dose/panel/selection change and does not reimplement the native recipe audit.
- Hard end = controller reservation start+1800, no shortening/extension; hard end must be at or before plan deadline, and **hard end+300 <= real lease expiry−21600**. The140s cleanup is inside1800, not added to it. Reservation must agree on seed/device/PID/start/end/plan/real expiry, external custody end, finite nonnegative monotonic start, and continuous reservation. Passing an already adjusted lease cutoff as the real expiry fails the available-window check; actual expiry authenticity remains Main's live responsibility.

## Signaling, evidence, and limits

Immutable launch/plan/driver/reservation/GPU XML/original-parent metadata/gate evidence hashes are rechecked before output and each signal. PID, PGID, start ticks, UID (watcher's UID), and full argv are checked before/after pidfd acquisition and immediately before signaling. **Only the identity-pinned controller pidfd** receives TERM at hard end−140 and, if still present, KILL at hard end. No numeric-PID fallback, process-group signal, foreign PID search, worker signal, or GPU-group cleanup exists. Linux pidfd unavailability fails closed. Late startup uses the already-due action without resetting grace.

UTC deadlines are anchored to monotonic time at watcher startup; either due clock triggers. Polling is at most0.2s; filesystem hashing/syscall/OS scheduling latency is not a real-time guarantee. As in the frozen watcher, clock error before startup is not independently reconstructed. SIGKILL may not immediately end an uninterruptible kernel task. At most5s post-KILL observation is permitted, with no repeated signal or runtime extension.

`watch.json` records the full bound contract/seed/device/UUID/parent/gate/custody pins, watcher hash and clocks. Exclusive `term-intent.json`/`kill-intent.json` precede action, with corresponding result receipts afterward; `terminal.json` distinguishes exit observation, signal failure and persistent controller. PID absence, matching zombie or exited pinned pidfd proves only a controller-exit observation. Intent/result gaps require Main reconciliation. Every terminal receipt explicitly reports `worker_cleanup_verified=False`, `gpu_release_verified=False`, `budget_extended=False`.

Tests cover both seed/device combinations end-to-end with synthetic launch/plan/parent/gate/XML/reservation, separate rehashed negative mutations, copied parent/readout identities, lease boundary equality and shortfall, venv spelling, argv empties/wrappers, aliases/overlapping roots, all custody-file mutations, PID reuse and last-moment identity changes, clock jumps, TERM/KILL timing, pidfd exit/open races, permissions, stuck KILL, and fresh-output refusal. No live runtime outcome, authentic lease/device observation, whole source tree, weight tensors, or native corpus/tokenizer audit was verified here. Main retains native preflight, watcher liveness, worker/full-GPU release checks and bounded300s collection; these are not inferred from watcher PASS. Scientific scope remains authored-material memory+habit repeatability, not parenting/G3/mechanism freeze.

**EDITSTOP — these three deliverables are handed to Main; no launch or real signal executed.**
