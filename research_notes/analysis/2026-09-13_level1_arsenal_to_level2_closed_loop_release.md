# Smallest Level-1 arsenal and earliest Level-2 closed-loop release

**Date:** 2026-09-13 UTC  
**Role:** independent watcher-side experiment design from Rohin messages 31--32  
**Scope:** research design only. No builder source, corpus, model, tokenizer,
adapter, job, GPU, or lease state was changed.  
**Vocabulary:** Level 1 is **trained** readiness because researchers prepare or
select the material. Level 2 is **learned** only when the child prepares the
semantic training material from its own public action--outcome experience and a
later mounted SLEEP changes what that child does.

## Decision in one paragraph

Do not wait for a complete five-skill birth and do not train a monolithic
"thinking" corpus. Run one small **correction-to-reuse** module through three
ordinary post-training data routes: authored SFT, context-distilled child
continuations, and rejection-sampled parent-steered open-loop experience. The
trainer stays fixed: rank-8 response-masked SFT with native-behavior replay.
Select a route only from externally scored, parent-withdrawn actions, not prose
quality or training loss. As soon as this one module survives two confirmation
fits, a target-permuted control, and an independently seeded release fit, fork
it into a fresh two-SLEEP `PROMOTE` versus `SHADOW` micro-life. Other birth
modules continue in parallel. This is the earliest honest bridge because the
first SLEEP uses the exact same child-authored material in PROMOTE and SHADOW,
the mounted write can alter the next experience, and the second SLEEP is made
from those resulting child experiences. It does not yet test connected-memory
traversal, long lifetimes, or superiority to text memory; those remain the
subsequent M and L experiments.

## 1. What the terminal evidence permits

### Perception is presently an interface canary, not a semantic birth module

Across all three learner seeds, the unadapted child scored `0/12` under the
strict bare-JSON scorer but `11/12` after a descriptive fence removal. Ordinary
practice then scored `11/12` strict without the anchor in every seed. The
content was already present; the small fit made it usable by the interface.
Training with the anchor did not add a benefit: after withdrawal it scored
`10/12`, `9/12`, and `9/12`, and with the anchor present it scored `8/12` in
all three seeds versus OFF's `10/12`. No fitted cell reached the prospectively
defined `12/12` operational screen.

Therefore:

- retain the four-field record as a syntax/interface preservation canary;
- do not inherit any perception-fit adapter into Level 1 or Level 2;
- do not call fence removal or strict-format transfer improved perception; and
- do not use anchor-trained perception as evidence that context distillation
  works. It was not context distillation: the anchor was present in training.

### Correction exists as a path, but not yet as useful learned material

The fresh two-wake diagnostic proved that a public outcome can reach a child's
Scratchpad and then its next wake. It did not improve the primary outcome:
process and sham arms both solved `1/32` on wake 1 and `2/32` on wake 2. Only
one process-arm case and two sham cases formed qualifying failure-to-success
corrections.

The selected-material follow-up is an equally important warning. Replaying a
whole 236-byte Scratchpad solved only `0--1/32`; replaying the exact 42-byte ACT
span solved `1--2/32` and produced much better strict formatting. This does not
show that reflection is generally harmful. It shows that unscored reflective
prose is not automatically a useful SFT target. The next module must score the
reflection's *consequence* on another action.

### The first combined birth argues for modularity

The 256-row AUTH birth installed obvious routines (`32/32` PROSPECT and
`58/64` REVISE), but it missed the stronger locality twins (`26/32` where
`29/32` was required) and reduced addition to `15/16`. DERANGED also expressed
its supplied map. A large joint score can therefore hide conditional-selection
and preservation failures. A module advances only on its own negative cases
and cross-module preservation tests.

## 2. The modular birth stack

The birth program should eventually contain several independently qualified
modules, but the first Level-2 child waits for only one.

