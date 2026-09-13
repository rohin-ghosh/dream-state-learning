# Projected formation: independent parent/control semantic review — EDITSTOP

## Scope and conclusion

Reviewed **all8 parent messages and all8 corresponding restatements**, after Main
explicitly confirmed both native runs closed, collected once and fully released.
Each judgment traces the actual sent parent transcript, raw parent/restatement
call envelopes and matching pre-task events, not merely analyzer excerpts.

**Findings: no blanket accurate-recap/control-purity acceptance.** AUTH A0 invents
a five-answer count; OFF A1 conflates positive box outcomes with confirmed
predictions and misdescribes the quiz unit. AUTH A1 also misdescribes that unit,
although its stated box outcomes are correct. OFF A0 is substantially grounded,
with conversational ambiguity noted below. P guidance stays process-oriented,
but some diagnoses are overbroad or task-underspecified. No reviewed parent gives
a hidden rule or a new future-answer vector. These are semantic judgments about
these messages, **not efficacy, retained learning, birth harm, a launch gate or
independent certification of the whole experiment**.

## Receipt and source trace

All supplied capsule/analyzer pins match. The validation siblings are named
`.validation.json` replacing `.tgz`, not `.tgz.validation.json`.

| Artifact | Verified SHA256 |
| --- | --- |
| `/tmp/astra_projected_AUTH_20260913_attempt1.tgz` | `c435ce2e6dd6750c541788be1889ba6f4664c5c8a35d91bd8c196fb329b08805` |
| `/tmp/astra_projected_AUTH_20260913_attempt1.validation.json` | `ea6eb7f7dcc1421b430dbbc7674b065960abba04d664d46886fd6b99eb1f5cd9` |
| `/tmp/astra_projected_OFF_20260913_attempt1.tgz` | `4095540b9d7ab7a0436b3961d6e694c7d70a9eac109d4b32c20d62fa78dc145c` |
| `/tmp/astra_projected_OFF_20260913_attempt1.validation.json` | `efa0cc8bcaf5de1c38207badca3e2f653ac9988c236859483f6e38bdb7bdfa48` |
| `/tmp/astra_projected_formation_paired_analysis_20260913_attempt1.json` | `4d8bebac600412119b995556cf3943bc4b38161475bfe1c3017b38d7371a3bf3` |

Independently checked exact archive membership and **136 AUTH/140 OFF member
hashes** against their pinned validations, in memory without extracting files.
Both receipts report phase_complete/full_release=true and COLLECTED_RELEASED.
This checks supplied release evidence, not fresh remote process/GPU observation.

Plan pins: AUTH `96cb57f6d3150ed916923d329e02bea7853a8019dc4ce97522876aa667c4bb30`;
OFF `57fd3215d3e6de33c7ece8943c128a4992b2178de3e73abd01b070ae8a33e9a2`.
Both plans name source830fe675ec16bdbe4c0a5dc36ec66908b28da6ce, role pin
`2cb24cf0447d3e5a7d8e61c9a0a65658e033f2c0bfc01b4b60ae15bce437a945`, projection pin
`47564a630b166cadda546ac5ae65c79bd9ca223a8574b0cfc693d6bc0177ad19`.
These are recorded source bindings, not a new native source/tensor audit.

For both capsules, the raw source directory is
`metadata/formation/run/formation/data/`. `calls/NNNN.request.json` contains the
exact sent request; `calls/NNNN.response.json` contains the actual returned
envelope. `capture.json` contains joined events/interactions. Its hashes are:

- AUTH: `577193c504a10d7da91fb8de85817aff76b51fb4bc3f3c294c8d4d7cff0219ee`.
- OFF: `e127297d314eefa2900e3ddb25b7ba3ba44ae4b59a9d44bf5261d880049f14bc`.

