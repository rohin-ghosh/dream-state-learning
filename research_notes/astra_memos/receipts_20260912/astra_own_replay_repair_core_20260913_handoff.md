# Own-source replay repair core — final handoff

2026-09-13. **EDITSTOP.** Only the three files named below belong to this worker.
No repository/old-helper/runner changes; no Git, network, native/model/tokenizer,
GPU, collector or launch operations. Temporary CPU fixture directories were
created by the owned tests and removed. No live monitoring resumed.

## Exact final hashes

- Core `/tmp/astra_own_replay_repair_core_20260913.py`: SHA256 `9d8777ea3bfdcf92bace3b1a459644b9249dae108db9d5d6a3e35433e0bcff93`.
- Test `/tmp/test_astra_own_replay_repair_core_20260913.py`: SHA256 `0b6ffe722b635eb26ad0a3d00240b7a6a97b35d6c3ad3477086e0b56bbe0eca4`.
- Handoff `/tmp/astra_own_replay_repair_core_20260913_handoff.md`: its SHA256 is returned separately to avoid self-reference.
- Frozen protocol `research_notes/astra_memos/ASTRA_OWN_SOURCE_REPLAY_REPAIR_2026-09-13.md`: verified SHA256 `fb523ee6d96ef6186ae187c3c9b4482b25084fa49f292aae15a34affa87103c7`. Main reports commit963aa528; no Git lookup performed.

## LOCKED API — matches Main / Parfit

```python
build(memory_plan, bound, capture_plan, capture_report, seed,
      *, protocol_path=PROTOCOL_PATH,
      capture_runtime_path=CAPTURE_RUNTIME_PATH) -> material

encode(material, arm, tokenizer, trainer, helper, probe, fit_seed) -> encoded_arm
```

Main/Parfit supplies the FULL once-collected `replay_report.json` as
`capture_report`. An exact seed admission object is also accepted, but is not
needed by the locked runner. Both supplied forms are compared with the same
saved summary/admission chain; neither form bypasses native custody checks.

`encode` returns a **FLAT PER-ARM** dictionary, NOT a nested arms object:
`items`, `encoding`, `epoch_order`, `fit_seed`, `rows`, `updates`,
`presentations`, `total_tokens`, `target_tokens`, `context_tokens`,
`train_tokens_seen`, `actual_supervised_tokens`, `actual_context_tokens`,
`actual_padded_tokens`, `padding_tokens`, plus `schema`, `material_sha256`,
`status`, `seed`, `arm`, `per_kind`, `presentation_counts`,
`training_items_sha256`, `epoch_order_sha256`, `encoding_sha256`.

The *material* alone contains `arms["REPLAY"]["rows"]` and
`arms["EXTRA_MEMORY"]["rows"]`, together with `schema`, `status`, `seed`,
`parent`, `source_bindings`, `memory_rows`, `replay_rows`, `replay_rejected`,
`counts`, `interpretation_limits`, `material_sha256`.

Both content hashes use canonical JSON (`sort_keys=True`, compact separators,
finite values, final newline), omitting their own hash field. The training item
and epoch-order hashes use the same serialization. Flat `rows` is a count;
flat `presentations` and `updates` both equal eight times that count.

Direct agent messaging is unavailable. Coordination used Parfit's read-only
owned runner handoff and Main's explicit relay. Runner calls were inspected
and match the API above; this worker did not run or edit Parfit's runner/tests.

## Source validation and custody boundary

- Requires the exact repair protocol and pinned capture runtime. Calls existing
  `capture.verify(root, plan_hash, native=False)` and `capture.validate_completed`.
  Does not call `core.admit`, `capture.collect`, generation, fit or native prepare.
- Reads the existing once-only collection claim; binds completion, all three
  admission-file hashes, full summary, collection, source pins, all-seed counts
  and native token/time costs. Rejects failed/retry collections and promoted flags.
- For the selected seed, joins every fixed TRAIN request to its saved native
  request/response and core response hash. Checks exact raw targets, original
  prompt/source/producer identities, all24 responses, lexical admission order,
  the full96-row ledger and every saved reject. Uses the unchanged source judge
  to validate saved audits; no new responses, admission policy, retry or source
  selection. Core admission flags are never flipped to claim native identity.
- Checks exact immutable original per-seed memory plan hashes and the plan-bound
  dataset/capture/retention hashes; preserves all14/8/8original rows unchanged.
  Requires capture producer/model/adapter-file/parent-plan identity to equal
  that memory plan's original recipient, not a descendant.
- `memory_plan,bound` must come from the original memory runtime's verified
  context. Full old memory completion/once-collection and historical LOWER/HIGH/LR0
  verification remain the runner's job. The core checks frozen plan/object pins
  rather than re-running a separate historical custody audit.
