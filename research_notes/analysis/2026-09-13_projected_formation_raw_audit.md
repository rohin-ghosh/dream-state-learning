# Matched AUTH/OFF action-projection formation: independent raw audit

**Verdict:** the projection mechanism does exactly its narrow engineering job,
but the comparison does **not** qualify formation or show a parenting effect.
On these exposed development tasks, the AUTH birth adapter produced six
multi-action responses while OFF produced none.  Every invalid AUTH proposal
was kept unexecuted and its next in-budget projection was valid and executed.
Even so, projection consumed a wake slot and AUTH reached a scored quiz on only
6/8 tasks, versus 8/8 for OFF.  This is evidence of a source-authored
birth/interface regression with a working fallback, not a repaired learning
system.

## Evidence and custody

I read the request/response JSON for every call and replayed action and record
parsing from those raw strings.  I did not use the stored aggregate as the
source of the counts below.

- Native roots:
  - `/localhome/local-rohing/astra_diagnostics/astra_projected_formation_AUTH_seed0_20260913_attempt1`
  - `/localhome/local-rohing/astra_diagnostics/astra_projected_formation_OFF_seed0_20260913_attempt1`
- Both `run/result.json` files are terminal
  `COMPLETE_AWAITING_MAIN_AUDIT`; both collection validations say
  `COLLECTED_RELEASED`, `phase_complete: true`, and `full_release: true`.
  The recorded controllers/workers (AUTH 292272/292356; OFF 292274/292390)
  were also absent in a fresh node-3 process query.
- AUTH capsule SHA-256 is
  `c435ce2e6dd6750c541788be1889ba6f4664c5c8a35d91bd8c196fb329b08805`;
  all 136 regular members exactly match its validation map.
- OFF capsule SHA-256 is
  `4095540b9d7ab7a0436b3961d6e694c7d70a9eac109d4b32c20d62fa78dc145c`;
  all 140 regular members exactly match its validation map.
- All separately copied native-root files bound by the validations also
  rehash exactly (AUTH 129/129, OFF 133/133).
- There was no fit, write, retained learning, or automatic progression in
  either root.

## Raw call and interface accounting

| child | calls by role | raw/original wake validity | projection | valid scored quizzes | records |
|---|---:|---:|---:|---:|---:|
| AUTH | wake 39, record 9, parent 4, restate 4 = **56** | P 14/17; A 13/16; combined **27/33** | **6/6** valid and executed | P 3/4; A 3/4; combined **6/8** | P 5/5; A 3/4; **8/9** faithful |
| OFF | wake 39, record 11, parent 4, restate 4 = **58** | P 20/20; A 19/19; combined **39/39** | no projection invoked | P 4/4; A 4/4; combined **8/8** | P 4/6; A 3/5; **7/11** faithful |

All 114 responses ended normally (`finish_reason=stop`); none hit its output
limit.  Independent parsing reproduced every validity and record-fidelity bit.

The six AUTH raw failures are call IDs `0001`, `0017`, `0024`, `0030`,
`0044`, and `0051`.  Every one contains multiple action markers.  None of
those call IDs appears as an execution.  The exactly corresponding next calls
`0002`, `0018`, `0025`, `0031`, `0045`, and `0052` explicitly cite the raw
call as an unexecuted proposal, emit one legal action, and are the only six
executions with `projection_of` set.  Thus there is no first-action salvage,
invented outcome, hidden retry, or extra wake slot.

Projection is not a complete formation repair.  In the two AUTH pre tasks
whose invalid response occurred at slot 3, the projection used slot 4 and the
quiz reveal used slot 5, leaving no slot for a scored quiz.  OFF needed no
projection and completed every quiz.

Record arithmetic is also narrower than a formation pass.  Both roots contain
at least two eligible apply records in each P/A arm, so the old mechanical
first-two shortage is gone.  But equal counts are not matched records: the
P/A arms often executed different triples, and selecting the first two faithful
rows is post-treatment selection.  Every one of the five record failures was
the same semantic error: an action with no `PREDICT` was written as
`relation: matched` instead of `relation: unavailable`.  Predicted-action
records were otherwise faithful.

## P/A pairing and parenting

P and A use the same four task identities, hidden rules, quiz panels, budgets,
and per-slot requested seeds.  That is environment-level matching, not
common-random behavioral pairing.  In OFF, byte-identical pre-parent prompts
with the same requested seed already yielded different raw outputs (for
example rule-0 slot 2 and rule-1's final quiz).  Later prompts necessarily
diverge as histories diverge; AUTH projection prompts additionally contain
different raw call IDs.  A two-lesson P/A contrast therefore has no defensible
sampling-based efficacy estimate.

The raw quiz results supply no parenting win:

| child | P pre -> apply | A pre -> apply | taskwise difference-in-change |
|---|---|---|---|
| AUTH | rule 0: .50 -> .33; rule 1: no scored quiz -> 1.00 | exactly the same | **0 on both tasks** |
| OFF | rule 0: .50 -> .50; rule 1: .50 -> .33 | rule 0: .50 -> .33; rule 1: .67 -> 1.00 | +.17, -.50 (opposite signs) |

There is a weak process-aligned observation—P supplied predictions for 5/5
AUTH apply TRYs versus A 3/4, and 4/6 OFF versus A 3/5—but two lessons, unequal
trajectories, and unseeded native variability do not identify a parent effect.

The parent/control text also fails the required semantic audit.  No message
states the hidden rule or a future quiz answer, but several descriptions are
not grounded in the transcript:

- AUTH P lesson 1 says the child failed to test the smallest case although it
  had just executed `TRY 1,1,1`, then recommends a “single value” for a
  three-value interface.
- AUTH A lesson 0 says the child supplied five quiz answers; it supplied six.
- OFF A lesson 1 says the box “confirmed your guesses” for 1--7, although the
  child's explicit forecasts were `F` and the observed outcomes were `True`.
- Both OFF P messages say the child did not predict before acting even though
  it predicted before the first two TRYs; the accurate criticism is only that
  it omitted a prediction on the third.

AUTH restatements also visibly retain its trained `PREDICT`/`COMPARE` dialect,
whereas OFF restatements are ordinary prose.  That is a birth-adapter behavior,
not learned reflection.

## Permitted claim and next action

**Permitted claim:** on one fresh, exposed development schedule, a strict
same-child projection turn safely converted all 6/6 malformed AUTH
multi-action proposals into one executable action without executing the raw
proposal; OFF required 0 projections.  The fallback removed the immediate
serialization stop and produced enough faithful rows for a nominal two-per-arm
material set, but did not restore AUTH task completion, validate the parent,
or establish parenting, learning, persistence, sleep, useful writing, clean
Level 2, or any paper headline.

Do not fit or promote material from these roots.  Keep projection as a logged
fallback for residual free-thought bundling, not as evidence that the birth is
qualified.  The next claim-bearing action remains the already frozen Q0
selective-writer root.  Separately, before another clean Level-2 formation,
require (1) a prospective birth-interface non-inferiority canary without
projection, (2) a fixed no-prediction -> `unavailable` record canary, and
(3) transcript-grounded parent/control review.  No threshold, parser, birth
corpus, Q0 input, or experimental result should be tuned from this exposed
root.
