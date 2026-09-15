# R127: parent-free evidence access differs; useful learning remains unproven

September 15, 2026. All seven prospectively selected conditions completed. Native run: **20:01:54–20:26:30 UTC, 24.6 minutes**. No condition, source world, failed action or checkpoint was discarded based on results.

## Answer

The canonical parented checkpoints consult more supplied records than their unparented counterparts on fresh same-family worlds. The C2 and C4 differences have positive pointwise paired-world intervals. This is an observable **parent-absent evidence-access difference**, not proof of semantic evidence use, richer written thinking, useful metacognition, or a parenting-specific task-performance improvement. Every guided-versus-unparented correctness interval includes zero. The overall learning objective remains **UNPROVEN**.

## Design and verification

- One fixed initial **level-1 adapter**, held frozen for the SEED reference; this is not an untrained-base or LoRA-OFF reference.
- Historical GUIDED and UNPARENTED checkpoints after C2, C4 and C6, selected before this assay. Fresh process and empty evaluation context per condition, no parent, optimizer or training activity.
- Six-turn maximum per task; identical original public prompt and decoder. Sixteen new worlds, two tasks per world, shared across all seven conditions. Fresh identifiers do not make this a new task family.
- The fixed initial child generated the common source store: **64 accepted of 64 offered events, all 16 worlds complete**. No unavailable-memory read occurred. This establishes availability, not semantic use or correctness of every record.
- **224 evaluation episodes, 1,219 evaluation calls, 128 source calls; 1,347 total of the 1,472-call cap.** All eight stages exited zero with final unchanged-state checks. No inference was retried.
- Offline verification checks **3,971 files**, all checkpoint/source/capture joins, common tasks, parent absence and unchanged-state receipts. Result: COMPLETE, no errors.

Verified reduction: `COMPLETE_VERIFIED_1.json`, SHA256 `627a63796a66b04ee098ba0763a12c835a978dd0daa9b489f8d41114b65deaf6`. Native root: `/localhome/local-rohing/orch_r127_route_transfer_20260915` via `gpu/ovx_ssh.sh`; raw evidence remains there.

## Behavior first

All means below average the two tasks within each of the sixteen worlds, then average worlds. EOS-inclusive tokens are **generated tokens over the entire episode**, not reasoning-token counts.

| Condition | Cumulative updates | Supplied records read / episode | Generated tokens / episode, including EOS | Literal-command responses / all responses |
|---|---:|---:|---:|---:|
| Frozen SEED | 0 | 3.34375 | 58.40625 | 167/167 |
| GUIDED C2 | 104 | 3.625 | 61.75 | 177/177 |
| GUIDED C4 | 320 | 4.000 | 67.03125 | 192/192 |
| GUIDED C6 | 424 | 3.625 | 64.03125 | 174/176 |
| UNPARENTED C2 | 104 | 3.375 | 59.03125 | 169/169 |
| UNPARENTED C4 | 320 | 3.625 | 62.09375 | 178/178 |
| UNPARENTED C6 | 536 | 3.125 | 56.000 | 160/160 |

There are **zero repeated READ attempts and zero truncated responses in every condition**. Reading before the first ROUTE was already universal where a ROUTE occurred; that binary behavior did not newly appear. GUIDED C4 reads all four records before routing. More record access is not automatically a better allocation of effort.

The post-hoc literal-shape audit finds **1,217/1,219 responses consist entirely of a single READ EVENT or ROUTE command**. Every condition's median response is **11 generated tokens including EOS**. The two other responses, both GUIDED C6, are not automatically classified as reasoning. The full raw text was captured; near-absence of written rationale is not a logging truncation.

The producer's separate `generated_text_tokens` telemetry is missing for every condition. It remains UNKNOWN, not zero. EOS-inclusive token IDs are observed. Semantic evidence use and response to corrective feedback remain UNKNOWN; the original episode ends on an invalid action, leaving no post-error recovery opportunity. Method counts, metacognitive quality and novel-thought yield are not inferred from command length.

### All prospectively fixed guided–unparented contrasts

| Checkpoint | Extra supplied-record reads / episode | Pointwise 95% interval | Paired worlds |
|---|---:|---:|---:|
| C2 | +0.250 | [+0.09375, +0.4375] | 16 |
| C4 | +0.375 | [+0.125, +0.6875] | 16 |
| C6 | +0.500 | [−0.09375, +1.000] | 16 |

UNPARENTED C4 also exceeds SEED in reads: +0.28125, interval [+0.0625, +0.53125]. Therefore ordinary unparented training also changes the access policy. Do not describe all post-sleep change as parenting-specific.

## Task outcomes, secondary

| Checkpoint | GUIDED correct | UNPARENTED correct | Difference, percentage points | Pointwise 95% interval, percentage points |
|---|---:|---:|---:|---:|
| C2 | 28/32 | 25/32 | +9.375 | [0, +25] |
| C4 | 30/32 | 29/32 | +3.125 | [−6.25, +12.5] |
| C6 | 27/32 | 26/32 | +3.125 | [−12.5, +18.75] |

Frozen SEED is 26/32. These trajectories are not monotonic. Even GUIDED C4 versus SEED (+12.5 percentage points) has interval [−3.125, +31.25]. These exploratory pointwise intervals are not multiplicity-adjusted significance tests, and zero at an interval boundary is not exclusion of zero.

## What the controls establish—and do not

The separate TRAIN audit verifies **32 delivered GUIDED interventions through C4 versus none in UNPARENTED**, shared initial weights, ordered tasks and available source observations. C2 and C4 have equal optimizer updates and matched row-presentation schedules; C6 does not have equal updates. Through C4 the guided arm has 29,840 new supervised-token presentations versus 26,144. Longer child continuations could mediate a total parenting-system effect; these runs do not isolate a token-matched effect of parent text alone. Recipe/sampler equivalence is awaiting a bounded addendum.

Intervals resample **16 paired worlds**, keeping their two tasks together, with 2,000 bootstrap draws and seed 0. They are conditional on these fixed checkpoints and this fixed source store. There is only one historical training trajectory per arm: no training-seed replication, no claim of population-level causal improvement, no FINAL reproduction, and no changed task family.

Next decisive evidence requires a prospective test of **content-sensitive evidence use and actual feedback-recovery opportunities**, followed by independently trained lineages. This report does not silently redefine the objective as increasing READ counts, and does not stop or tune current parenting lives on their game scores.

## Analysis and operational receipts

- IO and descriptive analysis: 49 native CPU tests passed; full running producer source remained unchanged.
- Literal-shape audit: `gpu/orch_r127_protocol_shape.py`, six local and six native CPU tests passed; `PROTOCOL_SHAPE_1.json` binds the verified result and exact raw capture hashes. This audit is explicitly post-hoc and performs no model calls.
- A separate reader (the reducer's author, not an independent implementation) checked the compact artifact hash, all reported key numbers, denominators and interpretation caveats. It checked intervals as reported; it did not independently recompute the bootstrap from world-level data.
- After all assay processes exited, the pre-armed owner verified process absence and fresh GPU admission, then issued generation-resume launch receipts at approximately **20:26:39 UTC**. Subsequent owner verification binds the first genuinely new call, **21260/B302P19 at 20:27:36 UTC**, and 431 completed new responses by 20:37. Both continual-training arms also adopted C3; the control's new target labels remain masked. These are operational continuity/ingestion results, not evidence of richer thinking. No checkpoint, optimizer or old logical input was reset or replayed. See `research_notes/analysis/orch_r109_l1_20260915/R119_FINAL_VERIFICATION_2037.json`.
