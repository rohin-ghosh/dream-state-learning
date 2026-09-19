# C2 same-block count reconciliation

**Resolved: the original distinct counts stand, reproduced from C2's own completed files. The discrepancy is replay counting, not an imported base result.** Only the broad beat-base claim remains retracted, not the factual counts or their within-block arithmetic comparison. This is a non-material reporting clarification, not a change to the evaluator or scientific claims.

Completion receipt: **2026-09-18 22:36:12.809337 UTC**; batch completed **22:30:53.862041 UTC**. Independent completed-file metadata read: **2026-09-19 00:44:03.114942 UTC**. All three sources completed six cells, **3,072 actual generated tokens per independent seed / 6,144 per source**, on the same three DEVELOPMENT scenes. C2 sleep117 is the source selected at September18 21:58:47 UTC, not current live weights.

## Same-block counts

Scored / accepted / pixels are shown in that order. Seeds are never pooled.

| Source | Seed | Events | Tokens | Raw returned scored / accepted / pixel-status rows | Distinct scored / accepted / new pixels |
| --- | ---: | ---: | ---: | --- | --- |
| base | 23201 | 25 | 3072 | 72 / 43 / 28 | 50 / 24 / 15 |
| base | 23202 | 24 | 3072 | 75 / 54 / 40 | 51 / 36 / 24 |
| c2sleep51 | 23201 | 29 | 3072 | 98 / 66 / 35 | 94 / 62 / 34 |
| c2sleep51 | 23202 | 30 | 3072 | 78 / 42 / 31 | 76 / 40 / 31 |
| c2sleep117 | 23201 | 80 | 3072 | 114 / 70 / 22 | 106 / 62 / 19 |
| c2sleep117 | 23202 | 67 | 3072 | 94 / 54 / 26 | 93 / 53 / 26 |

The raw column reproduces Fable's event sums. The distinct column reproduces **every count and curve point** in `AGE_BLOCK_REFRESH.json`. `STATUS.md` and `TOKEN_CURVES.svg` use the distinct definition through the existing shared renderer.

## What stands and what remains retracted

- **Original factual numbers stand:** per independent seed23201 / seed23202, distinct new pixels remain base **15 / 24**, C2 sleep51 **34 / 31**, C2 sleep117 **19 / 26**. All original distinct scored/accepted counts, actual-token budgets and curve points also stand.
- **Narrow descriptive comparison stands:** both pinned C2 checkpoints have more distinct operational new pixels than their own block's base in each measured seed. This is arithmetic about these six completed cells under the frozen protocol, not an additional scientific claim.
- **Broad claim remains retracted:** these counts do not establish general superiority, causal learning, certified humor, globally unique ideas or an independent replication across the two base blocks.
- **No substitution of metrics:** raw **28 / 40**, **35 / 31**, **22 / 26** are correct as replay-inclusive returned pixel-status/event counts. They are **not** corrected distinct-new-pixel counts and must not replace **15 / 24**, **34 / 31**, **19 / 26** under that label. Posting both columns with their definitions is the reconciliation, not an admission that the original distinct counts were wrong.

## Why the numbers differ

- **Raw scored / accepted:** count every returned row with a non-null rank / `accepted=true`, including replayed responses; these are not counts of fresh judge calls or distinct strings.
- **Distinct scored / accepted:** the observer keeps the first non-cached `(contest_id, caption_sha256)` within each seed; the set persists across events, with scenes separately keyed.
- **Distinct new pixels:** count `status=new_pixel` only on those first-seen rows. Independently counting distinct `(contest_id, pixel_id)` among new-pixel rows gives exactly the same six totals. This is operational embedding novelty within a source/seed, not globally unique ideas.
- **Counter mismatch:** `gpu/ny_caption_game.py:326` returns the original submission result with `replayed=true`, retaining its old `status=new_pixel`. The pinned evaluator `research_loop/workers/post_recovery_age_queue_20260918/runner.py:109` sums that status while excluding only `cached`, not `replayed`. Thus `score.new_pixels` repeats old successes. Deduplication at `research_loop/workers/post_recovery_age_queue_20260918/observe.py:25` removes them before counting. The captured remote observer and checked-out sources match their bound hashes. No evaluated code or stored event has been changed.

Raw minus distinct is exactly the replay contribution for **all three metrics**. Extra pixel-status counts, seed23201 / seed23202: base **13 / 16**, sleep51 **1 / 0**, sleep117 **3 / 0**. Replayed scored rows are respectively **22 / 24**, **4 / 2**, **8 / 1**. No `cached=true` rows occurred. The discrepancy is fully accounted for, not a budget difference.

## Same-block provenance and two-base comparison

The audit reads `/localhome/local-rohing/orch_post_recovery_c2_age_eval_20260918/{base,c2sleep51,c2sleep117}`. For every arm, CONFIG, LOADED, COMPLETE and SOURCE_MANIFEST hashes equal the September18 22:36 receipt. Each COMPLETE cell equals its own RESULT.json, and every RESULT event equals its individual event file. All **350** metadata/evidence files in the two-block read retained identical before/after hashes; every pinned evaluator source file also verified.

The comparison base is `/localhome/local-rohing/orch_post_recovery_age_20260918_attempt3/base`, not the input to C2's result table:

| Binding | Earlier block base | C2 block base |
| --- | --- | --- |
| Condition | R233_ADOPTED_BASE | R233_C2_AGE_base |
| CONFIG SHA256 | `1c73a5b793861da7dc5ef888c913bf76857fa7fc94ea1176a9a0889290d327cd` | `5968895c64166238afc2240b4c5a9e40f72d9c603f4d4ba85c8998e2a978d6f7` |
| LOADED SHA256 | `f3e758786a9469fd6586188af59b94b6ecfa60a547a3271067d852f75431cd5d` | `fa3e93bbe95f0538b0752713820e1e53e14cfa03b1651493d571ebb8770639d8` |
| COMPLETE SHA256 | `d62eeec3c037bc3fac750d4413041383c4633d8aa640da1bf0f9b0a9b28667e7` | `91e8c2587d1994c11000252730f4c511635fc53732e6e68d837be0a5f1e94040` |

Both use source-manifest SHA256 `bcdd5adbcd03bc52e0ae20ca400cd6b328bc9d89aeb19a3f1d9fbae20b3e5c7b`, game-manifest SHA256 `31e3c9919524deacc1d8255caa65f5121744ef6f0465988576b2d1b7ad281274`, and judge epoch `216f34224e27a2ced6671026c482041c3e6024aecbabd105341a365d2935268a`.

Loaded base/tokenizer/template/decoder/library identities are identical. Config differences are only root, epoch path, condition label, deadline and C2's added source-readiness binding. The initial contexts, generated text hashes, token counts and returned score trajectories match in all six base cells. The same seeds/protocol reproduce the same base counts; **these two base blocks are not additional independent replicates**. Sleep51/sleep117 retain their separate pinned adapters and source optimizer counters **4,908 / 7,948**; probe parameters remained frozen, with zero training updates and parent tokens.

### Exact completed-source pointers

The authoritative full completion records, including cells/events, are:

- C2 own base: `/localhome/local-rohing/orch_post_recovery_c2_age_eval_20260918/base/players/R233_C2_AGE_base/COMPLETE.json`.
- C2 sleep51: `/localhome/local-rohing/orch_post_recovery_c2_age_eval_20260918/c2sleep51/players/R233_C2_AGE_c2sleep51/COMPLETE.json`.
- C2 sleep117: `/localhome/local-rohing/orch_post_recovery_c2_age_eval_20260918/c2sleep117/players/R233_C2_AGE_c2sleep117/COMPLETE.json`.
- Earlier comparison base only: `/localhome/local-rohing/orch_post_recovery_age_20260918_attempt3/base/players/R233_ADOPTED_BASE/COMPLETE.json`.

`RECONCILIATION.json` → `source_pointers` binds each exact CONFIG, LOADED, COMPLETE, SOURCE_MANIFEST, GAME_MANIFEST and cell RESULT path to its SHA256 and byte length from `SAME_BLOCK_REMOTE_RECEIPT.json` → `files`. That remote receipt's `blocks.c2.rows` contains only this C2 block's three arms; `blocks.earlier.rows` is separate comparison evidence. The historical local input is `AGE_BLOCK_REFRESH.json` → `rows[].per_seed`, not the earlier block's `AGE_BLOCK_CURRENT.json`.

## Receipts and limits

- `SAME_BLOCK_REMOTE_RECEIPT.json`: exact remote filenames, SHA256/size receipts and text-free event projections; SHA256 `8b4b55c187138ffb4378d9d4bbfed13965a3c65d728cc084ca78b738207b5245`.
- `REPORTER_SOURCE_RECEIPT.json`: retained remote observer source; SHA256 of that observer is `294e682bec4f91c676c393728e0d9c98f2a9f0d7a7699b965dfef05b39ec2810`, identical to the local observer inspected. The verified evaluator runner SHA256 is `64b118f16dd310a97379aa4640f9f7689c36a4024cd6b4a41be14cfc6b5f79f9`.
- `RECONCILIATION.json`: independent recomputation, metric identities and local artifact hashes. Original `AGE_BLOCK_REFRESH.json` SHA256 remains `980cef105dcf2ff6555a7b86980a79be5f763fe6f7ef46bf694cd14e46d9cae3`; stale 22:12 renderings are preserved as `STATUS_2212.md` / `TOKEN_CURVES_2212.svg`.
- `REPORT_VALIDATION.json`: final local test exit status and test count, binding `REPORT_TESTS.log`, the test code, reconciliation receipt and every rendered artifact by SHA256. No new remote reads or jobs are needed to reproduce these reporting checks.

Acceptance is not certified humor; pixels are not pooled global novelty. This is a descriptive pinned-lineage comparison, not a causal learning or broad superiority result, and not every-sleep backlog coverage. The earlier exposure audit's limits remain unchanged; this audit makes no new contamination guarantee.

The September19 00:39 UTC controller error `receiving_lease_expired_no_access` was not bypassed. This audit used the user's separate valid node scope for read-only completed files, conservatively before October1 00:00 UTC. No evaluation rerun, model load, dispatch, life signal, parent/sealed disclosure, git commit or push occurred. The empty failed-observe artifact and all original evidence remain untouched.
