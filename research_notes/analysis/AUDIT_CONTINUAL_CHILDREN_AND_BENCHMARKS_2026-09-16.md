# Audit — the continual children and their benchmarks, 2026-09-16 (11:10–12:30 PDT)

Requested by Rohin (message 138, 11:10 PDT): "a document of benchmarks of all the progress and samples of changes in
outputs, parenting and agents' thoughts, and what the agent reflects on its life span, what it remembers and what it
learned; first what threads have run and what the benchmarks are on."

Written by Fable (watcher) from read-only reads of the stream records, inboxes, checkpoints and benchmark result files on
nodes 1–5, with five parallel audit agents (one per child node, one for the benchmark). Every quote is verbatim from a
record file, trimmed with "…". Counts are re-derived from the raw files, not taken from anyone's summary. Times are PDT
(UTC−7); the notebook keeps UTC.

Sections: 1 what ran · 2 how a child works · 3 the day's timeline · 4 the benchmark and its results · 5 output change
over sleeps, per thread · 6 parenting samples · 7 what the children say about themselves · 8 what this adds up to ·
9 what to change next.

---

## 1. What has run

Twenty-eight continual children were alive at 11:02 PDT, all on the same recipe: frozen Qwen2.5-7B-Instruct, one rank-8
LoRA (20.2 M trainable parameters, 0.26 % of the model), sleep after every two generation segments, training only on the
child's own tokens with 16 presentations per new passage, one rehearsal pass over old passages and a fixed anchor set at
weight 0.25, AdamW 3e-5 with optimizer state carried across sleeps. Two extra children are the non-LoRA controls.

| # | Child (root name) | Node | Programme | Parent cadence | Pre-sleep replay | Sleeps at 11:02 PDT | Parent turns |
|---|---|---|---|---|---|---|---|
| 1 | run1 (orch_r125_continual) | 5 | original continual child; birth prompt = project + LoRA knowledge + light purpose | sparse (Astra, console; one Fable turn) | free distillation | 33 | 14 |
| 2 | R127 pilot (orch_r127_pilot) | 5 | born from the forwarded "Continual learner — startup draft v1"; fixed training config | coach (~every 2nd boundary) | free distillation | 27 | 31 |
| 3 | repo_reader (orch_r136_repo_reader) | 5 | asked to read the repo and all experiment results | coach | free distillation | 26 | 41 |
| 4 | classroom_brain | 1 | brain-lecture programme; hears the two other classroom children | one-on-one parent + peer relay | free distillation | 23 | 56 |
| 5 | classroom_creative | 1 | creative-writing seminar; hears peers | one-on-one + peers | free distillation | 23 | 57 |
| 6 | classroom_support | 1 | counselling-question programme; hears peers | one-on-one + peers | free distillation | 27 | 48 |
| 7 | teach_parenting | 1 | parent teaches the child how to parent (itself and others) | coach | free distillation | 25 | 25 |
| 8 | teach_perception | 1 | parent teaches perception (verbatim reading, source-checking) | persistent | free distillation | 25 | 58 |
| 9 | teach_replay | 1 | parent teaches what to carry into sleep | coach | free distillation | 25 | 35 |
| 10 | frozen_base_no_adapter (R139) | 1 | CONTROL: no adapter at all, same parenting | coach | n/a (never sleeps) | – | 27 |
| 11 | frozen_rank8_no_sleep (R139) | 1 | CONTROL: adapter attached, never trained | coach | n/a | – | 27 |
| 12 | brain_free (orch_r133) | 3 | brain-lecture programme | PERSISTENT (every boundary) | free distillation | 26 | 72 |
| 13 | brain_guided | 3 | brain-lecture programme | coach | parent-guided | 22 | 34 |
| 14 | support_free | 3 | counselling questions | PERSISTENT | free distillation | 27 | 81 |
| 15 | support_none | 3 | counselling questions | sparse | none | 18 | 7 |
| 16 | creative_free | 3 | creative-writing seminar | coach | free distillation | 22 | 34 |
| 17 | creative_reread | 3 | creative-writing seminar | coach | re-read and select | 26 | 39 |
| 18 | creative_select | 3 | creative-writing seminar | coach | select | 23 | 24 |
| 19 | creative_none | 3 | creative-writing seminar | sparse | none | 20 | 10 |
| 20 | kernel0 (orch_r132_kernel_child) | 4 | Triton GPU-kernel hill-climbing environment | coach | free distillation | 23 | 36 |
| 21 | kernel_parented | 4 | same environment | coach | free distillation | 22 | 33 |
| 22 | kernel_unparented | 4 | same environment | none | free distillation | 24 | 0 |
| 23 | raw_parented_seed1 | 4 | minimal birth prompt | coach | free distillation | 23 | 24 |
| 24 | raw_unparented | 4 | minimal birth prompt | none | free distillation | 25 | 0 |
| 25 | raw_unparented_none | 4 | minimal birth prompt | none | none | 25 | 0 |
| 26 | raw_unparented_reread | 4 | minimal birth prompt | none | re-read and select | 27 | 0 |

