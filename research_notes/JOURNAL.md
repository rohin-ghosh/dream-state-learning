# Research Journal — Dream-State Learning

Running log of ideas, debates, and decisions between Rohin and Claude.
Newest entries at the bottom. This is the thinking record — the design doc
will crystallize from here.

---

## 2026-07-09 — Project origin

Started from resume concept: "Dream-State Learning — Adaptive Memory
Consolidation for Continual Agents." Original framing: wake-sleep agent on
ALFWorld with a meta-learned routing policy sending trajectories to
episodic (FAISS) / semantic (SQLite) / parametric (LoRA) memory. Built full
codebase skeleton. Targets: NeurIPS 2026 workshop → ICLR 2027.

## 2026-07-10/11 — First cluster session (28h lease, ipp1-1619, A100 80GB)

Setup consumed most of the session (driver install, conda, deps). Ran first
baselines. Process lesson learned: **freeze the experiment plan before
booking compute.** Next lease starts with tested scripts.

### The pivot (mid-session, Rohin)

ALFWorld's 6 task types are too independent — memory reduces to per-type
procedure lookup. Real question: **relational structure.** Cup-on-coaster:
you can't grab the coaster without moving the cup. Forgetting the
dependency breaks the task; forgetting the cup's color doesn't.

Key reframe: **selective forgetting is the mechanism, not the bug.**
Original framing treated forgetting as failure. New framing: compression.
Forget detail (color, exact position), keep structure (dependency edges,
co-occurrence). Maps to systems consolidation (McClelland 1995): replay
extracts schema, cortex absorbs it.

### Salience bottleneck (Rohin)

Human brains retain few macro-structures per experience; a quant HFT model
absorbs innumerable micro-patterns from massive data. We want the human
end: **fewer structural nodes absorbed per episode → each memory more
impactful → useful overfitting to own experience.** "Make the model less
generally intelligent so it latches onto its experiences well." The
bottleneck size is a core hyperparameter.

### Environment iterations

1. Dependency-graph household tasks (cup/coaster) — built generator, but
   episodes were independent → no cross-episode memory pressure. Rejected.
2. Minecraft (real) — right dependency depth (crafting DAG), too heavy.
3. **Text-based crafting simulator** (built, verified) — persistent worlds,
   fixed resource locations discovered across episodes, real crafting DAG
   subset. Scripted agent completes stone_pickaxe chain in 11 steps.
   Qwen2.5-7B zero-shot: 0% success (after fixing hallucination-prompt,
   explore-routing, and circular-tool-dependency bugs). Hard task confirmed.

### Memory architecture brainstorm (Rohin)

- Not just external stores: what about a **masked region of the model as
  memory** — "ligamented parts of the brain"? Fixed-capacity subspace
  written during sleep, read during wake. Capacity constraint does the
  forgetting automatically.
- Or a **small model as the memory** — tiny model can't memorize
  everything, so it's forced to learn structure. Learned compression.
- Hopfield networks connection to explore (attention = associative memory).

## 2026-07-11 — Literature surveys (3 agents, ~80 papers)

Notes: 01_wake_sleep_consolidation.md, 02_parametric_memory.md,
03_agent_memory_benchmarks.md, synthesis in 00_synthesis.md.

