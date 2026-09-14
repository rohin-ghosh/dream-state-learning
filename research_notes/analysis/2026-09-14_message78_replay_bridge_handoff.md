# Message78: replay-layout implementation and closed-loop bridge

Old Builder handoff, 2026-09-14. No GPU allocation or native launch. The new
orchestrator owns the experiment, controls, admission and native integration.

## Answer to Rohin

The finite supplied-text transfer result makes a repeated experience/write
comparison worth testing. A learned compiler need not be a prerequisite:
begin with byte-faithful projection of admitted actual child responses, and
test model-reasoned replay as a separate later treatment. That separates the
question of whether the loop works from whether learned selection improves it.
It does not establish either result in advance.

One important correction to Fable's interpretation: SEQ266 used FOUR trajectory
presentations, not16. Its1452 new rows received5808 presentations over2928
four-slot updates. With the same rows,16 presentations implies11712 updates.
Higher dose may be worth studying, but it is a changed recipe, not replication.
The original all-world conjunction remains failed15/16 despite the strong
aggregate contrast. A new DEV test must name its actual starting artifact
and cannot silently present it as a promoted clean lineage.

## Implemented, CPU-tested reusable part

New module: `organism_v6/experienced_event_goal_replay_layout.py`.
New tests: `tests/test_experienced_event_goal_replay_layout.py`.

`GoalReplayLayout(new_trajectory_rows, trajectory_presentations=4)` preserves
the old row groups128memory/20cue/62audit/12legacy-trajectory, and parameterizes
only the added trajectory count and its exposure. Four slots per update remain
one old memory, one old cue/audit, and two old/new trajectory slots. Updates
equal `(12 + new_trajectory_rows) * trajectory_presentations / 2`; partial
two-slot cycles are rejected rather than rounded. Empty/invalid counts and
out-of-range updates fail explicitly.

```python
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout

layout = GoalReplayLayout(1452)
indexes = layout.training_indexes(1)
full_manifest = layout.manifest('FULL_TARGET')
control_manifest = layout.manifest('NEW_TRAJECTORY_LOSS_OFF')
```

Manifests expose dose counts and control mask indexes; they do NOT encode
targets or apply masks, certify provenance, choose an adapter, or execute a
fit. They omit learning rate/optimizer/seed/native versions intentionally:
those remain the prospective caller's bound recipe. Old reference-label
normalization and prefix/EOT masking must still be used by that caller.
The helper changes no frozen driver and is not automatically imported into
any native experiment. Its schema is not an accepted old-run replacement.

Validation:7/7new CPU tests plus9/9existing frozen quality-runner tests pass.
New tests cover every original2928index tuple,11shared recipe fields per arm,
variable1/2/17/1000/1452/5000row pools,4/16presentations, exact per-row counts,
control mask boundaries, invalid inputs and detached immutable configuration.
Saved native replay separately matches all5856FULL/control batch index rows,
every row presentation count and11recipe fields/arm. This is artifact replay,
not a new native training test or independent reviewer endorsement. Receipt:
`2026-09-14_goal_replay_layout_native_parity.json` in this directory.

## Concrete remaining integration work: not a ready loop

1. **New collection:** `experienced_event_goal_quality.source_plan` and its
   collector are bound to the original eight exposures/selected units. They
   cannot simply be relabeled as a fresh cohort. A new caller must bind fresh
   experienced TRAIN material, actor state and held exclusion, preserving actual
   child target bytes. Existing outcomes can select material; no invented child
   reasoning or parent lesson bytes become targets. Declare zero-yield behavior
   prospectively; this helper rejects an empty new pool rather than making one.
2. **Persistent child:** `gpu/astra_goal_quality_train.py::load_inputs` requires
   the37ec parent; only its AFTER phase loads the newly trained adapter. Calling
   that frozen runner repeatedly does not instantiate an evolving child.
   A successor must bind each arm's previous completed adapter into BOTH next
   collection and next training, and load that updated state in its fresh readout.
   Preserve frozen-base/one-LoRA and parent-blindness constraints.
3. **Reuse existing lineage patterns, not the whole old diagnostic:**
   `gpu/astra_experienced_event_adult_cycle.py::load_cycle2_initial` checks the
   same arm's prior receipt, collection, adapter files and base. Its material
   companion permits exactly two cycles and a different32/64old+32new mixture.
   Those are useful binding patterns, not a drop-in breadth loop. Do not remove
   their historical checks to make a new experiment fit.
4. **Explicit optimization/recovery:** SEQ266 uses fresh AdamW. Carrying child
   weights forward while resetting AdamW each sleep is distinct from resuming
   optimizer state; bind the chosen behavior symmetrically. Saved adapter-only
   endpoints support stage-boundary continuation, not a claim of exact mid-fit
   recovery. Existing guards are not extended by the new layout's update count.
5. **Causal comparisons:** parented+sleep versus frozen and unparented+sleep
   remains the intended comparison, with parent absent at evaluation and budgets
   recorded. Supplied text and unavailable/parametric-memory readouts remain
   separate. A deterministic projected-material loop tests only part of learned
   extraction; later child-reasoned replay needs its own utility comparison.
   No first-loop gain alone establishes an improving learning process.

The shortest integration path is a newly declared native caller around these
existing pieces, not a replacement training system. The tests above remove
schedule/dose ambiguity only. They do not clear native provenance, family
admission, checkpoint promotion, repeated-sleep retention or H1/H2 gates.

## Commands and ownership release

`python3 -m unittest tests.test_experienced_event_goal_replay_layout -v`

`python3 -m unittest tests.test_astra_goal_quality_train -v`

Old frozen driver byte-diff against executed commit
`7f9d4251ae1ff4c5ff9138adf267d081fffa6331` is empty. The two new helper/test
files are released to astra2 for optional successor integration after this
handoff is published; no active old worker, native process or GPU accompanies
them. All unrelated dirty files are preserved.
