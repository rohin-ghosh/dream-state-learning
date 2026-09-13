# Authorized recovered additive execution — COMPLETE / EDITSTOP

September 13,2026. Exactly ONE authorized local reduction, rc0, empty stderr.
Started **12:01:12.939942 UTC**, ended **12:01:17.229842 UTC**, elapsed **4.265231s**.
No new native/model calls, collection, fits, updates, code/scorer/protocol edits,
Git operations or evidence changes. Source/test were frozen before reveal and
Main had independently passed13tests. Subsequent work only read/summarized the
produced analysis and compared archived baseline receipts; no second scoring run.

## Principal result

ADDITIVE passes the unchanged descriptive screen on seeds0/1, not seed2.
Fresh MEMORY_ONLY passes seed0 only. Neither arm passes all three seeds.
ADDITIVE seed2 acquires exact recall but loses9LR0-correct held items; its
paraphrase4/8 only ties the evaluator's best constant target. This is NOT a
generally successful retention repair, and there is no automatic promotion.

Fresh MEMORY_ONLY fails to reproduce historical EXTRA_MEMORY on all three
native seeds despite verified same initial tensor receipts and exact full
memory occurrence schedule. Their loss traces and final tensor receipts differ.
Preserve these scientifically intact results, but diagnose that drift before
making a clean causal mechanism claim. No cause is inferred or repaired here.

## All six fresh cells

Exact is **production-eligible**, paraphrase is **content-correct**, held/canary
use unchanged `passed`. These are not all strict canonical or raw-byte metrics.

| Seed | Arm | Exact | Paraphrase | Held | Canary | Lost LR0-correct held | Screen |
|---|---|---:|---:|---:|---:|---:|---|
| 0 | ADDITIVE | 14/14 | 10/14 | 47/48 | 12/12 | 0 | PASS |
| 0 | MEMORY_ONLY | 10/14 | 10/14 | 47/48 | 12/12 | 0 | PASS |
| 1 | ADDITIVE | 7/8 | 7/8 | 48/48 | 12/12 | 0 | PASS |
| 1 | MEMORY_ONLY | 8/8 | 8/8 | 46/48 | 12/12 | 2 | FAIL |
| 2 | ADDITIVE | 8/8 | 4/8 | 39/48 | 12/12 | 9 | FAIL |
| 2 | MEMORY_ONLY | 3/8 | 2/8 | 47/48 | 12/12 | 1 | FAIL |

Floors remain8/14,7/8,5/8 exact AND zero lost LR0-correct held/canary.
No canary regressions in any fresh cell. Seed0LR0 was already47/48; retaining
that same missing item is not a new regression. Original possible-record
denominator16 remains distinct from admitted-memory14/8/8. No excluded seed.

## Fresh paired and LR0 contrasts

Each entry is **gained/lost item counts**, first arm relative to second.
Gains never compensate a loss for the noncompensatory screen. IDs and all
additional metric contrasts are preserved in analysis.json.

| Comparison | Seed | Exact gain/loss | Paraphrase gain/loss | Held gain/loss | Canary gain/loss |
|---|---:|---:|---:|---:|---:|
| ADDITIVE vs MEMORY_ONLY | 0 | 4/0 | 0/0 | 0/0 | 0/0 |
| ADDITIVE vs MEMORY_ONLY | 1 | 0/1 | 0/1 | 2/0 | 0/0 |
| ADDITIVE vs MEMORY_ONLY | 2 | 5/0 | 2/0 | 1/9 | 0/0 |
| ADDITIVE vs LR0 | 0 | 14/0 | 10/0 | 0/0 | 0/0 |
| ADDITIVE vs LR0 | 1 | 7/0 | 7/0 | 0/0 | 0/0 |
| ADDITIVE vs LR0 | 2 | 8/0 | 4/0 | 0/9 | 0/0 |
| MEMORY_ONLY vs LR0 | 0 | 10/0 | 10/0 | 0/0 | 0/0 |
| MEMORY_ONLY vs LR0 | 1 | 8/0 | 8/0 | 0/2 | 0/0 |
| MEMORY_ONLY vs LR0 | 2 | 3/0 | 2/0 | 0/1 | 0/0 |

