# RuleGame-compatible birth: two ready-queue options / EDITSTOP

Design only; no rows generated, code changed, fit/probe launched, or live outcomes inspected.
Main chooses after the current birth readout and AUTH level2 sample. Current birth has NOT
been declared failed. These are existing-source proposals, not claims of an already reviewed
training dataset. No new mandatory gate, grader, parent visibility or thesis is proposed.

## Directive and actionable difference

Read Rohin's raw Message28 in `research_notes/THESIS_RAW_ROHIN_2026-09-11.md:301`,
including “this wohle seciotn is just suggestive”: investigate which birth behaviours help
level2, using instructions/diverse examples and iterative calibration. This does not require
seven skills, a factorial, another fit now, or finding outside datasets in this assignment.
The earlier `/tmp/astra_birth_level2_bridge_review_20260913.md` already motivates the
interface mismatch; this note only specifies two possible curriculum replacements.

Current `birth_conditional_corpus.response_text` teaches opaque action/outcome strings and
COMPARE/POLICY/NEXT. Its truthful ADDITION/COPY anchors do not encode RuleGame state transitions.
The actual consumers are `rulegame_parenting_diagnostic.parse_action(...,'interaction_v3')`,
`play_task`, `record_prompt`/`judge_record`, and `rulegame_process_material.validate_wake`.
They consume one action, a preceding unambiguous `PREDICT: T/F`, three integer TRY arguments,
reveal before six-label QUIZ, and exact post-execution JSON—not opaque-action substitutions.

Important boundary: `play_task(notes=True)` requests a record after EVERY executed TRY;
record responses are not appended to the wake history. Process-v2 `select_slots` chooses
the SECOND pre-reveal TRY in each prescribed P/A lesson position, independently of correctness.
There is no consumed KEEP/DROP or surprise-priority field. “Selective recording” cannot mean
training an abstention, extra JSON key, or new retention selector here. Grounded next actions
and faithful records can improve available material; useful retention remains unproven.

## Option A — minimum protocol/serialization bridge (first choice if syntax is the bottleneck)

Source specifications: diagnostic `BOOT`, `interaction_settings`, `parse_action`,
`record_instruction('interaction_v3')`, `record_prompt`, `judge_record`; existing accepted
forms and scripted fixtures in `tests/test_rulegame_parenting_diagnostic.py`.
Provenance: SOURCE_AUTHORED_BIRTH_NOT_CLEAN, not a child's own wake or parent-produced lesson.
Future authoring compiles these specifications into short instruction/answer exercises;
it must NOT relabel the scripted fixture's constant TRY0,0,0/all-T quiz as successful induction.

Public input → complete target contracts:
- An explicitly supplied triple and explicitly supplied Boolean forecast →
  `PREDICT: <T/F>\nACT: TRY <x,y,z>`; this is ordered serialization, NOT a correct-world-forecast label.
- Supplied harness state “reveal still needed”, zero remaining TRYs → `ACT: QUIZ ?`.
- Explicitly supplied ordered six Boolean labels plus revealed-state instruction →
  `ACT: QUIZ <six T/F labels>`; this is label transcription, NOT hidden-rule inference.
- Exact `record_prompt(execution, emitted_wake, 'interaction_v3')` → ONLY the four-key JSON
  whose try/observed/predicted fields equal that public execution and whose relation is
  matched/mismatched/unavailable. Include truthful wrong-prediction and absent-prediction cases.

The supplied forecast/quiz-label practice inputs are AUTHORING scaffolds, not native hidden
answers. Remove them in the downstream native probe; do not add them to BOOT, parent inputs,
or the grader. This option directly teaches consumed output forms but does not itself teach
choosing a TRY, induction, belief revision, or autonomous material selection.

Control: a prebound, balanced whole-target permutation within each serialization/record
family (DERANGED), holding prompts, legal target vocabulary, target multiset and dose fixed;
exclude identical-target swaps. Keep the same truthful locality anchors in both arms.
It intentionally breaks the supplied-input→output mapping, not the environment's truth.
An instruction-only/no-new-write reference is the cheaper SHAM for the preliminary probe;
it is NOT dose-matched and must not be described as such. Do not add both comparisons by default.

Positive controls: deterministic field-to-string rendering and `judge_record` must accept
the AUTH targets; committed ScriptedBackend/role fixtures check request sequencing and routing.
Their all-T quiz is a syntax control only. Invalid labels: reordered/missing quiz entries,
multiple ACTs, post-action “prediction”, invented OUTCOME, incorrect null/relation, hidden
answers smuggled into a purported native prompt, or ambiguous-source predictions labelled valid.

## Option B — grounded native-history next-wake revision (if syntax works but causal use is weak)

Source functions: `rulegame.RuleGame._rule`, `evaluate`, `quiz_triples`, `RULES`;
diagnostic `play_task` for the EXACT public history/state renderer, `parse_action` for actions;
process material `validate_wake(..., protocol=PROTOCOL_V2)` for the future second-TRY target form.
No existing helper supplies a gold “best next probe”; any action policy below is an explicitly
authored practice policy, NOT an established optimal exploration label or sampled learner trace.

