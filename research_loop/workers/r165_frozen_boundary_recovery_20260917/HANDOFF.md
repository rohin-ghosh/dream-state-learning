# R165 frozen sleep1 boundary repair — September 17, 2026, 07:22 UTC

**Boundary-only CPU preparation is ready. Nothing has been applied to the live
root. GPU readmission is not yet executable under the original R158 admission
contract; do not issue/reuse a GPU GO for this candidate.**

## Declared and actual write set

- `gpu/orch_r165_frozen_boundary_recovery.py`
- `tests/test_orch_r165_frozen_boundary_recovery.py`
- This worker receipt directory.
- New inactive remote root only:
  `/localhome/local-rohing/orch_r165_frozen_boundary_recovery_20260917/candidate1`.
  Its source is an exact candidate5 closure copy with only the matched-stream
  predicate/import changed and the R165 helper added. All other bytes, including
  native, guard, scanner, readout custody, and matched-native runtime, are unchanged.

No protected source, checkpoint, journal, initial state, old failure, old once
marker, parent, R162 service, or running learner was edited. No GPU probe, model
construction, generation, training, signal, or restart was performed. Main owns
R163; this worker did not inspect it.

## Stable implementation and tests

Helper SHA256: `ccd0baad8550a3d7e1912d015dc57071ec9214a5a1f2b13ca8c161b0ae6e909f`.
Tests SHA256: `2c935292306e07deff5b187742a26e0d0a259f2a06fcedb3bf2312c589c09043`.

The source renderer accepts the exact candidate5 stream SHA
`99f1fc1b1c02d789d7d22e58cb98f2e36cd43f051e5e7a08b1afcabde7ed2866` and native SHA
`bcd716db469665d6c2070ed46d4b910d619b7366b66af2891c9ed71a5e069af6`. It requires a
complete original inventory, refuses an existing destination, preserves original
bytes, and verifies the complete resulting inventory. The receiving stage also
checked every original Python file against the actual original GUARD source pins.

The repaired predicate always revalidates both actual COMMITs and native raw
checkpoint hashes. It requires identical safetensors/model-file bytes and actual
CPU tensors, identical other adapter files, and the entire parsed config after
sorting **only** a nonempty list of unique string `target_modules`. Unknown config
fields remain part of equality. Numeric/type, rank, alpha, dropout, module
membership, and other-list ordering changes are not normalized away.

Both checkpoint metadata and actual optimizer payload must have integer zero
steps and an empty optimizer state. Full optimizer groups, parameter order, and
experiment must agree. Actual Python/CPU/CUDA RNG payloads are retained; RNG is
not incorrectly required to equal initialization after generation. Existing
recorded adapter-state and all no-update/exposure predicates remain in place.

CPU evidence:

- Node4 actual Torch+safetensors, `CUDA_VISIBLE_DEVICES=` and Python `-B`:
  **27 tests PASS, 0 skips, 0 errors/failures**, CUDA uninitialized. Includes real
  checkpoint mutations, actual MatchedJournal append/restore, full completion
  against a temporary fixture only, duplicate rejection/no-retry receipt,
  pending-state rejection, and unchanged future frozen receipt checks.
  Reproducible receiving command:
  `env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r165_frozen_boundary_recovery_20260917/candidate1/source /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r165_frozen_boundary_recovery_20260917/candidate1/receiving_tests2.py`
  Log: `RECEIVING_CPU_candidate1_regressions2.log`.
- Local `python3 -B -m unittest tests.test_orch_r165_frozen_boundary_recovery -v`:
  14 stdlib tests PASS; 13 Torch tests skipped because local Torch is absent.
  These are the same tests actually exercised on node4, not untested skips.
  Log: `LOCAL_CPU.log`.
- Existing `python -B -m pytest -p no:cacheprovider -q tests/test_orch_r150_matched_stream.py tests/test_orch_r150_matched_native.py`:
  **141 PASS**, log `LEGACY_CPU.log`. Legacy source files were not edited.

## Actual read-only preparation

Remote receipts are under the candidate1 directory. Exact local byte copies are
in `candidate1_inputs/`:

| Receipt | SHA256 |
| --- | --- |
| `CPU_REGRESSIONS2.json` | `8c47131f51c32c703c76f2fb5626769263f39a25f9a35e750813260bf73b7b30` |
| `SOURCE_REPAIR.json` | `4cea74e84b136049976221d09bd06b4c39975a5d4a8be9cc33c0c4e638e9244b` |
| `PREPARED_BOUNDARY.json` | `1c393cb7db1564a18faa67aada40e1cdc5210d595887f3d3cee7a821e90b6822` |

