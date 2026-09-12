# Exact-training probe recovery recommendation — 2026-09-12

## Decision

**Prefer one Main-elected fresh, unchanged full root0 attempt if live evidence
supports a transient management-query failure.** Preserve attempt1 intact, keep
root1 running unchanged, use a new root0 output directory and new launch receipts,
and retain the existing 1,800-second root / at-most-900-second worker caps.
Do not resume in place, relabel the failed attempt as complete, splice OFF files
into a nominally fresh execution, or relax GPU identity validation.

If the same GPU-query timeout recurs, a separately reviewed, narrowly scoped
retry of that management query can be justified. It is not necessary to edit
the scorer, model loader, original d160 inputs, gates, or inference policy.
No code changes or launches were made for this recommendation.

## Evidence and limits of this review

Main reports root0 attempt1 failed with `subprocess.TimeoutExpired` from the
15-second `diagnostic.w0.gpu_identity()` query, before `r0_plus/LOAD.json`; OFF
completed 256 records, and both worker cleanup receipts passed. Root1 remains
running according to Main. Those terminal logs, OFF records, and cleanup receipts
were not present in the local paths inspected, so their contents are **reported
by Main**, not independently revalidated here. I did not query GPUs, processes,
remote files, or the network.

Read locally:
- `/tmp/astra_exact_train_launch_20260912.jsonl`: launch receipts, not completion
  evidence. Root0 started September 12, 2026 at 14:14:11.841212 UTC on device 0,
  UUID `GPU-0ee6f753-c61e-e18a-8aea-acccd3042939`; root1 started at
  14:14:22.572505 UTC on device 7. Both specify a 1,800-second execution cap.
- `/tmp/astra_launch_semantic_train_probe_20260912.py`: Main's two-root launcher.
  It checks fresh output/log paths and GPU availability before launch. These
  initial checks do not establish later GPU availability or query responsiveness.
- `/tmp/astra_exact_train_source_4465e537.tar.gz`: CPU-only byte comparison showed
  the probe, its tests, W0 helper and worker supervisor match current inspected
  files exactly. The launch receipt names native source directory
  `/localhome/local-rohing/astra_sources/4465e5374d50bc1843dd5802d053c0d10ece1ae2`.

## What the failure means

`gpu/astra_semantic_train_probe.py:161 worker()` performs:

1. `verify_probe()`; state/deadline and reserved UUID checks.
2. Exclusive state-directory creation.
3. `diagnostic.w0.gpu_identity(config)` at line 169.
4. Torch configuration, tokenizer loading, fresh base/adapter loading.
5. `LOAD.json` creation at line 175, then 128 generation/score pairs.

`organism_v6/multikey_writer_gateway_simple.py:1066 gpu_identity()` checks the
node hash, then runs `nvidia-smi` for the requested UUID/name/driver with a
15-second timeout. On success it requires one three-field row, the exact UUID,
an A40 name and the pinned driver version. A timeout does not satisfy or bypass
those identity checks.

Given the reported exception location, r0_plus did not reach Torch configuration
or the model load call. The absence of `LOAD.json` alone would not prove this
(the receipt is written after model loading); the traceback location plus the
source order is the decisive evidence. This is not a reported score-mass failure,
generation failure, OOM, or semantic result. It provides no evidence that the
OFF scores or adapters changed. It also does not by itself prove the GPU is
healthy, absent, hung, or incorrectly identified.

Possible transient GPU-management/driver response delays remain hypotheses.
Successful earlier availability queries and later cleanup queries, if verified,
would be consistent with an intermittent query problem, not a diagnosis of its
cause. One failure cannot establish recurrence. Main owns live investigation.

The inherited `run_reasoning_neutral.py:105 run_worker()` always attempts owned
process-group cleanup and records GPU process-table status. A nonzero worker exit
can surface as `CalledProcessError` in controller `FAILED.json`; the underlying
`TimeoutExpired` may only be in the state log. Preserve both levels. Cleanup
success is operational evidence, not permission to ignore a failed identity
check or a guarantee about future node/GPU health.

