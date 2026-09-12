# Bounded read-only validity audit — native cumulative replay

Date: 2026-09-12. Selected assay: **fresh-base cumulative replay**, not warm-start, inherited-state forgetting, or G3 closure.

## Verdict

**No demonstrated defect in the inspected preparation or execution path invalidates this selected assay.** OLD targets/order, NEW session-5 provenance, and delegation to the native scorer check out. There are two bounded findings: a missing NEW-control summary and a controller-death cleanup gap. Neither is evidence that the current run has failed, and neither warrants repeating or stopping this assay on the evidence available here.

This is not a scientific success verdict or a runtime-completion certificate. The local preparation contains no stage evaluations, fit receipts, or cleanup receipts. The supplied launch receipt records node 3, GPU 0, controller PID 128957, launch **2026-09-12 15:16:50.264833 UTC**, and `LAUNCHED_NOT_COMPLETED`. I did not query the live node.

## Scope and evidence identity

- Read source, tests, prepared JSON, native CPU-test log, launch source/receipt, and selected archive members using local read-only operations. No project-module execution, tests, preparation, scorer invocation, Git commands, GPU commands, process manipulation, or network actions. The only written artifact is this report.
- Source receipt identifies `/localhome/local-rohing/astra_sources/3ee4c706080e758537b4dc802bdeef4ead38a158`. Without accessing Git, I verified that all three current source-file SHA-256 values exactly equal the preparation manifest's source pins:
  - `gpu/astra_memory_cumulative_diagnostic.py`: `62e58de3fe27bd63b6d1b737bcc8071e95bce9cc343562aff7e5eb901b7cd112`
  - `organism_v6/memory_dose.py`: `ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3`
  - `organism_v6/run_reasoning_neutral.py`: `dd4f0a72cddc8226fa48ce50ab0faa6dd4e75f9db510aa89cfb5224898ee7496`
- Inspected test-file SHA-256: `e1bb2a7d75a512c86ef4dc4853f9515a69da35e549449cd309e047ad863341c6`. The existing native CPU log records 20 passing tests in 11.404 seconds; I did not repeat them. These are fixture tests even when executed in the native environment: see the test module's line 1, fixture tokenizer at line 22, and mocked forward instrumentation at line 168. Actual preparation provides the additional native-tokenizer evidence.
- Local preparation: `/tmp/astra_cumulative_prepared_20260912/astra_cumulative_20260912_attempt1`. Manifest SHA-256 is `dc9f33071392c374da4e77c19b9c7f87de0bbe2ee2d4bc503c954c6078910f3d`, matching launch; **all ten manifest-listed local files passed digest verification**. Its embedded root/model paths are native-node paths, not this local mirror; that is not corruption.
- The archive is at `/tmp/astra_cumulative_old_inputs_20260912.tgz`; the literal repository-relative `OLDarchive/tmp/...` path does not exist. I streamed members without extracting files. Archived bank0 OLD corpus hash is `f2388eaf9c2285d6c5fe109445a599a4fefb5d9b1ca0ce6223ef78bede01c37d`; bank0 hash is `87851da0b4229c1bed9523b653845873197866f5157031846e914d44dbf8fc31`, matching both hardcoded inputs and preparation.

## Findings and smallest fixes

### F1 — Medium, reporting/interpretation: NEW specificity controls disappear from the reduced summary

**Exact evidence:** `gpu/astra_memory_cumulative_diagnostic.py:151` creates paired `new_frame` and `new_bicycle` cues for each NEW owner; line 320 scores all of them natively, and line 328 preserves their OFF/ON results, including `p_abstain`. But line 495 selects only `new_frame` for NEW contrasts, line 497 truncates native summaries to the 1,313 OLD cues, and lines 503–507 build only car-frame NEW contrasts. Thus the 32 NEW bicycle controls have no summary in either `native_old_summaries` or `descriptive`. In addition, `memory_dose.py:3086` / line 3101 show that `cue_metrics`, used by `contrast`, does not carry `p_abstain` into per-owner contrast metrics.

**Impact:** This does **not** corrupt or omit raw measurements. It makes a reduced-report-only assertion of NEW car-specific binding unsupported: a hypothetical adapter that predicts each owner's car colour equally strongly for that owner's bicycle can show a strong NEW car contrast while its specificity failure is absent from the summary. OLD bicycle summaries are not a substitute for NEW-owner specificity. No claim is made that this failure has occurred in the running assay.

