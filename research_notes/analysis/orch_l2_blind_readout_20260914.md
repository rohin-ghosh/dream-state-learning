# L2-BLIND-READOUT — prospective scientific critique

2026-09-14. Recommendations only; Main reviews and publishes. No launch hold.

**Scope.** Read only the supplied AGENTS instructions and the permitted shared
interface, SHORT protocol, shared module, guided episode module and shared runner.
No results, state/board/coordination files or peer journals read; no result counts
rederived, experiments/tests run, reviewer models invoked or GPU used. Artifact
names below describe code-recorded evidence, not evidence inspected on disk.

## Strongest identifiable comparison

**Strongest result available to this blind review is a design-level finding, not
an empirical gain:** same-stage, same-world, opposite-goal-paired parent-free
SHORT versus guided FROZEN is the clearest comparison for retained behavioral
change under dense parenting. Both start from the same adapter and use the same
coaching policy; only SHORT consolidates. Fresh-process evaluation removes direct
parent coaching and rich instructions. Compare episode disagreements within each
world, retaining failures, rather than treating an across-sleep score slope as
learning. FROZEN is coached during experience, not an unparented control.

Use all four lanes without conflating their questions:

- SHORT versus FROZEN tests the evolving dense-guided learning package versus
  dense-guided no-update behavior. Their response-aware coaching and subsequent
  experience diverge: this is not sleep applied to identical training transcripts.
- SHORT versus UNPARENTED compares the added dense-parenting package among
  sleepers. UNPARENTED still receives the rich experience contract. Yield, target
  content and realized update count can differ; this does not isolate parent
  advice quality at equal training dose.
- LONG versus SHORT compares guidance policies, not pure frequency, duration or
  efficiency. The shared contract requires fewer LONG opportunities/tokens; the
  LONG hook itself was outside this read. Actual delivered guidance matters.
- UNPARENTED versus FROZEN changes both coaching and updating. There is no
  unparented frozen lane, so no full parenting-by-sleep interaction is identified.

FROZEN across stages anchors cohort difficulty because its evaluation adapter
stays initial. Stagewise learner-minus-FROZEN gaps, with initial discrepancies
shown, are more informative than learner slopes alone. Changing gaps still need
not mean acceleration: cohort difficulty can interact with learned strategy.

## Nonidentifiability, ceiling and assumptions

Stage and held cohort change together (`orch_l2_shared.py:14` and
`gpu/orch_l2_shared_run.py:231`). A before/after comparison is not the same child
tested before and after sleep on the same problems. Shared SOURCE controls
between-lane stimulus differences, not between-stage difficulty or unavailable
EVENTs. Keep source failures in the fixed denominators. Eight worlds with two
related goals are eight paired world contexts, not sixteen independent worlds;
one training seed cannot establish general acceleration.

Ceiling leaves no accuracy headroom. Flat scores at ceiling neither establish
improvement nor falsify learning; extra prose is not a substitute. Conversely,
repeated equal scores below ceiling may conceal different failures, so inspect
paired actions. Loss reduction, changed adapter hashes, admission yield and
150–400-token compliance establish neither retained cohesion nor transfer.
Old-memory/audit preservation is useful against forgetting, but rehearsal is
part of sleep; preservation alone cannot attribute benefit to new reflection.

The retained-change interpretation assumes matching SOURCE/cohort identities,
the actual output adapter loaded in a fresh process, unchanged base, genuinely
neutral evaluation prompts and comparable decoding/runtime. These are receipts
to inspect, not facts verified here. Prompt masking removes direct parent text,
not the parent's causal influence on child-native targets or on earlier child
utterances in their prefixes. Behavioral coherence is observable; internal
representational cohesion is not identified by these traces.

## Minimal already-recorded learner-centric evidence

Use existing raw records, not new grades, thresholds or a composite metric:

