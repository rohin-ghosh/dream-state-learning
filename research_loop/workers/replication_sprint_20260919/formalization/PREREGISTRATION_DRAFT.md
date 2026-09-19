# Bounded parenting/consolidation replication

**DRAFT / NOT REGISTERED / NOT LAUNCHED — September 19, 2026.**
This specifies a doable pilot, not a promise that its ingredients are currently
integrated. The [formalization](FORMALIZATION.md) defines its estimands.
`proposal.json` records fixed proposal parameters and intentionally unfilled
execution bindings. Resolve those bindings, timestamp/hash the final protocol
and scoring code, and retain that immutable version **before any scored probe
or outcome-based model selection for this experiment**. No new approval layer
is proposed for invariant-preserving builder work.

## 1. Question, replication unit, and minimum design

Primary question: under the same strong parenting policy, does developmental
LoRA consolidation improve parent-free fresh-context performance at a fixed
developmental age relative to a frozen sibling?

Use **three independent seed blocks**, each born prospectively from the same
pristine, provenance-verified frozen base, with independent developmental RNG,
task-instance order, sampling, and optimizer/adapter initialization across
blocks. Within each block share the initial adapter, task schedule, environment
opportunities, and resource caps; randomize arm-to-device/order assignment.

| Arm | Development parent | Development updates | Purpose |
|---|---|---|---|
| PL | Strong contingent teacher | Pinned LoRA sleep recipe | Proposed developmental treatment |
| PF | Same teacher policy and help budget | None | Strong scaffold/frozen-sibling control |
| UL | None; same environment information | Same recipe as PL | Ordinary experience-learning comparator |

Nine developmental trajectories, **three independent lineages per arm**, are
the core. Forks, checkpoints, test items, and two evaluation decoding seeds are
not additional training replications. Descendants of C2sleep51 share selected
history and cannot stand in for independent births. A three-block pilot has
wide uncertainty; preregistration prevents selection, not low statistical power.

All arms share tools, compaction, task wording, common birth/task instructions,
base, adapter capacity, and child token caps. The common lifecycle text must be
truthful for both updating and frozen arms; neither gets an extra test-time
checklist. PL and PF receive equal **opportunities** for guidance, not identical
messages: their errors differ. The parent sees only its own child's development
history and permitted environment outcomes. Parent identity, model/settings,
brief, fallback rules, and per-turn budget are pinned. UL receives no disguised
teacher in its environment messages. All arms already share the common scaffold,
so PL-versus-UL estimates parenting beyond that scaffold, not versus no prompt.

## 2. Fixed, diverse development window

Measure **48 cycles**, with a natural sleep after each four cycles (12
boundaries), maximum **512 THINK + 512 ACT child tokens per cycle**, and at most
one **256-output-token** parent turn per cycle in PL/PF. Requests and revisions
consume the same cycle budget; no unlimited retries or hidden human coaching.
Pin the existing optimizer/rank/learning-rate/replay recipe before running; do
not select a new recipe using evaluation results. PF traverses matching nominal
boundaries with zero updates. Count actual rows, presentations, tokens, updates,
and costs rather than pretending the realized histories are identical.

The task schedule is fixed before sampling so adaptive parenting cannot
silently replace one arm's assigned task with an easier one:

| Cycles | Sequence | What persists |
|---|---|---|
| 1–12 | Checkable arithmetic and sorting | Demand an actual calculation/artifact; teach checking and a reusable correction |
| 13–24 | Repeat math, reading, math, reading-linked writing | Preserve math; use short sourced development excerpts, the six reading steps, and a later recall question |
| 25–48 | Repeat math, reading, grounded self-probe, writing, development game, recall | Keep diverse external objects; parentheses/checksum games only; recall occurs after a logged sleep |

Specify the actual 48 task IDs and all excerpt/prompt bytes in the registered
manifest. Each task cycle has one primary requested artifact; do not bundle a
memory question with unrelated writing. Reading feelings/model-philosophy are
developmental material, not measures of sentience or primary success. Recall
is coded correct-supported / honest unknown / invented / no answer against its
source; a response saying “I remember” is not its own verification.

