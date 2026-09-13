# SEQ124 — matched residual-projection formation

Status: EXECUTED, COLLECTED_ONCE, raw paired replay VERIFIED; parent semantic
audit complete with limitations accepted by Main. Both owned controllers/workers/launchers have exited and both
collector receipts report full release. No parameter update or fit occurred.

## Registered descriptive results

Each mode has two rule families, pre/apply tasks, and P/A parent-prompt arms.
Task instances/seeds, initial base, original AUTH adapter custody and budgets
are matched; interactive trajectories and actual parent text can differ.

| Child / arm | Original-valid wakes | Recovered projections | Valid scored quizzes | Faithful records |
|---|---:|---:|---:|---:|
| AUTH / P | 14/17 | 3/3 | 3/4 | 5/5 |
| AUTH / A | 13/16 | 3/3 | 3/4 | 3/4 |
| OFF / P | 20/20 | 0/0 | 4/4 | 4/6 |
| OFF / A | 19/19 | 0/0 | 4/4 | 3/5 |

Zero projection denominators mean no projection was needed, not a 100% recovery
rate. Valid scored quizzes are completed legal quizzes, not necessarily correct
answers. Faithful-record denominators are generated record requests on different
trajectories; these fractions do not isolate a treatment effect on record skill.

All six AUTH invalid proposals contain multiple action markers; none is
executed or salvaged. All six subsequent strict projections execute one legal
TRY within the unchanged five-response budget. No projection fails. Both AUTH
rule1 pre tasks reach the wake budget without a scored quiz, showing that
recovery still costs an action opportunity. OFF has no invalid wake or projection
in these eight tasks. There is no unprojected AUTH sibling on these new instances,
so this is not a causal estimate of net task benefit from projection.

There are56 AUTH calls and58 OFF calls, all finish_reason=stop and none=length.
Do not infer independent token-level EOS verification from that field alone.
Main inspected every invalid/projection execution and ineligible record join.
All five ineligible records have the same relation error: predicted=null but
relation=matched (one AUTH A, two OFF P, two OFF A). Thus this interactive error
is not exclusively AUTH-specific, even though the earlier four fixed record
practice prompts exposed it only in AUTH. Raw historical results stay unchanged.

## Main-discovered prompt-ID mismatch

The v1 interface includes global call IDs in public tentative/projected markers.
In AUTH rule1/pre, P/A ticks1-3 have identical prompts and generation seeds.
At tick4 the prompts differ only in call=0017 versus call=0044. The outputs
then differ: P projects TRY1,1,1; A projects TRY10,11,12, with different actual
world outcomes. This demonstrates different inputs before parenting, not failure
of same-input determinism or a parenting effect. It is an avoidable pre-parent
control mismatch. No claim that the marker alone causally explains every later
difference is made.

The original v1 source/captures/results remain immutable. Arendt owns a forward
v2 hygiene repair: task-local response references in model-visible markers,
global call IDs retained only in custody metadata, plus exact prompt-parity
regressions. No v2 GPU run or birth tuning is selected ahead of runnable Q0.
Replay v1 with native source830fe675 or the frozen local copy
`/tmp/astra_projection_replay_source_830fe675`, not a later edited checkout.

## Costs and custody

| Measured nested interval/count | AUTH | OFF |
|---|---:|---:|
| Input tokens | 24983 | 23209 |
| Output tokens | 1541 | 1341 |
| Summed call seconds | 79.492846 | 40.115812 |
| Worker reserved seconds | 264.549166 | 193.377055 |
| Controller seconds | 293.498131 | 232.152951 |
| Collection seconds | 34.624328 | 38.484359 |
| Launch to recorded release seconds | 369.270620 | 414.370157 |

Intervals overlap and must not be added. OFF's longer launch-to-release interval
includes waiting while Main collected AUTH first; it is not slower inference.
Both fit within900-second controller plus300-second collection allowances.

- AUTH archive `astra_projected_AUTH_20260913_attempt1.tgz`,136 members,
  SHA c435ce2e6dd6750c541788be1889ba6f4664c5c8a35d91bd8c196fb329b08805;
  validation ea6eb7f7dcc1421b430dbbc7674b065960abba04d664d46886fd6b99eb1f5cd9.
- OFF archive `astra_projected_OFF_20260913_attempt1.tgz`,140 members,
  SHA4095540b9d7ab7a0436b3961d6e694c7d70a9eac109d4b32c20d62fa78dc145c;
  validation efa0cc8bcaf5de1c38207badca3e2f653ac9988c236859483f6e38bdb7bdfa48.
- Paired analysis `astra_projected_formation_paired_analysis_20260913_attempt1.json`,
  SHA4d8bebac600412119b995556cf3943bc4b38161475bfe1c3017b38d7371a3bf3.

All276 exact capsule members, stored/raw metrics, request/world joins, budgets,
source/role routes and paired custody replay on VM. This uses the interface
author's analyzer, not an independent scientific reviewer. Einstein separately
audits all eight parent messages/restatements against actual source transcripts;
no semantic-purity approval is assumed here. Exact plans, driver, launcher and
acceptance receipts are in the pilot memo and committed receipt directory.

## Interpretation and next work

Action projection can recover these residual AUTH multi-action outputs without
dispatching invalid text or granting extra responses. The born adapter remains
less compatible with this interface than OFF on these exploratory instances.
Neither a clean birth/Level2 qualification nor parenting, useful learning,
persistence, P1/G3/G5/H1/H2 or mechanism freeze follows. Parent/control semantics
and prompt-ID mismatch independently limit P/A interpretation. Record relation
errors remain a required hygiene check before any selected learning material.

Continue the independently specified closed Q0 executor and native writer test,
without selecting or tuning its material, recipe or thresholds from this result.
No new birth fit is justified by this diagnostic alone. Preserve the v2 repair
for a separately declared future interface test; do not rerun v1 unchanged.

## Parent semantic review and forward repair

Einstein traced all8 parent messages and8 restatements to exact sent transcripts,
raw call envelopes and actual events, independently verifying276member hashes.
Main accepts the review's conclusion: no blanket accurate-recap/control-purity
approval. AUTH A0 incorrectly says five answers despite six submitted labels;
its child restatement repeats this. OFF A1 treats positive world observations
as confirmed forecasts despite two F predictions and True observations, and
confuses individual values with triples. Both A1 recaps misdescribe the quiz unit.
OFF A0 is substantially grounded with conversational ambiguity. Preserve correct
parts of those messages; they do not all invent executed rejected proposals.

P guidance remains process-oriented but several diagnoses are overbroad or
task-underspecified. In OFF, some TRYs genuinely lack forecasts, so local advice
to forecast consistently has a basis; no blanket claim of absent learning is
established by dialogue. No reviewed parent supplies a hidden rule or a new
future-answer vector. These are retrospective semantic judgments, not proof of
efficacy or a new launch gate. Reviewer involvement in prior project helpers/
tests and lack of blinding are disclosed in the archived review.

The forward v2 repair removes global IDs only from harness-authored public
markers, retaining them in raw custody/execution metadata. It uses task-local
response references and a separately versioned namespace/interface. Main45
focused/adjacent tests PASS2.230s, including exact P/A pre-prompt parity and
different global offsets. Projection module SHA
9eeb962e9e2d7716bdbc9963dfdcccfc3219db52e852a00e8d8e655cdf68cbfe;
tests ab4c10491d373b72606a34608e8322215ac3fcf6cc94fbf2e3b450d57942c110.
This is implemented/CPU-tested only, not a new run or a repaired v1 result.
No new birth fit or interface run displaces the independently active Q0 work.
