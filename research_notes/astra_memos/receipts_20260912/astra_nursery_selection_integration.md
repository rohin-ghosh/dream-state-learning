# Nursery selection-custody integration — main review handoff

Date: 2026-09-12. Assignment began at 07:50:31 UTC; final focused CPU run
finished at 07:59:54 UTC. Completed inside the original <=15-minute bound.

## Status

The actual clean runner now observes its existing format canary, durably records
selection evidence before the final marker, verifies the selected candidate,
closes the candidate backend on success/failure, and binds selection custody into
lineage. Historical replay requires the original manifest-bound selection files.
There is no production fallback that invents a historical receipt or accepts
missing custody. The clean positive fixture no longer unconditionally mocks a
passing format_canary; it executes the actual evaluator using explicit CPU doubles.

Scoped implementation/tests are complete. One out-of-scope fixture migration
remains for main: five positive tests in `tests/test_child_receipt_integration.py`
still omit the new required custody. That file was deliberately NOT edited.

## Ownership / files changed

Production:

1. `organism_v6/run_life_v2.py`
2. `organism_v6/life_lineage.py`
3. `organism_v6/nursery_selection_receipt.py` (new helper from the prior assignment)

Tests:

4. `tests/test_clean_nursery_runner.py`
5. `tests/test_life_lineage.py`
6. `tests/test_adult_controls.py`
7. `tests/test_nursery_note_integration.py`
8. `tests/test_nursery_selection_receipt.py`

Only these eight repository files were edited. James's neutral-probe module and
tests, live/deployed W0 and B0 sources, GPU scripts, coordination, main's evidence
archives, and all unrelated changes were left untouched. This report and CPU logs
are scratch files under /tmp. No pull, stash, rebase, checkout, commit, branch,
network, GPU, deployment, or lease action. Earlier status/diff inspection was
read-only; no Git commands were issued after main's resumed-status message.

## Runner integration

- `run_life_v2.py:153`: optional `selection=None` observer on format_canary. The
  default non-clean path retains the existing prompts, drivers, three-round
  budget, seeds, canonical ACT regex, zip counting, rate and threshold rule.
- The observer checks the evaluator's actual birth prompt, canary IDs, driver
  class and threshold, receives the actual prompts/outputs/seeds, and records
  completion after the unchanged consume loop. No alternate scorer is run.
- At `run_life_v2.py:1217`, clean candidate selection records configured
  model/adapter identity and hashes, prior-manifest pin, evaluator configuration,
  exact prompt/output trace, parseability and the computed decision.
- Publication creates read-only `canary_selection/trace.json`, `receipt.json`,
  then `selected.json`. The last file is the durable selected receipt digest,
  configuration, candidate identity and predecessor pin. File and directory
  fsync precede return; interrupted/existing selection directories cannot be
  overwritten as a retry.
- Candidate handling uses finally to close the backend even if validation,
  generation or publication fails. A false close result blocks clean promotion.
- `run_life_v2.py:1249` verifies the selected intent, receipt, trace and current
  adapter before CANDIDATE is renamed. Final verdict must equal the selected
  canary verdict. A valid negative selection preserves REJECTED_CANARY and its
  evidence, never a descendant checkpoint. Errors leave CANDIDATE/partial evidence.
- The selected path and selected-intent pin are explicitly passed into
  life_lineage.record_sleep. Clean model reload also invokes historical training
  and selection replay before constructing the backend.

## Lineage / replay contract

- `record_sleep` (`life_lineage.py:697`) requires selection_path and
  expected_selection_sha256 for every successful call. The None defaults retain
  earlier diagnostic ordering for malformed old callers; they NEVER permit
  successful recording without custody and are not a clean-mode bypass.
- The selected intent must match the current predecessor, pinned birth-model
  input and exact original candidate adapter input. Actual accepted adapter
  bytes and unchanged renamed marker bytes are reverified at stage DONE.
