# Held commands — do not execute before Main's source and node2 authority

These are command preparations, not a ready-to-run copier or enrollment script. Replace no missing evidence with guessed values. Runtime_generation2 has **no `copy` or standalone `enroll` CLI**: authorized source copying is a separate custody operation; `validate` is CPU-only; `dispatch` durably reserves the slot and launches its bounded evaluator. Do not call internal `reserve` directly.

## 1. Authorized source reader: exact initial-only archive

After actual births, Main must bind `COPY_ALLOWLIST` to the actual initial COMMIT hashes and authorize the exact candidate5 roots/read deadline and node2 transfer destination. Source reader verifies all three COMMIT hashes, native adapter inventories/state/initial-clone binding, and no symlinks immediately before and after capture. Use only the allowlisted12 files (each arm's COMMIT plus three known adapter files). Never select `latest`, glob sleeps, include optimizer/RNG, histories, INBOX, readouts, or evaluator content. The common-initial metadata is supplied separately from verified archives.

Exact archive creation command for that already-authorized/verified source reader, with fresh output and no traversal or recursion beyond named files:

```bash
set -euo pipefail
: "${MAIN_SOURCE_COPY_GO_SHA256:?actual source-copy authorization required}"
: "${MAIN_NODE2_CONFIG_GO_SHA256:?actual node2 staging/config authority required}"
: "${NEW_INITIAL3_ARCHIVE:?new private archive path required}"
test ! -e "$NEW_INITIAL3_ARCHIVE"
umask 077
set -C
tar -C /localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5 \
  --no-recursion -cf - \
  parented_learning/checkpoints/initial/COMMIT.json \
  parented_learning/checkpoints/initial/adapter/README.md \
  parented_learning/checkpoints/initial/adapter/adapter_config.json \
  parented_learning/checkpoints/initial/adapter/adapter_model.safetensors \
  parented_frozen/checkpoints/initial/COMMIT.json \
  parented_frozen/checkpoints/initial/adapter/README.md \
  parented_frozen/checkpoints/initial/adapter/adapter_config.json \
  parented_frozen/checkpoints/initial/adapter/adapter_model.safetensors \
  unparented_learning/checkpoints/initial/COMMIT.json \
  unparented_learning/checkpoints/initial/adapter/README.md \
  unparented_learning/checkpoints/initial/adapter/adapter_config.json \
  unparented_learning/checkpoints/initial/adapter/adapter_model.safetensors \
  > "$NEW_INITIAL3_ARCHIVE"
sha256sum "$NEW_INITIAL3_ARCHIVE"
```

The environment checks above merely prevent accidental execution with missing bindings; they **do not themselves verify or grant authority**. Main/source owner must verify the named GO objects and current custody before this command. Transfer only after Main supplies the destination/transport; do not infer credentials or execute now. After transfer verify archive SHA, exact member allowlist, regular files/no links, and native adapter hashes. Preserve any failed/partial capture; do not overwrite or quietly retry it.

## 2. Node2 custody preparation, still no enrollment

Use the existing `gpu.orch_r130_benchmark_sidecar.extract_regular_archive(archive, NEW_STAGING_DIRECTORY, exact_sha256)` helper to reject traversal, links and duplicate names. Keep its extracted `arm/checkpoints/initial` directories in staging, then place the verified regular files at the `COPY_ALLOWLIST` destinations `inputs/candidate5/<arm>/initial` without rewriting COMMIT bytes. The two path layouts intentionally differ; do not point candidate manifests at a guessed extraction location.

Copy only the eight hash-verified shared metadata archives to their explicitly listed `inputs/candidate5/shared` destinations after authority. Do not fetch the old source root. Finalize the three manifest/custody/candidate files from templates after checking actual born-arm COMMIT hashes, the common initial binding and all trusted timestamp receipts. Fill execution source pins from runtime_generation2/SOURCE_MANIFEST.json and use runtime_generation2/CPU_GATE.json; leave actual model/interpreter/device/walls/service/provenance to Main's bound node2 config. Never edit source/PLAN/frozen taskset.

## 3. Exact metadata validation and eventual dispatch

For each arm, after Main has issued the exact config GO:

```bash
export PYTHONPATH=/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1/preparation/runtime_generation2/source
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=
: "${R159_MAIN_GO_SHA256:?exact Main execution-GO hash required}"
: "${EXECUTION:?absolute finalized execution file required}"
: "${MAIN_GO:?absolute matching Main GO required}"
/localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r159_matched_evaluation \
  validate --config "$EXECUTION" --go "$MAIN_GO"
```

Validation alone never reserves/enrolls or loads CUDA. The following is **withheld until explicit Main evaluator enrollment/launch GO**, not authorized by the initializer's run GOs:

```bash
/localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r159_matched_evaluation \
  dispatch --config "$EXECUTION" --go "$MAIN_GO"
```

Run at most two concurrently, one per bound physical0/1; third initial waits for an admitted slot and full remaining job window. Each distinct initial slot charges56, so all three charge168 inside the immutable672/12 plan. Failed/ambiguous keys remain charged and never replay. Return only metadata:

```bash
/localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r159_matched_evaluation status \
  --plan /localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1/preparation/runtime_generation2/PLAN.json
```

No commands in this document have been executed by this preparation. Private corpus, prompts, answers, per-call results/scores and logs stay sealed.
