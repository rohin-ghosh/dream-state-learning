# NODE1 actual R179 execution

This supersedes the preparation-only status in `PREPARATION.md` and
`PREPARED_NODE1.json` without overwriting those consumed observations.
Main's READY/GO is present and has been applied, not deferred.

## Exact authority and implementation

- Main scope SHA: `85441db890036947f6bc242e66ef15db750a683d73fe02d06778ebe996d4fb54`.
- Policy SHA: `b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b`.
- Main CPU log SHA: `be9ff6c0cbad47c6e8e5a449aa711cfdf4a6b6c31c8d462941c2cdb4104685eb`;
  its exact receipt records 108 tests + 145 subtests passed.
- Actual operator SHA: `d0f8b00ab53b0e20bc00c6b3170f0d89038f9f67b5ff5aa3a088800eca4d8ef5`.
- Existing A100 base mechanism SHA:
  `6e4d91c9581d952924ae269d7f4831fc9840c741805ebcddf2f2c78e8d356270`.
- Operator tests SHA: `4b586ead7a578f0d072b1cfa3c1f6467dadb09c15be37048a5c93bd27a85a9bb`.
  Eleven local CPU tests pass; nine preparation cross-binding checks also pass.
- Receiving CPU probe SHA: `189aeecf76ec62b6c5ad1ad7ea5cb30e9e5b0b735edfd81590cea967a284497e`.

Actual remote operator package:
`/localhome/local-rohing/orch_r179_node1_20260917_attempt1/operator`.
Candidate roots:
`/localhome/local-rohing/orch_r179_node1_20260917_attempt1/lanes/lane<N>`.
All three state-carry tests ran in a fresh actual A100 interpreter against each
lane's staged native and policy modules: low-context retention/sleep/restore,
threshold compaction, and no-distillation unchanged view. CUDA was not initialized.
These 15 receiving behavior checks are not claimed as GPU load or sleep proof.

Python files are isolated copies; only native's two compaction lines change and
the policy module is added. Non-Python source assets are same-inode hard links:
their content is not opened by source inventory/copy. Existing non-code bytes
and Python hashes are rechecked; original files are not chmodded or rewritten.
The full original guard validation and Python closure are preserved. Candidate
PLAN changes only source/startup relocation; existing walls, resource bounds,
variants, containment, UUID/minor and admission machinery are unchanged.

## Tangible checkpoints

- `STAGE_LANE7_1789665015443830999.json`: actual original `prepare_sleep`
  no-distillation branch executed on CPU with no history accessor available;
  returns without touching context. Actual actor PID 1997023 remains unchanged.
  **ALREADY_COMPLIANT_VERIFIED_NO_RESTART.** No frozen controls are included.
- `STAGE_LANE2_1789665027186139752.json`: real lane2 source staged and validated;
  receiving CPU receipt SHA `2d34261b9fba2889f34d42c9737e74b4cc5ed909f01d953bd4628e32022c0638`.
- `STAGE_LANE3_1789665052915770491.json`: lane3 receiving CPU PASS.
- `STAGE_LANE4_1789665058196423309.json`: lane4 receiving CPU PASS.
- `STAGE_LANE5_1789665063277020334.json`: lane5 receiving CPU PASS.
- `STAGE_LANE6_1789665068483128126.json`: lane6 receiving CPU PASS.

All five independent per-life handoff operators are actually dispatched and
armed, not mere proposed commands. Their PIDs at dispatch were lane2 1264481,
lane3 1272083, lane4 1272286, lane5 1272446, lane6 1272649. They have independent
30-minute boundary waits and independent 300-second actor-resume watchdogs.
No all-node/all-fleet gate is introduced. Handoff dispatch is not load success.
The status receipt files, not this static description, establish subsequent
boundary/retirement/load/completed-generation outcomes.

Each operator waits for a current terminal SLEEP_COMPLETE plus owned readout
dispatch, pauses only its exact actor, drains the independently running readout,
and preserves the full saved stream and checkpoint within explicit byte/disk
limits. CPU restores the actual full saved envelope in the new source before
retirement. Original actor/timer/supervisor natural exits are required; then the
unchanged privileged guard/device admission and seven-foreign-device confinement
must pass for the successor. No guard bypass or lease/wall extension is added.
Failure resumes a pre-retirement actor via watchdog or records a post-retirement
hold without retry/reset. No original journal is opened for writing by the
operator; the continuing guarded learner alone appends new records.

## Read-only status

```sh
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B research_loop/workers/r179_context_survival_20260917/node1/collect_status.py
```

This reads only own operator metadata receipts and exception summaries, and
creates a new local `EXECUTION_STATUS_<timestamp>.json`; no learner text,
sealed output/map/score or credentials are returned. Exact native source hashes
are lane-specific in the receiving receipts/source proofs; do not assume every
lane's full native file is equal merely because relevant ASTs match.

No Main COORDINATION edit, no other node's control action, no parent message and
no frozen-control action has been performed. A successor LOADED receipt and
first generation still do not prove a subsequent CONTEXT_RETAINED/completed
sleep/post-sleep context-custody chain; that needs actual new journal metadata.
