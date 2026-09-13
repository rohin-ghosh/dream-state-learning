# SEAL: primary-source claim-boundary check

2026-09-13 | Bounded literature sidecar; no manuscript/science-code change or launch authority.
Primary text/code inspected with `web.run`; code was not executed. Gate definitions:
`research_notes/ASTRA_LAUNCH_PROMPT_2026-09-12.md` §§6–7. Implications below are analysis, not new acceptance criteria.

## Identity and source pins

- **Self-Adapting Language Models** — Adam Zweiger, Jyothish Pari, Han Guo, Ekin Akyürek, Yoon Kim, Pulkit Agrawal. [M]
- arXiv **2506.10943v1**, submitted **2025-06-12 17:48:13 UTC**; **v2**, revised **2025-09-18 16:17:30 UTC**. Metadata currently lists v2; no conference-status assertion. [M]
- [M] `https://arxiv.org/abs/2506.10943` — submission history/authors.
- [P1] `https://arxiv.org/html/2506.10943v1` — original methods/results checked.
- [P2] `https://arxiv.org/html/2506.10943v2` — §§3.1–3.2, 4.1–4.2, 5; Appendices A, B.1–B.4/B.6/B.10.
- [R] Authors' linked repository: `https://github.com/Continual-Intelligence/SEAL`.
- Verified code pin **6d9c9f9ee392c6cc618e771f399d436d190f6ca4**: `https://github.com/Continual-Intelligence/SEAL/commit/6d9c9f9ee392c6cc618e771f399d436d190f6ca4` (commit date not independently verified).
- [C] Pinned continual driver: `https://github.com/Continual-Intelligence/SEAL/blob/6d9c9f9ee392c6cc618e771f399d436d190f6ca4/general-knowledge/src/continual/continual_self_edits.py`.
- [U] Pinned helpers: `https://raw.githubusercontent.com/Continual-Intelligence/SEAL/6d9c9f9ee392c6cc618e771f399d436d190f6ca4/general-knowledge/src/utils.py`.
- Other code below was read at `main` through web-cached primary pages; not independently byte-matched to that commit or bound to the published runs. Locators are repository-relative; use [R] + `/blob/main/` + path.

## What actually learns

**Two objectives, not merely a fixed generator feeding a task adapter.** Algorithm 1 separates inner adaptation from outer ReST-EM self-edit-policy training: “SFT on good self-edits.” [P2 §3.1]

- **Knowledge writer:** `general-knowledge/src/EM/build_SFT_dataset.py`, `_top_k`/`main`, ranks generated completions by `adapter_mean` (default top one), then saves prompt/completion pairs. `general-knowledge/src/EM/train_SFT.py`, `main`, LoRA-trains those pairs and merges/saves the writer checkpoint. Defaults: `Qwen/Qwen2.5-7B`, rank 64, alpha 128, attention/MLP projections. This is the base checkpoint, **not Qwen2.5-7B-Instruct**. [EM code]
- **Knowledge consumer:** `general-knowledge/src/inner/TTT_server.py`, `main`, trains a task LoRA, saves `final_adapter`, loads it into vLLM for QA, then unloads it. [U] `build_train_sequences` ordinarily includes generated text **plus original passage**; `format_answer_prompts` supplies the question, not passage or gold answer. Gold answers go to the GPT-4.1 grader. [TTT code; U]
- **ARC writer versus consumer:** `few-shot/BC-self-edit.py` selects successful configuration responses, masks prompt labels, LoRA-trains and merges/saves the generator. `few-shot/self-edit.py`, `main`, generates augmentation/training JSON using `model_name`, then initializes TTT from that same checkpoint with a separate rank-128 task LoRA. The documented writer LoRA is rank 16. [ARC code; `few-shot/README.md`]
- A self-edit is text/data or a tool configuration, **not directly predicted adapter tensors**. Training the consumer on facts is not the same objective as reinforcing the writer's successful edit decisions. [EM/TTT/ARC code]

## What the experiments support — and their bounds

