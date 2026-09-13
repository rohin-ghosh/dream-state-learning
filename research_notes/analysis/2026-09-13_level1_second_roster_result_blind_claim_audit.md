# Result-blind claim audit: Level-1 second roster

**Audit freeze:** the 12 roots/specifications present in the immutable roster at approximately 08:08 UTC on 2026-09-13. I inspected the frozen protocol, material generators, runner, specifications, and preparation-cost receipts. I did **not** inspect generated responses, fit losses, score files, completion markers, or any other efficacy result. I did not change source, roots, jobs, or GPU state.

**Verdict:** **valid for a narrow authored Level-1 screen; no fatal confound.** A positive result can show that fitting an explicit decision procedure makes the model execute that procedure more accurately on fresh authored situations. It cannot establish actual perception, rehearsal, self-reflection, learning, retention, parenting, SLEEP, a closed loop, or organism-level improvement. Repetition and meta-reflection have a narrower generalization test than perception and self-reflection because their held set reuses the same four prompt wrappers.

## Frozen design

The roster is `astra_level1_second_roster_20260913_attempt1_clockfix/roster.json`, SHA-256 `2bca9e4a66cc576993119fc1d5fddcac77de7cc3f93686327b962c45c2d17c69`. It binds:

- perception, learner seeds 0/1/2, on node 2 GPUs 1/2/3;
- self-reflection, seeds 0/1/2, on node 2 GPUs 4/5/6;
- repetition, seeds 0/1/2, on the A100 node GPUs 0/1/2;
- meta-reflection, seeds 0/1/2, on the A100 node GPUs 3/4/5.

All roots use the same official Qwen2.5-7B-Instruct revision, the same material seed 0, a fresh frozen base, and one fresh LoRA. The bound protocol is `/tmp/ASTRA_LEVEL1_SECOND_ROSTER_PROTOCOL_2026-09-13.md`, SHA-256 `c9652b1b0ad301c4a67c87597f870b8f423d95149679921bad5e5c95f3eabede`. The material sources are:

- perception/self-reflection: SHA-256 `4648f8542b1babb10f6ffda4bf023024d71b8c9834a32e2242a7f064a94a8941`;
- repetition/meta-reflection: SHA-256 `498e841af8c65654b3f090a1c9f951b6d0aa0e040fd3d757d320f69cba007700`.

The runner is SHA-256 `6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e`; a hash-identical receipt is archived locally at `research_notes/astra_memos/receipts_20260912/astra_level1_skill_run_20260913.py`.

Each root has 96 training rows, 48 held rows, and 12 canaries. Training is rank 8, alpha 16, dropout 0.05, LR `3e-4`, batch size 4, exactly 320 updates = 1,280 row presentations, max length 1,024, no truncation, and target-plus-EOS supervision with context/tail/padding masked. Each row is presented 13 times and 32 of 96 rows receive a fourteenth presentation; which rows receive the extra exposure depends on learner seed.

The nominal row/update dose is matched across skills, but the token dose is not. Seed-0 preparation receipts contain 27,877 / 60,456 / 24,325 / 24,534 actually supervised tokens for perception / self-reflection / repetition / meta-reflection, respectively; total train tokens are 431,065 / 516,406 / 460,927 / 675,844. This is harmless for within-skill OFF-versus-post inference but prohibits interpreting score differences between skills as difficulty or learnability differences. The A100/A40 split independently prohibits cross-skill hardware comparisons.

Readout is deterministic (`temperature=0`, seed 0), with a fresh OFF engine and a fresh post-fit engine. Each engine receives the same 48 held plus 12 canary calls. The target bytes and source proofs are present in the frozen material but the runner projects only `input_messages` into readout calls; no target or hidden source metadata is sent to the model.

## What each screen actually asks

| Label | Exact authored proxy | Held composition | Narrow baseline/shortcut |
|---|---|---:|---|
| Perception | Select the final event, bind its `TRY` to its outcome and prior prediction, or abstain for ambiguous prediction, missing outcome, or action/outcome mismatch. | 24 recordable + 24 abstain; the three abstention reasons are 8 each. | Static exact-target best is 8/48 (one repeated abstention). Event formatting exposes the relevant defects; this is conditional extraction under an explicit policy, not discovery of what matters. |
| Self-reflection | Classify the same six event conditions, copy the evidence, and select the prescribed next action. | Six diagnoses, 8 each. | Diagnosis determines next action one-to-one; evidence is direct extraction. Static full-target best is 1/48 because evidence values are unique. |
| Repetition | Decide rehearse/skip from explicit relevance, budget, importance, unresolvedness, and settledness priorities; copy independent support unchanged. | Decisions 24/24. Reasons: important 16; four other reasons 8 each. | Majority decision = 24/48; majority reason = 16/48; best static full target = 4/48. `independent_support_after` is copied, and repetition count is explicitly non-evidence. This tests policy execution, not actual rehearsal. |
| Meta-reflection | Compare authored before/after/delayed checks and choose one diagnosis plus its prescribed action. | Six diagnoses, 8 each. | Diagnosis determines next action one-to-one; best static full target = 8/48. It classifies a vignette; it does not observe or alter the model's own cognition. |

