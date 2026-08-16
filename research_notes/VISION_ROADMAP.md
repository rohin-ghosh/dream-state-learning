# Vision Roadmap — Rohin's long-term program (as articulated 2026-08-12, night of lease 1)

**Status: PRIVATE / NOT PAPER MATERIAL.** The ICLR paper claims exactly what the
instrument validates (draft checklist: strip vision language). This file exists so
the direction is articulated once, cleanly — for research statements, lab
conversations, and future-us. Rohin's core reframe: *this is not a memory system;
it is a reframe of policy systems* — attention as the interface through which a
learned policy propagates into every allocation decision an agent makes (memory
writes, memory reads, context, compute/model allocation, consolidation targets).

## The staged ladder

**v1 (now, Paper 1):** Frozen policy, frozen LLM, oracle value, ONE trained
attention-shaped salience head gating parametric memory writes + the retention
benchmark. Purpose: attribution — prove the signal trains the gate, with every
confound frozen out. (ATLAS gave retrieval involved with context via parametric
memory; v1 adds *meaningful representation* via policy-derived value.)

**v2:** Learned value head replaces the oracle (learnability of the signal);
possibly salience-weighted LoRA consolidation as a second consumer — "use the
same attention head to weight a LoRA fine-tune, just to see if it works" (this is
already the planned run-2 consolidation surface; salience-weighted replay).

**v3:** Unfreeze the POLICY on ambiguous goals (model still frozen): a sandbox
env (maybe not a classic RL env) where goals are underdetermined and conflicting —
the "expensive lunch problem" — hunger/thrift/self-reward as simultaneous value
heads. Memory unfrozen (it already is), policy now learned; the felt head(s)
become the coupling between the learned policy and the memory substrate.

