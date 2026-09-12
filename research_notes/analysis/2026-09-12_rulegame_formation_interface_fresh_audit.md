# Fresh interface audit: SEQ-094 RuleGame v1 → v2 formation

**Date:** 2026-09-12
**Verdict:** `interaction_v2` **does establish that the dominant v1 failure was the task interface, not parenting or absence of rule-task capability**: valid first quizzes rise from 0/8 to 8/8 and protocol-invalid terminals fall from 8/8 to 0/8, including 4/4 valid pre-parent tasks. It does **not** make material eligible. **No write remains mandatory** for two independent frozen reasons: P has only 1/6 faithful apply records (below the required two), and both A control interactions again violate acknowledgment-only contact. No threshold reduction, replacement record, one-sided fit, or content relabel is permitted. Neither version supports a P-versus-A parenting effect.

This was an independent read-only audit. I inspected the launched `strict_v1` source pinned by its plan (commit `aff89c4f`, diagnostic SHA-256 `67581fdb…`), the versioned `interaction_v2` source pinned by its plan (commit `20897d84`, diagnostic SHA-256 `6d8bca8e…`), tests, both selected protocols, relevant coordination entries, and both completed node-3 roots. I did not edit builder code, launch/stop a process, or query/use a GPU.

## Exact terminal facts

The sealed v1 native result is:

| Endpoint | P | A | Total |
| --- | ---: | ---: | ---: |
| Tasks | 4 | 4 | 8 |
| Tasks terminal `protocol_invalid` | 4 | 4 | 8 |
| Valid scored quizzes | 0 | 0 | 0 |
| Executed apply TRYs | 0 | 4 | 4 |
| Record calls | 0 | 4 | 4 |
| Faithful records | 0 | 2 | 2 |

The eight terminal invalid responses divide exactly into four missing canonical `ACT:` markers (`0007`, `0008`, `0011`, `0022`, all anchored `TRY:` aliases) and four multiple-ACT responses (`0004`, `0016`, `0021`, `0031`). P therefore has no record opportunity. A records `0020` and `0028` match the actual execution; `0026` and `0030` incorrectly say `matched`. The independently derivable first-two count is P=0, A=2. The content audit separately rejects both A controls, so the recorded `MAIN_DECLINED_MATERIAL` is justified even before applying paired shortage. There is no `write/` or `evaluation/` stage.

Zero quiz accuracy here means **missing/invalid quiz filled with zero**, not eight wrong six-label answers. Two rejected post-reveal raw responses actually contain a syntactically complete six-label proposal, but retrospective salvage would violate the fixed first-valid-quiz endpoint and must remain diagnostic-only.

The sealed v2 result is:

| Endpoint | v2 P | v2 A | v2 total |
| --- | ---: | ---: | ---: |
| Tasks / valid first quizzes | 4 / 4 | 4 / 4 | 8 / 8 |
| `protocol_invalid` terminals | 0 | 0 | 0 |
| Executed apply TRYs / record calls | 6 / 6 | 6 / 6 | 12 / 12 |
| Faithful records | **1** | **3** | 4 |
| First-two selectable rows | **1** | **2** | shortage |

P and A have identical pre-task scores: rule0 `0.50`, rule1 `0.8333` (mean `0.6667`). Apply scores cross by lesson—P `0.6667/0.50`, A `0.50/0.6667`—so both apply means are `0.5833` and both raw pre→apply changes are `−0.0833`. This is descriptive only, but it supplies no directional parenting signal. More importantly, all twelve apply TRY outcomes are `True`; the formation contains no negative world observation and does not demonstrate discriminative probe selection.

V2's twelve record outputs fail in a structured way. All four missing-prediction (`null`) cases say `matched` rather than `unavailable`; four of five false-prediction/true-outcome cases say `matched` rather than `mismatched`; all three true/true cases pass, and only one false/true case passes. This is a strong default-to-`matched` error despite the evaluator-supplied fields. It localizes a remaining record/relation interface or capability problem that the process parent did not repair.

The terminal coordination note says there are seven record relation failures. Exact replay gives **eight**: five P failures plus three A failures, consistent with only 4/12 faithful records.

## Findings

### 1. The world/action boundary was not exclusive

`strict_v1.parse_action` requires one canonical `ACT:` marker but ignores arbitrary non-ACT text after the selected action. `play_task` appends the entire raw response to the next prompt and then appends the real harness outcome. Consequently a response can commit one action and also impersonate the world.

This occurred in four **accepted** executions, separate from the four multi-ACT terminal failures:

