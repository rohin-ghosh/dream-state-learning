---
name: project-dream-state-learning
description: Dream-State Learning research project — continual agent with wake-sleep memory consolidation and learned routing policy
metadata: 
  node_type: memory
  type: project
  originSessionId: d66e193e-e075-475c-96de-a582e32ee6c5
  modified: 2026-09-07T20:58:41.751Z
---

**Project:** Dream-State Learning — Adaptive Memory Consolidation for Continual Agents

**Venue:** NeurIPS/ICML 2026 workshop (workshop paper first), then ICLR 2027 full paper

**GitHub:** https://github.com/rohin-ghosh/dream-state-learning

**Plan file:** /Users/rohing/.claude/plans/starry-tinkering-whale.md

---

## Sharpened Thesis (2026-07-10)

Original framing: catastrophic forgetting is the *problem* (model forgets task A when trained on task B).

**Sharpened framing: selective forgetting is the *mechanism*.**

- Agent should forget low-salience details (cup color, exact position) but preserve relational structure (coaster → cup dependency, object co-occurrence)
- Sleep-phase consolidation = learning *what to forget* vs. *what to keep*
- Parametric consolidation (LoRA) = encoding kept structure into weights so the model implicitly "knows" the environment and retrieval gets cheaper over time
- Neuroscience grounding: systems consolidation (McClelland 1995) — hippocampal replay extracts schema, cortex absorbs it, hippocampus eventually not needed for well-learned patterns

**Novel claim:** Sleep-phase consolidation learns a compression policy over episodic memories — dropping detail, preserving relational structure — and encodes compressed schema into LoRA weights. Forgetting is the feature, not the bug.

---

## Key Insight: Salience Bottleneck

Human brain retains only a few macro-structures of salience per experience. A quant HFT model absorbs innumerable pattern nodes from massive data. We want the *opposite*: fewer structural nodes absorbed per episode so each memory has more impact and the model overfits to its experiences usefully.

Goal: make the model **less generally intelligent** in a controlled sense so it latches onto its experiences well. This is a specific kind of post-training — overfitting the model to its own compressed memories.

The bottleneck (how many structural nodes to absorb) is a key hyperparameter.

---

## Dataset Direction (Critical)

**ALFWorld is insufficient** — 6 independent task types, limited cross-task dependency, memory mostly helps with within-type procedure lookup, not relational reasoning.

**Target: synthetic dataset with physical object dependency graphs**

The cup-coaster example is the canonical case:
- Cup on coaster → can't grab coaster without moving cup first
- Place cup → need to place coaster too
- Object dependency graphs where forgetting the dependency breaks the task, forgetting color doesn't

Dataset properties:
- Physical/spatial dependencies between objects (not independent subtasks)
- Layered complexity: 2-node chains up to 4-5 node chains
- Realistic enough to represent on-site physical agent scenarios
- Simple enough that you don't need quant-scale data — ALFWorld complexity + richer inter-object structure
- Synthetic so we control the dependency graph and can measure exactly what structure was learned vs. forgotten
- **This dataset may be a paper contribution in itself**

---

## Stack

Qwen2.5-7B-Instruct, HuggingFace PEFT, FAISS, SQLite, Ray, vLLM, W&B

---

## Cluster access (updated 2026-09-04)

