# EDITSTOP — native OFF-only perception anchor diagnostic

Prepared September 13, 2026 UTC. Main binds final reviewed bytes and owns all
tests, preparation, device allocation, native execution, and acceptance.

Only these three assigned files were created/edited:

| File | SHA-256 |
| --- | --- |
| `/tmp/astra_birth_skill_probe_run_20260913.py` | `59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c` |
| `/tmp/test_astra_birth_skill_probe_run_20260913.py` | `06fdf58a796454145b4f9e5e86ac4ebc688a81496becb7851691b893c0b59d22` |
| `/tmp/astra_birth_skill_probe_runtime_handoff_20260913.md` | Supplied in final EDITSTOP response; not self-hashed here. |

Driver is executable. No repository files, Q0 material/results, fitted birth
adapters, native environment, model/tokenizer instances, GPUs, network, or Git
were operated on. Only public source interfaces were inspected. Q0 ownership
and monitoring remain entirely with Main; this driver must receive a separately
available single GPU, never an occupied one.

## Non-material operational repair — bounded GPU query

Main reports the tokenizer repair accepted: **23 CPU tests PASS in 1.880s**;
native PREPARE passed with prompt lengths **262/268 absent, 297/303 present**.
Main then launched controller PID `311696` on Node3 GPU0, plan hash prefix
`630111ae`, with source frozen under `perception_anchor_fixed_20260913_attempt1`.
That controller **aborted before its first worker**: the initial
`nvidia-smi -i 0 -q -x` query exceeded the former 3-second subprocess timeout.
Main reports node NVML queries taking approximately 20 seconds, with a GPU7
driver fault and no reset. These observations are supplied by Main; no native
query, live-source inspection/edit, driver reset, or reproduction occurred here.

The only runtime code changes are `GPU_QUERY_SECONDS = 30` and using that
constant for the existing query timeout. The **900-second outer controller cap
and 180-second collection cap are unchanged**; query time consumes the existing
controller budget, and its remaining deadline can interrupt a query earlier.
UUID/index validation, query exit/XML validation, process-absence/release checks,
owned-group cleanup, no-retry policy and immutable root semantics are unchanged.
Three new CPU fixtures verify timeout 30, nonzero/malformed/timed-out queries
failing closed, and strict identity/process-absence checks.

Before this repair, the previous three files were preserved with original
basenames in `/tmp/astra_birth_probe_query_prerepair_20260913/`, with SHA-256:

| Preserved original basename | SHA-256 |
| --- | --- |
| `astra_birth_skill_probe_run_20260913.py` | `0e61f80738d28370d614a2f786138f3dd2ea79bdbacb02193d9e7d7dbe6fd086` |
| `test_astra_birth_skill_probe_run_20260913.py` | `6fe7a180f70c6b0b064228d6bbbf8e03eb542013e8715784dce2015fa27be728` |
| `astra_birth_skill_probe_runtime_handoff_20260913.md` | `6dcd630c73f8b7eba605adff419841bb82f8fa10be2d2242b7f1a8f2b4b47712` |

No failed root is reused or relabeled. Main preserves the aborted attempt,
measures the actual query independently, freezes these new bytes, and prepares
a **new immutable root/plan** before any later launch. Only the same three local
files and explicitly authorized backup directory were written during repair.

## Earlier non-material repair — template return normalization

Main reports the original native-environment **CPU suite: 19 PASS in 1.254s**.
Main's native PREPARE then failed **before `root.mkdir()`** in `render`: on
Transformers 5.5.3, the tokenizing template call returned a BatchEncoding mapping
with `input_ids` and `attention_mask`. Calling `list(mapping)` yielded keys,
not the token IDs, despite `encode(rendered)` yielding matching actual IDs.
These are Main-reported observations; no native reproduction occurred here.

Repair is confined to normalizing `collections.abc.Mapping` through `input_ids`,
accepting a flat list/tuple of nonnegative integer IDs, and rejecting missing,
empty, nested, string, negative, boolean, or float token vectors. The same strict
validation applies to `encode` output. The independent template-versus-encode
equality check, system-text capture, context bound, source visibility, pairing,
generation settings and scientific claim limits are preserved. No C11 guards,
architecture decision, weakened acceptance check, or scope expansion is added.

Four CPU regression tests cover plain dict and UserDict mapping returns,
malformed token vectors on both sides, and a well-shaped token mismatch that
must still fail equality. Tests now honor `BIRTH_PROBE_DRIVER` so Main can run
them against a uniquely frozen native driver path without overwriting `/tmp`.

