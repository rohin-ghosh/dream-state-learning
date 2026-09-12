# Parenting next-gate audit: qualify teaching before asking SLEEP to carry it

Date: 2026-09-12 UTC

Status: read-only watcher-side design audit. This note changes no builder-owned
source, model, adapter, run, node, or claim authority. It authorizes no launch.
It applies Rohin's simple-hygiene-now / C11-final ruling and leaves the formal
C11 guard parked.

## Plain verdict

The smallest useful parenting experiment **right now** should not train a
LoRA. It should ask one prior question cleanly:

> Given the same child failure, does a strong parent's *choice of process
> lesson* cause a better child-authored plan and better subsequent action than
> an equally long, equally warm but task-mismatched lesson?

Call this `P0-COACH`. Run it in the task-disjoint Reasoning Gym with a frozen
child and no SLEEP. The parent never sees a reference answer or the later apply
task. It selects one item from a fixed answer-free process-card bank; the sham
arm receives a card selected for another matched child. The child then writes
its own plan. On the primary fresh case, only that child-authored plan is
visible: the parent's text, source transcript, and source answer are absent.

This can measure three valuable links while the writer is being repaired:

1. **diagnosis:** did the parent select a useful process intervention rather
   than generic advice?
2. **uptake:** did the child turn that intervention into its own usable state?
3. **thought-to-action:** did the state improve an authoritative action/outcome
   on a different instance?

It cannot measure weight-carried learning, retention through SLEEP, durable
parenting, or later autonomous learning. That separation is the point: if
`P0-COACH` is null, improve the teaching path; if it is positive but a later
LoRA test is null, improve the writer. The present experiments confound those
failures.

## Immediate update: what the live 64-schedule pair can decide

A builder-owned exploratory material-formation pair is now running on the
same 64 schedules with a fixed record-writing lesson versus a fixed active
sham. It has no adapter, training, sleep, deployment evaluation or clean-lineage
claim. The deterministic clock removes one known nuisance, but the teaching
packages are not dose-matched: the lesson prompt is 203 tokenizer tokens and
the sham is 158, a 45-token (28.5% relative to sham) difference.

This pair can answer only:

> Does this exact, longer lesson package make the frozen child produce more
> strictly grounded child-authored records than this exact, shorter sham
> package on these 64 schedules?

The smallest meaningful reducer should keep the schedule as the paired unit
and report, before any writer use:

1. strict ACT-linked faithful `NOTE_AFTER` formation per schedule (primary);
2. NOTE_AFTER-slot response, valid ACT, first-person attempted action, exact
   observed score/verdict, and rejection reason separately;
3. paired discordant counts and the paired effect interval, plus all 64 rows;
4. child output length and total child-visible tokens as diagnostics; and
5. exact lesson/sham prompt bytes and tokenizer counts beside the result.

Do **not** divide the outcome by prompt tokens; that does not remove the
confound. A positive result is an effect of the whole exact prompt package,
not evidence that the semantic lesson rather than 45 extra tokens caused it.
A null is also only a null at this dose and sample size. The run says nothing
about adaptive diagnosis, better task decisions, SLEEP, LoRA learning,
retention or parent deletion. It is nevertheless useful: it tells us whether
the current classroom can manufacture grounded child-owned material for a
writer at all.

If a clean semantic attribution is still valuable after this read, the next
no-training replication should tokenizer-match the sham to 203 tokens using
content-neutral teacher text, without editing either prompt after seeing the
64 outcomes. That is smaller than redesigning the parenting system.

### Smallest later writer application

Do not fit this material with the currently unqualified writer. Once an
independent writer gate has established selective carriage and interface
preservation, run one bounded developmental canary:

1. freeze the 64 schedules and exact child outputs before any LoRA result;
2. compile only strict ACT-linked child `NOTE_AFTER` rows; teacher/sham bytes
   are visible childhood influences but never targets;
3. fit lesson-material and sham-material adapters independently from the same
   clean base with the frozen writer recipe, recording their different row and
   token yields as an intended mediator of the prompt package;
4. add a predeclared equal-training-token sensitivity using deterministic
   chronological truncation to the smaller corpus—never outcome-selected
   examples;
5. on fresh task-disjoint schedules, delete all teacher/sham/source text and
   compare each adapter ON versus OFF on the same strict grounded-record
   endpoint; and
