# Actual-context RuleGame record export — September 12, 2026

**PLAN ONLY / EDITSTOP.** One new thin exporter, later and separately assigned; no implementation, historical-renderer replacement, task change, training, or guard framework here. Only this note was written. No source modules, tests, GPU, Git or network were executed.

## Proposed function I/O

`build_record_pair(capture_root, main_audit, fixed_selection, tokenizer, max_len) -> {corpora: {P, A}, source_receipts}`; fail atomically with explicit reasons, returning **no trainable pair** on any failure. Inputs bind the capture manifest/identity, replay-verified events, accepted Main audit, and **unchanged first-two-per-arm selection**. Retain `check_capture`, `validate_main_audit`, `select_records` and `judge_record` semantics (`organism_v6/rulegame_parenting_diagnostic.py:522`, `:604`, `:619`, `:262`). Never search later records when a selected one fails export. Archive the new projection separately; preserve old material/renderer bytes.

| Join | Exact fields and checks |
|---|---|
| Selected record | `kind="record"`, `arm`, `eid`, `execution_id`, `source_call_id`, `call_id`, `text`, `eligible`, `failures`; require original selection/order, faithfulness and distinct executions. |
| Record request/response | `calls/{call_id}.request.json["request"]`: role `record`, matching arm/eid/call_id/tick and exact `prompt`; receipt identity, `prompt_sha256`, `started`. Response receipt: `response_sha256`, `ended`, and `response.{text,rendered_prompt,prompt_token_ids,output_token_ids}`. Target equals `response.text == record.text` byte-for-byte, **not reserialized JSON**. |
| Source execution | Join unique `execution_id` plus arm/eid; require `kind="execution"`, `action_kind="try"`, `call_id == record.source_call_id`. Bind `tick`, `values`, `observed`, `predicted`, `prediction_ambiguous`, `outcome` to replayed world execution. |
| Source wake | `calls/{source_call_id}` is role `wake`, same arm/eid/tick; its `response.text` supplies emitted output. Execution precedes record in event order; wake response ends before record request starts. **Do not use the wake request as training context.** |

## Context, forbidden bytes, and causality

The actual record request (`rulegame_parenting_diagnostic.py:443`) is:

```text
Task: {eid}
Execution: {eid}#t{tick}
Actual emitted output:
{source_wake_response.text}
Actual world response:
{execution.outcome}
Observed fields: {JSON(values, observed, predicted)}
{existing RECORD instruction}
```

Use the **stored exact prompt**, verifying reconstruction without substituting it. Its displayed execution identifier omits the arm; the event's full `execution_id` includes it. This is past-action/outcome-conditioned **record prediction**, not future-action supervision. Add no later quiz/score, future action, gold relation, corrected record, or hidden rule.

**Actual inspection:** all12 SEQ095 v2 record prompts have no direct parent/restatement block; embedded wake outputs contain only ACT, optionally PREDICT. None contains full parent/restatement payloads or copied lesson prose. Checked51 relevant source/event/request/response files against capture manifest SHA256 `4fef2770a6be151bc00fc4782575134643f8754b2cd149380b48a4aaf6dfed41`. This does not certify future prompts. The wake prompt itself includes the temporary restatement; a future child can echo it into wake output and thereby contaminate the record prompt.

Bind forbidden payloads/lesson-bearing spans to all delivered `result.interactions[].parent` and `.restatement` messages and their call receipts. Check **raw prompt, rendered context and raw target**, including copied spans embedded in child history. Masked context is not exempt. Any copied lesson/restatement or unresolved provenance blocks the fixed pair: **no stripping, paraphrasing, whitespace cleanup or silent surgery**. Shared protocol words/triples alone are not evidence of copied pedagogical prose; full-payload substring checks alone are insufficient. Preserve Main's semantic content assessment and exact record-faithfulness checks.

## V3 output and reuse

Each arm returns a V3 `corpus` list of items with:

```text
spans = [[actual_rendered_record_prompt, false, "record_context"],
         [complete_raw_record_text, true, "own_raw_record"]]
```

Bind selection ordinal, arm/eid/full execution ID, both call IDs and input/output hashes in sidecar receipts. Reuse the **encoding assertions** in `organism_v6/parent_wake_material.py:185–207` and V3 `encode_item_segments`/`collate`: local tokenizer rendering must equal stored `rendered_prompt` and native prompt IDs; input is context IDs + raw-target IDs + **one EOS**; labels are context `-100` + target IDs + EOS, with correct causal shift. Disable extra chat templating/packing; reject splitting, truncation, empty targets or token mismatch. Do **not** call `without_teacher` or reuse that exporter's candidate-selection logic.

**Regression cases:** wrong record-versus-wake call; forged/resealed source/tick/outcome; false versus null prediction and ambiguous prediction; semantically wrong relation; parent sentence echoed into context or target; lesson only in masked context; raw JSON whitespace preserved; wrong native rendering/IDs; causal off-by-one/double EOS; overlength; selected-record rejection with a later valid replacement available; rejected Main audit or one-arm shortage. All must preserve historical bytes and forbid partial-pair output. Existing SEQ095 remains blocked: P1/A2 selected records and declined controls; clean prompt bytes do not admit it. Native token/mask checks described here were **not run**.
