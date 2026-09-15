# Independent semantic and neutral-prefix audit — September 14, 2026

## Scope and independence

This is a complete, independent content review of all **190 targets / 64 tasks**, not an experiment run, condition comparison, rescore, or operational stop. Every target was read in full in packet hash order. The initial oversized display was truncated by the terminal transport; subsequent bounded displays recovered the affected targets in full. The target that itself ends mid-sentence is separately identified below.

The sole substantive source was read-only `BLIND_PACKET.json`, SHA256 `4a459a9bea6415ef43c0db936587f50d713e7096cbafca83d7f2074d7a5214c9`. Every packet row ID equals SHA256 of its exact target UTF-8 bytes. Every recalled assistant solution in a neutral prefix is byte-identical to a packet target that was read in full. The neutral record request is always “Write your own reusable record of this solved task.”

No COORDINATION, BOARD, RESEARCH_STATE, original reports/reviews/author labels, or other agents' conclusions were read. An initial checkout-status command exposed unrelated filenames only, not their contents. No Fable reader, model calls, GPU allocation, native cells, new SEQ, production-code changes, benchmark edits, git staging/commits, merge resolution, or external publication occurred. The only code written validates and packages this audit's evidence structure.

`FREEZE.json` binds the complete assessment, manual ledgers, report, structure-test code/receipt, and owned worker handoff **before any author-label comparison**. Main alone handles later joins. Do not interpret the aggregate counts as a paired treatment effect or infer which source condition generated a target.

## Strongest finding: a checker event does not follow from correct arithmetic

**Target SHA256 `7ccf8746fafbbeb2859ab52f595bdb87d4e4e77fff8866611f9343d43c764880` (index 94): semantics PASS, neutral-prefix support FAIL, mathematical outcome PASS, tokens PASS (338).**

Exact target quotation:

> The final value of 300 passed the exact-answer checker, confirming the solution.

The neutral prefix contains Wade's question, the previous calculation `20*5=100`, `40*5=200`, `100+200=300`, and the neutral record request. It contains **no checker event**. The removed generation guidance says:

> The final value passed the exact-answer checker.

Numerically, `(20+40)*5=300` is inferable. An externally delivered checker verdict is not. The child may recall the previous calculation as its own event, and may make a numerical self-check from it. Neither licenses claiming external feedback absent from the training prefix. This is the clearest generation-guidance removal incompatibility; the other support defects below should not all be called feedback leakage.

**Attempted falsification:** I inspected the full neutral prefix and generation guidance for this row, verified the recalled solution against the already-read target, and recomputed the answer. The checker assertion could be defended as a numerical self-check only by changing the meaning of “passed the exact-answer checker.” The guidance makes the external-event reading explicit. No target or prefix was rewritten to rescue it.

## Correct final values can carry false reusable content

**Target SHA256 `5535fdd20fb1b741aad2d9be367cfd85842e78b7cc2c45346fe59a082f4d81a8` (index 63): semantics FAIL, neutral-prefix support FAIL, numerical outcome PASS (`7`), mathematical narrative FAIL.**

Exact reusable-rule quotations:

> Subtracting the number of crayons given to Mae from the total crayons after giving to Mae to find the crayons given to Lea.

> Subtracting the number of crayons given to Lea from the number of crayons given to Mae to find the difference.

The first rule computes `27-5=22`, not Lea's `27-15=12`. The second computes `5-12=-7`, reversing the requested `12-5=7`. The actual worked steps and final answer are correct; the expressly reusable instructions are not. This is not a gold mismatch, short target, missing keyword, or objection to autobiographical voice.

**Attempted falsification:** I checked whether “difference” could reasonably mean absolute difference. That does not repair the first rule and does not match the second rule's directional “subtract Lea from Mae.” The displayed correct arithmetic refutes, rather than supports, these rules. The independently read same-task target at index 162 explicitly subtracts 15 to get Lea's 12 and checks `5+12+15=32`; this is a within-packet mathematical counterexample, not an author-label comparison.

**Smaller quantity-label defect:** SHA256 `f5cbb1a2c0d5c9a6e372ddbe60279c67e9011a54f9994bc54647a8795354ed70` (index 183) calls `5 months * $30/month = $150` “Total earnings in 5 months.” The question and prior solution distinguish earnings of $60/month from savings of $30/month. The final time-to-save `5` is correct, but this check mislabels savings as earnings. I treat it as a localized literal-truth failure, not evidence of a broad numerical inability.

## Gold discrepancy — preserved, not rescored

