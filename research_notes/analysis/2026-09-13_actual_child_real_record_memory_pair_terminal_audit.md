# Actual-child real-record memory pair: independent terminal audit

**Date:** 2026-09-13 UTC  
**Role:** independent terminal reducer  
**Scope:** read-only recount of the finalized node-2 `scores.json` artifacts;
no source, fixture, model, tokenizer, adapter, job, or GPU state changed  
**Assay label in artifacts:**
`astra_real_record_memory_paired_write_lr0_20260913_v1`

## Verdict

This is a real but sharply bounded positive memory-write result and a strong
negative retention result.

Starting from the same previously trained Level-1 perception adapter, fitting
only exact child-authored public records made some of those records available
after their source context was withdrawn. The zero-learning-rate partner
retrieved none. Some WRITE records also survived a paraphrased request.

However, WRITE retained only `98/143` previously correct Level-1 held items;
the three seeds lost `3`, `11`, and `31` previously correct items. All generic
canaries remained `36/36`. Thus the write learned some small-bank records while
substantially and variably erasing the skill that formed them, and the current
generic canary did not detect the damage.

This does not pass an automatic or scientific gate: every artifact records
`automatic_pass=false`, `scientific_pass=null`, and `status=WRITE_AVAILABLE`.
It is an exploratory paired diagnostic, not a promoted SLEEP recipe.

## 1. Artifact custody

The three audited roots were:

```text
/localhome/local-rohing/astra_diagnostics/
  real_record_memory_seed{0,1,2}_20260913_attempt1_collected/scores.json
```

All three bind the same upstream formation collection:

```text
77260fe6d540beb65cd4f9717a76fc827cb3e441a23663077f72dbdbd7a70a4c
```

Their final completion hashes are:

| seed | completion SHA-256 | plan SHA-256 |
|---:|---|---|
| 0 | `08deffd0a0baa3bcad110884d250893f8470ae320afd13a3d71e20a651da4972` | `66fb0ae06fce25feb04c422add3062f8665be9bafaa72efdb348365fa82208c1` |
| 1 | `56d19072b3f9474631c4b0d61ca23a21fde490ad80a9dd197f310ecd7023ff92` | `9886ef9f19869f69649ee894e15c1fb47dfc85e301ee728adfbefc4df2c9c52b` |
| 2 | `e7ef9be2d572251e64c5973305fdcad0112d9569498c79c6646848049850987f` | `48f64f78aa6953baa72067602bf3043c0a8fb5531750f0433c6fdd8ef76dc5ea` |

The artifacts report native capture custody checked. Each memory target is an
exact admitted child record; there was no teacher rewrite or new formation in
this assay. That supports provenance of the fitted rows, not autonomous use of
the memories later.

## 2. Denominators and formation

There were 16 possible record slots per seed, 48 total. Only production-
eligible child records entered fitting and memory scoring.

| seed | admitted / possible | refused | refusal causes | distinct raw targets | distinct triples |
|---:|---:|---:|---|---:|---:|
| 0 | 14/16 | 2 | 2 prediction mismatches | 4 | 2 |
| 1 | 8/16 | 8 | 8 prediction mismatches | 5 | 4 |
| 2 | 8/16 | 8 | 3 prediction mismatches, 5 record-schema failures | 5 | 3 |
| **pooled** | **30/48** | **18** | **13 prediction, 5 schema** | **14 within-seed target types** | — |

Both denominators matter:

- **Acquisition conditional on a writable record:** divide by 30 admitted
  rows.
- **End-to-end opportunity yield:** divide by all 48 possible record slots;
  refused formation slots remain failures rather than disappearing.

Rows are not independent. There are three independent optimizer seeds and
only 14 within-seed distinct target byte strings. In every seed, one or more
targets recur; seed 0 has target multiplicities `4,4,4,2`, while seeds 1 and 2
each contain one target repeated four times. Row-level totals therefore must
not be given binomial or root-level uncertainty.

## 3. Exact-cue and paraphrase recount

