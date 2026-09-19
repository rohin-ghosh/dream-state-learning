# Matched controls: next experiment, not an existing result

2026-09-16 12:32 PDT. Planning only. No GPU allocation or launch is recorded
here. Frozen Qwen2.5-7B-Instruct and rank-8 LoRA remain unchanged; no scientific
claim is promoted. Main has not read the sealed benchmark findings.

## Current evidence gap

The read-only control audit found that R139 frozen controls omit sleep,
presleep generation and compaction, and insert different runtime notices.
Matching their every-two-ordinary-segment readout setting does not match the
full experience or context schedule of a distilling learner. Native full
adapter/AdamW/Torch-RNG loading exists, but a new-life fork from that checkpoint
is not exposed by the current launcher. Identical seeds alone do not prove
initial tensor identity. R137 raw1/raw3 remain unmatched observational lives.

Relevant implementations: `gpu/orch_r139_continual_controls.py`,
`gpu/orch_r125_continual_native.py`,
`organism_v6/orch_r125_continual_stream.py`. This is a source audit, not a new
model evaluation or an explanation derived from held scores.

## Proposed primary comparison

Three new, explicitly matched lives from the same saved initial rank-8
adapter: parented learner, parented frozen-adapter control, and unparented
learner. All use the same frozen base/tokenizer, initialization manifest,
condition-neutral factual startup bytes, decoder, context budget, ordinary
segment boundaries, presleep invitation and replay policy. Use one seed,
with later replication labelled separately. Never relabel existing lives.

The frozen arm should execute the same presleep generation and context
compaction schedule but perform **no optimizer updates**. It needs an explicit
control-boundary receipt, not a fake successful learning receipt with invented
steps. The unparented arm needs an enforced empty-parent input channel; tool
and environment turns remain separately attributed. Parenting uses the same
policy and cadence, responding to each actual child's trajectory; identical
parent text or equal realized trajectories are not assumed.

Every branch records actual parent exposure, generated tokens, context
operations, eligible/rejected rows, optimizer steps and durations. Label
ordinary-segment alignment separately from token exposure and wall time.
Sleep-0 and each corresponding boundary receive fixed, parent-free,
file-free, fresh-process readouts. The evaluation custodian retains held
contents and findings; no score gates continuation, checkpoint selection or
parent messages.

## Implementation and tests required before allocation

1. Expose a bounded new-life initialization from a pinned checkpoint without
   inheriting old conversation, inbox, training rows or event IDs. Preserve
   source lineage and verify actual adapter tensors and applicable optimizer
   and RNG state, rather than merely filenames or seeds.
2. Add the explicit frozen control-boundary path with matching presleep and
   compaction semantics. Test zero weight/optimizer change and truthful
   receipts; never relax ordinary learning-receipt validation globally.
3. Add cross-arm startup/decoder/schedule checks, enforced no-parent input,
   isolated evaluation routing, and regression tests proving readouts never
   enter learning buffers or parent prompts.
4. Register the fixed comparison and missingness rules before dispatch;
   independently check the actual state/prompt bindings and log the builder's
   CPU/provenance pre-GPU gate. No performance claim follows from that gate.

## Allocation status

No three-GPU allocation has been verified free. Node2 physical0/1 belong to
the benchmark and 2–7 to the six protected generation workers. Node4 physical2
is the kernel execution sandbox, not spare inference capacity. Node5 physical1
is F2's failed life awaiting exact-state recovery, not an available control
slot. Existing continual children and their parents are protected. Any new
allocation requires a fresh occupancy and ownership check; do not displace
those lives or acquire/extend leases under this planning note.
