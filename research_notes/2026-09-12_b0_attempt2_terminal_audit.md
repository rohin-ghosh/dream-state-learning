# B0 attempt-2 terminal replay audit (2026-09-12)

Status: **PASS only as quarantined writer-plumbing instrumentation; no causal
behavior claim.** This fresh read-only audit followed exact node-1 PIDs
`2374535` (A) and `2374683` (B). It launched, stopped, and modified no job.
A reached `LIFE_DONE` and exited by 07:46:35 UTC; B reached `LIFE_DONE` and
exited by 07:54:55 UTC. Neither PID existed at the final 07:55:16 UTC poll.

## Immutable binding and quarantine

Both launch manifests bind commit
`0babc3ccbe1f2378a61dd0dac6f18f7371b82176` and source-archive SHA-256
`c7c2e8b69812382ab927e87ce1c18f0f674a571bd9ff42825138ce096be6311a`.
The archive and extracted source are read-only on node 1; the remote
`preschool.py`, `run_life_v2.py`, and `train_adapter.py` hashes equal those
files in the Git object. Both manifests say `QUARANTINE_TASK_EXPOSED`,
`clean_lineage_eligible: false`, no parent, no initial adapter/corpus, and a
disposable writer-instrumentation purpose.

## Exact gate reconstruction

`G`, `N`, and `F` are the immutable gate's episode grounding, numerical
agreement, and first-person completed-action record tests. Counts are over
every `note_after`; `None` means unevaluable. Admission is the permissive
frozen high rule `G and (N is not false) and not D` (the observed high and low
counts are equal), not an `F` requirement.

| arm | ledger rows | ACT / record | numeric ACT | G T/F/None | N T/F/None | F T/F | D true | admitted | admitted and F | raw articulation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 1,404 | 356 / 356 | 246 | 99 / 147 / 110 | 91 / 63 / 202 | 12 / 344 | 6 | 72 | 0 | 0/246 |
| B | 1,390 | 336 / 336 | 224 | 85 / 139 / 112 | 87 / 46 / 203 | 10 / 326 | 40 | 66 | 1 | 1/224 |

B cleared `min_items=64` by only two records. Of its 66 training admissions,
65 were not first-person `F` records. A admitted 72 but, as the no-write arm,
created no adapter; none of its admissions were `F`. B's 270 rejections were:
no-result-number 71, not-adjacent 20, no-pass-run-here 20, no-measurement 112,
N-mismatch 17, result-numbers-unmatched 15, practice-only 3, duplicate 2,
no-content 9, and prediction-only 1.

An independent raw-ledger join found exactly one ACT and one record for all
356 A and 336 B execution IDs. Every ACT precedes its record; episode, tick,
occurrence ID/index, action, and outcome agree in every pair; every record has
both occurrence fields; and neither gate reports a `provenance-*` rejection.
Each articulation state exactly reconstructs its ordered deduplicated corpus.
The closed ledger SHA-256 values are
`c809521ea0addf3cfec7b0995f7952a2d2781e93826ebe03bc33e91fcc7f72b0`
(A) and
`8e3b17cf4e946e535f444d0cd5cfe3e6394a4b7c5d429263f404b7aee56409e2`
(B); enforced corpus hashes are
`1630a49136cca640b55b7174398060a598a6367679d2040440421c00a8dd5399`
(72 A items) and
`da1212de27a844b7a75515a73e32a64b3ad3b166c3b8e8c3a3004323301defd0`
(66 B items).

## Write, canary, reload, and probes

B trained the 66-item `preschool_records_v1` corpus successfully: rank 8,
seed 9100, three epochs, 51 steps, 23,079 non-padding tokens, finite final loss
0.7225936651. `train_meta.json` binds the exact corpus hash and reports
`loss_target: child_body_only`, 19,497 supervised tokens, and 3,582 masked
non-padding tokens. The saved adapter SHA-256 is
`52f97fcaf3694202912ba9ef708d05fcfeafb3258e00abb921a2c63c92f3160a`.
The immutable trainer uses tokenizer offsets to exclude wrapper,
special/padding, and boundary-straddling tokens. This is only the evidence
available in the older run: `deterministic_algorithms` is false, and it
predates the later per-record, causal-shift training receipt, so it does not
cryptographically bind child-generation receipts or native shifted-label
counts.

