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

### Seed 2 — fixed recipe (E=60–960 done; rest pending)
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

### What this adds up to
The world, evals, gates, and retrieval baselines all work. Consolidation
into weights is real but ~5× too weak, in exactly the way the literature
and our pre-registration predicted. This is the intended scientific
position: a measured gap with named causes, not a mystery.

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

## 8. Open decisions with your name on them
1. Dreamer co-learning: frozen-generator + learned-curator split (my
   proposal) vs fully-learned dreamer — sets paper-2 scope.
2. fn difficulty ladder calibration (IQ-matched questions) — after
   fixed-recipe fn numbers at 3840 land.
3. Enrichment × capacity 2×2 approval (next run, all four workers).
4. Instruction-preservation mix for task play.
5. September switch date; A-Mem baseline timing.
