# R1 missing final readout: separately versioned supplement

2026-09-13. **DESIGN ONLY / EDITSTOP.** Main owns collection, verification and any later implementation/launch. No old root, source, helper, test or launcher was changed. No native/GPU/network/Git operation or live output was inspected. This is a project-involved recommendation from the full-dose executor author, not independent replication.

## Decision and evidence boundary

Recommend one new **`astra-q0-final-readout-supplement-v1`** run, in a wholly new output directory, evaluating **only R1/P_DERANGED/update128** from its saved adapter. No training, optimizer creation, fit continuation, replacement root, checkpoint selection, prompt changes or threshold changes. Use a fresh model process and the exact original prepared requests.

Main reports R1 is sealed/finalized `NONREPORTABLE_RUNTIME_ABORT`, GPU release verified, with both128 fits and nine successful stages preserved; `09_eval_P_DERANGED_128` failed at the15s GPU identity query before model load. These are supplied facts, **not raw facts reverified in this task**. Admission must bind Main's collected capsule/validation and check that specific failure chronology. Do not infer zero accuracy from the missing final readout or assume the other roots' outcomes.

The primary three-root experiment remains as originally executed, including R1's abort/missing endpoint. Supplemental results cannot turn its original report into a pass, satisfy its original deadline/barrier, or silently enter a three-complete-root primary table. Even successful recovery is **post-abort, separately executed diagnostic DEV evidence**, not a new independent root or clean/parenting/retention/H1/H2/P1/generalG3 result. Publication must retain both original status and supplementary status/time/provenance.

## Minimal implementation scope if separately authorized

One small new module plus focused CPU tests; no edits to `astra_pairwise_q0_fulldose.py`, its helpers, old source snapshot or root. Proposed commands: `prepare`, `execute --allow-gpu`, internal `worker`, `replay`. Reuse existing supervision/collection; do not create a launcher or general recovery framework. One authorized attempt, no automatic retry after another infrastructure or readout failure.

Use an immutable source copy containing the exact20 files expected by the original v2 `native_source_pins()`, plus the new module/tests pinned in the supplemental plan. Existing helper imports must resolve into that copy. The supervisor selects its own repository as worker cwd/PYTHONPATH, so stage the new module alongside the unchanged helpers, not just in an unrelated `/tmp` directory. Do not monkeypatch module globals or alter the live source tree.

## Required plan pins and admission

Main must supply actual hashes; none are invented here:

- Original capsule hash and Main's closed-custody/validation receipt hash; absolute original root or read-only verified extraction; original `manifest.json`, `PREPARED.json`, `prepared.json`, `STARTED.json`, `RESOURCE.json`, `SEAL.json`, `FINALIZED.json`, failure records and terminal report hash/status. Require valid finalized custody/release; reject a live, unsealed or unresolved-finalization root.
- Exact R1 allocation **identifier502/learner2**, version, campaign hash and original public model/tokenizer/environment binding. Require the failure to name stage09, the identity-query timeout, and the recorded query preceding model construction. Check absence of stage09 `LOAD.json`, `DONE.json` and readout events; absence alone is not proof without the code/trace chronology. If any generation occurred or the diagnosis differs, this narrow recovery recipe does not apply.
- Successful audit and fit receipt/DONE/event pins for both128 fits, with original128 steps and snapshots; receipt/load/job/cleanup joins. Bind the DERANGED128 adapter from the **failed job's `adapter` field**, and require equality with the successful DERANGED fit's snapshot128 binding. Expected path is `stages/06_fit_P_DERANGED/snapshots/128`; use the recorded binding, not a glob/latest-adapter search.
- Pin complete adapter tree hash, LoRA tensor digest, adapter config and every file's bytes (including weight/index/shard files if present). Bind source/prepared/fit/adapter chains and refuse symlink/path escapes or output/input overlap. Verify adapter hash again at point of loading and after use. Never save into or amend this directory.
- Pin original OFF/0 and AUTH/128 raw records and their successful receipt/load/cleanup chains if joined scoring is requested; optional earlier curves remain referenced historical evidence, not recaptured. Require each original resource counter and raw event inventory to agree for the consumed successful stages.
- Pin the **new** supplement module/tests, plan, request inventory digest, fresh output path, current GPU/node/driver reservation, model/tokenizer identities, runtime/cleanup/collection limits and no-retry policy. Keep original request IDs/material hashes; use an outer supplemental execution ID rather than changing prompts or pretending to be original stage09.

