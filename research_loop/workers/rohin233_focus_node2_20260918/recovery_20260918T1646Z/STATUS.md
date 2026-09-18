# R233 node2 kept-life recovery

## Actual renewed natives — September18 18:21UTC

| Arm | Alive / exact completed source / actual renewed output | Fresh parent status | Native / wrappers |
| --- | --- | --- | --- |
| C0 GPU4 | 881309/start98332476; COMPLETE102/opt6348; WALL3191 filetime18:17:33.666160; **LOAD3192 18:17:34.010007UTC**; REQUEST3196 → RESPONSE3204/ACT3206 18:18:36.770010. Reload gap**575.248534s**. | Sole CPU parent913254; exact preserved ledger, clock101→actual102 corrected/tested without learner controls. **New turn024 queued18:20:25.763086**, idc442d95a490a4f61ae34e45953252495. INBOX/render/ACT not yet observed; earlier17:33 delivery is NOT counted. | Actual WALL/nativeSeptember20 18UTC; active systemdapproximately17:59:44 and timeout17:59:48.76 that date. Parent17:59UTC/80-publication cap. |
| Astra7 GPU1 | 886059/start98343651; COMPLETE92/opt7052; WALL3544 filetime18:15:05.607489; **LOAD3545 18:15:05.943992UTC**; REQUEST3547 → RESPONSE3555/ACT3557 18:15:22.859973. Reload gap**314.863329s**. | Exact new identity/LOAD handed to Turing; P7 bridge rebind and fresh authenticated parent render remain **unverified**, not inferred from ACT. | Actual WALL/nativeSeptember20 18UTC; active systemdapproximately17:59:44 and timeout17:59:48.5 that date. Bridge owner reports separately. |
| Kept caption GPU2 | Unchanged787115/start98128665; no new stop/reload in this follow-up. Existing WALL3304/LOAD3305 17:38:46.250332. | Existing same-incarnation INBOX3455 → REQUEST3457 → ACT3467 at17:55:24.001294; API parent3001805 remains alive. Not used as C0/Astra7 proof. | NativeSeptember20 18UTC; active systemd/timeout approximately17:59:44/17:59:48.64; parent17:59UTC. |

Gaps are old-native-absent→newLOAD; TERM→LOAD is575.499274s(C0),315.164559s(Astra7). No deliberate idle or SIGSTOP; CPU replay/loading accounts for handoff time. Both source-record bindings, actual loaded adapter-state digests, optimizer counters and deadline-only saved-state comparisons verify. This is restored-state continuity, not uninterrupted resident execution or recall success. Exact files: `C0_CONTINUATION_LOADED.public.json`, `ASTRA7_CONTINUATION_LOADED.public.json`, `C0_POST_RENEWAL_PARENT.public.json`. One readout regression explicitly distinguishes adapter-file-manifest hashes from adapter-tensor-state hashes; no model source changed.14 local/14 receiving bounded controller/parent/readout tests pass after CPU-only clock repair; original receiving native suites125 each remain unchanged.

## Exact-COMPLETE continuations — September18 18:10UTC

Explicit17:59:12 authorization is being executed now, not at22:55. Gate/source pushed582215ddb9d2b9981ac8f2d79660d0f2399afefa before controls:125 receiving tests per arm plus12 local/12 receiving boundary/parent-ledger regressions. The gate's initial18:08 heading was a one-minute labeling error, corrected to18:07; actual controls have timestamped receipts.

| Arm | Actual current continuation | Parent / feedback | Horizon |
| --- | --- | --- | --- |
| C0 GPU4 | Latest COMPLETE102/opt6348, record3189; old process absent18:07:58.761473UTC. New native881309/start98332476 is STARTING; new LOAD/gap not yet available. Same journal/state preserved. | Supported exit of sole CPU parent preserves full ledger/pending packet. One successor waits for actual LOAD; no duplicate/republication. | New plan, timeout and systemdSeptember20 18UTC; actual WALL pending. |
| Astra7 GPU1 | Latest COMPLETE92/opt7052, record3542; old process absent18:09:51.080662UTC. New native886059/start98343651 is STARTING; LOAD/gap pending. | Turing notified in TO_TURING.md; authentic P7-only bridge rebind is his task, not claimed here. | New plan and wrappersSeptember20 18UTC; actual WALL pending. |
| Caption GPU2 | Same live native787115/start98128665, LOAD3305 at17:38:46.250332UTC. No continuation/control performed in this follow-up. | **Actual parent INBOX3455 → REQUEST3457 at17:55:12.151217 → RESPONSE3465/ACT3467 at17:55:24.001294**, masked history. Not a quality/uptake claim. | Actual WALL3304 and active timeout/systemd boundSeptember20 18UTC; parentSeptember20 17:59UTC. |

Caption's earlier17:59:30 transport deadline is superseded by its owner's17:47 renewal receipts `LEASE_TRANSPORTS_RENEWED.json` and `LEASE_RENEWED_SHARED3.json` under `rohin233_ovx4_recovery_20260918`. This worker did not modify or inspect private scorer content; future feedback only, no history rescore. Old dated entries below are historical, not current blockers. No SIGSTOP, deliberate idle, unrelated-owner controls or new lease. Final actual LOAD gaps and parent/bridge observations will follow.

## Caption real output/feedback — September18 17:40 UTC

First ACT RESPONSE3323/ACT3325 finished17:39:09.899196Z. R184_ACT3326 reportsPUBLISHED/executedtrue with a scorer receipt, and that feedback is **actually visible in REQUEST3329**, history tokens masked. The outcome is `scene_not_unambiguously_identified`, not a successful score or quality result. Two subsequent genuine ACTs likewise produce visible ambiguity feedback. WALL_EXTENDED3304 proves the deadline-only extension toSeptember20 18Z. Actual sleep recipe3355 confirms all-authentic rows, empty semantic filters, exclusionfalse. Private results/scores/panels are not exported; `CAPTION_OUTCOME.public.json` contains operational evidence only.

Caption sole API parent3001805/start186017646, launched with inherited current-shell credentials without logging/persisting them, actually published message548e901e48134e2e83dcdb01ba3bee96 at17:39:54.806272Z. Its parent horizon isSeptember20 17:59Z. INBOX/render/answer remains pending while native completes sleep; a running process/publication is not mislabeled as delivery. External scorer/transport horizon renewal remains with its owner; last verified17:59:30Z. C0/Astra7 remain untouched pending Main's requested boundary-restart exception.

## Caption actual LOAD — September18 17:38:46 UTC

Caption native787115/start98128665 actual **LOADED3305 at17:38:46.250332Z**, SHA `22e8f53f17de848e2b2700ae38edd2565b979b4853f3cf275b41033e8c505b4b`; resumed sleep76/optimizer6940, same journal. First REQUEST3307 at17:38:47.431631Z/10482 tokens. Supported deadline-only extension applied for this resume through**September20 18UTC**, existing lease unchanged. Outage7326.536s. `CAPTION_LOADED.public.json` contains hashes. First ACT and future feedback still being observed; API parent startup is separate from actual publication/render. The17:38 table accurately recorded the earlier17:37:59 pre-load snapshot and is not rewritten. All three native LOADs now observed; **not** all parents, feedback, or live long-horizon updates restored.

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
