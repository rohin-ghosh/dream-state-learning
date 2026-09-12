# Watcher audit: Astra guards and post-outcome path (2026-09-12)

Status: **REWORK before clean parenting/H2 or post-outcome science.** Astra's
writer-seed replications are separate synthetic diagnostics and may continue;
this note does not invalidate or pause them.

Three fresh read-only audits inspected commit `f2e5b65e` and the current
post-outcome path. Their findings were reconciled against locally replayed CPU
tests.

## Parent visibility

The numeric gate-score path is repaired. The parent now receives categorical
write decisions rather than `candidate`, `base`, `floor`, or report-panel
values. The loopback/mock suite passes independently:

```text
python3 -m pytest -q tests/test_agentic_parent_mock.py
27 passed
```

Two boundaries remain before any new parented run can be called clean:

1. `default_society_dir()` is global, and `society()` / `other_children()` can
   expose one lineage's briefs and summaries to another. A task-exposed child
   can therefore influence a nominally clean child. Clean confirmation should
   begin with fresh root-local empty parent state; sibling/society reads stay
   disabled unless their complete ancestry is admitted.
2. Parent advice repeated by the child can later become a full-loss NOTE
   target. This is not direct parent-text training, but exact normalized parent
   lines in loss-bearing targets need a refusal/audit, with paraphrastic echo
   measured as a mediator rather than silently called leakage.

Historical RP/R4 lives did not use the repaired agentic-parent score path, so
that defect does not newly invalidate them. They remain task-exposed,
exploratory artifacts and cannot seed a clean lineage.

## Lineage guard

`organism_v6/lineage_guard.py` is a useful low-level
`FILE_CLOSURE_VALIDATED` primitive: recursive hashes, strict `UNEXPOSED`
declarations, no symlinks/traversal, cycle checks, and a strict schema. Its 30
tests plus the 17 input-preparation tests pass independently when the macOS
temporary root is canonical:

```text
TMPDIR=/private/tmp PYTHONPATH=tests python3 -m unittest -v \
  tests.test_lineage_guard tests.test_prepare_memory_seed_run
47 passed
```

The default macOS temporary path (`/var/...`, a symlink to `/private/var/...`)
is deliberately refused, so the test suite currently needs the canonical
`TMPDIR`; this is a reproducibility/portability issue, not a Linux-VM launch
failure.

The module is not called by a launcher and validates truthful declarations,
not semantic cleanliness. It lacks mandatory entry/plan pins and closure over
domain/split/purpose, actual adapter construction, code/config/seeds,
parent/session/society state, nursery tape, and score-driven selection. It
also cannot stop bytes being swapped after validation.

Minimum clean path: exact frozen base -> new empty root -> isolated
target-blind nursery -> receipted sleeps. Preflight must occur before any
output creation, backend/parent initialization, model load, or network call;
the consumer must use the bound file handles/bytes. Evaluation forks become
one-way `TASK_EXPOSED` descendants and cannot promote back into the clean head.

No existing bootstrap/adult is currently clean-eligible. In particular,
R2/R3/R4/R5/RP, bootstrap v1-v3, `lineage3_*`, and `parent_scout_*` are
exploratory or development artifacts, not clean ancestors. No R6/R7 artifact
was found.

## Post-outcome record gate

The current enforced gate is not provenance-safe. `judge_record()` derives
execution facts from the candidate `note_after` row itself rather than joining
an earlier authoritative ACT receipt. Thus forged, orphaned, pre-outcome,
unexecuted, duplicated, and mismatched rows can satisfy the 64-record minimum
and enter training. The full harness-authored prefix is also loss-bearing.

Required repair before launch:

- unique visit/tick/action execution receipt from the actual executed ACT;
- exactly one earlier ACT joined with exact action, outcome, and measurement
  agreement;
- child-generation receipt (model, seed, decode, prompt/output hashes);
- first-person child articulation plus attributable result;
- 64 distinct newly admitted records, ledger-prefix hash, transactional
  gate/compile state, and crash/resume tests;
- fresh-root/base/no-parent assertions and held-out identifier scans over
  record text;
- mask the harness prefix or train only the child continuation.

The clean factorization is (1) a frozen slot-only feasibility/cost scout, then
(2) one fit on the exact admitted corpus with paired fresh-context Scratchpad
ON/OFF, or exact RUNNING versus train-but-do-not-mount SHADOW. A positive pilot
would establish only prompted record production and one-cycle carriage of
record-writing behavior—not outcome learning, parenting, H1/H2, connected
memory, or improved action.

## Live state at audit

At the read-only poll, A1 S1/F training seeds 2 and 3 and A2 CF attempt-2
training seeds 0 and 1 were live on node 2; the remaining A2 seed was queued.
There was no Astra `summary.json`. Five inherited writer pretests also had no
terminal `summary.json`. This is a verified wait, not a result.
