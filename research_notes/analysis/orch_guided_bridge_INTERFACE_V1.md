# GUIDED-BRIDGE public interface V1 — frozen for Old Builder via Main

2026-09-14, after raw Rohin79 (`36a0a2db`). Import from
`organism_v6.orch_guided_bridge`. No GPU/model/task generation or native launcher
exists here. Main assigns all `gpu/orch_guided_native*`,
`organism_v6/orch_guided_native*`, `tests/test_orch_guided_native*` work separately;
GUIDED-BRIDGE does not edit those paths. All coordination goes through Main.

## Exact loader-facing types

`AdapterIdentity(path: str, state_sha256: str, base_sha256: str, files: tuple)`

- `path`: canonical absolute adapter directory, no directory aliases.
- `state_sha256`: lowercase64-hex loaded-adapter tensor-state identity using
  the exact native protocol's hash convention. Not a label such as37ec.
- `base_sha256`: lowercase64-hex frozen-base state identity using that same
  published protocol's base-hash convention. Native caller supplies model path
  separately and must keep the Qwen2.5-7B-Instruct/one-LoRA invariant.
- `files`: ordered tuple of `(relative_filename, lowercase64-hex_file_sha256)`
  tuples, covering all files in the adapter directory. Preserve recorded order
  when constructing observed identities. No traversal or symlink aliases.
- `.verify() -> self`: streaming manifest verification, no model load.
- `.document() -> dict`: keys `path`, `state_sha256`, `base_sha256`, `files`;
  the last value is a JSON list of two-element lists.
- `.from_document(document) -> AdapterIdentity`: exact-key parse plus verification.

`StageBinding` is a frozen dataclass with fields, in order:

`run_id`, `arm`, `cycle`, `phase`, `adapter`, `parent_present`,
`fresh_process`, `plan_sha256`, `receipt_refs=()`.

`adapter` is the above `AdapterIdentity`; `receipt_refs` is a tuple of
`ReceiptRef(path, sha256)` with exact-byte receipt-file hashes. Consume bindings
returned by the bridge, not manually invented expected states.

Exact boundary signature:

```python
binding.verify_loaded(
    adapter=observed_adapter_identity,
    base_sha256=observed_frozen_base_hash,
    parent_present=observed_parent_present,
    fresh_process=observed_fresh_process,
    transient_context=observed_transient_context,
    sleep_prompt=observed_sleep_prompt,
)
```

Returns `None` on success; validation mismatch raises `ValueError` (filesystem
errors propagate). **Observed means measured, not copied from binding.** This
checks receipt bytes and adapter-file bytes again, exact path/state/base/files,
parent visibility, and readout freshness. For `phase='sealed_readout'`,
`transient_context` must be exactly `()` and `sleep_prompt` must be `None`.
Native loader must actually load `binding.adapter.path`, measure tensors/base,
and maintain appropriate process/context isolation. There is no load method or
authorization token in this object. A returned `None` is not launch permission.

## State handoff

- `plan_cycle(lineage, contract) -> CyclePlan` validates all prior receipts.
- `plan.binding('collection')` and `.binding('training')` use the identical
  previous completed adapter. Training binding is forbidden for GUIDED+FROZEN.
- `complete_cycle(plan, completed_receipt_ref) -> (next_lineage, readout_binding)`
  verifies the output and returns its fresh parent-free readout binding.
- `initial_readout(lineage, contract) -> StageBinding` binds cycle0 evaluation.
- Retain `next_lineage` for the next `plan_cycle`; do not restart from genesis.
- Three exact arms: `GUIDED+SLEEP`, `GUIDED+FROZEN`, `UNPARENTED+SLEEP`.
  Three cycles only. Frozen always uses the original adapter and has no fit.

The handoff document specifies receipt fields and exact owned arm/cycle paths.
No old native receipt is implicitly upgraded into this completion schema.

## Family and optimizer declarations, not a registry

`CallerContract(new_trajectory_rows, trajectory_presentations,
optimizer_lifecycle, recipe_json, family=FAMILY, family_status='PENDING',
family_designation_sha256=None)` accepts a symbolic named family. Status is
`PENDING` or `MAIN_APPROVED`; the latter requires a lowercase64-hex hash of
Main's published designation supplied by Main/caller. It neither reads nor
writes the family registry. The default route-family constant is a convenience,
not a whitelist. Pending has no designation hash. Manifest has
`execution_scope='CPU_PREPARATION_ONLY'` and **no `launch_authorized` field**.

Only `RESET_EACH_CYCLE` is supported for sleeping arms; frozen reports `NONE`.
Recipe JSON contains exactly `optimizer='AdamW'`, explicit `optimizer_kwargs`
(betas, eps, weight_decay, amsgrad, foreach, fused), `learning_rate`, `seed`,
`native_protocol_sha256`. Native training must implement that declared policy;
this bridge does not instantiate AdamW or support optimizer restoration.

## Projection/mask boundary

`project_child_capture(capture, expected_sha256, collection_binding,
private_guidance=tuple_of_exact_private_strings)` copies public captured prefix
and exact raw admitted child bytes; rejects inventoried guidance, never scrubs
targets. No actual captures supplied or manufactured by this CPU worker.

`validate_encoding_boundary(encoded, prefix_ids=..., target_ids=...,
suffix_ids=..., eos_token_id=..., validate_masks=existing_validator)` validates
exact token concatenation and prefix/target/EOT/suffix masks. Native caller owns
byte-to-token roundtrip and original reference-label loss normalization.

Main-facing peer message: this is the frozen V1 seam Old Builder can import.
Honor priorstate in both collection and training and test the observed tensors;
do not echo expected hashes. New native seam belongs to Old Builder only.
