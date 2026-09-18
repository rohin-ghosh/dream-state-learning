# R233 node2 kept-life recovery

## Deadline table — actual capture September18 17:37:59 UTC

`TABLE_1738.public.json`: C0 native745118 alive at UPDATE3003; Astra7 native762967 alive at UPDATE3250; caption native787115 alive/replaying, head3303, **new LOAD still absent**. C0 sole parent778946/start98105351 remains alive, with actual new INBOX2951 → REQUEST2953 → ACT2963/2965. Parent receipt/source and explicit horizon limits published `937cfaa254136713eee8d23858ad295ce764e5c6`. Native horizons remain C0 Sep18 22:55:15Z, Astra7 Sep18 22:59:36Z, caption new plan/guard Sep20 18Z; C0 parent Sep20 17:59Z. Caption API parent and future feedback are not yet proven. Longer C0/Astra7 live native horizons are authorized but not applied. No all-restored claim.

## Current table — September18 17:35 UTC

| Arm | Actual alive/LOAD/first ACT | Parent delivery | Effective deadline |
| --- | --- | --- | --- |
| C0 GPU4 | PID745118/start98001699; LOAD2871 17:21:10Z; ACT2883/2885 17:22:07Z; continuing training | **New** publication0021 17:30:21Z → INBOX2951 → REQUEST2953 → ACT2963/2965 17:33:48.940358Z. Sole parent778946, no duplicate. | Resident native stillSep18 22:55Z; renewed CPU parentSep20 17:59Z. |
| Astra7 GPU1 | PID762967/start98059264; LOAD3128 17:26:46Z; ACT3140/3142 17:27:10Z; continuing training | Turing owns authentic P7 bridge; no renewal/render claim from this worker. | Resident native stillSep18 22:59Z; long-horizon live extension unresolved. |
| Kept caption GPU2 | PID787115/start98128665 starting/replaying; LOAD pending17:34:23Z | API parent not yet started before actual LOAD; scorer owner reports transport onlythrough17:59:30Z, future result pending. | New tested plan/guardSep20 18Z; actual LOAD and service horizons separately tracked. |

`C0_NEW_PARENT_0021.public.json` proves new parent visibility and subsequent output, **not recall correctness/retention**. `LIVE_1735.public.json` is current-incarnation metadata only. User's longer existing allocation does not retroactively mutate C0/Astra7 resident alarm/loop/timeout values: see `DEADLINE_EXTENSION_LIMITS.md`. Caption's failed pre-native attempt was preserved, fixed and retested125 CPU tests; repaired gate/source pushed `b94415f46926e1e548cde28af18a699e3c139837` before its one-shot retry. No all-restored claim.

## Update — September18 17:27 UTC

Astra7 actual LOADED3128 at17:26:46.873724Z, native762967/start98059264, completed sleep87/optimizer6796; first REQUEST3130 at17:26:47.915813Z/12175 tokens. Outage7018.849s. Turing handoff contains exact new identity/source/guard/journal and22:59:36Z horizon; no P7 bridge success is inferred. Caption one-shot dispatch started immediately after this verified LOAD; no ACT dependency. Both original roots/devices remain separate; no duplicate starts. `ASTRA7_LOADED.public.json` contains source hashes. C0 continues running with verified empty semantic filters and sole curriculum writer.

## Current recovery — September18 17:24 UTC

| Kept arm | Actual incarnation evidence | Current blocker / next step |
| --- | --- | --- |
| C0 / GPU4 | Native745118/start98001699; LOADED2871 at17:21:10.338114Z, sleep98/optimizer6156; REQUEST2873 at17:21:12.417179Z, 11483 tokens; RESPONSE2883/ACT2885 at17:22:07.164669Z | Running. Outage17307.073s; same journal and saved state. No uninterrupted-memory claim. |
| Astra7 / GPU1 | Native762967/start98059264 dispatched17:22; no new LOADED yet at17:22:41Z | Existing native validating original journal. Do not duplicate. Turing alone owns P7 bridge. Estimated LOADED17:29–32Z, not a receipt. |
| Kept R229 caption / GPU2 | Not dispatched; receiving124+32 tests, full archive replay, saved sleep76/optimizer6940 and correction cache verified | Launch immediately after verified Astra7 LOADED; no semantic ACT dependency (Main17:25). External transport owner reports route renewed only through17:59:30Z; real future feedback still unverified. |

C0 sole curriculum writer762836/start98059019 began17:22:31Z. Its first attempt failed before publication because the CPU identity receipt omitted `journal_id`; failed files preserved, scoped fix passes6 local and6 receiving regressions, no learner restart. Actual inherited INBOX2858 rendered in current REQUEST2873, followed by THINK2874 and ACT2883/2885. It was **not republished**. This is visibility and output evidence, not reading uptake or recall success. `C0_LOADED.public.json` and `C0_PARENT_RECEIPTS.public.json` carry hashes and paths, not raw text. R227 all-authentic policy is present in both recovery plan/THINK; fresh sleep recipe evidence follows when observed.

Receipt reader now finds current PID/start-bound LOADED even beyond256 records, and excludes inherited/reused-PID loads. Readout-only change; frozen running native remains unchanged. Next aggregate table due17:38Z even if some rows remain pending.

17:24 live-policy evidence: C0 SLEEP_RECIPE2899 SHA `b3b78c3f36738c9db7a4e66d696eeeec675f15c447e5a17b9e546ecb27a5100a` explicitly reports `R227_ALL_AUTHENTIC_CHILD_ROWS_V1`, `active_semantic_filters: []`, `semantic_row_exclusion: false`; UPDATE2909 was current at17:24:05Z. This is actual resumed training-policy evidence, not an edit to unloaded source. C0 receipt/source publication pushed `20dc2a2096a1ee5723aee47fab3e249314980899` (8 explicitly audited paths, no transcripts/hosts/binaries).

## Initial diagnosis

2026-09-18 16:53 UTC: diagnosis complete; neither recovery launched yet.

- Node2 has not rebooted since September 7. The three occupied devices belong to unrelated creative lives (GPU0/5/7); protected, no signals issued.
- C0 GPU4: old native2561156 absent. Systemd explicitly records its finite runtime limit at12:32:43.014559 UTC, then timeout. Coherent saved sleep98/optimizer6156 survives; interrupted REQUEST2869 remains preserved.
- Kept R229 caption GPU2: old native2884345 absent. Outer timeout returned124 at15:36:39.690600 UTC, ten seconds before the configured operator wall. Coherent saved sleep76/optimizer6940 survives; later partial sleep updates are not a completed checkpoint.
- Original journals and all tail records will remain. Saved-boundary recovery is not uninterrupted resident/RNG continuity. No snapshot51 rebirth or stale-life resurrection.
- Recovery uses the existing guarded one-device continuation path, with a new explicitly authorized finite epoch, source-bound CPU/provenance checks and prospective R227 no-semantic-exclusion policy in native and THINK.
- Caption scorer owner coordination required: renew the existing session and trusted node2 socket relay for the new epoch. No ovx4/P3 operations are authorized here; no direct child networking or fabricated feedback.
- Main exclusively owns `rohin216_c0_20260918/commit-worktree`; it will not be written here.

Initial census: `INITIAL_DIAGNOSIS.public.json`. Parent/feedback restart and LOADED/REQUEST/ACT are pending, not claimed.
