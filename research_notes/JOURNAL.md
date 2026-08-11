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

### Devil's-advocate pass — the strongest attacks (2026-07-17)

Steelmanned reviewer objections, ranked by how hard they land (for the paper's
own limitations/rebuttal section):

1. **Bitter-lesson-against-us (existential).** Long context + scale keeps eating
   specialized memory architectures (NTM/DNC → forgotten once transformers +
   context got big). Why won't "just scale context / just fine-tune with replay"
   win again? → Rebuttal: unbounded context has cost/persistence/lost-in-middle
   limits AND our claim is specifically the fixed-budget regime; but the honest
   risk is real — must SHOW the advantage grows with scale (RQ2), else this kills
   it. This is the attack to answer first.
2. **Novelty crowding + subtle delta.** PEAM/Auto-Dreamer/EVAF/SCM all 2026;
   "structure-vs-detail" may be too subtle to carry a paper, and may be an
   ARTIFACT of a synthetic sim with a clean graph. → Rebuttal: the measurement
   is the contribution, not just the mechanism; but must show it generalizes
   beyond the toy (ScienceWorld/ALFWorld slice) or it reads as sim-gaming.
3. **Structure may not emerge (R3).** Interference + value-weight might NOT yield
   clean structure-up/detail-down without hard-coding relational bias. → If so,
   RQ1 negative — still publishable as a negative result, but a smaller paper.
4. **Retrieval crux (R1).** Overtrained small net retrieves unreliably; this is
   why parametric memory lost to RAG historically. → Exp 0 first; Larimar backup.
5. **Reinventing test-time training / associative memory with extra steps.** →
   Delta is offline value-weighted consolidation + structure-selectivity +
   standalone structural measurement; must state crisply or it reads as
   ATLAS-with-a-sleep-loop.
6. **"So what" of standalone (no LLM).** Showing a small net keeps some facts may
   read as uninteresting without a task payoff. → Need the usefulness readout to
   be convincing, or the structural-retention finding must be striking on its own.
7. **Value-weighting may not matter.** Ablation could show uniform ≈ value-weighted
   → then the "attention/capital" story collapses to "small net forgets." Must
   pre-register this ablation as make-or-break for the core claim.

Hardest two to answer BEFORE building: #1 (show scale-advantage) and #7 (show
value-weighting matters). If either fails, the framing collapses. Both are cheap
to test early (Exp 2 + Exp 4).

### Dopamine-as-binding + policy-conditioned retrieval (2026-08-09)

Rohin's insight: humans have episodic memory *because* dopaminergic attention
is complex — a dopamine spike doesn't just save the event, it binds the
SEQUENCE leading up to it + co-occurring strong signals into one trace. Also
proposes: attention heads should include POLICY in their K/V search — build
context by retrieving from learned memory AND given context, PLUS a separate
head trained on the dopaminergic/policy system. Wants a deeper LTM↔reasoning
connection.

**Mechanism he re-derived (already in 04_neuroscience):** synaptic tagging &
capture / behavioral tagging (Frey&Morris 1997; Moncada&Viola 2007) — a
salience/dopamine event retroactively stabilizes recent weak traces within a
time window. Episodic memory = salience-gated BINDING of temporal+sensory
context around a valued event. Reframe: episodic memory is the AUTOMATIC
BYPRODUCT of salience-gated binding, NOT a deliberate "decide-what-to-write."

**Split (scope discipline):**
- **B (write-side, KEEP):** value/salience doesn't only weight imprint
  STRENGTH — it defines episode BOUNDARIES / what binds together (the run-up
  sequence + salient co-signals around a value spike). Refines B's writer:
  an "episode" is a value-tagged temporal binding, not a fixed window. Affects
  how we segment episodes in the sim (need salient value events to bind
  around) + connects to retroactive consolidation (reach back when reward
  lands).
- **A (read-side, DEFER):** policy-conditioned retrieval head — queries
  augmented/gated by policy+value embedding so retrieval is GOAL-conditioned,
  not just content-similar; building context from memory+context streams; the
  deeper LTM↔reasoning connection. This is the capital-allocation read fabric
  = Paper A. Pulling it into B breaks the standalone/measurable scope.

**A design note (logged for later):** in transformer terms, the
policy-conditioned head = Q augmented with policy/value embedding (goal-
conditioned retrieval) alongside the content head. Two heads: content-address
+ value-address. This is the concrete A mechanism.

### Scope tightened: Paper 1 = "just KV memory" (2026-08-09)

Rohin's structural realization: value-conditioned RETRIEVAL requires
value-conditioned WRITES — read/write coupled through what's stored. So the
policy-conditioned retrieval head is UNTESTABLE in isolation → definitively
Paper A, not a scoping choice but a structural necessity.

**Paper 1 = the KV memory only:** write + consolidation + structure-vs-detail
retention measurement. Standalone. NO retrieval fabric, NO LTM↔reasoning
coupling, NO policy-conditioned retrieval. Dopaminergic/value machinery can be
done separately (Paper 2).

**One remaining knob — value-weighting in the WRITE:**
- Option 1a: fully uniform/recurrence-only (strict "just KV memory"); value =
  Paper 2.
- Option 1b (RECOMMENDED): keep value-weighting as ONE ablation arm, but paper
  does NOT depend on it. Nearly free (one weighting term); it's the clean
  differentiator vs Auto-Dreamer's uniform compression. Run uniform + value,
  let data pick the headline. De-risks Attack #6 (value-weighting may be inert)
  — either outcome publishable.

**Novelty floor (must hold or it reads incremental):** "small net forgets rare
things" is old. What keeps Paper 1 non-incremental = (1) structure-vs-detail
measurement vs ground truth (the moat) + (2) scaling/bitter-lesson result
(RQ2). Keep BOTH as co-headlines regardless of what value-weighting shows.

### The capacity-constraint answer to "why not long context" (2026-08-09)

Q (Rohin): how is attentioned parametric memory different from sheer context
length? (With enough heads, some head encodes episodes+details anyway.)

**Answer — the difference exists ONLY under a capacity constraint.**
- Context/KV cache: verbatim, unbounded, lossless, O(n) retrieval, blunt/no
  forgetting.
- ATLAS-style parametric memory: compressed into FIXED weights, bounded,
  lossy, O(1) retrieval, graceful capacity-driven forgetting.
