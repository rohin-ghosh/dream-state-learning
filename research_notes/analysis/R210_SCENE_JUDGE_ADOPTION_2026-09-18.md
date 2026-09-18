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
