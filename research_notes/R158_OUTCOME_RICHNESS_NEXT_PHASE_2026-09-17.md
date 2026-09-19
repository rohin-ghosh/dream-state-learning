# R158 controlled collection and the required gated-learning phase

Status: prospective design, not implemented selection or a learning result.
The current R158 matched triplet collects real TRAIN feedback under the existing
raw sleep recipe. It must not be relabelled outcome-and-richness-gated training.

## Evidence chain required before selecting a target

1. An immutable TRAIN task and published environment message, with the exact
   generator/version/split ledger, must join to a REQUEST that actually rendered
   the task. A queued message alone is not an exposure.
2. A hash-joined REQUEST, RESPONSE and COMMITTED record must identify the learner's
   actual own text, token IDs and original masked prefix. No rewritten exemplar,
   parent text, environment text or evaluation response becomes a target.
3. An answer target must join its exact submitted answer to an actual accepted
   verifier receipt for that task. A post-feedback reflection target instead joins
   to a prior accepted own attempt, its real result, and the actual feedback
   rendered before the later own reflection. Its reviews bind both the outcome
   anchor and the reflection text and check a faithful corrected retelling; an
   earlier accepted answer does not automatically verify a later record's truth.
   An incomplete newer revision is not replaced by an earlier answer. A positive
   outcome is not a proposal, parent compliment, solver self-report or exception
   mapped to success.
4. Richness is a separate content judgment over the complete candidate and its
   visible TRAIN context. Reviewers must bind exact source hashes and quote
   supporting spans for grounded operations, a checkable expectation or check,
   useful revision when feedback contradicts a prior attempt, reusable content
   with stated applicability, and absence of padding or invented observations.
   First-person register, English fluency, token length, headings, branch counts
   and emotional language are not quality gates. The existing content-readmission
   contract in `organism_v6/orch_math_readmission.py` is relevant precedent, not a
   verifier for these new tasks.
5. PASS, FAIL and UNRESOLVED must all be preserved. At least two independently
   produced full-context judgments and their disagreements are retained for the
   first packet. Missing evidence or unresolved disagreement excludes a target;
   it does not license an automatic model-consensus scientific claim. Selection
   reasons remain auditable separately from training and evaluation outcomes.
6. Feedback-use examples additionally require the earlier attempt, actual feedback
   rendered before the continuation, and an attributable changed action or
   expectation. A correct answer without that chain can support grounded reasoning,
   but cannot be counted as demonstrated revision or parenting dependence.

## Application and controls

Build a new immutable packet from eligible own trajectories, preserving rejected
and unresolved examples. Validate exact tokenization/masking, no special-token
injection, context fit, contamination exclusions and presentation accounting.
Do not crop text silently or train arbitrary padding to reach a token minimum.
The capability anchor remains the explicit 0.25 objective mix. Training uses
new labelled forks of the common saved initializer, never an unlogged hotpatch or
reset of the R158 raw lives. First run a bounded end-to-end packet through one
learning/frozen/unparented matched comparison before expanding collection.

Keep initialization, parenting exposure, selected trajectories, optimizer steps,
own/anchor token exposures, replay policy and failures separately observable.
If selection leaves fewer trajectories in one arm, report the changed data dose;
do not describe the resulting contrast as exposure-matched. A frozen arm retains
the same prompt/compaction/readout schedule but performs no optimizer updates.

## What would demonstrate the requested result

All checkpoints must have parent-free, file-free, fresh-process, empty-context
evaluation on the same frozen unseen task set. Initial and per-sleep snapshots
need common-initial-state and checkpoint-custody evidence. General retained
capability and experiment-specific feedback/revision/reusable-record behavior
need separate measurements; activity or verbal metacognition alone is insufficient.

Compare retained changes against both the frozen and unparented twins across
sleeps, preserve the whole branch/task distribution, and distinguish in-context
behavior from retained weight effects. A reusable-record claim also needs a real
recipient or later fresh-task use test, not merely a plausible-looking note.
Parenting-dependence claims require actual rendered parent exposure and the
predeclared contrast, not assigned cadence alone. A future held-score change is
not a license to feed sealed evaluations into parenting or selection.

The raw triplet, parser tests, capacity proof, resumed benchmark controller and
kernel service each support a bounded part of this chain. None on its own
completes the active goal. The first real TRAIN attempt/check/rendered-feedback
cycle, an accepted richness packet, its gated fit and matched retained outcomes
remain required evidence.
