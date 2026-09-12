# Fixed mini-Sudoku useful-versus-wrong-board write diagnostic

Prospective specification, September 12, 2026, 10:24 UTC. Main owns resources,
launches and analysis. This is external-oracle material, not a child-authored
sleep, parented life, clean lineage, H1/H2 result or mechanism freeze. Rohin's
message13 motivates validating useful material before extending syntax work.
Formal paper-grade C11 guard remains deferred; simple hygiene stays enforced.

## Fixed question and data

Can the existing rank8 writer turn independently validated action material into
better first actions on new mini-Sudoku puzzles after fresh-process reload,
relative to the exact same question/target marginals with wrong associations?
Use32training IDs `rg/mini_sudoku/1850000` through1850031 and16development-
validation canary IDs1900050 through1900065. No outcome-based rerolls. Popper's
CPU examination history is preserved by the preparer, including unused IDs.
Four evaluation solutions also occur in training (1900054/55/59/65): different
puzzles/givens, not unseen-solution transfer. No untouched confirmation claim.

Useful targets are native `ACT: ` plus canonical4x4solution rows separated by
semicolons. Corrupt targets use the next training board cyclically, keeping the
same target multiset. Independent rows/columns/boxes/givens checks and native
score verify useful answers; every corrupt association must violate recipient
givens and score below1. Native scorer is reference matching/partial credit,
not an independent constraint solver. All48puzzle identities must be distinct.

Prompt context comes from the unmodified one-tick native driver, one prompt
call, including its actual CLOCK. Save raw prompt and actual tokenizer chat
rendering. Feed the rendered context as a zero-loss span to existing V3 plain
encoding (NO `--chat-template`); target and EOS alone carry loss. This avoids
the existing chat-encoder rstrip difference without modifying shared trainer.
Actual node tokenizer/collator must prove exact context IDs, complete target
labels, equal target marginals and no truncation/segmentation before launch.

## Matched implementation and endpoints

Frozen local Qwen2.5-7B-Instruct snapshot, newly initialized rank8 LoRA,
alpha16/default dropout.05/all existing projection modules, AdamW1e-4,
3epochs,32items,96steps, batch1, accumulation1, no packing, maxlen4096,
default gradient checkpointing, optimizer seed0 for both arms. Verify actual
manifest/corpus/model/source hashes,96steps, finite losses and token counts.
Official model origin remains UNRESOLVED_LOCAL_HASHES_ONLY, not authenticated.

Each arm uses existing run_reasoning_neutral fresh-process OFF then ON on the
same16canaries, generation seed0, one tick,400wake tokens. No live parent,
retrieval, corpus examples or carried conversation. Post-outcome Scratchpad
is existing harness bookkeeping,100tokens per ACT, never the endpoint or
training data. Reserve38400maximum output tokens per condition to accommodate
multiple ACTs; the original one-ACT-only8000reservation would fail unnecessarily.
This finite cap and per-process timeouts fail with explicit receipts if exceeded.

Primary endpoint: first ACT solves/16; missing or invalid first ACT=0. Retain
all ACTs and report first-ACT score, native best and ACT counts separately.
Report useful-minus-OFF and corrupt-minus-OFF and their paired difference;
compare duplicate OFF observations rather than silently pool differing runs.
Single optimizer seed is exploratory; do not substitute episode uncertainty
for independent learner replication. Useful improvement beyond wrong-board
and OFF suggests this narrow positive-control write; null/negative results
localize material/capacity/dose/interface failures, not parenting failure.
No retention/general reasoning claim from this panel alone.

## Execution and budget

Fresh node3 root `~/astra_diagnostics/astra_mini_sudoku_useful_corrupt_20260912_attempt1`:
`material/`, separate `training/{useful,corrupt}_seed0`, `probes/{useful,corrupt}`,
external `logs/{useful,corrupt}`. No overwrite/reuse. Source is a fresh archived
commit recorded at deployment. Node3 lease ends September25 20:03Pacific;
all work here fits the six-hour safety margin.

CPU preparation CLI: `python -B -m organism_v6.mini_sudoku_behavior_material
--out ROOT/material --model-path LOCAL_SNAPSHOT --training-root ROOT/training`.
Launch only after native preparation: `python -B gpu/astra_mini_sudoku_diagnostic.py
--root ROOT --arm useful --device 1`, then `--arm corrupt --device 3`.
These launch explicit controller reservations through reload gaps; recheck
GPU XML, own-user CUDA environments and pending/running queue first. Never
displace another life; GPUs0/2 remain reserved for lower-LR diagnostics.
Each arm has900sfit and2100spaired-evaluation ceilings. Expected actual cost
roughly5–15minutes/arm plus hashing/coldstart, to replace with measurements;
hard aggregate stage budget100A40minutes. No automatic seed1/2replication.
Inspect and analyze terminal artifacts before deciding the next comparison.

## CPU status before native preparation

Main:19material and5launcher tests pass; V3 script reports9/9 but3dependency
paths skip locally (peft/torch), so not9fully executed training tests. Native
node checks remain required. No model has been trained for this comparison
at this specification time; lower-LR memory jobs remain independently active.

## Prospective operational amendment, 10:29 UTC

Attempt1 preparation passes native checks but both launches refuse before
creating logs/processes: slow nvidia-smi (~11–12s) exceeds the reused10scheck.
Non-material repair extends its bounded timeout to30s and eliminates duplicate
query at launch, preserving fail-closed occupancy checks and all science bytes.
22wrapper tests including new timing regression and5launcher tests pass.
Use separately archived repaired source and fresh `..._attempt2` for actual
execution; keep attempt1material untouched. No outcome inspected or protocol
endpoint/dose/data amendment. Actual native tokens are25708input/1216target
per epoch per arm,77124input/3648target over3epochs.

Attempt2failed before model load: resolving the venv interpreter symlink
selected system Python without torch. Preserve logs and material; both owned
worker/group/GPU cleanups verified. A second non-material repair preserves
venv invocation, tested with a symlink regression (20material tests pass).
Actual attempt3source3d56c5cd703cb6adc66f732905845a1b787a40ec launched at
10:32:26/39UTC onGPU1/3, controllers56987/57084. All native corpus/token
bytes identical, no science-protocol change or prior learning outcome.