The real-gym canary logged parseable-ACT rate 1.00 and `pass=True`; the
candidate marker became `DONE`. Its denominator/trace was sent to `/dev/null`
and is not recoverable, so the evidence is the rate and verdict, not a claimed
12/12 count. No score gate ran because the launch omitted `--probe-gate`.
Subsequent vLLM engines loaded the LoRA path (Punica was logged), including a
last adapter-enabled reload after the final frozen-base probe and before
`LIFE_DONE`. The post-neutral receipt binds the ON arm to the same adapter and
config hashes.

The fresh held-out neutral program had articulation 0.0 before sleep. After
reload it remained 0.0 both ON and OFF; descriptive scores were 0.153846 ON
and 0.192308 OFF. B's final eight-program means were 0.487793 ON and 0.462921
OFF; its initial base mean was 0.487161. A, which never trained, moved from an
initial 0.468116 to a final 0.499194. These are diagnostics only.

## Two independent replay failures

1. **Cross-arm model-visible wall time.** The eight initial tick-1 child
   outputs are byte-identical. At `cbench-v1/susan` tick 2, however, the only
   prompt-line difference is `alive 27s` (A) versus `alive 26s` (B), producing
   prompt hashes
   `2d8b2c4e7531920338e3905f0c227f43fc64eff62542cd566ac2d9494339029e`
   and
   `63ad7af92c31b835e3f28ac8009c4a4308c13c52d72b6932d78bc08f58bacf07`
   under the same derived seed 1890556771. At `cbench-v1/sha` tick 2 the same
   sole clock difference produces prompt hashes
   `f89862d538372274d02d9679d587719469662f88ecbc159b00aefbf84dd0d434`
   and
   `e53621e83188a30fe22dbb55ad683e049df56b3e9c629f48724a7f403146dd43`;
   with the same seed 46886905, child-output hashes diverge to
   `d00be72267e9aa019f8c30d509d2e71b28f083bdb1655c69b537291ee621ff2c`
   and
   `f2bd2a5cfae184ddb623fc42229bfc0f33cc52ef13c6a7eb567a7acacecc5e0d`.
   The arms therefore diverged before the write
   intervention; gate and score differences are not paired potential
   outcomes.
2. **Identical prompt plus explicit seed is still not a byte replay.** A's
   neutral pre/post probes used the same frozen base, program, and generation
   seed. At tick 2 both prompts have SHA-256
   `b945f26ab52019822a3af0675b474312abf4b8a9db1ac31c9a90e1b3a673be54`
   and the same derived seed 2049694779, yet output SHA-256 values are
   `ceaf56b076c97bfbf35d50cfd9419cb68b43639d847e19a8c7ac3b13c11387c6`
   and `2e2de3b80279365dd1451783a63e26306c4e072b094fa1336f6343af11391d12`.
   Later prompts diverge through different state and elapsed time. Explicit
   request seeding is not demonstrated replay-deterministic in this runtime,
   independently of the cross-arm clock defect.

## Bounded claim

This single uninterrupted task-exposed run supports only this engineering
claim: immutable source `0babc3cc` produced occurrence-unique,
ACT-before-record joins; its permissive gate replaced the legacy corpus; B
completed a finite reported child-body-only rank-8 fit, saved it, passed the
untraced format canary, mounted/reloaded the exact adapter, ran the expected
diagnostics, and reached terminal state.

It does **not** show acquisition of the intended first-person record behavior
(only 1/66 B admissions was `F`, and post-neutral articulation was zero), a
causal score or articulation effect, autonomous outcome learning, parenting,
generalized/persistent memory, improved action, H1, or H2.
`QUARANTINE_TASK_EXPOSED` makes both descendants permanently ineligible as
clean nursery ancestors. Confirmation needs frozen or absent elapsed-time
text plus byte-replay-deterministic inference or a byte-identical exogenous
tape, with prompt/output hashes asserted at every paired step.
