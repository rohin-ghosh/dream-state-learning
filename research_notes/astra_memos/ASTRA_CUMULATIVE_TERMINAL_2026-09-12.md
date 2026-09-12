# SEQ-092 — cumulative reconstruction, assay dependence and NEW-cue spill

Executed and terminal, not a mechanism freeze or a sequential-learning gate.
Node3 GPU0 controller128957 ran September12 15:16:50.264833–16:06:04.227211UTC.
Six fresh workers completed; native reduction verified actual A1/AN/A2 adapter
trees and all cleanup receipts. Main verified complete GPU0 release at
16:07:39.725090UTC. No experiment or fitted adapter was rerun during capture.

## Comparison and observed outcomes

A1=Fit(base,OLD), AN=Fit(base,NEW), A2=Fit(base,OLD+NEW). These are fresh-base
fits, not A1 parameters surviving NEW-only updates, optimizer resumption or
catastrophic forgetting. Rank8, seed2, three epochs, chronological batch4,
max512; inherited OLD12924rows, NEW2048, union14972. The union preserves OLD
rows/order/encodings exactly but changes inter-epoch training history and
total dose. Corpus conditions are not compute-matched.

Values below are mean ON-minus-OFF target probability conditional on the
four colour candidates. OLD uses16 dose-16 owners; NEW uses32 owners. These
are cue/owner denominators, not independent learner replications.

| Adapter | OLD native fact gain | OLD frame gain | NEW frame gain | NEW bicycle-control gain | NEW frame minus bicycle gain |
|---|---:|---:|---:|---:|---:|
| A1 OLD only |0.292056|0.425674|0.005779|0.008963|-0.003184|
| AN NEW only |-0.004837|-0.020875|0.673276|0.713845|-0.040570|
| A2 OLD+NEW |0.341508|0.209910|0.359223|0.620610|-0.261387|

The existing native fact ratio A2/A1 is1.169323, whereas the OLD frame-gain
ratio is0.493124. Neither is retention of the old adapter's parameters.
Reporting only the native fact ratio would conceal the frame degradation.
The original primary JSON also emits large NEW pre-exposure ratios through
a generic contrast helper; those are not meaningful retention estimates and
are not promoted here. The separately frozen specificity supplement reports
absolute and paired gains without those ratios or any new pass threshold.

NEW-only learning raises target probability substantially, but raises it
even more on bicycle controls. In A2, mean NEW bicycle colour mass is0.997979
and abstention probability is2.576e-7; AN is0.999216 and3.452e-7. These are
not selective factual memories. OLD frame-binding and abstention gates fail
for every read; the native-assay G7 ratio alone passes when supplied for A2.
Native `memory_dose` gate labels are not the sprint's G0–G6 gates.

Repeated A1_before/A1_after raw cue scores match exactly, ON and OFF: maximum
raw probability drift0. This supports read/reload reproducibility within this
run, not arbitrary recovery, retention through updates, or learner-policy
improvement. No task generations occur in this assay.

## Interpretation and next decision

The recovered writer executes both larger fits, saves/reloads their artifacts
and produces reproducible scored outputs. Cumulative training reconstructs
some OLD and NEW associations, but assay-dependent OLD change and strong NEW
bicycle spill prevent qualification as selective memory. There is no new
G3/P1/G5/H1/H2 or mechanism-freeze claim. One training seed and one bank make
these exploratory mechanism diagnostics, not a robust population estimate.
Do not run an unchanged rank/dose sweep or declare the native fact ratio a
success certificate. The separately launched own-citation write and selected
bounded RuleGame integration address different links; their outcomes remain
pending. A true sequential warm-start test, retention/interference, and the
integrated parent-removal campaign remain unfinished.

## Measured costs and preserved evidence

Continuous reservation2953.833434seconds. NEW fit1536steps/199.4native-loop
seconds/171264input passes/165120supervised passes; union11229steps/1416.8loop
seconds/921249input passes/876333supervised passes. Total12765updates,
1092513input and1041453supervised passes. Fit-loop time1616.2seconds excludes
load/save. Four reads total965.251713scoring seconds,1160forward calls,
84800candidate sequences (including1792abstention sequences),3511832padded
forward input positions. These token units are distinct; no p50/p95, peak
VRAM, active-GPU compute or full-campaign throughput is inferred.

- Immutable source3ee4c706080e758537b4dc802bdeef4ead38a158.
- Manifest dc9f33071392c374da4e77c19b9c7f87de0bbe2ee2d4bc503c954c6078910f3d.
- Native report c641c3d3261b10539c934ecfe7828fe76eb12a6af6d99f48a9a7f45ba7321404.
- Terminal capsule c5a7649d14886ac86fdb966086fb08fe6440a6b766ba904a34ae20ec96266d9c.
- Capsule4,802,823bytes contains metadata, raw evaluations and logs, explicitly
  excluding fitted adapter directories. Actual weights remain in the native
  node3 run; original OLD archive/source provenance is in the durable handoff.
  Transfer SHA256 agrees on node3 and VM. This is not a standalone weight backup.
- Native report, specificity JSON, summary JSON/CSV/SVG and their scripts are
  archived under `receipts_20260912/astra_cumulative*` and
  `receipts_20260912/astra_summarize_cumulative_20260912.py`.

Capture's first helper compared in-memory integer dose keys with JSON string
keys and raised an AssertionError after successfully writing report.json.
The original report is preserved unchanged. A second CPU reduction to a new
file matches it exactly after JSON normalization, rechecks native weights and
cleanup, and records the correction in MAIN_TERMINAL_AUDIT.json. This was a
capture comparison bug, not an experimental failure or an extra GPU run.
Official model origin remains UNRESOLVED_LOCAL_HASHES_ONLY. Independent
scientific review of this new result is pending; formal C11 work stays deferred.
