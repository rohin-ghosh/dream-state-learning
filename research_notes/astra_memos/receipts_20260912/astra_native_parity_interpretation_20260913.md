# Native first-backward parity: bounded interpretation

September 13, 2026 — SEQ162 handoff. Read-only review of completed local
receipts and frozen source. No comparison command, scoring, tests, native
calls, repeat execution or frozen-source edits were performed in this review.
Only this document is new. Baseline drift remains unresolved; no cause inferred.

## Evidence checked

Mirror: `/tmp/astra_native_parity_evidence_20260913_attempt1/`.
Run directory: `additive_native_parity_seed0_20260913_attempt1/`.

- Main-supplied archive SHA256:
  `3fd33489a8c0f7eebe0566307f8404421628339e84a111642b3536a80feefad0`.
  Archive provenance is supplied by Main; this review did not re-extract or
  rehash the archive.
- Existing `comparison.json` bytes verified against
  `4e52301965fe1b2142fe46aac741cca0a6f64bcd45a45f7875616d79630f2120`.
- Plan bytes verified:
  `f81eef545ba86eb52b17d1a440d7f0783c6fb62290c3164184b855158d9b92d5`.
- OLD receipt verified against the existing comparison's binding:
  `24c5bbf31aa735e06ee8f27786dceb784afe6e271385934ba23ca01aef2386a0`.
- NEW receipt verified against the existing comparison's binding:
  `d4ad625def96bc6abc3b25c476f20ccf3c8ca99c4730775244fbc79f021ba44c`.
- All twelve phase files were individually checked against their receipt
  hashes. No new cross-path comparison output was generated.
- Mirrored probe and reviewed probe bytes both match
  `a331210a8f230c4ee3b5ff3cbe1fcef09a26925502fb9716c7e3ec617d914b7a`.
  Reviewed OLD trainer matches
  `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`;
  NEW additive trainer matches
  `3f2e73ef69b12c8db211e1d3043e4559713e036ffe09571ab8bc4c5199a426a0`.

Existing receipts show OLD PID147381 and NEW PID147989, both successful
first-backward interceptions with zero optimizer steps, adapter saves and
readouts; parents unchanged. Holder elapsed times are 53/54 seconds,
respectively; worker receipts report 52.135/53.052 seconds. NEW's recorded
`scratch/failure.json` is the expected deliberate interruption cleanup, not
an unsuccessful model operation; its step journal has the empty-file hash.

The already-executed comparison reports equal initial tensors, inputs,
settings, optimizer and environment, and equal RNG at all six phases. Both
first losses are **1.907779335975647**. The loss-tensor record is scalar
float32 on logical CUDA device 0 with data hash
`96bc30812c82320515cacf6683603aa2277944e01406682e9e9582d48f83db70`.
The comparison reports unequal gradients. Main's additional inventory count
is **256/392 gradient data hashes different**, with all associated
shape/dtype/device metadata equal; that count was not recomputed here.

## Observation placement: what is actually bracketed

The pinned probe's trace logic is at
`gpu/astra_additive_native_parity_probe.py:178`; observation logic begins
at `gpu/astra_additive_native_parity_probe.py:281`.

1. `before_init` is the call event of frozen `_warm_initialize`, AFTER the
   trainer's natural Python/torch seeding and fresh base loading.
   `after_init` is that function's return: exact parent-loaded trainable
   tensors are hashed. This does not hash every in-memory frozen-base tensor.
2. `before_forward` is immediately before OLD trainer line812
   `out = model(**t)` or NEW line214 `loss = model(**tensors).loss`.
   Actual token IDs, labels, attention mask, empty optimizer state and
   absence of preexisting gradients are checked. `after_forward` is the
   next line event: OLD reads `out.loss`, NEW reads assigned `loss`.
   Neither phase records logits, hidden activations or saved autograd tensors.
3. **`before_backward` precedes evaluation of the entire backward statement.**
   OLD line818 is `(loss / cfg.grad_accum).backward()` with grad_accum=1;
   NEW line216 is `loss.backward()`. The observer hashes the ORIGINAL `loss`
   in both cases, not OLD's subsequently created division result or its
   autograd edge. Thus the bracket includes that expression-level difference.
