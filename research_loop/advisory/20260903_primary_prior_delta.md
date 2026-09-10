# Primary-source prior-art delta for the RML paper

**Date:** 2026-09-03  
**Status:** paper-design advisory, not an experiment result or implementation authorization  
**Sources:** primary paper pages and full-text arXiv versions inspected on 2026-09-03

## Executive ruling

The project cannot credibly claim novelty for any of the following in
isolation:

- online LoRA as an agent's parametric memory;
- outcome-training the policy that emits LoRA supervision;
- offline "dream" consolidation over multiple agent trajectories;
- provenance-linked, multi-source memory synthesis;
- structured, evolving, interconnected external agent memory;
- parametric consolidation of embodied action skills;
- sleep-inspired selection of what and when to internalize.

TMEM, Auto-Dreamer, A-Mem, PEAM, EVAF, and Parametric Memory Law collectively
occupy much of that space. The
paper-worthy opening that remains is a narrower causal and experimental one:

> Does target-blind, prospectively grounded consolidation of an agent's own
> public action--outcome experience create a connected causal world model that
> changes held-out multi-step action after the experience leaves context; which
> part of that effect is due to semantic induction, retrieval/traversal, or
> weight-space transport; and does authentic memory causally improve the next
> round of information acquisition?

RTCW is valuable only if it makes those questions identifiable. The paper
must compare against the relevant prior systems as capable native baselines,
not caricature them behind a common impoverished interface.

## Exact overlap and remaining distinction

### TMEM — parametric memory during agent rollout

