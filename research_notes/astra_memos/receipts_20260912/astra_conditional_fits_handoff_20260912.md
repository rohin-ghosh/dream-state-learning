# Conditional root0 fresh-fit pair — September 12, 2026

**EDIT-STOP.** Implemented only the three assigned sidecars. No GPU/network/
Git, native model execution, allocation, launch, repository modifications,
or edits to Bernoulli's files. No generation/readout path exists in this wrapper.

## Files, tests, hashes

- `/tmp/astra_conditional_fits_20260912.py`
  SHA256 `3be6583f97f68d944774ff15f5fcd4d66522991d62bf865b03f005808cf4f96f`
- `/tmp/test_astra_conditional_fits_20260912.py`
  SHA256 `fd7d3afaf456a8840fed69029cda17f81404bc1df8655fe550a76dbe22a763af`
- `/tmp/astra_conditional_fits_handoff_20260912.md` — this handoff.

**29 stdlib CPU tests PASS, no skips**, locally about0.31 seconds:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 /tmp/test_astra_conditional_fits_20260912.py
```

Tests import no repository modules or native libraries and launch no
subprocesses. They use temporary fake source/model/material/adapter files and
stub native supervision. Coverage includes sealed/exclusive paths, source and
tokenizer changes, extra tokenizer files, exact commands/counts, missing or
ambiguous weights, unwanted checkpoints, wrong saved base, all drop/skip/split
fields, fresh-vs-warm manifests, sequential order, startup cost, failed first/
second arm, missing cleanup accounting, and no implicit GPU permission.
Separately rehashed all seven actual local attempt2 capsule material files:
all match the embedded pins. No native preparation was executed here.

## Fixed inputs and experiment

Consume the existing native material unchanged:
`/localhome/local-rohing/astra_diagnostics/astra_conditional_behavior_20260912_attempt2/material`.
Do not recreate it or reuse attempt1's failure. Root0 spellings must remain
actions `dax,wug`, outcomes `fep,nup`.

Embedded source receipt:
`/localhome/local-rohing/astra_sources/5f6e1f1d217dcdb15176dc84b9ac34ec960c48de`.
Imports must resolve from the supplied source root and match native material
source hashes. Model path comes **only** from native audit `tokenizer_path`;
there is no guessed model argument, download or default preview material.
The wrapper rehashes actual tokenizer/config files and the full base inventory.

Material SHA256 pins include:

```
candidate.json  5d1644b90ff7621ee121aba65be7dd7cae7f15168f5a3c3a09a1bc9aa9a7af8c
AUTH.json       344ec17779696b184468d96ce26ef89e8d3bd0cb5b8dbfde84a4b8dc1c437d48
DERANGED.json   060255b11551b55b20d39f91301cc4e0362134af321bc740134b86e3ca6d511d
manifest.json   d70aea1ae832cd9a60c28cd41f4f2ff2a4071716d1859f50a28405891ce6c4b6
native_audit.json 9c1f9f22a17caf17b36d62b08c35371eb809e6a3feb03b7e60710546257d0760
recipe.json     99deef7593dfc7e8d8ffe14af082876bcff5f27d3ce1ba0580050bb5e54dbf0e
teacher_forcing_interface.json eaf287d50ffb623e6efb0fd4744c5749375061317dc0dcf1a63f64ece6407211
```

The teacher-forcing interface file is hashed solely as part of the immutable
material inventory; this script performs no teacher forcing or readout.

Exactly **AUTH then DERANGED**, each in a separate V3 CLI subprocess and
separate initially absent adapter directory. Both start fresh from the same
frozen base; **no parent adapter, warmstart, merge, resume or arm chaining**.
Seed0, LR1e-4, rank8/alpha16/dropout.05, all seven projection targets/all layers,
four epochs, batch4/accum1, bf16, max512, no packing,128 rows and128 updates.

Per arm:
-11248 input/1888 supervised target tokens per epoch (input includes targets).
-44992 input/7552 target presentations over four epochs.

Pair:256 updates,89984 input/15104 target presentations. The inherited native
recipe uses `overflow=truncate`, but this is **not permission to drop tokens**:
native material says no truncation and actual fit manifests must have zero
context/target drops, truncated/split items and skipped rows, or the pair fails.

Claim/origin are explicitly recorded as
`ORACLE_AUTHORED_DIAGNOSTIC_NOT_CHILD_EXPERIENCE_NOT_CLEAN_LINEAGE` and
`UNRESOLVED_LOCAL_HASHES_ONLY`. This produces fit artifacts, not an L1 result.

## Exact Main commands

Use the same native Python path for prepare and run; its command bytes are
sealed. Main chooses an unused output root and the device. Example output
root below must not already exist. Supplying a device during CPU prepare does
not reserve or allocate it.

```sh
PY=/localhome/local-rohing/v2/venv/bin/python
SCRIPT=/tmp/astra_conditional_fits_20260912.py
SOURCE=/localhome/local-rohing/astra_sources/5f6e1f1d217dcdb15176dc84b9ac34ec960c48de
MATERIAL=/localhome/local-rohing/astra_diagnostics/astra_conditional_behavior_20260912_attempt2/material
RUN=/localhome/local-rohing/astra_diagnostics/astra_conditional_behavior_20260912_attempt2/fits_root0_attempt1
# Main supplies GPU, DEADLINE_UNIX and actual LEASE_END_UNIX.
# Need a full future1200s pair window and lease >= deadline+10 seconds.
PYTHONDONTWRITEBYTECODE=1 "$PY" "$SCRIPT" prepare \
  --source-root "$SOURCE" --materialroot "$MATERIAL" --runroot "$RUN" \
  --device "$GPU" --deadline "$DEADLINE_UNIX" --lease-end "$LEASE_END_UNIX"
