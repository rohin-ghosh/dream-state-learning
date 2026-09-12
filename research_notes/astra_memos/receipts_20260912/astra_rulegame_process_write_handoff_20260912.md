# Process-v2 write bridge — stable API / EDIT-STOP

2026-09-12, 22:31 UTC. CPU-side implementation and mocked verification only.
Main is sole native/Git/GPU operator. No real native tokenizer/model was loaded,
no actual capsule was prepared, and no fit/readout/collector was launched here.

## Owned files and exact hashes

- `/tmp/astra_rulegame_process_write_20260912.py`
  SHA256 `a73dd6074fdd099cea19f46cfed94bf31f22b2ce02b8741ac2f224413ee514d9`
- `/tmp/test_astra_rulegame_process_write_20260912.py`
  SHA256 `a20f900690d552d8aac4ad97c60ce373cfc38a092852b859de7964725a7e26a0`
- `/tmp/astra_rulegame_process_write_handoff_20260912.md` (this handoff).

Frozen starting driver, unchanged and required as a hashed provenance dependency:
`/tmp/astra_rulegame_record_write_v2_20260912.py`, SHA256
`183b48be6193da953f699d718575f9227fd946d9f8111d2d1647ae5dd431ec7c`.
The new sidecar is a standalone CLI/source fork, not an import or mutation of
that driver. Keep the frozen file at that exact path on the execution node.

Read-only local process exporter SHA256:
`a060f11165e68baa9baaf50433e157e2b3d348a3577e4fbc8ba540d269c24168`.
Main reports accepted/committed source snapshot
`4c3064c1c3eef068951e9c3b2ca46630754564e7`, deployed on node3 at
`~/astra_sources/4c3064c1c3eef068951e9c3b2ca46630754564e7`, archive SHA256
`030b10ebbb6c5438dc8f6c5811a15c92e1b126c59b808116ff142aa2726f0099`,
and Main45CPU/native45PASS. That deployment/native result is Main-reported;
this sidecar did not use Git, SSH, network, or independently inspect node3.
Ohm's exporter/tests/handoff were never edited. `send_input` was not exposed in
this tool session, so no direct message to Ohm was sent; Main now reports Ohm
EDITSTOP closed.

## Stable CLI

Use the actual node's known native interpreter. The earlier node3 launcher used
`/localhome/local-rohing/v2/venv/bin/python`; Main must confirm that remains the
intended interpreter. The bridge records and verifies
`os.path.abspath(sys.executable)`, **never resolves the interpreter symlink**.
No fallback to another Python, model, source, candidate, or target is permitted.

```bash
NATIVE_PYTHON=/localhome/local-rohing/v2/venv/bin/python
SOURCE_ROOT="$HOME/astra_sources/4c3064c1c3eef068951e9c3b2ca46630754564e7"

"$NATIVE_PYTHON" -B /tmp/astra_rulegame_process_write_20260912.py prepare \
  --formation-root "$FORMATION_ROOT" \
  --fixed-candidate "$PROCESS_V2_CANDIDATE_JSON" \
  --main-review "$PROCESS_V2_MAIN_REVIEW_JSON" \
  --source-root "$SOURCE_ROOT" \
  --out "$FRESH_PAIRED_ROOT" --device "$DEVICE" \
  --deadline "$AWARE_DEADLINE" --lease-end "$AWARE_ACTUAL_LEASE_END"

"$NATIVE_PYTHON" -B /tmp/astra_rulegame_process_write_20260912.py write \
  --root "$FRESH_PAIRED_ROOT" --plan-sha256 "$RETURNED_PLAN_SHA256" --allow-gpu
```

The write command belongs **inside Main's continuously reserved launcher**, not
an unattended direct shell invocation. The sidecar does not acquire or certify
that outer reservation. Preserve it across both fits, CPU checks, and cleanup.
`prepare` requires a new root beside the formation root, existing parent, no
symlinks/overlap, and timezone-aware deadlines. Deadline must leave strictly
more than 1200 seconds at preparation and be no later than actual lease end
minus six hours. It returns `status`, `root`, `plan_sha256`, `readout`.

Private supervisor-only CLI (not for manual launch):

```text
_worker --root ROOT --arm P|A --plan-sha256 SHA --launch-token TOKEN --allow-gpu
```

It requires the actual original supervisor's PID/PGID/device/argv receipt,
matching live controller parent PID, a fresh owned process group, the exact
interpreter and environment device, and the launch's cleanup-bounded window.
The token alone cannot authorize an unsupervised worker.

