# Prospective same-input memory prefix-mask diagnostic

September 12, 2026, 11:00 UTC. Exploratory, synthetic oracle memory only;
not a clean lineage, parenting result, C11 qualification, or mechanism freeze.

## Decision

SEQ-071's original and two lower-rate fits all fail the unchanged G9 spill
ceiling. Park further LR sweeps. Before implementing a new preservation/KL
objective, test the missing same-string mask-only comparison. Recovered
target-only compiler pretests and TMEM cells change other factors and are
not evidence that this F_r16k16 comparison already ran.

Use the original source-seed1 bank0 F_r16k16 corpus, SHA256
`f2388eaf9c2285d6c5fe109445a599a4fefb5d9b1ca0ce6223ef78bede01c37d`.
Change only `mask_context` from false to true on 5,376 fact and 1,344 lesson
rows. Lesson contexts are empty, so their actual labels do not change.
Preserve all strings, row order, event references, weights, filler rows,
input token IDs, and native evaluator settings. Recompute mask-sensitive
identities and actual shifted-label token totals. Do not overwrite the
original corpus or use its whole-text identity for this fit.

One new fit: fresh rank8 adapter, alpha16, dropout.05, AdamW1e-4, seed2,
batch4, maxlen512, three epochs, 9,693 steps; no gradient checkpointing,
same original memory trainer. Reuse the completed same-seed 1e-4 A1 baseline
from node2; do not refit a known control merely to occupy another GPU.
New execution on node3 is disclosed. Compare all saved OFF scores and cue
metadata exactly before treating native evaluations as matched.

Masking changes supervised-token count and token-mean loss normalization.
It does not remove canonical sentence-format CE or colour-filler training.
This estimates the effect of supervision placement at matched input/step
dose, not a pure isolated causal effect of observing prefixes, nor a
matched-supervised-token experiment.

## Acceptance, budgets, and interpretation

CPU preflight requires identical encoded inputs, only intended label removal,
no truncation or boundary straddles, original input749,985 and supervised711,213
token passes, and explicit new supervision count. Require all12,924 items,
6,720 mask flags changed and5,376 actual-label changes. Source-bank provenance
and disposable synthetic status travel unchanged; official model authentication
remains UNRESOLVED_LOCAL_HASHES_ONLY. No new final C11 guard is introduced.

Run all1,313 original native cues, template/abstention checks and report.
Keep G9 unchanged: lower owner-bootstrap I_d_frame bound >0 and spill≤.03.
Report G11 unchanged too, plus acquisition, spill decomposition, training
stability, runtime, and OFF agreement. Lower spill accompanied by lost
acquisition is under-writing, not selective memory success. One bank/seed
cannot establish reliability. No outcome-selected threshold or prompt edits.

Proposed new root `~/astra_diagnostics/astra_A1_prefixmask_bank0_ts2_20260912_attempt1`.
Node3GPU0 subject to fresh GPU process/environment/queue checks. Reserve it
through fit and evaluation reloads. Expected30–35 A40minutes; one owned-worker
cap of2,700seconds. Node3 lease ends September25 20:03Pacific; this diagnostic
clears the six-hour completion margin. No automatic follow-on fits. Existing
behavior replications keep GPUs1/3 through their paired arms.

Preparation: `python -B -m gpu.prepare_memory_mask_run --source BASELINE_INPUTS
--destination NEW_ROOT --tokenizer CACHED_MODEL_PATH` under frozen source PYTHONPATH.
Launch: `python -B -m gpu.astra_memory_mask_diagnostic --root NEW_ROOT --device 0`.
Inspect `logs/{launch_receipt,result,failure}.json`, `logs/worker.log`, native
adapter metadata, eval JSON and report. Source hash, native token receipt,
CPU test receipts, and actual PID are appended when available; this
specification is not an execution or result.

If selectivity remains poor, use the observed acquisition/locality tradeoff
to decide whether a preservation objective is justified. Behavioral transfer
and source-linked child-material preparation continue independently; neither
is promoted by a successful oracle-memory write alone.
