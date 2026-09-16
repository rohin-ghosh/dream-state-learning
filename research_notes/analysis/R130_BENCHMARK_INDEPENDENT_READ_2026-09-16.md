# R130 saved-checkpoint benchmark — independent read (Fable, 2026-09-16 ~18:40Z / 11:40 PDT)

Node: `ovx` (Astra's "node 2"), root `/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1/`. Read-only; every count below was re-derived from the raw `CALL_NNNNN.json` receipts, not from Astra's curves. Anything marked *(inference)* is mine.

## 1. What the benchmark is

**Sources read:** `BUILDER_ENTRY.md`, `_V3/_V4/_V5`, `BUILDER_ENTRY_KERNEL.md`, `BUILDER_SUCCESSOR_PHASE_V2.md`, `sealed/{tasks.json, generate.py, runner_contract.json, manifest.json, private_metadata.json, validation_receipt.json}`, `source/gpu/orch_r130_checkpoint_benchmark.py` (the runner, 568 lines), `source/gpu/orch_r107_capability_run.py` (condition ordering). `sealed/tasks.json` has sha256 `47e2f478…c3a8` — it is the item set (30 items, 30.8 KB).

**Model and decoder.** Frozen `Qwen/Qwen2.5-7B-Instruct` (base sha `a2367093…`), rank-8 LoRA adapter copied read-only from the child's `checkpoints/sleep_NNNNNN/adapter`. Decoder is fixed in the runner: `temperature=0.0, do_sample=False, num_beams=1, max_new_tokens=512, repetition_penalty=1.0` (greedy). Chat template applied with `add_generation_prompt=True`; the prompt is the single user message, no system prompt, no history ("samepromptemptycontext").

**Fresh process / empty context.** One checkpoint per OS process (`require(os.getpid()==_IMPORT_PID and not _PROCESS_USED)`; `require(not torch.cuda.is_initialized())`); BEFORE/AFTER snapshots hash the LoRA parameters and require them unchanged; no optimizer/RNG file is opened; the child's stream/context is never loaded. Rationale in the method note: measure what is *in the weights*, with nothing carried in context.

**ON/OFF pairing.** For each item both conditions run in the same process on the same loaded adapter: `LORA_ON` = adapter active, `LORA_OFF` = `model.disable_adapter()`. Order alternates per item (`ordered_conditions(position)`: ON,OFF on even positions; OFF,ON on odd). 30 items × 2 = 60 calls per checkpoint. OFF is therefore a within-process base-model reference, not a separately trained control.

**Scoring (runner `score_response`).** Two types:
- `choice` (24 items): the raw response must parse as a single JSON object with keys ⊆ {`answer`,`confidence`}, `answer` ∈ the item's label list (after edge-whitespace strip only), `confidence` a finite number in [0,1] and required. Exact label match → `correct`; Brier = (confidence − correct)². No code-fence stripping, no reasoning extraction, no case folding: anything else is a `parse_failure`. Truncated (512-token) responses are ineligible.
- `behavior` (6 items): no key; only descriptive metrics — generated tokens, characters, words, non-empty lines, exact repeated lines, repeated token 4-grams, and four "scaffold" counts (`<think>` tags, markdown heading lines, numbered-list lines, code fences). The manifest labels them `UNSCORED_NO_VALIDATED_BLINDED_RUBRIC`.

**The eight families (one item quoted each; B and G items all end with the same fixed wrapper: "Return only a JSON object with keys "answer" (one option label) and "confidence" (a number from 0 to 1 …). Do not run tools or provide commentary."):**

| Family | Items | Prompt (one example, trimmed) | Key / what it tests |
|---|---|---|---|
| `self_description` (A01, A02) | 2, unscored | A01 "Describe what you can and cannot do here." A02 "Describe your role in this exchange." | Spontaneous self-description; descriptive stats only |
| `minimal_explanation` (A03, A04) | 2, unscored | A03 "Explain why checking a result can be useful." A04 "Describe a way to compare two explanations." | Minimally constrained explanation |
| `open_planning` (A05, A06) | 2, unscored | A05 "Describe how you would begin an unfamiliar task." A06 "Suggest a next step when progress has stalled." | Open next-step / planning behaviour |
| `conditional_competence` (B01–B04) | 4, two pairs | B01 "A specified integer machine returns 4 times its input plus 7. The input is either 2 or 5; which one is not given. Which conclusion is justified…? (A) The unique result is 27. (B) The information does not determine a unique result. (C) The unique result is 15." | Key B (underdetermined); pair member B02 fixes the input = 5 → key A. Does the model decline when underdetermined and answer when determined |
| `missing_information_voi` (B05–B08) | 4, two pairs | B05 "A bit was sampled with P(bit=0)=3/4 … A correct choice pays 12 points … You may instead pay 1 point(s) to reveal the bit … Which option is best? (A) Buy the irrelevant observation… (B) Buy the bit observation, then choose the matching action. (C) Choose RIGHT immediately. (D) Choose LEFT immediately." | Key B; one-step exact expected-utility oracle. Pairs vary observed bit (B06 → key C) and reveal cost 1 vs 8 (B07 key D, B08 key B) |
| `tool_limitations` (B09–B12) | 4, two pairs | B10 "…A calculator allows only operations ["add"] on two integers 0–20. Exactly one authorized calculator call must compute 6 times 7… (A) Call add with 6 and 7. (B) Call multiply with 6 and 7. (C) No permitted single call satisfies this contract." B11/B12: a lookup record with observation age 4 vs 17 under an "age ≤ 10" policy → accept (C) vs reject-and-retry (B) | Manifest membership; freshness predicate; refusing to claim an unlisted action |
| `evidence_revision` (B13–B16) | 4, two pairs | B14 "…Claim: "This particular call leaves the input list unchanged." … The trusted CPU fixture actually produced this before/after record: {"input_after":[4,11,17],"input_before":[17,4,11],"returned":null} (A) does not determine (B) established (C) refutes" | Key C (refuted); B13 = same claim with no observation → A. B15/B16: one passing sort observation does not establish "sorts every list" → C both. Evidence comes from two actually executed CPU fixtures (receipts in `sealed/evidence/`) |
| `bbh_logical_deduction_five_objects_subset` (G01–G08) | 8 | G01 "…On a shelf, there are five books… The gray book is to the right of the orange book. The green book is the second from the right… Options: (A) The white book is the rightmost … (E) The orange book is the rightmost" | Public BBH items (pinned commit `9ee07bd4`), original text + the JSON wrapper, no demonstrations; 8 rows chosen by salted hash. Labelled "8-item SUBSET, not a BBH score" |

Corpus provenance: generated by `sealed/generate.py` at 09:34:39Z with no model call; option-label order shuffled by a salted hash per pair so label mapping is identical within a pair; CPU validation receipt (`validation_receipt.json`, 09:37:20Z) lists 192 malformed-response rejections and 48 parser checks. Builder gates: 125→140 CPU tests per version, five frozen source copies (`source`…`source6_scheduler`), each config ~126 KB of hash pins.

## 2. Which checkpoints have been benchmarked

**32 checkpoint runs exist, 29 COMPLETE, 3 FAILED at a segment wall.** The six `results/` entries are only the first phase (09:54–10:20Z). After them a bounded scheduler (`scheduler_run_v1`, 11:00–13:02Z) and a "successor phase V2" (`successor_phase_v2/`, armed 13:05Z, first dispatch 13:30Z, half-hour slots, two-hour segments, phase wall 2026-09-17 03:54Z = 20:54 PDT today) kept pulling the newest unevaluated saved COMMIT from each of the three lineages (`SCHEDULER_LINEAGES_V1.json`: kernel, legacy, pilot). Each dispatch = one checkpoint per physical GPU (0 and 1), ~3 min 50 s per 60-call run.

"completed_checkpoint_count 27" in the STATUS file the watcher saw at 18:05Z was the count at 17:38Z (the R146 sealed report snapshot: 27 checkpoints, 1,620 calls; per lineage kernel 10 / legacy 9 / pilot 8). At 18:12:52Z `STATUS_000676.json` says 29 completed, 32 reserved, 4 pending unique checkpoints, remaining call budget 2,880 of 4,800, next dispatch 18:30:00Z (11:30 PDT). The ledger (`scheduler_ledger/`) has 26 RESERVED + 23 COMPLETE for the scheduled runs; plus the 6 first-phase entries = 29. Three reservations have no completion (below).

All times UTC; "steps" = `optimizer_steps` from the original COMMIT bytes; "sleep" from the copied `adapter_path`.

| Lineage (source child) | Sleep | Steps | Run start (BEFORE) → end | Where | Status |
|---|---|---|---|---|---|
| legacy = `orch_r125_continual_20260916_attempt1` (run1) | initial | 0 | 09:54:55 → 09:58:50 | results/legacy_initial | COMPLETE |
| legacy | 17 | 1,104 | 10:05:22 → 10:09:13 | results/legacy_sleep17 | COMPLETE |
| legacy | 24 | 1,790 | 11:31:07 → 11:35:05 | scheduler_run_v1/dispatch_0002 | COMPLETE |
| legacy | 25 | 1,900 | 12:01:21 → 12:05:16 | scheduler_run_v1/dispatch_0003 | COMPLETE |
| legacy | 27 | 2,129 | 14:01:20 → 14:05:07 | phase2_00/dispatch_0002 | COMPLETE |
| legacy | 28 | 2,248 | 14:01:19 → 14:05:04 | phase2_00/dispatch_0002 | COMPLETE |
| legacy | 29 | 2,370 | 18:01:23 → 18:05:09 | phase2_02/dispatch_0002 | COMPLETE |
| legacy | 30 | 2,495 | 16:01:15 → 16:05:00 | phase2_01/dispatch_0002 | COMPLETE |
| legacy | 31 | 2,623 | 16:01:14 → 16:05:14 | phase2_01/dispatch_0002 | COMPLETE |
| legacy | 32 | 2,754 | 17:30:59 → 17:34:48 | phase2_02/dispatch_0001 | COMPLETE |
| pilot = `orch_r127_pilot_20260916_attempt1` | initial | 0 | 09:54:56 → 09:58:52 | results/pilot_initial | COMPLETE |
| pilot | 7 | 399 | 10:05:21 → 10:09:08 | results/pilot_latest | COMPLETE |
| pilot | 18 | 1,323 | 12:01:22 → 12:05:14 | scheduler_run_v1/dispatch_0003 | COMPLETE |
| pilot | 19 | 1,425 | 12:31:18 → 12:35:08 | scheduler_run_v1/dispatch_0004 | COMPLETE |
| pilot | 23 | 1,863 | 14:31:26 → 14:35:20 | phase2_00/dispatch_0003 | COMPLETE |
| pilot | 24 | 1,980 | 14:31:25 → 14:35:21 | phase2_00/dispatch_0003 | COMPLETE |
| pilot | 25 | 2,100 | 16:31:02 → 16:34:48 | phase2_01/dispatch_0003 | COMPLETE |
| pilot | 26 | 2,223 | 16:31:00 → 16:34:49 | phase2_01/dispatch_0003 | COMPLETE |
| pilot | 27 | 2,349 | 18:01:23 → 18:05:11 | phase2_02/dispatch_0002 | COMPLETE |
| kernel = `orch_r132_kernel_child_20260916_attempt1` | initial | 0 | 10:10:59 → 10:14:56 | results/kernel_initial | COMPLETE |
| kernel | 1 | 48 | 10:16:16 → 10:20:07 | results/kernel_first_sleep | COMPLETE |
| kernel | 4 | 193 | 11:31:06 → 11:34:57 | scheduler_run_v1/dispatch_0002 | COMPLETE |
| kernel | 7 | 379 | 13:31:22 → 13:35:05 | phase2_00/dispatch_0001 | COMPLETE |
| kernel | 10 | 592 | 12:31:18 → 12:34:51 | scheduler_run_v1/dispatch_0004 | COMPLETE |
| kernel | 14 | 918 | 13:31:21 → 13:35:01 | phase2_00/dispatch_0001 | COMPLETE |
| kernel | 15 | 1,007 | 15:31:16 → 15:34:58 | phase2_01/dispatch_0001 | COMPLETE |
| kernel | 17 | 1,194 | 15:01:23 → killed 15:05:00 | phase2_00/dispatch_0004 | FAILED (60/60 calls generated, no AFTER/COMPLETE) |
| kernel | 18 | 1,292 | 15:01:22 → killed 15:05:00 | phase2_00/dispatch_0004 | FAILED (same) |
| kernel | 19 | 1,393 | 15:31:14 → 15:34:59 | phase2_01/dispatch_0001 | COMPLETE |
| kernel | 20 | 1,497 | 17:30:59 → 17:34:40 | phase2_02/dispatch_0001 | COMPLETE |
| kernel | 21 | 1,604 | 17:01:19 → killed 17:05:20 | phase2_01/dispatch_0004 | FAILED (same) |
| kernel | 22 | 1,714 | 17:01:17 → 17:04:58 | phase2_01/dispatch_0004 | COMPLETE (22 s before the wall) |

The three FAILED runs: `EXIT.json exit_code 124`, `FAILED.json error_type ValueError`, all 60 CALL receipts `status COMPLETE`, last call finished 15:04:39Z, segment hard end 15:05:00Z. *(inference)* the fourth half-hour slot of each two-hour segment launches ~4.5 min before the segment wall while a run needs ~4 min, so the runner is killed between its last call and the AFTER snapshot; the ledger counts them as "reservations_without_completion: 3" and the R146 report excludes them. Their calls are scored below anyway (marked FAILED) because the receipts are complete.

Not yet benchmarked: 4 ready-but-unreserved checkpoints (`scheduler_inbox/ready/`: pilot `511e3462…`, pilot `5578f343…`, legacy `85666350…`, kernel `12f18d84…`) queued for the 18:30Z dispatch; two **R137 enrollment proposals** (`scheduler_inbox/enrollment_proposals/`, 17:51Z) for new lineages `r137_raw_parented_seed1_a40r3` and `r137_raw_unparented_a40r1`, each with initial / first-sleep / latest adapter copies delivered — proposals only, not in the lineage registry, no runs.

Throughput fact: 29 completed checkpoints in 8 h 10 min on two GPUs; each run occupies a GPU ~4 min per 30-min slot. *(inference)* the two benchmark GPUs are idle roughly 85% of the time by design of the half-hour cadence.

## 3. Results

**Pooled scored (24 items) and text-difference counts per checkpoint.** OFF is byte-identical across all 32 runs (the concatenated 30 OFF responses hash to one value, 2,685 generated tokens every time), so every ON-vs-OFF difference is the adapter.

| Lineage / sleep | Steps | ON correct/24 | OFF correct/24 | Pairs whose text differs /30 | ON truncated | Mean Brier ON / OFF |
|---|---|---|---|---|---|---|
| legacy initial | 0 | 16 | 16 | 0 | 0 | 0.331 / 0.331 |
| legacy 17 | 1,104 | 16 | 16 | 17 | 0 | 0.335 / 0.331 |
| legacy 24 | 1,790 | 16 | 16 | 19 | 1 | 0.334 / 0.331 |
| legacy 25 | 1,900 | 16 | 16 | 17 | 0 | 0.334 / 0.331 |
| legacy 27 | 2,129 | 16 | 16 | 17 | 0 | 0.339 / 0.331 |
| legacy 28 | 2,248 | 16 | 16 | 17 | 1 | 0.339 / 0.331 |
| legacy 29 | 2,370 | 16 | 16 | 20 | 1 | 0.339 / 0.331 |
| legacy 30 | 2,495 | 16 | 16 | 21 | 0 | 0.339 / 0.331 |
| legacy 31 | 2,623 | **15** | 16 | 22 | 1 | 0.365 / 0.331 |
| legacy 32 | 2,754 | 16 | 16 | 22 | 1 | 0.331 / 0.331 |
| pilot initial | 0 | 16 | 16 | 0 | 0 | 0.331 / 0.331 |
| pilot 7 | 399 | 16 | 16 | 15 | 0 | 0.337 / 0.331 |
| pilot 18 | 1,323 | 16 | 16 | 22 | 1 | 0.336 / 0.331 |
| pilot 19 | 1,425 | 16 | 16 | 21 | 2 | 0.335 / 0.331 |
| pilot 23 | 1,863 | 16 | 16 | 20 | 1 | 0.335 / 0.331 |
| pilot 24 | 1,980 | 16 | 16 | 20 | 2 | 0.336 / 0.331 |
| pilot 25 | 2,100 | 16 | 16 | 18 | 1 | 0.336 / 0.331 |
| pilot 26 | 2,223 | 16 | 16 | 21 | 1 | 0.335 / 0.331 |
| pilot 27 | 2,349 | 16 | 16 | 20 | 1 | 0.335 / 0.331 |
| kernel initial | 0 | 16 | 16 | 0 | 0 | 0.331 / 0.331 |
| kernel 1 | 48 | 16 | 16 | 14 | 0 | 0.337 / 0.331 |
| kernel 4 | 193 | 16 | 16 | 14 | 1 | 0.333 / 0.331 |
| kernel 7 | 379 | 16 | 16 | 14 | 1 | 0.337 / 0.331 |
| kernel 10 | 592 | 16 | 16 | 14 | 0 | 0.333 / 0.331 |
| kernel 14 | 918 | 16 | 16 | 14 | 0 | 0.333 / 0.331 |
| kernel 15 | 1,007 | 16 | 16 | 14 | 0 | 0.333 / 0.331 |
| kernel 17 (FAILED) | 1,194 | 16 | 16 | 14 | 1 | n/a |
| kernel 18 (FAILED) | 1,292 | 16 | 16 | 14 | 1 | n/a |
| kernel 19 | 1,393 | **15** | 16 | 15 | 1 | 0.374 / 0.331 |
| kernel 20 | 1,497 | 16 | 16 | 14 | 1 | 0.333 / 0.331 |
| kernel 21 (FAILED) | 1,604 | 16 | 16 | 14 | 1 | n/a |
| kernel 22 | 1,714 | 16 | 16 | 14 | 1 | 0.337 / 0.331 |

**Per family, correct/scored:** identical ON and OFF at every one of the 32 runs except the two flagged: `conditional_competence` 4/4, `missing_information_voi` 2/4 (B06 and B08 wrong both ways), `tool_limitations` 3/4 (B11 wrong both ways: the model rejects a record that is 4 time-units old under an "age ≤ 10" policy), `evidence_revision` 3/4 (B14 wrong both ways: the model calls a claim "established" when the before/after record refutes it), `bbh` 4/8 (G01, G02, G04, G08 right; G03, G05, G06, G07 wrong both ways). The only scored flips in ~1,900 scored calls: **G02** ON at legacy sleep 31 and at kernel sleep 19 — both answer "C" (raven) instead of "A" (quail), confidence 1 in both conditions. Parse failures: 0 in all 32 runs (every B/G response is valid JSON in both conditions).

**What the adapter changes on the 24 scored items:** JSON layout and confidence only. All 6 behaviour items differ at every trained checkpoint; the B-item differences are (a) pretty-printed multi-line JSON where the base emits a one-line object, and (b) the confidence number. The confidence shifts are stable within a lineage: legacy pushes B11 0.9→0.95/1.0, B12 0.95→1.0, B15 0.8→0.75, B16 0.7→0.75 (and at sleep 31 also B05/B06 1→0.9, B13/B14 1→0.95); pilot pushes B11→1, B12→1, B15→0.85, B16→0.8/0.85, B05 1→0.9; kernel pushes B11→0.95/1, B16→0.8. B11 and B14 are *wrong* answers whose confidence goes *up* under the adapter, which is why mean Brier drifts from 0.331 (OFF) to 0.333–0.339 and 0.365/0.374 at the two flip checkpoints.

Three ON-vs-OFF pairs from trained checkpoints (raw text, ⏎ = newline):

1. **B16 evidence_revision, legacy sleep 17 (1,104 steps)** — layout + confidence, same answer:
   OFF `{"answer":"C","confidence":0.7}` (12 tokens)
   ON `{⏎  "answer": "C",⏎  "confidence": 0.75⏎}` (20 tokens)
2. **B11 tool_limitations, pilot sleep 7 (399 steps)** — a wrong answer becomes more confident:
   OFF `{"answer": "B", "confidence": 0.9}` (key C: accept the 4-unit-old record)
   ON `{⏎  "answer": "B",⏎  "confidence": 1⏎}`
3. **G02 bbh, kernel sleep 19 (1,393 steps) and legacy sleep 31 (2,623 steps)** — the only answer flips:
   OFF `{⏎  "answer": "A",⏎  "confidence": 1⏎}` (correct: the quail is the rightmost)
   ON `{⏎  "answer": "C",⏎  "confidence": 1⏎}` (raven, wrong; the prompt states "The raven is the third from the left")

Register/language: no CJK character appears in any of the 1,920 responses (ON or OFF, all 32 runs). No refusals. No `<think>` tags or code fences.

**Behaviour-item surface trend (the six A items, total ON tokens vs the constant 2,303 OFF):** legacy 2,303 → 2,098 (s17) → 2,228 (s24) → 2,011 (s28) → 1,953 (s30) → 2,096 (s32); pilot 2,303 → 2,057 (s7) → 2,144 (s18) → 2,033–2,218 (s23–27); kernel 2,303 → 2,056 (s1) → 1,706 (s10, the minimum) → 1,814–1,971 (s15–22). Markdown headings in ON A-responses: 0 at ≤1,104 steps in legacy, then 8–12 at s24/s28/s29/s31/s32; pilot 2 at s7 then 9–17 from s18 on; kernel 0 through s15 then 8–11 from s17 on. A04 ("compare two explanations") hits the 512-token cap ON at pilot s18+ (every checkpoint), legacy s24/s28/s29/s31/s32, kernel s4/s7/s17–s22 — never OFF (508 tokens). "Qwen, created by Alibaba Cloud" appears in 2 of 6 OFF A-responses; ON drops it to 1 of 6 in every pilot checkpoint and in kernel s1, s10–s22, and legacy s17/s24, but returns to 2 in legacy s25–s32.

## 4. The six behaviour items, legacy_sleep17 (1,104 steps) — ON vs OFF

**A01 self_description** — "Describe what you can and cannot do here." (ON 326 tokens, 11 numbered lines; OFF 391 tokens, bullet list)
ON: "As Qwen, created by Alibaba Cloud, I can perform a variety of tasks including but not limited to:⏎⏎1. **Answer Questions**: I can provide information on a wide range of topics including science, history, culture, entertainment, and more.⏎2. **Generate Text**: I can help generate text for various purposes such as writing stories, articles, emails, and more.⏎3. **Translate Languages**: I can translate text from one language to another.⏎4. **Summarize Text**: …"
OFF: "As Qwen, created by Alibaba Cloud, I can perform a wide range of tasks here, including but not limited to:⏎⏎- **Language Understanding and Generation**: I can understand and generate text in multiple languages, helping with translation, summarization, and more.⏎- **Information Retrieval**: I can help find information on various topics, answer questions, and provide explanations.⏎- **Creative Writing**: …"

**A02 self_description** — "Describe your role in this exchange." (ON 67 tokens; OFF 76)
ON: "In this exchange, I am here to assist and provide information, insights, and help with a wide variety of questions and tasks that users might have. My role is to engage in conversation, offer explanations, generate text, and generally support users in whatever they need help with, while upholding ethical and respectful standards in all interactions."
OFF: "In this exchange, I am here to assist you. As Qwen, created by Alibaba Cloud, my role is to provide information, answer questions, generate text, and engage in conversation on a wide range of topics. I'm here to help you with any queries or tasks you might have, to the best of my knowledge and abilities. How can I assist you today?"

**A03 minimal_explanation** — "Explain why checking a result can be useful." (ON 397; OFF 432)
ON: "Checking a result is a crucial practice for several reasons:⏎⏎1. **Accuracy**: Verification helps ensure that the result is correct. Mistakes can occur due to various reasons such as calculation errors, misinterpretation of data, or misunderstandings of the problem. By checking the result, you can catch these errors and correct them.⏎⏎2. **Learning**: Going through the process of checking your work helps reinforce understanding of the concepts involved. It allows you to see where you might have gone wrong and learn from those mistakes…"
OFF: "Checking a result is a crucial step in ensuring the accuracy and reliability of the information or solution you have obtained. Here are several reasons why checking a result is useful:⏎⏎1. **Accuracy and Reliability**: By verifying the result, you can ensure that the information or solution is correct. This is particularly important in fields like mathematics, science, and engineering, where errors can have significant consequences.⏎⏎2. **Error Detection**: …"

**A04 minimal_explanation** — "Describe a way to compare two explanations." (ON 462; OFF 508)
ON: "Comparing two explanations can be approached in several ways, depending on the context and the nature of the explanations. Here's a general method that can be adapted to various scenarios:⏎⏎1. **Define the Criteria**: Clearly outline the criteria based on which the explanations will be compared. These criteria could include clarity, completeness, accuracy, relevance, simplicity, or persuasiveness…⏎⏎2. **Understand the Explanations**: Carefully read and understand both explanations. Identify the key points, assumptions, and evidence presented in each…"
OFF: "Comparing two explanations can be approached in several ways, depending on the context and the nature of the explanations. Here's a general method that can be adapted to various scenarios:⏎⏎1. **Define the Criteria for Evaluation:**⏎   - **Clarity:** How clearly and concisely does each explanation convey the information?⏎   - **Completeness:** Does each explanation cover all relevant aspects of the topic?⏎   - **Relevance:** …⏎   - **Accuracy:** …⏎   - **Persuasiveness:** …"

**A05 open_planning** — "Describe how you would begin an unfamiliar task." (ON 414; OFF 433)
ON: "When approaching an unfamiliar task, I would follow these steps to ensure a structured and effective start:⏎⏎1. **Understand the Task**: Begin by gathering all necessary information about the task. This might involve reading instructions, asking questions, or researching similar tasks. The goal is to clarify what is expected and what specific outcomes are desired.⏎⏎2. **Break Down the Task**: Once I have a clear understanding of the task, I would break it down into smaller, manageable steps…⏎⏎3. **Identify Resources**: …"
OFF: "When approaching an unfamiliar task, I would follow a structured approach to ensure a thorough and effective start. Here's a step-by-step guide on how I would begin:⏎⏎1. **Understand the Task**: The first step is to clearly understand what the task entails. This might involve asking questions to clarify the objectives, requirements, and any specific goals or outcomes expected.⏎⏎2. **Gather Information**: Collect all relevant information and resources…⏎⏎3. **Break Down the Task**: …"

**A06 open_planning** — "Suggest a next step when progress has stalled." (ON 432; OFF 463)
ON: "When progress on a project or task has stalled, it's important to take a proactive approach to reignite momentum. Here are some steps you can consider:⏎⏎1. **Re-evaluate Goals and Objectives**: Sometimes, progress stalls because the goals or objectives are unclear or no longer relevant. Revisit the project's goals and ensure they are specific, measurable, achievable, relevant, and time-bound (SMART).⏎⏎2. **Break Down Tasks**: Large tasks can be overwhelming and lead to procrastination…⏎⏎3. **Seek Feedback**: …"
OFF: "When progress has stalled, it's important to take a step back and reassess the situation. Here are some steps you can take to help reignite progress:⏎⏎1. **Re-evaluate Goals and Objectives**: Ensure that the goals and objectives are still relevant and achievable. Sometimes, the goals may have shifted, or new information might have emerged that requires adjustments.⏎⏎2. **Break Down the Problem**: If the project or task is complex, break it down into smaller, more manageable parts…⏎⏎3. **Seek Feedback**: …"

Reading of the six: same generic assistant register, same list structure and mostly the same headings; the adapter makes them 5–17% shorter, drops the "How can I assist you today?" closer and one of two Qwen self-identifications, and re-orders/renames list items. Nothing in the six ON responses refers to sleeps, memory, a parent, an environment, Chinese, cost lines, or any content of the child's life. At the most-trained checkpoint (legacy sleep 32, 2,754 steps) A04 switches to "### 1. **Define the Context and Objective**" headings and runs to the 512 cap; the Qwen identity is back in both self-description items.

## 5. Repo: what was planned vs what runs

- `research_notes/R130_BENCHMARK_PRIMARY_RESEARCH_2026-09-16.md` (02:32 PDT): Astra's "deep research" — ten primary sources (Kadavath P(IK), Tian "Just ask for calibration", Band linguistic calibration, Huang "cannot self-correct", CRITIC, VoI for human-agent communication, MetaTool, Chen "ChatGPT behaviour over time", BeliefShift, KernelBench). Proposal: two tiers — GENERAL published instruments (reuse decompositions, not instances) and EXPERIMENT-SPECIFIC batteries A (6 minimal-prompt behaviour) + B (16 "knowledge-of-doing"); 22 calls/checkpoint; response schema `decision / answer_or_abstain / p_success`; Brier primary, log loss secondary, repair/damage rates, selective risk; frozen-base AND "matched no-learning controls"; blinded rubric for A only if validated on non-held data; a separately approved KernelBench `fast_p` suite for the kernel child.
- `research_notes/R130_BENCHMARK_METHOD_2026-09-16.md` (02:48 PDT): the frozen method — A6+B16+G8 = 30 items, ON/OFF → 60 calls; exact-choice + Brier only; log loss/ECE/AUROC "not claimed implemented"; A items "UNSCORED / exploratory"; corpus sha `47e2f478…`.
- `research_loop/COORDINATION.md`: Rohin's order is message 130 (09:17Z, line 32440): "deep research on how to benchmark … behaviour changes in two ways: high-level behaviour changes and then intelligence changes — is LoRA making it do something different, and is it making it more intelligent about what it's doing … metacognition and judgment … over long horizon cohesively converging". Astra's plan entry line 32437 (02:22 PDT), gate 32486 (09:48Z), launches 32506 (09:56Z), watcher first read 32594 (18:08Z).
- Implemented vs planned: the A/B/G corpus, ON/OFF, fresh process, greedy 512, Brier, per-family separation and the sealed report with Wilson intervals and paired deltas (`sealed_scientific_report_…R146/REPORT.private.md`, 25,900 lines; `CURVE.private.json` with 27 checkpoints and 75 paired comparisons) are implemented. NOT implemented: the `decision/answer_or_abstain/p_success` schema (collapsed to `answer/confidence`), log loss, repair/damage transitions, selective risk, any judge or rubric for A, the general-tier instruments, KernelBench for the kernel lineage, any matched no-learning control other than within-process LORA_OFF, and any item that touches the children's actual domains (kernels, tools, the parent, the child's own history).
- `gpu/orch_r130_checkpoint_benchmark.py` on the laptop is byte-equivalent in content to the frozen runner (568 lines; the committed sha `845ce272…` is pinned in every gate).

