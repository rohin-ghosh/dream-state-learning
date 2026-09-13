# Post-training one policy for agentic behavior: evidence and minimum birth curriculum

**Date:** 2026-09-13  
**Question:** What published post-training recipes actually coordinate tool use, planning, correction/reflection, multi-turn action, memory cueing, and reasoning in one policy, and what part of Dream–LoRA–Think's composition-birth claim remains unshown?  
**Method and scope:** Representative primary-source survey of official papers and author repositories. It is not a proof that no concurrent or unpublished result exists. “Direct” below means the behavior is trained and exercised by the evaluated policy, not supplied entirely by a scripted wrapper or a second model. No models or GPUs were run for this note.

## Decision summary

The literature supports training several agentic behaviors into one policy, but it does **not** support treating them as eight independent data piles and assuming they will compose. The strongest recipes train decisions inside successful multi-turn trajectories, stratify or stage the hard decisions, mask environment-generated text from the loss, add explicit no-op and recovery cases, and select the mixture on held-out tasks. More methods or more data can hurt.

The broad novelty claim “an agent writes its own experience into parameters and uses it later” is no longer tenable. [TMEM](https://arxiv.org/abs/2606.04536) writes supervision distilled from the current rollout into fast LoRA weights and uses the adapted policy later in the same episode. [PEAM](https://arxiv.org/abs/2605.27762) consolidates an embodied agent's experience into category-specific LoRA experts for future skill execution.

The defensible unshown claim is narrower:

> A target-disjoint birth curriculum installs a generic composition policy in one small adapter; later, the same adapter absorbs exact opaque action–outcome facts from one life, survives a context reset, autonomously cues those facts, and composes them into new multi-hop actions—with own/foreign, same-identifier derangement, memory-cut, and birth-only causal controls.

I found no reviewed paper demonstrating that conjunction. TMEM is the closest collision, so any paper or experiment description should lead with this distinction rather than a broad “first parametric memory” claim.

## What the primary sources actually show

| Source | Post-training data and objective | Behaviors coordinated by the learned policy | Important limit for this project |
|---|---|---|---|
| [AgentTuning paper](https://arxiv.org/abs/2310.12823), [official repository](https://github.com/THUDM/AgentTuning) | Response-only SFT on 1,866 reward-filtered ReAct trajectories from six agent tasks, mixed with general chat data at a selected agent ratio of 0.2. | Reasoning/action interleaving, tool/API use, multi-turn state tracking, multi-task transfer. | Held-out gains are much stronger at 70B than at 7B/13B. It does not train memory writing or intrinsic correction. The general-data mix is a preservation device, not evidence that arbitrary skills compose. |
| [Agent-FLAN paper](https://arxiv.org/abs/2403.12881), [official repository](https://github.com/InternLM/Agent-FLAN) | Decomposes agent data into instruction following, reasoning, retrieval/function selection, and argument understanding; rebalances toward slower-learning abilities; normalizes diverse traces to chat format; includes negative tool-use cases. | Tool selection and arguments, reasoning, format control, selective action, multi-turn dialogue. | Capability decomposition is a data-design result, not proof that every named behavior is independently acquired. There is no parametric memory. |
| [FireAct](https://arxiv.org/abs/2310.05915) | SFT on mixtures of CoT, ReAct, and Reflexion trajectories, with single- and multi-task variants; also reports LoRA versus full tuning. | A single policy can choose a one-turn answer, multi-turn search, or reflective pivot. | Mixtures are backbone-dependent and non-monotonic: adding Reflexion or all three methods sometimes lowers exact match. Reflection points in the training traces were scheduled by the data-generation process. This is QA/search, not autonomous memory. |
| [STeP](https://arxiv.org/abs/2505.20023) | Learner rollouts are critiqued by a stronger model; only successful reflected trajectories are retained. Erroneous thought/action tokens remain in context but are masked from the loss, while the corrected continuation is supervised. | Environment interaction, error recognition in context, reflection, replanning, and successful continuation. | The stronger teacher supplies the correction and task knowledge. The result therefore supports a correction-data format, not intrinsic self-correction from outcome alone. |
| [ETO paper](https://arxiv.org/abs/2403.02502), [official repository](https://github.com/Yifan-Song793/ETO) | ReAct behavioral cloning with task/observation tokens masked, followed by iterative learner rollouts and trajectory-level DPO on learner failure versus expert success. | Multi-turn action and recovery from the learner's own error distribution on embodied/web tasks. | The preference pairs come from the target task family and an expert; this is not target-disjoint birth. It suggests a later rescue stage, not a necessary first-stage objective. |
| [SCoRe](https://arxiv.org/abs/2409.12917) | Two-stage on-policy RL: first constrain attempt one near the base while improving attempt two, then jointly optimize with an improvement bonus. | Intrinsic two-turn self-correction on math and code. | Offline correction SFT collapses or suffers distribution shift in this setting. There are no tools, environment observations, or memory writes, and the models are proprietary Gemini variants. |
| [Search-R1 paper](https://arxiv.org/abs/2503.09516), [official repository](https://github.com/PeterGriffinJin/Search-R1) | Outcome-only RL makes one policy interleave thinking, repeated search calls, returned information, and an answer. Retrieved text is masked from policy and KL losses. | Autonomous retrieval cueing, tool use, multi-turn reasoning, and answer production in Qwen2.5 3B/7B. | It retrieves external evidence; it neither writes nor reads parametric memory. Its wrapper appends a repair prompt after invalid actions, so not every recovery is policy-autonomous. |
| [ReTool](https://arxiv.org/abs/2504.11536) | Cold-start SFT on validated code-augmented reasoning traces, followed by PPO with a live interpreter and final-answer reward. | Reasoning, deciding when/how to call code, multi-turn execution, and emergent repair after tool feedback. | Demonstrated at Qwen2.5-32B in math. It supports staged cold start then RL, but is a scale/domain mismatch for the proposed 7B SFT birth test. |
| [Agentic Memory / AgeMem](https://arxiv.org/abs/2601.01885) | Three-stage RL: construct long-term memory from context; reset/add distractors and learn short-term-memory control; then answer tasks requiring retrieval and reasoning. Memory operations are explicit tool actions, with step-wise GRPO and composite rewards. | One policy selects Add/Update/Delete/Retrieve/Summary/Filter operations and coordinates external long- and short-term memory with downstream action. | This is the strongest curriculum analogue, but the memory remains textual and external. The memory backend and top-k retrieval semantics perform part of the work; no knowledge is installed into the policy's weights. |
| [TMEM](https://arxiv.org/abs/2606.04536) | During a rollout, the policy emits grounded QA-style memory-writing records; a fast LoRA is updated online, history and explicit memory are cleared, and later decisions use the adapted policy. The base extraction/action policy is optimized across rollouts with GRPO. | Within-episode memory writing, parametric consolidation, later recall/use, reasoning, and search actions in one fast-adapted policy. | The write trigger is a context-length heuristic, not autonomous sleep; the training write prompt exposes accumulated session context; birth and target are not target-disjoint in the proposed sense. The paper does not report own-versus-foreign banks, same-ID binding swaps, or memory-cut causal tests. |
| [PEAM](https://arxiv.org/abs/2605.27762) | Successful and failure–correction embodied trajectories are selected for consolidation and trained with behavioral cloning plus a contrastive/preference objective into a multimodal mixture of LoRA experts. | Experience consolidation and later execution of learned Minecraft skills. | It is a two-system architecture: a slow deliberative LLM plus a fast module with routed, physically isolated category adapters. It does not test exact opaque facts in one shared birth-and-memory adapter. |

The evidence divides cleanly. FireAct, AgentTuning, Agent-FLAN, Search-R1, and ReTool show that reasoning, tools, and multi-turn action can coexist in one policy. STeP, ETO, and SCoRe show that correction requires deliberately constructed data or on-policy optimization, not merely a “reflect” token. AgeMem shows that delayed memory construction, interference, retrieval, and use benefit from explicit stages. TMEM and PEAM establish broad parametric-memory prior art, but leave the project's specific causal composition test open.

## Reusable training principles

1. **Train a closed-loop policy, not a bag of labels.** A trace should expose the state–goal decision that requires a `READ`, the returned relation, a concise `THINK` update, the selected `STEP`, its observed consequence, and `STOP` or a replan. This lets one example exercise cueing, reasoning, planning, action, and verification. AgentTuning and Search-R1 support this trajectory unit; FireAct warns that simply unioning named methods is not reliably additive.

2. **Stratify by decision state and learning difficulty.** Agent-FLAN finds format compliance easier than reasoning and benefits from rebalancing. Count targets by decision type—information acquisition, state update/action, verification/recovery, and abstention/termination—rather than advertising an equal “eight-behavior” mixture.

3. **Keep non-policy tokens input-only.** Search-R1 masks retrieved passages; AgentTuning and ETO mask instruction/observation text; STeP additionally masks the learner's erroneous attempt while supervising the correction. This directly supports the planned response-only loss: service messages, world transitions, evaluator text, and injected errors must not become imitation targets.

4. **Include negative and no-change cases.** Agent-FLAN's tool/no-tool negatives teach when not to act. SCoRe shows that a correction objective can damage the first answer or encourage gratuitous changes. Every recoverable mismatch should therefore have a matched expected-outcome case where the correct policy continues without revision, plus `MISS`, irrelevant-read, and already-solved `STOP` cases.

5. **Separate acquisition, interference/reset, and later use.** AgeMem's three-stage curriculum is the clearest precedent. In the present design, birth should teach only the generic loop; later memory writing should occur without the target goal/answer; and use should follow a context reset with distractors. Mixing target solutions into birth or the write prompt would dissolve the main claim.

6. **Escalate objectives only after diagnosing SFT.** The minimum experiment should remain response-only SFT so the composition treatment and active sham are simple and dose-matchable. If the policy learns grammar but fails autonomous cueing or recovery, a separate successor can use learner-distribution DPO (ETO) or on-policy RL with an improvement/outcome reward (SCoRe/Search-R1/ReTool). That successor is a different causal treatment and should not be silently folded into the birth result.

## Proposed minimum birth curriculum

Do not create eight independent corpora. Keep the existing target-disjoint synthetic graph families and express the birth dose as **256 four-target episodes = 1,024 child-output training units**, divided into three auditable strata:

| Stratum | Episodes / units | Required contents |
|---|---:|---|
| **Interface and selective action** | 32 / 128 | Exact `READ`/`THINK`/`STEP`/`STOP` grammar; useful versus irrelevant reads; unavailable relation/`MISS`; already-solved and unsafe-to-act states. At least half should be negative or abstention cases. |
| **Successful closed loops** | 160 / 640 | Full state+goal → missing information → `READ` → relation interpretation/state update → predicted consequence → `STEP` → observed consequence → continue/`STOP`. Balance the three sealed graph families, depths, goal switches, and causal twins; no PCFL identifiers, topology, or solutions. |
| **Verification and recovery contrasts** | 64 / 256 | Thirty-two generator-matched pairs: one member receives an explicit action-outcome mismatch, stale/irrelevant read, or failed step and must replan; the twin receives the expected outcome and must not gratuitously revise. Keep the bad attempt and world/service response as masked context and supervise only the next child decision. |

These strata are episode tags, not permission to change the frozen corpus marginals: the compiled set must remain balanced across graph family, `READ`/`STEP`/`STOP` target type, goal side, route depth, edge-swap state, and display order. Use only child-generated tokens in the loss. Match the active command-card sham on the number of child targets, target-token distribution, interface vocabulary, and update schedule. If general-dialogue replay is needed for preservation, add the same replay to both arms and report it separately; it is not part of the discriminating 1,024 units. Select one versus two passes only through the frozen DEV endpoint, then judge the held-out causal panel.

This curriculum is deliberately small. It asks SFT to install the generic loop and correction affordance, not to solve later-life memory during birth. Its decisive qualification is behavioral: novel graph families, deeper paths, goal-switched causal twins, cue/no-cue contrasts, and correct-no-change controls. Failure on those tests means the adapter learned syntax or local patterns, regardless of training loss.

## Exact claim limits for the project

### Already shown broadly

- One post-trained policy can coordinate reasoning, tools, and multi-turn action across multiple task families.
- One policy can learn when to retrieve and how to manage external memory operations.
- An agent can distill its own rollout history into fast LoRA weights and use the adapted policy later in that episode (TMEM).
- Embodied experience can be consolidated into parametric LoRA skill modules for later execution (PEAM).

### Not established by the reviewed work

- A **target-disjoint** birth adapter acquiring a reusable composition operator rather than target facts or topology.
- The **same small adapter** retaining that birth policy while later absorbing exact, opaque, self-generated action–outcome bindings.
- Autonomous use of those bindings after a clean reset to solve new multi-hop goals, when the eventual goal/answer was absent during experience and writing.
- Causal attribution through own-versus-foreign life, same-identifier derangement, memory cut, binding redirection, and birth-only/sham controls.
- Autonomous discovery of the write/sleep procedure, indefinite continual learning, or separable mastery of a claimed set of “eight behaviors.” Those remain outside the proposed experiment.

Accordingly, the strongest honest result would be: **target-disjoint post-training caused a generic closed-loop composition skill that later made same-adapter, own-life parametric facts usable under causal controls.** It would not establish the first parametric memory agent, a complete self-improvement flywheel, or a general solution to lifelong memory.
