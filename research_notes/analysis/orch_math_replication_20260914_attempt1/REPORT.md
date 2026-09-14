# MATH-REPLICATION — independent terminal report

Completed September 14, 2026 UTC. Assignment f0f53343. All three native shards
completed successfully; this is not an abort, missing-denominator result, or
clean math null. No prior math outcome values or prior authors' conclusions
were read, before or after the independent protocol/analysis freeze.

## Strongest supported result

**Rich prompting improves strict checked-answer performance on this fixed
fresh cohort: 31/32 versus terse10/32. Semantically acceptable own-record
outputs exist, but only3 of31 record calls pass the frozen full-text rubric.**
Across rich and own-record candidates together,6 rows across5 tasks pass.
Thus the prospective combined strong-support criterion is **not met**:
the positive checked-answer gap does not supply the required8 semantic-PASS
rows. No training pool, fit, scaling run, or new-family claim is promoted.

| Frozen family | Rich initial | Terse initial | Fixed denominator |
|---|---:|---:|---:|
| percentages | 8 | 3 | 8 |
| work_rates | 8 | 4 | 8 |
| fractional_quantities | 8 | 2 | 8 |
| group_accounting | 7 | 1 | 8 |
| **Total** | **31** | **10** | **32** |

The absolute difference is65.625 percentage points (96.875% versus31.25%).
Paired discordances are21 rich-only and0 terse-only;10 tasks pass both and1
fails both. The frozen exact two-sided McNemar probability is
9.5367431640625e-7. This is a nominal paired test on this DEV cohort, not a
population-wide generalization, clean-transfer or learning claim. Family
counts are descriptive; no multiplicity-adjusted family superiority claim
is made. Corrections and records never replace an initial answer in this table.

## Failure diagnosis without rescoring

Of22 terse failures,15 have a parseable but wrong numeric final answer and7
violate the final-line numeric contract. All32 terse responses terminate;
none is truncated, and they use2–8 generated content tokens. The64-token
terse cap therefore did not censor this run. Two of the seven format failures
contain the intended number with forbidden units/percent signs; the other
five also contain wrong numbers. These observations do not change any score.
The result is not explained solely by formatting or token-limit truncation.
Nevertheless the conditions differ in guidance, message role and generated
explanation length; this is not a matched-token causal decomposition.

The sole initial-rich failure is gsm8k-train-4979: it reports130 hours for a
whole-semester calculation instead of the fixed gold52 for the conventional
halfway-midterm interpretation. The correction repeats130 and speculates
about checker format, without a meaningful mathematical revision. Both failed
attempts remain preserved; the task remains in denominator32. Two own records
truncate at512 tokens and lack the required final line; neither is a candidate.

## Full-text semantic assessment

All47 candidates were read in full with their questions. Every judgment binds
the exact target SHA256, quoted evidence, an explicit reason, and all six
substantive axes. No heading/keyword classifier or length-based semantic
admission was used. One mistyped evidence quote was caught by exact-span
validation and corrected without changing its FAIL judgment; the initial
notes are preserved in the local artifact directory.

| Call kind | Calls | Checked successes | Candidates | Semantic PASS |
|---|---:|---:|---:|---:|
| terse | 32 | 10 | 0 | 0 |
| initial rich | 32 | 31 | 21 | 3 |
| correction | 1 | 0 | 0 | 0 |
| own record | 31 | 29 | 26 | 3 |
| **Total** | **96** | **70** | **47** | **6** |

There are41 semantic FAIL,0 unresolved row judgments, and0 unreviewed
candidates. These are not41 arithmetic errors: overlapping rejection axes
include30 failures of substantive first-person account,22 lacking a concrete
check/checkable expectation,4 generic-padding failures, and2 unsupported-premise
rows on one task. All47 contain recognizable reusable mathematical operations;
that alone does not meet the full contract. Ten correct initial-rich responses
are shorter than150 tokens, and three correct records exceed400 tokens; these
are retained but never bypass candidate admission.

The three passing own records are:
- gsm8k-train-6637: part-to-whole division and count scaling, with an explicit
  first-person consistency check of20% versus100% capacity.
- gsm8k-train-4531: grouped page/photo products and aggregation, with owned
  numerical verification of both products and their sum.
- gsm8k-train-6433: successive fractions of the remaining crayons, with
  first-person verification of the changing base and subtraction steps.

Three initial-rich rows also pass: gsm8k-train-6637, gsm8k-train-1745 and
gsm8k-train-4455. Their explicit unknown-containing equations provide
checkable expectations; an independent second solution was not required by
the frozen rubric. The month-conversion assumption in1745 is explicitly
conditional, not treated as a supplied fact. Mere phrases such as "we need"
or a heading called "Concrete check" were not enough to establish the axes.

A substantive negative example is gsm8k-train-1293: the rich answer asserts
"Since they are senior citizens" although the question never establishes the
buyers' eligibility. Its own record applies the discount unconditionally.
Both match the numeric gold and both fail semantic admission. Correct final
numbers do not validate invented premises.

