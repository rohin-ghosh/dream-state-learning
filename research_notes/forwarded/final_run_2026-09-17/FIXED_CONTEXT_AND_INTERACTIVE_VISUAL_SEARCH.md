# Fixed-context and interactive visual search

Companion protocol — 17 September 2026

Status: specification for parallel implementation. No experiments have been launched by creating this document. Complements NEW_YORKER_JUDGE_PIXELS_AND_THREE_ARM_TEST.md, version 2. The existing document supplies the judge, semantic-pixel calibration, and continual-learning controls. This document defines the two environment variants; implement both without changing running experiments.

## Purpose

Separate exploration of possible captions from exploration that also includes choosing what visual information to acquire. Both settings measure distinct accepted caption ideas. The interactive setting additionally lets the learner search over questions and observations that may lead to those ideas.

“Chained search” is descriptive terminology here, not a claim that the search space has a known mathematical size or dimension. The fixed-context agent can still think, revise, use files, and learn over time. Only additional visual information acquisition is disabled.

## Two settings

| Property | F: Fixed-context caption search | V: Interactive visual search |
|---|---|---|
| Task | Produce diverse acceptable captions | Produce diverse acceptable captions |
| Cartoons | Same three selected cartoons | Same three selected cartoons |
| Initial information | Same neutral descriptions | Same neutral descriptions |
| Further visual inspection | Unavailable | Optional factual questions to a frozen visual model |
| Output | Caption tied to cartoon ID | Caption tied to cartoon ID |
| Within-life memory | Continuous context and own files | Continuous context and own files |
| Reflection and revision | Allowed | Allowed |
| Main measure | Distinct accepted caption ideas | Distinct accepted caption ideas |

F holds supplied visual information constant; V permits additional observations. V therefore changes available information as well as the learner's choices. A V-F difference cannot by itself distinguish the value of extra information from the skill of choosing questions.

## Shared task and descriptions

Use the same cartoon IDs and byte-identical initial descriptions in matched runs. Prepare descriptions before experimental generation, from images without reference captions or scores. Include enough concrete information to permit plausible captioning in F. Do not deliberately impoverish descriptions to force V to win. Audit this on development cartoons, before main scene selection.

Omit explicit explanations of why the cartoon is funny from learner startup, unless their inclusion is registered for both settings. Keep known captions hidden from learners and parents. The fixed humor judge uses the same canonical scene inventory in both settings, generated independently from images. Its scores must not depend on an agent's private inspection history.

The same caption may be assessed differently from an agent's expectations if the agent lacks a scene detail. That information constraint is part of F. Select adequately described scenes before main runs; do not alter descriptions after observing which arm performs best.

Both settings allow free switching among all three cartoons within one life. Related ideas may transfer between scenes. Score each submission for its declared scene; report per-scene counts and allocation. Neither setting requires equal effort per scene or forced submission cadence.

## Tools and boundaries

Both settings receive submit_caption(contest_id, text), local notes, and the same public acceptance/duplicate feedback. Give both the same ordinary local computation tools. Keep raw image files, URLs that expose them, historical caption files, and external generative services inaccessible to the child except through the designated V interface. This restriction defines the information contrast; otherwise F could recreate the visual tool through another route.

V additionally receives inspect_image(contest_id, question, optional_region). The wrapper supplies the selected image each time. The visual model is frozen, stateless, and factual. It receives no historical captions, arm identity, child reasoning, parent messages, or quality scores. It must not generate captions, suggest joke strategies, or rank ideas. Follow-up questions explicitly identify the detail because the tool does not retain dialogue state. The child retains returned observations in its own transcript and files.

Use the response-length ceilings, total allowance, caching and failure handling in the main protocol. Freeze identical V limits across A/B/C. No minimum tool-use quota and no “submit after X questions” rule. F receives no pretend observations or dummy calls. Mark unavailable inspection requests explicitly rather than hallucinating responses.

The parent in C has only information available to its child through that setting and public feedback. In F it cannot inspect images privately and supply missing observations. In V it may recommend further inspection without supplying a caption or concrete joke. Match parent model, budget, process objective and withdrawal schedule. The tool-access facts in startup and parent instructions necessarily differ by setting; keep all other wording matched where applicable.

## Three learner arms in each setting

| Arm | Weight updates | Process parenting |
|---|---|---|
| A | Disabled | None |
| B | Continual LoRA sleep updates | None |
| C | Same LoRA sleep recipe as B | Present, then withdrawn |

