# First-eleven writer-pretest cumulative audit

**Date:** 2026-09-12

**Role:** independent read-only audit

**Evidence cutoff:** the first eleven completed/available writer-pretest source lives in the standing tally, including the A/C-only result from `R4_B_seed604`. Later completions are outside this memo's denominator.

## Executive verdict

The first eleven lives support a narrower and more useful conclusion than several running summaries implied:

1. **The writer can change behavior and can sometimes reinstall a supplied fixed routine.** Whole-text fitting produced a report-panel gain of at least `+.015` in 4/11 lives. All four had positive point estimates on the source-disjoint panel, but only 2/11 cleared `+.015` there. The aggregate effect was effectively zero: `+.0045` on report and `-.0045` on disjoint.
2. **No tested format yet demonstrates selective experiential memory.** The evaluated CompilerGym panels do not contain program-conditioned trigger/nontrigger pairs, so a global action habit can score well. The repeated score plateaus and action-string audits are consistent with carriage of a bootstrap-supplied routine, not learned conditional knowledge.
3. **Masking the causal antecedent from loss is not enough.** The full two-scale framed child-stream recipe was null on average and unstable. Its nominal target-budget-matched variant was often harmful. Episode-only frames were also null.
4. **The deterministic QA writer is interface-destructive in its present form.** It drove the measured task score to exactly zero in all 11 lives on both panels. This rejects that exact corpus/extraction/rendering recipe, not QA memories in general.
5. **The bundled “TMEM-style” cell is strongly negative, but it is not a clean TMEM test.** It changed the corpus, rank, layer placement, optimizer, initialization, learning rate, and epoch count together. It produced no positive cell and was harmful in 10/11 report and 9/11 disjoint comparisons.
6. **Short child briefs look safer than parametric writes, not proven superior.** The final brief was descriptively non-harmful but was drawn from a later horizon than the episode-512 adapters. At the matched episode-512 horizon, the brief did not outperform whole-text fitting and was negative on average on the disjoint panel.
7. **Spill is the current binding writer defect.** Separate canonical-frame assays prove that cue-compatible completions can be installed, but strong acquisition generally changes unsupported cues too. The available OLD+NEW test is a simultaneous replay fit from base, not a sequential retention experiment; it shows attenuated carriage of both banks, not forgetting.

Accordingly, the highest-information next writer test is **not another lifetime-format bakeoff**. It is a minimal opposing-input sign canary that asks whether one adapter can move two equal-format inputs toward two different legal actions. If it cannot, this writer family should stop before more scale is spent on it.

## Evidence population and classification rule

The fixed cutoff contains:

- `R2_B_seed0`, `R2_B_seed1`, `R2_B_seed2`, `R2_B_seed4`, `R2_B_seed5`, `R2_B_seed6`, `R2_B_seed7`, `R2_B_seed8`
- `RP_B_seed400`
- `R4_B_seed601`, `R4_B_seed604`

This is a **mixed-arm, completion-time convenience set**, not a randomized confirmatory sample. It contains eight ungated R2 lives, one parented ungated RP life, and two gated/parented R4 lives. I use the existing descriptive bands consistently:

- positive/carry: delta `>= +.015`
- harmful: delta `<= -.030`
- flat: everything between

The bands are descriptive rulers, not hypothesis tests. Means below are equally descriptive; no standard errors or p-values are warranted for this heterogeneous set.

## Aggregate reconstruction

All values are deltas from the same-life adapter-OFF probe. “P/F/H” means positive / flat / harmful under the bands above.

| Writer/read condition | n | Report mean | Report P/F/H | Disjoint mean | Disjoint P/F/H | Both positive | Both harmful |
|---|---:|---:|---:|---:|---:|---:|---:|
| A: whole-text legacy corpus | 11 | +.0045 | 4 / 6 / 1 | -.0045 | 2 / 8 / 1 | 2 | 1 |
| A_v3: same flat strings, v3 trainer | 11 | +.0101 | 4 / 7 / 0 | -.0028 | 0 / 10 / 1 | 0 | 0 |
| B: episode + local child frames | 10 | +.0038 | 2 / 7 / 1 | -.0037 | 3 / 6 / 1 | 2 | 1 |
| Bs: episode frame only | 10 | +.0011 | 0 / 10 / 0 | -.0052 | 0 / 9 / 1 | 0 | 0 |
| B_match: nominal A-target-budget match | 10 | -.0534 | 3 / 4 / 3 | -.0292 | 2 / 3 / 5 | 2 | 3 |
| C: deterministic QA | 11 | -.4865 | 0 / 0 / 11 | -.2509 | 0 / 0 / 11 | 0 | 11 |
| C_tmem: bundled TMEM-style recipe | 11 | -.2052 | 0 / 1 / 10 | -.1102 | 0 / 2 / 9 | 0 | 9 |
| Final child brief in context | 11 | +.0166 | 5 / 6 / 0 | +.0069 | 2 / 9 / 0 | 2 | 0 |
| Episode-512 child brief in context | 11 | +.0004 | 4 / 5 / 2 | -.0143 | 2 / 7 / 2 | 1 | 1 |

