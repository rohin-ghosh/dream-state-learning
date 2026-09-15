# Replay compiler handoff — Laplace / Main / Cicero

2026-09-15 05:05 UTC. CPU interface and checkpoint99 math adapter ready; no admitted native replay batch compiled or fitted yet.

## Ready source and tests

- `organism_v6/orch_continual_batch_replay_compile.py` SHA256 `0c4564d47bd3666a5589b8964b770f6ea04da351a0d04e7b8940bd4bbc06db46`
- `gpu/orch_continual_batch_replay_compile.py` SHA256 `9f7635b039fe6977a793974ca6310bb400f43c9dc0685c1656be57ab85fb7478`
- `tests/test_orch_continual_batch_replay_compile.py` SHA256 `650c8f19a2a88b191f1dd9c1d9a3f447285c0681f70278019e690160c4dfaf0d`
- `REPLAY_CPU_TESTS_0503_ADAPTER.txt`: 63 focused tests PASS; SHA256 `6bbdae29216b40b154504692888f1670c86a881f1bef14637fc9c8a1ead489fe`. Earlier 60-test receipt preserved.

The tests cover TRAIN held-ID/hash exclusions, teacher/parenting/held-readout rejection, purpose-based registry rejection despite safe filenames, actor/checkpoint mismatch, changed raw bytes, symlink escape, prospective sample binding, exact native target masks, oversize rejection without mutation, mixed-vs-isolated claim boundaries, and CPU/outside-worktree execution guards. Branching/serialization tests retain rejected-path evidence without automatic FAIL and unsampled UNKNOWN.

## Actual child generation exists; not yet a compiler batch

Native node2 root: `/localhome/local-rohing/orch_rich_hot_node2_checkpoint99_20260915_attempt1`.
Exact inspected evidence is in `CHECKPOINT_TRAIN_SOURCE_HANDOFF_0459.json`.
At 04:59:06 UTC, 782 captured calls had the exact FULL256 identity, checkpoint commit and generation source hashes: 39 CODE, 39 math, 704 ROUTE actions. All 39 math responses matched their original cached TRAIN question and numeric gold with observed oracle success and zero frozen held-ID/question-hash/route overlap. These are 39 distinct raw math targets, NOT 39 semantically admitted examples. No code/route semantic or mechanical admission is inferred from their counts.

First real child CODE capture was 04:26:24.097610 UTC; first math was 04:26:32.117565 UTC. Child state `93a036b93e2d41d2715230aaf2f2fa5382f4cbe404c743fd36dc37aba7f7c0d8`; frozen base `a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`. Classification CHECKPOINT_DERIVED_NOT_IMPROVED; no held readout was accessed. The older source's last captured completion was 04:47:25.700081 UTC; this receipt does not assert that its original PID is still running after the producer's V3 roll.

Native producer manifests: `/localhome/local-rohing/orch_rich_hot_node2_supply_20260915_attempt1/checkpoint99_raw/batches/*/MANIFEST.json`. The exact `NODE2_CHECKPOINT99_MATH_V1` adapter now preserves original `B...` task IDs in provenance, binds source TRAIN IDs/checkpoint/source code, and preserves original messages, response bytes and native token IDs. It rejects CODE/ROUTE, non-single-pass calls and wrong answers rather than fixing them. The native CPU probe at 05:05:08 verified all 39 math captures against real tokenizer, original intent and full masks; maximum train sequence 565, 8,799 generated content tokens total. The probe produced no semantic review, admitted batch, fit or GPU call. See `NATIVE_REPLAY_CPU_REFERENCE_0505.json`.

39 verified math targets are below the frozen 64-row pilot; do not fill with teacher/held/L2 or silently mix original37ec. `REPLAY_SOURCE_REGISTRY_0505.json` enrolls only the verified checkpoint99 math source for future prospective sampling, not training admission. V3-derived captures require their own purpose/root/source identity binding before combination. No new review calls or quota reset are authorized by this source receipt.

## File-bound compile interface

Run the new CLI only from a separately hash-pinned, native outside-Git runtime with `CUDA_VISIBLE_DEVICES=''`; do not change the currently running publisher's runtime. Arguments are `--request`, `--request-sha256`, and a fresh native-only `--output` whose name starts `orch_continual_batch_`.

Request fields:

- `native_evidence_root`: unique node-local evidence directory.
- SHA256-bound `{path, sha256}` references: `registration`, `source_registry`, `exclusions`, `checkpoint_handoff`, `loaded`, `tasks`, `candidates`, `reviews`, `sample`.
- `model_dir` and `tokenizer_files`: frozen native tokenizer hashes, including tokenizer JSON and template config.
- Registration explicitly fixes `source_kind=CHECKPOINT_DERIVED_TRAIN`, `source_purpose=L1_EXTERNAL_GENERATION`, `split=TRAIN`, false parenting/teacher/held-output flags, allowlisted generation roots, child state, base, EOS, and checkpoint-manifest lineage. The source registry must agree field-for-field.
- Candidate provenance binds the original native call path/SHA and `native_intent_ref`; any reconsideration additionally binds `previous_own_call_ref`. Set `native_format=NODE2_CHECKPOINT99_MATH_V1` for the actual checkpoint source; provide original task ID, source-code SHA and checkpoint commit in the bound registration/provenance. Neutral-format math remains supported. No raw bytes or historical task IDs are rewritten.

The compiler checks all candidates against their native call, intent, source task/gold, loaded child, held exclusions and exact tokenizer/masks. It verifies the pre-outcome 12-sample registration, validates existing fulltext reviews without new calls, recomputes >=10/12/no-hard-grounding-or-gold batch admission, and excludes sampled nonPASS. It never fabricates per-row semantics for unsampled candidates. Oversized native rows remain raw and are logged in `SKIPPED.json`; no crop or padding. Native-only outputs are `ROWS.json`, `SKIPPED.json`, and `COMPILE_HANDOFF.json`; the CLI returns only native path/hash/counts.

## Fit and claim boundary

`CURRENT_MIXED_CONTINUAL_APPEND` is not isolated own-output attribution. `ISOLATED_PAIRED_WINDOW` requires a prospective paired-window ID, common initial state and matched masked-target control. Laplace owns actual paired fit and richness-first held readout; neither is executed by this compiler. Held outputs NEVER become compiler inputs. Behavior readout tracks default tokens, distinct approaches, rejections with exact why, repetition and cohesion; oracle success is a source-admission requirement, not a substitute for richness.

## Disk / current publication

The native-only controller PID3443504 remains active with its original 06:10:32.518 UTC deadline, <=128 single-attempt review invocations and <=2 parallel providers. It does not read the old segment2 raw trees. All new raw/archive/ROWS evidence remains native; only bounded temporary sample/provider packets are held outside Git on VM, removed after verified native transfer.

Main may mirror only segment2 `batch_000` through `batch_026` `/raw` directories, verify native bytes and push tree/hash receipts, then prune those exact scopes. `QUIESCENT_RAW_INVENTORY_0457.json` enumerates all paths; select `kind=raw_extraction`, NOT archives. Keep all manifests, candidates, ROWS, budgets, reviews, decisions and wrappers unchanged. No old publisher PID exists and no own pending readers remain. Cross-user reader checks were restricted; recheck other consumers immediately before pruning and publish relocation receipts for historical raw references. Main owns archive/Git actions; this worker deleted nothing.