Primary source: [Scaling Self-Evolving Agents via Parametric Memory](https://arxiv.org/abs/2606.04536).

Verified overlap:

- The agent maintains context, optional explicit memory, and online LoRA fast
  weights during a rollout.
- A memory-writing action distills accumulated history into grounded QA-style
  SFT supervision, then a lightweight update writes it into LoRA.
- The base policy is outcome-trained so its future extraction actions produce
  more useful online supervision; gradients stop through the online update.
- The paper compares no memory, summary memory, A-Mem-style retrieval, and
  TMEM on LoCoMo, LongMemEval-S, multi-objective search, and CL-Bench.
- Its own ablation finds QA supervision substantially better than raw
  next-token training, especially on LongMemEval-S.

Consequence: "agents can internalize their own experience into LoRA and alter
future behavior" is not our novelty. Neither is "the write format matters."

Remaining distinction to test, not merely assert:

- induced relational/causal structure rather than primarily answering or
  executing supervision extracted from history;
- target-blind prospective claims admitted only by later ordinary public
  outcomes;
- an identical admitted semantic set transported through text and LoRA, with
  the same resolver and explicit adapter/twin/binding interventions;
- post-context action requiring recurrent composition across old and new
  experience;
- a randomized memory-to-information-action-to-later-action cycle.

Required baseline: an outcome-trained direct-QA/TMEM-like LoRA arm using the
same public lifetime and resource accounting. Calling raw-context SFT
"TMEM-like" is insufficient.

### Auto-Dreamer — learned offline memory consolidation

Primary source: [Auto-Dreamer: Learning Offline Memory Consolidation for Language Agents](https://arxiv.org/abs/2605.20616).

Verified overlap:

- A fixed per-session writer creates typed memory entries.
- A learned offline consolidator selects a working region and source
  trajectory evidence, then rewrites it into a compact replacement set.
- Synthesized entries preserve source provenance; reported fan-in peaks at
  five source memories, so this is genuinely multi-source consolidation.
- The consolidator is GRPO-trained on downstream task utility plus a
  counterfactual random-masking term that rewards load-bearing, nonredundant
  entries.
- It is evaluated continually on ScienceWorld, ALFWorld, and WebArena against
  ten baselines including ReasoningBank, LightMem, Mem-alpha, and UMEM.
- The untrained rewriting pipeline already produces most of the bank-size
  reduction; learning adds task success but can lose location-specific detail.

Consequence: "dreams turn multiple episodes into smaller, useful memories"
is directly anticipated, including learning the consolidator on downstream
agent reward and testing it in actual action environments.

Remaining distinction to test, not merely assert:

- prospective hypothesis formation before the supporting outcome is visible,
  followed by chronological public-outcome admission;
- causal structure and hidden-binding transfer rather than free-text utility
  alone;
- explicit decomposition of proposal, admission, compilation, access, and
  recurrent goal-conditioned traversal;
- identical semantic text/LoRA transport and targeted causal swaps/cuts;
- independent causal-program roots and sealed post-native action evaluation;
- whether authentic memory changes what evidence the agent chooses to gather.

Required baseline: either run the released Auto-Dreamer design natively where
feasible, or implement a faithful region-rewrite/provenance/counterfactual-
utility comparator and label deviations. It should be a primary comparator,
not a related-work footnote.

### PEAM — parametric embodied skill consolidation

Primary source: [PEAM: Parametric Embodied Agent Memory through Contrastive Internalization of Experience in Minecraft](https://arxiv.org/abs/2605.27762).

Verified overlap:

- A slow deliberative LLM is paired with a fast multimodal MoE-LoRA skill
  executor.
- Successful trajectories and failure--correction pairs train per-category
  isolated adapters via behavioral cloning plus trajectory-level DPO.
- A hand-designed parameterization-worthiness score chooses what to
  consolidate; a failure-statistics trigger chooses when.
- The paper reports Minecraft long-horizon action performance, retention,
  latency, and comparisons with Voyager, Reflexion, retrieval agents, full
  fine-tuning, shared LoRA, and EWC.

Consequence: neither "experience becomes embodied action competence" nor a
sleep/consolidation framing is available as a broad novelty claim.

Remaining distinction to test:

- life-specific causal world knowledge and goal-conditioned traversal, rather
  than a fixed-category procedural reflex library;
- public-outcome grounding and counterfactual binding identity;
- a semantic authority layer shared by text and LoRA;
- new-evidence acquisition caused by memory, rather than only reuse of a
  learned skill.

Required baseline: a procedure-in-weights PEAM-like control becomes necessary
for any claim that LoRA is learning agency rather than just carrying facts.
Paper 1 should otherwise explicitly restrict itself to per-life semantic
transport.

### EVAF — selective parametric goal persistence after context unload

Primary source: [Memory Depth, Not Memory Access: Selective Parametric Consolidation for Long-Running Language Agents](https://arxiv.org/abs/2606.26806).

Verified overlap:

- The loop-drift protocol explicitly preserves retrieval while unloading
  working context, separating factual access from durable goal-conditioned
  behavioral influence.
- A surprise-times-valence gate selects events for sparse replay-backed LoRA
  updates; matched random gates test selection beyond write count.
- Actuation strength is varied independently and shown to be model-dependent;
  over-actuation can invert the selection comparison and increase
  contamination.
- Routed EVAF+RAG combines retrieval for facts with parametric persistence for
  goals.

Consequence: "memory in weights shapes behavior after context unload," the
access-versus-depth distinction, selective writes, and selection/actuation
factorization are not novel here.

Remaining distinction to test:

- acquisition of latent causal structure from the agent's own actions, not
  persistence of explicitly stated goals/preferences;
- target-blind prospective hypotheses and later public-outcome admission;
- recurrent composition that changes a novel held-out action;
- binding-identity interventions and an identical-semantic text/LoRA channel;
- a randomized effect on the next evidence-gathering action.

Required baseline: a matched selective event-to-LoRA arm with write count and
actuation calibrated independently. Raw or write-everything LoRA alone cannot
support a parametric advantage claim.

### Parametric Memory Law — rank/length capacity and exact-recall training

Primary source: [How LoRA Remembers? A Parametric Memory Law for LLM Finetuning](https://arxiv.org/abs/2605.30260).

Verified overlap:

- The paper sweeps LoRA rank and sequence length and fits a power law for loss
  reduction across semantic/random mixtures and phonebook data.
- It identifies token-level threshold failures under greedy decoding and
  proposes MemFT, which reallocates gradient budget toward unmastered tokens.
- A small linear-rule task separately measures seen-pair recall and unseen-pair
  generalization across ranks.

Consequence: a LoRA rank/capacity curve, exact-recall exposure recipe, or
simple rule-generalization result is not independently novel.

Remaining distinction to test:

- semantic utility is held-out multi-step action, not verbatim reconstruction
  or a single explicit algebraic rule;
- capacity is evaluated jointly with causal coverage, false-memory rate,
  retention, and recurrent read utility;
- writer/admission quality and substrate transport are experimentally
  separated.

Required baseline/design consequence: include uniform SFT plus a
hard-example/token-weighted write control in any capacity study, but keep rank
economics out of the core paper unless they explain action utility beyond
exact memorization.

### A-Mem — connected and evolving external memory

Primary source: [A-Mem: Agentic Memory for LLM Agents](https://arxiv.org/abs/2502.12110).

Verified overlap:

- New interactions become atomic notes with content, time, keywords, tags,
  contextual descriptions, embeddings, and links.
- An LLM creates links and can evolve prior memory descriptions as new
  experience arrives.
- Retrieval expands from a matched note to linked notes in the same semantic
  box.
- The paper evaluates multi-hop, temporal, open-domain, single-hop, and
  adversarial questions on LoCoMo and DialSim.

Consequence: "memories become a connected evolving graph and help multi-hop
reasoning" is already a published systems claim.

Remaining distinction to test:

- controlled action--outcome acquisition rather than dialogue QA;
- private causal bindings with target-identical twins;
- chronological support and false-memory accounting;
- held-out action under context cuts;
- exact interventions proving that the authentic learned content caused the
  action change.

Required baseline: native linked/A-Mem-like memory is the primary G4 efficacy
comparator. An atoms-only vector retriever cannot stand in for it.

## Revised contribution stack

The paper should be sold in this order:

1. **Benchmark/instrument:** RTCW, a randomized paired causal-lifetime
   benchmark that distinguishes recall, induction, binding, recurrent
   composition, and action effects after context expires.
2. **Causal architecture:** target-blind DREAM proposals, later public-outcome
   admission, deterministic SLEEP compilation, and recurrent goal-conditioned
   THINK traversal, with every component separately intervenable.
3. **Mechanistic result:** the phase diagram of where proposal, admission,
   access, traversal, and transport succeed or fail.
4. **Conditional transport result:** identical admitted semantics retain action
   value in an isolated per-life LoRA under recognition-assisted one-hop reads.
5. **Optional causal flywheel result:** authentic lifetime memory changes
   information gathering and thereby improves the next supported memory and
   sealed action over one cycle.

The main baseline comparison is against native connected/consolidating memory,
not NONE. The target-independent gold store and exact graph are ceilings. A
generator-aware program inducer is an honest symbolic reference and may win.

## Claim deletions and replacements

Delete or forbid:

- "first dreaming agent memory";
- "first online LoRA agent memory";
- "first memory consolidation for long-horizon agents";
- "first learned memory writer/consolidator";
- "external memory cannot connect or compress experience";
- "LoRA uniquely enables learned agency" without a PEAM-like procedural arm;
- "post-unload behavioral memory" without distinguishing EVAF;
- "a LoRA memory scaling law" or "rank controls generalization" without
  distinguishing Parametric Memory Law;
- "continues improving where existing systems saturate" until a separately
  powered and preregistered equivalence/crossover study passes.

Replace with the conditional sentences already registered in note 50. The
strongest currently defensible novelty hypothesis is not an ingredient claim:

> Existing work optimizes parametric memory, connected external memory, or
> learned consolidation. We test the complete causal pathway from public
> action--outcome experience to prospectively supported connected semantics to
> post-context multi-step action, while independently intervening on semantic
> content, access, traversal, and weight transport.

That sentence is still a hypothesis until the complete primary literature
table is finished and the RTCW evidence passes.

## Immediate design consequences

1. Keep G1 small: it establishes only that supplied knowledge can alter the
   exact recurrent action interface.
2. Before G2 implementation, add Auto-Dreamer-style region rewriting and a
   native A-Mem-like linked store to the frozen comparator contract.
3. G2 must score prospective-hypothesis recall, chronological admission
   precision, connected causal coverage, and action value separately.
4. G3 must be same-corpus text versus LoRA. Raw-event and outcome-trained QA
   LoRA are mandatory controls; a matched selective EVAF-like LoRA control is
   mandatory for any post-unload behavioral comparison.
5. Defer agency/loop-LoRA claims unless a PEAM-like procedure-in-weights arm is
   actually run.
6. Treat G5 as a separate randomized trial. It is the only stage that tests
   the self-improving action-data flywheel rather than static memory utility.
