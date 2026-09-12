# Process-v2 parent-free readout — EDITSTOP, 2026-09-12

## Delivered scope and hashes

Only these three new sidecars were authored; no Arendt/Ohm file, repository source, frozen driver, material, or legacy test was modified:

- `/tmp/astra_rulegame_process_readout_20260912.py`
  SHA256 **46e3d0974cab9a3c35e732634a22c29ad25ccd670472dc5b1a57c344cb20af46**
- `/tmp/test_astra_rulegame_process_readout_20260912.py`
  SHA256 **f38b3b92056ee6a1230c99f8d722b4e94d3f4fbfb6fec8a520908fd62d85bf21**
- This handoff.

**22 CPU mock tests PASS in 39.609s.** No native tokenizer/model, GPU query/launch, SSH, network, Git, or actual run outcome inspection. Synthetic fixtures and their temporary artifacts only. Main alone integrates and performs native acceptance/launch. No readout or learning result is asserted.

The new sidecar is a scoped adaptation of the frozen record-readout source, not a change to it. AST regression compares the full `worker`, `worker_spec`, `owning_process`, `verify_worker_bytes`, `close_native`, `work_window`, `supervised_window`, and `absolute_python` functions against that reference and confirms exact code identity. The changed surfaces are process-v2 acceptance/native custody, explicit protocol/claim metadata, descriptive event reductions, and controller receipt handling.

## Stable writer API coordination

For Main / Arendt (`01a097b5-1d8e-7bb3-bb6b-52e0844e371a`), consumed API:

```text
checked_plan(root, expected_hash) -> (root, plan, diagnostic, exporter, trainer)
verify_inputs(plan, diagnostic)
validate_fit(root, arm, plan, diagnostic, trainer)
full_tokens(corpus, tokenizer, trainer)
check_pair(pair, candidate, review, tokens, diagnostic)
exporter.inspect_capture(capture_root, protocol=...)
exporter._review(candidate, review, protocol=...)
```

Required identities are `WRITE_PROTOCOL=rulegame_process_write_v2_20260912`, `PROTOCOL=rulegame_grounded_process_pair_v2`, conditioning `CONTEXT_DISTILLATION_NOT_UNCHANGED_NATIVE_CONTEXT`, origin `UNRESOLVED_LOCAL_HASHES_ONLY`, and the current process writer's explicit false clean-lineage/G3/P1/G5/H1/H2/certification claim flags. The driver hash is supplied explicitly, checked **before import**, then pinned in the new plan. It is not inferred from a familiar filename. Record/P0/v1 drivers or material are rejected. An incomplete/failed pair cannot be prepared for readout.

Compatibility was tested with the existing process writer at SHA **a73dd6074fdd099cea19f46cfed94bf31f22b2ce02b8741ac2f224413ee514d9**, and its read-only fixture suite at **a20f900690d552d8aac4ad97c60ce373cfc38a092852b859de7964725a7e26a0**. These hashes were unchanged across this task; this is not an assertion that the other owner has issued EDITSTOP. Main must use Arendt's accepted final driver and its exact supplied hash; a changed API needs explicit reconciliation, not a fallback to record-write receipts.

Reference readout remains **120e260a76395586736d47e4f8a55c425b090f9f8654208dcfbef7eac5cccbde**. Current local process exporter is **a060f11165e68baa9baaf50433e157e2b3d348a3577e4fbc8ba540d269c24168**. Source-root is inherited from the process-write plan, not hardcoded to an earlier snapshot missing the exporter.

## Exact Main CLI

Preparation is CPU-native validation of an **already completed** pair. It does inspect fit completion/loss/token receipts but never selects a fit/target by its loss, reads new-rule outcomes, or generates material. `READOUT_ROOT` must be a fresh sibling of the supplied process-write root; no overwrite or resume.

