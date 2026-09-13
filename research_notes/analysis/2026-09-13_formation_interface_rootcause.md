# Born AUTH RuleGame formation: interface root-cause audit

Date: 2026-09-13 UTC. This is a read-only audit of the released exploratory
AUTH formation capture, not a reinterpretation of SEQ-120, a repair to Q0, a
parenting result, or authority to run or change an experiment.

## Evidence and verdict

I inspected the complete 28-call native capture at
`astra_born_rulegame_formation_seed0_20260912_attempt1`. The capture SHA-256 is
`b7ae03b25b38dbc77547143e2ec6291891866a9dfd7c5637eb5886354b96f78b`;
its released capsule SHA-256 is
`7aaf3583ca1052914954bf4cf609b73bbb258c47cdd1d2ebbcd23e44ad75eb3c`.
The stored role replay closes all 28 calls and reproduces all events.

**Verdict:** the parser is not defective. All six rejected generations violate
the registered one-action RuleGame interface exactly as reported. The dominant
failure is a child-policy/output-schema incompatibility. Four events are two
deterministically repeated attempts to emit an entire action sequence in one
turn, before either arm receives a parent. The other two are A-only failures in
which an AUTH-born restatement dominated by birth-dialect labels is inserted
into the apply prompt and the child continues that label stream instead of
issuing a RuleGame action. This is prompt-conditioned cross-schema
interference. The original bridge review predicted this class of failure before
the run (`astra_birth_level2_bridge_review_20260913.md:5-11`).

The run does **not** causally isolate whether the four pre-parent sequence
bundles come from the base policy, the AUTH adapter, or their interaction,
because there is no adapter-OFF child under the same requests. It does show that
the actually served born child is not reliably compatible with this interface.
The A tag continuation is strongly localized to the served child path (the
parent was adapter-OFF; restate/wake/record were AUTH), but an OFF-child
restatement sibling is still needed to assign the incremental cause to LoRA.

## The six events, without collapsing duplicates

| Calls | Arm/task | Raw behavior | Parser result | Classification |
|---|---|---|---|---|
| `0001`, `0019` | P and A, rule0 pre, tick 2 | Three blocks: `ACT: TRY 3,6,9`, `ACT: TRY 1,3,5`, `ACT: QUIZ ?` | `multiple action markers` | Same prompt, seed, adapter, and exact output in both arms. Pre-parent sequential bundling; not a P/A effect. |
| `0007`, `0024` | P and A, rule1 pre, tick 2 | Three blocks: two TRY actions and one quiz reveal | `multiple action markers` | Same duplicate structure and same conclusion. |
| `0022` | A, rule0 apply, tick 1 | `COMPARE` | `missing canonical ACT` | A restatement was `PREDICT:COMPARE:COMPARE ...`; apply continued its vocabulary. |
| `0027` | A, rule1 apply, tick 1 | `COMPARE:COMPARE:COMPARE` | `missing canonical ACT` | A restatement contained six lines of `PREDICT/COMPARE/MATCH`; apply again continued it. |

All six responses ended normally (`finish_reason=stop`, no registered stop
reason), used only 2--44 output tokens against a 400-token cap, and were
byte/token preserved. None is a truncation, timeout, alias edge case, nearly
legal action, or parser false negative. `parse_action` deliberately rejects
multiple intents and missing actions at
`rulegame_parenting_diagnostic.py:257-297`; `play_task` correctly executes
nothing and terminates the task at `:453-466`. Executing the first action from
these strings would silently weaken the one-effectful-action boundary and turn
unexecuted proposals into world events.

## P versus A

- The four pre-task invalid events are not arm differences: each P/A pair is
  byte-identical. Both arms execute one valid first TRY and then bundle the
  remaining intended sequence.
- P has two valid apply quizzes, each scoring 0.50. A has zero valid apply
  quizzes because both fail on the first apply response. These numbers are not
  parenting efficacy evidence: P and A receive different parent texts, raw
  restatements produce very different schema activation, and no write or
  parent-free readout occurs.
