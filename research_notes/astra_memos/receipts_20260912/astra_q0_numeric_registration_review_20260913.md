# Independent Q0 numerical-registration advisory

Reviewed 2026-09-13 02:02 UTC (2026-09-12 Pacific). Advisory concurrent verification, not a governance pause or native/scientific approval. Carver's files were not edited. Only the four permitted memos and two permitted source/test files were read from the repository. No experiment artifacts, formation/birth data, model, network, Git operation, or GPU was used. This report is the only file written.

## Registration assessment

**Main's prospective `safety=4`, `gradient_floor=1e-12`, and `arithmetic_middle_two` are compatible implementations of the closed contract's unfilled numerical choices.** They do not themselves relax acquisition, complement, locality, or four-prompt directional gates. This is compatibility, not a proof that every helper is numerically sound.

- Closure v2 at `research_notes/analysis/2026-09-12_q0_pairwise_falsifier_implementation_closure_v2.md:60` explicitly requires a registered floor and null cosine for zero/near-zero norms; at line 98 it requires `safety * gamma_(n-1) * abs_sum` and analogous observed-margin bounds. Neither passage chooses these constants.
- The adjudication's `1e-12` at `research_notes/analysis/2026-09-12_pairwise_binding_falsifier_adjudication.md:125` is the **R denominator**, not an earlier registration of the zero-norm floor. Main's explicit selection supplies the latter separately. `gpu/astra_pairwise_q0.py:443` correctly uses `<= floor`, null cosine if either norm is small, and the unchanged R denominator. `gpu/astra_pairwise_q0.py:459` retains strict `<.001`, `<.05`, and `>.999` degeneracy comparisons.
- `research_notes/analysis/2026-09-12_q0_pairwise_falsifier_mathematical_redteam.md:264` requests an explicit even median and mentions arithmetic-middle-two as usual. `gpu/astra_pairwise_q0.py:927` selects it; acquisition still uses strict positivity, not `>=0`, at lines 952 and 958. This affects exact class-gain medians as well as held key medians.
- `tests/test_astra_pairwise_q0.py:53` already supplies these three fixture values. `gpu/astra_pairwise_q0.py:341` still describes fixture parameters, and `gpu/astra_pairwise_q0.py:68` still lists them as unresolved in the binding documents. Preserve the distinction: record Main's prospective numerical registration with the implementation/policy hashes rather than claiming the old documents supplied it. CPU sealing already records policy bytes at `gpu/astra_pairwise_q0.py:1290`. No outcome-conditioned adjustment is justified by this audit.

## Findings and minimal repairs/tests

### 1. Reproduced: accepted derived-probability drift can change a closed gate

`gpu/astra_pairwise_q0.py:879` validates q/M approximately, but `gpu/astra_pairwise_q0.py:923` retains supplied scalars and `gpu/astra_pairwise_q0.py:983` gates them directly. Synthetic prefix records with identical logits `z0=z1=0`, normalizer `log(2)`, and M=1 accept both q=.5 and `nextafter(.5,+inf)`. With eight otherwise identical missing-mode rows and accepted OFF q=.45, the actual locality helper returns:

```text
q=.5:                 mean_abs_delta_q=0.04999999999999999 -> passed=True
q=nextafter(.5,+inf):  mean_abs_delta_q=0.0500000000000001  -> passed=False
```

This is a scalar-helper integrity ambiguity, not evidence of corrupted experiment data. **Minimal fix:** use one canonical reconstruction for gate-bearing derived fields in producer, validator, and reducer; a serialization tolerance must not leave multiple classification-bearing q/M values for the same primitives. Add an accepted-record one-ULP mutation test through validation and reduction, for both mean and tail gates. Keep scientific `.05`/`.10` cutoffs unchanged. Existing direct locality boundary tests at `tests/test_astra_pairwise_q0.py:615` do not exercise this validation/reduction interaction.

### 2. Reproduced scalar case; tensor round trip unrun: M reconstruction is shift-sensitive

`gpu/astra_pairwise_q0.py:835` forms M via an exponentiated difference of log-sum-exp values. The validator at line 888 instead adds two separately exponentiated differences. For the synthetic two-equal-branch record `z0=z1=1000`, `log_normalizer=1000+log(2)`, q=.5, M=1, validation raises `IntegrityError: raw q/M algebra`: its reconstructed mass is `1.000000000000055`. The corresponding zero-offset record passes. These are synthetic arithmetic inputs, not observed model logits; the Torch producer was not executed.

