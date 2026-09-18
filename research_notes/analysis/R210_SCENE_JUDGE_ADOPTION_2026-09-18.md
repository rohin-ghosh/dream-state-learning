# R210 completion and scene-aware judge transition

Verified 2026-09-18 18:09 UTC from the original ovx5 artifacts. This is an
operational benchmark-version transition under the explicit supervisor order,
not a preregistered result or evidence that the learning hypothesis is true.

## Completed training

| Adapter | Completed UTC | Total comparisons | Updates | New-phase comparisons | New-phase pairs/s |
| --- | --- | ---: | ---: | ---: | ---: |
| Rank 8 | 2026-09-18 14:19:28 | 1,000,000 | 15,625 | 990,720 | 30.691 |
| Rank 16 | 2026-09-18 14:19:55 | 1,000,000 | 15,625 | 990,784 | 30.537 |

Throughput is the training artifact's `phase_pairs_per_second`, not end-to-end
game throughput. Rank 8 retained 145 earlier updates, then used 247,680 crossed
and 743,040 within-contest comparisons. Rank 16 retained 144 earlier updates,
then used 247,696 crossed and 743,088 within-contest comparisons.

## Selection-rule mismatch

The original Spearman-only selector chose rank-8 step 146 and rank-16 step 145,
near the warm start. Its objective did not cover the scene-awareness defect it
was meant to repair. On the recorded six-type contrast battery those selected
checkpoints scored only 51/100 and 47/100 on other-contest comparisons. Final
step 15,625 scored 90/100 and 89/100, respectively. These are exact 100-case
diagnostics; do not substitute differently sized warm-start audit percentages.

Rank-8 macro mean-rating Spearman fell from 0.273879 at selected step 146 to
0.251140 at step 15,625. Rank-16 fell from 0.277172 to 0.245333. The two final
scene accuracies differ by one case; this is not an equivalence test.

## Six-type diagnostic counts

Every entry is wins out of 100; the new rank-8 battery has no ties or skips.
The widegap column is the supervisor's supplied historical comparison, not a
newly executed side-by-side evaluation. The rank-8 and rank-16 columns are
existing checkpoint diagnostics; a fresh adopted-checkpoint rerun is separate.

| Contrast | Historical widegap-6250 | Rank 8, step 15,625 | Rank 16, step 15,625 |
| --- | ---: | ---: | ---: |
| Word shuffled | 100 | 97 | 98 |
| Scene description | 100 | 97 | 95 |
| Nonsense | 99 | 96 | 95 |
| Truncated | 94 | 93 | 92 |
| Mid-tier | 74 | 77 | 73 |
| Other contest | 51 | 90 | 89 |

## Adopted target and receipt requirements

The ordered target is rank-8 step 15,625, with adapter SHA-256
`a070b28ef0bf1f57ad994e5bd715db77e2649d196960cea422971523696be3c4`
(10,114,552 bytes); config SHA-256
`57e7a77670d826d004b3849b8694f7042036f6ce80c5ca4f6464c1c3b9c09649`.
No model bytes are committed. The receipt is not the unrelated P7
`ADOPTION.public.json`.

At this note's cut, the scorer owner is implementing the transition. This note
does **not** claim that an old resident scorer already loaded the new adapter.
Each player needs an actual judge binding and explicit epoch boundary. Rank
threshold remains 50. Old/new counts must never be summed into one apparent
learning curve. For the transition hour, identical candidate strings need
separate old-judge and new-judge records. Re-scored seed packets and P3 history
are retrospective measurements, never new opportunities or new discoveries.

The audit's human finding that many accepted strings were plans or non-jokes
does not become a new classifier label automatically. A judge acceptance is
not certified humour. Parents may receive their TRAIN-candidate judgments and
corrections, not sealed cases, reference panels, or answer keys.

## Evidence

- `research_loop/workers/rohin233_recovery_20260918/R210_COMPLETION_AGGREGATES.json`
- `research_loop/workers/rohin233_recovery_20260918/R210_RANK16_COMPLETION_AGGREGATES.json`
- Original artifacts stay on ovx5, including both adapters, optimizer state,
  full checkpoint diagnostics, private case texts, and completed manifests.
- Rank-8 case-ID digest:
  `6763a62cf349e969c1dd7ecad0637c8718fef45572eced5a07a50406e3de66ba`.

## Actual scorer adoption — 18:22 UTC cut

The scorer owner has now produced actual loaded-weight and listener-handoff
receipts for all eight sessions. This supersedes the deployment-pending status
at the earlier note cut, but does not imply any child has supplied a new
scorable caption yet.

