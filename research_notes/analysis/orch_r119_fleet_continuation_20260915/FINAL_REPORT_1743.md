# September15 17:00 FINAL report — observed17:39–17:43 UTC

**Visibility: evaluation-report only. Never include this report, the FINAL
outputs, scores or task keys in parent/head-parent/exchange/sleep inputs.**
This is a read-only reduction of completed original readouts, not a rerun.

## What actually learned

The pooled node5 learner completed **one** shared sleep, generation1, at14:41:13
UTC:1,884 shared optimizer updates,319,802 child-token exposures and35,885
anchor-token exposures. Lifetime counters including predecessor training are
3,009 updates /388,033 child-token /56,236 anchor-token exposures. The next
shared sleep has not committed. Repeated pooled learning and retained thinking
improvements remain **unproven**; preparation, restart attempts and residency
do not establish them.

FINAL selected that generation1 at17:00:00.000183 UTC; selection SHA256
`65899137a9833b177547f6ba3f392576436d590049ebf6454e1a3199642891b7`.
Checkpoint SHA256
`43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d`;
optimizer SHA256
`2afebd67c922367e3735ef9b5ed31b3c9a7c6e329758478781e5ea3cb469c0b5`.

## Output shape first

Each family evaluated8 tasks per branch. F/A are two evaluations of **one shared
child**, not independently trained Fable and Astra models. There are80 completed
responses across the eight branches (route uses16 responses per8 tasks), not80
independent tasks. All observed response truncation flags are false.

| Family / branches | Responses per branch | Total output tokens per branch | Median tokens per response | Multiline responses per branch | Mean repeated lexical4-gram fraction |
| --- | ---: | ---: | ---: | ---: | ---: |
| Route F1 / A1 | 16 | 188 | 12 | 0 | 0 |
| Math F2 / A2 | 8 | 1,131 | 114.5 | 8 | 0.01643 |
| Code F3 / A3 | 8 | 393 | 48 | 6 | 0 |
| Grid F4 / A4 | 8 | 101 | 11.5 | 0 | 0.00962 |

Repetition is a descriptive lexical proxy: lowercase `\w+` tokens, overlapping
4-grams, `(count - unique_count) / count`, zero when no4-grams; average across
responses. It is not a novelty, cohesion or metacognition judgment. Newline count
is not a measure of thinking. Route's stored semantic labels are UNKNOWN16/16
in each branch; this report does not manufacture semantic annotations from
short outputs. Departures-and-returns, obstacle persistence, metacognitive
movement and a matched sleep0 FINAL change are **not yet measured here**.
No OPEN/FOCUSED route FINAL execution is claimed; its original scope is8 routes.

## Original recorded outcomes, secondary

- Route: original `HELD.json` records0/8 correct in both evaluations.
- Code: original `SEALED_OUTCOMES.json` records0/8 correct in both; the native
  batch-response artifact is byte-identical across the pair.
- Math/grid: completed FINAL receipts preserve responses but do not contain
  scores. No new evaluator was substituted and no score is invented here.
- None of these counts establish a parenting-system advantage, a retained gain,
  or a comparison with the matched initial child. No continuation is gated on them.

## Parenting completed before the cut

Counts below come from each original branch's `parent_transcripts/*/RESULT.json`.
All418 results have `finished_unix` before17:00. COMPLETE means the provider
result reported completion; **this reduction does not independently establish
child consumption or a behavioral change**. SILENT is separate, valid intentional
silence; MISSING is not silently dropped from denominators.

| Branch | COMPLETE | MISSING | SILENT | Total slots | COMPLETE / slots |
| --- | ---: | ---: | ---: | ---: | ---: |
| F1 | 3 | 65 | 0 | 68 | 4.4% |
| F2 | 20 | 40 | 0 | 60 | 33.3% |
| F3 | 32 | 68 | 0 | 100 | 32.0% |
| F4 | 5 | 35 | 0 | 40 | 12.5% |
| A1 | 23 | 10 | 3 | 36 | 63.9% |
| A2 | 20 | 15 | 1 | 36 | 55.6% |
| A3 | 13 | 27 | 0 | 40 | 32.5% |
| A4 | 25 | 13 | 0 | 38 | 65.8% |

Fable COMPLETE60/268 (22.4%); Astra COMPLETE81/150 (54.0%), plus4 SILENT.
These are historical delivered-result disparities, not evidence that one parent
model caused greater learning. New high-effort/600s/branch-concurrent broker
settings must be assessed from **new** requests, not these historical counts.

## Compact evidence references

All paths below are node5-local via `gpu/ovx3_ssh.sh`; raw stays there.

| Branch | COMPLETE path beneath `/localhome/local-rohing/` | COMPLETE SHA256 |
| --- | --- | --- |
| F1 | `orch_r111_route_final_20260915_F1_attempt1/sealed_final_readouts/readout_0001/COMPLETE.json` | `5cdee7e9ee6ba9431116886b10374a1ce7df6d2516479e3d9ccc3d5f26ddf163` |
| A1 | `orch_r111_route_final_20260915_A1_attempt1/sealed_final_readouts/readout_0001/COMPLETE.json` | `205b8d2fcb2aee80f3ab5ba2a6400bee843f42fa18b5d9bc1b005aef38c106fb` |
| F2 | `orch_math_feedback_uptake_r119_final_premodel_20260915_attempt1/lane1/COMPLETE.json` | `f078b42b07b4e5862049317c592ace4be88a5eb0e1dd6179208b140c7870920d` |
| A2 | `orch_math_feedback_uptake_r119_final_premodel_20260915_attempt1/lane5/COMPLETE.json` | `2d2d70bf7eeced8ed74b313d189a8dfefeba96cca9846f8a62699ca99f7966ae` |
| F3 | `orch_r108_code_parent_r115_node5_2_20260915_attempt1/parallel_v4/final_failed_recovery/COMPLETE.json` | `38e93c88288bea041d86b1d93ecf8c3453bb04b3b6cb75cc109ae5a3a8af20ab` |
| A3 | `orch_r108_code_parent_r115_node5_6_20260915_attempt1/parallel_v4/final_failed_recovery/COMPLETE.json` | `b67acc0232265f27e7a4e38fb690073617815b96b9a34fcc554929bb02dc67a2` |
| F4 | `orch_r118_grid_final_parallel_20260915_attempt1/F4/COMPLETE.json` | `6385075a2ff37d4e820a443606924dd7e80b7c1ca7175bf2a64401e4db345cd7` |
| A4 | `orch_r118_grid_final_parallel_20260915_attempt1/A4/COMPLETE.json` | `b653284f13b3fe61cbd12f0671d32788c8aa8df56dd46136efce7320e12de091` |

Code batch SHA256 `e00a4d6c0966e18ac0decb11f6a832f37d8ab28a832cdd656890235b9f9a6687`;
original outcomes SHA256 `1d5868681019f80f00ee5b1ab34c54d0b75d04b40d0c3a73b7f0a6f1c4e381e7`.
Route/math scoped pre-model recoveries preserved failed attempts and completed
within the original17:20 evaluation window. No charged task was repeated.

## Operational correction

The17:00 report cut erroneously stopped the fleet. Restoration continues saved
states, not a reset: both L1 arms have now committed15,716 (+256 each from15,460),
and all12 L1 generators have resumed actual calls. Independent17:42 census:
21/40 resident,19 positive instantaneous utilization; node5 still0/8 resident.
Actual full-fleet restoration and repeated shared sleeps remain outstanding.
