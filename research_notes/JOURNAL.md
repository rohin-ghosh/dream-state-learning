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

---
