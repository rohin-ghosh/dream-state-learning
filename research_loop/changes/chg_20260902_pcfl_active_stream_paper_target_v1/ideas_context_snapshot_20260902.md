# Immutable IDEAS context snapshot — 2026-09-02

- Source: `research_notes/IDEAS.md`
- Source SHA-256: `0b2aa2eebdb16a9099e81005b9c0cac4055e93218ffec2d28fd0ab5c4c7a7fdc`
- Captured date: 2026-09-02 (America/Los_Angeles)
- Status: immutable proposal context. Everything after the marker below is the source payload preserved byte-for-byte.

<!-- BEGIN_VERBATIM_SOURCE_PAYLOAD -->
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
- **Self-verification must be BLIND** (dream ladder v1, 2026-08-28):
  with observed outcomes visible, the dreamer marked every hypothesis
  SUPPORTED — "predictions" back-fit to the shown answer. Separate
  prediction from evidence at generation time; compare mechanically or
  in a fresh context. [ledger]
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
  per-memory (MCTS-like tree growth). The dreamer is not required to emit the
  eventual parent set or answer: LoRA carries/compresses the connected state,
  and the goal-conditioned thinker may reconstruct the parent/action
  hypothesis by traversing several stored paths. Generalization belongs to the
  whole dream-memory-think trajectory unless an ablation localizes it.
  MEASURED (2026-08-26): at toy
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
- **V5 is a direct-proposal ceiling, not recurrent dreaming** (2026-08-31):
  four independently seeded, task-family-scaffolded parent draws form nested
  sample prefixes and are filtered against public target observations. Calls do
  not consume and extend prior parent memories. Preserve it as a proposal
  frontier/curriculum diagnostic; the architecture-faithful next test exposes
  one temporal episode plus bounded prior nodes and permits one ADD/REVISE/
  OPEN_QUESTION/PASS operation per cycle. FINAL: proposal recall
  0/12->3/12->3/12->3/12; supported parent precision 0/5; retained parents
  0/12 true; role self-pairs collapsed retained role precision to .375.
  Corpus is barred from transport. [ledger, notes/42,
  recurrent_microdream_v0]
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
- **LoRA as the bootstrap for self-training on actions (Rohin 2026-09-02,
  the full-altitude vision)**: base models cannot train on their own action
  data today because raw agent trajectories are too noisy/incoherent to be
  worth pretraining on. The LoRA-loop system is the SHORT-TERM LEARNER that
  fixes this: deployed on a frozen base in a sandbox, it learns from its own
  actions within one lifetime (including a LEARNED exploration allowance,
  estimated from its own past rather than hand-set) until the agent shows
  sustained success — at which point that life's trajectories, now
  high-quality because the adapter made the agent competent, are PROMOTED
  into the base model's training set. Many sandboxes in parallel → the
  first generalized, high-quality dataset of acting (not just knowledge),
  with the value of exploration measurable at scale. "Let baby learn here,
  then train on what we've learned": adapter = individual learning, base
  update = species learning; eventually the base absorbs the capability.
  KEY UNIFICATION: the verified-write / sleeper-compile machinery is the
  quality gate that makes promotion possible — v5's poisoned-corpus collapse
  is the same failure law that kills naive self-training flywheels (contrast
  AlphaZero/STaR, which work because a filter guarantees promoted data);
  Paper 1's verification layer is the admission ticket to the whole pipeline.
  EXTENSION — training-rank cascade: multiple adapter levels at
  geometrically slower timescales, fast ranks learning quickly and feeding
  what persists upward to slower, more generalized ranks, terminating in
  base weights. Exact neuroscience anchor: Benna & Fusi 2016 synaptic
  cascade (chain of variables per synapse, fast feeds slow); ML echoes:
  fast-weight programmers, multi-timescale memory. Our memory+loop adapters
  are the depth-2 case, so the architecture generalizes without replacement.
  Measurable when scale allows: does promotion improve base ACTION competence
  (not just knowledge); learned vs fixed exploration coefficient; cascade vs
  two-tier consolidation. Paper-3-scale; goalposts for Paper 1 unchanged.
  TRIANGLE DESIGN (Rohin 2026-09-02): the cascade as a RANK PYRAMID — small
  fast adapter at the bottom (little data, quick updates), geometrically
  larger ranks upward, each trained on the ACCUMULATED verified data from the
  level below, until the top rank is large enough that merging into the base
  is natural. Design rule that resolves "the right LoRA size is not obvious":
  rank is a FUNCTION of accumulated verified data — each level needs
  proportionally more data to justify its parameters, so promotion from level
  k to k+1 triggers on data volume, not on a clock. Keep levels as SEPARATE
  adapters (composable via the proven read-only/clean-base protocol,
  independently ablatable), not a monolithic trailing structure. Two
  propagation mechanisms to compare: (a) DATA-MEDIATED — the higher rank
  trains on the filtered corpus/traces accumulated under the lower rank
  (verification gate applies at every promotion; cleaner, auditable);
  (b) WEIGHT-MEDIATED — LoRA deltas add, so periodically merge the fast
  adapter into the slow one (SVD re-truncate at the higher rank), reset the
  fast adapter, lightly decay the slow one's singular values (SHY downscaling
  in weight space) — merge-and-reset IS a sleep cycle in weight space.
  EXISTENCE PROOF at the endpoint: ReLoRA shows repeated low-rank merges
  into full weights approximate full-rank training — the top of the triangle
  is already demonstrated at pretraining scale. Near-term ladder (A40-sized):
  (1) rank sweep of the loop adapter under BC at 7B — prediction: agency is
  LOW-rank (steering, not knowledge); (2) depth-2 cascade (fast r~8 per-life
  → slow r~64 across lives, both mechanisms) vs single-adapter baseline,
  measuring retention + transfer; (3) promotion-to-base deferred.
