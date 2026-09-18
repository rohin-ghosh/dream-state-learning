# R177 attempt4 — actual timings saved; GPU6 released, partial matrix

## Final result for Main

**Eleven measured timing trials and three excluded warmups are saved. GPU6 is
released. None of the measured cases reached40 tok/s per life.** These are actual
synchronized HF-call timings, not attempt2's post-load timestamp-window estimate.

| Input tokens/life | Output cap | Phase | Batch | Actual outputs/life | HF wall (s) | Per-life tok/s | Aggregate tok/s |
| ---: | ---: | --- | ---: | --- | ---: | --- | ---: |
| 2048 | 256 | First-use | 1 | 256 | 12.775318 | 20.038641 | 20.038641 |
| 2048 | 256 | Warm | 1 | 256 | 11.039654 | **23.189133** | 23.189133 |
| 2048 | 512 | First-use | 1 | 289 | 12.394956 | 23.315937 | 23.315937 |
| 2048 | 512 | Warm | 1 | 289 | 12.390052 | 23.325165 | 23.325165 |
| 2048 | 256 | First-use | 2 | 256,256 | 13.208163 | 19.381953 each | 38.763906 |
| 2048 | 256 | Warm | 2 | 256,256 | 13.039124 | **19.633221 each** | **39.266441** |
| 2048 | 512 | First-use | 2 | 512,512 | 25.635089 | 19.972624 each | 39.945248 |
| 2048 | 512 | Warm | 2 | 512,512 | 25.680271 | 19.937485 each | 39.874969 |
| 12288 | 256 | First-use | 1 | 256 | 50.385777 | 5.080799 | 5.080799 |
| 12288 | 256 | Warm | 1 | 256 | 50.935459 | **5.025968** | 5.025968 |
| 12288 | 512 | First-use | 1 | 512 | 100.424991 | 5.098333 | 5.098333 |

Token counts are actual sampled IDs through EOS inclusive; inserted padding after
EOS is excluded. A pad-token ID genuinely sampled before EOS remains a generated
token under the unchanged native configuration. Output caps are not substituted
for actual counts: the singleton512-cap cases produced289 tokens. Batch2 shares
one fixture; per-life rates divide each sequence's tokens by whole-batch wall, not
its individually observed completion latency. Aggregate speed is not per-life speed.

## Evidence-backed bottleneck region

Warm256-output singleton comparison:

| Timing | 2048-token input | 12288-token input |
| --- | ---: | ---: |
| Synchronized HF-call wall | 11.039654 s | 50.935459 s |
| Prefill CUDA-stream interval | 0.333480 s | 2.162355 s |
| Decode-forward CUDA-stream intervals, summed | 9.012604 s | 9.388545 s |
| All model-forward intervals, summed | 9.346084 s | 11.550900 s |
| HF wall minus model-forward intervals | 1.693570 s | **39.384559 s** |
| Model-forward fraction of HF wall | 84.66% | **22.68%** |
| Diagnostic end-to-end wall, excluding sleep | 11.134458 s | 51.145456 s |

At12k, **most measured HF-call time lies outside the model-forward intervals**.
The extra context increased prefill time, but forward timings alone do not explain
the approximately40-second increase in HF-call wall. This narrows the problematic
region to HF generation work outside the instrumented model forwards; it does
**not** identify a particular logits processor, CPU operation, driver wait or
sampling implementation. At2k, the cached decode-forward region is the larger
measured component. CUDA event intervals can include stream idle/host-dispatch
gaps; they are not a pure GPU-busy or memory-bandwidth profile.

For the12k warm case, render including its token count was0.031783 s, the separate
tokenizer probe0.031968 s, target encoding0.037950 s, fixture hash0.025503 s,
serialization0.000272 s and three synthetic journal writes0.002490/0.003006/
0.003488 s. Those measured auxiliary stages do not account for the39.38 s HF
residual. Render includes a tokenizer call; do not treat its timing and the
separate tokenizer probe as disjoint parts of an uninstrumented live runner.

The inspected native generation already uses `model.generate(use_cache=True)`
without requesting retained per-token logits/scores. No evidence identifies
per-token logit logging as the culprit. No runtime optimization, alternate backend
or change to the model/benchmark was deployed or claimed tested.

## Completion boundary and release

The user requested completed actual timing trials followed by release. Once these
durable cases were available, only this owned profile unit was explicitly stopped
for handoff. **The full matrix is not complete:**12k warm512,12k batch2 and the
synthetic sleep step were not completed. A partially running generation is not
included in the table, output totals or rates. Sleep and complete-life wall are
therefore unmeasured; no projected sleep numbers are supplied.