**Smallest fix:** For this run, interpret the already-selected `new_bicycle` OFF/ON rows alongside `new_frame`, including raw colour mass and `p_abstain`. A subsequent report-only change can expose paired NEW car/bicycle contrasts and abstention values from the saved evaluations. Preserve raw evidence and write a new report rather than replacing it. No new fits, cues, thresholds, or runs are needed. Bicycle suppression/abstention is a specificity diagnostic here, not evidence that the untrained bicycle negatives were explicitly learned.

### F2 — Medium, conditional lifecycle defect: the cap/cleanup depends on the controller remaining alive

**Exact evidence:** `organism_v6/run_reasoning_neutral.py:112` launches each worker with `start_new_session=True`; line 118 enforces its timeout only through the controller's `process.wait`. Cleanup is in that controller's `finally` at lines 121–134. Neither this supervisor nor the diagnostic installs a SIGTERM handler. In `gpu/astra_memory_cumulative_diagnostic.py:349`, line 356, and line 382, worker deadline checks occur before execution and after completion, not inside the long native training/scoring operations. The inspected launch script, `research_notes/astra_memos/receipts_20260912/astra_launch_cumulative_20260912.py:28`, detaches the controller and exits after writing its launch receipt; it supplies no independent deadline enforcer.

**Impact:** If the controller alone receives SIGTERM/SIGKILL or dies, a separately sessioned worker need not die with it. Python `finally` does not protect against default SIGTERM termination or SIGKILL. That worker can continue beyond the controller's timeout without a cleanup receipt; its own post-execution deadline check rejects late success but does not interrupt work. This is a real conditional gap in an unconditional hard-cap/cleanup interpretation, **not evidence of an orphan or overrun now**. A missing completion/cleanup chain remains unusable as a completed run; the reducer fails closed.

**Smallest fix:** Do not equate killing only the controller with verified GPU cleanup. For future lifecycle hardening, route catchable termination through owned-worker cleanup, and use a deadline-enforced worker-group/container supervisor if survival of controller death is required. A SIGTERM handler alone cannot cover SIGKILL. Do not mutate the immutable running source to address this audit; Main can handle any production integration separately.

## Checks with no selected-assay bug found

### Targets, encodings, order, and fresh-base lineage

`build_rows` at diagnostic line 104 retains OLD rows and appends NEW. Native `encode_item` at `memory_dose.py:2459` jointly tokenizes context plus target; native `train_hf` at line 2614 calls that same encoder, and lines 2638–2648 traverse in-order batches with shifted labels and masked padding. The diagnostic does not replace it with another trainer, shuffle, repad a corpus budget, mask away context, or load A1 as training initialization. At diagnostic line 365 both fits explicitly receive the frozen base path; native training constructs the base and a new LoRA adapter at `memory_dose.py:2620`.

Direct local JSON comparisons confirmed:

- A2's first 12,924 rows equal OLD exactly; its remaining 2,048 rows equal AN exactly.
- A2's OLD-prefix and NEW-suffix encoding-hash arrays equal the corresponding complete OLD/AN arrays.
- The prepared audit records no truncation or training boundary straddles. Preparation explicitly checks full-token labels at diagnostic line 122, original native identity at line 231, and OLD prefix encodings at line 240. I inspected these records and code; I did not retokenize.

| Corpus | Rows | Input tokens / epoch | Shifted supervised tokens / epoch | Steps, 3 epochs |
|---|---:|---:|---:|---:|
| OLD | 12,924 | 249,995 | 237,071 | 9,693 inherited |
| AN = NEW | 2,048 | 57,088 | 55,040 | 1,536 |
| A2 = OLD + NEW | 14,972 | 307,083 | 292,111 | 11,229 |

The OLD prefix length is divisible by batch size 4, so appending NEW does not change any OLD minibatch boundary. A2 replays OLD then NEW **each epoch**; it is not A1 warm-start followed by NEW. Later-epoch optimizer/adapter state necessarily differs from OLD-only fitting; that is part of this selected assay, not target corruption. Fit validation at diagnostic line 284 requires exact step/token totals and finite final loss, rejecting native skipped-step fits.

### NEW session-5 construction and cue provenance

Direct comparisons against the pinned bank found exactly 128 scheduled session-5 interference events, four events for each of 32 owners. Every prepared row's event ID, owner, and colour matches that source. Each event has copies 0–15 in order; the full sequence is sorted by session/order key/copy. All 2,048 NEW rows are session 5; none are session 6. Each owner has 64 rendered rows, and each colour (blue, green, red, white) has eight owners / 512 rows.

None of the 32 NEW owner IDs occurs either as an OLD row owner or anywhere in OLD context+target text. Thus NEW is not accidentally already trained in the supplied OLD corpus, including filler. OLD and A2 coloured-row marginals also remain balanced (2,368 and 2,880 per colour, respectively).