```

Only after Main's node3 allocation/full vacancy checks and budget declaration:

```sh
CUDA_VISIBLE_DEVICES="$GPU" PYTHONDONTWRITEBYTECODE=1 "$PY" "$SCRIPT" run \
  --source-root "$SOURCE" --runroot "$RUN" --allow-gpu
```

Receipt/status inspection:

```sh
PYTHONDONTWRITEBYTECODE=1 "$PY" "$SCRIPT" status \
  --source-root "$SOURCE" --runroot "$RUN"
```

Main retains external stdout logging, watchdog and continuous ledger
reservation across both fits, CPU hashing/verification and inter-fit gaps.
There is no inner full `check_free` or device selection; existing
`rulegame_parenting_diagnostic.supervise` handles each worker's occupancy,
process-group cleanup and lease accounting. No previous sidecar is a runtime
dependency; their narrow supervision patterns were reused, not modified.

## Bounds and failure semantics

Pair clock starts at CLI entry, including imports/setup. A full1200-second
window must fit both the declared deadline and real lease minus10 seconds;
otherwise launch is rejected. Effective deadline and real lease are distinct.
Cleanup alarm is armed before CPU input re-verification at effective deadline
minus140 seconds. Each native worker is capped by existing600-second bounds
and the remaining common deadline minus cleanup/safety time. Two600-second
workers do **not** get an additional1200 seconds after CPU work.

Ordinary failure/interruption is passed through the existing owned-worker
cleanup path. No second fit follows a technical failure of the first. A failed
second fit preserves the first and all partial artifacts. No automatic retry,
overwrite, resume, replay, seed progression or outcome-based selection exists.
Even if all work is done, absent/failed supervision or unverifiable release
prevents COMPLETE. Main's external watchdog is still necessary for an
uncatchable controller death or import/OS stall before alarm installation;
missing terminal evidence never grants permission to reuse the GPU.

## Output contract for Main / Bernoulli

Exclusive root files: `plan.json`, `plan.sha256.json`. Schema1 includes exact
source/material/model/tokenizer hashes, full V3 config, native command arrays,
counts, device, deadlines, authored origin and fresh-base initialization.
Offline CPU preparation timing is separate from the later GPU reservation.

Each `run/{AUTH,DERANGED}/` contains:
-`adapter/`: native V3 checkpoint, config, train manifest, metadata and DONE.
-`worker/`: process argv/PID/group, stdout and supervision receipt.
-`fit-result.json`: absolute adapter path, complete file hashes, manifest hash,
  exact counts, supervision and sealed-plan hash.

Bernoulli can consume `run/AUTH/adapter` and `run/DERANGED/adapter` with their
fit-result manifests; the wrapper neither imports nor calls the new readout.
`run/reservation.json` and `run/terminal.json` cover the complete controller.
Statuses: PREPARED_NOT_LAUNCHED, COMPLETE, FAILED_PARTIAL_NO_RETRY, NOT_STARTED,
or NONTERMINAL_OR_ABANDONED. Status is a receipt display, not a new audit.

Terminal includes both fit results when complete, actual whole-controller
seconds, summed supervised-worker seconds, worker accounting, verified native
release and deadline flags. Monetary cost is unknown. Main's eventual full
reservation through independently observed release can exceed controller time
and must be recorded separately; no Main release receipt is fabricated here.

Post-fit verification requires DONE, exact config/base/corpus hash,128 encoded
items/steps, finite loss, no skipped/nonfinite/dropped/split data and exact
44992/7552 accounting. It rejects warm/SVD manifests, missing/empty/ambiguous
weights, optimizer/full-model/nested checkpoints, and mismatched saved LoRA
rank/alpha/dropout/bias/targets/base/layer settings. Model/source/material and
both completed adapter inventories are rechecked without overwriting anything.

## Remaining limitations

Native preparation and execution remain Main's responsibility; only stdlib
fixtures and local material hashes were checked here. The existing native
token audit is consumed and authenticated, not rerun. Freshness/base freezing
are enforced by fresh directories, separate processes, pinned V3 fresh-PEFT
code, config and saved adapter checks—not an independent pre-update or full
base-tensor dump. This wrapper does not reload checkpoint tensors to diagnose
arbitrary corruption beyond file/inventory/config checks. COMPLETE means both
fits technically completed with receipts, **not** conditional acquisition,
clean lineage, readout completeness or scientific promotion.

**EDIT-STOP.**
