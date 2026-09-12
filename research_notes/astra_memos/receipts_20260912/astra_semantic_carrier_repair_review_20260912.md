# R1 repair re-review — 2026-09-12

**Recommendation: ACCEPT the R1 repair within the explicitly accepted DEV scope. No remaining blocking R1 defect identified by code inspection.** This is a safety recommendation, not launch authorization or a C11 gate. Main owns selection, current CPU results, prelaunch `fullcheck_free`, and final GPU XML/process checks.

## Frozen bytes verified

```text
fd31dc722f7a1a4b65a2fb597811e2598d603c650e8f6fe4e852915fc38c7392  organism_v6/semantic_carrier_diagnostic.py
fc9b1b9992f6a3d8066918c9ade5429526b568f472f76055db0e3fd19b08df1c  tests/test_semantic_carrier_diagnostic.py
```

Both hashes matched the supplied freeze on initial and final checks. The actual newly called helper was inspected, not assumed equivalent to the former helper:

```text
dd4f0a72cddc8226fa48ce50ab0faa6dd4e75f9db510aa89cfb5224898ee7496  organism_v6/run_reasoning_neutral.py
4fccd5b0192653a2446b745d5385ea547b78e466150e07ade9e2caff2b7f4e08  /usr/bin/timeout
```

## Why R1 is addressed

- **Controller cancellation and spawn race:** `organism_v6/semantic_carrier_diagnostic.py:364` records SIGTERM/SIGINT, defers raising until the process handle exists, checks cancellation after spawn, and suppresses repeated cancellation exceptions during cleanup. Original handlers are restored at `organism_v6/semantic_carrier_diagnostic.py:406`.
- **Cleanup on every handled exit:** `organism_v6/semantic_carrier_diagnostic.py:391` calls group cleanup in `finally`, including normal/nonzero exits, cancellation, and controller wait timeout. It records `CLEANUP.json` and rejects unsuccessful cleanup. `organism_v6/semantic_carrier_diagnostic.py:512` rejects nonzero completion before sealing; replay requires a successful, uncancelled cleanup receipt at `organism_v6/semantic_carrier_diagnostic.py:479`.
- **Actual helper fixes the leader-only defect:** `organism_v6/run_reasoning_neutral.py:77` checks live non-zombie members by process-group ID. `organism_v6/run_reasoning_neutral.py:88` performs bounded TERM/KILL escalation even after the leader exits, tolerates disappearance during signaling, reaps the leader, and returns group emptiness. It does not use global process-name or GPU-user kills.
- **Independent timeout for a running worker:** `organism_v6/semantic_carrier_diagnostic.py:375` reserves eight seconds, wraps the worker with `/usr/bin/timeout --signal=KILL`, and starts a separate session. The external timeout is independent of the Python controller's survival. Normal helper grace waits total at most six seconds, apart from scheduling/proc-I/O delays. `organism_v6/semantic_carrier_diagnostic.py:411` verifies supervisor PID/start identity, session/group, command bytes, controller start identity, and deadline before GPU setup. The helper and timeout binary are included in source pins at `organism_v6/semantic_carrier_diagnostic.py:86`.

## Accepted limits

The documented boundary at `organism_v6/semantic_carrier_diagnostic.py:5` is explicit: this is not an escaped-process/cgroup guarantee; loss of the timeout supervisor, uninterruptible waits, and descendants left after early direct-child exit following controller loss are outside the independent-timeout guarantee. These match the scope accepted by main and are not reopened as blockers. No scientific-material, threshold, backend, or C11 expansion was reviewed or requested.

## Test evidence status

**No tests executed during this re-review**, as requested. Source contains 31 test methods. Inspected cancellation/assignment and repeated-signal coverage (`tests/test_semantic_carrier_diagnostic.py:440`), normal/nonzero exits and fail-closed cleanup (`tests/test_semantic_carrier_diagnostic.py:477`), surviving-group/race checks (`tests/test_semantic_carrier_diagnostic.py:500`), and parent binding (`tests/test_semantic_carrier_diagnostic.py:517`). Real CPU-process test definitions cover supervisor binding (`tests/test_semantic_carrier_diagnostic.py:565`), an exited leader with a surviving child (`tests/test_semantic_carrier_diagnostic.py:586`), and controller SIGTERM/SIGKILL while its worker remains running (`tests/test_semantic_carrier_diagnostic.py:601`). Passing execution results remain main's responsibility; source inspection is not a test-pass claim.

Only this new `/tmp` report was written. No repository edits, git commands, GPU access, worker launches, or duplicate repairs.
