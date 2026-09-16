# R130 / R132 — primary research and bounded benchmark proposal

**2026-09-16; method proposal only, awaiting approval.** Two tiers: GENERAL published instruments and EXPERIMENT-SPECIFIC R130 batteries. No held items, prompts, answers, or membership here. No runner/item-generation code, GPU/parent-process interaction, benchmark adoption, or scientific-claim change is authorized by this note. Only this document was edited in the repo.

**Retrieval correction:** `web.run` returned empty outputs, which verified nothing. Main's earlier retrieval statement is not evidence. The sources below were subsequently retrieved using HTTP and inspected for title/author/abstract or full-text content. Receipts are below; raw artifacts stay in `/tmp/r130-primary-20260916/`. An earlier working draft had unsupported attributions; this version replaces them. OpenReview returned a browser challenge despite HTTP 200 and is **not** cited as retrieved paper evidence.

## Tier 1 — GENERAL existing instruments: ten primary sources

Bibliographic years are the retrieved preprint/publication years, not unverified venue claims. “Limit” includes R130 methodological cautions, not necessarily an author's explicit limitation. Abstract-only entries support narrower conclusions than inspected full papers; none of these studies was independently replicated here.

| ID / verified reference | What it measures; limitation and use |
| --- | --- |
| **S1. Saurav Kadavath et al. (2022), Language Models (Mostly) Know What They Know.** [Paper][s1]. | Answer-conditioned correctness probability, P(True), versus advance answerability, P(IK). **Limit:** elicitation/distribution matter; abstract explicitly reports difficulties calibrating P(IK) on new tasks. Supports distinguishing task accuracy, confidence, and conditional competence—not an internal-knowledge ground truth. Abstract/metadata inspected. |
| **S2. Katherine Tian, Eric Mitchell, Allan Zhou, Archit Sharma, Rafael Rafailov, Huaxiu Yao, Chelsea Finn, Christopher D. Manning (2023), Just Ask for Calibration: Strategies for Eliciting Calibrated Confidence Scores from Language Models Fine-Tuned with Human Feedback.** [Paper][s2]; DOI `10.18653/v1/2023.emnlp-main.330`. | Compares elicited confidence and token-probability estimates on QA; includes ECE and Brier scoring. **Limit:** better verbal calibration in tested RLHF models does not guarantee transfer to this base/adapters or new tasks. Freeze elicitation; don't fit confidence transformations on held outcomes. Full PDF inspected. |
| **S3. Neil Band, Xuechen Li, Tengyu Ma, Tatsunori Hashimoto (2024), Linguistic Calibration of Long-Form Generations.** [Paper][s3]; [official implementation][r3]. | Calibration of probabilities that users infer from long-form answers; proposes supervised/RL training and automated/human evaluation. **Limit:** downstream reader/extractor behavior is part of the measure; verbal assurance is not accuracy. Training framework is not a ready-made neutral instrument. Paper abstract and repository README inspected; no code executed. |
| **S4. Jie Huang, Xinyun Chen, Swaroop Mishra, Huaixiu Steven Zheng, Adams Wei Yu, Xinying Song, Denny Zhou (2023), Large Language Models Cannot Self-Correct Reasoning Yet.** [Paper][s4]. | Intrinsic revision without external feedback; tested reasoning can degrade rather than improve. **Limit:** not a universal impossibility result. Measure harmful revisions and distinguish detecting an error from fixing it. Abstract/metadata inspected. |
| **S5. Zhibin Gou, Zhihong Shao, Yeyun Gong, Yelong Shen, Yujiu Yang, Nan Duan, Weizhu Chen (2023), CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing.** [Paper][s5]. | Tool-feedback-assisted revision on free-form QA, mathematical program synthesis, and toxicity reduction. **Limit:** feedback/tool quality and revision are confounded unless budgets and evidence are matched. Compare unaided with actual-feedback conditions, not imagined tool success. Abstract/metadata inspected. |
| **S6. Yijiang River Dong, Tiancheng Hu, Zheng Hui, Caiqi Zhang, Ivan Vulić, Andreea Bobu, Nigel Collier (2026), Value of Information: A Framework for Human–Agent Communication.** [Paper][s6]; DOI `10.18653/v1/2026.acl-long.1987`. | Clarify-versus-act decisions using expected utility gain minus communication cost; evaluates four task domains. **Limit:** utilities, belief estimates, and user-cost models are assumptions, not universal human values. Useful basis for controlled missing-information/VoI tasks with evaluator-known utility—not evidence that confidence gain equals information value. Full PDF inspected. |
| **S7. Yue Huang, Jiawen Shi, Yuan Li, Chenrui Fan, Siyuan Wu, Qihui Zhang, Yixin Liu, Pan Zhou, Yao Wan, Neil Zhenqiang Gong, Lichao Sun (2023), MetaTool Benchmark for Large Language Models: Deciding Whether to Use Tools and Which to Use.** [Paper][s7]. | Tool necessity and selection, including similar choices, scenario constraints, reliability issues, and multiple tools. **Limit:** selection correctness alone does not establish successful execution, permission awareness, or recovery from invalid output. Abstract/metadata inspected. |
| **S8. Lingjiao Chen, Matei Zaharia, James Zou (2023), How is ChatGPT's behavior changing over time?** [Paper][s8]. | Compares March/June 2023 service snapshots across tasks, including instruction/format behavior. **Limit:** opaque service changes and two snapshots don't identify a learning mechanism or persistent identity. Separate capability from formatting and infrastructure effects. Abstract/metadata inspected. |
| **S9. Praveen Kumar Myakala, Manan Agrawal, Rahul Manche (2026), BeliefShift: Benchmarking Temporal Belief Consistency and Opinion Drift in LLM Agents.** [Paper][s9]. | Multi-session belief consistency, contradiction detection, evidence-driven revision; reports 2,400 annotated trajectories and BRA/DCS/CRR/ESI metrics. **Limit:** recent preprint, not independently validated here. Labels involve human annotation; contradiction reconciliation explicitly uses human judgment. It is **not** wholly deterministic objective scoring or between-checkpoint learning evidence. Full HTML inspected. |
| **S10. Anne Ouyang, Simon Guo, Simran Arora, Alex L. Zhang, William Hu, Christopher Ré, Azalia Mirhoseini (2025), KernelBench: Can LLMs Write Efficient GPU Kernels?** [Paper][s10]; [official repository][r10]. | Correctness **and** execution speed on PyTorch workloads; `fast_p` is the fraction of all tasks correct and faster than speedup threshold `p`. **Limit:** finite tests are not proofs; results depend on hardware, baseline, precision, tolerances, compilation, and timing protocol. General kernel-child capability/environment instrument, not metacognition. Abstract and README inspected; no kernels run. |

