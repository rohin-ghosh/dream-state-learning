# R136 completed author reduction — 2026-09-15

**No successful task correction and no feedback-versus-neutral correctness lift.**
The completed author reduction agrees with Main's preliminary counts. It is an
author-side evidence check, not a replacement for Main's independent review.

| Frozen model state | Draft correct/planned | Actual feedback correct/planned | Neutral correct/planned | Common complete triplets |
| --- | ---: | ---: | ---: | ---: |
| FULL checkpoint18404 | 4/16 | 4/16 | 4/16 | 15/16 |
| True base / no LoRA | 0/16 | 0/16 | 0/16 | 16/16 |

FULL has 15 complete responses per stage: correctness is 4/15 among complete
responses, while **4/16 remains the planned-denominator result**. Task index 3
(zero-based) hit the token cap for draft, neutral and feedback: calls 22–24.
All BASE responses completed, but all 48 failed the expression-JSON parser.
Do not interpret parser failures as a direct measure of underlying semantic skill.

## Corrections and paired controls

| Complete draft/fork pairs | FULL feedback | FULL neutral | BASE feedback | BASE neutral |
| --- | ---: | ---: | ---: | ---: |
| Complete pairs | 15 | 15 | 16 | 16 |
| Failed-draft pairs | 11 | 11 | 16 | 16 |
| Failed→passed task checks | 0 | 0 | 0 | 0 |
| Strict formatting-only recovery to a passing expression | 0 | 0 | 0 | 0 |
| Task-semantic correction | 0 | 0 | 0 | 0 |
| Interface execution-error recovery | 2 | 0 | 0 | 0 |
| Regression from passed to failed | 0 | 0 | 0 | 0 |

The two FULL interface recoveries (task indices 11 and 15; feedback calls 72 and
96) move from sandbox rejection to executable expressions that **still fail task
checks**. They are execution-only improvements, not formatting-only success,
semantic recovery, learning or admission candidates. FULL sandbox failures fall
from 5 at draft to 3 with feedback; task-check failures rise from 6 to 8. Neutral
retains the draft distribution. The same four FULL passes persist in both forks.

On the common complete triplets, FULL has 4 both-pass, 11 both-fail, 0 feedback-only
and 0 neutral-only passes: feedback-minus-neutral correctness difference **0/15**.
BASE has 16 both-fail and no passes: difference **0/16**. Among common failed
drafts, successful-correction contrasts are 0/11 FULL and 0/16 BASE. Do not pool
the 96 calls as independent trials or conceal the capped FULL triplet.

## Completion and integrity

Node-local re-derivation completed at **2026-09-15 22:26:20 UTC** from
`/localhome/local-rohing/orch_r136_code_feedback_20260915_attempt1/run1`:

- **96 CALLs, 96 INTENTs, zero FAILURE files; all 96 cells retained.** There are
  93 complete responses and 3 truncated responses, not 96 complete responses.
- **425 artifacts verified**: exact source/task/exclusion pins and regeneration,
  every reservation and native prefix, 32 shared drafts, 32 actual-feedback
  prefixes and 32 neutral prefixes; all PUBLIC/VERIFY/correction/terminal receipts
  rederived from actual responses. No gold/expected output in supplied feedback.
- Snapshot stability passed. Native/episodes COMPLETE and exit 0 are bound to
  SUPERVISOR_COMPLETE by the native-terminal hash. Launch→GUARD and
  launch→privileged clear ADMISSION hashes also match; physical index/UUID,
  checkpoint and deadline bindings agree.
- Native unchanged-weight completion receipt verified; loaded optimizer count 0.
  The reducer did **not** rehash weights, invoke a model or load CUDA.
- Reducer tests: **23/23 local CPU** (4.119 s) and **23/23 node CPU** (3.118 s).
  Node tests used synthetic fixtures only, outside the frozen source tree.

## Pinned hashes

| Artifact | SHA256 |
| --- | --- |
| GUARD | `9ab84cb88a4e1e8a8314cf7e5f017ea05527f891c83715801c718b87fd6ccc0d` |
| PLAN | `4e6c6093b50d0ec3b79be50134a60cb9f5796da8034bf85b2b65bdc50e987195` |
| NATIVE_TERMINAL | `2b985f3641a739c1f74d2868e8635e197aeba39ae05aff10a6000bd65b6043e4` |
| SUPERVISOR_COMPLETE | `4be1dfd6a5f55d6e4642a825956e1bc8931008bcad7caaf5c30644dfd3035685` |
| Reducer source | `4ccb153dce13f23846fe8a3e69c0dda23c9c0d8a393fd2c7d00cb4233144ea19` |
| Reducer tests | `efef093152a54352970c41ec8001f28478cfb6b45a2573d37d58b6147f0fe0bf` |
| Full node-local reduction | `d4080ff2bb8dfc34d976bc21c801f1943b85f0cbd7264ddf74a61a2238029a01` |
| Compact RESULTS JSON | `6aac5f0b942eb3a06336d9c258ddc3373f71db5a4a1500162cef8f0635f3fd88` |

Full proof-bearing reduced output remains beside the run as
`REDUCTION_R136_AUTHOR_20260915.json`; its evidence-map digest is
`230723f22a5f69ac5d0fb45911587741e756bdc94b5c1a7c4af4f84a0fcfb748`.
The compact JSON is 18,720 bytes and retains every cell's outcome/category and
correction flags, per-model denominators and paired contrasts. Raw text, prompts,
expressions, token IDs, probe outputs, raw errors and tasks were not exported.

## Scope and disposition

R136's pinned bounded exclusion inventory contains **70 specification hashes,
96 task-ID hashes and 1 seed hash**, including `R133_FAILED_ALL_PLANNED_CODE`.
Projection-union verification belongs to Main's guard; this author reduction did
not reread old or held task contents. **Failed R133 remains separate, unchanged,
not pooled and not replayed.** No source/guard mutation, new model/provider call,
fitting or training admission occurred in this reduction.

This is exploratory immediate PUBLIC TRAIN behavior on sixteen task clusters,
not retained learning, persistence, metacognition or confirmatory causal evidence.
Passing means the finite fresh-task CPU checks passed, not universal correctness.
No automatic scientific promotion or dataset admission follows.

Exact repository write allowlist for this results handoff:

- `research_notes/analysis/orch_r133_code_feedback_20260915/RESULTS_R136_AUTHOR.json`
- `research_notes/analysis/orch_r133_code_feedback_20260915/RESULTS_R136_AUTHOR.md`

New node-local reporting helpers/results were placed only outside the frozen
source: `REDUCTION_AUTHOR_4ccb153d.py`, `REDUCTION_AUTHOR_TEST_efef0931.py`,
`REDUCTION_R136_AUTHOR_20260915.json`, and `RESULTS_R136_AUTHOR.json`.
