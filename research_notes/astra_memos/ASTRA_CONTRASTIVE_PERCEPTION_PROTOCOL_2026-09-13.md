# Contrastive perception material screen — 2026-09-13

Status: predeclared exploratory authored Level0/1 screen; no native fit yet.
Rohin message33 motivates teaching discrimination between similar observations.
This is a material hypothesis, not evidence that the writer is faultless and not
a change to exact child-authored SLEEP targets. Formal C11 guard remains deferred.

## Question, treatment and source contract

Does grouping the same source facts by field, with an explicit instruction to
attend to differences, improve held-out record discrimination over source-first
enumeration? Both arms expose the same selected and companion transcripts and
eight field-value cells, with the same original assistant target bytes, row
order and supervision. The contrast includes grouping and attention instruction;
it does not separately identify their effects. All contextual notes are masked
from loss; targets are the original sourced records plus native EOS.

Generator `astra_contrastive_perception_material_20260913.py` SHA256
`b3c7fa549fdade0866da51131f64fe067ad7cd3ce36187f67e4c56ac7fbe5c1d`.
Canonical material SHA256
`7f9045242e98dc05b85f814574a1eb87cacebf463af88dcca60729c4aa5ebd66`.
The archived generator, tests and handoff in `receipts_20260912` specify source
pins, factorial selection, opposite-observation companion pairing, templates,
filtering and deterministic held-out generation. Native preparation must rebuild
and verify that material, isolate training rows, validate tokenizer masks/EOS,
reject truncation, and report actual context/supervised-token costs.

## Conditions and budget

- Frozen official Qwen2.5-7B-Instruct; OFF and two fresh LoRA adapters.
- PLAIN and CONTRASTIVE: 12 rows each, rank8/alpha16/dropout.05, LR1e-4,
  4epochs, batch4, accumulation1, unpacked; 12updates and48presentations each.
- Same learner seed0 and ordering recipe, not a claim of identical stochastic
  trajectories when context lengths differ. No warm starts or adapter sharing.
- Fixed literal templates; no tokenizer-length search or parity gate. Report
  different context costs; do not claim equal compute or total-token exposure.
- Four panels of12calls per state: D1/D2, C-record and C-general. Total144calls,
  two fits/24updates; samplingseed0, temperature0, max192generatedtokens/call.
- D1/D2 render the same12 fresh situations in two held-out wrappers; they are
  24calls, not24independent situations. Only two fresh numeric triples and one
  learner seed. C-record is previously exposed DEV, explicitly not confirmation.
  C-general has six arithmetic and six exact-copy canaries, not broad capability.
- Planned node2, one freshly checked vacant GPU; controller2700seconds including
  cleanup, collection180seconds. Every stage remains finite. Exact paths, UUID,
  source/model/environment/plan pins and PID go in launch receipts. No launch if
  this cannot finish six hours before the verified lease end.

## Scoring and decision

Preserve raw outputs and truncation status; no schema repair. Report syntax,
schema and each source-field score separately alongside strict whole-record
counts. Training/evaluation proof fields never enter evaluation prompts. Scoring
occurs only after all raw captures close. OFF-correct canary regressions are
itemwise, not hidden by equal aggregate counts.

Predeclared screen: CONTRASTIVE at least20/24 held, at least9/12 in each wrapper,
at least4/24 better than each of PLAIN and OFF, no loss on any OFF-correct
canary, and all outputs complete. OFF at least21/24 is ceiling-limited, not
success. These are exploratory triage criteria, not a general learning gate.
Report paired wins/losses and every panel even when the screen fails.

If promising, next compare independent learner seeds and additional fresh
source families before any numbered scientific claim. If gains are syntax-only,
report interface practice rather than learned discrimination. If null, inspect
field errors, source selection and acquisition before increasing scale or
concluding that perception cannot be taught. No tuning on these held-out panels
is described as confirmation; later selected comparisons need fresh data.

This screen cannot establish parenting, child-generated material utility,
clean ancestry, mechanism freeze, P1, H1 or H2. It prepares a candidate behavior
for later child-authored learning experiments. Existing LR loops remain frozen.

## Execution interface

Main's prospective wrapper is `astra_contrastive_perception_run_20260913.py`:
`prepare --root ROOT --spec-path SPEC --spec-sha256 PIN --allow-native`, then
`controller --root ROOT --plan-sha256 PIN --allow-gpu`, and one terminal
`collect --root ROOT --plan-sha256 PIN --completion-sha256 PIN --out NEW_OUTPUT`.
Final accepted wrapper schema and concrete launch receipts govern exact flags;
this prospective interface is not a claim that a native run was executed.
