# 35 — GOALPOSTS: what Paper 1 claims, what it defers, and what counts as cheating
*(Ruling record, 2026-08-26 — Rohin + Codex + Fable converged. This is the
document to check any new experiment against.)*

## The Paper 1 claim (frozen scope)
> Given a capable FROZEN pretrained model, an inference-time
> consolidation system (prompted dreamer/thinker) can transform
> distributed experience into durable parametric memory (LoRA) that
> supports held-out compositional behavior beyond raw context and
> retrieval — WITHOUT an exact verifier inside the cognitive loop.

Two-front comparison (notes/32, 2026-08-25): downward vs RAG/context,
upward vs batch post-training on the same lifetime. The flywheel
(better memories -> better actions -> better data) is the large-scale
version of the upward claim.

## The honesty ladder (the four arms)
| arm | dreaming | filtering | status |
|---|---|---|---|
| perfect-gate CEILING | game-informed prompts | adaptive FactorSolver in-loop | 0.917 D2 (aligned s0) — labeled ceiling, not headline |
| no-gate | same | none | measures raw dreamer output cost |
| self-check | same | model reflection (SUPPORTED/CONTRADICTED/UNRESOLVED) | the headline condition |
| self-check + drift | + re-dreaming over own accepted memories | model reflection | multi-hop condition |
Prompt-ablation ladder on top: minimal -> generic cognitive loop
(RETRIEVE/NOTICE/HYPOTHESIZE/PREDICT/REVISE/COMPRESS) -> generic pattern
repertoire -> game-informed (engineering ceiling).

