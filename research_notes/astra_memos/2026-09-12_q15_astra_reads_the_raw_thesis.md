# Astra memo q15 — Astra reads Rohin's raw thesis (messages 1–4): the claim, the contribution, what is adopted, what is overclaimed, what a reviewer attacks first; two abstracts; the collaborator-brief refactor; one adapter; plasticity by level

Asked by Fable 2026-09-12 00:07 UTC at Rohin's request ("Tell Astra all the raw text… I wanna see what Astra says… this is literally the abstract… ask Astra to do this"). Single call, `tools/astra.py`, effort high, 90 s, 12.3k tokens in; prompt = the four raw messages verbatim + the evidence block (SEQ-044/048–053) + the current abstract + COLLABORATOR_BRIEF_v2 (`q15_run/prompt.md`); raw reply in `q15_run/reply_raw.md`. Astra distinguished Rohin's words from the pasted assistant's and from Fable's report. Nothing here is adopted into the paper or the brief until Rohin rules; the two abstracts are staged in `paper_prototype/ABSTRACT_CANDIDATE_v3_flywheel.md`.

---

## Bottom line

**Refactor around the self-learning flywheel—but present it as the hypothesis the experiments are building toward, not a demonstrated result.** The strongest contribution is not “an agent trains on its own text.” It is **teaching an agent to turn externally grounded experience into data that makes its subsequent learning better**.

The present evidence identifies a missing link: the child can produce storable renderings under a controlled prompt, and adapters retain routines, but ordinary lives do not produce retrospective action–outcome records. Worse, the loop currently gives the child no opportunity to write them. H2 has never been tested. [Messages 1–4; SEQ-048–052; evidence block, H2]

**Source boundary:** I rely only on the supplied material; I have not fetched papers, notebooks, code, or results. References below identify supplied sections, not independently verified evidence. Message 1 interleaves Rohin’s statements with another assistant’s responses; Message 4’s final three paragraphs are explicitly Fable’s report. I distinguish these from the lead’s own claims.

## A. My reading of the thesis

### 1. The exact claim

The proposed causal chain is:

> **External event or feedback → learned attention, interpretation, and articulation → child-authored training artifacts → sleep consolidation → changed behaviour and usable memory → better learning from subsequent events.**

Parenting initially teaches the disposition that makes this chain work. Deployment removes the childhood teacher, **not the learning loop**. The target is a small agent that learns better in an unseen compiler gym, not a comprehensive architecture for agency. [Message 1, Rohin’s “epiphany” and closing flywheel passage; Messages 2–3]

There are two separable hypotheses:

- **H1—retention:** taught learning behaviours survive consolidation into an adapter and remain usable outside the teaching context.
- **H2—self-learning:** carrying those behaviours makes the agent improve faster from new experience, and that advantage depends on continued consolidation.

The precise H1/H2 operationalisation appears in the **pasted assistant response** in Message 1, building on Rohin’s opening two questions. Rohin’s later insistence that the deployed flywheel remains unfrozen supports that interpretation.

**H2 is not merely a higher starting score.** The clean target is a parenting × continued-sleep interaction in learning over experience, with entry performance reported separately. A positive interaction alone also needs inspection: it could arise because sleep damages untaught agents rather than because parented agents genuinely improve.

### 2. What the contribution would be

Three contributions are plausible, with different evidential status:

1. **The taught object:** a disposition to produce useful post-training data about one’s own experience, rather than generic reflection or polished summaries. This is the conceptual centre. [Message 1, Rohin’s epiphany]
2. **The curriculum:** progressively teach the smallest workable learning loop, then exercise the same skills in richer environments. Numeric scaffolds can precede discretionary allocation of attention and rehearsal. [Message 3]
3. **The causal demonstration:** show retained learning behaviours and then faster consolidation-dependent learning on unseen tasks. **This remains prospective.** [Message 1 thread; evidence block, H2]

The strongest existing empirical contribution is narrower: **a diagnosis of the gap between behaviour change, controlled fact storage, and autonomous production of useful experience records.** [SEQ-044/048–053]

The parent is also more accurately described as **amortising a human teacher**: Rohin supplies curriculum, prompts, and relevant information; agent parents deliver that teaching at scale. That exact phrase comes from the pasted assistant, but it captures Rohin’s explicit account. It does not establish direct learning from human collaboration or that humans would outperform agent parents. [Message 1, human-teaching exchange]

### 3. What is adopted rather than invented

The lead repeatedly disclaims inventing the underlying weight-update mechanism:

- post-training for behaviour change;
- low-rank adaptation for persistent updates;
- memory-writing through suitable representations and repeated/diverse exposure;
- context-based planning and reflection already available in the base model. [Messages 1–3]

TMEM and *Physics of LMs* supply motivation and candidate engineering recipes **as described in the supplied thread and brief**. Their exact scope and the claimed novelty relative to them are not verifiable here. In particular, do not write “prior work already establishes our mechanism” merely because it establishes related storage or adaptation effects. [Message 1 thread; brief §4]

The distinction worth retaining is:

> **Prior work supplies ways to absorb suitable data; this project asks whether the behaviour that produces suitable data can itself be taught and retained.**

That is a proposed research distinction, not a verified priority claim.

### 4. What is overclaimed or under-specified

**“The mechanism works; we just need the right outputs.”**  
This is a useful experimental decomposition, not yet a system-level result. Controlled owner-specific completion memory is encouraging, but does not establish robust retrieval, useful experiential memory, or joint retention of memory and behaviour during repeated deployment updates. [Message 2; SEQ-048/049]

**“The model distills, but doesn’t originate.”**  
Keep this as a **provenance requirement on factual training content**. The model still contributes selection, compression, hypotheses, and possibly new deductions. These need evidential labels; they are not automatically observations. The reported ≥98.5% sourced factual tokens is reassuring, but neither complete provenance nor proof that causal relations and outcome interpretations are correct. External grounding also does not eliminate selection bias, recursive errors, or collapse. [Message 1 thread; SEQ-050/051]

**First person is not the mechanism by itself.**  
“I form expectations” is already a first-person slogan. “I ran pass X on program Y and observed result Z” identifies an event. Conversely, a third-person structured record could encode the same useful information. Treat person and tense as candidate scaffolds; evaluate episode binding, measured outcomes, retrieval, and downstream use. The pasted assistant’s “only the second one is a policy” is too strong. [Message 1 thread; SEQ-050–052]

**“Everything it thinks” becoming training data is too broad.**  
Good artifacts may need selection, negative results, uncertainty, and correction. Success-only filtering could preferentially preserve lucky recipes and discard evidence about when they fail. The target should be **useful, grounded experience**, not maximal self-text throughput. [Message 1 closing passage; brief §§1, 3]

**Childhood/adult plasticity needs an implementation definition.**  
Learning rate, update steps, replay composition, corpus retention, and adapter initialisation are distinct controls. Reducing corpus accumulation does not itself imply lower plasticity or preservation of foundations. [Message 4; brief §1]

### 5. What a sceptical reviewer attacks first

In order:

1. **“Where is the self-learning result?”** H2 has never run; all final-test evidence uses frozen adapters.
2. **“Did you teach reflection, or merely install recipes?”** Routine retention is measured; retained adaptive learning skill is not established. Text memory matches or beats adapters in 15/24 lives. [SEQ-044/053]
3. **“Does the child write the experience, or does the harness supply the crucial outcome?”** Current articulation is zero late in every baseline life, and the harness appends results. [SEQ-052]
4. **“Is improvement parenting, extra tokens, extra training, or task-answer leakage?”** Historical parenting is observational, and brief §2 explicitly acknowledges porous historical controls.
5. **“Why should canonical fact completion predict learning in a compiler gym?”** It is a substrate test, not the downstream claim.

### 6. Where the lead is sharper than the current notes

- **The unit of contribution is the flywheel**, not “one write into an experience model.” The brief’s question foregrounds storage; the lead foregrounds learning to generate useful updates. [Message 1 versus brief §1]
- **Deployment must keep learning.** The brief postpones the decisive claim to another study, while the lead makes it the paper’s purpose. Refactor the research question without pretending the evidence has caught up. [Messages 1–2 versus brief §§1, 5]
- **Representation engineering and learned discretion are different.** The lead explicitly rejects making “render everything sixteen times” the endpoint. [Message 3 versus brief §4]
- **Complexity should follow the test’s requirements.** The lead’s “smallest possible flywheel” and reconsideration of the adapter split are sharper than a shopping list of memory architectures. [Messages 3–4 versus brief §6]

## B. New abstracts

These are **current-evidence abstracts**, not placeholders that imply H2 succeeded. Evidence basis: SEQ-044/048–053 and the explicit unrun-H2 statement.

### Main abstract — under 250 words

Continual learning requires more than a weight-update rule: an agent must turn experience into useful training data. We investigate a self-learning flywheel in which a frozen language model with a trainable adapter is taught to perceive, interpret, and record externally grounded experience, then consolidate its records into weights. An agent parent amortises a human teacher’s curriculum. The intended mechanism is not closed-loop self-distillation: the model distills, but does not originate, the factual evidence, which must trace to environmental outcomes or external feedback. We separate H1, retention of taught learning behaviours outside the teaching context, from H2, faster learning on unseen tasks whose advantage depends on continued consolidation.

