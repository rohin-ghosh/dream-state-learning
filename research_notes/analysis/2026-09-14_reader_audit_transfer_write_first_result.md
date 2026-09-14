# SEQ-247: executable selections affect a shared writer's acquisition

September14,2026. Main inspected the completed native train and fresh AFTER.
Independent captured-source reduction is COMPLETE: both stages, reference
joins, exact outputs, dose and denominator verified;43CPUtests pass. Receipt
`SEQ247_independent_reduction_20260914.json` in the preservation directory has
SHA256 `9c6dfe501557b3ff83c4e6875e3f99d477a4607fc56ed7043539da38fb4e3c7c`.
See `2026-09-14_reader_audit_transfer_write_independent_result.md`. Design:
`2026-09-14_reader_audit_transfer_write_design.md`.

## Results, with unchanged reference observations

| Endpoint | Shared BEFORE | SFT-selector material (SEQ245 reused) | Uniform (SEQ245 reused) | LOSS_OFF_SELECTOR (new) |
|---|---:|---:|---:|---:|
| Own routing | 1/4 | 4/4 | 4/4 | 3/4 |
| New exact W0 recall | 0/4 | 4/4 | 4/4 | 1/4 |
| New exact W8 recall | 0/4 | 4/4 | 4/4 | 1/4 |
| Old W0 recall | 12/12 | 12/12 | 12/12 | 12/12 |
| Old W8 recall | 12/12 | 12/12 | 12/12 | 12/12 |
| Original held audit | 16/16 | 16/16 | 16/16 | 16/16 |
| Next actual audit | 8/8 faults | 6/6 true | 6/6 true | 7/7:5fault,2true |
| Reader OFF routing | 2/4 | 2/4 | 2/4 | 2/4 |
| Held text, both panels | 8/8 | 8/8 | 8/8 | 8/8 |
| Unseen MISS | 0/4 | 0/4 | 0/4 | 0/4 |

Only source1 receives new-memory presentations in the new arm: [0,200,0,0]
versus [48,56,48,48] in selected and [50,50,50,50] in uniform. New exact recall
succeeds on that selected record only. Routing succeeds on tasks0,1,2; task3
terminates invalid_route without a committed port/outcome. Correct routing
therefore does not imply complete record recall or faithful use of every read.
Do not infer the actor's internal reasoning from its terse commands.

The new writer's own subsequent audit chooses
[null,0,null,3,2,3,2], correctly identifying all five faulty and two accurate
reads. This is a different packet from either reference AFTER, not a fixed-test
classifier comparison. The writer is the SAME taught A3 pre-write child in all
three arms; it is NOT the original loss-off auditor becoming a better checker.
No further write on those choices has been run or automatically authorized by
this recipe.

## Causal interpretation and limitations

This component comparison connects the original taught-versus-loss-off
auditors' different executable outputs to persistent acquisition and actions
through a shared writer. The six control failures were literal invalid `E_id`
placeholders, not NONE; the result does not isolate newly learned semantic
judgment from address binding/output formatting. It is compatible with an
already capable base needing to learn the required machine-usable interface.

Both selectors saw third-party captured A3 stimuli. The shared writer really
experienced the selected source EVENTs, but material choices were replayed from
earlier auditor checkpoints. Therefore this is an off-policy material
intervention, not a full parented-versus-unparented adult lineage. All writer
arms retain the SAME62 audit-lesson rehearsal rows. Uniform remains as good as
taught selection; no selection superiority over uniform, H1/H2, new independent
seed, generic mechanism freeze, or population learning-efficiency claim follows.

## Implementation, costs, and preservation

Exactly one new fit, source `d0f16e22f0b4a5b61998164193ee8d8bf155c0f3`;
node2GPU0 guardian386793, started14:12:43UTC, completed14:18:56UTC.
Root `/tmp/astra_reader_audit_transfer_write_20260914_attempt2`.
The existing 100update/freshAdamW/LR3e-5/rank8/frozen-base writer is unchanged.
All210 encoded rows, prior-memory/cue/lesson data and common UNIFORM label
denominator16319 match the two referenced fits. Native CPU preparation verified
reference source/kernel/roster/recipe equivalence before reusing them. No
reference fit was repeated. Actual supervised tokens16969 versus16345/16319;
budgets are matched presentations/updates, not equal actual token counts.

Native train wall199.256seconds; AFTER172.024seconds and117calls; summed
0.1031 dedicatedA40-hours, not kernel-active time. An allocator OOM/recovery
warning occurred, as in references; all100 updates, save and AFTER completed.
Final adapter state:
`b4a5383e6b8c2eb73415833227b7eea15e2ebb34b631bda670adac33a0e5b3d8`.
Fresh AFTER loads that state; native unchanged-base and readonly-after checks pass.

Attempt1 failed CPU preparation before model loading because native cue_rows
is a tuple while its saved JSON is a list. Canonical JSON contents and both
reference recipes were identical. A non-material serialized-content comparison
fix plus changed-content regression passed51tests before attempt2. No data,
kernel, metric or target changed; the failed source/receipt remain preserved.

Complete evidence directory:
`gpu_artifacts_local/astra_reader_audit_transfer_write_terminal_20260914_attempt2/`.
Use `extracted_complete`, NOT the incomplete initial `extracted` directory:
the first transfer/extraction shell exceeded its20second host bound after
archive hash verification. A new extraction completed and all5894regular file
contents (484260291bytes) match the archive. No source evidence was overwritten.
Remote/local terminal archive SHA256:
`14386b5015b65a5fb3f18e1e57d27915f42c914c4e98638c70f6f2dcb73126db`.
Separately preserved failed CPU preparation archive SHA256:
`a4428bfe8a7da892a92ae7d0243ac4d1fd3f844db28126d3d42f7f60fdcd92c2`.
