# EDITSTOP — actual-record paired V3 write sidecar, 2026-09-12

Implemented only the two owned `/tmp` Python files and this handoff. No repository edits, Git, network, GPU queries, native tokenizer/model execution, training, or readout. Main remains sole Git and launch authority. This is an engineering bridge, not evidence of parenting, semantic nonleakage certification, model authentication, or a change to claims.

## Exact tested bytes

SHA256:

| File | Hash |
|---|---|
| `/tmp/astra_rulegame_record_write_20260912.py` | `b81df36cdefd8679b6bcaa786965fcd8c900f7a279c338c6143d32a584eb9032` |
| `/tmp/test_astra_rulegame_record_write_20260912.py` | `784ee4b5fdf314b3cfcebff9ff46e1aa3113ad16f25ba1ad32f12038f26f4e74` |
| `organism_v6/rulegame_parenting_diagnostic.py` | `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526` |
| `organism_v6/rulegame_record_material.py` | `7eb7bbd04068a34be4932f11a0eab0109ddabcceb03210a07b657d57a0c621c1` |
| `organism_v6/train_adapter_v3.py` | `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7` |

Main reports the frozen source integration as `610c6edd05ce9c85720ee6e992889badecc2c158`; no Git verification performed. Actual input files were inspected for schema compatibility and hashed, not reassessed for outcomes:
- Main audit `/tmp/astra_rulegame_v3_main_audit_20260912.json`: byte SHA256 `d362f530bb422dae799f57607779bdc6d83873dd23e77e9a8437ddf13c16fda6`.
- Separate selection `/tmp/astra_rulegame_v3_fixed_selection_20260912.json`: byte SHA256 `54dd744a779decf44fd60ab41fcfcd100948fe85060491552611261d6970d816`; Main-supplied value hash `e3af02aca182aabee659a5e1fc98ac434f9228202ae328e06e7664f0f39db3d8`.
- Separate selection is supported without changing the audit JSON. If an embedded selection also exists it must agree; both input files are byte-pinned through fitting. Main's selected records/acceptance remain inputs, not a new decision here.

## Test result

**PASS: 23 tests, 15.615 seconds**, using synthetic captures, mocked native interfaces/tokenizer/models/training/supervision and existing pure export/encoding logic:

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES='' \
python3 -B -m unittest discover -s /tmp -p test_astra_rulegame_record_write_20260912.py -v
```

Coverage includes exact raw whitespace/context/target/EOS and causal masks; pair-atomic rejection/shortage; fixed selection, declined review and native-context mismatch; separate selection custody/conflict; freshness, deadlines and six-hour lease margin; independent fits and fixed recipe; GPU opt-in; source/base/audit/material/config/token tamper; base freezing; saved adapter identity/bytes; counts/drops/splits/packing; P failure blocks A, A failure preserves P; no retry/readout; cleanup verification and controller watchdog reserve. Tests do not establish native feasibility or semantic fidelity of Main's real records.

## Main execution templates — NOT run here

Run on the formation machine, with its unchanged original base/source paths available. Set `SOURCE_ROOT`, `DEADLINE_UTC`, and `LEASE_END_UTC` explicitly to the frozen source checkout, a timezone-aware future deadline, and the actual supplied lease expiry. Copy the unchanged audit/selection/sidecar to the paths below if absent there; no relocation of formation/base identity is implemented. `WRITE_ROOT` must not exist and must be a sibling of formation root.

```bash
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
FORMATION_ROOT="$HOME/astra_diagnostics/astra_rulegame_interaction_v3_20260912_attempt1"
WRITE_ROOT="$HOME/astra_diagnostics/astra_rulegame_interaction_v3_record_write_20260912_attempt1"
python3 -B /tmp/astra_rulegame_record_write_20260912.py prepare \
  --formation-root "$FORMATION_ROOT" \
  --main-audit /tmp/astra_rulegame_v3_main_audit_20260912.json \
  --fixed-selection /tmp/astra_rulegame_v3_fixed_selection_20260912.json \
  --source-root "${SOURCE_ROOT:?set frozen source root}" --out "$WRITE_ROOT" \
  --device 2 --deadline "${DEADLINE_UTC:?set deadline}" --lease-end "${LEASE_END_UTC:?set real lease expiry}"
```

`prepare` performs replay, native-call/context auditing and `build_record_pair` with the actual local tokenizer. It checks both arms fully before creating output; no rejected pair is published. Preserve its returned `plan_sha256` verbatim, then only Main may authorize:

```bash
python3 -B /tmp/astra_rulegame_record_write_20260912.py write \
  --root "$WRITE_ROOT" --plan-sha256 "${PLAN_SHA256:?copy exact prepare return}" --allow-gpu
```

## Frozen behavior / remaining checks

- Exact actual corpora are sealed separately from source maps, Main audit and full-token receipts. Trainer receives only corpus spans, never provenance maps or parent assessment prose. Existing exporter rejects forbidden parent/restatement spans, wrong contexts/versions and invalid source joins; no stripping, raw JSON reserialization, synthetic Situation, later replacement, or SEQ095 reuse. Raw-origin binding is not automatic semantic nonleakage certification; Main's explicit assessment remains required.
- P then A, fresh independent bases/adapters/optimizers: r8/alpha16/dropout .05/LR1e-4/epochs12/batch2/accum1/seed2, maxlen4096, no pack, all standard projection modules, AdamW/bf16, no init adapter. Exactly 12 updates per arm; any drops/splits/count mismatch fails. Existing trainer's split policy is never accepted as actual splitting: full native encoding and resulting manifests must show zero splits/drops.
- Reuses existing V3 trainer and diagnostic supervisor. Controller budget is 1200 seconds inclusive of 140 cleanup reserve; workers capped at600, with existing supervisor remaining-time/cleanup bounds (and its existing10-second guard). These are nested, not additive or promises of two full600-second fits. Supplied deadline must initially leave1200 seconds and remain at least six hours before supplied lease end. No independent lease-control-plane verification is claimed.
- Full tokens, config, manifest, base pin inventory, pre-first-update and final LoRA-only trainability/counts, adapter configuration/safetensors coverage/hash identity are captured/checked. Pair material and each fit are sealed. Failure preserves partial evidence, blocks favorable retries and blocks A after a failed P; cleanup must be acknowledged. No legacy material/write/evaluate path is invoked.
- **Decisive pending native check:** Main must execute real `prepare` against the released formation using its actual tokenizer, then the two authorized supervised fresh fits, checking native receipts, exactly12 updates each, frozen base/LoRA-only trainability, saved adapters and resource release. None was executed here. A real failure is a preserved blocker, not permission to substitute material or retry automatically.
- **Fresh parent-free OFF/P_ON/A_ON readout is a distinct, still-pending bridge.** Successful writes report `PAIRED_ADAPTERS_SAVED_READOUT_PENDING`, not competency/readout completion. Legacy CLI write/evaluate are not wired to this actual-record path.

EDITSTOP. No further implementation or ownership outside these three `/tmp` files.