The final-brief row is not horizon-matched to the writer rows. The episode-512 brief is the relevant matched comparison. Relative to A, the matched brief averaged `-.0041` on report and `-.0097` on disjoint. The apparent final-brief advantage over A (`+.0121` report, `+.0114` disjoint) is therefore not interpretable as a clean substrate advantage.

## What each writer condition actually tests

### A: whole text

A trains a rank-32 all-layer adapter on flat legacy strings, with every token targeted, learning rate `1e-4`, three epochs, and no pinned trainer seed in the original recipe. It is the only condition that repeatedly carried the supplied fixed routine on the report panel:

- Report-positive: seeds `0`, `1`, `7`, `8`.
- All four had positive disjoint point estimates.
- Only seeds `0` and `1` exceeded `+.015` on disjoint.
- Seed `2` collapsed (`-.1411` report, `-.0858` disjoint).

The exact deltas for the four report-positive lives were:

| Life | Report | Disjoint |
|---|---:|---:|
| R2 seed0 | +.0448 | +.0244 |
| R2 seed1 | +.0451 | +.0177 |
| R2 seed7 | +.0400 | +.0135 |
| R2 seed8 | +.0311 | +.0105 |

This is evidence of **parametric behavioral carriage**. Because the routine was present in the bootstrap and because the panels do not demand different actions under matched cues, it is not evidence of novel discovery, program-conditioned memory, or reasoning transfer.

### A_v3: trainer-bundle change, not a masking experiment

A_v3 uses the same all-target flat strings as A. It does **not** introduce prompt/response loss masking. It changes the training bundle: one epoch rather than three, seed `0`, and different EOS/length/batching/fallback geometry. It had four report positives but zero disjoint positives under the `+.015` band. Therefore:

- It cannot be cited as evidence for or against masking.
- It does not improve the source-disjoint result.
- Differences from A cannot be attributed to any single trainer feature.

### B, Bs, and B_match: child-stream frames

B places real causal antecedent context before a verbatim child thought/action chunk and applies loss only to the child continuation. Each selected child target is represented at two scales: episode context and a smaller local frame. The node implementation safely fell back to one item per sequence, so no neighborhood packing effect was tested.

B also carried far more supervised target mass than A—roughly `1.25M` to `5.50M` target positions across two views in the audited lives—and historical children contained substantial harness-shaped echo text. The format therefore is not a clean collection of compact semantic memories.

The result was approximately null on both panels, with two both-panel positives (`R2 seed1`, `RP seed400`) and one both-panel harmful life (`R2 seed7`). In `R2 seed1`, B reproduced the same absolute behavior as A, again consistent with the fixed routine rather than conditional frame use.

Bs retains only the episode-scale frame. It produced no positive cell on either panel and one harmful disjoint result. The extra local view in B is therefore not cleanly credited, but the episode-only alternative supplies no rescue.

B_match subsamples framed targets toward A's compile-time target-token budget. It is **not an exact dose-matched causal contrast**: item selection, actual post-tokenization target positions and EOS targets, content exposure, and optimizer-step geometry still differ. Its frequent harm is important operationally, but it does not identify “frames” as the cause. The two both-panel positives (`R4 seed601`, `RP seed400`) are leads, not a stable pattern.

### C: deterministic QA

C deterministically extracts selected notes, executed actions, and reflections into chat examples and masks loss to the answer. In this implementation, action answers can be raw action strings rather than continuations beginning in the native `PREDICT:`/`ACT:` dialect. Every audited C adapter scored exactly `0.0` on both panels.

The supported claim is narrow: **this deterministic QA extraction/rendering/training recipe destroys the measured action interface.** It does not show that QA-formatted memories or response-only loss are intrinsically bad.

### C_tmem: a coupled bundle