## Minimal recovery with unchanged code

1. Preserve attempt1 root0's `probe.json`, `requests.json`, `OFF/LOAD.json`,
   `OFF/records.jsonl`, `OFF/DONE.json`, failed r0_plus directory, both state logs,
   process/cleanup receipts, controller log, launch/native-preflight receipts and
   `FAILED.json`. Inventory/hash what exists; record missing artifacts as missing.
   Never synthesize `r0_plus/LOAD.json`, state completion or overall completion.
2. Main confirms the controller and its owned descendants are terminal and both
   cleanup receipts really bind this attempt, with `owned_group_empty`,
   `gpu_processes_absent`, `reservation_release_verified` true and no cleanup
   error. A prior cleanup receipt does not replace a fresh reservation/availability
   decision. Do not inspect or disturb root1's owned GPU or processes.
3. If Main elects a transient-failure retry, use the same immutable source,
   original root, row coverage, seeds, adapters, scorer, generation cap and
   protocol. Choose a fresh destination, for example
   `/localhome/local-rohing/astra_diagnostics/astra_semantic_exact_train_20260912_attempt2/root0`,
   and a fresh root0-only launch-log directory. Keep root1 attempt1 as its own job.
   A changed reserved GPU UUID, if necessary, must remain an explicit runtime
   override with fresh hardware validation and a receipt; it is not an identity
   fallback after failure.
4. Use the unchanged probe CLI with `--root-index 0`, `--timeout-seconds 1800`,
   the selected `--gpu-uuid`, matching `CUDA_VISIBLE_DEVICES`, and explicit
   `--allow-gpu`. Preserve the original launcher environment, including
   `CUBLAS_WORKSPACE_CONFIG=:4096:8` and offline flags. Do not rerun the existing
   two-root launcher verbatim: it hardcodes attempt1 and expects both roots and
   their log directories not to exist.
5. The new attempt recomputes OFF, plus and minus, each in a fresh worker/model.
   Consume only its own complete 768-record root0 result for that attempt's
   report. Keep failed-attempt OFF as additional preserved evidence, not as a
   baseline selected according to favorable scores. Link attempt2 to attempt1 by
   recovery reason and evidence hashes in Main's launch/protocol record.

`execute()` at line 319 requires a fresh output and starts all three states;
`worker()` exclusively creates its state directory; `collect_records()` at 306
requires all three completions. There is no resume/import interface. Removing
the failed directory, changing an old deadline, hand-invoking remaining workers
inside the failed attempt, deleting `FAILED.json`, or fabricating a merged
completion would bypass the supported lifecycle. Do not do so.

Cost accounting: full retry adds **384 generations + 384 scores**, with zero
fits. If attempt1 contained only the completed OFF state's inference, cumulative
root0 inference becomes **512 generations + 512 scores**, of which the failed
attempt accounts for 128 of each. Successful root0 reporting still has the
registered 384+384 denominator. Preserve both the extra compute and the fact that
the new 30-minute cap is a new attempt budget, not a concealed extension of the
old deadline. Root1 is neither restarted nor duplicated by this recommendation.

## Can the completed OFF state be reused?

**Scientifically potentially reusable; not a supported recovery in current code.**
Its exact requests do not depend on the output directory or deadline, so an
explicitly designed provenance-aware recovery could reuse a complete matching
OFF state. However, merely copying its directory does not make it a new fresh
OFF load, and `execute()` would still try to create/run OFF again.

Minimum validation before considering an import:
- Bind attempt1 source hashes, original manifest/seal/fit/model/tokenizer pins,
  root index and the full exact request set to the intended recovery.
- Verify OFF `LOAD.json` identifies OFF/no LoRA, the actual runtime UUID/config,
  and original source context; retain that receipt as historical, not rewrite it
  for a new GPU/deadline.
- Verify OFF `DONE.json` is for OFF, count 256, and its records hash matches;
  prove exactly one generate and one score for each index 0..127 with unique IDs.