## Stable Python API and Main's native review

```python
prepare(formation_root, main_review, fixed_candidate, source_root,
        out, device, deadline, lease_end)
checked_plan(root, expected_hash)
write_pair(root, plan_sha256, allow_gpu=False)
worker(root, arm, plan_sha256, launch_token, allow_gpu=False)
native_review_template(pair)
full_tokens(corpus, tokenizer, trainer)
```

The material protocol is `rulegame_grounded_process_pair_v2`; the write-plan
protocol is `rulegame_process_write_v2_20260912`. All inspect/build/export calls
explicitly pass the V2 protocol matching `process.PROTOCOL_V2`; no default-v1
path, record selector, P0 material, or optional candidate fallback is accepted.
The bridge also uses the accepted exporter's `_review` and no-replace `_publish`
helpers; the complete exporter dependency hash map is pinned.

Main's exact workflow, before bridge `prepare`:

1. In the final native source/capture location, call
   `process.inspect_capture(capture_root, protocol=process.PROTOCOL_V2)`.
   `capture_root` is the formation root's `formation/data`, not the whole run.
   Save that exact candidate; its hash binds absolute paths and source bytes.
2. Call `process.review_template(candidate, protocol=process.PROTOCOL_V2)`.
   Main manually assesses all four ordered source-bound contexts/whole targets,
   supplies accepted decisions/nonempty notes, and acknowledges context
   distillation. Do not automate the decisions or copy a relocated candidate.
3. With the real native tokenizer, call
   `process.build_process_pair(capture_root, review, tokenizer,
   fixed_candidate=candidate, max_len=4096, protocol=process.PROTOCOL_V2)`.
   This is a CPU/tokenizer audit, not training or generation.
4. Add `review["native_review"] = bridge.native_review_template(pair)`.
   This helper does **not** accept anything: all four rows start pending.
   Main manually reviews the exact rendered transformed contexts and complete
   raw targets in that native pair and changes each native-review row to
   `decision="accept"` with nonempty `notes`. Save the full review JSON.
5. Run bridge prepare with those two JSON files. Do not edit them afterward.

The extra `native_review` envelope binds actor Main, candidate SHA, exact-native
scope, ordered slot/source-call IDs, SHA256 of UTF-8 rendered context/raw target,
and SHA256 of serialized transformed input IDs and original native prompt/output
IDs. ID-array serialization is exactly bridge `encoded`: sorted-key JSON,
`ensure_ascii=False`, `allow_nan=False`, default JSON separators, trailing LF.
Use the helper rather than another serializer. The process source review binds
all unrendered contexts/targets/teacher-removal evidence; the native envelope
additionally binds the actual rendered/tokenized view. Neither authenticates a
human identity nor provides semantic certification.

Prepare does read-only full preflight before output creation, then calls the
explicit exporter to publish the same bound pair and rechecks export against
preflight. This deliberate second validation is not a retry or reselection.
An export/publication failure leaves an unusable root/pending evidence, never a
partial runnable plan. Existing roots cannot be retried or silently replaced.

## Material, fits, and exposure evidence

V1's original shortage is preserved. V2 is the after-inventory exploratory
amendment `96a71289`, not a rewrite of V1 acceptance. It accepts the existing
interaction_v3 TRY aliases in exactly the same four fixed source positions.
No wrong prediction is corrected, no later slot substituted, and no action
canonicalized. Teacher restatement is neither a target nor appended context.

Only `material/corpora/P.json` and `material/corpora/A.json` are trainer inputs.
Each has two V2 rows with precisely masked `parent_removed_wake_context` then
loss-bearing `complete_own_raw_wake`, plus one EOS. No directory corpus glob,
extra template, packing, truncation, split, drop, warmstart, or teacher metadata.
Original V3's fixed `overflow="split"` config is retained for compatibility,
but preflight requires <=4096 IDs and exactly one unsplit, zero-drop segment;
fit-manifest checks reject any actual splitting/truncation.

Each fresh base independently receives rank8/alpha16/dropout0.05, seed2,
LR1e-4, AdamW, batch2, grad_accum1, 12 epochs/12 updates, all seven projections
in every layer, bf16 CUDA, `init_adapter=None`. Base trainability, complete
default LoRA coverage/shapes, saved safetensor intervals/config, finite losses,
exact optimizer/microbatch/epoch counts and model/corpus/token hashes use the
original fit checks. No adapter from the first fit enters the second fit.

Evidence layout:

