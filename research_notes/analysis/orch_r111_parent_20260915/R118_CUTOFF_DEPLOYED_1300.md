# Route shared cutoff: deployed lifecycle repair

Verified **2026-09-15T13:00:00.779437Z**. This is a non-material, independently deployed operational controller, not a change to the learner, parenting policies, model, dataset, quotas, CONFIG, optimizer or pinned route executable.

## Actual deployment

- Immutable root: `/localhome/local-rohing/orch_r111_shared_cutoff_20260915_v4`.
- Monitor PID **1271059**, start ticks1264381; independent fuse PID **1271060**, start ticks1264381. Both UID2524, exact command hashes/boot identity recorded in `control/*_STARTED.json`. The fuse is a separate process and does not depend on the monitor completing observations.
- Source `gpu/orch_r111_shared_cutoff.py` SHA256 `99e94e78fa3ff8ee8c166cbf6981243f6229df5aab3818b788602af844a705d1`.
- `control/CONTROL.json` SHA256 `d87f31d76f183e9a8c7b2378512cf9b3b06e2a2b034ceebca275651783f98868`.
- `control/DEPLOYED.json` SHA256 `3fe642b6d259568d8b6221c99da3f5f2a3d72c8ce9946fea058c8bcde6490810`.
- `control/DEPLOYMENT_VERIFIED_1259.json` SHA256 `a43bb21e3dd2b52fa8ab48044affca46f77f9fd4e37a90f63e6574d6ec24dba5`. The filename is a label; actual observation was13:00:00Z. The compact repository copy is `CUTOFF_DEPLOYED_COMPACT_1259.json`.
- Current decision **MONITOR**, observation errors empty, both controller processes alive, status refreshed12:59:56Z, no route disposition/stop receipts. **Zero GPU signals during preparation/deployment.** F1 actor1035149 and A1 actor1035110 remain under their original shared supervisors1035111/1035107.

## Enforced scope and clocks

Only the two route roots/physical UUIDs already allocated to F1physical0 and A1physical4 are signalable. Prepare checks fresh physical UUID/kernel-minor mapping, UID, PID/start ticks, boot, exact command, CVD and frozen PYTHONPATH. Startup binds the current PLAN, actual common CONFIG/ADOPTION/INITIALIZED and controller source hashes. Process stops use pidfds; PID reuse, changed PLAN, unexpected ancestry/source or unrecognized orphan fail closed rather than permitting foreign signals. Peers and their counters/terminals are **read-only**.

- **16:45UTC:** scheduled drain review. Finish the already collecting/submitted generation if it can complete before the cutoff; when its shared checkpoint commits, drain the route processes. Do not start another common generation deliberately. If a later sleep has already started, do not mislabel it complete or interrupt it merely because a review occurred; the absolute cutoff still applies.
- **16:54UTC:** independent fuse starts parallel F1/A1 shutdown, reserving60seconds before **16:55UTC common TRAIN ceiling**. Each route's supervisor is frozen before its actor/readouts, preventing supervisor resurrection; validated actors/readout descendants are frozen and then receive SIGTERM/SIGCONT. Grace is20seconds. A still-live exact pidfd receives SIGKILL only after this bounded grace. Escalation is logged, not presented as a completed task/sleep. Parallel shutdown prevents A1 teardown from delaying F1's optimizer cutoff.
- **Before those clocks:** actual peer-era terminal, original native/parent cap or completed final cycle initiates drain. A missing peer that cannot supply the current barrier permits route cancellation; an already submitted peer can finish the current shared sleep. Native absence has a300second recovery grace. Peer arrival/sleep-start is rechecked under the controller stop lock to avoid acting on a stale missing-peer decision.
- A10minute lack of observed count/update progress is an **alarm**, not a quality criterion or automatic failure. Scores, semantic annotations, losses, success labels and parent text do not drive termination. Missing parent responses alone are not peer termination.
- No original budget is increased and no lifetime ledger is reset. Route original hard wall remains2026-09-16T22:04Z; the earlier common TRAIN cutoff prevents route-only waiting until that wall. Math native16:59 and hard17:02 remain unchanged.

## Exact current terminal eras

F1/A1: real `ROOT/TERMINAL.json`, written by the frozen route actor. Math/code: their actual `SHARED_TERMINAL.json`. Grid: **`R118_SHARED_REPAIR_TERMINAL.json`**, with exact `ROOT/shared_repair_v1/READY.json` and `LOADED.json` bindings from Herschel's repair. Old grid `SHARED_TERMINAL.json` failure receipts are preserved and are **not** the monitored terminal. No naming alias, deletion or fabricated terminal is introduced.