6. estimate the interaction
   `(lesson_ON - lesson_OFF) - (sham_ON - sham_OFF)`, with action validity and
   non-record behavior as no-harm checks.

That can establish only that one fixed lesson package caused child-authored
record material whose effect later appeared without teacher text. It still
does not establish adaptive parenting, better reasoning, task benefit or the
full THINK/DREAM/SLEEP loop. `P0-COACH` below is the next experiment for those
parent-selection and thought-to-action links.

## Why this is the next gate

### Existing parenting evidence does not establish teaching

The terminal R4/R3 audit contains six parented and six historical control
lives, all 1,024 episodes. After the indexed parent event, R4 first-note token
overlap rose about 13 percentage points, but pre-event overlap was already
67.188% and the brief explicitly demanded repetition. Authoritative
changed-action episodes were only 10/192 directly, 12/192 after one sleep and
6/192 after four; parented score changes were +0.046, +0.384 and -0.371
percentage points. Controls improved more at every window. Assignment,
teacher model, event age, later briefs and writer selection were confounded.
This is prompted lexical accommodation, not a causal parenting result.

The adapter was already behaviorally active before parenting: across 17
pre-parent/boundary ON/OFF pairs it improved the repeated report score in
17/17, mean +0.020675, while suppressing the coarse changed-action signature.
Post-parent ON/OFF behavior therefore cannot identify the parent.

### Existing post-outcome evidence says the child needs teaching, but not that
### SLEEP can preserve it

B0 attempt 2 produced one source-joined NOTE_AFTER after every execution, but
only 1/224 numeric B records and 0/246 A records satisfied the intended
first-person articulation predicate. The permissive gate nevertheless trained
66 items, 65 without that predicate. The fresh postwrite articulation read was
0 ON and 0 OFF. This is strong motivation for an explicit teaching
intervention; it is not evidence that the intervention will survive a write.

B0 also established that same request seeds do not currently provide exact
generation replay and that model-visible wall time can separate arms before a
treatment. A new experiment must start both continuations from one persisted
pre-treatment transcript and use independent task blocks; it cannot call two
separately generated childhoods “paired” merely because their seeds match.

### The writer is not qualified to adjudicate parenting yet

The current multikey writer attempt is `ASSAY_INVALID`, and earlier writer
cells moved non-owner controls substantially. The project therefore cannot
interpret a parent-absent adapter null as failed parenting, or an adapter
behavior change as retained lesson semantics. The clean order is:

```text
P0-COACH: parent -> child-authored plan -> authoritative action
writer gate: grounded child continuation -> selective LoRA carriage
P1-PERSIST: parenting -> grounded child continuation -> SLEEP -> parent-deleted action
```

`P0-COACH` can run in parallel with the writer gate because its result neither
depends on nor selects a LoRA recipe.

## Current implementation audit

Snapshot: laptop `main` at `dbff0023`, with builder state observed through the
append-only coordination record. Builder source and jobs were read only.

