# Dream-State Learning: where the idea currently stands

Working research narrative — 17 September 2026

This is a record of the direction emerging from our discussions, not a ruling, implementation specification, or claim that the hypothesis is already demonstrated. It should help a collaborator understand what Rohin is trying to get working and why the current experiment was chosen. The execution handoff governs the immediate build; this document explains the motivation behind it. Both can evolve with evidence.

## The core idea

The ambition is to help a pretrained model turn more of what it can describe and reason about into behavior it actually sustains, then learn from the experience that behavior creates.

A model may be able to explain reflection, persistence, memory, uncertainty, experimentation and changes of strategy without reliably using those abilities during an extended run. Our working hypothesis is that a continuous agent, given a way to update its weights from experience and guidance about how to use that opportunity, may develop a more effective ongoing exploratory process.

The phrase we have repeatedly returned to is **turning intelligence into behavior**. Here, “intelligence” means the model's available repertoire of knowledge and reasoning abilities. “Behavior” means how it allocates attention, records experience, revisits questions, uses tools, changes approach and produces actions over time. This is a useful research distinction, not a claim that these are cleanly separable components inside a network.

The intended feedback loop is: behavior creates experience; the agent works with that experience; sleep updates consolidate selected or compiled material under the training recipe; the changed model then generates further behavior and experience. Parenting is meant to help this loop become useful without specifying every action it must take.

## What we are trying to get working first

The first goal is an agent whose behavior makes productive use of having both continuity and a trainable adapter.

This is more specific than having a model generate for a long time or showing that LoRA changes its responses. We want to see whether the agent can develop ways of operating that help it continue exploring: recognizing an exhausted approach, preserving a useful distinction, returning to an earlier idea with a change, or using an observation to open another direction.

An action might be valuable because it improves a later learning opportunity, even when it does not immediately yield the best answer. For example, the agent could investigate a visual detail, compare several interpretations, or articulate why its recent attempts have become similar. The hypothesis is that some such behavior can become useful experience for subsequent adaptation.

We are not assuming that every reflection is useful training data. Nor does the agent need a correct verbal theory of LoRA for the system to benefit. Explaining its actual memory and update mechanisms gives it information it may use; whether that explanation changes behavior is an empirical question.

The aspiration is for the agent to participate in shaping how it learns, within a runtime and training procedure that we still define. The present implementation is not complete autonomy over its own optimization.

## Why continuity, sleep and parenting belong together

**Continuity** gives a suggestion or experience time to affect later activity. The agent can attempt something, encounter a consequence, revisit it and continue from the resulting state. The relevant property is preserved usable state across interactions and sleeps. An uninterrupted token stream or suppressed end token alone does not establish that property. Compaction, files, context handling and recovery are part of the mechanism.

**Sleep** gives some experience a route into parameter updates. The base model remains frozen while LoRA changes. We are building on the existing experimental sleep recipe, but the claim that a particular recipe works must remain attached to its actual evidence and conditions. Updating an adapter does not guarantee improvement, retention or preserved access to base capabilities.

**Parenting** provides responsive guidance. A parent may notice repetition, ask the child to reconsider its approach, or encourage it to make better use of memory. The aspiration is to influence a process that the child carries forward through its own activity, rather than supply each caption or dictate an entire sequence. In practice, this remains an externally influenced system; communication does not make that influence disappear.

The current development design parents both agents from their first loop. That is deliberate. A capable continuous agent with context, files, tools and guidance is the comparison we want. The difference under examination is what ongoing adapter updates add to that functioning system.

## Persistence and metacognition: useful starting ideas, not a script

Earlier discussions emphasized more tokens and richer thought. That narrowed toward two candidate behavioral ingredients:

- **Persistence:** continuing worthwhile engagement beyond the first adequate response or first unsuccessful approach.
- **Functional metacognition:** evaluating and changing how effort is being spent, using observable behavior and available feedback.

Neither should require a fixed number of branches, an introspective paragraph every turn, or endless self-questioning. We want room for the model to choose when to explore, act, revisit, consolidate or change direction. Curiosity may create useful experience without an immediate payoff, but verbosity and curiosity are not interchangeable.

“Learning to learn” remains a motivating description. Demonstrating it would require evidence that the agent improves how it acquires or uses experience, not merely that its outputs change. The current experiment tests a narrower consequence that could support further investigation of that idea.

## How the scope narrowed

The long-horizon proposal originally included developmental exploration, consolidation, diverse outcome-grounded environments, eventual deployment and agents helping develop successor agents. That remains a possible research program. It is much larger than the present paper.

Within that program, exploration and consolidation need not be strictly separate stages. The working view became an ongoing alternation: explore, preserve or consolidate what emerges, then explore from the changed state. There can be short investigations inside longer trajectories. We do not yet know which timescales or training representations make this effective.

We then looked for an observable outcome earlier than broad task mastery or recursive self-improvement. The question became whether adaptation could help an agent sustain differentiated exploration over a long horizon.

Simply measuring non-repetition was insufficient. A stream can remain different through irrelevant variation, and repeated behavior can be useful. Trying to measure the entire semantic space of all internal text also made the evaluation difficult to define and validate.

That led to the present compromise: **observe the breadth of acceptable ideas produced in a bounded language task**. Internal activity can remain flexible; the task supplies a common place where some of its consequences become inspectable. This does not capture every valuable thought. It gives us a tractable window onto exploratory behavior.

## Why the cartoon-caption game fits the current question

