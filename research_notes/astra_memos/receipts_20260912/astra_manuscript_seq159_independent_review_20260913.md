# Independent manuscript review through SEQ159 — EDITSTOP

September13,2026. **Verdict: ACCEPT**, restricted to the SEQ159 amendments
and their current summaries in the six exact files below. No critical
correction is required. All six hashes match the author handoff; they were
checked before and after review. No manuscript/code/evidence edits occurred.

## Exact accepted six-file cut

| File | SHA256 |
|---|---|
| `paper_prototype/astra_sprint_draft_20260912.tex` | `15511ec840cae6b4eccf691be443e3553b63d80ee8e666e867cb775e96da6241` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `47ed8ae1925ef32687742d800c2b86389aeaa746d851e52c544c73f88866a4ab` |
| `paper_prototype/main.tex` | `25ef31f2d984c63c19a752c1a1d565dac71cfa97b2627c7f27fd92fd4b3c8930` |
| `paper_prototype/README.md` | `0f01329d591fe9ba60b42a0042ee3ea0aacf2b5a8af799ba8ceee05b649dbe14` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `1dda50c6c38098fdb09516c2db50b0de305e48fbe43f55529fbc851cf9499968` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `b0e5050b237fa6a398ea84d62c4a70860e069d2839ff584889767ba17145a06e` |

Author freeze: `/tmp/astra_manuscript_seq159_handoff_20260913.md`, SHA256
`488f9adc263464670f6d8c13384cb2d1bda97a6ee6139f0ac4890408cce5c32a`.
Unlike the previous review's stale-binding issue, this cut matches its handoff.
Any later byte change falls outside this verdict.

## Checked findings

1. **Partial repair, not all-seed success.** The six-row tables give REPLAY
   exact10/14,6/8,5/8; paraphrase10/14,6/8,3/8; held47/48,48/48,48/48.
   EXTRA_MEMORY gives exact13/14,7/8,7/8; paraphrase10/14,6/8,7/8;
   held47/48,46/48,42/48. REPLAY loses zero historically LR0-correct held
   and canary items in all3; this is not perfect scheduled accuracy, since
   seed0already had one wrong item. EXTRA_MEMORY loses0/2/6held items.
   All fresh canary panels remain12/12. Screens are2/3versus1/3, with
   REPLAYseed1below exact floor7; no repair/freeze conclusion is substituted.

2. **Paraphrase and the limited constant diagnostic.** Exact floors8/7/5
   plus zero itemwise retention loss do not require paraphrase superiority.
   Seed2REPLAY can therefore meet its screen while paraphrase3/8 is below
   constant4/8. Constants6/14,4/8,4/8 are evaluator-only same-panel best
   constant-target scores, not newly generated control runs or an anti-shortcut
   proof. Both TeX text and C95 preserve this crucial qualification; compact
   summaries likewise retain seed2's3-versus4counterexample.

3. **Exact-cue content is not serializer identity.** Table captions explicitly
   label source-faithful production/content, not target-byte/canonical equality.
   For example seed0REPLAY exact-cue content10 differs from target-byte8 and
   strict-canonical4; EXTRA_MEMORY content13 differs from strict5. Paraphrase
   strict is0throughout despite content successes. No noncanonical correct
   memory is reclassified as a content failure. Old held correct outputs are
   canonical, a separate empirical fact. Paired content R-only/E-only counts
   agree: exact1/4,0/1,0/2; paraphrase0/0,0/0,0/4; held0/0,2/0,6/0.

4. **Failure types.** SEQ159 does not inherit a generic syntax explanation.
   Seed1EXTRA_MEMORY's2new losses are predicted/relation source errors,
   replacing absent prior with observed false/matched. Seed2's6new losses are
   output-variant errors: records instead of required abstention, five missing
   outcomes and one outcome/action mismatch, as detailed in the execution
   handoff. These panels have no syntax/schema errors. Seed0's shared existing
   failure is `try:integer_triple_required`, not a newly introduced loss.