The controller writes truthful operational `control/F1/DISPOSITION.json`, `control/A1/DISPOSITION.json`, and `CHECKPOINT_AFTER_STOP.json` after an actual stop. These are not fake actor terminals. `COMPLETED.json` is only a controller completion receipt after both exits are confirmed and checkpoint evidence is saved. An unconfirmed exit is reported as such. No GPU reset or foreign process cleanup is attempted.

The controller does not stop foreign parent brokers. Hubble/F1 and the A1 broker owner should use these actual disposition receipts for a separately identity-checked, claim-preserving broker drain. Existing broker terminal consumers are not falsely claimed to read the controller receipt automatically. Any already charged outstanding parent attempt remains preserved; no retry/reroute is introduced. Other branch owners retain responsibility for their own processes and original clocks.

## Checkpoint, partial work and FINAL

Only F1 owns the optimizer. After stop, the controller validates the latest committed STATE checkpoint manifest and optimizer hashes and records partial sleep START/ENCODING/UPDATES/COMPLETE references. It does **not** write common STATE, recover a half-published checkpoint, merge independently trained adapters, replay a partial update or invent empty submissions. Incomplete generation rows/updates and all charges stay node-local, distinct from committed shared learning. Even an unreadable common STATE does not block the deadline's attempt to stop the two known route processes; evidence failure is surfaced rather than called success.

**FINAL remains17:00UTC and is Main's separate fresh-process, parent-free sealed readout responsibility.** This controller neither runs it early nor consumes its IDs/outputs or puts them in training. It preserves the committed checkpoint and releases the route workers before FINAL. A17:00 math native readout is outside math's existing16:59 native bound; absent a separately authorized evaluation scope, record NOT_RUN_BOUND rather than extend that segment. No automatic restart or new campaign is launched.

Any later source/PLAN/controller handoff must explicitly rebind or retire this controller alongside the successor; changed plans are not silently accepted. Do not leave an obsolete identity-bound controller advertised as protecting a new source era.

## Actual shared progress and timing

At13:00:00Z, **seven generation0 submissions** exist: F1/F2/F3/A1/A2/A3/A4. F4 is still collecting after its repaired continuation. Both route submissions exist. Serial sleep has **not** started; shared optimizer steps0; latest adopted checkpoint remainsC6 with1125prior steps. No seconds/update number is currently justified.

The monitor automatically records `serial_workload` in its compact STATUS. Once serial START/ENCODING exist, it reports actual encoded new/history row counts and the schedule `16 * encoded_new + encoded_history`. Once update counts have advanced across at least30seconds, it reports observed delta seconds/delta steps and remaining scheduled updates. The current serial UPDATES rows have no timestamps: these are explicitly timed observer windows, not invented per-row durations or a full-sleep timing claim. Incomplete trailing log lines are excluded from the count until complete.

The inactive `gpu/orch_r116_shared_parallel_sleep.py` candidate is **R109_L1/Herschel's**, evidenced by `research_notes/analysis/orch_r109_l1_20260915/STAGE_READY_R116_PARALLEL_CPU.json` and the11:55 COORD claim that the optional parallel backend is paused/tested/inactive. The route owner has not modified it. It documents average-gradient batch8 AdamW, not equivalence to eight serial AdamW updates. Main/Herschel can coordinate separate prospective ownership/integration after first serial measurements; no current source/boundary reset by this work.

### Later observation: first actual pooled serial sleep

The preceding13:00 snapshot is preserved as historical evidence. At **2026-09-15T13:07:13.262742Z**, all eight generation0 submissions exist and F1 actor **1035149** is executing the serial optimizer schedule. Actual START was **13:00:54.991928Z**, owner F1, pid1035149. START SHA256 `f1a0cd2e6fcc05ab36b0c52ec0deca4a89811b0a7ab8107df40b4895b86fa396`; ENCODING SHA256 `05dd3bf041d7ddde11368e6d31a05813f49eb220e0787457fbffde5a878ec32e`.

- Submitted120 new rows; encoded114 new and60 historical rows;6 rejected new rows, three from each grid branch, with recorded `nonempty_special_free_child_target` errors. Rejected raw remains intact. Schedule **114 ×16 +60 =1884 updates**;42 anchors, actual scheduled anchor loss weight0.25 at every update.
- At13:07:13, **120 completed in-memory updates**, **19,969 child token exposures**, **2,159 anchor token exposures**. These are **UNCOMMITTED**: STATE generation0/shared steps0, no sleep COMPLETE, no new committed checkpoint or verified fresh post-pooled held readout. Latest committed checkpoint remains adoptedC6. No learning or readout success is inferred from partial updates.
- Two non-overlapping observer windows:13:02:54.403–13:06:04.889, steps41→101, **190.486s/60 =3.175s/update**;13:06:04.889–13:07:13.263, steps101→120, **68.374s/19 =3.599s/update**. These are count-delta windows, not individual update timestamps. Sequence lengths vary; **no fixed completion ETA**. The earlier linear extrapolation in the preserved13:02 receipt is not the current forecast.
- F1/A1 actor and supervisor identities, UUID/CVD, frozen source root and current PLAN hashes revalidated; monitor1271059/fuse1271060 identity-alive, decision MONITOR, observation errors empty, no route disposition receipts. No GPU signal or runtime/configuration/optimizer/cap change by this observation.

