# PERSIST-MATH terminal L1 screen — September 14, 2026
Final answer success: RICH **0/16**, TERSE **2/16**.
Answer + checked nontrivial record: **0/16 vs 0/16**; admitted targets **0**.
Native calls: **32/32 per arm, 64 total**; fits/updates **0/0**.
Node: **A100 physical GPU6 RICH / GPU7 TERSE**.
Native root: `/localhome/local-rohing/data/orch_persist_math_20260914_attempt1`.
Reduction: `research_notes/analysis/orch_persist_math_20260914_attempt1/REDUCTION.json`.
Release: GPU7 PASS22:09:32UTC; GPU6 detached PASS22:18:01UTC.
Conclusion: retire this bounded recipe; no record-memory or sleep benefit measured.
Publication-order SEQ requested from Main after terminal reduction; none invented.

## Observation and control

| Metric | RICH | TERSE |
|---|---:|---:|
| First-turn answer success | 0/16 | 1/16 |
| Final answer success | 0/16 | 2/16 |
| Final answer + nontrivial checked record | 0/16 | 0/16 |
| Corrected joint successes | 0/16 | 0/16 |
| Tasks receiving prior accepted records | 0/16 | 0/16 |
| Native calls | 32 | 32 |
| Truncated calls | 16/32 | 0/32 |
| Generated tokens, including terminal EOS | 11,489 | 1,105 |
| Generated-token range per call | 13–512 | 14–164 |
| Calls with150–400 generated tokens | 5/32 | 1/32 |
| Actual prompt tokens, total | 15,763 | 7,336 |
| Largest actual prompt | 790 | 261 |
| Native wall seconds | 607.48 | 119.41 |
| Fits / updates / admitted targets | 0/0/0 | 0/0/0 |

Both frozen37ec children received the same16 tasks and checker/action schema,
greedy decoding, two-turn maximum,512-token generation ceiling and their own
record store. Prompt richness was the manipulated condition. Realized compute
was not equal: RICH generated about10.4 times as many tokens. Native assigned
time sums to0.202 GPU-hours, including model loading/checks. This is not a
training comparison, a fitted rich-vs-loss-off pair, or an unseen-family test.

## Evidence and falsification

`raw/RICH/RESULT.json`, `raw/TERSE/RESULT.json`, both DATA.json files and all64
CALL receipts replay exactly through `gpu/orch_persist_math_reduce.py`:
original call order, pre-action messages, native response joins, deterministic
oracle decisions, record-store transitions and all16 denominator tasks/arm.
REDUCTION.json records every call hash. Final base and adapter state checks
pass for both native processes. Author-side replay is NOT independent
verification; no VERIFIED or promoted result is claimed.

RICH failures comprise16 truncated responses,14 action-projection failures and
two parsed-but-unsuccessful submissions. TERSE has31 parsed answer/record
failures and one overfull-record-list rejection. No endpoint, truncation or
invalid record was excluded from the task denominator. Length alone did not
solve the task or establish reusable records. As an adversarial check on a
pure formatting explanation, sampled prose contains explicit incorrect modular
remainders and false cycles; conversely one sample gives a genuinely correct
fixed-point explanation despite failing the action/record contract.

SEMANTIC_REVIEW.md binds a substantive six-call illustrative RICH review:
1PASS/5FAIL/0UNRESOLVED, not an exhaustive32-call review. No semantic label is
inferred from headings. There are no outcome+record-qualified candidates to
admit; failed raw attempts remain intact. Parsed-prose token metrics in the
reduction are conditional on strict action projection: the many unparseable
rich responses have missing, not zero, prose-token accounting. Generated-token
counts in the table do not depend on projection and do not establish richness.

## Interpretation, assumptions and obstacle

The minimal curriculum exists:128 unique L1 instances, four recurrence blocks,
and an exhaustive finite-domain checker for child-authored affine-power records.
The first bounded native feasibility screen failed to bootstrap even one
accepted nontrivial record. **The record stores never became populated.** Thus
this screen does not demonstrate even warmed in-context record competence,
much less a learner changed by sleep. The supported null is this recipe under
the frozen prompt/action/budget contract, not the record-learning hypothesis.

