# 32 — v2 experiment design (adopted decisions, 2026-08-19)

Source: Rohin's design session (state/salience/dream/scaling). Canonical
one-pager: SPEC_V2.md. This note records the WHY behind each pin.

## Adopted
1. **Vocabulary:** "vibey memory" → **induced regularities** — generalizations
   over experience present in no single episode. The paper hangs on this term.
2. **Claim form:** not "we beat RAG" — **different scaling curve** (x = episodes,
   y = performance, one line per substrate) + measured crossover. Report the
   regime where RAG wins (exact recall) as instrument calibration. Map, not
   victory.
3. **Salience, two information sets (reconciled):** encoding-time salience =
   state, online, NO hindsight (filter into STM); consolidation-time salience =
   dream, offline, HAS episode outcomes (policy for LTM). The encoding/dream
   gap is a prediction error → dopamine = RPE, one predictor + supervisor.
   Two losses from one renorm pass (salience error trains state layer; corrected
   valuation trains prompter). **Formalize all four boxes (state/dream/use/
   salience), implement amortized, train none — that's papers 2–3.**
4. **Dreamer v2 = one prompted LLM call** over the life log (state, experiences,
   outcomes, value logs) → look-back memories as TEXT. Cross-episode patterns,
   NOT per-episode summaries (that's the thing RAG structurally can't produce).
   Dumb dreamer = raw transcription → separates substrate claim from policy
   claim (2×2). Renormalize-then-write: dream re-scores with hindsight.
5. **Append-only resolution:** the LOG is append-only; the LoRA is retrained
   from the full curated corpus each dream cycle (wasteful, clean, no drift
   ambiguity). Drift allowed by design; measurement uses frozen checkpoints.
6. **Reads:** LoRA read = just generation from the adapted model. No ReAct.
   The open question is WHEN to read, not how.
7. **Compute parity:** same reasoner + same prompter in every arm; only the
   memory substrate varies. (Reviewer-proofing; also isolates the variable.)
8. **Environment:** custom AlchemyWorld (built, alchemy/). Latent parameters:
   stable across life, never stated, randomized per run (contamination-proof
   via nonce names + randomized rules). Compositional: essences predict unseen
   pairs. Complexity taxonomy: exact recall / attribute composition / chain
   depth / distractors (incl. visible false-correlate features). NOT meta-RL:
   latent fixed for the whole life (continual, not fast adaptation).
9. **Long-context arm:** don't handicap — let the real window break; the break
   is a result ("not applicable beyond N episodes"). Small base model = honest
   limit.
10. **Metrics:** held-out pair prediction (ground truth free — we set the
    latent) with confabulation priced (abstain=0.25, confident-wrong=0 +
    confab rate) + task success. Gates: G1 seen-pair recall ≥0.9 (LoRA arms),
    G2 zero essence-token leakage (grep over all emitted text — property in
    the physics), G3 no_memory flat.
11. **Scale:** episodes 60/240/960; LoRA rank {8,32} (ceiling moves with rank
    ⇒ capacity limit, not mechanism failure). Batched episode generation =
    throughput only, no claim. Parallel agents with separate memories = v2.1+
    (union raw logs, retrain — the P-ladder from a new angle).
