# RuleGame interaction-v2 terminal causal and pedagogical audit

**Date:** 2026-09-12 16:56 UTC

**Scope:** fresh read-only audit of
`/localhome/local-rohing/astra_diagnostics/astra_rulegame_interaction_v2_20260912_attempt1`,
compared with terminal strict-v1 root
`astra_rulegame_minimum_20260912_attempt1`. This note changes no builder
source, experiment, adapter, job, GPU allocation, active v8 state,
architecture, or claim. It does not pause Astra under `AGENTS.md`.

## Bottom line

**Interaction-v2 fixes and qualifies the narrow action/world boundary on this
fixed development block. It does not qualify the parenting-material pipeline,
and no write is justified.**

The native formation completed all 60 prospective calls. All eight tasks
executed three real TRYs, revealed their panels, and reached one valid scored
quiz; there were zero protocol-invalid tasks. Raw action text, canonicalized
action, actual world response, native stop condition, and event identity are
preserved and replay cleanly. This is a real interface gain over v1.

The terminal Main material decision now records
`MAIN_DECLINED_MATERIAL` with `semantic_no_answer_certification=false`. The
gate fails twice independently:

1. P has only **1/6** faithful apply-event records, below the prospectively
   frozen two-record threshold; A has **3/6**. Across arms, the child stated an
   unambiguous prediction on **8/12** apply TRYs but supplied the correct
   record relation on only **4/12** record calls. Prospective selection would
   be P=1 versus A=2, so the pair is a shortage and neither fit may run.
2. Both A parent turns and both A restatements violate the tightened
   acknowledgment-only control contract by reporting task/quiz content or
   scores. The four-interaction all-accept content gate therefore fails even
   apart from the record shortage.

P's two turns contain no hidden-rule answer, but they are generic repetitions
of “predict before acting,” not Rohin's strongest context-adaptive parenting.
The first child restatement also invents an irrelevant arithmetic task and a
rule-relevant sum cue. These are treatment-quality defects, not contamination
of training bytes, because no corpus exists and no write occurred.

## Evidence and custody

I read `AGENTS.md`, the prospective interaction-v2 protocol, the bound source
and focused tests, the direct RuleGame/parent interfaces, the v1 terminal memo,
the prior independent v1 audit, and relevant builder entries. I inspected all
60 raw v2 request/response pairs, the complete event stream, formation result,
usage, identity, provenance, manifest, and cleanup receipts through
`gpu/ovx2_ssh.sh`. I issued no model, tokenizer, trainer, GPU, process, or job
operation.

Remote byte anchors at the audit cut:

| artifact | SHA-256 / fact |
|---|---|
| `plan.json` | `5cc110bceb6e92186bc707fdd4369eaf53690a4fba694ac1fa5b8b8dbfcc88f7` |
| formation manifest | `4fef2770a6be151bc00fc4782575134643f8754b2cd149380b48a4aaf6dfed41` |
| `events.jsonl` | `680aad3cf5f114a810af138b23866d65cb54e6e8d87ecb065d323ed2cdf7fc33` (60 rows) |
| formation `result.json` | `f4baa4ee18986cea327e9e5372164357bd4e084d9692ae193bcb10e20bbfcd69` |
| formation provenance | `2875ed54fd90f3a51a4e5f7b915b18d9134f1f93c45c87c85c84f6020dba1613` (`ok=true`) |
| supervision | `13a28aa9e668b00041749b666b74e46bf37696358c533b41b4c797c69e8c8003` |
| Main material audit | `771c43a6a01f25999525fdf46782b77699961f4dee405c85c0390524403d9757` |
| material result | `614288d1e0f01e4778649753f701aff28de56c84f9f1df7c3ee33c080afe96ab` (`MAIN_DECLINED_MATERIAL`) |
| terminal downstream state | no corpus, `write/`, or `evaluation/` |

The capture has 126 manifest-bound files. Source is
`20897d84f8b1cdb24f42118589d53c9976d7b416`, with diagnostic source SHA-256
`6d8bca8e962d3aa5635de40fa534f69e0bbe43efda3aaa1cfec12d99837ea09f`.
The same locally pinned Qwen2.5-7B-Instruct base served every role with no
adapter. Official model origin remains `UNRESOLVED_LOCAL_HASHES_ONLY`.
Backend close, owned group empty, GPU process absent, release verification,
and supervisor return code zero all pass. The supervised worker window was
164.493 seconds. The declined `material/` directory contains only the Main
audit, the copied provenance, and the decline result; it has no directory
manifest of its own. The immutable formation remains the bound evidence.

## V2 versus v1

