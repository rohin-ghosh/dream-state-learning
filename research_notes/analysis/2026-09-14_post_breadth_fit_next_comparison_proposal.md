# Post-breadth next-fit choice — bounded scientific proposal

2026-09-14. **Advice for Main, not a fit protocol, admission, launch request,
checkpoint promotion, or efficacy claim.** Read-only review; only this memo is
authored. Main owns rich repair, collection integration and subsequent decisions.

## Evidence reviewed and what it actually distinguishes

Sources are local records, not a fresh full ancestry or episode-level audit:

- `research_notes/analysis/2026-09-14_goal_pair_incremental_fit_design.md`
  and `2026-09-14_goal_pair_incremental_fit_first_result.md` (SEQ256).
- `research_notes/analysis/2026-09-14_goal_breadth_recipe_design.md`
  and `2026-09-14_goal_breadth_fit_first_result.md` (SEQ260). The latter
  explicitly leaves independent episode-level reduction pending.
- `research_notes/analysis/2026-09-14_goal_quality_collection_protocol.md`
  (SHA256 `cf742f62dc45810caeea3ec68272a9e1a8c97d3b7c6c06f148639252ba1738f1`).
- `research_notes/analysis/2026-09-14_rich_trajectory_collection_protocol.md`,
  the parallel recipe design and prediction-gate successor proposal. A proposal
  is not evidence that a repaired collection has completed or been admitted.
- Message 69 in `research_notes/THESIS_RAW_ROHIN_2026-09-11.md` and Main's
  stage-specific response in `research_loop/COORDINATION.md`.

| Endpoint | SEQ256 FULL / loss-off | SEQ260 FULL / loss-off |
|---|---:|---:|
| TRAIN goals | 8/8 / 3/8 | 32/32 / 17/32 |
| TRAIN opposite-goal pairs | 4/4 / 0/4 | 16/16 / 4/16 |
| PROBE goals | 5/8 / 5/8 | 5/8 / 6/8 |
| PROBE pairs | 2/4 / 2/4 | 1/4 / 2/4 |
| Original taught graph | 2/4 / 2/4 | 2/4 / 2/4 |

These are different TRAIN/PROBE identifiers, not repeated measurements of the
same test. SEQ256 uses 400 updates and 48 new targets; SEQ260 uses 1,632 updates
and 192 new targets, with changed legacy rehearsal. It is not a controlled
coverage-only scaling curve. Both recipes give strong within-recipe TRAIN
acquisition contrasts without the required PROBE advantage or original-graph
retention. Full TRAIN success makes failure to fit the taught instances an
unconvincing reason for simply extending either completed fit.

SEQ260's unchanged 37ec baseline is PROBE 4/8 goals, 0/4 pairs; the active
rehearsal control reaches 6/8, 2/4. Thus FULL's improvement over baseline alone
does not isolate new-trajectory benefit. Both trained states still fail one
PROBE world entirely at the pair level. FULL retains old memory 16/16 at both
wrappers, audit 15/16 and previously fresh graph 4/4; the original graph falls
from 3/4 to 2/4. Exact recall retention is not sufficient behavioral retention.
Small, exposed DEV endpoints do not establish that scale cannot work, that
richness will work, or that either mechanism has been identified.

## Recommended first choice: two matched rich-loss fits, if data qualify

Prefer a **RICH versus RICH_ACTION_ONLY** comparison to an immediate maximum
quality-corpus dose. It asks a new, narrow question: does supervising the actual
grounded articulation add useful behavior beyond action supervision at the
same teacher-forced inputs? A separate TERSE fit is informative about format
and conditioning, but not necessary to answer this first question. Omitting it
means this comparison cannot establish superiority to a terse-output recipe.

Start both from unchanged state
`37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`,
not either SEQ260 adapter. Keep frozen base/rank8, fresh AdamW 3e-5, seed0,
batch4 and the same 222 legacy rows. No critiques enter this first fit.
Both arms receive identical admitted rich responses, public prefixes,
tokenization, padding, EOT and schedule. Only the rationale/envelope labels
differ; actual action and EOT labels remain active. Scale the action-only
mean loss by active/full-reference label count per batch. This is an added
supervision comparison, not equal active-token compute or verified reasoning.

Rohin69's floor is **useful grounded content AND successful outcome**, not
length, a literal prediction heading, or successful commands alone. Before
encoding, bind Main's repaired source/visibility contract and content rubric;
apply it without arm or PROBE information. For this proposed fit, additionally
retain opposite-goal pairs only when both six-turn episodes pass, identically
in both arms. This is a proposed shared fit-admission rule, not a rewrite of
rich v1's episode-level candidate records. Preserve all rejected counterparts.
Require at least eight represented TRAIN worlds and at least one admitted pair
from each of the four fixed rich shards; this is an operational coverage floor,
not a statistical power calculation. Use all qualifying pairs, not a favorable
shard or score-selected subset. Maximum remains 384 new rows across 16 worlds.

For actual admitted new-row count N, propose exactly 16 presentations per
trajectory target, including the old12: U = 8*(12+N), at most **3,168 updates
per arm**. Slots 0/1 cycle the old128 memory and old82 cue/audit rows; slots2/3
cycle the 12+N trajectories. Freeze N, masks and dose ledger before gradients.
Do not substitute the unexecuted original 32-update rich design or silently
increase dose following a poor readout.

## Quality corpus: useful alternative, not the rich loss control

