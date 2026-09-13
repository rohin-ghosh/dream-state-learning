# EDITSTOP — EVENT-only execution seam

**2026-09-13 15:21 UTC. Ready for Main integration; ownership released.** Only the four new files below and this handoff were written. No importer/writer, existing own-write/interface/lifecycle files, scope, originals, allocation, or other worker files were edited. No commits, remote access, GPU/model execution, native tokenizer qualification, fitting or native READs were performed. In particular, no node2 SSH occurred during A1's detached release window.

## Frozen files and tests

| File | SHA256 |
|---|---|
| `gpu/astra_pcfl_event_only_command.py` | `3ebef8ce6c8cd783104f5d0d74946fd1df5f99e41208508451482f56fdf9d916` |
| `gpu/astra_pcfl_event_only_outer.py` | `5bc4f24a744a2ee53edbe7623ce0e10831fd8a566fcfbae58e1f84531a89aac4` |
| `tests/test_astra_pcfl_event_only_command.py` | `50d187c18406e76ffd39ac35563692acab218969f24ce5991529290af4c80254` |
| `tests/test_astra_pcfl_event_only_outer.py` | `697e43ef0547a1c296c9a5f6bd1520f468b84e2435079d8ba633830a95c35520` |

**78 tests PASS /25.809 seconds**:11 command,8 outer,13 existing importer,13 existing EVENT writer,33 existing readout.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. python3 -m unittest -q \
  test_astra_pcfl_event_only_command test_astra_pcfl_event_only_outer \
  test_astra_pcfl_event_prefix_import test_pcfl_event_only_train \
  test_astra_pcfl_own_write_readout
```

The tests use the fixed local archived evidence with explicitly simulated original replay/tokenizer/encoding/trainer fixtures, plus injected ReadoutActor sessions and real harmless local child processes. They are **not wholly synthetic input evidence** and do not certify native tokenization or numerical execution. Importer/writer tests still require the fixed archived fixture. AST/trailing-whitespace checks on all four files and prepare/fit/readout/outer CLI help checks pass. Command305 lines, outer212; no new numerical loop or general guard framework.

Unchanged dependencies checked:

```text
7f12702dffd10d78fae1d115b0bfb6fcf4f993ef8de70c312e47ff6abfa9f88f  gpu/astra_pcfl_event_prefix_import.py
24faf066d22bd15361cd8fe95a40033a3011307cebb6ea94dad05c29aadf04e2  organism_v6/pcfl_event_only_train.py
8e33dc7876db5786ae07dfeec8306b0bfce5b2932ecbdf78284af89905e46428  research_notes/astra_memos/ASTRA_PCFL_EVENT_ONLY_SCOPE_2026-09-13.md
874bab61bc26549ad79f85fe193a26bc6ee53664e4957f0b45abbd89d5f1ed77  gpu/astra_pcfl_own_write_command.py
d8d4ef962ca80933f3c3a60681c8375198197855f8d5f00a2b7835461e8427c4  gpu/astra_pcfl_own_write_readout.py
fdd29c64bc73b1602998e6509da9f6d3132b90f9a5d50dceb1ad20ce86128f19  gpu/astra_pcfl_zero_fit_outer.py
```

## API agreed with Parfit's published contract

The implementation directly consumes Parfit's EDITSTOP APIs: `prefix.load_evidence`, `build_import`, `verify_tokenizer`, `event.build_schedule`, `build_fit`, `encode_fit`, `train_fit`, `read_roster`. No additional importer/writer behavior is requested. A direct inter-worker messaging tool was unavailable; the published handoff and Main's review updates were the coordination channel.

Command API:

```python
prepare(spec_path, spec_file_sha256, fresh_output)
stage(manifest_path, manifest_file_sha256, absolute_worker_deadline,
      stage="fit", arm=None)
stage(manifest_path, manifest_file_sha256, absolute_worker_deadline,
      stage="readout", arm="AUTH_WRITE")
stage(manifest_path, manifest_file_sha256, absolute_worker_deadline,
      stage="readout", arm="NO_WRITE_C0")