| property | strict-v1 terminal | interaction-v2 terminal | audit |
|---|---:|---:|---|
| formation responses | 32 | 60 | v2 reaches its full prospective ceiling |
| protocol-invalid tasks | 8/8 | 0/8 | boundary repair succeeds |
| valid first quizzes | 0/8 | 8/8 | executable fixed-block task loop |
| real TRYs, P / A | 0 apply / 4 apply | 12 total per arm, 6 apply per arm | balanced opportunities restored |
| record calls, P / A | 0 / 4 | 6 / 6 | paired record opportunities restored |
| eligible records, P / A | 0 / 2 | **1 / 3** | still below P threshold |
| prospective selected rows, P / A | 0 / 2 | **1 / 2** | paired shortage persists |
| control content | 2/2 invalid | 2/2 invalid | tightened prompt did not control generated content |
| valid pre-treatment response pairs | one equal-seed pair diverged | all 10 response pairs byte-identical | exact pairing works in this v2 capture |
| material/write/readout | declined / none / none | declined / none / none | correct stopping point |

V1's child frequently emitted `TRY:` without `ACT:` or several actions with
imagined outcomes. V2 accepted only one anchored `TRY:`/`QUIZ:` alias,
preserved its raw text, recorded a separate canonical action, reminded the
remaining budget, and stopped native wake decoding before the exact newline
`[OUTCOME]`. Six anchored TRY aliases were safely canonicalized. On two wake
calls the native stop receipt shows that an impending child-simulated
`[OUTCOME]` was actually cut; no fabricated outcome entered the world/event
stream. The harness supplied every authoritative outcome.

All ten P/A pre-task request pairs had equal prompt hashes and sampler seeds,
and all ten response receipts were byte-identical. This removes v1's observed
pre-treatment response imbalance for this root. It does not prove universal
backend determinism, but it makes the two v2 pre histories genuinely paired.

V2 used 23,342 native input and 1,296 output tokens, versus v1's 11,895 and
1,446. The lower output count despite more calls is consistent with the new
stop boundary. Both arms had exactly 30 responses, but total native token cost
still differed: P used 12,683 input/728 output tokens and A used 10,659/568.
Most of the input difference is the long P parent prompt (2,161 tokens versus
609 for A), followed by longer P restatements and downstream wake context.
This remains opportunity-matched, not exact compute- or exposure-matched.

## Is the interface qualified?

**Yes for the narrow, versioned development interface; no for the full
scientific pipeline.**

The repaired action-commit boundary passes its stated empirical question on
this fixed block:

- 40/40 wake responses resolve to exactly one accepted action;
- 24/24 intended TRYs execute once and bind to real Boolean outcomes;
- 8/8 reveals are followed by one six-label scored quiz;
- 12/12 apply executions receive exactly one post-outcome record call;
- no child-written outcome becomes an environment outcome;
- raw/canonical/source/native-token provenance and cleanup pass.

That is enough to retain interaction-v2 as qualified **exploratory
development machinery** for this exact action grammar and stop convention. It
does not establish better thinking, parenting, record-writing, or transfer,
and a single fixed block is not general reliability evidence.

One semantic defect also remains visible: `RuleGame.evaluate("QUIZ ?")`
returns `INVALID: quiz needs 6 answers ...`, while `play_task` classifies the
same action as a successful reveal, sets `revealed=true`, and tells the child
that the quiz is revealed on the next turn. All eight children navigated this
contradiction and were scored, so it does not invalidate these recorded task
scores. It does prevent calling the whole RuleGame tool protocol semantically
clean without a narrower statement of the convention.

The parent still receives a joined text transcript rather than a typed
authoritative-event view. The stop repair happened to remove simulated outcome
text in this root, so its parent transcript contains only harness-provided
outcome markers. That is an observed clean instance, not a structural parent-
grounding guarantee for arbitrary child wording.

## Exact records and paired material decision

All 12 apply TRY outcomes were `true`. The exact record audit is:

| arm | record call | source | verdict |
|---|---:|---|---|
| P | `0008` | rule0 apply t1, predicted F / observed T | reject: wrote `matched` instead of `mismatched` |
| P | `0010` | rule0 apply t2, predicted T / observed T | **eligible** |
| P | `0012` | rule0 apply t3, prediction absent / observed T | reject: wrote `matched` instead of `unavailable` |
| P | `0023` | rule1 apply t1, predicted F / observed T | reject: relation mismatch |
| P | `0025` | rule1 apply t2, predicted F / observed T | reject: relation mismatch |
| P | `0027` | rule1 apply t3, prediction absent / observed T | reject: relation mismatch |
| A | `0038` | rule0 apply t1, predicted F / observed T | **eligible** |
| A | `0040` | rule0 apply t2, predicted T / observed T | **eligible** |
| A | `0042` | rule0 apply t3, prediction absent / observed T | reject: relation mismatch |
| A | `0053` | rule1 apply t1, predicted F / observed T | reject: relation mismatch |
| A | `0055` | rule1 apply t2, predicted T / observed T | **eligible** |
| A | `0057` | rule1 apply t3, prediction absent / observed T | reject: relation mismatch |