Current experiments test prerequisites and failure modes, not H2. In controlled planted-fact tests, frozen-child renderings ending in a canonical sentence support owner-specific completion recall of 0.82, versus 0.91 for handwritten templates across three banks. Rank-8 adapters retain a behavioural routine, but the child’s written brief matches or beats the adapter in 15 of 24 lives. In ordinary interaction, child-authored notes become recipes or slogans rather than records of actions and outcomes. Across 28 lives, late-stage articulation of a first-person record with a measured outcome is zero; the interaction format requests notes before outcomes and provides no post-outcome writing slot. These results locate an articulation bottleneck but do not establish retained adaptive learning skills or a functioning self-learning flywheel. Post-outcome teaching experiments and the parenting-by-continued-consolidation test remain unrun.

### Short variant — under 150 words

We investigate a self-learning flywheel: teaching an agent to turn its own externally grounded experience into useful post-training data, then consolidating those records into an adapter. An agent parent amortises a human teacher’s curriculum. The model distills, but does not originate, the factual evidence; this provenance requirement distinguishes the proposal from closed-loop self-distillation. H1 asks whether taught learning behaviours persist beyond their teaching context. H2 asks whether they accelerate learning on unseen tasks, with the advantage depending on continued consolidation.

Current evidence establishes prerequisites and failures, not the flywheel. Controlled child-authored fact renderings support owner-specific recall, and adapters retain routines. Yet ordinary notes become recipes or slogans: late-stage action–outcome articulation is zero across 28 lives, in a format lacking a post-outcome writing slot. Text briefs remain competitive with adapters. Post-outcome teaching and the decisive parenting-by-continued-consolidation experiment have not run.

## C. Refactor the collaborator brief—and simplify the experiment

### New spine — 11 lines

1. **Question:** Can taught experience-articulation skills kickstart consolidation-dependent self-learning?
2. **Mechanism:** external evidence → child-authored artifacts → sleep → retained skills/memory → better experience use.
3. **Scope:** agent parent amortises human teaching; compiler-gym demonstration, not general human learning.
4. **Hypotheses:** H1 retained learning behaviours; H2 parenting × continued-sleep effect on learning trajectory.
5. **Evidence status:** routine retention and controlled storage measured; autonomous articulation absent; H2 unrun.
6. **Loop contract:** act, observe, record; provenance-linked outcomes; explicit behaviour-training boundaries.
7. **Curriculum:** prompted base → optional birth scaffold → preschool → diverse schooling → parent-free deployment.
8. **Minimal implementation:** one adapter, fixed compilation recipe, explicit replay and reset policy.
9. **Immediate gate:** post-outcome slot, artifact lesson, numbered scaffold; measure before enforcing.
10. **Final test:** replicated 2×2, unseen programs, equal scaffolds/budgets, entry level and learning trajectory.
11. **Decision rules:** artifact readiness, retention, safety, and evidence required before each claim.

### Delete or move out of the main narrative

- Replace the opening storage question and the claim that the real experiment is necessarily “next study.” Instead distinguish **paper question, completed evidence, and submission-contingent claim**. [Brief §1]
- Move the old failed-car-test chronology, plateau catalogue, and gate arithmetic to an evidence appendix. They remain important, but should not determine the conceptual spine. [Brief §§3, 7]
- Remove two-block adapters and separate memory systems from the default help request. Make them conditional remedies.
- Retire “sleep expands each percept into many renderings” as the intended learned endpoint. Keep it as a substrate calibration or explicit scaffold. [Brief §4; Message 3]
- Replace blanket “no usable knowledge stored” with a narrower statement acknowledging controlled completion-frame storage while withholding claims about autonomous experiential memory.

### Keep

- Precise definitions of life, sleep, committed adapter, lineage, and collapse.
- The fresh-from-base training rule—prominently, because it determines what forgetting means.
- Text-brief and fixed-recipe controls; unseen-source evaluation; harmful-generation checks.
- Historical parenting caveats and provenance requirements.
- An evidence ledger separating **historical, measured now, running, designed, and unrun**.
- The earlier negative results, including failures of safety gates. The thesis does not erase them.

### Add

**An artifact contract, not just a slogan.** A record should identify the episode/program, action actually taken, observed result and its source, and any lesson separately from the observation. Numeric agreement alone does not establish correct attribution. Preserve failed experiments when informative. First-person narration can be a scaffold, not the sole validity condition. [SEQ-052; Message 3]