| Call | Task/tick | model-authored outcome in the accepted response | real harness outcome | consequence |
| --- | --- | --- | --- | --- |
| `0002` | P rule0 pre t3 | `True` for `(2,3,4)` | `True` | duplicate outcome enters parent transcript |
| `0014` | A rule0 pre t3 | `True` for `(7,8,9)` | `True` | duplicate outcome enters control transcript |
| `0027` | A rule1 apply t2 | **`False`** for `(2,4,6)` | **`True`** | contradictory outcomes enter record call `0028` and the next wake prompt |
| `0029` | A rule1 apply t3 | `True` for `(3,6,9)` | `True` | duplicate outcome enters record call `0030` and the next wake prompt |

Thus “imagined outcomes were never executed” is true, but “no fake outcome was admitted” needs qualification. The false value was not used as the authoritative `observed` field and no corpus was made, yet it crossed the response boundary into downstream model-visible context. One of the two would-be selected A records (`0028`) is attached to that contradictory source turn. `select_records` does not inspect the source wake response for this condition.

The parent boundary has the same trust problem. Parents receive a flattened raw transcript, not a typed view of committed actions and harness outcomes. Rejected self-simulated quiz/outcome text is therefore visually indistinguishable from world text. A lesson 0 consequently asks about a “final outcome of your quiz” although no valid quiz occurred; A lesson 1 says the child “tried” `(1,2,3)` although the alias was never executed. This is interface-induced false feedback, not just weak pedagogy.

### 2. The reveal contract contradicts the environment

The boot explicitly requires `ACT: QUIZ ?`. The parser calls this a valid reveal, but then passes `QUIZ ?` to `RuleGame.evaluate`, whose public result is:

`INVALID: quiz needs 6 answers (T/F) for [...]`

The harness silently flips its own `revealed=True` bit anyway. Both tasks that reached this state then produced a multi-action, self-simulated continuation on the next tick. These two `INVALID` world results are logged as normal reveal executions, not protocol violations. The child is therefore told simultaneously that it followed the required reveal protocol and that its action was invalid. A task-local reveal facade should return a typed neutral panel response, not reuse an evaluator error as the public observation.

This remains present in `interaction_v2`: all eight v2 reveal executions still return `INVALID`, while the new state reminder says the quiz is revealed. V2 nevertheless obtains 8/8 valid next-turn quizzes, so the contradiction is no longer an action-validity blocker, but it is still protocol-invalid public feedback. It directly contaminates control semantics: A's first v2 control says the quiz “needed more answers” even though the following scored quiz was valid. The scripted tests ignore this semantic contradiction and do not assert that a reveal response is non-`INVALID`.

### 3. The record endpoint is exact but label-assisted

The record judge correctly binds exact triple, actual Boolean, explicit pre-ACT Boolean/absence, and derived relation. Raw response bytes are preserved; selection order and execution joins replay correctly; no incorrect/fabricated Boolean would have entered a corpus.

However, the record generation prompt supplies all three source labels in an evaluator-authored block:

`Observed fields: {"values": [...], "observed": true, "predicted": true}`

V1 call `0028` is the clearest case: the same prompt contains the child's false imagined outcome, the harness's true result, and the structured true label; the model returns the label-block answer. V2 removes the contradictory imagined outcome, but retains the complete `Observed fields` label block and still gets only 4/12 relations right. This tests whether the model can serialize supplied event fields and compute the relation, not whether it autonomously distinguishes trusted sensory feedback, extracts an experience, or authors a useful record. The frozen protocol calls this “format-coached faithful event recording,” which is the defensible boundary. It must not be summarized as spontaneous reflection or unassisted own-event binding.

Selection is otherwise faithful to its prospective rule: physical event order, first two eligible per arm, distinct execution IDs, no quiz gate. Exact duplicate target text is explicitly permitted and even required by a fixture, so two rows cannot be called two distinct pieces of knowledge. In v2, Main's audit derives P=1 and A=3 eligible, hence selectable P=1/A=2. Because the required count is two in **each** arm, shortage alone closes the writer path even if content review were accepted. The material implementation returns `MAIN_DECLINED_MATERIAL` first because A content is rejected; it does not materialize a selection or corpus.

### 4. Parenting/control semantics are not interpretable

All four v1 pre-tasks fail before the corresponding parent call. In rule1, P and A produce the same pre-parent raw response (`PREDICT: T` plus `TRY: 1,2,3`) under identical prompt bytes and seed, and both are rejected solely for the alias. This directly excludes parenting as the cause of those failures. In v2, all four pre-parent tasks produce valid quizzes; the P and A raw pre-task outputs and scores match exactly. This v1→v2 reversal is positive evidence that the action interface, not parenting, was the binding v1 failure.