Headline: the intersection **learned consolidation policy × embodied agent
× structural-retention benchmark** is unoccupied as of July 2026.
- No benchmark separates structural retention from detail forgetting.
- All existing consolidation selectors are heuristics (SuRe's surprise,
  PEAM's worthiness score). Learned policy = clean novelty claim.
- "Consolidation collapse" is a named, unsolved failure mode (2605.12978:
  utility rises then falls below no-memory baseline) — we position as the fix.
- Masked-region memory exists for facts (MEMOIR) and tasks (MoSEs), NOT for
  agent experience. Small-model-memory exists (Larimar, M+) but not as
  trained compressed store of agent experience.
- Threat: TMEM (Alibaba, 6/2026) — online LoRA agent memory. No sleep, no
  learned policy, no embodied eval. Window narrowing; move fast.
- Hopfield-for-agent-memory: theory mature, system unbuilt (ICLR 2026
  MemAgents workshop lists it as open direction).

### Paper shape decision

Analysis+benchmark chassis (A) with novel method as engine (B):
1. Benchmark with ground-truth structure metrics
2. Run existing memory families faithfully (no tweaks — credibility)
3. Novel consolidation method competes against that field
If B works it's the headline; if B stalls, A ships alone. B standalone has
no floor.

## 2026-07-11 — Design debates (pre-design-doc)

### The supervision problem (Claude)

What makes direction B hard: **there is no label for "what should have been
remembered."** A memory's value is only revealed episodes later. Sparse,
delayed reward; brutal credit assignment. Every heuristic selector in the
literature exists because this signal is hard to learn.

### Reward-modulated consolidation (Rohin's insight, convergent)

Rohin independently proposed "external reinforcement system that fuels its
attention" → this IS the missing training signal. Neuroscience:
dopaminergic modulation of hippocampal replay (reward-tagged experiences
replay preferentially). ML: task outcome trains the consolidation policy
via policy-gradient outer loop — did consolidating memory M improve
later-episode return? Learned selector vs PEAM's heuristic = the delta.
Rohin's MCTS/AlphaGo-Zero background applies directly: reward shaping lets
short-term consolidation choices be credited against long-term outcomes.

### Rohin's hunches logged (to develop)

- "Everything in ML done long enough goes back to data and training, not
  hardwiring" — bet on learned consolidation over hand-designed rules.
- "Attentioned memory and attentioned actions are driven on similar
  mechanisms" — memory retrieval and action selection as the same kind of
  query-key gating.
- Board-game-with-changing-rules environment: agent masters rules, rules
  shift, measure adaptation. Static chess = just post-training; continual
  learning needs a moving task.
- Survival Minecraft as "unsupervised self-post-training" — agent deployed
  with survive-goal, sleeps and retrains on own graded memories.
- Open questions raised: what's the right sleep rate (adaptive? "if he dies
  every game, sleep faster")? Cold start — policy only, or initial context?
- Parked deliberately: ever-changing/vague reward policies (humans have
  them; separate research topic; stay scoped to memory).

### Scoping direction (emerging consensus)

Scope to memory, not action learning. Dopamine-for-memory only, not
dopamine-for-choice. Fixed goal-conditioned episodes in persistent worlds;
survival pressure at most as a step budget, not open-ended reward design.

## 2026-07-11 — The architecture debate (Rohin's big-picture pass)

### Rohin's pushback on frozen-actor scoping

Confounding isn't a bug — it may be a necessity: human skills (muscle
memory, energy, emotion) don't optimize individually, they optimize *as a
group* under massive data, precisely because they're confounded. The
end-state vision requires memory and action growing together.

### Rohin's compute concern

A good memory architecture may show nothing until the agent has run
immense trials — memories only pay off once they're a good representation
of the task space. (Note: this cuts in favor of frozen-actor v1 — the LLM
prior does the acting for free; only the small memory system needs data.)

### Rohin's bitter-lesson refinement

"Someone had to invent the perceptron/transformer" — the job is to set up
the learning so that scaling data actually scales the learning. Hardwire
the *shape*, learn the *content*.

### The architecture sketch (Rohin, verbatim essence)

Not inventing thinking (transformer does that) or perception (CV/audio
models do that). Architecting the continual-learning wrapper:
- Two inputs: **data** (what's happening) and **reinforcement** (how it's
  being rewarded)
- Components: long-term memory, short-term memory, sleep, and a context
  composed from reasoning + action + memory + policy streams
- Key synthesis: "this is literally a transformer-like attention memory —
  attention over long memory, short memory, and policy/desire composes the
  context; the transformer transforms that context into next-token
  generation. Context length is the immediate thoughts in your mind."
- During sleep: long-term memory, policy, AND the thinking model train.
- The balance between attention-for-context (retrieval) and
  how-much-to-learn-from-new-events (weight updates) must be honed by
  data — that balance is what produces "dynamic plastic intelligence."
- Agents like OpenClaw use rudimentary md files/skills/context because
  hardcoded memory doesn't scale — you can't scale a knowledge graph to
  the internet. The missing piece is architectural.

### Sandbox/currency vision (parked as future work, papers 2-3)