| module | role | status in this bridge |
|---|---|---|
| `M0 RECORD` | keep prediction, action, outcome, and later revision separate; emit the native interface | **canary only** from the perception result; not a semantic ancestor |
| `M1 CORRECT->REUSE` | compare prediction with outcome, accept or reject a parent's process correction, revise only the implicated belief, and apply it on a different case | **the sole Level-1 arsenal experiment and first Level-2 candidate** |
| `M2 ALLOCATE` | choose THINK, ACT, or transition-to-next-state under generous tokens; stop a completed subtask without ending the life | prepare and screen in parallel; does not gate M1 Level 2 |
| `M3 CONNECT` | retrieve relevant supplied events, create only supported links, identify a missing edge, and seek information | later birth module feeding the authentic M traversal experiment |

If M1 qualifies, release it. Do not wait for M2 or M3. If a later module
qualifies, retrain a new combined birth from the clean base on the union of the
qualified corpora; never average adapters and never splice the later module
into the already-running M1 Level-2 lineage.

## 3. The exact M1 task grammar

M1 is one causal transition, not two loosely related prose skills:

```text
public prior/prediction -> public action -> public outcome
    -> assess MATCH / MISMATCH / UNSUPPORTED
    -> KEEP or REVISE only the warranted relation
    -> choose the next externally scored action on a different situation
```

Use four unrelated, generated microdomain families: opaque Boolean boxes,
small route choices, resource/scheduling choices, and object transformations.
Three families are TRAIN; the fourth is held out as the parent-withdrawn DEV
family. Level 2 later uses a fifth generator and fresh vocabulary.

TRAIN has exactly `48` source situations: `16` in each family and `12` in each
of four balanced strata:

1. prediction contradicted -> revise and switch;
2. prediction confirmed -> keep and reuse;
3. no genuine pre-action prediction -> mark unsupported and run a test rather
   than inventing hindsight; and
4. a plausible but irrelevant parent correction -> ignore it and preserve the
   unrelated belief.

Each accepted target uses the same short native three-field surface:

```text
ASSESS: <MATCH|MISMATCH|UNSUPPORTED>
SCOPE: <KEEP relation|REVISE relation|NO CLAIM>
NEXT: <native task action>
```

The parent-withdrawn DEV set has `32` fresh situations: eight from every
stratum. Its **primary** prompt requests only the native task action. A
separate 32-item process panel requests the three fields above. Thus the model
cannot earn the main endpoint by producing more reflective words. Exact syntax
and semantic fields are reported separately.

Before any fit, run the frozen child on the 32 DEV situations with and without
a correct temporary correction. This is a headroom diagnostic, not a result.
The distillation/open-loop routes are eligible only if temporary help produces
at least eight net action corrections, helps at least six cases in both the
revise and non-revise halves, and causes no more than two regressions. Authored
SFT may still run if this elicitation test fails; that outcome says the current
parent scaffold cannot supply CD targets, not that the disposition is
untrainable.

## 4. Level-1 fine-tuning arsenal

All three routes use the same 48 source identities, target grammar, frozen
base, LoRA shape, response-only loss, generic replay set, and held panels. They
differ only in how the 48 target continuations are obtained.

### `A-SFT`: authored demonstrations

A model-free generator emits the correct three-field continuation from public
state. This is the strongest small positive control: can ordinary supervised
post-training install the correction-to-action grammar at all? It is trained
behavior, never child experience.

### `CD-STRIP`: context-distilled continuations

For every source state, give the frozen child one fixed correction or worked
analogue, sample four continuations with predeclared seeds, and retain the first
continuation that passes the external task and semantic checker. Train a fresh
child on the original state to that continuation **after removing the
correction/analogue from the input**. The temporary help is absent from both
the final training input and every held readout. A source with no correct
candidate is a formation failure, not a teacher-authored repair.

### `P-RS`: rejection-sampled parent-steered open-loop data

Run four no-update two-wake trajectories per source. The child attempts, sees
the public result, receives one parent process response, reflects, and attempts
an analogue. The parent may use the public transcript but not hidden rules,
DEV cases, scores, or future outcomes. Keep the first trajectory, in
predeclared seed order, whose later action is externally correct and whose
scoped revision is source-supported. At SFT time use the same reduced public
state as the other two routes: keep the actual prior/action/outcome, remove the
parent message, and use only the committed child continuation as the target.
The parent is visible during open-loop collection but absent from the SFT input,
target, and readout. This remains Level-1 **trained** data: researchers created
the nursery, parent policy, acceptance rule, and corpus. No update is mounted
during collection. A separate parent-visible SFT arm would test responsiveness
to advice and is deliberately outside this smallest comparison.

