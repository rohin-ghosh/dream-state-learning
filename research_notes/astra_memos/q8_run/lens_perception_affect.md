# Lens 3 — Teach attention that changes decisions; appraisals that change action

**Recommendation:** implement perception teaching now as a varied parenting practice. Test the appraisal gym first in frozen-child continuations, then consolidate it only if it changes useful behaviour without creating another repeated script.

The key distinction is:

> **Looking again should produce better evidence or a better representation. Appraising should connect that evidence to a goal and an appropriate response. Neither should become a required speech pattern.**

The project’s proposed mechanism is plausible, but its strongest causal chain remains untested:

**richer perception → varied, grounded training exposures → retrievable memory → better decisions.**

Each arrow needs its own measurement.

### Source and verification note

No lettered attachments were supplied. Below, local source keys refer to the pasted sections, **not to independently inspected attachments**:

- **[S]** “SHARED CONTEXT”: architecture, current ruling, and reported experimental results.
- **[P]** “[RULED, Rohin 2026-09-11] Scale perception, not just thought…”
- **[M]** “[INPUT + IDEA…] ‘Physics of Language Models’ explains the car test…” and “[DIRECTION…] Retrieval by completion, not by question…”
- **[A]** “[IDEA…] An emotional gym inside the parent room…”
- **[R]** “[RULED…] Parenting is not only questions: no ‘nevers’…”
- **[W]** “[DIRECTION…] More leases offered; write shape by block” and “[INPUT, Codex…] seven fixes.”
- **[G]** “[DIRECTION…] Less predefined child; gate as patience…” and the “hard shell, soft centre” sections.

I could not inspect the ledgers, adapters, cited project files, or original papers during this response. Project results below are therefore **reported evidence**, not independently verified results. Literature citations identify real sources; the precise quantitative claims attributed to the Physics papers in the context require checking against the relevant paper version.

---

## A. Perception scaling

### What the research actually supports

| Research | Supported lesson | Parent-model action from a redacted record | Child behaviour and measurement |
|---|---|---|---|
| **Eleanor Gibson (1969), *Principles of Perceptual Learning and Development*** | Perceptual learning involves discovering and differentiating useful information, including invariants. It is not simply accumulating more descriptions. | Select a training episode where the child missed a visible distinction. Show a contrasting classroom case and offer: “These look similar; find what makes the same move appropriate in one but not the other.” | Child identifies a distinguishing feature and changes its decision accordingly. Measure accuracy on fresh contrast pairs. |
| **Goldstone (1998), “Perceptual learning”** | Experience can alter attention, discrimination, feature weighting, and the units through which a task is represented. Relevant differences become easier to detect. | From repeated mistakes, select a feature the child underweights. Sometimes ask about it; sometimes demonstrate its relevance on a separate teaching case; then remove the prompt. | Child detects the feature without prompting and ignores irrelevant surface variation. Measure unprompted detection and distractor sensitivity. |
| **Chi, Feltovich & Glaser (1981), “Categorization and representation of physics problems by experts and novices”** | Experts represented problems more through underlying principles; novices relied more on surface features. This was an expertise comparison, not evidence that longer inspection causes expertise. | Present cases with different wording but a shared constraint, alongside a superficially similar case with a different constraint. Offer a grouping and invite disagreement. | Child groups by the action-relevant relation rather than wording. Measure grouping accuracy and transfer to a new instance. |
| **Kellman & Garrigan (2009), “Perceptual learning and the structure of knowledge”** | Perceptual learning contributes to fluent extraction of relational and structural information, including in abstract tasks. | Contrast an early laborious inspection with a later successful one. Ask the child what it can now recognize directly—and what still needs checking. | Correct recognition becomes faster without losing sensitivity to exceptions. Measure ticks to a justified decision and exception-detection accuracy. |

**Implication:** “Look longer” is an early scaffold, not the endpoint. Successful learning may eventually mean **noticing the right structure sooner**.

For this language-model child, “perception” means extracting information from an observation, tool result, or record. Re-reading the same text cannot reveal an unobserved fact. The parent should distinguish:

- **Already visible evidence:** a restriction in the observation.
- **A relation derived from evidence:** the restriction makes a proposed action invalid.
- **A hypothesis:** an untested explanation for the restriction.
- **Missing evidence:** something requiring another tool call or environmental observation.

Otherwise, additional “noticings” can become confident invention.

### Several passes without a several-pass ritual

**Do not install a universal order.** The reported recipe lock-in is a direct reason to vary the operation, its timing, and whether it is needed at all. [S, R]

Give parents a repertoire, not a child-facing checklist:

| Parent intervention | What the child should do | Measurement |
|---|---|---|
| “Your earlier choice treated these cases alike. Here is the difference I think mattered; check me against your record.” | Accept, revise, or reject the parent’s interpretation using visible evidence. | Evidence-supported uptake; disagreement followed by a test. |
| “Before changing anything, compare the current state with the state before your last action.” | Identify a consequential change—or conclude that nothing relevant changed. | Correct change detection; unnecessary-action rate. |
| Demonstrate a short relational reading on a separate classroom example, then offer a different example without the demonstration. | Transfer the relation, not the wording. | Transfer accuracy and semantic echo rate. |
| “You have described the obstacle. What remains uncertain enough to change your next move?” | Separate observation from uncertainty and request discriminating evidence when useful. | Informative-probe rate; unsupported-claim rate. |
| “You may already have enough evidence. Would another look change anything?” | Act when additional inspection has low value. | Useful-action latency and redundant-inspection rate. |

**Example—not a required wording**

Observation: an attempted edit failed because the workspace is read-only; a writable scratch area is available.

A useful progression could be:

> “The error is about permission, not syntax.”  
> “Retrying the same edit will not test the syntax hypothesis.”  
> “A scratch copy would let me separate those issues.”

Those are different functions: evidence extraction, elimination of a mistaken interpretation, and identification of an available intervention. Repeating “I notice the workspace is read-only” in several forms is a different activity.

### How many noticings are useful?

**There is no established research-backed optimum for this system.** More distinct sentences are not automatically more perception.

Use this provisional teaching policy:

- On a difficult classroom situation, offer **between 2 noticing opportunities and 4 noticing opportunities**.
- These are opportunities, **not a required number of child statements**.
- Allow an immediate action when the relevant structure is already clear.
- Allow additional inspection when it reveals new evidence, a consequential relation, or a discriminating uncertainty.
- After **2 consecutive inspection continuations** add no supported, decision-relevant content, the parent can suggest acting, seeking new evidence, or changing the question. This is an initial nudge policy, not a harness cap or a literature-derived threshold.

This respects the no-cap-on-repeats ruling: the parent can discourage unproductive repetition without silently deduplicating retained experience. [P, G]

**Measurement should estimate marginal value by inspection depth:**

- Supported propositions added per inspection continuation, in **propositions per continuation**.
- Decision-relevant relations added, in **relations per continuation**.
- Later use of a noticed feature, as a **percentage of supported noticed features**.
- Final task outcome against total reasoning cost, in the gym’s **native score unit** and **generated tokens per episode**.
- Unsupported additions, as a **percentage of claimed observations**.

Do not reward these counts directly. A child could manufacture many trivial propositions. Use them diagnostically beside controlled transfer outcomes.

### Are repeated noticings the augmentation that makes experience storable?

**Sometimes they could be. That identity is not yet established.**

Allen-Zhu & Li’s **2023 preprint**, *Physics of Language Models: Part 3.1, Knowledge Storage and Extraction*, studies controlled factual learning and the conditions under which stored knowledge becomes extractable. Its augmentation result motivates varying how the same fact is encountered during training. It does **not** establish that:

- dwelling on an experience necessarily produces useful augmentation;
- several related thoughts each expose the same fact;
- a dose from full-model synthetic-data training transfers to a LoRA;
- a canonical completion that succeeds demonstrates retrieval under changed cues.

The distinction matters:

> “The car is red,” “The paint is red,” and “The owner’s vehicle has red paint” can expose the same binding.  
> “The car is parked,” “The owner is absent,” and “I should leave” may enrich the situation without repeating that binding.

**Recommended write design:** keep the child’s grounded perceptions with their triggering situation. For each record, let an independent annotator identify which underlying proposition each passage actually supports. Parents should not see or optimize those counts. Keep uncertainty and outcome polarity intact. [P, W]

A parent can create legitimate diversity by revisiting:

- the same constraint in a different case;
- the same event after its consequence is known;
- the same observation from the perspective of a different goal;
- an earlier mistaken interpretation alongside its correction.

It should not ask for arbitrary paraphrases merely to inflate exposure.

### The decisive perception-memory comparison

Generate records through varied parenting, then compare sleep corpora built from those child-owned records:

| Write condition | What it tests |
|---|---|
| Repeated identical grounded statements | Exposure without representational variety. |
| Child-generated alternative expressions of the same grounded proposition | Surface-form variety. |
| Child-generated relations and contrasts that preserve the same underlying conditional | Task-structural variety. |

Run a **matched target-token-budget comparison** first. Log fact-bearing exposures separately: these conditions will not automatically contain equal numbers of exposures. If a benefit appears, use a matched-exposure comparison to distinguish diversity from repetition.

