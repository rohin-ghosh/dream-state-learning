# Outer memory-pair launcher custody review — EDITSTOP

September13,2026. Bounded mock CPU review only. Owned files are the new test
and this handoff. No production source, plan, live root, source archive,
native preparation, collector, GPU state or launched process was changed or
queried. The existing13memory-runner tests were not duplicated or rerun.

## Source and test pins

- Frozen reviewed production source `/tmp/astra_memory_pairs_main_20260913.py`:
  `5df4a3c00016ad07305658e2febc642a1182d1944106d70b92b463235ede2dbe`.
  Checked before test import and rechecked unchanged after the suite.
- Owned `/tmp/test_astra_memory_pairs_main_20260913.py`:
  `ea93484df0d743b7e4235e09fe02ea78cf62a55e9c0c766187ab6a3070129164`.
- Owned `/tmp/astra_memory_pairs_main_20260913_review_handoff.md`:
  digest supplied separately, avoiding self-reference.

Command run once:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s /tmp \
  -p test_astra_memory_pairs_main_20260913.py -v
```

**13tests PASS in0.035seconds.** Owned test AST/whitespace checks also pass.
All module-loading boundaries, environment-reservation checks, GPU checks,
process creation/wait and process-identity lookup are mocked. File receipts
use isolated temporary directories, not native/spec/launcher/live paths.
Tests exercise the frozen wrapper's actual launch/hold/write code. No models
or original prepared roots are loaded. The import has no CLI side effects.

## Covered behavior

1. All3seed launches use the intended GPU index/UUID and a separate holder
   session; command launches `hold`, not the memory controller directly.
   Holder receives its GPU UUID in CUDA_VISIBLE_DEVICES; the launch caller's
   environment remains unchanged. Reservation, XML GPU vacancy and allocation
   checks occur before spawn. Plan pin/identity/status are retained in the
   `LAUNCHED_NOT_RESULT` receipt; launcher does not wait or claim completion.
2. For all3seeds, the holder keeps its GPU UUID in its own environment while
   the controller subprocess receives CUDA_VISIBLE_DEVICES="". The reservation
   is still visible during the mocked blocking wait. `controller.json` exists
   before wait; `exit.json` appears only after wait returns. Controller remains
   in the holder's process group (no new session requested at that boundary).
3. Nonzero controller exit7 is preserved in exit.json and propagated through
   SystemExit7, not changed into success. Incorrect holder CVD or runner hash
   fails before spawning the controller.
4. Reservation exception, occupied GPU and failed boot/lease allocation check
   each prevent spawn. Already-created precheck/claim/failure evidence remains.
   Retrying the same claimed path fails rather than overwriting failure bytes.
5. Popen failure retains precheck and stdout log, with
   controller_may_be_running=false. Identity-read failure or launched-receipt
   write failure after spawn records controller_may_be_running=true; wrapper
   neither falsely reports no process nor kills a potentially running process.
6. Existing controller_started.json or launcher directory prevents duplicate
   spawn; existing contents remain. Roster-pin/plan-verification failure before
   claim creation produces no new claim or process.
7. Paused/interrupted holder wait is tested separately from a nonzero child
   exit: see the limitation below. No synthetic success or release is inferred.

## Bounded finding: exceptional holder termination

The normal launch/hold protocol and pre-spawn failure preservation pass these
fixtures. This is not full exceptional-process custody approval. The frozen
`hold` has a bare `process.wait()` and no try/finally or exception receipt.
Injected wait OSError propagates and leaves controller.json intact but produces
neither exit.json nor failure.json. There is also no outer wait timeout; the
3600second bound is provided by the memory controller, not independently by
this holder. A holder write failure immediately after controller spawn is
likewise not handled by a holder-level failure recorder (source inspection;
not a separate injected regression here).

Main must treat missing exit.json as unresolved, not completed/released, and
reconcile the recorded controller PID/process group and live allocation before
reusing the GPU. Post-spawn launcher failures already carry an explicit
may-be-running flag, but may lack launched.json if identity/receipt writing
failed; preserve the launcher directory/stdout and avoid automatic retry.
Abrupt holder death, real signals, filesystem exhaustion, PID races, scheduler
coordination and native `/proc` visibility are not certified by mocks.

No production repair was made or proposed as necessary to rewrite the frozen
run. If Main later wants stronger exceptional-exit reporting/watchdog behavior,
that is a separately owned versioned change, not covered by this source pin.
These findings do not alter the memory protocol, prepared plans, scientific
claims or Main's allocation/launch authority.

EDITSTOP. Main owns interpretation of current live status; this sidecar did
not monitor, launch, stop or collect any native process.