C_tmem reuses the deterministic C extraction while also changing to rank 6, the last four FFN blocks, SVD initialization with frozen A, SGD at `5e-4`, and five epochs. It is only “TMEM-style” in a loose bundle sense. It omits key aspects of the cited method's model-written, query-aware, within-episode online extraction and policy.

It had no positive cells at all. Ten of eleven report comparisons and nine of eleven disjoint comparisons were harmful. This strongly rejects the bundle for this system, but **cannot support “TMEM fails”** or isolate which bundled choice caused the damage.

### Child briefs

The brief is a short piece of text placed in context, not a trained writer. It is the closest current textual-memory comparator, but it is not a strong retrieval baseline:

- it is one static summary, not query-conditioned retrieval;
- it contains selected positive evidence;
- it can reflect an evolving child/parent lineage;
- the final brief usually comes from episode 1024, while A/B/C train on episode-512 material.

The final brief was non-harmful in all eleven lives and had positive mean deltas. That is useful safety evidence. The horizon-matched episode-512 brief, however, averaged essentially zero on report and `-.0143` on disjoint and did not beat A. No substrate conclusion follows. A paper-grade external-memory comparison still needs an age-matched, active, query-conditioned text-memory arm.

## R4_B_seed604: exact boundary

`R4_B_seed604` contributed valid A/A_v3/C/C_tmem and brief cells:

| Condition | Report delta | Disjoint delta |
|---|---:|---:|
| A | +.0042 | -.0046 |
| A_v3 | +.0042 | -.0057 |
| C | -.4836 | -.2541 |
| C_tmem | -.2180 | -.1268 |
| Final brief | +.0042 | -.0046 |
| Episode-512 brief | +.0042 | -.0037 |

B, Bs, and B_match are absent for the correct reason: their transcript windows contained literal parent text, the leakage scan refused them, and no result was imputed. The equal report score (`.4878`) for A, A_v3, and both briefs is another warning that this panel can collapse different mechanisms onto the same fixed behavior.

## Report panel versus disjoint panel

### Report panel

The report panel contains eight CompilerGym programs withheld by identifier from wake experience. That makes them held out from the child's source trajectory, but not uniformly untouched by the research process:

- In R2 and RP lives it was a repeatedly examined development diagnostic, though not an adapter-admission gate.
- In R4 lives the same panel was used by the write gate to accept or reject sleep adapters. Those histories are therefore panel-conditioned at the lineage level.
- The present eleven-life comparison is post hoc across multiple recipes and a completion-time subset.

The metric is best-of-trajectory over 16 generated chunks with uncapped actions. It mixes action identity, action count, stopping behavior, parser/interface preservation, and program response. Repeating one globally useful action recipe can score well. It is a useful development diagnostic, not sealed confirmatory evidence.

### Disjoint panel

The disjoint panel contains twelve programs drawn from different benchmark datasets and absent from the source curricula. It was not used to fit the audited episode-512 adapters, and for R4 it is also different from the write-gate panel. It is therefore the stronger read for source-disjoint carriage.

It is still not a sealed confirmatory panel: it was development-built from 24 candidates by requiring at least `.02` headroom for the birth routine, has since been inspected repeatedly, and currently uses only two decoding seeds. Most importantly, it also rewards a generally useful fixed routine. It cannot distinguish “knows when this memory applies” from “does this everywhere.”

The honest distinction is:

- **Report:** familiar development diagnostic, and R4 lineage-selected.
- **Disjoint:** source- and gate-disjoint development diagnostic, but researcher-used and routine-sensitive.
- **Neither:** a trigger/nontrigger test of selective memory or a sealed final panel.

## Spill, replay attenuation, and why this is not forgetting evidence

Separate canonical-frame micro-assays establish that the LoRA substrate can increase a requested completion under its trained surface cue. They also show that acquisition is generally nonselective:

- Strong fits produced unsupported-cue spill around `.26`–`.40` or higher in representative assays, far above the registered `.03` locality target.
- Lower learning rates (`3e-5`, `1e-5`) left spill at approximately `.394` and `.296`.
- Prefix masking reduced one spill measurement from `.416` to `.202` but also erased registered owner acquisition (`I=.015`, interval crossing zero).
- A frozen-OFF preservation coefficient of `.1` reduced spill from `.416` to `.0367`, but again suppressed selective acquisition (`I=.152`, interval crossing zero).

The available cumulative OLD+NEW diagnostic defines:

- `A1 = Fit(base, OLD)`
- `AN = Fit(base, NEW)`
- `A2 = Fit(base, OLD + NEW)`

