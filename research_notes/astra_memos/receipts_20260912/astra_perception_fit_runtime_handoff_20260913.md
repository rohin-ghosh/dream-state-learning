# EDITSTOP — perception fit/runtime handoff, 2026-09-13 UTC

Implemented only the three assigned new sidecars. Accepted corpus/tests,
`train_adapter_v3`, Boyle's runner, notebooks and all other project files were
left unchanged. No real model/tokenizer, GPU, NVML, network or Git operation
was run. Tests use CPU tokenizers, fake model/backend objects, mock NVML output
and temporary fixture artifacts; they provide no model-performance evidence.

## Scope and fixed work

- Two independent cold fits: training anchor absent / present, same 12 train
  sources and targets. Existing `train_adapter_v3.run_training` is unmodified.
- Rank 8, alpha 16, dropout .05, LR 1e-4, four epochs, batch 4, seed 0,
  no packing, max sequence 1024, grad accumulation 1, all seven default LoRA
  projections/all layers. Twelve optimizer updates / 48 presentations per fit.
- Six fresh-process readouts: `OFF`, `fitAbsent`, `fitPresent`, each crossed
  with readout anchor `absent` / `present`. Identical fixed DEV12: **72 calls**,
  max 192 output tokens/call, maximum 13,824 generated tokens.
- All six engines use `enable_lora=True`, `max_lora_rank=32`; OFF explicitly
  passes `lora_request=None`. The earlier disabled-LoRA OFF is not substituted.
  Greedy temperature 0 / seed 0, prefix caching disabled, bf16, context 16384.
- Eight separate worker processes/groups: two fits, six readouts. No warm
  start, merge, inter-cell transcript, online update, replacement sample,
  dev-driven selection, or checkpoint tuning. All captures close before any
  generated-response score is computed.
- Origin/claim is explicitly author-sourced DEVELOPMENT-only exploratory
  record fidelity, not sleep, teacher-generated context distillation, learned
  general perception, L2 qualification or demonstrated withdrawal persistence.

## Native full-assistant encoding — Main must accept before launch

`prepare` uses the real local tokenizer only when Main invokes it. Both
`apply_chat_template(..., tokenize=True)` token vectors and
`Mapping['input_ids']`/BatchEncoding are accepted; nested/bool/empty vectors
are rejected. The full assistant turn is rendered separately from the prompt.
Its bytes and token IDs must match native encoding, the generation prefix must
be an exact prefix, and the supplied raw target must be unchanged.

The v3 item has four existing span categories: masked rendered prompt,
supervised raw record, supervised native EOS, masked trailing template-only
whitespace if present. `chat_template=False` prevents a second user-only
wrapper; **`add_eos=False` prevents adding another EOS**, because the actual
native end token is already an explicit supervised span. These flags implement
the native assistant boundary, not a new model response grammar. Full native
sequence IDs are retained, including the masked final newline.

Preparation checks the actual unmodified v3 `encode_item_segments` and
`collate` outputs: one segment per row, exactly target+one EOS supervised,
prefix/padding/template-tail masked, no drop, split or truncation. It audits
the real batch-4/epoch ordering and identical supervised IDs across anchor
arms. A full-template/span boundary mismatch is a hard failure, not silently
normalized. The fit worker re-encodes and verifies actual IDs/masks again.

“Absent” refers to the experimental anchor, not necessarily absence of the
tokenizer's generic system message. Actual system text/segment and prompt IDs
are preserved in the preparation and capture evidence.

## Main interfaces

The driver is `/tmp/astra_perception_fit_run_20260913.py`. It exposes:

1. `prepare(...)` / CLI `prepare`: requires `--root`, `--source`, `--model`,
   `--probe-driver`, `--probe-sha256`, `--binding-path`, `--binding-sha256`,
   `--corpus-sha256`, `--gpu-uuid`, `--gpu-index`, and `--lease-end` (Unix time).
   Returns `PREPARED_NOT_LAUNCHED` and `plan_sha256`.
2. `controller(root, plan_sha256, allow_gpu=False)` / CLI `controller` with
   `--root --plan-sha256 --allow-gpu`: supervises the fixed eight workers and
   returns `ALL_CAPTURES_CLOSED_UNSCORED` plus `completion_sha256` only after
   all captures and owned-resource release checks pass. No scores here.
3. `worker` is controller-owned: `--root --plan-sha256 --stage --allow-gpu`;
   requires its own process group and the bound GPU UUID in
   `CUDA_VISIBLE_DEVICES`. Main should not manually create partial stage trees.
4. `collect(root, plan_sha256, completion_sha256, out)` / CLI `collect` with
   those four flags: CPU-only bounded validation followed by all 72 record
   scores, writing a fresh external output directory. No GPU call or fit.

Preparation binds source files, exact anchor, tokenizer chat template, native
environment including PEFT, model-file hashes and the full recipe. The Python
executable retains its venv symlink spelling for child processes rather than
resolving away the virtual environment. The public-model-only binding is
reused for base custody only; it is not reinterpreted as an old fit approval.

## Boyle dependency — final hash supplied by Main

