# R202 repo Tool-feedback visibility repair

Recorded: 2026-09-18T03:02:11Z (September 17, 2026, America/Los_Angeles).
Classification: authorized non-material repair; ready for Main review, **not deployed**.

## Finding and retained receipt

`has_scaffolding()` classifies `source_sha256` as institutional scaffolding. This also dropped genuine source-bound repo Tool JSON from the child's plain live context and replay prefix.

Existing bounded observation: `REPO_CHILD_FIRST_FEEDBACK_FILTER.json` (observed Unix `1789699722.5781298`, SHA-256 `806f6f5eb0ad774dd7fa5abc18c3d3e1af0632b0dc5e8ad0d7e4f2b8a3c4d68b`). It records actual Tool publication in INBOX record 8 and absence of both the full Tool text and source hash from REQUEST record 9. REQUEST started at Unix `1789684074.3000474`; the on-node source matched the pre-repair local source hash below. Exact original journal paths, file hashes, and record hashes remain in that receipt. No new remote inspection was needed.

## Minimal patch

- `organism_v6/orch_r125_plain_context.py`: recognize valid `Tool: ` JSON with schema `R183_ACTUAL_TOOL_RESULT_V1`, status `COMPLETE`, and child/TRAIN origin. Permit source/receipt hash metadata without dropping the exact result content. Retain rejection of all other existing institutional/role markers.
- Live recognition is restricted to environment/feedback events. Already-plain replay recognition is restricted to user-role Tool messages; legacy replay uses the same event path.
- Generic `has_scaffolding()`, target eligibility, parent/runtime masking, and history loss masking are unchanged. A copied Tool receipt remains ineligible as a child training target. This is not a new authenticity/security boundary; existing attributed-inbox provenance remains authoritative.
- `tests/test_orch_r125_plain_context.py`: synthetic representative repo JSON goes through the actual `_inbox`/journal/stream path with a mocked generator. Assert exact Tool JSON in the generator REQUEST prefix and saved replay prefix, source-bound publication, unchanged history, all history labels `-100`, no history target tokens, legacy replay preservation, and replay idempotence. Negative cases cover institutional/role markers, non-feedback actors/phases, and private/evaluation schema or origin.

Both files were already modified before this repair. The existing `<|im_start|>` marker and `test_generated_role_header_is_preserved_raw_but_not_replayed_or_trained` were preserved, not authored by this repair. The aggregate git diff includes those prior changes.

## Validation

CPU-only command, no model invocation:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CUDA_VISIBLE_DEVICES='' \
/data/home/rohing/.cache/uv/builds-v0/.tmpSWv1MH/bin/python -B -m pytest \
-q -p no:cacheprovider \
tests/test_orch_r124_train_history.py tests/test_orch_r125_plain_context.py \
-k 'not all_scaffolding_rows_skip_training_without_fabricating_progress'
```

Recheck: **71 passed, 1 deselected, 120 subtests passed in 0.66s**. `git diff --check` passes for both owned code paths. Two positive feedback regressions failed before the source fix and passed afterward during implementation.

Full plain-context file recheck: **29 passed, 1 failed in 0.61s**. The failure is the same pre-existing `test_all_scaffolding_rows_skip_training_without_fabricating_progress`: `KeyError: 'new_presentations'` at `gpu/orch_r125_continual_native.py:501`. Before this repair the file had 13 passing tests and this same failure. It is explicitly excluded from the combined green run, not fixed or reclassified as passing. The native file is outside this task's write scope.

## Source receipts

| File | Pre-repair SHA-256 | Post-repair SHA-256 |
| --- | --- | --- |
| `organism_v6/orch_r125_plain_context.py` | `dcfd1f7f5584867e39356f336f53bb7222aeb535da87d5ecb8f1f0bb59f72feb` | `009e2994d1221a86e6029104576c64352572d894e7ebbe0d8ddedeb097690976` |
| `tests/test_orch_r125_plain_context.py` | `d25a61989c4b12880a514ccda1ff8706b59e20abb4d036f32b849643bf1c521d` | `9adeae73bfbbbae7886c4c35946eb4d056ba84f52ab9d4e638bede06c8dc2aca` |

## Handoff and boundaries

Main owns review/publication of the small immutable receiving overlay for pending REPO-C and any later saved-boundary repair of the existing repo child. Local tests demonstrate the repaired prefix path; they do not demonstrate deployment or repaired live child receipt. No live deployment, GPU/model call, process-control action, hidden/sealed/FINAL content read, score transfer to a parent, or new training occurred. No stream, console, native, R184, COORDINATION, Main arm table, or canonical environment-audit file was edited for this repair. Only the two authorized code paths and these worker repair reports were written.