`content` below is semantic record correctness. `target bytes` is the
artifact's `exact_target_bytes` field. `strict` is strict canonical output.
LR0 produced zero correct memories under every acquisition field.

| seed | exact content WRITE / LR0 | exact target bytes | exact strict | paraphrase content WRITE / LR0 | paraphrase target bytes | paraphrase strict |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 8/14 / 0/14 | 7/14 | 3/14 | 6/14 / 0/14 | 4/14 | 0/14 |
| 1 | 7/8 / 0/8 | 7/8 | 0/8 | 5/8 / 0/8 | 5/8 | 0/8 |
| 2 | 5/8 / 0/8 | 5/8 | 0/8 | 5/8 / 0/8 | 5/8 | 0/8 |
| **admitted pooled** | **20/30 / 0/30** | **19/30** | **3/30** | **16/30 / 0/30** | **14/30** | **0/30** |
| **all possible slots** | **20/48 / 0/48** | **19/48** | **3/48** | **16/48 / 0/48** | **14/48** | **0/48** |

The paired direction is unambiguous at this narrow direct-read surface: every
semantic success is WRITE-only and none is LR0-only. It is not uniformly
address-selective memory:

- seed 0 emitted only two unique exact-cue outputs for four target types and
  only one paraphrase output for all four;
- seed 1 emitted four exact-cue and two paraphrase outputs for five target
  types; and
- seed 2 emitted two outputs for five target types under both request styles.

Scoring each target type as robust only when every occurrence of that target
was correct gives exact-cue `7/14` and paraphrase `6/14` distinct target types.
The corresponding row totals are higher partly because one learned target is
repeated four times. This is evidence of partial keyed acquisition mixed with
seed-specific output-mode collapse, not a complete episodic map.

Paraphrase success is still useful: the only supervised request form was the
source-withdrawn exact-record corpus, so correct output under a separately
worded request is evidence that some acquired content crossed a request-
surface change. But zero paraphrase responses were strict-canonical, and the
collapsed unique-output counts prevent describing it as broad extractability.

## 4. Original Level-1 retention and generic canary

The 48-item held panel measures retention of the original researcher-authored
Level-1 perception skill in the parent adapter. It is not a test of new
experiential learning.

| seed | LR0 held | WRITE held | previously correct lost | generic canary LR0 | generic canary WRITE |
|---:|---:|---:|---:|---:|---:|
| 0 | 47/48 | 44/48 | 3/47 | 12/12 | 12/12 |
| 1 | 48/48 | 37/48 | 11/48 | 12/12 | 12/12 |
| 2 | 48/48 | 17/48 | 31/48 | 12/12 | 12/12 |
| **pooled** | **143/144** | **98/144** | **45/143** | **36/36** | **36/36** |

There were no gained held items. Retention of initially correct items was
`98/143 = 68.5%`; forgetting was `45/143 = 31.5%`. The seed range—from losing
6.4% to losing 64.6% of initially correct items—also shows high optimizer/
corpus sensitivity.

The generic canary is therefore necessary but not sufficient. It certified
all three harmful writes. A promoted cumulative writer needs task-/skill-
specific retention gates or replay of the capabilities it is expected to
preserve, not only a generic behavior panel.

## 5. Exact fit dose

Each seed used the same previously trained perception adapter for WRITE and
LR0, then fresh optimizers. Both arms used rank 8, alpha 16, dropout `.05`, all
28 layers, all attention projections plus MLP projections, batch size 1, and
eight epochs. Each admitted row appeared once per epoch.

| seed | rows | steps **per arm** | WRITE LR | LR0 LR | supervised tokens per arm across epochs | WRITE mean loss epoch 1 -> 8 | WRITE final loss |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 14 | 112 | `1e-4` | `0` | 3,248 | .51329 -> .05062 | .05662 |
| 1 | 8 | 64 | `1e-4` | `0` | 1,592 | .61808 -> .04172 | .13797 |
| 2 | 8 | 64 | `1e-4` | `0` | 1,936 | .32336 -> .03567 | .01838 |