Agent in a sandbox (e.g. CUDA kernel design), currency-backed reward
(throughput per energy). Trains policy + short/long memory in sandbox 1,
transfers to sandbox 2, learns faster — meta-learning across sandboxes.
Currency as the cleanest agency driver for machines (safer than
survival/lust drives; it's literally training for value production). Elo
as currency for chess. Multi-agent selection dynamics acknowledged as fun
fantasy, explicitly deferred.

### Claude's proposed decomposition: reader/writer split

The consolidation-policy-output question resolves cleanly inside Rohin's
sketch:
- **Read side = attention** (dense, cheap, every step): learned retrieval
  over short-term store, long-term store, and policy state to compose
  context. Trainable end-to-end.
- **Write side = consolidation policy** (sparse, sleep-time): decides what
  enters long-term memory and what gets baked into weights. Trained by
  policy gradient on downstream return (the dopaminergic signal).
Maps to hippocampus(writer)/cortex-attention(reader). Two learned
components, one architecture.

## 2026-07-11 — Vocabulary settled: currency / policy / two attentions

### Rohin's PFC-dopamine correction

Earlier framing conflated them. Corrected: **PFC is the policy** (evaluates
how good actions are, goal-directed control). **Dopamine is the currency**
(the reward signal that trains the policy). Policy shapes thinking AND
context; context is what an intelligent agent has most control over.
→ ML mapping: currency = reward function, policy = learned value/policy
network, dopamine signal = the training gradient. This is actor-critic.

### Freeze currency (Rohin)

Sleep consolidates all systems — wipe short-term, write long-term, update
policy, update thinking — but **currency stays frozen** as the dependent
variable. (Correct experimental design: reward function is
experimenter-defined; everything else learns against it.)

### Two attention systems (Rohin)

- **Thinking attention**: how thoughts in the head become the next
  productive thoughts — the transformer's internal attention.
- **Context attention**: how the agent decides what thoughts to bring INTO
  the head — retrieval/composition over memories + policy.
Both should become fluid/trainable over time, trained by currency. True
long-term intelligence requires fluidity in attention, not just weight
retraining — agents use policy/memory/currency to influence how they
think, including reasoning-directed self-training (choosing what data to
train yourself on = the writer choosing replay content).

### The substrate/harness reframe (Rohin)

The real contribution may be the **trainable harness**: wiring tweaked
memory forms + LLMs + policy functions together, with a system that trains
each module through time and sleep while also training the harness itself —
all against currency. Connects to the OpenClaw observation: current agent
harnesses (md files, skills, static context) are hand-coded and don't
scale; a trained harness is the delta.

### Data cost + evolution-pretraining (Rohin)

Training a harness on top of a transformer needs an order of magnitude
more data. Long-term fix: evolution-like pretraining that sets base harness
weights so it doesn't start from zero, without hand-designing. (Practical
v1 version: imitation-initialize the policies from heuristics, then RL.)

### Existential riff (parked, but logged because it's good)

Currency = the existential pull. Universe as bitter lesson: rocks are
molecular structures that withstood planetary formation; organisms are
systems that withstand time by exploiting patterns in data; sentience is
using mental simulation (sandboxed brains) to grow withstanding faster
than brute-force physics. An agent becomes sentient-ish when its currency
is no longer externally defined — humans revise their own currency; our
agent won't (yet). For now: define the currency, freeze it.
→ Adjacent formal literature: Friston's free-energy principle,
Schrödinger's "What is Life" (organisms resist entropy via modeling).

## 2026-07-11 — Two more surveys (prior-art on "second attention" + neuroscience)

Notes: 05_learned_retrieval_prior_art.md, 04_neuroscience.md.

### Prior-art verdict: PARTIALLY PUBLISHED — the broad lane closed in 2026

"Learned retrieval for LLM agents trained by task reward" is now a crowded
subfield (Memory-R1, Mem-α, MemRL, AgeMem, Mem-π, ContextCurator,
Auto-Dreamer — several on ALFWorld). Direct overlaps with our scoped v1:
- **ContextCurator (2604.11462)**: separate lightweight "subconscious"
  policy composing a frozen executor's context, RL-trained on task reward.
  ≈ our reader/subconscious split. (But: prunes transcript only; no LTM
  retrieval, no goal-state stream.)
- **MemRL (2601.03192)**: utility/Q-value memory selection replacing cosine,
  on ALFWorld, +82% vs memory-free. ≈ our "learned retrieval beats fixed."
- **Auto-Dreamer (2605.20616)**: offline wake/sleep consolidation, GRPO on
  agent reward, ALFWorld transfer. ≈ the writer half of dream-state.

**Still genuinely open (the narrow wedge):** a *dense, differentiable
second-attention layer* that jointly attends over typed LTM + STM +
**policy/goal state** to softly compose context, coupled with sleep-phase
consolidation, jointly trained. Everyone else uses DISCRETE memory ops
(tool calls, prune/keep, value tags) — nobody has one dense attention
composer over typed streams incl. policy. Policy-as-attention-stream is the
least-claimed piece.

**Strategic shift:** edge is no longer "first to the idea" (funded labs
converged on it in 2026) but "referee the crowded field on an axis nobody
built a ruler for" (structural-retention vs detail-forgetting benchmark
still does not exist) + stake the narrow dense-attention mechanism. Open
strategic fork for Rohin: referee-the-field analysis paper vs jump out to
the emptier-but-brutal harness/substrate vision.

### Neuroscience findings that change the design

1. **CLS is literally our architecture.** Kumaran/Hassabis/McClelland 2016
   (TiCS, written for AI) is the load-bearing citation: consolidation replay
   should be *weighted and selective* — prioritize rewarding/surprising/
   goal-relevant. Direct motivation for a learned writer.