- Stored release receipts are checked; no live process release is inferred.

## Material and encoding behavior

- Original memory rows remain in their saved array order. Replay uses every
  admitted row in lexical original row-ID order. EXTRA_MEMORY cycles that saved
  original memory order for exactly r extras; it does not create new records.
- Presentation IDs are unique across both arms (`own-repair:seedN:ARM:NNN`).
  `source_row_id`, `item_kind`, `presentation_index` and unchanged source/proof
  distinguish presentation identity from original source identity.
- Replay spans use original TRAIN request prompts and unchanged actual child
  observation responses. Memory/extras use unchanged source-withdrawn memory
  cues and raw records. Neither source metadata, provenance nor saved readout
  material is inserted into training text.
- Eight deterministic batch1 passes,1024token bound, one item per sequence;
  frozen helper/trainer/probe pins are checked before nonempty encoding. Raw
  target plus one EOS is supervised; context, template tail and padding are
  masked. Splitting, context/target truncation and rewritten target bytes fail.
- Both arms receive8(m+r)updates. Pair order matches by presentation position
  under the same original seed. Per-kind counters explicitly distinguish8m
  original-memory exposures from8rreplay or8rextra-memory exposures; token
  totals are not claimed matched. Padding is zero in the batch1 path.
- r0 gives `REPLAY_UNAVAILABLE`, both material arms empty and flat zero-cost
  encodings, with no tokenizer/helper/trainer calls. The original memory bank
  and all rejects remain in the material. Neither arm may fit.

Main reports current native r24/24/24; this worker did NOT inspect those new
admissions or execute the builder against their live roots. At r24, arithmetic
is304/256/256updates per arm,1632across six fits. This is not a fit result.

## Validation performed

Final command: `python3 -B /tmp/test_astra_own_replay_repair_core_20260913.py`.
**15 tests PASS,6.665seconds.** Core syntax compiled in memory; no bytecode
output. No model or native tokenizer loaded. The frozen trainer's CPU list-based
encoder, packer, epoch ordering and collator were exercised with a toy tokenizer.

Fixtures read the actual original memory archive in memory, with no extraction:
`gpu_artifacts_local/actual_record_memory_20260913_attempt1/evidence.tar`, SHA256
`3ed6579e7e885139d78faf3457eb3bec254215d36b533558ef22f8199ff6a003`.
Original TRAIN fixtures come through the pinned replay core's actual perception
archive, SHA256 `addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a`.
Synthetic child responses give r24/12/0 deliberately, covering full/mixed/empty
admission. These scripted receipt trees are NOT actual native outcomes.

Capture verify and completed-custody validation run unchanged on the synthetic
receipt trees. Test-only capture binding supplies already-loaded original
corpus bundles and fake adapter-tree availability. Model/GPU preparation is
not called. `admit` and `collect` are patched to fail if invoked by build.

Coverage: original all-seed memory/source pins; all-row preservation; maximum
step arithmetic; seed/full-report API equivalence; distinct duplicate IDs and
cycling; raw JSON/whitespace roundtrips; source/teacher/held/source-ID/prompt
tampering even after rehashing saved admission; omitted admission; forged source
eligibility; raw/native/producer/release tampering; prepare/completion/once-claim
and join tampering; deterministic matching pair order; per-kind tokens/dose;
exact context/target+EOS/tail masks; EOS/PAD and truncation rejection; no-write
r0; material tamper detection; no mutation of input objects.

During development, the initial toy tokenizer merged leading response whitespace
with the prompt newline, which the frozen encoder correctly rejected. Only the
toy whitespace token rule changed. An added test-block placement error was
also repaired. No frozen helper/trainer edits were made.

Unchanged dependency hashes rechecked after implementation:
- Capture runtime: `1142593afb544dec2344c77788f6dbb624f519897b0bb65e135a9e8eb1910107`.
- Replay source core: `f64e65a462afe7c2ed28d3dae16289d12bfc62b624b8d4900ff66a713f105f1a`.
- Row encoder helper: `6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e`.
- Frozen trainer: `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`.

## Remaining Main responsibilities / limits

Main runs integration tests and native CPU preparation on immutable accessible
original roots, passes native copies of the two source-bound protocol/runtime
paths, freezes both arms' artifacts, then separately decides launch. Native
token boundaries, fresh optimizer/LoRA tensors, actual parameter change, budgets,
release and unchanged cold readout/constant diagnostics are runner/native duties.
No launch approval, native/HF parity, repair success, keyed binding, parenting,
new TRY experience or H1/H2 promotion follows from these CPU results.