```

Tests can inject tokenizer/identity/environment, trainer/base factory, actor and clock. Injection is explicitly labeled; injected preparation/fit cannot be used as native evidence. Production CLI exposes no injection switches.

## Closed spec — native values supplied by Main

Use `schema="pcfl.event_only.command.v1/spec"`. Exactly these13 keys are accepted:

```text
schema, model_path, model_binding, base_state_receipt, shutdown_binding,
gpu_uuid, environment, expires_monotonic, boot_id,
archive, replay_receipt, authority, source_files
```

Six spec fields (`model_binding`, `base_state_receipt`, `shutdown_binding`, `archive`, `replay_receipt`, `authority`) use exact `{path, sha256}` records; the spec file itself is independently pinned by the CLI argument. Paths, environment, UUID, boot and cutoff must describe Main's actual native installation, not VM placeholders. `model_path` is the absolute existing offline base directory. `environment` reuses the own-write envelope **`{"native": native.environment_identity(), "peft_version": ...}`**, not the interface command's flat native environment shape.

`source_files` must equal `command.source_files()` evaluated from the intended executed snapshot. It includes the actual new command/outer/importer/writer, existing own-command/readout numerical dependencies and lifecycle sources, plus both required readout scope and the new EVENT-only authority. Stage the final source snapshot, compute this map there, then independently hash the finished spec. The old formation source map is not substituted for this new execution map. The unchanged own-write installed-shutdown source pin is reused; an installation mismatch fails rather than silently choosing another shutdown method.

Fixed original archive authority:

```text
ARCHIVE FILE SHA256 bd6829dfa4e6c0a63f48cf184e28091e12cf9de9a231e0f6cda6672d5133c869
```

Use Main's actual archive path with that pin. No alternate attempt/prefix is accepted, and archived source is read in memory, not extracted/executed by this seam.

Independent original-v3 replay provided by Main/Parfit:

```text
/tmp/astra_pcfl_event_prefix_original_v3_replay_20260913_attempt1.json
FILE SHA256 5659e39989a4dd26ca336c2787318bda43b1223bc7a52d67dbbf52b950b58dea
canonical receipt seal 56ca52a34fae625747423cd89a4829b91d8c5f15b422977e741ed98325bb1898
```

The spec pins its **file hash**, while `build_import` checks its canonical seal and exact original-path fields. The replay execution itself remains Main's external fact; this command does not rerun original formation or load relocated archived code.

`authority.path` must be the canonical EVENT-only scope path within the executed source tree and its file hash must equal **`fit.binding.authority_sha256`**. At this EDITSTOP that hash is `8e33dc7876db5786ae07dfeec8306b0bfce5b2932ecbdf78284af89905e46428`.

Base tensor, initialization/dropout seeds, training environment and tokenizer binding remain exactly Parfit's preserved original binding. The pinned CPU base-state receipt is checked against it and actual prepared model identity; the unchanged trainer separately checks fresh bf16 C0 tensor identity before LoRA/optimizer creation. No base-state hash is fabricated or inferred from adapter success.

## Preparation and its CPU gate

Fresh output only, disjoint from source/model/input files; explicitly empty CVD, local-only tokenizer and all offline flags;180-second preparation limit. Preparation:

1. Pins actual archive, independent replay file, CPU/model/shutdown/scope and current source map.
2. Loads the one original archive, validates/replays its fixed first16-call EVENT prefix, preserving all17 original captures and original FAILED/rc1 evidence. No new model calls.
3. Persists immutable `import.json`. Its status correctly remains **`EVENT_PREFIX_IMPORTED_TOKENIZER_PENDING`**; successful verification does not rewrite that object.
4. Runs the **actual offline** `prefix.verify_tokenizer`, persists positive sealed `tokenizer.json`, and binds both its canonical seal (`manifest.tokenizer_sha256`) and file hash (`manifest.input_files["tokenizer.json"]`). Manifest validation requires positive status, matching import,16 checked calls and zero model calls.
5. Builds the fixed14+6 schedule and scoped fit, then persists **all160 actual training encodings**, rejecting truncation through the unchanged encoder. Encoding is compared again before fit. W0–W7 only train; five epochs yield800 presentations/200 updates.
6. Checks public base/tokenizer identity and CPU tensor receipt; measures the exact28 W0/W8 read prompts with the offline tokenizer and checks input/context caps.
7. Persists **exact-child service14/14**, deterministic and not a model arm.

Prepared files: `spec.json`, `import.json`, `fit.json`, `tokenizer.json`, `encoding.json`, `identity.json`, `read_measurements.json`, `service.json`, then sealed `manifest.json`. All eight inputs are independently file-hashed inside the manifest. Original authority and positive tokenizer receipts are revalidated at each stage boundary. Native preparation has **not** been executed by this worker; Main must inspect those actual native CPU results before fit.

## Exact launch templates — Main executes, not this worker

Main supplies real `$SOURCE_ROOT`, `$PYTHON`, input paths, UUID/lease allocation, and fresh output variables. First prepare:

```sh
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 VLLM_NO_USAGE_STATS=1
export PYTHONDONTWRITEBYTECODE=1
CUDA_VISIBLE_DEVICES="" PYTHONPATH="$SOURCE_ROOT" "$PYTHON" -B -m gpu.astra_pcfl_event_only_command prepare \
  --spec "$SPEC" --spec-sha256 "$SPEC_FILE_SHA256" --output "$FRESH_EVENT_ROOT"
