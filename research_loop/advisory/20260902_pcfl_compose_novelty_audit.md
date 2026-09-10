# PCFL-Compose novelty audit

Date: 2026-09-02  
Scope: primary-source search of the proposed factorized, noncommutative
action-world claim against papers, conference pages, and two directly relevant
software artifacts. This is a related-work/novelty audit, not an architecture
ratification or execution authorization.

## Bottom line

I found no single prior work that combines all of the proposed ingredients:

1. a fixed-source life with independently growing, hidden per-life action
   operators;
2. operator identification from action/outcome experience rather than an
   announced task descriptor;
3. order-sensitive (noncommutative) multi-operator action composition;
4. target-blind consolidation into comparable text, graph, and LoRA substrates;
5. unseen compounds evaluated after the raw life exceeds usable context; and
6. causal twin/binding interventions plus separate new/old/cross-era action
   scores.

That conjunction is a credible benchmark/causal-measurement contribution.
It is not a cleanly novel LoRA algorithm, first parametric agent memory, first
lifelong skill library, or first compositional action benchmark. Two
contemporaneous artifacts make an unqualified “first noncommutative action
world” or “first parametric-vs-context composition benchmark” claim unsafe:
[FactWorld](https://github.com/ianbarber/factworld/) and
[ActionShift](https://github.com/Archerkattri/actionshift). They are not, on the
available pages, peer-reviewed papers, but they are direct public artifacts and
must be cited or explicitly distinguished if they remain available at release.

The paper is ICLR-credible only with a narrow thesis: **PCFL-Stream/Compose is
a controlled, target-blind benchmark that identifies how compilation, memory
substrate, and bounded resolver use affect acquisition, retention, and
cross-era action as independent causal information grows beyond context.**
The current broad “self-learning agent improves throughout life” framing is
not supported by a fixed immutable source life.

## Closest prior work

| Prior source | What it already establishes | Exact PCFL delta; required concession |
|---|---|---|
| [TMEM, *Scaling Self-Evolving Agents via Parametric Memory*](https://arxiv.org/abs/2606.04536) | Online cumulative LoRA/fast-weight memory; extraction actions create supervision; updates change subsequent policy behavior within a rollout; outcome-trained extraction and CL-Bench/LoCoMo/LongMemEval evaluation. | PCFL can test offline/cross-episode per-life persistence, post-context lifetime curves, new/old/cross-era action, identical-corpus text-versus-LoRA transport, and authentic/twin binding cuts. It cannot claim first action-changing fast weights or first outcome-shaped parametric writing. Direct-QA/instruction-response LoRA must be a core baseline. |
| [PEAM, *Parametric Embodied Agent Memory through Contrastive Internalization of Experience in Minecraft*](https://arxiv.org/abs/2605.27762) | Embodied parameter-resident skills; MoE-LoRA routing/isolation; failure/correction contrastive consolidation; a worthiness score and self-triggered consolidation; held-out Minecraft skill execution and forgetting tests. | PCFL's advantage is identification (frozen common lives, exact hidden entropy, age/depth, external-versus-parametric comparison, binding interventions), not embodiment or consolidation. Do not claim first embodied parametric memory, first failure-aware consolidation, or first sleep-inspired embodied memory. |
| [A-MEM, *Agentic Memory for LLM Agents*](https://arxiv.org/abs/2502.12110) | Agent-driven Zettelkasten-style notes with indexing, links, and memory evolution. | A-MEM is the natural linked external-memory comparator. Run its native interface as well as a common-channel version; compare it on the same life/targets and disclose its indexing/retrieval state. |
| [Voyager, *An Open-Ended Embodied Agent with Large Language Models*](https://arxiv.org/abs/2305.16291) | Lifelong Minecraft exploration, automatic curriculum, executable compositional skill library, environment feedback/self-verification, and transfer of skills to a new world. | PCFL adds hidden per-life causal bindings, certified depth/age, post-context acquisition and retention, text/graph/LoRA substrate attribution, and twin interventions. Voyager owns the naturalistic on-policy skill-library territory; PCFL cannot claim a stronger self-directed learning loop from a fixed source stream. |
| [LifelongAgentBench](https://arxiv.org/abs/2505.11942) | Interdependent skill-grounded tasks over persistent Database, OS, and Knowledge Graph environments; reproducible labels; experience replay and context-length analysis. | PCFL's controlled synthetic value is independent causal entropy, presealed targets/twins, operator-binding attribution, order-sensitive compounds, exact target-only Bayes/graph ceilings, and matched text/LoRA arms. This is a benchmark competitor, not something to omit from comparison. |
| [CL-Bench, *Continual Learning Bench*](https://arxiv.org/abs/2606.05661) | Six expert-validated real-world domains with shared latent structure, sequential experience, verifiable rewards, and a gain metric intended to separate learning from base capability. | CL-Bench is the closest benchmark-level competitor for “agents genuinely improve from experience.” PCFL's delta is mechanistic control and causal identification, not breadth or realism. Include its framing in related work and avoid “first continual-learning benchmark” language. |
| [MemoryAgentBench](https://arxiv.org/abs/2507.05257) | Incremental multi-turn benchmark covering retrieval, test-time learning, long-range understanding, and selective forgetting, with context/RAG/external-memory baselines. | PCFL evaluates executable action and multi-hop construction under hidden operator bindings, not primarily memory QA. Retain MemoryAgentBench as a memory-quality baseline/reference, not as a substitute for action validity. |
| [LongMemEval](https://arxiv.org/abs/2410.10813) | Long-term interactive chat memory: extraction, cross-session/temporal reasoning, updates, and abstention; 500 curated questions and indexing/retrieval/reading analysis. | Strong long-memory precedent, but chat QA has no hidden action operators, intervention outcomes, or action-return measure. Use it to reject claims of first long-term interactive-memory benchmark. |
| [gSCAN](https://arxiv.org/abs/2003.05161) | Grounded grid-world language/action commands and systematic compositional generalization, including novel modifier/verb combinations. | PCFL's hidden per-life mappings are learned from outcomes and persist across a stream; gSCAN generally evaluates command compositionality, not lifetime memory or substrate transport. Cite as the closest language-grounded composition lineage. |
| [CompoSuite](https://arxiv.org/abs/2207.04136) | 256 simulated manipulation tasks formed by robot/object/objective/obstacle factors; compositional multi-task RL and unseen task combinations. | PCFL varies latent causal bindings within a life and tests memory across time/context, rather than giving task descriptors and recombining known robot-task factors. Include as a compositional-RL baseline/precedent. |
| [CoDE, *Environment Generation for Zero-Shot Compositional RL*](https://arxiv.org/abs/2201.08896) | Compositional MiniGrid/gMiniWoB task generation, dependency-graph curricula, and zero-shot composition. | PCFL is not an automatic curriculum or generator-learning method; its contribution is controlled per-life information accumulation and memory substrate attribution. |
| [TextWorld](https://arxiv.org/abs/1806.11532) and [ALFWorld](https://arxiv.org/abs/2010.03768) | Generated/text-based interactive environments and abstract-to-embodied policy transfer with multi-step action feedback. | These establish the environment/tooling lineage, but do not provide PCFL's hidden operator identification, cross-era memory cuts, or text/graph/LoRA comparison. |

### Priority-risk public artifacts

* [FactWorld](https://github.com/ianbarber/factworld/) explicitly reports a
  non-abelian pointer-permutation (“S5 word problem”) state-tracking family,
  a state×binding composition family, deferred readout, and parametric versus
  in-context variants. This is near-fatal to a bare claim that PCFL is the
  first benchmark for order-sensitive/noncommutative composition or for
  parametric-versus-context composition. The defensible distinction is that
  PCFL must add hidden per-life operator semantics inferred from observed
  action/outcome transitions, target-blind per-life consolidation into text,
  graph, and LoRA, post-context lifetime scaling, and causal twin/binding
  interventions. If PCFL does not implement and verify those distinctions,
  the benchmark novelty is weak.

* [ActionShift](https://github.com/Archerkattri/actionshift) makes a hidden
  compositional robot action-interface contract (permutation, sign, scale,
  target convention, frame, lag, gripper) the object of adaptation, with
  bounded probes, belief/oracle controls, unseen-composition splits, and fixed
  task dynamics. This is near-fatal to “first hidden compositional action
  contract/interface” language. PCFL differs by making operators world
  semantics learned from outcome-bearing experience and by testing durable
  cross-episode composition and memory substrates; ActionShift adapts an
  already competent policy to hidden wiring and does not, on its public
  description, test lifetime text/graph/LoRA consolidation. Cite and run a
  conceptual distinction table; do not silently compete for the same priority.

## Exact novelty verdict

The strongest novelty is **the controlled causal conjunction**, not any single
component:

```
same immutable source life
  -> target-blind compiler
  -> text / exact graph / LoRA treatment
  -> bounded typed reads
  -> unseen action compounds
  -> new / old / cross-era value
  -> authentic-vs-twin and decisive-binding interventions
```

The benchmark is materially different from long-context or memory-QA suites
only if independent causal information grows (not merely tokens), target and
twin manifests are presealed before compiler success, depth is graph-certified
with shorter proof routes excluded, and action scoring cannot be reduced to a
target-signature lookup. The noncommutative claim requires an explicit
commutation/shuffle control: reversing two learned operators must change the
outcome, and a commutative surrogate must fail the order-sensitive targets.

The fixed-source design has a necessary limitation: it is off-policy with
respect to evidence acquisition. It can identify whether memory changes later
action, but cannot establish the full action → new evidence → revised memory →
better later action flywheel. Reserve “on-policy self-improvement,”
“self-learning,” “autonomous exploration,” and “continual forever” for a later
study with arm-specific streams and a separate policy-selection intervention.

## Fatal risks and mandatory repairs

1. **FactWorld overlap.** Add explicit FactWorld comparisons: non-abelian
   state-only, binding-only, state×binding, and PCFL hidden-operator cells;
   answer-only versus outcome-supervised traces; context versus text/graph/LoRA.
   State whether the PCFL source stream contains genuinely new entropy beyond
   FactWorld's fixed permutation/binding families.
2. **ActionShift overlap.** Add hidden-interface/action-contract language to
   related work and say whether PCFL's operators are semantic transitions or
   merely an action ABI. Include a no-memory bounded-probe/action-interface
   control where feasible.
3. **LoRA novelty overclaim.** TMEM and PEAM own action-changing parametric
   memory territories. PCFL must include direct-QA LoRA, raw-history LoRA,
   shuffled/dreamless LoRA, same-corpus text, recognition-assisted versus
   unaided LoRA, clean-base candidate-only, wrong/twin adapter, and an exact
   sufficient-statistic graph/program.
4. **Reader leakage.** A recognition/index/candidate universe can carry the
   answer independently of the adapter. Report candidate-only clean-base,
   matched candidate-assisted text, explicit-index, wrong-adapter, and
   unaided-generative readers under a constant atomic-read cap and a
   sublinear-in-life candidate-work audit.
5. **Target/compiler selection.** Freeze total target allocation before any
   support, compilation, or realized score. Unsupported and uncompiled targets
   stay in the denominator; the compiler must not see evaluation goals or
   descendants of those goals.
6. **Causal memory attribution.** Citation masking alone is not a LoRA
   intervention. Use whole-life authentic-versus-twin adapters on primary
   cells; use paired decisive-binding versus equal-size sham cuts for a
   smaller panel; require action changes in the authentic direction.
7. **Pseudoreplication and resource confounding.** The independent unit is a
   world-life/twin pair, not target calls or checkpoint rows. Use disjoint
   calibration/confirmation roots, powered pair counts (the existing four
   DEV pairs are not evidence), and report canonical/training/adapter/index
   bytes, repetitions, compiler/training/query calls, latency, and action
   amortization.
8. **Benchmark toy-ness.** Release deterministic generator, renderer,
   oracle/certifier, presealed manifests, target/twin byte-equality tests,
   exact target-only Bayes controls, depth certificates, graph-edge deletion,
   shortcut predictors, and executable evaluation code. Otherwise call it a
   controlled assay rather than a benchmark contribution.

## Baseline minimum for a credible ICLR study

At matched model, action, write, resolver, and read budgets, the primary core
should include: (i) no persistent memory plus exact target-local Bayes ceiling;
(ii) honest native context and frozen truncation; (iii) raw episodic RAG and a
strong linked/A-MEM-native memory; (iv) exact public sufficient-statistic
graph/program; (v) TMEM-style direct-QA LoRA; (vi) target-blind compiled text;
(vii) identical-corpus compiled LoRA; (viii) raw-history, shuffled/dreamless,
recognition-assisted, unaided, wrong/twin-adapter, and candidate-only readers;
and (ix) batch post-hoc SFT at sentinel checkpoints.

Use one pre-native point and at least three strictly post-native checkpoints.
Report independent new-cohort acquisition, earliest-cohort retention, and
cross-era composition at each point, plus supported/compiled/retrieved/action-
usable coverage and minimal sufficient-statistic bits. A single terminal score
cannot establish continual acquisition or retention.

## ICLR credibility and recommendation

**Credible accept path:** benchmark contribution primary, causal mechanism
contribution secondary, systems/LoRA contribution conditional. The paper can be
strong if it shows (a) monotone independent causal information, (b) target-blind
compiled text improves action under a bounded reader and binding cuts, (c)
identical-corpus LoRA transports life-specific bindings beyond clean-base and
direct-QA controls, and (d) acquisition, retention, and cross-era action remain
useful after context overflow with a resource frontier.

**Not credible:** a new-LoRA or “first parametric memory” paper; a claim that
text/graph/LoRA itself proves compression; autonomous graph/schema discovery;
an on-policy self-improvement claim from a common scripted life; or a generic
SOTA/saturation claim based on a terminal endpoint. PCFL-Schema, learned
scheduler/critic, and the complete action–experience flywheel should remain
deferred.

Recommendation: proceed only as **“PCFL-Stream: Causal Evaluation of Compiled
Per-Life Memory Beyond the Context Window”**, with FactWorld and ActionShift
explicitly audited in the final related-work and baseline tables. If the
operator-inference, order-sensitivity, target-blindness, and causal binding
interventions are not all implemented, narrow the contribution to a memory
transport assay and do not claim a new factorized noncommutative action-world
benchmark.