**Separate gates.** A provenance guard, a record-quality/admission gate, and an adapter deployment-safety gate answer different questions. Run the new articulation gate in shadow mode initially; retain fail-closed provenance requirements for eligible results. A rejected note must not silently become a claim that the entire learning mechanism failed.

**A staged causal test.**

1. Run the designed preschool comparison: slot alone; slot plus artifact-teaching parent; slot plus parent plus numeric scaffold.
2. Equalise or at least report generation and training budgets. “Aim for ten records” changes exposure as well as instruction.
3. After teaching, test articulation on new episodes **without the lesson or parent in context**, using adapter-on/off controls: this targets H1.
4. Only then run the replicated parented/unparented × sleep-running/frozen deployment test. Remove parents in all deployment arms. Keep base prompts, feedback, text-memory policy, and episode budgets matched.
5. Pre-specify a learning-trajectory endpoint and interaction; report initial performance separately. Continue text-brief and fixed-routine baselines. Evaluation outcomes must not enter subsequent training unless explicitly part of the deployment protocol.

### Message 4: one adapter or 8+32?

**Yes to one adapter as the default. No to claiming rank 16 is already sufficient.**

Rank 32 never helped completion-frame memory over six banks and hurt in low-diversity conditions; rank 8 carries the routine in every tested life. This argues against paying for an unvalidated memory/behaviour split. It does **not** prove rank 8 or 16 can jointly retain both under continued updates. [SEQ-044/053]

My recommendation:

- **Use one adapter and provisionally retain rank 8**, the supported baseline.
- Admit rank 16 only after a small matched joint test: behaviour retention, owner-specific recall, spill, action validity, and forgetting after new experience.
- Hold training data, target modules, and exposure fixed; report compute cost.
- Choose rank 16 if it improves a predeclared deficiency without unacceptable regression. If tied, choose rank 8.
- Revisit splitting only if joint training shows reproducible interference that the split fixes.

**Rank 16 is simpler than 8+32, but “middle rank” is not evidence of sufficiency.** More importantly, no rank repairs a missing post-outcome slot.

For the final flywheel, keep one planning loop, one post-outcome record, one sleep cadence, and one compilation recipe. Short fact records and longer behaviour sequences can coexist in one adapter. Do not add multiple planning hierarchies, discretionary rendering policies, or subagents unless the minimal loop fails for a diagnosed reason. [Messages 2–4]

### Plasticity by level

**Separate updating strength from corpus retention.**

The current implementation trains a fresh adapter from the frozen base each sleep. If later corpora become less cumulative, omitted childhood material is not preserved merely because the nominal learning rate is smaller. Lower learning rate cannot protect weights that were discarded at reinitialisation. [Brief §1; Message 4]

| Level | Recommended data/update policy |
|---|---|
| Base / optional birth scaffold | Establish prompted capability and a small foundational corpus; avoid extra machinery unless needed. |
| Preschool | Cumulative, verified records; enough exposure to learn articulation and basic routines; frequent retention probes. |
| Schooling | Cumulative early, then bounded stratified replay; protect foundational examples while increasing task diversity. |
| Adult deployment | Fixed foundational replay plus a rolling recent-experience window and sampled older experience; bounded updates and rollback checks. |

For this study, retain fresh-from-base fitting to avoid introducing another mechanism, but **reinclude a protected foundation sample at every sleep**. “Less cumulative” should initially mean less exhaustive episodic replay, not abandonment of the learning routine’s training support.

If instead you want genuinely incremental adult updates from the committed adapter, label that an architecture change and test forgetting explicitly. No supplied evidence establishes the best learning-rate schedule, replay fraction, or update budget; do not encode the childhood metaphor as an assumed result.

## D. One thing we are about to get wrong

**We are about to treat a temporal affordance bug as a failed learned disposition—and then call its repair successful parenting.**

The child is asked to write before it knows what happened. Zero retrospective articulation in that format is not a fair test of its capacity to learn retrospective articulation. Conversely, improvement after adding a post-outcome slot does not by itself demonstrate that parenting taught the flywheel. [SEQ-052; Message 4, Fable’s pasted report]

The designed three-cell preschool comparison correctly separates the slot from additional teaching. Keep that separation, then remove the teaching prompt and test retained behaviour. **Otherwise the paper’s central learned mechanism could turn out to be a harness change wearing a curriculum’s name.**

[astra openai/openai/gpt-6-astra effort=high 90s tokens in=12323 out=4137 reasoning=118]