| Evidence | Attributable result / boundary |
|---|---|
| Knowledge, §4.2/Table 2 | No-passage QA: 47.0% SEAL, 39.7% untrained self-edits, 33.5% passage-only. Parametric incorporation, not parenting. |
| ARC, §4.1/Table 1; A.1–A.3 | 72.5% versus 20% without RL; 11 training tasks, eight TTT-solvable held-out tasks × five edits. Not forty independent tasks. |
| Repeated updates, §5/Fig.6; B.6 | Eight sequential edits: forgetting, but “without complete collapse.” Not long-horizon consolidation. |
| Version distinction, §4.2 | v1 CPT: 43.8%/200 passages; v2 full-FT: 58.2%/200, 46.4%/2067. Batched CPT ≠ sequential learning. |
| Supervision, §5; B.10 | Main reward uses reference tasks; v2 also tests GPT-4.1 rubric reward (45.6%). Neither establishes autonomous reward discovery or parent removal. |

All table claims: [P1/P2, specified sections].

Version caution: v2 §4.2 explicitly says full-FT CPT, while B.3/Table 4 still lists LoRA hyperparameters. Do not silently reconcile this into an exact CPT recipe. The ARC README's command counts also differ from the paper; use the paper's stated denominator, not CLI examples. [P2; ARC README]

**Persistence/feedback connectivity is stronger than “only independent task edits.”** [C] `run_one_sequence` restarts services from `current_model_path`, generates the next edit from it, trains/evaluates, and `_merge_lora` saves the updated weights for the next step. Thus earlier task updates reach the subsequent writer. Scores are collected before that step's merge; the next iteration reloads the merged state. This is executable persistence/connectivity evidence, not my reproduction or a controlled demonstration that the writer improves. The driver deletes older/final merged directories and skips a missing merge; do not copy its artifact policy. [C]

`few-shot/eval-self-edits.py` separately initializes the checkpoint engine and attaches saved task adapters via `LoRARequest`; the README separates training and evaluation invocations. Reload paths exist. They do not by themselves certify our complete prompt/store purge, adapter-OFF causal test, or interrupted-optimizer resume assay. [ARC evaluation code/README; inference]

## Concrete G1–G5/P1 implications (analysis; preserve existing gates)

| Our distinction | Implementation/evaluation consequence |
|---|---|
| **G1 — write** | Save/hash adapter and base identity; reload in a fresh process with context/stores cleared; compare original checkpoint and no-write/adapter-OFF. A writer-training curve cannot substitute for the consumer's persistence assay. |
| **G2 — behavior** | Test held-out conditional use **and non-use** of learned material after reload. Separate factual recall, task-specific adaptation, and transferred learning-process behavior; do not infer one from another. |
| **G3 — repeated learning** | Track old/new task matrices, interference, stability, and interrupted/resumed continuity over a retained checkpoint lineage. Do not describe SEAL as lacking repeated updates; measure the stronger distinction we need. |
| **G4 — extraction utility** | Compare generated/selected material with raw/replayed/shuffled/no-update arms. Fix the consumer start state when comparing writers; separately budget generation, candidate search, grading, fit work, and persistent state. |
| **P1 — amortized parenting** | Require a developmental parenting treatment, matched non-parenting control, genuine parent-access removal, then held-out process decisions and downstream update utility. Offline RL supervision ending is not this causal intervention. |
| **G5 — integrated pilot** | Combine parent removal with subsequent adult experience→write→reload→adaptation measurements against the matched substrate control. Component results do not establish the integrated developmental effect. |

**Native-writer interpretation:** log separately (a) which parameters generate learning material, (b) which receive each update, and (c) which checkpoint generates the next material. Connectivity is necessary, not sufficient. Compare pre/post writers on the same held-out experiences using a fixed consumer and matched update budget; then assess prospective closed-loop adaptation/retention/cost without sealed-score feedback.

**Bottom line:** credit SEAL for learned self-edit generation and the verified repeated writer-feedback path; reserve “improving autonomous learning policy during adulthood” for a causal improvement assay, not mere parameter reachability or better task recall. The prior local related-work note's “same base” and per-task-only simplifications should not be carried into claims; that file remains untouched. No project result is promoted by this note.
