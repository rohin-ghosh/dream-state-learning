# Q0 native lifecycle: bounded independent static advisory

Review date: 2026-09-13 UTC. Advisory concurrent verification, not a governance pause; Main retains operations and Carver retains implementation ownership. No repository files were changed. No tests, project-code execution, model/tokenizer loading, GPU, Git, network, or experiment-artifact reads occurred. Only the permitted Q0 source/memos and four pinned historical helper sources were inspected; static parsing and hashing are not runtime validation. Numerical constants remain frozen.

## Snapshot and ruling

Findings refer to `gpu/astra_pairwise_q0.py` SHA256:

```text
a58af68df8a29d2628c77b3ba48224f1306b8f3c24fb461b35fd5bb15eb33f3a
```

This snapshot was observed at 2026-09-13 02:21:27 UTC and rechecked in subsequent static reads. Carver was editing concurrently; this is not a verdict on later bytes. The concurrently observed test-file hash was `5b2e029df780fd914cbdb4ed69707cd5be3844ccbc93b2b99efeb5c007b77120`; no test outcome is asserted.

**Two concrete terminal-correctness bug cases remain, plus a controller-time accounting mismatch.** I did not identify a definite fresh-base/optimizer or snapshot-selection bug in the inspected construction path. That is a static observation, not native qualification.

The relevant closed requirements are fresh state and no restored optimizer, exact runtime accounting, nonreportable integrity failures, and replayable terminal evidence: `research_notes/analysis/2026-09-12_q0_claim_bearing_implementation_preflight.md:194`, `research_notes/analysis/2026-09-12_q0_claim_bearing_implementation_preflight.md:309`, and `research_notes/analysis/2026-09-12_q0_pairwise_falsifier_implementation_closure_v2.md:193`.

## Blocking terminal bug cases

### 1. Final raw validation/release failures bypass the failure finalizer

**References:** `gpu/astra_pairwise_q0.py:1853`, `gpu/astra_pairwise_q0.py:1856`, `gpu/astra_pairwise_q0.py:1866`, `gpu/astra_pairwise_q0.py:1944`.

The controller's `except BaseException` ends before the final GPU-release query, `native_reduce`, and inventory/seal work. A concrete case is a stage whose payload passes `Lifecycle.accept` but whose native counter record fails the separate exact-counter check in `native_reduce`. The controller has already appended that stage and may have run all subsequent stages. At final reduction, the counter `require` raises outside the catch; `RESOURCE.json`, `report.json`, and `SEAL.json` are never written. On an otherwise successful run, `FAILED.json` is absent too. Raw-event/hash validation errors take the same path. A final release-query exception also escapes rather than becoming a recorded release-unknown failure.

Adding a `FAILED.json` alone does not solve this: `native_reduce` validates completed stages before its failure branch at line 1949, so replay would encounter the same invalid raw record before returning an abort.

**Smallest repair:** include post-worker release verification and terminal raw reduction in the existing failure-finalization scope; use one deterministic nonreportable failure projection that can replay the rejected evidence without requiring that rejected stage to validate successfully. Preserve raw files and the rejection reason; do not reinterpret invalid records as scientific failures or continue/retry fitting. Do not report release as verified when the query itself failed. This repairs the existing terminal path, not process-guard architecture.

### 2. Deadline crossing during final writes leaves a sealed scientific report that cannot replay

**References:** `gpu/astra_pairwise_q0.py:1868`, `gpu/astra_pairwise_q0.py:1879`, `gpu/astra_pairwise_q0.py:1882`, `gpu/astra_pairwise_q0.py:1976`.

The last conversion to a nonreportable deadline result happens before writing and fsyncing `RESOURCE.json` and `report.json`. Suppose reduction/inventory finish just inside the root deadline, but those final writes cross it. `report` retains `scientific_claim=True`; `SEAL.json` records a later `finalized` timestamp. Immediate `native_replay` then rejects `seal['finalized'] >= deadline`. The run is left with an immutable scientific report/seal and a replay exception instead of the promised nonreportable terminal result. This follows directly from the control flow; no slow-I/O experiment was run.

Also, `finalized=time.time()` is evaluated before `write_once` finishes/fsyncs the seal, so it is not evidence of durable completion time.