```text
plan.json, plan.sha256.json
material/manifest.json, material/export_manifest.json
material/corpora/{P,A}.json
material/audit/{candidate,main_review,token_receipts}.json
material/provenance/{P,A}.tokens.json, material/provenance/pair.json
run/controller.json, run/{P,A}.launch.json
run/{P,A}/{process,supervision}.json, run/{P,A}/stdout.log
run/result.json OR run/failure.json
fits/{P,A}/full_tokens.json, fits/{P,A}/forwards/0001.json ... 0012.json
fits/{P,A}/{pre_update_trainability,post_update_trainability,receipt,manifest}.json
fits/{P,A}/adapter/...
```

The candidate/export audit contains teacher-visible original source bytes and
native receipts, **audit-only**, never enumerated or passed as corpus. Original
native prompt/output IDs and transformed training IDs remain explicitly
separate. Frozen driver, source dependencies, formation plan/completion/capture,
base file inventory, fixed candidate, Main review, export, and material are
hashed and rechecked. Plan/material are immutable by seals; runtime outputs use
exclusive creation and are subsequently sealed, not filesystem read-only flags.

Native token receipts report each row's raw target/full target (including EOS),
context/input/padded width/padding, 12 presentations, and exposure totals; they
also enumerate all 12 two-row batches. Natural target/input token imbalance is
reported, never artificially equalized. Expected exposure is not itself proof
of execution: a `with_kwargs=True` pre-forward hook audits actual input IDs,
labels and 2D attention tensors, preserving row permutations, and writes each
observed paired batch. Duplicate/dropped rows, changed masks, extra forwards,
cached/embedded inputs fail. Successful fit validation requires exactly 12
matching actual-forward receipts **and** the original finite 12-update checks.
Failed pre-forward attempts are not certified optimizer updates. Actual
training timings remain in the trainer manifest; supervisor timing/cleanup is
separate. No readout/collector code is supplied.

Controller cap is 1200 inclusive seconds, workers <=600, cleanup reserve 140,
and the Main-supplied six-hour lease cutoff is never treated as independently
verified control-plane evidence. Original diagnostic supervisor owns process
creation/cleanup; the worker watches its real parent and terminates only its
own group on parent death or worker/controller work-window expiry. Main owns
continuous reservation and external controller lifecycle protection.

Every write is labeled `CONTEXT_DISTILLATION_NOT_UNCHANGED_NATIVE_CONTEXT` and
`UNRESOLVED_LOCAL_HASHES_ONLY`. No clean-lineage, G3/P1/G5/H1/H2, semantic,
latent-erasure, model-authentication, or efficacy claim is made.

## Tests and unresolved native acceptance

Final local command:
`PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_rulegame_process_write_20260912.py`
**35 tests PASS, 48.452s**. Synthetic captures/tokenizer/tensors/LoRA weights only;
actual trainer encoding, source replay/export, plan/fit validation are reused.
The original process-material suite also ran locally: **45 tests PASS, 33.909s**.
No third-party model stack or GPU was loaded by these tests.

Coverage includes explicit V2 versus record/P0/V1, unchanged V1 shortage and
wrong predictions, fixed slots/no replacement, wrong source/stage/model,
missing/stale/partial/rejected reviews and exact native bindings, overlength,
EOS/masking/drop/append negatives, raw/native/transformed receipt joins,
source/candidate/completion/material mutation, export failure/no retry, actual
forward input/attention/exposure tampering, fresh paired fits, failed P/A fits,
prior-adapter corruption, frozen-base and saved-weight/config checks, supervisor
ownership/parent-death/time bounds, concrete virtualenv interpreter, six-hour
margin, and no-launch opt-in. Exporter45 additionally covers source interval,
future-outcome, teacher-copy, alias/prediction grammar and atomic-publication
negative cases without relaxing their rules.

Main may rerun the **bridge** CPU mock suite with `ASTRA_SOURCE_ROOT` set to the
accepted node3 snapshot and the concrete native Python; no GPU is needed. Main's
reported native45 is exporter acceptance, not bridge-native acceptance.
Still unresolved: bridge tests under that exact native interpreter; actual
four-row candidate/token lengths and exact rendered-context review; successful
real prepare; native torch/PEFT forwarding-hook compatibility, runtime/memory
feasibility and GPU/supervisor behavior. Reject any mismatch; do not retry with
another interface/selection/model. Those checks and any GPU launch are Main's.

Only the three owned files were changed; no repo changes, Git, SSH, network,
native run, GPU action, readout, or collector work. Stable bytes above; EDIT-STOP.