**Teacher policy draft:** ask what the child knows and what evidence is missing;
request a relevant check; credit a verified step; make the next ACT concrete.
After a promise without an artifact, quote the promised artifact and request
it now. After repetition in two consecutive responses, explicitly contrast
the repetition with the assigned external object and vary the question/register.
Show language drift and request a self-check, without filtering the child's
rows. Demonstrations may use distinct development examples, not the answer to
the scored target. Do not pretend to be Rohin or fabricate outcomes. The same
trigger policy applies to PL and PF; semantic choices remain with the teacher.

This is a fixed-window operationalization of diverse parenting, **not** a test
that the entire earlier six-stage milestone schedule is optimal. Keep that
distinction in the paper. Any scheduler or prompt repair receives a new epoch;
never relabel an old trace as having received the repaired treatment.

## 3. One primary fresh-task assay

Proposed family: **unweighted shortest-path problems on small finite graphs**,
with equal fixed difficulty mix and an exact CPU checker accepting every valid
shortest route. The four-family R213 environment provides a candidate checker,
but its public fixtures are DEVELOPMENT-only. Do not reuse them as held-out
evidence or claim a sealed generator already exists.

Before registration, bind a private generator/checker pair and a finite graph
panel, including disconnected and non-unique-shortest-path cases. Require an
independent CPU oracle agreement check on construction. Reserve this family
entirely from these new lineages' development: no graph/path demonstrations,
teacher notes, or task-selection decisions drawn from the report panel. This
family is “unseen in experimental development,” not new to the pretrained base.

At age **48 cycles / 12 completed nominal sleep boundaries**, evaluate each
arm on **24 panel items × two decoding seeds**, each with a fresh context and
at most 512 THINK + 512 ACT tokens. Use the same item/seed panel within each
block and counterbalanced difficulty panels across blocks. The panel and RNG
bindings are fixed before any model scoring. A fixed task-local action contract
asks for a route or “unreachable”; no advice about self-reflection is added.

Copies have no teacher/peer mailbox, developmental transcript, working-state
notes, retrievals, writable shared memory, or parenting birth checklist. Pin
and audit the exact neutral evaluation prefix and all accessible surfaces.
The parameter state is the intended carry-over; tool definitions and task
instructions are identical across arms. Source lives are not context-cleared.
Probe updates are disabled, raw outputs stay in evaluator custody, and neither
answers nor report scores return to parents or development data.

**Endpoint:** fraction correct in the first committed ACT. Use the same pinned
literal route extractor and checker in every arm; no LLM “best interpretation,”
different decoder, or selective salvage. Missing/ambiguous artifacts, a quit,
or a request for an absent parent use the opportunity and score zero, with
separate reason codes. They do not kill or reset a source life. A malformed
answer is an observed task failure, not an unreported dropped example.

The primary contrast is `Delta_H1 = mean_b(Y_PL - Y_PF)`. Predeclare a **10
percentage-point** difference as a useful pilot-scale effect, not a significance
threshold, power guarantee, or new paper claim. Report `Delta_P = PL - UL` and
all absolute scores regardless of sign. A positive primary contrast without a
parenting advantage supports consolidation under that policy, not a unique
benefit of parenting versus ordinary experience training.

## 4. Diagnostics: corrections, sleep, and developmental age

Use the L0–L3 rubric from the formalization on development traces. Link actual
parent/Tool delivery to rendered REQUEST and committed ACT, with timestamps,
hashes, and feedback identity. Log whether the correction was visible, not
merely published; log actual parent tokens/calls and unparented gaps. Also count
content artifacts, intention-only acts, requests for help, repeated output,
language drift, and valid/incorrect/missing checks. Review failure traces as
well as attractive examples, blinded to condition where possible.

Optional fixed-budget diagnostic copies at ages 0, 16, and 48 cycles use
separate disjoint panels, all registered in advance. Age means declared
opportunities and committed sleep boundaries, accompanied by cumulative child
tokens, training tokens, updates, and elapsed time; “hours old” alone is not a
matched developmental age. The age-48 panel remains primary even if age16 is
better. Do not peek at intermediate scores to change this cohort's parenting.