Quality preserves actual command data from 61 source-eligible TRAIN worlds,
with at most 1,452 admitted rows; it measures outcome-filtered command
experience, not Rohin69's content floor. The 756 reused rows are candidates;
the newly collected yield is not asserted here. Preparation PASS and requested
guardians are operational progress, not a terminal dataset or fit result.

If rich data do not meet the shared floor when quality assembly is ready,
the bounded alternative is **one FULL versus new-label-loss-off quality pair**,
not automatic six-seed maximum scale. Use every admitted pair in the assembled
corpus, including reused provenance and attrition, without ranking worlds by
scores. Keep the same parent, optimizer and 222 legacy rows. Propose four
presentations per new target but preserve 16 presentations per old trajectory:
an explicit trajectory-slot list has old12 repeated16 times followed by newN
repeated4 times; consume two consecutive entries per update. Hence
U = 96+2*N, at most **3,000 updates per arm**; memory/cue-audit slots each have
U presentations. Mask only new labels in loss-off and use the shared full-label
denominator. Both arms use the identical order; no score-based reshuffling.

This tests wider actual command coverage at a bounded lower new-target dose.
It is not a pure scale contrast with SEQ260, and a null would not rule out a
higher-dose quality recipe. Rich and quality differ in worlds, source filtering,
format and dose, so their raw accuracies cannot estimate a richness effect.
Do not run both alternatives automatically or blend their corpora in this
first comparison; either would obscure the immediate question and spend the
budget twice. Parallel collection/content review can continue independently.

## Readout, hard budget and stopping rules

**Proposed reservation: two fits, one seed, at most 9.3 allocated GPU-hours
including a baseline allowance; zero new source/teacher calls for fitting.**
Per trained arm: at most 10,800s TRAIN + 3,600s fresh AFTER + 300s admission
+ 60s teardown = 14,760s (4.1h); two arms = 8.2h. Allow an additional baseline
process up to 3,600s + 300s admission + 60s teardown = 1.1h only if existing
baseline captures are not exactly compatible. These are proposed ceilings,
subject to Main's physical/lease admission, not promises of runtime.

SEQ260 measured about 3,150s for 1,632-update TRAIN and 341–345s AFTER.
Naive linear TRAIN extrapolation gives approximately 102 minutes for 3,168
updates and 97 minutes for 3,000, before accounting for rich sequence length.
Longer teacher-forced prefixes/targets can invalidate that estimate. CPU
admission must report actual lengths and active/reference token doses; if the
reservation is not credible, defer rather than truncate targets or extend a
completed fit. No sweep, best checkpoint, repeated seed, or adaptive early stop.
A timeout preserves partial evidence; no automatic repeat fit follows.

- Rich: all four fixed PROBE worlds, both OWN_TEXT/UNAVAILABLE = <=192 calls
  per state. Add old W0/W8 (32), audit (16), original/fresh graphs (48), and
  four preselected TRAIN worlds, one per shard, OWN_TEXT (96): **<=384/state**.
  Select diagnostic TRAIN IDs before content outcomes; never refill failures.
  Three states including unchanged parent cost <=1,152 readout calls total.
- Quality alternative: retain all16 original PROBE worlds and both conditions
  (<=768), the same 96 retention calls, and four fixed TRAIN worlds (<=96):
  **<=960/state; <=2,880 across three states**. Preserve the bad PROBE address
  as literal MEMORY UNAVAILABLE, with its other three actual EVENTs intact;
  denominator stays 64 goals/32 pairs, with missing-source results stratified.
- Use shared actual child source text, task order, parser/action caps and public
  prompts across states. This measures text-supported action use, not new
  parametric memory acquisition. Existing baseline reuse requires exact
  source/task/prompt compatibility. Rich collection's command-only baseline
  cannot stand in for a newly articulation-permitting prompt without checking.
- For rich, use the same bounded public envelope-or-command interface for both
  arms and baseline, without coaching; report parser failures separately from
  semantic/action failures. Assess useful grounded articulation on every
  planned PROBE task, not only successful/verbose episodes. Missing or rejected
  content remains failure on this content endpoint, not an exclusion.

## What would change the next decision

Freeze exact decision criteria before a fit; suggested operational targets are
at least 6/8 rich PROBE pairs (quality:24/32), at least one in each world,
old memory >=15/16 per wrapper, audit >=15/16, original/fresh graphs >=3/4.
Require an incremental strict-pair advantage over BOTH the matched fit control
and compatible unchanged-parent baseline; an absolute threshold alone is not
enough. These small DEV thresholds are not statistical significance claims.

For the rich choice, additionally report the all-planned-task rate meeting
outcome AND the fixed stage-specific content rubric; require an increase over
both reference states to justify investing in rich baseline behavior. Length
and a few good examples are insufficient. Improvement on actions alone would
not meet Rohin69's joint aim; articulation alone would not resolve SEQ260.

If rich beats action-only on this joint endpoint and pairs while preserving
retention, the next informative expenditure is a prospectively matched TERSE
projection or replication, not immediate maximum scaling. If both fit arms
improve similarly, rationale-label benefit remains unshown. If only TRAIN
improves, close that finite recipe. If quality wins its controlled comparison,
invest next in whether the benefit survives adequate repetition/retention,
without crediting rich supervision. If either loses the old taught graph,
do not promote it merely because recall remains exact.

No outcome here would establish internal reasoning, autonomous parenting,
whole-life superiority, population efficacy, clean lineage, or H1/H2. This
memo proposes one decision-sized comparison; Main retains the actual choice.