ADDITIVE seed1 restores both old EXTRA_MEMORY held losses while foregoing one
exact and one paraphrase success relative to fresh MEMORY_ONLY. Seed2ADDITIVE
repairs MEMORY_ONLY's one malformed held answer but introduces nine different
held failures: net-8held is not zero harm. MEMORY_ONLY seed2 restores six old
EXTRA_MEMORY held losses but introduces one other LR0-correct loss.

## Historical references and native baseline parity

Historical endpoints are noncontemporaneous imports, **zero incremental cost**.
Values below are exact/paraphrase/held/canary counts; denominators as above.

| Seed | LR0 | LOWER | HIGH | REPLAY | EXTRA_MEMORY |
|---|---|---|---|---|---|
| 0 | 0/0/47/12 | 10/10/47/12 | 8/6/44/12 | 10/10/47/12 | 13/10/47/12 |
| 1 | 0/0/48/12 | 4/5/46/12 | 7/5/37/12 | 6/6/48/12 | 7/6/46/12 |
| 2 | 0/0/48/12 | 4/3/47/12 | 5/5/17/12 | 5/3/48/12 | 7/7/42/12 |

| Compared to historical EXTRA_MEMORY | Seed | Exact gain/loss | Paraphrase gain/loss | Held gain/loss |
|---|---:|---:|---:|---:|
| ADDITIVE | 0 | 1/0 | 0/0 | 0/0 |
| ADDITIVE | 1 | 0/0 | 1/0 | 2/0 |
| ADDITIVE | 2 | 1/0 | 0/3 | 0/3 |
| Fresh MEMORY_ONLY | 0 | 0/3 | 0/0 | 0/0 |
| Fresh MEMORY_ONLY | 1 | 1/0 | 2/0 | 0/0 |
| Fresh MEMORY_ONLY | 2 | 0/4 | 0/5 | 6/1 |

No canary changes in these comparisons. Fresh MEMORY_ONLY raw/finish drift
counts against old EXTRA_MEMORY (exact/paraphrase/held/canary) are **5/0/0/0**,
**1/2/0/0**, **5/5/7/0** for seeds0/1/2.

| Seed | Old EXTRA_MEMORY last loss | Fresh MEMORY_ONLY last loss | Same source/initialized tensor receipts? | Same final tensor receipts? |
|---|---:|---:|---|---|
| 0 | 0.005187715 | 0.014876134 | Yes/Yes | No |
| 1 | 0.074396327 | 0.036297157 | Yes/Yes | No |
| 2 | 0.003047768 | 0.043439660 | Yes/Yes | No |

Epoch loss traces already differ at epoch1, so this is not solely a formatter or
score-collector discrepancy. Exact parent/config/occurrence/order checks pass;
the cause of native trajectory drift is unresolved. Tiny Torch CPU parity is
not native numerical/trajectory parity. The fresh paired contrast remains
descriptive evidence but cannot settle an isolated mechanism without addressing
this limitation. No post-outcome recipe change or new experiment was attempted.

## Constant, format and raw-record limits

Best evaluator-only fixed raw-target counts are6/14,4/8,4/8 for both cue variants;
distinct candidate raw targets are4/5/5. These are oracle summaries of repeated
targets, not a trained constant baseline and not an independence estimate.

- ADDITIVE exact14/7/8 exceeds those constant counts on all seeds, but seed2
  paraphrase4/8 merely ties4/8. MEMORY_ONLY seed2exact3/8 and paraphrase2/8 are
  below the constant4/8. Exact acquisition is not evidence of robust general
  cue/key binding or repeated-cycle retention.
- All480new readouts stopped; zero length terminations. Only5/120memory readouts
  are strict canonical JSON (seed0ADDITIVE exact); the other115memory readouts
  are noncanonical JSON. Production eligibility/content and strict formatting
  remain separated; no raw normalization or repair was applied.
- Exact raw-target-byte matches ADDITIVE13/14,7/8,8/8 and MEMORY_ONLY8/14,8/8,3/8
  differ from canonical counts. Byte matching must not be relabeled canonical.
- Seed0 both arms: four paraphrase outcome mismatches; MEMORY_ONLY additionally
  four exact outcome mismatches. Both retain one held `try:integer_triple_required`
  failure already present underLR0.