For direct retention, preserve pre- and post-final-sleep states without
interrupting the source; run identical probes on both and matching PF states.
Separate an explicit-context positive control from the fresh-context test.
For adapter attribution, compare the learned adapter to its verified birth
adapter on disposable copies with otherwise identical test inputs. These are
secondary checks requiring separately accounted inference caps; no assertion
that a correct answer alone establishes adapter retention.

## 5. Bounded H2 extension, decided before its scores are opened

From each of the three PL and three UL endpoints, fork two finite deployment
copies with learning on/off: **12 deployment trajectories**. Both begin from
the same checkpoint and task-local context within each pair; neither has a
parent. Environment feedback remains available every round, including an
explicit “no judgment, reason” receipt on tool failure. Teacher requests receive
a truthful unavailable response, never an infinite wait on silence.

Run **16 new adaptation opportunities**, at most 1,024 child tokens each;
continue the pinned sleep recipe every four opportunities in the update-on
copies, and record zero updates in frozen copies. Use new adaptation graphs,
not report-panel graphs. Freeze weights only in the declared control copies,
not in ongoing source lives. At experience counts 0/4/8/16, generate
read-only report copies and score **8 disjoint fresh items × two decoding
seeds**, at most 1,024 tokens per item. Later panel difficulty is matched;
panels are counterbalanced, never chosen for increasing easiness.

Register the slope and interaction `Gamma` defined in the formalization,
intercepts, endpoint changes, and uncertainty. Experience opportunities are
the primary x-axis; actual generated tokens and training cost are separate
secondary efficiency axes. A positive intercept alone is not H2. This compact
extension tests further learning on one family, not improvement of a universal
learning algorithm. Existing captions may remain an explicitly exploratory
side measurement with one pinned judge epoch and deduplicated strings/pixels;
they are not substituted for an unfavorable primary assay.

## 6. Secondary tapering comparison

Tapering is optional and **not presumed necessary**. Use matched experimental
descendants of each prospective PL checkpoint, announce each parenting schedule
to the child, and maintain environment information. A feasible 12-cycle pair:

- **Taper:** guidance on cycles 1, 2, 3, 4, 5, 7, and 9, then none on 10–12.
- **Abrupt:** guidance on cycles 1–7, then none on 8–12.

Both get seven calls at the same cap and the same long-horizon policy. Guidance
at the last assisted turn plans across several attempts: what to investigate,
what would disconfirm an approach, what to do if feedback is missing, when to
branch, and how to check progress. The child is told the next available turn
and that missing teacher help is not an environment verdict. Do not simultaneously
lower learning rate in just one arm: keep plasticity matched to isolate this
schedule comparison. Test plasticity reduction separately if desired.

Record dependence on reminders, enactment, and correction reuse, then run
matched parent-free transfer probes. Equal call counts do not equate realized
teacher information; log all content and cost. The schedule comparison includes
timing/recency effects, not a pure latent “independence” intervention. Descendant
pairs are clustered by original block; their shared upbringing is not new
independent replication. An accidental outage is never a taper treatment.

## 7. Analysis and failure handling, fixed before scoring

1. Average the two decoding seeds and the declared item set within each lineage;
   report all three paired block differences, their mean and range. A paired
   t interval with two degrees of freedom may be shown with its small-sample
   normality assumption, not promoted to a robust significance claim. Items,
   ACTs, checkpoints, and sampling seeds do not enlarge the training sample size.
2. Use one primary endpoint/timepoint/contrast. Other comparisons are labeled
   secondary or exploratory; no “best age,” seed, caption, or favorable subset
   replaces the primary result. Report every arm, failed trajectory, and amendment.
3. A generated wrong/intention-only answer is a scientific outcome and stays
   in the denominator. Infrastructure failure before a valid response is
   **missing execution**, with reason, not secretly a wrong cognitive answer
   or an omitted run. Report planned/completed counts and worst/best-case
   bounds for missing scheduled scores. Show completed-only scores explicitly
   as such; do not claim an identified effect from differential delivery loss.
