# Static teacher-present/no-write comparison: independent offline review

Reviewed 2026-09-12 UTC. Scope: captured traces, endpoint semantics, prompt/source bindings, and observable returned-grid failures. No inference, remote access, GPU activity, repository edits, or changes to the original endpoint. Machine-readable checks, per-episode grids/violations, and input SHA256 inventory are in `/tmp/astra_static_competency_review_20260912.json`.

## Decision

**Preserve the primary null: process 1/16, sham 1/16, both solving only `rg/mini_sudoku/1850005`.** No concrete interface or trace-binding defect invalidates this comparison. The secondary format difference narrowly supports **one optional, prospectively fixed 16-question format follow-up**, not a solve-effect claim or posthoc rescue. Freeze its format endpoint and otherwise retain the same wrapper, dose, generation settings and paired comparison before observing results. No new threshold or significance claim is proposed.

Use `rg/mini_sudoku/1850016` through `1850031` only as the remaining questions unused in **this static comparison**. They are not globally untouched or novel: the earlier oracle training material included all32. Describe this as exploratory within-training-family format replication. Changing the wrapper or splitting the combined teacher package would instead be a different intervention, not a direct replication.

## Independently checked results

| Endpoint | Process | Sham |
|---|---:|---:|
| First ACT solved /16 | 1 | 1 |
| Complete strict four-row numeric ACT /16 | 7 | 4 |
| Format-masked native first-score mean | 0.192578125 | 0.11875 |
| Raw native first-score mean, unmasked | 0.21654829545454546 | 0.15965909090909092 |
| Total ACTs | 16 | 16 |
| Recorded retokenized output tokens | 1079 | 1068 |
| Recorded per-output token range | 38–104 | 38–102 |
| Outputs at recorded 400-token cap | 0 | 0 |

Every output has exactly one ACT; no missing-first or later-ACT rescue issue occurs. Format-masked native mean difference is +0.073828125; form-valid difference is +3/16 with zero paired regressions. Raw native partial scores are retained from the ledgers, **not independently recomputed through installed reasoning_gym**. Independently enumerating all288 valid 4x4 Sudoku grids gives exactly one completion for each of these16 captured questions; direct comparison against those completions reproduces both strict solved endpoints exactly. Form validity and all aggregate results match Main's reduction.

Token counts are captured tokenizer measurements, not a new local retokenization. Being below400 is not a recorded finish reason and does not establish that additional reasoning budget would help.

## What actually failed

Counts below overlap; they are descriptive diagnoses, not replacement scoring rules. Given violations include replacing or blanking an original given. Duplicate checks ignore blanks but examine all assigned digits.

| Observable property of first ACT | Process | Sham |
|---|---:|---:|
| Incomplete grid containing blanks | 9 | 11 |
| Non-grid suffix inside ACT | 4 | 7 |
| Exact unchanged givens echo, ignoring non-grid suffix | 3 | 3 |
| Violates at least one original given | 7 | 6 |
| Duplicate assigned digits in a row, column or 2x2 box | 9 | 7 |
| Intrinsically valid complete Sudoku, but wrong givens | 1 | 1 |

The form gains are not additional solutions:

- **1850004:** sham leaves one blank; process supplies16 digits. Process nevertheless changes two givens and violates all four 2x2 boxes. Sham also violates all four boxes and one given.
- **1850008:** sham leaves10 blanks and appends `PREDICT: 0.8` inside ACT. Process supplies16 digits without the suffix, but changes three givens and repeats digits in rows3 and4.
- **1850009:** sham has16 digits followed by an inline `PREDICT: 0.8`, so fails strict form. Process removes that suffix but still changes four givens and violates all four boxes. Sham's first four rows already change five givens and violate all four boxes: deleting the suffix would not solve it.
- **1850007, both arms:** a genuinely valid complete Sudoku for the wrong givens (two process violations; three sham violations). This isolates puzzle conditioning failure from Sudoku structure failure.
- **1850000, both arms:** identical16-digit answer, but two given violations and all four boxes invalid despite valid row/column permutations. Complete-looking output is not constraint competence.
- **1850001/06/12:** both arms return the unchanged givens. Other partial grids add assignments but sometimes introduce duplicate digits or lose givens. All individual violations and actual questions/actions are in the JSON.