Before any repair, all three originals were preserved with their original
basenames under `/tmp/astra_birth_probe_prerepair_20260913/`. Verified SHA-256:

| Preserved original basename | SHA-256 |
| --- | --- |
| `astra_birth_skill_probe_run_20260913.py` | `de1cd675be66026f916a10633d1e5672ebe71ce9616f4d1ce25a8a88ad503caf` |
| `test_astra_birth_skill_probe_run_20260913.py` | `9bdeaf527d7051b9f00887a7d83bc69ca229fd614149a3a33a1573f9771769cc` |
| `astra_birth_skill_probe_runtime_handoff_20260913.md` | `b45136f40093b9fcb39f3904e8051abaa5c788f9b3780495e9dfdb8e1ca61eb0` |

Only the authorized originals backup and the same three assigned files were
written during repair. Main retains all native acceptance and Q0 inspection.

## Implementation and exact scope

- Commands: `prepare`, `controller`, private `_worker`, `collect`. This is a
  direct, standalone adaptation of `fundamental_teaching_readout.capture`,
  `rulegame_parenting_diagnostic.NativeBackend.generate`, and the small owned
  process-group/GPU-release primitives in `run_reasoning_neutral`. It does not
  import the training/native-world diagnostic module or its training imports.
  The corpus extracts its existing public parser definitions with its own AST
  interface, unchanged.
- Builds only `build_variants("perception", split="dev", system_anchor=ANCHOR)`.
  Fixed corpus seed/order, 12 public situations, absent then present, 24 calls.
  No training split is built or consumed. Identical paired row/source/target
  bytes are checked; the extra system message and resulting input hash are
  the only corpus-row differences. No adapters, fit, teacher, or science gate.
- Anchor, verbatim:

  > Keep observations, prior predictions, and later outcomes distinct. Report only what the public record supports. Do not invent a prediction when none was stated. Compare an explicit prediction with its matching outcome; do not infer a hidden rule. Follow the requested record format.

- Local Qwen2.5-7B-Instruct revision
  `a09a35458c702b33eeacc393d103063234e8bc28`, OFF only. vLLM inference, BF16,
  tensor parallel 1, engine and sampling seed 0, temperature 0, maximum 192
  output tokens, no LoRA, no prefix cache, no training/dropout path; explicit
  `torch.inference_mode()` around generation. Engine and sampling parameters
  are fully recorded in every identity. No remote model/tokenizer names are
  passed to loaders; offline/telemetry-disabling environment is set.
- Exactly one fresh request conversation per item, one new worker/backend per
  condition. Only the row's `input_messages` reach generation. Metadata, case
  labels, targets, source proofs, scorer, and corpus manifests never enter a
  model request. IDs remain archive bookkeeping only.
- Actual tokenizer chat template, rendered prompt, token IDs, system text and
  system segment are captured at prepare and matched against native capture.
  **Absent does not mean no system prompt.** Qwen's tokenizer-inserted default
  system text is recorded. Present supplies the exact anchor as the explicit
  system message, replacing the tokenizer's fallback, not appending to it.
  This operational contrast is part of the diagnostic's interpretation.
- Each request is written before generation; raw output, actual input/output
  token IDs, decoded output, finish/stop reason and monotonic timing are saved
  before validation. Identity (source/model/native environment/driver bytes)
  is saved before the first call. No scores exist in worker/controller output.
- Controller wall ceiling 900 seconds includes verification, both workers,
  cleanup, final checks and archive closure. Launch deadline reserves the last
  20 seconds for cleanup. It never retries/resumes a used run. Each worker is
  its own session/group, checks the controller ownership receipt and GPU UUID,
  and has deadline/parent-loss guards. Only spawned groups are signaled.
  GPU UUID/index and the process table are queried, never memory thresholds.
- All worker stdout/stderr goes to exclusive files in an existing **external**
  log directory. After exit and verified release, a closed copy is archived.
  Caller stdout/stderr within the run/collection root is rejected. Roots and
  protected source/model/log inputs may not overlap. JSON records use atomic
  no-overwrite publication. Failed runs keep completed evidence, have no valid
  success archive, and are not reused.
- Both 12-call closures and per-worker release receipts must validate before
  `archive.json` is created. Main pins that archive's SHA-256. Collection has a
  separate 180-second wall bound, validates every archive file and the complete
  file set, source/model/environment identity, all 24 captures, and release
  receipts **before any scoring call**. It does not start a GPU or tokenizer.
  It writes a new disjoint collection directory and leaves the archive alone.
