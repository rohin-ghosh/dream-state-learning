# Main / Hubble: actual V2 deployment and bounded route supply

Node1 measured 2026-09-15T04:32:27.490092+00:00. Route measurements are individually timestamped in `TERMINAL_STATUS.json`. Snapshot folder uses the measurement time, not report creation time.

## Node1 physical slots — all eight native V2

| GPU | PID | V2 calls | Numeric correct | Raw calls/hour | Status |
| --- | --- | --- | --- | --- | --- |
| 0 | 42080 | 110 | 101 | 311.1 | LIVE V2 |
| 1 | 42942 | 103 | 91 | 310.1 | LIVE V2 |
| 2 | 43839 | 137 | 134 | 440.9 | LIVE V2 |
| 3 | 44696 | 130 | 123 | 447.5 | LIVE V2 |
| 4 | 46196 | 63 | 59 | 313.4 | LIVE V2 |
| 5 | 47188 | 56 | 52 | 309.2 | LIVE V2 |
| 6 | 48170 | 52 | 49 | 327.8 | LIVE V2 |
| 7 | 50316 | 33 | 28 | 310.3 | LIVE V2 |

Total **684 V2 native outputs**, 637 numeric-oracle correct. Aggregate wall rate **1934.4 raw calls/hour**, **414204.7 content tokens/hour** over 1272.9 seconds from the first V2 call start through this observation, including rolling ramp. Per-slot rates use each slot's first V2 call start through the same observation; ongoing calls remain in the elapsed denominator. These are short-window raw-output rates, not qualified-data rates. Qualified rows/hour is not established.

All eight complete-task checkpoints have zero unfinished calls/pairs, preserved original call hashes, and no V1/V2 task overlap per physical slot. All captured V2 calls carry the phase version and respect 8192 new /16384 total tokens. Original lifetime bytes and global ledger are unchanged; 2161/24576 reservations at observation, not a reset. Native cutoff 2026-09-15T15:40:10.822773Z; hard end 15:45:10.822773Z. No LoRA/base updates.

## Node3 physical slots — live current batch

| GPU | Phase | PID | Raw calls | Completed episodes / correct | Raw calls/hour |
| --- | --- | --- | --- | --- | --- |
| 3 | node3_batch02 | 192127 | 94 | 39 / 9 | 423.4 |
| 4 | node3_batch02 | 192124 | 85 | 33 / 10 | 382.9 |
| 5 | node3_batch03 | 218805 | 12 | 5 / 1 | 597.6 |

Batch02 slots3/4 retain pending native work; batch03 waits their complete episodes/process exit. Slot5 already has actual batch03 outputs. No task is interrupted to manufacture a restart. The new queues contain distinct public display/task hashes over the SAME eight existing TRAIN worlds and 32 replay-verified child-authored events, not new independent worlds. Batch02 froze 120 displays/720 maximum calls; batch03 froze 48 more/288 maximum calls. Batch03 admission budget bound was 1613 existing +54 prior remaining upper bound +288 new =1955≤2048. Original node3 2048-call ledger, 15:18:38.782722Z hard end and lease limits remain; no automatic budget reset.

Initial route V2 batch completed 330 native calls /96 episodes, with 24 verifier-correct episodes. These were identical 32-task treatments on three slots (8/32 correct per slot), not 96 independent tasks. Several raw responses contain fabricated observations or confuse CURRENT and PORT; verifier success alone is not semantic quality. All retained, no automatic admission.

## Quality handoff

`RAW_BATCH_64.json` gives 64 exact raw files/hashes, first eight calls per physical slot, without quality filtering. `SEMANTIC_SAMPLE.json` and `SEMANTIC_SAMPLE_REVIEW.md` document full-text review of 12 final outputs across all four conditions plus six supplied first passes: **0/12 supported search branches, 1/12 fabricated consequential branch, 11/12 numeric correct**. The harmful META case changes correct 80 to incorrect 100 by inventing ambiguity over two free lessons. Preserve it; do not relabel or regenerate. These are author-side measurements, not Hubble admission.

`branch_candidate/CALL_00049.json` is an actual LIGHT_BRANCH counterfactual (28 birds without theft vs21 after the given theft). `branch_candidate/REVIEW.md` distinguishes a supported operational counterfactual from genuine independent search branching. It is a selected illustration outside the twelve-output denominator. No strong positive search-branch claim is made.

## Repairs and limitations

- The first controller paused before GPU4 after node3 naturally completed. At 04:14:37 a conservative census observed 15 ready generators while node1 GPU3 loaded; therefore uninterrupted ≥16 is NOT claimed. Fresh route backfill restored headroom before resuming. Original failure receipt is preserved.
- GPU7 admission correctly rejected a transient root process with the mapped device open. The process disappeared naturally; failed scan/log were archived, a fresh unchanged privileged scan passed, and GPU7 returned native V2. No whitelist, peer kill, or native retry occurred.
- Each rolling stop had a fresh floor receipt and only one owned GPU was transitioned at a time. Final census counts 16 ready generators across known roots; it is not an exhaustive fleet utilization claim.
- Node3 0/1/2 remain released to Pasteur;6/7 peers untouched. No commits, rebases, resets, staging or shared BOARD edits were performed. Only own dated COORD append entries were added.

## Ready to stage

`STAGE_READY.json` lists exact source/test/evidence paths with SHA256 hashes. Tests: **22 node1 +10 route CPU tests PASS**. Native preparations: 12,320 node1 V2 prompt encodings; route batches32/120/48 prompts, original37ec/base/tokenizer/source checks. Frozen native source inventories and admission/checkpoint evidence are in the snapshot and corresponding route analysis roots. Hubble/Main owns downstream sampled publishing; no parenting data entered L1 through this work.