## Assumptions, gold ambiguity and falsification

The cohort is32 distinct public GSM8K train questions, eight per original
family, selected with the independently frozen seed after excluding only the
original32 task IDs. No original response or reference rationale was used.
The source is public; pretraining contamination and upstream revision identity
remain unresolved. Frozen-model prompting success is not adapter learning,
new-family transfer, H1/H2 confirmation or evidence of hidden reasoning.

Before reading selected gold values or any own native response, the
question-only audit recorded six wording/default-assumption risks: senior
eligibility1293; growth-versus-duration wording181; weeks-per-month1745;
doll antecedent4818; active-versus-cumulative cases184; and midterm timing4979.
These are not all established gold errors. All gold values are numerically
parseable, but unique semantic interpretation is not guaranteed. No gold was
repaired, rationalized from outcomes, or dropped; no denominator changed.
These source risks are distinct from the zero unresolved *row* judgments.

The frozen clean nonpositive-gap falsifier did not occur: the paired gap is
positive. The combined quality criterion did fail because6<8 semantic-PASS
rows. This rejects treating this run as a sufficiently productive admissible
record collection, not the broader thesis. Semantic decisions are those of
this independent assessor and remain available for a separate reader's audit;
no Fable outputs or checks were run or consulted.

## Provenance, safety and compute

PreGPU publication46a5e8b8 was pushed and verified before launch. The original
protocol, cohort, model runner and independent analysis-policy bytes stayed
unchanged through generation and reduction. Only a documented operational
guardian repair was made before native: read-only privileged /proc inspection
and an independently observed, executable/command/UID/PID/start-time-bound
nvidia-persistenced identity. Unknown ownership still fails closed; native
guardians run unprivileged, and no process was killed.

Only node3 physical GPUs2–4 were used through existing gpu/ovx2_ssh.sh. Fresh
UUID/PID+/proc CVD scans and live child CVD receipts bind the actors. Exact
portable manifest5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469,
base/tokenizer inventories, runtime versions, mounted named_parameters adapter
hash37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0 and unchanged
base checks all pass. No PEFT-export-key surrogate hash was used. Post-run CPU
validation reconstructs all96 exact original prompts and masked student
prefixes, verifies prompt lengths and token budgets, and reproduces every raw
target from its generated token IDs. All16 targeted CPU tests still pass.

Shards finish at22:51:06–39 UTC after263.29–297.18 seconds each, approximately
0.232 aggregate guardian GPU-hours, versus the2.25 GPU-hour maximum. All96
calls are preserved. The assigned GPUs returned to1MiB idle usage. No fitting,
lease modification, scale-up, parent gate or Fable gate occurred.

**Compute recommendation:** no additional native calls or fit/scale from this
assignment. These cells are finished and available for PI reuse. Prioritize
CPU/reader audit of semantic yield and source assumptions before proposing
any separately frozen follow-up; do not infer adequate training material from
the answer gap or reproduce generic padding to reach a row target.

## Evidence pointers

- Frozen protocol: ../orch_math_replication_20260914_protocol.md.
- TASKS.json SHA256:
  42ec9ca3605579ced04941ae2518fe3dd9638d7dd5e680fa856e71cd4da38dc0.
- Native source archive SHA256:
  25a0d9b4816a3ffcc5e5ac9d3e160493a60f04c1f91a93dedd577029d01e7030.
- Native terminal archive SHA256:
  388daa11e102dff7b30aac896967ea49885ff046be1d76939d3aba194b15aa52.
- Exact native rows/receipts: native_terminal/;126 file hashes in
  final/NATIVE_FILE_SHA256.json. Full archives and operational capture history
  remain in /data/home/rohing/dream-state-orch/gpu_artifacts_local/orch_math_replication_20260914_attempt1.
- Independent counts: final/INDEPENDENT_REDUCTION.json; diagnosis and compute:
  final/DIAGNOSTICS.json; reduction provenance: final/REDUCTION_PROVENANCE.json.
- Exact serialization verification: final/TOKEN_PROVENANCE.json; final CPU
  tests: final/FINAL_CPU_TESTS.txt; publication file bindings: EVIDENCE_INDEX.json.
- All full texts and reviews: final/FULLTEXT_REVIEW_QUEUE.json,
  SEMANTIC_MANUAL_NOTES.json, SEMANTIC_REVIEWS.json and
  final/BOUND_SEMANTIC_REVIEWS.json. Initial/blocked/provisional artifacts remain
  separately preserved and do not replace terminal evidence.

## Peer message to Main / PI

MATH-REPLICATION completes blind to prior math outcome values: native rich31/32
versus terse10/32, all four fixed family gaps positive, zero runtime failures.
Full-text review of47 candidates yields6 PASS rows across5 tasks, including
3 own records; the>=8-row combined threshold is not met. Seven terse format
failures do not explain the whole gap, and no terse response was truncated.
Unsupported senior-eligibility premises and failed midterm correction are
preserved. No fit/scale recommendation; physical2–4 are idle for reassignment.
