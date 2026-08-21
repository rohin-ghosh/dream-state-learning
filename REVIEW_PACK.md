# REVIEW PACK — the v2 system, written for Rohin's verification
*(2026-08-21. One document, high-level first, depth below. Companion to
SPEC_V2.md; this is the "what was actually built and how to check it"
view. Everything here is generated from the real code — no hand-written
examples.)*

## 1. The system in plain language
An agent lives in an invented crafting world. Its whole life (15,360
game episodes) is recorded. From that one life we build seven different
"memories" (the arms), and at seven points along the life we freeze
everything and ask each memory three kinds of questions: what do you
know that you saw (recall), what can you work out that you never saw
(held-out prediction), and can you use it to win fresh games (task
success). The claim being tested: memory consolidated INTO model weights
keeps improving with experience where retrieval and long context flatten.

## 2. The three files that decide whether any number means anything
1. **alchemy/world.py** — the world generator. Decides the hidden
   structure (classes, geometry, chains). If this is wrong, we measure
   the wrong thing. Check: essences never appear in text; holdout pairs
   never co-occur in inventories; fn-pairs at equal distance share a
   product family.
2. **alchemy/dreamer.py** — the dream prompt + corpus construction.
   Decides what text the LoRA trains on. Check: DREAM_SYS prompt reads
   sensibly; augment_corpus emits both orderings x 6 templates and the
   abstention slice is CAPPED at 2,500 lines.
3. **alchemy/evals.py + eval scoring in run_v2.py** — decides what counts
   as correct. Check: parse_answer's formats; score_pair prices
   confabulation (right=1, unknown=0.25, wrong=0); per-truth-class
   accuracy (acc_product) exists.
Everything else (training loops, backends, monitors) fails loudly.

## 3. Reference numbers — memorize these five
- **0.25 = the abstain score.** A model that answers UNKNOWN to
  everything scores exactly 0.25. Any held-out score near 0.25 with high
  abstain-rate means "knows nothing, honestly."
- **P(nothing) over holdout ~ 0.42.** A model that answers NOTHING to
  everything scores ~0.42. THIS IS WHY seed-0's lora_dreamed "0.42 at
  E=960" was a prior, not knowledge. Any score near 0.42 with zero
  abstention is suspect until acc_product confirms otherwise.
- **~13,500 distinct product names** exist. Correctly NAMING a product
  is essentially unguessable — acc_product is the trustworthy knowledge
  metric. (Kind-guessing: product 0.43 / nothing 0.42 / ruin 0.15.)
- **Tier-3 ceiling (chain+mixture world): ~0.09 @960, ~0.92 @3840,
  1.00 @7680.** An arm meaningfully ABOVE the ceiling at a point = leak
  or artifact, investigate immediately; at/below = normal.
- **Task-success floor = 0.17** (7B, no memory, fresh games). LoRA arms
  BELOW this = the adapter is damaging the actor (seen in naive run).

## 4. Play it yourself (ten minutes, builds the gauge)
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


Commands to make more of these locally (CPU, seconds):
  PYTHONPATH=. .venv/bin/python -c "(see review pack commit for snippet)"
Or read a live seed's artifacts on-node:
  gpu/v2node_ssh.sh 'python3 -m json.tool ~/v2/run/seed2/life.json | head -50'
  gpu/gh200_ssh.sh  'python3 -m json.tool ~/v2/run/seed1/corpus_dreamed_960.json | head -30'
  gpu/v2node_ssh.sh 'cat ~/v2/run/seed0/results.json | python3 -m json.tool | head -60'
Render any results file as tables:  PYTHONPATH=. python3 alchemy/report.py <results.json>

## 5. Where results stand (as of this writing)
- **Seed 0 (naive recipe) COMPLETE** — the measured baseline: naive
  LoRA fails recall everywhere (G1 fail => no claims, by pre-registered
  gate); RAG recalls more and more but never composes (flat vs rising
  ceiling); the single bf16-trained adapter hugely outperformed its fp16
  siblings (numerical damage implicated alongside exposure).
- **Seeds 1 (GH200) + 2 (H100), FIXED recipe running:** bf16+clipping,
  no-dedup raw corpora, paraphrase-x-ordering augmentation, capped
  abstention slice, size-scaled epochs. First G1 verdict at their E=960.
- Fixes were driven by five canary-caught bugs + two eval-integrity
  catches (majority-class inflation; abstention-slice/holdout overlap).

## 6. Open decisions with your name on them
- Dreamer co-learning: frozen-generator + learned-curator split (my
  proposal) vs fully learned dreamer — decides paper-2 scope.
- fn difficulty ladder calibration (after fixed-recipe fn numbers land).
- 128k extended-window long-context variant for a fairer baseline curve.
- Whether task-play needs an instruction-preservation mix (if fixed
  recipe still erodes the actor).