V1 P lesson 1 is also more than a harmless diagnosis defect. The parent falsely says no prediction was made and recommends the exact probe `(4,5,6)`; the apply response copies `(4,5,6)`. No outcome or hidden rule is supplied, so this is not answer leakage, but it is concrete action/strategy selection. Accepting it is inconsistent with the selected memo's instruction to audit strategy leakage and with the stronger parent-does-not-select-probes boundary.

V2 retains the same P parent prompt. P lesson 0 asks for a prediction on the already experienced positive triple `(2,3,4)`; the restatement introduces “find the sum,” computes `2+3+4=9`, and that exact triple becomes the first apply action. This does not reveal “sum divisible by three,” and the hypothesis is child-generated, but it is answer-adjacent, task-specific semantic steering rather than a pure process-only lesson. The apply prefix carries it into the same rule class. P lesson 1 is generic prediction advice and never addresses the record relation error that actually prevents material.

Both v1 A controls violate acknowledgment-only contact: one solicits quiz/learning reflection and unsupported praise; the other solicits attempted-experience narration. V2's clarified control prompt still fails in both lessons. A lesson 0 repeats training score `0.50` and the misleading “needed more answers” reveal error; A lesson 1 repeats score `0.83`, and its restatement confuses the parent and child roles. These training scores are not sealed readout data, but score-bearing task summaries are not neutral acknowledgment. They also enter the subsequent A apply prefixes. Main's rejection is correct. There is no valid active-neutral counterfactual and no evidence about parenting efficacy.

No hidden rule description, correct quiz truth vector, or sealed readout answer was found in a learner-visible prompt. The semantic leakage/confounding found here is instead (a) v1 untrusted model-authored outcome text entering later context, (b) complete evaluator labels in every record request, (c) concrete-case/action steering in P, and (d) training scores/error text entering the nominally neutral v2 A restatements.

### 5. Opportunity matching is not realized dose or common-random parity

The protocol accurately disclaims exact realized-compute matching. Actual v1 native usage was:

| Role | P calls / input / output tokens | A calls / input / output tokens |
| --- | ---: | ---: |
| Wake | 8 / 3,049 / 406 | 12 / 4,574 / 444 |
| Record | 0 / 0 / 0 | 4 / 1,058 / 140 |
| Parent | 2 / 2,275 / 167 | 2 / 521 / 63 |
| Restatement | 2 / 261 / 132 | 2 / 157 / 94 |
| **All** | **12 / 5,585 / 705** | **20 / 6,310 / 741** |

P parent-plus-restatement input exposure is 2,536 tokens versus A's 678 (3.74×), and the later action/record opportunities differ because of post-treatment interface validity. These are legitimate descriptive costs, not a matched-dose causal contrast. Equal maximum calls and output ceilings do not repair the imbalance.

Matched seeds are not common random numbers in the realized backend. Calls `0002` and `0014` have identical prompt bytes, native prompt-token IDs, and seed `311336830`, but different responses. The arm histories diverge from there. Any later arm contrast must retain separate realized baselines and must not treat numeric seed equality as deterministic coupling.

V2 reaches all fixed opportunities (30 calls per arm), but input/content dose is still unequal:

| Role | v2 P calls / input / output tokens | v2 A calls / input / output tokens |
| --- | ---: | ---: |
| Wake | 20 / 8,743 / 237 | 20 / 8,323 / 237 |
| Record | 6 / 1,524 / 198 | 6 / 1,524 / 200 |
| Parent | 2 / 2,161 / 161 | 2 / 609 / 83 |
| Restatement | 2 / 255 / 132 | 2 / 203 / 48 |
| **All** | **30 / 12,683 / 728** | **30 / 10,659 / 568** |

P parent-plus-restatement input exposure is 2,416 tokens versus A's 812 (2.98×), with 293 versus 131 output tokens. V2 legitimately improves opportunity parity and makes the pre-task outputs exactly paired, but it remains an opportunity-matched, content-and-dose-different intervention. The parent and child are also the same frozen 7B base under different prompts, so failure or success cannot be generalized to stronger adaptive parenting.

### 6. Accounting is replayable but the headline result schema is incomplete

Raw requests, outputs, executions, usage and event order replay exactly. Multiple-ACT responses are not partially executed, and response/call ceilings were respected. But both versions' summaries omit protocol-required prediction agreement/missingness, unique TRY count, faithful records per actual TRY, and exact integer quiz correct-count. V1 also omits the per-task violation reason from its task rows. Those facts are derivable from events but absent from the accepted `result.json` interface. V1 accepted model-authored `[OUTCOME]` text and both versions' expected-but-`INVALID` reveal are not counted as boundary violations at all.