| Sessions | Scorer PID | GPU | Listener handoff UTC |
| --- | ---: | --- | --- |
| Five node-3 caption forks | 499900 | ovx4 GPU4 | 2026-09-18 18:17:12.803 |
| Extra node-2 caption player | 499905 | ovx4 GPU5 | 2026-09-18 18:17:11.887 |
| Continuous frozen-weight base | 506797 | ovx4 GPU6 | 2026-09-18 18:21:08.044 |
| P3 | 573479 | node4 GPU0 | 2026-09-18 18:21:35.696 |

Each session has its own epoch binding and restored prior seen-origin ledger.
The widegap shadow window starts with that player's first genuine new score,
not the earlier listener handoff. Prior cached outcomes retain their original
judge attribution. All 113 tensors, including the classifier, were checked
against each declared adapter after inference-dtype conversion. The base
player itself was not stopped for this scorer handoff. P3's scorer had an
explicit failed attempt and approximately four-minute repair gap; that failure
is retained, not relabelled uninterrupted service.

Receipts are under
`research_loop/workers/rohin233_ovx4_recovery_20260918/`:
`JUDGE_SHARED2_ADOPTED.json`, `JUDGE_SHARED3_ADOPTED.json`,
`JUDGE_BASE_ADOPTED.json`, and `JUDGE_P3_ADOPTED.json`.
`STATUS_ADOPTION_LIVE.md` records scope and remaining work. Fresh 600-case
rerun, retrospective seed/P3 rescoring, and actual new-score/Tool-rendered
outcomes are still separate receipt requirements at this cut.

## Fresh serving-path battery and retrospective check

The fresh 600-case run completed at 2026-09-18 18:24:37 UTC using the actually
adopted serving weights. In the table's order it reports **97 / 97 / 96 / 95 /
78 / 90** wins out of 100. The retained checkpoint diagnostic was **97 / 97 /
96 / 93 / 77 / 90**. The difference of two truncated cases and one mid-tier
case is retained explicitly; its cause is not established by this note. Scene
contrast remains 90/100 against the historical widegap 51/100.

`JUDGE_FRESH_CONTRAST.json` binds the case IDs, serving-weight receipt and exact
execution. It contributes no player attempts. The retrospective
`HISTORICAL_RECHECK_COMPLETE.json` contains 225 entries: 223 P3 entries and two
source-verified base seed entries. Of P3's 26 formerly accepted entries, 19
fail the new rank/relevance check; 14 P3 entries pass in total, including
entries previously rejected. Both recovered seed entries still pass. These
are entry counts, not a claim of distinct jokes. Novelty was not re-evaluated,
no game counters were incremented, and original outcomes remain unchanged.

At the diagnostic's cut, 209 P3 entries and the two seeds had verified origins
eligible for parent correction; the diagnostic itself delivered no parent
message. Parent delivery is a separate requirement, not implied by writing a
correction file. The two recovered seeds are not falsely called the complete
requested 10–12-example packet.

## Post-adoption counters — September 18, 19:57 UTC

A new read-only audit independently binds all eight per-player epoch ledgers
to the current scorer PID, start ticks, command hash and adopted epoch hash.
It counts exact distinct caption strings within each scene, separately from
scoring occurrences, inherited cached outcomes and retrospective rescoring.
Six CPU regressions cover these distinctions, incomplete comparisons and
hour boundaries. No life, scorer, parent or ledger was changed by the read.

| Player | ACT origins | Distinct scored | Distinct accepted | New pixels |
| --- | ---: | ---: | ---: | ---: |
| Frozen-weight base | 18 | 148 | 127 | 11 |
| Observation fork | 24 | 6 | 2 | 0 |
| Perspective fork | 24 | 0 | 0 | 0 |
| Revision fork | 24 | 4 | 1 | 1 |
| Selfderive fork | 16 | 2 | 1 | 1 |
| Formerly unparented node-3 fork | 21 | 0 | 0 | 0 |
| Extra node-2 player | 21 | 0 | 0 | 0 |
| P3 | 1 | 0 | 0 | 0 |

For the base's 100 same-string transition comparisons: 66 pass both judges,
four pass only widegap, 15 pass only the adopted judge, and 15 pass neither.
Those comparisons are not additional attempts. The three caption-bearing
node-3 forks have 12 paired comparisons in total. New-epoch scoring is live,
but these totals do not certify humor, establish improved exploration, or
compare equal generated-token budgets. P3's recovery is still incomplete;
its one historical post-adoption ACT is not evidence that it is now alive.

Receipt: `research_loop/workers/rohin233_recovery_20260918/JUDGE_EPOCH_AUDIT_195736.json`.
UTC-hour bins and paired counts stay separate by player and epoch. Parsed
caption totals, format faults, no-caption acts and generated tokens are not
present in these epoch ledgers; this audit leaves them unknown rather than
fabricating zeros or calling itself the complete token-normalized curve.
