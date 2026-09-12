# Astra NOTE-kind integration repair

Date: 2026-09-12, completed after the 07:32 UTC scope review.
Classification: bounded non-material repair, explicitly requested by Rohin.
Read: `research_notes/courier/CODEX_NOTE_TO_ASTRA_NURSERY_NOTE_KIND_SEAM_2026-09-12T0724Z.md`.

## Scope and policy

Only these repository files were edited by this repair:

- `organism_v6/preschool_reasoning.py`
- `organism_v6/life_lineage.py`
- `tests/test_preschool_reasoning.py`
- `tests/test_life_lineage.py`
- `tests/test_nursery_note_integration.py` (new)

`note` is now an explicitly recognized child-visible influence, not an admission
candidate. Its existing producer shape is validated: nonempty `note`, positive
integer `tick`, reserved training `episode_id`, matching nonempty reasoning-ledger
provenance stamps, and implicit child or explicit `speaker="child"`. Unsupported
NOTE fields, contradictory/missing provenance, foreign/held-out/quarantined
content, and unknown kinds fail closed. The lineage validator shares the same
NOTE influence validation. NOTE rows need a preceding matching episode reservation;
no ACT link or generation authentication is inferred for them.

`note_after` remains the only write record, with the existing unique prior ACT,
occurrence, measurement, exact source/record SHA256, generation, and corpus recipe
checks unchanged. NOTE cannot be substituted for either admission endpoint and
does not count toward the unchanged 64-record minimum. Ledger bytes, including
NOTE, remain in the hash-bound snapshot. No NOTE generation receipt is fabricated.

No thesis, invariant, base model, training mask, threshold, runner, batch loop,
coordination file, or scientific claim was changed. No GPU use, network access,
lease action, commit, branch creation, or modification of other agents' work.

## Reproduction and tests

The new full-run fixture first reproduced `ReasoningGateError: unknown or probe
ledger influence` at the first SLEEP before the implementation change.

The positive fixture reuses `test_clean_nursery_runner.CleanNurseryRunnerTests`
read-only, adding NOTE before ACT through a model fixture. It completes 64 episodes,
emits 64 NOTE influences and 64 admitted NOTE_AFTER records, exercises the existing
simulated trainer/receipt/promotion/reload path, and reaches LIFE_DONE. Assertions
verify exact ledger snapshot bytes and gate hashes, NOTE exclusion from the corpus,
ACT/NOTE_AFTER-only admission endpoints, and absence of NOTE generation receipts.
These are explicitly synthetic CPU fixtures, not authenticated model evidence or
real training. Existing production receipt writers consume the synthetic fixture
outputs; no generation receipts were invented by hand.

Corruption coverage includes malformed/missing NOTE fields, wrong/noninteger ticks,
non-child attribution, missing/wrong gym/domain/clone stamps, unreserved/held-out
episodes, missing or later reservation, unknown kinds, unsupported receipt fields,
quarantine/foreign content, NOTE-only minimum-count attempts, corrupted ACT source
identity, raw ledger hash changes, and rebound gate links targeting NOTE.
Full-run corruptions assert no training subprocess, no descendant checkpoint, and
no LIFE_DONE. Held-out NOTE is rejected even earlier by existing split hygiene.

Commands and results:

| Command | Result |
| --- | --- |
| `python -m pytest -q tests/test_nursery_note_integration.py` | Could not run: `python` absent. |
| `python3 -m pytest -q tests/test_nursery_note_integration.py` | Could not run: pytest not installed. No installation attempted. |
| `python3 -m unittest discover -s tests -p test_nursery_note_integration.py` (before repair) | Expected red reproduction: 1 test, unknown NOTE influence. |
| `python3 -m unittest discover -s tests -p test_preschool_reasoning.py` | PASS, 53 tests. |
| `python3 -m unittest discover -s tests -p test_life_lineage.py` | PASS, 61 tests. |
| `python3 -m unittest discover -s tests -p test_nursery_note_integration.py` (final) | PASS, 2 tests with corruption subtests. |
| `python3 -m unittest discover -s tests -p test_clean_nursery_runner.py` | PASS, 13 tests; fixture file read-only. |
| `python3 -m unittest discover -s tests -p test_child_receipt_integration.py` | PASS, 29 tests; file read-only. |
| `PYTHONPATH=tests python3 -m unittest test_preschool_reasoning test_life_lineage test_nursery_note_integration test_clean_nursery_runner test_child_receipt_integration` | PASS, all 158 tests, 9.468 seconds. |

During test development one corruption assertion expected ReasoningGateError but
the held-out case correctly raised the runner's earlier split-hygiene RuntimeError.
Only that test expectation was corrected; no production guard was relaxed.

`git diff --no-index --check` against the four pre-edit snapshots, and against
`/dev/null` for the new integration test, all completed with no whitespace errors.
The ordinary scoped `git diff --check` was also clean; explicit snapshot checks
were necessary because the owned source/test files were initially untracked.

Warnings: the test runs emit ResourceWarning messages for pre-existing unclosed
bootstrap/log/fixture DONE files. These also occur in unchanged adjacent tests;
they are outside this repair and did not fail any tests.

## Preserved evidence and concurrency

- Pre-edit copies of all four existing owned files: `/tmp/astra_note_kind_baseline/`.
- Final combined log: `/tmp/astra_note_kind_combined_tests.log`.
- Individual logs: `/tmp/astra_note_kind_preschool_tests.log`,
  `/tmp/astra_note_kind_lineage_tests.log`, `/tmp/astra_note_kind_integration_tests.log`,
  `/tmp/astra_note_kind_runner_tests.log`, `/tmp/astra_note_kind_receipt_tests.log`.
- Existing fixture cleanup still removes temporary test runs; no production
  evidence was overwritten or deleted by this repair.
- The read-only runner fixture changed concurrently, as anticipated by the user:
  initial SHA256 `3a74a4e89e1452e2d970568c29c6bfc815d2509ceb4eef9d13aece8188b7d29d`,
  observed final SHA256 `a36b06065646c739bef38ba5cd530a22de5c200b4c4d91a43d08f04c7b8ff940`.
  Its modification timestamp preceded the final combined test run. Those edits
  were preserved, not reverted or claimed as this repair's work.

CPU integration success is not model authentication, scientific evidence, or a
claim that the separate birth-pin/backend-loader identity concerns are resolved.