`prepare` ran successfully against the **actual original frozen root** without
opening its writer lock or mutating files. It binds original failure, exit,
clean-empty lifecycle, initial and orphan COMMIT hashes, journal manifest and all
28 record/intent files through record13, exact original plan/cohort, full source
inventories, and one proposed transition digest:
`4d842d1a4e037560067a5d3dd7b339d040dea1d89aff1aef5575f6c2d8394941`.

The selected orphan COMMIT is
`1aa0ab173c105e880c5b8da7ce697d57113c49d6c6536255b15cd4a3d443b977`.
Its optimizer+RNG payload remains
`ac936284676923e264bfa5d12fbb0eb39f7f584231ce0ff3a30ce4705809915c`.
No copy or rewrite of that checkpoint is proposed.

## Exact boundary-only Main GO

`MAIN_GO_PROPOSAL.json` is explicitly **not an authorization**. Its
`required_boundary_GO` gives the exact accepted six fields. Main chooses current
`not_before` and short future `expires` (both numeric Unix seconds; expiry no later
than existing wall `1789646400`, September 17 12:00 UTC), writes a NEW GO file, and
provides its SHA. It binds the prepared receipt above and action
`COMPLETE_MISSING_SLEEP1_ONLY_NO_GPU` on host `[REDACTED_HOST]`.

Only after that GO, the command is:

```sh
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/localhome/local-rohing/orch_r165_frozen_boundary_recovery_20260917/candidate1/source \
  /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r165_frozen_boundary_recovery complete \
  --prepared /localhome/local-rohing/orch_r165_frozen_boundary_recovery_20260917/candidate1/PREPARED_BOUNDARY.json \
  --prepared-sha256 1c393cb7db1564a18faa67aada40e1cdc5210d595887f3d3cee7a821e90b6822 \
  --main-go "$NEW_MAIN_GO" --main-go-sha256 "$NEW_MAIN_GO_SHA256" \
  --receipts /localhome/local-rohing/orch_r165_frozen_boundary_recovery_20260917/candidate1/boundary_attempt1
```

The operator rechecks the prepared evidence, creates a new once receipt outside
the life, takes the existing journal's exclusive writer lock, rechecks evidence
again, and appends only `SLEEP_COMPLETE` using the repaired original journal
validator. It preserves all prior record bytes, carry, history, pending-row
contents, experiment, counters, cohort and root. Failure retains
`FAILED_OR_UNCERTAIN`/`no_retry`; an uncertain append is not replayed. It does not
construct a child or dispatch readouts/GPU work.

## Saved-boundary resume/admission proposal and blocker

The machine-readable proposal specifies physical6 only, UUID
`GPU-06b31c8f-7a96-d812-23f3-df3444d95397`, original root, original plan SHA
`3ad87461ea05a9893cca1ad4ca0b6e4a927c17e757e7e3a1263085fb85eb1c44`, original cohort SHA
`da04b4cd814f6f695ca49a1ace66f9378039f6166d04e26bbd27ed7692ad0b4b`, a new control and
attempt directory, `phase=run`, `resume=true`, unchanged wall/lease, and exact
orphan checkpoint and repair-manifest references.

**Do not simply rerun R158/R160.** R158 `validate_extra` explicitly rejects resume
with `exact_node4_arm_assignment_fresh_only`. In addition, original guard
`frozen_source_location` requires its loaded source directory to equal original
`plan.source_root`. Changing that plan field would violate saved stream/cohort
identity. No flag/environment masquerade, source-root relabel, ignored rejection,
or permissive validator has been implemented.

The next narrowly scoped admission implementation must keep original plan/cohort
and native recipe intact while explicitly binding both original and repaired
execution-source inventories. It must derive and test the source/admission seam
rather than waive it: original guard/source/scanner derivation verified separately;
repair manifest and loaded origins checked; new phase/device once lock; new
allocation/intake/CPU/Main GO binding; unchanged privileged scanner and fresh
foreign-device-open checks; nonroot strict-device systemd capsule; new attempt
directory, delayed transport teardown, full native/lifecycle receipts, no native
retry. Freeze only the new tested execution source before its eventual GO.

After that distinct admission, unchanged `matched.run(original_plan, resume=True)`
uses the newly completed stream boundary to load the **existing sleep1**
checkpoint, including post-generation RNG. It must not copy initialization or
repeat compaction/sleep1/generation. Recovery-source provenance must be separate
and honest; a source manifest is not proof of GPU admission.

Actual sleep1 readout disposition is **NOT_STARTED**, not completed. Unchanged
R150 resume dispatches its fresh readout after load and before the next generation.
Any incomplete/uncertain readout custody is a refusal, never an implicit replay.
No held readout contents were opened; no successful evaluation or scientific gain
is claimed. Parent3693784 and R162 service1389517 remain untouched.
