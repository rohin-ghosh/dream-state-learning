# SEQ-086 — equal-shape supplementary semantic scoring

Source `02a772f8376f431274699d121f691e80e5e6ea0e`; node3 GPU0,
controller110916, run `astra_semantic_rescore_20260912_attempt1`.
Five fresh OFF/adapter workers rescore832original requests. No new fitting,
data selection, generation or gate change.880original generated records are
explicitly reused. Old `d160e0b2` run remains unchanged and replayable.

## What changed

SEQ-084 identifies inconsistent BF16 logits at a shared prefix when full
candidate sequence lengths differ. Future-only EOSpadding now gives the
two forwards the same total length; original target labels are unchanged.
The scorer checks finite values, identical shared-prefix log distributions,
and combined complete-candidate mass no greater than one. All832requests
pass these checks. Native62CPUtests pass before launch.

This is fixed-shape teacher-forced scoring, not a direct measurement of
the dynamic-length greedy generator's sequence probabilities. The candidates
include LF+EOS whereas the earlier greedy outputs omit LF. Numeric agreement
is not an independent certification of semantic selectivity or backend
equivalence; the one-prompt FP32check is a diagnosis, not a full precision study.

## Supplementary results

| Root / map | Unchanged generation BA | Corrected mean conditional gain | Mean binary spill range |
|---|---:|---:|---:|
| 0 / W+ |37/64|1.078957|.280090..370003|
| 0 / W- |33/64|.951426|.373298..656300|
| 1 / W+ |32/64|.646593|.498690..616421|
| 1 / W- |34/64|.608320|.303592..350136|

The unchanged reducer label remains `OPTIMIZATION_INCONCLUSIVE`; binding
and spill still fail, interface passes. No threshold is lowered. The original
half-nat conjunction must not be retroactively rescued, and its prior
ceiling calculation belongs to the old score set, not automatically this one.

Post-hoc absolute-mass audit of the corrected report now completes. Its
three-category TV over the two terminated candidate strings plus all other
strings is .978273..998658 across cell/family means. This coarse statistic is
not full output-distribution TV or semantic action change; its scale is
dominated by near-unit candidate-format mass after training versus tiny OFF
mass. Directional valid/invalid changes are zero; generation action flips
remain a separate nonlocal-bias diagnostic. Do not infer selective memory from
a common format boost, or rely only on relative two-candidate probabilities.

## Verification and decision

Actual adapter/source/base identities checked; native supplementary reduction
repeats exactly; all five worker cleanup receipts pass, controller absent,
full GPU0release checked.347.467967seconds inside runner plus external
verification/release; no process killed. These checks repair this measurement
path, not G1–G3 readiness. Original W0 has equal candidate lengths already;
memory-dose next-token and variable-length paths must be distinguished rather
than globally invalidated. Bounded blast-radius note retained.

Next selected diagnostic: exact-training-row generation plus repaired scores
using these existing four adapters, no new fit, to distinguish failure to
store the keyed mapping from failure to extract it in held forms. Predeclare
all128rows per state and retain failures; no likelihood-only promotion.

## Receipts

- Capsule `receipts_20260912/astra_semantic_rescore_terminal_20260912.tgz`:
  `7b2f6bc8642055889f5cd824a1bb7762b3b7938e9a644372e18846dec88aedf4`.
- Supplementary report inside capsule:
  `f066f98d19cd3801253d63b0cf0622b77865feabffddaf26c25baa96a32e18df`.
- Native CPU receipt `astra_rescore_native_cpu_20260912.log`:
  `b311f46dea6d8d7ce27601d6419146c3932c982e8809e46ce73cabc8759586c6`.
- Main capture/replay script and post-hoc absolute audit script/JSON are
  archived alongside the capsule. Original weights remain on node3.
