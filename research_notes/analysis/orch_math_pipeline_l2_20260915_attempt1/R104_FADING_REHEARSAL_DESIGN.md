# R104 separate fading-rehearsal treatment — design only

Directive: exactly TWO episodes/sleep, ONE shared three-arm baseline; other
parent GPUs are treatments. Preserve bad outcomes as negative examples, with
truthful outcome tags. Existing R102 schedule, old-row mix, sources, deadlines,
and allocation remain UNMODIFIED. This document authorizes no dispatch, added
calls, provider retry, epoch reset, or modification of an existing life.

## Objective and interpretation

Current sleep minimizes ordinary causal cross-entropy on source-attributed
child utterances under masked, outcome-tagged historical context. INCORRECT
attempts are explicitly non-endorsed examples of an unsuccessful past attempt.
The next actual child reflection receives the real verifier outcome and private
parent guidance; teacher words are excluded from compiled prefixes/targets.
This is outcome-conditioned SFT of negative-example records, NOT negative
gradient, unlikelihood, preference optimization, or proof that wrong-answer
probability decreases. It positively trains reproduction of the unsuccessful
utterance *under that historical context*. Generalization can still be adverse;
parent-free behavior must establish any useful change. No scientific claim is
inferred merely from a negative tag or improving supervised loss.

## Proposed next lineage, frozen before any dispatch

Use a new uniquely named parented-only treatment, not another control triple.
Record a genuine saved initial adapter/base and any explicit epoch decision.
Never transplant L2 data into L1. Anchor shared canonical controls descriptively;
without a matched math comparator, do not claim a causal fading/style effect.
Keep eight sequential two-episode cycles, current held schedule, strongest
verified provider and fresh-process tests as the starting design. Resource
allocation, exact cohort, additive native/parent accounting, source bindings,
deadline fit, and own Builder CPU/provenance receipt must be frozen separately;
there is currently no reservation or launch-ready claim for this next arm.

### Stage A: cycles1–4, fading historical rehearsal

- Every current episode keeps its outcome-tagged original-attempt record when
  actual response bytes exist, and one actual own reflection. Both are used
  regardless of correct/incorrect status. Missing response remains NO_RESPONSE
  with provenance, never a fabricated trace. Current paired row weight is1.
- Historical own/legacy rows keep immutable bytes and provenance. Proposed
  historical loss weight is `2**(-age_cycles/2) * min(2, 1+log1p(train_uses_4))`.
  `age_cycles` is cycles since the latest eligible TRAIN use (creation/import
  cycle initially); `train_uses_4` counts eligible original TRAIN episodes in
  the last four cycles. All historical rows remain represented, not selected
  by outcome; weights are strictly positive in this bounded stage.
- Eligible use is a deterministic predeclared source-key dependency: exact task
  key by default, or a generator-provided skill key whose row mapping was
  frozen before the run. Never invent a semantic dependency after outcomes.
  Each distinct original TRAIN episode increments a key once regardless of
  success and refreshes its last-use cycle. Replaying a row, teacher statements,
  reflections, HELD/retention, and optimizer presentations cannot refresh it.
- Multiply that row's mean supervised-token CE by its recorded weight, then
  backpropagate into LoRA only. No signed loss and no outcome-based multiplier.
  Proposed LR remains the source recipe3e-5 in Stage A. Keep source-mask checks
  and paired current-attempt/reflection exposure. Log eligible keys, ages,
  weights, presentations, weighted/unweighted losses, and actual updates.

### Stage B: cycles5–8, lower plasticity and no replay

The proposed transition is at fixed cycle5, never triggered by held scores or
0/8 outcomes. Continue the same adapter AND optimizer state, with documented
LR3e-6; do not reset parameters or optimizer. Historical/legacy replay stops
entirely. Neither earlier rows nor the current recorded original attempt is
reproduced as a supervised target in this stage: that would still be replay.
Instead each of the two fresh episodes produces a fresh source-bound own
reflection, followed by a masked reflection-only write. The original attempt,
failure tag, and verifier feedback remain explicit negative-example context
and immutable ledger rows, not relabelled or deleted. Teacher words remain
excluded. Log this as **fresh-reflection-only adaptation, no replay**, not the
Stage A paired-original/reflection objective. This is a proposed objective
delta, not a reinterpretation or live alteration of R102.

If “no replay” is intended to prohibit even fresh reflection adaptation, that
would instead be a no-write stage, conflicting with the requested learning
cycle writes; stop and report that exact scope conflict rather than silently
calling repeated trace SFT “no replay.” Current design explicitly uses the
fresh-reflection-only interpretation, which must appear in its eventual frozen
protocol and CPU tests before dispatch.

## Required tests and reporting before implementation launch

1. Equal-age/use correct and incorrect rows receive identical positive weights;
   every failed current episode has coverage and at least one actual sourced
   reflection write. Source tamper/relabel/omission and teacher copying fail.
2. Age increases monotonically without eligible TRAIN; repeated eligible TRAIN
   refreshes decay. Replay, reflection, HELD and retention cannot refresh it.
3. At cycle5, historical AND original-trace replay updates are exactly zero;
   only fresh reflection targets are trained. LR lowers without state reset.
4. Exactly two sequential original episodes and two reflections per sleep;
   parent-free tests after every cycle and taught-to-next-cycle linkage.
5. No outcome-based stopping, tuning or resource release; all failures retained.
   Thinking/approach/rejection/repetition/coherence are primary descriptive
   readouts, not automatic admission labels. Accuracy is ancillary.
6. Actual phase walltimes, dataset sizes, masks, update weights/counts, lineage
   and terminal/partial failures remain node-backed, with repo hashes/tables
   only. Current R102 eight-episode legacy phases stay unchanged until their
   already-declared safe boundaries; this design cannot mutate them.
