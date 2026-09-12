# What to parent, and why — nine papers read on 2026-09-12 (Fable, watcher)

Rohin, raw message 10 (`THESIS_RAW_ROHIN_2026-09-11.md`): "did you read the papers I referenced btw? … OPD-Evolver, MemSkill, Meta-TTL and Training Language Agents to Learn from Experience — parenting should have a lot of information to work on; MemSkill needs to be in the prompt too." I had not. Nine independent readers (one per paper) fetched each paper from arXiv (abstract, method, experiments, appendices; PDF via `tools/pdftext.py` where the HTML dropped a prompt), verified the identity, and answered the same questions: what changes and how, what the paper tells us to teach, the competencies it implies, its evidence scale, and how it bears on our three links — A (the write), B (parenting installs the form), C (the integrated loop learns faster). The structured answers are saved verbatim in `research_notes/analysis/out/parenting_papers_read_2026-09-12.json`; this file is the synthesis. Every identity below is **verified** against arXiv.

## 1. The nine papers

| key | title | arXiv | date | status |
|---|---|---|---|---|
| MemSkill | MemSkill: Learning and Evolving Memory Skills for Self-Evolving Agents (Zhang, Long, Bao, Feng, Zhang, Yue, Wang — NTU/UIUC/UIC/Tsinghua) | 2602.02474 | v1 2026-02-02, v2 05-24 | preprint, ICML-formatted; code + controller weights released |
| OPD-Evolver | OPD-Evolver: Cultivating Holistic Agent Evolver via On-Policy Distillation (Zhang, Xu, Yue, Su, Zhou, Hu, Yan — NUS/FDU/PKU/ByteDance) | 2606.17628 | 2026-06-16 | repo says EMNLP'26 Findings; partial code + LoRA |
| Meta-TTL | Learning to Learn-at-Test-Time: Language Agents with Learnable Adaptation Policies (Lou, Chen, Li, Wang, Hooi — NUS) | 2604.00830 | v1 2026-04-01, v3 07-15 | preprint; code |
| Train-from-Experience | Training Language Agents to Learn from Experience (Shalev, Ding, Jamnik — Cambridge) | 2605.20477 | 2026-05-19 | preprint; MetaGym code |
| OEL | Online Experiential Learning for Language Models (Ye, Dong, Dong, Wu, Huang, Wei — Microsoft Research) | 2603.16856 | v1 2026-03-17, v2 06-29 | preprint; code |
| SEAL | Self-Adapting Language Models (Zweiger, Pari, Guo, Akyürek, Kim, Agrawal — MIT) | 2506.10943 | v1 2025-06-12, v2 09-18 | preprint; code |
| TMEM | Scaling Self-Evolving Agents via Parametric Memory (Ren et al. — Qwen-Character Team, Alibaba; PKU) | 2606.04536 | 2026-06-03 | preprint |
| Early Experience | Agent Learning via Early Experience (Zhang, Chen, Liu, … Weston, Su, Wu — Meta / OSU) | 2510.08558 | v1 2025-10-09, v3 2026-05-24 | ICML 2026 |
| SDFT | Self-Distillation Enables Continual Learning (Shenfeld, Damani, Hübotter, Agrawal — MIT / ETH) | 2601.19897 | v1 2026-01-27, v2 08-07 | preprint; code |

Correction to earlier shorthand: TMEM's own term is "grounded SFT QA pairs", not "self-written canonical pairs".

## 2. What each one changes, and how (one paragraph each)

**MemSkill.** Nothing in the LLM's weights changes. A small MLP controller (PPO, reward = downstream recall score) selects, per 512-token span, which "memory skills" to apply; a frozen LLM executor writes INSERT/UPDATE/DELETE items into an external text memory; a frozen LLM "designer" mines hard cases every 100 steps, diagnoses failures as storage / retrieval / memory-quality, and rewrites or adds skills in a fixed form (Skill / Purpose / When to use / How to apply / Constraints). Controller and skill bank are frozen at deployment and transfer across datasets and base models.

**OPD-Evolver.** A LoRA on the policy (Qwen3.5-9B, Qwen3-4B) learns four behaviours by on-policy self-distillation: the student acts under deployment conditions; a privileged teacher — the same model given hindsight (which memories later paid off, a successful trajectory) — scores the same tokens; token-level KL trains selection, execution, writing and maintenance. Memory itself stays in an external four-tier store (trajectories, tips, skills, tools). The only external signal is task return, turned into per-memory "outcome-calibrated attribution".

