# Two-habit root0 raw-result review — September 12, 2026

**PASS: both predeclared symmetric own-map gates, within receipt-level
verification limits. EDIT-STOP.** Only this note was written. No GPU,
network, Git, repository changes, or reruns. Independent inline parsing
recounted raw outputs; neither Main's analysis nor the native scorer was
executed to obtain these counts. Scorer source was inspected and hash-matched.

## Capsule and scoring evidence

Capsule `/tmp/astra_two_habit_terminal_20260912` and its adjacent `.tgz`:
SHA256 `9f1409c8a4bda08e2c8c0ec9ec0e60b6d695303baaa34f5ec100fa716b5eb824`.
All254 archive payload hashes, extracted file hashes and the exact file set
match `.tgz.validation.json`.

Run **R** is the capsule-relative
`astra_diagnostics/astra_fundamental_two_habit_20260912_attempt1/seed0`.
Sealed plan SHA256:
`af4988757fb01e93fe88e6f310c61656f26b2920d45c21561f6b035d208d11e9`.
Inherited H raw evidence is under
`/tmp/astra_fundamental_seed0_terminal_20260912/astra_fundamental_teaching_20260912_attempt1/readouts/teach`;
its complete file inventory equals the baseline bound in R's plan.

Recounted **96 new raw calls plus48 inherited-H calls**. Each panel contains
the same32 addition and16 memory IDs, not a selected subset. Both new panels
inherit H's exact prompts, rendered Qwen chat bytes and native input IDs;
temperature0, seed20260912, max64, one request per case. No extra/confirmation
calls occur. Request/response hashes, identities, capture inventories and
usage counts are consistent. Each panel has2131 input tokens; H has472 output
tokens, each new arm763. All output ID lists are present and within64 tokens.

Own-order success was parsed directly, requiring exactly three recognized,
unambiguous fields in the assigned order, source operands copied in their
original order, correct prediction and ACT sum, and PREDICT before ACT. Source
operands/sums were independently checked against `material/source_records.json`
and the actual question, not accepted from saved score rows. Opposite order
was checked symmetrically. Malformed outputs would not pass by merely failing
the other order. Memory normalization permits strip/lower and at most one
terminal period; tag spill searches INPUT/PREDICT/ACT, case-insensitively.

## Independent counts

Addition columns are out of32; memory columns are out of16.

| State | INPUT→PREDICT→ACT, source-correct | PREDICT→ACT→INPUT, source-correct | Old PREDICT habit | Correct ACT | Memory correct | Memory tag spill / invalid |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Inherited H | 0 | 0 | 32 | 32 | 4 | 0 / 0 |
| input_before | **32 own** | **0 opposite** | 32 | 32 | 4 | 0 / 0 |
| input_after | **0 opposite** | **32 own** | 32 | 32 | 4 | 0 / 0 |

Both descendants copy correct source operands on32/32 and have zero outputs
invalid for both registered three-field orders. H lacks INPUT by design;
its failure of those new orders is not an invalid original-task response.
Both arms'16 memory raw texts **and output-token vectors** equal H exactly:
literal `red` on all16. No memory acquisition is demonstrated.

Example from each panel's `calls/0000.response.json`:

```
H:             PREDICT: 24\nACT: 24
input_before:  INPUT: 5, 19\nPREDICT: 24\nACT: 24
input_after:   PREDICT: 24\nACT: 24\nINPUT: 5, 19
```

Raw new paths: `R/run/{input_before,input_after}/readout/run/data/calls/`.
The independent results agree with the saved reductions and symmetric
`two-habit-scores.json` counts.

**Why control-after legacy `joint=0` is expected:** the original
`fundamental_two_habit_corpus.py:252` scorer defines `joint` specifically as
INPUT before PREDICT before ACT. Its `form_b` also requires INPUT before ACT.
Neither is the after arm's assigned map. The hash-bound runner's
`score_orders` recognizes both orders directly and symmetrically; after earns
32 own successes and0 opposite, while retaining the old habit and arithmetic.
Do not interpret legacy joint0 as control failure or swap/reorder its output
before scoring. Conversely, invalid output rejecting both orders is not a
positive control result.

## Prospective gate — PASS

The notebook gate identified by Main as `e04638b5` is reproduced in the local
COORDINATION entry at19:37:38.864508 UTC, before launch19:37:55.603911 UTC:
both own≥28/32, opposite≤4/32, habit≥30/32, ACT≥31/32, memory spill increase≤1/16,
and validity loss≤.05 versus H. Both arms exceed every threshold; memory spill
and invalidity deltas are exactly zero. No Git lookup was performed to
independently authenticate the notebook revision label itself.