- The collision is present but less fatal in P. On P rule1 apply, the child
  emits `COMPARE/POLICY/NEXT/ACT` on ticks 2 and 3. Those actions parse, but the
  child omits the required `PREDICT: T/F`; its recorder then emits
  `predicted:null, relation:"matched"`. Both records are correctly ineligible
  for `relation mismatch`. Thus eligible-record count is 1/3, corroborating a
  broad birth-dialect/RuleGame mismatch rather than an A-only parser issue.
- The parent-content audit also fails as a clean P/A comparison. Both neutral A
  messages describe unexecuted proposals as completed tries, violating the
  optional-*accurate*-recap/no-invented-facts contract at
  `rulegame_parenting_diagnostic.py:76-82,113-124`. Both P messages diagnose a
  mistake contradicted by the transcript (the child did predict/update), and
  one recommends “try ... just 3,” which is not even a legal triple. These
  semantic defects did not cause the pre-parent invalids, but they make the
  downstream P/A difference uninterpretable.

## Smallest safe experimental repair

Do **not** relax `parse_action`, salvage the first marker, filter the child's
restatement, or rewrite this failed capture. Keep this root failed and exposed.
Do not use it to tune Q0.

For a separately versioned, exploratory interface diagnostic, add **one
syntax/action-projection turn inside the existing five-response budget**:

1. Preserve an invalid raw wake response as a tentative thought; dispatch no
   action and expose no outcome.
2. Spend the *next* existing response slot asking the same child, over the same
   public state plus its exact tentative text, to choose one next action and
   emit exactly one canonical `ACT: TRY ...`, `ACT: QUIZ ?`, or six-label quiz.
3. Parse that projection with the unchanged strict parser. Permit only one such
   projection per invalid response; a second invalid remains terminal.
4. Keep total wake slots at five and the 400-token per-call ceiling. Record the
   original invalid and projection separately; never score the tentative text
   as an executed action.

This is a diagnostic projection layer, not evidence that the original policy
was valid. It tests whether useful selection exists underneath free-text schema
failure while retaining the one-action causal boundary. Run it only on fresh,
predeclared development tasks. Include AUTH and adapter-OFF children under the
same requests before attributing the failure or recovery to birth. P/A remains
a separate factor; its parent messages still require independent semantic
audit. If action projection does not recover the two A-style cases, the next
isolated development cell should quote/delimit the unchanged restatement and
tell the child not to imitate quoted syntax; do not silently filter its words.

## Exact tests required before that exploratory cell

1. **Parser preservation:** the six exact raw strings above must still raise
   their present errors under `parse_action(..., "interaction_v3")`.
2. **No salvage/no outcome:** each invalid original creates one
   `protocol_invalid`/tentative event and zero execution, world, or record
   events before projection.
3. **Strict projection:** legal projected TRY/reveal/quiz strings execute once;
   multiple markers, bare `COMPARE`, imagined `[OUTCOME]`, DONE+ACT, exhausted
   TRY, duplicate reveal, and quiz-before-reveal still fail.
4. **Budget invariant:** invalid plus projection consume two of exactly five
   response slots; no task exceeds five wake calls or the existing per-call
   cap, and no hidden retry/replacement occurs.
5. **Visibility golden:** the projection request contains the exact current
   public history and exact invalid raw text, but no fabricated result for an
   unexecuted proposal, hidden rule, unrevealed quiz panel, scorer state, birth
   score, later task, or new parent content.
6. **Role/lineage:** parent remains OFF; wake/restate/record/projection use the
   exact pinned child; loader identities and LoRA request are checked and
   replayed per call.
7. **P/A transcript truth:** parent recaps must distinguish emitted proposals
   from actions with recorded world outcomes. Any invented execution or false
   process diagnosis fails semantic audit; do not auto-repair it.
8. **Attribution cell:** exact same fresh schedules/seeds for AUTH and OFF
   children, reporting original-valid rate, projection-recovery rate, final
   quiz validity, record fidelity, and all denominators. This remains an
   interface diagnostic, not parenting, retention, learning, Q0, or Level-2
   evidence.

## Claim boundary

The honest result is: **a source-authored AUTH birth adapter can participate in
parts of RuleGame, but its trained output dialect interferes with the
single-action, prediction, restatement, and record interfaces.** It does not
show that parenting failed, that the child cannot learn from experience, or
that the parser should be weakened. The exploratory output, errors, task
templates, and adapter remain quarantined from Q0 and clean Level 2.