- The snapshot copies all three immutable files into
  `lineage/sleep_N/canary_selection/` with verified hashes.
- `trace.json` is a separate `experienced_event` source for observed selection
  inputs/outputs, not a claimed environmental measurement.
- The selection receipt, selected intent and adapter/DONE artifacts reference
  ONLY that selection trace. Corpus, training receipt, train metadata and LoRA
  training references retain their original training-only source inventory.
- Canary IDs/prompts/outputs never enter the training ledger or corpus.
- `_prior_training` (`:637`) requires all three historical files to be locally
  bound by the manifest, verifies the original selected intent using its
  manifest-pinned digest, and rechecks the candidate bytes, parse count, rate,
  verdict, marker and predecessor. Original historical input strings remain
  historical; copied adapter bytes are checked at the snapshot location.
- Replay rejects missing historical custody, false verdicts even with rebound
  outer hashes, selection artifacts referencing training sources, and canary
  references mixed into training artifacts/corpora. A new descendant receipt
  cannot fill a missing selection in an ancestor. Adult clean entry uses this
  same existing replay path; no adult production module needed edits.

## Synthetic fixture migration

`tests/test_nursery_selection_receipt.py:55` exports synthetic_selection for the
owned fixtures. Its CPU model, adapter bytes and gym outcomes are explicitly
synthetic. A fixture's staging-complete marker becomes CANDIDATE while the actual
format_canary and actual receipt writer run; selection is verified before the
synthetic acceptance marker is restored. It is never used by production or on
historical deployed evidence. Deliberately malformed fixture adapters retain
their negative-test behavior rather than obtaining fabricated selection data.

The runner's actual-canary fixture now handles all canary family IDs, not just
the wake fixture's mini_sudoku IDs. Its CPU trainer remains explicitly simulated.
The NOTE integration test now verifies the separate actual-canary custody.
A 128-episode, two-SLEEP fixture verifies predecessor binding and historical
selection replay across both accepted snapshots.

The adult local-base compatibility test now constructs a fresh, properly selected
synthetic candidate instead of relabeling an accepted adapter after selection.
That old relabel-and-repin pattern is now a dedicated rejection regression.

No fixture result is represented as real Qwen inference, real training, GPU
execution, authenticated model loading, or scientific performance evidence.

## Validation commands / results

### Focused owned suites — PASS, 141 tests, 25.527 seconds

```bash
PYTHONPATH=tests python3 -m unittest test_nursery_selection_receipt test_clean_nursery_runner test_life_lineage test_adult_controls test_nursery_note_integration
```

Log: `/tmp/astra_selection_focused.log`.

Includes pre-DONE durable publication, real positive/negative canary execution,
two-SLEEP replay, backend cleanup on errors, close failure, selected-intent write
failure, adapter changes after recording, missing custody, historical omissions,
mixed source references, rebound false verdict, NOTE support and adult handoff.

### Adjacent CPU suites — PASS, 125 tests, 3.425 seconds

```bash
PYTHONPATH=tests python3 -m unittest test_preschool_reasoning test_generation_identity test_child_target_loss test_child_training_receipt test_lineage_guard test_preschool_provenance
```

Log: `/tmp/astra_selection_broader.log`. Any B0-labelled records printed by these
tests are CPU fixture output only; no deployed B0 source or run was touched.

### Legacy runner golden behavior — PASS, all 12 checks

`python3 tests/test_compiler_golden.py` initially passed 11/12; the standalone
script failed to supply a pre-existing pytest-style tmp_path parameter to one
test. It was a harness invocation error, not a behavior difference. No golden
file was regenerated and no harness file was changed. All 12 passed when the
missing temporary-directory fixture was supplied explicitly:

```bash
PYTHONPATH=tests python3 - <<'PY'
import inspect
from pathlib import Path
import tempfile
import test_compiler_golden as golden
for name in sorted(name for name in vars(golden) if name.startswith('test_')):
    test = getattr(golden, name)
    if 'tmp_path' in inspect.signature(test).parameters:
        with tempfile.TemporaryDirectory() as directory:
            test(tmp_path=Path(directory))
    else:
        test()
    print('PASS', name)
PY
```

Logs: `/tmp/astra_selection_legacy_golden.log` and
`/tmp/astra_selection_legacy_golden_complete.log`.

### Out-of-scope legacy fixture suite — 24 pass, 5 migration errors

```bash
PYTHONPATH=tests python3 -m unittest test_child_receipt_integration
```

Log: `/tmp/astra_selection_unowned_child_receipt.log`. Ran 29 tests, 0.650 seconds.
All five errors are `LifeLineageError: canary selection custody is required`:

- test_actual_main_labels_and_metadata_round_trip_with_cpu_doubles
- test_all_batches_preflight_once_and_preserve_distinct_row_counts
- test_missing_candidate_and_rejected_markers_never_publish_lineage
- test_real_helpers_round_trip_into_lifecycle_snapshot
- test_reasoning_wrapper_receipt_round_trips_through_lifecycle

Main migration: update that file's shared synthetic candidate-acceptance/verify
fixture to run the exported synthetic_selection helper for each new candidate,
using `self.birth.model_dir` and `self.previous_sha`, then pass selection_path
and expected_selection_sha256 into record_sleep. Maintain malformed-marker and
trainer-evidence negative cases; do not add a production missing-custody bypass
or hand-build generation receipts. The common call requiring migration is
`tests/test_child_receipt_integration.py:215`. This file was outside ownership,
so its edits are explicitly left to main rather than silently expanding scope.

### Static checks

AST parsing passed for all eight owned files. Earlier read-only diff whitespace
checks were clean. No Git commands followed the resumed-status request.
Existing unclosed-file ResourceWarnings occur in adjacent fixture/runtime code;
unrelated cleanup was not folded into this repair.

## Remaining gaps / main review

1. Migrate the five positive cases in the unowned child-receipt fixture file.
   The broader repository suite is NOT claimed wholly green until that is done.
2. Review and commit these scoped changes using main's Git ownership. No agent
   pull/stash/rebase/commit or deployment was performed.
3. Current official birth pins remain unresolved as stated by main. This is not
   clean GPU launch authorization. Configured identity plus byte hashes is not
   proof of actual in-memory backend loading or real-Qwen authentication.
4. Crash/partial selection directories intentionally fail closed and preserve
   evidence. There is no automatic overwrite, retroactive receipt manufacture,
   or grandfathering of old accepted markers into clean selection ancestry.
5. No changes to live W0/B0 or James's neutral-probe implementation were made.

Main can review this report now; all artifacts above remain available under /tmp.

## Freeze and repository-wide caller inventory — 08:02:33 UTC

All eight owned source/test files are FROZEN for main's combined validation.
No further code edits are planned; only this report received the caller-inventory
addendum after the freeze announcement.

Repository-wide Python searches for `record_sleep(`, direct imports, assignments,
attribute calls and explicit getattr use found:

- Production: `organism_v6/run_life_v2.py:1262`, the clean candidate branch. It now
  supplies selection_path and expected_selection_sha256 from the prospective
  recorder, after verification and before lineage recording. No other production
  Python caller or imported alias was found by these searches.
- Owned tests: `tests/test_life_lineage.py` and `tests/test_adult_controls.py`;
  their synthetic acceptance fixtures have been migrated and pass.
- Unowned tests: `tests/test_child_receipt_integration.py:215`, its common verify
  method. It still omits custody and accounts for all five migration errors
  identified above. Main should migrate this shared fixture; no production
  compatibility bypass is appropriate.

Searches were local and read-only; no Git, network, GPU, deployment or live-source
action occurred. W0/B0 progress and the documentation commit were not modified.
