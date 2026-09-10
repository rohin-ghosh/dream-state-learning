# Developmental metacognition and scaled THINK: evidence map

Date: 2026-09-09

Status: **evidence-only discussion artifact**. This note chooses no architecture,
protocol, prompt, curriculum, corpus, SLEEP-eligibility rule, model, tokenizer,
benchmark, rank, dose, compute budget, child lineage, statistic, or claim. It
authorizes no implementation, execution, fit, GPU/resource use, release, or
publication. Rohin requested that Codex discuss the design with Fable before
formalization; the bound Fable response is still pending at writing.

## The narrow question

The base model plainly contains language for reasoning, correction, social
interaction, and self-description. The developmental hypothesis is therefore
not that parenting creates chain-of-thought from nothing. It is that repeated
practice, feedback, reflection, and later personal consolidation can change
the child's **policy for using those existing capabilities**:

- when to open another route;
- when to deepen the current route;
- when to seek discriminating evidence;
- when an outcome should revise a named belief;
- when to compare with prior experience;
- when to take an outside view of its process; and
- when further recursion has low value and action should resume.

This distinction is an experimental hypothesis, not an established property
of the current child.

## Relevant human-learning evidence

### Attempt before instruction

Kapur's productive-failure studies show that an unsupported initial attempt
can improve later conceptual and transfer performance when followed by
instruction, even when the initial attempt fails. Later controlled work found
that the number and diversity of student-generated solutions during the
attempt phase can predict learning. This supports testing **productive search
before parental correction**, not treating initial task score as the complete
value of an episode.

- Kapur (2008), *Productive Failure*:
  https://doi.org/10.1080/07370000802212669
- Kapur (2014), *Productive Failure in Learning Math*:
  https://doi.org/10.1111/cogs.12107

It does not establish that unlimited search is useful, that arbitrary failure
teaches, or that model-generated alternatives should all become weight-update
targets.

### Self-explanation and explaining to a listener

Chi et al. found that stronger learners spontaneously produced more
self-explanations, refined the conditions under which actions apply, connected
steps to principles, and monitored their understanding. Rittle-Johnson and
colleagues found that prompting young children to explain improved later
problem solving; in one study, explaining to a familiar listener produced
greater transfer than self-explanation alone. Legare and Lombrozo found that
explanation selectively improved causal learning and generalization rather
than memory for irrelevant perceptual detail.

- Chi et al. (1989), *Self-Explanations: How Students Study and Use Examples
  in Learning to Solve Problems*:
  https://doi.org/10.1207/s15516709cog1302_1
- Rittle-Johnson, Saylor, and Swygert (2008), *Learning from explaining: Does
  it matter if mom is listening?*:
  https://doi.org/10.1016/j.jecp.2007.10.002
- Legare and Lombrozo (2014), *Selective effects of explanation on learning
  during early childhood*:
  https://doi.org/10.1016/j.jecp.2014.03.001

This supports high-dimensional parent--child conversation as a candidate
THINK treatment. It does not show that lexical repetition is learning, that a
self-description is true, or that every conversational statement should be
trained into parameters.

### Error explanation needs scaffolding

A recent two-experiment study found that merely asking learners to explain
errors was weak; structured prompts improved error correction and near
transfer, but not far transfer. The relevant lesson is that "reflect more" is
not a sufficient teaching operation. Reflection must direct attention to the
failed inference, relevant evidence, and a changed future procedure.

- Zhang and Fiorella (2024), *Effects of self-explaining feedback on learning
  from problem-solving errors*:
  https://doi.org/10.1016/j.cedpsych.2024.102326

### Modeling, guided practice, and transfer of responsibility

Reciprocal teaching makes a teacher initially model a small set of cognitive
operations--questioning, clarifying, summarizing, and predicting--then provide
corrective feedback while responsibility shifts toward the learner. This is
evidence for scaffold fading and child execution, not for indefinitely showing
the same instruction.

- Palincsar and Brown (1984), *Reciprocal Teaching of Comprehension-Fostering
  and Comprehension-Monitoring Activities*:
  https://doi.org/10.1207/s1532690xci0102_1

### Near transfer is common; far transfer is not automatic

A double-blind active-controlled study of children found durable improvement
on trained and related working-memory measures, with some additional
near-transfer from metacognitive strategy training, but no reliable additional
benefit on mathematics or reading comprehension. Dynamic strategy training in
children has similarly improved trained problem-solving trajectories without
necessarily improving a distinct transfer task.

- Jones et al. (2020), *The academic outcomes of working memory and
  metacognitive strategy training in children*:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7379186/
- Resing et al. (2016), *Dynamic testing and transfer: An examination of
  children's problem-solving strategies*:
  https://doi.org/10.1016/j.lindif.2016.05.011

This is the main warning for the parenting thesis: uptake on one rule game is
not learning-to-learn. Candidate metacognitive operations must recur across
different task surfaces, and parent-absent transfer must be measured rather
than inferred from fluent reflection.

## Relevant model-reasoning evidence

### Parallel breadth can outperform one greedy path

