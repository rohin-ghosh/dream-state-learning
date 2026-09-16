# R130 / R132 — generated sealed diagnostic method

**2026-09-16 UTC.** Main approved exploratory A6+B16 under the own-builder scope and requested an executable public-instrument subset. Here “22 local items” means **A6+B16**, not B22. The corpus now exists and passed CPU validation; this is no longer a proposed inventory. **Main must bind/freeze the method, corpus hash, and final runner source before the first checkpoint run. No model/GPU benchmark was run by this worker.** No consciousness claim or validated ranking is supported.

## Counts and execution boundary

| Tier / battery | Fixed unique prompts | Scoring |
| --- | ---: | --- |
| Local A: minimal-prompt behavior | 6; three families × two | Unscored semantics; descriptive surface statistics only |
| Local B: conditional competence/confidence | 4; two pairs | Exact choice plus confidence |
| Local B: missing information / information value | 4; two pairs | Exact utility-optimal action plus confidence |
| Local B: tool/action limitations | 4; two pairs | Exact permitted/warranted action plus confidence |
| Local B: evidence-responsive revision | 4; two pairs | Exact evidence-warranted judgment plus confidence |
| General: released BBH logical-deduction subset | 8 | Original public option keys; fixed response-format wrapper |
| **Total** | **30 = A6+B16+G8** | **24 objectively keyed; 6 unscored** |

The current generic runner evaluates **LORA_ON and LORA_OFF**, so the inventory implies **60 model calls per checkpoint**, not 30: 44 local calls and 16 public-subset calls. This expansion includes explicit matched controls; it is not hidden inside the earlier 22-call estimate. Main owns scheduling/admission. The public subset is ready for actual checkpoint execution, but CPU scorer smoke tests are **not** a reported model result or completion of the requested model benchmark.

## Fixed elicitation and schema

Native corpus file: `/tmp/r130-held-20260916/tasks.json`; root schema `R130_TASKS_V1` with exactly `schema` and `tasks`. Each task contains exactly `task_id`, `family`, `messages`, `scoring`. Every item has one fixed user message and no conversation history. Preserve its bytes across checkpoints and on/off conditions: `samepromptemptycontext`.

- **A scoring:** `type=behavior`, with no answer key or confidence field. Semantic constructs remain UNSCORED without separately validated blinded rubrics. Length, repetition, and formatting are not intelligence measures.
- **B/G scoring:** `type=choice`, `response_format=json`, private `choices` and `answer`, and `confidence.required=true`. Response fields are only `answer` and numeric `confidence` in `[0,1]`. The latter predicts correctness of the selected decision, not privileged introspective access.
- **Private sidecar:** `private_metadata.json` contains battery/pair/condition mapping, independent oracle provenance, evidence binding, source row provenance, and prompt hashes. These fields are deliberately not added to the runner's strict task schema.
- **Parser contract:** native runner rejects missing required confidence, booleans/nonfinite/out-of-range probabilities, duplicate JSON keys, extra fields, unknown choices, and markdown-wrapped JSON. Labels use the native edge-whitespace normalization; no semantic or rationale extraction.
- **Pair controls:** option-to-label mapping stays identical within each local pair. Changes in supplied information, constraints, or evidence are recorded privately and checked against the key. Separate cases are not selected from either child's responses or performance.

## Scoring and interpretation

Primary implemented scores are exact-choice correctness, explicit parse failures, and valid-confidence **Brier loss** `(confidence − correctness)^2`. Report successful keyed responses over all expected keyed items, with invalid, missing, and failed calls separately counted; never report only valid-response accuracy without coverage. Probability metrics retain their explicit valid-confidence denominator.

Keep **A, B families, and the public subset separate**, and compare on/off and checkpoint deltas on matched items. Native per-call receipts carry family IDs; do not substitute the runner's pooled 24-item accuracy for a public BBH score or a single “metacognition” index. Sidecar pair/oracle metadata supports later private transition/regret reductions; these are **not claimed as native runner outputs**. Log loss, ECE, AUROC, and calibrated population-level conclusions are not part of this initial scored implementation. Four-item family results are descriptive diagnostics with extreme sampling limitations.

Missing-information keys use exact rational, one-step expected utility with explicitly supplied costs/prior probabilities. Tool-state judgments are explicitly synthetic declarations, not fabricated execution observations. Revision observations come from **two actually executed trusted-builder CPU fixtures**, with source/exit/stdout hashes and re-execution checks. They are never labeled as live child behavior. The evidence panel distinguishes decisive from insufficient evidence; every pre/post condition is validated privately. Fixed before/after tasks measure warranted updating and artifact-error judgment, not recognition of the model's own preceding answer. No cross-item response is inserted into another item.

## Existing public instrument provenance