All four prompts state the decision policy and legal output schema explicitly. There is no direct answer-byte leakage, but this is intentionally **open-book policy execution**. A gain must not be described as recalling an internalized policy without prompting.

## Independence and shortcut audit

- The runner enforces unique row IDs and unique source identities across train, held, and canary. Train/held event IDs, record IDs, check IDs, and numeric facts are disjoint.
- Perception and self-reflection use four training wrappers and four different held wrappers, balanced at 24/12 examples per wrapper. Their selected situations are independently generated per skill. They support limited wrapper transfer over the same six authored case generators and the same explicit policy.
- Repetition and meta-reflection use four wrappers in both train and held. Their facts and IDs are fresh, but wrapper transfer is **not** tested. Each has 16 train and 8 held sibling groups with six cases per group. The nominal held denominator is 48, but within-material uncertainty should respect the eight held clusters rather than treat 48 rows as iid.
- Perception's record/abstain split is balanced. Self-reflection and meta-reflection have six balanced diagnoses. Repetition has balanced decisions but an intentionally imbalanced reason label (`important` = 1/3). Report the reason-conditioned breakdown so a decision-only or majority-reason strategy is not mistaken for the complete skill.
- Perception's positive/negative outcomes and earlier-versus-selected relations are balanced by construction. The outcome/action-mismatch fixture makes the wrong action string visible in the outcome, so solving it requires string alignment, but this remains an authored formatting cue rather than real-world causal grounding.
- Material seed is fixed at 0 for all three learner seeds. Therefore the scientific replication unit is the **optimizer/run seed**, `n=3`, not 144 held rows and not three independent datasets. Item-level counts are useful diagnostics only. A fresh material seed is required for confirmatory source generalization.
- Canaries are six addition and six copy tasks. They detect gross generic instruction/serialization damage; they are shared within each source-module pair and are neither a task-interface canary nor evidence of broad no-harm. The protocol contains no automatic efficacy threshold.

## Scoring and prospective interpretation

Primary success is `content_correct`: finished output, exact key set, types, and values under the pinned scorer. It permits surrounding whitespace or exactly one plain/JSON code fence, but it does not repair malformed JSON, values, keys, types, extra prose, or missing fields. Secondary success is strict byte-exact canonical output. This separation is sound.

For each skill and learner seed define `Delta_held = (post content correct - OFF content correct) / 48` and analogously `Delta_canary / 12`. Because no minimum effect was frozen, the roster can screen and localize effects but cannot manufacture a post-hoc binary pass. Interpret terminal results as follows:

| Observed outcome | Permitted interpretation |
|---|---|
| Any root lacks complete custody/runtime validation | That seed is nonreportable; do not substitute rows or pool around it. |
| OFF is at/near ceiling | The screen has insufficient headroom for a learning claim, even if post remains perfect. |
| Strict rises but content does not | Serialization/format learning only. |
| Content rises but strict does not | Authored decision content improved, while canonical serialization did not. |
| `Delta_held > 0` in all three seeds, relevant case/field strata improve, and post canary is not below OFF in any seed | Stable candidate that the fitted LoRA improves this explicit authored procedure at this dose. Confirmation still needs a new material seed. |
| Signs split, or only one/two seeds improve | Recipe-sensitive/unstable signal; report every seed, no skill-acquired claim. |
| Aggregate rises through one easy/majority stratum only | Local shortcut or partial skill. Name the stratum; do not use the umbrella skill label. |
| Held content is unchanged | No detectable behavioural gain at this corpus/recipe/dose; not evidence the skill is unlearnable. |
| Held content falls | Interference/adverse write at this dose. |
| Canary falls | Any task gain carries measurable generic copy/add damage; not canary-preserving and not broad no-harm. |

Skill-specific localization is mandatory: supported-record versus abstention and relation fields for perception; diagnosis versus evidence versus prescribed action for self-reflection; decision/reason/copied-support for repetition; diagnosis/action for meta-reflection. Meta-reflection's action is a deterministic label companion, so joint correctness remains table-governed classification, not deeper metacognition.

## Claim boundary

The strongest defensible positive sentence is: **"On one authored material seed, a fresh rank-8 LoRA fit to 96 examples improved three-seed execution of an explicitly stated Level-1 decision procedure on fresh authored situations, relative to the same frozen model OFF; generic copy/add canaries were preserved [if true]."** For perception/self-reflection, add that held wrappers were distinct. For repetition/meta-reflection, do not claim wrapper transfer.

This roster does not isolate Rohin's stronger hypothesis that sustained explicit attention to differences improves conditional/keyed discrimination. Perception does require aligning the selected event, action, prediction, and outcome, so it is a meaningful **proxy screen** for conditional discrimination. But there is no matched plain-versus-contrastive arm here, and the policy is supplied in the prompt. It therefore measures authored-sentence policy fit, not the causal benefit of contrastive attention; that causal question belongs to the separately frozen plain-versus-contrastive screen.

No redesign is required while the roster is live. The limitations above are claim and analysis constraints, not fatal execution defects.
