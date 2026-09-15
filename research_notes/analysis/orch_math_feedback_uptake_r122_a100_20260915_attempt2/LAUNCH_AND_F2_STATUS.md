# R122 A100 launch and R121 F2 status — 2026-09-15 18:46 UTC

Metadata only. Raw calls, optimizer files, checkpoints and transcripts stay on nodes.
No Git mutation. Main owns a40r4/5; MATH touched only assigned A1005/6/7.

## Actual A100 launch

Root: `/localhome/local-rohing/orch_math_feedback_uptake_r122_a100_20260915_attempt2`.
Source: `/localhome/local-rohing/orch_math_feedback_uptake_r122_oldfleet_source_20260915_v2`.
All three privileged full `/proc`+UUID/CVD admissions returned clear with no blockers.
The model-loader verified each genuine C8 adapter against its mounted frozen base.
These are **read-only learned-child elicitation forks**, not optimizer continuation or weight sleep.
Raw historical AdamW files are verified/preserved, never loaded or rewritten.

| Physical | Guard PID | Native PID/start ticks | First input UTC | First COMPLETE UTC | Child tokens | First call SHA256 |
|---|---:|---|---|---|---:|---|
| 5 | 3210464 | 3210534 / 21880718 | 18:42:05.016271 | 18:42:41.439847 | 792 | 71f682b00865dcefe31f25769de5e89c40ace081b721b438d803177af4ca435f |
| 6 | 3210465 | 3210501 / 21880710 | 18:42:07.133524 | 18:42:54.639880 | 1028 | 7cc69204d0bfa248976a13bdf5d18420ebb2a8929424dfb31795378a1a37336c |
| 7 | 3210466 | 3210531 / 21880715 | 18:42:05.032975 | 18:42:42.389131 | 807 | 289f2c2be0e2ca40f9d6815c6466461a3f83a045680c19460c63302964f17df0 |

Boot: `273420dc-cd6c-4760-a264-0027d2f6aede`.
First artifacts: `lane{5,6,7}/calls/CALL_00000001.json` under the root;
fields `messages`, `response.raw`, `response.token_ids`, `token_count`,
`started_unix`, `completed_unix`, `raw_saved_before_parser`.
At the bounded follow-up lanes5/6/7 had respectively6/5/6 completed calls;
all had no terminal and actual BROKER_READY. Parent delivery not yet claimed.
VM CPU brokers3584464/3584465/3584466 run low-effort Astra,1024 output cap,
per-episode600sTTL and no child wait. Fixed v4 prompt re-read each provider call;
every transcript is uploaded and hash-verified before bounded local buffer cleanup.

Native manifest: `a02c8c322b7c74fa8c60980f827c80ff5ae59f56d26fd9aa5332bebfd9e7a1e9`.
CPU7local+7native PASS: `78e4a419a7907db56f9435cf14d23f73667d81ac10afb7759356fade2f1c5574`.
Broker frozen source `/tmp/orch_math_feedback_uptake_r122_broker_source_20260915_v2`:
manifest `b1bbe40de85bcf78aea575b6b667c68f17941585c384dbaa4ff79512789c60b3`;
focused broker test passes locally and from frozen source.
An earlier broker source-copy attempt failed before import; all three processes
exited, no remote lock/provider/input charge. Failed logs remain in `/tmp`.

## Node5 F2 gap is a crash, not a transition

Root: `/localhome/local-rohing/orch_math_feedback_uptake_r121_independent_20260915_attempt3`.
F2 native3403682 is absent. `lane1/TERMINAL.json` FAILED at18:42:44.182202;
guard returncode1 at18:42:45.119172. Missing packaged file:
`/localhome/local-rohing/orch_math_feedback_uptake_r121_independent_source_20260915_v3/research_notes/PARENTING_BATTLE_PLAN_v4_2026-09-15.md`.
Failure occurred after completed C13 presleep, while configuring reflection.
Native reservation292 is preserved; do not retry it or replay preceding calls.

Both independent branches performed real saved LoRA sleeps with lambda0.25:

| Branch | First sleep | First saved UTC | Steps | Second sleep | Second saved UTC | Cumulative AdamW steps |
|---|---|---|---:|---|---|---:|
| F2 | C11 | 18:29:40.004105 | 270 | C12 | 18:41:30.115461 | 3555 |
| A2 | C7 | 18:29:28.303795 | 270 | C8 | 18:41:11.537964 | 3555 |

Second sleeps add276 steps. Each sleep encoded all6 new rows, with174 then180
encoded rehearsal rows;6 legacy rehearsal rows were rejected by the existing
`nonempty_special_free_child_target` encoder check. This is not outcome selection;
rejections and original evidence remain, and no all-rehearsal-coverage claim is made.

F2 last genuine checkpoint:
`lane1/checkpoints/000012/CHECKPOINT.json`
SHA `f978cee8e8d256bc07724783e305efd95ae8e735541f4081b3f303b6224183bc`;
raw optimizer/RNG SHA `4fbe43c4dc4df4c5ed8cf1b94c4687f1743d51aa8617c966e272f9278771b0d3`.
Counters at failure: native292,parent66,steps3555,
child-token exposures473221,anchor-token exposures66177.

Both branches' first two fresh DEV processes failed with OOM before successful
readout completion: resident training model retained about39GiB, leaving too little
for the fresh readout model. `readouts/DEV_C*/PROCESS_RESULT.json` truthfully says
FAILED_NO_RETRY. No successful DEV or retained-behavior claim.
A2 native3403683 was still alive at this check. No actors/guards were signaled;
no immutable native source/checkpoints changed, no inputs retried.
Follow-up needs a separately versioned missing-document packaging repair and
resident model/optimizer CPU offload around future fresh readouts, preserving
saved optimizer/RNG/counters and charged failures. Healthy A2 is not hotpatched.
