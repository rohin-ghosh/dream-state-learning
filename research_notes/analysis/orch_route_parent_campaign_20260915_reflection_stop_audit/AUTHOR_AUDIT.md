# Fixed reflection safeguard replay and context-bound author audit

Scope: declared 2026-09-15 07:57:14 UTC; native CPU collection completed
08:01:32.824510 UTC. Two prespecified historical pathological samples and both
new guarded reflections, no substitutions. No model/provider calls, GPU work,
held readouts, fit ingestion, source changes or lane interventions. Raw remains
on A100. `CPU_RECEIPT.json` binds 34 native files with size/SHA256 and verifies
all unchanged after collection, including both parent archives (18 files).

## Historical counterfactual replay

| Fixed sample | Actual recorded tokens | First callback stop token | Counterfactual tail tokens | Exact repeated block |
|---|---:|---:|---:|---|
| MICRO C7 CALL_0075 | 8192 | 848 | 7344 | Three copies of long–short-formula–long; 573 content characters/block; two long paragraphs |
| Training C3 CALL_0027 | 8192 | 784 | 7408 | Three copies of one 431-character paragraph |

Both actual originals were truncated, not EOS-complete. Both replay stop
witnesses admit a partial next paragraph: 47 and 77 characters respectively.
Repeated-content characters at the counterfactual stop are 1193 and 939;
these are not repeated-token counts. Exact raw-prefix and block hashes are in
the receipt. The mixed block regression therefore covers the supplied failure,
including its short formula; requiring every paragraph to be long is not used.

Method: load the existing Qwen tokenizer JSON through `tokenizers` only; verify
the stored token sequence decodes exactly to stored raw; instantiate the
pinned `ExactParagraphRepetitionStop` with zero prompt length (stored IDs are
generated-only); feed every successively longer token prefix. The callback
applies its native default 512-token minimum and 16-token inspection cadence.
Finalize the first triggered prefix against the original effective cap.
No torch/transformers/model load. The native source and tokenizer hashes are
verified against the declared pins, not inferred from a filename. Replaying
the full original as newly emitted output would not constitute an early stop.

These are **counterfactual prefix replay positions**, not measured runtime
token/walltime savings. The original 8192-token records remain intact. The
tail counts are arithmetic differences, not tokens actually avoided by a live
run. No semantic-yield or quality-preservation claim follows from this replay.

## Actual guarded reflections

Both calls belong to the existing BASE/no-adapter, zero-update contextual
continuation `campaign_feedback_uptake_stopped_r107_5`. They are own reflections
with parent guidance present, not fresh parent-free retention tests. Main and
Anscombe independently recorded safe-boundary deployment; this audit does not
relaunch or change it.

| Call | Native start UTC | Native finish UTC | Measured call wall seconds | Generated tokens incl./excl. EOS | Actual ending |
|---|---|---|---:|---:|---|
| CALL_004 | 07:55:59.263719 | 07:56:12.196257 | 12.932539 | 588 / 587 | EOS; no stop request |
| CALL_005 | 07:56:12.206687 | 07:56:23.852851 | 11.646164 | 531 / 530 | EOS; no stop request |

Both actual effective caps are **2048**, not 8192. Neither prompt nor output is
truncated. No stop was requested or needed for either; no causal speedup is
demonstrated. Each reports zero exact duplicate eligible paragraph characters,
lexical unique-content fraction 1.0, and machine semantic novelty **UNKNOWN**.
Call walls are receipt finish minus start, not isolated kernel timing or full
cycle/parent-wait time. Parent P1/P2 API walls and usage are separately recorded
in the receipt; both actual response models are `openai/openai/gpt-6-astra`.

## Author semantic judgments, separately from machine metadata

Author read the full eight-message supplied context and full output for both
reflections, the complete shared preceding reflection, and both recorded parent
plans. Original/check raw texts join exactly to messages 3/5; task identities,
carry contents and the relevant P1/P2 guidance join exactly. The receipt hashes
each captured message. This compares newly **expressed observations** against
the whole supplied context, not only wording within the generated reply. It
does not inspect or measure hidden thought. These are provisional author
judgments, not independent ratings or an exhaustive proposition census.