**Meta-TTL.** No weights change. A meta-agent rewrites a frozen actor's system prompt after every episode; the meta-agent's own instructions (the "adaptation policy") are learned by reflective prompt evolution against W-AUC, a learning-curve area that weights later episodes more — the outer loop literally optimises the slope of test-time improvement. Frozen at deployment.

**Train-from-Experience.** A separate reflector (Qwen2.5-7B-Instruct, full GRPO fine-tune) learns to read a batch of the frozen actor's trajectories and write ANALYSIS then an IMPROVED PROMPT for future unseen tasks; reward = replaying the same batch under the new prompt. Learning at test time is in-context only; the actor never changes.

**OEL.** Full-model update on Qwen3 in two stages: the model extracts "transferable experiential knowledge" from its own trajectories under a fixed prompt, accumulating without repetition; then on-policy context distillation makes the bare model match its own knowledge-conditioned distribution (reverse KL). Redeploy, re-extract, re-consolidate — a wake/sleep cycle with the environment as the only outside source.

**SEAL.** Two nested weight changes. Inner: the model writes a "self-edit" (implications, rewrites, or training hyperparameters) about a new passage and is SFT'd on it (LoRA r=32–64). Outer: ReST-EM keeps the self-edits that made held-out QA correct and SFTs the policy on them. Base Qwen2.5-7B, our model.

**TMEM.** Within an episode, when context exceeds a budget the agent writes grounded QA pairs about the session and SFTs a rank-6 LoRA on the last four FFN layers (A frozen from SVD, only B trained); the context is cleared and facts live only in the fast weights. Across episodes, GRPO on outcome reward trains the full base to write pairs that make its own future updates useful. The adapter is per-episode memory, not lifetime memory.

**Early Experience.** Full SFT (LoRA only at 70B) before any RL. From expert states the policy proposes alternatives, executes them, and trains either to predict the resulting state (implicit world model) or to write a contrastive "internal monologue" explaining why the expert action beats the alternatives it actually observed, then emit the expert action. Reward-free; expert demonstrations anchor every state.

**SDFT.** Full fine-tuning of Qwen2.5-7B-Instruct: the student answers a bare prompt; an EMA copy of itself conditioned on the demonstration ("answer with a response of your own, including the thinking process") scores the same tokens; per-token KL. Test time: no demonstration, no context. It is on-policy RL against an implicit reward; the target stays near the base distribution (0.68 vs 1.26 nats for SFT), which they credit for no forgetting.

## 3. What they tell us to parent — the union, grouped

Every item below is something a paper installs by prompt, loss or selection and shows to matter. Our question is whether a parent can teach the child to do it unprompted, so that the disposition lives in the LoRA.

**Perceive along fixed axes, write atomic items.** MemSkill's evolved skills are perception directions the base primitives missed — capture temporal context (start/end/duration/sequence), activity details (type, place, participants), entity nuances (aliases), relationships, action constraints, object-location-state; split distinct facts into separate items; keep each concise and specific. TMEM: cover who/what/when/where, preferences, plans, events, temporal detail. SEAL: restate as implications and atomic facts, rewrite the same content several ways, write long and detailed rather than terse (RL "dramatically increased the length"). This is Rohin's sixteen-renderings baseline stated by three papers.

**Decide what deserves storing (discretionary memory).** MemSkill: Skip "trivial, fleeting, or speculative content"; the controller's job is which lenses to apply given what is already stored. TMEM: "Generate QA pairs adaptively based on how much useful information is present … If there is no usable evidence, return an empty JSON array." OPD-Evolver: the count written is chosen by the agent, may be zero, and only the top 30 % by later value are kept. Meta-TTL: separate durable facts from episode-specific diagnosis. This is Rohin's learned skill (message 3) — three papers hardcode it, none learns it into weights without a prompt.

**Provenance: write only what was experienced.** MemSkill: every evolved skill carries "Avoid inferring details not directly stated". TMEM: "Each answer must be … directly supported by the session." Meta-TTL: durable facts "evidenced by the most recent episode log, preventing hallucination" (discovered at iteration 14 of their evolution). Early Experience: STaR-style rationales written without observing the alternative's real outcome are "ungrounded" and *hurt* (WebShop 47.3 → 25.0), while the same rationale written after seeing the outcome helps (58.2). SDFT: strip context-referencing scaffolding ("Following the example…") so the child does not carry markers of a context it no longer has. Our provenance gate is the mechanical form of a rule five papers state in prose.

