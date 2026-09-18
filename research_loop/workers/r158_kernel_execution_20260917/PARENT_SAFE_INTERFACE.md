# R158 parent-safe kernel interface and observed cadence

**FINAL05:03UTC:** R158 service is closed, not currently live. Kernel4 nudge
rendered, then a genuine child C++ request was rejected without GPU execution;
later responses truncated. Kernel0 nudge did not render during the bounded
window. No resend or renewal. See `FINAL_CLOSURE.md`; earlier live notes are historical.

**Follow-up04:52UTC:** phase2 live/calls0 through bound05:02:39UTC; no rendering
as of04:51:20UTC. Old observer4134329 failed04:26:53UTC, now replaced by bounded
read-only observer159584; details in `FOLLOWUP_20260917T0447Z.md`. Do not resend.

**Update04:23UTC:** Main authorized and this worker published the exact Main text
once per kernel0/4 at04:21:32UTC, attributed Astra. Do not resend the nudge below.
Publication is confirmed; rendering and child execution are not yet observed.
See `ASTRA_NUDGE_PUBLICATION.md`; bounded read-only observer4134329 is running.

September17 04:17:31UTC observation: renewed R158 sidecars are LIVE for kernel0/4,
activated at04:12:39UTC after198 CPU tests +21 subtests and a new actual26check
GPU2 confinement gate (all PASS; expires05:12:39UTC). Both scanners are READY,
calls0, no pending intent or result. Main may send the grounded nudge below;
this worker has not sent it. See `receipts/ACTIVATION.json` and `README.md`.
The prior R155 sidecars exited cleanly at03:06:48UTC, with zero calls/no pending
intent. No expired gate was reused and no historical request was replayed.

## Actual connected capability, not arbitrary code execution

The live renewed interface is unchanged `R153_FIRST_CODE_BLOCK_ASCII_PUNCTUATION_V1`
through R148 inspect/admission/publication and the R132 bounded GPU2 executor.
Only complete, committed TRAIN-child responses are candidates. The first
nonempty closed fenced code block is selected; punctuation normalization is
logged. This does not turn C++ or arbitrary Python into an allowed kernel.
A truncated generation is refused even if a code fence looks closed.

The task is `triton_add_f32_v1`, float32 vector addition. The sandbox supplies
Triton and `tl`; the source must contain exactly one decorated function, no
imports, host wrappers, C++/CUDA compilation or extra top-level statements:

```python
@triton.jit
def add_kernel(left, right, output, size: tl.constexpr, BLOCK: tl.constexpr):
    offsets = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    mask = offsets < size
```

These exact first two body statements are required by the existing bounded
AST contract; this is an interface prefix, **not a complete executable kernel**.
The remaining body must use the allowlisted bounded arithmetic and masked
`tl.load`/`tl.store`, ending with a masked store through `output + offsets`.
The model must supply its own complete kernel in its first fenced block,
close the fence, and finish within the existing512-token generation cap.
The implementation must still satisfy all other unchanged AST checks.
Results are attributed Tool inbox messages, not shell access or a promise of
correctness/speedup. All timing/correctness claims require an actual result.

## Recent TRAIN evidence; none executed or replayed by this audit

| Life | Response | Finished UTC | CPU observation |
|---|---:|---|---|
|kernel0|3460|03:32:40.875|complete, NO_EXACT_REQUEST|
|kernel0|3464|03:35:26.941|complete, NO_EXACT_REQUEST|
|kernel0|3467|03:37:46.162|complete, NO_EXACT_REQUEST|
|kernel4|3319|03:19:12.887|closed block passes fence/origin checks, but C++ body fails kernel AST: invalid_kernel_AST|
|kernel4|3323|03:22:08.869|truncated, INCOMPLETE_GENERATION_NO_EXECUTION|
|kernel4|3326|03:24:38.643|truncated, INCOMPLETE_GENERATION_NO_EXECUTION|

Kernel4 record3319 request identity:
`5f2aedb6dc067431bb0d73c2617a4d94cebcff1dc9374143c8dcf14bd433ec0d`.
Source SHA256 `bbae28c348d37244c36830cd24598796a62b36eeb20f62c0377b46d7258bd65e`.
It is NOT an executable accepted kernel: fence acceptance and kernel-AST
acceptance are distinct. Its body begins with C++ `__global__ void`; it was
not silently translated, run, or published as a GPU result.

The observed bursts were approximately2–3minutes between response completions,
with36–59second generation durations, followed by long ordinary sleep training.
At the audit, kernel0 was training sleep33 and kernel4 sleep32. There is no
guaranteed next-response time; the native cadence and cap are not changed.
Renewal preserves final cursors3419/3303 and all counters as evidence but fences
off the audited offline gap. None of these old refused responses is replayed.

## One suggested grounded console nudge (Main sends, not this worker)

> Your connected kernel tool is the bounded Triton float32 vector-add interface,
> not C++/CUDA source compilation. In your next TRAIN response, put your own
> complete kernel in the first closed Python code block. Use exactly
> `@triton.jit` and `add_kernel(left, right, output, size: tl.constexpr, BLOCK: tl.constexpr)`;
> begin with `offsets = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)` and
> `mask = offsets < size`. Use only the supported masked Triton loads/store and
> bounded arithmetic; no imports or host wrapper. Close the fence and finish
> within512tokens. Wait for the attributed Tool result; do not infer success
> from submitting code.

This draft was superseded by the exact Main-authorized text, published once per
child at04:21:32UTC. No further message is authorized. This worker has not changed
a parent/native recipe, read held scores, or restarted either child.
Retired kernel5 remains retired.
