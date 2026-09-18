# R177 generation throughput profile — blocked, one attempt preserved

Scope: standalone throughput instrumentation under Rohin170/171 and Main's
one finite physical6 assignment; no live runtime, child, judge, R179 or R166 edits.
This is an invariant-preserving Builder experiment/non-material instrumentation,
not an architecture, benchmark, acceptance-test or scientific-claim change.

## Result for Main

**No throughput result. No bottleneck established. The >=40 tokens/s per-life
target is untested, not failed or achieved.** The single permitted GPU attempt
stopped at `actual_CUDA_UUID` validation **before model loading, adapter creation,
prefill, or generation**. It produced zero generated tokens; a tokens/s estimate
would therefore be invalid. There were no retries or subsequent GPU model probes.

- Attempt: September17 2026, 20:09:53.805 UTC.
- Fresh privileged admission: 20:09:54.192 UTC; physical6 was empty, 46068 MiB
  total / 0 MiB used, 0% utilization, no compute process and no minor5 FD owner.
- Strict confinement verified: 20:09:54.355 UTC; actual `DevicePolicy=strict`,
  allowed GPU `/dev/nvidia5`, successful own-device open, denied opens of minors
  **0,1,2,3,4,6,7**. `ProtectSystem=strict` permitted writes only to the owned root.
- Run start: 20:09:54.343 UTC; failure: 20:09:58.932 UTC, **4.589 seconds** later.
  Service exited nonzero by 20:09:59.941 UTC. Maximum permitted service wall was
  1100 seconds (18m20s), not a new lease or a child launch.
- Post-stop check at 20:12:07.495 UTC: physical6 **0 MiB / 0%**, no minor5 FD
  owners, service `MainPID=0` and empty `ControlGroup`. The failed transient unit
  remains as a diagnostic record, not a running worker.
- Physical2/5 and other children were not written, signalled, stopped or launched.
  No shared environment or COORDINATION edits; all remote operations used
  `gpu/a40r_ssh.sh`. The original lease-authority metadata was read, not extended.

## Blocker and CPU-only repair

The executed source compared `str(properties.uuid)` directly with NVIDIA's
`GPU-...` string. That version did **not** preserve the observed UUID representation,
so the failure alone cannot prove either incorrect device assignment or the exact
format mismatch. Do not invent that missing observation.

CPU-only inspection identified the installed PyTorch commit as
`cf30153c4c131c8164ee7798e5022d810682e2cb`. Its primary source defines `_CUuuid`
with a read-only 16-byte vector and a separate display formatter. The working
profiler now compares the complete 16 bytes to the expected UUID, and records the
raw bytes, display string and normalized UUID before its decision. Wrong or
malformed UUIDs remain rejected. **This repair has not been GPU-revalidated.**

All **17 current CPU regressions pass**, including two identity regression tests.
The executed version had **15 passing tests**, on both the local machine and node4,
and a CPU-only installed-API compatibility probe. No CPU fixture timing is claimed
as model throughput. The original executed source snapshot, gate and receipts are
untouched; the repair's hashes/tests are separately bound in
`CPU_ONLY_REPAIR_TESTS.json`.

Do not reuse this consumed attempt or its old Builder gate to launch repaired
code. Further GPU work needs a new Main allocation/authorization, new source pins
and gate, and fresh admission. This handoff returns the short standalone slot.

## Observed source, not assumed bottleneck

The native `generate` method in `gpu/orch_r125_continual_native.py` already calls HF
`model.generate` with `use_cache=True`; the inspected method does not request
per-token logits/scores for logging. Its adapter hash is calculated on return.
The journal rescans existing records and publishes intent and record files.
These are candidate costs, not measured bottlenecks. There is no evidence here
supporting per-token logit logging as the cause of poor throughput.

## Implemented instrumentation (GPU measurements not reached)

- Only public Qwen2.5-7B-Instruct revision
  `a09a35458c702b33eeacc393d103063234e8bc28`, frozen bfloat16/SDPA, with a
  seed-created untrained rank8 LoRA fixture. No saved child adapters, state,
  captions, ratings, R176 or FINAL inputs. No model installation or vLLM changes.
