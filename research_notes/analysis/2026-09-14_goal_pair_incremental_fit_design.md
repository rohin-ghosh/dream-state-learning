# Prospective incremental paired-goal teaching comparison

Declared before any new fit and before Main inspects the new PROBE baseline.
The no-fit collection/teaching/baseline job runs separately. Its PROBE records
are excluded from all training, and its scores are not provided to the parent.
This compares additional trajectory-target gradients from the already taught
37ec child, NOT parented versus never-parented whole lives.

## Two finite arms from the same parent

FULL_TARGET and NEW_TRAJECTORY_LOSS_OFF start the same37ec snapshot, each with
freshAdamW3e-5, seed0, rank8,400updates,batch4. Exactly270rows:128oldmemory,
20cue,62audit,12originalactualtrajectory targets,48newactualTRAINtrajectory
targets. Do not include the32fresh EVENT rows from253 or any PROBE row. Both
arms see identical saved inputs, tokenization and update schedule. Only the
new48trajectory-row labels are masked in LOSS_OFF; retain original12trajectory
labels in BOTH. Control mean CE is scaled by active labels / full-reference
labels per batch, preserving the shared full-label denominator. Record both
actual and reference label totals, not an equal-active-token claim.

For offset=update-1 (updates1..400), batch indexes are:
`(offset%128, 128+offset%94, 222+(2*offset)%48, 222+(2*offset+1)%48)`.
This gives800newtrajectory presentations, approximately16–17per actual new
target, matching the presentation count of the earlier12-target teaching
recipe rather than silently quartering its per-target dose.400oldmemory and
400oldbehavior presentations are identical between arms. No dose/LR/rank sweep;
no score-based early stop or completed-fit repetition. Abort on technical or
nonfinite-update failures, preserving the partial run. Full48actual source-bound
targets and provenance/CPU preparation are required before either fit.

## Fresh parent-free readout

Each saved adapter reloads in a fresh process. Evaluate:
- Both TRAIN worlds, OWN_TEXT:8tasks (<=48actorcalls), to separate acquisition
  failure from transfer failure.
- Both PROBE worlds, OWN_TEXT and UNAVAILABLE:16tasks (<=96actorcalls), with
  identical captured source text/tasks across arms and the saved37ec baseline.
- Old16facts W0/W8 (32calls), heldaudit16calls, originaltaughttext4tasks and
  previousfreshgraphtext4tasks (<=48calls combined):<=240nativecalls overall.

Primary report: strict goal-pair success on PROBE OWN_TEXT, four fixed-display
pairs total, broken down by world and arm; retain individual8task counts and
first-port/second-step failures. Pair requires both opposite goals, distinct
source-correct first ports and two legal commits per task. Report UNAVAILABLE
and deterministic first-port reference, not only aggregate arrivals. No new
primary metric is substituted after seeing outcomes.

Engineering promotion target for FULL: at least3/4 PROBE pairs with at least
one pair in EACH world; retain at least15/16 old facts per wrapper and15/16
audit cases; originaltaughttext>=3/4 andpreviousfreshtext>=3/4. Report every
count even when targets fail. A control tie, forgetting, training-only learning
or probe failure narrows the finding; do not relabel it as a success. These are
two identifier instances of one topology and one lineage—not independent birth
seeds, population efficacy, generalized planning or H1/H2 evidence.

## Execution and subsequent decision

Two independent node2GPUs once preparation passes. Each TRAIN<=7260s and
AFTER<=3660s including teardown, plus300sadmission,<=11220s per arm. Expected
time is substantially smaller based on measured100-update fits, but must be
measured. No shared mutable adapter or sequential stages run concurrently.
One collection and one baseline are reused, not recollected per arm. These
two fits are the entire recipe; no automatic sweep follows. If useful goal-
sensitive transfer appears, test its preservation and parametric use in a
separately declared fresh-memory loop; do not assert that loop has already run.
