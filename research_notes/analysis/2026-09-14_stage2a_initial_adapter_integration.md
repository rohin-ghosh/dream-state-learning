# Stage2A initial-adapter inspection: focused CPU integration

Builder, September 14, 2026, 00:51 UTC. Non-material caller-boundary helper;
no protocol, task distribution, visibility, recipe or claim change.

## Implemented boundary

`organism_v6/composition_birth_stage2a_initial_adapter.py` supplies
`inspect_initial_adapter(model, *, torch, layer_count, adapter_name,
expected_initial_adapter_sha256=None)`. It observes an already constructed
CPU model, derives the trainer-ordered all-layer ParameterSpec roster, and
reuses `validate_trainable_roster`, `_validate_model` and `adapter_sha256`.
It adds finite/nonzero-A and zero-B initialization observations. The frozen
result contains no tensors and preserves actual fp32 or bf16 adapter storage.

Pass the returned `trainable_roster` and `initial_adapter_sha256` to the
existing StatefulTrainer with the same layer/adapter identity. Arm, master,
batches, lineage and preparation identity remain separate caller inputs.
The caller must prevent concurrent model changes. The trainer independently
checks current adapter bytes against the supplied initial digest.

This is deliberately CPU-only, not a GPU-model inspector or loader. It does
not initialize a model, set seeds, change modes/configuration, fit, generate,
write files, or open native preparation. Observed zero-B/nonzero-A and default
policy metadata do not prove Kaiming sampling, RNG/seed history, byte-copy
history or authenticated model/tokenizer/runtime origin. Optional expected
hash agreement is integrity only, not authorization. No source-owner route/
core decision is inferred. Full native preparation remains unqualified.

## Main execution, not just worker reporting

Main staged an immutable 31-file source/test snapshot plus an empty test-package
marker and source hash manifest in an exclusive node2 directory:
`/tmp/astra_stage2a_initial_adapter_cpu_20260914_attempt1`.
Shared checkouts and old test artifacts were untouched. The exact command is
in the receipt. CUDA was hidden and never initialized; network-dependent
model fetching was disabled through offline environment variables. CPU intra-
and inter-op threads and OMP/MKL threads were all one.

Observed execution: September14 **00:49:57–00:50:03 UTC**.
The new focused module ran **11 tests, all PASS, no skips, 2.654 seconds**.
All31 staged hashes passed before/after execution; local source hashes were
unchanged. The receipt records distribution metadata: torch2.13.0,
transformers5.5.3, PEFT0.20.0. It does not record a torch build suffix or
authenticate runtime wheels, and is not full runtime qualification.

- Nine cases exercise synthetic source/error branches.
- One real-torch case checks both fp32 and bf16 adapter storage, exact hashes,
  parameters, storage pointers/version counters, gradients, mixed modes,
  config and CPU RNG preservation, and a changed-initialization rejection.
- One real PEFT case constructs a tiny two-layer Qwen2 from random config
  weights on CPU, with seven target modules and28 trainable A/B tensors. It
  checks roster/hash compatibility and no parameter/RNG mutation.

No pretrained Qwen2.5-7B weights, tokenizer, forward generation, optimization
or CUDA execution were used. A tiny config-built Qwen2 fixture is not the
frozen target base. This is not controller acquisition, native initialization
provenance, G1–G3, parenting or mechanism freeze.

Worker's earlier local run was9PASS/2skips; Main's receipt supersedes that
limited validation for this module. The historical604-test suite was not
repeated, and no combined615-test claim is made.

## Independent review and exact evidence

Noether independently reviewed the exact source/test hashes read-only and
returned scoped PASS: compatible ordered roster/hash handoff; preserved
storage dtype; CPU preflight covers frozen parameters and buffers; no
inspection-induced mutation under the concurrency exclusion; limitations
do not overclaim authentication or initialization history. Noether ran no
tests or models and granted no scientific/native execution approval.
Lovelace and Noether are closed; Main retains integration ownership.

| Artifact | SHA256 |
|---|---|
| Source module | `13fe0baeaab7ad19f59fa1efbc2db1fc5cee4a5ccc3d8ef17a9e88cea9059da8` |
| Focused test module | `805f15f0b48ed69ff4c7b6015c823b206838894aa4430268d7d3625a511d3978` |
| `receipts_20260912/astra_stage2a_initial_adapter_cpu_20260914_attempt1.log` | `9f1694764aac2c4601761b11dfb70ad7d4938d730bfcad6695d53925d9d0228e` |
| `gpu_artifacts_local/stage2a_initial_adapter_cpu_20260914_attempt1/source_bundle.tar` | `a88b6646580d792a9ce0f476491c0533d1f9ebe991051bd68f204a9a879637ba` |

The receipt path is relative to `research_notes/astra_memos/`; the archive
path is checkout-relative. Its embedded manifest binds all31 staged files.

## Next real campaign step

The requested Q0-FULLDOSE native preparation and three-root experiment already
completed in the historical record; no roots are reactivated. See
`2026-09-14_q0_fulldose_relay_and_level1_continuation.md`. Level1 work moved
this unfinished initial-binding boundary forward rather than repeating a
failed recipe or a passed suite.

Still required: owner-bound registered multi-step routes and core-depth/
recovery/history semantics, complete source inventory and adequate whole-
schema bounds, then separate real material/tokenizer/runtime preparation.
The next execution remains reduced560-slot BASE/D1 ATOM_LOCAL, then qualified
authentic same-adapter two-SLEEP. No new final-C11 gate, claim promotion, GPU
science, node1 write, Q0 launch, kill, or approval request occurred. Mission
active and incomplete; no worker/test/GPU experiment remains active here.
