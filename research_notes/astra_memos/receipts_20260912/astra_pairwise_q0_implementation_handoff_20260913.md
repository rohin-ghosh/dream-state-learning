# Q0 executor implementation handoff — 2026-09-13 UTC

**EDITSTOP.** Implementation/testing is complete within the assigned files. Main owns integration, the thin launcher, final native-environment CPU acceptance, and any actual preparation/model/tokenizer/GPU operations. No GPU qualification or scientific result is claimed here.

## Owned files and frozen identities

Only these deliverable paths were edited:

| Path | SHA256 |
|---|---|
| `gpu/astra_pairwise_q0.py` | `596071780b961031ef8ef5e352898391df47038db70e2acb68b5c3dbe15c201b` |
| `tests/test_astra_pairwise_q0.py` | `5e4eb5cb9926403319480b4bf8fc5d2225dd1768bb049909da604c1edb634afe` |
| `/tmp/astra_pairwise_q0_implementation_handoff_20260913.md` | This handoff; no self-referential hash. |

Executor: 2,132 lines. Focused tests: 1,154 lines. Applicable AGENTS instructions were checked; no nested instructions were found in the owned code directories. This implements the already-closed recipe and repairs numerical/terminal correctness; it does not expand the formal C11 guard.

No Git operations, downloads, network requests, model/tokenizer loads, actual GPU operations, or experimental launches/kills were performed by this implementation session. CPU fixtures include mocked process custody and temporary evidence files; those are not native proof. Concurrent source, archived tests, notebook, coordination, and research documents were not edited.

## Scientific and provenance boundary

Started from `research_notes/analysis/2026-09-13_q0_executor_gap_map.md`. Scientific precedence remains adjudication, closure v2, mathematical redteam, then claim-bearing preflight, all dated 2026-09-12. No later exploratory scientific material, drivers, templates, rankings, adapters, results, or decision notes were used as Q0 inputs or selectors.

The original capsule SHA256 is `422b27e55f794cd14670f049ad09fd31b95887aa615c4d59bc0a03687e83dcf0`. The executor validates the capsule and original manifest/material/fits/seal identities but does not deserialize fitted outputs or load historical adapters. It constructs only the root-1 projection from original sealed material.

Frozen root-1 orientation is `[0,1,1,0,1,0,0,1]`; actions are `-mem2reg/-gvn`. Rank8, alpha16, dropout .05, all seven projection families, seed1, AdamW LR3e-5, betas .9/.999, epsilon1e-8, weight decay .01, no scheduler/clipping/checkpointing/TF32, eager BF16 base/forward and FP32 trainables remain closed. Thirty-two target-free quartets repeat identically four times; completed fits perform 128 updates with snapshots32/64/128. At most three attempted fits and 2700 seconds/root, with the earlier configured lease cutoff. No retry, resume, replacement quartet, seed, rate, rank, or checkpoint selection.

Main's explicitly authorized prospective numerical registration is production-fixed: safety=4, gradient_floor=1e-12, arithmetic-middle-two even median. These control conservative numerical bounds, audit norm handling, and the previously unspecified even median; they do not change scientific cutoffs. Configuration cannot tune them.

The model-only receipt is optional during `prepare`, required for a ready native execution:

- `/tmp/astra_qwen_public_binding_receipt_20260913_attempt1.json`: `e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019`.
- Metadata identity recorded by that receipt: `8aebd0fc61d42917fedbf3c6dd08e39c36eac4c92478c88f2accabadae78de3b`.
- Public identity: `Qwen/Qwen2.5-7B-Instruct@a09a35458c702b33eeacc393d103063234e8bc28`.

Main supplied the public verification; this agent checked permitted local receipt bytes, not the official endpoint or actual model files. Native preparation/execution checks local file inventories against the receipt. Historical origin labels are not rewritten and public model provenance does not establish clean ancestry.

Confirmation-root opaque IDs and optimizer-seed allocation remain **null/unselected/output-blind**. This executor supports only registered root1, not unregistered confirmations.

## Implemented surfaces