```bash
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export ASTRA_SOURCE_ROOT="${PROCESS_SOURCE:?exact source-root from process-write plan}"
export PYTHONPATH="$ASTRA_SOURCE_ROOT"

"${NATIVE_PYTHON:?exact process-write native venv spelling}" -B \
  /tmp/astra_rulegame_process_readout_20260912.py prepare \
  --write-root "${PROCESS_WRITE_ROOT:?completed process-v2 root}" \
  --write-plan-sha256 "${PROCESS_WRITE_PLAN_SHA256:?accepted process plan hash}" \
  --write-driver /tmp/astra_rulegame_process_write_20260912.py \
  --write-driver-sha256 "${PROCESS_WRITE_DRIVER_SHA256:?Main accepted writer hash}" \
  --out "${READOUT_ROOT:?fresh sibling readout root}" \
  --deadline "${DEADLINE_UTC:?set readout deadline}" \
  --lease-end "${LEASE_END_UTC:?real supplied lease expiry}"

"${NATIVE_PYTHON:?exact process-write native venv spelling}" -B \
  /tmp/astra_rulegame_process_readout_20260912.py evaluate \
  --root "$READOUT_ROOT" \
  --plan-sha256 "${READOUT_PLAN_SHA256:?exact prepare return}" \
  --allow-gpu
```

Keep the absolute venv spelling; **do not resolve its interpreter symlink** to system Python. Source, base, device and adapters are inherited; there is no device/model/adapter override. The internal `_worker --spec --spec-sha256 --allow-gpu` is for the owning controller only. Prepare returns `PROCESS_READOUT_FROZEN_NATIVE_PAIR_VERIFIED`; evaluate returns the inherited `COMPLETE_EXPLORATORY_READOUT` only after all cells and final rechecks, with additional process protocol/metric metadata.

The new readout has no launcher or full-release collector. Main retains continuous GPU/lease reservation, launch provenance, all-cells-finish outcome discipline and terminal/full-release collection. Do **not** apply the old hardcoded record-readout collector unchanged: its driver/root/source/receipt pins and expected cell-receipt contents do not describe this sidecar.

## Material, fit, and native custody

Read-only acceptance verifies the existing process-write plan, original formation identity/seal/completion, exact Main review and fixed candidate, exporter source pins, model inventory and explicit fresh-base recipe. It consumes only the already published material layout:

```text
material/corpora/{P,A}.json
material/audit/{candidate,main_review,token_receipts}.json
material/provenance/{P,A}.tokens.json
material/export_manifest.json and material/manifest.json
fits/{P,A}/manifest.json and receipt.json
fits/{P,A}/adapter/{train_manifest,train_meta,adapter_config}.json
fits/{P,A}/adapter/adapter_model.safetensors and DONE
run/{P,A}/supervision.json and run/result.json
```

`inspect_capture` must reproduce the unchanged candidate from the original source calls/events. No favorable reselection, target rewriting, export, `build_process_pair`, synthetic context, training function or legacy material path is called. An in-memory pair is assembled **from existing sealed files** solely for `check_pair` verification. Native CPU validation checks the original call token audit, exact rendered parent-removed user context, complete raw own wake bytes, full input/label/EOS receipt and V3 collation/exposure receipts. A coherently altered corpus/receipt/Main-review hash with inserted parent context still fails actual template rendering against the fixed source-derived transformed context.

Every item must be the explicit process-v2 view with exactly masked `parent_removed_wake_context` and trainable `complete_own_raw_wake` spans. The inherited check validates that conditioning changed and original native output token IDs were **not** reused as transformed-training target IDs. This is context distillation of existing raw wake responses, **not an unchanged actual-RECORD objective**. Wrong predictions already in those wakes remain untouched. No teacher/parent/restatement/audit/corpus bytes enter the readout worker spec or prompts; the CPU controller alone reads them for custody. This is code/prompt isolation, not an OS filesystem sandbox or automatic semantic-nonleakage proof.

Both fits must be sealed and match `validate_fit`: fresh base, no warm start/init adapter, frozen base/one adapter trainability, saved LoRA tensor/config identity, inherited 12 updates/epochs and exact token/mask/drop/split/packing metadata, finite final/per-epoch losses, and exact completed-pair/supervision receipts. Readout lineage records both losses, all 12 per-epoch losses, token counts, train-tokens-seen and exposure summaries; they are descriptive custody, not selection thresholds or a learning claim. Natural P/A target/input length differences remain visible, without token matching, dose adjustment or new target padding.

The completed lineage is pinned during prepare, checked again at evaluate with native tokens, and rechecked before/after cells. Each fresh OFF/P_ON/A_ON process loads only the frozen base and its exact intended saved adapter (OFF has none), verifies native generation identity and source/model/adapter hashes, runs unchanged `diagnostic.run_evaluation`, verifies native input/output token rendering, closes the backend and seals the capture. Controller replay and an independent native tokenizer audit validate that capture before reducing metrics. Tampered prompts, native IDs, masks, protocol, parent context, identities or earlier-cell files fail closed; no subsequent favorable replacement is attempted.

