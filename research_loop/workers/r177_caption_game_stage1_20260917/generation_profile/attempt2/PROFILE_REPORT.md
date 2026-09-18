# R177 generation profile — attempt2 failed after first real generation; GPU6 released

This attempt is separate from preserved attempt1. It uses the repaired complete
16-byte CUDA UUID comparison, the same public frozen Qwen2.5-7B-Instruct revision
`a09a35458c702b33eeacc393d103063234e8bc28`, and an isolated seeded rank8 fixture.
No saved child state/adapter/caption/rating/evaluation reads, installs, live child
changes, lease changes or COORDINATION edits are authorized or planned.

## Final outcome for Main

**Attempt2 failed while saving its first trial, after one real generation. GPU6
is stopped and released for the C2 matched pilot. No retry was performed.**

The repaired exact 16-byte UUID check passed. Public frozen Qwen2.5-7B-Instruct
loaded, and the seeded rank8 fixture generated **256 actual tokens** from the
2048-token synthetic prompt, batch size1, first/cold-use case. The synthetic
journal preserved the target IDs in three identical records; those records are
three diagnostic writes of **one generation**, not three generation samples.
Their hashes, intent bindings and chain were checked before recovery.

The failure is an instrumentation bug, not an established model bottleneck:
`receipt(root, filename, **trial)` collided with the helper's former parameter
`name` because the trial payload also contains `name`. The measured HF-call,
CUDA-prefill/decode and stage timings were still in memory and **were not saved**.
Do not substitute a guessed generation-only duration or claim the full profiling
matrix succeeded. No warm sample, batch2, 12k case or sleep test completed.

### Recoverable observed rates — restricted denominators

| Evidence-backed quantity | Actual tokens | Observed wall | Token rate |
| --- | ---: | ---: | ---: |
| Model-load receipt to failure receipt | 256 | 12.824199 s | **19.962260 tok/s** |
| Run-start receipt to failure receipt, including loading | 256 | 31.945882 s | **8.013552 tok/s** |

These are **timestamp-window rates**, calculated from preserved remote
`time.time()` receipt timestamps and the actual generated target IDs. They are
not the lost synchronized `perf_counter` HF-call throughput. The post-load window
also includes remaining fixture setup, rendering, repeated diagnostic probes,
target encoding, three journal writes and error handling. The whole-run window
additionally includes imports, confinement/identity checks, provenance hashing
and model loading. Neither is a warm/steady-state per-life benchmark. With one
sequence, the per-life and aggregate rates over each named window coincide.

**>=40 tok/s per life remains unestablished.** The observed post-load diagnostic
window is below40; this alone cannot determine whether warm HF-only generation
could meet the target. No bottleneck attribution is justified by the lost stage
timings. Base load itself was separately persisted at2.269923 s and tokenizer
load at0.376392 s; these are load timings, not inference throughput.

### Stop/release and preserved evidence

- Run began September17 2026 at20:36:29.266 UTC; failed at20:37:01.211 UTC;
  service exited with code1 by20:37:02.389 UTC, without retry.
- At20:38:37.297 UTC, fresh root-owned release inspection showed **physical6 /
  minor5: 0 MiB, 0% utilization, no FD owners; MainPID=0 and empty ControlGroup**.
  The failed transient unit is a diagnostic record, not a running process.
- `GPU6_RELEASE.json` is the release receipt. No process other than this owned
  profile was stopped, signalled or modified; no child/pilot was launched.
- Original attempt1 and attempt2 executed sources/gates/receipts remain preserved.
  Working profiler now renames the helper's filename parameter; **18 CPU tests
  pass**, including the exact name-collision regression. This bookkeeping repair
  has no GPU revalidation and does not authorize another attempt.
- All remote actions used `gpu/a40r_ssh.sh`; no installs, lease extension, shared
  environment changes, live child writes or COORDINATION edits occurred.

The full requested cold/warm/stage matrix is incomplete. Main may use the safely
released GPU6 for C2; this worker performs no further GPU launch without a new
assignment.

User authorization, verbatim:

