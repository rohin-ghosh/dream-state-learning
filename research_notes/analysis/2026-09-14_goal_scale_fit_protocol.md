# Prospective full-corpus goal-scale comparison

Declared2026-09-14 18:18UTC while source shards run, before scale-fit admission
or any scale baseline inspection. Running breadth fits are not amended.

## Fixed data, initial state and matched arms

Admit exactly the eight ordered source shards from the independently bound
goal-scale collection protocoldd1d078a, all1536actual TRAIN targets. Native
replay checks actual row/source joins and absence of PROBE targets. No
baseline-dependent worlds, ranking, subset, dose or success-only replacement.
The starting adapter is unchanged37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0,
not the outcome of either running breadth fit. The frozen7Bbase and rank8
adapter remain unchanged in architecture. Three training RNG seeds0,1,2 each
run FULL_TARGET and NEW_TRAJECTORY_LOSS_OFF on independent GPUs. These are
same-corpus stochastic-fit replications, not three independent developmental
lineages or independent environment draws. Adapter dropout remains0.05.

Exactly1758rows:128oldmemory+20cue+62audit+12legacytrajectory+1536newtrajectory.
Fresh AdamW3e-5, frozen native optimizer parameters, batch4,12384updates.
At offset=update-1, indexes are
`(offset%128,128+offset%82,210+(2*offset)%1548,210+(2*offset+1)%1548)`.
Every1548legacy/newtrajectory target receives16presentations:192legacy,
24576new; oldmemory and oldcue/audit each12384presentations. LOSS_OFF masks
only newrows222–1757; all legacy targets remain supervised. Inputs, row order,
reference masks and per-batch full-reference denominator match each paired
seed. Active-label totals differ and are reported. No equal-token/compute,
optimizer-trajectory or retained-competence claim follows from matching rows.

This tests adding new actual trajectory supervision to a heavily rehearsed
shared substrate; increasing corpus coverage and balanced legacy rehearsal
is the declared recipe, not isolated proof of a coverage mechanism. No
checkpoint selection or unplanned LR/rank/dose extension. Finite losses,
actual trainable LoRA set, saved/reloaded state and frozen-base checks apply.

## Readout and decisions

After each terminal fit, fresh process uses all16unparented PROBEworlds under
OWN_TEXT and UNAVAILABLE,64goals/32opposite-goal pairs per condition. Max768
calls; old16facts at W0/W8=32,heldaudit16,original/fresh OWN_TEXT=48, total864.
All arms use the same actual source text and tasks. TRAIN postfit generation
is omitted from this comparison; do not report unmeasured acquisition.
Report loss trajectories separately, without treating TRAINloss as transfer.

Compare FULL/control/unchanged37ec for each seed and world; report failure
categories, individual goals, strict pairs, first-port reference, retention,
generated/active/reference tokens, wall/GPU cost and full state lineage.
The engineering target is>=24/32OWN_TEXT PROBEpairs,>=1pair in eachworld,
oldfacts>=15/16 at eachwrapper,heldaudit>=15/16,original/fresh goals>=3/4each.
Positive incremental transfer additionally requires improvement over paired
LOSS_OFF and unchanged baseline; passing an absolute threshold alone is not
an improvement. All three seeds are reported, not best seed. UNAVAILABLE
performance and shared topology limit any semantic-memory interpretation.
This is exposed DEV, not population efficacy, H1/H2 or full flywheel evidence.

Close this recipe at its declared endpoints regardless of direction. A useful
connected actor may justify a separately specified new-experience/sleep/reload
continuation. Failure directs a new justified recipe, never extra updates on
these stopped fits. Independent richer/critique work continues meanwhile.

## Resources and recovery

Prefer node2GPUs2–7 while breadth occupies0/1, each admitted using physical
process and CVD checks. GPU assignment may follow availability, never scores;
log exact seed/arm/UUID/PID. Node2expires2026-09-21 08:43UTC; require entire
54420s bound before six-hour cutoff. Per arm TRAIN43200s plus60teardown,
AFTER10800s plus60teardown, admission300s, overall54420s. Six-arm maximum
allocation bound90.7A40h; observed~2.1s/update suggests~7.2hTRAIN/arm with
sequence/contended-throughput uncertainty. These are forecasts, not results.

Never rerun completed TRAIN to fix AFTER only. Keep failed attempts and state,
use a new readout attempt directory, and bind its original trained artifact.
No newnode1 work, other users' PIDs, paid allocations or lease changes.
