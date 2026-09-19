# Overnight preliminaries — September 19, 2026

Use the submitted abstract below as the research direction. Tonight, gather useful preliminary evidence and get the machinery ready. Rohin will direct the larger experiments during the day.

1. **Check the current state.** Identify which agents, checkpoints, environments, and evaluation paths are usable. Confirm that actions, feedback, sleep updates, and logs actually connect.
2. **Run a few small, informative probes.** Use existing setups to inspect whether reflection changes the next action, whether a correction survives sleep or compaction, and what happens without a parent. Where practical, compare a frozen baseline under the same evaluation budget. Label these preliminary findings.
3. **Clear straightforward blockers.** Fix and verify small implementation issues that prevent useful tests. Preserve ongoing runs and checkpoints; flag larger architectural decisions for Rohin.
4. **Prepare the daytime work.** Identify what is ready and what remains missing for parented/unparented × LoRA/frozen comparisons. Prepare runnable commands and rough time/cost estimates for the most promising next experiments.

**Morning handoff:** A short summary of what ran, what it showed (with receipt links), what is blocked, and two or three recommended next steps. Leave the major experiment choices to Rohin's daytime directives.

## Submitted abstract

*Animating Intelligence: Language-Guided Development of Continually Learning Agents*

[ICLR 2027 OpenReview portal](https://openreview.net/group?id=ICLR.cc/2027/Conference) — individual submission link pending.

<details>
<summary>Read the submitted abstract</summary>

Language models can articulate sophisticated strategies for reasoning, exploration, and self-correction, yet may fail to initiate or sustain those strategies during extended activity. We investigate whether developmental guidance can help models acquire stable routines for drawing on these promptable capabilities while flexibly determining what to investigate, how to interpret experience, and how to act. We call this process animating intelligence. Our framework pairs a continuously operating language model, the learner, with a language-model parent that provides intermittent guidance through questions, targeted probes, demonstrations, and feedback across grounded tasks. These interventions encourage the learner to examine its approach, draw on relevant knowledge, and translate its judgments into actions. The learner alternates reflection and action, maintains working context, and periodically trains a low-rank adapter on its own generated experience while keeping the base model frozen. Guidance addresses task outcomes and the processes of exploration, judgment, and learning within and across successive attempts, without optimizing the parenting process through an explicit scalar task reward. The framework connects two adaptation timescales: in-context reflection revises immediate reasoning and action, while periodic weight updates aim to consolidate reusable patterns for directing subsequent reasoning and behavior.

Preliminary observations show concrete checks leading to revised judgments and continued investigation, alongside failures to enact articulated corrections and recurring unproductive patterns. In a cartoon-caption generation task, exploratory coverage measured under equal token budgets varies across developmental checkpoints, with early gains over a frozen base diminishing after further development. These findings motivate a factorial evaluation separating parenting from continual weight updates, with parent-free assessments of retention, transfer, and sustained exploration. We investigate when guided experience produces behavioral changes that persist beyond the immediate interaction and support further adaptation.

</details>