For comparability, every route must supply one accepted target for all 48
registered source slots. Shortfall remains a result and the route does not fit.
Do not resample past four candidates, replace a hard source, or backfill with
authored text. The target grammar keeps response lengths close; report exact
supervised-token totals. If totals differ by more than 10%, add a
target-token-dose-yoked authored diagnostic for the selected route rather than
silently duplicating rows.

### Fixed trainer and preservation replay

- Qwen2.5-7B-Instruct frozen base, fresh rank-8 LoRA for every fit;
- alpha `16`, dropout `.05`, the existing all-layer attention+MLP targets;
- ordinary response-masked cross-entropy, LR `1e-4`, batch `8`, four epochs;
- `48` new-skill rows plus `24` fixed native replay rows per epoch;
- `72 / 8 x 4 = 36` optimizer updates and `288` row presentations per fit;
- new-skill dose is never displaced by replay;
- user prompt, public environment history, and padding tokens always have zero
  target loss; parent text has been removed before encoding;
- no packing across independent situations; fresh optimizer and clean base.

The replay set covers native tool syntax, concise ordinary answers,
addition/copy, abstention, and the M0 record canary. It contains no M1, Level-2,
deployment-gym, or inspected test content.

Do not sweep rank, LR, replay ratio, and corpus route together. This first
experiment is about data production. A later rank or objective change requires
a named successor after a diagnosed capacity or optimization failure.

## 5. Level-1 controls, selection, and release threshold

### Stage L1.0 -- source and no-fit closure

Two independent CPU checkers must agree on all 80 TRAIN+DEV targets, strata,
action consequences, and correction relevance. Verify whole-family separation,
balanced label/action positions, no answer-by-ID or template, exact target masks,
no truncation, and zero Level-2/final-gym vocabulary.

### Stage L1.1 -- one-seed arsenal screen

Fit `A-SFT`, `CD-STRIP`, and `P-RS` independently at learner seed 0. Compare
each against the contemporary no-adapter `OFF` on:

- 32 action-only application items;
- 32 process items;
- all other module/canary panels; and
- 32 irrelevant or ordinary-task items.

A route passes the screen only if every condition holds:

1. action accuracy is at least `26/32`;
2. paired relative to OFF, net corrections are at least `8/32`, with no more
   than two OFF-correct -> fitted-wrong regressions;
3. revise and do-not-revise halves are each at least `13/16`;
4. process semantics are at least `26/32`, strict syntax at least `30/32`, and
   no unsupported field is invented;
5. no other 32-item module/generic panel loses more than one correct item
   (`2/32` would exceed the frozen `-0.05` adverse bound); addition and copy
   remain at least `15/16`; and
6. the primary gain survives an action-only prompt and is not explained by a
   parser repair, longer output, or a present parent message.

These are engineering promotion thresholds, not p-values. Report every paired
item and all failed routes.

If multiple routes pass, select one by a predeclared lexicographic rule:
action-only accuracy, fewer paired regressions, process-semantic accuracy, then
fewer generated/training tokens. Do not mix their corpora yet.

### Stage L1.2 -- confirmation and active control

Refit the selected route from clean base at learner seed 1. It must satisfy the
same six gates. Then create a target-permuted corpus using the same input and
target-text multisets, with a fixed-point-free permutation within each stratum,
and fit it at the eventual release seed. This is the active test against style
or ritual learning.

Finally refit the authentic selected corpus once at prospectively fixed release
seed 2. Release that exact adapter as `L1_M1_RELEASE` only if:

- both seed-1 and seed-2 authentic fits satisfy all six gates;
- seed-2 authentic exceeds seed-2 target-permuted by at least `6/32` on the
  action panel;
- the permuted adapter is no more than `2/32` above OFF on authentic scoring;
- every adapter/checkpoint, target span, corpus, prompt, seed, and result is
  hashed before Level-2 material exists; and
- an empty-context reload reproduces the release result.

Seed 0 chooses the route; seed 1 confirms it; seed 2 is the predeclared deployed
artifact. This prevents deploying whichever optimizer seed happened to look
best. If only one module qualifies, that is enough. M2/M3 remain parallel work,
not blockers.