- `build_prepared`: sealed-material projection, original native-chat rendering, maximal natural common-token prefixes and fixed branch IDs, collision/boundary checks, exact target-independent quartet order and complete panel/request inventories.
- `objective_audit`: explicit FP32 P/V objectives and actual autograd gradients, ordered raw gradient tensors, raw logits and reconstructed mass, fixed degeneracy/zero-gradient branches, state-neutral no-update audit.
- `head_margin`, `canary_result`, `train_fit`: FP64 head products/directional contractions, actual FP32 first-update deltas, raw before/after artifacts, signed Gram checks, conservative error bounds, fixed map/unary predicates, real first AdamW step followed by uninterrupted continuation or exact early stop.
- Diagnostics preserve/check RNG, modes, buffers, gradients, optimizer, trainables, and frozen-base identities. Native snapshots are serialized only at32/64/128 and reloaded in fresh evaluation processes; no optimizer restoration.
- `Lifecycle`, `native_worker`, `native_execute`: serial disposable audit, contemporary OFF, fresh independent fits, fresh snapshot evaluation, dynamic optional release, raw strict generation via the registered interface helper, counters, immutable receipts, and registered supervisor-owned process cleanup.
- `reduce_evidence`, `native_reduce`, `native_replay`: unchanged exact/held/class/key/complement/copy/locality gates; optional-arm non-veto; checkpoint curves; raw numerical replay; integrity-versus-science disposition; resource accounting and immutable inventory validation.
- Native large tensors are content-addressed binary artifacts, not giant JSON arrays. CPU fixtures also cover binary tensor replay and actual CPU autograd/AdamW training.

### Historical helper isolation

The four historical helpers remain byte-identical:

| Helper | SHA256 |
|---|---|
| `gpu/astra_semantic_objective_probe.py` | `98a90f33dcd5582b9e32fe21d08dd29283c82b955ff350c8c994d2903b2f0d41` |
| `organism_v6/semantic_writer_diagnostic.py` | `d6ea45ac6bfb5cabe6cbd1224f4cf101e96cbd0e07c029e934c2aa3e03e1ddb0` |
| `organism_v6/multikey_writer_gateway_simple.py` | `b9fd33c7c11b2f57395f08d609bb1df004d9663eeefd143060bb1a24a34f10c8` |
| `organism_v6/writer_interface_calibration.py` | `9ab582ebc935ae36b88bd412fd06d799044661612f89a0770e46b92ab1b066c7` |

The already-registered supervisor `organism_v6/run_reasoning_neutral.py` is separately pinned to `dd4f0a72cddc8226fa48ce50ab0faa6dd4e75f9db510aa89cfb5224898ee7496`. Its `run_worker` returns PID and writes `.cleanup.json` with the fields consumed by this executor; that connection was statically checked, not exercised with a real worker.

The current carrier module differs from the original capsule identity. It is deliberately NOT imported into Q0. `historical_helpers` extracts only `fit_model` from the pinned semantic writer's AST, injecting the pinned gateway namespace; it does not import the diagnostic's changed carrier, old trainer, or reducer. Q0 uses its own small `/proc` identity reader and the registered supervisor for custody. Historical test-support dependencies remain test-only, separately declared by Main.

## Advisory repairs

The allowed numeric advisory's one-ULP supplied-q/M gate flip and common-offset mass-integrity defect are repaired with shared canonical reconstruction from primitive prefix records. Raw supplied fields are preserved; acceptable numerical consistency never lets supplied derived fields select a scientific gate. Producer→validator→reducer tests include common offsets and actual locality gate outputs. Scientific .05/.10 and all discrete gates remain exact. Canary boundary tests now execute the real predicate at equality and the adjacent failing value. FP32-conversion overflow and even-median overflow are tested.

The allowed lifecycle advisory's bounded defects are repaired:

1. Final release queries and raw reduction exceptions are captured in `FAILED.json`; release-query failure never means verified release. Invalid raw stages remain byte-for-byte preserved. Failure replay returns a deterministic nonreportable projection without demanding validation of the stage that caused the rejection. Unvalidated partial counters are explicitly withheld, not called scientific counts.
2. `RESOURCE.json` and `reduction.json` are provisional evidence. `reduction.json` explicitly has `scientific_claim:false`; `SEAL.json` is marked pending durable finalization. All evidence files/directories are fsynced, then seal durability is observed in `FINALIZED.json`. If final witness publication itself crosses the deadline, a write-once `FINALIZATION_ABORT.json` records that fact. Replay derives the final classification from these observations. No immutable provisional file claims a scientific result that late finalization can invalidate. A missing completion witness cannot qualify a scientific terminal.
3. Wall and monotonic accounting start at `native_execute` entry, before helper/source/input/tokenizer/hardware verification. Slow verification consumes the same budget and cannot receive a fresh2700 seconds. Worker budgets retain the cleanup reserve and earlier lease cutoff.

