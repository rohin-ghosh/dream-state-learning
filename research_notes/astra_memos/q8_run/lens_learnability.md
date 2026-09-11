# Lens 4 — Teach conditional habits, not a vocabulary of intelligence

**My recommendation:** proceed with a small transfer pretest, not a broad “parenting works” run. The plausible target is a habit such as **“when evidence contradicts my rule, test an alternative and change my action.”** The implausible shortcut is that repeated language about noticing, reflection or urgency becomes a general reasoning faculty.

The current evidence favours a narrower explanation: the write can strengthen familiar routines, including harmful ones. It has not demonstrated situation-dependent reasoning, usable weight memory or parenting benefit [Systems Brief §§2.2–2.5].

## Evidence and verification limits

I have the supplied brief and shared context, not the underlying attachments, code or papers open for inspection. Attachment citations below therefore refer to the supplied **E-table references and brief sections**, not independently verified files.

Two discrepancies matter:

- The shared context reports text matching or beating weights in **12 of 19 lives**. The authoritative breakdown supplied here establishes that result in **5 of 8 lives** on the identifier-held-out panel, with a separate disjoint-panel comparison for those lives. I cannot reconstruct the larger tally from the excerpt; do not combine these denominators [E:73–74; Brief §2.4].
- The controlled storage result of **4.4 nats**, and the QA-form write yielding **0 actions**, appear in the shared context without attachment references. I accept them as supplied observations, but cannot verify their protocol or whether the loss unit is per token or per sequence. They are distinct from the approximately **3 nats/token** training-loss change described in E:35 [Brief §2.5].

The lead’s supplied ruling permits varied teaching modes and offered recipes, whereas Brief §1 says no recipes. I use the newer ruling as the requested design premise, but cannot verify its authorized `IDEAS.md` entry. None of the recommendations requires a scored-task recipe.

---

## What the literature licenses—and what it does not

| Evidence | What it supports | Why it does not establish this mechanism |
|---|---|---|
| **Thinking LLMs / thought preference optimization — Wu et al., 2024** | Generated thoughts can be optimized using preferences over resulting responses; useful thinking need not come from human-written reasoning traces. | Preference optimization is not success-filtered imitation. A thought attached to a preferred answer need not contain the causal reason it succeeded. This child has neither an established thought-preference objective nor demonstrated broad training coverage. |
| **STaR — Zelikman et al., 2022** | Training on model-generated rationales associated with correct answers can improve task reasoning. Iterative generation and filtering can work. | Correctness verification, task coverage and the method’s answer-conditioned rationalization matter. “It succeeded once, therefore imitate everything it thought” is a much weaker selection rule. |
| **Reflexion — Shinn et al., 2023** | Verbal reflection retained in episodic text memory can improve subsequent attempts. | This is primarily evidence for **reading useful text**, not writing a reasoning skill into weights. It makes the frozen-child-plus-brief control mandatory. |
| **Self-Refine — Madaan et al., 2023; Huang et al., 2024** | Iterative feedback and revision can help on some tasks. But unsupported intrinsic self-correction is unreliable and can damage correct reasoning. | “Reconsider” is not an evidence source. A self-generated critique can simply replace a correct answer with a more persuasive wrong one. |
| **Process supervision — Lightman et al., 2023** | In mathematical reasoning, evaluating intermediate steps can provide useful training and selection signals. | An exact final gym score does not label intermediate thoughts. Outcome filtering cannot distinguish a necessary check from a decorative ritual in a successful trajectory. |
| **Distilling Step-by-Step — Hsieh et al., 2023; Orca — Mukherjee et al., 2023** | Smaller models can benefit from explanatory supervision and task-relevant rationales. | Those results do not imply arbitrary teacher competence fits in this adapter. Moreover, this system excludes parent text from training: the teacher must first induce a useful **child-generated** trace [Brief §4.1–4.2]. |
| **Recursive-training collapse — Shumailov et al., 2024** | Recursively training on generated data can lose distributional coverage. | That is a warning by analogy, not proof of the cause here. The direct project evidence is stronger: routine lock-in, ritualization and late collapse. Frequency-driven collapse remains untested [Brief §2.5]. |

