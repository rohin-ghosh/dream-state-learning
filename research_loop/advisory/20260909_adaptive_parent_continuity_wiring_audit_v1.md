# Adaptive-parent and child-continuity wiring audit v1

Date: 2026-09-09

Status: source-only audit. No code, process, model, benchmark, adapter, child,
resource, or external state was changed. This is evidence for the pending
Fable--Codex design discussion, not a protocol or execution authorization.

## Bottom line

The exploratory classroom code already contains useful pieces of Rohin's
direction: a stronger server parent with bounded nonparametric memory, one
shared child snapshot fanned into parallel task sessions, pooled child-authored
experience, one clean-base cumulative write, and saved round checkpoints.

It does **not** yet implement the requested long-horizon teaching learner or a
strict never-regress child lineage:

- the parent learns only from immediate post-versus-pre admission deltas;
- delayed exams and later transfer are not written back to the parent ledger;
- candidate promotion is gated against the base but not necessarily against
  the previous child checkpoint;
- code/mechanism identity is not sealed across rounds; and
- the current classroom has fixed curriculum mixture/anchors rather than the
  still-pending jointly adjudicated scaled-THINK and parenting semantics.

## What is actually present

### Parent improvement without parent-weight updates

`organism_v6/parent_backend.py` defines a `ServerParent` backed by a stronger
model and a `ParentLedger` plus bounded `parent_playbook.md`. Every intervention
and immediate admission delta can be appended to the ledger. At the end of a
round, `rewrite_playbook` summarizes recent admissions/interventions into
mastered skills, misconceptions, interventions that helped or confused,
coverage, next topics, and open teaching hypotheses.

This is genuine nonparametric parent adaptation. It does not modify parent
weights.

### One composite developmental lineage

`organism_v6/classroom_round.py` resolves the last committed adapter as the
round snapshot. Every classroom branch acts from those same bytes; branches do
not update weights independently. Their admitted child rows are pooled, mixed
with older rows, and used for one next adapter. A later round resumes from the
latest `DONE` adapter, walking backward over explicitly rejected rounds.

Scientifically, this is **one composite child lineage with data-parallel
experience**, not `N` independent children. Classroom branches and task
episodes are repeated observations within the lineage and cannot be used as
population replication.

### Parent text versus child targets

The stronger parent may be answer-aware for diagnosis, with a leak scanner and
process-only fallback. Parent utterances are stored as `kind="parent"` but are
not selected as training targets. On an admitted pair, the child's restatement
and eligible child thought continuations may enter the corpus. Thus the current
path mostly preserves the intended parent -> waking child -> child-generated
continuation boundary.

## Missing short-to-long teaching feedback

The live phase records one immediate comparison: whether a single post-advice
task score is at least the pre-advice score. `ParentLedger` receives that delta,
and the next playbook may react to it.

The exam phase writes `exam.json` locally but never appends delayed retention,
transfer, calibration, ritualization, or regression results to
`parent_ledger.jsonl`. Consequently the parent cannot learn that an
intervention looked helpful immediately but disappeared, overfit one rule
surface, or caused a later regression.

The requested parent learner needs two distinct evidence clocks:

1. **short horizon:** comprehension/restatement, changed next attempt,
   information gained, and immediate world outcome; and
2. **long horizon:** spontaneous later use without a cue, transfer across task
   surfaces, retention after intervening sleeps, calibration, and side
   effects such as ritualization, indecision, or reduced action.

The parent may then keep, revise, space, or retire a teaching hypothesis. This
remains development behavior; confirmation must freeze the parent or
prospectively freeze the full adaptive rule.

## Missing strict continuity guarantees

The round manifest records rank, learning rate, epochs, classroom/lesson
counts, prior snapshot path, corpus hash, and ledger hashes. It does not bind
the source bytes, compiler/trainer identities, mask semantics, writer contract,
eligibility policy, model/tokenizer revisions, or architecture-change root.
Nothing prevents a changed mechanism from being resumed under the same lineage
directory.

The exam computes `on`, `off`, and optional `prev`, but promotion requires only
that the candidate's score not trail the **base** by more than `0.03` and that
its action syntax not trail base by more than `0.10`. The reported `prev` score
does not gate commit. A candidate can therefore replace a stronger previous
child while remaining near base.

Rohin's continuity rule requires:

- same mechanism + new subject/parenting/task -> continue the canonical child;
- changed THINK, DREAM, SLEEP, writer, rank/capacity semantics, mask,
  eligibility, or promotion law -> fork an immutable sibling from the last
  common snapshot;
- no changed mechanism may silently overwrite the canonical developmental
  lineage; and
- promotion must compare against the previous child on preservation and
  relevant competence, not only against the raw base.

## Admission and repetition limits

Immediate `post >= pre` is a noisy one-pair development heuristic, not evidence
that the correction caused learning. It is valid for inexpensive exploration
only if delayed tests independently judge persistence and transfer.

Repetition can be valuable, but lexical restatement rate is not mastery. The
useful outcome is spontaneous, situation-sensitive application after cues
fade. The parent should track both repeated rehearsal and delayed unprompted
use so that it can distinguish a forming habit from a copied ritual.

## Scaled THINK is not implemented here

The current child gets a fixed eight-tick episode. It does not separately
allocate parallel breadth, sequential depth, and post-outcome reflection, nor
does it learn when to open, merge, or stop routes. Data-parallel classrooms are
parallel **experiences**, not parallel thoughts about one state.

Those mechanisms remain intentionally unselected until the requested direct
Fable--Codex discussion is returned and adjudicated.