Main supplied and local read-only hashing confirmed the final Boyle SHA-256:
`59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c`.
Pass it using `--probe-sha256`; the runtime still accepts the explicit caller
pin rather than hard-coding a development path/hash. The exact `ANCHOR` is
loaded from that pinned final driver; no
alternate or approximate anchor parameter is accepted. Preparation compares
its DEV rows to Boyle's `fixed_rows` exactly.

Reused narrow helpers are model-only binding/hashing, local tokenizer,
rendering, raw-response validation, GPU-vacancy and owned-group cleanup.
Boyle's OFF-only `prepare`, `capture`, controller and identity are not reused
as if they supported adapters. No old material builder, corpus or native
output is imported. His final module must expose `GPU_QUERY_SECONDS == 30`.

## NVML and timing bounds

- NVML now receives **30 seconds**, through Boyle's final helper, not 3s.
  Regression fixtures verify exact timeout, selected physical index/UUID,
  nonempty process rejection, and timeout propagation. No release test is
  weakened or converted into “assumed free.”
- Outer cap remains **2700 seconds**, with separate **180-second collection**.
  Each fit has a maximum 600s worker window; each readout **240s**. These are
  ceilings, not measured duration forecasts.
- Each of eight stages budgets up to 30s pre-launch vacancy query plus 40s
  post-worker reserve: 10s for the existing owned-group cleanup and 30s for
  the release query. Adding every per-stage ceiling gives
  `2*600 + 6*240 + 8*(30+40) = 3200s`, which **exceeds the outer cap**;
  ceilings are not summed expected runtimes or an assurance of completion.
  Worker waits clamp to actual remaining time, preserving the release reserve;
  initial native verification also consumes the same outer budget. The global
  cap may abort and preserve partial evidence. No threshold/token/data changed.
  Main requested this increase after reporting approximately 123s for an
  independent OFF condition through shutdown; no live output was inspected here.
- The controller alarm is set at 2660s, reserving the final 40s for cleanup
  and release on failure. A stage is not started without time for vacancy and
  release checks. Lease checks reserve outer + collection + cleanup margin.
- Every worker is launched `start_new_session=True`. Cleanup targets only its
  returned process/group; busy or mismatched GPUs are rejected, not cleared.
  A failed release leaves failure evidence and no successful completion.

## Evidence, failures and scoring

Run root retains `prepare_started.json`, immutable prepared train encodings,
DEV rows, calls, `plan.json`, controller receipts and per-stage stdout/stderr,
launch/start/release receipts. Fits retain actual adapters, v3 manifests and
`fit.json`; readouts retain raw requests/responses, honest adapter/engine
identity and `closed.json`. `capture_complete.json` binds all stage artifacts.

Common hard failures: wrong final Boyle/source/model/environment hash;
native full-assistant/EOS/mask mismatch; truncation; nonfinite/skipped or wrong
update count; changed adapter; occupied/wrong GPU; NVML/worker/outer timeout;
surviving process group; incomplete or tampered raw capture. Failure artifacts
and partial adapters/responses remain; no automatic retry or root reuse.
DONE alone does not qualify a fit: required finite-loss, zero-drop, 12-update,
48-presentation/token-exposure and adapter checks must pass before readout.

Malformed model records remain ordinary raw outcomes, scored false only at
collection, not regenerated. Missing/infrastructure-invalid captures prevent
all scoring. Collection first verifies all eight fresh-process receipts and
all six 12-call inventories; only then calls the existing corpus scorer.
`scores.json` reports paired row/source IDs, correctness and length finishes,
with `automatic_pass=False`. Raw evidence remains in the run root; this
sidecar does not upload, archive, delete, or replace it.

## CPU validation and final pins

Command run:
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s /tmp -p test_astra_perception_fit_run_20260913.py -v`

Tests accept `PERCEPTION_DRIVER` and `PERCEPTION_PROBE_DRIVER` for unique frozen
script paths; defaults remain the original `/tmp` paths. Existing
`PERCEPTION_PUBLIC_SOURCE` selects the source checkout. An override regression
imports unique temporary frozen copies without replacing either original driver.

**30 tests PASS**, final run 4.547s. Covers BatchEncoding/full-assistant masks,
exactly one supervised EOS, masked padding/trailer, no truncation/dev loss,
recipe/order/exposure, two cold fit calls, six adapter-routed matched engines,
all-captures-before-scores, raw-error retention, artifact/adapter tampering,
NVML 30s and strict release semantics, timeout/owned cleanup, venv preservation,
explicit launch flags, frozen-path test overrides, the 240s readout/global-cap
clamp, and no native-library imports at module import.

- Runtime SHA-256: `f62da57d1a66cd287b72ac8ad8b8724601062813653a63d3dcd6cd8a3b69cd51`
- Tests SHA-256: `4d9a1128518944337a63800bae82025763993378c69c94d3608e8fc6bd5dc96e`
- This handoff's hash is reported in the final EDITSTOP response.

**Remaining with Main:** native CPU acceptance of the actual full assistant
boundary/masks and bindings using the final Boyle pin, then decide whether to
launch under the unchanged global cap. CPU fixture passes
are not native acceptance or scientific evidence. No launch was performed.
