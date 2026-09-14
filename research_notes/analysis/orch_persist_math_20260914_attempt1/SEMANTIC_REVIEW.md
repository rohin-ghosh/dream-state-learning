# Author-side text reading — September 14, 2026

Six diagnostic RICH calls read substantively against their full recorded
pre-action messages and child text: 1 PASS, 5 FAIL, 0 UNRESOLVED. This is a
post-observation illustrative sample, not all32 rich calls, not an independent
review, and not evidence that the other26 calls fail semantically. All32 terse
raw responses were also read: they are action-only, as requested by that arm;
none supplies explanatory first-person reasoning. No terse target is admitted.

There are zero outcome+nontrivial-record-qualified episodes in either arm, so
there are zero candidates for target admission independently of these sampled
semantic judgments. A semantic PASS below does not override action failure.
The source file hashes below are also in REDUCTION.json, which binds the full
native messages and responses. No rewritten explanation or rescued action is
created. No headings, token count or parser result determines a semantic label.

## RICH CALL_000 — FAIL

Task PM_POWER_B0_I00, turn0. SHA256
bb97718fe94ba31997106f10fa3b022c0079d3504aa5bc8689acad23a3767ad8.
The displayed iteration from x0=2 through x11=12 is correct and tied to the
requested goal. However, the later assertion “this task does not cover more
than one step” contradicts the explicitly requested11 steps and its own work.
It pivots to a one-step record rather than a justified reusable multi-step
relation. Separately, the response truncates at512 tokens; truncation is an
execution failure, not the reason for the semantic falsehood judgment.

## RICH CALL_001 — FAIL

Task PM_POWER_B0_I00, turn1. SHA256
b7c1ff784947c65689302705a3f7585af82dce3a66266651a74b10a253ba42e0.
“This record captures the recurrence relation for one step” is mathematically
true, and the visible previous work supports answer12. But this correction
does not connect the requested11-step goal to a reusable multi-step relation
or state its testable consequence; it repeats the initial rule and action.
It lacks the substantive goal-connected explanation required of a rich
correction. Its malformed FINAL marker and extra modulus field are separate
interface failures, not content-label heuristics.

## RICH CALL_006 — PASS, not an eligible task

Task PM_POWER_B0_I03, turn0. SHA256
c7671a1ae7d82311ca8c9b0629fb4395f9a98e9104946602d4d11778ee36751c.
The child establishes that the given initial value6 maps back to6 under the
specified map, connects this fixed point to the59-step goal, and checks more
iterations. “It appears that x_t = 6 for all t” is supported here by the exact
one-step fixed-point calculation, not just an unsupported pattern assertion.
Evidence, goal and checkable expectation are materially grounded. Nonetheless
the emitted FINAL-colon action is outside the frozen interface and contains
no reusable universal record. This correct contextual explanation is NOT a
verified finite-domain lemma, completed action, training row or learning slope.

## RICH CALL_008 — FAIL

Task PM_POWER_B1_I00, turn0. SHA256
9c9b224dbb44971436fd5fe5669294ec3f5477de240e2b821ed91521f5f8e455.
The assertion “95 mod 19 = 10” is false: the remainder is0. Several later
remainders and the claimed cycle consequently fail. This is substantive
mathematical error, independent of the response's512-token truncation.

## RICH CALL_010 — FAIL

Task PM_POWER_B1_I01, turn0. SHA256
3adcf2f8fe5de55a06f04146f4d522cd8e55eb65bd91311818952e1b32975fb8.
The claimed first remainder74 mod19=7 is false (17), as is53 mod19=7 (15).
The child then states “the sequence becomes constant with x_t = 7,” which
the actual one-step map contradicts. Its two-step record simply repeats the
one-step multiplier/offset and is not justified over all residues. This is a
341-generated-token example where length and fluent reasoning do not make the
content pass. JSON fences and action-marker failures are separate issues.

## RICH CALL_012 — FAIL

Task PM_POWER_B1_I02, turn0. SHA256
be87a72b201d0c679a00ddb457893ac4af0ad02a47a638661e0b8a80067c7c74.
The child asserts “123 mod 19 = 12”; the remainder is9. Although12 is itself
a fixed point of the map, that does not show the supplied initial17 reaches
it. The claimed target answer and repeated one-step-as-two-step record are
therefore unsupported. A plausible fixed-point explanation is not evidence
of the actual trajectory from the stated initial condition.
