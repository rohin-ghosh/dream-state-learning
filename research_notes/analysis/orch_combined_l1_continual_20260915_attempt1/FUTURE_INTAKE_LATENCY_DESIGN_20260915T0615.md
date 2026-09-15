# Future intake latency: CPU-only recommendation, not an active sampler

Status: DESIGN ONLY. No live source, optimizer, RNG, cursor, corpus, allocation,
readout registration, or admission-policy changes. No new calls requested.

## Verified readout reservation

The exact native ledger in `READOUT_BUDGET_DOSE_20260915T0613_COMPACT.json` contains
1,408 completed/reserved calls: historical prompted P64 224, minimal P64 128,
true no-adapter BASE 64, and intermediate DEV 992. The authorized ceiling is
1,824: original 1,760 plus the separately authorized BASE64. **416 remain**.

All remaining calls belong to the already registered TERMINAL paired panel:

| Per arm | Held items | Maximum native calls | Token cap |
|---|---:|---:|---:|
| Math, same frozen minimal-prompt cohort | 64 | 64 | 1,536 |
| Route, registered first four worlds / sixteen goals | 16 | 96 | 1,536 |
| Legacy retention/audit | 48 | 48 | 160 |
| Total per arm | | 208 | |

Both arms use fresh parent-free processes and matched saved checkpoints. The
route action protocol is unchanged, not a request for free-form rich explanation.
These reused panels are adaptive DEV, not a new confirmatory H1 holdout.

All new375 received their first presentation by update3647: FULL at
06:09:47.873973Z and OFF at06:09:48.089151Z on September15. Checkpoint3684 is a
verified matched post-coverage checkpoint, **but the active guard does not
schedule a readout there**. No second intermediate panel is currently reserved.

The next registered readout occurs at the first matched durable 128-update
boundary whose guard check reaches the training deadline **07:03:10.779610Z**.
The terminal update number is not fixed prospectively: at the audited
FULL3829/OFF3830 snapshot, measured last384 wall-clock steps were 1.05327/1.05217
seconds per update, projecting **boundary6756 around07:04:40–07:04:45Z**.
This is an estimate, not a launch commitment: future content, checkpoint I/O,
and shared-node conditions change throughput and hence the boundary number.

Previous parent-free processes took approximately 657s FULL math and923s OFF
math including about59s load. Route now has one quarter of the intermediate
call allowance; legacy took169s per arm. With the existing three-device
dispatcher, comparable behavior suggests about15–20min after launch, roughly
07:20–07:25Z under that projection. Longer generated outputs can take longer.
The dispatcher enforces at most1,980s (33min), bounded also by native deadline
08:03:10.779610Z; global hard end remains08:06:10.779610Z. Failed/reserved calls
are charged, failures preserved, no retry or extension. These are not extra calls.

If a post-coverage readout is wanted immediately, it would have to **relocate
this same416-call reservation** to a prospectively recorded earlier boundary,
not add another panel. That would replace, not supplement, the terminal readout.
No such relocation is made by this recommendation.

## Exact incremental dose at matched checkpoint3684

These are continual-child counters, not sums with the separately archived
math764 fit or inherited route-child history. FULL and OFF presentation arrays
are exactly identical at3684; OFF labels on nonlegacy rows remain masked.

| Group | At ingestion2020: presentations | At3684: presentations | At3684 row-dose distribution |
|---|---:|---:|---|
| Legacy memory128 | 2,020 | 3,684 | 100 rows×29; 28×28 |
| Legacy cue20 | 500 | 900 | 20×45 |
| Legacy audit62 | 1,520 | 2,784 | 56×45; 6×44 |
| Legacy trajectories12 | 24 | 36 | 12×3 |
| Original3260 corpus rows | 4,016 | 6,957 | 437×3; 2,823×2 |
| Newly added375 | 0 | 375 | 375×1 |
| Entire four-row batches | 8,080 | 14,736 | exactly4×logical updates |

Within original3260, SEQ266 has1,452 rows:437 have three presentations and1,015
have two (3,341 presentations). Every remaining original corpus row has exactly
two: MATH7641,528; MATH_RICH1938; MATH_RECORD92184; INTENSITY56112; TWO_PASS916;
FULL_RICH36; delta76152; readmission473946; original sampled64128; sampled003126;
sampled020128; sampled021124; sampled024128. Exact group histograms are in the
compact dose receipt, including2020 values.

New batches027/033/034/036/038/040 have64/62/62/63/62/62 presentations at3684,
one per row. Full supervised tokens are1,205,635, masked OFF218,395; both use
reference total1,205,635. Old physical OFF recovery adds117 separately charged
updates; logical retained3684/cell is not inflated by those replayed updates.

First new375 exposure was update3460, **1,440 updates and28min31.1s after
ingestion2020**. Source admission, corpus inclusion, target presentation,
supervised-token exposure, and demonstrated learning are separate milestones.