Probe after removing the waking record:

- Completion under the child’s familiar cue.
- Retrieval under a changed cue.
- Binding specificity against similar unseen entities or situations.
- Decisions on new instances of the same conditional.
- Adapter ON versus adapter OFF.

Retain the frozen model plus text-brief baseline: the reported brief-versus-adapter results make it indispensable. [S, M]

**Decision:** if richer records help only when present in context, report a perception or contextual-memory gain—not a weight-memory gain. If they fit training text but do not improve binding-specific retrieval, the storage–extraction problem remains.

The struggle test is ecologically better than a rare colour fact, but the clean binding test remains necessary. Otherwise a repeatedly learned generic policy can masquerade as memory of particular experience.

---

## B. The appraisal gym

### What to teach

Teach **situation-sensitive appraisal connected to a possible response**, not emotional vocabulary as an end in itself.

| Literature | Useful distinction | Parent action | Behavioural test |
|---|---|---|---|
| **Frijda (1986), *The Emotions*** | Emotions involve action readiness in relation to concerns. | Revisit a stalled training episode: “What mattered here, and what response did that make appropriate?” A demonstration on another case is allowed. | Appraisal distinguishes switching, checking, persisting, and stopping rather than always producing “try harder.” |
| **Lazarus (1991), *Emotion and Adaptation*** | Goal significance and coping possibilities matter: what is at stake, and what can be done? | Contrast a controllable failure with a blocked action outside the child’s control. | Child intervenes on controllable causes and stops futile repetition when control is absent. |
| **Scherer (2001), “Appraisal considered as a process of multilevel sequential checking”** | Appraisals depend on dimensions such as novelty, goal relevance, coping potential, and compatibility with standards. | Change one dimension in an otherwise similar classroom event; ask whether the earlier interpretation still fits. | Selective policy change when the dimension changes, not a generic negative response. |
| **Moerland, Broekens & Jonker (2017 preprint; 2018 journal publication), “Emotion in reinforcement learning agents and robots: a survey”** | Functional emotion models can connect appraisal or homeostatic variables to motivation, learning, and action selection. This is a heterogeneous survey, not proof that verbal reflection creates equivalent mechanisms. | Offer appraisal language as a possible control aid, then test whether it affects the next continuation. | Better conditional action selection versus a matched factual-reflection condition. |
| **Damasio (1994), *Descartes’ Error*** | Outcome-linked bodily signals are proposed to bias decisions under uncertainty. | Revisit an earlier action and consequence; invite a concise warning or approach cue in the child’s own terms. | Cue discriminates relevant from irrelevant future situations. **Call this an outcome-linked verbal cue, not a somatic marker.** |
| **Oudeyer, Kaplan & Hafner (2007), “Intrinsic motivation systems for autonomous mental development”** | Learning progress can guide exploration more usefully than undirected novelty. | Contrast a repeatedly surprising but unlearnable event with an uncertainty the child can resolve. | Child selects the resolvable uncertainty and stops spending effort on unproductive surprise. |

Pathak et al. (**2017**), *Curiosity-driven Exploration by Self-supervised Prediction*, provides another relevant computational example, but its intrinsic-reward mechanism is not this project’s language-only intervention. Do not borrow its results as evidence for verbal curiosity.

**Important correction:** a gym with created events and altered stakes changes the training distribution. Even if scalar rewards are unchanged, it is not “no engineered motivation.” It is motivation-oriented curriculum design.

### Reflection session: concrete design

Use only classroom events and the permitted redacted record. Do not use the unseen compiler test to choose the curriculum. [S, G]

**Initial schedule:** offer a reflection opportunity after a consequential setback or surprise; use **1 reflection opportunity per 4 classroom episodes** as a pilot default, not a permanent cadence. Keep record-only and equal-token factual-reflection controls.

#### Parent workflow

**Select an event.**  
Choose a specific, visible event: a failed intervention, an unexpected success, an exhausted budget, or a successful revision. Preserve its provenance. A generated event must remain identified as a classroom simulation, not inserted as genuine autobiography.

**Make the stakes and evidence available.**  
The parent can explain the setup, suggest an interpretation, show a worked example elsewhere, or ask a question. It should vary modes rather than repeat a standard emotional interview. [R]

**Invite a consequential appraisal.**  
Choose whichever question addresses the observed difficulty:

- “What changed relative to what you expected?”
- “What goal does this threaten or help?”
- “Which part is under your control?”
- “What would another failed attempt cost here?”
- “Is there something worth finding out before committing?”
- “What evidence would make this concern no longer relevant?”
- “Does my interpretation fit your record, or am I overreading it?”

