# One-parent/one-child closest-work fresh audit v1

**Date:** 2026-09-07  
**Status:** read-only scientific advisory; no experiment, implementation, or
frozen-source change was authorized or performed  
**Verdict:** **the broad “per-life parametric learning for acting agents” lane
is occupied. The defensible novelty is the causal developmental question:
whether target-blind process parenting changes the later marginal benefit of
an individual child's own deployment-time writes after the parent and all
parental text are removed.**

This distinction is decisive. TMEM already changes an agent's future behavior
with online LoRA written from its accumulated experience. PEAM already
internalizes embodied success and failure--correction trajectories into
category-isolated LoRA skills. EVAF already studies selective LoRA
consolidation that survives working-context unload while retrieval remains
available. LEAFE already distills reflective recovery into an acting policy
while removing the reflection at test time. Several frozen-weight systems
already learn online from success/failure feedback by evolving structured
external text. The proposed one-parent factorial can still ask a new and
interesting question, but the paper cannot sell any of those ingredients as
new.

The current frozen v2 packet is a **proposal**, not a result. This audit is
therefore a novelty and comparator audit of the intended experiment, not an
endorsement of any empirical claim.

## 1. Exact audited target

The closest-work boundary below uses the v2-frozen design, not every statement
in the unconformed manuscript:

- one reset, frozen Qwen2.5-32B parent supplies only closed-surface process
  corrections on target-blind Codebreaker/RuleShift practice;
- one Qwen2.5-7B child either receives that parent edge (`P`) or dose-matched
  own practice without semantic parent lessons (`U`);
- three cumulative, clean-base, response-only childhood LoRA fits produce the
  parented and unparented entry checkpoints;
- the parent, nursery transcript, correction text, and prohibited childhood
  state are deleted before a fresh CompilerGym lifetime;
- each childhood checkpoint is forked with deployment-time LoRA writes off/on,
  giving `P0/P1/U0/U1`; `R0` is a raw-checkpoint, fit-free public reference;
- all deployment services have isolated copies of the same
  `ACTIVE_TEXT_FIXED` system: frozen adapter-free reflection and deterministic
  curation into a typed, evidence-linked playbook, followed by pinned hybrid
  retrieval;
- `P1/U1` additionally rebuild cumulative rank-8 LoRA from the clean base at
  16/32/48 wake-program cuts using admitted native `THINK_TO_ACT` and
  `DREAM_STATE` response suffixes grounded in public outcomes;
- the primary estimand is the root-level interaction
  `D = (P1-P0) - (U1-U0)` over entry-adjusted lifetime gAUC. `P1-P0` is the
  parented child's total closed-loop write-enablement effect; `P1-R0` is only a
  full-developmental-package public contrast.

Two attribution boundaries follow directly. First, because enabling LoRA
writes changes later actions and therefore the later on-policy text store,
`P1-P0` is a **total effect of enabling the recurrent write loop**, not proof
that the relevant information is carried in weights. Second, roots resample
program/task randomness under one fixed parent policy and one fixed child
checkpoint; they do not sample parents or child models. A positive interaction
is conditional evidence for this fixed system, not a population-level
parenting effect.

## 2. Exact mechanism comparison