2. **Reward-gated consolidation is mechanistic + gives us a design nuance:**
   synaptic tagging & capture (Frey/Morris 1997) = a biological *eligibility
   trace* for what to store — recent weak experiences get retroactively
   consolidated if a high-value event occurs soon after. → the writer should
   be able to reach back and consolidate earlier episodes when later reward
   arrives (retroactive credit, not just current-episode).
3. **"Two attentions" is real as a THREE-way gate:** input-gate (write) /
   maintenance / output-gate (read), learned by an RL signal — PBWM
   (O'Reilly & Frank 2006), basal ganglia dopamine-trained gating over PFC.
   Our reader = output gate; writer = input gate. Both RL-trained. Confirmed
   blueprint.
4. **Global Workspace Theory legitimizes the subconscious-gate → conscious-
   workspace module** (Dehaene: bottom-up salience × top-down amplification →
   broadcast). Use as FUNCTIONAL inspiration only — "subconscious" is folk
   terminology, not a consciousness claim. Composed context = the workspace.
5. **Biggest gap in our module list: no neuromodulatory/homeostatic control
   layer.** We have where info lives, not when/how-fast/whether to write.
   Highest-value missing pieces:
   - **Metaplasticity** = biological EWC (Kirkpatrick 2017): per-weight write
     protection — the mechanism most directly preventing catastrophic
     overwrite. Relevant if/when we do parametric consolidation.
   - **Homeostatic downscaling during sleep** (SHY, Tononi/Cirelli 2014):
     sleep should PRUNE/renormalize, not only strengthen. → the writer needs
     a forget/downscale operation, not just write. (Matches Rohin's
     selective-forgetting thesis exactly.)
   - **ACh encode-vs-consolidate mode switch**, **NE adaptive gain** (learning
     rate/exploration), Doya 2002 map (DA=TD-error, 5HT=discount, NE=explore,
     ACh=learning-rate). Our "reward" module currently = dopamine only.
   - Cerebellar/motor learning correctly LOW relevance for a text agent.

### Emerging freeze schedule (Claude, from the debate)

| Module | v1 (paper 1) | v2 | v3+ |
|---|---|---|---|
| Currency (reward fn) | FROZEN (forever, until sentience paper) | frozen | frozen |
| Thinking (LLM + internal attention) | FROZEN | frozen | sleep-time LoRA updates |
| Context attention (reader) | **TRAINED** | trained | trained |
| Consolidation (writer) | **TRAINED** | trained | trained |
| Policy (PFC/value) | LLM prior, static | **TRAINED** | trained |
| Sleep schedule | fixed K | adaptive | learned |

## 2026-07-11 — DECISION: build the harness. The communication-layer reframe.

### Direction decided (Rohin)

Chose the harness over the referee-the-field benchmark paper. Reasoning:
existing memory mechanisms aren't compelling enough to be worth
benchmarking for their own sake; the higher-level *orchestration* is the
real object of study. "Wide open would be bad — it means the problem isn't
ready. The mechanisms exist now (2026 papers), so the orchestration is
ready to pursue." Follow curiosity; we have a better idea than the safe one.

### The reframe: this is a COMMUNICATION/CONTROL layer, not an agent

Rohin's NVLink insight (his day job is NVLink MSE): what we're building is
a communication fabric between cognitive modules.
- **Attention (wake) = communication** that gathers from the modules
  (LTM, STM, policy, currency-state) to compose context for the "conscious"
  transformer.
- **Dreaming (sleep) = communication** that stops routing to short-term,
  reconciles long-term memory + policy, renormalizes.
The contribution is the *trained* communication layer + packaging the
mechanisms into one form. Existing agent harnesses (md files, skills,
static context) are hand-coded routing; ours is learned.

### Key distinction: "exists in time," not an agent loop

An agent = a loop above reasoning: fixed context → reason → self-judge
execution. This thing is different: it **exists continuously in time**, with
an *ongoing* context and *ongoing* execution, learning as it runs. This is
the streaming/lifelong distinction, not episodic agent behavior. Design
must not treat episodes as independent resets — the substrate persists.

### The floor problem, and its resolution (Claude's discipline injection)

Rohin's own principle: "you need good mechanisms to prove the
orchestration." → RESOLUTION: the 2026 papers become the MODULES, not
competitors. Use an existing learned-retrieval store, an existing
consolidation method, an existing memory op — off the shelf, faithful — and
make the LEARNED COMMUNICATION LAYER BETWEEN THEM the contribution. This
gives the harness a floor (modules are known-good) and isolates the novel
variable (the orchestration). Without this, the harness has no floor and is
undebuggable.

### Control layer jobs (emerging)

1. Dreaming (sleep-time reconciliation: write LTM, renormalize/downscale,
   retroactive consolidation)
2. Attention (wake-time context composition from typed streams)
3. (candidate) Traversal / information routing between modules
Currency frozen throughout.

### DECISION IS DETERMINISTIC (Rohin, 2026-07-11)

Two candidate contributions surfaced:
- **A** = learned communication fabric (the harness/orchestration layer)
- **B** = structural-renormalizing long-term memory (keep relational
  structure, drop episodic detail, via sleep-time downscaling)

Decision rule (not a preference — a test): **search whether B exists in
usable off-the-shelf form.**
- If B EXISTS → build the harness (A) using B + other off-the-shelf modules
  as components; A is paper 1, uses B as a module, B-as-novel becomes a
  later ablation/paper.
- If B DOES NOT EXIST → build B fully as paper 1, shelf A for after. Use a
  DUMB fixed communication layer for B's harness (static retrieval, fixed
  sleep schedule) to keep B's contribution isolated and legible.

