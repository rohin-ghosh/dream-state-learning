# SEQ101 — level-zero repetition/context sentinel

Evidence cut September12,2026 18:51UTC. EXECUTED, Main native reduction and
capsule verification complete. Independent numerical review PASS,192rawoutputs.
Exploratory trainer-seed0 development comparison; not final confirmation.

## Frozen comparison and results

Source `ed3aac9f888935a40e3a2f8f4e0e1953e17f2ea9`; node3 root
`~/astra_diagnostics/astra_fundamental_repetition_20260912_attempt1`.
Each original example repeated16times:1280 short context-reset rows versus
80 concatenated long rows. Same original groups per optimizer update,
80updates,4epochs,r8/alpha16/dropout.05/LR3e-4/seed0. Each cell receives
289088input/58368targettokens. Short max61tokens,batch4/accum16;
long max976tokens,batch1/accum4. Different attention context, microbatch and
dropout computation mean this is not identical gradients or pure length alone.
No packing, dropped targets, truncation, new facts or extra optimizer steps.

| Cell | Correct ACT | Predict-before-ACT adherence | Memory correct | Memory outputs |
|---|---:|---:|---:|---|
| teach_short |32/32|32/32|4/16|red16|
| control_short |32/32|0/32|4/16|red16|
| teach_long |32/32|32/32|4/16|red16|
| control_long |32/32|0/32|4/16|red16|

Exactly192new calls across four states. Same48development cases and actual
seed0 OFF reference as SEQ098. No new OFF calls or confirmation requests;
all64confirmation cases remain unrequested. All trained memory outputs valid,
but constant-color guessing is not item-specific binding. Arithmetic already
32/32 in the baseline; adherence, not arithmetic gain, is the level-zero goal.

Within each treatment, all48rawresponse texts also exactly equal original
seed0 same-arm outputs. Long-minus-short is0/32adherence,0/32correctACT and
0/16memory. Relative to original seed0 dose, repetition did not improve the
fixed development-paraphrase memory readout. The notebook18:39 prediction
specifically said in-sample: original-training-prompt recall on these new
repetition checkpoints remains UNTESTED, so that literal prediction is not
falsified by this result. It does not
identify loss allocation, extraction, loading, capacity or latent binding as
the cause. Long-fit loss near zero is not evidence of retrieval. Original
training-prompt SEQ100 is diagnostic of ORIGINAL seed0 adapters; do not silently
apply that in-sample observation to these new repetition adapters.

There is no evidence here requiring separate behavior/memory adapters.
Control failure also does not prove absence of every possible interference
mechanism. Main is auditing native encoding/masking and train/readout loading
before spending on larger dose or rank sweeps. Compiler changes remain aside.

## Instrumentation and cost

All fits complete80updates with fresh adapters and immutable inventories;
all readouts fresh-process with bound source/model/adapter/rendered-input
hashes. Readout controllers178523,178581,178741,178909 launched18:42:57–
18:43:30UTC, fully released18:46:18–18:47:26UTC. Main full vacancy checked,
no foreign process killed. Fit controllers175686–175689 already fully released.

Fit supervision1300.292523s; readout supervision417.340742s;
combined1717.633265s=28.627221A40min. Together with SEQ098–100:
3227.769201s=53.796153A40min, within initial90A40min budget.
Readout generation81.901202s; input8524/output1888tokens, ceiling12288.
Full readout reservations sum883.068789s, including Main audit delay.
Supervision, full reservation and active GPU compute are distinct; no monetary
cost is inferred. Three-rate continuation has a separately declared budget.

## Reproduction and artifacts

Archived scripts: `receipts_20260912/astra_repetition_readouts_20260912.py`,
`astra_archive_repetition_20260912.py`, `astra_analyze_repetition_20260912.py`.
Analysis: `receipts_20260912/astra_repetition_main_analysis_20260912.json`.
Capsule: `receipts_20260912/astra_fundamental_repetition_terminal_20260912.tgz`.
SHA256 `36e9ca2637d1f78ab218afd3348b0cc547ea098188e3d418aa2b08c4e48a198b`.
All507capsule files verified before/after packaging and after transfer.
Weights remain at the node3 root, excluded from the lightweight capsule;
their exact inventories are retained in fit and readout plans. No overwrite.

No H1/H2, P1/G5, representative memory gate, mechanism freeze or finalC11
promotion. Origin remains `UNRESOLVED_LOCAL_HASHES_ONLY`. Simple hygiene holds.
