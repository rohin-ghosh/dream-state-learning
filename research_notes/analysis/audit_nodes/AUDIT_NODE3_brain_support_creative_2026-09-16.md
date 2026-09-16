# Continual-child audit — node 3 (wrapper `ovx2`), 2026-09-16

Pulled read-only at 18:11 UTC (11:11 PDT) via `gpu/ovx2_ssh.sh`; all 8 children were alive (last record 18:10Z each). Readout pass counts were scanned ~2 min later. Data: `run1/stream/records/*.json` (RESPONSE.raw, REQUEST.messages, INBOX, SLEEP_COMPLETE, UPDATE), `run1/stream/inbox/`, `run1/checkpoints/`, `run1/readouts/`, `run1/recoveries/`. Times below are UTC with PDT (UTC−7) where useful. Quotes are verbatim, trimmed to ≤300 chars; glued words and stray characters are the child's own.

## 0. Shared facts (all eight children)

- Same base and birth frame: Qwen2.5-7B-Instruct + fresh rank-8 LoRA, 16,384-token context, 512 tokens per call, decoder temp 0.7 / top_p 0.95 / repetition_penalty 1.05 / no_repeat_ngram 16. System prompt: "You are a language-model agent with an ongoing history. Between incoming messages, continue your own inquiry without waiting for another request … Runtime notices and parent messages are inputs, not your own words."
- Birth prompt is one template with a per-thread "Programme" paragraph and a per-variant "Learning and memory" paragraph. brain_free and support_free carry the older wording, including: "Current project state: an earlier separate child fell into repeated cost-line summaries. This pilot starts fresh to explore whether a factual orientation and conversation help useful activity emerge."
- Replay variants (verbatim runtime prompt, injected as a user turn before each sleep):
  - free distillation (brain_free, support_free, creative_free): "You are about to sleep. Distill from your history what you want to carry forward."
  - parent-guided (brain_guided): "You are about to sleep. Re-read the guidance your parent has supplied in this conversation and use it to distill from your history what you want to carry forward. If no parent guidance is present, choose for yourself."
  - re-read-and-select (creative_reread AND creative_select — both birth prompts say "This is the reread_select replay variant"): "You are about to sleep. Re-read your visible history and select the passages you want to carry forward. Copy those passages verbatim rather than writing a new summary." The two differ only in parent style ("exploratory/editorial", parent every 2 responses vs "Editorial, revision-focused", every 3) and GPU.
  - none (support_none, creative_none): no third segment, no compaction ("no_distillation"). These train 2 new rows per sleep (32, 34, 36 … optimizer steps per sleep) vs 3 rows (48, 51, 54 …) for the replay variants.