```

After successful real CPU preparation, independently hash `$FRESH_EVENT_ROOT/manifest.json`. Use a pinned allocation with the **existing `pcfl.zero_fit_outer.v2/allocation` schema**, pointing `outer_sha256` to the new controller hash below. Python must be the actual matching venv interpreter. Do not reuse another controller's source pin or an old allocation/queue snapshot.

Run each outer command **inside Main's detached launcher**. Fit:

```sh
CUDA_VISIBLE_DEVICES="" PYTHONPATH="$SOURCE_ROOT" "$PYTHON" -B -m gpu.astra_pcfl_event_only_outer \
  --manifest "$FRESH_EVENT_ROOT/manifest.json" --manifest-sha256 "$MANIFEST_FILE_SHA256" \
  --allocation "$FIT_ALLOCATION" --allocation-sha256 "$FIT_ALLOCATION_FILE_SHA256" \
  --outer-sha256 5bc4f24a744a2ee53edbe7623ce0e10831fd8a566fcfbae58e1f84531a89aac4 \
  --outer "$FRESH_FIT_OUTER" --stage fit
```

After the fit and its same-controller release/collection succeed, cold AUTH:

```sh
CUDA_VISIBLE_DEVICES="" PYTHONPATH="$SOURCE_ROOT" "$PYTHON" -B -m gpu.astra_pcfl_event_only_outer \
  --manifest "$FRESH_EVENT_ROOT/manifest.json" --manifest-sha256 "$MANIFEST_FILE_SHA256" \
  --allocation "$AUTH_ALLOCATION" --allocation-sha256 "$AUTH_ALLOCATION_FILE_SHA256" \
  --outer-sha256 5bc4f24a744a2ee53edbe7623ce0e10831fd8a566fcfbae58e1f84531a89aac4 \
  --outer "$FRESH_AUTH_OUTER" --stage readout --arm AUTH_WRITE
```

And a separate cold no-write process:

```sh
CUDA_VISIBLE_DEVICES="" PYTHONPATH="$SOURCE_ROOT" "$PYTHON" -B -m gpu.astra_pcfl_event_only_outer \
  --manifest "$FRESH_EVENT_ROOT/manifest.json" --manifest-sha256 "$MANIFEST_FILE_SHA256" \
  --allocation "$C0_ALLOCATION" --allocation-sha256 "$C0_ALLOCATION_FILE_SHA256" \
  --outer-sha256 5bc4f24a744a2ee53edbe7623ce0e10831fd8a566fcfbae58e1f84531a89aac4 \
  --outer "$FRESH_C0_OUTER" --stage readout --arm NO_WRITE_C0