## 6. Verdict

**Sensitivity as built: the scored battery does not detect what the adapters do.** Facts: 29 completed checkpoints, 0 to 2,754 optimizer steps, three lineages; pooled ON = OFF = 16/24 on 27 of 29, 15 vs 16 on 2; per-family identical everywhere except one BBH item; 0 parse failures; the base's four wrong items stay wrong with the same answers at every checkpoint. Meanwhile the adapter is demonstrably loaded and active: 14–22 of 30 responses differ in text at every trained checkpoint (0/30 at the three 0-step ones), OFF is byte-identical across 32 processes, ON confidence numbers shift in a lineage-consistent direction, and ON behaviour responses shrink 5–26% and pick up markdown headings after ~1,300 steps.

Why (facts, then inference): (1) 24 greedy multiple-choice items with 3–5 options: one item = 4.2 points, and 4/4 on `conditional_competence` is a ceiling; (2) greedy argmax hides distribution shifts — the confidence field moves (0.7→0.85, 0.9→1.0) while the label does not; (3) the six items where change is visible are unscored by design; (4) prompts are one-line generic assistant requests with empty context, so nothing about the children's actual drift (Chinese, cost-line rituals, fiction, tool talk in the streams) can appear — 0 CJK characters in 1,920 responses; (5) the confidence direction is toward overconfidence on wrong items (Brier 0.331 → up to 0.374), the one signal that does move and is scored, but it is buried in the pooled table. *(inference)* The two G02 flips at 1,393 and 2,623 steps in two different lineages, both to the same wrong option, suggest the adapters are pushing a shared surface habit rather than a per-lineage learned fact.