## Allowed vs forbidden (the cheating line)
ALLOWED — prompt scaffolding (process guidance): search for recurring
patterns; compare across entities; look for irregularities; ask what
observations have in common; derive predictions; retrieve
counterexamples; connect earlier conclusions into higher-order ones;
decompose questions into dependencies; iterate reflection.
Rationale: "the LLM could come up with these self-prompts anyway" and a
future policy can LEARN them — scalable, learnable.
FORBIDDEN in headline conditions — solution guidance and in-loop exact
verification: stating the latent structure (three positions, palette
rotations, "compare same-colored animals", parent-set menus); the
FactorSolver/engine gating or steering proposals ("the verifier graph is
not scalable or learnable — the intelligence is"). The verifier runs
OFFLINE ONLY, scoring committed batches; feedback never reaches the
dreamer. It is also not the tool-use story — deliberately out of scope.
DISCLOSE — the mechanical episodic cell layer (grammar-parsed witnessed
facts) is supplied to every arm: Paper 1 tests autonomous ABSTRACTION
and CONSOLIDATION over a reliable episodic base, not raw extraction.

## Memory epistemics (target architecture)
Every dreamed memory carries: claim, parent observation/memory ids,
derivation depth, prediction, confidence, status (provisional /
supported / contradicted). Depth-2+ memories must cite earlier memories
— that is how "multi-hop dreaming" is measured rather than asserted.
False self-approved memories STAY in the corpus; we measure their
downstream cost. RECOVERY (revisit -> contradict -> retract ->
reconsolidate) is the C3loop feature, not claimed in Paper 1 unless
built.

## The thinker/dreamer system (C3loop — the systems contribution)
Conscious/subconscious framing (Rohin): thinker = goal-driven regime,
narrow retrieval, resolve next dependency, act; dreamer = surprise/
uncertainty-driven regime, broad retrieval, discover/connect/compress.
ONE recurrent machine: persistent state (goal, slowly-changing agenda,
beliefs+provenance, unresolved questions, contradictions, budgets) ->
select operation -> retrieve -> one cognitive step -> update state ->
optionally write provisional memory -> loop. Scheduler v1 is simple and
inspectable (dream at episode boundaries / on stall / on high
unexplained coverage; think on actionable dependency; replan on
contradiction). Reads are recursive dependency resolution with a call
budget, not oracle read plans. Log full trajectories — they are the
future amortization training data.

## D3 protocol (search vs capability, before scale)
1. Hold the 7B dreamer fixed; sweep hypothesis budget k = 1, 4, 16 and
   drift rounds. Report META_RULE success@1 and success@k.
2. Only then compare a larger frozen dreamer at MATCHED sampling/token
   budgets. If 7B improves with k: bottleneck was search. If only the
   larger model improves under matched search: dreamer-capability
   scaling — a headline finding either way.
(Empirical basis: the 7B already proposed the Blendyland META_RULE in
its main dream pass — it died at parsing, and its parent set was one
land off. Formation is present; ranking and formatting are the gaps.)

## Success criteria (Paper 1 done when)
- Self-check improves memory precision over no-gate without destroying
  recall (measured: 0.61 -> 0.829, recall 0.557 — refine, then freeze).
- D2 transports through LoRA across >=3 seeds and all 3 skins with NO
  in-loop exact verification.
- Some correct depth-2 memories emerge from earlier memories (drift).
- Generic prompts approach game-informed prompts (or the gap is
  reported as the prompt-ablation result).
- Recursive reads beat the one-pass D3 thinker.
- Every claim and read has provenance; every failure is attributable.

## Deferred (future work, in order)
1. Amortize the controller: post-train dreamer/thinker on logged
   successful trajectories (sequence-level relative outcomes / GRPO).
2. Trajectory-value model: predict which dream/think sequences will pay
   off (the 1999-research-snapshot evaluator pretraining; reality
   evaluates the evaluator via citations/stars/downloads).
3. Value-guided search (MCTS over hypothesis trees).
4. Full continual loop: environment-learned verification replaces the
   offline scorer; the system becomes environment-learning.
Naming (Codex): ProofGate = offline FactorSolver; TrajectoryValueModel
= future learned critic; OutcomeEvaluator = real-world outcomes.

## Calendar
ICLR 2027: abstract Sep 18, paper Sep 25 2026. ~20 days at time of
writing. Gate: if the self-check arm holds across seeds/skins by ~Sep 8,
Paper 1 is the systems paper above; fallback remains the honest-negative
framing of SPEC_V2 Parts I–II plus the measured G-series mechanics.

## Reframed ideal claim + controller parameterization (ruling 2026-08-26)
THE HEADLINE ARCHITECTURE is the depth-growth loop:
wake experience -> one-hop micro-dream -> provisional memory ->
reactivation by later experience -> higher-order memory -> parametric
consolidation -> chained thinking (later: action). Dreaming is continual
graph-like growth, not a batch operation. The paper's centerpiece figure
is this loop, with measured emergence timelines and depth histograms.
CONTROLLER RULING: text prompts STAY for Paper 1 — prompted controllers
are canonical (Voyager, ReAct, Reflexion, ToT); rigor comes from frozen
published prompts, the process-vs-solution guidance line, prompt-ablation
ladders, and per-transition measurement — not from vectors. Formalism:
o_t ~ pi_phi(o | z_t, goal); z_{t+1} = F_theta(z_t, retrieve(M_t), o_t);
M_{t+1} = update(M_t, z_{t+1}). Paper 1 instantiates pi_phi as fixed
prompts + deterministic scheduler and states it is LEARNABLE BY
CONSTRUCTION from logged trajectories.
PARAMETERIZATION LADDER (future work, in order of interpretability
cost): (1) discrete prompt optimization (DSPy/OPRO — still readable);
(2) mode adapters / mode-LoRAs per cognitive function; (3) prompt/prefix
tuning (P-Tuning v2) — static mode bias only; (4) conditional prefix
generator / recurrent latent controller (a static prefix is NOT a
consciousness stream — state-dependence requires a generator); (5)
learned operation policy + trajectory-value model. The trade named in
one line: vectors buy learnability and cost inspectability — the same
trade as parametric memory vs retrieval, one layer up.

## Systems-level claim + two-track gates (convergence, 2026-08-26)
THE CLAIM (final form): "We are not proposing a better fact store. We
test whether an agent can progressively transform experience into a
CONNECTED PARAMETRIC WORLD APPROXIMATION that supports new inferences
and actions." Intelligence is a property of the full temporal system —
episodic traces preserve, dreams connect, LoRA/LTM carries across time
and beyond the window, the thinker reconstructs goal-relevant paths,
self-checking compares predictions to remembered evidence, real
feedback corrects the approximation. LoRA is not "the intelligence";
it is the substrate of learned associations. Blendyland is the
cooperative proof: learned operation + inferred parent connection +
role abstraction + role-specific memories + goal-conditioned
reconstruction = an unseen answer no single stored fact contains.
TWO-TRACK PROTOCOL (isolate, then connect):
- Track A bottom-up: experience -> repeated dreams -> operator/parent/
  connection memories -> LoRA write -> MANUAL recognition/reconstruction
  probes (no adaptive thinker in the loop).
- Track B top-down: question -> thinker identifies needs -> KNOWN-GOOD
  text memories (prevents dream/LoRA failures contaminating the thinker
  test) -> chain -> self-check -> answer/defer.
GATES before end-to-end: (1) dream corpus contains the right operator/
parent connections; (2) LoRA recognizes them from VARIED cues; (3)
thinker solves Blendyland from known-good memories within a bounded
budget; (4) neither corpus nor any checker contains the withheld answer.
LoRA is necessary only for the parametric-consolidation half of the
claims; dreaming is testable in text.

## The three nested loops + outcome critic (convergence, 2026-08-26)
1. COGNITIVE LOOP (seconds/tokens): state -> retrieve -> think -> plan
   -> act/observe -> update -> repeat, until outcome / supported answer
   / low expected value / budget / defer-to-next-session.
2. EXPERIENCE/DREAM LOOP (episodes): ~10 episodes -> dream connections
   (shared causes, action-conditions, latent-structure identities,
   exception splits, revisit-worthy patterns) -> consolidate stable to
   LoRA/LTM; provisional stays inspectable.
3. OUTER LEARNING LOOP (sessions/lifetime): session outcomes -> train
   critic/controller -> improve what future loops attend to.
THE OUTER CRITIC is NOT a thought-verifier: it asks "are we making
progress; spend more compute, change strategy, act, stop, or preserve
for another session?" — V(state), Q(state, operation);
progress = V(new) - V(old) - compute cost. Prompt-amortized rules first
(continue when uncertainty reducible; replan on contradiction; retrieve
on missing dependency; stop when transitions stop progressing; preserve
promising unresolved states); trained from session trajectories later.
TIMESCALES: fast = working state/plan; medium = dream connections +
LoRA; slow = controller attention/scheduling; very slow = base model +
broad critic. TWO LEARNING KINDS: world learning (what is true/
connected/causal — via dreamed experience) vs controller learning (what
to attend to, which operation is worth it — via trajectory outcomes).
SHOWN: LoRA stores formatted experiential memory; structured frozen
loop constructs+uses multi-hop Blendy connection; computation ceiling
high. NOT SHOWN: generic dreams build that depth autonomously; the
connection survives LoRA and is reconstructed by an adaptive thinker;
controller learns attention; outcome-trained beats prompted scheduling.
PAPER-1 TARGET (frozen): experience -> prompted recurrent dreaming ->
connected memories -> LoRA -> prompted adaptive thinker -> better
unseen inference/action. Critic + project-horizon = paper 2.
CORE THESIS (canonical flywheel sentence): "An agent converts the
consequences of its actions into an increasingly connected experiential
world model; that model supports better future reasoning and action,
which generates better experience, creating a continual intelligence
flywheel."

## The learning architecture (Rohin's day-off consolidation, 2026-08-27)
THE HARNESS RESOLUTION: the harness is not supposed to get smarter
within one lifetime — it GENERATES the operational trajectories that
train the reusable loop policy across lifetimes. Two adapters, kept
conceptually distinct: MEMORY ADAPTER ("what happened / what structure
this lifetime") — resets per world; LOOP ADAPTER ("how to retrieve,
connect, test, plan, act, stop") — improves globally across worlds.
PARAMETER HIERARCHY (rates fall out of DATA VOLUME, not preference):
working state (no gradients) < lifetime LoRA (one life) < loop policy
(many session trajectories) < base model (very many) ; outcome critic
trained on trajectories paired with delayed outcomes.
LOOP TRAINING LADDER: (1) behavior cloning from scripted/exhaustive
expert trajectories, (2) rejection-sampling SFT on successful
self-generated trajectories (STaR-style; evaluator filters, SFT learns;
mask environment/tool/user tokens, train only cognitive+action tokens),
(3) preference training (success/efficient > failed/wasteful),
(4) GRPO/actor-critic only if on-policy exploration is needed.
RL is optional initially, not necessarily forever.
LOSS DIVISION: memory = next-token/recognition over dreamed abstractions
+ read-fidelity probes; loop = outcome-weighted next-token over
cognitive/action sequences; critic = predict eventual outcome from
intermediate states; base = broad pretraining. No end-to-end backprop
through dreams/retrieval/environment required.
THE CONCRETE LOOP-LEARNING EXPERIMENT (paper 2 or stretch): distill the
exhaustive 57-branch search (expert trajectories — PRESERVE ALL RUN
ARTIFACTS AS CURRICULUM) into a proposal policy; target: untrained loop
0.25 success@12 -> trajectory-SFT loop improves on HELD-OUT worlds.
CANONICAL SENTENCE: "The lifetime LoRA is fast experiential state; the
dream/think policy is a slower reusable skill trained from successful
multi-episode operational trajectories; the base model is the
still-slower general substrate."

## PAPER FORM, FINAL (repositioning session 2026-08-27)
FORM: benchmark suite + reference system + characterization study of
CONSTRUCTIVE EXPERIENTIAL MEMORY (the academic term; not "brain-like"):
register memory ("what color was the fox") < experiential ("these
failures share a condition") < CONSTRUCTIVE ("several episodes imply a
latent rule no episode stated") < agentic use ("that rule changes the
next action in a novel situation").
BENCHMARK SUITE: L0 (atomic structure) / Semantic World (cross-episode
abstraction) / Blendyland (higher-order construction) / Action World
(memories improve multi-step behavior). REFERENCE SYSTEM: standard
frozen agent loop + recurrent dream consolidation + LoRA lifetime
memory + context reset + goal-conditioned memory use.
BEHAVIORAL HEADLINE (the missing piece that de-bares the paper):
dream-connected LoRA beats raw-history LoRA, TMEM-style QA LoRA,
trajectory imitation, RAG/reflection, skill-library (Voyager-style) and
DECKARD-style explicit graph on held-out multi-step ACTION tasks after
context clearing, at matched reflection/write compute.
PROOF OF SCALE (the strongest outcome): capability-GROWTH curves —
depth tiers unlocking with accumulated experience+dreams (1-hop ->
2-hop -> abstractions -> novel multi-step plans) while baselines
plateau/degrade; three growth axes: lifetime length, world complexity,
required depth. Baselines are NOT assumed to stop learning — find their
actual boundaries (retrieval noise, schema-bound graphs, skill-rule
gaps, QA-fact limits, raw-LoRA interference; dream-LoRA may saturate
too — report it).
LINEAGE POSITIONING: DECKARD (LLM dream/wake -> explicit subgoal DAG,
mostly reconstructing pretrained Minecraft knowledge) and DreamerV3
(latent dynamics + imagined rollouts) are the conceptual ancestors;
ours discovers world-specific structure from own experience, keeps it
in PARAMETERS, schema-free, used by a deliberative language planner.
DECKARD-style graph baseline must be implemented fairly in Action World.
LORA NECESSITY: at current scale context==weights (2x2); the weights
claim requires lifetimes swept PAST the prompt budget — scale is not
optional for the paper, it is where the substrate claim lives.
TMEM CORRECTION: it DOES outcome-train its extraction policy (notes/00_
synthesis corrected; forbidden-claims list expanded there).
TITLE DIRECTION: "From Experience to Weights: Evaluating Constructive
Parametric Memory in Language Agents."

## THE ONE-SENTENCE HYPOTHESIS (Rohin, 2026-08-27 — canonical)
> Dream–LoRA–Think enables self-learning agents to convert experience
> into persistent, connected world models, CONTINUING TO IMPROVE as
> agent lifetimes and task depth grow where existing memory systems
> SATURATE.
Not "faster" — BETTER past the saturation point of other systems. This
is the central hypothesis the experiments must prove, not yet a
demonstrated claim. The saturation framing sets the experiment shape:
run every system far enough that baselines flatten, and show the
dream-connected curve still rising.