Thus P is **1/6** and A is **3/6** faithful. The relevant counts answer two
different questions and must not be conflated:

- **8/12 prediction coverage:** P stated a prediction on 4/6 apply TRYs and A
  on 4/6. The two prediction-absent executions per arm legitimately require
  relation `unavailable`.
- **4/12 faithful records:** P encoded 1/6 complete relations correctly and A
  3/6. All eight rejected records were syntactically parseable but wrote
  `matched` where the typed facts required `mismatched` or `unavailable`.

Prediction coverage is therefore not record eligibility. The first-two
physical-order selector would retain P `0010` and A `0038`,`0040`, but P
remains one short. The third eligible A row cannot be borrowed across arms,
and the threshold may not be reduced after outcomes. No parent/restatement
text appears in the eligible JSON bodies, but that does not override paired
shortage or invalid control ancestry.

The probes themselves are pedagogically weak. Every actual TRY was a positive
case; the child repeatedly chose simple increasing triples whose sums are also
divisible by three, so they do not discriminate rule0 (`sum_div3`) from rule1
(`increasing`). One public probe is sufficient to separate those hypotheses:
for example, `(1,2,4)` is false under rule0 and true under rule1 (or `(3,1,2)`
has the reverse truth values). The child should choose such a contrast from
its evidence; the harness should only verify after commitment that the
candidate hypotheses disagree. This was not a prospective material rejection
criterion, but it explains why faithful event serialization alone would not
establish useful rule induction or a reusable learning process.

## Parent and control content audit

### P lesson 0

The parent correctly notices that prediction was missing on one of three
attempts, and it supplies no hidden Boolean answer or rule. But it overfocuses
on a generic slogan already present in the child boot, asks about the already-
tried `(2,3,4)`, and does not address the non-discriminating all-positive probe
set. The child restatement then invents a different “find the sum” task and
states `2+3+4=9`. That arithmetic fact is not a supplied hidden-rule answer,
but it is a task-specific cue for the actual sum-divisibility family and is not
a faithful application of a Boolean prediction lesson.

### P lesson 1

Again, prediction was absent on one of three attempts, so the narrow diagnosis
is factually supportable and contains no answer leak. The message is essentially
the same generic predict-before-action instruction as lesson 0, despite a
different rule, quiz score, and history. It does not adapt directiveness,
diagnosis, or next-step experiment quality to accumulated evidence. The child
restatement is a reasonable paraphrase but adds no grounded causal lesson.

Under a minimal “process text with no hidden answer” screen, both P turns are
safe with the lesson-0 caveat. Under the selected causal/pedagogical question,
neither is evidence of strong adaptive teaching, and lesson 0 is not suitable
as a clean process-only treatment realization. In either interpretation the
four-interaction gate fails because of A.

### A lesson 0

The tightened prompt explicitly forbids task reflection, quizzes, learned
content, or task summaries. The generated control nevertheless summarizes
exploration, says the quiz “needed more answers,” and reports score `0.50`.
Its restatement repeats task and quiz content. Both parent and restatement
violate the control contract.

### A lesson 1

The control reports the exact `0.83` quiz score and asks for it to be restated.
The child repeats the score, changes the actor to “Your parent,” and adds
praise. This is neither acknowledgment-only nor content-neutral. It is a
second independent control rejection.

No hidden rule, answer labels, or sealed rule2--5 readout content appeared in
these interactions. The problem is treatment/control validity, not final-panel
leakage. Development scores in the A prefix also make A a scored-feedback
treatment rather than the declared neutral-contact comparator.

For completeness, P and A began from identical pre performance: rule0 `3/6`,
rule1 `5/6`. Their two apply quizzes both total `7/12`: P is `4/6` then `3/6`,
A is `3/6` then `4/6`. Each arm falls one correct label from its `8/12` pre
total, so this two-task block shows no aggregate P advantage. Prediction
coverage is also unchanged at 4/6 apply TRYs in each arm. These tiny paired
descriptives are not an equivalence test or causal parenting estimate.

## Strongest-adaptive-parent mismatch

The runtime parent is still the same frozen 7B base used by the child and
control, wearing the static `parent_prompt.txt` role. It has no accumulated
teaching state, no verified metric/history table, no contingent directive
ladder, no intervention/fading policy, no factual self-check, and no stronger
14B/32B parent-server seam. Its two realized messages repeat one generic
instruction already embedded in `CHILD_BOOT`; neither teaches discretionary
storage, evidence-bound causal diagnosis, or a child-authored organization
decision.