- Unbounded-capacity parametric memory = context (it can memorize verbatim,
  no compression, no point). Compression — and everything interesting
  (structure-up/detail-down) — happens ONLY because a fixed net can't keep
  everything and must choose.

**Consequence for the experiment:** the paper's claim is NOT "parametric
memory vs context" in the abstract. It's: at a FIXED memory budget, does
compression-via-consolidation retain more USEFUL (structural) info than
context, which must truncate? The advantage is invisible while everything
fits in context; it appears only when #experiences > budget → **the scaling
curve IS the "different from context" proof.** Differentiation-from-context =
the scaling behavior; they are the same thing.

**Redirect on multi-head intuition:** abstraction is NOT the differentiator
(attention heads over context also abstract). COMPRESSION-under-capacity is.
Don't chase "more heads = richer memory."

**How ATLAS/Titans works (substrate ref):** memory = small MLP whose WEIGHTS
are the memory. Write = gradient step making M(key)≈value, scaled by surprise,
with momentum + weight-decay forgetting. Titans = online (per-token); ATLAS
"Omega rule" = optimize over a WINDOW at once → maps to a batched sleep pass.
Read = forward pass M(query). Forget = decay + finite capacity.

**Recommendation refined:** use ATLAS as substrate (don't reinvent). The
"tweak" that makes it a paper (not a scaling study of ATLAS): (1) run its
window update as an OFFLINE sleep pass; (2) add structure-vs-detail
measurement vs ground-truth graph (the novel apparatus); (3) compare vs
context at matched budget; (4) scaling curves.

### Exp 0 ran — noise-floor gate worked, task too easy (2026-08-10)

Built + ran `experiments/exp0_noise_floor.py` (numpy only, local, seconds).
Adopted the pasted verification-loop discipline: oracle-by-construction, noise
floor, null canary, seeds.

Result: harness VALID (null/canary diagonal ≈0.00±0.04 — eval not biased),
noise floor small (~0.04–0.09). BUT task trivially baked in: structural facts
recur by construction, so even TRUNCATION (dumb context baseline) scores 0.80
diagonal; frequency 0.98 with ZERO variance. "A diagonal exists" is NOT a
result — the cheap baseline gets it.

→ The gate did its job: caught a too-easy task in 10s before building ATLAS.
Real bar = a regime where truncation/frequency FAIL and only value/structure-
aware memory wins. Task v2 (in exp0_results.md): (1) recurring-but-useless
details (frequency wrongly keeps), (2) rare-but-critical structure (frequency
wrongly drops), (3) downstream structural-query readout not set-membership.
This ALSO resolves the value-weighting oscillation empirically: if value beats
frequency in v2 it's core; if not, the capital thesis is in trouble — learned
cheaply either way.

Verification-loop components still to add (from pasted advice): two-tier eval
(cheap proxy inner loop + expensive survivors), diversity archive (niche-best
not single champion), reasoning-at-proposal-stage. Defer until task v2
discriminates.

### Exp 1 ran — value-weighting is CORE (2026-08-10)

Built discriminating task (rare-critical structure SR + recurring-useless
distractors DR + noisy runtime value signal; label used only for scoring).
`experiments/exp1_value_vs_frequency.py`, report in
`experiments/REPORT_exp0_exp1.md`.

Result: frequency & truncation both provably fail (freq keeps 100% distractors,
drops 57% of rare structure; trunc drops 99% of rare structure). value(MAX
one-shot imprint), using only the noisy signal, gets 1.000 structural retention
incl. rare, drops distractors (dr_kept 0.415), +0.282 readout over frequency
(~6× noise floor). Degrades gracefully; breaking point ~p_hit 0.4.

**value_sum ablation is the key defense:** accumulative value underperforms
MAX (struct_rare 0.675 vs 1.000; dr_kept 0.825 vs 0.415) → the ONE-SHOT MAX
imprint is load-bearing, refuting "value = frequency in disguise." Canary clean,
noise floor ~0.048.

→ **Resolves the value-weighting oscillation: CORE, not cosmetic** — but only as
a NECESSARY-condition test on an idealized set-retention model. NOT yet proven
for a real (lossy) parametric memory. Next: port to ATLAS-style fast-weight MLP
(value-scaled gradient imprint + forward-pass probe), same discipline, check the
+0.28 gain survives interference.

### Exp 1 CORRECTED — earlier headline RETRACTED (2026-08-10)

External adversarial CODE review (not prose) refuted Exp 1. Confirmed defects:
binary HIGH/LOW made the sweep closed-form (degenerate oracle at p_hit=1.0);
canary couldn't fail; dr_kept was budget-fill; significance test invalid.
`exp1_corrected.py` + `REPORT_exp1_corrected.md` fix all five.

Corrected findings (continuous overlapping value ~N(d',1), budget-free AP,
paired tests, 30 seeds):
- **"value-weighting is CORE (+0.282)" is RETRACTED** — it was a binary-magnitude
  artifact.
- **Canary (d'=0) now does real work:** value_mean → 0.024 (exact chance,
  frequency-neutral ✓) but value_max=0.204 & value_sum=0.137 sit ABOVE chance
  with ZERO type signal → **frequency-contaminated** = the "value is frequency in
  disguise" attack, now MEASURED. My "max is load-bearing" claim was partly that.
- **No aggregation robustly beats frequency under moderate overlap (d'=1.5):**
  value_max +0.220 AP but flips with budget & is contaminated; value_mean (only
  clean aggregation) is WORSE than frequency (0.176 vs 0.438) — rare facts have
  noisy means. Clean win only at d'≈3 (ceiling).
- Net: a value signal helps ONLY if high-discriminability (d'≈3) AND
  frequency-decorrelated. Hand-set signals don't clear it. NEGATIVE-leaning
  necessary-condition result — quantifies the bar.

**→ This MOTIVATES Rohin's trained-value-function proposal.** Path: (1) synthetic
data with known outcomes; (2) TRAIN value model on outcomes, MEASURE its d' +
frequency-correlation — does it clear the bar? (3) only then: weight consolidation
into real ATLAS memory, compare vs ATLAS/frequency/RAG/LoRA baselines.

**Method lesson enforced:** critic = separate adversarial pass over CODE +
per-seed numbers, prompted to refute. Narrative self-review grades the prose (the
strongest part) and misses the sharpest attack. This is the failure mode a long
autonomous loop mass-produces.

### Exp 2 — trained value function clears the bar (qualified) (2026-08-10)

`exp2_trained_value.py` + `REPORT_exp2.md`. Tests Rohin's proposal: value
weighting must be TRAINED on outcomes. CPU logistic regression, no GPU/ATLAS/LLM.

Design fixes vs a first flawed v1: frequency made UNINFORMATIVE by construction
(all facts marginal 0.4 → freq dP≈0, verified); value model never sees the label,
only (presence, outcome); collinear confounded details (sweepable strength).

Results: trained value recovers causal structure — dP=7.84 on confounded case,
AP=1.000, freq-decorrelated (−0.01); frequency useless (dP≈0). **Training is
NECESSARY:** confound sweep shows naive co-occurrence credit collapses at strong
collinearity (a=0.9: naive dP=1.08 vs trained 5.23) — joint fit disentangles what
marginal counting can't. Honest limit: near-perfect collinearity (a=0.99) defeats
even training (dP=1.31).

**Key caveat (flagged, not hidden):** MATCHED MODEL CLASS — data generated by
linear-logistic, fit by logistic regression, so "trained works" is partly the
estimator fitting its own form. Next: **exp2.5 = nonlinear causal structure +
mismatched learner** before committing GPU.

Gate verdict: **QUALIFIED GREEN LIGHT.** Pipeline if exp2.5 survives: train value
on outcomes → weight consolidation into ATLAS memory → compare vs
ATLAS/frequency/RAG/LoRA.

Conclusion reached with Rohin: **ATLAS's fast-weight KV memory alone is NOT
enough — it needs a trained value-weighting layer on top to decide what to
consolidate.** That trained layer is the paper's core mechanism.

**CORRECTION (2026-08-10, Rohin caught this):** the above is an OVERCLAIM. exp0/1/2
never ran ATLAS or any parametric KV-MLP memory — they are abstract set-retention
+ logistic-regression simulations. They establish only a NECESSARY-CONDITION
argument about the value SIGNAL (frequency/co-occurrence insufficient;
trained-on-outcomes signal can recover causal structure). They do NOT prove
ATLAS-alone fails — that requires actually running ATLAS. Restated honestly:
*"IF we weight consolidation, THEN the weight must be a trained value signal, not
frequency/surprise."* Whether ATLAS+value beats ATLAS-alone is an UNTESTED
hypothesis, to be settled by running both. Note ATLAS weights writes by SURPRISE
(gradient magnitude), not frequency or outcome-value — so the differentiation
(surprise vs learned value) is real but must be shown empirically on ATLAS.

### Exp 2.5 — mismatch test exposes a DEEPER issue: value may need to be RELATIONAL (2026-08-10)

`exp2_5_mismatch.py`. Nonlinear (conjunctive) outcome: success = ANY structural
PAIR both present. Fit with mismatched linear logreg AND a nonlinear MLP; per-fact
value via occlusion attribution.

Result: under nonlinear structure the trained per-fact value signal DROPS HARD —
dP(vs confounded) ≈ 1.8 (both learners) vs 7.84 in matched Exp 2. AP still 0.88
(usable, not collapsed). The MLP did NOT beat logreg (1.72 vs 1.80) — so it's not
just "use a bigger model."

**Two honest findings:**
1. Exp 2's strong numbers were substantially INFLATED by matched model class +
   additive-per-item outcome. Realistic (nonlinear) structure weakens per-item
   trained value a lot. Green light downgraded from "qualified" to "conditional."
2. DEEPER: when value lives in RELATIONSHIPS (pairs/dependencies), a SCALAR
   PER-ITEM value is fundamentally lossy — no single fact is valuable alone, so
   per-item attribution is weak. This is the whole project's thesis biting back:
   structure IS relational (cup→coaster), so the consolidation weighting may need
   to be RELATIONAL (value of a relation/key-pair), not per-item. Hypothesis
   raised by exp2.5, not proven — but it redirects the design: the value signal
   and the memory keys may need to encode relations, not items.

→ Next design question BEFORE ATLAS: should consolidation value be per-item or
per-relation? exp2.5 suggests per-relation. This is cheap to test in the abstract
(make value a function of pairs, attribute to pairs) before any GPU.

### Prior-art check: the intersection is OPEN (2026-08-10)

`research_notes/12_atlas_baselines_learned_write.md`. Three verdicts:
1. **ATLAS baselines = sequence-model architectures ONLY, no RAG/memory systems.**
   Defends "parametric test-time memory > attention/linear-recurrent at long
   context" (BABILong +80% @10M tokens). RAG only in Titans as a beaten strawman.
2. **Learned-value WRITE into parametric memory = OPEN.** Nearest: GradMem (learns
   parametric write, NO value head, self-supervised) + Auto-Dreamer (outcome-
   trained consolidation but into EXTERNAL TEXT BANK, not parametric weights). We
   sit in their unoccupied intersection. **Auto-Dreamer = the differentiate-from
   paper**; our delta = outcome-trained value writing into PARAMETRIC fast-weights.
   Caveat: fast-moving, moderate confidence, final sweep before submission.
3. **Cross-episode? NO** — Titans/ATLAS only long-context within a single sequence,
   memory resets per sequence. Cross-episode consolidation = clean separate
   novelty axis (confirms the long-context ≠ LTM nuance).

Positioning crystallized: novelty = [outcome-trained value head] weighting
[parametric fast-weight] writes in a [cross-episode consolidation] regime. All
three axes needed; each alone is taken.

### Exp 3 — relational value recovers what per-item lost (2026-08-10)

`exp3_relational_value.py`. Same conjunctive generator as exp2.5. Value learned on
PAIRS vs per-item value lifted to pairs.
Result: relational dP=7.08, AP=1.000 (perfect); item_lifted dP=2.84, AP=0.442.
→ Confirms: when structure is relational, the value head must predict PER-RELATION,
not per-item. exp2.5's collapse fixed by matching representation to structure.

**Caveat (pre-empting overclaim):** AP=1.0 is partly matched-representation — I
handed the model the pair features matched to the generative structure. Real
consequence: (1) conceptually right but the perfect number is an artifact;
(2) enumerating relations DOESN'T SCALE (40 facts→780 pairs, worse for triples).
→ The scalable version can't enumerate — it must LEARN relational keys. That's
exactly what an ATLAS-style MLP memory does (distributed relational reps, not
explicit pair tables). So exp3 motivates WHY a learned parametric memory beats an
explicit relational store: learned keys discover relations you can't enumerate.

Design decision settled: the value head predicts relational value; the memory must
form learned relational keys (not per-item, not enumerated pairs). This is a
concrete spec for the ATLAS-integration stage.

### CPU-experiment arc summary (exp0–exp3)
0: killed a trivial task (noise-floor gate).
1: retracted a false "value is core" positive under adversarial code review.
2: trained value clears the bar (qualified) — but matched model class.
2.5: mismatch → per-item value collapses; value is RELATIONAL.
3: relational value recovers structure — but must be LEARNED, not enumerated.
Next (still CPU): could test learned relational keys (small attention/MLP) OR move
to ATLAS integration. All prior-art axes confirmed open (note 12).

### Refinement: ATLAS and "long-term memory" (Rohin, 2026-08-10)

Rohin's push-back on the "long-context ≠ LTM" framing (accepted as a refinement):
it's partly bitter lesson — ATLAS DOES prove the fast-weight MLP substrate *works*
(can compress + recall a lot). What it lacks isn't a different architecture, it's
**another layer of representation — a VALUE layer smarter than surprise** — so it
stores more intelligently, plus recompilation/reconsolidation (ideally driven by
CHANGED value functions, later). So the honest statement is NOT "ATLAS is
irrelevant to LTM" but: **ATLAS proves the substrate; it is not yet LTM-READY; the
value-representation layer is what closes the gap.**
Claude's one caveat to keep: the value layer is necessary but maybe not sufficient
— cross-episode consolidation (sleep, forgetting, reconsolidation across separate
episodes) is a training-REGIME ATLAS never ran, not only a representation gap. So:
substrate = proven; value layer + cross-episode regime = the two things to add.

### Architecture: value head SHAPES K/V (not surprise post-weighting) (2026-08-10)

Rohin's cleaner proposal: don't bolt value onto write-STRENGTH (surprise-style
post-KV weighting). Instead add a NEW ATTENTION HEAD trained on a policy/value
loss; that head produces a value-aware K/V representation, and then a NORMAL KV-MLP
write naturally prioritizes by value. Remove surprise entirely. The same head
weighs both memory (write) and attention (read) — the shared policy head. Also:
benchmark vs RAG + other memory systems (the gap ATLAS left).

Claude's key connection: **attention is inherently RELATIONAL** (QKᵀ is pairwise),
so an attention head is the RIGHT tool for the relational value exp3 showed is
required. "Add an attention head" (Rohin) + "value must be relational" (exp3) fit
together — the head can learn relational value without enumerating pairs (fixes
exp3's non-scaling caveat).

Two honest tensions to design around (not blockers):
1. K/V must serve BOTH content-retrieval AND value-prioritization. Shaping K/V for
   value could hurt content-addressing. Likely fix: value as an added
   channel/dimension alongside content, not replacing it.
2. Removing surprise also removes ATLAS's FORGETTING mechanism (surprise gates
   write strength = capacity control). Need a replacement: decay, or value-driven
   forgetting.

This is testable cheaply next: can a small attention head LEARN relational value
from outcomes (frozen backbone)? = the scalable version of exp3.

### COMPETITIVE VERDICT after 6 deep-reads (2026-08-10) — see note 18

Parametric memory is red-hot (6+ papers May–Aug 2026). EVERY axis of the original
idea is occupied: parametric fast-weights (Titans/ATLAS/TMEM/EVAF), value-gated
writes (D-MEM/TMEM), offline cross-episode consolidation (COVE), what-to-internalize
+ anti-recitation forgetting (COVE), CLS framing (User-as-Engram), embodied
parametric skills (PEAM). Nearest: D-MEM (dopamine-gated writes, ~90% of value-gate
axis), COVE (offline cross-episode what-to-internalize — HIGH but per-item &
surface-form), TMEM (RL LoRA writes but online within-episode — cousin).

**Surviving novelty collapsed to ~one axis: RELATIONAL value + relational-vs-episodic
forgetting** (exp3's angle — unseen anywhere; everyone else is per-item + surface-form).

**Honest position:** independent researcher as 7th method paper at this exact
intersection, racing funded labs, is structurally weak. RECOMMENDATION: PIVOT to
BENCHMARK-LED — build the structure-vs-detail ground-truth benchmark (half-built:
the crafting sim), evaluate the CROWD on relational-structure retention, show they
miss it, relational-value consolidation fills it. A benchmark gains value as the
field grows (scoop-immune) and is the natural home for our one real novelty. Method
becomes the benchmark's headline result, not a standalone claim vs D-MEM/TMEM/COVE.

Decision pending Rohin. Alternatives: pure benchmark paper; pivot to a less-crowded
cognitive-stack cell; or race the narrow relational lane.

### Post-verdict reflection + the "AI research being" vision (2026-08-10)

Rohin processed the competitive verdict maturely (not discouraged — "learned a lot,
feel happy, cool this exists"). Floated a big pivot: an "AI research AI being" /
self-iterating research harness that composes all the continual-learning systems,
produces research, gets judged, learns, and rebuilds parts of itself → "AI research
exponential." Bet: position ~6 months ahead of the field.

Claude's honest counterweight (recorded so we don't relitigate):
- **"Continual learning is ~solved" = FALSE.** Many papers = active OPEN problem,
  not solved. Each = narrow slice, favorable conditions, known limits, NO shared
  benchmark, no consensus, no winning method. Catastrophic forgetting, robust
  cross-episode consolidation, consolidation-collapse-over-time all still open.
- **"Compose them into a live assistant" is a RESEARCH problem, not a compute one.**
  Composition breaks (conflicting assumptions, uncharacterized failure modes);
  long-horizon robustness/drift unsolved; general reward signal unsolved; stable
  self-improvement (rebuild-without-degrading) is the least-solved of all.
- **The self-iterating AI-research-being = recursive-self-improvement/AGI frontier**
  — a north star, NOT a tractable independent project. Gap from "LoRA that helps QA"
  to "self-rebuilding researcher" ≈ most of AGI. Resource-bound, not foresight-bound.
- **Tractable slice that IS real:** the human-in-the-loop research-assist harness we
  ran THIS session (agents search + experiment + adversarially critique + correct).
  Improving research-automation TOOLING is a genuine independent contribution now.

Decision framing (Rohin's two currencies): (1) elite research env → finished real
artifact (benchmark) beats unfinished moonshot; (2) help the field → benchmark helps
now, AGI-being helps nobody until it works & labs get there first. Both point to:
SHIP the tractable thing (benchmark or research-tooling), keep AGI vision as the
taste-generating north star.

Open decision for Rohin: benchmark paper vs research-tooling contribution vs a
less-crowded cognitive-stack cell. Awaiting his call on what OUTCOME he's optimizing.

### Benchmark built + adversarially hardened overnight (2026-08-10/11)

Decision: benchmark-led (StructMem-Bench) to get into a lab; vision = north star.
Built M1 (spec), M2 (full CPU package: config/tasks/memory/metrics/stats/harness +
17 tests + runner), M3 scaffold (llm_tier.py, GPU-ready, CPU-testable plumbing).

Red-teamed with 3 adversarial subagents (2 died on API errors; rest + self-review
sufficient). CRITICAL bug found 3× independently: contiguous type layout +
stable-sort tie-break → zero-info index-ranker scored AP=1.0, faked "surprise
recovers rare structure" (0.53→0.02 after fix). Canaries couldn't catch it. Fixed:
seeded column-permutation (index⊥type) + tie-safe ranking + constant-scorer canary
+ regression tests. See research_notes/redteam_response.md + redteam_1/redteam_3.

**Honest corrected finding:** relational value beats per-item SIGNIFICANTLY only in
the concentrated-dependency + adequate-data regime (+0.18–0.21, t≈3.6–3.9), NOT
data-starved/diffuse or single-pair. exp3's "AP=1.0" was a favorable-setup artifact
(same species as exp2 matched-model-class). Hardening deflated it to a real but
regime-specific effect.

**Posture shift:** the BENCHMARK (rigorous, honest, adversarially-hardened
instrument) is the solid contribution; the relational METHOD claim is real but
narrow. This is exactly what a good benchmark does to its own method. Ship = the
benchmark; the method is its headline result where it honestly holds.

Status: M1+M2 done + hardened (CPU, 17/17 tests, pushed). M3 (LLM tier) needs GPU.
Artifact is lab-outreach-ready. NEXT (Rohin's call): M3 on GPU + workshop write-up;
outreach to paper authors with the benchmark as the hook.

### External audit + fixes (2026-08-11)

An external auditor (ran the code, turned objections into probes) confirmed the
rigor layer is real and found 6 things. All implemented + regression-tested:
- **value_z = vsum/√count** (the sufficient statistic) DOES beat frequency
  (+0.46, t=41) and passes the d'=0 canary → exp1-corrected's "no aggregation
  beats frequency / negative-leaning" was itself an OVERCORRECTION (tested only
  max/mean/sum). Third flip: exp1(yes)→corrected(no)→audit(yes-with-z). Weakens
  the "value must be trained" motivation. Relational-pair finding unaffected.
- linear-outcome base rate was degenerate (2.1%, analytic offset assumed rare SR
  shared marginal p) → empirical centering, base ~0.5. Now tested.
- DR-partner invariant could silently break "frequency uninformative" when
  n_detail_recurring > n_struct_frequent → config assert + partner DR with SF only
  + sweep test.
- item_lifted was a signed product (anti-predictive pair scored high) → relu-
  product; relational wins by MORE against the corrected baseline.
- the relational sweep confounded episodes×recipes; the "grows as concentrate"
  claim was wrong → fixed-episode sweep shows an INVERTED-U peaking at 3-4 recipes.
- exp2 green light RETRACTED (trained_value ties frequency n.s. on the benchmark).
- Hygiene: archived orphaned dream_state/scripts/configs; dead knob removed;
  README 14→23 tests; .gitignore. 23/23 tests pass.

Meta-lesson reinforced: the MACHINERY was sound every time; the CLAIMS overshot,
and a separate adversarial pass (auditor writing assertions, not opinions) is what
catches it. Same pattern as exp1. The benchmark is now genuinely hardened.

### Benchmark prior-art RE-CHECK (2026-08-11, note 19) — Rohin's probe was right

Rohin probed: scale-beyond-context, robust LTM-recall definition (forgetting
curves, LTM-vs-STM, graded importance), and "if trivial it'd exist — go check."
Re-check verdict: **benchmark space also filled in during July 2026.**

Corrections to our claims:
- 2604.15877 "Missing Diagonal" is a SYSTEMS gap, not a benchmark gap — stop
  citing it for our gap claim.
- **ForgetBench** (2607.26455, Jul 2026): forgetting curves + disentangles factual
  vs relational retention — but PARAMETRIC-ONLY (knowledge editing).
- **RECON** (2607.16716): provenance DAG w/ typed edges — has the graph, scores
  holistically (no structural/detail split).
- **MemTrace** (2606.17328): retention-vs-age across 4 EXTERNAL paradigms.
- **Name collision:** StructMemEval (2602.11243, Yandex) exists → RENAME ours.

Six-axis verdict: forgetting-curves LARGELY COVERED; LTM/STM PARTIAL (EvoMemBench);
**graded-importance OPEN**; relational/KG LARGELY COVERED (RECON); **cross-memory-
type single-probe interface OPEN (strongest — every harness excludes parametric/
LoRA; parametric benchmarks are parametric-only; NOBODY bridges)**; enforced
budget+horizon PARTIAL (BEAM reports, doesn't enforce).

**Repositioning:** virgin-gap framing is unsafe. New pitch = **"first memory-type-
agnostic retention benchmark"** — one probe interface spanning RAG + parametric/
LoRA + text banks (axis 5), importance-stratified retention (axis 3), and the
CONJUNCTION: structural/detail split from one dependency graph + enforced budget +
age curves across all memory types (each fragment exists somewhere; the unification
doesn't). Cite ForgetBench/RECON/MemTrace/GroundTruthFirst as fragments to unify.
Adopt: Ground-Truth-First's script-before-text generation; MemTrace's knowledge-
point probes. RENAME pending Rohin.

### Human-memory paradigms check (2026-08-11, note 20) — Rohin's framing upgrade VALIDATED

Rohin proposed running the benchmark parallel to real human memory evals. Verdict:
**the combination is OPEN, narrowly, and closing.**

Already ported (cite as anchors, not novel): serial position (saturated — lost-in-
the-middle = primacy/recency, 2406.15981); interference (well ported; KEY FINDING:
LLMs show proactive-interference dominance — the OPPOSITE of humans, 2603.00270 —
great motivator); forgetting curves (piecemeal: 2410.04727 long-context, ForgetBench
parametric); recall-vs-recognition (SORT 2410.08133 = cleanest port template); DRM
false memory (one-off battery: 2509.17138).

**UNPORTED as evaluation: gist-vs-verbatim / fuzzy-trace theory** — OUR structure-
vs-detail axis, with 30 yrs of human data, used only as architecture inspiration
(ReadAgent), never measured as paired probes. Also unported: spacing/testing
effects. Both align naturally with wake-sleep consolidation.

No general-purpose psychology-grounded agent-memory benchmark exists. Near-misses:
**eMEM-Bench v1** (2606.03374, Jun 2026 — 8 cog-psych paradigms but EMBODIED-ONLY +
coupled to their system) and EvolMem (taxonomy, not paradigms). CogBench (ICML'24)
proves the "psychology lab for LLMs" pitch lands at top venues — zero memory
paradigms in it.

**ASSEMBLED FINAL FRAMING (three confirmed-open legs):**
"The first psychology-grounded, memory-type-agnostic benchmark for agent memory"
1. Gist/verbatim probes (= our structure/detail, FTT pedigree, UNPORTED)
2. Cross-memory-type single probe interface (RAG+parametric+banks — nobody bridges)
3. Importance-stratified retention (open) + enforced budget (BEAM reports, doesn't
   enforce)
Anchor probes from ported paradigms (serial position, interference, curves) cited
generously. Differentiate vs eMEM-Bench: general text-agent vs embodied-only,
backend-agnostic vs system-coupled. Motivators: PI-dominance-opposite-of-humans,
MemDelta (evals confounded), tenure-crossover (rankings invert with time).

URGENCY: eMEM-Bench (June) proves the framing is in the air — someone will
generalize it. Move fast. Name decision pending (Rohin: "decide once we learn the
project").

### DIRECTION SET: the head IS the project; benchmark = its structure (2026-08-11)

Rohin's call: build the RL/policy/dopamine-trained attention head as the project he
cares about, with the benchmark as its evaluation structure. Believes it's the best
novel package + perfect timing ("front lines = right timing if done right"). NVIDIA
summer compute possibly available.

**Rohin's methodological correction (important, adopted):** the benchmark does NOT
generate the training signal — that would be teaching-to-the-test/leakage AND
circular (the claim is that OUTCOME-trained value DISCOVERS structure; training on
structure probes hardcodes it). Outcome reward trains the head; benchmark = the
held-out exam. Design the benchmark WITH the head in mind, keep the firewall.

### Exp 4 — end-to-end miniature PASSES (2026-08-11)

`experiments/exp4_end_to_end.py` + REPORT_exp4.md. First PHYSICAL memory (linear
associative, real superposition interference, normalized write budgets = pure
allocation comparison). Train/eval firewall enforced.
1. **Bitter-lesson curve real on the data axis:** trained−uniform advantage grows
   monotonically with horizon at fixed capacity (+0.099, t=7.8 at 800 eps). THE curve.
2. **My capacity hypothesis FALSIFIED:** advantage does NOT grow as d→0 (interference
   swamps everyone; even oracle 0.44 at d=16). Allocation needs d big enough to
   express selection; helpful scarcity = data≫capacity.
3. **Relational standout:** outcome-trained pair-weights in a binding memory: +0.468
   (t=9.3) over co-occurrence; oracle 1.0. Relational thesis survives physics.
4. **Architectural finding:** per-EVENT salience tags (value_z) ≫ post-hoc per-item
   credit (0.63 vs 0.25) → the head should emit TD-like per-event tags + trained
   relational credit; not per-item regression.
5. Canary clean at d'=0.
CPU-tier green light for the GPU tier.

### Compute precedents (note 21, 2026-08-11) + a novelty-relevant discrepancy

Three-tier estimate (precedent-grounded): (a) CPU tier done, $0; (b) minimum
credible LLM tier (1.5-4B frozen, one env, 5-20k eps, 3 seeds) ≈ **50-150 GPU-h ≈
$100-400**; (c) workshop-grade (frozen 7B, ~5 conditions, 3 seeds + baselines +
benchmark sweep) ≈ **500-1,000 H100-h ≈ one 8×H100 node 3-5 days ≈ $1.3-2.6k spot.**
NVIDIA-summer feasible. Field's trained-memory runs are TINY (152-3,604 training
items, 100-205 GRPO steps; Mem-α's 2,300 H100-h is the ceiling). Folklore anchor:
~5-20 H100-h per 1k rollouts (7B). Biggest cost risk = episode/context length —
and the parametric memory keeping wake-context short is ITSELF the cost control.

**DISCREPANCY TO RESOLVE (novelty-relevant):** note 14 said D-MEM's critic router is
"trained via RPE"; note 21's deep-read says D-MEM is **training-free** (heuristic
surprise z-score × prompted utility, $0 training). Same for MemRL (runtime Q-EMA, no
gradients). If note 21 is right, the "TRAINED dopamine gate" axis is MORE open than
we believed — the closest 'trained gate' works are actually heuristics, and our
learned head has no direct trained competitor on the gate axis. MUST verify by
reading D-MEM's paper directly before any claim. Also: D-MEM + MemRL become
mandatory $0-training baselines for our head ("does learning beat the heuristic
gate" is THE ablation).

Recommendation adopted: do NOT reproduce a full-model GRPO baseline (200-600 H100-h
line item) — cite instead.

### D-MEM discrepancy RESOLVED by direct read (2026-08-11) + project name

**D-MEM (2603.14597) is TRAINING-FREE. Note 21 was right; note 14's "trained via
RPE" was WRONG — correct it wherever cited.** Direct read of the method section:
- Surprise = embedding-cosine z-score through a sigmoid (no training).
- Utility = a constrained zero-shot LLM call (JSON schema, lifecycle classes).
- "RPE" = heuristic formula: RPE(x) = min(1, 1[Utility≥τ]·[Utility×(Surprise+β)]).
  NOT a learned value function. No gradients anywhere. GPT-4o-mini API backbone.
- Routes into EXTERNAL buffers + knowledge graph (not weights).

**Consequences:**
1. The "TRAINED dopamine gate" axis is MORE OPEN than believed — D-MEM took the
   dopaminergic FRAMING but shipped a heuristic. Nearest trained neighbors remain
   TMEM (RL extraction, no head, text→LoRA), Mem-α (RL tool-call ops, fine-tuned
   backbone), Auto-Dreamer (GRPO, text bank). A trained attention/value head gating
   PARAMETRIC writes still has no direct competitor.
2. D-MEM = the perfect $0-training heuristic baseline. THE ablation of Paper 2:
   "does a learned gate beat the heuristic dopamine gate."
3. Lesson: agent summaries of papers can disagree — resolve novelty-critical facts
   by direct read. (Note 14's error survived two syntheses before being caught.)

**PROJECT NAME (tentative, Rohin): "Felt Attention"** — attention that carries
valence/feeling; the value-weighted allocation thesis in two words. Benchmark name
TBD (must not collide with StructMemEval; check "FeltMem"/similar before use).

### FELT ATTENTION — architecture of record (2026-08-11, Rohin's scoping)

Scoping principle (Rohin): the part that doesn't exist must be as simple/legible/
architectural as possible; leverage everything that does.

Rohin's "progress-toward-outcome RL" = the VALUE FUNCTION (TD/λ-returns/AlphaGo),
potential-based reward shaping (Ng 1999: r' = γV(s')−V(s)), and in LLM-land Process
Reward Models. All mature — adopt, don't invent. For text envs the LLM IS the
action model (ReAct).

**Three-stage architecture:**
1. Value net V(s) trained SEPARATELY on task outcomes (mature recipes).
2. ONE attention head grafted on the FROZEN LLM, trained on VALUE loss (other
   heads: token loss; this head: policy loss). ← the only new trainable object,
   THE paper.
3. Head's weights feed three consumers: (a) context/KV selection, (b) LTM
   fast-weight writes, (c) LoRA consolidation weighting. All exist; wiring only.

Head's training loss (v1 decision): DISTILLATION — head predicts the value net's
per-event salience (TD-error/advantage). Supervised, stable; RL difficulty stays
quarantined in stage 1. Matches exp4 finding (per-event tags ≫ post-hoc credit;
TD-error IS the per-event tag). End-to-end REINFORCE = v2/ablation.
Staging: write-side consumers first (LTM+LoRA, offline, benchmark-measurable),
read-side second (read/write coupling, keep results attributable).

Novelty posture: value functions solved for games; UNCLAIMED = one value-trained
head allocating context+memory+training simultaneously on a frozen LLM (note 14:
closest = attention-as-RL-policy; D-MEM verified heuristic). Ablation spine: learned
head vs D-MEM-style heuristic gate vs surprise vs uniform, on the benchmark.
Hard parts (Rohin, correct): value-net quality for the env (exp2 d' bar) + legible
per-consumer attribution (= the benchmark's job).

### DECISION: ICLR 2027 (2026-08-11)

Target: ICLR 2027 benchmark paper — abstract Sep 18, full Sep 25. Solo + agents.
Skip waiting for ICML (field too fast). arXiv preprint ASAP after submission =
the lab-entry signal, dated BEFORE NeurIPS 2026 (Dec) in case overlapping work
drops there. PALM (Aug 24) optional 4-pager if time allows; non-archival so it
doesn't burn ICLR.

Critical path (6.5 weeks):
- Wk1 (Aug 11-17): benchmark v2 CPU — paradigm ports (gist/verbatim paired probes,
  age-stratified forgetting curves, importance strata). ← STARTED
- Wk2 (Aug 18-24): LLM tier — real backends (RAG/text-bank/parametric), first GPU
  session. BLOCKER: Rohin's compute confirmation needed THIS WEEK.
- Wk3-4 (Aug 25-Sep 7): full runs (≥2 backbones, ≥3 orderings, budget sweeps).
- Wk5 (Sep 8-18): write; abstract in.
- Wk6 (→Sep 25): polish; full in. Then arXiv + outreach to mapped authors.

### Second external audit processed (2026-08-11, note 23) — all fixes in, 27/27

Audit part 1 (code): gist/verbatim probe was EXPOSURE-CONFOUNDED (verbatim drew from
all detail incl. one-shots; frequency faked 0.21 dissociation) → verbatim now DR-only
(marginal-matched) + permanent frequency-dissociation≈0 canary. C1 wording corrected
(beats UNIFORM, not "untrained" — value_z beats trained_item everywhere).
Forgetting-curve age↔type confound → SF-only curve + SR labelled point. Counts fixed.

Audit part 2 (prior art): our lit notes verified NOT hallucinated (6 IDs spot-checked,
all real+accurate). **KVP (2602.10238, Apple, ICML 2026)** = policy-trained per-head
RL eviction on frozen LLM under budget → the CONTEXT consumer is OCCUPIED. Surviving:
(1) objective distinction — decoding-utility vs distance-to-OUTCOME ("KVP learns what
the model will want; we learn what the task will need"); (2) tri-consumer unification
(one head/value → context+LTM+consolidation) — NOBODY crosses it. TRIM-KV weakens
"importance-stratified unclaimed" (cite it); PM-Bench = paradigm-porting precedent
(compound survives). AgeMem revised Jul 2026 (one GRPO policy over LTM+STM — re-read).

Decisions: v1 = HEAD-AS-SCORER (modulator = v2, Flamingo gating) — spec updated;
KVP-ablation adopted as the novelty-isolating experiment (swap reward, hold harness);
final re-sweep scheduled ~Sep 20 (NeurIPS ~Sep 29 arXiv dump); "self-determinance"
framing stays out of reviewer-facing text (roadmap language only).

Rohin's staged plan CONFIRMED against the map: frozen policy → prove STM/LTM/thinking
can be conditioned on it → unfreeze later. The unification is the claim.

### Compute CONFIRMED + regime-design scoping (2026-08-11/12)

**Quota facts (Rohin, from Colossus docs):** rolling 30-day quota = 1440 lease-hours
(1 unit = 1 hr), i.e. ~60 lease-days/month, self-service; over-quota blocks new
leases/extensions. Default lease 48h (--duration overridable, min guaranteed 1h).
Only `general` pool is open to all colossus-users; 8×A100/H100/H200 nodes EXIST but
in private pools (nim-factory-dev, vrdc-dev, swdl-fw-infra...) — authorization
required. Numeric concurrent-lease cap + max-duration are policy-driven per
pool/role, not published.

**Translation:** our jobs (small-model rollouts + ~1M-param head) don't need
multi-GPU interconnect → single-A100 general-pool nodes are the right shape.
Min-credible tier (50-150 GPU-h) ≈ 1-2 weeks of quota; workshop-grade (500-1000
GPU-h) fits in 1-2 months rolling, fully self-service. Multi-GPU pools = optional
accelerator via mentor. **Compute is NOT a blocker.** Remaining human blocker:
publication/IP question to manager (CoI KB0025363 + NXP arXiv page).

**Regime-design scoping (Rohin):** the paper's target regime = the WINDOW where
baseline context has aged out, surprise-memory kept novel-but-useless over
boring-but-vital sequence info, and policy-attention kept just enough outcome-
relevant sequence to win. Mechanism (ii) [modest: right info survives] is the
target; mechanism (i) [emergent episodic replay at absurd scale] = try-and-report,
paper doesn't bank on it. The regime is SEARCHABLE ON CPU first: sweep chain depth
(craft hierarchies), distractor rate, horizon-vs-budget ratio in the abstract tier;
set the LLM-tier game at the widest differentiation window. exp4 shape: advantage
grows with horizon at fixed capacity → deep hierarchies + long horizons + tight
budgets is where to hunt.

**Oracle clarified for Rohin:** (1) oracle baseline = ceiling marker + metric sanity
(nothing may beat it); (2) oracle VALUE = exact BFS graph-distance on our DAG —
zero-cost perfect value signal for Stage 1, giving clean fault isolation
(mechanism-vs-signal) before training any value net.

### Overnight hardening pass (2026-08-12) — exp6 RETRACTED, LLM half built, ledger honestly green

Red-team round 2 (redteam_4/5/6; agent 5 pending at write time). redteam_4 killed
the exp6 headline: the felt effect was a hardcoded fallback constant + type≡action
label-leak equivalence + cosine-floor confound + salted-hash irreproducibility.
ALL fixed with canaries (keyword_gate policy, floor-corrected probes, determinism
test, detour rollouts creating within-type salience variance). redteam_6 caught
the dishonest GREEN ledger (LLM half had zero code, 0/5 gates runnable) → built
felt/llm_player.py (MockTextPlayer text-driven planner, HFBackend w/ multi-layer
state extraction, manual/memory injection) + felt/gates.py; engine move-anywhere
fix (knowledge must be actionable). Gates: mock 1.0/0.0. SIZING corrected (3B
likely, decode volume, multi-layer cache); spec §5b amendments (run-1 gate =
head-regret-on-real-states ≤3× mock; goal-agnostic head recorded; LoRA = run-2).

HONEST STATE: realistic policies ≈ 0 on corrected metric; oracle ceiling
+0.11/+0.22 @ h≥128; head-works question = GPU tier with an hour-12 kill-switch.
Better pre-lease position than the fake positive: we know the signal, the test,
and the cost. 47 tests green. DEEPDIVE_GUIDE finalized w/ lease spec (general
pool, 1× A100-80GB, 48h, one lease).

Meta: this is the 4th time adversarial code-review reversed a headline (exp1,
exp2 green light, gist/verbatim confound, exp6). The pattern is now structural:
NO result is real until a code-level adversary fails to kill it.

### redteam_5 landed late + processed (2026-08-12, post-wrap)

The third red-teamer (code/stats) finished after the wrap — deepest pass (50 tool
calls), re-verified against HEAD. Remaining bugs found + ALL FIXED:
- HIGH: duplicate-ingredient recipes (a==b, ~1.4/world) broke engine/oracle
  agreement — inventory −1, V collapse 15→0, phantom salience spike; latent on
  CPU, LIVE for the LLM tier (would poison distillation). Fixed: no-dup DAG
  generation + Counter-based multiset craft/solve. Regression test.
- HIGH: oracle_value neither exact nor monotone (per-raw explore charge → now
  per-distinct-location; docstring now honest "NEAR-EXACT heuristic"; engine now
  logs UNclipped td_signed so setbacks are visible).
- HIGH: harness durability — _save now ATOMIC (tmp+os.replace; kill mid-write
  previously lost ALL progress), config-drift guard fails loudly (test),
  probe_eval done-guard.
- MED: np.seterr global → scoped errstate + finiteness asserts (global numpy
  state verified untouched); keyword_gate+oracle_weight now in DEFAULT policy
  set; labels reach _weights ONLY for oracle_weight; psychic detours fixed
  (detour only to already-known sites).
- LOW: context_fifo dedup/denominators, det_pool empty guard.
- Verified clean by the agent: requirements() recursion, kill-resume
  byte-identical, fast-weight numerics under stress, exact head gradients,
  harness pairing.
Honest-test reframe: with mock embeddings felt must show NO advantage beyond
keyword_gate (any felt-only mock win = returning artifact); keyword_gate's own
modest signal (~0.16) is legitimate env structure (counts are gather-only).
50/50 tests across suites. All three red-team reports now processed.

### Overnight session 2 (2026-08-12→13): GPU tier + paper prewrite complete

Built for the 8 AM lease: gpu/setup_node.sh (two-phase driver→env→models→tests),
run_gates.py (S0 calibration w/ real model), rollouts.py (vLLM lockstep PASS A +
multi-layer state cache PASS B; padding-side + world-seed-logging defensive fixes),
train_head_real.py (S2 + hour-12 kill-switch, mock comparator 0.03 w/ provenance),
probe_eval_real.py (S3 policy zoo on real-state salience, felt-vs-keyword_gate as
THE decisive line), RUNBOOK.md (hour-by-hour). All CPU-importable, resumable.
paper/draft.md v0.1: full ICLR skeleton, all CPU results + verified attributions in,
GPU results as [SLOT]s, negative-control ledger as §6 (methodological contribution),
tone rules + submission checklist embedded.
Verification: agents flaky tonight (1 stall, 1 launch-block); paper fact-check done
by self-audit (all numbers traced to sources ✓); GPU-script red-team relaunched.
Absorbed from Rohin's external-AI paste (selectively): contrastive K-V loss idea
(GPU-tier memory-training option), confirmation our sigmoid head avoids softmax
saturation, residual-alpha = our existing v2 Flamingo plan; discarded garbled
attributions (ATLAS≠Meta).

### Meta (Rohin, on his own currency)

Two currencies for the project: (1) get into elite research environments,
(2) do something he's proud of / help the field. (2) is overarching, (1)
may be instrumental to (2). Explicitly wants curiosity as the attention
mechanism, with just enough outcome-pressure to ship. Self-initiated, no
lab, no formal research background — arrived at the frontier problem shape
through reasoning + lit search. Wants to keep it fun, publishable, real.

---
