# Scoped OLD AUTH writer — final handoff / EDITSTOP

Freeze: 2026-09-13T13:59:56Z (source/test verification). This replaces stale
proposal/progress notes. Main explicitly approved the shared extraction; it is
implemented, not pending. Full tiny-Qwen/PEFT numerical acceptance remains
Main-owned and pending. EDITSTOP is not native/scientific launch approval.

## Scope and implementation

- One independent disposable OLD AUTH acquisition diagnostic: actual native
  child formation, admitted own rows, one clean-C0 LOW200 rank8 fit. Cold
  source-withdrawn READs and fresh no-write C0 are Main/readout responsibilities.
- Freeze 17 first query blocks plus three distinct deterministic authentic
  EVENT replays. Existing replay selection uses domain
  `[plan_sha256, "S1", "S1_four_arm", "EVENT", "replay"]`; this is a scoped
  single-life domain, not full-campaign qualification.
- Pre-output deterministic disjoint-support partition: five groups of four,
  at most one LINK per group, W0-W7, five epochs, exactly 200 updates.
- Existing LOW 3e-5, rank8/alpha16/dropout .05, pooled response-token-plus-EOS
  objective, fresh base/optimizer and existing lineage/masking/save loop.
  No ideal/oracle targets, altered thresholds, base/science/config changes,
  full CAL/P1/C11, parenting, H1/H2 or learning claims.
- Only `_encode_corpus` and `_train_encoded` were extracted from the shared
  writer. Public full `encode_fit`/`train_fit` retain their existing validation
  and execution gates. No duplicate numerical loop or production-gate patch.

## Concrete API for Main / Parfit

```python
from organism_v6 import pcfl_own_write_train as own

schedule = own.build_schedule(plan, plan_sha256, batch_seed=integer)
fit = own.build_fit(config, config_sha256, report, report_sha256,
                    schedule, schedule_sha256, binding, native_receipts)
encoded = own.encode_fit(fit, tokenizer)
receipt = own.train_fit(fit, tokenizer, base_factory, fresh_output_dir)
```

`plan = config["planner"]`. Formation config/report are independently sealed;
the complete report is required, not only writer_payload. The writer invokes
the real formation `replay_validate` and requires all 20 native formation
captures (eight action/EVENT pairs plus four LINKs). Admission, exact UTF-8
whole-response spans, sidecar hashes, stop completion, queries and provenance
are replayed. The actual supplied tokenizer must reproduce native prompt
renders and decoded outputs before shared encoding.

`binding` has exactly these input fields:
`authority_sha256`, `init_seed`, `dropout_seed`, `base_state_sha256`,
`environment`, `tokenizer_receipt`, `sources`. The fit adds fixed learning_rate.
`native_receipts` has exactly `config`, `identity`, `load`, `close`.
`base_factory()` returns `(fresh_bf16_base_model, exact_binding_environment)`.
The output directory must be fresh. Scoped validation writes
`own_write_scope_report.json`, not a full execution-contract approval.

Cold first-call ordering is **generation_started >= load.ready_at**. An
operation may begin before model load completes. A dedicated regression
accepts that valid case and rejects generation preceding readiness.

Successful native close kind/error/budget/call flags remain required, but
`close.shutdown.shutdown_method_available=True` is NOT a GPU-release gate.
Regression accepts False without claiming native custody or GPU vacancy.
Actual engine/process/GPU release is Main's separate external receipt.

## Accepted CPU base-state receipt (Parfit coordination)

Verified against `gpu/astra_pcfl_own_write_command.py` preparation validation.
Exactly eight top-level fields; no internal `sha256` field:

```json
{
  "schema": "pcfl.own_write.cpu_base_state.v1",
  "status": "COMPLETE",
  "base_state_sha256": "<existing writer._state_hash(model.state_dict())>",
  "model_binding_sha256": "<spec.model_binding.sha256>",
  "model_files": {"<each original model filename>": "<file SHA-256>"},
  "dtype": "bfloat16",
  "device": "cpu",
  "environment": {"native": "<exact spec native object>", "peft_version": "<exact spec value>"}
}
```

