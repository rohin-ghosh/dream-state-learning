# IDEAS — the repo's own consolidated memory
*(This file is the SEMANTIC layer of the project's memory; notes/32 is the
episodic stream; REVIEW_PACK is the compiled read surface. MAINTENANCE
RULE: any session that adds a ruling/idea to notes/32 must also touch this
file — promote, demote, or add. Statuses: ACTIVE = current frontier;
LAW = proven/standing principle; ALIVE = deferred but must not be lost;
DONE = proven and absorbed; DEAD = superseded (kept to prevent re-litigating).)*

## THE HYPOTHESIS (canonical, 2026-08-27)
> Dream–LoRA–Think enables self-learning agents to convert experience
> into persistent, connected world models, continuing to improve as
> agent lifetimes and task depth grow where existing memory systems
> saturate. (Better, not faster. Still to be proven.)

## LAWS (proven principles — design against these)
- **Five-rule stack** (G2f→G4h): dreams coin NAMES; memories are 1-hop
  atomic QA; measured exposure; thinker does resolved reads; CLEAN base
  composes (read-only adapter). [ledger G-series]
- **Recognition reads**: finite grammar answer-space → score candidates
  under the adapter, don't generate. 228/228 fidelity. [ledger C2r]
- **Verifier placement**: exact verification lives OFFLINE (ProofGate
  scores committed batches); never in the cognitive loop for headline
  arms — "the intelligence is scalable and learnable; the verifier graph
  is not." Prompt scaffolding allowed; solution guidance forbidden. [notes/35]
- **Priors localize**: storage is prior-indifferent (G5b); PROPOSING and
  COMPOSING are prior-scaffolded (~20pt skin gaps). Vividness matters
  where intelligence happens, not where memory sits. [ledger G5b, C-ladder]
- **Exposure economics**: write cost is fact-SHAPE-driven — relations
  ~3× entities; long composite answers unstorable; ~24 touches for
  uniform atomic facts. [ledger G5c]
- **The resolution protocol is the memory intelligence** (2x2, 2026-08-26):
  context+recognition == LoRA+recognition (D2 0.50) at 1086 memory
  tokens; direct context/LoRA floor (0.083/0.167). Mounted-LoRA D0 is
  0.50 vs 0.75 with recognize+unmount. Substrate is
  interchangeable while memory fits the window; LoRA's value condition
  is memory >> window + persistence. Always report memory token counts.
- **Coverage prices capability ~linearly** (equiv coverage 9/15→D2 0.50;
  14/15→0.917) and must be tracked PER ENTITY, not per claim. [ledger C3]
- **Attribution discipline**: peel one scaffold at a time; keep ceiling +
  previous + stripped conditions; the degradation curve is a result. [notes/35]
- **Eval discipline**: generous max_tokens + final-answer parse; balanced
  per-kind floors; answer-suppression is a trap (the D2 "wall" was the
  one-word protocol). [notes/33]
- **Experiment-resolution**: when dreaming finds an evidence gap, ACT in
  the world to create the missing evidence (G4k; priced reachout in lands).
- **Docker principle**: pretrained model = base image; a world/lifetime =
  thin diff of salient deviations; dreams = commit layers; repeats
  reinforce existing layers. [notes/32 2026-08-25]
- **Atomic proof leaves unlock useful recurrence** (v0.2, 2026-08-26):
  monolithic recurrent dreaming fails at both 7B and 32B, but canonical
  reads + one-role proof leaves + branch revisit recover higher-order parent
  structure. Under the same exhaustive controller, 7B exact-parent recall is
  .50 and 32B is 1.00 on development s0; frozen 32B replication is 23/24 on
  untouched s1-2. Recurrence should revisit a precise memory state and extend
  it one check at a time; a longer transcript is not automatically more depth.
  [notes/39]