- Scores use corpus `score_response` / `public_record_parser`, reporting all
  paired booleans and counts plus present-minus-absent. Scientific pass is null;
  learned-skill claim is false. Diagnostic n=1 elicitation only: no learned
  skills, persistence, H1/H2, L2, exact-wording, or paraphrase-validity claims.

## Main's binding receipt

Prepare requires both `--binding-sha256` and `--corpus-sha256`. No contaminated
birth normalization or old adapters are accepted. The supplied corpus pin was
`078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6`;
Main reports the corpus pushed as `c0db09a6`; no Git check was made here.
Main may explicitly pin different **final reviewed** corpus bytes. DEV12 and
anchor-pairing invariants must still hold. Review remains pending until Main
binds the final source and driver bytes.

**Use Main's existing receipt directly; no new formal receipt or C11 workflow
is required:** `/tmp/astra_qwen_public_binding_receipt_20260913_attempt1.json`,
SHA-256 `e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019`.
Its public-only contents were inspected here without any fetch, model read or
native operation. It declares 14 matched official files for the frozen revision.
Prepare requires that exact receipt hash, repository/revision/local model path,
14 public-match records and their file hashes. It scopes this existing public
model receipt to the supplied source snapshot and actual native environment in
the plan, then compares the complete current local model manifest. Original
receipt bytes are archived unchanged. No old birth normalization is needed.

Main's explicit prepare invocation is the final scoped source/environment
binding; the internal `approved_by: Main` label records that caller contract,
not cryptographic authentication or an independent review. The receipt's
`clean_lineage_certified: false` limitation remains untouched. Local comparisons
do not reauthenticate the original official metadata or upgrade provenance.
An already scoped model-only receipt is also accepted, but is unnecessary here.

`--source` is a pinned public source snapshot root containing the two listed
paths. Only those source files are read/copied; only the corpus is imported.
Both original and archived copies are checked for drift. No Git operation is
needed. The native manifest records Python path/executable hash/version and
installed vLLM, torch, transformers, tokenizers, safetensors and huggingface-hub
versions. It is not a wheel-level reproducible-environment attestation.

## Tests and exact invocation (Main only)

Performed by this author on the repaired files: **two AST syntax parses passed**. No test suite,
prepare, controller, worker, collection, native/model/tokenizer/GPU/network/Git
operation was executed. Main reports **19 original CPU tests passed in 1.254s**,
then **23 tokenizer-repair CPU tests passed in 1.880s** with native PREPARE passing.
The current **26-test CPU suite has not yet been run by this author**, respecting
Main's exclusive execution assignment. Prior passes do not certify these new
query-timeout repair bytes or successful controller execution.

Coverage: fixed paired DEV12/messages-only visibility/default system capture;
fresh condition backends; scope/adapters/fit/legacy/revision rejection; actual
corpus hash; greedy/OFF/inference parameters; failure evidence without closure;
all-24-before-scoring; missing final capture; source/model/environment drift;
stdout/root lifecycle; controller timeout and no retry; owned-group cleanup and
external stdout; direct existing-public-receipt scoping and rejection tests;
independent ceilings; immutable collection/full archive
tampering; weak release/termination rejection; fresh-process receipt binding;
mapping-shaped tokenizer return normalization and malformed token vectors;
30-second query timeout with unchanged outer cap and fail-closed GPU queries.

```bash
PYTHONDONTWRITEBYTECODE=1 BIRTH_PROBE_PUBLIC_SOURCE=/ABS/PUBLIC_SOURCE_SNAPSHOT \
  BIRTH_PROBE_DRIVER=/ABS/UNIQUE_FROZEN/astra_birth_skill_probe_run_20260913.py \
  python3 -B /tmp/test_astra_birth_skill_probe_run_20260913.py
```

The fixture suite imports only stdlib and the public corpus/parser interface.
Tokenizer rendering, model hashes, native environment, backends, subprocesses
and GPU inspection are replaced by CPU fixtures/mocks. No real inference or
real process termination occurs in the suite.

After tests pass and Main accepts the public receipt, substitute reviewed paths,
the returned plan/archive hashes, and an actual lease Unix
timestamp below. `RUN` and `OUT` must not exist; `LOGDIR` must already exist and
must be outside both roots. Use the **same native interpreter** for all stages.

Candidate only, not a reservation: **Node3 GPU0**,
`GPU-0ee6f753-c61e-e18a-8aea-acccd3042939`. Main must verify `/proc` reservations
and availability before using it. The driver checks live GPU processes but does
not replace Main's reservation check. Run the following on the intended node,
not a different machine that happens to have a GPU index 0.