Self-consistency samples multiple reasoning paths and aggregates their answers;
it reported sizeable gains on several arithmetic and commonsense benchmarks.
Tree of Thoughts explicitly explores, evaluates, and backtracks among coherent
candidate routes and substantially improved selected search-heavy tasks. These
results support Rohin's hypothesis that parallel breadth can expose routes a
single continuation misses.

- Wang et al. (2022), *Self-Consistency Improves Chain of Thought Reasoning in
  Language Models*: https://arxiv.org/abs/2203.11171
- Yao et al. (2023), *Tree of Thoughts*: https://arxiv.org/abs/2305.10601

They establish an inference-time search effect, not durable learning, child
continuity, or valid SLEEP targets. They also confound topology with extra
sampling unless total generated compute is separately matched.

### More sequential thought can hurt

The repository's resolved D3 condition moved from **0.83 without CoT to 0.35
with CoT** (`research_notes/IDEAS.md`, lines 126--128): an internal example
where additional explicit reasoning degraded performance. Recent external work
also reports non-monotone test-time scaling and proposes parallel rather than
ever-longer sequential thought as a remedy.

- Ghosal et al. (2025), *Does Thinking More Always Help?*:
  https://arxiv.org/abs/2506.04210

Therefore trace length, route count, and self-critical statement count are
diagnostics, not success criteria. The developmental target is allocation of
thought where another route or another layer has expected value.

## Current repo evidence that constrains the design

1. The current base/adapter stack can emit the THINK dialect and respond to
   in-context correction. This is consistent with existing reasoning and
   instruction-following priors; it does not prove durable metacognitive
   control.
2. A waking parent brief delayed ritual onset in all three exploratory
   parented old-writer lives and produced one four-window remission, but the
   ritual later returned. Immediate uptake is not persistence.
3. First-NOTE rehearsal reached roughly `0.50--1.00` in the three reported
   parented lives. This proves prompted echo/rehearsal, not selective use.
4. The old writer produced late-life harm in `3/9` unparented lives while the
   exploratory parented set had `0/3`; both the writer path and small root count
   forbid a parenting-safety claim.
5. One harmful adapter retained parseable action syntax while reducing work
   from about `13` to `1--2` chunks per episode. Interface correctness and
   useful cognitive persistence are different axes.
6. The objective-coverage audit shows that the one-parent experiment alone
   does not establish connected/compressed parametric knowledge, traversal, or
   expansion. Developmental teaching and experiential-knowledge mechanism
   need related but distinct evidence arcs.

## Design-facing observations to discuss with Fable (not decisions)

1. Separate THINK compute into **breadth** (independent candidate routes),
   **depth** (continuation on one route), and **post-outcome reflection**.
2. Compare parallel and single-route thinking at matched total generated
   tokens to identify topology, then compare generous high-budget packages to
   measure the practical total-system effect.
3. Let one continuing child inspect and synthesize candidate routes before one
   committed action. Do not equate temporary thought branches with parallel
   child lives.
4. Preserve speculative branches in the lossless ledger if desired, but do
   not automatically turn every abandoned statement into a SLEEP target.
   A child-authored later synthesis can retain useful branch content without
   training contradictory raw drafts equally.
5. Treat world/procedure claims and first-person provisional perspectives as
   different semantic classes. The former require action--outcome grounding.
   The latter, if ever eligible, need repeated cross-context endorsement,
   explicit uncertainty, counterevidence sensitivity, and a separately
   deliberated self-reinforcement safeguard.
6. Keep the longitudinal child across changes in subject matter and teaching;
   take immutable age snapshots and fork siblings for comparisons. A change to
   THINK/DREAM/SLEEP, writer, rank, masks, eligibility, or promotion semantics
   starts a new mechanism lineage.
7. Let the parent improve nonparametrically from both immediate and delayed
   outcomes. Development may adapt freely within governance; confirmation must
   either freeze the policy or predeclare the complete adaptive update rule.

## Candidate high-dimensional questions (exploratory only)

- What have you started to believe about how you personally learn, and what
  evidence would change that belief?
- Which repeated behavior is a justified method, and which is merely a habit
  that succeeded once?
- What two explanations for your recent outcomes remain live, and what is the
  cheapest observation that separates them?
- What would an outside observer distrust about your recent reasoning?
- When did another layer of thought change an action, and when did it merely
  delay one?
- What does your parent currently misunderstand about how you learn?
- Which intention should survive the next context reset, and what event should
  trigger it?
- What have you made automatic that still deserves conscious review?

Durable perspective must be distinguished from copied wording by semantic
stability after context reset, situation-sensitive expression, calibrated
revision under counterevidence, and a prospective relation to later choices.

## Open empirical questions

- Does parallel breadth add value after matching total generated tokens?
- Does the child learn to choose breadth, depth, or action rather than merely
  consume whichever budget it is given?
- Which branch information, if any, can be consolidated without causing
  contradiction, indecision, or self-imitation drift?
- Can a perspective persist while remaining corrigible, or does personal SFT
  merely make its wording sticky?
- Do the same metacognitive operations transfer across task families, or does
  each classroom teach a local performance ritual?
- Does continuity make teaching compound, or does it mainly compound the
  writer's existing biases?