The top-level artifact counts `224/128/128` updates because it sums the WRITE
and LR0 fits. It must not be reported as the WRITE dose. The write dose was
`112/64/64` optimizer steps, or eight presentations per admitted row. The
starting Level-1 adapter already carried 320 cumulative steps; the terminal
manifests report `432/384/384` after adding this assay's steps.

WRITE changed about 20.185 million adapter elements. Its parameter L2 delta
was `3.921`, `3.590`, and `3.180`; LR0 changed zero elements and had L2 delta
zero. Loss fell strongly, but lower final loss did not predict safe retention:
seed 2 had the lowest final loss and the worst skill erasure.

## 6. What this proves

Within this exact three-seed diagnostic, it establishes:

1. **Actual child-record gradients can cause source-withdrawn generative
   recall.** Exact child records, not teacher rewrites, were the targets;
   WRITE produced `20/30` semantically correct admitted-row reads versus
   `0/30` for the otherwise paired LR0 arms.
2. **Some acquired records cross a request paraphrase.** WRITE produced
   `16/30` admitted-row paraphrase-correct reads versus `0/30` LR0, although
   only `6/14` distinct target types were robust across all their occurrences.
3. **The effect is genuinely parametric at this bounded read surface.** The
   source material was withdrawn, WRITE changed adapter parameters, and LR0
   did not. This is stronger than a training-loss-only observation.
4. **The writer/reader seam is partial rather than absent.** The result
   localizes the next obstacle to conditionality, diversity, retention, and
   native use rather than proving that raw child experience cannot enter an
   adapter at all.

## 7. What it contradicts

It contradicts or seriously weakens these propositions:

1. **"Eight raw repetitions at LR `1e-4` safely add memories to an existing
   skill adapter."** They do not: pooled original-skill retention fell from
   `143/144` to `98/144`.
2. **"A perfect generic canary rules out write damage."** It does not:
   canary stayed `36/36` while 45 previously correct held items disappeared.
3. **"Low final training loss means a usable scoped memory map."** It does
   not: output diversity collapsed to `2/4/2` exact outputs per seed and
   robust exact target-type acquisition was only `7/14`.
4. **"Row-level acquisition counts are memory breadth."** They are not here;
   recurring target types inflate `20/30`, and there are only 14 distinct
   within-seed targets across three independent seeds.
5. **"Paraphrase transfer makes the memory production-ready."** It does not:
   paraphrase semantic success was partial, no paraphrase response was strict-
   canonical, and no downstream native action used it.

## 8. What it does not establish

This assay does not establish:

- a complete SLEEP or DREAM compiler;
- native agent use, goal-conditioned traversal, useful experiment selection,
  connected LINK utility, or behavior improvement;
- a second write, OLD/NEW retention, recurrence, a lifetime curve, textual-
  memory superiority, compression, parenting, or general-domain transfer;
- a safe writer recipe for PCFL v2.2; or
- population reliability from three optimizer seeds.

The artifact's own claim boundary is correct: no teacher rewriting, new
formation, closed loop, H1/H2, scientific pass, or automatic promotion.

## 9. Consequence for the critical path

Preserve this as the first bounded evidence that admitted real child records
can enter the parametric carrier and be read after source withdrawal. Do not
promote its `1e-4`, eight-epoch raw-row recipe.

The result strengthens the need for the already proposed v2.2 writer
qualification:

- lower heat first;
- truthful balanced replay and source-diverse batches;
- unique-output/confusion diagnostics, not only aggregate exact score;
- candidate-free semantic/locality gates; and
- an explicit retention panel covering the capabilities present at the write
  boundary, because the current generic canary missed severe erasure.

The next claim-bearing question remains whether the repaired writer can carry
diverse child EVENT/LINK rows without this collapse or forgetting, then use
them through the native PCFL path. This diagnostic is a positive bridge into
that test, not a substitute for it.