```bash
PY=/localhome/local-rohing/v2/venv/bin/python
DRIVER=/ABS/UNIQUE_FROZEN/astra_birth_skill_probe_run_20260913.py
RUN=/tmp/perception_anchor_RUN_UNIQUE
OUT=/tmp/perception_anchor_COLLECT_UNIQUE
LOGDIR=/tmp/perception_anchor_logs

"$PY" -B "$DRIVER" prepare \
  --root "$RUN" --source /ABS/PUBLIC_SOURCE_SNAPSHOT \
  --model /localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 \
  --binding /tmp/astra_qwen_public_binding_receipt_20260913_attempt1.json \
  --binding-sha256 e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019 \
  --corpus-sha256 078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6 \
  --gpu-uuid GPU-0ee6f753-c61e-e18a-8aea-acccd3042939 --gpu-index 0 \
  --lease-end ACTUAL_UNIX_TIMESTAMP --log-dir "$LOGDIR" \
  > "$LOGDIR/prepare_UNIQUE.json"

"$PY" -B "$DRIVER" controller --root "$RUN" \
  --plan-sha256 EXACT_PREPARE_RETURNED_SHA256 --allow-gpu \
  > "$LOGDIR/controller_UNIQUE.json" 2> "$LOGDIR/controller_UNIQUE.stderr"

"$PY" -B "$DRIVER" collect --root "$RUN" --out "$OUT" \
  --plan-sha256 EXACT_PREPARE_RETURNED_SHA256 \
  --archive-sha256 EXACT_SUCCESSFUL_CONTROLLER_RETURNED_SHA256 \
  > "$LOGDIR/collect_UNIQUE.json"
```

Never invoke `_worker` manually. Nonzero exit, missing/partial closure, false or
unknown release, missing archive, drift, excess time, and malformed native
capture are failures, not a partial paired readout. Preserve the failed root
and external logs, resolve with Main, and use a new root for any separately
authorized subsequent attempt. No automatic reruns occur.

## Remaining actual acceptance needs / limitations

1. Main reruns the repaired 26 CPU fixtures against the uniquely frozen driver
   via `BIRTH_PROBE_DRIVER`, then rebinds its exact bytes. The prior 23 PASS
   (1.880s) predates the query-timeout repair; syntax-only checks do not certify
   the new suite. Main separately measures the actual node query latency.
2. Main reviews the final source/driver/test bytes, accepts the existing public
   model-only receipt, verifies the exact local base revision, and checks that
   source/model/log/run paths and GPU/lease allocation are independent of all
   ongoing science. No extension, lease purchase, or reservation is implemented.
3. Main prepares a new immutable root after freezing the query-timeout repair;
   the previously accepted Mapping normalization remains unchanged. Prepare must
   demonstrate tokenizer default-system extraction,
   template/token agreement and context budget on all 24 requests. The strict
   parser expects the Qwen `<|im_start|>system` template segment; incompatible
   template behavior fails closed rather than silently claiming no system.
4. Main checks the installed vLLM version accepts the pinned engine/sampling
   kwargs, BF16 and single-GPU allocation, and that native output decoding with
   special tokens skipped exactly matches vLLM's returned text. Incompatibility
   is a capture failure requiring a reviewed repair, never a weakened audit.
5. Main validates real child-process/session behavior and the nvidia-smi XML
   identity/process-table release checks on the allocated node. GPU queries
   fail closed; no other process/group is killed. Release receipts prove the
   observed cleanup at that time, not indefinite future GPU vacancy. There is
   no independent reservation-service release integration.
6. Parent-loss/deadline guards kill only the worker's owned group. Escaped native
   descendants, driver hangs and unverified GPU release are failures for Main,
   not permission to kill unrelated processes. CPU fixtures do not certify the
   real backend's process topology. Native shutdown is best-effort followed by
   controller-owned group cleanup and strict GPU-process absence validation.
7. Collection does a full local model hash/environment check within its separate
   180 seconds but loads no model/tokenizer and queries no GPU. Slow storage may
   exhaust the bound. Pinning local bytes/manifests is not independent origin
   authentication; no C11 machinery or scientific qualification is introduced.
8. Absent then present is fixed, not counterbalanced; hardware/order effects and
   n=1 uncertainty remain. Anchor changes the explicit system condition versus
   the tokenizer default. No result yet exists, and even a positive paired
   difference is only public-record elicitation on authored DEV12 situations.

EDITSTOP: implementation handed back; all native acceptance remains with Main.