| Surface | Reusable now | Why it is not already the proposed experiment |
|---|---|---|
| `reasoning_gym_gym.py` + `reasoning_gym_families.json` | Best current task source. Exact public scores, no answer in feedback, deterministic item IDs, CompilerGym-like/code families excluded, and train/gate/exam families plus seed ranges disjoint. | Its ordinary birth prompt already tells the child to predict, investigate, self-judge, use the whole budget and build cross-task understanding. Teaching those same acts has little headroom. `P0-COACH` needs an interface-only child prompt for both arms. |
| `preschool_reasoning.py` | Strong ACT-to-child-record provenance, exact teacher-row exclusion, target-disjoint split validation, and a static lesson/sham pair. | The fixed q14 content tests production of a measured record. It is not an adaptive diagnosis and does not test whether a parent-selected process intervention changes a later decision. Reuse the task/verifier and receipts, not the q14 claim. |
| `nursery_dialogue.py` | Shows the intended attempt -> correction -> child restatement -> apply shape. | Do not run it as evidence. Parent and child are the same engine; control is no-parent rather than active sham; all streams remain eligible despite the apparent admission calculation; the writer is legacy; the probe has eight instances; and the ten transparent hand-written rules recur in train and probe. |
| `rulegame.py` | Cheap UI smoke test only. | Ten recognizable rules are not a fresh task-family transfer test. The `ruleN/...` addressing also repeats a known rule class across source/apply. Historical rule-game eight-item base panels had SD 0.067, making their small deltas underpowered. |
| `agentic_parent.py` | Provider isolation, allow-listed reads, answer/leak checks, bounded calls, and a single-parent mode exist. | The current object is a sleep-boundary brief writer optimized around CompilerGym ritual metrics. Its society and sibling tools intentionally cross children, and its default documentation/topology includes two parents. Those violate the present one-parent/one-child scout. Do not expose society, siblings, gates, probes, or prior children in `P0-COACH`. |
| `parent_backend.py` | Separate stronger teacher backend and basic leak refusal. | Its answer-aware mode inserts the hidden answer into a free-writing parent prompt. Lexical scanning cannot prove that free prose transmitted no answer information. The first gate should withhold reference answers structurally and deliver only a fixed process card. |
| `life_lineage.py` / `lineage_guard.py` | Hash/ancestry tools useful for future persistent children. | They do not turn current scouts into clean final ancestors. For `P0-COACH`, a simpler and stronger rule is to create no child checkpoint at all: every root is disposable and produces no adapter/corpus. |
| `adult_controls.py` | Correct intended boundary: fresh adult ledger; no inherited childhood notes, parent turns, briefs, retrieval or lesson state; adult wake gets only the gym birth prompt. | This is a helper contract, not current evidence that a full fresh-process parent deletion has run. It is for P1/H2 after a qualified writer, not needed for no-write P0. |

Relevant source SHA-256 values at inspection:

- `nursery_dialogue.py`: `ca8da87a8b1b1980afcb95d97b36305cb2082612ca139565bb88ee6ee11cbb5c`
- `rulegame.py`: `88304996b00837ad1855e8a6661aad39e64f3beb0c0ab4491b63119e797226f3`
- `reasoning_gym_gym.py`: `da9879537d33923c9702b1a5b3d63d6a2fcb396a64e110a886bd445c33e1c084`
- `reasoning_gym_families.json`: `220071c8783ed4d608b04015c188e8b22fc5745c10f250c7fbd724dd854649ea`
- `preschool_reasoning.py`: `4b4edcb6f03c41504e6a93e660f5d1905248670dd98dc811b2107e8ddae417dc`
- `agentic_parent.py`: `87b266efb2baf96cb90a253ba9b370eea6ad768cd9063c9a85301f019db81349`
- `adult_controls.py`: `ea598a67f4ce62d3792f551c6f46e8899a5b02af954d22b862b0e3f3346b0743`

## `P0-COACH`: smallest high-information design

### Question and target

Test one narrow atom of Rohin's parenting hypothesis:

> A strong parent can look at the child's actual failed reasoning and choose a
> better next thinking move than an untargeted but otherwise matched teacher
> message; the child can restate that move and use it on a fresh homologous
> problem.

This is process teaching, not answer teaching and not post-training.

### Task material

- Use only `reasoning_gym` train families that yield useful partial feedback:
  `countdown`, `mini_sudoku`, `futoshiki`, and `arc_1d`.
- Use 32 independent source/apply blocks: eight per family. Source and apply
  seeds are disjoint, prebound, and never taken from the existing gate/exam
  ranges. Mark all 64 item IDs consumed for future selection.
- Use the frozen Qwen child with a **neutral interface-only bootstrap**: task
  statement, ACT syntax, verifier meaning, and generous token/action budget.
  Remove the present bootstrap's metacognitive answers (“predict,” “judge
  yourself,” “investigate,” and “build understanding”) equally from all arms.
- No CompilerGym identifiers, tasks, passes, scores, ledgers, adapters,
  retrieval stores, or briefs enter this experiment.

### One block

1. **Persist one source tape.** The frozen child gets the source puzzle and two
   action opportunities. Persist exact child bytes, parsed authoritative ACTs,
   public scores, prompts and generation identity once. Both experimental
   continuations begin from these same bytes; there are not two independently
   generated “matched” prehistories.