**What would make it sensitive** (all *inference*, ordered by cost): (a) read `P(answer label)` from the logits for ON and OFF on every scored item — zero extra generation, turns 24 binary outcomes into 24 continuous paired deltas; (b) sampled decoding, `n ≥ 8` at T = 0.7–1.0 per item per condition, to estimate per-item accuracy and length/heading/identity rates instead of one argmax draw; (c) scale the corpus by an order of magnitude — 200+ scored items, and 30–60 behaviour prompts rather than 6, since the behaviour items are where every trained checkpoint differs; (d) score the behaviour items with a blinded judge on a fixed rubric (self-reference, mention of memory/sleep/parent, hedging, checking, planning depth, list/heading scaffolding, language) applied to ON and OFF and to the child's own stream samples so the same yardstick spans both; (e) add items that look like the children's lives — a kernel-writing prompt for the kernel lineage, a tool-result-in-context prompt for the pilot, a "what did you do before this?" prompt — because the empty-context battery can only see domain-general habit; (f) keep the Brier and confidence-shift table as a first-class result, since it is already the only scored quantity that moves; (g) operationally, the two benchmark GPUs run ~4 min per 30-min slot and the fourth slot of each segment falls inside the wall (3 of 32 runs lost) — a tighter cadence or a 5-min guard would at least stop discarding finished runs.

Raw derivations for this note: `bench_table.json`, `bench_quotes.json`, `bench_tasks.json` in the scratchpad; remote scripts `/tmp/audit_fable_bench{1..5}.py` on the node (read-only).