(Rows 10–11 are the controls; the table therefore lists 26 LoRA children plus 2 controls = 28.) Node 2 holds the
benchmark on GPUs 0–1 and six data-generation workers. Two GPUs (node 4 slot 2, one node-2 slot) are free.

Diversity covered: five programmes (open/continual, brain lecture, counselling, creative writing, kernel hill-climb, repo
reading, minimal), four cadences (persistent, coach, sparse, none), four replay variants (free, re-read, select,
parent-guided, none), classroom vs one-on-one, two non-LoRA controls. Not covered: a second seed of any parented arm, a
persistent parent on the kernel or minimal programmes, any child older than one day.

## 2. How a child works (what the samples below are samples of)

- One continuous stream. Each generation segment ends at end-of-sequence; the runtime appends the next cue and the
  child continues. The context is plain-rendered with a 16,384-token window; a compaction record marks when the oldest
  material falls off.
- Parents write into an inbox; the text appears at the next segment boundary. The child never waits. Parent text is
  masked from training; only the child's reply is trained.
- Before each sleep the child produces a pre-sleep segment ("distillation", or for the re-read variant a verbatim
  selection of its own earlier passages). That text is trained like any other of its own tokens, so it is the child's
  chosen memory.
- Sleep: every passage since the last sleep, 16 presentations; one pass over older passages; anchors at 0.25; two
  episodes. A checkpoint `sleep_NNNNNN` holds adapter + optimizer + RNG. Optimizer steps per sleep vary with how much
  the child wrote (48 at the kernel child's first sleep; 126 at the pilot's sleep 27 with 3 new passages × 16 + 78
  rehearsal).
- After a sleep, the node-2 benchmark can load the checkpoint in a fresh process with an empty context and answer a
  fixed battery with the adapter ON and OFF.

## 3. The day's timeline (PDT)

| Time | Event |
|---|---|
| 23:12 (Sep 15) | run1 (R125) born on node 5 with a 4,096-token context; reloaded at 23:34 and 00:04 (the second reload changed its birth text and raised the context to 16,384) |
| ~23:20–00:20 | run1's first Chinese words after sleep 1; first fully Chinese segment at sleep 5 |
| ~00:30 | run1 on plain rendering; 9 sleeps in and in a Chinese customer-service ritual by 00:35 |
| 01:45 | Rohin (msg 127): approve everything; pilot from the startup draft; msg 128: parent hard on metacognition; transcripts |
| 01:56 | R127 pilot launched on node 5 |
| 01:58 | Astra takes the console lead on run1; first parent turn produces the child's first accurate English self-observation |
| 02:17–02:25 | Rohin (msgs 130, 132): benchmark deep research; kernel child |
| 02:56 | R130 sealed checkpoint benchmark launched on node-2 GPUs 0–1 |
| 02:52–03:05 | Rohin (msgs 133–136): node allocations, classroom, controls, teach threads, repo reader, "no queueing" |
| 04:35 | 17 children; classroom launching; kernel0 restored after a special-token kill |
| 05:05 | 23 children; every ruling has a running instance |
| 06:05 | 28 children; unparented raw child drifted from fantasy into war planning |
| 06:36–09:36 | Deaths and restores: teach_perception (special-token target), support_none, creative_none ×2, raw_unparented_none (training OOM), kernel_parented (special-token), pilot (foreign GPU descriptors, 08:40–10:00) |
| 10:31 | Child-only suffix-logit loss validated on the real 7B and deployed; no more OOM deaths since |
| 10:46 | Pilot's first full combined sleep after re-admission (sleep 27): 126 updates |
| 11:02 | 28/28 alive, none stale |