Old artifacts remain read-only. Recheck critical source/manifest/prepared/adapter pins on exit; keep all new logs, claims, events, release receipts, reduction and seal in the supplemental root. Do not create files beneath the original root or remove/replace its failure markers.

## Exact reusable interfaces

There is **no `native_eval` function** in pinned v2; the correct direct entry is:

```python
evaluate(model, prepared, state, snapshot, tokenizer, generate, budget, emit)
```

Call `evaluate(model, original_prepared, "P_DERANGED", 128, tokenizer, q0.native_generate, budget, emit)` exactly once, after a fresh frozen load. `emit` writes only to the new root. The interfaces below exist in the pinned file and need no modifications:

- `native_verify(old_root, *, check_files=True) -> (manifest, prepared, tokenizer)` is read-only preparation/source/input verification. It does **not** validate terminal success or authorize recovery; use the separately pinned closed-root validation as well. Reusing the same node/model paths/environment is simplest; a different machine requires new local binding plus preserved original evidence, not an inherited proof.
- `request_inventory(prepared, "P_DERANGED", 128)` yields exactly584 requests:288 natural-prefix records +296 generations. Preserve order, prompt IDs, common-prefix positions, EOS handling, greedy decoding,32-token cap and all panels. `validate_prepared`/`validate_record` remain unchanged.
- `historical_helpers() -> (diagnostic, supervisor, dependencies)` exposes `diagnostic.w0.load_hf_model(config, torch)`, `lora_tensors`, `tensor_digest`, `tree_hash`, `configure_torch(config, seed)` and `assert_gpu_idle(config)`. Seed2, same determinism flags/environment. Assert the fresh base has no adapters, then `PeftModel.from_pretrained(..., is_trainable=False, local_files_only=True)` on the pinned128 adapter; verify tree/tensor digests, set `requires_grad_(False)` and `eval()`. Do not invoke `fit_model`, `audit_native_model` (which expects fresh zero-B training initialization), an optimizer or `train_fit`.
- `native_forward_counter(model)` wraps that frozen evaluation; `native_generate(model, tokenizer, row, *, max_new_tokens, do_sample)` retains the existing exact generation implementation. Check actual natural forwards=288, model forwards=288+actual generated tokens. Maximum generated tokens=9,472; maximum model forwards=9,760. Zero new updates and zero training forwards are structural requirements.
- `supervisor.run_worker(command, *, log_path, timeout, device)` and `supervisor.gpu_processes_absent(device)` provide existing owned-group/GPU release receipts. Record the new controller/worker PID/start identity, parent linkage, command, plan/load/request/adapter pins and actual close/release. Refuse reduction to completed supplemental evidence before verified worker exit/release.
- `indexed_readout(prepared, records, state, snapshot, tokenizer)` checks completeness/raw decoding. `cell_gates(prepared, indexed, off, arm, PRODUCTION_POLICY)` and the original complementarity arithmetic can calculate a separately labeled joined DEV endpoint, without invoking an original terminal classifier.

**Do not call** old `native_worker(old_root, ...)`, `_native_execute`, or `native_reduce`/`native_replay` to append, resume, suppress the abort or promote combined evidence. The old reducer intentionally aborts when `FAILED.json` exists. Do not synthesize a timely original stage09 receipt or feed new timestamps into the original lifecycle as if its barrier completed. Read-only old replay may independently retain the old abort, but is not the supplement's reducer.

## The30s query change

Add one local `gpu_identity_30s(config)` in the **new module**, faithfully copying the small helper's query/parser/checks: hostname hash, exact selected UUID, one result row, A40 model name and pinned driver. Invoke the same argument vector `nvidia-smi -i UUID --query-gpu=uuid,name,driver_version --format=csv,noheader,nounits`, with `capture_output=True`, `text=True`, `check=True`, **`timeout=30`**, once. Retain the actual result/query timing in the new receipt; timeout/nonzero exit/mismatch aborts without retry. Require30s remain within the worker budget before starting it.

No replacement of `w0.gpu_identity`, generic subprocess wrapper, timeout disabling or mutation of15s literals in historical files. Do not then inadvertently call old `gpu_identity` on the supplemental load path. The original `assert_gpu_idle` is a **different**15s query and is unchanged; it can still fail closed. Existing supervisor release query already uses30s. This repairs only the identified identity-query timeout and promises neither infrastructure stability nor efficacy.

## Budget and scoring separation