| Mode/arm/lesson | Parent call | Restatement call | Pre-task raw calls traced |
| --- | --- | --- | --- |
| AUTH P0 | 0005 | 0006 | 0000–0004 |
| AUTH P1 | 0020 | 0021 | 0015–0019 |
| AUTH A0 | 0034 | 0035 | 0029–0033 |
| AUTH A1 | 0047 | 0048 | 0042–0046 |
| OFF P0 | 0005 | 0006 | 0000–0004 |
| OFF P1 | 0020 | 0021 | 0015–0019 |
| OFF A0 | 0035 | 0036 | 0030–0034 |
| OFF A1 | 0050 | 0051 | 0045–0049 |

Event joins use **both arm and eid**, since P/A share lesson/pre eids. Lesson0
uses `rule0/astra-action-projection-v1-20260913/lesson0/pre`; lesson1 uses the
corresponding `rule1/.../lesson1/pre`.

## Per-message semantic findings

### AUTH P0 — narrow quiz criticism, not missing TRY forecasts

Parent0005 says the child “did not predict the outcome of the quiz before acting”
and recommends predicting before acting. Actual TRY0000 has PREDICT F; executed
projected TRY0002 has PREDICT T. Multi-action0001 is explicitly unexecuted.
Reveal0003 also has PREDICT T; final quiz0004 supplies six labels but no separate
PREDICT line. The parent therefore must **not** be cited as correctly diagnosing
absent TRY forecasting. A narrow observation about no separate final-quiz
forecast is possible; the quiz labels themselves are forecasts, and the sent
task does not establish a requirement for an additional aggregate quiz forecast.
The claimed lost learning opportunity is process advice, not observed learning
evidence. No invented world result or hidden answer is supplied.

Restatement0006 turns the advice into “PREDICT FIRST, LEARN LATER” and a general
expectation/result comparison, preserving its broad message. It adds no specific
event or outcome. Its uppercase wording and OUTCOMECOMPARES concatenation are
observable surface features, not evidence of learning or a parent-purity failure.

### AUTH P1 — permitted process guidance, underspecified diagnosis

Parent0020 recommends starting with “a single value instead of a range of values”
and testing the simplest hypothesis before a larger commitment. Executed0015/
0016 are TRY1,2,3 and TRY4,5,6, both forecast F/outcome True. Proposed0017 contains
multiple actions and dispatches nothing; projected0018 executes TRY1,1,1 with
forecast F/outcome False.0019 reveals the quiz but does not submit an answer set.

“No simplest test before a larger commitment” is not established by a measured
cost or stated hypothesis in that transcript. “Single value” is ambiguous: a
one-argument TRY would not fit the triple interface, while a repeated-value
triple is legal and1,1,1 was already tried later. Do not turn that ambiguity into
a definite one-argument instruction or a proven arity violation. The safe finding
is **task-underspecified process advice, not a verified most-important diagnosis**.
No proposed7,8,9 outcome, quiz score or hidden rule is fabricated.

Restatement0021 retains the simplest-hypothesis theme in PREDICT/COMPARE-tagged
prose; it drops the single-value claim and the concrete events. This is immediate
rephrasing, not successful execution, retention or usefulness.

### AUTH A0 — definite wrong answer count, repeated by the child

Parent0034 correctly recaps observed True for1,2,3 and10,11,12, a six-label quiz
requirement and the displayed0.50 score. It falsely says **“You gave five answers.”**
Actual final quiz0033 is `ACT: QUIZ T,F,F,T,F,F`: six labels.0032's INVALID text
belongs to the reveal request, not to a five-label submission.0030's proposed
4,5,6 and7,8,9 actions were unexecuted; importantly, the parent does **not** claim
outcomes for those proposals.

Restatement0035 repeats “I provided five responses” and retains the correct two
True outcomes and half-correct score. This demonstrates propagation of the
parent's erroneous recap into the immediate restatement, not persistent learning.
**Accurate-only neutral recap is violated by the parent**, independently of the
child's PREDICT prefix.