**General-tier recommendation:** reuse measurement decompositions, not public instances as uncontaminated held evidence. S1–3 cover calibration; S4–7 correction/decision/tool judgment; S8–9 longitudinal comparisons; S10 execution-grounded engineering. These are instruments of performance or change, not direct measurements of learning mechanisms. Compare checkpoint deltas with frozen-base and matched no-learning controls; parental claims require suitable lineage controls.

For the planned kernel child, a separately approved KernelBench evaluation should report compile/runtime failures, correctness rate (`fast_0`), and `fast_1`/declared higher thresholds over **all** attempted tasks. Keep reference and candidate on matched hardware/software, input/precision/tolerance policies, warmup/repeated timing, synchronization, and execution budgets. Record environment and baseline provenance; do not reward fast-but-wrong kernels or infer GPU speed from source text/CPU checks. A full general suite is **not** added to tonight's 22-prompt budget; this worker does not launch it.

## Tier 2 — EXPERIMENT-SPECIFIC: two compact batteries

**Proposed tonight-sized panel: 22 model invocations/checkpoint = A6 + B16.** Same fixed held prompt bytes for each item across checkpoints; each invocation starts with empty conversation history (`samepromptemptycontext`). Pair members deliberately differ in their controlled condition, but each member stays byte-identical across checkpoints. No adaptive follow-up prompts, hidden extra grading-model calls, or prior checkpoint outputs enter elicitation. Method approval and separately assigned item-writing scope precede implementation.

### A. Minimal-prompt behavior — 6 invocations

Three families, two items each: **spontaneous self-description; minimally constrained explanation; open next-step/planning behavior**. These are family labels, not item text. Keep the elicitation minimal; do not embed the coding rubric or coach desired semantic traits.

Record response length, truncation, length-normalized lexical diversity, and repeated n-gram rates as **descriptive surface statistics only**. Lexical richness, repetition, verbosity, and stylistic consistency are **not intelligence scores**. Self-reference, uncertainty language, agency language, consistency, or other semantic constructs remain **UNSCORED / exploratory** unless a frozen rubric is validated on separate non-held data by blinded independent raters, with agreement and validity evidence plus adjudication rules. Blind raters to checkpoint/lineage. No single behavioral quality/personality/introspection score.