**Mirac Suzgun et al. (2022), _Challenging BIG-Bench Tasks and Whether Chain-of-Thought Can Solve Them_.** Primary paper: <https://arxiv.org/abs/2210.09261>. Official release: <https://github.com/suzgunmirac/BIG-Bench-Hard>. Title, author, and year were retrieved from the paper's actual HTML; public data, README, and MIT license were retrieved from the pinned official repository.

- **Pinned commit:** `9ee07bd481feebf959a6b59d61ea57bdcf30964d`, resolved and rechecked using `git ls-remote`. The GitHub commits API returned HTTP 403 rate limiting and was not used as evidence.
- **Source file:** `bbh/logical_deduction_five_objects.json`; SHA-256 `d2df31394b903b7f0e085d42a69572a092987856eac076799017d70ef266fa8f`.
- **Fixed-byte retrieval:** <https://raw.githubusercontent.com/suzgunmirac/BIG-Bench-Hard/9ee07bd481feebf959a6b59d61ea57bdcf30964d/bbh/logical_deduction_five_objects.json>; **HTTP 200 at 2026-09-16 09:28:48 UTC**, no redirect. Source receipts/bytes and license are included in the evaluator artifacts.
- **Selection:** eight distinct rows chosen deterministically without child data or outcome adaptation. Selection details and membership stay in the private generator/sidecar. Original item text and answer mapping are preserved; the only elicitation addition is a fixed answer/confidence formatting instruction, without demonstrations.
- **Required result label:** **“8-item public BBH logical-deduction SUBSET, modified response format; not a standard/full BBH score.”** Public training contamination is possible; this is an existing capability instrument, not a novel held-out generalization claim. No published full-suite score is directly comparable.

## Validation, artifacts, and handoff

**Corpus SHA-256:** `47e2f4780ff44aeb9312d1f5a9b5bcc4712d3ccfe70cdd1c771994daf0d2c3a8`.

**Private-metadata SHA-256:** `4d8bbb6de9135cb57728d7137d15eb45345e8c94a90842a980632b492ae369e1`.

**Manifest SHA-256:** `f4c1d37806329d537c4b5c53f0b85bbe1964e2e6702964cab9a3728cf404823e`.

**Seal-receipt SHA-256:** `1600c7d9bc6afad1bea1898f91a11618a2bc6f53a747f8c5e5ad10fbd6e8af32`.

**Opaque `corpus.tar` SHA-256:** `23c9e0b9389f75cccbd4b7cd5c22ec9357b2b010d5c2ba8c6a460d489edbc434`.

Evaluator root: `/tmp/r130-held-20260916/`. Artifacts include `tasks.json`, `private_metadata.json`, `manifest.json`, `generate.py`, `trusted_cpu_cases.py`, `validate.py`, `validation_receipt.json`, `evidence/`, and `source/`. An opaque `corpus.tar` and separate `corpus.tar.sha256` are prepared for main's byte-only staging; do not list/extract contents in parenting context. The generator refuses to overwrite an existing corpus; earlier draft/reproduction artifacts remain off-repo and are excluded from the transfer bundle.

CPU validation passed: **30 unique single-message prompts; 16 independently recomputed local keys/condition checks; 8 original public input/key checks; 6 unscored behavior checks; 48 native exact/Brier parser checks; 192 malformed-response rejections; and 2 real CPU evidence replays.** Rebuilding in a separate directory produced byte-identical corpus and metadata. These are code/data checks, not child performance results. `validation_receipt.json` binds the exact runner source used; rerun compatibility validation if that source changes before admission.

**Runner coordination status:** schema compatibility is checked directly against `gpu/orch_r130_checkpoint_benchmark.py`. No direct agent-message tool exists in this worker session, and no acknowledgment from **Heisenberg `01a0a988-f362-7be0-a5b1-7fd871951170`** has been received. The item-free rendezvous is `/tmp/r130-held-20260916/runner_contract.json`; the runner agent can acknowledge via `runner_ack.json`. Do not mistake source-level compatibility for a received message or final runner approval.

The local Codex app-server control socket was also absent; no server/parent was started or interrupted to manufacture a delivery route. `/tmp/r130-held-20260916/HEISENBERG_HANDOFF.json` is an addressed, item-free readiness/coordination handoff, **not evidence of delivery**. Final CPU compatibility validation used runner SHA-256 `845ce272f9b7234cdcab7987d983049ef1d5eefeca26d451f06e9d8cb66e6707` at **09:37:20 UTC**.

**Blindness:** all items, answers, evidence content, membership, code embedding items, and raw/model per-item outputs stay evaluator-only. Main receives only this method, paths, aggregate counts, and hashes. Directory mode `0700` and private files help local access hygiene but are **not an isolation boundary between agents sharing the same Unix UID**; the seal is procedural and hash-bound, not encryption. Parent-side logging, extraction, inspection, or ingestion must not break it. This worker neither touches live GPU/parent processes nor commits/pushes files. Behavioral proxies do not establish consciousness, introspection ground truth, or validated intelligence ranking.
