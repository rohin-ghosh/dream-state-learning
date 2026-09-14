# Prospective broader actual-experience recipe after SEQ256

Declared before new source collection or fits. SEQ256's fixed 400-update recipe
is closed: TRAIN acquisition differs, held PROBE endpoints tie, and both arms
lose one original-graph success. This successor changes actual experience
coverage and legacy-trajectory rehearsal together. It does not isolate which
change explains any improvement over the earlier recipe.

## Collect once from unchanged37ec, no fits

Use eight new TRAIN worlds and two new PROBE worlds, with namespace prefix
`ASTRA-GOALBREADTH-20260914-V1`. Four fixed two-TRAIN blocks reuse the existing
goal-pair helper's source-bound teaching procedure. Only block0's two PROBE
worlds are exposed/evaluated. No selection by baseline scores or identifiers.
All identifiers must be disjoint from old16 facts, original/fresh graphs, and
all four SEQ255 worlds. Do not use failed fa3/2a8 states or scored PROBE rows
as teaching data. This is new identifier coverage of the same topology.

- EXPOSE: ten worlds,40 actual source EVENTs,80 calls. No fabricated or repaired
  events; failures retained. No parent at exposure.
- TEACH: eight TRAIN worlds, all four tasks/both goal-display pairs, six actual
  child command targets each:192 calls/192 targets. Source-informed parent
  guidance is present only during collection, absent from student prefixes.
  All four48-row blocks are required; incomplete collections do not emit a
  successful subset for fitting. No parent access to PROBE cases or scores.
- BASELINE, unchanged37ec fresh process: TRAIN OWN_TEXT192 calls, PROBE
  OWN_TEXT/UNAVAILABLE96 calls maximum; <=288 calls. Record unassisted TRAIN
  acquisition baselines this time. No baseline-dependent curriculum or fit dose.

No-fit stages each bounded at3660s including teardown, plus300s admission,
<=11280s total; one node2 GPU, verified physical/CVD and lease margin. Keep
actual phase cost separate from these upper bounds. Maximum560 native calls.

## Two matched finite fits, after actual source admission

Start the same37ec snapshot in both FULL_TARGET and NEW_TRAJECTORY_LOSS_OFF.
Exactly414 rows:128 old memory,20 cue,62 audit,12 original trajectory,192 new
actual TRAIN trajectories. No SEQ255 trajectory or PROBE rows in this mixture.
FreshAdamW3e-5, seed0, rank8, frozen base.1632 updates,batch4. For offset=update-1:

`(offset%128, 128+offset%82, 210+(2*offset)%204, 210+(2*offset+1)%204)`.

This gives exactly16 presentations to each of the204 old/new trajectory
targets (192 old,3072 new presentations total), plus1632 old-memory and1632
cue/audit presentations. It is a declared per-target dose for the broader
curriculum, not an extension or rerun of SEQ256. No step/dose/LR/rank sweep.
Only new rows222–413 are label-masked in LOSS_OFF. Keep original12 trajectory
labels in both; scale control mean CE by active/full-reference labels per
batch. Report both actual/reference totals; no equal-active-token claim.

Per arm: TRAIN<=7260s and AFTER<=3660s including teardown, plus300s admission;
<=11220s. Current measured400-update cost predicts roughly an hour of training
per arm, with sequence/throughput uncertainty. Launch independent guarded GPUs;
never refit a completed adapter to repair only a readout failure.

## Readout and decisions

Fresh-process, parent-free AFTER<=384 calls: eight TRAIN worlds OWN_TEXT
(192), two PROBE worlds OWN_TEXT/UNAVAILABLE(96), old16 facts at W0/W8(32),
held audit(16), original taught and earlier fresh graphs OWN_TEXT(48).
Report strict opposite-goal pairs and individual goals by world/arm, original
baseline, deterministic first-port reference, failure identity, exact retention,
calls, cost and saved-state lineage. No best-checkpoint selection.

Engineering target for FULL: >=3/4 PROBE pairs, >=1/2 in each world,
>=15/16 old memory at each wrapper, >=15/16 audit, >=3/4 original taught and
earlier fresh text goals. TRAIN acquisition is diagnostic, not an efficacy
stop. Ties or baseline ceilings are not incremental transfer gains. One exposed
lineage and two fixed identifier instances do not support population/H1/H2 claims.
Only a usable connected actor warrants the fresh parent-free memory-write
continuation. Otherwise close this recipe and diagnose before another choice.