2. **Parent chooses, but cannot answer.** The exact pinned strongest teacher
   receives the source task, child thoughts, executed actions and public
   scores. It receives neither the reference answer nor the apply task. It
   emits only a `card_id` plus an audit-only rationale. No free parent prose is
   delivered to the child. “Pinned” fixes the parent's model, prompt, tools and
   notebook-update rule; it does not require amnesia. A bounded root-local
   notebook may accumulate earlier source-side teaching observations, but the
   parent sees no targeted/sham continuation outcome until all 32 card choices
   are frozen. This preserves Rohin's adaptive-parent intent without letting
   evaluation outcomes tune the measured intervention. This small test does
   not itself claim the parent improved over time.
3. **Deliver a fixed card.** The targeted continuation receives the selected
   answer-free process card. The sham continuation receives the card selected
   for another source block in the same family and pre-score bin, under a
   prebound no-fixed-point permutation. The exact card text, register, timing,
   turn count and tokenizer-counted dose are therefore matched. Card examples:
   check the demanded output form; externalize the live constraints; compare
   two candidates before commitment; after partial feedback revise one
   identified component; after a zero score change the governing hypothesis;
   stop checking after acceptance.
4. **Child authors the carrier.** Each continuation asks the child for one
   concise plan in its own words. The no-parent anchor gets an equally long
   neutral prompt and produces the same plan field. Parent card bytes and the
   audit-only rationale are never copied into that field by the harness.
5. **Short outcome.** On the source task, continue for three fixed action
   opportunities with the relevant card and child plan visible. This is the
   direct, parent-visible manipulation check.
6. **Relay outcome (primary).** In a fresh process/context on the homologous
   apply puzzle, provide only the child's authored plan. The source transcript,
   teacher/card text, parent state, source question and source scores are
   absent. Run three fixed action opportunities. This tests a child-authored
   context carrier, not a weight-carried memory.
7. **Sterile anchor.** Run the same apply item from the frozen child with
   neither parent text nor child plan. This bounds ordinary task variation and
   detects accidental state reuse; it is not another learned child.

Thirty-two source tapes, card choices and permutations are frozen before any
apply result is read. Randomize continuation order and GPU position. Common
decode seeds are logged, but inference treats task blocks—not decodes—as the
units because the current runtime has not shown byte-deterministic replay.

### Endpoints

For three action opportunities define `best@k` after each opportunity, keeping
invalid or absent actions as the prior best (initially zero), then:

```text
action_AUC = (best@1 + best@2 + best@3) / 3
```

Primary:

```text
mean_block(action_AUC[targeted child-plan relay]
         - action_AUC[yoked-sham child-plan relay])
```

Report a paired randomization interval/permutation test over the 32 task
blocks, family-stratified sensitivity, and every block—not decode repetitions
as `n`. Do not treat this small DEV test as confirmatory.

Secondary, in fixed order:

1. targeted minus sham on the direct same-task continuation;
2. targeted plan relay minus sterile frozen-child anchor;
3. valid ACT rate and missing-action rate;
4. score change between attempt 1 and attempts 2/3;
5. mechanically coded use of the selected process move and inappropriate use
   when its precondition is absent;
6. plan length, parent-card copying, answer/reference leakage, and card-choice
   distribution.

Lexical agreement, card restatement, longer thought, praise, remorse-shaped
language and parent self-ratings are never primary outcomes. More thinking is
useful only when it changes a valid decision under the generous common budget.

### Decision table

| Result | Interpretation | Next action |
|---|---|---|
| Targeted beats sham directly and through the child-plan relay | The teaching and thought-to-action links work in context. | Freeze the exact source tapes, parent decisions and grounded child continuations. Once the writer passes selectivity/retention, use these bytes in P1 without redesigning the lesson from its LoRA outcome. |
| Targeted helps directly, relay is null | Child can follow the parent but does not form a useful self-state. | Improve the restatement/DREAM-state interface; do not tune rank or training heat. |
| Targeted direct effect is null | Parent selection or task feedback is not useful enough. | Improve the card bank/teacher observations and repeat on new DEV blocks; do not blame SLEEP. |
| Targeted and sham are equal and both beat sterile | Generic structured prompting is sufficient at this scale. | Treat this as instruction scaffolding, not adaptive parenting; the parent diagnosis adds no demonstrated value. |
| Targeted helps only on the source task | The message exploits local task context rather than teaching a reusable process move. | Narrow the claim and redesign changed-case coverage. |
| Validity/action rate falls | The teaching consumes or disrupts the acting channel. | Fail P0; repair the intervention/budget before any write. |

