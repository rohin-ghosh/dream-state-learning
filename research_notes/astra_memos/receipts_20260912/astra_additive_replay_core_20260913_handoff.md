# Additive replay core — EDITSTOP

September 13, 2026. Source/data-only pairing, no fit/model/native operation.
Main owns protocol and launches; Beauvoir owns the explicit trainer. Existing
files/results/IDs are untouched. This core is frozen; runner freeze is separate.

- Core `/tmp/astra_additive_replay_core_20260913.py`:
  `b58e4c90e2abdd26648475c9fb1fe92e3bc3fef2fa7664ecaaa69fc93591076a`
- Tests `/tmp/test_astra_additive_replay_core_20260913.py`:
  `b73c81f3d3b15f85bfcfb475cbbd30425b0f132d79bd1f4586a99f3863f53aee`
- Protocol `ASTRA_ADDITIVE_REPLAY_DEV_2026-09-13.md`:
  `724d5a6e1aea7dca4b0ae42aec6e2fd0252b98646f7c903432927263f2c391e9`

## Concrete API

```python
build(repair_plan, repair_bound, *, protocol_path=PROTOCOL_PATH) -> material
validate_material(material)
prepared_from_saved(material, arm) -> prepared
encode(material, arm, tokenizer, trainer, helper, probe, fit_seed) -> prepared
```

`repair_plan,repair_bound` must come from the unchanged frozen own-repair
verification/custody path. Runner adds `saved_training` keyed EXTRA_MEMORY/REPLAY
and `saved_training_sha256` holding their actual file-byte hashes after checking
the old plan's pins. Source identity is NOT inferred from arbitrary JSON. Core
also checks canonical object consistency and original encoding self-hashes.
Original plan/mixture/parent/source lineage remains unchanged. Runner validates
completion/collection/raw joins; this core is not a substitute for that check.

`material` schema `astra_additive_replay_material_20260913_v1` contains exact
mixture, both old training objects, actual file-byte bindings, protocol, original
parent, repair plan/source/input hashes, counts,24pairs and material self-hash.
Every pair is `{memory_row_id,replay_row_id}` using the historical occurrence
IDs, not source IDs. Pair construction is fixed once in original construction
order; the observation side follows frozen lexical source order.

Both arms preserve EXTRA_MEMORY `items`, `encoding`, `epoch_order`, item IDs,
source metadata, target bytes, context masks, EOS and tail masks EXACTLY. No
rotation, rebalancing, renaming or replacement of a memory position. Seed0
preserves four source rows with16presentations and ten with24presentations over
eight epochs. Seed1/2 preserve their original counts too.

Prepared schema `astra_additive_replay_encoding_20260913_v1` keeps the flat
primary legacy accounting fields memory-only and exposes explicit
`token_accounting` for memory versus executed replay and combined totals.
`replay_items/replay_encoding` are exactly the24existing observation entries;
the old REPLAY memory prefix is never replayed as an observation. `pairs`,
`objective`, source encoding hash, pair hash and memory-source presentation
counts make ancestry/repetition visible. ADDITIVE192extra observation forwards
per root; MEMORY_ONLY0. Steps304/256/256each arm,1632campaign, unchanged.

Native `encode` calls frozen own-repair `encode` separately for both old arms
and rejects any original token/prompt/mask/order mismatch before returning.
Frozen source is `/tmp/astra_own_replay_repair_core_20260913.py`, hash
`9d8777ea3bfdcf92bace3b1a459644b9249dae108db9d5d6a3e35433e0bcff93`.
No collection/admission/capture/teacher/model call is made. Non24 banks fail
closed; this adopted protocol has no zero-admission fallback or source filter.

## Accepted trainer interoperability

Beauvoir's original seam is ACCEPTED, superseding the earlier proposed signature:

```python
paired = additive_trainer.prepare_pair(
    old_extra_memory_encoding, old_replay_encoding,
    seed=seed, source_pins={"extra_memory_sha256": actual_file_hash,
                            "replay_sha256": actual_file_hash})
additive_trainer.run_training(paired, tokenizer, base, config, out,
    arm=arm, init_adapter=original_adapter, expected_parent_files=original_files,
    trainer=frozen_trainer, corpus_sha=new_training_file_hash)
```

Runner checks trainer `primary/replay/pairs` against this core and all token/dose
totals against independently computed prepared counts. `paired.json` is common
to both arms; no incompatible alternative trainer-plan format is used. Sum of
separate mean-token CE, gradients and native optimizer parity belong to the
explicit trainer and Main's tiny Torch prerequisite, not this list-based core.

## Verification and limits

10 CPU tests PASS,1.218s on final code. Tests read preserved old plan/mixture/
training input objects for all3roots, not historical fit outcomes; they verify
actual source hashes, all pair/dose counts, unchanged raw spans/audits/orders,
no rebalance, per-source repetitions, compute asymmetry, rehashed pairing drift,
changed context/schedule, parent/seed rejection, no mutation, and both old
encoder calls. Encoder orchestration uses mocks where a native tokenizer is
required. No Torch/model/native tokenizer was loaded.

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 90s python3 -B -m unittest discover \
  -s /tmp -p 'test_astra_additive_replay_core_20260913.py' -q
```

Sources remain own responses to already-trained authored observation contexts,
not novel TRY experience. Original memory records remain actual earlier TRY
records. Matched memory occurrence dose does not imply matched tokens/FLOPs,
RNG, gradients or elapsed time. No fit decision, promotion, parenting or H1/H2
qualification is produced. Native tiny Torch/tokenizer verification is pending
Main, not established by these CPU fixture passes.