```

One stage per detached controller; no looping, retries or resuming failed stage directories. The outer constructs fixed `-B -m gpu.astra_pcfl_event_only_command fit|readout` argv, including `--deadline <absolute worker cutoff>` and arm only for readout. The corresponding command subcommands exist for that child, not as a substitute for Main's outer launch.

## Native lifecycle and outputs

- **1800 seconds total /60 seconds reserved cleanup /at least six-hour lease-finish margin**. The4-second detach delay, preflight, cold load, training/inference, collection and post-checks consume the same outer clock. This is a fixed conservative bound, not a measured native fit-duration claim; no open-ended retry if it expires.
- Reuses existing node/queue/CVD/GPU and owned-group helpers unchanged. Worker gets only fixed UUID CVD, pinned source PYTHONPATH, offline flags, fresh stdout/stderr, DEVNULL stdin and its own session. Outer validates actual PID/PGID/SID/UID/boot/start ticks. Unknown identity is never killed; cleanup is only for the spawned verified group. Same detached controller records worker exit/signals/events and once-only post-worker release/resource observations; no foreground finalizer.
- `fit/` calls the unchanged EVENT writer/numerical trainer. It requires all200 updates,800 presentations/forwards, exact prepared encoding/fit hashes, original saved writer completion and complete file inventory; partial failures remain failures. Saved rank8 adapter is hash/size bound in `fit/adapter.json`. No formation completion is consulted, fabricated or repaired.
- `readout_AUTH_WRITE/` requires unchanged completed fit evidence; `readout_NO_WRITE_C0/` mounts no adapter. Existing ReadoutActor enforces one cold native engine per process, identical engine treatment, source-withdrawn public query/wrapper messages and unconstrained sampling. **No LF scaffold/regex actor** is used. LF remains part of exact child target/output bytes and is scored without normalization.
- Each arm makes exactly28 ordered calls: sorted14 queries at W0, then W8. Original call/config/identity/load/close bytes bind PID, NATIVE_OWN_WRITE_READOUT kind, actual LoRA route, raw response/finish, default sampling and cold-ready chronology. Installed EngineCore shutdown is explicitly verified/called by the existing readout session close; close/call accounting must succeed. The fit process uses PyTorch rather than EngineCore and is released through its own process/group exit and outer checks.
- Ordered `scores.json` preserves raw strings, strict/semantic scores and finish reasons; strict_stop/semantic_stop require actual stop, so length remains failure even if text matches. Per-view denominators are14, arm denominator28. Scored bad answers can complete infrastructure successfully; backend/capture/close/timeout/failed-release cannot. Missing/failed arms are never zero-filled.
- Stage `completed.json` binds stage files and explicit original `FORMATION_FAILED`, rc1, `full_contract_released=false`; outer `collection.json` is only that new stage's lifecycle result. It is not original C0/full-bank release or qualification. Failures preserve usage as unavailable/partial rather than asserting zero cost.

## Endpoint and remaining Main responsibilities

The exact predeclared endpoint is carried from `event.ENDPOINT`: service14/14; **W8 AUTH strict_stop≥13/14, C0 strict_stop≤1/14, paired difference≥12/14**. W0 is descriptive. Both arms' independently collected/released results must be joined by the same roster/query IDs. This stage seam deliberately does **not** infer a paired pass from one arm: `paired_endpoint` states `REQUIRES_BOTH_RELEASED_ARMS_NOT_INFERRED_HERE`. Main owns the paired report and final interpretation; no missing arm is treated as zeros and the old17-query threshold is never applied here.

One life/root/fit, eight retrospectively selected format-assisted original EVENTs, trained facts/addresses; W8 is a held wrapper, not unseen facts. No LINK composition, full-bank formation, parenting, retention, address selectivity, generalization, clean-lineage, compute-matched no-write, H1/H2, C11 or general qualification claim follows. Original failed formation/captures and Parfit's importer/writer remain untouched.

Main next: freeze/stage these exact sources, form the closed spec with actual native paths and independent file pins, run the real offline prepare gate, then launch one fresh fit with current allocation through the detached outer when the live A1 release window is clear. All allocation, remote launch, observation and notebook logging remain Main-owned.