## Unchanged assay and explicit descriptive metrics

- Exactly existing development rules **2–5**, four tasks × six quiz items = **24 fixed items per cell**. Invalid/absent first quizzes score zero. Mean first-quiz accuracy and P−OFF, A−OFF, P−A contrasts are unchanged. Rules 0/1 formation and confirmation data remain excluded.
- Same seed `20260912`, temperature `.7`, five wake responses/task, up to three TRYs/task, max model length16384, wake cap400/record cap100, per-cell caps20 wakes+12 records, hence **96 maximum model calls /27600 maximum generated-token budget** across three cells. Early endings do not trigger replacement tasks.
- No parent/restate calls or initial parent prefix. Each task resets its history and retains only that task's own wake responses/public outcomes. Diagnostic RECORD calls remain enabled for measurement, with the exact interaction_v3 definition; their text is not fed into subsequent wake prompts, and there is **no online update or sleep** in readout.
- Separate per-task/per-cell counts: PREDICT-emitting wake responses and lines; executed TRY probes/distinct triples/repeated triples; valid unambiguous predicted probes, correct predictions and absent/ambiguous predictions; invalid actions; actual/faithful/invalid records; valid versus invalid/absent quizzes. Prediction accuracy uses actual valid predicted-probe denominator (null when zero); executed-probe fraction is null when no probes. Also report fixed12 prediction opportunities. Record faithfulness reports actual-request fraction (null when zero) and allotted12 fraction, so failures/missing opportunities remain visible.

**Important inherited boundary:** CHILD_BOOT already explicitly asks for `PREDICT` before every TRY. These are emission/adherence measures, not an unprompted-spontaneity test. Counting a PREDICT line does not establish a valid executed prediction; RECORD faithfulness is separate. Distinct probe triples measure diversity, not information gain or causal cognition. This is a fixed post-write competence/transfer assay, not adult autonomous adaptation, clean lineage, G3/P1/G5/H1/H2 evidence or a new scientific claim. Origin remains `UNRESOLVED_LOCAL_HASHES_ONLY`; no origin-promotion option exists.

## Bounds, tests, and outstanding risks

Inherited controller **1800s inclusive**, per-worker execution cap600s, nested cleanup reserve140s, native load180s/call120s and supplied lease expiry−6h are retained. Preparation must leave the full1800s after native validation. The first controller custody check is now inside its timed work window too. Owning worker session/parent-death watcher and supervisor cleanup are byte-identical to the frozen reference. The sidecar does not kill foreign processes. Partial captures remain intact; failure has `aggregate=null`, completed-cell names, no final result and no retry/overwrite. Nested clocks must not be added. Full release and actual lease verification remain Main responsibilities.

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
CUDA_VISIBLE_DEVICES='' ASTRA_SOURCE_ROOT=/data/home/rohing/dream-state \
python3 -B -m unittest discover -s /tmp \
  -p test_astra_rulegame_process_readout_20260912.py -v
```

22 tests cover a completed process pair/native mock masks/losses/exposure; full three-cell fresh readout and current-task/no-parent prompts; incomplete/failed writes; record/P0/v1 rejection; coherent parent-context forgery; warm-start/adapter bytes; nonfinite loss/token/update metadata; masks/EOS; fixed24 invalid-zero quiz denominator; PREDICT versus execution versus record-faithfulness denominators; opt-in and failed middle cell/no retry; extra worker context/wrong OFF adapter; resealed parent prompt/native token tampering; cleanup failure; rehashed protocol tamper; interpreter spelling, lease/cleanup timer; and AST preservation of the generation/ownership functions. Fixtures import the unchanged process-write tests and frozen record-readout tests; on native Main tests set `ASTRA_SOURCE_ROOT` to the actual immutable source tree containing the process exporter.

Outstanding: Main must reconcile Arendt's final API/hash, run native tests/prepare on the actual completed pair and native tokenizer, and perform launch/full-release custody. Real rendering/offset/collation, tensor inventory and finite fit receipts have not been tested against native artifacts here. Repeated source/formation/model/adapter verification plus native token audits consume CPU time inside the unchanged controller cap; no throughput promise or relaxed deadline is implied. No launch, scoring outcome, independent science review or claim promotion was performed. **EDITSTOP.**