`OPERATOR_RELEASE_REQUEST.json` records the stop decision. The existing SIGTERM
handler reports `TimeoutError: bounded_single_profile_deadline`, and the launcher
records a nonzero exit. Those raw receipts are preserved; here the reason was the
explicit early release request, **not expiration of the20-minute window** or a
claim that every planned case completed. No `COMPLETE.json` is fabricated.

At**September17 2026 21:04:53.561 UTC**, fresh root-owned inspection verified:

- Physical6 / exact expected UUID / minor5: **0 MiB,0% utilization, no FD owners**.
- Both owned attempt3 and4 units: **MainPID=0, empty ControlGroup**.
- Release occurred**962.561 seconds (16m02.561s)** into the shared20-minute window,
  before**21:08:51 UTC**. Exactly two additional attempts were used; none remain.
- No other child, shared environment, lease, model, benchmark or COORDINATION
  file was changed. No installs or GPU model inference followed the stop.

`GPU6_RELEASE.json` is the release receipt for Main's C2 matched pilot. Attempt1,
attempt2 and attempt3 source snapshots and evidence remain preserved separately.

## Measurement limits

This is a public frozen Qwen2.5-7B-Instruct, untrained seed-created rank8 synthetic
fixture, not a saved child or caption benchmark. The fixed revision, source hashes,
bfloat16/SDPA settings, seed, decoder, admission and strict device proof are bound
in the preserved receipts. No40 tok/s claim extends to untested configurations.
First-use means first use of that shape/cap in this process, not disk-cold or an
independent process for every case. Three warmup cases capped at8 tokens per
sequence are excluded from reported rates. Cold/warm cases are not statistical
replications of learning lives.

New journal depths0/1/2 cannot establish long-history journal scaling. Diagnostic
wall includes repeated probes and is not a living-child end-to-end wall. Batch2
does not demonstrate serving different evolving LoRA adapters concurrently.

## Historical authorization and repair

This is additional attempt2 of at most2, with the **same September17 2026
21:08:51 UTC absolute deadline**. No timer reset or additional GPU authorization
is inferred. Attempt3 has valid timing receipts and is preserved separately.

## Non-material bookkeeping repair

Attempt3 stopped on `padding_without_EOS_is_ambiguous` in output accounting.
The fixed HF recipe stops only at the configured EOS or output cap. The installed
HF sampling source initializes each sequence as unfinished, samples its next
token, inserts padding only for an already finished sequence, then updates the
stopping mask. Therefore a pad-token ID sampled before EOS—or in a no-EOS row
that reaches the cap—is an actual generated token, not inserted padding.

Counting now includes such IDs and still excludes everything after the first
configured EOS. The model, EOS/pad settings, generation configuration, stopping
rule, sampling seed, prompts, caps, timers and rate denominators are unchanged.
This restores the existing actual-token-count definition rather than changing it.
Two regression cases cover sampled-pad counting and actual post-EOS padding.

Primary installed `_sample` source SHA256:
`1d5f9f669d48681f85db509b8476203103d83764d550ec1a1a59b03641a57836`.
That inspection was CPU-only with CUDA uninitialized; no extra GPU model probe.

[Builder] September17 2026 UTC —22 scoped CPU regressions passed against the
fresh snapshot locally and on node4, including sampled-pad/post-EOS counting and
shared-deadline confinement. The CPU native API check passed without CUDA
initialization. `BUILDER_GATE.json` binds those results, the unchanged measurement
function/configuration AST and the remaining time in the original window.

Status: dispatching the final allowed attempt; strict admission is rechecked.
There is no fifth attempt or independent new20-minute budget under this authority.

## Preserved files

- `RESULTS.json`: all eleven measured rows and explicit partial-matrix status.
- `TOKEN_AND_RECEIPT_AUDIT.json`:5186 measured output tokens; all target digests,
  journal chains and HF denominators checked. Three copied records per case are
  not counted as three generations; warmups are excluded.
- `attempt_receipts/`: immutable launch/admission/identity/model-provenance data,
  fourteen trial receipts, this fixture's synthetic journals, and closed logs.
- `GPU6_RELEASE.json`: fresh no-owner/empty-cgroup/zero-memory release proof.
- `SOURCE_PINS.json`, `BUILDER_GATE.json`, CPU test/API receipts:22 pre-GPU
  regressions and the unchanged configuration with accounting-only repair.
- `EVIDENCE_MANIFEST.json`: SHA256 inventory of the preserved local bundle.

Receipts are exclusive, fsynced and read-only; journal/log copies are frozen and
hash-bound locally. This is evidence preservation, not external notarization.
