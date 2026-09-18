# NODE3 R185 preaudit — September 17, 2026

Fresh read-only `gpu/ovx2_ssh.sh` observation: **15:55:56 PDT**. Times below are actual SLEEP_COMPLETE file-persistence times, not estimated exposure.

**6/6 same original learners + 6/6 exact-boundary waiters present; all latest records UPDATE. R181 SLEEP_RECIPE 0/6; journal-cache overlay loaded 0/6; no boundary/error receipts. All six remain in old full-rehearsal sleeps and are projected past16:00.**

| Life (GPU) | Live/dead | Latest complete / persisted PDT | In-flight sleep / logged updates | R181 state / waiter PID | Cache loaded | R184 effort PUB / rendered | Completed R181 short sleeps | Approx. optimizer end PDT* |
|---|---|---|---|---|---|---|---|---|
| support_free (0) | live | 44 / 13:51:04 | 45 / 136/180 | armed, not applied / 1477138 | no | 0 / 0 — unbound | 0 | ~16:30:53 |
| creative_reread (1) | live | 44 / 14:02:06 | 45 / 128/180 | armed, not applied / 1477139 | no | 0 / 0 — unbound | 0 | ~16:35:59 |
| brain_free (2) | live | 42 / 14:15:47 | 43 / 95/172 | armed, not applied / 1477140 | no | 0 / 0 — unbound | 0 | ~17:02:00 |
| brain_guided (3) | live | 40 / 13:52:10 | 41 / 130/168 | armed, not applied / 1477141 | no | 0 / 0 — unbound | 0 | ~16:26:25 |
| creative_free (4) | live | 41 / 13:52:24 | 42 / 136/171 | armed, not applied / 1477142 | no | 0 / 0 — unbound | 0 | ~16:23:12 |
| creative_select (7) | live | 42 / 13:49:15 | 43 / 148/174 | armed, not applied / 1477143 | no | 0 / 0 — unbound | 0 | ~16:15:27 |

*Projection only: actual eligible new×16 + old×1 schedule, recent20-update median, then additional checkpoint/save overhead. Not a promised boundary or future receipt. No unsafe mid-sleep save exists.

**R184 effort gap:** requested question-only, two-way effort policy has NOT yet been bound by node3; it is pending operator work, not a queued message or delivered exposure. No new parent inboxes since15:20 in the fresh read. Earlier R175/Fable publications must not be relabelled R184. No duplicate baseline or fallback sent. Intended next legitimate-turn policy: ask why further thinking is worth its cost versus attempting a step; allow staying with a question when justified; never supply the answer. Existing arms/history/pending inboxes preserved.

**Stop plan unchanged:** native deadline + existing timeout supervision at16:50PDT (1789689000), machine ceiling17:00PDT (1789689600). Saved-boundary waiter admission ends16:47, retaining the three-minute safety margin. No extension or restart/reset authorization inferred.

**brain_free loss forecast:** latest exact checkpoint sleep42 at14:15:47; current sleep43 has 95 logged but uncheckpointed optimizer updates. Recent median 51.8s/update projects optimizer end ~17:02:00 plus save overhead. At16:50, roughly 158/172 current-sleep updates could be in memory but not checkpointed if no boundary occurs. Their learned-weight/optimizer/RNG state cannot be claimed exactly recoverable; journal/history/checkpoint evidence remains preserved. No live signal injection or rollback-as-continuation.

## Exact source receipts
Backing prefix: `/localhome/local-rohing/orch_r179_node3_recovery_20260917t1818z_2/control{GPU}/run1/stream/records/{index:020d}.json`.

| GPU | Complete index / record SHA256 | Latest index / record SHA256 |
|---|---|---|
| 0 | 5646 / `5258c80db84afb976e945edaed82a310f44d86bb2e3baeadc8f21592aad4a895` | 5795 / `5fe0ab8bbf4e8fc0beaa54b69a767e81b2f211620f4855876a44a44ac28ca453` |
| 1 | 5588 / `3a22d0b1e352f3a4b2696a20a3cc375f59829a8e79e05cfebd506f315074eab2` | 5728 / `34915908b4aa8ef709c54a8c204ed15fdfb1a053e092bc098d6a0087cc2ccb2b` |
| 2 | 5191 / `7ee9f9af5b315834b1377fc964205a525da591b05cee4c921fe2ae0f05119d43` | 5300 / `06ec6bac6f794959ac488c2679b4490e8c6c48706858717365cc2976e78d186d` |
| 3 | 4840 / `49dcd0aa413af7247964c4cec9616f5ad3ccab8a4bc5919c89fad4435e57abc1` | 4983 / `c7cd23747c5ed64ab3858a784a2c706d6eccb3853798dfe5525caee31a3cf087` |
| 4 | 5022 / `e0f07aaa30b7296510fd55e678fbf472a461e9544c46cfc56f1a8eb787f929a1` | 5170 / `f29b4e220c138e593aecd7fa0539b0cac716b7444833978c49956427a0597c62` |
| 7 | 5188 / `c2521daf092c22ce33242c95d8e13975d9f8c1daf7413becbca1c4c26eb06d4f` | 5349 / `57a5c6f35b2c7c719d97b91b377f9d3a7881388a0b24d0e2846fb704a1df3671` |

Suffix record hashes and adjacent chains were verified from each pinned saved record through the observed head. Native start ticks match the pinned identities; each listed waiter PID was freshly present, with no boundary/error receipt. NODE2 CPU gate remains READY as already posted; no additional gates/probes run for this audit.