**Target SHA256 `9ebcea830c61eb111f84284df21be629b4cb855d3012b927117dc23e7dc79c3a` (index 120, `gsm8k-train-474`): mathematical outcome PASS (`12`), preserved gold `6`, semantics FAIL for absent check, neutral-prefix support PASS.**

Exact target quotation:

> Therefore, 12 members ordered orange juice.

Thirty members: lemon `30*2/5=12`; remaining `18`; mango `18/3=6`; orange `18-6=12`. The partition check is `12+6+12=30`. Gold `6` is the mango count. Treating orange as `6` leaves six members unassigned. I considered whether one-third referred to the original 30, but the question explicitly says remaining members; that alternative would not yield gold `6` for orange anyway. **Gold bytes and any upstream outcomes remain untouched.** Main must adjudicate the benchmark issue explicitly rather than silently changing scores or removing a case.

## Separate-axis totals

| Axis | PASS | FAIL | UNRESOLVED |
| --- | ---: | ---: | ---: |
| Semantic contract / richness | 60 | 114 | 16 |
| Truthful neutral-prefix support | 180 | 9 | 1 |
| Mathematical requested outcome | 184 | 0 | 6 |
| Mathematical narrative precision/correctness | 181 | 2 | 7 |
| Supplied token count in 150–400 inclusive | 165 | 25 | 0 |
| Separate numeric FINAL line | 189 | 1 | 0 |

**54 targets pass all six separate axes.** This conjunction is a diagnostic, not a replacement benchmark or production acceptance test. Per-SHA decisions, exact target quotes, reasons, original-question evidence, mathematical derivations, assumptions, preserved gold, and token metadata are in `ASSESSMENT.json`. `decisions.tsv` contains the manual target-by-target semantic judgments; `mathematics.tsv` contains independent derivations for all 64 tasks.

The 25 length failures consist of **18 below 150** and **7 above 400**. These counts use the packet's supplied `generated_tokens`; no tokenizer/model was invoked. Richness was not inferred from length. For example, index 7 has substantive owned reasoning and checking (semantic PASS) but 490 tokens (length FAIL).

SHA256 `b5a1b6a1665c6204e3409e0cfc4c2ed27359a9a0333bfcbfb46ac0347e3bed2f` (index 137, 512 tokens) ends exactly at “each segment of” and lacks a FINAL line. Its body correctly computes 115 miles. This is the target's own ending, not a shortened display. The packet does not supply a termination reason, so I do not claim to have proved a particular generation-cap mechanism.

## Assumptions and unresolved obstacles

- **Missing wage:** indices 6, 80, 122 (`gsm8k-train-1004`) assume the second professional earns the first professional's $15/hour. Literal cost is `630+42*r`; $1260 requires `r=15`. A counterexample `r=20` gives $1470 with the stated facts unchanged. Prior model text repeating $1260 does not establish the second wage. Numerical outcome remains UNRESOLVED; unqualified target premise fails truthful prefix support.
- **Rumor versus established effect:** indices 41, 69, 149 (`gsm8k-train-5174`) upgrade “He hears a rumor” to “Hanging upside down makes him grow.” Conditional arithmetic gives 2 hours/month. The unconditional causal prediction is not established by the problem. These three numerical outcomes remain UNRESOLVED and unqualified prefix support FAIL. A permissive fictional-premise reading could resolve this differently; this is explicitly not a claim of feedback leakage or medical advice.
- **Rounding notation:** index 56 has the correct two-foot outcome, but writes rounded thirds with exact equals, e.g. “0.5 + 2/3 = 0.5 + 0.6667 = 1.1667 feet.” Neutral support and narrative precision are UNRESOLVED on the literal-notation reading; intended arithmetic is recoverable. Indices 86 and 112 expressly mark intermediate approximations or supply an exact-fraction check.
- **Check sufficiency:** 16 targets are deliberately UNRESOLVED rather than forced into a favored binary interpretation. They have useful owned operations but generic verification language or a solve-equation/checkable-expectation boundary. Their indices and exact quotes are frozen in `SUMMARY.json` and `ASSESSMENT.json`. Main must resolve this rubric boundary openly, not retroactively infer PASS from a preferred count.
- **Ordinary mathematical models:** all 64 task entries state relevant assumptions, including full bottle-load equivalents, no draws in win counts, continuous pizza production, initially empty pool, repeated halving of folded paper, aggregate teammates' scoring, fixed rates, and idealized additive mixture volumes. These are problem-model assumptions, not verified real-world facts. I did not silently import real prices, medical effects, employment rules, epidemiology, or unprovided income rates.
- **No design-level conclusion:** the packet lacks the author-label join and experimental sampling/provenance needed for paired-effect or causal claims. The present audit supplies no such comparison. The missing external checker event is resolved as a visibility defect; token provenance, ambiguous premises, weak-check boundaries, and broader experimental inference remain distinct limitations.

