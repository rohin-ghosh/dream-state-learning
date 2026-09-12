# Abstract draft v2 — lifetime parametric learning (2026-09-06)

Status: **archival and superseded by
`abstract_experience_models_v3_one_parent_causal.md`.** Bracketed outcome
language was never claimable. This file preserves the earlier topology for
history and must not guide implementation or current paper wording. The
superseded social topology was fixed:
one frozen, reset, target-blind parent teaches one child; there is no
classroom, cohort, peer exchange, teacher ensemble, or population-learning
mechanism.

Language agents can already learn from their own interaction data through
batch experience distillation, and they can adapt at test time through
evolving textual memory. These paradigms leave a gap: the first trains one
fleet policy after collecting a dataset, while the second keeps the acting
policy fixed and carries each life only in context. We study a third setting,
**per-life parametric learning**, in which one deployed agent periodically
consolidates its own prospectively recorded thoughts, typed actions, observed
outcomes, and corrections into a small low-rank state attached to a frozen
base model. The same model performs ordinary reasoning and action; an
experience compiler selects verified recovery pathways and trains native,
response-only continuations, while an append-only ledger keeps context
distillation reversible. Before deployment, one parent teaches process-level
thinking by assigning target-blind tasks, eliciting thought into action, and
proposing corrections whose lessons are admitted only when supported by
public task outcomes. The parent and every childhood-only artifact are then
deleted. The central test is not whether action data can fine-tune a model,
but whether repeated within-life writes make this parented child learn faster
from later, parent-absent experience, without interface drift, negative
transfer, or forgetting. In a streaming optimization gym, the public figure
compares the deployed Think--Dream--Sleep learner (`P1`) with a strong
frozen-parameter active-text agent (`R0`) under matched deployment
affordances. A dose-matched `U0/U1/P0/P1` factorial separately identifies
whether parenting changed the marginal benefit of later personal writes,
rather than merely improving entry competence. We also compare native
continual LoRA, one-shot Early-Experience/LEAFE-style batch distillation, and
active textual-memory refinement. We evaluate lifetime learning curves,
first-action and equal-token value, forward and backward transfer,
typed-action compliance, and adapter-removal, wrong-life, and
shuffled-experience controls. Our initial long-life scout
reveals the key failure mode: naive bare-text LoRA training can preserve
useful action proposals while teaching the agent to serialize them outside
its executable interface, collapsing registered task value. [A successful
paper must then show that native-format, low-heat consolidation crosses the
frozen/textual/batch controls on prospectively sealed tasks.] This frames
experience compilation as an online stability–plasticity problem for an
individual acting policy, rather than memory retrieval or batch agent
post-training alone.

## Evidence boundary

Currently supported, descriptively:

- naive periodic LoRA writes can cause persistent interface collapse;
- at B2 episode 1,024, strict task value was `0.0511`, while a post-hoc
  permissive extraction of the saved first action scored `0.5287` and the
  paired adapter-off panel scored `0.4859`;
- this localizes a proposal-versus-routing failure but is not a controlled
  learning benefit because the run lacked common generation seeds and clean
  causal/provenance receipts.

Still required before the bracketed positive sentence is usable:

1. prospectively bound typed-action and public-outcome traces;
2. native-format response-only writer calibration with behavior rehearsal;
3. parent-absent absorption under wrong-life/shuffled/adaptor-off controls;
4. a clean repeated-write lifetime protocol with common randomness;
5. active textual-memory, Early Experience, and LEAFE-style batch baselines;
6. cross-environment forward/backward-transfer and forgetting endpoints.
