# Q0 prospective numerical implementation constants

Registered by Main on September13,02:01UTC before any execution of the new
pair-balanced Q0 executor. This is not a change to material, root orientation,
scientific thresholds, model, LoRA recipe or closed lifecycle. The binding
implementation-closure document requires a registered gradient floor and a
prospectively implemented analytic floating-point bound without giving all
implementation constants. Main selects these once, without new Q0 outcomes:

- FP64 analytic summation-bound safety multiplier:4.
- Finite gradient near-zero floor:1e-12, applied to the specified norm branch.
  It is not substituted into undefined cosine denominators.
- Even-count median: arithmetic mean of the two middle sorted values.

Rationale: the safety multiplier conservatively exceeds the first-order
summation bound; the floor supplies the explicitly required near-zero branch;
the median convention resolves an implementation ambiguity without changing
strict positivity or integer gates. These choices are not experimentally
optimized or claimed universally optimal. Equality and immediately adjacent
values need explicit regression tests; raw norms, bounds and margins remain
stored for audit. Numerical integrity failures remain distinct from reportable
scientific nulls under the closed contract.

Carver retains executor/test ownership. Its CPU helpers do not constitute a
native executor or scientific evidence: preparation, fresh model/optimizer
process lifecycle, runtime bounds, cleanup, raw replay and release accounting
must actually be implemented and verified before native promotion. Main handles
Git and actual native launches. Boole independently reviews this numerical
registration and pure-helper risks in parallel; this is not a new formal guard
or governance pause. Original historical Q0 input allowlist stays unchanged;
no later exploratory experiment data selects or tunes this Q0.