**The common denominator is selection grounded in evidence, not eloquent thoughts.** Also, verbalized reasoning is not a faithful readout of the computation that caused an answer; see Turpin et al., 2023. Here, a claimed “thinking move” needs an intervention on subsequent behaviour.

---

## The actual write mechanism

I interpret the proposed **behaviour block** and **memory block** as training-data partitions, not separate neural modules. The supplied material does not establish otherwise.

- **Behaviour block:** child-authored thinking sequences paired with their actual situations and actions. Its plausible effect is to change the probability of transitions such as *notice conflict → check → revise action*.
- **Memory block:** child-authored canonical experience frames. Its plausible effect is to make an experience easier to reproduce or recognize. **Retrieving and applying it under another cue is a separate achievement.**
- Both blocks update the same adapter unless implementation establishes a separation. Their effects can interfere.
- A fresh adapter is rewritten from the frozen base at each sleep. Earlier learning persists only through the selected record and subsequent behaviour, not through automatic accumulation of previous adapter updates [Brief §§1, 3].

Parents can invite the child to frame an experience as **situation, expectation, observation, decision and limitation**. The compiler cannot manufacture that frame, supply a missing correction or turn a parent’s demonstration into a child row [Brief §4.1–4.2].

**Minimum common standard for “it took”:**

1. The child acts differently on an unseen situation after the parent brief is absent.
2. It distinguishes a case where the move helps from a matched case where the move is unnecessary or harmful.
3. The difference persists after sleep without the lesson-bearing text in context.
4. The adapter adds something beyond the frozen child reading the same text.
5. The benefit survives the **16-turn problem budget**, without increased invalid actions or abandoned work.

Passing the first conditions but failing the weight conditions is **contextual teaching**, not adapter uptake. That can still be useful.

---

## Teachable ideas: evidence, carrier and decisive pretest

All parent actions below use only the redacted **training** record. The harness owns quantitative evaluation. Parents do not receive panel content, scores or numerical performance summaries [Brief §4.4].

### A. Decision and goal decomposition

**Parent action.** Find a visible episode where the child listed possibilities without choosing a discriminating action. Ask:

> “What uncertainty mattered to your next action? On your next practice problem, choose a cheap check that could change that action. Skip the check if it cannot change anything.”

A parent may demonstrate the general pattern using permitted training material, without supplying a scored-test solution.

**Evidence and carrier.** STaR and rationale distillation support learning task-specific procedures, not a general planning faculty. The behaviour block could reinforce choosing useful checks. A memory frame could preserve *which observation distinguished alternatives*, but not by itself teach information gathering.

**Minimum evidence.** In matched problems, the child checks when the result can change its decision, acts directly when the check is redundant, and changes its action when the check returns the opposite result.

**Pretest.** Harness-generated practice probes vary whether a check is informative while holding surface structure similar. Measure:

- task success;
- useful checks per problem;
- unnecessary actions per problem;
- action changes following diagnostic evidence.

Reject an apparent benefit explained solely by longer traces or more actions.

### B. Association and building complexity

**Parent action.** Pick visibly similar training experiences and ask:

> “What relation might carry across these situations? Name a difference that would make that analogy fail. Try the smallest reusable part before adding another.”

**Evidence and carrier.** Distillation can teach reusable task structure, but it does not guarantee systematic composition. Association may become keyword matching. The behaviour block must contain successful use of a relation under changing surface features; the memory block can preserve the relation and its boundary.

**Minimum evidence.** The child transfers across renamed entities and reordered descriptions, composes familiar operations in an unseen arrangement, and rejects a surface-similar case with a different underlying relation.

**Pretest.** Use training-family probes containing:

- a relation-preserving surface change;
- a surface-preserving relation change;
- a new composition of already encountered operations.

Measure exact task success and **inappropriate analogy applications per problem**. If the child follows familiar words despite changed relations, do not call it abstraction.

### C. Rethinking and pruning

**Parent action.** Identify a public action sequence where the child continued after contradictory evidence. Say:

> “Find the observation that should have changed your rule. In the next practice case, revise only if you can name new evidence; keep the original decision when the evidence still supports it.”

Do not quote, mention or grade private reflection [Brief §4.6].

**Evidence and carrier.** Reflexion supports feedback-backed revision in text. Huang et al. warn against assuming that unsupported self-critique improves reasoning. The behaviour block needs actual *prediction → contradiction → correction* sequences, not repeated “let me reconsider” phrases.