Use the unchanged `organism_v6.pcfl_vertical_train._state_hash` on actual clean
bf16 CPU C0 state, before formation, without GPU or numerical updates. The
`model_files` object must equal the native identity's exact 14-file map.
`environment` equals **spec.environment**, not writer binding.environment;
its closed keys are `native` and `peft_version`. Placeholder strings above are
documentation only: preserve the actual nested objects and values.
Pin the complete receipt's file bytes externally via
`spec["base_state_receipt"] = {"path": ..., "sha256": ...}`.
Parfit validates this receipt and copies the scalar into the writer binding;
training independently hashes its own fresh base state again. Main owns CPU
loading and receipt creation; no additional receipt framework is needed.

## Source pins and frozen files

Formation/readout owners must freeze their source pins AFTER this extraction
and Main's separate actor-close edits. Rebuild `binding.sources` with
`own.source_snapshot()` and reseal encompassing records. Nine source roles:
own_writer, writer, shared, core, preparer, planner, formation, native_actor,
tokenizer_render. Do not reuse historical shared-writer pins.

```text
b5af7c634b960288ffe329bc603d09c251125a63f3194409c7b6bb74c9ca7af9  organism_v6/pcfl_own_write_train.py
5a09d929f9aa46d2527ecc0154110d1a28b503e65bd69818c91afb8f62f2c841  tests/test_pcfl_own_write_train.py
9a392dc17eab4db77416b81642def0842c5b353c5ff9aca5fcdf94a04474b078  organism_v6/pcfl_vertical_train.py
194b96dbc76d0b2faed6ddeb4527038a66cf82cb821b01a9d8cbe5ec7b0828b8  tests/test_pcfl_vertical_train.py
```

## Tests and acceptance boundary

Latest local rerun ended 2026-09-13T13:59:56Z:
- Own suite: 14 tests, 12 PASS / 2 opt-in numerical skips, 4.796s.
- Shared suite: 38 tests, 36 PASS / 2 numerical skips, 2.317s.
- Full unresolved execution gate rejects before either extracted helper.
- Exact byte/span/mask/provenance, cold-call timing, close-flag semantics,
  deterministic schedule, source identity and failure tests use explicitly
  synthetic fixtures; no native output was inspected.
- Previously executed real CPU Torch pooled-objective/backward tests passed:
  own 5.844s, shared 1.875s, cached Torch 2.8.0+cpu. No installs/downloads.
- Earlier formation integration 27 PASS and readout 33 PASS; those other-owner
  files were only tested, never edited.
- Static AST extraction audit passed against original shared-writer SHA
  b8d033566574967e6f579c6b1451e65c1bb15a99fce554ba71ced0c270ad39c3:
  encoder/numerical/update/save/failure bodies unchanged under approved
  parameter/report-name substitutions. Full gates, objective, lineage,
  validation and state hashing unchanged. Whitespace checks pass.

Local PEFT/Transformers/NumPy/safetensors unavailable; actual tiny-Qwen/PEFT
LOW200/save/reload parity is NOT locally claimed. Main runs on node2 CPU:

```sh
env CUDA_VISIBLE_DEVICES= ASTRA_PCFL_TINY_CPU=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  timeout --signal=TERM --kill-after=5s 115s \
  /PATH/TO/NODE2/VENV/bin/python -B tests/test_pcfl_own_write_train.py -v
```

The opt-in test constructs random tiny bf16 CPU Qwen, compares scoped and
direct shared-loop 200-update runs, LoRA/optimizer hashes and update receipts,
unchanged base tensors, saved/reloaded adapter logits, and warm-base rejection.
It is a numerical test, not a pretrained/scientific fit; opted-in dependency
failures do not silently count as acceptance. Main retains the real test log.

No commits, remote/network/GPU/model runs, active/native result reads, or
other-owner edits by this worker. Only four source/test files above and this
handoff are owned. All edits stop here; Main owns frozen-tree transfer and
remaining CPU acceptance. Handoff file hash is returned separately.