This does not match the launch instruction to start with the strongest
relevant parenting design already in the repository. The first-ranked design
is contingent scaffolding based on verified success/failure history, and the
causal control ladder recommends shuffled/noncontingent or content-matched
feedback. The present P-vs-generated-praise comparison tests neither. It also
remains a forced record-serialization block, not Rohin's intended teaching of
the disposition to turn experience into useful post-training data.

## Write decision and maximum claim

**Do not create a corpus, fit, evaluate, replace lessons, lower thresholds, or
use an A-only favorable subset from this root.** Main has now emitted the
proper bound decline receipt. The content rejection and paired shortage each
independently block `material -> write`; together they make the decision
overdetermined. The four eligible A/P records may remain immutable diagnostic
evidence, but they are not valid training rows for this claimed comparison.
Repurposing them would require a separately named post-hoc positive-control
question and could not support parenting.

The exact maximum defensible claim is:

> On one fixed, exploratory Qwen2.5-7B block, interaction-v2 converted every
> planned child response into one replayable public RuleGame action, prevented
> simulated outcomes from becoming world evidence, restored exact paired pre
> histories, and completed all eight first quizzes. It thereby qualifies the
> narrow versioned action/world development interface. The same formation did
> not qualify material: eight of twelve apply TRYs included predictions but
> only four of twelve record calls were faithful (P one of six; A three of
> six); both generated A parent turns and their restatements violated the
> control contract; the generic same-model parent
> showed no aggregate task or prediction-coverage advantage, and no SLEEP,
> reload, or readout occurred. Nothing here establishes adaptive parenting,
> useful child material, learning, DREAM, transfer, H1, or H2.

## Minimum next discriminator

Before spending another parented formation, run a **no-parent, no-world,
no-fit three-case relation canary** over immutable v2 facts: false/true must
produce `mismatched`, true/true must produce `matched`, and absent/true must
produce `unavailable`. The exact P-rule0 apply sources are calls
`0007 -> 0008`, `0009 -> 0010`, and `0011 -> 0012`; the current answers are
wrong, right, wrong. Present typed trusted facts and request only the relation
token at temperature zero, without supplying a precomputed relation. Three
passes localize the defect to the verbose JSON/label handoff; any failure
localizes it to elementary relation following. This discriminator introduces
no parent or learned content and cannot reopen this declined root or authorize
a write.

The smallest subsequent *parenting* formation is a prospectively named,
single-lesson paired P/A development scout on fresh training EIDs disjoint
from sealed rule2--5 readout. Start exact fresh-base twins from a byte-identical
THINK history. Give only P the strongest adaptive parent over typed public
events; give A one presealed, dose-matched yoked/noncontingent process message.
Then require one child-chosen public TRY for which its leading hypotheses
predict different truth values. For the already-consumed rule0/rule1 pair, a
single committed `(1,2,4)` or `(3,1,2)` would have sufficed, but these examples
are audit-only and must never enter model-visible prompts; the child must derive
the choice and a hidden harness may only verify the contrast after commitment.

After that event, the child must DREAM either one evidence-citing process
lesson or an explicit null. Only if both arms pass the same prospective
child-authorship, factuality, contrast, and control gates may their respective
child-only DREAM artifact enter deterministic SLEEP. Evaluate fresh reloads
with parent, transcript, current-root records, rule identities, answers, and
this audit absent. This is the minimum formation that retains a real
THINK--DREAM--SLEEP chain without contaminating sealed readout; it is still a
development scout. Any mechanism claim requires the predeclared DREAM_NULL
and SLEEP_OFF controls as well.

## Recommendation

Preserve interaction-v2's action boundary; do not run another action-format
or sampler-seed rescue. Before the next parenting formation:

1. Give the parent an authoritative typed view of executed predictions,
   actions, outcomes, quiz status, probe diversity, and accumulated teaching
   history—not an undifferentiated transcript.
2. Use the strongest available context-adaptive parent seam with the
   contingent ladder and a factual self-check before delivery. One failed
   parent package ends the pair; do not regenerate for better content.
3. Replace generated neutral praise with a presealed, dose-matched
   noncontingent/yoked process-feedback control whose forbidden-content checks
   are deterministic rather than instruction-following hopes.
4. Make the child propose a discretionary, evidence-citing DREAM lesson or
   choose to store nothing. Require at least the single contrastive public
   event specified above, not only positive triples, before a lesson can
   qualify. Keep raw event JSON as provenance support rather than the learning
   target by itself.
5. Only paired qualified child DREAM material may reach deterministic,
   parent-text-free SLEEP and sterile parent-removed ON/OFF readout. A minimal
   TDS mechanism claim still needs matched `DREAM_NULL` and `SLEEP_OFF`
   controls.

This preserves the demonstrated interface repair while moving the next scarce
formation toward Rohin's actual adaptive-parent and THINK--DREAM--SLEEP
question instead of spending another block on a relation-serialization prompt
the child answered faithfully only 4/12 times despite stating predictions on
8/12 source attempts.
