# Repository map

This index separates maintained code, experimental candidates, and evidence.
Saving a candidate or a passing CPU test does not mean it is deployed or that
an experiment succeeded.

## Code and tests

- `organism_v6/`: learning-loop, context, history, and target-policy components.
- `gpu/`: native runtimes, confinement, parent transport, caption game, and
  node-operation entry points. Local `gpu/hosts.env` is not versioned.
- `tests/`: shared CPU regression suite. Historical tests can depend on archived
  fixtures or optional packages; consult the recorded test results rather than
  assuming every test passed.
- `research_loop/workers/`: dated experimental source, candidate versions,
  reviews, and execution receipts. Keep versioned candidates separate from the
  canonical modules; do not infer a live deployment from their presence.

## Current scientific and operational receipts

- `research_notes/analysis/CONTINUATION_RECEIPTS_2026-09-19.md`:
  completed frozen-sibling probe and caption-parent/transport recovery, with
  actual delivery distinguished from uptake and unresolved work kept explicit.
- `research_loop/workers/post_recovery_c2_age_eval_20260918/RESULTS.md`:
  same-block, per-seed caption counts and the replay-count reconciliation.
- `research_loop/workers/post_recovery_correction_review_20260919_0139/REVIEW.md`:
  bounded correction-chain review, including parent visibility at ACT.
- `research_notes/analysis/POST_REBOOT_RECOVERY_2026-09-19.md`:
  timestamped recovery history and explicit unresolved work.
- `research_loop/workers/post_recovery_node2_caption_20260919/MAIN_LOADED_AND_NOTICE.json`:
  actual caption-player reload; publication is distinguished from delivery.
- `research_loop/workers/post_recovery_node2_sleep_20260919/`:
  declared interrupted-sleep restart contract, not a completed C0/Astra7 recovery.
- `research_loop/workers/post_reboot_probe_queue_20260919/V4_REBIND_HANDOFF.md`:
  immutable queue rebind and CPU checks, with activation status explicitly stated.

## Research instructions

- `research_notes/00_THESIS.md` and `research_notes/35_goalposts_paper1.md`:
  thesis, claim boundaries, and controls.
- `research_notes/DEVELOPMENTAL_CURRICULUM_2026-09-18.md` and
  `research_notes/BIRTH_PROMPT_AND_PARENTING_SCHEDULE_2026-09-18.md`:
  curriculum and parenting policy.
- `research_loop/COORDINATION.md`: dated operator coordination and provenance.

## What stays outside Git

Credentials, copied Git worktrees, Python/test caches, process locks, model
weights, optimizer binaries, database files, and large transfer archives are
not source code. Preserve them at their original locations with their existing
manifests and hashes; ignoring a path does not delete or retire it. Do not move
live journals, checkpoints, or mailboxes to tidy the repository.