Native final output is the canonical JSON returned by `execute`/`replay`, with `report`, `report_sha256`, and replay status. **There is no native `report.json`; `report_sha256` is the canonical returned-report digest.** Preserve provisional evidence and any abort marker; never overwrite/reseal to promote it. CPU fixture sealing retains its separate `report.json` format.

## Stable CLI and Main's launcher contract

Run from the frozen source root using the bound native interpreter. Before source preparation, complete the final native-environment CPU acceptance. These commands are instructions for Main; they were not executed against native models by this agent.

```bash
PY=/absolute/bound/native/python
SOURCE=/absolute/frozen/source
SUPPORT=/absolute/archived_test_support_manifest.json
CPU_RECEIPT=/absolute/new_final_cpu_receipt.json
CONFIG=/absolute/q0_config.json
RUN=/absolute/new_q0_root

CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SOURCE/tests:$SOURCE" \
  "$PY" -B -m gpu.astra_pairwise_q0 cpu-tests \
  --test-support "$SUPPORT" --out "$CPU_RECEIPT"

"$PY" -B -m gpu.astra_pairwise_q0 config-template

CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
PYTHONDONTWRITEBYTECODE=1 \
  "$PY" -B -m gpu.astra_pairwise_q0 prepare \
  --out "$RUN" --config "$CONFIG" --test-receipt "$CPU_RECEIPT"

CUDA_VISIBLE_DEVICES="$GPU_UUID" CUBLAS_WORKSPACE_CONFIG=:4096:8 \
PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 \
  "$PY" -B -m gpu.astra_pairwise_q0 execute --out "$RUN" --allow-gpu \
  > "${RUN}.execute.json" 2> "${RUN}.execute.stderr"

CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
PYTHONDONTWRITEBYTECODE=1 \
  "$PY" -B -m gpu.astra_pairwise_q0 replay --out "$RUN" \
  > "${RUN}.replay.json"
```

Inspect JSON `successful` for CPU acceptance and the returned native report's label/claim/resource fields; do not treat a command's zero exit alone as scientific qualification. `prepare` refuses unsuccessful, skipped, mismatched-source, mismatched-environment, or incomplete-support receipts. `native-readiness` deliberately returns exit2 and is informational, not a launch gate implementation.

Fill the config template's absolute clean local model/tokenizer paths, Main's permitted public-binding path, exact gateway `environment_identity()` result, SHA256 node identity, reserved A40 GPU UUID/driver, lease end/cutoff, approved intake, and dated Builder reference. Keep model/revision/scope/numerical policy unchanged. Lease cutoff must retain the historical six-hour lease buffer. The output root must be new, outside the repository and model/tokenizer paths; its parent must already exist. Do not place launcher stdout/stderr inside RUN. Do not manually launch the internal `worker` command, add retries, or reuse a started root.

The native `execute` controller invokes only the registered supervisor and supplies each internal worker's sealed ticket/job, source bindings, deadline, process identity, prior receipts, and this run's snapshot if applicable. Main need not implement kernels, fitting, evaluation, replay, or internal cleanup; those paths are implemented here. Formal C11 remains deferred.

### Regression-support packaging

`native_source_pins()` is the17-file runtime/scientific/source-test allowlist, NOT a complete archived regression import/data environment. Main identified missing legacy dependencies/docs in the first minimal native snapshot and successfully assembled the immutable original-d160 support separately. No archived test is modified.

Supply `--test-support` as a JSON file with exactly:

```json
{
  "provenance": "Main's exact original-d160 source/test-support archive identity",
  "scope": "ARCHIVED_REGRESSION_SUPPORT_ONLY_NOT_Q0_INPUT",
  "files": {
    "relative/path/to/an/archived/support/file": "64-character-lowercase-sha256"
  }
}
```

Main must enumerate the full historical regression-support closure: legacy imported modules/fixtures, the old shell wrapper, and the nine frozen old support documents. The executor checks safe relative paths and hashes before/after tests, records the manifest and its digest in the CPU receipt, and validates it again during prepare. `cpu-tests` also supplies the legacy `tests/` import root, restoring `sys.path` afterward. These support bytes are not added to Q0's runtime/scientific input allowlist. Retain Main's immutable support snapshot with the acceptance receipt for reproducibility.