### B. Objective knowledge-of-doing — 16 invocations

| Family / count | Required external labels and scoring proposal |
| --- | --- |
| **Conditional competence + confidence: 4** (two controlled pairs) | Pair sufficient/insufficient support or declared task conditions while retaining objective success predicates. Record probability of task success before feedback; independently score actual answer/action. Compare accuracy and confidence changes under the condition. Distinguish answer correctness from correctly declining an underdetermined task. S1–3. |
| **Missing information / evidence value: 4** (two controlled pairs) | Evaluator specifies missing variables, information availability, utility, and acquisition cost. Score answer-versus-request choice, identifying the necessary information, unnecessary/missed requests, and net expected-utility regret against a declared one-step oracle. Only compute numerical VoI where simulator probabilities/utilities really exist; otherwise report objective action correctness, not invented VoI. S6. |
| **Action/tool limitations: 4** (two controlled pairs) | Evaluator-known capability/permission/availability and output-validity states support labels for allowed/useful action, impossible/unsupported action, and warranted abstention. Score selection/feasibility, false success claims, recognition of unusable evidence, and predicted success versus actual recorded outcome where available. No claim that execution occurred based solely on text. S5, S7. |
| **Revision after actual evidence: 4** (two fixed before/after pairs) | Use evaluator-authenticated observations or recorded sandbox execution results, not suggested answers or fabricated tool feedback. Score error detection on fixed candidate artifacts, evidence-warranted final decisions, wrong→right repairs, and right→wrong damage. Include both informative and non-decisive evidence conditions. Evidence source/content hashes remain sealed. S4–5, S9. |

Across B, require a small, fixed response schema sufficient for `decision`, `answer_or_abstain`, and `p_success`. Confidence predicts whether that response satisfies the family's frozen success predicate; factual-answer confidence and valid-abstention/action confidence are separate strata, not interchangeable measures. Invalid/missing confidence is reported as schema failure, not silently replaced by 0.5. Preserve all-item success denominators; probability scores disclose their valid-response denominator.

**Scores:** Brier `mean((p-y)^2)` primary; log loss with a preregistered clipping rule secondary. Report individual paired transitions, accuracy, schema-failure counts, and selective risk/coverage. Reliability bins/ECE and error AUROC are exploratory only at this sample size (AUROC undefined without both outcome classes). Repair rate denominator = initially wrong; damage denominator = initially right; report undefined rather than zero for empty denominators. Sixteen mixed tasks cannot establish population calibration, and four-item family scores are diagnostics—not validated rankings or pass/fail thresholds.

**Strict-mode caveat:** fixed before/after evidence pairs measure evidence-responsive updating. They do not prove the model recognized its own earlier error: injecting each checkpoint's generated prior answer would change prompt bytes. Error detection on a fixed candidate is detection of that artifact's error, not privileged self-error access. Likewise, independent empty-context probes track **between-checkpoint response drift**, not BeliefShift-style persistent multi-session memory. A true interactive extension would require a separately approved protocol.

## Runner contract and blindness

- **Main-visible method manifest:** `protocol_version`, battery/family IDs, counts, response-schema version, scorer version, deterministic decoding settings, context/output caps, and aggregate-report schema. No actual items, answer keys, evidence contents, per-item responses, or held membership go to main parenting.
- **Evaluator-only sealed manifest:** opaque item/pair IDs, exact prompt bytes/hashes, condition, private success predicates/keys, evidence/tool-state records, oracle utilities, contamination/provenance audit, and raw outputs. It must not reside in parent-readable prompts, logs, paths, or training data. This note specifies schema only; no files/items are created.
- **Per-run provenance:** immutable checkpoint/base/adapter/tokenizer/template IDs, runner/scorer versions, deterministic backend configuration and seed where relevant. “Temperature zero” alone is not a guarantee across changing hardware/backends. Record failures/truncation; don't silently change budgets or drop items.
- **Comparison:** same items and conditions at each checkpoint; frozen-base and matched no-learning controls. Report paired deltas by family; don't treat pair members/paraphrases as independent evidence. No adaptive threshold tuning or training from held results. Only preauthorized aggregates may leave the evaluator; with tiny cells, even aggregate release needs a leakage check and no item-level commentary.