## What may be learned before writer qualification

Permitted claims from P0 are deliberately modest:

- the exact parent selector chose process cards that improved immediate action
  relative to the exact yoked sham;
- the child authored a textual plan which carried some of that benefit to one
  fresh homologous case after parent-message deletion; and
- the effect was or was not conditional on the diagnosed failure type.

Not permitted:

- the child learned in weights;
- parenting survived context deletion (a child-authored plan is still text);
- SLEEP retained or caused the effect;
- the parent improved over time;
- a general disposition, far transfer, long-term learning, or H1/H2 passed;
- the task-disjoint child is a final deployment ancestor.

The P0 artifacts are development material. They may inform and, after an
independent writer qualification, populate a separately frozen P1 experiment;
they never initialize the final CompilerGym child.

## Continuity and fork rules for the later real child

Rohin's continuity intuition is correct if “same child” means a fixed
developmental mechanism, not a directory that absorbs every experiment.

Continue one child when only these evolve under already frozen rules:

- its own action/outcome evidence, child-authored THINK/DREAM state and LoRA;
- the one parent's bounded root-local notebook under its frozen transition;
- curriculum position under a frozen schedule or adaptive rule.

Fork from the last eligible pre-change head when any of these change:

- parent model/revision, system prompt, tools, files, skills, process-card
  bank, notebook schema/transition, or teaching visibility;
- child base/bootstrap, THINK/DREAM/SLEEP implementation, LoRA rank/heat/dose,
  compiler/admission policy, action interface, task generator/split, or metric;
- an analyst uses an evaluation result to change what the child will see.

Always make these descendants one-way and non-returning:

- any development/gate/exam clone;
- any CompilerGym or other deployment-task exposure;
- any parent-policy comparison arm;
- any writer ablation or changed-rank/recipe branch.

A parent notebook may improve within one life only under a frozen update rule.
Cross-root society, sibling summaries and shared parental memories are disabled
for this paper. The later mature pedagogy core may be frozen from development
and copied into fresh roots, but root-local parent records never flow between
confirmation roots.

## Parent deletion and the later gates

`P0-COACH` deletes only the parent's message before the primary apply case and
retains the child's own plan. Call it **child-state relay**, never parent-free
learning.

After the writer is qualified, `P1-PERSIST` must instead start a fresh process
with all parent/card text, child plan text, childhood conversation, DREAM/wake
briefs, retrieval/store/index/cache/query state and source task material
absent. The only treatment-carrier difference may be the exact child LoRA.
Evaluate both P and sham adapters ON/OFF:

```text
PERSIST = (P_ON - P_OFF) - (SHAM_ON - SHAM_OFF)
```

Only a positive conditional-use/non-use result there can say one bounded
lesson survived removal. Only after P1 should the clean child enter the
running-versus-shadow adult factorial. The full C11 guard remains reserved for
that paper-grade confirmation.

## Recommendation to Astra

Build/run `P0-COACH` as a disposable, no-training parent-policy experiment
while the writer calibration proceeds. Reuse Reasoning Gym's task/verifier and
split machinery plus the existing generation/provenance receipts. Do not route
it through `nursery_dialogue.py`, `rulegame.py`, the legacy sleep compiler, the
agentic society, or `adult_controls.py`. Its output should be source tapes,
parent card decisions, child plans, continuations, exact public scores and a
single reducer report—no adapter, no corpus promotion, no lineage head.

The design is intentionally small. It tests whether there is something worth
writing before spending GPU-hours asking whether the current writer wrote it.

## Inspected evidence identities

- Adaptive Parent v5 proposal SHA-256:
  `f3f100b68dfcdf126e9cac897a9b6198d6521e08cbfe76fc73cb8823756fa052`.
- Parenting terminal-union audit SHA-256:
  `b1779edc74fa158b2003d8805ad71d4c44bc9c628524aeb8b1b499fba81f8c84`.
- B0 attempt-2 terminal audit SHA-256:
  `38969b50e01a2f56b6a8d80b4229dc14ccebd660443804c7fb60a38bab036791`.
- Simple-hygiene ruling:
  `research_notes/2026-09-11_simple_hygiene_now_c11_later.md`.
- Lifetime factorial audit:
  `research_notes/2026-09-12_lifetime_parenting_factorial_fresh_audit.md`.