**Diagnose and assign credit before writing the lesson.** Meta-TTL's learned reflection has six mandatory sections — diagnosis, durable facts, next-episode priorities, route with save points, a concrete 15–25-move script, parser tips — and an explicit credit protocol: what scored and how to reproduce it, what caused death, what wasted turns, what blocked progress. Train-from-Experience: what went well/wrong → how the current instruction caused it → rewrite for future unseen tasks; generalise from the one success to the failures. OPD-Evolver: write "compact causal tips" that "target the root cause of the failure" rather than generic advice ("Exploring adjacent is insufficient" beats "add an action validator"). MemSkill's designer: classify a recall failure as storage vs retrieval vs quality, group failures into patterns, change one rule per pattern, never for a one-off miss. Early Experience: obtain the counterfactual first (try the alternative, look at the error), then write a contrastive lesson naming the violated constraint, comparing only 2–4 alternatives.

**Judge a memory by what it does later, not by how it reads.** SEAL: reward a write by whether the model then answers correctly *without the source in context*; keep only the writes that did (ReST-EM); a four-axis rubric — length, diversity, quality, correctness — nearly matches full RL (45.6 vs 47.0). OPD-Evolver: value a memory by the mean return of episodes that carried it minus episodes that retrieved but did not select it. Meta-TTL: judge a reflection habit by the learning-curve slope it produces (W-AUC). This is what a parent's grading should look like, and what sleep should prioritise (Rohin's message 6: replay weighted by importance).

**Leave working rules alone; explore with discipline.** Train-from-Experience: on all-success, reproduce the previous instruction nearly exactly — no churn. Meta-TTL: exploit the known route first, at most one new experiment per episode under a save point, a fallback rule after two failures, and "identify the actual situation before applying stored facts; ignore the ones that do not apply".

**Write in your own words, from your own attempt.** OEL: knowledge the model wrote from its own trajectories beats knowledge written by a stronger model (31.1 vs 22.7 % after consolidation) — "on-policy consistency". SDFT: the training target is the child's own attempt corrected by its demonstration-aware self, not the demonstration; offline distillation from the identical teacher underperforms. Rohin's rule that the parent's words never enter the sleep bytes is the same finding.

**Manage the store.** OPD-Evolver: periodic maintenance episodes (lookup / merge / delete / retire). MemSkill: Update merges rather than duplicates; Delete only on explicit contradiction, prefer no action under uncertainty. TMEM: write at a budget boundary, not continuously — too often discards detail, too rarely makes grounding harder (their L_max bell curve).

## 4. Numbers that ground our claims

| claim in our paper | paper | number |
|---|---|---|
| Raw experience is bad post-training data | OEL | consolidating raw trajectories 7.8 % vs 7.5 % no-experience baseline; extracted knowledge 21.4 % (Sokoban, Qwen3-4B) |
| | TMEM | supervision form: raw next-token on transcript 10.37 F1, free summary 35.44, QA pairs 41.24 (LongMemEval-S, Qwen3-4B) |
| | SEAL | fine-tune on the passage itself 33.5 % vs base 32.7 %; self-written implications 39.7, rewrites 55.6, RL-trained 47.0 |
| | Meta-TTL | online SFT on raw (state, action) pairs from own trajectories: W-AUC 0.116 vs static 0.084, weak and unstable |
| The child's own words beat a stronger model's | OEL | self-extracted 31.1 % vs Qwen3-4B-extracted 22.7 % (Frozen Lake, Qwen3-1.7B) |
| | SDFT | own restatement 89 % strict vs SFT on QA pairs 80 % vs continued pretraining on the source 9 %; indirect questions 98 vs 80 |
| The base model lacks the write disposition; it is installed from outside | SEAL | no format prompt 13.8 %, 18.9 % after RL; prompted implications 39.7, rewrites 55.6 |
| Ungrounded reflection harms | Early Experience | STaR rationales without observed outcomes: WebShop 47.3 → 25.0, ALFWorld 80.5 → 74.2; grounded contrastive reflection 58.2 / 85.2 |
| Reflection without an artifact adds nothing | SEAL | chain-of-thought before the self-edit 38.7 vs 39.7 without |
| How-to-learn is a trainable skill that transfers | Meta-TTL | Jericho ID W-AUC 0.18 → 0.41, OOD 0.23 → 0.28 (0.34 with fact banks removed — the form transfers, not the facts) |
| | Train-from-Experience | unseen task types: Cool-and-Place 42.4 → 49.2 %, Pick Two 28.3 → 41.2 % (k=5); the untrained model already has the skill "to some extent" |
| | MemSkill | evolved skills 53.82 vs four fixed primitives 46.50 (LoCoMo L-J); random skill selection costs 5–11 points |
| | OPD-Evolver | frozen weights + memory only 33.1 vs full 38.7 (InterCode-4B); written-memory quality 0.80 → 0.90 after distillation |
| A better start learns faster afterwards | Early Experience | same GRPO from different checkpoints: IL 93.8, SR 98.5, IWM 97.7 (ALFWorld, Llama-3.1-8B), "the gap grows during RL" |
| A self-teacher cannot install a new form of thinking | SDFT | failed to turn a non-reasoning model into a chain-of-thought model; "struggles when the desired behaviour requires a fundamental shift in generation patterns" |