## ACTIVE (current frontier — world-building phase, target = Blendyland/D3)
- **Epistemic memory states**: SUPPORTED / PROVISIONAL (re-dream queue,
  not trash) / CONTRADICTED; two-axis check (evidence × existing
  structure, evidence outranks); connector re-check for chain-entailed
  claims; revision actions (revise/split/retract) still unbuilt. [C3e]
- **Incremental associative dreaming** (the monkey chain): one modest hop
  per new experience; depth accumulates across the lifetime; hops are
  per-memory (MCTS-like tree growth). MEASURED (2026-08-26): at toy
  lifetimes (23 eps) batch dreaming dominates streaming (D2 0.50 vs
  0.25); streaming's value condition is lifetime >> context — test it on
  a long-lifetime world. Caring dial measured: shy = 1 thought @1.0
  precision; assertive = 29 @0.57. Depth>1 chains didn't form (prompt
  must teach thought-parent citation; retrieval must be entity-keyed,
  not recency-cut). [C3stream, ledger]
- **Reinforcement rule**: similar memory ≠ new node — +support, only via
  the independent-parents rule (re-derivation from new evidence counts;
  repetition doesn't). [c3stream --reinforce]
- **Sleep-growth**: sleep both verifies AND expands (dreams over dreams
  on top-support thoughts). [c3stream --sleep-grow]
- **D3 repaired; compression + transport are ACTIVE**: v0 is retired because
  it was underspecified twice. V0.2 passes 1000/1000 identifiability audits.
  A verifier-free but exhaustive atomic branch/revisit controller at 32B now
  discovers exact parents and final answers on 23/24 untouched aligned cases
  (s1-2, floor .083). This is the ceiling, not the endpoint: replace 57-subset
  enumeration with model-proposed top-k branches, report success@k and engine
  query budget, ablate scaffolds, replicate skins/seeds, then write the same
  accepted memories to context and LoRA under matched reads. [notes/37, 39]
- **Prompter isolation** (Rohin: "easiest part but not obvious; fully
  handed-off; testable isolated"): the C1 protocol ladder IS the isolated
  prompter test — same oracle leaves, prompt-only swings D2 0.35 -> 0.72
  -> 0.92 (one-word / CoT / pairwise) and inverts D3 (0.83 no-CoT ->
  0.35 CoT, overthinking). Ordering ruling: FINISH MEMORY before action.
  Completed substrate 2x2 (same 1086-token dreamed corpus): direct context /
  LoRA = .083/.167; context+recognition / LoRA+recognition = .50/.50.
  Memory's observed value at this size is targeted RESOLUTION; LoRA is the
  persistence/beyond-window substrate hypothesis. [ledger 2026-08-26]
- **T2 release-gated recurrent thinker**: stateful controller —
  retrieve, feed LLM, LLM emits request-or-next-state (never the answer),
  verify+replan each step, answer RELEASED only on an explicit output
  token; per-step caring dial (get-more / ignore-this); calibration =
  stopping policy. Fixes T1's overconfident one-shot self-assessment.
  [notes/32 2026-08-26]
- **Four-arm honesty ladder** as the paper spine: perfect-gate 0.917 /
  no-gate / self-check / self-check+drift, with the confusion matrix and
  false-memory accounting. [notes/35, 36]

## ALIVE (deferred — do not lose)
- **Two-front paper comparison**: downward vs RAG, upward vs batch
  post-training on the same lifetime; **the flywheel**: better memories →
  better actions → better data (random-play lifetimes are redundant).
  Requires the direct-QA distillation (TMEM-style) baseline arm. [notes/32]
- **Three-phase factorization** (Rohin: "I didn't forget for no reason"):
  1 world-building (nearly done) → 2 experiential combination
  (Blendyland, current) → 3 ACTION construction (the Alchemy question).
  "Action needs Blendy": action intelligence = same compositional
  machinery unrolled through time. A0–A4 ladder; CAUSAL_RULE +
  ACTION_SCHEMA memory kinds; receding-horizon think loop. [notes/32]
- **Habitat world**: real features (night vision, swimming) × coherent
  habitat transformations, exact hidden fitness function; world-building
  as VALUE estimation; global priors across worlds + per-world deltas.
  [notes/32 playthrough rulings]
- **C3loop**: one recurrent machine, two regimes (thinker = goal-driven
  narrow; dreamer = surprise-driven broad); persistent state + agenda-as-
  while-loop; inspectable scheduler; recursive dependency-resolution
  reads; full trajectory logging as future amortization data. [notes/35]
- **Evaluator ladder**: ProofGate (now) → TrajectoryValueModel [SUPERSEDED NAMING: the outer component is an OUTCOME CRITIC + SCHEDULER (V/Q over states and operations, progress = dV - compute cost), never a thought-verifier — three-nested-loops architecture in notes/35] (learned
  sequence critic; 1999-research-snapshot pretraining; reality evaluates
  the evaluator via citations/stars/downloads) → OutcomeEvaluator.
  Slow-learning: sequence-level relative outcomes (GRPO-style) over
  logged dream trajectories. [notes/32, 35]
- **Dream language strata** (candyland spec): witnessed facts w/
  provenance; evidence-scaled generalizations; prior-contrast/surprise;
  named abstractions; connections. Two-lands provenance (candy vs dandy)
  forces situated reads. [notes/32 2026-08-25]
- **MoE / function-specific layers** for dream/think/verify modes — later
  scale mechanism, ad hoc if needed now, must be labeled. [Rohin+claude.ai]
- **Peeling ladder remainder**: answer-aware read plans → generic
  cognitive-loop prompts (no game nouns) → raw-stream extraction (drop
  tabulated evidence) → recurrent dreams-over-dreams → new worlds →
  amortized controller. [notes/35]
- **Prompt-ablation ladder**: minimal / generic loop / pattern repertoire
  / game-informed ceiling. [notes/35]
- **Controller parameterization ladder**: prompts (Paper 1, learnable-
  by-construction) -> discrete prompt optimization (DSPy/OPRO) -> mode
  adapters -> prefix/P-tuning (static mode bias) -> conditional prefix
  generator (the real "consciousness stream" — state-conditioned) ->
  learned operation policy. Vectors buy learnability, cost
  inspectability. [notes/35 2026-08-26]
- **Self-prompt legitimacy ruling**: process guidance is allowed because
  "the LLM could come up with these self-prompts anyway" — later, let the
  model WRITE its own next dream question (self-directed drift). [notes/32]

## DONE (proven, absorbed into the system)
- Nonce L0 closed at oracle ceiling, replicated ×3 worlds w/ variance
  (0.949/0.849±.06/0.872±.09); daydreaming + merge inference validated.
- Semantic World C0–C2: context-break real; CoT clears D2; transport
  proven (D2 0.92–1.0, 100% read fidelity); C1b prior-scaffold on D3.
- Gauge machinery: emitter recovers full coordinate system from correct
  claims (fit 1.000) — positions by class order, rotations propagated,
  palette order incl. reflections, label permutations.
- Self-check works oracle-free: precision 0.61→0.83, gauge 0.35→0.87 vs
  no-gate; conservative recall is the cost (recovering via connector
  re-checks + provisional queue).

## DEAD (superseded — do not re-litigate)
- Circle-geometry/deep-cipher worlds (IMO-puzzle grade, un-inducible).
- Naive fact-injection (v2.0/2.1 falsifier failed honestly; capacity was
  never the wall — write FORMAT was).
- In-loop FactorSolver as the headline condition (now the labeled ceiling).
- Enrichment × capacity 2×2 (answered by the G-series diagnosis).
- "LoRA memory is novel" as a headline claim (preempted: TMEM, New News,
  LoRA-as-Knowledge-Memory, Language Models Need Sleep — see notes/36).