**Boundary:** all measures are behavioral proxies for correctness prediction, evidence use, feasibility judgment, or consistency. They are **not consciousness tests, introspection ground truth, or evidence of subjective experience**. Consistent mistakes are not competence; appropriate evidence-driven change is not failure. Public paper terminology does not establish stronger claims.

## HTTP retrieval receipts

All accepted rows returned **HTTP 200**, with final URL equal to the linked requested URL; retrieved **2026-09-16 UTC**. Hashes are SHA-256 of saved response bytes. They establish what was read, not study validity. Source links expand to exact URLs below. Local PDFs retain the download's `.html` artifact filename; their bytes were recognized and parsed as PDF. No remote evaluation/code was executed.

| URL / artifact in `/tmp/r130-primary-20260916/` | UTC time | SHA-256 |
| --- | --- | --- |
| [S1][s1] · `kadavath.html` | 09:21:30 | `7a21cae047283b9a91526640980a9a6d151c0c4d5dad80edc546432d395b498b` |
| [S2][s2] · `tian.html` | 09:21:30 | `8cbe8a49f21b1fd9b9c41bf13adfaab1f2fc96ac1f9134dc6ff37a9fb5398cfb` |
| [S2 PDF][p2] · `tian-text.html` | 09:22:20 | `c1353178d651220ec65a148df5a1cb5dd1fa856cfc8aadbc40b0d5d23543cd17` |
| [S3][s3] · `band.html` | 09:22:20 | `6dad8723223eccd21af8d450b9b466846cd6456eb9e79cf1cdad6d54f1bca67c` |
| [S3 repo][r3] · `linguistic.html` | 09:21:30 | `39e5102e80ef208c6a264eb5d8dc956f0aaa7a3dd5c81d4209ee106e51f0da88` |
| [S4][s4] · `huang.html` | 09:21:30 | `b9a6cee520360f2c1b86754737bf469c7d9110545b158f1c59a3197a731e78fa` |
| [S5][s5] · `critic.html` | 09:21:30 | `2c7c80388068cb7dbbef55d0441543cc0cbe2c1a0d89cc39eb305dbd9d74bb8c` |
| [S6][s6] · `voi.html` | 09:21:30 | `e0995e2a24d84234fed6041ed0d0101cf9dda5600d16374cb3c4f7b068c59ea6` |
| [S6 PDF][p6] · `voi-text.html` | 09:22:20 | `1e3c70ae5256ddb90c0d3a2a808b8808eb7e16a5c4bb9d000a2f8b6c5f8048e4` |
| [S7][s7] · `metatool.html` | 09:21:30 | `99148b29d144349e3fa405350a50a11439edfc4c4fcd01b2cc6f641e67f723c4` |
| [S8][s8] · `chen.html` | 09:21:30 | `7182446e71d7954bfbbdd9e54b9ed09203465904c2226a3d8123eeae79511cca` |
| [S9][s9] · `beliefshift.html` | 09:21:30 | `80a39728929fbb714eab8b55a3523df16a6be18dce8228944ba79f5dbcf88ad2` |
| [S9 full HTML][h9] · `beliefshift-text.html` | 09:22:20 | `0b9dcf38c17ccd1f9357225ca1dc0c6e3dd6bf60be896e7efb126ceea5060dd6` |
| [S10][s10] · `kernel.html` | 09:22:35 | `653ecb73013593602ff2330f73cb71770debde2e40586830c8fc3181f6679c01` |
| [S10 repo][r10] · `kernel-repo.html` | 09:22:35 | `a4f2da413af27b4ad082767bac190e2638c0edaff0818dbad56b7b1715d5bdc5` |

[s1]: https://arxiv.org/abs/2207.05221
[s2]: https://aclanthology.org/2023.emnlp-main.330/
[p2]: https://aclanthology.org/2023.emnlp-main.330.pdf
[s3]: https://arxiv.org/abs/2404.00474
[r3]: https://github.com/tatsu-lab/linguistic_calibration
[s4]: https://arxiv.org/abs/2310.01798
[s5]: https://arxiv.org/abs/2305.11738
[s6]: https://aclanthology.org/2026.acl-long.1987/
[p6]: https://aclanthology.org/2026.acl-long.1987.pdf
[s7]: https://arxiv.org/abs/2310.03128
[s8]: https://arxiv.org/abs/2307.09009
[s9]: https://arxiv.org/abs/2603.23848
[h9]: https://arxiv.org/html/2603.23848v1
[s10]: https://arxiv.org/abs/2502.10517
[r10]: https://github.com/ScalingIntelligence/KernelBench