Caveats the readers flagged: MemSkill's conversational test set is two dialogues; OPD-Evolver is single-seed with no intervals; Meta-TTL's WebArena gains are within 0.01–0.03; TMEM's LoCoMo 4B gap is 0.06 F1.

## 5. Where each paper stands on our three links

| paper | A: weights carry the write | B: the form is installed and expressed without the prompt | C: faster later learning, consolidation running |
|---|---|---|---|
| MemSkill | no (external text store) | no — skills are prompt text a controller selects forever; the executor internalises nothing | no — evolution stops before deployment |
| OPD-Evolver | partly — the LoRA holds the four behaviours, memory stays external | partly — installed by self-distillation from hindsight, no parent | level only; frozen-vs-trained arm exists, no slope |
| Meta-TTL | no | partly — the form is learned, but in a second model's prompt | closest analogue of H2, in prompt space; adaptation policy frozen at deployment |
| Train-from-Experience | no | partly — a second model learns the reflection form | in-context slope continues past the training horizon |
| OEL | yes (full model) | no — fixed extraction prompt, never internalised | supportive: gains persist over 2–3 rounds; no unseen-task transfer, no 2×2 |
| SEAL | yes (LoRA, our base) | no — form prompted per passage; RL sharpens it | no; sequential edits show monotone forgetting |
| TMEM | yes (rank-6 LoRA, per episode) | no — fixed prompt d; disposition trained into the full base by RL | level after RL; no slope, no frozen arm |
| Early Experience | yes (full SFT) | partly — the model emits the reflection unprompted after training, but anchored to expert actions | one-step yes: better checkpoints reach higher RL ceilings with a growing gap |
| SDFT | yes (full FT) | no — hardcoded template and loss | sequential accumulation without regression; no slope |

## 6. What none of them does — the gap the paper claims

No paper removes the teacher, clears the prompts, and asks whether the disposition to turn experience into good training data is *expressed from the weights alone* on a held-out task (H1), nor whether an agent carrying it learns faster from its own experience with consolidation still running versus frozen (H2, the 2×2). Discretionary memory — deciding what deserves a write — is hardcoded in every paper that has it. All the reflection forms are installed by a prompt or a second model; the two papers that train a reflector into weights (Train-from-Experience, TMEM) keep the prompt at inference. Only SEAL and Early Experience use our base model; only TMEM and SEAL write into a LoRA, and neither accumulates one adapter over a life. Meta-TTL's authors argue that separating strategies from facts "would not be possible if the policy were encoded in model weights" — H1 is the direct answer to that claim.

## 7. Consequences for the build (for the builder; pointers, not orders)

- **Frame template for taught skills:** MemSkill's Skill / Purpose / When to use / How to apply / Constraints is a ready first-person procedural form; its evolved skills are a ready list of perception axes for the sixteen-renderings baseline.
- **Sleep prioritisation:** OPD-Evolver's hindsight attribution (return with the memory present minus return with it retrieved but unused) and SEAL's ReST-EM filter are two implementations of Rohin's message 6 — replay weighted by what mattered.
- **H2 metric:** Meta-TTL's W-AUC (later episodes weighted more) is a published slope metric; report it alongside the plain slope.
- **Parent grading rubric:** SEAL's four axes (length, diversity, quality, correctness) plus Early Experience's "does the conclusion match the evidence" filter.
- **Discipline rules worth teaching verbatim:** no churn on all-success (Train-from-Experience); one experiment per episode with a fallback (Meta-TTL); write nothing without sourced evidence (TMEM).
- **Compile candidates:** OEL's on-policy context distillation (bare child matches its knowledge-conditioned self) and SDFT's per-token KL with first-token masking are alternatives to plain SFT for the memory write; SDFT's KL-to-base (0.68 vs 1.26 nats) is a candidate "perceived well enough to be written" metric. Warning from SDFT: a self-teacher alone will not shift the form of thinking — that is the parent's job.
- **Counterfactual before lesson:** Early Experience's K = 2–4 alternatives observed before the contrastive monologue, and its finding that ungrounded rationales hurt, argue for a gym step "try the other move, then write".
- **Prompt §5 list:** add MemSkill (2602.02474); the other eight are already named or implied.
