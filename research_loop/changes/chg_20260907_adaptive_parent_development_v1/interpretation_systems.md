# Fresh interpretation A: adaptive-parent systems

Date: 2026-09-07

Status: read-only interpretation. No implementation or scientific execution.

## Core object

Each committed developmental age is a joint state:

`J_k = (C_k, P_k, M_k, E_<=k)`

- `C_k`: the child checkpoint, the only learned parameter state.
- `P_k`: bounded, content-addressed, nonparametric parent teaching state used
  by a separate strongest-permitted fixed-weight teacher.
- `M_k`: exact THINK/DREAM/SLEEP mechanism version.
- `E_<=k`: canonical immutable public evidence.

Development updates the parent's teaching state and writes the child. Final
evaluation seals the mature initial joint state and clones isolated roots.

## Minimal persistent parent

Use an append-only `parent/events.jsonl` plus a bounded `parent/state.json`.
The event log keeps every intervention, child restatement, public result,
exam, compiler/write decision, rollback, and proposal. The active state is a
validated projection containing the exact teacher spec, mechanism and child
hashes, developmental age, curriculum coverage and difficulty, independence
schedule, evidenced misconceptions/masteries, active teaching hypotheses,
predicted effects, confidence, evidence references, intervention-response
summaries, and open questions. Raw evidence is never lost; only the active
projection is bounded.

The parent proposes a source-bound state patch. Deterministic validation checks
referential integrity and exact hashes before atomic promotion. Continuity is
therefore reproducible from the repository rather than dependent on a provider
chat transcript.

## Round transition

1. Load the committed joint state. The parent receives its bounded state plus
   deterministic retrieval from the event/evidence ledgers and produces a
   hash-locked lesson plan and admission rule.
2. Fan out short, isolated classrooms from the same child and parent state.
   Branch-local conversation may evolve, but child weights and canonical
   parent state do not update inside branches.
3. Validate public dispatches/outcomes and apply the predeclared admission
   rule. Merge the exact set-union of admitted evidence, never adapters.
4. Compile provenance-preserving child-native continuations. Parent text may
   condition the child under the agreed visibility rule but carries no loss.
5. Make one cumulative clean-base candidate child write. Compare it to the
   previous committed child on interface, absorption, retention, no-harm, and
   scheduled development exams.
6. Commit or roll back the child transactionally. Advance the parent state once
   from valid pedagogical results, including real failed interventions and
   child rollbacks; exclude infrastructure-invalid observations.
7. At maturity, seal child, parent, mechanism, teacher config, split, budgets,
   and analysis.

## Evidence and lineage

One evidence ID denotes one committed public action/outcome dispatch, not an
episode. Paraphrases, replay views, contrasts, and other compiler derivatives
retain their source evidence IDs. Canonical evidence count is separate from
the deterministic training-dose multiset.

Every transition has a content-addressed manifest for the parent and child
inputs/outputs, mechanism/code/config, round plan, branch assignments, seeds,
evidence-union hash, compiler/views/dose hashes, exact models, train receipt,
canaries, exams, decision, and rollback reason. Mechanism or teacher-spec
changes fork lineage; ordinary evidence-backed pedagogy updates advance it.

## Current implementation gaps

- The current classroom uses the child adapter backend as both child and
  parent; it needs a separate strongest-model parent backend.
- There is no persistent parent teaching state.
- Evidence identity is too coarse and cumulative history is reconstructed from
  sampled corpora instead of exact canonical evidence.
- Admission can still admit unrelated rows from an episode.
- The candidate gate compares against base rather than the previous child.
- Candidate training/commit is not a complete atomic transaction.
- Exact model, tokenizer, trainer, parent, child, and artifact hashes are
  incomplete in lineage receipts.

## Decisions exposed

The exact teacher model/config and upgrade rule; final root-local update
semantics; answer/process visibility and covert-answer audit; parent visibility
in training; the boundary between a parent-state revision and mechanism fork;
state caps/retrieval; dev panels/stopping; evidence-bound rank selection; and
exact implementation/execution scopes require explicit closure.

