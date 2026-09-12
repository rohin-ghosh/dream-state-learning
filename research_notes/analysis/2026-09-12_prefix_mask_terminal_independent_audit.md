# Prefix-mask terminal result: independent watcher audit

Date: 2026-09-12 UTC  
Evidence cut: local `main` containing builder commit `dc00f176`  
Status: watcher-side audit only. No builder source, adapter, process, GPU job,
lineage, or authority was changed.

## Verdict

**The prefix mask reduced the old global completion habit, but it also erased
the intended owner--colour acquisition.** It is an under-writer, not a
selective writer.

An independent reduction directly from the 1,313 saved cue rows reproduces:

| endpoint | whole-text baseline | prefix mask |
|---|---:|---:|
| dose-16 correct frame probability, OFF -> ON | `.260 -> .685` | `.260 -> .251` |
| `I_d_frame`, 95% paired-owner interval | `1.921 [1.203, 2.683]` | `.015 [-.133, .174]` |
| spill: unexposed / similar / bicycle | `.321 / .417 / .509` | `.184 / .198 / .223` |
| mean frame spill | `.416` | `.202` |
| dose-16 candidate mass ON | `.998` | `.993` |

Candidate mass therefore did not collapse. The mask changed the learned
relation: it removed measurable owner binding while leaving a smaller but
still broad completion tendency. Prefix-mask spill remains `6.73x` the
registered `.03` ceiling.

The unchanged gates dispose the run noncompensatorily:

- **G9 frame binding: fail.** Its acquisition interval crosses zero *and*
  spill exceeds `.03`.
- **G10 dose: fail.** Frame shifts at doses `1/4/16` are
  `-.00587 / .0000013 / -.00870`; the registered rise is absent.
- **G11 abstention: fail.** Prefix-mask ON probabilities are approximately
  `.000011` on unexposed frames, `.000016` on bicycle frames, and `.000013`
  at dose 16. The first two must be at least `.5`.

This matches the prospectively declared `acquisition collapses + spill lower`
cell: **under-writing; do not promote the recipe**.

## Prospective status and comparability

The result interpretation was fixed before the fit. The initial proposal was
committed at 10:59 UTC. Native tokenization then exposed 5,376 boundary
straddles; the conservative `Owner`-token amendment was committed at 11:02:30,
the native preflight at 11:04:17, and the run launched at 11:04:20 UTC. Thus
the boundary treatment was not selected after seeing the result.

The capsule and reduction verify the intended matched dimensions:

- the same 12,924 ordered input strings, row weights, filler rows, and
  249,995 input tokens per epoch;
- the same Qwen2.5-7B-Instruct specification, rank 8, alpha 16, dropout `.05`,
  optimizer seed 2, learning rate `1e-4`, batch 4, three epochs, and 9,693
  steps;
- 749,985 input-token passes in both arms;
- the same frozen `memory_dose.py` bytes (`ab98329c...76e3`) as the captured
  historical baseline;
- all 1,313 cue identities, order, metadata, candidate order, and OFF scores
  equal at serialized precision.

The treatment is nevertheless **not matched in supervised-token dose**. It
sets `mask_context=true` on 5,376 fact and 1,344 empty-context lesson rows,
but only the fact rows change labels. Under the measured joint tokenizer it
removes 288,288 shifted labels across three epochs, including the first
`Owner` token at each of the 5,376 fact boundaries. Supervised-token passes
fall from 711,213 to 422,925 (`59.5%` of baseline). Consequently this run
estimates the bundled effect of loss placement, lower supervised-token dose,
and the documented boundary omission. It cannot isolate “context supervision
causes spill.”

The terminal capsule hash (`7017ef23...be18`), fit metadata, evaluation, and
cleanup receipt are present. The adapter weights are deliberately absent;
only a remote hash receipt is retained, and official model authentication is
still `UNRESOLVED_LOCAL_HASHES_ONLY`. The saved cue outputs can be reduced,
but the fitted model cannot be replayed or independently authenticated from
the repository capsule.

## Reducer portability defect

Re-running
`python3 -B -m organism_v6.memory_mask_analysis` on independently extracted
baseline and mask capsules reproduced every substantive value and gate.
However, on local Python 3.9 the reducer returned `valid=false` because
`check_report` requires exact dictionary equality between freshly computed
floating-point gate values and the stored native report. The largest relevant
difference was `2.78e-17` in frame spill; gate booleans and confidence limits
were unchanged.

The committed reduction's `valid=true` is therefore environment-sensitive.
Before treating this custody path as paper-grade, compare reported floats with
a declared tolerance (while retaining exact comparison for discrete fields
and pass/fail booleans), then regenerate the validation receipt. This defect
does **not** rescue or weaken the negative scientific result; it only narrows
the claim from “portable reducer validation” to “raw saved metrics independently
reproduced, with one checker portability defect.”

## Narrow claim and next experiment

The supportable claim is:

> On one synthetic oracle bank and one optimizer seed, at matched inputs,
> updates, and input-token passes, masking fact contexts lowered frame spill
> from `.416` to `.202` but eliminated measurable dose-16 owner binding. The
> intervention did not produce selective memory, and unequal supervised-token
> dose prevents attributing the tradeoff to context masking alone.

Close this mask/LR-only branch. A supervised-dose-matched mask experiment
would isolate the mechanism more cleanly, but it is lower-value than testing
the thesis-relevant conditional action geometry. The highest-information next
step is the fresh V10R2 exact-row positive-carrier gate. Only if that carrier
passes should semantic W0 fits run. If the unchanged writer then fails W0,
use the already specified rank-8 `query-only versus cross-view` x `no anchor
versus targeted OFF-KL` factorial. That experiment can distinguish storage,
fresh-form extraction, motor-interface realization, and locality; another
learning-rate or mask-only sweep cannot.

## Evidence inspected

- `research_notes/astra_memos/ASTRA_PREFIX_MASK_COMPARISON_2026-09-12.md`
- `research_notes/astra_memos/ASTRA_PREFIX_MASK_TERMINAL_2026-09-12.md`
- `research_notes/astra_memos/receipts_20260912/astra_prefixmask_terminal_20260912.tgz`
- `research_notes/astra_memos/receipts_20260912/astra_seed_bank0_evidence_20260912.tgz`
- `research_notes/astra_memos/receipts_20260912/astra_memory_mask_reduction_20260912.json`
- `organism_v6/memory_mask_analysis.py`
- `organism_v6/memory_dose.py`
- `research_notes/analysis/2026-09-12_next_bounded_experiments_after_behavior_replication.md`
- `research_notes/analysis/2026-09-12_post_v10r2_writer_recipe_factorial.md`