12. **A-Mem** (NeurIPS'25): strong published baseline to add after naive RAG;
    also the PROBE — run their explicit importance heuristic vs our dreamer
    over the same log, compare what each keeps (agree/disagree figure). Tune
    their k honestly.
13. **Domain shift / memory refresh / multi-goal lives:** real, deferred —
    discussion-section future work. One environment, one latent set, one life.

## Deferred (written down, not built)
- Off-policy RL reading of renormalize-then-write (learned value fn + policy
  improvement) — paper 3.
- KV-space dreaming (train on raw KV): own research project, no precedent —
  v2 dreams on TEXT.
- Salience-weighted replay ("simulate more similar memories" = generative
  upsampling of salient memories) — needs its own gate (synthetic-data risk).

## Status
SPEC_V2.md written (red-pen items: arm list, memory text format, episode
counts). alchemy/ package built: world/env/player/dreamer/lora_mem/evals/
run_smoke. Smoke = 8 ingredients, 20 eps, ScriptedExplorer for coverage,
Qwen2.5-0.5B local (MPS) for dream+LoRA+read.

## Sizing pre-registration (2026-08-19, alchemy/sizing_mc.py + sizing_mc.json)
Method: information-availability ceiling — fraction of held-out pairs an
IDEAL learner (union-find over product-family evidence; conservative,
product-only) can deduce from the life log. No memory system can beat it.
- 4 essences saturates by 30 eps (latent too small — no scaling regime).
- LOCKED: N=64 ingredients (8 inert), K=12 essences, inventory 6, 30%
  structural holdout. Ceiling: 0.13@30 → 0.39@60 → 0.47@120 → flat@960.
- Two regimes named for the paper: ACCRUAL (≤~120 eps) vs REPETITION
  (>120): info constant, exposure grows — consolidation's home turf,
  retrieval's failure mode. MC uses the fastest-coverage explorer, so real
  LLM play shifts accrual right = conservative.
- Memory format LOCKED (Rohin): mix — declarative facts + cross-episode
  patterns + QA slice + negative knowledge.
- Capacity estimate: ≤~2k pair facts + 64 class memberships; LoRA r=16 on
  7B ≈ 30M params — capacity not binding at this scale (lit: ~2 bits/param,
  Physics-of-LMs 3.3); exposure/repetition is the binding constraint,
  which is the thesis. Rank sweep {8,32} still runs (ceiling-moves test).
- Compute estimate (A100, vLLM, 7B player): one 960-ep life ≈ 8M tok ≈
  30–45 min; measurement points are prefixes (no extra lives); fresh-task
  eval ≈ 20 min/arm/point; dreams negligible; LoRA trains minutes.
  Full 2×2 + rails × 3 points × 5 seeds ≲ 3 A100-days — inside quota.

## Sizing v2 REVISION (2026-08-19, after Rohin's context-capacity catch)
Rohin: "learnable" must mean learnable BEYOND context, not from-the-log —
the accrual phase itself has to outrun the context window, and 60 eps is
nothing. Confirmed by MC: old config's accrual ended at ~120 eps ≈ 42k
tokens (fits in 128k — regime not hard). RE-LOCKED: N=256 (32 inert),
K=32 essences (528 rules), inv 6, points 60/240/960/3840. Ceiling
0.00→0.20→0.46→flat; 128k context breaks between 240 (45k tok) and 960
(184k tok) WHILE info is still arriving. Full evidence, context-budget
table, throughput plan, pre-registered predictions: SPEC_V2.md Part II (single doc
per Rohin: overview on top, depth below). Perf fixes en route: recipe-map cache
(960-ep life: minutes → 0.1s), nonce space 256→2048 names (N=256 worlds
exhausted it and hung). Doc structure per Rohin: spec = high-level top +
constants below; all depth in the same doc's Part II.

## Connected-data principle + two ceilings (2026-08-19, Rohin)
DOCUMENTED PER ROHIN: (1) The experiment's data must be CONNECTED/
STRUCTURAL — memory must learn high-dim patterns that extrapolate; the
game latent is intelligently generated as a structure spectrum: Stratum R
(i.i.d. random core, incompressible, tests retention-at-scale), Stratum G
(hidden geometric meta-pattern over essence classes → predicts rules never
observed in any form; retrieval structurally cannot; 🔴 v2 inclusion),
Stratum D (distractors/false correlates, tests not-learning). Not a
"couple games into LoRA" problem — a scale+throughput problem.
(2) Ceiling metric upgraded after Rohin's perfect-reasoner challenge: the
i.i.d. core IS underivable (incompressibility is the design point — data
is the only winning resource), but the learner's evidence model was too
weak; ceiling v2 transfers any observed outcome across proven same-class
pairs: asymptote 0.46→0.77 (residual = inert pairs, 1−(7/8)²). Report
both ceilings; normalize by perfect-reasoner one.
(3) Sizing requirement raised (Rohin): accrual phase alone must span
5–10× context. N=512/K=64: accrual ~1920 eps ≈ 377k tok (3× of 128k,
12× of Qwen native 32k). N=1024/K=96 sweep pending → target ≥5× of 128k.

## Final size lock (2026-08-19): N=1024, K=96
Sweep (both ceilings): accrual to ~6k eps ≈ 1.2M log-tokens = 8-11x of a
128k window, 30x+ of Qwen native 32k — Rohin's 5-10x requirement MET.
Even 1M-token context breaks inside accrual. N=2048/K=128 rejected (12x
but first 2k episodes at ceiling 0.01 = dead points). Points:
960/1920/3840/7680/15360. Perfect-reasoner ceiling 0.43/0.75/0.77/flat.
Nonce generator made exhaustion-proof (numeric fallback) after N=1024 hang.

## Ceiling tier 3 + generation-as-research-problem (2026-08-19)
Rohin challenged 0.46 then 0.77 ("perfect reasoner should reach >=90%") —
CONFIRMED RIGHT: adding statistical inert elimination (never product/ruin
+ nothing vs >=8 distinct proven classes) takes the ceiling to 0.99@3840,
1.00@7680 (127-128/128 inerts found). World is fully compositional; no
fact islands. Three-tier ceiling now reported: retrieval 0.46 / transfer
0.77 / elimination 1.00 — itself a nice figure (what each REASONING tier
is worth on the same evidence). Accrual under strongest learner: ~3.8k
eps ~= 770k tok ~= 6x of 128k (still >=5x requirement). Target zone named
(advisor): HIGH CEILING / LOW ACHIEVED / WIDE GAP.
Also adopted: sleep cadence = dream every ~context-window of experience
(~160 eps @32k), checkpoints at dream boundaries; value function = exact
BFS over true crafting graph (no learned VF at this scale); game
generation = first-class amortization problem, parameter-searched via the
sizing MC with target-zone acceptance; split methodology from SCAN/COGS/
gSCAN compositional-generalization literature.

## Advisor audit round (2026-08-20) — all seven edits executed
1. Part I/II config contradiction fixed (Part II §3 table now shows full
   sweep history; single lock = N=1024/K=96; points unified).
2. Measurement points unified: 60/320/960/1920/3840/7680/15360 (early two
   recomputed after real tokenizer measurement).
3. Eval play 40→200 episodes/arm-point (n=40 binary = ±15pt CI, blind to
   small gaps; 200×5 seeds = ±3-4pt). Headlines never rest on task success.
4. Tokens/episode MEASURED with real Qwen tokenizer: 332 (chars/4 was 66%
   low). Context table rebuilt: accrual ≈1.27M tok = 10x of 128k, 40x of
   native 32k; even 1M ctx breaks inside accrual.
5. Falsifier tightened, no escape hatch: at 3840-ep point, tier-3-
   normalized held-out composition, LoRA-dreamed > best RAG by >=0.05 abs
   AND paired-t p<0.05 across 5 seeds, while G1 passes. Fail = dead.
6. Scripted-explorer factorization stated as limitation + feature (identical
   life stream per arm isolates substrate; exploration = paper 3).
7. Stratum G PROMOTED to required — carries the induced-regularities claim
   (i.i.d.-only world reduces the claim to class-membership compression).
   Generalized per Rohin to PATTERN-SPECTRUM MIXTURE: rho_iid (incompressible,
   retrieval's home turf — printing that loss makes wins credible) /
   rho_fn (hidden function over essence properties — predicts never-observed
   rules) / rho_analog (structurally similar pairs share outcomes).
   Sweep mixture => performance vs WORLD COMPRESSIBILITY curve (the map).
   Advisor caution adopted: parameterize+sweep, don't estimate reality's
   pattern distribution (discussion claim, not design dependency).

## 2026-08-20 late adds (debug-agent evidence, Nemotron mtg, memory mechanics)
- MEMORY = POLICY PRIOR (Rohin's formalization): read = "state + target
  state in -> action prompt out"; captures pattern->action pathways. Spec'd
  into read interface + format stratum (e) goal-conditioned lines.
- REVERSAL CURSE fix spec'd + implemented: dreamer emits both orderings;
  eval randomizes pair order. PARAPHRASE DIVERSITY spec'd as requirement
  (Physics of LMs: single-phrasing knowledge is near-invisible).
- Anti-forgetting = corpus-level: incremental dreams + cumulative corpus +
  full-retrain-per-cycle (already the design; now stated). True generative
  replay (re-dream old memories, reconcile) deferred v2.1+ with own gate.
- FT-vs-RAG headwind literature named in predictions (our claim = induced
  regularities, not fact injection).
- Rank x rho interaction pre-registered (hold-vs-think split): rho_iid
  should want rank; rho_fn shouldn't. Free second result.
- Debug-agent evidence framing (advisor): proves LLM distillation works
  HUMAN-GUIDED and INSIDE context (5k tok) — motivates the question,
  doesn't answer it; it's the regime before our claim applies.
- Deferred (paper 3): shared-trunk + small learned heads (dream/prompt/
  verify) over frozen base; prompt engine as SOFT PROMPTS (prefix tuning)
  not a decoder; verifier as sole backprop source = learned reward model
  (reward-hacking surface — its quality bounds the system).

## 2026-08-20 close-out (dreamer division of labor + Jeremy reading list)
- Dreamer is CONTEXT-BOUNDED: per-window local work only; cross-chunk
  induction structurally impossible for it -> accumulation belongs to the
  memory. Converts "dreamer does everything" from vulnerability to
  architecture argument. Rohin's phrasing: "the dreamer does enough to
  give power to the memory." Spec'd.
- Dreamer ladder ablation (prompts-only variants): transcription /
  per-episode summary / cross-episode patterns (v2) / +prior-memory access
  (renormalizing) / action-conditioned. v2 runs rungs 1+3.
- Forgetting stays corpus-level (not a dreamer concern) — confirmed.
- Jeremy reading list: doc-to-LoRA (hypernetwork text->adapter, no grad
  descent — could REPLACE retrain loop; read first), hypernetworks
  (paper-2 candidate: outcome-credit hypernetwork emits the adapter),
  Engram (startup; memory-layer arch), Harvey (market existence proof),
  Sutton podcast (plasticity/experience framing — thesis-adjacent).

## 2026-08-20 postscript (Rohin)
- Cross-chunk induction, scalable form: rung-4 dreamer = dream WITH the
  memory (run dreamer on the ADAPTED model), not dream OVER the store in
  context. O(1) context cost; the complex pull-everything version is
  correctly rejected as non-scaling.
- Forgetting is fine (graceful, by design); EXCESS forgetting = capacity
  diagnosis. Instrument already exists: G1 seen-recall curve per rank
  across checkpoints (rank 8 degrades where 32 holds -> ceiling located).

## 2026-08-20 postscript 2: loss menu + Engram path (Rohin Qs)
LOSS DESIGN — next-token is SUBSTRATE not objective (reads are generations
so any loss must shape the generative distribution; target/data/weighting
are open): (1) context distillation [teacher-with-chunk vs student-with-
weights KL] = "loss on intention," v2.1 ablation vs SFT; (2) self-study
QA-probe loss (Cartridges/Eyuboglu — likely Engram's mechanism);
(3) salience-weighted loss = PAPER 2 (felt head output becomes the sample
weight: "paper 1 fixes the loss, paper 2 learns the loss weights");
(4) policy loss on (state,goal)->action, success-weighted = paper 3 /
action-conditioned dreamer rung. v2 ships SFT.
ENGRAM PATH (down the line): v2 curve (proof) -> open env+benchmark
(Nemotron play) -> DOGFOOD: dream Rohin's debug-agent logs into a LoRA,
match the hand-distilled 5k prompt at fraction of context cost (their own
100-tok-vs-100K metric, on a real NVIDIA workload) -> raise with three
artifacts. Wedge vs Engram: they do static org docs; the experiential
outcome-credited on-the-job loop is the empty quadrant. Moat includes the
trust instrumentation (gates/ceilings/forgetting gauge). Fleet-scale
later: hypernetwork write amortization + population tier.

## 2026-08-20 pre-run intuition pass (Rohin Q&A adoptions)
- ARM 7 ADDED: lora_dreamed_multiread — explicit read protocol before task
  play: interrogate the adapted model with several goal/inventory queries,
  assemble answers into working context, then act. Directly operationalizes
  memory-as-policy-prior ("multiple queries for the overall vibe before
  pushing intuition"). Implemented pre-run.
- Clarified for run 1: extrapolation = class-membership inference + rule
  transfer (rule-level extrapolation = rho_fn stratum, run 2); targets
  depth-1 only; dreamer input = state/action/obs/VALUE logs, no thoughts
  (scripted life; thought-inclusive dreams arrive with self-played lives).
- Eval power restated: 200q free-form (not MC; ~2,900 possible product
  names) x 7 points x 5 seeds = 7,000/arm/metric; prediction isolates
  knowledge, task success measures usable-in-action.

## 2026-08-20 SCOPE CHANGE (Rohin): chains + mixture promoted INTO run 1
Rationale (Rohin, adopted): depth-1 pairs are the neural-learner worst
case — one weak isolated constraint per observation, evidence thin over
~500k pairs; chains are conjunctions that PROPAGATE (one failed step
falsifies many hypotheses; valid chains rare = sharply identifying;
sequences compress into procedures = policy-prior-shaped). Literature
(comp-gen) supports structured strata. Plan: tonight's 1-GPU canary on
depth-1/rho_iid world = PLUMBING-TRUTH ONLY; generator upgrade (chain
targets depth ~1-4 mixed + basic rho mixture iid/fn) + chain-aware
sizing-MC rerun; real run on upgraded world. Node evidence for complaint:
4u4g-gen-0310 3/4 GPUs RmInitAdapter 0x22:0x38 (897->776), PCIe Gen5 x16
healthy, persists across proprietary/open drivers + BMC power cycle.

## 2026-08-21 (Rohin): chains longer (max_tier 4, mix .3/.3/.25/.15);
episode-count increase pending canary timings (candidate +30720 point).
Patterns-between-chains confirmed already present: same essence rules +
fn geometry govern every tier — regularities transfer across depth.
Node policy: nothing older than Ampere, nothing under 24GB (V100 s1114
rejected); aarch64 g242 box = batch-2, vLLM-from-source risk flagged,
HF-backend fallback plan. Keeping 3/4-dead H100 box (1 unit = 1 hr/node).

## 2026-08-21 night (Rohin, co-design item — not blocking)
fn-stratum DIFFICULTY LADDER: current cycle-distance geometry may be
above the system's "IQ" at 7B+LoRA scale — if fn column reads ~0 we
can't tell substrate-failure from question-too-hard. Proposal: graded fn
sub-strata (easy one-hop regularities -> full geometry) => a
difficulty-response curve ("how much structure can the memory induce")
instead of pass/fail. Discuss before fleet run; canary unaffected.

## 2026-08-21 eval-integrity items (from Rohin's verification standards)
- REPRODUCIBILITY RULE (standing): no reported number without a repo
  script computing it (report.py; extend as metrics land).
- fn-INFLATION CONTROL (before quoting any fn/held-out win): fn answers
  are far more guessable than iid (shared families per distance => small
  answer space). Add MAJORITY-FAMILY GUESSING BASELINE computed from
  ground truth; fn extrapolation claims must beat it, not the floor.
  Triggered by lora_dreamed@960 held=0.42 > implied class-transfer bound
  (~0.32) — verify before celebrating.
- Memory-IQ calibration: anchor difficulty ladder empirically to canary
  fn scores (target mid-range performance), then MC + sweep. Frontier-
  practice-then-sweep also applies to LoRA config: rank sweep exists;
  ADD target-module ablation (attention vs MLP — D2L used MLP down-proj).

## 2026-08-21 canary diagnosis: the exposure failure (pre-registered, now measured)
E=960 lora_dreamed held=0.42 DECOMPOSED = majority-class prior (answers
NOTHING; P(nothing over holdout)=0.42 exactly; iid/fn sub-scores match
per-stratum nothing-rates). E=1920 collapse to 0.02 = style tips to
confident wrong product names. Dreamed corpus content VERIFIED healthy
(goal-form/pattern lines, correct names) -> root cause = EXPOSURE ~1 per
fact (1.6k lines / 1k+ facts, x4 identical epochs). Matches Physics-of-
LMs single-exposure invisibility + our own pre-registered prediction.
Own-goal found: dumb_dream deduped raw lines (destroyed natural
frequency). FIXES (implementation debt on locked format, not new
design): (1) no dedup; (2) augment_corpus — every observed fact x 6
templates x both orderings, frequency-preserving, incl. QA slice;
(3) abstention slice (unseen pairs -> UNKNOWN; 15%) so calibrated
abstention exists in-weights. Canary + seed 1 finish as the NAIVE
baseline (citable); fleet relaunches all seeds on fixed recipe.
Also: per-truth-class accuracy added (acc_product = unguessable metric).

## 2026-08-21 SEED-0 (NAIVE BASELINE) COMPLETE — verdicts
Full 7-point x 7-arm table in alchemy/v2_out/seed0_naive_results.json
(report.py renders it). (1) G1 FAILS for naive LoRA everywhere (recall
~0) => no substrate claims from this run, per pre-registered gates; it
is the measured naive-consolidation baseline. (2) RAG: recall grows
0.24->0.38 but held-out pinned ~0.25-0.30 vs ceiling ->1.0 — REMEMBERS
BUT CANNOT COMPOSE (the predicted structural gap; format-caveat pending
seed-1 samples). (3) SURPRISE: lora_raw@15360 (the ONE bf16-retrained
adapter) scores held 0.38 / fn 0.31 vs zeros for all fp16 siblings =>
fp16 numerical damage implicated ALONGSIDE exposure; fixed recipe fixes
both; optional attribution ablation = bf16-without-augmentation seed.
(4) multiread == lora_dreamed on predictions (same adapter), differs
only on task play — moot until adapters work.

## 2026-08-21 evening (Rohin, driving riff + decisions pending)
- THREE-TIMESCALE UPDATES formalized: event->state, sequence->experience
  (gist adapter), accumulated->world (base). Recency-skew risk named:
  over-updating long-term memory from recent experience skews the world
  model toward the recent; the weighing is genuinely hard and is what a
  learned dreamer would be FOR.
- DREAMER CO-LEARNING: reverses earlier "dreamer needs no training,
  verifier carries it." Proposed reconciliation for Rohin's call:
  dreamer = FROZEN GENERATOR (LLM emits candidate memories, amortized)
  + LEARNED CURATOR (selection/weighting parameters co-learn with the
  system, trained through verifier signal). Preserves both intuitions;
  paper 2 = the curator. Decide before paper-2 framing is written.
- Driving-triage example (one-hand drink vs oncoming truck): learned
  arbitration between two learned behaviors = salience in one everyday
  sentence. Candidate intro illustration for the paper.
- Cosmos link (advisor): our LTM = world model FROM EXPERIENCE rather
  than observation — fast one-liner for non-memory audiences.

## 2026-08-21 north-star riff (filed, none touches paper 1)
- SLEEP PRESSURE = CONTENTION, not clock: replay and acting compete for
  the same reasoning hardware; consolidate when marginal value of
  consolidating > marginal value of acting. When-to-learn is learnable
  and has the same shape as every other allocation decision. (Circadian
  rhythm is Earth's forcing function; ours is compute contention.)
- Central shared reasoner, modules (prompter/actor/verifier/dreamer)
  COMPETE for it; currency = next-token generation; state is central
  because policy is about state. Maven (Rohin's day job) = the
  hand-designed version of this allocation problem one layer down —
  credibility bridge worth using.
- Hot-swap consolidation = async RL practice (train while actors run a
  stale copy; off-policy staleness; Michael Loh's rollout work = internal
  precedent). Parallelism converts the serial experience bottleneck into
  a staleness problem, never eliminates it.
- MOTIVATION SENTENCE (paper intro candidate): "Nobody optimizes for
  agent-lifetime throughput because no agent has a lifetime."
- Extended-pretraining (not fine-tuning) for base-weight updates needs
  general-corpus replay mixed in (anti-degradation).

## 2026-08-22 NAMED (Rohin): "SLEEP + DAYDREAMING"
World validated (RAG recall 0.99 = questions answerable, corpus complete);
bottleneck is now the MEMORY side — we scaled the world, not the dreaming/
storage. Diagnosis hypothesis: mixture of too-small LoRA and not-nearly-
enough dreaming. The brain makes memories RICH by revisiting the needed
ones (offline=sleep, online=daydreaming), enriching them into more
learnable forms. Mechanism ladder to test (ascending cost):
(1) enrichment depth, UNEQUAL by need — salience as replay/variant count;
(2) re-dreaming: dream on the dreamed corpus (memories referencing
memories — where richness lives);
(3) daydreaming: cheap targeted enrichment between sleeps aimed at what
recent episodes needed and missed (rung-4 in natural habitat);
(4) capacity: rank sweep 16->64->128 + steps-per-fact.
NEXT EXPERIMENT after seed-2 verdict: enrichment x capacity 2x2 to
attribute "too little dreaming" vs "too small memory."
Observed so far (fixed recipe, seed 2): retrieval arms near-ceiling on
recall; in-weights recall FALLS as corpus grows (0.10@60 -> 0.02@320) —
interference/dilution signature, the pre-registered failure arriving
where predicted.

## 2026-08-22 FORMALIZED (Rohin): THE DAYDREAMER
A second amortized enrichment channel, running DURING waking runs, not
only at sleep boundaries. Type signature:
  input:  recent episodes + current memory state + what recent tasks
          needed-and-missed (value-function misses)
  output: enrichment lines appended to the cumulative corpus (same
          corpus the next sleep retrains on)
  cadence: between episodes / on idle compute; small and targeted where
          sleep is global and heavy. Same mechanism-or-not as sleep is
          left open (doesn't matter while both are amortized).
STICKING vs VALUABLE (Rohin): making memories stick (exposure) is
separate from making enrichment VALUABLE — the field-evidence self-report
(CURE debug agent) is the ground truth for what valuable enrichment looks
like on a real workload.
RICH DREAMS AS WORLD-BUILDING (vision, near-verbatim): dreams are not
just memories — they are experiences replayed THROUGH other experiences,
building the experiential world model; as the built world grows, raw
reality fades — "a puzzle off of a light-projected real world." The
gist/verbatim separation emerges from the constructive side. Literal
mechanisms to derive this weekend (Rohin's pass): dreams that cite other
memories; replaying an episode against the current world model and
recording the DIFF; enrichment that connects facts to the loose
generalized world rather than restating them.

## 2026-08-24 architecture session (Rohin + advisor) — filed
- POST-TRAINING REFRAME (the honest claim): post-training already IS
  experiential learning; our claim = moving it OFFLINE->ONLINE and
  POPULATION->INDIVIDUAL. Ready answer for "why don't labs do this":
  online individual updates = catastrophic forgetting, no held-out eval,
  unbounded drift, no rollback — our paper is one measurement in that
  space, not a novelty claim.
- COMPOUNDING-LOOP CAVEAT (own it in the paper): v2's life is scripted
  and frozen across arms, so data CANNOT improve with memory — v2
  measures one LINK of the loop, not the loop. "Loop is the program,
  link is the paper."
- "ISN'T THIS RL" answer: SFT on curated text; the verifier supplies
  HINDSIGHT FOR CURATION, not reward for the gradient.
- ACTOR-CRITIC FACTORIZATION (named): evaluator = critic, the ONLY RL'd
  component (minimal RL surface = design win); dreamer/thinker distill
  from its judgments. Watch: single evaluator at read+write = correlated
  failure (consider two heads on shared trunk: score-what-to-keep vs
  generate-what-to-look-for — the latter may BE the prompt engine);
  dreamer-vs-learned-evaluator = Goodhart/reward-hacking in the write
  path. Both are arguments for v2's frozen evaluator.
- FAST/SLOW SPLIT (keeper sentence): "the dreamer is a fixed function
  with a changing argument" — how-to-dream = slow capability
  (pretrained); what-to-dream-about = fast (its input, the evaluator,
  moves). Paper 1 = the fast-learning half (LTM + simple evaluator).
- v2 LIMITATIONS TO STATE PLAINLY: evaluator is exact BFS (static);
  dreamer static; everything upstream of LTM frozen; value function
  necessarily domain-specific (exact graph distance because this
  environment permits it).
- Consciousness stream mechanism = PREFIX TUNING (soft prompts).
  Karpathy system-prompt-learning as reference — CONFIRM SOURCE before
  citing.

## 2026-08-24 THE WALL, TRIANGULATED (three independent measurements)
1. ORACLE: reasoner composes at 0.91 given explicit structure.
2. RETRIEVAL DIAG: top-12 surfaces both ingredients 0.88 / shared-partner
   class evidence 0.63 — evidence reaches context, model doesn't use it.
3. All arms fn~iid~floor on held-out.
=> The wall is the INDUCTION STEP (raw observations -> class equivalence),
which the model will not perform in-context. Dreamer's job = do induction
OFFLINE, hand the model structure (which it converts at 0.91).
TASK SPLIT: only 14% of eval goals are pure lookup at E=3840; RAG's
climbing task curve (0.08->0.175, monotone, 3 seeds) contains genuine
transfer — PROMOTE task success to headline metric w/ seen/unseen split.
PRIORITY-ZERO: family-level credit implemented (evals.score_levels);
re-eval running (was our acc_product=0 hiding family-level induction?).
Also adopted from audit: 1000 stratified questions (fn/iid x kind);
LoRA-destroys-actor = standalone replicated negative; dream-budget-per-
episode as 4th scaling axis; dream-retrieval-hits as free dreamer
utility signal; eval unit shifts fact->PATHWAY (procedure-shaped split).

## 2026-08-24 EVAL REFRAME (Rohin): induction unit = PROCEDURE, not fact
"You did this-this-that before in a few ways; learn about this-and-that;
see that our situation's this is that; do this-this-that." The quiz
measured declarative induction because ground truth was free; the thesis
(and the only metric with signal — task success 0.08->0.175, 86%
non-lookup) is PROCEDURAL. New eval hierarchy:
1. HEADLINE: task success with a SHAPE-PRACTICED / MATERIAL-NEW split
   (solution shape seen before, specific ingredients never co-available)
   — procedure induction made countable.
2. Supporting probe: the fact quiz (declarative half, family credit).
3. Calibration: oracle (apply-structure, 0.91) + induction ceiling
   (leap-from-perfect-evidence, queued) + retrieval (leap-from-mess, ~0).
Measuring induced-experience generalization is ITSELF the invention —
the field's benchmarks all measure playback; this hierarchy is the
contribution's instrument.

## 2026-08-24 V3 SKELETON (Rohin — locked sequencing)
v2 status: closed for learning; current work = diagnostics/sweeps wrap-up.
V3, in build order:
1. GAME REDESIGN (follows the induction-ceiling result): more inducible
   structure — shallow induction (recoverable from a handful of
   examples), fn-forward (Rohin: iid barely matters; induction subsumes
   the retrieval that matters), fewer classes / more evidence density
   per sizing_mc target: lookup-coverage ~0, deducible high, induction
   shallow.
2. DREAM + THINK made RICH but PRE-SHAPED (not learned; "we learn how to
   shape it" = designer iteration). Micro-test first: does a fact held
   in 10 DIFFERENT PERSPECTIVES (semantic contexts, not rephrasings)
   retain better than 10 paraphrases? (contexts-per-fact experiment —
   feeds dream design.) Plus: pulling PAST memories in to enrich current
   ones (dream-with-memory).
3. READ path: prompt + memory block stays (fine for now); define the
   dream->corpus and read->prompt interfaces precisely.
4. EXPERIMENT: learned memory + model plays FULL GAMES with k tries per
   goal; HEADLINE METRIC = TRIES-TO-SUCCESS falling with lifetime
   experience (pass@k curve) + shape-practiced/material-new split.
   One-shot success too noisy; k tries separates can't-do from variance.
5. Then scale (dream budget axis, population later).

## 2026-08-24 V3 SPEC REFINEMENTS (advisor, all adopted)
- METRIC: paired per-goal TRIES-TO-GOAL (graded — every game informative
  vs binary's wasted bits), capped at N with censoring rate reported;
  identical goal set across arms; median tries headline.
- iid STAYS AS CONTROL: equal improvement on inducible and lookup-only
  goals = general improvement, not induction; THE GAP IS THE EVIDENCE.
  New unit: inducible-goals vs lookup-only-goals.
- PATHWAY INDUCTION TEST (CPU, gates world design): classify every goal
  as LOOKUP (recipe observed) / ANALOGY (structurally identical solution
  practiced on different materials) / NOVEL. Design target: analogy
  plentiful and SHALLOW (few examples suffice).
- READ REDESIGN: query = goal+inventory (state, not quiz); retrieve PLAN
  FRAGMENTS not log lines; two channels reported separately: exact-
  material vs analogous-shape (the induction channel).
- DREAM TYPES (cheapest first): symmetry/substitution; generalization;
  PROCEDURAL ABSTRACTION ("to make tier-3, get two same-family tier-2s
  first" — the thesis one); counterfactual. VOYAGER RULE, non-negotiable:
  every dream ENGINE-VERIFIED before entering the corpus (free verifier;
  control_confab=1.00 is what unverified dreaming produces).
- PERSPECTIVES TEST spec: hold gradient steps CONSTANT, vary distinct
  framings (1x200 / 10x20 / 40x5), 3 seeds — diversity-vs-repetition at
  matched compute; if diversity wins it's the dreamer's existence proof.
- SEQUENCE: metric -> induction test -> world -> dream/read spec ->
  prompt assembly -> experiment -> play.
- TIMING (ROHIN'S CALL, urgent): Sep 18 abstract = 25 days; V3 done
  properly exceeds it. Paper-now option = the replicated negatives
  (parametric consolidation destroys the actor, 3 seeds; capacity wall
  forces selection; retrieval-augmented agents improve with lifetime
  while parametric degrade) — coherent honest measurement paper. Decide
  deliberately: V3 this cycle or next.

## 2026-08-24 V3 STAGE-1 RULINGS (Rohin)
- GEOMETRY IS DEAD: circle-distance fn stratum = IMO-puzzle/encryption-
  grade induction, unrealistic and unfeasible. V3 inducible stratum =
  ONE-HOP regularities only: same-class => same behavior ("x behaves
  like x'" — the debug-agent-shaped leap).
- DESIGN LOCUS = THINKER, not memory-as-structure-store: model must
  IN-CONTEXT induce given strong context; thinker builds that context
  from memories + present state; if it can't induce with strong context,
  the game is bad. Dreamer = multi-perspective memory construction so
  the LoRA learns each memory better; dream/read CO-DESIGNED (writes
  resemble reads). Dreamer designed empirically: test memory retention
  under different dreaming sizes/prompts ("take this memory + these
  past ones, make different memories").
- INDUCTION TEST protocol verified with Rohin: current = one-shot pure
  induction (5 curated raw lines: two same-class proofs + one transfer
  obs; answer never in context). EXTENSION TO BUILD: k tries with
  outcome feedback (the thinker-loop shape: attempt -> outcome appended
  -> retry). Game design targets the k-try number.
- Sequence per Rohin: in-context results -> game lock -> trial-and-error
  amortized dreamer/thinker -> numbers -> V3 run (possibly <3 days).

## 2026-08-24 Stage-2 seed (Rohin, verbatim-ish) + test scoring fix
- INDUCTION TEST SCORING: exact-name is over-strict (product suffix
  depends on hidden grades the evidence only partially reveals) —
  FAMILY-LEVEL is the fair primary for the ceiling test.
- k-TRY VARIANT = AMBIGUITY-CALIBRATED: include evidence sets that pin
  the answer to 2-4 candidates; k attempts with outcome feedback;
  measure how fast the candidate space collapses (induction-under-play).
- V3 DREAM/THINK = AGENT CALLS WITH INSTRUCTIONS (amortized):
  dreamer-agent gets context-window batches of memories (+ pulls from
  prior cycles), instructed: "look for what behaves similarly; keep
  looking until you stop finding; make guesses; test which hold" —
  every emitted memory ENGINE-VERIFIED before entering corpus. Learned
  version later = general pattern recognizer; now = prompted specialist.
  thinker-agent reads memories as instructions, builds prompter context,
  drives the retry loop. Dream sifts patterns; the context-window
  intuition lives here (dream consumes windowfuls).

## 2026-08-25 Stage-1 convergence (Rohin)
- BAR: given the induction steps in evidence, the model must hit 70-90%
  or the game leaves no headroom for memory to show its work. Current
  world misses the bar (forced family 0.20) BECAUSE product names are
  arbitrary ciphers — even perfect induction can only COPY, not derive.
- REDESIGN (pending probe + Rohin sign-off): COMPOSITIONAL NAMING
  (boy+toy=btoy): product name = visible morphological blend of inputs;
  hidden classes govern only react/nothing/ruin. Division of labor:
  MEMORY = broad induction (who reacts with whom, pieced across a
  lifetime, larger than context, written/read specially); CONTEXT =
  last-mile derivation via the visible grammar. "Memory hands context
  intermediary intelligence, not answers" — thesis enforced by
  construction. naming_probe.py testing the 90% claim now.
- INVALIDATION BY RE-DREAMING (filed): when daydreaming reaches opposite
  conclusions on new/contradicting info, sufficient consideration of the
  CHANGED disposition trains more on it and backprop reverses the old
  weights; deeply-ingrained old facts need repetition/investigation to
  reverse — which is the robust behavior, not a bug. Contradiction
  handling is emergent from re-dreaming + full-corpus retraining.
- Dreaming + prompting parallelize/distribute like any transformer work
  — dreaming need not slow the system.
- Population dreamer: later, after single-agent success, for scale.

## 2026-08-26 EXTERNAL AUDIT (Codex/GPT-5.6) — adoptions
SECURITY (P0, Rohin action): repo is PUBLIC with internal hosts/IPs/
procedures/colleague refs in history -> make private NOW; separate
sanitized anonymous artifact for ICLR; AI-use disclosure required.
ADOPTED (science):
1. READ-ONLY ADAPTER PROTOCOL: mount adapter only to produce a bounded
   memory block; unmount; unchanged base reasoner answers. Separates
   storage/retrieval/policy-modification/degradation. Next cycle.
2. ORACLE-IN-WEIGHTS (their G2, decisive): train adapter directly on the
   TRUE compact rules; if read-only read can't transmit them, the
   substrate is broken regardless of dream quality. Run before more
   dreamer work.
3. Verifier-as-oracle risk: unlimited engine checks = rejection-sampling
   exploration. Dream language needs: claim schema, supporting episode
   IDs, witnessed-vs-counterfactual distinction, counterfactual budget,
   reject unparsed. (Cycle-2 group verifier = partial.)
4. STATS: unit of replication = world/lifetime; v2 falsifier = p~.08
   directional (softened in REVIEW_PACK); success@k + restricted-mean
   attempts with censoring; analogy-minus-lookup pre-registered primary.
5. Factorial core: representation {raw, verified-abstractions} x storage
   {context/RAG, parametric} + oracle + agentic-search ceilings, same
   goal-conditioned thinker everywhere.
6. Pathway taxonomy too coarse (shape=sorted tier pairs) — do NOT lock
   N=192/K=12; define pathway identity on canonical dependency graphs;
   verify taxonomy on small worlds manually. (L0 line supersedes.)
7. Target-module ablation (attention vs MLP down-proj; TMEM) before any
   capacity claim; capacity claims softened to recipe-specific.
8. Claims-not-yet-safe list adopted (RAG-can't-induce, abstraction-must-
   be-parametric, forgetting-impossible, etc. — all softened to tested-
   configuration statements).
9. New must-reads/cites: TMEM 2606.04536, PEAM 2605.27762, COVE
   2608.01234, Auto-Dreamer 2605.20616, procedure-memory 2604.27003,
   Ground-Truth-First 2607.21962, MemTrace 2606.17328, RECON 2607.16716.
10. Gate calendar (Aug30 L0 factorial ×3 worlds / Sep3 oracle-in-weights
    / Sep7 first replicated analogy / Sep10 claim freeze / Sep13 pivot
    decision -> negative paper "Why Naive Parametric Consolidation
    Fails" as the honest fallback).
Position: keep "dream" as mechanism name; paper = lifetime learning +
experiential parametric memory; title candidate "Beyond Playback".

## 2026-08-26 THE DREAM LANGUAGE (Rohin, candyland spec) — five strata
1. WITNESSED FACTS with PROVENANCE ("the monkey in candyland was red")
   — situatedness so worlds don't blur; enables "where did I see that?"
2. GENERALIZATIONS with confidence ~ evidence count ("animals in
   candyland are red" — only after ~10x supporting facts; below that,
   "the ones I've seen were red"). Confidence spoken in language.
3. PRIOR-CONTRAST / SURPRISE ("monkeys aren't usually red; this one
   was") — store the world's DELTAS from pretrained priors; that's what
   makes a new world learnable compactly.
4. NAMED ABSTRACTIONS (G2e) — coin names so downstream reads are atomic.
5. CONNECTIONS — dreams reference other memories; 50 observations
   expand into hundreds of linked lines.
THINKER = the READ CASCADE mirroring the strata: query at descending
abstraction until something answers ("what color are apes here?" ->
"are animals differently colored here?" -> "have I seen a monkey? what
color?"). Writes resemble reads, per-level.
MEMORY TESTS implied: PROJECTION queries (did observations become a
world?) + SITUATED RETRIEVAL (provenance binding) — both gradeable vs
ground truth. G4 covers strata 1/2/4; strata 3/5 + cascade = L1 ladder.

## 2026-08-25 IDENTIFIER VIVIDNESS + controlled hallucination (Rohin)
- Candyland was NOT a game redesign — it exposed a variable: identifier
  VIVIDNESS. Hypothesis (human-memory analogy): "red monkey in candyland"
  binds better in LoRA than nonce syllables, because rich pretrained
  embeddings give gradients an intuition scaffold to attach deltas to.
  You'd remember red monkeys better than greek symbols.
- Design: SAME hidden L0 structure, two skins — nonce names vs vivid
  fantasy entities, with RANDOM type assignment so priors can't predict
  outcomes (any gain = binding/retention, not knowledge leakage; any loss
  = prior interference). Either result is a paper section. Ruling: test
  modules on BOTH skins; the abstract game stays as the clean test-bed.
- Deployment argument: real agent memories are numerical-with-context
  (the model has strong priors about what the numbers mean); nonce worlds
  have no intuition scale, so vivid worlds may match deployment better
  than abstract symbols.
- DREAMING = CONTROLLED HALLUCINATION (via Rohin's friend): we are
  deliberately eliciting extrapolation of the entire scene from fragmentary
  memories; the engine-verifier is what separates dream from confabulation.
  The dreamer is amortized learned instruction: find sequences, connect
  facts, extrapolate from limited information.
- Two-lands worlds (candy/dandy: same entities, different laws) =
  provenance stratum made testable; forces chain-of-thought in dreaming
  AND prompting; L1 ladder item.
