# Process-v2 metadata/full-release collector — EDIT-STOP

2026-09-12. This is a new collector, not a modification to the accepted writer.
Only these three files were authored in this task:

- `/tmp/astra_rulegame_process_write_collect_20260912.py`
  SHA256 `e23160132bf4eac82f220b8066c49de3cf8461e50929f9a82f3eac5e12906892`
- `/tmp/test_astra_rulegame_process_write_collect_20260912.py`
  SHA256 `b61da718d19b41678e480b7585729f650bc067c41e0c020c1eee088c271d4d32`
- `/tmp/astra_rulegame_process_write_collect_handoff_20260912.md` (this handoff).

**35 collector CPU-mock tests PASS in 43.903s.** No real model/tokenizer load,
fit, native execution, GPU or queue query, SSH, network, Git, or repo edits were
performed here. All execution/release queries are for Main on node3. Test
fixtures are temporary CPU-only files; all frozen sidecars remain unchanged.

## Exact identity and stable CLI

The collector is deliberately specific to Main's announced native run:

- Plan SHA256: `67f2b89a769dd1f21e2ae3f048aa2d3743a5761f0574dcca3f47e1a8c51b0f44`
- Root basename: `astra_rulegame_process_write_v2_20260912_attempt1`
- Source snapshot: `4c3064c1c3eef068951e9c3b2ca46630754564e7`
- Node3, device `2`; exactly P/A, two own-wake rows each.
- Native input totals P=760 / A=758; supervised target totals P=32 / A=31,
  **including the appended EOS for each row**. These are per-arm corpus totals,
  not per-row counts and not a token-matched claim.
- Schema 2; write protocol `rulegame_process_write_v2_20260912` and material
  protocol `rulegame_grounded_process_pair_v2`.

The actual launcher source was read but never executed:
`/tmp/astra_launch_rulegame_process_write_20260912.py`, SHA256
`b4e2ee193f4ba7cc9138c0652498e3318cb4e685c12a9fbe2f5cf9442b05fee6`.
It writes the sibling `ROOT_launch/{launch.json,gpu.xml,controller.log}` layout.
Its actual launch-receipt hash/PID/time/UUID were not supplied to this sidecar;
Main must provide the exact reviewed `launch.json` SHA256. Do not invent it.

```bash
ROOT="$HOME/astra_diagnostics/astra_rulegame_process_write_v2_20260912_attempt1"
LOGS="${ROOT}_launch"
OUT="${ROOT}_collection_attempt1"
SOURCE="$HOME/astra_sources/4c3064c1c3eef068951e9c3b2ca46630754564e7"
PLAN=67f2b89a769dd1f21e2ae3f048aa2d3743a5761f0574dcca3f47e1a8c51b0f44

env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH="$SOURCE" \
  ASTRA_SOURCE_ROOT="$SOURCE" \
  "${NATIVE_PYTHON:?exact Main-reviewed plan interpreter}" -B \
  /tmp/astra_rulegame_process_write_collect_20260912.py status \
  --root "$ROOT" --plan-sha256 "$PLAN" \
  --launch-root "$LOGS" --launch-sha256 "${LAUNCH_SHA:?exact Main-recorded receipt SHA256}"

# Main only: after ready=true; OUT must not exist.
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH="$SOURCE" \
  ASTRA_SOURCE_ROOT="$SOURCE" \
  "${NATIVE_PYTHON:?exact Main-reviewed plan interpreter}" -B \
  /tmp/astra_rulegame_process_write_collect_20260912.py finish \
  --root "$ROOT" --plan-sha256 "$PLAN" \
  --launch-root "$LOGS" --launch-sha256 "${LAUNCH_SHA:?exact Main-recorded receipt SHA256}" \
  --out "$OUT"
```

Python API:

```python
status(root, plan_sha256, launch_root, launch_sha256)
finish(root=..., plan_sha256=..., launch_root=..., launch_sha256=..., out=...)
validate_archive(path, hashes)
```

`finish`, not its internal `collect`, applies the 300-second watchdog. CLI uses
`finish`. The exact native Python spelling must equal
`os.path.abspath(sys.executable)` in the sealed writer plan; never resolve its
venv symlink. No `--allow-gpu` option exists. This collector does not compute on
the GPU; Main's native finish does live process/reservation/queue queries.

## Frozen dependencies and reuse