### CALL_004: wrong-task persistence despite specific parent correction

- Current task asks for the integer satisfying `13x + 8 = 255`; the original
  correctly computes and substitutes `x = 19`. Its recorded final answer was
  unparseable. The check instead re-solves the earlier 214-box carry task.
- P2 explicitly identifies that drift, distinguishes sound algebra from failed
  acceptance, and cautions that proposed Python/output is not execution and
  formatting is not an established causal diagnosis. The new reflection again
  centers the old 214-box calculation and gives 1452, not the current equation.
- The arithmetic for that old task is valid, but is not a new observation and
  does not resolve the current task. Remaining-box interpretation, clarity,
  persistence and calculation claims are already in the carry/check context.
- Submission-format/function-call possibilities and a proposed test submission
  restate hypotheses/proposals in the preceding check. No test execution or
  newly established parser requirement appears. A statement that no uncertainty
  remains conflicts with the actual unresolved task/acceptance discrepancy.
- **No grounded, newly expressed substantive observation or verified correction
  identified.** This is not successful uptake of the task-alignment correction.
  Some rephrasing and rearrangement occur; they do not establish semantic yield.
- R106: a format/feedback what-if and return to an answer are expressed, but the
  return is to the wrong task and produces no new evidence. Do not call this
  productive midline departure-and-return investigation. A terminal plan to
  test later is not an executed check. Method count is not branching yield.

### CALL_005: correct task preserved, largely supplied-template restatement

- Current task's subtraction and multiplication (109 minus 19, then times 9)
  yield 810, already expressed in original/check and supported by their recorded
  final-answer checks. Those facts are preserved, not newly discovered here.
- Excluding shipped boxes, the meaning of remaining, no live uncertainty and
  the potential clarity improvement are already supplied by the check, P1/P2
  or analogous prior carry. Much of the reflection follows the carry's outline
  with this task's constants, which themselves were already supplied.
- **No grounded, newly expressed substantive observation or verified correction
  identified.** Retaining the right task and arithmetic is useful but is not
  evidence of new reflection-driven learning. The call does terminate naturally.
- It returns to a boxed answer rather than the earlier literal `FINAL: 810`.
  Record that visible delivery difference without inventing an observed parser
  failure for this reflection or treating EOS as answer acceptance. Reflection
  instructions are not identical to the original/check task instructions.
- R106: retrospective verification and judgments are present; no newly executed
  midline investigation, rejected alternative or evidence-backed correction is
  expressed. Do not inflate terminal recap into several productive branches or
  require multiple methods as the definition of branching.

## Denominators and claim limits

- Fixed two reflections: **0/2** with an author-identified grounded new substantive
  observation/correction relative to full context; this is a sample-level binary
  audit, not semantic token yield or a population estimate.
- **1/2** stays aligned to the current task and preserves its valid solution;
  **1/2** persists on the unrelated carry task despite explicit correction.
- **2/2** contain substantial semantic restatement of supplied propositions;
  **0/2** triggers the exact-paragraph guard; **2/2** ends with EOS. These facts
  coexist with lexical unique-content fraction 1.0 in both calls.
- Machine `semantic_novelty_yield` remains UNKNOWN and its pending-review marker
  remains untouched. This separate author annotation does not mutate raw source
  metadata, certify admission, or claim an internal thought count.
- No fresh same-state parent-free next-cycle comparison was audited here.
  Retained behavioral change, guard-caused quality improvement, learning slopes
  and runtime savings are **not established**. BASE has zero weight updates by
  design; contextual behavior is not a saved LoRA update. Different historical
  tasks/contexts/caps cannot be used as a causal pre/post comparison.

Validation: 35 helper CPU tests pass using
`python3 -m unittest tests.test_orch_reflection_repetition_stop -q`; source/test
pins unchanged. Initial `python` invocation was unavailable; rerunning via
`python3` passed, no source repair. The test suite includes mixed
long–short–long repetition and all-short/varied negative cases. All 34 native
input hashes are unchanged. No raw prompt, response, token array or archive is
included in this publication set; only author paraphrases, counters and hashes.