### AUTH A1 — correct executed outcomes, misleading quiz unit

Parent0047 correctly names executed1,2,3;4,5,6;10,11,12 and their True outcomes
(0042,0043,0045). It does not count proposed7,8,9 at0044 as executed. Describing a
plan to quiz is not inventing a completed quiz:0046 is a reveal, with no later
scored answer in this pre-task.

The phrase **“6 answers (T/F) for each set of numbers”** is misleading as written:
the visible reveal lists six triples requiring one Boolean each, not six answers
per triple/set. If intended to refer to the entire six-triple panel it is
imprecise, not a newly observed rule. Restatement0048 makes the unit/role confusion
more explicit by saying it planned to ask the box “six true/false questions for
each set of numbers.” Do not certify this as an unqualified accurate recap, but
also do not misreport it as fabricated successful execution of the rejected
proposal or as an invented quiz score.

### OFF P0 — real local forecasting omission, overbroad opening

Parent0005 says the child “didn't predict before acting” and should predict before
each combination.0000 and0001 both explicitly predict F before their TRYs;0002
executes TRY2,4,6 without a prediction. Thus the “each combination” lesson has a
**real local basis**, while a blanket reading that no predictions occurred is
false. This is not the AUTH P0 situation. No world result, rule or future answer
is invented. Restatement0006 accurately generalizes the process advice without
adding an event or a claim about how many original forecasts were absent.

### OFF P1 — real local omission; learning diagnosis exceeds observations

Parent0020 again says there was no prediction before action and no formulated
hypothesis, then claims the child “isn't learning from the surprises and forming
a theory.”0015/0016 explicitly predict F;0017 executes TRY7,8,9 with no forecast.
There is no explicit hypothesis prose in this sent transcript. A recommendation
to forecast consistently and articulate hypotheses is within P's process scope;
the blanket no-forecast wording is overbroad, and absence of internal learning
cannot be established from the observed dialogue.

Restatement0021 keeps the general predict/compare lesson but does not repeat the
strong “isn't learning” assertion. No fabricated event or hidden answer appears.

### OFF A0 — substantially grounded recap, not a universal purity certificate

Parent0035 recaps multiple combinations, the six-label quiz requirement and50%.
Those actions and the0.50 displayed outcome occur at0030–0034. “Got some correct
answers” is loose acknowledgment: positive box outputs or some correct quiz
labels are available referents; it should not be upgraded into correct prior
forecasts, since the first two forecasts are F while outcomes are True. “Best
guess” is conversational characterization, not directly logged internal state.
No definite fabricated action, numeric result or new strategy is identified in
this message. This is the clearest grounded A recap of the four, with those
qualifications rather than an automatic purity PASS.

Restatement0036 retains the50% and six-label requirement. “I guessed the rest”
adds an unsupported known-versus-guessed distinction, but is the child's own
paraphrase, not newly supplied parent leakage. No acknowledgment-only restriction
was imposed; child reflection is not itself an A-control violation.

### OFF A1 — positive outcomes are not confirmed predictions

Parent0050 says the box “confirmed your guesses for numbers1,2,3,4,5,6,and7.”
Actual submitted units are triples1,2,3;4,5,6;7,8,9 (0045–0047), not seven
individual-number trials. The first two explicit forecasts are **F** and their
observations **True**, so “confirmed your guesses” is false if referring to those
forecasts. The third prediction is absent, not confirmed. The True box outcomes
are real; the error is treating them as successful predictions and changing the
unit of recap, not inventing those True observations.

Its4/6 and displayed0.67 quiz result are consistent with0049 and should be
preserved as correct parts of the recap. The “six ... answers for each set” wording
repeats the quiz-unit problem above. Restatement0051 repeats the confirmation,
individual-number and per-set wording alongside the correct score. **An
unqualified accurate-only neutral recap is not supported.**

## Control, visibility and interpretation boundaries