4. `after_backward` is the first subsequent line event: before OLD line819
   `micro += 1` or NEW line217 `losses.append(...)`. The observer checks
   finite/present gradients, absent frozen-base gradients and unchanged
   trainable parameters, hashes gradients, then tracing raises the deliberate
   stop BEFORE that next statement. No optimizer step occurs in the interval.
   CPU copies used to hash GPU tensors require their data to be available;
   these are materialized gradient bytes, not a hash of pending GPU handles.

## Narrow conclusion and exclusions

**First observed nonidentity is in the materialized gradients following the
first backward, despite equal recorded initial conditions, scalar loss and
RNG snapshots.** This establishes failure of bitwise first-gradient parity
for these two instrumented executions, before optimization. It does not
establish that the first underlying difference originated inside backward.

- Equal scalar loss is NOT equal logits, activations, saved tensors or graphs.
  Unobserved forward differences could become visible only in gradients.
- Equal RNG snapshots are NOT a trace of each random operation or each
  dropout mask. They do not establish identical checkpoint recomputation,
  operation-to-random-number assignment, scheduling or reduction ordering.
  Observer RNG checks exclude consumption by the observer itself, not all
  possible path-dependent numerical behavior.
- Recorded attention implementation is `sdpa`; checkpoint configuration
  includes `use_reentrant=False`. Deterministic algorithms are disabled;
  flash, memory-efficient and math SDP backends are enabled. These are
  configuration observations, NOT identification of the executing kernel,
  proof that an operation was nondeterministic, or causal attribution.
- OLD's divide-by-one expression is a concrete graph/execution seam within
  the observed bracket, but is NOT proven responsible. Neither it, bf16,
  checkpointing nor CUDA nondeterminism is isolated by this pair.
- Different tensor hashes show differing byte representations, not effect
  size, sign, number of differing elements or practical relevance. There are
  no raw gradient arrays here from which to estimate a norm/ULP difference.
  The 392 tensors are correlated components of ONE backward per path, not
  392 independent replications.
- Zero steps exclude an optimizer update as the source of THESE gradient
  differences. They say nothing about subsequent updates or explain the
  historical whole-fit/readout drift. Tracing/hashing perturbs execution,
  and this probe does not replay every historical process preamble.

## Would one fresh OLD-only repeat help?

**Yes, as a minimal within-path bitwise-repeatability diagnostic, not a
decisive OLD-versus-NEW causal test.** If Main elects it, predeclare one new
root and one fresh OLD worker using unchanged frozen source, source inputs,
base/parent, first occurrence, native recipe, instrumentation and device
binding. Preserve natural seeding; do not add deterministic flags, change
checkpoint/precision, normalize the backward expression, fit further, or
retry based on its result. Existing evidence remains immutable.

Interpret that ONE new OLD run against the first OLD, conditional on the
recorded initial/input/config/environment/RNG conditions matching:

| Possible result | Licensed interpretation |
| --- | --- |
| Gradients differ within OLD | OLD is not bitwise repeatable across these two instrumented processes under the recorded controls. A code-path change is not necessary for some gradient variation; an additional NEW-path effect remains possible. |
| Gradients match within OLD while the existing NEW differs | OLD repeated once; this strengthens the motivation to investigate a path-associated effect, but cannot exclude intermittent within-path variation, process/device-history effects or estimate their rate. |
| A recorded prerequisite differs, or the worker fails | Not a controlled within-path gradient repeat; preserve it as such, without rescue or automatic retry. |

Even a within-OLD difference does NOT by itself prove a specific nondeterministic
kernel: unrecorded process state and instrumentation remain alternatives.
A repeat matching NEW but not the first OLD would still be within-OLD
variation, not proof that NEW is correct or equivalent.

Implementation constraint for Main: the frozen `compare` CLI intentionally
requires OLD/NEW labels and equal plan hashes. A new-root plan has a different
hash, and an OLD/OLD pair is rejected. Do NOT relabel a receipt or overwrite
the old plan to make it pass. Any later within-path audit must be explicitly
identified as such and join the invariant source/input/recipe fields while
allowing the new root/process/plan identity. No such audit or repeat is
implemented/executed in this handoff.

SEQ162 wording: “Instrumented first-gradient nonidentity observed before any
optimizer update, with matching recorded initial conditions, loss and RNG;
within-path repeatability and the cause of historical baseline drift remain
unresolved.” No scientific pass or attribution.

EDITSTOP.
