# Authored reflection/correction uptake — prospective bounded comparison

September 13, 2026, 05:10 UTC. Main implementation review and CPU/native-tokenizer
acceptance complete; no GPU launch or model outcomes inspected at this point.
Simple hygiene applies. This does not finish or enforce the final C11 guard.

## Question and limits

Does ordinary authored restatement practice, versus the same practice with a
public correction present during training, change the model's subsequent
unprompted choice of a source-supported recording procedure? This is a small,
exploratory level-1 data-production diagnostic, not closed-loop parenting,
teacher distillation, clean ancestry, a general competency gate or H1/H2 evidence.
It is independent of the writer full-dose comparisons and does not alter them.

The correction-present and correction-withdrawn conditions retain identical
public events, authored targets, order and explicit generic system message.
Before execution, both prompts were repaired symmetrically to ask:
“Summarize the selected public event and state a reusable recording procedure
in 2-3 sentences.” Neither asks to restate an absent parent message.
This construct repair is prospective, not outcome-based retuning.

## Frozen comparison

- Official frozen Qwen2.5-7B-Instruct revision
  `a09a35458c702b33eeacc393d103063234e8bc28`; all model files locally verified.
- Two cold fits: withdrawn and correction-present training, each learner seed0.
  No fitted perception adapter or old learner is used as an initializer.
- Same12 authored restatement TRAIN rows/targets; rank8, alpha16, dropout0.05,
  LR1e-4, four epochs, batch4, gradaccum1, AdamW, BF16, no packing.
  Exactly12 optimizer updates and48 row presentations per fit.
- Six fresh readouts: OFF, withdrawn-fit and present-fit, each under correction
  absent/present; each24 DEV calls:12 restatement plus12 application,144total.
- All application rows are DEV only. Both DEV panels are held out from fitting;
  source/event/template separation is checked before preparation. This DEV
  material is not a final confirmatory holdout or clean-founder corpus.
- Greedy readout, seed0, max192 output tokens, same LoRA-enabled engine; OFF has
  no adapter request. Separate processes load each selected adapter afresh.
- Single selected root on node3GPU0, up to3600controller seconds plus180collection
  seconds. Fits600s each/readouts300s each, clamped to remaining global budget.
  Cleanup uses only owned worker groups. No retry or replacement root is planned.

## Outcomes and decisions, fixed before launch

Primary diagnostic: strict bare-A/B application accuracy, correct/12 per cell,
with per-row paired flips for each fit versus OFF and present-fit versus
withdrawn-fit after correction removal. A net positive difference is a local
signal for replication, not an established treatment effect. No improvement,
syntax failure, or regression is preserved as an informative outcome.

Restatement exact-authored-string match is a secondary fixture metric, not
semantic prose accuracy. Keep raw prose for separately labeled descriptive
inspection; do not count truthful paraphrases as scientifically incorrect or
combine these two panels into one metric. Report syntax failures, output-length
finishes, costs, token exposures and all cells. No best-cell/checkpoint selection.
The small application set has residual option-reading/lexical shortcuts; it
tests near-transfer discrimination, not free production or useful sleep writes.
Selection of a follow-up uses this DEV evidence; any confirmatory claim needs
fresh material and at least three independent learner seeds, not144independent
observations. No automatic L2 or ancestry promotion follows a positive cell.

Abort only for integrity/numeric/resource/ownership/deadline failures; wrong or
malformed model outputs remain results. Collect only after all144captures,
eight stage receipts and releases close; partial panels are not scored as zeros.
Preserve failed roots and logs. Live-parent removal here means only withdrawal
of a static public paragraph, not the final developmental adult-removal design.

## Acceptance and custody

Independent CPU acceptance102tests, zero failures/errors/skips,10.190s; exact
commands and transcripts in `receipts_20260912/astra_reflection_main_cpu_acceptance_20260913_attempt1.json`.
Main inspected source construction, actual trainer masks, paired exports,
source/model checks, process budgets, fresh-fit/reload and collection controls.
Native preparation succeeded against final source in a fresh snapshot.
Both arms:604target+EOS tokens/epoch (592authored+12EOS),2838target UTF-8 bytes;
withdrawn1696total tokens/epoch, present2272; largest rows146/194tokens.
Zero truncation, full-target plus one EOS labels; prompt/padding/template tail
masked. Supervised exposure matches; prompt/compute exposure does not.

Source `/localhome/local-rohing/astra_sources/reflection_fit_20260913_attempt1`;
root `/localhome/local-rohing/astra_diagnostics/reflection_fit_20260913_attempt1`;
external logs at the same root name with `_logs` suffix. Node3GPU0 UUID
`GPU-0ee6f753-c61e-e18a-8aea-acccd3042939`; actual vacancy checked again at launch.
Plan SHA256 `098d023ab4ac01976370bcd3e1d2ce1992e7636cb04edf8cb96a9546d7c03e1f`.
Runtime SHA256 `0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc`.
Corpus SHA256 `b69dfe4ab39e60fab826e67758d21e708c87d538f3fcd2b8a579bb778b0ace80`.
Five-file source pins SHA256
`111528d41e8fca6863a853da5d311d414e1a9e83f8c7a6839a9e82a3b80457f1`.
Accepted helper is the frozen perception source helper59874c67, NOT the stale
node `/tmp` helperde1cd675. The latter has old token handling/3s NVML limits and
was not used or modified. First read-only vacancy command exceeded the tool's
20s deadline; repeated read-only check with60s tool budget passed, no mutation.
Reported lease September26 03:03UTC; launch additionally requires six-hour
lease margin. A100 onboarding remains Fable-owned and is not needed here.
Complete preparation, helper/runner handoffs and CPU acceptance are archived.

## Prospective learner-seed replication amendment — 05:14 UTC

Before any reflection outcome inspection, Main selects learner seeds1and2 in
addition to the live seed0 pair. This is an independent replication extension,
not success-selected follow-up or a modification of seed0. The derivative
runtime changes only training seed/epoch order and binds those differences;
readout engine and generation seeds remain0, with unchanged data/targets,
methods, metrics and per-root ceilings. All seeds and all failed runs will be
reported. Three roots mean six cold fits and432readout calls in total; at most
3aggregate controller GPU-hours plus separate bounded collections. Identical
OFF readouts remain matched deterministic controls, not independent samples.
Native preparation and fresh allocation are still required for each replica.
Selected placement node3GPU1/2 is provisional until checked; no replacement
seed/root is authorized by an unfavorable outcome. The original root/plan/runtime
and all its source hashes remain unchanged. No replica is launched at this entry.