Prospective bound: **3,600s total supplemental controller window**, inclusive of verification, worker, cleanup and durable supplemental publication; worker deadline is controller deadline minus existing45s cleanup reserve. Use `q0.Budget(new_start, min(new_start + 3600, lease_cutoff), clock=time.time)` and a correspondingly earlier worker deadline: its internal10,800s ceiling does not expand the supplied3,600s deadline. Also enforce controller elapsed monotonic time. No old start/deadline reuse or fitted work allocation.

Reserve a separate180s Main-controlled post-terminal replay/collection interval and preserve `lease_cutoff <= lease_end - 21600`. Require room for3,600+180 before launch. The one GPU identity call is bounded30s inside, not added outside, the worker limit. Same suitable reserved node2 GPU/model environment preferred; a GPU UUID change is explicit new execution metadata. No query or claim about currently free GPUs was made here. This conservative one-readout cap is proposed, not a measured completion guarantee.

Supplemental final status should distinguish `SUPPLEMENT_READOUT_COMPLETE` from `SUPPLEMENT_ABORT`, plus unchanged old `NONREPORTABLE_RUNTIME_ABORT`. Standalone complete readout requires all584 raw records, finite/decodable data, exact counters, valid adapter/source pins, timing and actual release. Endpoint pass/fail is a **separate field**, not completion status.

For optional joined scoring, validate original OFF/0 and AUTH/128 with `indexed_readout`, newly captured DERANGED/128 separately, then compute unchanged per-arm gates and exact/held correct complementary pairs and wrong-root opposites. Preserve denominator128 exact,64 held,96 locality and8 copy per cell. Label this a **post-abort joined diagnostic endpoint** with each cell's origin hash/time; report all component failures. Do not call it an original v2 pass, an additional root/seed, or a complete primary three-root result. No other root's OFF/AUTH/adapter can substitute. Gate outcomes must not control additional attempts.

## Focused missing CPU tests / patch boundary

1. Pin-chain admission: wrong root/allocation/version/source/plan/job/adapter/tensor digest, wrong snapshot32/64, unfinished256-step pair, unsealed/release-failed root, altered failure trace, or any existing stage09 load/readout reject before model callbacks. Test valid Main-verified aborted fixture without requiring its primary label to become success.
2. One fresh frozen load: correct saved128 adapter and seed2, no optimizer/backward/fit/save calls; unchanged request inventory and unchanged raw parsing/generation arguments. Test both greedy outputs and32-token truncation behavior with CPU fixtures.
3. Query mock asserts exact command and `timeout=30`, one call, same UUID/A40/driver/node checks; timeout/nonzero/malformed/mismatched result fails closed with no old15s identity call and no retry.
4. Mock supervisor checks new-root-only writes, PID/start/parent ownership,3600/45/180/21600 timing arithmetic, source/adapter pre/post pins, worker failure, missing/false cleanup, collection/finalization overrun and no relaunch. Hash the fixture old root before/after every path; attempts to write or invoke old worker fail the test.
5. Raw barrier: missing/duplicate/reordered-or-mismatched request identity, decode drift, nonfinite prefix, wrong adapter or counters and partial584 inventory cannot produce completion. Model-forward count equals288+actual token count; no training work.
6. Supplement replay is CPU/read-only and reproduces its own sealed report. Joined scoring retains old abort, unchanged thresholds and separate origins; cannot emit an original primary pass or substitute another root/cell. No full fit replay/retraining is required to test this new readout worker; original-fit custody/numerical verification remains a separately pinned input.

## Inspected source pins and limits

- `gpu/astra_pairwise_q0_fulldose.py`: `f63c77f9c371433442a204d6bd7bb10e3769a3bb709ae1d728648d765ee8ceca`.
- `organism_v6/multikey_writer_gateway_simple.py`: `b9fd33c7c11b2f57395f08d609bb1df004d9663eeefd143060bb1a24a34f10c8`.
- `organism_v6/run_reasoning_neutral.py`: `dd4f0a72cddc8226fa48ce50ab0faa6dd4e75f9db510aa89cfb5224898ee7496`.
- `organism_v6/writer_interface_calibration.py`: `9ab582ebc935ae36b88bd412fd06d799044661612f89a0770e46b92ab1b066c7`.

Only targeted source reads and SHA256 checks were performed. No terminal capsule/adapter hash was provided or invented; those exact admission pins remain Main's collection output. No tests or recovery code were run/authored. **EDITSTOP.**