- Validate each record's canonical request hash, root, operation, adapter fields,
  attempts=1 and finite nonnegative timing. Use the original native generation
  parser for token/EOS/validity checks and score accounting for finite values,
  complete targets and mass. Shared-prefix distributions are not in the raw
  record, so rely explicitly on the pinned repaired scorer execution rather than
  claiming to independently reconstruct that guard from stored scalar scores.
- Bind successful OFF cleanup and all imported file hashes. Declare imported
  versus newly executed records, source attempt, load identity and runtime GPU
  separately. If the runtime GPU differs, disclose the mixed execution provenance.

Such a recovery would newly execute **256 generations + 256 scores**, importing
128+128 OFF operations. It needs a small separate importer/controller/report
design and explicit protocol treatment of reuse; it must not pretend that three
fresh loads occurred in the recovery attempt. Since all rows/adapters already
exist and root0 is small, the unchanged full retry is the lower-complexity,
lower-provenance-risk choice now. Do not add reuse infrastructure preemptively.

## If GPU-query timeouts recur: narrowly bounded retry, not weaker validation

A prospective local repair can retry **only the identity-query transport timeout
before any model loading**, not a model/inference request. Suggested minimal
policy for Main's consideration:

- At most **two query attempts total** (one retry), each with the existing
  15-second limit and one fixed short delay, e.g. one second. Account for this
  inside both the existing worker cap and the root's remaining deadline; do not
  reset either deadline. Two 15-second query windows plus delay are a nominal
  31-second allowance, not an OS-level absolute wall-time guarantee.
- Retry only `subprocess.TimeoutExpired` from the exact expected `nvidia-smi`
  UUID/name/driver query. Preserve the first failure details and its attempt
  number/elapsed time. Ensure the timed-out query has been reaped and cleanup is
  understood before another is issued; do not accumulate concurrent queries.
- Call the same validator again with the same config. A later successful result
  must still pass exact node, UUID, A40-name and driver checks. Do not accept
  cached OFF hardware identity, partial stdout, numeric-device fallback, a
  broader device set, or missing fields as a substitute.
- Wrong node/UUID/name/driver, malformed output, nonzero command exit and other
  unexpected exceptions remain immediate failures. A second timeout or
  insufficient remaining time fails closed with the ordinary preserved failure
  and supervisor cleanup. No retry of finite/mass/shared-prefix failures,
  generation outputs or partially executed state inference.
- Add focused CPU mocks for timeout→valid success, timeout→timeout failure,
  timeout→identity mismatch failure, immediate mismatch/no retry, deadline
  exhaustion and exact attempt counts/receipt preservation. No blanket retry
  around `worker()` or `execute()`.

If implemented later, scope the wrapper to this probe's hardware-validation
boundary instead of changing the shared W0 validator or supervisor for all
assays. Freeze a new source snapshot and launch a new attempt. Do not hot-edit
the immutable 4465 source, especially while root1 still uses its pinned hashes.
Do not keep restarting indefinitely if live evidence suggests a persistent
management/driver problem; Main should resolve that operational condition first.

## Byte identities checked

| File in 4465 archive and current checkout | SHA256 (equal) |
|---|---|
| gpu/astra_semantic_train_probe.py | 04c729f1f8d74a5b0275907ae7b96d1d45e409857f02b1034a071258da1f7f0a |
| tests/test_semantic_train_probe.py | 59e241710bc998d719ebb02a9220f64cf20a0826b41fe10a7837cb019cf14409 |
| organism_v6/multikey_writer_gateway_simple.py | b9fd33c7c11b2f57395f08d609bb1df004d9663eeefd143060bb1a24a34f10c8 |
| organism_v6/run_reasoning_neutral.py | dd4f0a72cddc8226fa48ce50ab0faa6dd4e75f9db510aa89cfb5224898ee7496 |

No inference outcome, storage claim, retention claim, unseen-key claim, new
threshold, or retrospective pass follows from this recovery diagnosis.