The new collector reuses the original record-write collector's pinned writer
loading, saved-fit/controller/worker receipt joins, release checker, metadata
hash custody and safe tar validation approach. It incorporates hardened
exclusive-file/process-session/credential primitives from the acquisition
collector. It does not import or execute those old collectors or their old
run-specific constants.

Runtime dependencies:

- Frozen process writer `/tmp/astra_rulegame_process_write_20260912.py`, SHA256
  `a73dd6074fdd099cea19f46cfed94bf31f22b2ce02b8741ac2f224413ee514d9`.
- Its original record-driver hash dependency remains unchanged:
  `/tmp/astra_rulegame_record_write_v2_20260912.py`, SHA256
  `183b48be6193da953f699d718575f9227fd946d9f8111d2d1647ae5dd431ec7c`.
- Exact Main launcher above.
- The source snapshot's `gpu/astra_mini_sudoku_diagnostic.py` query-only
  `check_free` entrypoint, SHA256
  `a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f`.
- Every original writer implementation/model/material/formation/review pin
  remains checked by its unchanged `checked_plan`/`validate_fit` routines.

No tokenizer, model, trainer execution, GPU tensor library, generation,
restatement, alternative material, or model warmstart is invoked by finish.
The accepted explicit-V2 `inspect_capture` source replay is CPU-only. Native
token receipts are verified against sealed plan/export/native-Main-review
bindings, not silently reconstructed with a substitute tokenizer.

## Custody and all-two-fit gate

`status` reads only launch/process metadata and terminal-marker existence. It
does not open terminal result/fit bodies, load the writer, or query vacancy.
It requires the exact root/plan/launch identity, exactly one terminal marker,
and no owned controller/worker PID, PGID, session member, or currently traceable
descendant in the process snapshot. PID reuse conservatively blocks collection.
Unknown process receipts, ambiguous terminals, process-scan errors, surviving
group/session members, or missing terminal evidence are never treated as free.
There is no polling, signaling, killing, or automatic retry.

After release readiness, finish validates the exact launcher command and its
fresh-base/seed2/rank-recipe, continuous-reservation declaration, node/device,
1200/600/140/300 bounds and initially vacant GPU UUID/XML. The declaration is
not an independently acquired lock; Main retains reservation ownership.

Material validation binds all four fixed slots, the same candidate/current
source replay, source/model inventories, Main's source review and exact native
four-context/target review, complete own-arm raw target bytes, original-native
versus transformed-token receipts, causal masks/one EOS, per-row/batch exposure
and teacher exclusion. It explicitly rejects record/P0/V1 substitutions and
retains wrong predictions; no later source selection or target repair occurs.

Each completed arm must satisfy all original fresh-fit checks: finite losses,
12 epochs/steps/microbatches, 12 actual forward receipts, no warmstart, correct
LoRA coverage/config/shape, frozen-base trainability receipts, token/masking/
padding exposure, whole saved-fit manifest and adapter-file custody. Worker
PID/PGID, parent/controller ID, exact argv/nonce, attempt receipt, sequential
nonoverlapping windows, cleanup flags/return code and controller receipt joins
are checked again. Missing or corrupt completed-arm evidence fails collection.

Saved safetensors are locally scanned in bounded chunks for IEEE nonfinite
values in F32/F16/BF16, with exact file hashes, structure/shape/offset checks and
stable-file identity. No model or tensor library is loaded. Credential patterns
in safetensor headers also fail. This adds **finite-weight metadata evidence**;
it does not put any weight bytes inside the capsule.

No aggregate is constructed before both arms validate. A successful paired
write can report 24 total optimizer updates and the actual native exposure
totals. If successful, expected full target exposure is 384 P + 372 A = 756
labels, and unpadded input exposure is 9,120 P + 9,096 A = 18,216 tokens. Padded
counts come from the actual receipts, not inferred equality. A terminal failure
may be preserved as `COLLECTED_FAILURE_NO_AGGREGATE`, even when two saved fits
exist; missing arms/costs are not zero-imputed. There is no efficacy/readout
aggregate, G3/P1/G5/H1/H2 or clean-lineage promotion.

## Full-release and safe archive

