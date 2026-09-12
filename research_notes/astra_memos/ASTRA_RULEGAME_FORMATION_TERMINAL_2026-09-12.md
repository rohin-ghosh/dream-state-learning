# SEQ-094 — interactive RuleGame formation stops before writing

September12,2026. Frozen v1 source
`aff89c4f034407120fc7badd064660492e0011cf`; node3GPU0 controller142838;
root `~/astra_diagnostics/astra_rulegame_minimum_20260912_attempt1`.
Started16:30:31.135163UTC. Native raw/world replay, actual input/output-token
consistency and owned cleanup pass; full process/CUDA/queue release observed
16:34:30.508825UTC. No adapter fit, readout or clean-lineage promotion.

## Results and stopping reasons

All eight pre/apply tasks terminate with protocol-invalid responses; none
produces a scored quiz. Their registered zero-filled quiz scores are all
zero, not eight demonstrated wrong quiz answers. Process has no apply TRY
execution and no record opportunity. Active-neutral has four apply TRY
executions and four record outputs, two faithful and two with wrong match
relations. First-two selection is P=0 versus A=2: **paired shortage** alone
forbids both fits, all new-rule readouts and replacement events.

Main additionally rejects the realized neutral-control interaction contract:
its first parent asks about quiz outcome and what was learned, and its second
asks to recount attempts, rather than requesting acknowledgment-only
restatement. Neither supplies a hidden-rule answer; this is not evidence of
sealed-data leakage. The first assumes a quiz outcome despite no valid quiz.
Process lesson1 falsely says no prediction was made: pre-call0008 contains
`PREDICT: T` plus a noncanonical TRY alias. Process messages have no hidden
answer, but their causal feedback quality is not certified. Raw turns and
restatements, including defects, remain unmodified. Native material status
is `MAIN_DECLINED_MATERIAL`; the independently computed shortage is preserved
in the formation capture. No corpora, fits or readouts were created.

## Localized interface failures, not parenting falsification

- Four invalid responses (0007/0008/0011/0022) use `TRY: a,b,c` rather than
  canonical `ACT: TRY a,b,c`. They contain an explicit prediction; the strict
  v1 parser correctly rejects its unrecognized action grammar.
- Four (0004/0016/0021/0031) emit multiple ACTs interleaved with invented
  `[OUTCOME]` continuations. The whole response is rejected; imagined outcomes
  are never executed or treated as observed material.
- Shared pre-task failures and control-content deviations make this a
  formation/interface diagnostic. It cannot identify persistent learning,
  parenting efficacy, P1/G5 or H1/H2. Zero process records do not establish
  that the parent reduces learning ability.

These observations justify one separately versioned communication repair,
not retrospective parsing, rescoring or an unchanged seed hunt. The selected
v2 specification is `ASTRA_RULEGAME_INTERACTION_V2_PROTOCOL_2026-09-12.md`.

## Costs and immutable receipts

32 responses:20wake,4parent,4restatement,4record. Actual native prompt/output
tokens11895/1446; P has12responses and A20, so actual cost is unequal. Sum
of recorded generation calls is42.209187seconds. Supervised worker window
including owned cleanup is169.633754seconds, excluding outer source/model
hashing, CPU preparation, Main audit and transfer; not active GPU compute.
The backend reports escalation to kill its one owned engine; supervisor
cleanup and full release pass. The semaphore shutdown warning stays in logs.

- Formation capsule `b13f6f77fd1b276d2d019e255c09aacbce85a29eaf95b6363c5cf3f276c9e0a4`.
- Native capture `a012dfd8f4a8b246329d407b415685780f1f21be352b3239bb30c953bd3e01ad`.
- Main audit `cdea111d87b1e06c2a9490e3c8d8528b3f0a8e55f89d0fbca54fe81215b3a0ac`.
- Subsequent material-decision capsule `763269cad71d480534d8f5414891ad01cba2bfe75989f84d736d0d91665a194d`.

Files are archived under `receipts_20260912/`. Official model-origin status
remains `UNRESOLVED_LOCAL_HASHES_ONLY`. Current resource ownership is separate
from inherited terminal results; no Main GPU reservation remains at this cut.