| Work | Persistent learned state / actor | Write signal and write form | Update cadence and boundary | What it already establishes | Exact remaining boundary for the one-parent v2 study |
|---|---|---|---|---|---|
| **One-parent v2 target** (proposal) | Common external typed playbook in every arm; cumulative per-life rank-8 LoRA only in `P1/U1`; the acting child is therefore repeatedly changed in write-on arms | Public action outcome plus prediction error/revision; accepted native response suffixes; cumulative response-only SFT with rehearsal | Three childhood fits, then deployment fits at 16/32/48 programs; deployment parent and nursery state deleted | Nothing yet; no sealed result exists | Tests whether a target-blind parent intervention changes the *marginal causal effect* of later personal writes, conditional on one fixed parent/child pair and task-root distribution |
| [**TMEM: Scaling Self-Evolving Agents via Parametric Memory**](https://arxiv.org/html/2606.04536v1) | Explicit memory plus online LoRA fast weights `Delta_t`; later actions use the adapted policy | The agent emits grounded QA-style supervision when a context-budget trigger fires; an outer GRPO loop outcome-trains the base/extraction policy; SVD-initialized LoRA subspace | Multiple cumulative updates inside one rollout; working context is cleared at a trigger; fast state is rollout/episode scoped in the reported protocol | Online experience-to-LoRA memory, repeated fast-weight updates, action-relevant behavior change, and an outcome-trained writer/extractor are already occupied | V2 differs in cross-program lifetime persistence, public typed-action provenance, and especially the prior-parenting-by-write factorial. It cannot claim first online/personal LoRA learning. **This is the closest parametric systems baseline.** |
| [**PEAM: Parametric Embodied Agent Memory**](https://arxiv.org/html/2605.27762v2) | Slow deliberative LLM plus a fast Qwen3-VL-8B MoE-LoRA policy with physically isolated category adapters | Verified successful/corrected trajectories; behavioral cloning plus preference/contrastive training on failure--correction pairs; parameterization-worthiness and self-triggered consolidation decide what/when | Sequential skill consolidation in Minecraft; adapter isolation is the forgetting defense | Embodied parameter-resident skills, failure as a first-class training signal, selective consolidation, self-triggering, and forgetting mitigation are occupied | V2's delta is target-blind parental preparation and factorial identification on a later environment, not embodied or failure-aware LoRA learning. A PEAM-like arm becomes required if procedural-skill or forgetting superiority is claimed. |
| [**EVAF / Memory Depth, Not Memory Access**](https://arxiv.org/html/2606.26806v1) | Retrieval remains intact; a small LoRA store carries durable goal-conditioned tendencies | Surprise-times-valence gate admits events to a buffer; buffer plus replay and L2 anchoring update LoRA; matched random gates and fixed-step actuation controls separate selection from write strength | Sparse online writes over 200-event streams, with explicit working-context unload | Selective parametric consolidation after context unload, retrieval/weights complementarity, matched-sparsity controls, and selection--actuation coupling are occupied (principally controlled synthetic probes, with 7B diagnostics) | V2 has public action outcomes and a parent intervention, but its prospective admission/rehearsal is not by itself a novel selective-write story. EVAF is the closest control if selection or “memory depth” is load-bearing. |
| [**Macaron-V1**](https://arxiv.org/html/2608.09819v2) | Frozen base plus routed specialist LoRAs and a versioned harness; model--harness successor revisions receive parameter updates | Executable trajectories are externally evaluated and selected for later specialist-adapter training; harness/configuration search is also versioned | Offline/release-style recursive successor cycle rather than one individual's online lifetime | The labels “experiential intelligence,” model--harness co-design, versioned experience-driven successor updates, response-only training infrastructure, and extensible LoRA specialists are already in use | Its report explicitly leaves compounding continual-learning gains open and does not test parenting. Cite it to avoid claiming the broad experiential-agent or versioned-LoRA vision; it is not a substitute for TMEM in the same-lifetime baseline. |
| [**LEAFE: Internalizing Agency from Reflective Experience**](https://arxiv.org/html/2603.16843v1) | Acting policy updated by SFT; explicit reflective experience is absent at inference | Periodic reflection chooses rollback points and actionable diagnoses; reset/replay produces recovered branches; successes and counterfactual experience-to-policy pairs train corrected actions from the original history | Batch two-stage post-training over collected trajectories, followed by evaluation | Reflection-to-policy internalization, rollback/recovery, behavior rehearsal, counterfactual corrections, and removing the reflection scaffold at test time are occupied | V2 is recurrent within life and asks a parenting interaction. A terminal descriptive LEAFE-style row cannot support superiority; a matched batch control is needed for claims about periodic consolidation or the compiler. |
| [**Agent Learning via Early Experience**](https://arxiv.org/html/2510.08558v3) | Acting model is updated by supervised mid-training | At expert-visited states the agent proposes alternative actions, executes them, and uses future states; variants train an implicit world model or reflection/rationale plus expert action | Batch/mid-training, then downstream/OOD evaluation | Learning from executed alternatives and their future consequences, environment-grounded reflection, and early-experience agent training are occupied | It relies on expert-trajectory anchoring and is not personal online lifetime learning. It is a required citation and a useful batch/oracle boundary, not necessarily a faithful same-domain baseline. |
| [**Learning on the Job**](https://arxiv.org/html/2607.22157v1) | Frozen actor plus an evolving Spark external-memory store of compact natural-language rules | Post-episode one-bit verdict or verified correction; same-agent reflection writes one validated `WHEN--THEN` rule, with supported values, merge/quality checks, feedback, and later agent-chosen retrieval | Store starts empty and persists across four spaced trials per task in tau-bench Banking | Continual improvement of tool-using frozen-weight agents from ordinary deployment outcomes/corrections, on top of static RAG, plus retention and cross-model transfer | This is now the closest public precedent for `ACTIVE_TEXT_FIXED`, closer than a generic “MemoPilot/Evo-Memory” label. V2's typed deterministic curator and evidence-link rules are an implementation choice, not a new category. Compare to or explicitly distinguish Spark's released harness. |
| [**MemoPilot**](https://arxiv.org/html/2606.08656v1) | Separate trainable memory model evolves a structured textual state; player/actor stays frozen | Identification--Maintenance--Guidance memory operations; the updater is trained with multi-turn GRPO using later-game reward | Online memory update between games/tasks | A learned, reward-optimized test-time memory updater and adaptive player improvement are occupied | `ACTIVE_TEXT_FIXED` uses a frozen prompted reflector plus deterministic curator, not a learned updater. It may be more auditable, but cannot be called stronger in general without evidence. Exact reproduction is not essential to a narrow parenting claim. |
| [**ACE**](https://arxiv.org/html/2510.04618v3) | Model weights remain fixed; an itemized context playbook with metadata evolves | Generator, Reflector, and Curator append/update/deduplicate granular bullets using environment feedback | Online sample-by-sample or offline context adaptation | Incremental structured playbook evolution, feedback-grounded curation, and avoiding monolithic context collapse are occupied | `ACTIVE_TEXT_FIXED` is intentionally ACE-like, with a stricter closed schema/provenance/retriever. That may strengthen identification but is not broad algorithmic novelty. |
| [**ReasoningBank**](https://arxiv.org/html/2509.25140v2) | External structured memory of title/description/content; acting weights fixed | Self-judged successes and failures yield reusable reasoning strategies; memories are retrieved and consolidated by addition; MaTTS expands experience generation | Closed-loop test-time accumulation across streaming tasks | Online lessons from both success and failure, structured reasoning memory, and later action improvement are occupied | V2's public verifier and typed evidence binding are stricter than self-judgment, but “process lessons from experience” and an evolving external playbook are not new. |
| [**Evo-Memory / ReMem**](https://arxiv.org/html/2511.20857v2) | External memory evolves; model weights remain unchanged | ReMem exposes Think/Act/Refine operations; Refine prunes and reorganizes accumulated memory in real time | Streaming tasks with online memory evolution | A benchmark for agent test-time learning with self-evolving memory and a real-time refine operation are occupied | Supports the frozen-weight external-memory comparator, not the parametric novelty. `ACTIVE_TEXT_FIXED` must not be described as an exact ReMem reproduction. |
| [**FLEX**](https://arxiv.org/html/2511.06449v2) | Frozen actor guided by a hierarchical structured experience library; auxiliary updater evolves the library | Forward exploration produces successes/failures; updater distills and revises semantic strategies; retriever injects relevant experience | Interleaved experience-library growth and reuse across tasks | Gradient-free continuous agent evolution, structured experience-library scaling, and experience inheritance across agents are occupied | It is external rather than parametric and does not test a teacher-induced change in later learnability. It blocks broad “first continuously evolving agent/experience inheritance” language. |
| [**When Continual Learning Moves to Memory**](https://arxiv.org/html/2604.27003v1) | Frozen actor plus growing retrieved external memory | Raw trajectories versus abstract insights; aggregate/individual units and task/step retrieval are crossed | Sequential A-then-B task streams in ALFWorld and BabyAI | Forward/backward transfer, forgetting, retrieval pollution, and a stability--plasticity tradeoff in external memory are already measured directly | V2 must cite this for its active-text stability/transfer framing. Sharing active text across arms controls access but does not make retrieval-side interference disappear. |
| [**CL-Bench**](https://arxiv.org/html/2606.05661v1) | Benchmark admits arbitrary stateful mechanisms; evaluated systems include accumulated context and dedicated memory | Earlier real-world task instances expose feedback about hidden shared latent structure; a gain metric contrasts stateful with stateless performance | Sequential schedules across six domains, sometimes with concept drift | A benchmark expressly designed to measure whether agents improve from experience, with learning curves/gain and stability--plasticity analyses, already exists | CompilerGym can offer tighter causal control and the parenting factorial, not “the first benchmark/test of genuine continual agent learning.” A CL-Bench transfer experiment would materially improve external validity but would require a new plan. |

### Ordering by closeness

For the **parametric writer**, the order is TMEM, PEAM (for procedural action),
EVAF (for selective carryover), then LEAFE/Early Experience (batch
internalization). For the **common active-text system**, the order is Learning
on the Job, ReasoningBank/ACE, ReMem, MemoPilot, FLEX, and When Continual
Learning Moves to Memory. Macaron-V1 is a terminology and system-vision
neighbor, but its reported evidence does not replace an online same-lifetime
parametric comparator.

## 3. What is genuinely novel, and what is not

### Defensible novelty, if the sealed result is positive

1. **The developmental causal estimand.** None of the audited closest works
   crosses a prior, target-blind process-teaching intervention with later
   deployment-time write enablement and makes the interaction—not final
   performance—the primary estimand. The clean claim is that parenting changed
   the *marginal responsiveness* of this child system to its own later
   experience.

2. **Separation of starting competence from later learning.** The dose-matched
   `P0/P1/U0/U1` fork can distinguish a better entry checkpoint (`P0-U0`),
   unparented continual adaptation (`U1-U0`), the parented write effect
   (`P1-P0`), and their interaction `D`. That identification structure is much
   more novel than the LoRA writer.

3. **A tightly bounded parent intervention.** A parent restricted to
   target-blind process corrections, admitted only after separate child
   application and public support, followed by complete parent/nursery-text
   deletion, is a distinctive operationalization of developmental teaching.
   The claim must remain “we test this intervention,” not “we introduce
   machine parenting” or “parenting teaches meta-intelligence” in general.

4. **Protocol rigor as an enabling contribution.** Native-response provenance,
   typed action-dispatch binding, public-outcome admission, clean-base
   cumulative rebuilds, common active text in every cell, isolated ledgers,
   and transaction/certificate gates form a useful identification bundle.
   Several ingredients have precedents; the bundle is valuable primarily
   because it makes the causal test interpretable.

5. **Conditional fixed-system evidence.** With one fixed parent policy and one
   fixed child checkpoint, a successful run can establish reproducibility over
   the registered program/task-root distribution. It can be a compelling
   mechanistic case study. It cannot estimate heterogeneity over parents,
   children, base models, or domains.

### Occupied or non-novel claims

- a deployed agent learning from its own subsequent experience;
- repeated online or periodic LoRA/fast-weight updates that affect later
  actions;
- parametric memory, LoRA as memory, context-unloaded parametric carryover, or
  an explicit-memory-plus-parametric-memory hybrid;
- outcome-shaped or selective experience writing;
- learning from successes, failures, corrections, rollback, or recovered
  trajectories;
- reflection/scaffold fading or removing reflection text at test time;
- rehearsal, replay, anchoring, adapter isolation, or stability--plasticity
  management;
- a structured, linked, curated, or evolving textual experience library;
- frozen-weight agents that improve online from one-bit deployment verdicts or
  verified corrections;
- forward transfer, backward retention, forgetting, learning curves, gain over
  a stateless system, or continual-agent benchmark framing;
- “self-evolving agent,” “continuous agent evolution,” “experiential
  intelligence,” “experience inheritance,” or “model learns from life” as
  novelty labels;
- `Think`, `Dream`, or `Sleep` as a scientific mechanism. In v2 these are
  named interfaces/write phases, not evidence of cognitive analogues;
- deterministic schema curation, evidence links, or a hybrid retriever as a
  stand-alone algorithmic contribution; and
- `P1>R0` as evidence that parenting caused better learning. It is a
  full-package contrast with unequal childhood histories and fits.

## 4. Required baselines and citations

### A. Non-negotiable for an ICLR paper retaining a parametric-method claim

1. **TMEM-style direct-QA LoRA.** Run a bounded functional reimplementation on
   the same CompilerGym life, with the same actor, task opportunities, public
   evidence, fit cuts, LoRA parameter/step budget, and active-text affordance.
   The writer should render grounded atomic question/instruction--answer targets
   directly from the public history. If the original outcome-trained extraction
   policy and SVD-fixed subspace cannot be reproduced, label the arm
   `TMEM-style`, enumerate omissions, and do not imply an exact reproduction.
   Without this arm the paper can still test parenting, but cannot argue that
   its per-life writer advances the closest parametric method.

2. **Naive/native continual LoRA.** Train the same LoRA at the same cuts and
   optimization budget from mechanically rendered raw/native successful and
   corrected events, without `DREAM_STATE` abstraction. This is the necessary
   test that the compiler adds value beyond ordinary continual SFT. `U1` is not
   this baseline: it still uses the proposed compiler.

3. **A matched batch internalization control.** Consolidate the same available
   lifetime corpus once at the terminal cut under the same total gradient/token
   budget. LEAFE is the closest conceptual precedent. The current v2
   descriptive-only terminal row can contextualize but cannot support
   superiority. This control is mandatory for claims that periodic writes,
   Dream/Sleep staging, or the proposed schedule matter; it can be omitted only
   if the paper explicitly makes no such comparison.

4. **A credible frozen-weight online-memory comparator.** At minimum compare
   `ACTIVE_TEXT_FIXED` against raw/full-history and static retrieval, and
   benchmark its learning curve/use/retention against one released functional
   system closest to the domain. Learning on the Job/Spark is now the most
   similar feedback-to-rule pipeline; ReasoningBank or ACE is a reasonable
   secondary alternative. Passing homegrown semantic/use certificates permits
   “validated under our contract,” not “state of the art” or “stronger than
   learned memory systems.”

5. **Keep the full parenting factorial.** `P0/P1/U0/U1` with dose-matched
   childhood and entry adjustment is not optional. Removing `U0/U1` collapses
   the only genuinely novel causal question into a final-score comparison.

### B. Required conditionally by the claims

- **EVAF-style matched selective LoRA** is required if prospective admission,
  selective consolidation, write sparsity, context-unloaded “depth,” or
  selection--actuation is claimed as a mechanism. Match selected-row count and
  inner-update strength, not only nominal LoRA rank.
- **PEAM-style failure--correction procedural LoRA** is required if the paper
  claims first/better procedural skill internalization, embodied agency in
  weights, or forgetting mitigation. Otherwise PEAM is a prominent citation
  and boundary, not a mandatory exact Minecraft reproduction.
- **Adapter/carrier intervention with a fixed downstream store/history** is
  required for a claim that information is carried parametrically. Write-on vs
  write-off alone is insufficient because LoRA changes future trajectories and
  external memory. Removing/swapping the adapter while holding the downstream
  playbook and query fixed is the minimum carrier assay.
- **A second environment or CL-Bench task** is required for cross-domain or
  general continual-agent claims. CompilerGym alone licenses a controlled
  compiler-domain result.
- **Independent parent/child checkpoints** are required for a population-level
  parenting or general learning-to-learn claim. More task roots from the same
  checkpoints do not supply that independence.

### C. Required citations even when not reimplemented

The related-work section and mechanism table should, at minimum, cite TMEM,
PEAM, EVAF, LEAFE, Early Experience, Learning on the Job, MemoPilot, ACE,
ReasoningBank, Evo-Memory/ReMem, FLEX, When Continual Learning Moves to Memory,
CL-Bench, and Macaron-V1. The paper should distinguish exact reproductions,
functional approximations, and literature-only comparisons. The current
`references.bib` contains only LEAFE, Early Experience, MemoPilot, and
Evo-Memory and is materially incomplete.

## 5. Dangerous overclaims in the current manuscript

| Current location / idea | Risk | Required repair |
|---|---|---|
| Title: **“Experience Models: Per-Life Parametric Learning for Acting Agents”** | Reads as the invention of a category already directly occupied by TMEM, PEAM, EVAF, and Macaron's broader experiential-intelligence framing | Put the parent-induced change in later learnability in the title; make the parametric loop the measured substrate, not the novelty claim |
| Abstract lines 17--18: post-training “does not teach one deployed agent to improve from its own subsequent life” | False as a field-level premise after TMEM/PEAM, and frozen-weight systems such as Learning on the Job also improve across deployment trials | “Existing parametric and external-memory systems enable deployment-time learning; we ask whether a prior process teacher can change the later marginal value of such learning.” |
| Introduction lines 41--42: “can one deployed agent convert its own ... experience into a persistent parametric change that improves how it acts later?” | Valid as a question historically, but TMEM already answers the broad form and PEAM answers an embodied version | Replace with the parenting-by-write interaction question; cite TMEM in the first paragraph |
| Contribution 1: one-parent protocol “teaches process-level thinking” | Before a positive transfer interaction, this states the intended intervention as an accomplished latent construct | Say “operationalizes target-blind process correction” and reserve “taught later learning” for a positive registered `D` plus rung conditions |
| Contribution 3: provenance-bound Think--Dream--Sleep architecture | The names and compiler bundle do not create strong algorithmic novelty; LEAFE, PEAM, TMEM, ACE, and Learning on the Job cover its ingredients | Present it as the controlled substrate required to run the causal study, then compare raw/native, TMEM-style, and batch writers if method superiority is desired |
| “Model meta-intelligence” at lines 83--86 | A positive interaction for one fixed teacher/child/domain may reflect compatibility of childhood SFT with the later writer; it does not demonstrate broad meta-intelligence | Prefer “parent-induced change in within-system deployment learning.” If the term remains, qualify it explicitly as an operational label conditional on this fixed pair and domain |
| “Strong active-text control” at lines 109--120 | Internal certificates test local fidelity/use/headroom but do not establish competitiveness with Spark, ReasoningBank, ACE, ReMem, or MemoPilot's learned updater | Say “common validated active-text control under the registered contract”; earn “strong literature baseline” only through a faithful external comparison |
| Headline `P1` versus `R0` at lines 154--164 and 193--205 | This contrast combines parenting, three childhood fits, entry competence, deployment writes, and resulting on-policy memory. It is not the parenting estimand and is not resource-equal overall | Lead every abstract/result with `D`; label `P1-R0` “full developmental package versus raw actor under deployment-only parity” |
| Abstract promises adapter-removal, forward/backward panels; methods keep a LEAFE-style terminal row | These statements appear unconformed to frozen v2, which replaced/limited diagnostics and makes the LEAFE row descriptive only | Rewrite only after ratification, from the v2 addendum's exact diagnostic roster. Do not advertise tests the frozen protocol does not power |
| “Benefit of LoRA writes” / “parametric-carrier mechanism” | The treatment changes later data and external text; total-effect success does not locate the carrier | Say “effect of enabling the closed-loop write system.” Use fixed-store adapter removal/swap before a parametric-carrier claim |
| Current related-work table's final-row distinction: repeatedly updated per-life low-rank state | Directly false as a novelty boundary because TMEM and EVAF repeatedly update LoRA online | Replace the table with the mechanism comparison above or a compact version centered on the parenting factorial |
| “same validated evolving textual memory supplies ... frozen-parameter reference” | `R0` has the same deployment active-text mechanism, but it has a raw checkpoint and no childhood fits; `P1-R0` is not a same-history carrier comparison | State deployment-only equalities and every non-equality; use `P1-P0` for write enablement and `D` for parenting |
| Independent unit / parenting generality | V2 fixes one parent policy and one child checkpoint; program roots cannot justify a general claim about parents or learners | Report inference over `Q` roots conditional on the fixed pair; call the study a mechanistic case study unless new independently raised model-level units are preregistered |

## 6. ICLR-facing positioning

### Recommended thesis

> Existing work shows that agents can update external memories or LoRA from
> experience. We ask a different causal question: can target-blind process
> teaching, delivered before deployment and then completely removed, make a
> fixed child system benefit more from its own later parametric updates? A
> dose-matched 2x2 design separates inherited competence, ordinary online
> adaptation, and their interaction while every arm retains the same evolving
> external memory.

This is a **developmental intervention / causal measurement paper**, not a
first-parametric-memory paper. The proposed writer should be described as the
experimental learning substrate. If TMEM-style, naive/native LoRA, and batch
controls are added and beaten, the paper may additionally claim a writer
advance. Without them, do not make that claim.

### Candidate titles

- **Can Process Teaching Make an Agent Learn Better From Its Own Experience?**
- **Teaching an Agent to Learn After the Teacher Leaves**
- **Process Parenting and Deployment-Time Learning in a One-Parent/One-Child Agent**

The first is clearest. “Experience Models” may remain a long-term program name,
but it is too broad for the novelty actually isolated here.

### Claim ladder

1. **Primary, only if all registered gates pass:** for this fixed parent/child
   system over the registered CompilerGym root distribution, target-blind
   process parenting increased the closed-loop gAUC effect of enabling the
   prescribed per-life LoRA updates (`D>0` by the preregistered rule).
2. **Secondary:** `U1-U0` or `P1-P0` shows beneficial within-system continual
   adaptation on top of common active text. This is not first-of-kind.
3. **Public full-package contrast:** `P1-R0` compares the complete parented
   developmental system to the raw actor under matched deployment affordances,
   not equal total training history.
4. **Writer superiority:** only after matched naive/native, TMEM-style, and
   batch controls.
5. **Parametric carrier:** only after an adapter intervention holding the later
   store/history fixed.
6. **General parenting/meta-learning:** not licensed by the frozen one-pair
   design, regardless of the number of program roots.

### Likely reviewer reading

- **If submitted with the current title/table and no TMEM/PEAM/EVAF/Learning on
  the Job citations:** novelty objection is immediate and justified.
- **If reframed around `D` but without closest parametric baselines:** the causal
  question may be interesting, but the systems contribution remains
  under-compared; the result must be unusually clean and strong.
- **If reframed around `D`, with TMEM-style + naive/native + batch controls and a
  credible external-memory comparator:** the work has a coherent ICLR story:
  not “agents can learn from life,” but “a prior social/process intervention
  causally changes the efficacy of later personal learning.”
- **Even in the best case:** one domain and one fixed model pair cap external
  validity. Say so plainly. The rigor of the factorial and provenance controls
  can make that bounded result valuable; broad biological or societal language
  will make it look weaker, not stronger.

## 7. Primary-source URLs

Technical claims in this audit were checked against primary paper pages or
their official arXiv HTML, not secondary summaries:

- TMEM: https://arxiv.org/abs/2606.04536 and
  https://arxiv.org/html/2606.04536v1
- PEAM: https://arxiv.org/abs/2605.27762 and
  https://arxiv.org/html/2605.27762v2
- EVAF / Memory Depth: https://arxiv.org/abs/2606.26806 and
  https://arxiv.org/html/2606.26806v1
- Macaron-V1: https://arxiv.org/abs/2608.09819 and
  https://arxiv.org/html/2608.09819v2
- LEAFE: https://arxiv.org/abs/2603.16843 and
  https://arxiv.org/html/2603.16843v1
- Agent Learning via Early Experience: https://arxiv.org/abs/2510.08558 and
  https://arxiv.org/html/2510.08558v3
- Learning on the Job: https://arxiv.org/abs/2607.22157 and
  https://arxiv.org/html/2607.22157v1
- MemoPilot: https://arxiv.org/abs/2606.08656 and
  https://arxiv.org/html/2606.08656v1
- ACE: https://arxiv.org/abs/2510.04618 and
  https://arxiv.org/html/2510.04618v3
- ReasoningBank: https://arxiv.org/abs/2509.25140 and
  https://arxiv.org/html/2509.25140v2
- Evo-Memory / ReMem: https://arxiv.org/abs/2511.20857 and
  https://arxiv.org/html/2511.20857v2
- FLEX: https://arxiv.org/abs/2511.06449 and
  https://arxiv.org/html/2511.06449v2
- When Continual Learning Moves to Memory:
  https://arxiv.org/abs/2604.27003 and
  https://arxiv.org/html/2604.27003v1
- CL-Bench: https://arxiv.org/abs/2606.05661 and
  https://arxiv.org/html/2606.05661v1

## 8. Local source-binding receipt

This advisory was prepared against the following bytes:

| Local source | SHA-256 |
|---|---|
| `AGENTS.md` | `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e` |
| `paper/iclr2027_experience_models/main.tex` | `3ad83dc406cdf2331a7ce833e1566002942fd21ed6b447313fe7315f6f83dc59` |
| `research_notes/related_work/20260906_experience_learning_neighbors.md` | `27697e0aa4d64d0f67b70eee688b0f33eadaa53f106f45f68f7bd8b365977450` |
| `research_loop/plans/one_parent_child_headline_v1.md` | `e356bcecc0cdec3199cf8ecb23c2dc9790a59a11ee6dc8f81b1bfd399c7cf4d5` |
| `research_loop/plans/one_parent_child_headline_v2_addendum.md` | `3c13492bb1378e07d966597efb9eb72f3c8742631a1e7ef1cb7b8977a5039cff` |
| `research_loop/plans/active_text_fixed_contract_v1.md` | `0fbb16b124f640c0adcecc46d2270a7ee11e6c63866885d56e3b0e3468ed09c7` |
| `research_loop/plans/active_text_fixed_prompt_schema_v1.txt` | `854f9215ca74ce3f753bb57cf05c781e190915eab591d800ddf495fb2767e85a` |
| `research_loop/workflows/one_parent_child_headline_v2.deliberation.json` | `d623cfb8f16e51286c8a34cb2822f20b13e44f65a9b80862d567aa3366eeff5a` |

Fresh searches were performed through 2026-09-06 (America/Los_Angeles). The
search was designed to find the direct mechanism neighbors and important
recent boundary papers; it is not a claim of an exhaustive systematic review.