| Evidence join | Supports retained behavioral cohesion | Challenges that interpretation |
| --- | --- | --- |
| Experience `EPISODE_*.json` captures, `prior_reads`, raw responses, commands, routes and parent messages; readout counterparts | A specific evidence-use or correction pattern first visible in experience recurs on fresh held identifiers without the coach; statements match actual READs/receipts and ensuing actions | Explanation expands but action stays wrong; invented evidence; the improvement appears only immediately after advice |
| Both opposite-goal episodes of each held world, with `terminal_reason`, `actor_calls`, errors and raw commands | Goal-dependent choices use shared evidence consistently; the learner avoids the same semantic failure on both tasks where appropriate | Same route regardless of goal; one favorable task hides failure on its counterpart; pooled success tracks easier cohorts |
| Readout `CALL_*.json` prompts/responses and generated token/terminal fields | Coherent evidence-to-action behavior occurs without rich prompting, including before corrective receipts when an opportunity exists; longer text is not its only change | Benefit needs repeated within-episode feedback; extra tokens consume turns or cause overflow; claimed correction never changes the next action |
| Experience gates/review hashes/admitted captures → sleep `MASKS.json`, `RECIPE.json`, `LOSSES.jsonl`, `COMPLETE.json` → readout `REQUEST.json`, `LOADED.json`, `BINDING.json` | Exact child targets connect to actual updates and the evaluated child, with neutral prefixes and target-only loss | Zero yield/no update, unchanged weights, wrong adapter, projection failure or guidance-bearing evaluation explains the apparent change |
| Existing retention/audit records alongside later held traces | New coherent behavior persists through subsequent sleeps without obvious loss of prior behavior | Transient post-sleep behavior disappears, or apparent improvement merely trades away old behavior |

Trace recurrence means the same kind of evidence-use behavior, not repeated
identifiers across disjoint worlds. Same-episode correction remains in-context
adaptation; later fresh-process recurrence is the relevant retention evidence.
Use discordant and failed episodes as well as favorable examples. These patterns
can weaken the proposed mechanism without proving that no learning occurred.

## Attempted falsification and unresolved obstacle

This was a prospective attempt to break the inference, not a raw-result audit.
Cohort substitution defeats a naive sleep-slope argument. Adaptive coaching,
selection and variable updates defeat a pure reflection-effect argument. Fresh
neutral readouts would challenge direct in-context coaching, but not distinguish
reflection from ordinary self-imitation plus rehearsal.

Two inspectable caveats sharpen that limit. The SHORT runner records
`PARENT_DISTILLATION.json`, but the inspected sleep path consumes admitted child
captures, not that summary (`gpu/orch_l2_shared_run.py:311`, `:318`). A parent
summary is therefore not itself evidence of child reflection being consolidated.
Also, the protocol promises a neutral-only semantic evaluator input, whereas the
runner queues the full episode and captures, including parent-bearing fields
(`gpu/orch_l2_shared_run.py:271`, `:86`). The uninspected downstream service may
sanitize these. Ask Main to check the already-recorded rendered backend request;
this is an unresolved visibility/admission-selection question, not a finding
that the evaluator actually saw guidance.

**Central unresolved obstacle:** there is no same-cohort adjacent-checkpoint
counterfactual in the specified fresh-cohort sequence, and no isolated causal
test of experience → reflection → sleep as distinct from the training package.

## Cheapest next discrimination; compute recommendation

- **If null:** first inspect existing update/admission/identity receipts and
  paired raw failures at zero additional inference cost. No update means no
  realized consolidation treatment; a ceiling null is uninformative. With
  genuine updates and available headroom, recommend an adjacent pre/post-sleep
  checkpoint comparison on one identical already-defined held cohort under the
  existing neutral readout, if Main later authorizes it. An indistinguishable
  result weakens retained task-relevant change, not all possible learning.
- **If promising:** first seek the predicted uncoached action pattern in existing
  held disagreements versus FROZEN and UNPARENTED. The cheapest direct challenge
  is the same checkpoint comparison: hold EVENT bytes, goals, prompts and
  decoding fixed in fresh processes and switch only the adapter. Fix the
  checkpoint/cohort choice before that comparison, not by selecting the largest
  observed gain. Disappearance of the advantage supports cohort/coaching as an
  explanation; persistence supports adapter-mediated behavior, not acceleration
  or reflection-specific causation. A reused held cohort is diagnostic, not a
  newly untouched confirmation set.

No new training, benchmark, success threshold, acceptance gate, framework or
model-call allocation is proposed. This review consumes zero GPU/model calls;
unused current capacity is not authorization for added evaluations. These are
recommendations to Main, not changes to the running protocol or native launches.

**Message to Main/raw-result reader:** please pair same-stage worlds against
FROZEN, show the concrete READ → evidence → goal-dependent action disagreement,
and bind it to the loaded child. A rising sleep score or eloquent reflection
alone is not the retained-change result we need.