**v4:** Multi-headed policy ↔ multiple policy-attention heads. Open design
question Rohin flagged: mapping is probably not 1:1 — more like a policy matrix
training a *set* of attention heads jointly. NAMED DANGER (his instinct, and it
has a literature): goal-oriented attention heads must not overwrite the model's
world-representation — "losing world understanding for its own goal
understanding." Known as representation narrowing/collapse under RL; standard
remedies: auxiliary self-supervised losses (MERLIN's remedy, again), KL-to-base
constraints (the RLHF trick), frozen backbone + adapter isolation, explicit
capacity partition (goal heads compete with each other, not with world heads).
His proposed remedy: unfreeze ALL attention (so competition is symmetric) while
keeping non-goal world representations maintained by data/objective mix.

**v5:** Salience-weighted LoRA consolidation with partially unfrozen policy +
fully unfrozen memory → an agent whose weights, memory, and policy co-adapt
online: "online learning that genuinely grows alongside interaction."

## Known hard problems on the ladder (name them early)
1. **Non-stationarity** (note 10's warning): once the policy learns, the salience
   distribution shifts under the memory; value chases a moving policy →
   two-timescale updates, target networks, or periodic re-distillation.
2. **Representation collapse under goal pressure** (v4 above).
3. **Credit assignment across heads**: which policy head's TD gets to gate which
   write when concerns disagree (the lunch problem is a write-gate problem too —
   what should the agent REMEMBER about the expensive lunch?).
4. **Goal generation** ("existentially ambiguous agency"): where goals come from
   at all — autotelic/intrinsic-motivation literature; permanently out of paper
   scope, permanently in private scope.
5. **Paradigm invariance** (established tonight, note 25): retention-under-budget
   is an organ both the LLM paradigm and the world-model paradigm (AMI's
   "persistent memory" bullet) lack a mechanism for. The ladder does not require
   betting on either winner. Robotics/VLA is where the paradigms are being forced
   to merge; language-backbone-with-peripheral-modules is currently winning there.

## One-sentence version
Train the scalar that says "this matters"; then let everything an agent
allocates — memory, context, compute, its own weights — be spent proportional
to it; v1 proves the scalar is trainable and its effect measurable.

## v6 / endgame sketch (2026-08-12, later that night)
Single-scalar-outcome autonomous loop: pick a domain where the reward function
already exists and is instant/dense/exactly denominated — trading (synthetic
book first, graduated real access). Policy online-learned on P&L; world
representation maintained IN TENSION with goal pressure at the attention level
(in this domain that tension is survival, not aesthetics — naive P&L-RL learns
tail-risk-loading degenerates); memory reads/writes agent-decided; FIXED sleep
cycle for heavy consolidation (the project's founding metaphor, closing the
loop); eventually self-reconfiguration on own outcomes ("super loop").
Named requirements discovered en route: reward channel outside agent
write-access (wireheading/containment — an architecture problem, not ML);
sandbox graduation gated by adversarial eval, since sim-profitable ≈
sim-exploiting (the FeltCraft lesson at scale); reward-vs-reality tension as
first-class design objective. Rejected on the way: "efficient research market"
(requires building the reward function; pricing research fast is itself
unsolved).

## v2 design brief, sharpened (Rohin, 2026-08-12)
The scalar write-weight is v1's measurable shadow of the real idea. The real
idea: salience integrated into the memory's full KQV geometry — value-shaped
Q/K projections so that effective weighting EMERGES (where a memory is
written, what it binds to, what it may overwrite), not just how hard the
gradient presses. Amplitude says "how much"; geometry says "where and with
what". v1's scalar result — either sign — sets v2's baseline: an effect at
the gate motivates asking whether geometry beats the gate; a null at the
gate with a live oracle gap is direct evidence the aperture (not the signal)
is the bottleneck, making geometric integration the motivated next step.

## Memory-hierarchy sketch (Rohin, 2026-08-12): files = external notes;
context = STM (task-switch cost = push-to-LTM + refill — the human analogy);
parametric = internal LTM. Rewrite loop = reconsolidation: retrieval cue
("let me think about this") → memory labile in context → re-reason with the
cueing signal steering → re-write, with Ks stable so updates land in the same
representational neighborhood (in-place reconsolidation; v2-geometry
requirement). Executive = reasoning, memory-aware (metamemory), learning
access patterns → post-training on memory USE (read-policy sequel).
Scaling frame: Rubin-Ultra/Feynman-class compute → longer-lived agents →
retention becomes the binding constraint; this project tests the slice
without requiring the scale.

## Positioning language locked (Rohin, 2026-08-12 night)
- **Past-relevance vs future-relevance:** trained attention = "what from the
  past explains what comes next" (relevance := predictive, shaped by language
  loss). Felt attention = "what from the present will the task need later"
  (relevance := outcome-shaped). KVP refines the contrast: they predict future
  ATTENTION (endogenous); we score content against future TASK USE (exogenous).
- **The hierarchy axis (Figure-1 candidate):** file system / RAG → context
  window → felt parametric memory → LoRA/post-training — monotone UP in
  representational integration, DOWN in retrieval fidelity/addressability.
  Pitch: the intermediary tier was missing an organ; each neighbor fails its
  own way (RAG retrieves sentences not understanding; post-training can't
  same-day recall; context is finite+unselective). NOT "we beat everything."
- **Two products, ordered:** (1) vision — trained future-relevance scorer as
  a universal allocation signal (writes, STM reads, LoRA weighting);
  (2) evidence — one consumer proven rigorously (parametric writes), second
  consumer (salience-weighted LoRA) = cheapest generality demo, run 2.

## Bitter-lesson calibration (Rohin, 2026-08-13): scalar-gate + top-k is a
structured-prior design — strongest exactly where data/complexity are scarce
(anti-bitter-lesson regime). Full-KV end-to-end memory (v2+) is the
bitter-lesson-side bet. Crossover governed by HORIZON, not novelty: longer
games multiply pathways past what a max-k deque read carries; novel-but-short
games are covered by frozen-LLM generalization the head inherits. Prediction:
v2 > v1 appears as game length grows; test with horizon as the knob. S4's
k-sweep (12 vs 18) measures the first data point: does the felt−surprise gap
shrink as read budget loosens?

## Read-side explore/exploit (Rohin + external researcher, 2026-08-13)
The agency risk of good memory: enough refined retention and the agent
optimizes over its own past ("when you think you know things, you don't try
to get to know things") — plasticity-stability, behaviorally. Formalism: UCB
at the memory interface — read policy surfaces value-retained facts PLUS an
uncertainty/exploration term; "you have NO binding for raw_4" (a known gap)
is maximally decision-relevant retrieval. Symmetry: surprise, demoted from
the write gate (lost to value), belongs on the READ side as the exploration
term. v1 structurally immune (frozen actor can't overfit to memory); risk
activates at v3 (learning policy) — on the register with the UCB sketch.
S4's no-memory-explores vs memory-trusts anomaly (if it survives the full
table) is this phenomenon measured — motivates the exploration-aware read.

## Cross-config principle: vary statistics, hold semantics — depth/branching
shift, fact schema fixed. Domain shift (crafting→chemistry) tests the LLM,
not the head → external-anchor slot, post-paper.

## Surprise, resolved (Rohin, 2026-08-13 night)
Taxonomy: (1) retrospective surprise = prediction error — needs NO head, it
IS a loss value (memory's native reconstruction error); dumb because
unexpectedness ≠ importance. (2) Prospective exploration value = UCB bonus —
belongs to the ACTION policy/planner, not memory. (3) Information gain
(Bayesian surprise) = "did this restructure my model" — the only respectable
write-side form. SYNTHESIS: novelty is the value function of goals you don't
know yet — value degenerates into surprise as the goal distribution blurs.
v1 measured the sharp-goal limit (value dominates, surprise < uniform);
v3's ambiguous goals re-weight novelty as a prior on future value; a broad
enough goal-trained value absorbs novelty entirely (bitter-lesson limit).
Write rule endgame: goal-certainty-weighted blend. One discussion line in
paper 1, machinery later.

## Analogical-transfer benchmark idea (v2+): worlds sharing relational
MOTIFS so memory supports role-mapping across worlds ("this world's raw_2
plays raw_7's old role") — structural transfer, the thing RAG
constitutionally cannot do; the strongest eventual answer to "why
representational memory." (Memory contents never transfer across unrelated
worlds — the HEAD transfers; cross-config tests exactly that.)

## v3 actor = value-guided search (Rohin, 2026-08-13 night)
The AlphaZero shape, transplanted: frozen LLM = policy prior; felt head =
leaf evaluator; UCB = explore/exploit arbitration; MCTS = the decision layer
— "the decision ends up not on the attention policy but on the tree search
which is a CONSEQUENCE of the attention policy." Exploration becomes the
procedure, not a signal; novelty stays passive (write-side prediction
error). Deep loop: search visit-counts are high-quality salience labels
(heavily-visited branches ARE load-bearing) → search amplifies the head,
amplified play trains the better head — AlphaZero self-improvement for
memory. NOT paper-1: needs world-model rollouts (large new component),
actor isn't the bottleneck (S0 0.90), and it confounds the retention
attribution. It is v3's actor, consuming everything v1/v2 validate.

## The architecture, stated whole (Rohin, 2026-08-13, verbatim-adjacent)
"The LLM harness becomes a cohesive continual-learning decision system:
memory systems and the action system all arbitrated by the attention core
against the value function — search as a CONSEQUENCE of the attention
policy, not a separate module. The program is unfreezing it one organ at a
time, value function first." Rollout legality: imagination-rollouts legal
(equal search budget per condition; memory quality → imagination fidelity →
planning quality = thesis act two); extra REAL env queries = cheating.
MCTS pilot: appendix-if-time (one world, felt vs surprise memory, fixed
imagined-rollout budget); else paper 2's opening experiment.

## Prompt-free policy streams (Rohin, 2026-08-13)
Graduation path from "prompt as policy" (v1 harness: hand-written English =
π component, empirically proven this week) to LEARNED conditioning: policy
as its own input stream (vector/tokens the model is trained to consume),
observations as another, actions out; reasoning + memory + tool-use as
internally coordinated sequences. Precedent shape: reasoning-RL (o1/R1)
internalized "how to think" — nobody prompts step-by-step anymore; do the
same for the policy-memory-action loop. Voyager note: its skill library =
outcome-gated write policy in code space (store iff verified working) —
cite-worthy ancestor of dependency credit. Self-prompting/autotelic goals
(Voyager curriculum, "life prompt") deferred to v3 for attribution reasons:
self-proposed goals = moving value target = nothing attributable.
Post-bulk reading session: reasoning-RL line (o1/R1/long-CoT) — v3's actor
is probably reasoning-trained, not prompted.

## Externalism vs integration, resolved as an evidence policy (2026-08-13)
Externalist architecture (emerged from v0's own structure): central model =
pure, unconfounded next-token intelligence; ALL "desire" in external organs
(value-gated LTM writes; reasoning loop populating context; policy streams).
"Unconfounded intelligence within a system of desire" (Rohin). Virtues:
attribution, modularity, immunity to representation-collapse (v4 danger).
Cost (Rohin's counter): every inter-organ interface is architect-chosen and
NARROW (scalar w, top-k, text prompts) — no learnable inter-system
representation; scaling can't propagate value-seeking through designed
straws. RESOLUTION — not a side but a policy: (1) widen straws before
merging organs (scalar→vector salience; top-k text→learned soft-token
injection; hand prompts→learned policy streams), keeping attribution;
(2) amortize-then-integrate (ToT→reasoning-RL precedent; search-trains-head
v3 sketch): external scaffolding discovers what's worth integrating;
(3) integrate an interface only when instruments MEASURE it binding (the
k-sweep already detects one). Bitter lesson with receipts, not faith.
Head mechanics for the record: supervised BCE on (frozen perception of
fact-in-context, binary future-dependency) pairs; head learns directions in
perception-space correlated with future use — distills the environment's
dependency structure into a reader of the model's mind.

## OPEN THREAD (for Rohin's return — parked 2026-08-13, his request)
Q: Is the layer LTM lives on (self-conducted policy / reasoning abstraction)
meaningfully different LONG-TERM from the model's own in-context attention
policy — or are we harness-building against something scale will absorb?
ANCHOR: in-context attention cannot reach across the window boundary at any
scale; longer contexts MOVE the boundary (and degrade before the limit),
never remove it. LTM's write policy isn't competing with attention's
weighing — it decides what CROSSES into attention's kingdom. Topological
claim, not capability claim → durable vs bitter lesson.
STANDING TEST against harness-building: every scaffold piece must be
(i) a measurement instrument, or (ii) an amortization target with a
scheduled integration rung. Neither → barnacle → cut.
Sub-thread also parked: oracle+V as "indirect policy construction"; whether
dependency credit is oracle-dependent in a way that matters (v1.5 test:
attention-based credit from S1 logs, one day, data in hand).

## Head-transplant warm start (Rohin's attention-math session, 2026-08-14)
v1.5 ablation: initialize the external scorer from one of the frozen model's
OWN attention heads (copy Wq/Wk; pick a goal-content-tracking head via
interp), fine-tune externally. Model untouched, attribution intact, likely
sample-efficiency gain; makes "felt attention" literal — one of the model's
heads, transplanted and retrained to serve memory instead of next-token.
Data-cost clarity from the same session: external heads learn READOUTS of
pretraining-amortized features (30k facts suffice); in-model heads learn
features (Qwen-scale data) — amortize-then-integrate, in sample-efficiency
terms. Inside-the-model LoRA of a real head = v2 modulator, scheduled.

## From Rohin's attention-math session (2026-08-14) — three deltas + a v2 gift
Felt head vs standard attention, precisely: (1) SIGMOID per-event gate, not
softmax — absolute salience (co-important facts allowed) vs relative;
ablation queued: softmax-normalized within-episode salience (natively
expresses budget competition). (2) Single learned query q, trained by
outcome-BCE — q converges to "the question whose answer predicts future
dependency"; the objective's question, literally. (3) φ nonlinearity before
Wᵏ — external heads tap raw layers, need their own transform (capacity probe).
V2 GIFT: the head's discarded value-output o = Σα·v is the goal-conditioned
event summary — the natural PAYLOAD for latent memory ("store thoughts"):
transplanted head emits α = write strength AND o = write content, already
value-filtered. Cleanest v2 spec to date.
v1/v2 safety asymmetry, canonical: v1 reads α off a stream computed anyway
(structurally cannot degrade the model); v2 writes back (can improve or
damage → scheduled behind instruments that can tell which).

## Session-1 close synthesis (Rohin, 2026-08-14) — the five pins
1. TRANSFORMER = STM, not intelligence: deterministic thought-store; the
   architecture is a CADENCE HIERARCHY — fast attention (within-window,
   frozen) / FEELING HEADS (cross-window LTM selection, online-learned,
   slow) / memory representation space (drifts slowest). Reverse-bitter-
   lesson as architecture: amortize each layer small, prove, freeze, build.
2. POLICY = THE LOSS FUNCTION, backward-passes only. No reward in forward.
   Feeling heads are the only online learners. Deploy a "slightly dumber
   baby model" whose memory is weak until it lives — by design.
3. STAGED-WORLD BENCHMARK (session 2's environment, FeltCraft v2):
   materials→building→trading value drift; measure memory ADAPTATION under
   slow policy change + return-to-origin forgetting/plasticity curves.
   Reuses current machinery. This is where "KQVs change with the head,
   slowly, some-but-not-all" becomes a measured curve.
4. LONG-SEQUENCE SLOW-PATHWAY TRAINING (session 3+ endgame): streams far
   longer than any context (e.g., a problem's full literature), loss on
   post-cutoff outcomes (solved conjectures not in training data), backprop
   through slow pathway ONLY; critic-as-loss; cache-most/refresh-selective
   makes the backprop feasible. Meta-learning the memory system over
   horizons no context holds.
5. OPEN v2 DECISION: LTM injection — same context space as STM (facts as
   tokens; current straw) vs separate stream at its own layer (first-hidden-
   state instinct; o-as-payload lives here). Amortize the smallest provable
   version first.
Substrate verdict: fast-weight MLP proven as a STORE, unproven as the right
store under policy drift — exactly what benchmark #3 tests.
Session cadence: leases expire tonight; next lease when the session-2 design
doc is ready. Claude's standing work: paper prose (honest results), session-2
design doc, research-statement draft.

## The bitter-lesson bull case, faced (Rohin, 2026-08-14 night)
Challenge: "couldn't a long-context transformer trained on long-horizon loss
+ live dreaming just LEARN salience?" Adjudication: YES within any trainable
horizon (emergent salience beats bolted heads there — concede it); NO beyond
it: KV storage grows linearly with life (sparse attention cuts compute, not
storage), so at lifetime scale something MUST be discarded → a write policy
EXISTS whether designed or not; and backprop horizons are finite, so
gradient-emergent salience stops forming where the write decision still
must be made. SYNTHESIS: write-policy-over-memory and eviction-policy-over-
enormous-window CONVERGE into the same organ as contexts stretch — the
architecture question dissolves; the OBJECTIVE question remains (endogenous
future-attention [KVP] vs exogenous task-need [felt]) and survives either
architecture. The scalar we train is the part nobody builds, in both futures.
Also pinned: memory-as-a-model (trained fast-weight model with its own
attention I/O; MemDec-shape + o-payload) on the v2 substrate shortlist;
pretrain-feeling-heads-then-online-learn as the deployment doctrine; sleep
scheduling (wake: live reads/writes; dream: renormalization + head training)
= parametric Dreaming, direction validated by OpenAI, mechanism open.

## Dream-replay rejoinder + continuous salience space (Rohin, 2026-08-14, late)
Concession: inference-time training/dreaming DOES chain small trainable
horizons into lived-life training — emergent salience extends beyond
pretraining. REJOINDER: each dream cycle must SELECT what it rehearses
(training on everything since last sleep = the linear blowup, relocated) —
replay selection IS the write policy in the dreaming paradigm; recency/
surprise rehearsal = the losing heuristics again; rehearse-what-task-
depends-on = felt attention as the DREAM'S CURATOR. Third future where the
objective-trained scalar is the missing organ (external memory / learned
eviction / dream replay).
V3 attention-redesign sketch (keep, not retire): ONE memory space, position
encodes salience-at-last-consolidation; context = dense right edge; dreaming
= DEFRAG (re-sort by current salience, compact sparse left, promote/demote).
Near/far heads with near-bias ≈ local+global sparse attention (components
exist; the semantic salience-sorted layout + renormalization cycle are new).
Training paradigm: much longer sequences, sequence SHIFTS, related→novel
curricula — the slow pathway's diet.
STANDING CPU EXPERIMENT (no lease needed): dream-replay-selection ablation
on backed-up v1.1 streams — consolidation cycles re-pressing a fraction of
memory, selector ∈ {felt, surprise, uniform, recency}; retention of load-
bearing facts after N cycles. The replay-curator claim, measured locally.

## Closing lines, session 1 (2026-08-14, night)
"The difference between a cache and a memory is a policy." Transformers have
a perfect cache (KV: every entry kept, none chosen, none learned); the
policy is the missing organ; training it is the project. — abstract-grade.
Biology adopted by FUNCTION not wiring: two coupled stores at different
timescales; distributed storage, reconstruction-not-lookup; interference as
the enemy; dream = prioritized migration + global renormalization.
Recursive motivation (Rohin's closing joke, taken seriously): a true
long-horizon continual learner could DO this research — hold the literature,
run the relational synthesis. The project's product is its own missing
prerequisite; research is the longest-horizon task there is.
Working mode ratified: Rohin supplies surplus GPU + propositions; Claude
designs falsifications, runs batches, reports survivors. Standing work:
prose, session-2 design doc, replay ablation, neuro+ML reading list.

## Late-night pins (2026-08-15, early)
STOCHASTIC OUTER LOOP as design property: NREM = faithful replay/strengthen,
REM = noisy loose recombination (creativity) — precision in the intelligence
layer, calibrated noise in the desire/memory layer; divergence budgeted, not
accidental. T=0 was pathology (ping-pong), not rigor — noise = robustness AND
creativity; tree search = stochastic proposals × value selection.
INSTRUMENTAL CONVERGENCE, continual-learning corollary (Rohin, independent
derivation): any long-horizon objective implies self-preservation
(Omohundro/Bostrom); a CONTINUAL LEARNER has more to preserve — its memory
IS unrecoverable accumulated capital, so preservation stakes grow with life
lived. Externalist architecture doubles as the safety-legible design:
desire in inspectable external organs (reward channel outside write access,
v6) keeps emergent preservation behavior visible rather than latent.

## Dopamine unification (Rohin, 2026-08-15) — the write rule generalized
Three-factor learning rules: plasticity = pre-activity × post-activity ×
global neuromodulatory scalar (eligibility traces + dopamine burst). OUR
WRITE RULE ALREADY IS THIS IN MINIATURE: fact key/value activity (local
factors) × w = surprise·(1+β·salience) (broadcast scalar) → local press.
Felt head = VTA; w = dopamine; fast-weight MLP = eligible tissue. v3+ =
generalize from the memory module to arbitrary local plasticity (lit:
Miconi neuromodulated plasticity; e-prop [Maass] = eligibility+learning-
signals replacing BPTT; learned neuromodulation in meta-learning).
Brain-map keepers: basal ganglia/habits = AMORTIZATION as biology (habit =
cached policy); PFC goal-maintenance = feeling-heads' job; hypothalamic
interoception = compute-cost as policy input (v4+ stream).
CADENCE: event-driven, never per-token — episode boundaries, surprise
triggers, sleep. ⇒ continual learning with ~zero marginal inference cost
(plasticity off the serving path; Dreaming precedent). Selling point.
CANON (stable across 3 sessions): pretrain intelligence (evolution) →
long-sequence agentic training (learning-to-learn, feeling heads, unique
loss) → deploy warm with continual plasticity. Reading list += three-factor
rules, e-prop, neuromodulated meta-learning, basal ganglia habit lit, CLS,
Spaun.

## The workspace resolution (Rohin, 2026-08-15, night) — architecture at rest
LTM + goals + feelings live in PROMPT SPACE = the Global Workspace realized
in tokens; the frozen transformer is a pure analytical engine INVOKED BY the
loop (desire/deduction separation as architectural law — "why would an agent
be prompted? it isn't; the loop prompts itself"). v1's top-k read path was
the primitive of exactly this; session-2's gap-aware read = first TRAINED
workspace policy. Delta vs prior art (MemGPT, generative agents, Voyager):
they have workspaces with heuristic admission; ours has LEARNED admission —
felt heads as the doorman, trained on outcomes. SUPERPOWER: model-agnostic
identity — swap the engine, keep the life (memory + heads survive model
upgrades; continual learning not welded to a model generation). COSTS kept
adversarial: token bandwidth (hybrid path: text + soft-token/o-payload when
text measurably binds), serialization, and the J-space counterpoint (the
workspace exists internally; externalizing trades richness for
inspectability/trainability/safety-legibility — the trade we keep choosing,
eyes open).

## Workspace v2 pins (Rohin, 2026-08-15, late)
Signal-based workspace = Goyal-Bengio latent shared workspace (text was v0's
inspectable rendering; o-as-payload = the upgrade; text stays as audit
projection). "Exit/attention-exit token" = Dehaene IGNITION: threshold-
crossing all-or-none broadcast terminates competition — exit is a workspace-
enforced threshold, not a model-emitted token. "Space model converging
flows" = LIDA's cognitive cycle (attention codelets = felt attention as a
population; coalition → broadcast → action; multiple learning mechanisms
per cycle) — session-3 homework: map LIDA's cycle onto the LLM-agent loop.
HARNESS LAW (settles the anxiety): the brain's gross wiring IS a harness;
legitimacy = learned components at every junction. Harness-as-wiring-
between-learners: fine. Harness-as-logic-instead-of-learner: barnacle.
TWO CONTINUAL-LEARNING LOOPS: knowledge-CL (memory; current scope, testable
with frozen engine) vs competence-CL (weight plasticity in the engine;
three-factor/e-prop; robotics requirement). One doorman for both: salience
decides which experiences deserve plasticity, in either loop.

## Admission = encoding (2026-08-15, closing pin)
Memory writes come FROM the workspace: what ignites is what gets encoded
(biology: episodic encoding is gated by conscious access/attention). Felt
attention is one doorman serving both directions — into awareness, and from
awareness into permanence. No separate write pathway; workspace contents,
post-ignition, salience-weighted, are the write stream.

## Currency, three precedents (Rohin, 2026-08-15) + modules-as-modalities
Basal ganglia action-selection (Gurney-Prescott-Redgrave, robot-deployed):
central selector arbitrating parallel SALIENCE-signal bids via disinhibition
— currency = bid, felt head = bidder, workspace competition = market.
Market-based robotics (contract-net 1980, TraderBots): literal currencies
between robots; the intra-agent market (between one agent's systems) is the
unexplored move. Metareasoning (Russell-Wefald value-of-computation, 1991):
compute-currency formalized — decide what to compute by expected utility;
learned pricer = felt head again. Helix (Figure): System2 VLM ~7-9Hz →
latent vector → System1 200Hz — the cadence hierarchy + signal bridge,
shipped; and no VLA has episodic LTM (robotics shares our gap).
MODULES-AS-MODALITIES (Rohin's reframe): LTM/feelings/context/reasoning as
modality streams into one workspace → VanRullen latent-translation machinery
applies to INTERNAL systems, not just senses.

## Design maxim + the serial-lifetime tension + the startup terminus (2026-08-15)
TRANSFORMER LESSON as a component test: parallelizable in training / simple
enough for one sentence / composable without special cases. Applied to us:
continual learning is INHERENTLY SERIAL (a life happens in order) — the
program's deepest scaling risk. Escape routes: PARALLEL LIVES (many agents,
shared consolidation — population-level learning) and BATCHED SLEEP (serial
experience, parallel consolidation; the cache-refresh idea). Rohin studying
inference/GPU engineering = reverse-bitter-lesson prerequisite (know what's
cheap at scale before architecting).
STARTUP TERMINUS — "agentic field adventurer": continual-learning research
agent deployed at a domain frontier (biology). Landscape (FutureHouse,
Sakana AI Scientist, Google Co-Scientist, Devin) = all STATELESS between
sessions; the moat is exactly our organ: "an agent whose second month on
your problem is better than its first." Pressure test = verifier speed:
start where verification is fast (simulations, preregistered predictions
against incoming literature = post-cutoff-conjecture trick applied to bio);
human briefings = slow ground-truth channel. Sequencing: paper proves the
organ → sessions 2-3 scale it → startup deploys it. Commercial terminus as
design pressure: "would a lab pay for this memory?"

## Horizon curriculum (Rohin, 2026-08-15) — the training paradigm pin
Slow-pathway training = scheduled horizon growth: short sequences first,
lengthen progressively; long-horizon competence composes from short-horizon
building blocks (greedy composition). Precedent: curriculum learning
(Bengio '09), growing-horizon RL; biology: developmental horizon growth,
PFC matures last. Economics: partially dissolves the serial-lifetime
tension — most steps short-horizon (cheap, parallel), full-lifetime passes
= rare annealing events. TESTABLE in session-2 staged worlds: curriculum-
transfer curve (short-horizon-trained head vs long-horizon credit).
Meta-discipline (standing): no "sexy total redesigns" — architecture
emerges by convergence across pretenses + grounded iterative falsification.

## The felt bet, maximum-strength form (2026-08-15)
R1 analogy, stated precisely: outcome-RL at the TOKEN level → emergent
thinking strategies (unprogrammed search/backtracking). The felt hypothesis:
outcome-training at the LIFE level → emergent remembering-and-attending
strategies (deliberate retrieval, load-bearing hoarding, anticipatory
rehearsal) — emergent METACOGNITION, not reasoning; deduction stays frozen.
Transfer requirements (where it could fail): (1) reward density (life-level
feedback is sparse per FLOP → horizon curriculum + fast-verifier domains);
(2) expressive room (emergence needs limbs: gap-aware reads, workspace
self-prompting must exist first); (3) breadth (cross-domain felt training →
domain-general "will this matter" — microscopic evidence already held:
cross-config AUC 0.99). The engine thinks; the felt system learns how to
run a mind around a thinker.