Main must run finish with `CUDA_VISIBLE_DEVICES` absent. The pinned checker
queries the selected GPU via `nvidia-smi`, reconciles same-user device-masked
process reservations and the existing queue's pending/running jobs, and
rejects occupancy, identity mismatch or uncertainty. This is performed after
auditing and again near publication. Owned sessions are rechecked throughout;
the collector never infers vacancy from an old worker cleanup receipt.

Output is a **fresh distinct sibling directory**. It never writes the source,
formation, writer root, launcher root, or `run/main_release.json`. Existing or
partially created outputs are rejected; no overwrite, resume, automatic retry,
cleanup/deletion, or previous-success rewrite path exists. A failed started
collection preserves sanitized `failure.json` plus partial evidence for Main.

Only exact known run/launch paths are eligible. Unknown files/directories,
symlinks, hardlinks, special files, duplicate/nonfinite JSON, invalid UTF-8,
known credential keys/tokens/assignments/URLs and unsafe archive entries fail.
Limits: 2,048 filesystem entries, 32 MiB per text file, 256 MiB total metadata,
256 MiB per scanned adapter weight file. Limits are not automatically relaxed.
Credential screening is bounded known-pattern rejection, not a universal
secret detector; no environment dump is copied.

Native-only exclusions, recorded by path/hash/reason in `custody.json`:
adapter weight bytes; raw corpus files; candidate, Main-review and original
native token audit bodies; full training-token arrays. Archive content is
allowlisted plan/manifests, safe run/fit/forward/launch metadata and logs, plus
derived hashed material summary and collection custody/release evidence.
The source/base/raw artifacts stay native; the capsule alone cannot reconstruct
or reload the adapters. Never promise that it contains weights.

Fresh output layout:

```text
started.json
audit.json
material_summary.json
custody.json
release.json, release.xml
metadata.tgz
final_release.xml
validation.json                 # only after complete validation
failure.json                    # instead of successful validation on error
```

`metadata.tgz` is validated without extraction: exact member set/hash, regular
files only, no links/duplicates/traversal, bounded sizes, credentials rejected.
It contains the initial release snapshot. The final vacancy XML is retained
beside the capsule and its hash is in `validation.json`; the final seal contains
the archive hash and complete member-hash map. A capsule without successful
`validation.json` is not an accepted collection.

Full reservation accounting is the launcher timestamp to observed final
vacancy, including gaps/wait-to-collect. Worker/cleanup/controller times are
nested subsets, not additive. The 300-second collector SIGALRM is independent
of those writer bounds. Timeouts preserve evidence and never initiate retries.

## Tests and remaining native acceptance

Local final test command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_rulegame_process_write_collect_20260912.py
```

**35 tests, PASS, 43.903s.** Integration tests reuse synthetic writer fixtures,
real CPU source/export/fit checks and finite-byte scans, while native loads,
training, process snapshots and vacancy calls are mocked. Production plan/root/
source/native-count pins are changed only inside synthetic test contexts; a
separate test verifies the announced production constants. No mocks exist in
the collector CLI.

Negative coverage includes missing/ambiguous terminals; live/reused PIDs,
groups/sessions/descendants; unexpected process receipts and scan errors;
wrong plan/launch/native counts; source-call/raw-target/native-review joins;
missing second fit and changed forwards; worker ownership/cleanup/window caps;
late metadata/unknown-file mutation; credentials including weight headers;
NaN/Inf in all supported weight types; unsafe filesystem/archive forms;
occupied/reappearing vacancy or queued work; existing output/no retry; masked
collector; watchdog expiry and restoration. Failure collections never produce
a successful-pair aggregate.

Main's reported 35CPU/native35PASS and prepared-plan success were **writer**
acceptance, not native acceptance of this new collector. Remaining: run this
collector's mock suite with the exact native interpreter and
`ASTRA_SOURCE_ROOT="$SOURCE"`; verify Main's actual launch SHA/schema; allow
finish to validate the real terminal/weights/material and live release within
300 seconds. No real terminal or native vacancy was inspected by this sidecar.
Any mismatch stops; do not substitute a different source, plan, tokenizer,
material, model, receipt or output as an automatic repair.

The writer and launcher hashes remain unchanged. All result interpretation is
`CONTEXT_DISTILLATION_NOT_UNCHANGED_NATIVE_CONTEXT`,
`UNRESOLVED_LOCAL_HASHES_ONLY`; no semantic or model-origin authentication,
clean lineage, efficacy or readout claim. **EDIT-STOP.**