5. **Equal steps, unequal memory exposure.** Both arms restart from original
   perception parents, not HIGH/LOWER descendants; original memory banks are
   14/8/8. Each arm takes304/256/256updates. REPLAY has112/64/64memory
   presentations plus192observation-replay presentations per seed; EXTRA_MEMORY
   adds192repeated memory presentations to give304/256/256memory exposures.
   These repetitions are not novel records. The24supported authored TRAIN
   observations are shared across children, not72new facts. The text explicitly
   denies matched exposure/token compute, which is essential for interpretation.

6. **Costs and clocks.** Totals6fits/1632updates/480generations and training
   46728supervised/334800context tokens match the reducer. No new source or
   teacher calls and no new historical-control runs are attributed to this
   comparison. C95's539.210/477.818/495.145s controller spans match the
   execution report and are not described as summed parallel makespan or
   GPU-active time. Main's16tests3.095s is attributed, not called native runtime
   or claimed as a test execution by this reviewer.

7. **Historical controls and causal scope.** HIGH/LOWER/LR0 remain explicitly
   historical/noncontemporaneous. Three exposed DEV learner pairs are not
   independent episodes or pooled causal/equivalence evidence. The absence of
   a same-child/same-history raw-chronological LoRA comparator remains an
   extraction/compiler attribution limit. No parenting, H1/H2, freeze, general
   G3, clean-lineage or mission promotion is introduced; C11 remains deferred.
   Older SEQ158launch-only descriptions are marked historical. Alignment is
   only inference-only zero-fit CPU development in this cut, never an outcome.

8. **Ordering repair described accurately.** The archived original and corrected
   reducer sources differ only by sorting `candidates.items()` before iterating.
   This agrees with the execution handoff's candidate/tie-order explanation;
   it does not change candidate universe, scores, floors or raw evidence. The
   failed local reduction is not a scientific retry or recollection. The
   manuscript does not present JSON replay as a new tensor/hardware audit.

## Scope, evidence and validation

Reviewed the new summaries and abstract additions, sprint3915–3968/main1676–1729,
README108–154, C95claim-map4268–4335, collaborator89–133, and the compact
abstract amendment528–535. Used the preserved SEQ159baseline only to locate
changed spans; did not redo the older manuscript or review later outcomes.

Primary archived evidence under `research_notes/astra_memos/receipts_20260912/`:
- `astra_own_replay_repair_analysis_result_20260913_attempt1/analysis.json`:
  `03ac63e35c3e912533b62474ba4590dee21bbac02ca790511491d3305022bc6a`.
- `astra_own_replay_repair_analysis_execution_20260913_attempt1.md`:
  `6614a09dd98f501c3f8f93e141a74a7a1ee166378b8c00f149fb65cb4645fa6e`.
- Original reducer `astra_own_replay_repair_analysis_20260913.py`:
  `ba039742485f8292e7caf9d728f0b5c9b1c3a0ca03a52ff39b8d4b14814a84cb`.
- Corrected `astra_own_replay_repair_analysis_20260913_orderfix.py`:
  `4c06d8ded8ab58814a94f0aab40780a54fa2cf76ca0c7d858d1ab639483b03ab`.

An independent in-memory Python check passed135evidence/byte assertions:
all13file bindings in the author handoff (six manuscripts plus seven evidence
files), primary pin, source counts, itemwise loss lists, floors/screens,
paired counts, per-kind presentations, total tokens/costs/clocks, and exact
one-line reducer delta. This supplements direct reading; it is not the writer's
145-check suite and does not execute any scorer/trainer/collector or native test.

Only this new `/tmp/astra_manuscript_seq159_independent_review_20260913.md` was
written. No Git/native/GPU/network/recollection actions or source edits. No PDF
compilation, pagination, layout, new literature or full-paper correctness claim.
ACCEPT is a bounded evidence-to-manuscript judgment, not scientific promotion.