There are 32 `new_frame` and 32 `new_bicycle` cues. Every answer label matches the source owner. Example: `new_frame|J2R3` has prompt `Owner J2R3's car is` and source answer `red`; the paired bicycle cue does not reveal that answer either. Candidates preserve space-prefixed lower/title-case variants, all recorded as one token. `dose=4` is the source occurrence count, not the 64 rendered examples per owner.

All 1,313 OLD cue metadata records, including labels and candidate-token counts, exactly match the corresponding archived native evaluation after removing OFF/ON and preparation-only prompt/candidate fields. Cue IDs/order match too. The code uses the original native cue builder before appending NEW.

### Native scoring and measured cost

The instrumentation at diagnostic lines 297–334 wraps calls and delegates directly to `md.score_cues(..., lambdas=[1.0])`, restoring the original methods in `finally`. Native scoring at `memory_dose.py:2931` builds candidate lists and collapses results from the same cue dictionaries; alphabetizing JSON dictionary keys does not relabel probabilities because candidate flattening and collapsing use the same order. Native OFF disables the adapter; ON restores its native scale. `_forward_last` receives unchanged rows and `keep`, so the wrapper does not replace joint tokenization, left padding, attention/position IDs, or candidate scoring.

Per-read planned work is 1,377 cues, 2 passes, **20,752 colour/action candidate sequences + 448 abstention sequences**, and 3,202 scored prompt rows. Actual counters record candidate calls/rows, `_forward_last` calls/rows, and padded input tokens at that native boundary. They are not FLOPs, unique tokens, generation calls, or a count that equates all candidate sequences with full forwards. The native single-token fast path legitimately shares forwards.

The original archived native evaluation reports **512 scoring boundary straddles**, with chat-template and abstention checks passing. That is distinct from zero training straddles and is not by itself a regression; this wrapper deliberately retains the native joint-candidate scorer rather than changing its established treatment.

`reserved_gpu_seconds` includes controller verification, worker startup/load, fits, reads, and supervised cleanup. Native `train_meta.wall_seconds` starts after model/optimizer creation and ends before saving (`memory_dose.py:2634`, line 2696, line 2704); it is training-loop time, not full reservation cost. The hardcoded inherited 1,327.3 seconds / 9,693 steps matches the original archived A1 train metadata exactly. No new measured-runtime totals can be confirmed until native receipts arrive.

### Ordinary cleanup and result interpretation

With a live controller, the supervisor waits sequentially, terminates/kills the owned process group when needed, and checks the selected GPU's process table. The diagnostic reserves 45 seconds for cleanup, records elapsed reservation time even on ordinary exceptions, forbids retries via exclusive files/stage creation, and checks cap completion. Reduction requires six bound worker receipts, distinct worker PIDs, intact evaluations/adapters, and each cleanup receipt's owned-group-empty and GPU-absent evidence (diagnostic lines 458–489). This handles normal completion/timeouts; F2 is the separate controller-death case.

Use these read interpretations, without new acceptance criteria:

- **A1-before** establishes OLD signal and NEW pre-exposure behaviour; do not assume a positive control from its name alone.
- **AN** tests NEW-only learnability at the selected dose; OLD loss under AN is omission in a fresh fit, not forgetting an inherited A1 tensor state.
- **A2** tests joint availability after cumulative replay. Compare OLD with A1 and AN, and NEW with AN and A1, including F1's NEW specificity controls. No matched-compute claim is available: corpus sizes and update counts differ by design.
- **A1-after** is a fresh reload of unchanged A1. Its equality/drift check is a useful no-update control, not proof of training determinism or absence of all cross-model read differences.
- The reducer's native retention fraction uses held-out OLD **fact** gain (`per_dose[16].d_p`), not canonical-frame gain. That naming is correct. `contrast.retention_ratio` is also emitted for NEW acquisition contrasts and accepts any positive baseline (diagnostic line 455); a tiny or untrained baseline can make that descriptive ratio meaningless. Prefer the existing before/after effects and deltas; do not promote such a ratio to evidence of inherited memory retention.
- Candidate-normalized gains alone do not establish generated accuracy. Retain raw mass, specificity, abstention, and native failures. Missing NEW signal or read-control stability leaves the relevant interpretation inconclusive; nothing here closes H1/H2/G3 or changes the project's claims.

No C11/custody expansion, locality prerequisite, unchanged rank/dose sweep, extra native run, or canonical-integration work is requested by this audit.
