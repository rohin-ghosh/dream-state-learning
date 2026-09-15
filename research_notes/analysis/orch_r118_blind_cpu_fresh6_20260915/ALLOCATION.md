# Remaining six inputs: repaired CPU annotation allocation

Main authorizes only the six inputs still never attempted after the original
unbatched run and the failed first batch. This is **not a retry or budget
refill**: four failed reservations plus six new reservations equal the ten
previously authorized slots. The six inputs represent nine member trajectories.

The installed tokenizer was checked on synthetic text: its default returns
`BatchEncoding`; explicit `return_dict=False` returns the exact same underlying
40 input IDs as a flat list. The repair validates this shape before claiming an
input. Native bfloat16 CPU smoke testing with a 22,816-parameter random Qwen2
model exercised prefill, cached decoding, variable left padding, independent
EOS and per-sequence caps, matching single-sequence results on that fixture.
This is not a pretrained-14B quality or bit-identity claim.

Bounds remain frozen Qwen-14B on CPU, 16 threads, zero CUDA/trainable weights,
parent calls or optimizer updates. Batches 4/2, at most 4096 tokens/input and
300 seconds/batch. Absolute deadline **September 15, 2026, 15:10 UTC** is
unchanged; no repeated dispatch of either predecessor's charged inputs.
All failed reservations, raw partial logs, and old annotations remain intact.

The two scheduled decode batches allow up to 600 seconds plus loading,
verification and bounded overhead; the absolute wall is authoritative.
PLAN SHA256:
`334eeaf9249c21d60a12ab4214ab99ee847787580e29fadd52570b40ea5d3de6`.
Source SHA256:
`84c7cc88c49dcf7170d9ca05f1eac30df04fed2bc6123d43ccf7558ea15c8399`.
Main's combined CPU suites passed 71 tests; the worker's native focused suite
passed 57 tests, separately from the actual tiny-model smoke receipt.

After publishing and transferring the exact `PUBLICATION.json`, execute on
ovx3 using `gpu/ovx3_ssh.sh`:

```bash
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r118_blind_cpu_source_20260915_fresh6_v2 /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r118_blind_cpu_batch run --root /localhome/local-rohing/orch_r118_blind_cpu_20260915_fresh6_attempt2
```

This allocation precedes actual launch. No GPU reallocation or live learner
change is authorized by it. No retained-learning or parenting-dependence result
is claimed. Batched and legacy annotations retain distinct decoder contracts.