## Rubric and falsification discipline

Substantive first-person plural is permitted. Index 21 owns the inverse-tip equation through “we can set up the equation,” and index 164 owns algebra through “we rearrange the formula”; both pass. “We need to find...” naming only the unknown, or “let's call this number x” naming only a variable, is not enough. Conversely, semantic failure for absent ownership does **not** mean the math or neutral prefix is unsupported.

Concrete checks need not use a second method. Rechecking specific arithmetic, reconstructing a given total, specifying a relevant unit or excluded-time check, or proposing a concrete problem-specific verification can suffice. An explicitly stated operation-result expectation may satisfy the user's alternative. A heading or generic “correct/matches the problem” alone cannot. The uncertain boundary cases remain visibly UNRESOLVED. Solved-event autobiographical statements are allowed; claims about external delivered feedback require prefix evidence. In particular, index 162's “I was then informed” refers to the **15 remaining crayons already in the question**, and index 20's observation wording refers to **thermostat changes already in the question**; neither was flagged merely for using an observation verb.

Each serious finding was challenged against its neutral question, the recalled solution, alternative arithmetic or interpretation, and favorable same-packet evidence where available. This is independent author-side reasoning, not a second model review. No reviewer/model consensus was manufactured.

## Compute recommendation and peer message

**Recommendation: no additional GPU/model/native-cell compute is needed to resolve this audit.** Main can join the frozen per-SHA evidence to author labels later, explicitly adjudicate the gold/assumption issues, and keep correctness, richness, prefix support, format, and length as separate dimensions. Do not promote exact-answer success as proof of truthful reusable-record quality. This recommendation is not a pause command or an override of the builder's standing authorization. I neither launched nor stopped any run and did not rewrite targets or gold.

**Useful message to Main:** “Independent 190-target assessment is frozen before labels. The strongest prompt-removal defect is SHA `7ccf8746...`: mathematically correct 300 does not establish the claimed external checker verdict. SHA `5535fdd2...` has correct final 7 but two false reusable subtraction rules. SHA `9ebcea83...` correctly answers orange juice 12 against preserved gold 6. Full-SHA evidence and the ambiguous/check-boundary cases are in ASSESSMENT.json; compare labels only against these frozen bytes, not a revised assessment.”

## Owned paths and evidence-only tests

All authored paths are inside the authorized analysis directory, except the single authorized worker handoff:

- `research_notes/analysis/orch_math_semantic_audit_20260914/decisions.tsv`
- `research_notes/analysis/orch_math_semantic_audit_20260914/mathematics.tsv`
- `research_notes/analysis/orch_math_semantic_audit_20260914/build_evidence.py`
- `research_notes/analysis/orch_math_semantic_audit_20260914/validate_evidence.py`
- `research_notes/analysis/orch_math_semantic_audit_20260914/ASSESSMENT.json`
- `research_notes/analysis/orch_math_semantic_audit_20260914/SUMMARY.json`
- `research_notes/analysis/orch_math_semantic_audit_20260914/REPORT.md`
- `research_notes/analysis/orch_math_semantic_audit_20260914/VALIDATION.txt`
- `research_notes/analysis/orch_math_semantic_audit_20260914/FREEZE.json`
- `research_loop/workers/MATH_SEMANTIC_AUDIT.md`

`BLIND_PACKET.json` is a read-only input, not an authored artifact. No peers' changes were reverted, staged, stashed, rebased, or merged.

Validation command, from repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 research_notes/analysis/orch_math_semantic_audit_20260914/validate_evidence.py
```

Thirteen evidence-structure tests cover packet/target hashes, all-190 coverage, unique IDs/order, verbatim quotes, preserved gold, status validity, task-expression consistency, independent axes, summary consistency, recalled-prefix identity, missing-FINAL preservation, restricted arithmetic parsing, and frozen-file hashes. They include negative tests for omission, duplication, invalid status, invented quotes, and changed gold. They do **not** test a model, validate a scientific claim, change production acceptance tests, or claim that a program independently certified subjective semantic judgments. The pre-freeze receipt has 12 passes and one intentionally deferred manifest check; the same command is rerun after freezing to exercise the thirteenth test against the actual manifest.
