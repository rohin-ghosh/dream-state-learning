# Bounded fresh-input CPU annotation allocation

September 15, 2026. Main authorizes the prepared `fresh10_attempt1` scope on
ovx3 CPU only: frozen Qwen2.5-14B, 16 threads, bfloat16, no CUDA initialization,
no trainable parameters, optimizer or parent calls. No GPU allocation changes.

Exactly 10 never-attempted inputs, representing 21 member trajectories, in
batches of 4/4/2. At most 4096 output tokens/input and 300 seconds/batch; absolute
deadline **15:10 UTC**, at most 3600 seconds from actual launch. No retries or
re-dispatch of prior charged inputs. All predecessor attempts and unresolved
outputs remain unchanged. Six unattempted rows duplicating prior charged inputs
remain excluded, not silently assigned cached labels.

The maximum scheduled decode time is three 300-second batches, plus model
loading, file verification and bounded overhead. This is an upper-bound plan,
not a measured completion-time guarantee. The hard wall remains authoritative.

The original judge's actual termination and process release are verified.
Legacy annotations are not inherited. Left-padded batched greedy CPU decoding
is explicitly **not assumed bit-identical** to the preceding unbatched run.
Every new result retains its decoder contract and exact member provenance.

Bound PLAN SHA256:
`b9f3884f784d4006395ac8ea0a2e35513347f7222cde700787eefb8c9280a329`.
Source manifest SHA256:
`9c3a1c8307b931c6b76905ec7f1b4992a85f37315a69fcf7adab1a5b970b512a`.
The worker reports 55 local and 55 native synthetic CPU tests; Main additionally
ran the 43 batch-specific standard-library tests successfully against the
published candidate. These tests are not a real-model execution receipt.

Node-local command, after publishing this allocation and transferring the exact
`PUBLICATION.json`:

```bash
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r118_blind_cpu_source_20260915_fresh10_v1 /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r118_blind_cpu_batch run --root /localhome/local-rohing/orch_r118_blind_cpu_20260915_fresh10_attempt1
```

Use `gpu/ovx3_ssh.sh`; raw annotations and token logs remain node-local. This
allocation is not a launch or result claim. Actual process/load/terminal
receipts will be published separately. It cannot establish retained learning
or parenting dependence by itself.