4. One exact-state infrastructure recovery is allowed per bounded cell, with
   original RNG, IDs, and an auditable no-duplicate result rule. Never retry a
   valid low score or an unfavorable sampled completion. Ambiguous publication
   is reconciled before replay. Failed/partial artifacts remain archived.
5. No stopping on efficacy or futility. Stop only the bounded evaluation at
   its declared budget or a genuine safety/lease/custody constraint; log why.
   An incomplete paired comparison remains incomplete, not a win by its survivor.

## 8. Costs, continuity, and refinement without leakage

| Component | Child generation ceiling | Parent output ceiling |
|---|---:|---:|
| Development: 9 × 48 × 1,024 | 442,368 | 6 × 48 × 256 = 73,728 |
| Primary transfer: 9 × 24 × 2 × 1,024 | 442,368 | 0 |
| Optional H2 adaptation: 12 × 16 × 1,024 | 196,608 | 0 |
| Optional H2 panels: 12 × 4 × 8 × 2 × 1,024 | 786,432 | 0 |

Separately account input/prefill tokens, parent model/reasoning usage as
reported by its provider, tool/judge tokens, authentic training tokens and
presentations, optimizer steps, GPU-seconds by device type, and all failed work.
Do not pad short generations to pretend realized token equality; report actual
usage and common caps. Additional age/retention/taper probes need explicit caps
before inclusion. Throughput and lease headroom must come from a training-only
calibration, not an invented wall-time promise. Schedule sequentially if needed;
do not displace a kept life to fill the proposed matrix.

**No-pauses/checkpoints:** preserve ongoing lives and the last exact durable
adapter, optimizer, RNG, working state, inbox/frontiers, and records. Snapshot
before a curriculum/policy change; a failing live treatment can receive a logged
development-only refinement while its earlier checkpoint is held. Never
silently roll back, reset a lineage, relabel its age, or erase deterioration.
Fork a new named, ancestry-linked treatment epoch when changing the policy.
Bounded evaluation copies and measured windows may finish; the source life
continues and is not blocked on a scoring queue. Recovery gaps are reported, not
called continuous operation. Respect existing confinement and lease deadlines;
this proposal neither extends leases nor removes access checks.

**Learning from midlife C2:** inspect training-visible history around sleep51
for candidate teacher moves, grounded tasks, artifact production, and actual
feedback visibility, including both successful and failed episodes. The
checkpoint was selected after seeing performance, so its favorable curve is
exploratory and winner-selected. Do not use evaluated captions, acceptance
rankings, report answers, or test-selected prompt variants to train or seed a
new “clean” cohort. Frozen-base trajectories reproduced by the same seeds are
not extra independent controls. A new refinement suggested by a scored result
starts a new version and a new untouched evaluation panel; old data stays
exploratory. Parents remain blind to final/report scores and answer keys even
when the analyst can see them.

**Minimal measurement readiness:** verify a genuine feedback→REQUEST→ACT
receipt, a sleep row/optimizer/RNG receipt with correct loss provenance, and a
parent-free probe surface audit on training-only fixtures. If a link is broken,
repair and epoch it while other useful work/lives continue. These are concrete
validity checks, not an elaborate review gate or a reason to idle all work.

## 9. Items to bind before this becomes a preregistration

- Exact base/tokenizer/birth adapter, source and runtime hashes; parent provider,
  model/settings/prompt; task and fallback schedule; immutable treatment IDs.
- Independent block RNGs, task panel/generator/checker/split hashes, decoding
  RNGs, extraction/rubric code, and private evaluator custody. No keys or sealed
  items in public child-visible files.
- Existing optimizer/sleep recipe, row masking proof, update counters, source
  checkpoint manifests, continuation method, hardware allocation and lease cap.
- Which optional modules are included, their token/compute caps, analysis code,
  missingness/recovery policy, and the timestamped hash of this frozen protocol.

These are currently **unbound**, not implicitly satisfied by this document.
Major new scientific claims, thesis changes, or invariant changes remain
reserved for Rohin. This workstream performs no implementation, run, commit,
publication, or editing outside its assigned directory.