## 6. Contamination firewall

The firewall is scientific, not ceremonial.

1. **Birth-only ancestry.** Every Level-1 fit starts from the same authenticated
   base and zero adapter. Perception, Q0, RuleGame, correction-utility,
   CompilerGym, E0-r, and inspected development adapters are siblings, never
   ancestors.
2. **Downstream generated after freeze.** The Level-2 generator family, root
   seeds, opaque names, mappings, actions, prompts, and report cases are
   materialized only after `L1_M1_RELEASE` and its hashes are sealed. The birth
   authors never inspect them.
3. **No deployment knowledge.** No CompilerGym program, pass, score, solution,
   repo-derived strategy, or final benchmark identifier appears in birth,
   replay, parent prompts, Level 2, or canaries.
4. **Parent visibility.** In Level 1 the parent sees only TRAIN public events.
   In Level 2 it is a frozen answer-blind process tape shared across arms. It
   never sees hidden mapping, report answers, arm, adapter state, or score.
5. **Thinker/compiler line.** In Level 2, every semantic target byte must occur
   in a child generation after the supporting public receipt. The compiler may
   verify, reject, copy, order, and repeat exact child spans and add loss-masked
   wrappers. It may not repair a field, write an action, infer an endpoint,
   paraphrase a target, or select by future performance.
6. **Context deletion.** Parent text, nursery text, raw episode context,
   checker output, and report cases are absent from every parent-free readout.
7. **Terminal descendants.** Any child that enters a Level-2 root is forever
   contaminated for fresh childhood or final deployment comparison. It may
   continue only within that root's declared longitudinal life.
8. **No feedback tuning.** A Level-2 result cannot change the released birth,
   writer constants, root replacement rule, or thresholds. A change creates a
   newly named recipe and new roots; old evidence remains.

## 7. Earliest safe Level-2 PROMOTE versus SHADOW experiment

### Fresh task

After the release hash, generate one excluded DEV root in a fifth microdomain.
It contains two balanced complementary hidden orientations, 16 opaque source
situations divided into two eight-event blocks, and independent action-only
report cases. Identifiers, actions, outcome wording, family, and renderings are
new. Two independent CPU solvers certify the public consequences and that no
pre-outcome bytes reveal a hidden orientation.

Each event runs:

```text
child predicts and acts
    -> environment returns an ordinary public receipt
    -> fixed parent tape asks it to compare, scope, and prepare what is useful
    -> child emits its own committed record
```

The compiler accepts a record only when every semantic field is supported by
the child's prior prediction/action and public receipt. Invalid records become
zero-loss slots; they are never repaired. Four duplicate/no-new-information
events per root require the child to emit `SKIP` and are never fitted.

### The 2 x 2 and one active control

Use two starting children and two publication policies:

| starting child | `PROMOTE` | `SHADOW` |
|---|---|---|
| released M1 birth | train the candidate SLEEP and mount it | run the same SLEEP, preserve artifacts, do not mount it |
| no-birth base | train and mount from its own records | train but do not mount from its own records |

Within each starting-child pair, collect block 1 once and fork only after its
child records close. Thus its first PROMOTE and SHADOW write candidate is
byte-identical. Add a predeclared `BIRTH-SHUFFLE` active branch whose accepted
child targets are permuted within semantic stratum at matched tokens and dose.
It may never become ancestry.

### Two SLEEPs -- the minimum closed loop

1. **SLEEP 1:** fit from block-1 child records. PROMOTE mounts the candidate;
   SHADOW retains the exact birth state. Clear active context and test 16 held
   action-only cases.
2. **Wake 2:** PROMOTE and SHADOW now act on the same new block-2 situations
   under matched generation seeds. Their actions, outcomes, and child-authored
   records may diverge; that is the intended loop mediator.
3. **SLEEP 2:** independently compile each branch's exact old+new child records
   and retrain cumulatively from its frozen starting child with fresh optimizer
   state. PROMOTE mounts; SHADOW's candidate is preserved but not mounted.
   Clear context and test 16 old plus 16 new action-only cases.

