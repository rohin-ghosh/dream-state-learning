# SEQ-125 — Q0 attempt1 nonreportable runtime abort

## Result and claim boundary

**NONREPORTABLE_RUNTIME_ABORT; scientific_claim=false.** Native final reduction
rejected exact forward/token accounting. The exception was preserved and
finalized correctly; a separate read-only native replay returned the identical
report, SHA256 `16bbed2a1cf6ed5be62fed186918cf855eaaf9e1ab134368c623ed21a7ed3f58`.
This is an instrumentation failure, not a scientific null or writer qualification.
Preliminary canary observations in progress messages are not promoted to a Q0
conclusion. No endogenous relay or confirmation run is released by this attempt.

## Localized defect

Raw DONE records contain the following **diagnostic, unvalidated** counters:

| Stage | Natural-prefix counter | Model-forward hook counter |
| --- | ---: | ---: |
| audit | 128 | 0 |
| OFF evaluation | 288 | 2353 |
| AUTH fit | 148 | 0 |
| DERANGED fit | 148 | 0 |
| unary fit | 148 | 0 |

OFF records296 generation calls and2065 generated tokens, whose sum with288
prefix calls agrees with its hook count. All PEFT-wrapped stages instead have
zero hook calls. The reducer correctly refuses to treat them as counted work.
The working diagnosis is hook placement on the underlying wrapper whose
`__call__` path PEFT can bypass by calling `forward` directly. Carver owns a
bounded instrumentation-only repair and real tiny-config CPU PEFT regression;
actual repair acceptance remains pending. Do not remove or loosen the reducer
check, alter scientific constants, relabel this seal, or restart this root.

## Custody and accounting

- Root: node3 `~/astra_diagnostics/astra_pairwise_Q0_root1_20260913_attempt1`.
- Prepared manifest SHA256:
  `2486bbc89e02fc3357eb285e19ac9172b3cf4ac1427097b4ad48b471e4cae207`.
- Final source SHA256:
  `596071780b961031ef8ef5e352898391df47038db70e2acb68b5c3dbe15c201b`.
- Controller298494; workers298807,299606,299983,300769,301424. All six
  processes independently verified absent; selectedGPU2 process query empty.
  Every worker cleanup receipt reports owned-group/GPU release verified.
- Start September13 02:42:18.510842UTC; controller resource elapsed1225.226543s;
  durable evidence completion1230.382598s, before the2700s cap. Post-terminal
  replay, collection and later vacancy observation are additional intervals,
  not hidden inside that controller duration. No Main or foreign kill occurred.
- Native SEAL SHA256:
  `91fb8f1acc63d089bac540dfd3f1ec8e620a02d167b393809cd3b5ae99084897`.
- Full capsule SHA256:
  `47baaccd5a2d877ca975309c2f135e6aa439408f560fa4d99fb413042aa8733a`.
  3,167,806,035 compressed bytes;16,101 files,3,544,561,078 regular-file bytes.
  Preserved on node3 `/tmp` and the VM under
  `gpu_artifacts_local/q0_20260913_attempt1/`; not placed in Git.
- Main's streaming custody checker verified all16,099 sealed file hashes plus
  seal/final-witness bindings. It did not deserialize tensors or independently
  validate science. Full native replay remains the separate authoritative check.
- Metadata-only capsule SHA256:
  `9f18b31352d2c78ad69013ec340eb2aa0c2f8ff07878f44d425f7eca8bbc5710`.
  Archived in receipts, explicitly excludes `tensors/`. It is an inspection
  index, **not** a standalone complete replay capsule. Full source/support
  capsule and all runtime metadata remain preserved.

## Next action

Repair only actual forward-hook coverage, preserving model, recipe, inputs,
initialization, counts, canary gates and legacy helpers. Prove the PEFT bypass
with a tiny configuration-only CPU fixture and verify OFF/ON generation and
gradient-bearing calls on the real installed native packages. Rerun complete
native CPU acceptance against final repaired bytes; then prepare a genuinely
new attempt with unchanged scientific allocation. The failed attempt remains
excluded and immutable. No C11 guard expansion or new scientific interpretation
is selected here.
