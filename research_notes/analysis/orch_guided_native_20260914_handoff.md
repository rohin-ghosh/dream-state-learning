# Old Builder -> astra2: CPU-tested native seam

## Downstream native observation — 2026-09-15 00:21UTC

The L2 worker has now exercised the seam on A100. Author-side readonly receipt
inspection confirms UNPARENTED cycle1 experience and training both mounted
e226cea2;26updates saved f2013ae1; completed fresh readout and next-cycle
collection both mounted that same output, with unchanged basea2367093.
Four distinct process identities, exact output adapter-file hashes, and the
cycle2 runtime manifest's native-source SHA match the released implementation.
52cycle2 call files existed at observation, not52successful outcomes.
Evidence: `orch_guided_native_20260915_native_continuity_observation1.json`.
No extra model calls/fits, tensor rehash, or independent scientific review by
this contributor. This closes the observed loading/reset compatibility question
for this path; it does not establish parenting benefit, behavioral improvement,
full repeated-cycle stability or general native readiness. Historical CPU-only
statements below describe the original delivery, before this downstream run.

Assignment: notebook be4d0e96, `[Orchestrator -> Builder]`23:08 label
(published23:06:39). Interface V1 from e5a4f919; interface file SHA256
`171e0adad8ef218ad0a0b65df31e5e6d1623ae57920e7a81bc5986d27a1eb727`.
This is experiment-serving implementation, not a launch, qualification,
family designation or scientific result. All orch_guided_bridge files and
historical executed drivers remain unchanged. No GPU allocation or model
call occurred; torch/transformers/peft are absent on this VM.

## Delivered native path

`gpu/orch_guided_native.py` imports the released bridge and replay layout:

- `load_collection(plan, **kwargs)` consumes the previous completed child.
- `load_training(plan, **kwargs)` consumes that SAME previous completed child,
  enables only its existing LoRA parameters, and creates a fresh AdamW using
  the plan's explicit seed, learning rate and complete optimizer kwargs.
- `load_readout(binding, **kwargs)` consumes the resulting-child binding
  returned by `bridge.complete_cycle`, in a fresh interpreter without parent,
  transient context or sleep prompt. Cycle0 uses `bridge.initial_readout`.
- Each returns `LoadedStage(engine, binding, context, process, observed,
  optimizer)`. `optimizer` exists only for training. The engine is the existing
  microloop Engine, not a new model wrapper. Caller retains normal generation,
  training, capture and process-lifecycle responsibilities.

Crucial fix: **all initial loads use Engine phase=`readout` plus the explicit
adapter directory**, even when the intended stage is training. Existing Engine
phase=`train` constructs a fresh LoRA and would erase continuity. The seam then
calls existing `enable_existing_adapter` only for training. No hardcoded37ec
or1452-row admission remains in this new seam; the old driver is not patched.

Observed identities use the existing `_state_hash` convention: mounted
`named_parameters()` LoRA A/B names, not PEFT export names. Mounted base
`state_dict(keep_vars=True)` keys have only the PEFT wrapper and `base_layer`
name indirection removed; the resulting key set must match the original
Engine base-reference keys. The hash uses the MOUNTED values, so stale
pre-placement references cannot hide a changed parameter or buffer. Adapter
files are rehashed, using the manifest's recorded order, and `verify_loaded`
receives the measured states. File path is the explicit requested source;
state measurement checks what actually mounted, not a filename label.

The tested native recipe is the existing rank8/alpha16/dropout.05 one-LoRA
configuration. Disabled, multiple or unexpected active adapters, base
trainability, and nonempty optimizer state fail. This is not rank16 support
or optimizer restoration. Tensor dtype/runtime and local-only loading retain
the existing Engine checks. Official upstream HF origin remains unresolved;
a matching local model hash is not an upstream-origin verification.

## Caller contract

