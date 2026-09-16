# R136 interface sensitivity — diagnostic only, September 16, 2026

**Canonical results are unchanged: FULL4/16 and BASE0/16 at every stage.**
The alternate extraction below is post-hoc, not a replacement benchmark score.
No provider/GPU call, new task generation, training, admission, replayed model
request, or frozen-source/run modification occurred. Raw responses stayed on node5.

| Model / stage | Strict passes / planned | Diagnostic finite-check passes / planned | Complete |
| --- | --- | --- | --- |
| FULL draft | 4/16 | 4/16 | 15/16 |
| FULL actual feedback | 4/16 | 4/16 | 15/16 |
| FULL neutral review | 4/16 | 4/16 | 15/16 |
| BASE draft | 0/16 | 4/16 | 16/16 |
| BASE actual feedback | 0/16 | 6/16 | 16/16 |
| BASE neutral review | 0/16 | 5/16 | 16/16 |

## Why BASE has 48 parser failures

All48 complete BASE outputs are single-line mappings with **an unquoted
expression value**, structurally `{"expression":sum(...)}` rather than
`{"expression":"sum(...)"}`. All45 complete FULL outputs use a quoted string.
There are no fences or multi-line reasoning transcripts among these outputs.
FULL's other3 outputs (task index3, calls22–24) are truncated and excluded from
alternate extraction even if a prefix looks repairable.

AST extraction selects exactly the existing value, without adding/removing
helpers, changing constants, renaming arguments or searching candidates.
Only the existing R133 safe expression interpreter executes it. Each selected
expression is fixed before any saved verification-input expected comparison.

BASE draft has4 diagnostic passes,1 executable check failure,4 non-integer
returns, and7 sandbox rejections (3 wrong helper arities,3 non-integer constants,
1 unsupported operator). Formatting is therefore a large but not exclusive
failure source. FULL and BASE share the same four draft-pass tasks:0,4,8,12.

## Why genuine feedback yields no strict correct revisions

Every BASE feedback prefix contains the real **parser error**, not an executed
candidate result or a semantic correctness verdict. BASE never fixes the missing
quotes, so all revisions remain strict parser failures. Nonetheless it changes
the expression AST on4 feedback tasks and5 neutral tasks;12 and11 outputs,
respectively, are byte-identical to the draft.

Diagnostic BASE corrections occur on tasks1 and13 after feedback; neutral also
corrects task13. Thus the paired diagnostic contrast is **one feedback-only
pass, zero neutral-only passes among16 tasks**, not6 independent successes or
proof of feedback-caused learning. The diagnostic tests remain finite and post-hoc.

FULL changes4 expression ASTs after feedback (tasks2,11,14,15) but no failed task
passes. Tasks11 and15 move from sandbox rejection to executable wrong answers.
Neutral changes2 ASTs and recovers no task. Eleven complete FULL outputs are
unchanged after feedback, versus13 after neutral; one triplet stays excluded.
The10 executable FULL draft probes supply an observed output without an expected
answer;5 draft sandbox failures supply errors, and1 truncated draft supplies a
parser error. These observations describe limited feedback information and actual
response behavior; they do not establish the model's internal cause.

## Sanitized structural examples (N hides every numeric task constant)

- Missing JSON quoting: `{"expression":sum(...)}` versus `{"expression":"sum(...)"}`.
- BASE task1 draft: `clip(affine(values,N,N),-N,N)` returns a list. Feedback:
  `sum(unique(clip(affine(values,N,N),-N,N)))` passes saved checks. Neutral:
  `sum(clip(affine(values,N,N),-N,N))` is executable but omits deduplication.
- BASE task13 adds `sum(unique(...))` in **both** forks and passes diagnostic checks.
- BASE task5 adds only `sum(...)` in both forks and remains wrong; task9 feedback
  deduplicates input values rather than the clamped outputs and remains wrong.
- FULL tasks11/15 replace invalid expressions with executable compositions that
  still fail checks. The reducer does not invent the missing correct composition.

Each N is an independent placeholder, not a shared variable or runnable code.
`DIAGNOSTIC.json` binds10 sanitized examples to raw UTF-8 hashes; it also contains
all96 compact cells,32 task/model revision records, and paired model aggregates.
On the15 common-complete task pairs, draft diagnostic successes are4 both-pass;
feedback adds2 BASE-only passes and neutral adds1. No FULL-only diagnostic pass.

## Evidence and tests

- Reduction time:2026-09-16T02:35:24.877985Z.19 local and19 native CPU tests passed.
-393 artifacts rechecked, including96 CALL/INTENT/PUBLIC/VERIFY sets, task and
  exclusion pins, author reduction, and terminal hashes. Strict receipts and all
  actual-feedback/neutral prefixes were independently rederived from saved bytes.
- Source pins and inputs remained stable before/after the audit. The393 count
  does not replace the prior author's425-artifact proof; that proof is hash-bound.
- Exact provenance and commands: `MANIFEST.json`. No benchmark or parser change
  is proposed for automatic adoption; any future interface should be fixed before
  collecting a new matched comparison. No Level2/3 or skill-acquisition claim.