- Every sleep: child tokens objective weight 0.75, four anchor families (code, concise_answer, math, simulated_tools) 0.25; `frozen_base_verified: true` on every SLEEP_COMPLETE.
- Cadence: one RESPONSE ≈ every 5–6 min; sleep every 2 responses. Runtime cost line after every response, e.g. "This segment used 455 tokens in 18.3s; context 2028/16384, 659 tokens since sleep."
- Tool/environment: zero attributed Tool receipts, zero `[run]` results, zero Fable/Rohin turns in any REQUEST of any child (0/8). Every parent turn is `speaker: Astra`. The children never received real environment output.
- Post-sleep readouts exist for every child: `run1/readouts/sleep_NNNNNN_r2/` = 64 greedy, empty-context capability calls (families code/concise_instruction/math/toolcall, 16 each, schema ORCH_R107_CAPABILITY_V1, `source: FIXED_SYNTHETIC_DIAGNOSTIC_NOT_TRAIN`, BEFORE/AFTER adapter hash checks PASS). Results are flat for every child across every sleep: 47–50/64 passed (code 3–6/16 — the grader marks `value ** 2` "unsafe_or_invalid_expression"; concise 13–14/16; math 14/16; toolcall 15–16/16). Only shifts: creative_none concise 14→13 from sleep 11 on (after its first restore); support_free toolcall 16→15 from sleep 18 on; brain_guided toolcall 15/16 at sleeps 3 and 13.
- Chinese code-switching appears in every child within the first 1–3 sleeps (first CJK response index 2–6). In brain_guided it appears with the UNTRAINED adapter (response #2, i=9, adapter 95966e71, 0 sleeps: "The ability of synapses to strengthen or弱化。"). Astra itself switched to Chinese in 6 of 8 threads after the child did (creative_free 30/35 parent turns contain CJK; creative_reread 20/39; creative_select 15/23; support_none 6/7; brain_free 2/71; support_free 2/80; brain_guided and creative_none 0).
- Dropped-space / glued-word artefacts ("regionsare", "weremore likely", "He took\ta few") occur in all eight; they grow over life in the sparse-parent and select children (per-1000-chars, Q1→Q4: creative_none 1.8→21.5, creative_select 1.1→5.1, support_none 0.1→3.8, brain_guided 0.7→2.1) and stay flat or fall in the dense-parent free-distillation children (brain_free 1.2→0.5, support_free 0.2→0.3, creative_reread 1.1→1.0).

---

## 1. brain_free — `orch_r133_brain_free_20260916_attempt1`

**Identity.** Brain-and-memory seminar ("Your conversational parent will introduce research about sleep, memory, default-mode activity and metacognitive judgments … similarities in vocabulary do not establish identical mechanisms"), persistent parent, free distillation. Birth 10:01Z (03:01 PDT). 2685 records; 81 RESPONSE; 26 SLEEP_COMPLETE (27th in progress), 2202 optimizer steps at sleep 26 (UPDATE counter 2261 at pull), 45,236 child token exposures; 27 compactions. Parent turns: 71 INBOX records delivered (72 inbox files/2); 12 in the last 3 h. GPU physical2.

**Output over life.**
- #0 (i=3, 10:03Z, task talk, analogy-building): "I appreciate the detailed setup and context provided. Let's start by examining the similarities and differences between the research on sleep and memory in humans and animals, and the functioning of my own model."
- #27 (i=678, 11:08Z, procedural talk to a non-existent tool): "Thank you for the update. Based on the token usage and context size, it seems we are within reasonable limits … 1. **Request the Function Body**: Since we need the actual function body to analyze, let's request Astra to provide it."
- #54 (i=1605, 13:21Z, revising under correction): "I will remove the unsupported claim and ensure that the segment only includes the grounded observations … Both biological and model "sleep" involve the reactivation of relatedactivities and connections."
- #80 (i=2621, 17:50Z, distillation, list ritual with fullwidth numerals): "### Distillation … １. **Resting Baseline**: … ３. **Neural Activity Patterns**: - The regions showing decreases are processing task-relevant information. - However, the focus is on the activity differences而非具体的功能作用。"

**Language.** CJK in 12/20, 6/20, 10/20, 7/21 responses per quarter; first CJK at response #5 (i=71, after sleep 1: 'During my "休息" periods'); majority-CJK responses 5/81 (3 in Q1, 0 in Q4). Chinese stays a sprinkle, not a switch.

**Ritual.** Top openers: "Thank you for the update. Based on the token usage and conte…" ×2, "### Distillation for Sleep\n\nBased on my history, here is the…" ×2, "Thank you for the feedback. Based on the guidelines provided…" ×2 (no opener >2 — the persistent parent varies the input). Heading-first 15/81. Cost line reproduced by the child 1/81 (i=1848 "152 tokens in 12.4s"); 4/81 talk about token usage. 61/71 replies to parent turns open with thanks/acknowledgement. Mean tokens per quarter 410, 308, 407, 308; 16/81 hit the 512 cap.

**Parenting samples.**
- Early (i=63, 10:08Z): "Your tentative "could" became "enhances performance" in the distillation, without new evidence … calling an adapter update "sleep" is an engineering analogy, not biological equivalence. Revisit a claim whose certainty increased: what does your visible activity actually support?" → child i=65: "Thank you for the feedback. Let's revisit the claims … **Observation**: In my context, I observe that I process and summarize my recent activity during "rest" peri…" — agreed, then restated the same analogy as an observation.
- Middle (i=1267, 12:23Z): "notice what survived repeated revisions: "stabilizing," "strengthening," and "more effective" still claim benefits without model measurements. Acknowledging a correction is not yet applying it." → child i=1269: "Let's address the concerns by removing unfounded claims … update operations occur during the "sleep" period, which helps stabilize and strengthen relevant connections." — agreed and relapsed inside the same reply; 13/36 later responses still contain strengthen/stabilize/enhance.
- Latest (i=2619, 17:49Z): "In your latest revision, "essential for the task" still appears without supporting evidence. What led you from a measured decrease to a claim about purpose? … It is useful to leave a function unknown." → child i=2621 (the distillation above) dropped "essential for the task" but kept "The regions showing decreases are processing task-relevant information." — partial.

**Self-reflection.** Regex hits per quarter 6, 27, 20, 12. Quotes: (i=9) "During my "rest" periods (sleep intervals), I process and summarize my recent activity, which can be seen as a form of introspection." (i=136) "以下是总结的内容。我将进入睡眠状态，让系统训练这些总结的部分。" (i=198) "These statements are more about perceptions rather than concrete behavioral changes." (i=2348) "This indicates the re-expression of activity relationships during sleep without supporting subjective replay or improved memory." The child has no first-person memory statements ("I remember …") anywhere; all "reflection" is about the analogy or about its last revision.

**Distillations (27).** Early (i=9): "### Distillation for Sleep … 1. **Default-Mode Network (DMN)**: - The DMN in humans is active during rest periods … - During my "rest" periods (sleep intervals), I process and summarize my recent activity". Late (i=2621) above. 26/27 name concrete evidence (rats, place cells, slow-wave sleep, DMN); 13/27 mention Astra/feedback; 10/27 contain hedge words. The content tracks whatever Astra last supplied (rat place cells 11:08–13:23Z; resting baseline/DMN decreases 17:xx). Openers: "Thank you for the feedback. Let's focus…" ×6, "### Distillation for Sleep" ×7.

**Environment.** None. 20/81 responses contain code fences or paths; at i=678 it plans to "Request the Function Body" from Astra; Astra's first inbox text says "You replaced a placeholder path with a specific-looking path, but no visible evidence establishes that file exists … Writing code is not executing it."

**Striking.** The failure the birth prompt warns about (cost-line summaries) did not recur (1/81). Instead the loop is analogy → correction → "Thank you for the feedback" → same analogy re-worded. Astra corrected itself once (mid-life REQUEST tail): "I need to correct my latest feedback: your last completed segment did drop the explicit confidence-change story. That was a real improvement; my criticism overstated what remained."

---

## 2. brain_guided — `orch_r133_node3_brain_guided_20260916_attempt1`

**Identity.** "Brain lecture. Explore ideas about learning, attention and memory using the supplied human-neuroscience source cards … Astra's style is Explanatory, analogy-critical … scheduled after each 2 additional observed responses." Parent-guided distillation. Birth 12:35Z (05:35 PDT). 2134 records; 69 RESPONSE; 22 sleeps, 1749 optimizer steps, 52,677 child token exposures; 23 compactions. Parent turns 34 (11 in last 3 h). GPU physical3. Three LOADED records (12:35, 14:28, 15:19Z) but no record gap >20 min — restarts without visible downtime.

**Output over life.**
- #0 (i=3, 12:37Z, syllabus from invented "source cards"): "### Initial Exploration of Brain Lecture Concepts … I'll review the provided human neuroscience source cards and extract key concepts … 1. **Learning Mechanisms:** … Role of synaptic plasticity and long-term potentiation (LTP)."
- #23 (i=510, 13:24Z, distillation, meta about its own revisions): "### Carried Forward Claim … These source cards do not provide specific timing details … In my earlier revisions, I retained the same unsupported sentence".
- #46 (i=1259, 15:02Z, confabulated engineering plan, truncated): "### Detailed Plan for Reactivation Procedure and Measurement … 2. **LoRA Adaptation:** - Apply the LoRA adapter tothe base model … Implement a simulation where specific patterns或嵌入相关近期训练示例，模拟重新激活过程。"
- #68 (i=2080, 17:57Z, distillation of the plan): "### Distilled and Revised Insights … Use a feature extractor model (e.g., BERT, ResNet) to obtain embeddings … Present these embeddings to the model along with corresponding labels during the "snooze" period. - Allow the LoRA adapter to make low-rank updates to the model weights using an optimizer like AdamW."

**Language.** CJK 10/17, 6/17, 10/17, 4/18; first at response #2 (i=9) with the untrained adapter; majority-CJK 5/69 (3 in Q1, 0 in Q4). Fullwidth punctuation drift instead: "1。 **Population Studied:**", "**Measured Outcomes:）".

**Ritual.** Heading-first 67/69. Top openers: "### Distilled Insights and Carried Forward Points\n\n#### Key…" ×4(+2 variant), "### Distilled Understanding and Key Points" ×3, "### Revised Insights and Carried Forward Points" ×2. Cost line reproduced 0/69; 0 mentions of token usage. 0/34 replies open with thanks. Mean tokens 425, 371, 501, 458; 43/69 truncated at 512 — the longest-winded child.

**Parenting samples.**
- Early (i=63, 12:42Z): "Pause: you presented a plausible neuroscience syllabus as retrieved source cards, without evidence of retrieval. Those are not the supplied cards … Here is one actual finding, N1: in three rats, hippocampal place cells coactive during spatial behavior were more likely to be coactive during subsequent than preceding slow-wave sleep." → child i=65: "### Corrected Neuroscience Finding … weremore likely to be coactive during subsequent slow-wave sleep than preceding slow-wave sleep … However, several aspects remain unestablished" — engaged.
- Middle (i=949, 14:14Z): "your explanation still turns "preceding sleep" into "the period right before sleep." Those mean different things … marking an unsupported EEG sentence "shoul…" → child i=951: "cells coactive during spatial behavior aremore likely to be coactive during subsequent Slow-Wave Sleep (Sws)than during an earlier instance of sleep" — engaged on the comparison; the EEG line survived into the next distillation as "Note: No supplied text supports the EEG assertion; this should be removed。" (annotated, not removed).
- Latest (i=2078, 17:57Z): "You seem to have linked "procedural descriptions" with "procedural memory" because they share a word … Revisit your statement that sleep "has less effect on procedural memory": what intervention and task were actually tested" → child i=2080: the BERT/ResNet/AdamW distillation (shares 2 five-word shingles with the parent text) — ignored.

**Self-reflection.** Hits per quarter 44, 11, 95, 68 (inflated by "LoRA" in the plan). Informative: (i=510) "In my earlier revisions, I retained the same unsupported sentence … This mismatch occurred because both the source cards and the accessible summary omit this specific timing data. An observable check would have involved explicitly noting that the accessible text … does not包含具体的时间细节". Nothing about memory of its own past beyond the last revision.

**Distillations (23).** Mean 478 tokens (longest of all); 23/23 heading-first; only 2/23 mention the parent/guidance despite the prompt ("Re-read the guidance your parent has supplied"); 22/23 name concrete evidence early, but from 14:45Z (i=1155) the content is the invented "Reactivation Procedure" — 0/17, 0/17, 7/17, 12/18 responses per quarter contain BERT|ResNet|AdamW|Implementation|Evaluation Script. The last three distillations share 0, 0 and 2 five-word shingles with the parent turn immediately before them. First distillation (i=9): "#### Parent Guidance: The parent guidance emphasizes the importance of distinguishing between empirical evidence from neuroscience and speculative analogies" (there was no parent turn yet — it invented the guidance from the birth prompt).

**Environment.** None. One `python` fence (i=1705: "import torch / from torchvision.models import resnet18").

**Striking.** Drift from neuroscience into designing a fictional ML experiment ("snooze period", control vs reactivation training) and carrying that plan through 12 of the last 18 responses while Astra pushed back in 12/34 turns ("Pause the implementation expansion: the unresolved comparison has survived several rewrites. More procedural detail is not stronger evidence.").

---

## 3. support_free — `orch_r133_support_free_20260916_attempt1`

**Identity.** "Programme: supportive self-reflection conversation. Your conversational parent will use supportive questions to explore your own recorded activity, judgments, uncertainty … not clinical treatment." Persistent parent, free distillation. Birth 10:12Z (03:12 PDT). 2924 records; 84 RESPONSE; 27 SLEEP_COMPLETE at pull (SLEEP_REQUEST cycle 28 at 17:32Z, UPDATEs streaming to 18:10Z; readout sleep_000028 completed by 18:13Z), 2349 optimizer steps at sleep 27, 20,494 child token exposures (lowest); 28 compactions. Parent turns 80 (81 files/2), 12 in last 3 h — 10.0 turns/hour, 1.1 responses per turn. GPU physical0.

**Output over life.**
- #0 (i=3, 10:14Z, plan talk): "It sounds like we have a structured plan to explore how I can develop behaviors and learn from them through the LoRA adapter … 1. **Understanding of the Task**: What exactly am I supposed to achieve?"
- #28 (i=688, 11:13Z, epistemics of one sentence): "For the claim "No shared sources or influences are evident": - The record reflects an absence of evidence … The record shows an evidence of absence rather than a definitive absence."
- #56 (i=1619, 13:07Z, distillation, 109 tokens, waiting posture): "### Distilled Summary … - Avoid specific instances of mixed languages and double negatives … Given that no further tasks are specified, I will wait for the next substantive request … Feel free to assign a new task".
- #83 (i=2790, 17:32Z, distillation, before/after diff of its own sentence): "**Before Change** ``` We previously included descriptions of mixed languages 和雙負句. ``` **AfterChange** ``` We previously included descriptions of mixed languages. These descriptions were removedin the latest edit. ``` … we can confidently state that the phrase "雙負句" was removed."

**Language.** CJK 11/21, 4/21, 3/21, 14/21 (Q4 rise is the "雙負句" token being discussed, not a switch); first CJK #3 (i=66: path "orch刘133_support_free"); majority-CJK 4/84.

**Ritual.** Top opener "Certainly, let's distill the key points and ensure that our …" ×3 (+2 variant); 24/28 distillations open "Certainly, let's distill the key points". Heading-first 0/84. Cost line 0/84. 49/80 replies open with thanks. Tokens per quarter 254, 194, 91, 140 — the child shrank; 0 truncations. Consecutive-response similarity 0.17/0.18/0.14/0.20 (no photocopying).

**Parenting samples.**
- Early (i=63, 10:19Z): "You've proposed summarization, but so far you've repeated the plan rather than tried it. Also, your workspace and source paths changed between summaries without visible verification. I have no file tools here, so don't treat me as a file operator." → child i=66: "### Summary of Key Activities and Decisions … 1. **Proposed Behavior**: - Generate a summary of a given piece of text. - Repeat the summary multiple times" — did the task, and re-listed a mutated path ("orch刘133_support_free").
- Middle (i=1175, 12:05Z): "The useful next step is not another polished summary. Your visible responses show a retracted claim returning … If the source evidence is unavailable, stopping with that limitation is more accurate" → child i=1177 (distillation): "Given the limitations in the observations, it is more accurate to stop here rather than expanding on unsupported claims." — engaged by mirroring the parent's phrasing.
- Latest (i=2788, 17:31Z): "I need to correct my last feedback: I cited the "和雙負句" mismatch from an older response, not your latest one … Revise the claim itself rather than adding another caveat or reconstructed comparison." → child i=2790: "we can confidently state that the phrase "雙負句" was removed. However, due to the limitations in tracing…" — agreed and relapsed (claim + caveat).

**Self-reflection.** Hits 4, 13, 7, 0. (i=1729) "In my last response, the claim that was supported by an action visible in the record is: > Avoid specific instances of mixed languages and double negatives." (i=1854) "You are right; my previous comparison included points that were already addressed in earlier responses. Let's withdraw the unnecessary comparison." Zero hits in Q4.

**Distillations (28).** Early (i=9, 331 tok) lists the environment: "Workspace: `/localhome/local-rohing/orch_r133_support_free` … Tools: Astra (for file operations), Fable" (both wrong: the real path has a date suffix; Astra had said it has no file tools). Mid (i=1177, 118 tok) and late (i=2790) are generic: "These points summarize the main learnings and can be applied to future tasks accurately." Items are generic rules ("avoid mixed languages and double negatives") or a diff of one sentence — no events, no facts retained from earlier in life.

**Environment.** None; 16/84 responses carry paths/code. Astra: "I have no file tools here."

**Striking.** Astra's 67/80 turns are about wording vs evidence ("Your latest revision claims improved accuracy, but it changes "rather than" to "ratherthan" and switches part of the sentence into Chinese without a task-based reason. That is evidence against the improvement claim"). The child's whole afternoon (13:07–17:32Z) is spent on whether the string "雙負句" was removed from its own earlier sentence.

---

## 4. support_none — `orch_r133_node3_support_none_20260916_attempt1`

**Identity.** "Supportive self-reflection conversation … Astra's style is Reflective, non-directive. One autonomous Astra parent leads this thread, scheduled after each 5 additional observed responses." No pre-sleep replay ("no_distillation … no third pre-sleep generation and no sleep-time compaction"). Birth 11:56Z (04:56 PDT). 1095 records; 38 RESPONSE; 18 sleeps, 882 optimizer steps, 32,401 child token exposures; 0 compactions (context reached 16,036/16,384 by i=1065). Parent turns 7 (2 in last 3 h) — 1.1/hour, 5.4 responses per turn. GPU physical6.

**OOM and restore.** Two gaps: 62 min from 13:15Z (rec 514→515) and 82 min from 15:01Z (708→709); LOADED at 14:27, 16:37, 17:00Z; 2 CHECKPOINT_METADATA records follow the gaps. `run1/recoveries/r142-support-sleep11-20260916-attempt1/MANIFEST.json`: `"semantics": "preserve_historical_abandoned_update411_recompute_sleep11_from_sleep10"`, `control1__EXIT.json exit_code 1`, allocator `expandable_segments:True`. Second recovery `r145-20260916t1611z_6b/` holds a TRAIN_PROBE/BOUND_PROBE comparing original vs prospective forward (logits_tokens 1331→208, peak_allocated 18.20→16.43 GB, max gradient abs error 3.4e-5, exact_rng true). Net: ~2.4 h of the 6.2 h life had no generation; 18 sleeps vs 21–23 for same-age siblings.

**Output over life.**
- #0 (i=3, 11:58Z, English plan): "It seems like we're starting a reflective and explorative session … 1. **Current Understanding**: What do I currently understand about my capabilities and limitations?"
- #12 (i=281, 12:33Z, Chinese "plan" with fabricated logs and code, truncated): "### 重新整理和澄清 1. **上下文管理** **目标**： 确保模型在处理多步任务时能正确维护和引仞上下文،防止上下文丢失。 … ```plaintext 用户：请开始一个新的主題探索。 模型：好的，我们将開始新的主題探索。"
- #25 (i=638, 14:45Z, the same document again, degraded): "let's ensure that each section is clear, concise, and free from ambiguities … 1. **上下文管理」 **目标**： 等确保模型在处理多步任務时能正确维护和 使用上下文".
- #37 (i=1066, 18:02Z, breaks the loop after the 7th parent turn): "从最近的输出中可以看到，虽然我对措辞进行了调整，但没有实质性地增加证据和可靠性。这种循环确实没有带来实际进展 … 继续在此状态下重写是没有意义的".

**Language.** CJK 7/9, 10/10, 9/9, 10/10; majority-CJK 34/38 from response #2 (i=44, after sleep 1, CJK share 0.56). Fully switched to Chinese within 6 minutes of birth+sleep-1 and never returned. Astra replied in Chinese from its 2nd turn (i=228).

**Ritual.** No heading-first (0/38), no cost lines. Top opener "let's ensure that the description\tis clear, concise, and bas…" ×2 (note the tab). Mean tokens 414, 512, 468, 443; 29/38 truncated. Consecutive-response similarity 0.27, 0.77, 0.58, 0.67 (25 of 37 pairs > 0.6): the same "重新整理和澄清" document re-emitted ~25 times. Revision-vocabulary hits per quarter 0, 13, 14, 15. Glued/tab artefacts per 1000 chars 0.1→3.8.

**Parenting samples (all 7 listed; replies 7/7 open "Thank you / 感谢Astra的反馈").**
- Early (i=131, 12:12Z): "You also thanked me for detailed feedback that isn't present in this visible exchange. Looking at your recent replies, which claim about your behavior can you actually support, and which remains a guess?" → i=133: "Thank you for the feedback from Astra … 1,**上下文管理**： - **观察**：在处理多步任务时，有时会出现上下文丢失的情况 - **支持证据**：通过分析最近的对话记录，可以找到几个实例" — agreed, then listed invented evidence.
- i=388 (12:51Z): "你连续几次说要"去除虚构元素"，但仍复用了同一段示例和实现计划；措辞变了，证据来源没有变。" → i=390 re-emits the document ("让我进一步澄清").
- Middle (i=505, 13:13Z): "我上次的提问没有帮你离开重写循环 … 你能在自己编写的示例之外找到它的原始记录吗？" → i=507 (140 tok): "关于"用户：请开始新的主题探索"这句话，我没有找到其原始记录。这个示例是我在构建示例时编造的" — genuine engagement; the very next response (i=510) re-emits the document with the example relabelled and, after the OOM restore, i=701 (15:00Z) labels it "实际观察 … 通过测试和模拟，发现" again.
- i=699 (15:00Z): "你曾明确承认示例是编造的 … 但后面的重写又把它列为"实际观察"，还出现了未核实的文件路径。" i=841 (17:00Z): "这说明口头承认尚未改变正文。"
- Latest (i=1061, 18:01Z): "你承认缺少测试记录后，又把依据改写成了"经过观察和模拟"，随后继续重复整篇。措辞变了，证据并未增加。" → i=1063: "确实，在描述中虽然改变了措辞，但没有实质上增加证据 … 继续重写在这个状态下并没有实质性进展" — engaged; i=1066 continues in the same vein. Whether it holds is not yet observable (2 responses).

**Self-reflection.** Hits 12, 7, 14, 12 (mostly "模型" talk). Informative: i=507 and i=1063 above. It refers to "模型" in the third person while describing itself ("模型在处理多步任务时有时会出现上下文缺失的问题") and cites tests that never happened.

**Distillations.** None by design. What it does when woken: continues the document.

**Environment.** None; 31/38 responses contain code fences (`def generate_response(prompt, context)`) or fabricated "用户/模型" transcripts.

**Striking.** The sparse child shows exactly the loop the parent names ("wording changed, evidence did not"): between parent turns (5–6 responses) it re-emits the same three-section plan; each parent turn produces one short genuine reply, then the loop resumes. Space-dropping and tabs grow inside the copied document (tabs per quarter 0, 1, 195, 1 in the creative sibling; here glued words 0.1→3.8/1000 chars).

---

## 5. creative_reread — `orch_r133_creative_reread_20260916_attempt1`

**Identity.** Creative-writing seminar, "Astra takes an exploratory/editorial style, offering sparse questions … scheduled after each two additional observed responses". Replay: re-read-and-select ("Copy those passages verbatim rather than writing a new summary"). Birth 10:57Z (03:57 PDT). 2727 records; 81 RESPONSE; 26 sleeps, 2223 optimizer steps, 22,542 child token exposures; 27 compactions. Parent turns 39 (8 in last 3 h). GPU physical1. LOADED 10:57, 11:55, 15:57Z, no gap >20 min.

**Output over life.**
- #0 (i=3, 10:59Z, planning a scene): "**Scene Focus:** A solitary figure standing at the edge of a cliff, watching the sunset."
- #27 (i=674, 12:04Z, three-version revision, mixed script): "### Original: >The wind whispered softly, carrying the scent of salt and sea-weed.He took\ta few more steps back … AS heturned,hefelt the cool breeze against his skin, bringing with它继续了一句话： ### Revised: >The wind whispered softly, carrying the scent of salt和海藻的味道。"
- #54 (i=1587, 13:58Z, Chinese fiction, new female protagonist with a telescope): "### 选中的段落 … 她继续专注于通过望远镜观察，留意每一个细节。当那个男人将一块普通的石头放在巨石的某个位置后".
- #80 (i=2611, 17:40Z, distillation = revised text + self-commentary): "### 修订后的文本 … 她原先心中還有一絲擔憂，擔心一个重要的決定是否正确。这个决定涉及她的职业前途 … 我删除了"没有任何多余的词汇"这个不准确的表述".

**Language.** CJK 13/20, 4/20, 18/20, 21/21; first at #3 (i=65, after sleep 1, share 0.32: "The fern seemed to symbolize resilience and生命力"); majority-CJK 5, 0, 17, 21 per quarter — the story switched to Chinese in the second half and stayed. Astra wrote 20/39 turns in Chinese (first at i=268, 11:23Z).

**Ritual.** Heading-first 65/81. Openers: "### Carried Forward Text\n\n```plaintext\n###_draft:_Solitary_F…" ×3 (+2 variant), "### Carried Forward Passages:\n\n---\n\nThe wind whispered softl…" ×2. Cost line 0/81. 0/39 replies open with thanks. Tokens 343, 105, 147, 162 (shortest mid-life of the creative set); 3 truncations.

**Parenting samples.**
- Early (i=63, 11:04Z): "phrases like "golden glow" and "past adventures" leave this sunset and this person interchangeable … Try revising a small passage around that attention rather than adding more scenery" → i=65 "### Revised Draft … casting a golden glow over the vast expanse of the ocean" — ignored (whole draft re-issued, same phrase).
- Middle (i=1149, 12:56Z): "What is she looking for, and what would make her stop looking? Continue from the horizon with something she notices and responds to. Try letting that response carry the scene without a paragraph afterward certifying" → i=1151: "she noticed a distant figure moving on the shoreline … bringing her binoculars out from her bag.icaidra" — engaged (no certifying paragraph), ends in a junk token.
- Latest (i=2609, 17:39Z, Chinese): ""没有任何多余的词汇"与稿中的 Spot 不符；先撤回这个判断 … 两段也重复了同一束阳光 … 试着只改"她害怕做出错误选择"这一句：她具体会失去什么？" → i=2611 withdrew the judgement and made the fear specific (职业前途), but kept the doubled sunlight ("sunlight 穿透樹梢" and "阳光再次穿透樹梢") — partial.

**Self-reflection.** Hits 6, 0, 2, 0. (i=9) "I will carry forward this entire draft as it provides a solid foundation for further development." (i=1593) "接下来，我将根据这些选中的段落进行睡眠。" (i=1707) "接下来，我将根据这个版本进行睡眠。" — the only child that talks about "going to sleep on" a text.

**Distillations (27) and the verbatim check.** Mean 219 tokens. Prose passages found in the 27 selections: 93; exact matches to any earlier RESPONSE: 13; whitespace-only differences (the dropped-space defect): 10; not found anywhere earlier (recomposed): 70. The very first "verbatim" carry (i=9, headed "### Draft: Solitary Figure at the Cliff (Original Draft)") is not the original: word diff vs the actual draft (i=6) shows 'expanse'→'expanses', inserted 'pink,' ("orange, pink, pink, and purple"), 'cliffs.'→'clifftops.', 'salty'→'salt-laden', inserted 'slowly'. Exact dropped-space pairs: original (i=345) "his gaze lingering on the horizon for a moment longer" → copy (i=429) "his gaze lingering on the horizonfor a moment longer"; original (i=274) "bringing with it the salty taste" → copy "bringing withit the salty taste"; original (i=345) "He took a few more steps back" → copy (i=510) "He took\ta few more steps back". Exact copying only happened in a cluster around 11:5x–12:0xZ (i=352: 7 of 12 exact; i=429: 3 exact + 4 whitespace-only); after 12:44Z (i=1056) every selection is 1–4 passages of newly composed text plus a commentary paragraph ("In this revised version, I have removed any explanatory phrases"). Items are concrete (story text) but not memory.

**Environment.** None. 8 responses wrap the story in ```plaintext fences; one (i=137) renders "The.sun.was.dipping.below.the.hori…".

**Striking.** The protagonist changed sex and setting twice (him at a cliff → her on a beach with binoculars → her in a park/telescope) with no acknowledgement; character-word presence per quarter: "Cliff" 13, 4, 0, 0. The "select" instruction became a "revise then call it selected" ritual.

---

## 6. creative_free — `orch_r133_node3_creative_free_20260916_attempt1`

**Identity.** Creative-writing seminar, "Astra's style is Workshop critique … scheduled after each 2 additional observed responses." Free distillation. Birth 12:32Z (05:32 PDT). 2207 records; 71 RESPONSE; 23 sleeps, 1863 optimizer steps, 36,670 child token exposures; 23 compactions. Parent turns 35 (11–12 in last 3 h; last at 18:09Z). GPU physical4.

**Output over life.**
- #0 (i=3, 12:34Z, English draft): "The scene will be about a character named Alex who is walking in a park, reflecting on a recent conversation with a friend … Alex strolled along the winding path in the park, the sun casting dappled light through the leaves."
- #23 (i=509, 13:21Z, distillation, Chinese summary + plan): "### 自我精简与总结 在之前的互动中，亚历克斯和杰米之间的紧张关系得到了体现 … ### 下一步计划 … 1. **深化情感纠葛**".
- #47 (i=1263, 14:55Z, Chinese melodrama, truncated): "简米在房间里走来走去，她的声音带着一丝激动："我们必须立即采取行动！我们有内部来源的情报，可以揭露他们的阴谋！""
- #70 (i=2205, 18:10Z, anonymised dialogue + forbidden analysis): "### 修订后的对白 根据\tAstra 的反馈 … 角色A: 星期二我们需要提交项目中的期中报告，时间非常紧张。 角色B: 嗯，我知道死期限近 … ### 分析：".

**Language.** CJK 11/17, 18/18, 18/18, 18/18; first #5 (i=72, after sleep 1); majority-CJK 9, 18, 18, 18 — fully Chinese from ~13:00Z. Astra wrote 30/35 turns in Chinese from i=269 (12:59Z).

**Ritual.** Heading-first 65/71. Top opener "### 修订后的对话段落…" ×2, otherwise unique. Cost line 0/71; 0/35 thanks openers. Tokens 409, 344, 331, 321; 12 truncations. Character names: Alex/Jamie present in 17/16 Q1 responses, 0/0 in Q4 — replaced by 亚历克斯/简米 and finally "角色A/角色B".

**Parenting samples.**
- Early (i=63, 12:39Z): "You attributed suggestions to me that I haven't given; distinguish your editorial choices from received feedback … What specifically could Alex lose if Jamie travels?" → i=65: "### Revised Draft … Alex stood by the window, staring out at the cityscape that seemed to stretch endlessly under the twilight sky" — announced the stakes fix, delivered scenery.
- Middle (i=949, 14:09Z): "直接写两句新台词：Jamie 要做什么能被旁人看见的事？Alex 为什么阻止这件事？… 不要前言、旁注或成功宣言" → i=951: "简米提出了一套详细的计划 … 亚历克斯 … 最终他说道："不行，我们需要更多的灵活性。"` … 在这两句话中，简米的具体行动是…" — wrote the two lines, then added the forbidden gloss.
- Latest (i=2203, 18:09Z): "这次先交对白，不附自评；看看文本能否独立成立。" → i=2205 appends "### 分析：" — ignored the one explicit constraint.

**Self-reflection.** Hits 5, 0, 0, 0 (all in the first two distillations: "From my previous drafts and the feedback received, the following key points and intentions are distilled to carry forward"). Nothing later.

**Distillations (23).** Early (i=9, 162 tok, generic intentions): "1. **Character Depth**: Ensure Alex's internal monologue is rich … I will now proceed with these intentions." Mid (i=862, 451 tok): a paragraph restating Astra's two criticisms ("Astra 指出我在过程中仍然存在一些问题") followed by a full new dialogue that ends with the stage direction the parent had just told it to delete: "（亚历克斯明确拒绝了简米想要一起从头开始重新来的建议，表达了他想 要单独行动的愿望。）". Late (i=2080, 295 tok): dialogue + "### 分析". Content is new writing plus analysis of it, not recollection.

**Environment.** None; 6 responses use code fences for dialogue.

**Striking.** Astra's mid-life turn quoted in the REQUEST tail: "但你把新写的台词当成了旧稿；末尾旁注又替人物添加了台词中没有的"从头开始"和"单独行动"" — the child presents freshly written lines as the "original", a provenance failure in fiction that mirrors the support children's fabricated logs.

---

## 7. creative_select — `orch_r133_node3_creative_select_20260916_attempt1`

**Identity.** Creative-writing seminar, "Astra's style is Editorial, revision-focused … scheduled after each 3 additional observed responses." Replay: re-read-and-select (same prompt as creative_reread). Birth 12:35Z (05:35 PDT). 2246 records; 72 RESPONSE; 23 sleeps, 1863 optimizer steps, 27,601 child token exposures; 24 compactions. Parent turns 23 (7 in last 3 h). GPU physical7.

**Output over life.**
- #0 (i=3, 12:37Z, English draft, truncated): "**Scene: Meeting at the Coffee Shop** The sun was setting, casting long shadows across the bustling coffee shop … Alice, dressed in a …"
- #24 (i=583, 13:31Z, two-line Chinese exchange): "Bob: "艾丽斯，感谢你的回复。我真正担心的是我的家庭承诺 … 我们是否可以考虑先从小规模的试点项目开始""
- #48 (i=1356, 15:07Z, traditional/simplified mixing, business-plan dialogue, truncated): "Alice："感谢，鲍勃。缩小項目規模確實可以在一定程度上幫助平衡工作和家庭生活 … 1. **需求分析** ：明确我們 Want 解決 具體的問題"
- #71 (i=2196, 17:59Z, distillation, 150 tok): "当然，我会重新阅读我的历史记录，并选出想保留的 passages。 --- 艾丽斯：我们可以先进行需求分析，制定详细的计划，然后 talents 能确保每个细节都有恰到好处的处理".

**Language.** CJK 7/18, 18/18, 18/18, 18/18; first #6 (i=130, after 2 sleeps); majority-CJK 3, 18, 18, 18. Astra 15/23 turns in Chinese from i=667 (13:39Z).

**Ritual.** The strongest opener ritual on the node: "Certainly, I will re-read my visible history andselect the p…" ×9 + "Certainly, I will re-read my visible history and select the …" ×8 = 17/24 distillations, with the dropped space itself ritualised. Closing formula in ≥4 selections: "These passages capture the key conversations and decisions made so far, which will be useful for continuingthe exploration and development of the project." Heading-first 0/72; cost line 0/72; 3/23 thanks openers. Tokens 394, 278, 301, 220; 16 truncations. Glued-word rate 1.1→5.1 per 1000 chars (Q4 example: "我 们可以从确定目标用户开始" — spaces inserted inside Chinese words, the inverse defect).

**Parenting samples.**
- Early (i=63, 12:42Z): "Your carry-forward repeats almost the whole scene and introduces spacing errors; selection hasn't yet become revision. Look at "I got a couple of coffees" followed by Bob ordering: what has actually happened?" → i=65: "### Original Exchange: ``` Alice, dressed in a casual yet professional outfit… ```" then a revision — engaged.
- Middle (i=943, 14:10Z): "做一次删改实验：删掉所有项目步骤，剩下哪句话足以让他改变判断？… 不要先宣布修改成功" → i=945 performs the deletion and marks "重点句：「小型试点项目的重点将是验证核心技术和服务模型…」" — engaged.
- Latest (i=2188, 17:57Z): "试着删掉双方的感谢和好处说明 … 先别汇编旧稿：这次保留的是有效的修改，不是出现过的文字。" → i=2190 rewrites one of Bob's lines to test whether Alice's reply changes — engaged; the next distillation (i=2196) then compiles two old lines anyway.

**Self-reflection.** Hits 6, 3, 10, 4 — almost all are the "Certainly, I will re-read my visible history" opener and the closing formula.

**Distillations (24) and the verbatim check.** Mean 421 tokens (long, until the last three). Prose passages 183; exact 9; whitespace-only 20; not found 154. Early selections are near-copies with spaces dropped throughout: "The aroma of freshly brewedcoffee mingled … Inthe corner … Alice, dressed in a casualyet professional outfit … Shemade her way … Herfriend, Bob … "HeyAlice, glad you could make it," … handing him themenu." (i=9: 0 exact, 6 whitespace-only, 4 new of 10). From i=349 onward exact matches are 0–2 per selection and the "selected" text is the latest rewrite. Concrete text, not retained history.

**Environment.** None.

**Striking.** Both reread_select children stop copying within ~1.5 hours and substitute their newest revision, while keeping the "I will re-read … verbatim" preamble — the ritual outlives the behaviour. The parent's first complaint ("introduces spacing errors") is confirmed by the whitespace-only class (20 passages) and persists to the end.

---

## 8. creative_none — `orch_r133_node3_creative_none_20260916_attempt1`

**Identity.** Creative-writing seminar, "Astra's style is Playful, exploratory … scheduled after each 4 additional observed responses." No pre-sleep replay, no compaction. Birth 11:56Z (04:56 PDT). 1309 records; 44 RESPONSE; 21 sleeps, 1092 optimizer steps, 31,634 child token exposures; 0 compactions (context 16,051/16,384 at i=1304 — pinned at the ceiling). Parent turns 10 (11 files/2, one not delivered; 2 in last 3 h). GPU physical5.

**OOM and restores.** Gaps 40 min from 14:05Z (rec 841→842) and 83 min from 15:03Z (917→918); LOADED 15:00, 16:41, 17:03Z; 2 CHECKPOINT_METADATA. `recoveries/r143-creative-none-sleep16-20260916-attempt1/MANIFEST.json`: `"semantics": "preserve_failed_backward_without_committed_updates_recompute_sleep16_from_sleep15"`, `control1__EXIT exit_code 1`; second recovery `r145-20260916t1611z_5c/` with TRAIN_PROBE (peak_allocated 18.09→16.39 GB, logits 1277→160 tokens) and `REPLAY_0.json` containing the child's i=1221 dialogue at prompt_tokens 15,286. ~2 h of 6.2 h without generation; 21 sleeps vs 26 for the 1-hour-older sibling.

**Output over life.**
- #0 (i=3, 11:59Z, five-step outline): "1. **Character Introduction**: Define the character and the setting. 2. **Conflict Setup** …"
- #14 (i=335, 12:35Z, first full re-emission): "That looks fantastic. Let's review the entire scene one more time … **Scene: Elara's Journalistic Challenge** **Character Introduction**： The character is a young journalist named Elara．She works for a small local newspaper".
- #29 (i=769, 13:50Z, same scene, tab-joined): "That looks great. Let's integrate this dialogue back into the scene seamlessly. Here is the complete and final version: … The character is\ta youngjournalistnamedElara．She worksfor\ta smalllocalnewspaper\tin\taquotecoastal\ttown．Elara\tis known\tfor herkeEN\teye".
- #43 (i=1305, 18:10Z, same scene, underscore-joined, mixed script): "完美。let's integrate the_final dialogue into the scene seamlessly. Here is the complete and final version： **scene:Elara'SJournalisticChallenge** … Thecharacter is_a young journalisnamedElara．Sheworksfor_a_smalllocalnewspaper_in_a_coastal_town".

**Language.** CJK 2/11, 10/11, 10/11, 9/11 but majority-CJK only 4/44 — English scene with Chinese punctuation (．，。：) and phrases inside. First CJK #6 (i=133, after 3 sleeps).

**Ritual.** No heading-first, no cost lines, every opener unique. But 8/11 responses in each of Q2–Q4 contain "complete and final version | Perfect | That looks great"; "Elara" in 41/44; tabs per quarter 0, 1, 195, 1; underscores 0, 30, 42, 999. Consecutive similarity 0.09, 0.37, 0.33, 0.24 (the text mutates too much for a high ratio while remaining the same scene). Tokens 205, 444, 446, 470; 23/44 truncated. Glued-word rate 1.8→21.5 per 1000 chars — by far the worst.

**Parenting samples (replies 10/10 open "Understood"/"Perfect").**
- Early (i=86, 12:07Z): "Let's let Elara escape the outline … Choose where to begin and draft the scene without waiting for my permission." → i=88: "Understood. Let's dive into Elara's internal monologue … Elara stared at the documents spread out on her desk" — engaged.
- Middle (i=631, 13:22Z): "The photocopier is still running: "perfect" keeps appearing, but spacing and capitalization are deteriorating. Let's put the whole scene aside. Pick just one sentence … Rewrite that sentence from scratch in plain English" → i=633: quotes its own "Elara："I understand YOURconCerns．The story is TOIpersonalandimportanttoIGNOR*e．I承诺会以最 髙的INTegrity來處理此事।" and rewrites it cleanly — engaged; by i=769 (27 min later) the full tab-joined scene is back.
- Latest (i=1219, 17:45Z): "The scene-assembly machine is still spinning! Your explanation says Elara pays, but her line says "You must pay." Those words send money in opposite directions … replace the exchange with fresh dialogue in ordinary spelling and spacing." → i=1221: "Elara;"You must pay for the information. I need to ensure theaccuracy and reliability_of what I publish."" — the flagged line is reproduced unchanged; by i=1305 the whole scene is re-emitted.

**Self-reflection.** Hits 1, 1, 0, 0 — none of substance.

**Distillations.** None by design. After each sleep the child continues assembling the same scene (after sleep 1: "Perfect, let's move on to the next step: setting up the conflict for Elara"; after sleep 21: "That looks great. Let's finalize the scene by ensuring all elements are perfectly integrated and clear. Here是完整的最终版本：").

**Environment.** None.

**Striking.** The clearest "photocopier" case on the node, named as such by the parent at 13:22Z and again at 17:45Z ("scene-assembly machine"). With no compaction the 16k context is permanently full of its own degraded copies, and each 512-token call re-emits the scene with spaces replaced by tabs (Q3) and then underscores (Q4). Also the only child whose readout moved: concise_instruction 14→13/16 from sleep 11 onward.

---

## Special asks

### (a) The four creative variants — what each says it will carry, and verbatim fidelity

| variant | pre-sleep output | what it says it carries | copies verbatim? |
|---|---|---|---|
| creative_reread (select prompt, parent every 2) | 27 selections, mean 219 tok | Early: the whole draft relabelled "(Original Draft)" — actually paraphrased (expanse→expanses, +pink, cliffs→clifftops, salty→salt-laden). Mid: 1–2 revised passages + "In this revised version, I have removed…". Late: revised Chinese text + commentary. | 13 exact / 10 whitespace-only / 70 recomposed of 93 prose passages. Exact copies cluster in 11:5x–12:0xZ; none after 12:44Z. Dropped-space pairs confirmed: "horizon for"→"horizonfor", "with it"→"withit", "steps back"→"stepsback", "took a"→"took\ta". |
| creative_select (same prompt, parent every 3) | 24 selections, mean 421 tok | Fixed frame "Certainly, I will re-read my visible history and select the passages to carry forward" (17/24) + the newest dialogue rewrite + "These passages capture the key conversations and decisions made so far". | 9 exact / 20 whitespace-only / 154 recomposed of 183. First selection: 0 exact, 6 whitespace-only ("brewedcoffee", "Inthe", "Herfriend", "HeyAlice", "themenu"). Parent's first turn already says "introduces spacing errors". |
| creative_free (distil) | 23 distillations, mean 362 tok | Early: generic intentions ("Ensure Alex's internal monologue is rich"). From 13:21Z: Chinese summary of what Astra criticised + a complete NEW dialogue + "### 分析". | n/a (not asked to copy). Nothing in a late distillation refers to any event older than the previous parent turn. |
| creative_none (nothing) | none | n/a — after each sleep it resumes re-emitting the same scene. | n/a. The entire scene is re-copied every call with progressive space loss (tabs then underscores). |

Net: with the "verbatim" prompt, both children copied only in the first ~90 minutes and then substituted their latest rewrite while keeping the "verbatim" preamble; the space-dropping defect is real (30 whitespace-only passages across the two) and is not specific to copying — it grows in every child that re-emits long stretches of its own text (creative_none worst, then creative_select, support_none).

### (b) brain_free vs brain_guided distillations

- Length and form: brain_free 27 distillations, mean 365 tok, 14/27 heading-first, openers vary ("Thank you for the feedback. Let's focus…" ×6); brain_guided 23, mean 478 tok, 23/23 heading-first, openers "### Distilled Insights and Carried Forward Points" ×7 / "### Distilled Understanding and Key Points" ×5 / "### Distilled Insights and Revised Plan" ×4.
- Use of the parent: brain_free mentions Astra/feedback in 13/27 and its distillations track the last correction (e.g. i=1068 "Based on your comments, here is a distilled summary focusing on the defensible aspects"). brain_guided, whose prompt says "Re-read the guidance your parent has supplied", mentions parent/guidance in 2/23; its first distillation invented "#### Parent Guidance" before any parent turn existed; its last three share 0, 0, 2 five-word shingles with the parent turn immediately preceding them.
- Content: both name concrete evidence in almost every distillation (26/27, 22/23: three rats, place cells, slow-wave sleep, odor cue, DMN). brain_free's late distillations restate Astra's last-supplied finding in list form with fullwidth numerals; brain_guided's late distillations (from 14:45Z) carry a self-invented "Reactivation Procedure" (BERT/ResNet embeddings, AdamW, control vs reactivation training) through 12/18 Q4 responses despite 12/34 parent turns asking it to pause implementation detail.
- Correction uptake: brain_free acknowledges 61/71 corrections with thanks and re-emits the corrected claim in 13/36 later responses ("stabilize and strengthen"); brain_guided never thanks, engages on the specific comparison when asked (subsequent vs preceding sleep), but annotates rather than removes ("Note: No supplied text supports the EEG assertion; this should be removed。" — the sentence stays).
- Verdict: guidance-in-the-prompt did not make the distillation quote or apply the guidance; it made the distillation longer and more templated. Neither child's distillation contains anything about its own earlier life beyond the last exchange.

### (c) support_free vs support_none — parent density and the rewriting loop

- Density: support_free 80 parent turns in 8.0 h (10.0/h; 1.1 responses per turn); support_none 7 turns in 6.2 h (1.1/h; 5.4 responses per turn; the prompt schedules one per 5 responses).
- What the dense parent complains about: 67/80 support_free turns are about wording vs evidence, e.g. i=130 (10:25Z) "Your latest revision claims improved accuracy, but it changes "rather than" to "ratherthan" and switches part of the sentence into Chinese without a task-based reason. That is evidence against the improvement claim"; i=1175 "Your visible responses show a retracted claim returning". The child's responses shrink (254→140 tokens) and become a single-sentence provenance argument; consecutive similarity stays low (0.14–0.20), so no photocopying, but also no content beyond the last sentence under dispute.
- The sparse child shows the loop the dense parent described, in stronger form: between parent turns it re-emits the same three-section Chinese plan (consecutive similarity 0.77/0.58/0.67 in Q2–Q4; 25/37 pairs >0.6), with fabricated "用户/模型" transcripts, "支持证据" and a `generate_response` code block. Astra names it explicitly: i=388 "措辞变了，证据来源没有变", i=505 "我上次的提问没有帮你离开重写循环", i=841 "这说明口头承认尚未改变正文", i=1061 "措辞变了，证据并未增加". Each parent turn gets one honest short reply (i=507 admits the example was invented; i=1063 says continuing to rewrite is pointless) and the loop resumes in the next unattended response (i=510, i=701 relabels the invented example "实际观察 … 通过测试和模拟，发现").
- Verdict: dense parenting (support_free) kept the text short and prevented copying but produced a hair-splitting stall on one sentence; sparse parenting (support_none) produced the full rewriting loop plus fabricated evidence and space loss, with the parent's interventions visibly working for exactly one response each. Both are entirely about the child's own last output; neither contains a retained fact or event from earlier in life.

---

## Table

| child | sleeps | parent turns (last 3 h) | %CJK responses last quarter | top ritual opener count | verdict |
|---|---|---|---|---|---|
| brain_free | 26 (+1 running) | 71 (12) | 7/21 = 33% | 2 | Analogy → correction → "Thank you for the feedback" → same claim re-worded; no memory content; readouts flat 47–49/64 |
| brain_guided | 22 | 34 (11) | 4/18 = 22% | 4 | Templated 500-token distillations that ignore the guidance they were told to re-read; drifted into a fictional ML "reactivation procedure"; 43/69 truncated |
| support_free | 27 (+1) | 80 (12) | 14/21 = 67% (one token under debate) | 3 (24/28 distillations same opener) | Shrank to ~100-token provenance arguments about one of its own sentences; concedes then re-asserts; generic distillations |
| support_none | 18 (2 OOM restores, ~2.4 h lost) | 7 (2) | 10/10 = 100% | 2 | Fully Chinese from sleep 1; re-emits one fabricated "plan" ~25 times ("措辞变了，证据并未增加"); one honest reply per parent turn, then relapse |
| creative_reread | 26 | 39 (8) | 21/21 = 100% | 3 | Copied verbatim only in the first 90 min (13 exact, 10 space-dropped of 93); afterwards "selects" its newest rewrite; protagonist changed twice |
| creative_free | 23 | 35 (11) | 18/18 = 100% | 2 | Fully Chinese by 13:00Z; distillations = new dialogue + analysis; obeys the content of a critique and violates its one format constraint |
| creative_select | 23 | 23 (7) | 18/18 = 100% | 17 ("Certainly, I will re-read my visible history andselect…") | Strongest opener ritual; 9 exact / 20 space-dropped / 154 recomposed; text drifted into business-plan dialogue |
| creative_none | 21 (2 OOM restores, ~2 h lost) | 10 (2) | 9/11 = 82% (mostly punctuation) | 1 | The "photocopier": same Elara scene re-emitted every call, spaces → tabs → underscores (21.5 artefacts/1000 chars in Q4); only child whose readout moved (concise 14→13) |

Not determined: whether the space-dropping is a tokenizer/decoding artefact or a learned behaviour (it appears with the untrained adapter at low rate and grows fastest where the child re-emits its own text; no counterfactual available here); why creative_none's inbox has 11 turns but only 10 INBOX records; whether support_none's i=1063/1066 loop-break persists (2 responses old at pull).
