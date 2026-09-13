# Main — own-write outer controller API (early handoff)

2026-09-13: ownership limited to NEW `gpu/astra_pcfl_own_write_outer.py` and
`tests/test_astra_pcfl_own_write_outer.py`; no other repository edits or commits.
Canonical `ASTRA_PCFL_OWN_WRITE_SCOPE_2026-09-13.md` read. No GPU/remote/model
operations by this worker. Main owns allocation, detachment, launches,
collection and prelaunch current observations.

## Exact API being implemented

```python
controller(manifest_path, manifest_sha256, allocation_path, allocation_sha256,
           outer_dir, *, outer_sha256, stage, arm=None)
```

```bash
CUDA_VISIBLE_DEVICES='' /ABS/VENV/bin/python -B -m gpu.astra_pcfl_own_write_outer \
  --manifest /ABS/OWN_WRITE_ROOT/manifest.json --manifest-sha256 FILE_SHA256 \
  --allocation /ABS/allocation.json --allocation-sha256 FILE_SHA256 \
  --outer-sha256 OWN_WRITE_OUTER_SOURCE_FILE_SHA256 \
  --stage formation --outer /ABS/FRESH_OUTER
```

Main starts this command using its detached launcher; the controller never
self-relaunches. Stage is exactly `formation`, `fit`, or `readout`. `--arm`
is required only for readout, using existing command/readout arm names;
other stages reject an arm. No stage loop, retries, or foreground finalizer.

Allocation uses the existing `zero_fit_outer.validate_allocation` closed
schema, with `outer_sha256` set to this NEW controller's source hash, also
supplied independently on the command line. The command source must be the
actual imported `gpu/astra_pcfl_own_write_command.py` in the pinned sources.
Allocation Python must be a venv interpreter matching the manifest's runtime
Python identity; launch preserves the venv path rather than resolving it away.

The entry clock starts before a mandatory four-second delay, before resource
checks. Total budget <=1800 seconds, including delay/cold start/cleanup/release;
60 seconds reserved for cleanup and post-worker observations. Deadline is also
bounded by manifest expiry and lease end minus max(6 hours, allocation margin).
Preflight demands an explicitly empty controller CVD, current UID/boot,
matching UUID/index, empty selected-device GPU/CVD owners and matching queue.
No unreadable-process exception beyond the existing exact init-pair policy.

Worker argv is fixed: allocation Python, `-B -m gpu.astra_pcfl_own_write_command`,
stage, original absolute manifest path and independent FILE hash, plus arm only
for readout. Source root is the pinned actual command's repository root.

The existing command writes `formation/completed.json`, `fit/completed.json`,
or `readout_<ARM>/completed.json` (not a literal `stagecompleted.json`). Outer
will preserve that raw receipt as `stage_completed.json`, without rewriting
the stage. Fresh `collection.json` uses an own-write outer schema and status
`COMPLETED`/`FAILED`; CLI exits 0 only for COMPLETED. Unknown worker identity
is FAILED and is never guessed/killed. Only a spawned, verified isolated group
is passed to the existing `cleanup_owned` helper.

## EDIT STOP / final handoff — 2026-09-13 14:11:32 UTC

**Ready for Main's integration. Code/test edits stopped.** Controller is 208
lines. **All 21 focused CPU tests passed in 6.351 seconds**; no full helper
suite was repeated. CLI help and `git diff --check` passed. Tests used actual
harmless subprocess sessions and a temporary pip-free venv, with GPU/CVD
observations injected; no native model/GPU/remote operations occurred.

Frozen file SHA-256 values:

```text
7c3197444113b610a3073e731c3e899f7e79423e6e37005c0f21b0d43e954725  gpu/astra_pcfl_own_write_outer.py
57f77a505d7aac02f9414a2df934010375af41e37c6d0335355c4224a2100220  tests/test_astra_pcfl_own_write_outer.py
fdd29c64bc73b1602998e6509da9f6d3132b90f9a5d50dceb1ad20ce86128f19  reused gpu/astra_pcfl_zero_fit_outer.py
cc5a9ec055537b6cd847804ec2212f2666a46023803d542da2fe3a4d2c8f80dc  existing gpu/astra_pcfl_own_write_command.py
```

For native formation, Main supplied (not opened or independently verified by
this worker):

```text
manifest: /localhome/local-rohing/astra_diagnostics/pcfl_own_write_20260913_attempt1/manifest.json
manifest FILE SHA256: ca0212fbbb13ffe0cc0426d331f0b4b8ac8dda64fc9f23b7c808940cdd7aa3ee
--stage formation
--outer-sha256 7c3197444113b610a3073e731c3e899f7e79423e6e37005c0f21b0d43e954725
allocation.outer_sha256: 7c3197444113b610a3073e731c3e899f7e79423e6e37005c0f21b0d43e954725
```

Main chooses and independently pins the allocation and fresh outer path,
deploys the exact source, and starts the controller detached with empty CVD.
Use the early-handoff CLI above; no separate foreground finalization command
exists. Avoid foreground SSH polling during the completion window as Main
specified. **No generic sshd/unreadable-process skip was added.** Readout arms
are exactly the worker's `NO_WRITE_C0` and `AUTH_WRITE`; formation/fit forbid arm.

Outputs: raw `manifest.input.json`/`allocation.input.json`, `context.json`,
`binding.json` (actual controller identity, argv/source/deadlines), pre/post
queue/GPU/CVD observations, raw worker stdout/stderr, spawn/start/wait/release/
exit receipts including return signal and cleanup events, unchanged raw
`stage_completed.json` when available, original stage inventory, failure
details, and fresh own-write `collection.json`. Stage failure bytes stay in
their original stage directory. No original C0 release attestation is created.

`COMPLETED` requires zero return code, a valid stage-specific sealed completion
and exact stage inventory, verified owned-group release and successful current
post-worker observations, unchanged source/input pins and remaining deadline.
Failures produce `FAILED`; expired budgets permit failure recording only, not
additional stage/release work or a new execution budget. Unknown identity is
never killed; its live/null exit state is reported for Main to handle.

Focused test coverage: real successful formation/fit/readout-shaped harmless
children; exact argv/manifest/arm and offline environment binding; real
nonzero/signal/timeout exits; verified-group SIGTERM and 60-second cleanup
reserve; unknown/foreign identity refusal; failed/nonaffirmative cleanup;
post-GPU error still followed by one post-CVD check; unreadable post-CVD PID;
missing/failed/misbound/tampered stage receipts and inventory/symlink guards;
independent manifest/allocation/self hashes; source/scope/UUID/boot/UID/venv/
lease/expiry guards; actual queue drift; fresh-only outer/stage paths; and an
actual four-second wait inside the original 1800-second budget.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_astra_pcfl_own_write_outer.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m gpu.astra_pcfl_own_write_outer --help
```

No commits or unrelated repository edits; concurrent edits preserved. Only
the two assigned new files and this requested handoff were written. No direct
MainAPI messaging tool is exposed; this handoff is the completed interface notice.