## Recommended future mechanism: FIFO first-exposure swaps

Recommend a small, versioned first-exposure FIFO and a ledger of displaced
rehearsal presentations, rather than resetting the corpus-wide modulo cycle or
adding extra optimizer steps. It remains whole-row replay, never target editing.

1. At an approved future paired intake boundary, append qualified external
   rows once by batch ID/hash. Eligibility, held exclusions, exact encoding,
   source/gold binding, teacher/L2 quarantine, and historical labels stay intact.
2. Freeze the unexecuted reference schedule and row IDs for an explicit finite
   accounting horizon. Preserve **every legacy222 slot in its original place**,
   including the twelve legacy trajectory rows, not just the first two rows.
3. Select at most one eligible nonlegacy trajectory slot per update for the
   oldest not-yet-presented row. Order uses admitted batch order and row index,
   never semantic scores, target length, held behavior, or treatment outcomes.
4. Swap that fresh row's planned later first-occurrence ticket with the old
   nonlegacy row displaced from the early slot. The displaced rehearsal is
   repaid at the reserved later slot. No presentation is silently discarded,
   padded, duplicated, or added. Keep the other trajectory slot rehearsing.
5. FULL/OFF consume the exact same resulting four-row schedule; only the
   existing OFF new-label mask differs. Preserve optimizer state, all RNGs,
   global update, and normalization rule. Save queue, ticket/repayment ledger,
   immutable plan hash, row exposure counts, and intake cursor transactionally.
6. Replan only an explicitly recorded unexecuted suffix for subsequent intake.
   Never move executed or previously credited tickets; record plan-version
   changes prospectively. New arrivals must not silently rebind prior promises.

For a **fixed V13 counterfactual only**, the included CPU integer-slot analysis
swaps375 first-exposure tickets over updates2021..3647. It verifies:

- First exposure moves from3460 to2021; all375 move from3647 to2395.
- One fresh priority presentation per early update; the other trajectory slot
  retains rehearsal. Every legacy222 slot stays exactly where it was.
- The complete four-row schedule's multiset over that accounting horizon is
  identical; displaced old-row doses are repaid by3647.
- FULL/OFF would share one plan. No model, checkpoint, or training process was
  accessed by this simulation. It does not certify a production implementation.

This is an **update-count** latency illustration, not a wall-clock claim:
front-loading longer targets can increase step time. A prospective service bound
must include the next intake-boundary wait (up to128 updates), existing FIFO
backlog, one eligible service opportunity per update, and protected-legacy gaps.
Compute the bound from the frozen schedule; do not assume every update is eligible.
No finite uniform guarantee is possible with unbounded arrival rate. Publish
backlog and feasible capacity; overflow remains qualified but explicitly lacks
the same latency promise, rather than being silently dropped or requalified.

## Why this changes interpretation even with dose repayment

- Until repayment, fresh rows have higher dose and recency and old nonlegacy
  rehearsal has lower/delayed dose than the original schedule.
- AdamW updates are order-dependent: weights, momentum/variance estimates, and
  interactions with later examples differ even after the final row multiset matches.
- Batch composition changes the actual global reference-token denominator and
  row weighting under the unchanged normalization formula. Equal end-window
  supervised-token totals do not mean identical per-step optimization.
- Variable target lengths can change throughput and therefore dose attainable
  before the same wall-clock deadline. Snapshot timing itself is a confound.
- FULL/OFF under the new shared plan tests new-label supervision under that
  plan; it does not alone identify the effect of FIFO versus the old sampler.

Thus a future phase must be labeled as a schedule intervention, anchored to a
paired checkpoint with explicit per-source doses. Do not pool its results with
the current schedule as if only corpus richness/breadth changed. A causal claim
about latency-aware scheduling needs a separately budgeted future schedule
comparator; otherwise report the phase descriptively, with these confounds.

## Required prospective scope and tests before any implementation/launch

- Pin intake boundary, reference horizon, FIFO ordering/capacity, protected
  legacy calendar, repayment rules, allowed source registries, and claim limits.
- Test real whole-row inputs, EOS/native boundary and OFF mask; exact matched
  FULL/OFF batches, label counts, global-reference normalization, and rank-local
  nonempty losses for current three-rank/two-rank partitions.
- Property-test legacy-slot preservation, end-horizon multiset/token counts,
  starvation/overflow bounds, ticket conservation, and no semantic selection.
- Test atomic exactly-once ingestion, duplicate/rebound manifests, interruption
  before/after ticket movement, resume with all optimizer/RNG/cursor state, and
  concurrent arrivals without changing executed schedule entries.
- Retain held/source/teacher quarantine and original deadline/call accounting;
  pre-GPU CPU/native equivalence and provenance receipts are still required.

The current native sampler is untouched. This document and the fixed integer
simulation are recommendations, not a new prospective approval or live config.