- Seed1ADDITIVE: one outcome mismatch in each memory panel. MEMORY_ONLY memory
  panels are correct but two held items each have predicted/relation mismatches
  (two items, not four independent failures).
- Seed2ADDITIVE: paraphrase action1/outcome1/prediction2 mismatches, plus nine
  held `output_variant` mismatches. MEMORY_ONLY exact action3/outcome2 mismatches,
  paraphrase action3/outcome3 mismatches, and one malformed held JSON answer.
- All new source/route/native-token/raw-hash/finish/stage-release checks pass.
  Content/format failures above are genuine retained child outputs, not broken
  raw receipt custody. The engineering failures below remain explicit.

## Native dose, losses, tokens and timing scopes

Both arms begin from the same original perception parent with fresh optimizer;
LR3e-5,rank8,alpha16,dropout0.05,eight passes. Exact full memory occurrence
schedule is matched:304/256/256updates per arm, **6fits1632updates480coldcalls**.
ADDITIVE adds192replay forwards per seed; it is not compute/RNG/gradient parity.

| Arm, all seeds | Updates | Memory forwards | Replay forwards | Memory tokens | Replay tokens | Total supervised/context tokens |
|---|---:|---:|---:|---:|---:|---|
| ADDITIVE | 816 | 816 | 576 | 141368 | 198552 | 39952 / 299968 |
| MEMORY_ONLY | 816 | 816 | 0 | 141368 | 0 | 22888 / 118480 |

ADDITIVE total tokens339920 vs MEMORY_ONLY141368. Constituent CE means are
summed, not averaged; absolute aggregate losses across differing objectives
are not directly comparable. Full epoch/component traces and token-kind
breakdowns remain in analysis.json and execution_review.json.

| Seed | Arm | Last loss | Parameter delta L2 | Train s | Fit process s | Readout process s | Generation s | Peak CUDA GiB |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | ADDITIVE | 0.006411808 | 2.198170 | 147.295 | 165.980 | 116.304 | 85.259 | 15.172 |
| 0 | MEMORY_ONLY | 0.014876134 | 2.168905 | 85.191 | 108.271 | 115.551 | 86.237 | 14.778 |
| 1 | ADDITIVE | 0.083356917 | 2.053241 | 130.727 | 152.958 | 91.339 | 63.334 | 15.174 |
| 1 | MEMORY_ONLY | 0.036297157 | 2.024493 | 71.608 | 91.180 | 95.077 | 64.148 | 14.764 |
| 2 | ADDITIVE | 0.001045399 | 1.963607 | 134.671 | 153.065 | 100.409 | 72.625 | 15.171 |
| 2 | MEMORY_ONLY | 0.043439660 | 1.931117 | 69.447 | 92.248 | 93.683 | 65.556 | 14.770 |

Peak is the recorded process CUDA allocator high-water, not isolated phase delta.
Component timings are host intervals with asynchronous CUDA, not kernel-time
attribution. Tensor-norm receipts are audited, not recomputed with a model.

Original node2GPU allocation from preserved plans: seed0GPU0
`GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0`; seed1GPU1
`GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4`; seed2GPU2
`GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05`. No fresh native query was made.

| Seed | Controller launch UTC | Controller exit UTC | Prepare s | Controller s | Failed collector wall s | Holder wall s | Separate CPU recovery s |
|---|---|---|---:|---:|---:|---:|---:|
| 0 | 11:39:17.666900 | 11:50:17.992662 | 33.373 | 660.238 | 17.542 | 677.930 | 30.245 |
| 1 | 11:39:31.104071 | 11:49:01.957048 | 30.645 | 570.774 | 14.608 | 585.522 | 23.559 |
| 2 | 11:40:10.520990 | 11:49:53.837927 | 30.347 | 583.234 | 14.649 | 598.028 | 23.829 |

All UTC times September13,2026. Original controller sum1814.246s; logged
preparation+holder sum0.543290hours across three allocations, below8hour ceiling.
Train638.939s and generation437.161s are nested in those process/controller spans:
do NOT add them as extra GPU usage. No independent GPU-active/utilization meter
or unlogged reservation-gap accounting. Each controller<7200s,prepare<180s;
separate repaired collection totals77.633CPU-seconds, each<180s, with zero
modelcalls/fits/updates. Local reducer4.265s is yet another separate CPU span.

## Both engineering failures preserved