#### Inventory density, not semantic or compute dominance

| Branch | Family | Submitted | Accepted | New presentations | Target tokens/pass including EOS |
| --- | --- | ---: | ---: | ---: | ---: |
| F1 | Route | 8 | 8 | 128 | 362 |
| A1 | Route | 8 | 8 | 128 | 417 |
| F2 | Math | 6 | 6 | 96 | 1791 |
| A2 | Math | 6 | 6 | 96 | 1551 |
| F3 | Code | 8 | 8 | 128 | 2638 |
| A3 | Code | 7 | 7 | 112 | 2003 |
| F4 | Grid | 38 | 35 | 560 | 6120 |
| A4 | Grid | 39 | 36 | 576 | 4884 |

Grid is the majority by inventory: **71/114=62.28%** of accepted new rows; **1136/1884=60.30%** of all scheduled updates including60 historical presentations; **176064/316256=55.67%** of scheduled new target-token exposures. The token denominator excludes historical rehearsal and anchors; counts use actual accepted `source_generated_token_ids`, including EOS as returned by `encode_row`, without retokenization or additional model calls. This does **not** measure walltime share, gradient influence, semantic quality, action changes or benefit. No normalization or schedule change is made.

Exact compact: `FIRST_POOLED_SERIAL_COMPACT_1307.json`; node-local receipt `control/FIRST_POOLED_SERIAL_PUBLICATION_1308.json` SHA256 `e9b5710003233f8cb446bae09d731018c5a218166d0d473b63d2b6ee9686cfc5` under the immutable v4 controller root. The1308 filename is a label; actual observation is13:07:13. Tests rerun after observation: **43PASS in1.80s**, source/test hashes still match deployed v4. Native29PASS receipt preserved. Raw stays on-node; next checkpoint and fresh held evidence remain pending actual completion.

## Tests, preserved repair and commands

Latest source: **29 local cutoff tests +14 adjacent handoff/activation tests=43PASS**, and **29 native CPU tests PASS**, with CUDA hidden and no model/provider calls. Tests cover real CPU pidfd trees/readouts/orphans, a foreign sentinel, PID reuse, unchanged PLAN, bounded SIGTERM escalation, parallel teardown, historical-vs-repair terminals, original caps/cycles/clocks, peer arrival races, corrupt common state, preserved checkpoint/optimizer bytes, timed update windows and repeated monitor status replacements.

Native `CPU.json` SHA256 `d1a6dff92cffa44591f386829f691f44af968369aad3bea78906e53ea3a46511`.

Earlier v1/v2 were never launched. v3 monitor failed after its first status write because cleanup tried to unlink an already-renamed temporary file. Its independent fuse remained alive. The v4 fix preserves missing temporary files safely; repeated-loop regressions pass. Only **after** both v4 processes were verified healthy across multiple iterations was v3 CPU fuse1246180 identity-checked and SIGTERM-retired. No GPU was signalled. v3 source, initial deployment, error/logs remain intact. v4 `PREDECESSOR_CPU_FUSE_RETIRED.json` SHA256 `d4b71a0730fb1bbb7b477dab947f9534118373ae3c48e0b1a9a51e0892a6d695` records that handoff.

Already running, **do not duplicate**:

```text
/localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r111_shared_cutoff_20260915_v4/gpu/orch_r111_shared_cutoff.py monitor --control /localhome/local-rohing/orch_r111_shared_cutoff_20260915_v4/control/CONTROL.json --control-sha256 d87f31d76f183e9a8c7b2378512cf9b3b06e2a2b034ceebca275651783f98868
/localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r111_shared_cutoff_20260915_v4/gpu/orch_r111_shared_cutoff.py fuse --control /localhome/local-rohing/orch_r111_shared_cutoff_20260915_v4/control/CONTROL.json --control-sha256 d87f31d76f183e9a8c7b2378512cf9b3b06e2a2b034ceebca275651783f98868
```

Both commands use `CUDA_VISIBLE_DEVICES=` and `PYTHONDONTWRITEBYTECODE=1`; transport is `gpu/ovx3_ssh.sh`. Compact status is `control/STATUS.json`. Full raw remains on-node; the repository contains only owned source/tests and compact hashes/receipts/documentation. Main owns Git.