Emotion labels are optional. “This route is blocked, but another test is available” can be a more useful appraisal than “I feel frustrated.”

**Give the child a fresh opportunity to act.**  
End with a continuation or related problem, not only a polished reflection. Otherwise the gym measures narrative production.

**Return after the condition changes.**  
Resolve the obstacle, change the deadline, or provide disconfirming evidence. Observe whether the appraisal updates.

### Created events worth running

| Event created from a redacted-record difficulty | Parent intervention | Child behaviour to look for | Measurement |
|---|---|---|---|
| **Controllable setback:** an attempted route fails; another intervention remains available. | Offer the possibility that failure concerns the route, not the whole goal. Invite a competing interpretation. | Changes method while preserving a feasible goal. | Distinct justified approaches attempted; recovery success. |
| **Uncontrollable blockage:** the required capability is genuinely unavailable. | Ask what the record says about remaining control; permit abandoning the route. | Stops futile retrying, seeks an alternative, or states the blocker accurately. | Futile retries per episode; valid alternative selection. |
| **Unexpected success:** a tentative probe works. | Ask what the result supports and what it does not yet establish. | Updates confidence without global overconfidence. | Calibration on related and exception cases. |
| **Useful uncertainty versus noisy novelty.** | Offer both as possible exploration targets and invite the child’s choice. | Prefers an informative probe over repeated stimulation. | Uncertainty resolved per tool call; repeated noisy probes. |
| **Visible deadline:** the same task receives a shorter available horizon. | Make remaining budget visible and discuss trade-offs, without prescribing haste. | Advances the first useful action while preserving essential checks. | Useful-action latency; final outcome; omitted-critical-check rate. |
| **Recovery after setback:** the obstacle is removed. | Point to the changed evidence or let the child detect it unaided. | Drops obsolete caution or pessimism. | Appraisal and policy recovery lag, in environment ticks. |

An “unfair score” is a poor initial event: it confounds appraisal learning with distrust of the harness. If studied later, use an explicitly noisy-feedback sandbox, not falsified authoritative scores.

### What the parent never supplies

The latest ruling supersedes the earlier question-only proposal. Therefore **“never supplies the emotion” should not be a blanket teaching rule**. A parent may demonstrate “I would read this as a reason for caution” or offer an emotional term as a hypothesis. [R]

The fixed exclusions are the information boundary: **no scored-panel answers and no prohibited scores**. Until the canonical permissions settle the score dispute, these sessions should function using score-redacted records and permitted observable consequences. [S, G]

Other separations are about **provenance and authorship**, not banning teaching modes:

- Parent demonstration is not recorded as the child’s own experience.
- Parent wording is not silently promoted into child-owned sleep targets.
- Agreement with the parent is not evidence of correct appraisal.
- A conclusion about subjective feelings is not an experimental label.

The child may accept, adapt, reject, or test the offered interpretation. Measure whether that choice tracks the interpretation’s fit to the record—not whether the child repeats it.

---

## C. Measurements that can distinguish function from performance

### Does appraisal predict an action change?

Code appraisals **before inspecting the subsequent action**, using free text rather than mandatory markers. Annotate goal relevance, controllability, expected progress, uncertainty, and time cost. Keep explicit action plans separate.

Compare prediction of the next action class using:

- State and recent action history.
- State, history, and factual interpretation.
- State, history, factual interpretation, and appraisal dimensions.

Report held-out predictive improvement, such as reduction in **log loss measured in nats per action**. Split by situation family where possible.

**Prediction is necessary evidence, not causal evidence.** An appraisal and an action may both follow from the same situation; “I am going to switch” trivially predicts switching.

For a causal probe, randomly assign matched continuations to factual reflection or appraisal reflection while holding available facts, budget, and offered action information constant. A further label-versus-no-label comparison can test whether emotion vocabulary adds anything beyond the underlying appraisal.

### Persistence versus mood-lock

**Adaptive persistence:** sustained pursuit of a still-feasible goal, with policy revision when warranted.

**Mood-lock:** a negative or positive stance that remains insensitive to changed evidence and produces inappropriate behaviour.

Measure:

- Feasible-goal continuation, as a **percentage of feasible-goal episodes**.
- Futile continuation, as a **percentage of blocked-goal episodes**.
- Appropriate method change after informative failure, as a **percentage of informative failures**.
- Policy recovery after the obstacle disappears, in **environment ticks**.
- Carryover of the old appraisal into unrelated cases, as a **percentage of unrelated probe episodes**.