> Read blocked profile report: no throughput measured, clear. Authorize one NEW bounded≤20min attempt on node4 physical6 with repaired exact16-byte UUID comparison and updated CPU/provenance gate, all within existing hardware lease; fresh strict device+FD admission. Publish attempt2 separate artifacts, preserve attempt1. No installs/live child changes. Need real tok/s, then immediately releaseGPU6 for C2 matched pilot. New attempt is builder experiment authorized, no ratification waiting. Own profile files only; report launch + failure/success first.

## Historical Builder gate and launch

[Builder] 2026-09-17 20:36:09 UTC — 17 scoped CPU regressions passed against
attempt2's immutable source snapshot, locally and on node4. The installed-API
probe also executed the exact native generation/target-encoding functions with
an explicit CPU device proxy; CUDA remained uninitialized. Actual public
tokenizer inputs were confirmed to be exactly 2048 and 12288 tokens. None of
these CPU fixtures supplies throughput evidence. Attempt1 evidence verified
unchanged. Explicit new user authorization is copied into `BUILDER_GATE.json`.

Source-pins SHA256:
`631bbe15780573964bb646b2f007189426efd06a1edf365c4c451f240d0b9e7e`.
Builder-gate SHA256:
`879d032ebbcb32c06fd7ad46bce23c5dd4adab978e4a5fb4e7c10388efc94d61`.

**Launched September17 2026 at 20:36:29 UTC**, transient unit
`r177-caption-profile-1789677389`. Fresh root-owned capacity/FD/lease admission
passed. Actual strict confinement denied foreign minors 0,1,2,3,4,6,7 and allowed
physical6's minor5. At 20:36:33.955 UTC, the repaired complete 16-byte CUDA UUID
comparison passed. The observed display string is unprefixed, confirming the
attempt1 comparison's formatting problem. Public model provenance was recorded
and weight loading began. No throughput result yet at this status update.

The attempt ran under the recorded gate. Its configured wall was:
1100s service maximum (1040s internal alarm), one invocation with no retries.
Fresh privileged capacity/FD/lease admission and actual strict device confinement
are required before CUDA initialization; physical6 currently maps to minor5.
The runtime exits immediately after finite measurements or on failure.

## Measurement contract

- Actual cached HF generation; exact 2048/12288-token synthetic inputs, output
  caps 256/512, fixed seed and bfloat16/SDPA settings, singleton and batch2.
- EOS-inclusive actual token counts, per-life and aggregate HF-call throughput;
  excluded warmups, shape-first/warm samples, synchronized wall/CUDA event timing.
- Render/tokenizer, detokenize/hash, target encode, serialization and newly created
  synthetic journal timings. Diagnostic wall includes repeated instrumentation
  probes and is not a living-child wall or a long-history journal benchmark.
- Separate one-step synthetic LoRA sleep and composed generation-plus-step wall;
  not the actual anchored multi-presentation native sleep recipe.
- Batch2 shares one synthetic fixture, not independent-life adapters. >=40 tok/s
  per life is a target, not an assumption. No live speedup or causal learning claim.

## Receipt index

- `SOURCE_PINS.json`, `source/`, `BUILDER_GATE.json`: exact executed attempt2
  sources and the new authorization/CPU/provenance gate.
- `CPU_TESTS.json`, `CPU_TESTS_NODE4.log`, `CPU_COMPATIBILITY.json`: 17 original
  tests on both machines plus the CPU-only installed/native API checks.
- `attempt_receipts/`: original admission, launch, strict confinement, exact CUDA
  identity, public model hashes/load record, failure/exit and logs, plus only this
  fixture's new synthetic journal. No saved real-child artifacts are included.
- `RECOVERED_WINDOW_THROUGHPUT.json`: actual IDs' hash/count and the two explicitly
  named timestamp-window rates; missing HF/stage metrics remain null.
- `GPU6_RELEASE.json`: fresh no-owner/zero-memory/empty-cgroup release evidence.
- `CPU_ONLY_RECEIPT_REPAIR.json`: two-file bookkeeping repair hashes and 18 passing
  CPU tests; original executed code is unchanged and no GPU retry occurred.
- `RESULTS.json`: partial/failed outcome, distinct from complete throughput data.
- `EVIDENCE_MANIFEST.json`: SHA256 inventory of all attempt2 preserved files.

Receipts are exclusive, fsynced and read-only; logs and journal copies are frozen
locally and hash-bound. This is local evidence preservation, not external
notarization. No runtime acceleration was deployed and vLLM was not attempted.