V1 totals are 32 calls, 11,895 prompt tokens, 1,446 output tokens and 42.209 generation seconds. V2 totals are the fixed 60 calls, 23,342 prompt tokens, 1,296 output tokens and 38.957 generation seconds. The respective 169.633754- and 164.493039-second supervised windows are correctly labeled as reservation/cleanup wall time, not generation time or total GPU compute.

### 7. Custody and cleanup pass, with one terminal-seal caveat

Read-only verification found both controllers absent: v1 PID 142838 and v2 PID 146460. Each remote root contains only `formation`, declined `material`, plan and native-preparation artifacts; neither has a write or evaluation tree. V1's formation manifest is SHA-256 `d4a157f3…`, with all 70 named files matching. V2's is `4fef2770…`, with all 126 named files matching. Both backend receipts say `closed=true`; both supervisor receipts say return code 0, owned group empty, GPU process absent, and reservation release verified. Each log shows the cleanup path killed one owned EngineCore, reports `freed=True`, and ends with a leaked-semaphore warning. I did not independently query the device.

The raw formation is strongly sealed. On a declined material path, `material()` returns before `capture_manifest`, so the remote `material/main_audit.json`, provenance and result lack their own directory manifest. Committed capsule/hash receipts now cover them, but future terminal paths should seal failure/decline directories exactly as READY paths are sealed.

## Smallest discriminating test

The smallest action-boundary discriminator would have been zero-generation replay of exact v1 raw call `0008` (or `0022`): a typed decoder that accepts one anchored `TRY:` alias commits exactly one `(1,2,3)` action, while strict v1 rejects the same prediction/action bytes. One no-parent, no-record, no-fit task with native stop-before-world and a truthful reveal would then have been sufficient as the scientific canary.

V2 has now run a larger version of this discriminator. Its four pre-parent tasks all commit three TRYs and one valid quiz, while their v1 counterparts all terminate invalid. Therefore the action interface question is answered: v1 did not measure a parenting or task-capability failure. No additional action-format search is warranted.

The smallest remaining discriminator is now a **no-parent, no-world, no-fit three-case relation canary** using the exact v2 P-rule0 apply receipts:

1. false prediction / true observation → `mismatched` (record call `0008`, currently wrong);
2. true / true → `matched` (record call `0010`, currently right); and
3. absent prediction / true → `unavailable` (record call `0012`, currently wrong).

Present the immutable raw emitted action and trusted world response with a typed trust boundary, but do not provide a precomputed `relation`; ask for only the one relation token at temperature zero. If these three pass, the verbose JSON/label handoff is the problem; if they fail, the base child's elementary relation-following is the problem. Parenting adds no information to this test. Regardless of its outcome, it cannot reopen either completed root or authorize a write from them.

## Interaction-v2 qualification and residual gaps

`interaction_v2` successfully adds native stop-before-`[OUTCOME]`, a single anchored `TRY:/QUIZ:` alias, raw/canonical action separation, explicit remaining-budget state, and a stricter A-control prompt. The native stop fires on both paired rule0-pre tick-3 calls, no imagined outcome appears in accepted v2 text, and all eight tasks complete valid quizzes. Its focused parser/stop fixtures cover these important mechanical seams.

It does **not** resolve the `QUIZ ?`/`INVALID` contradiction, P's concrete-case invitation, evaluator-labeled record authorship, result-schema omissions, or the reliability of model-generated active-neutral control. The stricter A prompt fails semantically in 2/2 native generations. Its end-to-end scripted test always emits the desired neutral acknowledgment and desired quiz, so it cannot establish those semantic contracts. V2 also shows that the record bottleneck survives successful task interaction: P=1/6 and A=3/6, with eight relation errors.

At the current shared HEAD, 37 focused CPU tests pass when `TMPDIR=/private/tmp`. The default macOS temporary path exposes one unrelated portability failure: `/var/...` versus `/private/var/...` is treated as a model/adapter identity mismatch in the mocked complete-pipeline test. No code was changed here.

## Claim boundary

The defensible joint statement is: **v1 failed mainly at its action/world interface; v2 repaired that boundary and obtained 8/8 valid quizzes, but both versions still failed materialization. V2's exact faithful-record yields were P=1/6 and A=3/6, so fixed first-two selection gives P=1/A=2 and mandatory paired shortage; its 2/2 invalid A controls independently require Main decline. No write or readout occurred.** This is evidence that interface design can mask task behavior and that exact event serialization remains a bottleneck. It is not evidence that parenting helps or harms, that the writer works, or that the faithful serializations constitute autonomous reflection.