**Minimal fix/test:** add the actual `prefix_record -> validate_record` common-offset round-trip test, including negligible outside mass and legal mass near one. Share numerically stable q/M arithmetic with finding 1; do not merely widen scientific locality gates. This distinguishes numerical reconstruction failure from an actual integrity mismatch.

### 3. Static test gap: the named error-bound equality test does not test gate equality

`tests/test_astra_pairwise_q0.py:299` tests a comfortably positive dot, then Python's `bound > bound` and `nextafter(bound) > bound`, not `fp64_dot`/canary decisions at those boundaries. The implementation correctly spells strict comparisons at `gpu/astra_pairwise_q0.py:440` and `gpu/astra_pairwise_q0.py:678`, but the test would not detect their replacement by `>=`.

**Minimal tests:** exercise the actual projection and observed-change predicates at equality and immediately on either side, with all other quartet predicates passing. Cover cancellation, multiple tensor blocks, and singleton/zero dots. Extend `tests/test_astra_pairwise_q0.py:283` beyond 0 and 1e-13 to both P/V zero branches and representable norms bracketing 1e-12; test exact floor equality at the scalar classifier. An FP32 literal 1e-12 need not equal the Python floor exactly. Add nextafter-zero median cases through acquisition, not only the standalone median.

### 4. Narrow helper-domain limitations; not demonstrated native failures

- **Analytic/static:** `gpu/astra_pairwise_q0.py:426` accepts arbitrary FP64 operands, although its bound covers summation of exact products. For one product `(1+2^-27)*(1-2^-27)`, FP64 rounds the exact `1-2^-54` to 1 while the returned formula has `gamma_0=0`. Finite FP32 operands multiplied after FP64 conversion do not have this product-rounding problem. Thus this does **not** refute the registered FP32 directional-dot bound. Document/test that domain at directional call sites; do not advertise the helper as bounding arbitrary FP64 dot-product error. Any broader product-error support should be explicit, not a tuned safety multiplier. Head recomputation at `gpu/astra_pairwise_q0.py:620` also needs its operand-provenance assumption retained.
- **Reproduced, out of normal FP32-logit range:** `gpu/astra_pairwise_q0.py:927` accepts finite `[1e308,1e308]` and returns an infinite median. A finite-output check or overflow-safe arithmetic mean is a minimal helper repair; do not infer that native FP32-derived margins reach this range.
- **Static only:** `gpu/astra_pairwise_q0.py:392` checks payload values before FP32 conversion, not finiteness afterward; `gpu/astra_pairwise_q0.py:363` likewise checks logits before `.float()`. Finite out-of-range FP64 inputs can overflow on conversion. Add post-conversion checks/tests. Existing gradient/fit checks catch some downstream cases, so this is not a demonstrated full-reducer promotion bypass.

## Evidence and execution boundary

Only selected scalar helper definitions were executed from an in-memory AST of the allowed source, using synthetic inputs and standard-library dependencies. No module fixture/material loader, model constructor, or full test suite ran. `python` was unavailable; `python3` had no Torch. No dependencies were installed. Tensor bounds/autograd, native tokenizer/model binding, fresh workers, deadlines, cleanup, and native outputs remain **unverified**, not failed. `require_native_ready` at `gpu/astra_pairwise_q0.py:354` still raises; CPU replay explicitly returns `scientific_claim=False` at line 1313.

The source changed during earlier concurrent reading; the findings above are bound to the final snapshot below, which was unchanged across the successful scalar probes and final hash check. References are to that snapshot, not a claim about subsequent Carver edits.

```text
gpu/astra_pairwise_q0.py
a9acda4a8def14f67d2a3336a831b06ac63545d895cd9a8291d0fb4250db40d9
tests/test_astra_pairwise_q0.py
a61c156f9583e3ba418d6b789cace4d6335937d779aecc60d60088b539edf4d9
2026-09-12_pairwise_binding_falsifier_adjudication.md
254655bbeef0723811f44b2bbd166e783fc67b928c1a18e90470487ba73387e4
2026-09-12_q0_pairwise_falsifier_implementation_closure_v2.md
bc4987eb49a89d7246e63540f0305705850f606e8fdcf18cc9ef7f41ed3f96b5
2026-09-12_q0_pairwise_falsifier_mathematical_redteam.md
97cc7a18705939edcb57bd5601cb23d149629987e374091ec2f3c27333c71850
2026-09-12_q0_claim_bearing_implementation_preflight.md
8712a1561bbab4b3930558765f135296ec196087cfc25b7c1bc218d97846f2a9
```