- **One-system view: dreaming = the write mode of thinking (Rohin 2026-08-31)**:
  maybe dreamer and thinker are not two modules but one thinking system in two
  modes — online (grounded, acting/retrieving) and offline (ungrounded,
  writing). "Dreaming is just the write mechanism, TMEM-style." Node
  connections then form NOT by an explicit dreamer program but through
  traversal: while thinking you BFS/DFS across memories, and co-traversal
  itself creates/strengthens edges ("you connect to one connected thing and
  now it's connected") — Hebbian, use-weighted, matching the earlier MCTS
  intuition (similar memory reinforces + deepens rather than spawning new
  nodes). Under this view the dreamer is demoted to a memory garbage collector
  + write sequencer + replay scheduler (episodic triage, high-level
  scheduling), and content arrives at memory already partially connected
  because the thought-trace IS a path — write the traversed edges, not
  isolated facts. Corollary correction to the "loss policy" phrasing: what to
  lose is not an explicit decision; with the right parameterization,
  compression itself creates the intelligence (a flow of linear algebra), and
  the pink pig is generalization succeeding, not failing — exploiting priors
  for everything outside the focus of attention is the smart move under
  bandwidth limits. Refinement to keep both truths: SELECTION vs COMPRESSION —
  compression is emergent (SGD + parameterization + bottleneck), but selection
  of what gets replayed/trained-on is still a mechanism (brains do prioritized
  replay of surprising/rewarded traces), and v5's 2026-08-31 result (corpus
  0/12 true → think 1/30) was a selection failure, not a compression failure.
  Note the convergence: Codex's recurrent-microdream design (WAKE cadence,
  node reactivation, per-edge self-check inside one recurrent loop) is this
  same one-system view arrived at independently — see notes/42.
  CRYSTALLIZED (Rohin, same day): one resolver mechanism, two invocation
  contexts. THINK mode = goal-driven, read-mostly: builds logic chains and
  connections from memory keyed by the current goal; its traversal log writes
  cheap local edges as a side effect. DREAM mode = episode-driven,
  write-mostly: the SAME think machinery invoked at a higher episodic level
  with no external grounding, owning durable writes — TMEM-style, proposing
  MULTIPLE candidate writes per episode, each passing the local blind
  self-check before commit, with the write policy itself outcome-trainable in
  the outer loop (this is where medium-rate learning bites). The only
  differences between modes: input source (goal+world vs episodic buffer),
  output permissions (actions/answers vs durable writes), and grounding
  (external feedback vs none) — everything else (ops grammar, retrieval,
  scaffold, budget) identical, which makes mode a single clean ablation axis.
  Practical consequence: no bespoke dreamer program — the dream arm is the
  organism thinker with a WRITE op, episodes as input, and k-sample write
  proposals; v5's failure (single-gate writes, no thinker in the write path)
  is the ablation that motivates it.
  MATURATION (Rohin, same day, explicitly a discussion not gospel): rename and
  re-scope. THINKER absorbs the dreamer's current generative capabilities —
  it thinks, builds connections and viewpoints, and its episodes of thought
  are deliberately voluminous ("a lotta data is good": traces are raw material,
  and trace statistics — frequency, co-occurrence — carry signal). The
  consolidation layer becomes THE SLEEPER: it does not generate content, it
  COMPILES the thinker's output into strong writeable data — dedup (reinforce
  rather than duplicate), abstraction layers, and multiple organizations of
  the same memory under "different vibes" (entity-keyed, attribute-keyed,
  topic/temporal views — a principled generalization of the entity+color
  retrieval keys the gold-control excavation forced on us). Sleep-cycle
  mapping: SWS = the write/transfer pass (prioritized replay, commit verified
  atoms), REM/dreams = the reorganization pass (cross-links, schemas, novel
  associations), synaptic downscaling (Tononi/Cirelli homeostasis) = the
  garbage collector. Deferral ruling: the episodic-generalization half of
  dreaming is not yet rewarded by our game — build thinker-with-write first,
  sleeper as compile stage when the world rewards cross-episode schemas.
  NAMING/NOVELTY CAUTION: PEAM owns sleep-framing per the forbidden-claims
  list — "sleeper" naming is fine internally but the paper must cite PEAM and
  differentiate (our claims: one-mechanism think/dream, connection-through-
  traversal, weight-space consolidation, beyond-saturation lifetimes).
  NAMING RULING (Rohin 2026-08-31): SLEEP = the whole offline system,
  including the PEAM/TMEM-style write-to-LoRA layer; DREAMING = the thinking
  that happens during sleep. Keeps the existing dream structure and branding;
  the write layer is a component of sleep, not a rival of dreaming.
