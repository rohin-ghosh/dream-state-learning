# External lifetime-environment audit

**Date:** 2026-09-02  
**Status:** read-only scientific advisory. This is not an architecture
consensus, ratification artifact, implementation authorization, execution
approval, or scientific-claim approval. No repository files other than this
advisory note were modified; no model, network experiment, or GPU run was
performed.

## Question and conclusion

Question: can an existing agent environment or benchmark be wrapped within
roughly two weeks into a true increasing-lifetime, action--outcome
experiential-learning study suitable for Paper 1?

**Conclusion:** no released environment natively supplies all of: a fresh,
persistent, hidden per-life rule family; action-dependent observations;
resettable worlds; long-lifetime scale; and the target/twin causal attribution
needed by PCFL. Every candidate requires a wrapper. For an external check,
MiniHack is the best practical **confirmation/sentinel**, not Paper 1's
primary evidence. PCFL-Stream remains stronger for the primary causal,
leakage, and growth-curve claims.

A MiniHack result could show that a memory treatment transfers to genuine
stateful action consequences under a recognized simulator. A positive result
does not broaden the Paper-1 claim beyond that; a null result does not by
itself invalidate PCFL.

## Evidence from primary papers and official repositories

- **MiniHack** is a maintained Gymnasium environment with resettable instances,
  custom levels, a level generator, configurable reward events, custom
  subclasses, and optionally language-form actions. [Official
  repository](https://github.com/facebookresearch/minihack) and [custom
  environment interface](https://github.com/facebookresearch/minihack/blob/main/docs/getting-started/interface.md).
- **TextWorld** can generate custom text games and exposes `reset`, `step`,
  reward, completion, and move-count interfaces. [Official
  repository](https://github.com/microsoft/TextWorld).
- **DiscoveryWorld** supplies interactive scientific actions, seed variations,
  normalized partial scores, task scorecards, and full action/history APIs. Its
  official benchmark is 120 theme/difficulty/seed tasks. [Official
  repository](https://github.com/allenai/discoveryworld); [primary
  paper](https://arxiv.org/abs/2406.06769).
- **ScienceWorld** exposes many task variations, reset/step, a 0--100 score,
  and action/object-combination interfaces, but its scientific mechanics and
  task families are fixed and published. It requires a Scala/JAR/Java stack.
  [Official repository](https://github.com/allenai/ScienceWorld).
- **ALFWorld** provides aligned text and embodied household environments and an
  admissible-command interface, but its task semantics are released and fixed.
  [Official repository](https://github.com/alfworld/alfworld); [primary
  paper](https://openreview.net/pdf?id=0IOX0YcCdTn).
- **AgentGym** is an integration framework over 14 heterogeneous ReAct-format
  environments rather than a single controlled lifetime world. [Official
  repository](https://github.com/WooooDyy/AgentGym).
- **ARE/Gaia2** provides dynamic multi-application scenarios and exact
  benchmark validation, but its 800 scenarios across 10 universes do not
  provide a controlled latent rule persistent through one life. [Official
  repository](https://github.com/facebookresearch/meta-agents-research-environments);
  [primary paper](https://arxiv.org/abs/2602.11964).
- **Voyager** already occupies Minecraft lifelong-learning/skill-library
  territory and brings a substantially larger Minecraft, Node, Python, and
  GPT-4-oriented integration. [Official repository](https://github.com/MineDojo/Voyager);
  [primary paper](https://arxiv.org/abs/2305.16291).
- **Crafter** has meaningful achievement scoring and procedural maps, but fixed
  mechanics and visual control make it a poor local-7B/32B action-language
  assay. [Primary paper](https://arxiv.org/abs/2109.06780); [official
  repository](https://github.com/danijar/crafter).

The factual interface statements above are sourced evidence. The feasibility
and role judgments below are design inferences from those interfaces and the
PCFL visibility/claim contracts, not experimental findings.

## Ranked shortlist

| Rank | Environment | Fresh hidden per-life rules | Action-dependent observations / reset / scoring | Local 7B/32B and two-week feasibility | Paper-1 role |
|---|---|---|---|---|---|
| 1 | **MiniHack** | Not native; needs a small protocol wrapper counterbalancing opaque labels to native mini-skills | Yes / yes / exact terminal and reward events | Best practical balance; language adapter and small discrete action space; 32B preferred, 7B plausible with constrained commands | Appendix/sentinel only |
| 2 | **TextWorld** | Strongest technical controllability through generated games | Yes / yes / exact reward, win, and moves | Fastest to implement and local-model friendly | Engineering sentinel only; too close to another bespoke world |
| 3 | **DiscoveryWorld** | Native experimentation, but no clean fresh persistent per-life latent | Yes / yes / normalized scorecards | Medium-to-low; large observations and scientific-task burden; 32B more plausible | Later ecological robustness check, not a two-week primary cell |
| 4 | **ScienceWorld** | Variations but fixed, published scientific laws and task generator | Yes / yes / exact score | Medium-to-low because JVM stack and task difficulty | Avoid for Paper 1 |
| 5 | **ALFWorld** | No usable fresh per-life rule absent invasive change | Yes / yes / task completion | Setup manageable; local 7B likely weak | Avoid |
| 6 | **Crafter** | No; mechanics fixed | Yes / yes / achievement geometric mean | Poor fit for text-only local models and LoRA-read attribution | Avoid |
| 7 | AgentGym, ARE/Gaia2, Voyager | Not controlled at the required per-life causal level | Interactive, but complex | Integration/evaluation cost exceeds two weeks | Avoid |

## Minimal MiniHack sentinel wrapper

Use a fixed-source **per-life protocol** over native MiniHack interactions;
do not change NetHack mechanics.

1. At life creation, sample a secret permutation for each cohort:
   `opaque protocol label -> native MiniHack micro-skill`. Use a small,
   observable native skill set, such as acquiring/using a required item,
   unlocking/opening, crossing an obstacle, avoiding a trap, defeating with a
   required tool, and navigation to a goal.
2. Each cohort introduces fresh nonce labels and new map/distractor
   instantiations. Early calibration episodes force actual attempts and return
   ordinary environment feedback/reward; labels persist through the life.
   Later held-out targets require one or two old/new protocol labels in a new
   map, so no stored episode directly gives the target action.
3. Generate one pre-native and at least three tokenizer-measured post-native
   checkpoints. Report new-label acquisition, old-label retention, two-label
   cross-era completion, terminal success, reward, excess moves/regret against
   an engine shortest valid solution, raw-life tokens, retained bytes, and
   writer/training/query cost.
4. Freeze source-life episodes and target manifests before memory compilation.
   This supports a matched fixed-source C0--C3-style experiment only; it is
   not an on-policy evidence-acquisition result.
5. Keep the sampled permutation solely in the generator/scorer. It must not
   appear in prompts, filenames, caches, candidate lists, training labels,
   diagnostics, or retrieval indices. Use fresh nonces and whole-life
   label-swap twins.
6. Compare no memory, honest/truncated context, raw episodic RAG, linked
   external memory, direct trajectory/QA LoRA, target-blind compiled text, and
   identical-corpus compiled LoRA. Reset the MEMORY adapter for every
   `(life_id, twin_id)` and freeze the base and reusable controller.
7. Require whole-life authentic-versus-twin text/adapters, candidate-only clean
   base, wrong/twin adapter, complete decisive text-memory cuts, and a smaller
   paired LoRA decisive-binding versus sham-cut panel. Never give the LoRA
   reader a candidate universe that itself resolves the protocol label.

## Interpretation limits

This wrapper tests per-life associative/procedural binding over real simulator
outcomes. It does **not** test discovery of unknown NetHack physics. The
NetHack/MiniHack ecosystem, documentation, and historical play data are
pretraining-leakage risks. Fresh counterbalanced labels make the life-specific
binding novel, while the underlying physical micro-skills remain
prior-anchored.

It is consequently appropriate only as a clearly secondary confirmation
sentinel. It must not substitute for PCFL-Stream's controlled independent
causal-information growth, target-blind compilation, same-corpus text/LoRA
transport comparison, or binding-level attribution package. It should not be
started before the PCFL fixed-corpus transport and adaptive-thinker gates pass.

## No-authority note

This advisory grants no authority to alter the frozen architecture, benchmark,
visibility contract, model loop, experiment plan, scoring, or scientific
claims. It authorizes no installation, code change, model run, GPU run,
network experiment, benchmark download, or paper-scope expansion. Any future
proposal to implement or run this sentinel must enter the architecture
deliberation and human-ratification path required by `AGENTS.md`.