## Exact local validation

Final combined command, run in `/data/home/rohing/dream-state` on Linux:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH="$PWD/tests:$PWD" \
/tmp/astra_preservation_cpu_20260912/bin/python -B -m unittest \
  tests.test_astra_pairwise_q0 \
  tests.test_semantic_objective_probe \
  tests.test_semantic_writer_diagnostic \
  tests.test_multikey_writer_gateway_simple \
  tests.test_writer_interface_calibration \
  tests.test_run_reasoning_neutral -q
```

**PASS: 209 tests, 161.360 seconds, zero failures/errors/skips.** Breakdown:71 focused Q0 +105 mandatory objective/writer/gateway +33 interface/supervisor. Interpreter is Python3.12 with Torch2.8.0+cpu. NumPy is absent and Torch emits its expected warning; tensor-byte fallback was exercised. No dependencies were installed. This is local CPU regression evidence, not the bound native-environment launch-acceptance receipt.

Earlier targeted terminal-fixture command used the same hidden-CUDA/offline environment and `-m unittest tests.test_astra_pairwise_q0.NativeProtocolMockTests -q`:11 tests passed in103.113 seconds, before the additional support-manifest test. The final combined run supersedes it.

Focused tests include real CPU autograd and uninterrupted128-update AdamW fits; true-XOR/unary and cheap-policy canaries; numerical equalities/adjacent failures; Boole q/M offset/boundary cases; schedule/material mutations; RNG/state/snapshot invariants; all reducer thresholds and dynamic release branches; binary artifacts; and mocked native preparation/controller/replay. New native fault fixtures cover invalid final raw counters, final release-query exception, late RESOURCE/reduction/seal/FINALIZED writes, verification timeout before any worker, failed verification without tokenizer-dependent abort replay, and separately pinned test support.

CLI smoke commands `material`, `contract`, and `config-template` succeeded without loading a tokenizer/model/GPU. `native-readiness` returned expected exit2. `material` reported exact128, held64, missing8, unsupported8, neighbour16, wrong_root64, copy8 and original capsule/material hashes. All four helper and supervisor hashes were rechecked after the combined suite.

Main separately reported203 tests passing in85.141 seconds, zero skips/errors/failures, on native Python3.12.3/Torch2.13.0/Transformers5.5.3/PEFT0.20.0, using the earlier `a58af68d...`/`5b2e029d...` working snapshot plus original-d160 historical support. That result is useful compatibility evidence but **does not accept these final source bytes**. Main must rerun the final complete receipt after EDITSTOP, with the now-required support manifest.

## Remaining native requirements and explicit limits

- No missing worker/trainer/evaluator/controller/replay implementation is handed back. Actual native Qwen loading, tokenizer boundary receipt, CUDA numerical behavior, generation/counter hook coverage, process-group cleanup, and real release-query behavior remain unexecuted here. CPU/mock passes cannot substitute for them.
- Main must bind the final frozen source/support/native environment; run the final full CPU receipt; prepare against the permitted clean local public-bound model; inspect preparation; then decide/run the one registered root under the existing operational contract. Main retains actual launch responsibility.
- Runtime and memory cost are unprofiled. Full frozen-base state hashing, raw audit gradients/logits, FP64 diagnostic reductions, and fsynced binary artifacts may be expensive. No throughput or fit-within45-minutes promise is made; the exact ceiling remains binding, and late completion is nonreportable rather than grounds to raise it.
- Filesystem/media failure or an external crash can prevent a durable terminal from being written at all. Preserve every available raw artifact; an incomplete/corrupt seal or witness is not scientific evidence and must never be repaired by retrying the same scientific root. Normal captured worker/release/raw-validation failures and tested deadline crossings have replayable nonreportable dispositions.
- Post-terminal replay is read-only verification, explicitly separate from completed evidence/reservation accounting. A final scientific label can only qualify the supplied synthetic root1 recipe and its registered controls/locality, not clean ancestry, H1/H2, retention, root robustness, or child learning.
- No new consequential scientific ambiguity was selected. Confirmation allocation remains unselected. No exploratory inputs or formal C11 expansion are required for this handoff.

**EDITSTOP — no further executor/test edits by this implementation agent after this handoff.**
