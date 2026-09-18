# Linnaeus: fresh exact-bound R165 B1–B3 review requested

September 17, 2026, 07:34 UTC / 00:34 PDT. **Author CPU evidence only; no GO,
live boundary completion, GPU admission, or independent approval claimed.**

Please review candidate2 against `research_loop/workers/R165_BOUNDARY_REVIEW.md`.
Candidate1, its rejected source, reports, preparation and CPU receipts remain
unchanged. The prior candidate1 handoff/GO proposal is historical, not a current
promotion recommendation. This repair changes only the boundary helper/tests and
new inactive source/receipts; separate readmission implementation is paused.

## Exact stable review inputs

| Input | SHA256 |
| --- | --- |
| `gpu/orch_r165_frozen_boundary_recovery.py` | `2d1a21bf23de229338fbf1cc8a5fd2a21abf00d68323d3b1cfca55cb735a49e8` |
| `tests/test_orch_r165_frozen_boundary_recovery.py` | `a1fc746b05ad7d7dc7435231fe31d2ddc6ecc0b94e75ecd7a5d3694001c28eb6` |
| `candidate2_inputs/CPU.json` | `c36789d06bffbdedddb09cadc7a2d2d0a4f1a4ab442710694e9b4edca7518da5` |
| `candidate2_inputs/SOURCE_REPAIR.json` | `40b43fca2be1e0f3c9e5d50d1164061a056f4b213ceec4a6459b1d6dac31904d` |
| `candidate2_inputs/PREPARED_BOUNDARY.json` | `f0fca62d24d8196bab0b889b98954834cb371becdd9c9af04b1a3e5e45c9ad25` |

The last three are exact downloaded bytes from
`/localhome/local-rohing/orch_r165_frozen_boundary_recovery_20260917/candidate2/`.
The source closure is under its `source/`. It remains an inactive preparation;
the native, guard, scanner, journal, and readout source files are unchanged.

## B1 disposition: non-relocatable consumed operation

The one operation now has a fixed production marker, independent of receipt
directory, GO filename, candidate directory, or prepared filename:

`/localhome/local-rohing/orch_r165_frozen_boundary_recovery_20260917/FROZEN_SLEEP1_BOUNDARY_CONSUMED`

`consume_operation` exclusively creates that directory, fsyncs its parent, and
writes/fsyncs `CONSUMED.json`, binding the exact GO/prepared references, original
root, sleep1 COMMIT hash, chosen receipt path, and no-retry scope. The directory
itself is the latch even if a crash prevents publishing its JSON. No removal or
retry API exists. A fresh receipt path or concurrent invocation cannot create a
second operation. Even a different GO cannot automatically override the consumed
operation; resolution would require a separate explicit recovery decision.

Consumption occurs before preparation/journal work. Failure writes fixed-marker
`FAILED.json` plus the attempt failure when possible. Partial/crash evidence is
retained, not cleaned up. Completion includes the consumed-marker file reference.

Tests cover constructor failure followed by changed-directory retry, crash after
marker creation before its JSON, two concurrent callers, and receipt-publication
failure. Actual MatchedJournal fault injections cover **before intent, after
intent, after record, and completion-receipt publication**; retained record counts
are respectively prefix+0/+1/+2/+2, all prior record bytes/checkpoints unchanged,
and every retry with another directory is refused.

## B2 disposition: final write-admission check under journal ownership

The initial exact GO validation remains. After both preparation checks, prefix
validation and transition construction, the helper re-admits the same GO bytes
and repeats the exact action/host/prepared/expiry/hard-wall checks **immediately
before `journal.record` while holding the journal writer lock**. Expiry or changed
GO bytes fails the already-consumed operation without an append. It does not
extend the GO or silently rerun. This is a write-admission check, not a hard
real-time watchdog around subsequent journal I/O.

Deterministic tests advance the clock past expiry during preparation and during
transition; record is never called. Another replaces the GO during transition;
the final bound-byte check rejects it before record.

## B3 disposition: hash and consume the same no-follow byte buffer

`safe_bytes` walks absolute path components through directory descriptors using
`O_DIRECTORY|O_NOFOLLOW`; the final open uses `O_NOFOLLOW|O_NONBLOCK` and requires a
regular file. It reads once from that descriptor, checks size/inode/time metadata
stability during the read, and hashes the exact returned buffer. `bound` decodes
that same buffer, not another pathname read. Duplicate keys/nonfinite JSON remain
rejected. Symlinked parents/final components and FIFOs are rejected.

Checkpoint identity captures each config/model/README payload with its admitted
checkpoint hash. It preserves the native base, experiment, raw adapter-inventory
digest and shared optimizer/RNG hash conditions directly against those buffers.
Optimizer decoding is `torch.load(BytesIO(admitted_bytes), map_location='cpu',
weights_only=True)`. Safetensors decoding uses `safetensors.torch.load(bytes)`;
there is no path-based tensor reload. Config decoding likewise uses its admitted
bytes. Tensor/config/empty-optimizer invariants and valid retained RNG fields are
otherwise unchanged. COMMIT metadata must still equal the stream's checkpoint.

Deterministic replacement tests cover GO/JSON after admission but before decode,
optimizer pathname replacement immediately before Torch loading, model pathname
replacement immediately before safetensors loading, and config replacement
after capture. The current operation consumes only original admitted bytes; a
subsequent attempt to admit replaced bytes fails their pinned hash. The ordinary
true-mutation rejection tests remain green. Plan preparation also derives its
reference from the same decoded byte snapshot and checks the returned cohort
against a safely bound cohort read.

## CPU and actual preparation results

- Actual node4 CPU: **40 PASS, 0 skips/errors/failures**, CUDA uninitialized.
  `RECEIVING_CPU_candidate2.log`; exact receipt above. All mutation tests use
  temporary CPU fixtures. The production operation marker was **absent** after
  the suite, as recorded in `CPU.json`.
- Reproducible receiving command:
  `env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r165_frozen_boundary_recovery_20260917/candidate2/source /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r165_frozen_boundary_recovery_20260917/candidate2/test_recovery.py`
- Local stdlib command:
  `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_orch_r165_frozen_boundary_recovery -v`:
  **23 pass, 17 skipped locally** for missing Torch/safetensors; all 17 exercised
  on actual node4. Log `LOCAL_CPU_candidate2.log`.
- Unchanged legacy stream/native tests: **141 PASS**, log
  `LEGACY_CPU_candidate2.log`, same command recorded in the prior handoff.
- Actual read-only candidate2 `prepare`: PASS, no writer lock acquired, no live
  append. It retains the same original orphan sleep1 COMMIT and optimizer/RNG,
  original pending history/prefix, and `readout.status=NOT_STARTED`.

Please return a fresh verdict bound to these exact helper/test/receipt hashes.
Main has issued no boundary GO. Parent3693784, R162 service1389517, all original
states and failures remain untouched; no R163 or readmission work was advanced.
