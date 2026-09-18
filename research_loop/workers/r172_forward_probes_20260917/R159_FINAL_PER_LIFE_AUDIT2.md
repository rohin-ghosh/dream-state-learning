# R159 final per-life execution audit — 2026-09-17 08:57:46 PDT

**New metadata observation: 2026-09-17 15:57:46 UTC / 08:57:46 PDT.** This is not the earlier 08:29 snapshot or a science rerun.

**71 completed condition jobs / 213 completed calls; 213 charged calls.** Initial: 37 jobs. Forward: 34 jobs. Verified paired checkpoints: 34.

| Life | Initial completed jobs | Forward completed jobs | Paired checkpoints | Missing / 8 jobs | Refused | Failed | Unresolved/unterminated | No attempt record |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C1 | 1 | 2 | 1 | 5 | 1 | 0 | 0 | 4 |
| C2 | 2 | 2 | 2 | 4 | 0 | 0 | 0 | 4 |
| C3 | 2 | 2 | 2 | 4 | 0 | 0 | 0 | 4 |
| C4 | 2 | 2 | 2 | 4 | 0 | 0 | 0 | 4 |
| C5 | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 0 |
| R158_parented_learning | 2 | 2 | 2 | 4 | 0 | 0 | 0 | 4 |
| brain_free | 2 | 2 | 2 | 4 | 0 | 0 | 0 | 4 |
| brain_guided | 2 | 2 | 2 | 4 | 0 | 0 | 0 | 4 |
| classroom_brain | 2 | 2 | 2 | 4 | 0 | 0 | 0 | 4 |
| classroom_creative | 2 | 2 | 2 | 4 | 0 | 0 | 0 | 4 |
| classroom_support | 2 | 2 | 2 | 4 | 0 | 0 | 0 | 4 |
| continual_run1 | 2 | 2 | 2 | 4 | 0 | 0 | 0 | 4 |
| creative_free | 2 | 2 | 2 | 4 | 0 | 0 | 0 | 4 |
| creative_reread | 2 | 2 | 2 | 4 | 0 | 0 | 0 | 4 |
| creative_select | 2 | 2 | 2 | 4 | 0 | 0 | 0 | 4 |
| pilot | 2 | 2 | 2 | 4 | 0 | 0 | 0 | 4 |
| repo_reader | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 0 |
| support_free | 2 | 2 | 2 | 4 | 0 | 0 | 0 | 4 |
| teach_parenting | 2 | 1 | 1 | 5 | 1 | 0 | 0 | 4 |
| teach_perception | 2 | 1 | 1 | 5 | 0 | 0 | 0 | 5 |
| teach_replay | 2 | 0 | 1 | 6 | 0 | 0 | 0 | 6 |

Each condition job contains exactly three frozen calls. A pair means both conditions completed against the same original checkpoint COMMIT hash, not that either retained anything. No condition assignment, response, rubric annotation, or outcome is disclosed.

C5 and repo_reader lack old-campaign registration: each contributes eight missing jobs, not eight failed or attempted jobs. For registered lives, missing jobs are reported separately from refusals, charged failures and absent attempts. “No attempt record” does not establish whether the source was uncaptured or merely unexecuted; no journal/adapter audit was authorized.

Audit reads: **169,716 bytes / 234 metadata files**, each charged before an exact-size read, ≤128 KiB/file. A fresh 8 MiB envelope was reserved inside the existing R172 discovery cap (authorization maximum: 16 MiB). No refund/reset; the earlier failed 1 MiB observation remains consumed.

Evidence: `preparation1/R159_FINAL_PER_LIFE_AUDIT2.json`; request/allocation: `preparation1/R159_FINAL_PER_LIFE_AUDIT2_REQUEST.json`; remote pre-read ledger: `/localhome/local-rohing/orch_r172_forward_probes_20260917_generation1/R159_FINAL_PER_LIFE_AUDIT2`.

No GPU/provider/model call, signal, old-ledger write, response/score/map disclosure, adapter read or journal-payload read. Exactly one new sanctioned-wrapper observation; no automatic follow-up.