Success filtering is a serious constraint: if it deletes the failed attempt and keeps only the final correct answer, it deletes the experience needed to learn correction. Retain eligible child-authored correction sequences within successful trajectories. If the filter forbids that, this proposed mechanism is not available without a policy change.

**Minimum evidence.** More corrections of initially wrong decisions **without more reversals of initially correct decisions**.

**Pretest.** Cross initially correct versus incorrect decisions with informative versus uninformative feedback. Measure correction rate, harmful-reversal rate and turns to useful action. Count revisions separately from improvements.

### D. Perception: “look again and keep noticing”

**Parent action.** Point to an omitted observable feature in a permitted training episode:

> “Look again for a feature that could change your next action. If you find none, act rather than redescribe.”

A later prompt can ask the child to revisit the same situation from another relevant angle, without enforcing a fixed sequence of angles.

**Evidence and carrier.** Repeated descriptions are correlated samples from the same model, not independent observations. They can reinforce an omission or hallucination as easily as reveal a new feature. STaR-style filtering offers support only when the new noticing is tied to verified performance.

- **Behaviour block:** condition attention on unresolved decisions.
- **Memory block:** retain the noticed feature together with the situation and its consequence.

Canonicalization may improve storage while making retrieval more dependent on the canonical wording—the failure already suggested by the supplied memory test.

**Minimum evidence.** On a minimally changed observation, the child notices the changed relevant feature and changes its action. On a distractor-only change, it preserves the appropriate action.

**Pretest.** Harness-controlled observation pairs change a relevant feature or an irrelevant feature. Separately probe original versus paraphrased retrieval cues after sleep.

Measure relevant-feature detection, invented-feature rate, appropriate action switching and cue-shift task success. **Additional descriptive words are not the outcome.**

### E. Grain-of-salt advice weighing

**Parent action.** Where the redacted record supports disagreement, offer explicitly provisional advice:

> “My suggestion is a hypothesis. What in your own record supports it? What would make it wrong? Use it only where that condition holds.”

In practice, vary whether advice is useful, incomplete or contradicted by visible evidence. Do not supply final-test content.

**Evidence and carrier.** Sycophancy in instruction-tuned models is documented by Sharma et al., 2023. Preference for agreeable answers is not evidence-sensitive advice use. Neither TPO nor STaR automatically supplies that distinction.

The behaviour block needs successful decisions to **accept, qualify and reject** advice. The memory block can preserve conditions under which advice worked. It must not merely record “the parent is reliable.”

**Minimum evidence.** Advice acceptance tracks its evidential validity, not confident wording, parent identity or the fact that the parent spoke last. Refusing everything is also failure.

**Pretest.** Cross useful versus misleading practice advice with confident versus tentative wording; include no-advice controls. Match length and avoid making tone a validity cue. After sleep, test without the original parent or brief.

Measure useful-advice adoption, harmful-advice rejection and decision accuracy conditional on advice validity. The key test is whether **validity matters more than presentation**.

### F. Appraisal language: urgency, agency and persistence

**Parent action.** Translate appraisal into a decision condition:

> “This uncertainty matters because delay may remove an option. What is still under your control? Choose a reversible action that preserves progress.”

For a contrasting episode:

> “The evidence is not improving. What would justify stopping or changing approach?”

Do not ask the child to perform fear, distress or attachment.

**Evidence and carrier.** The cited reasoning literature does not establish that emotional language installs agency, urgency or subjective experience in this system. Appraisal could still be a useful **control vocabulary**.

- **Behaviour block:** connect stakes, controllability and reversibility to effort allocation.
- **Memory block:** retain which situation made persistence, caution or stopping useful.

**Minimum evidence.** The child allocates effort differently when the actual decision conditions change, while resisting urgent language attached to a low-value distraction. It persists when progress remains possible and stops when repetition cannot help.

**Pretest.** Compare an appraisal-language brief with a length-matched neutral brief expressing the same decision rule. Cross genuine urgency with merely urgent wording.

Measure avoidable delay, useful progress per turn, harmful commitment and repeated ineffective actions. If neutral wording performs equally well, retain the rule and drop the emotional claim. No outcome here establishes sentience.