The New Yorker task keeps the agent close to language, interpretation and associations. A fixed scene can support multiple joke premises, viewpoints and ways of expressing them. A factual visual tool also lets the agent investigate details rather than receive only one short description.

We are interested in discovering distinct acceptable caption ideas over an extended budget. We are not primarily asking which agent writes the single funniest caption. That separates exploration breadth from the later problem of choosing and refining the best outcome, although a minimum acceptance criterion still matters.

“Outcome coverage” or “distinct acceptable idea coverage” is a more precise current term than literal “surface area.” The surface-area metaphor expresses the motivation: how much differentiated ground does the system reach? The operational measure depends on a humor judge and a definition of when two captions express the same joke idea. Neither defines the total possible space.

The factual tool creates an additional route for exploration through questions about the image. Our coverage measure remains on submitted captions. It does not directly measure the diversity or usefulness of all visual questions and intermediate reasoning.

## The working hypothesis and the question we can actually test

**Broader working hypothesis:** responsive guidance and experience-based adapter updates can help a continuous agent develop behaviors that make its subsequent experience more useful, supporting sustained exploration over longer horizons.

**Current experimental hypothesis:** with matched initial information, tools, parenting policy and child-token budgets, a parented continuous agent that continues updating its LoRA will discover more distinct acceptable caption ideas, or sustain their discovery later into the run, than a comparable parented continuous agent with frozen weights.

The second is an observable prediction motivated by the first. It is not equivalent to the first.

A coverage advantage could result from several mechanisms: retention of useful patterns, adaptation to the caption task, changes in output style, or more effective exploration. It would not by itself identify improved metacognition or a general ability to learn how to learn. Mechanistic claims would need additional evidence or ablations.

Likewise, both conditions receive parenting. This comparison does not isolate the causal contribution of parenting. It tests enabling ongoing updates inside a parented continuous system. The parent follows the same policy but responds to each child's actual behavior, so the resulting trajectories and messages can differ.

The relevant baseline is not assumed to fail. Context, files and tools can support sustained activity without online weight updates. Whether LoRA adds value, how much and at what cost are the questions.

## What different outcomes would mean

| Outcome | What it would suggest |
|---|---|
| More audited acceptable ideas, with continued gains late in the run | Evidence that the updating system sustains greater task-level coverage under the tested conditions. |
| More raw pixels, but the advantage disappears under acceptance or duplicate audits | An evaluator issue or an unsupported apparent gain; not evidence of expanded useful coverage. |
| Behavioral change without a coverage advantage | Adaptation occurred, but the proposed exploratory benefit was not demonstrated here. |
| Strong performance in both conditions | A meaningful result about the strength of parented continuity; ongoing updates may add little at this budget or on this task. |
| Learner deteriorates, repeats or loses useful capabilities | Evidence about failure of this recipe or setting, and a reason to inspect the update process rather than assume more time will fix it. |

Longer runs may reveal effects that short runs miss, but that is a hypothesis, not a reason to reinterpret every negative result as insufficient scale. We should report the tested horizon and observed trajectory without promising eventual grokking or a later crossover.

## A possible paper shape

The most defensible current paper would study **sustained exploration in a parented continuous agent with online adapter learning**.

Its contribution could combine a concrete continual system, a task-grounded coverage evaluation, and evidence about when ongoing updates help or harm exploration. The strength of that contribution depends on results, evaluator validity, comparisons and a proper related-work review. A new combination or a compelling philosophy does not automatically establish novelty.

A possible working title is:

> Sustaining Exploration in Continuous Language Agents through Experience-Based Adapter Learning

A more neutral title, suitable before results, is:

> Evaluating Ongoing Adapter Learning in Parented Continuous Language Agents

An abstract skeleton, deliberately without invented findings:

> Pretrained language models can describe strategies for reflection, memory and exploration, yet sustaining those behaviors during extended interaction remains an empirical challenge. We study a continuous agent that receives responsive process guidance and periodically updates a low-rank adapter from its experience. Our working hypothesis is that ongoing adaptation can support sustained discovery of differentiated task-relevant ideas. We compare two parented agents with matched starting information, tools and interaction budgets, enabling online adapter updates in one condition. In a cartoon-caption task, we evaluate cumulative coverage of distinct acceptable ideas across increasing token budgets, with independent checks of acceptance and semantic duplication. [Insert measured effects, uncertainty, costs and failure cases.] The study examines whether ongoing weight adaptation adds exploratory value within a guided continuous system; it does not establish general self-improvement or the causal effect of parenting alone.

This is a direction for an abstract, not submission-ready text. The final wording should follow what the experiments support.

## What remains open

We still need to learn which guidance elicits useful behavior, which experiences the sleep pipeline should consolidate, whether diversity survives adaptation, and whether the evaluator tracks distinctions people consider meaningful. We also do not yet know whether any advantage would transfer beyond these cartoons or persist under different parents and training recipes.

The long-term language of self-knowledge, developmental maturity and successor lineages belongs in motivation or future work for now. The earlier dimensional analogy—knowledge becoming a basis for acting on one's own behavior—is an intuition, not a mathematical account of model dimensionality. “Sentience” is not an operational claim or an endpoint of this experiment.

The current commitment is smaller and concrete: get a continuous, parented learner to use its update mechanism without losing functional behavior, then test whether that mechanism helps it keep discovering distinct acceptable ideas. The broader theory gives this experiment its purpose. The experiment should be allowed to change the theory.