This is a fresh-base simultaneous replay comparison, not `Fit(A1, NEW)`. In A2, the OLD effect was `.209910`, or `49.3%` of OLD-only `.425674`; the NEW effect was `.359223`, or `53.4%` of NEW-only `.673276`; spill remained `.286929`, and the locality/dose/abstention gates failed.

The supported statement is: **when both banks are fitted together under this dose, both completion effects are present but attenuated and nonselective.** It is not evidence of sequential forgetting, retention across sleeps, warm-start behavior, or lifetime consolidation. Those require a sequential, optimizer- and dose-controlled protocol with old, new, and unsupported cues measured after each update.

## Highest-information next writer test

Run one minimal **opposing-input sign canary** before any further semantic writer scaling:

1. Preseal two target-independent, equal-length input records.
2. Give them the same native action interface but opposite correct actions, chosen from exactly two legal actions.
3. Train one adapter using pairwise two-action loss for the first two real budgeted updates.
4. Before and after each update, record the canonical raw log-odds difference `z(action_0) - z(action_1)` for both inputs.
5. Require opposite motion: the first input must move toward action 0 and the second toward action 1. A global action prior cannot pass this gate.
6. Bind the initial tensor hash, optimizer state, RNG state, exact input bytes, token IDs, and FP32 loss receipt. No target or future-result token may appear in the input.

Decision rule:

- **Fail:** stop this semantic writer family. More whole-text/frame/TMEM lifetime cells will not resolve the inability to bind opposite outputs to inputs.
- **Pass:** claim only exact-surface supervised conditional carriage. Then run a common-prefix exact-row comparison and, only after that, held-form generalization plus spill/interface qualification.

This is higher-information than another end-to-end lifetime because the recent first-choice-only experiment already removed suffix-gradient ambiguity yet still converged on one constant action. The missing fact is whether the writer can produce *opposite, input-dependent parameter updates at all*.

## Exact paper-safe claim at this cutoff

> Across an exploratory mixed-arm convenience set of eleven CompilerGym lifetimes, a fresh rank-32 whole-text fit to each child's first-512-episode legacy sleep corpus sometimes reinstated a bootstrap-supplied fixed optimization routine: 4/11 lives exceeded a +.015 descriptive band on a repeatedly used eight-program report panel, while 2/11 did so on a source-disjoint twelve-program development panel. Mean deltas from the frozen child were +.0045 and -.0045 on the two panels, and one fit collapsed. A target-masked two-scale child-stream recipe was similarly null and unstable across ten eligible lives (+.0038/-.0037), while its nominal token-budget-matched variant was frequently harmful. The deterministic QA recipe destroyed the measured action interface in 11/11 lives; a coupled TMEM-style bundle was harmful in 10/11 report and 9/11 disjoint comparisons. Final short briefs were descriptively non-harmful but age-mismatched, and at the matched 512-episode horizon they did not outperform whole-text fitting. Separate synthetic assays establish cue-compatible parametric carriage, but strong writes spill to unsupported cues; one fresh-base OLD+NEW replay fit preserved only about half of each single-bank completion effect and remained nonselective. These data establish parametric behavioral carriage and diagnose writer failure modes, not selective experiential memory, sequential forgetting or retention, parenting, or lifetime learning.

That paragraph is the maximum defensible claim. For an abstract, it should be shortened further rather than strengthened.

## Principal evidence inspected

- `research_notes/2026-09-11_write_pretest_causal_audit.md`
- `research_notes/2026-09-11_writer_evidence_adjudication.md`
- `research_notes/2026-09-11_legacy_writer_seed0_7_8_terminal_closure.md`
- `research_notes/2026-09-11_brief_adapter_matched_2x2_audit.md`
- `research_notes/analysis/2026-09-12_writer_sleep_evidence_chain_audit.md`
- `research_notes/analysis/2026-09-12_cumulative_memory_diagnostic_post_result_fresh_audit.md`
- `research_notes/analysis/2026-09-12_lower_lr_writer_terminal_audit.md`
- `research_notes/analysis/2026-09-12_prefix_mask_terminal_independent_audit.md`
- `research_notes/analysis/2026-09-12_preservation_pair_terminal_independent_audit.md`
- `research_notes/analysis/2026-09-12_pairwise_writer_path_fresh_audit.md`
- `organism_v6/sleep_compile_v3.py`
- The first-eleven per-life `summary.json` artifacts, with seed0 A/A_v3/B values recovered from its raw report/disjoint probe files because its later summary was partial.
