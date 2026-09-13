# Offline LR analysis handoff

Prospective offline infrastructure only; no actual six-root results analyzed here.
Only Main performs one-shot native collection and supplies actual collection pins.

Run `python3 -B /tmp/astra_l2_lr_analyze_20260913.py --output NEW_OUTPUT.json`
with six repeated `--collection NAME PATH SHA256` arguments. Exact names:
`seed0_low`, `seed0_high`, `seed1_low`, `seed1_high`, `seed2_low`, `seed2_high`.
`--roster PATH` optionally relocates the roster but cannot change its hardcoded pin:
`2cf367e16116d205eb1e938d05d786d99309d4ae4df4d7afed66863d9d1f865b`.
Output creation is exclusive, never overwrite/retry into an existing output.

The native collector does not emit root paths: identity is bound by its exact
plan SHA256 to the unique root in the pinned roster, not by claiming direct
root observation. If a root field is present it must match. Complete and shortage
collections must provide the matching seeds and LR. Native abort collections omit
these fields: their identity is explicitly roster/plan-only, with no scored result.
Main's native-collection provenance remains necessary: file pins alone cannot
prove how a report was produced. This analyzer does not perform native or raw-byte
replay, read sealed roots, read corpora/models, or import the runtime.

Reports preserve every supplied baseline/first/second old/new panel, final paired
both/only/neither counts, formation, admissions, exposure, costs and work. Primary
values are final `(PROMOTE-SHADOW)/16` per seed/LR and paired high-minus-low.
Means and min/max ranges are emitted only when all three relevant learner values
exist; failures remain explicit and are never accuracy zero or silently dropped.
Shared first physical fit is counted once. Original seed0 is not a fourth learner.
Token, update, presentation, call and admission denominators are checked.

Losses, fit elapsed time and total controller elapsed time are not exported by
the collection API: output marks them unavailable, never zero or inferred.
Generation elapsed time and token counts remain present per supplied stage.
Per-root measured totals sum physical work, generation time/tokens, presentations,
training tokens and supervised tokens; aborted work is unknown, not zero.
First-report paired response intersections are not emitted by this API and cannot
be reconstructed from marginal scores; only final endpoint paired counts exist.

Interpretation is excluded DEV full-loop LR effect, not fixed-material quality,
clean ancestry, mechanism freeze, P1, parenting, H1/H2, or scientific-pass evidence.
No binary learning threshold or generalization claim is added.

CPU tests: `python3 -B /tmp/test_astra_l2_lr_analyze_20260913.py`.
Fixtures adapt the original collection example synthetically; test values are not
new experimental evidence. No repository changes, Git, GPU or network operations.