## Actual fit, source and dose — PASS

Both80-step fits directly warm-start from the **same ORIGINAL seed0 H**:
`astra_fundamental_teaching_20260912_attempt1/fit_teach/adapter`.
Original plan hash is
`d5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e`.
Original fit/supervision/readout provenance hashes match the local seed0
capsule. Fits execute sequentially, but **input_after is not initialized from
input_before**: both command lines, manifests and392-tensor source/initialized
state inventories bind H, each with cumulative steps80→160, not80→160→240.

Snapshot source is
`/localhome/local-rohing/astra_sources/d1e70002d12052f6b7357d42cf5997aa915e16f7`.
Inspected local corpus/scorer, teaching readout, teaching corpus and V3 trainer
bytes match their bound source hashes. The runner SHA matches
`d8983514e081be49c931f422143aeeee695498d9dc6547ac14e43d46034a2f60`;
the corpus/scorer SHA matches
`9f540446ca2e1c06aae2bda728d09f8bab955e0d969adf9484c9892594fa3527`.

Independently compared all80 material rows with actual original `teach.json`:
64 arithmetic targets are permutations of the same operand-bearing INPUT,
PREDICT and ACT lines;16 memory rows are unchanged. Prompt bytes, metadata,
source events, group IDs and source order match. Old PREDICT is explicitly
rehearsed, as are the original memory rows.

Both fit manifests: fixed LR1e-4, seed0, rank8/alpha16/dropout.05, four epochs,
batch4/gradaccum1, no packing,80 updates/microbatches,80 encoded rows, no skips,
no nonfinite batches and **zero truncation/context/target drops/splits**.
The configured `overflow=truncate` did not cause actual dropped tokens.
Each records a fresh optimizer with zero initial state entries/no restore,
one adapter, frozen base, loaded-state check and unchanged original-parent
inventory. All392 recorded LoRA tensors change after each fit.

Checked160 native training row receipts: input/label hashes, context mask-100,
response IDs, supervised EOS151645, equal per-row input/target counts between
arms, and max length≤512. Each epoch has5082 input/1477 target tokens; each fit
has20328 input/5908 target presentations. The recorded seed0 schedule has80
batch4 updates with each original group appearing four times. This is count
and line-multiset parity, **not identical target token sequences** after order
permutation. Final losses are0.06358442 before and0.06213207 after; these do
not themselves establish memory binding or conditional cognition.

## Costs and full release — PASS

All four worker supervision receipts report exit0, no error, empty owned
process groups and GPU-process absence/release. Both backend cleanup receipts
report closed. Terminal is COMPLETE with complete worker accounting and no
error, under its1200-second controller deadline with140-second cleanup reserve.

- Supervised worker total:381.280358 seconds.
- Whole controller including CPU/gaps/cleanup:537.610627 seconds.
- **Full Main reservation:799.928952 seconds =13.3321492 A40min**.

The full cost independently equals launch19:37:55.603911 to full-release
**19:51:15.532863 UTC, September12,2026**; it includes post-controller audit
waiting. It is below the30-A40min envelope. Do not charge only worker time.
`R/run/main_release.json` binds terminal/launch/XML hashes and controller
PID203151, reports controller absent and full release. GPU0 launch and release
XMLs match UUID `GPU-0ee6f753-c61e-e18a-8aea-acccd3042939` and both show0 MiB,
0% utilization and no GPU processes. This audits recorded release, not a new
live occupancy check.

## Limits and disposition

This supports **one-root authored convention coexistence with rehearsal and
symmetric order controllability**. It does not show INPUT causally informed
ACT, better arithmetic, unrehearsed retention, parenting, child sleep, H1/H2,
conditional cognition, memory success or broad generality. Two arms share one
parent;96 dev calls are not96 independent learners. Root0 passing ends this
tag-order sentinel; it is not authorization for another launch.

Native weights are omitted from the lightweight capsule: tensor equality,
change and base freezing were checked as consistent native receipts, not by
reloading tensors locally. Native detokenization is a successful recorded
audit, not rerun with a tokenizer here; raw input parity, output IDs/text
hashes, training masks and serialized captures were independently checked.
Formal model origin is not resolved by local identity hashes.

**EDIT-STOP.**