Thus the secondary gain concerns answer completion/marker placement. There is no corresponding observed constraint-checking or solving gain. These traces cannot establish an internal cause, deliberate checking, or learned competency.

## Trace, endpoint and interface binding

- Rehashed every file in the preparation/process/sham inventories; exact file sets and hashes match. `STARTED.preparation_sha256` and both arm configs bind the same preparation. Both terminal arm reports equal their `COMPLETED.json` entries and say `LOCAL_GPU_BACKEND` / `COMPLETE`.
- All32 actual requests match saved preflight rows byte-for-byte on their fields. Each contains exactly its captured question and exactly one correct teacher package. Prompt, rendered-prompt, package and raw-output hashes match. The logged thought prompt/output exactly match the request/raw output. Parsing raw outputs with the native line-marker rule reproduces every ledger ACT in order.
- Paired prompts are byte-identical after removing only the corresponding teacher package. The rendered wrapper is the same Qwen system/user/assistant chat structure. No reference solution appears in the actual prompt; the question givens and shared native scaffold are present. Independent completion enumeration happened offline after generation.
- Each pair uses the same episode, seed, recorded prompt-token count and model-loader identity: max400 output tokens, temperature0.7, one97-token package per question,16 presentations per arm (1552 teacher tokens). Native seeds match `(crc32(f"{episode_id}/1") XOR 7101) & 0x7fffffff`. The protocol records batch8/one tick, preflight4096 context and backend16384 context; recorded requests fit the preflight budget.
- Recorded source identity is vLLM, the same local Qwen2.5-7B-Instruct snapshot, `adapter_input=null`, `adapter_files={}`. All seven reviewed local source/config/bootstrap hashes match preparation's pinned source bytes. Those bytes send the saved raw prompts through the same chat-template operation and call the backend once per batch; ledger consumption follows generation with no feedback-based continuation. No training or additional NOTE-model calls are present. Emitted NOTE text is possible in the same output and is not a separate call.
- The native question asks for newline-separated rows; the surrounding prompt explicitly says to encode multiple rows with ` ; ` on one ACT line. The decoder implements that mapping. `PREDICT` is a marker only at the start of a line, so an inline `; PREDICT: ...` is legitimately part of the submitted answer, not a lost second request. Trailing semicolons alone are accepted. There is no evidence of the interface discarding a correct solution here; all32 actual actions are preserved.
- The shared bootstrap includes a generic claim about evaluation on unseen families, although this diagnostic actually uses training questions. That wording does not change the panel's status and must not be used as evidence of heldout transfer. It is shared across arms, not an arm-specific delivery mismatch.
- Native thought `win=true` denotes best-score improvement, **not solved**. This review uses strict first-ACT form plus unique-solution equality/native score1, not that field.

Configured loader identity and source linkage are evidence about this captured execution, not an independent attestation of every vLLM internal operation or official model origin. Model weights are not present/rehashed in this review. These limits do not introduce a new prerequisite for the authorized exploratory comparison.

## Terminal evidence and scope

Captured `COMPLETED.json`: **2026-09-12T12:02:55.307608+00:00**. Same GPU3, process then sham. Process cleanup PID87252 and sham cleanup PID88374 each match their worker receipts and report `owned_group_empty=true`, `gpu_processes_absent=true`, `reservation_release_verified=true`, `cleanup_error=null`. This preserves the receipt labels; it is not authority to release any other reservation. Launch controller PID87251 is reported gone by Main; this offline review did not perform a new process-table observation.

Inputs: `/tmp/astra_static_competency_terminal_20260912.tgz`, its extracted preparation/run/log directories, and `/tmp/astra_static_competency_terminal_analysis_20260912.json`. Every captured small-file hash and archive hash is preserved in the JSON. The JSON also includes all source pins, check outcomes, cleanup receipts and episode-specific evidence.

**Claim boundary:** single generation seed7101, sequential order, teacher continuously present, combined FORM_CHECK+CONSTRAINT_LEDGER package, existing training questions. No persistence/internalization, adaptive parenting, P1/H1, heldout generalization or significance claim. The primary tie remains final for this panel regardless of any later format follow-up.
