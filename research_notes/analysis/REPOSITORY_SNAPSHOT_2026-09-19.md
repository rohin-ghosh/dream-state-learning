# Useful-work repository snapshot — September 19, 2026 UTC

Rohin requested committing useful and important work, then continuing the
experiments. This is a source/evidence preservation change, not a rollout,
scientific success claim, lease change, or permission change.

## Scope and organization

- Preserve canonical source/test additions and changes, recent recovery source
  and its pinned candidate versions, small execution receipts, and the corrected
  same-block caption results.
- Add `research_notes/REPOSITORY_MAP.md` and link it from the root README.
- Exclude credentials, model/checkpoint binaries, archives, copied publication
  worktrees, caches, locks, and machine-local symlinks. Preserve them on disk;
  no checkpoint, journal, mailbox, or failed artifact is deleted or moved.
- Stage on top of the fetched remote `main` in a separate index. The long-lived
  working checkout and its existing index are not reset, checked out, or merged
  underneath running publishers. Do not replace the remote coordination notebook
  with the older local notebook.

The focused pre-staging inventory contains 9,299 changed/new files, 241,569,699
bytes; 2,196 candidate files already match remote `main`. Fourteen candidates
are omitted: thirteen machine-local symlinks and one bulk test fixture. These
inventory counts precede this report and the attached validation logs.

## Checks actually run

| Check | Result |
| --- | --- |
| Caption checkpoint-tail recovery and control bootstrap | 24 passed |
| Interrupted-sleep declaration and strict receipt comparator | 40 passed; 46 subtests passed |
| Immutable probe-queue runtime rebind | 107 passed; 26 subtests passed |
| Tests for the four canonical modules differing from fetched remote main | 80 passed; 135 subtests passed |
| Broader changed-runtime selection | 270 passed, 1 failed; 349 subtests passed |
| Broad root suite, stopped at the configured failure limit | 508 passed, 18 failed, 4 skipped, 7 collection errors |
| Python syntax in the focused inventory | No syntax errors |
| Credential-pattern scan in the focused inventory | Two candidates; both manually verified synthetic security-test fixtures |
| Whitespace in changed canonical source/tests and ignore rules | Passed |

The broader runtime failure is
`test_all_scaffolding_rows_skip_training_without_fabricating_progress`, whose
fixture lacks `new_presentations`. Broad-suite failures include archived
inventory/launch-fixture mismatches; collection errors include unavailable
Pillow and missing pinned Rohin-principles fixtures. The first collection attempt
also lacked PyTorch; subsequent checks use an already-cached CPU PyTorch
environment. No large dependencies were installed. The full suite is **not
green**. These failures are recorded, not bypassed or represented as successes.

The whole staged snapshot also reports whitespace in captured parent prompts,
historical logs, and pinned source copies. Those bytes are retained as evidence,
not silently reformatted. The canonical-source whitespace check remains separate.

Logs are under `research_loop/workers/repository_snapshot_20260919/`.

## Scientific and operational status preserved

Distinct new-pixel counts per independent seed remain base15/24,
C2sleep51 34/31, and C2sleep117 19/26. Replay-inclusive counts are a different
quantity; seeds are not pooled. These observations do not establish causal
learning, certified humor, or general superiority.

At the latest verified recovery cut, the extra node2 caption player has an
actual LOADED8529 receipt. C0 and Astra7 are not recovered; retention adoption
is not live; the new probe-queue runtime is CPU-verified but not activated.
The next experimental work must update those statuses from actual receipts,
not from this repository publication.