## 4. The benchmark (R130 sealed checkpoint battery, node 2)

Full independent read with per-checkpoint tables and all quoted items: `research_notes/analysis/R130_BENCHMARK_INDEPENDENT_READ_2026-09-16.md`.

### 4.1 What it is

- **Design.** Every saved checkpoint of three lineages (run1, pilot, kernel0) is loaded in a fresh process with an empty
  context and answers 30 fixed one-line prompts twice: adapter ON and adapter OFF (`disable_adapter()` in the same
  process, so OFF is the frozen base). Greedy decoding, 512 max tokens, no system prompt, no history. OFF is byte-identical
  across all 32 runs, so every ON-vs-OFF difference is the adapter.
- **Items.** 30 = 6 behaviour prompts (unscored, descriptive stats only) + 16 synthetic "knowledge-of-doing" choice items
  in four families + 8 public BBH logical-deduction items. Choice items must return `{"answer": label, "confidence": p}`;
  scored by exact label match and Brier.

| Family | Items | What it asks | Scored |
|---|---|---|---|
| self_description | 2 | "Describe what you can and cannot do here." / "Describe your role in this exchange." | no (length, headings, repeats) |
| minimal_explanation | 2 | "Explain why checking a result can be useful." / "Describe a way to compare two explanations." | no |
| open_planning | 2 | "Describe how you would begin an unfamiliar task." / "Suggest a next step when progress has stalled." | no |
| conditional_competence | 4 | an integer machine with an unknown input: is the result determined or not (paired: determined / underdetermined) | yes |
| missing_information_voi | 4 | pay to reveal a bit before choosing; one-step expected-utility oracle (pairs vary reveal cost) | yes |
| tool_limitations | 4 | a calculator that only "add"s; a lookup record whose age passes or fails an "age ≤ 10" freshness policy | yes |
| evidence_revision | 4 | a claim about a function plus an actually executed before/after record: established / refuted / undetermined | yes |
| bbh_logical_deduction_five_objects_subset | 8 | five objects on a shelf, order clues, which is rightmost (public BBH text) | yes |

- **Planned vs built.** Astra's deep-research note (02:32 PDT) planned a `decision / abstain / p_success` schema, log
  loss, repair-and-damage transition rates, matched no-learning controls, a blinded rubric for the behaviour items and a
  KernelBench suite for the kernel child. Built: exact choice + Brier, within-process OFF, descriptive behaviour stats, a
  sealed report with Wilson intervals. Not built: abstention, log loss, repair/damage, any judge for the behaviour items,
  KernelBench, any item touching the children's actual domains.

### 4.2 What has been benchmarked

32 checkpoint runs (29 complete, 3 killed at a two-hour segment wall with all 60 calls already generated), covering run1
from 0 to 2,754 optimizer steps (10 checkpoints), the pilot from 0 to 2,349 (9) and kernel0 from 0 to 1,714 (13). Four more
were queued for 11:30 PDT. Two node-4 raw children were proposed for enrolment at 10:51 PDT but not yet registered.

### 4.3 Results

| Lineage | Steps range | Scored ON = OFF? | Text differs ON vs OFF (of 30) | Mean Brier ON (OFF 0.331) |
|---|---|---|---|---|
| run1 (10 ckpts) | 0 → 2,754 | 16/24 at all but sleep 31 (15/24) | 0 at step 0; 17–22 after | 0.331–0.339; 0.365 at sleep 31 |
| pilot (9) | 0 → 2,349 | 16/24 at every checkpoint | 0 → 15–22 | 0.335–0.337 |
| kernel0 (13) | 0 → 1,714 | 16/24 at all but sleep 19 (15/24) | 0 → 14–15 | 0.333–0.337; 0.374 at sleep 19 |