- Inputs exactly 2048/12288 tokenizer tokens; output caps 256/512, actual
  generated tokens counted through EOS inclusive, padding excluded. HF batch1
  and batch2 share the same fixture; this is not multi-adapter-life batching.
- CUDA-event prefill/decode and synchronized generation wall; rendering with
  actual pinned TrainHistory, tokenizer, serialization, actual pinned journal,
  exact extracted native encode_own, and adapter-hash timing.
- HF call wall has the same timing boundary in both batch sizes. The separately
  reported singleton response-path wall includes native tokenization/decode/hash.
  Diagnostic end-to-end wall intentionally includes separately repeated stage
  probes and three real journal writes; it is **not** the living-child wall.
  Journals contain only new synthetic records at depths 0/1/2; they cannot establish
  long-history journal scaling or an old child's bottleneck. Batching amortizes
  one fixture across two sequences, not independently evolving life adapters.
- Shape-first and warm timings, excluded 8-token warmups. Shape-first is not
  process-cold or disk-cold. Separate model loading and full profile wall.
- One synthetic target-only optimizer step after all generation comparisons;
  report separately from generation and from their composed wall. This is not
  the actual native multi-presentation/anchor sleep or a living child's wall.
- Model-forward CUDA event times exclude sampling and other host-side work;
  prefill CUDA time is not whole-call time-to-first-token. Residual wall is not
  automatically attributed to one cause. Actual EOS-inclusive counts, not caps,
  determine per-life/aggregate rates. None of these GPU timings was reached.
- Strict systemd device cgroup plus actual foreign-minor open denials before
  CUDA; physical6's UUID currently maps to `/dev/nvidia5`, **not nvidia6**.
  Fresh privileged descriptor/capacity/lease admission; 1100-second service wall,
  one attempt, stop and preserve on any failure. No leases extended.

## Original pre-GPU gate (preserved)

[Builder] 2026-09-17 20:09:37 UTC — 15 scoped CPU/regression tests passed
locally against the immutable source snapshot and on node4, plus a CPU-only
installed Transformers5.5.3/PEFT0.20.0 batched generation/tokenizer compatibility
probe. CUDA remained uninitialized in that probe. Source/provenance gate passed.
Source-pins receipt SHA256:
`da8372c36186d93d1770912a51930a7df50255a2693034ed7ea3e126f85d3107`.
Builder-gate receipt SHA256:
`fd7418a71ab586ccf13717e1a59633278962f9ecafa3485a2e4bb6b671c1cdab`.
This line is intentionally here, **not COORDINATION.md**, per the exact write scope.

Fresh root-owned admission and actual device confinement passed on the original
attempt, followed by the separate CUDA-identity validation failure. Remote owned artifact root:
`/tmp/research_loop/workers/r177_caption_game_stage1_20260917/generation_profile/standalone_01`.
The existing lease authority is hash-bound, not extended; conservative hard end
is September18 18:00 UTC (11:00 PDT), well after this <=1100s standalone run.
CPU fixtures are correctness tests, not throughput. The requested >=40 tokens/s
per life remains a target, not a demonstrated result.

## Receipt index

- `SOURCE_PINS.json` and `source/`: original executed byte-pinned sources.
- `BUILDER_GATE.json`, `CPU_TESTS.json`, `CPU_COMPATIBILITY.json`: original
  dated Builder gate and pre-GPU correctness/provenance evidence.
- `attempt_receipts/`: admission, launch command, strict confinement, start,
  failure, service exit, and captured service/launcher logs.
- `POST_STOP.json`: fresh root-owned release/absence check, no GPU model call.
- `CPU_ONLY_REPAIR_TESTS.json`: current two-file repair hashes and 17 passing
  CPU tests, explicitly not permission for a second attempt.
- `PUBLIC_SOURCE_RECEIPTS.json`: public model revision and exact PyTorch source
  retrieval hashes; no external information was sent about child data.
- `RESULTS.json`: machine-readable blocked result; rates and bottleneck are null.
- `EVIDENCE_MANIFEST.json`: SHA256 inventory of the final local evidence bundle.

JSON receipts are created exclusively, fsynced and read-only; the final manifest
binds their bytes and log snapshots. This is local write-once evidence preservation,
not external notarization. Neither vLLM nor any installation/API migration was
attempted or claimed tested. No live runner speedup was deployed.