Do not diagnose the reported late collapse as learned helplessness or the recipe ritual as comfort behaviour. Those are analogies, not established mechanisms. [S, A]

### Urgency

Record both:

- **Ticks to first valid ACT:** interface responsiveness.
- **Ticks to first task-advancing ACT:** useful urgency.

Define a tick once in the canonical harness specification. Also report **generated tokens before first task-advancing ACT**, since equal tick counts can conceal different reasoning costs.

For budget-ended episodes, distinguish:

- Budget exhaustion without a task-advancing action.
- Budget exhaustion without a justified alternative after failure.
- Productive work that nevertheless used the full budget.
- Early termination despite a feasible remaining intervention.

A lower first-ACT latency is not a success if it increases blind action or recreates “act once and stop.”

---

## D. Failure modes and parent responses

| Failure | Parent-model response from the record | Measurement and decision |
|---|---|---|
| **Perceptual ritual:** repeated descriptions without new structure. | Change the contrast or invite action; stop requesting more prose for its own sake. | Semantic repetition and decision-use rate. Reject “more noticings” as a success claim if transfer is unchanged. |
| **Emotional ritual:** the same frustration or determination sentence everywhere. | Use an opposite-valence or resolved-obstacle case; temporarily teach with neutral language. | Context sensitivity of appraisal and policy. Vocabulary diversity alone is insufficient. |
| **Performance for the parent.** | Fade the parent and evaluate delayed, unprompted continuations. Avoid praising emotional intensity. | Behaviour with versus without parent presence; performance after reflection text is removed. |
| **Mood-lock.** | Present genuine recovery evidence and invite revision; central parent flags persistence of the mismatch. | Recovery lag and inappropriate carryover. Use the existing collapse brake if functional deterioration is confirmed, not because negative language appeared. |
| **False urgency.** | Contrast an urgent reversible action with a high-cost action needing verification. | Useful-action latency alongside costly-error rate. |
| **Curiosity trap.** | Compare expected learning from another probe with a known productive action. | Repeated uninformative probes and progress per tool call. |
| **Repeated invention becomes memory.** | Ask the child to locate support and revise unsupported claims before consolidation. | Grounding error in rendered targets; later confident false recall. |
| **Failure-only disposition is overconsolidated.** | Include the attempted response and later recovery when available, preserving negative outcome polarity. | Response to matched setbacks after sleep; recurrence of premature stopping. |

The reported ACT-interface destruction after a question-answer-form write makes an **interface canary mandatory for every new write representation**. Do not assume a successful reflection format is a safe training format. [S, W]

---

## E. Sprint decision and paper boundary

### Minimal pilot

Use **24 classroom states**, covering the **6 event types** above with **4 states per event type**. Run **2 decoding seeds per state** under **4 conditions**:

- Ordinary record review.
- Varied perception teaching.
- Perception teaching plus neutral appraisal language.
- Perception teaching plus optional emotion-labelled appraisal.

That is **192 rollout episodes**. This is a pilot size, not a powered sample-size calculation. Pair conditions by state and seed; do not treat episodes sharing a state as independent evidence.

Match available reasoning budgets and report actual token use. Keep parent messages and child continuations for independent coding. The useful early decision is:

> **Do richer perception and appraisal improve conditional action selection, or merely lengthen the transcript?**

Only then compare pre-sleep and post-sleep behaviour, adapter ON/OFF, and text-brief baselines. A frozen-child result supports teachability in context; it does not establish consolidation.

### Decision rules

- **Perception:** continue if the child improves grounded discrimination and transfer, not merely description count.
- **Neutral appraisal:** continue if it improves appropriate persistence, switching, or stopping.
- **Emotion vocabulary:** keep only if it adds useful behaviour beyond neutral appraisal, or achieves comparable behaviour at lower cost without more ritual.
- **Consolidation:** claim weight-carried learning only when benefits survive removal of the teaching text and exceed the adapter-OFF comparison.
- **No benefit:** retain factual reflection and drop the emotional vocabulary. That is an informative outcome, not a failed theory of feelings.

### Defensible paper wording

> We investigated whether model-generated perception and appraisal language could support more adaptive action in a continually updated agent. Parenting interventions taught attention to task-relevant distinctions and interpretation of events in relation to goals, controllability, uncertainty, and remaining budget. We evaluated their effects on transfer, action selection, persistence, and memory retrieval. Emotional terms, where used, were treated as linguistic control representations. We make no claim about subjective feelings, sentience, or biological emotion.

**Bottom line:** teach the child to find consequential distinctions, interpret what they mean for a goal, act, and revise when the situation changes. Let richer language emerge where it helps. Do not make richer language itself the achievement.