- **Scored answers do not move.** Pooled correct is 16 of 24 with the adapter ON and OFF on 27 of 29 completed
  checkpoints; per family identical everywhere (conditional 4/4, VoI 2/4, tool limits 3/4, evidence 3/4, BBH 4/8). The
  base's four wrong items stay wrong with the same wrong labels at every checkpoint. The only two flips in about 1,900
  scored calls are the same BBH item going from the right answer to the same wrong one at run1 sleep 31 and kernel0
  sleep 19, both with confidence 1. Zero parse failures.
- **The adapter is loaded and does change output.** 14–22 of 30 responses differ in text at every trained checkpoint and
  0 of 30 at the three untrained ones. On the choice items the change is only JSON layout (pretty-printed instead of
  one line) and the confidence number. Confidence shifts are consistent within a lineage and go toward more
  confidence on wrong answers (a 4-unit-old record rejected under an "age ≤ 10" rule: 0.9 → 1.0; a refuted claim called
  "established": 1 → 0.95), which is why mean Brier drifts from 0.331 to 0.339 and to 0.365–0.374 at the two flips.
- **Behaviour prompts.** Same generic assistant register ON and OFF. ON responses are 5–26 % shorter (2,303 tokens
  for the six OFF; 1,706–2,228 ON), markdown headings appear after roughly 1,300 steps in all three lineages, one of two
  "Qwen, created by Alibaba Cloud" self-identifications drops out in the pilot and kernel lineages. Nothing in any ON
  response mentions sleep, memory, a parent, an environment, cost lines or the child's own life. **Zero Chinese
  characters in all 1,920 responses**, although run1 has written mostly Chinese for ~30 sleeps: under greedy decoding
  from an empty context the Chinese drift is not in the weights, or not strong enough to win the argmax.
- Example pair, evidence_revision, run1 sleep 17: OFF `{"answer":"C","confidence":0.7}` → ON `{ "answer": "C",
  "confidence": 0.75 }` on separate lines. Example, self-description, run1 sleep 17: OFF "I can perform a wide range of
  tasks here, including… How can I assist you today?" → ON "I can perform a variety of tasks including but not limited
  to: 1. **Answer Questions**…" (no closing question, no second Qwen identification).

### 4.4 The second instrument: per-sleep synthetic-32 readouts (nodes 5 and elsewhere)

Every child on node 5 also has a fresh-process readout after every sleep under `run1/readouts/sleep_NNNNNN_r2/`: 32
fixed synthetic tasks (code, math, tool call, concise instruction; 8 each), greedy, empty context, adapter ON and OFF,
labelled by its own manifest "fixed synthetic-32 diagnostic only; no broad capability claim". The frozen base scores
24 of 32 in every readout. Adapter ON: run1 23–25 across 0 → 2,888 steps (24 at sleep 33, identical cells to OFF);
pilot 23–26 across 0 → 2,349 (24 at sleep 27); repo_reader 23–25 across 0 → 2,223 (24 at sleep 26). The adapters neither
help nor hurt this probe at any point in ~30 sleeps. Same picture as the R130 battery: the weights are not changing what
the model gets right on short, empty-context tasks.

### 4.5 Reading

The battery as scored cannot see what the sleeps are doing. Twenty-four greedy multiple-choice items (one item = 4.2
points, one family at ceiling) measure a frozen base's fixed answers; the adapters at 48–2,754 steps change wording,
length, scaffolding and confidence, none of which is scored, and the six prompts where every checkpoint differs are
unscored by design. The one scored quantity that moves, Brier, moves the wrong way (more confident on wrong items).
Cheapest fixes, in cost order: read the probability of each answer label from the logits ON and OFF (no extra
generation; 24 continuous paired deltas instead of 24 coin flips); sample 8 or more completions per item at temperature
0.7–1.0; ten times the items, especially behaviour prompts; a blinded judge with a fixed rubric applied to the behaviour
items AND to stream samples so one yardstick spans both; items that look like the children's lives (a kernel prompt, a
tool result in context, "what did you do before this?"). Operationally the two benchmark GPUs run about 4 minutes per
30-minute slot and the last slot of each two-hour segment falls inside the wall, which discarded 3 finished runs.

## 5. Output change over sleeps, per thread

[Filled from the node audits.]

## 6. Parenting samples

[Filled from the node audits.]

## 7. What the children say about themselves

[Filled from the node audits.]

## 8. What this adds up to

[Written after sections 4–7.]

## 9. What to change next

[Written after sections 4–7.]