- **Shortcut materialization = the lifetime-scaling mechanism (2026-08-31)**:
  chains do not live in the adapter — the adapter stores 1-hop atoms and the
  thinker hops at read time (proven: five-rule stack, substrate 2x2; matches
  the literature that composing separately-learned facts in-weights fails
  without externalized hops — reversal curse, grokked-composition results).
  So writes take two forms: (1) atoms a→b, b→z (hoppable edges), and
  (2) MATERIALIZED SHORTCUTS — when the thinker's traversal statistics show a
  chain a→b→z is hot, sleep writes the composed 1-hop atom a→z with
  provenance ("via b"), lossy by design (intermediates dropped from the fast
  path, re-derivable from provenance). Repeated consistent statements of the
  same relation are what carve the gradient direction (measured-exposure law
  governs how many). Consequence: effective reasoning depth per FIXED think
  budget grows with lifetime — each sleep compresses yesterday's multi-hop
  derivations into tomorrow's single hops (the MCTS-depth-per-dream intuition,
  now mechanistic). This is the beyond-saturation hypothesis stated as a
  mechanism: retrieval systems keep chains external forever so think-cost
  grows with task depth; a consolidating agent amortizes depth into the
  substrate, so deeper tasks stay in budget as lifetimes grow. Which chains to
  materialize needs little new thinking at write time — the thinking already
  happened during wake; sleep compiles its statistics (dedupe + hot-path
  materialization + GC).