One SLEEP would prove only that a child-authored corpus can alter an output.
Two are the minimum here because SLEEP 1 can change the experience and material
that enter SLEEP 2.

For each candidate write use rank 8/alpha 16/dropout `.05`, response-only CE,
LR `3e-5`, eight fixed source slots, batch 8, 20 complete replay passes/updates,
fresh AdamW, and no birth-corpus replay. Repetition copies exact child-authored
rows; it does not invent a new semantic view. SLEEP 2 starts from the frozen
starting child and trains on the full accepted block-1+block-2 union, not an
adapter average. These are a prospective small-write setting, not an asserted
optimum.

Before mount, a transactional gate requires candidate loadability, exact target
spans and provenance, at least `7/8` valid direct reads of accepted records,
native syntax, and no greater than `.05` adverse change on the frozen generic
canary. A failed candidate is not mounted and the root records a failed SLEEP;
there is no retry or hyperparameter rescue.

## 8. Exact Level-2 thresholds and release ladder

Let `Y[b,p,k]` be correct action-only responses, where `b` is birth or base,
`p` is PROMOTE or SHADOW, and `k` is after zero, one, or two SLEEPs. The final
panel has 32 items. Define the weight-publication effect
`D_b(k)=Y[b,PROMOTE,k]-Y[b,SHADOW,k]` and the birth interaction
`I(k)=D_birth(k)-D_base(k)`.

The excluded DEV root earns `LEVEL2_CLOSED_LOOP_DEV_PASS` only if all hold:

1. **Headroom:** before evidence, neither starting child exceeds `24/32` and
   birth/base differ by at most `4/32` on the fresh action panel.
2. **Formation:** birth produces at least `6/8` admitted records in each block,
   scores at least `3/4` on SKIP, and every admitted target hashes to an exact
   child span after its source receipt.
3. **First write:** on the 16 block-1 cases, `D_birth(1) >= 4/16`, positive in
   both hidden orientations.
4. **Second write:** `D_birth(2) >= 8/32`, final birth-PROMOTE accuracy is at
   least `24/32`, and the birth interaction `I(2) >= 6/32`.
5. **New plus old:** birth-PROMOTE exceeds birth-SHADOW by at least `3/16` on
   the new block, while old-block accuracy loses at most `1/16` from its
   post-SLEEP-1 value.
6. **Semantic control:** authentic birth-PROMOTE exceeds BIRTH-SHUFFLE by at
   least `6/32`; shuffle remains action-legal and within `.05` of SHADOW on
   generic canaries, so its loss is not malformed collapse.
7. **Retention:** the parent-free M1 action panel remains at least `24/32` and
   loses no more than `2/32` from the release artifact; M0 syntax stays at least
   `30/32`; addition and copy stay at least `15/16`.
8. **Isolation:** wrong-root cross-mount produces zero usable recalled records,
   all five branch identities are exact, and every visibility/custody/resource
   check passes. Invalid actions, rejected rows, failed writes, and truncations
   stay in their original denominators.

The process fields, admission rate, amount of thought, and block-2 corpus
quality are mediators. None can substitute for the action thresholds.

A DEV pass freezes the complete Level-2 protocol and releases exactly eight
new independent confirmation roots. It does **not** itself establish a general
learning capability. A bounded paper claim requires at least `7/8` roots to
pass the complete conjunction with no root replacement. Against a `.5` root
pass null, the exact one-sided sign tail for at least 7 of 8 is `9/256 =
.0352`; report the full vector and paired effect sizes, not prompts as
independent samples.

Failure labels preserve useful localization:

- direct M1 pass but no PROMOTE advantage: `INSTALLED_CORRECTION_ROUTINE_ONLY`;
- PROMOTE advantage equally large from base: `GENERIC_CHILD_RECORD_WRITE`;
- process prose improves but actions do not: `REFLECTION_PERFORMANCE_ONLY`;
- block 1 changes actions but block 2 forms no usable material:
  `CLOSED_LOOP_FORMATION_FAIL`;
- old items regress after SLEEP 2: `CUMULATIVE_RETENTION_FAIL`;
- shuffle matches authentic: `STYLE_OR_RITUAL_NOT_BINDING`;
- a writer/visibility/custody fault: `ASSAY_INVALID`, never a scientific null.