Credible alternatives include initial tasks being too demanding before a first
record is acquired, an interface unfamiliar to the child, long step-by-step
enumeration exhausting the budget, and weak modular arithmetic. No alternative
is isolated here. A correct finite-domain identity would certify only the
specified map/modulus, never an unrestricted theorem. The actor is the exposed
portable DEV37ec lineage, not a clean pretraining baseline. Local checkpoint
file binding is not proof of an independently verified upstream HF revision.

Confidence is high in the bounded replayed counts and low in any general
claim about mathematical learning, optimal curriculum or downstream H1/H2.
No retention, held-family transfer, parent contribution or sleep effect was
measured; no scientific claim enters the paper on this result alone.

## Operational caveats, preserved

Published native source226fc269e364ec3ef094a76ba2d0209ba53b09fd; archive SHA256
4844afe53c0c2a189843da0cae3ebfd87db923a0f610cdd461e61c4a48c16bb3.
Portable manifest5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469.
PreGPU packet042fa66d reached origin throughca8f8b2c before launch; the initial
push rejection stopped launch until reconciliation. No force/reset/stash.
The preGPU heading rounded to22:07 while the edit clock was22:06:42UTC;
publication was verified and launch occurred22:07:25UTC. This ordering is
explicit, not silently repaired. Actual A100 lease ends2026-09-27T05:05UTC;
the guardian's2700s bound lay below lease minus6h.

The native wrapper's precheck used len(tokenizer mapping), a fail-open token
accounting bug relayed by PERSIST-CODE. The Engine independently recorded real
flat-token counts. Every one of64 captured calls passes the reducer's strict
actual prompt+512<=2048 and actual generation<=512 checks: maxima1302/773 with
reserved output. Local repairbff02a9d explicitly requests return_dict=False,
rejects mappings, and has26 passing CPU tests including boundary/tamper tests.
It was not substituted into the immutable running archive; no restart occurred.
Initial prelaunch CPU suite was21 tests, not retroactively26.

RICH native exit0/COMPLETE was followed by guardian exit1 because its final
resource scanner encountered an unreadable transient sshd process. The failed
scan remains in `raw/RICH-launch/resource_after.json`; no process was touched
and no service exception was relaxed. A fresh detached scan passed22:18:01UTC
with no owners/unresolved processes (`gpu6-release-detached.json`). TERSE's
guardian exit0 and release scan passed22:09:32UTC. Both GPUs are released.

## Compute recommendation and peer message

Deallocate this recipe after its clean bounded scientific null. No fit, prompt
retry, larger cap or new native arm is queued. Off-the-shelf MATH-RICH should
continue independently. A future record-visible versus record-hidden test
would be discriminating only after child-authored records actually accumulate;
the current zero-record stores make that sequel uninformative. Revisit only
with a distinct preregistered acquisition mechanism, not more dose on this run.

Peer message for Main to route: separate arithmetic/action success, universally
checked record success, semantic explanation and token-length measurements.
A long explanation can contain wrong remainders; a correct contextual answer
can still supply no reusable record. Count actual flat token IDs, not the
length of a tokenizer mapping. This worker never blocks an off-the-shelf pool.

## Exact future scopes and consolidation prompt — not run

L1mining PM_AFFINE_POWER_V1; heldL1validation PM_AFFINE_WORD_V1 (distinct-map
ordered composition), reserved/unmined. L2proposal PM_CONGRUENCE_JOIN_V1
(compatible congruence joins across tasks) and heldL3proposal
PM_LINEAR_RECURRENCE_V1 (second-order modular recurrence records/deployment)
remain unadmitted and ungenerated until Rohin rules.

Proposed same-child consolidation instruction, not a solution corpus or an
executed compiler: “Using my visible experience and checker feedback, identify
what I actually learned from successful attempts and corrections. Explain
which observation supports each reusable record, its scope, and a testable
expectation on a fresh instance. Keep source task/turn references; state any
uncertainty. Do not claim that an unchecked generalization was verified.”

Later guided experience/reflection plus learned consolidation would target only
the child's outcome-successful, semantic-passing outputs. Student prefixes and
parent/feedback tokens receive no target loss; parent is ABSENT at evaluation.
Compare continued sleeps against a frozen same-child twin and an unparented
twin, separately controlling record visibility. Parent-free collection is not
a prerequisite. None of these cycles or comparisons happened in W1.
