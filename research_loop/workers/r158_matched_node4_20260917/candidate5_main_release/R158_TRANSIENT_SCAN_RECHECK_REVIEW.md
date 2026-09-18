# R158 transient scanner rechecks — independent bounded review

## Verdict — September 17, 2026, 05:23 UTC

**APPROVE the bounded scan-reobservation logic at the exact two hashes below.**
No concrete admission-bypass or native-retry blocker was found. This approves
only additional observations by the existing scanner inside one supervisor
attempt. It is not GPU launch authority, approval of an observed clear GPU,
or a change to saved-initializer/capacity acceptance. The evidence/timing
limits below are part of this bounded disposition.

| Reviewed file | SHA-256 |
| --- | --- |
| `gpu/orch_r158_matched_node4.py` | `4e21fe3b72f823b9b26ba2edd08e8442ac68c3ea0fe3cdfea1590a2a5cd085d7` |
| `tests/test_orch_r158_matched_node4.py` | `9eaa615d76dd7475e5ab79cc3a82fe66234a55f8214050a21247d6ff64cbac3c` |

Both hashes were verified before and after CPU checks. Only this new report
was authored; no author source/tests, previous reports, coordination, staging
or live processes were modified. No scanner subprocess was actually run:
all review executions used synthetic subprocess results, temporary files,
empty CUDA visibility and disabled bytecode/pytest caches. No GPU/model calls
or hidden-data reads occurred. Main's reported process-drift refusal is
context, not an independently inspected live observation.

## Semantics checked

- The AST transformation replaces exactly one `subprocess.run(command, ...)`
  call inside `supervise`, adding only the owned attempt directory argument.
  It rejects an unexpected command variable, keyword set, or call count.
  The passing AST regression reverses that call substitution and requires
  the complete supervisor AST to equal the original. Existing node4 profile
  substitutions remain separate. Service Popen, native dispatch, one-shot
  attempt creation, failure handling and `check_admission` are unchanged.
- The wrapper requires the existing guard module's `scan --config` command,
  owned attempt path and positive numeric original timeout no greater than
  100 seconds. Every observation uses the same command/environment and a
  subprocess timeout equal to the remaining `min(original_timeout, 60)`
  monotonic budget. There are at most eight scanner invocations, with bounded
  0.25-second pauses and no new invocation once the remaining budget expires.
- A repeat requires a root scanner report, exact node4 host hash, target
  minor/UUID, `clear=false`, zero target memory and utilization, and no target
  compute process. Every blocking reason must be precisely a numeric
  `process_identity_drift:PID`, with one corresponding process record, explicit
  `target_device_open=false`, absent/empty/disabled CUDA visibility, and no
  compute-process entry for that PID on any GPU. Other drift labels, extra
  reasons, unknown/missing process data or target activity are not retried.
- This predicate is permission to **observe again**, not permission to clear
  the previous failure. It does not itself prove same UID/start tick or argv-
  only drift; the pinned scanner owns process classification. No previous
  failure reason or clear flag is edited. An error return, malformed JSON,
  exception/timeout, nontransient report, budget exhaustion or eighth refusal
  stops reobservation. Exceptions propagate; failed reports remain failed.
- The exact original subprocess result from the last observation is returned.
  A later full-clear report still passes through the original return-code,
  root/clear/no-reasons, host/UUID/minor and 120-second freshness checks before
  service dispatch. Freshness uses the original scan-start timestamp; rechecks
  do not reset it. Exhausted transient refusals cannot satisfy admission.

## Preservation and timing limits

Each completed observation's unmodified stdout is exclusively created under
`ADMISSION_OBSERVATIONS/NNN.stdout`, followed by a write-once receipt containing
its byte digest, command digest, return code and timestamps. The wrapper never
overwrites an earlier observation; re-entering the same wrapper/attempt fails
on the already-existing directory before another subprocess invocation.
Timeout/error receipts record `retried=false`; the unchanged outer supervisor
retains its timeout partial-output handling.

Two precise limitations, **not admission bypasses**:

1. Raw `.stdout` files are exclusive-created and hash-bound, but not chmod'd
   read-only or explicitly fsync'd by this wrapper. In the independent fixture
   they were mode **0644**, while JSON receipts were **0444** and fsync'd.
   Thus “immutable failed reports” means no overwrite through this path plus
   a recorded integrity digest, not OS-enforced immutability or guaranteed
   crash durability of every raw stdout file. Do not claim the stronger property.
2. The 60-second/original-timeout limit bounds scanner scheduling and subprocess
   timeouts. Configuration reads, receipt writing/fsync and OS overhead are
   not covered by a hard total-wrapper watchdog. The original admission
   freshness and experiment-wall checks still apply; do not present this as
   a hard wall-clock bound on all I/O or kernel scheduling.

## Independent CPU evidence

**122 passed, 1 skipped in 1.98 seconds**:

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/r136-pytest-support:$PWD python3 -B -m pytest -q -rs -p no:cacheprovider tests/test_orch_r158_matched_node4.py
```

The sole skip, line 259, requires the actual receiving staged source/original
recovery paths and is unrelated to this scanner change. The full helper run
includes the AST/scanner-byte, eight-refusal, fresh-clear, uncertain-report,
malformed-output, timeout, deadline and no-overwrite regressions. An earlier
nine-test selection is included in this run and is not additive.

Four additional independent synthetic wrapper probes passed:
immediate clear (one invocation), transient then scanner error (two), transient
then nontransient refusal (two), and a **10-second original timeout** exhausted
after the first refusal (one). They checked exact returned-result identity,
unchanged raw stdout, receipt hash joins, unchanged commands, and subprocess
timeouts no greater than the original 10 seconds. These are not extra pytest
passes or live scans. Main's 349-pass/one-receiving-skip broader result is
Main-reported; it was not redundantly rerun by this reviewer.

## Bound supporting context / exclusions

- Original supervisor: `gpu/orch_r151_matched_containment.py`, SHA-256
  `cbef4a98de3f230c8a50f4ec2d54b02200e6f835477bb39e8b9b60f24691bf70`.
- Original guard: `gpu/orch_r125_continual_guard.py`, SHA-256
  `4be0fd5ac06bf447e9ae425ad940efbd203a1d6c3cfb88ad8b4dec0db449bea3`.
  The passing staged-guard regression requires exact scanner AST preservation
  and original scanner dependency pins, not replacement scanner behavior.
- R150 recovery remains unchanged at
  `f8919b47e63c759d2a15a89eaaa1e28b4c16a7c1d4dcf0fd5efa320227e3fed9`;
  capacity callback remains unchanged at
  `bca194706e6f758f4384a70e0597d8357f583e3098456ef7b5f6832b8e69c075`.

Existing scanner reconciliation is not newly implemented or relaxed by this
wrapper. No permission to retry a native run, recreate a common initializer,
alter a failed admission, or infer scientific improvement follows. Changed
source bytes require a new bound disposition. This report's final whole-file
hash is emitted separately.