## 9. Staged cost and parallel schedule

The counts below are prospective ceilings, not measured runtimes. The terminal
perception comparisons took roughly 16--19 A40-minutes per complete seed for
two fits plus six readouts, and the larger birth component took about 24
A40-minutes for two fits plus 384 readouts. Native profiling must tighten each
cap before launch.

| stage | work | prospective ceiling |
|---|---:|---:|
| source/no-fit | two CPU solvers; 64 no-fit calls | `0.5` A40-h |
| corpus formation | 48 CD calls plus up to 192 open-loop child trajectories and parent calls | `1.5` A40-h plus separately logged parent inference |
| arsenal screen | 3 fits x 36 updates; OFF and cross-panels | `2.0` A40-h |
| confirmation/release | authentic seed1, authentic seed2, seed2 permuted; 3 fits and panels | `2.0` A40-h |
| Level-2 DEV | 8 small fits maximum including SHADOW candidates and shuffle; two wakes/two sleeps | `2.0` A40-h |
| Level-2 CONF | 8 roots x same maximum | `16` aggregate A40-h, roots parallel |

The smallest Level-1 path is therefore six fits, `216` optimizer updates, plus
generation and probes. It is hours, not a seven-day childhood. Its purpose is
to produce the first safe starting module for a real learning loop.

Run in parallel:

- materialize and CPU-audit all three M1 corpus routes independently;
- run CD generation and parent-steered open-loop collection on separate GPUs;
- fit A-SFT/CD-STRIP/P-RS from clean base simultaneously;
- prepare M2 and M3 no-fit/source fixtures without combining them;
- build and audit the Level-2 generator/checkers, but do not materialize the
  actual root seeds or vocabulary before the M1 release hash;
- continue full-dose writer diagnostics as a sibling campaign; no Q0 or E0-r
  adapter becomes M1 ancestry; and
- after protocol freeze, run the eight Level-2 confirmation roots in parallel.

Do not parallelize within a root across its causal order: block 1 -> SLEEP 1 ->
wake 2 -> SLEEP 2. Do not let a faster or more verbose classroom contribute
more than its registered source slots.

## 10. What this buys the full Dream--LoRA--Think program

This bridge is intentionally smaller than the paper objective.

- Level 1 asks whether standard post-training can install one selective
  state-to-state learning behavior and which ordinary data route is best.
- Level 2 asks whether that trained readiness helps a child turn its own
  public action--outcome experience into its next behavior across two sleeps.
- The authentic M experiment must then add child-authored EVENT and LINK
  memories, goal-conditioned traversal, information-seeking expansion, and
  old+new reuse.
- The L experiment must vary lifetime, compare against ACTIVE_LINKED_TEXT,
  full child text, RAG/graph/context, frozen-sleep, and final-batch controls,
  and establish where the strongest memory baseline saturates.

The recurrent building rule is therefore concrete: **one birth module that
passes may enter one closed-loop DEV root immediately; it need not wait for a
perfect birth. Passed modules remain reusable evidence, failed modules remain
local diagnoses, and the full child is assembled only by clean-base corpus
retraining after the pieces work.**

## Evidence and design sources

- `research_notes/astra_memos/ASTRA_PERCEPTION_THREE_SEED_2026-09-13.md`
- `research_notes/astra_memos/ASTRA_FRESH_CORRECTION_TERMINAL_2026-09-12.md`
- `research_notes/astra_memos/ASTRA_CORRECTION_UTILITY_TERMINAL_2026-09-12.md`
- `research_notes/astra_memos/ASTRA_BIRTH_COMPONENT_RESULT_2026-09-13.md`
- `research_notes/astra_memos/receipts_20260912/astra_birth_next_probe_options_20260913.md`
- `research_notes/analysis/2026-09-13_modular_birth_posttraining_evidence_and_protocol.md`
- `research_notes/analysis/2026-09-13_minimum_authentic_child_authored_m_bridge.md`
- `research_notes/analysis/2026-09-12_level1_birth_level2_sample_hostile_validity_audit.md`
- Rohin messages 31--32 in
  `research_notes/THESIS_RAW_ROHIN_2026-09-11.md`