- **LoRA is not memory, it is learned reasoning (Rohin 2026-09-01, scope
  reframe)**: the evolution analogy for pretraining is backwards — humans
  start weak and learn their world; LLM agents are born omniscient-generalists
  and amnesiac-particulars (massive generalized knowledge, zero personal
  history). So the agent-memory problem is NOT the human episodic→semantic
  pipeline (the semantic layer already exists from pretraining); it is binding
  a particular LIFE to that knowledge. Three-tier restatement: context window
  = "what is in front of me" (strong, transient working memory); adapter =
  the middle tier we are building — learned agency: compiled reasoning,
  search control (when to go BFS vs DFS through options), shortcut chains,
  schemas; full continual pretraining = the slow permanent tier. Under this
  view the think/dream/sleep loop trains a REASONING POLICY, and stored facts
  are scaffolding for that training. This resolves the substrate-2x2 puzzle:
  LoRA-as-facts loses to context until memory >> window (measured), but
  LoRA-as-procedure has no context-window equivalent at any scale — trained
  dispositions from thousands of episodes cannot be carried as prompt text —
  so the value condition for LoRA-as-reasoning plausibly arrives much earlier.
  TESTABLE: train the loop adapter (BC on think traces, already-planned
  ladder) at small memory scale where fact-LoRA showed nothing, and look for
  gains. Convergence with prior art: EVAF's split (durable goal-conditioned
  tendencies in weights, shallow facts in retrieval) and PEAM (consolidates
  skills, not facts) both back procedure-in-weights/facts-in-text. Also
  reframes "memory before action": memory-as-learned-reasoning IS the
  prerequisite of action. Scope guard: Paper 1 goalposts stay frozen — this
  is intro-framing / paper-2 material, not a goalpost change.
  SUBSTRATE QUESTION (Rohin 2026-09-02): if LoRA is becoming AGENTIC POLICY,
  is LoRA-on-transformer the right thing to train? Ruling-in-progress: yes,
  for principled reasons — (1) our action space is language-native (ops
  grammar: MEMORY/THINK/WRITE/ANSWER are tokens), and a policy over token
  actions IS a language model, so tuning the LM is policy learning (RLHF/GRPO
  precedent); (2) low-rank is the right PRIOR, not a compromise: the base
  already contains the skills, and the policy delta should be a small steering
  field over existing capability — "the parameterization creates the
  intelligence"; (3) composability: keep the memory adapter and loop adapter
  SEPARATE (already in goalposts) so experience and agency stay auditable and
  swappable; (4) frozen base + KL-to-base guards against policy training
  degrading general intelligence. The hard part is NOT the substrate, it is
  the CREDIT SIGNAL — the BC → rejection-SFT → preference → GRPO ladder is the
  ramp, and v5 gives the first concrete target: train the write policy against
  whether downstream retrievals helped (TMEM-style outcome credit).
  NEW, TESTABLE — CO-ADAPTATION: "train this enough while training the
  intelligence and you intelligently learn how to use your agentic
  intelligence" = the loop policy must be periodically RETRAINED during sleep
  as memory grows, because it is a policy over a changing memory landscape.
  Predicted failure mode: frozen policy + growing memory → the agent gets
  WORSE at using its own expanding memory (retrieval precision decays with
  lifetime). If measured, this is a second saturation mechanism that pure
  memory systems cannot escape and our sleep loop can. Vocabulary that falls
  out: base = intelligence, context = situation, memory adapter = experience,
  loop adapter = agency.
  pink-frog/green-pig afterimage illusion as the paper's motivating image.
  Fixate elsewhere and perception runs on adapted priors: the brain keeps the
  old compressed structure ("pigs are pink") while the literal input changes —
  lossy, generalized memory being rendered live. The claim: compression is not
  a cost of memory, it is the mechanism of intelligence — reducing dimensions
  is what lets distant experiences blend and connect (exactly the Blendyland
  parent-blend structure), and the bottleneck (finite context window, finite
  information-transfer rate) is WHY abstraction emerges at all. Transformers
  already do this over pretraining data; Dream–LoRA–Think tries to do it over
  lived experience with orders of magnitude less data. Two sharpenings:
  (1) the intelligence is not the loss per se but the CHOICE of what to lose —
  structured loss keeps what predicts and discards what doesn't; v5's dream
  ladder (2026-08-31: recall 3/12 but supported-precision 0/5, retained truth
  0/12, think 1/30) is the illusion's dark side measured live — compression
  outpacing verification turns generalization into confabulation, the pink pig
  overriding the actual image. Compression quality = filter quality.
  (2) The architecture is complementary-learning-systems shaped: fast verbatim
  episodic store (our QA corpus / hippocampus) + slow generalizing store (LoRA
  / neocortex) + sleep replay (dreams) doing the transfer. Citations for the
  intro: McClelland/McNaughton/O'Reilly CLS 1995; Tishby information
  bottleneck; compression-as-intelligence lineage (Solomonoff, Hutter,
  Schmidhuber compression progress). LoRA's value condition (memory >> window)
  is this same statement: consolidation pays exactly when the bottleneck binds.
- **Capacity-compression phase diagram**: memory size is not monotonic
  intelligence. At fixed base model, sweep LoRA rank/effective capacity x
  dream compression while separately measuring (1) exact experiential-leaf
  recall, (2) withheld structural composition, and (3) novel multi-step action
  gain. Hypothesis to test, not assume: too little capacity drops evidence;
  excess capacity may preserve episode-specific detail without pressure toward
  reusable structure; an intermediate regime may best trade recall for
  constructive generalization. Then repeat selected points across base sizes
  to separate memory capacity from pretrained reasoning/prior quality. The
  target is latent intermediary action pathways, never recall alone.
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
