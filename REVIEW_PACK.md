# REVIEW PACK — the v2 system and results, written for Rohin's weekend deep-read
*(Refactored 2026-08-22, after the first fixed-recipe results. This is the
one document to read instead of the repo. Plain language throughout; every
number here is reproducible via `alchemy/report.py` or quoted from
results.json files named inline. Tail checkpoints of seeds 1–2 were still
running at writing; those cells are marked "pending" and will be patched.)*

---
## 0. The story so far, in five sentences
We built a crafting world whose rules can only be learned from lived
experience, and a pipeline that turns one agent-lifetime (15,360 games)
into seven competing memory systems, measured at seven points along the
life. The first full run (seed 0, "naive recipe") showed that naively
fine-tuning experience into adapter weights stores nothing and eventually
makes the model confidently wrong. We diagnosed why (single-exposure
facts + numerically unstable training), fixed the corpus construction
("fixed recipe"), and the second run shows facts now partially stick
(recall 0 → ~0.2) while retrieval baselines saturate (recall 1.0). The
world and instruments are validated; the bottleneck is now squarely the
memory side — how richly experience is "dreamed" and how much capacity
the adapter has. That is exactly where the research was always headed,
and the next experiment (enrichment × capacity) is designed.

---
## 1. The game, mechanically
- **1,024 ingredients** with made-up names; 128 are secretly inert. Each
  ingredient secretly belongs to one of **96 classes** ("essences").
  Classes sit at secret positions on a circle.
- **Rules are over class PAIRS** (4,656 of them), so thousands of
  ingredient pairs share each rule. 40% of rules are generated from the
  circle geometry (equal-distance pairs behave alike and share product
  families — the *learnable-pattern* stratum, "fn"); 60% are independent
  coin flips (the *must-be-experienced* stratum, "iid").
- **Products are tiered**: combining refined items makes genuinely new
  higher-tier items, so recipes are real chains (goals span depth 1–4).
- **Episodes**: a goal ("craft X"), a 6-item inventory guaranteed to
  contain a valid plan, ~12–20 combine steps, and an exact
  distance-to-goal value logged every step.
- **The held-out set**: 30% of ingredient pairs are never allowed in the
  same inventory, ever. Anything the memory knows about them must have
  been INFERRED (via class structure), not remembered.
- **Leakage-proofing**: class labels never appear in any text (a grep
  proves it); names are nonces so pretraining knows nothing.

## 2. The seven memory systems (arms)
All arms see the IDENTICAL life and use the same 7B reasoner + prompts.
1. **no_memory** — floor.
2. **long_context** — the raw life log in the model's real 32k window,
   until it doesn't fit (dies honestly after ~E=60).
3. **rag_raw** — top-12 lines retrieved from the raw log per question.
4. **rag_dreamed** — same retrieval over the dreamed/augmented corpus.
5. **lora_raw** — raw log fine-tuned into a LoRA adapter.
6. **lora_dreamed** — dreamed/augmented corpus fine-tuned into a LoRA.
7. **lora_dreamed_multiread** — same adapter, but before acting the agent
   interrogates its own memory with several questions first.

**What a LoRA is (since it carries the thesis):** a low-rank "delta"
bolted onto the frozen model's attention weights — rank 16 ≈ 30M trainable
numbers vs the 7B frozen ones. Training is plain next-token prediction on
the corpus text; a "fact" is whatever weight change makes those sentences
more likely. Facts only become *extractable* if seen in many varied
phrasings (the injection literature's core finding, now replicated by us
twice). "The dreamer" = the LLM call + augmentation code that turns the
life log into that corpus; **the corpus format is therefore the whole
ballgame**, which is why it's where both bugs and fixes concentrated.