**Smallest repair:** include terminal writes in deadline finalization and make a late finalization select the same replayable abort projection before committing the final terminal classification/seal. An after-the-fact replay exception is not that projection. Keep write-once raw stage evidence and the 2700-second ceiling unchanged; no additional scientific guard or parameter choice is needed.

## Controller-time accounting mismatch

**References:** `gpu/astra_pairwise_q0.py:1787`, `gpu/astra_pairwise_q0.py:1795`, `gpu/astra_pairwise_q0.py:1802`.

`_native_execute` performs fresh inventory checks, `native_verify` (including local snapshot hashing/tokenizer reconstruction), and hardware/idle queries before setting its wall/monotonic start. Those operations are part of the executing controller but are excluded from its reported elapsed time and 2700-second clock. A slow verification receives a fresh full budget afterward. This is distinct from separately authorized CPU preparation, and does not prove excess GPU compute time.

**Smallest repair:** start controller wall/monotonic accounting at execute entry; once the sealed configuration is read, bind the earlier lease cutoff and carry the same start through verification and workers. If reporting only post-verification runtime is intentional, it cannot be labeled the complete closed-contract controller wall time. No lease extension or changed ceiling is recommended.

## Paths that appear correctly connected, with limits

- **Fresh fits:** `gpu/astra_pairwise_q0.py:1690` invokes the extracted pinned `fit_model` separately in each worker. `organism_v6/semantic_writer_diagnostic.py:474` loads a new base, rejects preexisting LoRA, initializes the registered adapter, and creates an empty AdamW. `gpu/astra_pairwise_q0.py:1619` checks native inventory/recipe; the fit checks audit initialization and step-zero logits. No optimizer restore is present in this path.
- **OFF and snapshots:** `gpu/astra_pairwise_q0.py:1694` loads a fresh base for each eval; OFF attaches nothing. ON checks this run's snapshot tree hash, loads with `is_trainable=False`, verifies reloaded LoRA tensor digest, then freezes/evals the model. Snapshot bytes and tensor digest are captured at `gpu/astra_pairwise_q0.py:1730`. Strict generation delegates only to `organism_v6/writer_interface_calibration.py:236`, without assistant prefill. These are checks in source, not verified loaded bytes.
- **Model/source binding:** `gpu/astra_pairwise_q0.py:1513` compares local file inventories against Main's pinned public receipt. `native_verify` at line 1596 rechecks source, material, recipe, and input pins. The historical semantic diagnostic is AST-extracted for `fit_model`, not imported wholesale; no historical trainer/reducer is invoked by that extraction. No need to broaden scientific inputs was found.
- **Counters:** the current audit derives its initialization-logit digest from the same 128 audit forwards; it does not add a separate 128-forward pass. The final expected audit count of 128 is therefore not a static double-count bug. Actual hook coverage/generation counts were not executed. The independent native counter check must have the failure disposition described in finding 1.
- **Ownership limit:** Q0 checks controller-parent identity, GPU UUID/idle state, fresh load/process identities, serial receipts, and cleanup flags. However, it delegates timeout/kill/release behavior to pinned `organism_v6/run_reasoning_neutral.py` via `historical_helpers` at line 1450. That fifth source is outside this audit's four-helper read allowlist, so it was **not read**. The supervisor's return-value/PID contract, timeout duration including cleanup, and actual process-group termination remain unverified here. I do not assert a mismatch or request a new guard design on that basis.

An earlier snapshot's late-timeout fallback omitted counters and always chose the runtime-abort label. Carver's inspected final snapshot now preserves counters and distinguishes empty-stage precheck aborts at line 1874; that earlier schema mismatch is **not** an outstanding finding.

## Historical helper identity

All four read helper files matched the literal Q0 pins:

```text
gpu/astra_semantic_objective_probe.py
98a90f33dcd5582b9e32fe21d08dd29283c82b955ff350c8c994d2903b2f0d41
organism_v6/semantic_writer_diagnostic.py
d6ea45ac6bfb5cabe6cbd1224f4cf101e96cbd0e07c029e934c2aa3e03e1ddb0
organism_v6/multikey_writer_gateway_simple.py
b9fd33c7c11b2f57395f08d609bb1df004d9663eeefd143060bb1a24a34f10c8
organism_v6/writer_interface_calibration.py
9ab582ebc935ae36b88bd412fd06d799044661612f89a0770e46b92ab1b066c7
```

No native/result claim, experiment selection, or operational stop/launch is made by this review.
