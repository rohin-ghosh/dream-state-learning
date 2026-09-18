# R227 C0 follow-up — 2026-09-18 08:46:51 UTC

**C0 continues, but R227 exclusions-OFF is not live in this native.** The current bounded observation is `LATEST.public.json`; the reading publication cut is `READING_PENDING.public.json`. These contain metadata and raw-receipt pointers only, not child/parent text or host addresses. No learner stop is authorized or attempted.

## Latest actual status

| Item | Source-bound status |
|---|---|
| C0 native | Same PID2561156/start94173182, node2 GPU4, alive and not stopped |
| Original math parent | Same PID2561001/start94172764; one exact-command match |
| Additive reading publisher | Same PID2729920/start94773801; one exact-command match, no replacement or extra parent started |
| Last completed sleep | Cycle67, SLEEP_COMPLETE991, optimizer5372; 16 updates in that sleep |
| Completion time caveat | Last UPDATE990 finished08:44:47.135902 UTC; completion-file mtime08:45:40.342639 UTC, not an embedded completion timestamp |
| Actual eligibility | TARGET_ELIGIBILITY974: 3 candidates, 1 retained, 2 excluded for `provisional_english_target_script_quarantine`; completed991 corroborates |
| Math-parent delivery | Turn16 published08:41:31.042017 UTC, INBOX962, actual masked REQUEST964 render |
| Earlier math-parent delivery | Turn15 published08:32:10.450529 UTC, INBOX904, rendered in REQUEST947/954/964 |
| First reading | REQUEST849 at08:27:36.072316 UTC, response857 at08:28:02.588876 UTC; completed cycle65 ledger |
| Next reading | Publication1 after completed67, published08:45:47.505197 UTC by the existing service; **render still null at08:46:51**, so not claimed child-delivered |
| Memory | memory_after_cycle=null; no memory probe or adapter-retention result claimed |

The two publisher processes remain distinct and original: the established math/onboarding parent plus the previously authorized spaced reading service. Discovery found no duplicate exact commands. This does not claim that differently configured processes elsewhere were exhaustively searched.

## Adoption limit

Main's pushed commit **`bb1e9a9033979d50ed97072675515f7290de1237`** is verified in fetched `origin/main` ancestry and contains the new policy module and native/driver/plain-context changes. Main reports **191 tests / 372 subtests**; this worker did not rerun that suite.

C0's actual deployed plan has **no `learn_row_policy` at either plan or think level**, the deployed R227 policy module is absent, and the original native/driver/plain-context hashes still match its immutable guard pins. Live recipe remains R194 fullwidth-code exclusion, R195 review/receipt exclusion, R209 prose/script quarantine, R213 content filtering, and the old plain-context target check. The new repository commit is **not** evidence of C0 adoption.

The inspected deployed revision has no verified no-gap live adoption control. No source copy, config edit, unsupported toggle/injection, stop, pause, restart, V2 adoption, or extra parent message was attempted. Keep the same life running; preserve provenance, external masking, technical validity, history and the existing baseline. An actual later source-bound recipe/eligibility receipt is required before reporting adoption, not as a launch or learning gate.

## Evidence and publication scope

- Native record root: `/localhome/local-rohing/orch_r216_C0_20260918_attempt2/raw/stream/records/`.
- Math receipt: `/localhome/local-rohing/orch_r216_C0_20260918_attempt2/parent_receipts/000016.json`; latest masked render: `00000000000000000964.json` under the native record root.
- Eligibility: `00000000000000000974.json`; completed sleep: `00000000000000000991.json` under the native record root. Full record SHA256 values are in `LATEST.public.json`.
- Reading publication: `/localhome/local-rohing/orch_r226_c0_operator_20260918/reading/PUBLISHED_0001.json`; SHA256 and pending state are in `READING_PENDING.public.json`.
- Prior baseline-manifest publication remains `51440f045749e8263d5c8dd7848b0b4de03448d8`; prior first-reading/code publication remains `21e4c1fe82f2e79a74b9e06a833127e443f0ce96`.
- This publication is only the explicitly selected R227 reports and sanitized metadata receipts. No raw logs, child/parent text, hosts, credentials, checkpoint bytes, or shared code is included. Earlier `STATUS.md` and its receipts are a historical08:39 cut, not the latest status.