There are six conditions: F-A, F-B, F-C, V-A, V-B, V-C. Use isolated contexts, files, adapters, optimizer state, RNG and parent ledgers for every life. Start from the same registered initial checkpoint. Never reuse a trained F agent as initialization for V or vice versa.

One seed block means six independent agent lives, each working on three cartoons: 18 condition-cartoon trajectories. Three seed blocks mean 18 lives and 54 trajectories. Cartoons within a life are correlated measurements, not independent replications. Parallel development of both environments does not require launching all main runs immediately.

Pilot: one seed block on development cartoons with the same short cap in all six conditions. Main, if resources allow: three seed blocks, with a common cap fixed from measured throughput before main. At 1M child output tokens per life, this is 6M tokens for one block or 18M for three, excluding external inference and training. These figures are accounting, not a power calculation. If resources are tight, use F as the primary experiment and V as a clearly labeled extension; decide before examining main outcomes.

## Endpoints and attribution

Use the same frozen scene-aware humor judge, pixel rule, thresholds, and caption constraints across all six conditions. Every life has its own chronological pixel archive with the same initialization rule. Pixels count accepted ideas, including ideas absent from human references; no denominator claiming total possible search space.

Primary for the paired-setting design: C-B difference in mean per-cartoon accepted-pixel count at the registered total-life token cap in F. This directly examines parenting among learners with fixed external information.

Key secondary: the corresponding C-B difference in V. A provides the frozen reference in each setting. Report V-F differences within each arm. The difference between the two C-B effects is exploratory evidence of whether access to visual inquiry moderates the parenting effect; it is not automatically an effect on learning itself. The missing frozen-parented arm still prevents identifying a parenting-by-weight-update interaction.

Additional information-acquisition logs: questions asked, tool costs, scene allocation, repeated questions, details returned, and timing of subsequent captions. These can support descriptive case studies. Do not count every new question or observation as a new caption pixel, and do not infer causality from temporal association alone.

A later optional control could give a fixed-context agent observations acquired by another agent. That would help investigate information quantity versus active selection, but introduces its own matching decisions and is outside this first six-condition design.

## Resource fairness

All generated child tokens, including questions, count toward the same lifetime budget. Visual replies consume context and external compute; they are not child-generated tokens. Report total model input/output usage, image processing, parent/judge costs, GPU training hours, and elapsed time. Equal child-token budgets do not equalize total compute, especially between F and V.

Use the same child-token cap for the primary comparison and report actual resource usage alongside results. Compute-normalized comparisons are secondary and require measured rather than invented cost equivalences. Attributing gains to efficiency requires those comparisons. Do not impose selective quotas or change budgets in response to a condition's apparent success.

Shared services may be deployed once, but learner data and caches must not expose another life's activity. Balance concurrent resource assignments or randomize execution order so one condition is not systematically throttled. Record backend faults and checkpoints; do not restart poorly performing lives from scratch without reporting it.

## Implementation deliverables and checks

Build one environment wrapper with an explicit immutable setting flag: fixed_context or interactive_visual. Store it in every run's configuration and logs. Reuse the judge, archive, training, parent and submission infrastructure.

Before launch verify:

1. All six conditions receive identical initial scene text and their intended tool-access facts.
2. F cannot obtain additional image observations through files, parents or another model endpoint.
3. V factual responses do not provide captions or hidden reference material.
4. Given identical caption text and scene ID, scoring is identical across settings and arms.
5. Histories, adapters and files remain isolated; no cross-condition learning data is mixed.
6. Token/cost accounting includes questions and external responses in the correct separate fields.
7. Main scene IDs, seeds, budgets, evaluator versions and parent settings are frozen after development.

Retain raw outputs for independent blinded audits. Report null effects, evaluator errors and failures. This experiment tests sustained accepted-caption coverage under two information-access conditions; it does not establish the total size of either search space.

## References and implementation context

- Dataset: https://huggingface.co/datasets/yguooo/newyorker_caption_ranking
- Caption benchmark paper: https://arxiv.org/html/2406.10522v1
- Author code: https://github.com/yguooo/cartoon-caption-generation
- Main companion: NEW_YORKER_JUDGE_PIXELS_AND_THREE_ARM_TEST.md, version 2 (judge, pixels, visual-tool contract, training controls).

The documents are specifications only. No judge, visual wrapper, or main experiment was executed as part of this update.