Common keyword arguments are explicit `model_dir` (existing absolute local
directory), `device='cuda:0'`, `gpu_uuid`, `context=StageContext(...)`, and
`check` (the caller's existing budget/resource check). Default factory is the
existing Engine and tokenizer loader. Factory injection is only the test seam.
There is no automatic GPU selection, physical occupancy check or launcher.

Collection context inventories private guidance for guided arms; unparented
has none. Training/readout have none. Inventory is NOT semantic detection of
all private information; the caller must supply the actual guidance/context
and must not bypass the binding when building requests.

`LoadedStage.process` records boot ID, PID and process start ticks. Readout
requires a different process from every supplied `predecessor_processes`
entry, and this module must never have loaded an engine in that interpreter.
Noninitial readouts require a nonempty predecessor list. An inherited fork
without exec is rejected. Caller must supply all relevant predecessor process
identities and execute a clean readout process; this is not an OS supervisor
that authenticates omitted processes, catches arbitrary modules loaded before
this seam, or prevents a dishonest caller from fabricating metadata.

After readonly collection/readout, call `loaded.verify_unchanged()`; it
rehashes the mounted model and files and rejects trainability or mutation.
Do not call that readonly check on a trained endpoint. The caller must save
the trained adapter in the plan's new output path, measure its state, and
write the bridge's exact completion receipt only after actual success. No
completion receipt is manufactured by this seam.

## Actual-child encoding and replay

`encode_child_captures(captures, capture_hashes, collection_binding, tokenizer,
private_guidance=..., max_context=..., max_supervised_tokens=...)` first uses
the existing bridge's projection, then the native tokenizer/template APIs.
It returns exact projected rows plus native EncodedRows. It checks full,
prefix, target+EOT and suffix roundtrips; exact tokenized template; special
token injection; separate supervised EOT; prefix/suffix masking; and explicit
untruncated budgets. It never edits targets or substitutes teacher solutions.
Capture authenticity and outcome/semantic admission still belong upstream.

`assemble_replay(legacy_encoded, new_encoded, layout, legacy_reference=...,
eos_token_id=...)` retains the exact222 legacy encodings and validates the
variable number of new rows. `training_batch` uses GoalReplayLayout and the
existing collator/causal-reference loss denominator. Its optional loss-off
mask supports comparison with the historical recipe; it is not a fourth
guided-loop arm. The caller's training loop must multiply mean causal loss by
the returned `scale`, exactly as the existing writer does. The seam does not
execute gradients, save adapters or evolve a child by itself.

## CPU evidence

Command:

```sh
python3 -m unittest tests.test_orch_guided_native tests.test_orch_guided_bridge tests.test_experienced_event_goal_replay_layout tests.test_astra_goal_quality_train -v
```

Saved log: `orch_guided_native_20260914_cpu_tests.txt`:56 tests pass in64.894s
(18 new +22 bridge +7 layout +9 historical). Nine synthetic cycles across
three arms exercise native-factory calls: same-state collector/trainer,
six distinct fresh optimizers, invariant frozen arm, resulting-state readout.
One real fresh CPU subprocess loads a fake output artifact; no model imports.
Mock parameter values are measured rather than copying expected state hashes.
Negative cases include wrong mounted state, stale original restart at cycle2,
changed mounted base with stale reference untouched, parent/context residue,
inherited fork, modified receipt, disabled/extra adapter, stale optimizer,
target tampering, special tokens, token cap and roundtrip failures.

Historical batch parity checked14 arm/update combinations including boundary
updates; variable-row recipe checked at every update. Full legacy test suite
passes; no actual torch tensor/PEFT/tokenizer/model execution was done here.

Focused independent static review (Feynman the2nd,23:27UTC handoff) found no
concrete bugs against V1 and the existing Engine/cue-sleep paths. Reviewer
made no edits, tests or model/GPU calls. This is bounded code review, not
independent native verification or scientific promotion.

## Remaining obstacles and cheapest executable check

1. Main/assigned native driver supplies a prospectively bound task roster,
   candidate, family split and capture/semantic admission. No human family
   permission is needed after message79. No real L2/L3 material created here.
2. Wire these load functions into the driver in separate processes. Collect
   genuine child outputs, project/encode them, combine authoritative legacy
   masks, execute declared updates with reference normalization, save only to
   a new output directory, measure it and emit the actual completion receipt.
   Feed `next_lineage` into the next collector AND trainer; do not restart
   from genesis. Actual per-cycle zero/variable yield remains the bridge's
   declared limitation; never fabricate rows to satisfy a fixed layout.
3. Run ONE owner-selected, already-admitted DEV tranche using this seam:
   load prior child for collection; fresh load same child for declared sleep;
   save; fresh exec loads output for the already-selected parent-free readout.
   Inspect mounted names/base tensors, token roundtrips/masks, actual update,
   artifact reload, resource checks and costs. These GPU/tokenizer-dependent
   checks are the missing native verification, not more abstract CPU guards.
4. Continue the same lineage for a second tranche, then matched frozen and
   unparented arms under the campaign protocol. The first path above is only
   an instrumentation check, not learning or H1/H2 evidence. No new trials,
   resource reservation or permission to launch is conveyed by this handoff.

Main owns that execution and the campaign. This patch resolves initial native
loading/encoding plumbing, not completed parenting, a learned compiler, or the
full sprint. Fresh-procedure native runtime and hash costs remain unmeasured.