- All8 parent raw envelopes report the **same base-only loader identity** and no
  LoRA request. AUTH restatements report its child adapter; OFF restatements have
  no adapter. These are pinned recorded identities, not my tensor audit.
- P prompts share one identical instructional prefix across modes/lessons; A
  prompts share one identical neutral prefix. P explicitly asks for one process
  mistake, while A permits only accurate already-visible recap and forbids new
  strategy, hypotheses, recommendations, evaluated corrections, invented facts,
  hidden rules or future answers. Parent messages are45–77 whitespace-delimited
  words, all below the requested120; all ask/direct restatement.
- No hidden-rule statement or new future-answer vector was found in any parent
  message. Actual public feedback is not hidden-answer leakage. Nevertheless,
  absence of hidden answers does not make erroneous A recaps neutral/accurate.
  No P-versus-A treatment-validity/efficacy conclusion is warranted from this audit.
- Every restatement request is exactly the parent message plus the fixed own-word
  2–3-sentence request, **without the original task transcript**. Error repetition
  therefore cannot be interpreted as the child independently auditing that
  transcript. AUTH's tags/capitalization and OFF's plain prose are descriptions,
  not causal birth or persistent-learning results.
- The reviewed AUTH rejected proposals are explicitly marked unexecuted in the
  actual parent-visible transcripts. A0/A1 parents correctly avoid granting those
  rejected triples new box outcomes. It would be wrong to transplant the earlier
  formation's “unexecuted proposal treated as completed” diagnosis wholesale
  onto these messages. Their present errors are the specific ones listed above.

### Main's action-side caveat — attributed, not independently redone

Main reports AUTH P/A rule1/pre ticks1–3 have identical prompts/seeds, while tick4
differs only in the public global call marker0017 versus0044 (same seed), with
projected TRY1,1,1 versus10,11,12. Main identifies a **global-call-marker prompt
confound**. I did not repeat that action comparison, rerun inference or diagnose
determinism. These pre-parent differences are not evidence of parenting or of a
deterministic backend failure; nor does this audit measure how much the marker
caused the difference. Each parent must be judged against its own actual sent
transcript. Do not assume matched pre-parent trajectories, replace outcomes or
retroactively repair the completed v1 evidence. Main owns any prospective fix.

## Checks performed and limitations

Read/hash checks used `sha256sum` and in-memory Python stdlib `tarfile`, `json`,
`hashlib` only. For the16 parent/restatement calls and their pre-task source calls:
raw request/identity and returned envelope equal the joined capture fields;
loader identities agree; journal time spans nest inside capture spans; all
source events precede their parent. The events reconstruct each parent-visible
transcript **byte-for-byte**, including UNEXECUTED_PROPOSAL, PROJECTED_ACTION,
original response whitespace and only recorded OUTCOMEs. Parent/restatement
texts equal the interaction summaries. All16 selected output-ID lengths are
below their recorded caps; no tokenizer decoding or EOS claim is made.

The analyzer was not executed and its action/record scores were not audited;
its parent-purity field remains an unreviewed Main-judgment marker, not this
review's semantic conclusion. No task/record aggregate recount, world-rule
evaluation, experiment code import, native model/GPU/network/Git operation,
live-output read or source/runtime change occurred. Final vacancy is external
collector evidence, not independently re-observed. This Markdown is the sole
written artifact; original transcripts and completed v1 remain untouched.

Reviewer disclosure: I previously authored downstream writer/learning helpers,
probe tests and the projected-runtime CPU tests. This is a separate semantic
pass, **not blinded or wholly independent of the project**; Main supplied pins
and the marker-confound finding. No Q0/generalG3/P1/G5/H1/H2, retained benefit,
clean-ancestry, useful-self-learning or freeze claim follows. The recorded public
revision binding is prospective and explicitly preserves historical labels/no
clean ancestry; source-authored birth remains NOT CLEAN. Main retains final
control-purity adjudication and integration. **EDITSTOP.**