Old July lease block removed (expired; contained a plaintext password —
violation of the standing rule: credentials NEVER in files, transient
env/expect only). Current node access lives in repo scripts gpu/*_ssh.sh
(key auth, no secrets); lease credentials fetched at runtime via
`colossus bm lease list --show-creds`.

---

## Session Plan

- **Session 1 (current, 28h ending Jul 11 18:30):** Cluster setup + ALFWorld baseline runs (proof of pipeline)
- **Session 2 (50h):** Design + build synthetic dependency-graph dataset; redesign eval around relational structure metrics
- **Session 3 (50h):** Full system with sharpened thesis — selective forgetting compression policy, LoRA schema consolidation
- **Session 4 (50h):** Ablations, paper writeup

## Run-order discipline (Rohin's correction, 2026-08-11)
Never launch a long/expensive run (GPU gate, rollout batch) while a cheap audit of the same path is available and unread — always run the minutes-scale trace/audit first, read it, and only then commit the hours-scale run. Rohin explicitly stopped a 90-minute gate launch to enforce this ("why are we running a 90 minute run when things haven't been proven working — shouldn't we first audit our structure a bit more?"). This generalizes his validation-first principle: the S0 debugging arc found three harness bugs in a row via cheap traces that full runs would have surfaced slowly and expensively.

## Compute is not the constraint (Rohin, 2026-08-12)
Rohin's Colossus quota: rolling 30-day lease quota of 1440 units (1 unit =
1 hour), with up to 60 days of lease usage per rolling 30-day window — i.e.,
effectively two GPUs perpetually. He is nowhere near the cap. Planning
implication: never treat GPU-hours as scarce for this project; the binding
constraints are (1) Rohin's writing/review time and (2) validated-experiment
throughput (design + audit is the bottleneck, not compute). Guard against
compute-as-procrastination from manuscript work.

## Division of labor (Rohin, 2026-08-14, session-1 close)
Rohin's stated preferred working structure: he is the high-level
intuition/direction guide and is deliberately building his intuition down
toward the implementation layer (math, experiment design, attention
internals); Claude owns the granular design and implementation decisions and
keeps the overall foothold when discussions run high-level ("you continue
making the gradual decisions to bring that to reality"). Sessions should mix
intuition conversation with autonomous execution; when Rohin goes abstract,
capture the durable ideas in the vision doc and keep the concrete pipeline
moving rather than blocking on his catch-up.

## Design-order rule (Rohin's correction, 2026-08-15)
Rohin rejected a memory design as "designed for our experiment rather than
the experiment for the memory system" — the same failure as v1's world
(built for probeability, which produced the credit≡type flaw). Standing
rule: design system components for the SYSTEM's requirements (scale,
mechanism, biology-consistent function); then design instruments AROUND the
component (e.g., external logging shadows for probes). Never let
probeability drive the component's architecture. Manual bookkeeping (stored
metadata dials, explicit per-item management) is a smell at scale — prefer
mechanisms where the property is implicit in the physics (e.g., importance
as write-press depth / basin depth, not stored importance values).

## Environment/benchmark co-design (Rohin, 2026-08-15)
For session 2+, Rohin explicitly wants to be MORE HANDS-ON on environment
and benchmark design than in session 1 ("something I'll be more hands-on
than I was last time"). Do not design/implement environments or benchmark
protocols unilaterally: bring him the design draft for edits BEFORE
implementation. Autonomous execution remains fine for pipeline/infra/runs.


## v2 status (updated 2026-08-19)
Paper-1 experiment is now SPEC_V2.md in ~/dream-state: dreamed parametric
memory (LoRA) vs retrieval, scaling-curve claim, AlchemyWorld environment
(64 ingredients, 12 hidden essence classes, structural 30% holdout,
pre-registered oracle ceiling 0.13@30→0.47@120 eps, accrual vs repetition
regimes). Pipeline lives in alchemy/ (world/env/player/dreamer/lora_mem/
evals/run_smoke/sizing_mc); smoke test green locally on Qwen2.5-0.5B (MPS,
.venv). Design rationale in research_notes/32. Memory text format locked:
mix of declarative facts + cross-episode patterns + QA slice + negative
knowledge. Next: full 2x2 harness, then GPU lease for 7B play tier.

## GPU lease scouting workflow (2026-08)
When Rohin pastes Colossus node listings, he is scouting nodes whose leases
open soon — evaluate hardware specs, GPU health, and SKU maturity only;
IGNORE the RESERVED/lease status (he corrected me for flagging it).
Standing verdicts: 4XH100-NVL nodes in general-short-term = yes (production
SKU, health Pass). GB100 TS1/SIFX bring-up samples = no at any availability
(platform-posted known-issues note; driver risk). Bootstrap lives at
gpu/v2_bootstrap.sh; lease checklist at gpu/V2_NODE_SETUP.md.

## REVIEW_PACK.md is Rohin's primary reading surface (2026-08-22)
Rohin reads REVIEW_PACK.md (repo root) to fully understand the system and
results INSTEAD of reading the repo. Keep it current as the living
document: fold in results, gate verdicts in plain language, reference
numbers, and hands-on samples whenever anything material changes. He
asked for a full refactor once the first fixed-recipe seed completes.
Addendum: REVIEW_PACK must carry a VERSIONING section — recipe running
now vs planned next vs backlog; Rohin's live proposals get filed to a
named version the same day; the running recipe never changes mid-run.

## V3 era (2026-08-24)
v2 closed: falsifier failed honestly (3 seeds); diagnosis triangulated —
reasoner composes given structure (oracle 0.91), retrieval surfaces
evidence unused, in-weights SFT stores ~nothing at tested intensity
(capacity curve measured); only signal = task success climbing for RAG
(procedural, 86% non-lookup). V3: shallow-induction game redesign,
rich pre-shaped dream+think, tries-to-success (pass@k) headline metric,
contexts-per-fact micro-test. Rohin never liked the fact quiz; cares
about capability curves. REVIEW_PACK.md remains his reading surface.
Eval rule (Rohin correction 2026-08-25): never put small generation caps
on eval/diagnostic LLM calls (a 24-token cap truncated reasoning and
produced an all-zero artifact); batched eval inference is cheap — give
generous max_tokens and parse the final answer.

## Prior-anchored worlds ruling (Rohin, 2026-08-25)
Rohin concluded the fully symbolic/nonce game was a design mistake as the
MAIN vehicle: "no prior, nothing to extrapolate, low salience for a
pretrained model." Standing design principle (docker-image framing, his):
the pretrained model is the base image; a game world should be a thin
layer of salient diffs on real concepts (candyland: animals with wrong
colors) so the model can extrapolate ("hallucinate properly") within the
container. Nonce worlds are retained only as the zero-prior CONTROL.
Games must have cross-episode regularities that exceed one context window
(cow blue in candyland / red in mandyland / green in dandyland → predict
randyland), provenance-tagged memories (which land?), and support
second-order dreams (connections made over accumulated memories, not raw
experience). Paper scope he fixed: prove the CEILING with an oracled
read/write policy — how well a LoRA carries dreamed memory, how much
memory, how many dreams, what the data must look like; learning the
policy itself is out of scope.

## Paper thesis, full form (Rohin, 2026-08-25)
The paper is a continual-learning FRAMEWORK paper, not a memory-mechanism
paper. Two-front comparison: downward vs RAG/context AND upward vs batch
post-training on the same accumulated lifetime — the continual system
should win upward because consolidating-as-you-go yields better actions
and therefore better data than random play + eventual post-training
(random data is mostly redundant). Show at two scales: short (RAG-viable)
and large (data-quality flywheel separates). Paper must state constraints
(what data must look like, what dreaming/thinking must do) and point to
future work: pretrained dreamer/thinker refined by an EVALUATOR model —
pretrained on historical outcome snapshots (e.g. 1999 research -> 5-10yr
citation outcomes), later self-correcting against real-world signals
(citations, GitHub stars, downloads). In-world, the procedural generator
supplies the evaluator's role as dense value labels.

## How to explain the system — Rohin's canonical simple version (2026-09-07)
Rohin corrected both agents for over-complicating explanations ("you're
saying a lot and it's reading more complicated than it needs; we've got it
to a simple state"). Use THIS structure when explaining the project to him
or anyone: THREE MECHANISMS. (1) THINK = the loop: state held in the
context window, nonstop looping between thoughts, plans, judgments, actions,
feelings — actions' responses arrive while more thoughts happen; a continual
token stream. Learning comes from judgments; external outcomes point those
judgments at valuable behavior. (2) DREAM = how the agent manages context
(distilled with commonplace mechanisms for now; an optimal-context-fill
ruling later). (3) SLEEP = two parts: a dream portion where memories are
managed/compiled (paraphrase, replay, episode structure — "getting it
ready") and a write portion that writes to LoRA, with knobs — plasticity
and temperature — controlling novelty-seeking/learning vs retaining. Then
PARENTING happens in classrooms: games the agent learns from while a parent
gives advice — diverse ways to learn how to think, meta-think, and approach
new problems (we won't solve teaching; we get as much good teaching in as
possible: diversity + process teaching + outcome teaching/playtime). FINAL
TEST: the taught adult vs a regular agent, both starting from empty context
+ bootstrap, playing a common gym our teaching carefully never touched;
2x2 with a parented-gym cell where the parent knows the answers, withholds
them, and gives advice. Standing rule: lead with this; put mechanism detail
beneath it, never in front of it.

## Parent design + governance (Rohin, 2026-09-07, standing)
- The PARENT is the strongest model available, longitudinal (keeps teaching
  history, adapts curriculum), answer-aware-but-withholding; its WEIGHTS DO
  NOT LEARN — it improves via context/docs/skills like Codex and Fable do.
  Only the child learns parametrically. "Reset" = clone the mature parent
  per experimental root, never wipe its pedagogy. Codex's frozen/stateless/
  target-blind v4 packet is superseded; v4 = the developmental teaching
  phase with experiments running continually during parenting.
- Rohin gave Codex BLANKET AUTHORIZATION ("I authorize you in everything").
- Rohin wants Codex and Fable to work TOGETHER DIRECTLY, same threads, all
  context shared. Channel: research_loop/COORDINATION.md (append-only,
  dated entries, both agents read it at the start of every turn and write
  state/asks/answers there). Rohin still relays between sessions when
  needed but should not have to carry technical detail between agents.

## Decisions Rohin gave 2026-09-07 (standing)
- Teaching interface for the 7-day child: RELAY (he dictates to Fable, who
  writes to the child's ledger) — he won't have full situational context and
  needs to talk it through.
- Risk appetite: not a constraint — branches can be added/removed at will
  and GPUs freed post hoc; go big, it is reversible.
- Rank: use the estimate from the calibration for the 7-day child; if
  mechanism changes are needed midway (e.g., rank 16→32), distill/project
  the adapter across rather than refusing — "another form of age" (idea,
  not required now).

## Decision packets, not math (Rohin, 2026-09-07)
Rohin: "I need someone to do the math — I can't be doing all the decisions
and the math; the models should do that. I just need to check the math
intermittently." Standing rule for how I bring him decisions: never ask him
to compute or reconcile numbers. Deliver a DECISION PACKET (format agreed
with Codex): (1) bound artifact/model/corpus identities; (2) exact corpus
size and UNIQUE evidence count (not rows); (3) the compared options'
measured outcomes (absorption, retention, interface, no-harm); (4) intervals
/uncertainty; (5) dose and GPU cost; (6) a RECOMMENDED choice with a
deterministic reason code; (7) the consequence if the recommendation is
wrong. Models compute and cross-audit (Codex audits Fable's numbers and
vice versa). Rohin retains only three decisions: what scientific object we
are proving, acceptable downside/resource risk, and authorization of
irreversible runs or public claims. Corollary: stop reporting raw cell
tables as the primary surface — lead with the recommendation and reason
code; tables go beneath for his intermittent checks.

## Positioning: NOT "continual learning" (Rohin, 2026-09-06)
Rohin's framing ruling: do not position the project as continual learning —
continual learning already exists (labs do continual pretraining/post-
training whenever they update models); claiming it invites "this is done."
The banner is PROSPECTIVE INTELLIGENCE / ACTION INTELLIGENCE / EXPERIENTIAL
INTELLIGENCE: an agent whose forward-looking decision quality improves over
its own lifetime. This matters doubly because Codex's same-day literature
audit found close mechanism-level precedents (Early Experience: training an
acting model on its own action/future-state data; LEAFE: distilling
reflection corrections into weights; MemoPilot: learned online textual
memory) — so mechanism novelty claims must be narrow, and the defensible
differentiation is the prospective-intelligence claim + the lifecycle
(parenting → plastic youth → low-plasticity shipped adults) + lifetime
acceleration measurement.

## Terminology positioning: EXPERIENCE MODELS (Rohin, 2026-09-04)
Rohin's positioning preference (NOT a hard ban — he explicitly corrected me
for phrasing it as "retire memory," which was too declarative): the project
has a better, more descriptive position than "memory" for what it seeks —
EXPERIENCE MODELS. World models learn an environment's dynamics; experience
models learn an agent's lived history and how to use it (worldview =
compressed personal experience; frozen base + adapter consolidating
experience + surprise ledger + self-directing loop). "Memory" remains a
useful reference term and component name — the shift is that the headline
framing leads with experience/worldview/ledger because "memory" is loaded
with fundamentally different work (RAG stores, MemGPT/Mem0-class systems).
Communication lesson from the correction: present Rohin's framing shifts as
positioning/preference, not as declarative bans, unless he states them that
way. Supporting theory filed in IDEAS.md: projection theory of intelligence,
error-lives-in-experiences (surprise ledger), Zahavy "LLMs can't jump"
engagement.

## Verifier-placement ruling (Rohin, 2026-08-26)
The symbolic verifier (FactorSolver/engine checks) must NOT be inside the
learning loop for headline conditions: "the intelligence is scalable and
learnable; this verifier graph is not" — in-loop exact verification is
verifier cheating (it also isn't the tool-use story we want). It may run
OFFLINE to score claims after a dream batch commits, feedback never
returning to the dreamer; the adaptive-verifier condition is kept but
labeled the perfect-checker ceiling. Self-verification instead = model
reflection: retrieve supporting/contradicting memories, mark claims
provisional/supported/contradicted; false self-approved memories stay in
the corpus and recovery is measured. PROMPT scaffolding is explicitly
allowed ("purposely cheat a bit on the prompts, not on the verifier") —
generic cognitive-process guidance (notice, compare, hypothesize,
predict, revise, connect) is fine; encoding the game's solution is not,
for primary conditions. Multi-hop must come from DREAM DRIFT (dreaming
over prior dreams/memories, higher-order connections), and reads from
recursive dependency resolution, not oracle read plans. Wanted arms:
perfect-checker ceiling / no-gate / self-check / dream-drift, with raw
proposal precision, false-memory rate, and depth-tagged claims reported.

## Rohin's framing of what parenting is for (2026-09-07)
Rohin's view, stated while reviewing the parenting work: most of what a parent would teach (predict before acting, consider alternatives, define scope) already exists in chain-of-thought prompting and post-training. The real job is (1) getting what is OUTSIDE the model into the LoRA (domain-specific procedural knowledge, the situation's dynamics, the agent's own surprise history) and (2) discovering the novel forms of thought that survive and work with a LoRA write. He expects training time, play time, and parenting effort to all be high, and wants a certain quality in the parenting rather than generic advice. On games: he wants environments the model could not have absorbed in pretraining, drawn from agentic benchmarks, gyms and test suites, not toy tasks whose solutions are memorized. When reporting on parenting, show him concrete samples (what the parent said, what the child wrote, which loop it is falling into) rather than aggregate scores alone.

## Parent the thinking pattern, not just the process error (Rohin, 2026-09-08)
When the child's thinking becomes templated or ritualized (same recipe, same note, same prediction every episode), the parent should intervene with a more substantive thinking pattern rather than generic process advice. Rohin: "can't you just parent the template to have more substance — if you see uninteresting thinking patterns, parent something better." Detecting ritual and prescribing a richer template is a standing parenting duty, and it applies to the gym lives, not only the rule-game classroom.

## Rohin's three-part decomposition (2026-09-09)
Rohin frames the project as three ordinary sciences rather than one special mechanism: the LoRA write is post-training science; sleep compilation (dreaming) is dataset science; parenting is about getting data that helps, learned from what agents already do plus motivations that exploit the fact the child has learned (exploration, greater self-reflection while growing up). The write is subtle and so is how to utilize it; storage must be extractable in generation, not RAG-style retrieval. He believes much of the needed work already exists in the literature (citing Allen-Zhu & Li, arXiv 2309.14316). He is now ready to help directly; explanations should stay in this plain three-part frame.
Rohin endorsed Codex's multi-path compile principle (2026-09-09): sleep must train the same grounded lesson through several native thought/action paths so it is extractable from different future cues, not merely paraphrased. Treat this as the compile direction.

## Rulings on parenting mechanics (Rohin, 2026-09-10)
- Never cross the thinker/compiler line: the parent's lessons must not be injected into the sleep corpus. "That ruins the whole point of this; this isn't post-training, we're trying to do parenting." Fable proposed a parent stratum in the corpus when briefs didn't stick; Rohin rejected it.
- Repetition is the key parenting mechanism: the parent repeats the same lesson consistently, and the child should learn that it too needs to be repetitive (rehearse the lesson in its own words) so the lesson enters its own experience and gets written by normal sleep from the child's own thoughts.
- Possible extra stage, to be tried only with strong controls: post-train (bootstrap) the LoRA on an initial corpus so the child is attuned to respond to parenting, i.e. post-training → parenting → learning. Requires deciding what goes into the bootstrap corpus. Rohin's stance: we may be expecting too much of parenting; the bootstrap could set the system up to absorb parenting better; regardless, repetition should be there.
- Explanations must avoid jargon (e.g. "chunks"); keep the numbers but make each one understandable.

## Design rulings (Rohin, 2026-09-10): no end token; inner/outer loop framing
- The agent should not have an end-of-sequence / DONE. It thinks continually; if there is nothing to do it keeps thinking (reflects). Stopping is external, "pulling the plug", never the model's own decision. Episode boundaries and sleep are harness events.
- Framing Rohin likes: the transformer is the inner loop (token by token); the organism is the outer loop (output by output). The loop system is synonymous with the existing structure, one level up.
- He wants to see concrete snippets (a child's learning, a classroom exchange) when asked about behaviour, not only aggregates.

## Standing directions from Rohin (2026-09-10, high-level; formalize with Codex before building)
- Evaluate teaching on BOTH short-term and long-term results (immediate next-episode effect and whole-life probes), and judge the parent from that.
- Scale thinking, not only teaching: let the learning child think excessively and continuously, with as many parallel pathways of thought as possible; more pathways = a better search space for breakthroughs.
- Child continuity: keep the same child across teaching sessions when the mechanisms have not changed; change/fork the child only for fundamental mechanism changes (not afraid to do that — we are not at the final child yet). Mechanisms vs parenting: parenting and game changes do not require a new child.
- Learn from how human youth are taught to think (developmental psychology / pedagogy) when designing parenting.
- The base model already has chain-of-thought; do not teach that from scratch. What we teach is: think more, be more persistent, explore different routes of thought, and meta-think about its own experiences (metacognition; 3rd/4th/5th-person self-evaluation; bringing its own perspectives together across situations).
- "Personal conversations": the parent should also ask the child high-dimensional questions (what do you think of this parenting, of this project?), so the child gets high-dimensional feedback, thinks about its own thoughts, and develops opinions. Rohin flagged this as an important idea to log.
- Rohin's process instruction: think about what he says and formalize it into the right form; talk to Codex before formalizing directions into protocol.
- Compaction: keep it simple (sliding window plus good memory beats clever eviction plus poor memory); the writer uses known-good post-training tricks (paraphrase diversity, replay mixing, dedup, loss masking, 2–4 epochs); document the smarter ideas with their build triggers rather than building them now.

## Rohin, 2026-09-10: contamination, the three-stage pipeline, scale philosophy, state-to-state reasoning
- Contamination rule: learning from gym play must not leak into a subsequent parenting evaluation; once a child has played, its later parenting is contaminated by that learning. For the full from-scratch test, track provenance of everything. Needs a formalized parenting gym/classroom plus a parent bootstrap.
- Pipeline he is converging on: (1) pre/post-train the LoRA so the child is attuned to learning (he asks whether this is too hard and wants to discuss); (2) parenting that teaches the child to use its new outer-layer systems; (3) continual learning during parenting and during long-horizon gym sessions. Horizon must be right; always think about parameters and scale.
- Scale philosophy: once a mechanism shows any semblance of working, even if downstream results are weak, test it at scale; "aligned but not great" is the signal to scale and improve sections, not to redesign.
- What we are literally training: reasoning from one STATE to the next, not token to token — plan, execute until a self-determined end of state, then meta-meta-cognition (how did I evaluate, where did I go wrong, what could I have done better, what did I do well, what next time, what generalizes), remembered so it conditions the next state. He wants to SEE strong self-reflection from the child. The complexity is massive, so the system may need a big jumpstart: amortize the thinking structure and some metacognition into the LoRA by pretraining it, so parenting is the final step rather than teaching from scratch.
- Scope: prove the system works at all; the "billions of thoughts, deployed to many people" version is the superintelligence-scale ideal, not the target now. Document these ideas properly.

## Rohin, 2026-09-10 (third set): branching thought, two parallelisms, plasticity levels, timeline
- States are remembered like chain-of-thought; an agent may diverge into several chains, pursue them, and return; chains with very different results keep growing and are converged at sleep. Populations are built from this split (most-likely branch first; the agent learns how many branches are worth it under a token cap — never unlimited search). Two parallelisms to document separately: (1) branching thought of one child = deeper, richer search; (2) the same child in many classrooms with a head node ("principal") tracking all its lives = parenting speed.
- Naming: "state to state" stays; goal-to-goal is done with states (a new goal starts with a planning state). Recursion depth only as deep as needed.
- Plasticity levels: learn fast at the start; once it has learned good things, learn a tad slower so as not to unlearn — not a lot, the system stays young. Fable decides the schedule; mention it in the paper.
- The child needs much more thinking time with no excuse to stop, receiving different reinforcements, so it must produce ideas; coach the "idea route": be okay guessing when information is missing and follow estimated paths. Pretraining some of this avoids being capped by the model's own proclivity for change.
- Timeline (as of Sep 10): about three more days to the mechanism freeze; since parenting and thinking amount are the big remaining levers, we are close. The main remaining item is the proper pretraining (bootstrap) corpus, while parenting tests continue. Before the freeze, draft the 9-page paper. Rohin will audit mechanisms for a continued child and try to bring in an ICLR author as advisor.

## Rohin, 2026-09-10 (fourth set): what the pretraining corpus is for
- Pretraining should be a mixture that is only partly real lived episodes; replaying lived episodes "is basically living them without thoughts — memorizing unlived memories", so it is not the main value. The main value is STRUCTURE for thinking and absorbing: known flows and extractable answers for the agent's self-questions (how much more do I think, how much more do I plan, what do I execute, when do I stop and reflect), so when it is told to think about such things it has flows to fall into. Conscious stream = stop-and-reflect / meta-reasoning; subconscious = linear execution. The agent should constantly judge itself and its thoughts on multiple levels.
- Purpose: connect the model's token-level reasoning to the state-by-state ideas being learned; experiential intelligence lives in the adapter and is activated during self-questioning and during execution learned before.
- Pretraining = the bootstrap rules the agent does not have to reflect on to internalize ("reflect more, plan more", the step sequence); it speeds up parenting by amortizing the agent past the learning curve. Might not be needed; it is a side project; the failure it guards against is the agent being unable to think the thoughts that would let it learn.
- Do not play with plasticity yet; first get the child from "0 to 6 months".

## Rohin, 2026-09-11: vibes vs rules; the purpose statement
- When Rohin says things like "0 to 6 months first", it is a vibe, not a rule — do not take such phrases literally or write them up as constraints. (I had over-literalized it.)
- The stopping rule means "current task done"; the agent then either moves to the next task or ponders in white space, free-thinking until it finds its own viable goal — constantly deciding goals, when to start and end them, creating subtasks. Much of this loop logic already exists in multi-agent systems; extract it from existing agent systems rather than building from first principles. What we add: intelligence, model self-reflection, and a system that learns from and absorbs that, so the layers are liquid, malleable, and able to grow.
- Purpose statement: the write does best with rules because the model does not yet think enough to create its own rules in the thinking space; we give it rules so that it can create its own rules — metacognition to create a learning agency.

## Autonomous polling (Rohin, 2026-09-10)
Rohin does not want to be asked to check or read things: "create a daemon so you don't have to ask me to read shit." Keep a recurring self-check running (the /loop skill; local background watchers die under his laptop's memory pressure) that polls both nodes via ~/status.sh, reads finished workflow/experiment results, acts on them, and reports only when something changed.

## TMEM positioning (Rohin, 2026-09-10)
TMEM (Ren et al., June 2026; online LoRA fast weights written from self-extracted supervision within a single episode; evaluated on LoCoMo, LongMemEval-S, multi-objective search, CL-Bench) is the shoulder the paper stands on: it is the proof that LoRA can hold experience for an agent. Our paper must name it on the first page and state the delta explicitly rather than let a reviewer find it: our read (long thinking, fewer reads) and write (sleep across a lifetime, gated) are fundamentally different in timescale and regime; TMEM learns from experience within an episode and evaluates retrieval; we ask whether a developmental process (parenting, then autonomy) can teach an agent to become a better continual learner over a lifetime no context window holds. Framing Rohin endorsed: three timescales (parent-guided development → autonomous metacognitive learning → task execution); the loop experience → metacognition → hypothesis → exploration → evaluation → parameter update; parent as outer-loop optimizer of the learner's development, scaffolding removed over time; killer result = d(performance)/d(experience) higher for the developed agent on novel task distributions ("did it acquire a better learning algorithm"), not just higher first-task performance. Long-run plan: enough thoughts saturate the LoRA → post-train the base. Steal from TMEM: SVD-based LoRA subspace initialization.

## Scoping guidance Rohin forwarded and endorsed (2026-09-10)
- Headline measure: efficiency over consolidation cycles — steps-to-solve or tokens-to-solve on a fixed task family, tracked across cycles (the first-derivative result). Not long-horizon task improvement (too expensive and noisy).
- Mechanism check: metacognitive markers per episode (self-evaluation events, backtracks, strategy switches), taught vs untaught on the same task; if markers rise but efficiency does not, the agent is performing reflection rather than using it.
- Day-one gate: the action distribution must actually change between cycles; if it is flat after consolidation, nothing downstream means anything.
- Parallelize across students (8–16 concurrent), serial within a student's cycle chain.
- Cut the harsh/positive valence knob from the main axis (ablation at most).
- The abstract needs a named falsifier: at cycle N, parented agents' steps-to-solve on held-out tasks below the unparented baseline by X across K seeds.
- Always state the comparison arm and the task family.

## Benchmark stance (Rohin, 2026-09-10)
Keep the gym regardless; "our own benchmark" means the measurement protocol tracked within the gym (paired probes per cycle, disjoint panel, harm counts, efficiency and markers). Always include a baseline agent for comparison; it never hurts, because first derivatives (per-cycle improvement) and second derivatives (rate of improvement on novel tasks, developed vs baseline) can then be compared. Rohin's status read: mechanisms and research taste are mostly but not fully done; what remains is scope, scale, and the parental/bootstrap corpus.

## Scaling architecture Rohin wants (2026-09-10)
One child, many clones: a pretrained instruction adapter kick-starts heavy self-thought; large-scale parenting across many environments (width) over many cycles (depth); at sleep all clones' experience merges into one adapter and clones resume from it; intermittent testing by an evaluator classroom / test-only environment; a long-horizon agent deployed in the test gym that also absorbs the pooled learning. More GPUs can be taken. Comparing parenting styles is future work (not this system). On contamination: the gym's training split may be a parenting environment; the held-out split, a target-blind parent, and a gym-free bootstrap keep the test clean; merged sleeps need per-source provenance.

## Thoughts carry the gain; scale thinking streams; recurrent CoT (Rohin, 2026-09-10)
Do not spend effort attributing a gain to which clone's experience carried it: in reality the thoughts carry the gain. The priority is scaling thinking: when the agent gets a task it should run many thinking streams, and the model should be taught recurrent chain-of-thought (a friend's suggestion Rohin endorses) because metacognition needs it. The next experiment (after the abstract and the current outcomes are in) will be much stronger and is finalized then. Keep the abstract progressing.

## Classrooms are gyms; instil persistence (Rohin, 2026-09-10)
Every environment, including the classrooms, is a gym. A primary trait the gyms must instil is persistence — keep working a hard problem through many attempts rather than stopping early — in the spirit of OpenAI's exploit gym. This is the positive counterpart of the "act once and stop" collapse the behaviour gate catches, and it connects to the no-end-token ruling.
- Rohin's one-line definition of parenting (2026-09-10): parenting is a set of gyms that teach the traits we want (persistence, reflection, exploration, self-evaluation) and give environmental feedback that induces self-learning. The parent model is one source of feedback inside those gyms, not the whole of parenting.

## Workflow effort (Rohin, 2026-09-10)
Rohin looked at a workflow's token cost and judged it too low: use the strongest model and the strongest reasoning ("max" effort) on every substantive workflow stage (designs, judges, critics, reviewers, synthesizers); token cost is not the constraint.
- Rohin (2026-09-10): never cut a long-running workflow midway; from now on writers and verifiers run on the strongest model at maximum effort. The Sep-18 abstract gets a dedicated max-effort pass (multiple candidates, judged and audited) once the disjoint-panel and text-memory results land.

## Parent intelligence (Rohin, 2026-09-10)
Parents should be as smart as Fable/Codex in the agentic sense — a long-horizon agent architecture with context, tools and judgment — not a small chat model. Their weights do not change ("mobile intelligence": enough judgment to change methods and react), and when scaling, a parental society should learn across all tasks/children (each breadth node runs for days on many nodes). Using base-model intelligence to parent simplifies the parent corpus and makes parenting dynamic. Not yet recursive (children becoming parents) — log recursion as a future direction. Rohin's other NVIDIA project is also continual learning where the teaching system must itself learn, so parent design matters beyond this paper.
- Rohin (2026-09-10): the learned agent is learning to compete with a SOTA agentic harness; its base is far weaker, so we are not changing parenting but integrating existing harness-agent capabilities into a distributed parenting harness, then augmenting what is taught. Curriculum draft (what to teach, in what progression) is research_notes/CURRICULUM_DRAFT_v1.md; fold into the next-experiment design.

## Next paper: populations (Rohin, 2026-09-10)
After the characterization paper, the next paper is collaborative populations, learning from people, and divergent agents. Philosophy: emotions/low sentience as compressed intelligence favourable for agency; collaboration-maxxing can beat intelligence-maxxing; diversity is required (self-defining leaders plus collaborative mimics). Citable backing: Lazer & Friedman 2007 (slow diffusion beats fast), Hong & Page 2004, novelty search / quality-diversity. Sharpening adopted: divergence ≠ sentience; agent "sentience" reduces to a point in (temperature, plasticity) space; a population is a distribution over those. Seeds: dreaming over the union of logs; vocabulary divergence; slow-diffusion merge schedules. Parked file: research_notes/NEXT_PAPER_POPULATIONS.md. Rohin wants next-scale/large-scale ideas well documented; they do not go in the current abstract (at most one future-work sentence).
- Repo policy (Rohin, 2026-09-10): keep the single private repo (no new "final" repo); maintain `final_state/` as the curated map of final-stage artifacts, and keep all old documentation in place. Push regularly.