Every original controller returned0; all original automatic collectors and
holder-written terminal receipts returned1. The stored failure is
`AttributeError: 'dict' object has no attribute 'score_row'`, caused by additive
material dict shadowing the retention scorer module. Originals contain ONLY
the failure file; original claims, logs, completions and stage data are unchanged.
Main's separately versioned collector uses the original scorer module; all three
recovery receipts record0, collection_attempt2, scientific_retry=false, and
zero fits/updates/generation. This is a scoring implementation recovery, not a
second scientific attempt. Each recovery binds the old five failure-file hashes,
same original plan/completion and exact repair source.

Seed1's launcher additionally preserves
`BrokenPipeError(32, 'Broken pipe')`, `holder_may_be_running=true`. This is distinct
from its collector failure and is not hidden by recovery. Main reported the
preceding SSH30s timeout after seed0launch, reconciliation of holders135911/135927
without retry, and seed2first launch136095. Those external transport events are
operator-reported context; only seed1's BrokenPipe has the local failure receipt.
No local failure receipt for seed0transport does not mean no transport anomaly.

Holder/recovery receipts are written before CLI return, not independent OS
wait/reap evidence. Main separately reports all recovery execution rc0. Archived
stage release receipts pass; no current live-process absence or other-root retry
exclusion is asserted. No source or score correction was needed during reduction.

## Reproduction record — do not rerun this authorized attempt

Executed once:
`python3 -B /tmp/astra_additive_replay_recovered_analysis_20260913.py --manifest /tmp/astra_additive_replay_recovered_analysis_inputs_20260913_attempt1.json --manifest-sha256 d975feca8197f2c09f45452101d9111afdaaa5988417cf9144fdc33089418c24 --out /tmp/astra_additive_replay_recovered_analysis_result_20260913_attempt1`

Manifest: `/tmp/astra_additive_replay_recovered_analysis_inputs_20260913_attempt1.json`
SHA `d975feca8197f2c09f45452101d9111afdaaa5988417cf9144fdc33089418c24`.
Result directory `/tmp/astra_additive_replay_recovered_analysis_result_20260913_attempt1`:

- `analysis.json` SHA `848602f01ca0596306dcb629a2e1d6896e08620cc6a67baa996853118c1cdb89`
- `analysis.md` SHA `986028f66f62829b19f5c46e062b130f5a1e99dee860840a91255da656e67312`
- `execution.json` SHA `f8c263aacfc61d85ecb64d253ae1b52cb372421b6117cfc3921f09b093c7387a`
- `execution_review.json` SHA `c7e8f7eb64a42589869e6f5f903854044405eb9acfc944102d450164b12c35d1`
- `reducer.stdout.log` SHA `f46fe95b6dbfb9f4d66a1e6485a33cad2497a3466aaba8a1b939b33d14086b10`
- `reducer.stderr.log` SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty)

`execution_review.json` is a read-only extraction and archived baseline receipt
comparison, NOT another scorer/reducer execution. Original analysis files were
not edited. Its source file hashes for baseline comparisons are included.

Verified archive SHA `1faf1f6a6482a3834f7aa4c98c34b71c29644acdc4dfec9ac7c0b3cd7c3b1d16`,
523970560bytes/1366members/6adapters. Main's all-extracted-bytes receipt SHA
`75dfaa74c7bfa429216467a2a021bf35935e75a3581c3b236780edaca504ce32`.
The reducer independently hashes its required local inputs and all stage bytes.

Frozen recovered reducer `8a35836aa22267d6199feed676a162c7018e5960a396370cd4f83bb2cc45e63d`;
tests `880252d41bee39865cd562d3b5e407b8d4b5b2214859880add34a9a1647555bc`;
original reducer `df38efd210929ec21523d19daa8b65f98d50fef435b3fa23b719929bca6dc472`;
repair `9b67256c42b7f7c18e79a10f9bc6201140833e8d6c339a7e192ca18de67c854a`.
All remain unchanged. Full seed plan/completion/recovery/source pins are in the
manifest and analysis; no native-root bytes, thresholds or protocols were edited.

Conclusion: useful but seed-dependent acquisition/retention tradeoffs, unresolved
native baseline drift, no all-seed pass and no H1/H2/parenting/clean-lineage claim.