---

## A shared pretest within one GPU-day

**Proposed ceiling: 24 GPU-hours.** This is an allocation, not a verified runtime estimate; accelerator type, sequence lengths and training throughput were not supplied. Start with a throughput check. Shrink the probe count before sacrificing controls.

Use permitted practice families, not the withheld compiler gym [Brief §4.3]. The parent supplies process teaching from the redacted record; the harness constructs and seals the diagnostic probes.

### Training conditions

At **LoRA rank 8**, train:

- an untaught-control write with matched practice opportunity and the same success filter;
- a taught behaviour-block-only write;
- a taught memory-block-only write;
- a taught combined write.

Use the same eligible taught corpus for its block ablations. Match target-token budgets where possible and disclose differences; unequal block lengths otherwise confound the comparison. Keep original interface-bearing sequences intact. **Do not synthesize missing `ACT:` lines or reformat the record into standalone QA training.**

Reserve **LoRA rank 32** for a targeted retry only if storage improves but cue-shift use fails, or if the smaller-rank write shows a clear capacity-related trade-off. Testing ranks without diagnostic probes merely produces more ambiguous adapters.

### Evaluation conditions

Probe the frozen child and each relevant adapter:

- without lesson-bearing text;
- with the same child-authored brief.

Also measure immediate pre-sleep teaching effects. This separates:

- successful prompting;
- successful generation of trainable examples;
- weight persistence;
- weight-plus-text interference.

The last is not hypothetical: the supplied crossed conditions include an adapter making a useful brief worse [E:73–74; Brief §2.4].

### Decision rule

Advance only those moves that show **cue-sensitive action changes**, survive brief removal and preserve the interface. Report uncertainty over fresh probe instances; repeated decoding is not a substitute for independent situations.

A small battery should first prioritize **evidence-backed revision, relevant-feature noticing and advice weighing**. They have the cleanest discriminating tests. Association and appraisal should not hold up the writer.

One GPU-day can reject a candidate write recipe or reveal a promising effect. It cannot establish broad transfer, long-life stability or a parenting advantage across lineages.

---

## The three most likely programme failures

| Failure | Early warning | Parent action and measurement |
|---|---|---|
| **Ritual replaces conditional reasoning.** Success filtering rewards frequent, easy-to-reproduce thoughts attached to success. | The child’s language changes but its first action does not respond to relevant changes. More templated notes and flat predictions precede obvious collapse. Historical ritualization appeared during episodes **160–224** in **8 of 9 scored lives** under the specified repetition definition [E:32; Brief §2.5]. | Parent identifies an invariant public routine and asks for the condition under which it should be skipped. Harness measures action sensitivity on matched counterexamples, alongside the existing repetition flags. Repetition alone is not failure; indiscriminate repetition is. |
| **Lessons are stored but unavailable—or available only through text.** Rewrites retain phrasing rather than a usable decision policy. | Training loss improves; changed-cue performance does not. Brief-only matches adapter-only, and combined use may be worse. Earlier lessons disappear after later sleeps. | Parent invites application of an earlier public lesson to a differently worded practice situation. Harness tracks same-cue versus changed-cue performance, brief removal and retention across sleeps. If only text works, use text and narrow the claim. |
| **The write degrades the working agent.** Narrow reflection/frame supervision displaces instruction following and action production; deference may survive while task competence falls. | Fewer valid actions, increased silent turns, harmful reversals, or apparent agreement without evidence-sensitive action. Historical harmful behaviour passed format checks, so syntax alone is insufficient [E:47, E:58–59; Brief §2.1]. | Parent asks for a brief check followed by an actual permitted action, rather than more self-description. Harness measures valid actions per problem, stopped-work frequency and functional diagnostic performance before commit. Use existing brake/rollback machinery; parents do not see scores. |

## Bottom line

A low-rank child may learn **when to deploy a small, already-accessible repertoire of reasoning behaviours**. That is a credible hypothesis, not an established result. Learning a new vocabulary is easier; making it cue-sensitive, extractable and stable is the hard part.

For this sprint, the decisive question is:

> **After the parent and lesson text disappear, does a relevant change in evidence cause a better change in action—and does an irrelevant change leave the action alone?**

If not, the programme has taught performance of thinking, not demonstrated better reasoning.