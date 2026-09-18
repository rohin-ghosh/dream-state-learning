# R157 C1–C5 saved-boundary wall extension

Scope: same-life, same-device runtime-wall extension for C1/0, C2/1, C3/3,
C4/4 and C5/5 on `[REDACTED_HOST]`. Protected run1/2, pilot/6 and reader/7
are outside this helper's scope. No adapter, AdamW, RNG, history, prompt,
learning-method, workspace, inbox or visibility reset is authorized.

Exact shared runtime authorization:
`research_loop/workers/r157_keepalive_20260917/AUTHORIZATION.json`, SHA256
`05c50f8012559360221a889b26c00700a988878fbe4d32d30e3f786937dfc392`.
Configured hard wall: September 19, 2026, 00:00 UTC (`1789776000`).
Compatibility resource ceiling: 00:10 UTC (`1789776600`). These are
operator-authorized runtime bounds, **not provider booking evidence**.
`PROVENANCE.json` records no actual conflicting reservation found in the
bounded source trace; it does not establish a provider expiration date.

## Tested operator and stages

Helper: `gpu/orch_r157_community_wall_extension.py`, SHA256
`7e0fcf8c35b72fc6fa01738446d51d8fe9e996afefae66236dd2d5c47d6a2419`.
Tests: `tests/test_orch_r157_community_wall_extension.py`, SHA256
`cf4a0cf5e7620f6554d7c4330c4734773afc3af6f0a90418e37a585678e873b6`.

Receiving-node immutable operator:
`/localhome/local-rohing/orch_r157_community_operator_20260917t0224z`.
Its `CPU.json` binds 42 passing node5 tests, helper/test hashes and test log.
Local combined regression command: **147 tests PASS in 24.882 seconds**:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_orch_r157_community_wall_extension \
  tests.test_orch_r131_saved_boundary_handoff \
  tests.test_orch_r153_community_runtime \
  tests.test_orch_r153_community_launch
```

Stages are `/localhome/local-rohing/orch_r157_community_C1_20260917_attempt1`
through the corresponding `C5` namespace. Each `REQUEST.json` pins its
original guard, plan, source bytes, host/GPU identity, original actor,
timeout and contained-supervisor identities. Its `source` copies the entire
original closure unchanged, adding only this helper and its tests.
Original source trees are never hotpatched.

## Entry points (already dispatched; do not replay)

Run with the receiving-node Python, empty `CUDA_VISIBLE_DEVICES`, and
`PYTHONPATH` pointing at the frozen operator source:

```text
python -B -m gpu.orch_r157_community_wall_extension stage
  --agent C1 --config EXACT_ORIGINAL_GUARD
  --authorization AUTHORIZATION.json --provenance PROVENANCE.json
  --cpu CPU.json --output NEW_UNIQUE_AGENT_NAMESPACE

python -B -m gpu.orch_r157_community_wall_extension handoff
  --output STAGED_AGENT_NAMESPACE --seconds 3600 --execute-handoff
```

All five watchers were dispatched once at September 17, 2026, 02:27:22 UTC.
Their PIDs were C1=2524537, C2=2524538, C3=2524539, C4=2524540,
C5=2524541. These are operator watchers, not learner identities.

`handoff` pauses only the exact native actor at its own completed sleep,
with a separate resume watchdog. It waits for the independent readout,
preserves the full checkpoint/journal and verifies adapter, AdamW and RNG
on CPU before ending the exact old actor. It invokes a fresh privileged
original R125 scan, exact one-GPU systemd confinement, foreign-device open
denial checks, and the frozen native guard with `resume=True`.

The original life root, journal, workspace and inbox remain the same. New
control is `control/GUARD.json` in the corresponding R157 stage. Services
must not interpret the new source/control path as a new child birth.

No automatic retry: an `ARMED.json` is not an applied extension.
`FAILED.json` requires inspection; never replay `HANDOFF_ONCE` or launch a
second actor. Old artifacts and failed attempts remain preserved.

## Actual evidence

`STATUS_*.json` snapshots contain metadata, not readout contents.
Each `C*_APPLIED.json` is copied only after the actual original journal
contains the CPU-predicted `WALL_EXTENDED` followed by `LOADED.resume=True`
with matching adapter hash and optimizer steps. It binds the new actor,
timeout PID/start ticks/command and measured timeout expiry. The timeout
has the existing short safety lead before the configured hard wall; report
its measured expiry rather than asserting it ends exactly at midnight.
Append-only `research_loop/COORDINATION.md` entries relay each verified
application separately. No preparation or service-readiness receipt is
presented as an actual learner resumption.