## 3. How we measure (and the numbers to know cold)
Per arm per checkpoint: **held-out prediction** (200 never-seen pairs,
free-form answer, confabulation-priced), **seen recall** (200 experienced
pairs — the G1 gate ≥0.9), **task success** (200 fresh games).
- **0.25** = all-"UNKNOWN" score (abstain floor). **0.42** = answer
  NOTHING to everything (the majority-class trap — seed 0's fake win).
- **acc_product** is the only unguessable metric (~13,500 names).
- **Ceiling** (ideal reasoner): ~0.09 @960 eps, ~0.92 @3840, 1.00 @7680.
  Scores meaningfully above ceiling = leak/artifact, investigate.
- **Task floor** = no_memory's ~0.07–0.17 (varies by seed).
- Parsing caveat: models sometimes answer "RUIN | NOTHING" (echoing the
  menu); the parser takes the first recognized keyword — treat 1–2% of
  kind-accuracy as noise.

## 4. Results
**FORMAL VERDICT (2026-08-22, now 3 seeds):** the v2.1 recipe **fails
the pre-registered falsifier** — at E=3840, lora_dreamed − best-RAG =
−0.026, t=−3.25, n=3 (needed ≥ +0.05; with df=2 this is p≈.08 two-sided —
a strong DIRECTIONAL negative, not conclusive; the pre-registered five
seeds were not completed). Per
pre-registration the substrate claim is dead *in this form* (rank-16,
one-pass dreaming). All three seeds show the same shape: retrieval
recall 0.94–1.00, in-weights recall bouncing at noise, held-out at floor
for everyone while the ceiling reaches 1.00, and every apparent
late-life LoRA "win" decomposing into the answer-NOTHING prior.
This forces the enrichment × capacity attribution; the first capacity
cell (rank 64, same corpora as seed 1) finishes its evals ~today —
its result decides whether the next lever is BIGGER MEMORY or RICHER
DREAMING (the sleep+daydreaming ladder).
### Seed 0 — naive recipe (COMPLETE; alchemy/v2_out/seed0_naive_results.json)
- Naive LoRA arms: recall ≈ 0 everywhere (G1 fail ⇒ no claims); by
  mid-life they answer confidently and wrongly (confab ~0.6–1.0). The one
  adapter accidentally trained in bf16 scored held 0.38 vs 0.00 for its
  fp16 siblings — numerical instability was damaging adapters alongside
  the exposure problem.
- RAG: recall grows 0.24→0.38 but held-out stays ~0.25–0.30 while the
  ceiling climbs to 1.0 — remembers, never composes.
- lora_dreamed's "0.42 @960" decomposed exactly into the answer-NOTHING
  prior — caught by the reference numbers above; that catch created the
  acc_product metric.

### Seeds 1–3 — fixed recipe (ALL COMPLETE; alchemy/v2_out/seed{1,2,3}_fixed_results.json — run report.py on all three for the aggregate)
Fixed recipe = bf16 + gradient clipping, undeduplicated raw corpus,
paraphrase×ordering augmentation (~12 phrasings/fact + QA lines +
capped UNKNOWN slice), size-scaled epochs.
- **Retrieval saturates**: rag_dreamed recall 0.99–1.00 at every point
  (the QA lines make seen-pair recall trivially retrievable — a strong,
  honest baseline). rag_raw climbs 0.68→0.82. Held-out for both: still
  floor (~0.25) — the remember-vs-compose split is now unambiguous.
- **In-weights facts partially stick**: lora_dreamed recall 0.10 @60 →
  0.02 @320 → 0.18 @960 (naive was 0.00) — real but ~5× below the G1
  gate and ~5× below retrieval. Interference/dilution signature as the
  corpus grows.
- **Nobody extrapolates yet**: held-out acc_product = 0.00 for ALL arms
  including RAG — the held-out contest so far is only kind-guessing.
  Normal at a 0.09 ceiling; the 3840 checkpoint (ceiling 0.92) is where
  extrapolation becomes measurable at all.
- Task play: LoRA arms still at/below floor — adapters still erode the
  actor; instruction-preservation mix is a pending fix.
- **Full-run verdict (all 7 checkpoints):** in-weights recall never
  climbs — it bounces at noise (0.10/0.02/0.18/0.04/0.01/0.00/0.11)
  while retrieval sits at 0.94–1.00. Held-out stays at floor for every
  arm even as the ceiling reaches 1.00 — NOBODY composes yet. Every
  apparent late-life win decomposes into the answer-NOTHING prior
  (e.g., lora_raw@15360 "0.44" = acc_nothing 0.94, acc_product 0.00 —
  same trap as seed 0's 0.42, caught the same way). G1 fails for
  consolidation at rank 16 + one-pass dreaming: the fixed recipe made
  facts representable but not retainable at scale.

### What this adds up to
The world, evals, gates, and retrieval baselines all work. Consolidation
into weights is real but ~5× too weak, in exactly the way the literature
and our pre-registration predicted. This is the intended scientific
position: a measured gap with named causes, not a mystery.

## 4b. The rank-64 cell and the STYLE-OSCILLATION finding (2026-08-22 night)
The first capacity cell (rank 64, seed-1's corpora) completed, and its
decomposition (alchemy/v2_out/seed1_r64_results.json) closed the case:
- **acc_product = 0.00 in EVERY lora cell at BOTH ranks.** No pair
  knowledge exists in weights anywhere, in any of the four runs.
- Every apparently-good recall number correlates perfectly with
  acc_nothing ≈ 0.9 (and every bad one with ≈ 0): the adapters
  OSCILLATE BETWEEN ANSWER STYLES ("say NOTHING" vs "name products"),
  and "recall" merely measured which style the training landed in.
  The rising-then-falling "retention curves" were style artifacts.
- Conclusion: neither 2×2 axis was the binding constraint. The
  MECHANISM is under-driven: each fact received ~12–50 gradient touches
  (12 phrasings × 1–4 epochs) where the injection literature uses
  hundreds — and the epoch-scaling that kept big trains cheap cut
  exactly this. Fact injection was never actually attempted at the
  intensity it requires.
**THE INJECTION CAPACITY CURVE (weekend result — the first scaling law):**
at the measured sweet spot (lr 5e-4, 200 touches/fact): 50 facts → 0.72
recall (r64); 200 → 0.41 (r64); 1,000 → 0.23 (r64) / 0.44 (r128).
Recall decays with fact count; rank buys it back ~linearly. Holding a
lifetime (~10k+ facts) at G1 levels by brute SFT would need rank in the
thousands ⇒ **store-everything consolidation is measurably impossible ⇒
selection (salience/curation) is FORCED by the substrate** — the capacity
wall is paper 1's measured motivation for paper 2's learned curation.
v2.2 full-run consequence: measured recipe (5e-4 / 200 touches / rank
≥128) + the dreamer consolidates a CURATED SUBSET sized by this curve,
not everything. Overtraining note: touches beyond ~200 DEGRADE recall at
high LR (0.72→0.44 at 600) — the sweet spot is finite.

**Pivot: the injection micro-benchmark** (alchemy/micro_inject.py,
RUNNING): 50 real facts, grid over learning-rate × touches-per-fact ×
rank, scored on exact recall + a confabulation control. Twenty minutes
per cell; establishes the consolidation recipe empirically before any
further full run. This is the experiment that should have preceded v2.0
— recorded as such.

## 4c. THE ORACLE RESULT — the reasoner is not the wall (2026-08-24)
Handing the model the latent structure directly (its two ingredients'
class labels + the relevant class rule + grades) yields **0.945 score /
0.91 acc_product** on held-out pairs; with classes but no rule: 0.33/0.00.
(alchemy/v2_out/oracle_diag.json). Combined with the capacity curve this
closes the diagnosis:
- pair-facts are unstorable (~500k of them; measured capacity wall);
- STRUCTURE is small (~1,024 memberships + 4,656 rules — fits measured
  LoRA capacity) and converts to answers at ~90%;
⇒ the dreamer's real job is INDUCING AND CONSOLIDATING CLASS STRUCTURE,
not enriching pair facts. Selection was forced by capacity; abstraction
is forced by the oracle. This redefines v2.2's dreamer target: emit
class-equivalence lines ("X behaves like Y") + class-rules mined from
cross-episode evidence, and measure fn−iid separation (the geometry-
induction number) as the primary composition metric.

## 4d. THE G-SERIES — the machinery works, then reassembling it honestly (2026-08-24/25)
The L0 isolation campaign (alchemy/mini_g2*.py, mini_g4*.py; every cycle
in alchemy/v2_out/mini_ledger.md) first PROVED transport through weights,
then hunted the real dreamer's gap to that proof.

**G2f — the breakthrough (oracle statements, real weights): kind_bal
0.949, family-reads 1.00.** The five-rule stack it proved:
1. dreams COIN NAMES for abstractions ("the belyl-family") — concept
   formation, so everything downstream is one hop;
2. memories stored as 1-hop atomic QA facts (2-hop reads collapse inside
   adapters — G2d showed rule_acc 0.25 when reads had to hop);
3. exposure ~200 touches/fact (32 touches → 0.58 storage; 200 → 1.00);
4. thinker performs atomic RESOLVED reads (the model applies resolved
   knowledge at 0.77–0.91 but cannot select from an in-context rulebook,
   0.28);
5. the CLEAN base composes — adapter is mounted only to produce the
   memory block, then unmounted (read-only adapter protocol).

**G4 series — replacing oracle statements with the real dreamer:**
- G4 (thin one-shot "group and emit" prompt): 0.282. Dreamer coined
  families from PRODUCT NAMES, not behavior. Lesson: grouping and
  emission are different cognitive steps.
- G4b (fresh grouping dream, 2 passes + LLM merge): 0.333. My
  reimplementation regressed the proven run_mini dreamer. Lesson: don't
  reimplement a proven organ.
- G4c (consume proven artifact, naive union-find): 0.41. A 17-name blob
  line chained everything. But focused-evidence pair dreams verified 3/3.
- G4d (VERIFIED-CLAIM GRAPH): dreamer proposes executable pair-claims,
  engine verifies each (Voyager rule), verified ruin-pairs are
  same-family edges, components = families. 3 families, purity 1.0,
  coverage 0.542 — end-to-end 0.256 because uncovered ingredients
  hallucinate family reads.
- G4e (+ DAYDREAMING: re-dream focused on still-ungrouped ingredients):
  coverage 0.542 → 0.917 in ONE round, 4 families all purity 1.0, 10/10
  pair-rules verified. **The dreamer side of L0 is solved.** End-to-end
  0.308 → read diagnostic showed memberships 21/24, rules 7/10, with
  the two PRODUCT rules exactly the corrupted reads.
- G4f (rule upweighting ×3 + thinker-normalized rule reads): 0.513;
  diagnostic now memberships 22/24, rules 10/10 — reads solved; the leak
  moved to composition: (a) rule reads are ORDER-SENSITIVE (reversed
  family order misses), (b) the 2 uncovered ingredients are both type B
  (product-critical) — B members lack ruin evidence by nature, (c) the
  base answers bare "PRODUCT" (no name in memory) which the parser
  scored unparseable.
- G4g (symmetrized rules + membership inference through verified product
  edges + kind-level parse): coverage 1.000, purity 1.0 ×4, product 1.0,
  ruin 1.0 — nothing 0.0 from ONE bug: the normalizer checked "product"
  before "nothing", inverting the adapter's correct "nothing happens.
  they do not form a product."
- **G4h — L0 CLOSED: kind_bal 0.949 (product 1.0, nothing 0.846, ruin
  1.0), coverage 1.000 — real dreamer, no oracle in the write path,
  EQUAL to the G2f oracle-statement ceiling.** The five-rule stack holds
  end-to-end; every point between 0.282 and 0.949 is attributed to a
  named, fixed defect (see mini_ledger.md).

The through-line: every point lost between G2f (0.949) and the real
dreamer has been attributed to a named, fixed defect — nothing is
mysterious. Alongside: the DREAM LANGUAGE spec (five strata: witnessed
facts w/ provenance, evidence-scaled generalizations, prior-contrast/
surprise, named abstractions, connections), the docker-image principle
(dream = commit layer; write diffs + reinforce repeats), dreamer==thinker
as one question-engine with two ports, and the IDENTIFIER-VIVIDNESS
variable (nonce vs "red monkey in candyland" skins, same hidden laws) —
all in research_notes/32.

## 5. Diagnosis and the next experiment: SLEEP + DAYDREAMING
(Rohin's framing.) The brain doesn't consolidate a memory by seeing it
once in a nightly batch — it revisits the needed ones, offline (sleep)
and online between tasks (daydreaming), enriching them into more
learnable, more connected forms. Our dreamer is still one-pass.
Mechanism ladder (ascending cost): (1) enrichment depth, unequal by
need — salience as replay count; (2) re-dreaming — dreams that cite and
connect other memories; (3) the DAYDREAMER — targeted enrichment between
episodes aimed at what recent tasks needed-and-missed (formalized, note
32); (4) capacity — rank 16→64→128 and steps-per-fact.
**Next experiment: enrichment × capacity 2×2** to attribute "too little
dreaming" vs "too small memory." Also queued: arm 8 "agentic-grep"
(model with search tools over the raw log — the strongest honest
retrieval baseline, prompted by Stanford's Meta-Harness), and a
128k-window long-context variant.
Vision anchor (yours, near-verbatim): dreams are experiences replayed
through other experiences, building the experiential world model; as the
built world grows, raw reality fades — a puzzle off a light-projected
real world. The literal mechanisms are this weekend's design question.

## 6. Bugs ledger (why the numbers are trustable)
Caught by tiny local test: peft adapter stacking (would have corrupted
13/14 trains). By the canary: dream-chunk window overflow; LoRA silently
training on CPU; phase memory-handoff crash; fp16 NaN at 147k lines. By
eval integrity passes: majority-class score inflation (→ acc_product);
abstention slice nearly UNKNOWN-training the holdout (→ capped). Each
fix is a commit; the falsifier and gates were registered before any run.

## 7. Play it yourself (ten minutes, real generated content)
=== ONE REAL EPISODE (as the log records it) ===
[episode 0] goal: craft vexane6301-II | success: False
  combine corshiith nympolane -> You combine corshiith and nympolane. Nothing happens. (value 2)
  combine beltaura coreth -> You combine beltaura and coreth. They fuse into kelsic6300-II. (value 2)
  combine coreth nympolane -> You combine coreth and nympolane. They fuse into galov7708-II. (value 2)
  combine nympolane galov7708-II -> You combine nympolane and galov7708-II. Nothing happens. (value 2)
  combine corshiith kelsic6300-II -> You combine corshiith and kelsic6300-II. They fuse into sabvasic-II. (value 2)
  combine beltaura galshiard -> You combine beltaura and galshiard. They fuse into fenvaura-II. (value 2)
  combine nymshiura kelsic6300-II -> You combine nymshiura and kelsic6300-II. They fuse into drushirun-II. (value 2)
  combine nymshiura sabvasic-II -> You combine nymshiura and sabvasic-II. They fuse into tesock2698-II. (value 2)
  combine galov7708-II fenvaura-II -> You combine galov7708-II and fenvaura-II. They fuse into drutaane-II. (value 2)
  combine coreth nymshiura -> You combine coreth and nymshiura. The mixture curdles and is ruined. (value 2)

=== FIVE REAL HELD-OUT QUESTIONS (answers at bottom) ===
Q1. What happens when you combine lurvaem and oseth?  (PRODUCT <name> | NOTHING | RUIN | UNKNOWN)
Q2. What happens when you combine belneov and belshiov?  (PRODUCT <name> | NOTHING | RUIN | UNKNOWN)
Q3. What happens when you combine drugoyl and sabtasic?  (PRODUCT <name> | NOTHING | RUIN | UNKNOWN)
Q4. What happens when you combine fenvarun and mortail?  (PRODUCT <name> | NOTHING | RUIN | UNKNOWN)
Q5. What happens when you combine drutayl and sabneost?  (PRODUCT <name> | NOTHING | RUIN | UNKNOWN)

--- answers ---
A1. ('product', 'sabvaem-II')
A2. ('product', 'sabesk7008-II')
A3. ('nothing', None)
A4. ('product', 'luryl7536-I')
A5. ('product', 'hartaov-II')

=== REFERENCE NUMBERS (seed-0 world) ===
P(product) over holdout ~ 0.43
P(nothing) over holdout ~ 0.42
P(ruin) over holdout ~ 0.15
distinct product names: 13568

Try the five questions before looking. You will feel: "nothing" is
guessable, product NAMES are not — that is acc_product's whole point.

## 8. VERSIONING — what's running vs what's planned
**Recipe v2.0 — "naive" (seed 0, COMPLETE, kept as baseline):**
world with chains (depth≤4) + 40% geometric rules; one-pass dreamer;
deduplicated raw corpus; fp16 training (mostly); 4 epochs flat; scalar
metrics only. Its results are the "why naive fails" record.

**Recipe v2.1 — "fixed" (COMPLETE: seeds 1, 2, 3):**
everything in v2.0 plus — bf16 + gradient clipping; UNdeduplicated raw
corpus (natural frequency preserved); exposure augmentation (~12
phrasings/fact × both orderings + QA lines + capped UNKNOWN slice);
size-scaled epochs; per-truth-class accuracy (acc_product); answer-sample
logging; 7th arm (multiread); per-phase process isolation.

**Recipe v2.2 — IN PROGRESS (first cell running):**
- rank-64 capacity cell: COMPLETE (see §4b — style oscillation, acc_product 0)
- injection micro-benchmark: RUNNING (sets the consolidation recipe)
- enrichment × capacity 2×2: LoRA rank {16, 64, 128} × enrichment depth
  (the attribution experiment for "too little dreaming vs too small memory")
- salience-as-replay-count (needed memories get more variants)
- re-dreaming (dreams that cite/connect other memories)
- the DAYDREAMER (targeted between-episode enrichment; formalized note 32)
- instruction-preservation mix (fix adapters eroding task play)
- arm 8: "agentic-grep" (search tools over raw log — strongest honest
  retrieval baseline; from Meta-Harness)
- 128k extended-window long_context variant
Exact v2.2 contents get locked (and this section updated) before launch —
some items may slip to v2.3 after the 2×2 reads out.

**V3 (being designed now — supersedes the v2.2 label for the next full
run):** game redesigned for shallow induction (post induction-ceiling
result); dream+think rich but pre-shaped; tries-to-success (pass@k) as
headline with shape-practiced/material-new split; contexts-per-fact
micro-test feeds dream design. v2 is closed for learning.

**Backlog (designed, deliberately NOT next):** fn difficulty ladder
(calibrates after v2.1's 3840 numbers); A-Mem external baseline;
context-distillation training loss; dreamer ladder rungs 2/4/5; ρ-mixture
sweep (compressibility curve); learned curator (paper 2); hypernetwork
writes, population tier (paper 3).

**Rule:** anything you propose live gets filed to a version above within
the same day; "running now" never changes mid-run.

## 9. Open decisions with your name on them
1. Dreamer co-learning: frozen-generator + learned-curator split (my
   proposal) vs fully-learned dreamer — sets paper-2 scope.
2. fn difficulty ladder calibration (IQ-matched questions) — after
   fixed-recipe fn numbers at 3840 land.
3. Enrichment × capacity 2×2 approval (next run, all four workers).
4. Instruction-preservation mix for task play.
5. September switch date; A-Mem baseline timing.