Either way: exactly one novel piece per paper. The other modules are
off-the-shelf, faithful, unmodified. One mechanism / two directions
(wake-read + sleep-write) stays unified as a single fabric.

Bonus insight (Rohin): designing the harness top-down *reveals the needed
modules* — a goldmine of downstream research topics (each missing module is
a potential paper). The harness is both the destination and the map.

### RESOLVED: B is paper one (2026-07-11)

Verdict from 06_structural_memory_decision.md: **(b) PARTIAL** — every
ingredient exists separately, but no released system consolidates toward
structure and away from detail (schema-up / detail-down) over time. Per the
pre-committed deterministic rule → **B does not exist usable → build B as
paper 1, shelf A (harness).**

Gift: a 2026 position paper — **Experience Compression Spectrum**
(arXiv:2604.15877) — names this exact axis the **"Missing Diagonal"** and
proves no system moves along it. We cite them for the gap; we build the
mechanism. We don't have to argue the gap exists.

Closest partial ingredients (cite, don't compete):
- **SCM** (2604.20943): has SHY-style renormalization (0.8× downscale) +
  typed semantic graph, but forgetting is node-importance-based, not
  detail-vs-structure; toy factual recall only, no agent tasks.
- **Auto-Dreamer** (2605.20616): learned offline sleep consolidator on
  ALFWorld etc., but abstraction is generic blob-compression — no
  structure-preserving/detail-discarding objective.
- **Experience Compression Spectrum** (2604.15877): states the target
  property exactly, proves the gap, implements nothing.

Verify-before-cite: SleepGate/"Learning to Forget" ID 2603.14517.

→ Paper 1 = a memory that consolidates by keeping relational structure
(dependency graphs, schemas) and shedding episodic detail, measured on the
crafting-sim benchmark (which already has ground-truth dependency graphs).
Dumb fixed communication layer around it (static retrieval, fixed sleep
schedule) to isolate B's contribution. Harness (A) is the sequel.

### Paper 1 (B) substrate crystallizes: small overtrained net + attention-weighted imprinting (2026-07-11)

Scope reaffirmed: B is a **POC paper**, not the scalable bitter-lesson
mechanism. Live-learning attention fabric = paper A (next). B builds the
memory module + a policy-driven consolidation, hand-scheduled.

**Substrate (Rohin's concrete proposal):** LTM = a *small* trainable net —
"a small version of the thinking model / basic low-compute world model" —
that gets **overtrained/overfitted to the memories written into it.**
Attention weights how strongly each memory imprints ("100 attention points
→ shows up stronger in the model"). Structure = the *connections the net
forms in its weights* (structurally biased "the way a model is," not a
hand-built graph). This is the LoRA-as-memory / small-model-as-memory line.

**Dream mechanism (simple):** freeze the thinking model; during sleep,
attention-weighted fine-tune the small memory net on STM contents; purge STM.

**The crux (Rohin named it):** "what sort of model can hold these
vectorized relations while keeping proper retrieval." Retrieval from an
overtrained small net is the known hard part — this is where the research is.

**Attention source:** policy → currency. Delayed reward is tractable
*because* of the policy/value function (PFC): you judge value at the current
state, so you don't need the final outcome to assign credit. POC currencies
are simple (chess: closeness to winning; crafting sim: progress to goal).

**Measurement (corrected):** beat a *filled short context* on a
short-context model (NOT 700k long context) at a fixed memory budget.
Headline = task currency at fixed budget. Explanation = structural- vs
detail-retention via ground-truth graphs (emergent, not imposed).

**Claude's synthesis to confirm:** small net + attention-weighted imprint +
capacity-limited interference = a modern ASSOCIATIVE MEMORY where the
interference that normally degrades recall becomes the *forgetting
mechanism* — strongly-imprinted structure survives, weakly-imprinted detail
gets overwritten. The bug (interference) becomes the feature (selective
forgetting). Ties Hopfield (associative memory) + synaptic homeostasis
(renormalization) + Missing Diagonal (structure-up/detail-down) into one
mechanism. Open step-2 question: substrate concretely = LoRA on frozen
model vs separate small LM vs associative net.

### SETTLED — Paper 1 (B) scope, ready for design doc (2026-07-11)

The eight-point skeleton, confirmed:
1. B = a consolidation **procedure** (attention-weighted sleep post-training),
   NOT a new model architecture. Standard small net + standard fine-tune;
   novelty is how writes are weighted and scheduled.
2. Mechanism = attention-weighted imprinting + capacity-limited interference
   → structure survives, detail washes out. Emergent, not imposed.
3. Attention source = policy → currency. Delayed reward tractable via value
   function (PFC). POC currencies simple (chess: closeness to win; crafting:
   progress to goal).
4. Substrate = **separate small parametric net** (NOT masked-in-model) —
   chosen for MEASURABILITY (can probe contents against ground-truth graph).
   Masked-region-in-thinking-model is more biological but opaque → deferred
   to paper A+. "Consolidate into the model later as it grows; not now."
5. Measurement (refined): **attentioned-memory + small context** beats
   **slightly-less-small filled context** at a FIXED memory budget. Also
   compare vs RAG, LoRA-memory. Headline = task currency at fixed budget;
   explanation = structural- vs detail-retention via ground-truth graphs.
6. De-risk = **Experiment 0**: test the memory module's write/read cycle in
   isolation from the agent loop (write known structured memories → probe
   retrieval → find capacity break point → see how attention-weighting
   shifts it). This is a scoped test of the renormalizing-attention
   mechanism in a confined problem.
7. Environment = crafting sim (ground-truth dependency graphs).
8. Deferred to paper A: live/learned attention, masked-in-model memory,
   full multi-module orchestration, memory+policy+context unified.

Last open sub-fork (to be resolved empirically by Experiment 0, not debate):
small memory net = tiny LM (queried in text) vs key-value/associative net
(queried by embedding).

Overarching one-line framing (Rohin): "Can we build an attention mechanism
that works for memory (and later policy and other forms) OUTSIDE just the
model, while also composing context — i.e. expand attention beyond the
transformer's own inputs to external memory." B = the confined POC of that;
A = the live/learned/unified version.

NEXT ACTION when Rohin returns: draft the design doc from these 8 points.

### Grand vision + paper framing (Rohin, 2026-07-11)

The endgame: once memory and policy are engrained into the model, the
EXTERNAL attention mechanism we're building must become INTERNAL — a way the
model retrieves from *itself* during reasoning. The full "live model":
- currency as the telic/atelic outcome (the pull)
- live inputs constantly training it
- live actions constantly executed
- a policy for deciding actions
- short-term memory = RAM, long-term memory = disk
- all inside one model
= a machine analogue of consciousness: experiencing inputs from senses +
memories + desires/currency, using the thinking part to decide what to
reason on and what to do; capable of metacognition (thinking about what its
currency is, what its policy looks like), dreaming to build its own model.
Some things hard-engrained (sleep, energy, curiosity/drive); attention —
external or internal — is THE mechanism throughout.

**Paper framing to use:** attention is at the heart of all of this. Even
"Attention Is All You Need" *underestimates* attention — it's not just
sequence mixing inside a model, it's the general mechanism of compute
allocation across memory, policy, context, and action. B is the first
confined proof that attention can be extended beyond the transformer's own
inputs (to external memory); A internalizes and learns it; the grand vision
is the fully self-attending live model. Open the paper with the big picture,
keep the contribution scoped to B. (Discipline note: vision goes in
intro/discussion as framing; experiments stay scoped to B.)

Personal thread (worth remembering, motivational core): Rohin suspects ADHD
— frames it as a difference in currency/reward that produces an atypical
attention mechanism. Lifelong interest in his own attention + metacognition.
The through-line: someone who has always studied his own attention ending up
architecting attention mechanisms. This is the curiosity fueling the work.

### Deep literature round — 5 clusters (2026-07-13)

Notes 07-11 + INDEX + RANKED_READING_LIST. Crystallized decisions:

**Substrate RESOLVED:** small **ATLAS/Titans-style neural fast-weight module**
(deep-MLP memory, salience-gated gradient write, adaptive decay). Use ATLAS
window/batch (Omega-rule) variant — built to memorize a window at once =
matches a sleep batch. Its write literally IS attention-weighted
post-training; forgetting is native (capacity superposition + decay gate);
standalone = measurable in isolation (Experiment 0). LoRA-on-backbone
REJECTED as substrate (entangled, unmeasurable) → becomes a baseline.
Backup substrate = **Larimar** Kanerva matrix (one-shot write) → the
"gradient-imprint vs one-shot-imprint" ablation arm.

**Write-attention signal RESOLVED:** consolidation weight `w ≈ f(V(s),
|TD-error|)` — value magnitude (salience) + TD-error (surprise) =
generalized Prioritized Experience Replay. V(s) = "policy judging value at
current state" → gives per-memory weight BEFORE reward lands (the
delayed-reward answer). Estimate via Dreamer λ-returns, cheap in a sleep
pass.

**Non-stationarity CAUTION:** learned value only valid near data-policy
("What Model Does MuZero Learn?"). Stale value mis-ranks which memories to
imprint. Fix: refresh value targets each sleep cycle; KL/trust-region-bound
per-cycle policy move (Policy Consolidation).

**MCTS → deferred to Paper A** (B needs only a scalar value; MCTS confounds
the core ablation; its home is the subconscious-simulation story).

**Formal foil:** "Transformers are Stateless DNCs" (2026) proves transformer
memory is write-once/stateless — frame the contribution against THAT
boundary (stateful, re-writable, offline-consolidated), not "adding memory
to transformers."

**Competitive landscape TIGHTENED — important:** four 2026 concurrent works
now in close orbit — **PEAM (2605.27762)** closest system (parametric
embodied memory + consolidation governance), **Auto-Dreamer (2605.20616)**
near-identical (learned offline dreaming consolidation, same envs) =
baseline-to-beat, **EVAF/Memory Depth (2606.26806)** keep-parametric-vs-
discard split (goal-vs-fact, not structure-vs-detail; declares forgetting
unsolved = ammo), **SCM (2604.20943)** richest component donor (NREM
downscaling). The lane is a RACE now, not empty. Wedge that survives:
structure-up/detail-down + value/attention-weighted imprint + **ground-truth
dependency-graph measurement (the moat — nobody else can measure the axis).**

**Baseline set (matched memory budget):** no-mem floor → filled short-context
→ RAG (+Mem0) → LoRA/Remembering-Transformer → CLIN (reflective) → A-GEM
(classical CL) → Auto-Dreamer (bar to beat) → graph-oracle ceiling.

**Eval-fragility rules:** (1) score via ground-truth graph programmatically,
not LLM-judge; (2) run table on ≥2 backbones, claim only persistent gains;
(3) average ≥3 curriculum orderings, tune replay fairly (naive replay fails
for LLM agents = false floor). Complement crafting-sim with ScienceWorld/
ALFWorld slice for comparability + LifelongAgentBench to defuse
"bespoke-benchmark" objection.

**Borrowable components:** MoE-LoRA isolated adapters (PEAM), NREM downscaling
(SCM), 4-D importance/surprise+valence tag (SCM/EVAF), self-triggered
when-to-sleep + forgetting-gate (PEAM/SleepGate), RL dreaming curriculum +
REM recombination (2606.03979/SCM), wake→NREM→REM + param-freeze template
(WSCL). **Must build new:** attention-weighted structure-up/detail-down loss;
the structure-vs-detail metric+benchmark; learned routing vs heuristic gates;
embodied instantiation with the split.

### Thesis framing: attention as capital / the cognitive stack (2026-07-13)

Rohin's grand framing: transformer attention must EXPAND beyond token-mixing
to memory, policy, and other functions. Each function has its own internal
attention; a general attention substrate allocates between them. Precise
reframe: this cross-module allocation is not softmax "attention" — it's
**capital / resource-economics** — a signal that TRAINS within each function
(internal) and BETWEEN functions (external). "Attention" is fine as LLM-era
language; "capital allocation" is the more accurate mechanism for the
heterogeneous multi-module case. (Distinct from dopamine=currency; capital =
the allocation of compute/representation across modules.)

Cognitive stack (Rohin's table → build-now vs defer):
| Function | Bio | Status for us |
|---|---|---|
| Sensors | eyes/ears/skin | given (text input) |
| Input router | brainstem/thalamus | trivial v1 |
| Perceptual encoder/world model | sensory+assoc cortex | frozen LLM |
| Active scratchpad | frontoparietal WM | context window (STM) |
| Episodic memory index | hippocampus | **BUILD (Paper B)** |
| Learned concepts/knowledge | neocortex | frozen LLM + consolidated LTM |
| Value & significance | OFC/vmPFC/amygdala/striatum | value fn (write-weight) |
| Policy & action gating | PFC–basal-ganglia | LLM prior (v1), learned (A) |
| Prediction/error | cerebellum | defer |
| Global gain/exploration | neuromodulators | defer (v3) |
| Homeostatic objective mgr | hypothalamus/endocrine | currency (frozen scalar) |
| Actuators | motor cortex | action interface |

→ The table IS the program map (each cell = a potential paper — the
"goldmine" insight). v1 builds ONE cell (episodic/LTM) + its update
mechanism. Do NOT build the stack.

Precise novelty correction (from cluster-1 findings): "we don't have
attentioned memory" is imprecise — NTM/DNC/Titans/ATLAS DO have
attention-addressed read/write memory. What's missing = **stateful,
offline-consolidated, structure-selective** memory. Frame against the
stateless/write-once boundary (2026 stateless-DNC proof), not "no attentioned
memory exists."

Scoping (reaffirmed): FIRST get the right LTM system.
- LTM = parametric, attention-consolidated (matches ATLAS/Titans substrate
  decision), updated by sleep (+ later: conscious/manual attention).
- STM = retrieval or set-aside context.
- Context PARTITIONED into {inputs} vs {retrieved memories} — a real v1
  design choice to keep.
- "Variable amount of attention controlling LTM" (live/conscious allocation)
  = Paper A. Paper B = fixed-schedule sleep consolidation into the right LTM.

### The reframe that gives the paper its spine: it's a LEARNING problem (2026-07-13)

Rohin: "this isn't just a memory problem, it's a learning problem — you're
using attention to TEACH memory. LTM is smart, dynamic, purposefully not
fully accurate; you remember memories by how you PARSED them." Attention =
efficient capital: learning what groupings, and HOW MUCH of them, yield the
most efficient results (MoE routing = the existing instance; must be trained
on where AND how much).

**THE crux question (Rohin):** episodic sleep consolidation is basically
training — so how does this architect DIFFERENTLY from just fine-tuning the
LLM? → This is the project's justification. Answer = Complementary Learning
Systems:
- Fine-tuning the one big net on each experience = ONE system, ONE timescale
  → catastrophic interference. (This is literally our naive-FT baseline, not
  our method.)
- CLS = TWO systems, TWO timescales: a fast, plastic, pattern-separated
  episodic store encodes specifics WITHOUT disrupting the slow stable
  world-model; offline replay during sleep gradually + SELECTIVELY teaches
  the slow system. Separation both prevents forgetting AND enables schema
  extraction.
- Our small net = hippocampus (fast, high-plasticity, lossy, RECONSTRUCTIVE
  — stores "by how parsed," structure-preserving/detail-shedding = a feature
  of small-capacity + value-weighted imprint, NOT a bug). Frozen LLM =
  neocortex (in v1, frozen entirely; the slow cortical update is later).
- So Paper B = the hippocampal encoder + its consolidation dynamics.

**Biology of task differentiation (why the brain doesn't use one learner):**
parallel anatomically-separate systems with different plasticity rules,
gated by neuromodulators + sleep stage:
- hippocampal/declarative (fast, sparse, one-shot) vs neocortical/semantic
  (slow, overlapping, extracts regularities) vs striatal/procedural
  (dopamine-trained habit) vs cerebellar (error-correction) vs PFC working
  memory (transient, no lasting change).
- ACh high in waking = encoding mode (favors input, suppresses retrieval
  interference); ACh low in SWS = consolidation mode (hippocampal→cortical
  replay via sharp-wave ripples). Schema-fit (Tse 2007, mPFC-gated) speeds
  cortical consolidation when new info fits existing structure. SHY
  (Tononi/Cirelli): sleep net-downscales synapses = renormalization.
- Differentiation is not a decision — it's parallel systems + neuromodulatory
  gating + salience/reward tags (DA/NE) prioritizing what consolidates.

**Scoping decision (Rohin):** test the memory as an INDIVIDUAL SYSTEM, NOT
wired into LLM context. Context integration = Paper A ("capital allocation
training"). Implication: Paper B becomes a MECHANISM/ANALYSIS paper — measure
structure-vs-detail retention via reconstruction/retrieval probe against
ground-truth graphs, no LLM in the loop. Bonus: this DODGES the
eval-fragility warnings entirely (no backbone-dependence, no LLM-judge) and
the standalone structure-vs-detail measurement IS the moat. Tradeoff: needs a
readout/probe to show "usefulness"; the "beat filled-context at fixed budget"
comparison becomes secondary/optional.

**ATLAS/Titans deltas (our differentiation):** ATLAS/Titans update memory
ONLINE at test time via per-token/window SURPRISE. We update OFFLINE during
sleep, weighted by VALUE (not just surprise), with structure-vs-detail
selectivity, tested STANDALONE. "Between a transformer and ATLAS attentioned
memory" — ATLAS-style fast-weights + a sleep-consolidation training loop +
value-weighting.

### Meta (Rohin, on his own currency)

Two currencies for the project: (1) get into elite research environments,
(2) do something he's proud of / help the field. (2) is overarching, (1)
may be instrumental to (2). Explicitly wants curiosity as the attention
mechanism, with just enough outcome-pressure to ship. Self-initiated, no
lab, no formal research background — arrived at the frontier problem shape
through reasoning + lit search. Wants to keep it fun, publishable, real.

---
