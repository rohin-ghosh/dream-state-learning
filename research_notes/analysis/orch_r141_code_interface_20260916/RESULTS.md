# R141 independent result verification

**COMPLETE_INDEPENDENTLY_VERIFIED**, checked 2026-09-16 04:26:48 UTC.
Exactly the Main-authorized ovx3 physical7 `run1`, using immutable `source_v2`.
Native start: **04:19:01.857 UTC**; supervisor exit: **04:24:19.141 UTC**.
All calls finished before the 05:40 ceiling and 06:00 reservation.

Verification here means **independent recomputation by the implementation
author**, not a fresh independent reviewer. The numerical observations and
evidence hashes are unchanged by this authorship clarification.

## Result in brief

**Every complete response meets the unchanged JSON-string contract: 95/95.**
There are 96 recorded calls, not 96 complete responses. BASE task index13's
draft hit the 2048-token cap and is truncated. It remains in planned stage
denominators but is excluded from both complete-draft paired comparisons.

**Actual feedback produces no failed-to-passed correction in either model.**
BASE neutral review recovers two complete draft sandbox failures; actual
feedback regresses one previously passing BASE draft. These are descriptive
observations from this fresh cohort, not evidence of retained learning or a
causal improvement over the historical prompt.

## Formatting and strict finite-check correctness

All stage denominators are **16 planned tasks**; all 16 calls per stage exist.
Passes below require terminal, non-truncated output and the original scorer.
The recorded strict pass counts equal these eligible counts in this run.

| Model / stage | Complete / planned | Format-valid / complete | Safe-expression / complete | Strict passes / planned |
| --- | ---: | ---: | ---: | ---: |
| FULL draft | 16/16 | 16/16 | 10/16 | 5/16 |
| FULL actual feedback | 16/16 | 16/16 | 9/16 | 5/16 |
| FULL neutral review | 16/16 | 16/16 | 9/16 | 5/16 |
| BASE draft | 15/16 | 15/15 | 8/15 | 8/16 |
| BASE actual feedback | 16/16 | 16/16 | 9/16 | 8/16 |
| BASE neutral review | 16/16 | 16/16 | 12/16 | 11/16 |

Format validity does not establish allowed expression syntax, integer return,
or correctness. Among complete drafts, FULL has six sandbox failures and one
interpreter failure; BASE has seven sandbox failures. No complete draft is a
JSON parser failure. The sole recorded parser failure is the truncated BASE
draft, not a complete unquoted-expression response.

## Draft-to-fork changes and corrections

Counts here exclude incomplete draft/revision pairs. All 32 stored triplet
summaries were verified, but only 31 triplets have three complete responses.

| Model / fork | Complete pairs | Failed drafts | Failed→pass | Format recovery | Semantic correction | Raw text changed | Validated AST changed / comparable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FULL actual feedback | 16/16 | 11 | 0/11 | 0 | 0 | 2 | 1/9 |
| FULL neutral review | 16/16 | 11 | 0/11 | 0 | 0 | 1 | 0/9 |
| BASE actual feedback | 15/16 | 7 | 0/7 | 0 | 0 | 4 | 0/7 |
| BASE neutral review | 15/16 | 7 | 2/7 | 0 | 0 | 6 | 0/8 |

The predeclared `semantic_correction` field requires safe expressions on both
sides. BASE's two neutral recoveries start with **sandbox-rejected expressions**,
so they are genuine strict failed-to-passed/interface recoveries but not counted
in that narrower field. Zero semantic corrections does not mean no improvement
in those two responses. There are five safe-but-failing FULL draft expressions
and zero safe-but-failing BASE draft expressions among complete pairs.

Parsed expression-text changes are respectively **2, 1, 4, 6** in table order.
AST comparisons are unavailable for rejected expressions; unavailable is not
equivalent to unchanged. No unquoted/truncated candidate was recovered or
reinterpreted to manufacture an AST comparison.

## Paired actual-feedback versus neutral comparison

Both forks share the exact same original draft. This comparison includes only
triplets with complete drafts and complete responses in both forks.

| Model | Complete triplets / planned | Both pass | Feedback-only pass | Neutral-only pass | Both fail |
| --- | ---: | ---: | ---: | ---: | ---: |
| FULL | 16/16 | 5 | 0 | 0 | 11 |
| BASE | 15/16 | 7 | 0 | 3 | 5 |

On the **seven common-complete failed BASE drafts**, neutral alone recovers two,
feedback alone recovers zero, both recover zero, and five remain failures.
The third neutral-only pass in the overall table is the feedback regression
from a previously passing draft. FULL has no recoveries among its eleven failed
drafts and no regressions. The truncated BASE draft's two later responses remain
in stage totals, but no correction is attributed from that incomplete baseline.

## Verification, caps, and limits

- Rechecked **96 INTENT, 96 CALL, 96 PUBLIC, 96 VERIFY, and 32 COMPLETE**
  receipts; rejected missing/extra/retry artifacts. Independently reconstructed
  all prompts, real feedback, neutral withholding, shared-draft hashes, strict
  scores, and saved R141 pair metrics, including the terminal summary.
- **427 run artifacts**, two configuration/authorization artifacts, and the
  exact **2,649-file source set** are hash-bound; inspected bytes were stable.
  Main's guard, plan, tasks, exclusions, and exact launch receipt match pins.
- Token cap **2048 per call**, 96-call ceiling, context limit32768; recorded
  output tokens total **6515**, versus maximum196608. The sole cap-hit draft is
  identified explicitly in `RESULT_VERIFICATION.json`.
- Same fixed FULL18404/base identities; zero optimizer/admission/parent calls
  in the collection receipts. Loaded adapter identity and the successful
  weights-unchanged native terminal were verified; no weight-file rehash or
  model/tokenizer execution was performed by this reducer.
- **15 reduction-specific CPU tests passed** in16.556seconds, including
  tampered scorer/public/fork/metric receipts, token overflow, retry artifacts,
  incomplete-pair denominators, and completion/hash gates. Exact test and
  read-only node commands plus reducer hashes are in `RESULT_VERIFICATION.json`.

Exact audit-script backups are preserved outside `source_v2`, under
`/localhome/local-rohing/orch_r141_code_interface_20260916_attempt1/audit_source/`:

- `orch_r141_independent_reduction_20260916_0420.py`:
  `1309e9b31a32d0f9750ba953a314b48631693ccdb2c2d423a298ffaf40d5d52e`.
- `orch_r141_independent_reduction_20260916_0420_test.py`:
  `dc3ba3241185c579095543018809347de5fc0978e69780bb24cee7bc4fb189b5`.

Both backup hashes match the original `/tmp` scripts exactly. The test script
retains its original `/tmp` import path; no portability edits were made to the
archived bytes. `source_v2` and all result observations remain unchanged.

Run evidence SHA256:
`08f870b86ae0a43fd14a8df2e2499a51e7c49a2b82814d2396b6b9bdb1612003`.
96-call-set SHA256:
`91d3e199a5bd9d856e26b07224fbfa6bb3f5eb43dd397f8fec398d416ca2130c`.

This is an exploratory PUBLIC TRAIN interface/control result, with sixteen
shared task clusters, not96 independent samples. There is no old-prompt matched
control, four-way benchmark, retention test, or richness-specific causal claim.
Historical canonical scores remain unchanged. Inventory coverage remains
Main's declared bounded hash-only inventories, not global semantic disjointness.
Raw content stayed on node; this worker made no calls, signals, launches,
redispatches, Git operations, shared-ledger edits, or pinned-source changes.