Public input → target contract: one native-shaped PRE-action prompt, ending before the target
action's feedback → the full next wake containing exactly one Boolean PREDICT followed by
one legal TRY. Use a fixed, disclosed practice action order; do not choose actions retrospectively
for reward or helpfulness. For a repeated already-observed triple, the forecast equals its
public observation. For a novel triple, label a forecast as grounded only when all hypotheses
consistent with the visible observations in the declared finite RuleGame family agree.
If they disagree, there is no gold truth label for that forecast: omit that proposed AUTH
training row prospectively/report the shortage, or retain it only as a grammar probe without
an accuracy label. Do not use the episode's hidden function alone to settle this ambiguity.

Revision examples compare the earlier emitted prediction with the subsequently PUBLIC
outcome, then emit the next legal pre-action forecast/action. Earlier wrong predictions remain
verbatim in history. The simplest defensible label is correcting the forecast on the same
observed triple; that proves evidence-sensitive revision, NOT informative new-probe choice.
Revealed quiz targets are AUTH-grounded only when the same public-consistency test determines
all six answers. Otherwise retain quiz format testing, without manufacturing an oracle answer.
The finite-family assumption is an authored prior, not unrestricted deduction or clean lineage.

Use the record mapping from A only as a shared small role-integrity block, not as the primary
target: process-v2 writes whole own-wake responses, not those record summaries. No imagined
experience, post-action feedback, teacher prose or restatement is appended to a PRE-action target.
Control: pair contexts with opposite publicly determined forecasts and the same action shape;
swap whole prediction/action targets within balanced groups. Keep truthful record/locality
blocks identical. This preserves grammar while breaking grounding; report actual exposure.

Positive controls: a public-history checker implements the declared consistency test; a
separately labelled RuleGame function oracle checks environment labels ONLY in the audit.
The oracle is never a child/parent input or evidence that the learner inferred the rule.
Invalid labels: underdetermined forecasts called true, changed earlier predictions, unseen
outcomes in context, illegal budget/reveal state, or claiming a chosen action is uniquely useful.

## Shared partition, dose and exclusion decisions

Preserve current formation rules0–1 and evaluation rules2–5/IDs/quiz triples unchanged.
For proposed rule-dependent authoring, reserve only existing rule indices6–9 (`prod_even`,
`range_le4`, `first_largest`, `sum_gt15`); split practice train/probe by entire source episode
BEFORE renderings. Never mine the current formation, readout, or their descendant material.
Old prescribed process-v2 rows on rules0–1 are therefore NOT a disjoint birth curriculum for
this same level2 sample. No eligible alternate bank has been claimed or generated here.
For A, partition source tuples, forecasts and six-label lists before wording variations;
for B, additionally partition public histories and quiz instances. Audit exact/near-copy overlap.
`Task: ruleN/...` is visible: changing only the suffix is not held-out rule generalization.
Disjointness here is relative to this sample, not proof those repo rules were never exposed.

If Main selects a later fit, compare ONE option against its matched control; reuse the fixed
base/single-LoRA recipe and existing native target-only/EOS/masked-padding audit patterns.
Freeze row budget only after a feasible bank exists; replace rather than silently append the
opaque conditional block. Keep anchor dose equal and report tokens/updates/padding per arm.
Equal total budget is not equal new-behaviour dose; a matched permutation needs actual native
batch auditing. No arbitrary dose escalation or claimed equivalence to the current256-row fit.

## Tiny probe before choosing another birth fit — proposal, not launch authorization

After the current closed sample, Main can request16 fixed developmental requests/state:
4 public-input→TRY serialization,4 reveal/quiz-format requests,4 post-TRY record mappings,
and4 native-history revision requests (two paired evidence contrasts). Use current base-OFF
and immutable birth-AUTH:32 calls total, existing role generation settings, no optimizer.
Use practice-source episodes only; scaffolded format cases are labelled separately from
native-shaped evidence cases. Include mismatched/null records and preserve all invalid outputs.
Run the deterministic syntax/record positive controls first; close ALL model calls before
comparing parser validity, supplied-field fidelity, and public-evidence-consistent revision.
This is not a new L1 threshold. Syntax weakness suggests A; syntax intact but evidence ignored
suggests B; missing faithful source at prescribed slots is reported, not replaced. If these
already work, neither option is necessary on that evidence; inspect downstream utility separately.

Do not reuse `bootstrap_corpus.main` as a shortcut: it invokes an author model, defaults to
wins-only selection, and `acts_ok` only checks an ACT-set subset—not exact chronology or outcome
preservation. Curriculum prose such as `05_replay_what_matters.md` is instruction inspiration,
not grounded labels or verified neuroscience evidence. No literature or outside data is asserted.

Only this design note was written. Existing code, selectors, graders and visibility remain frozen.
