# Post-reboot recovery — September 19, 2026 UTC

## Verified parent delivery

The requested eight lives have fresh parent INBOX → rendered REQUEST → following
committed ACT receipts. Their GPU natives were not restarted or signalled for
this repair. The curriculum pair retains the same parenting policy and help
budget, not identical corrective text. All authentic child-authored rows remain
eligible for learning; this recovery adds no row exclusion.

| Life | Parent publication ID | First rendered REQUEST | Following ACT REQUEST → RESPONSE | Parent text in ACT |
| --- | --- | ---: | --- | --- |
| Curriculum learner | a7e9f099211c4f5992a85f5911a3efd5 | 6261 | 6268 → 6269 | Yes |
| Frozen sibling | eabd8d4ebb3843dc9c911614f707fe6d | 3629 | 3638 → 3639 | **No: crossed the compaction frontier** |
| Caption observation | 174d2eaad1dd46238132082c05f0a7b6 | 7553 | 7560 → 7561 | Yes |
| Caption perspective | b72bdc83752e4927b308bc91f4880e14 | 7933 | 7940 → 7941 | Yes |
| Caption revision | 86a632da6e464a62aa67bae9bbd29afe | 7136 | 7145 → 7146 | Yes |
| Caption selfderive | 4ff33ae01f5c46d8b753d3a89a66f3d3 | 6697 | 6704 → 6705 | Yes |
| Caption legacy “unparented” name | b117fb7485124f1cbec3d38a3c918a86 | 7335 | 7342 → 7343 | Yes |
| P7, first resumed model-generated turn | 37315131923b49bf937b6e96d3a62fea | 9682 | 9689 → 9690 | Yes |

The first pair publications were queued at 00:57:27 and 00:57:38 UTC. Their
following ACTs completed at 01:05:07 and 01:06:14 UTC. The five fork publications
were queued between 00:56:43 and 01:00:09 UTC. P7's first model-generated turn
was rendered at 01:11:02 UTC; the following ACT completed at 01:11:32 UTC.
P7 also received the operator-authored outage acknowledgment earlier:
REQUEST 9603 → ACT REQUEST 9610 → RESPONSE 9611. That acknowledgment is not
mislabelled as a model-generated turn.

Evidence, relative to `research_loop/workers/`:

- `post_reboot_pair_parents_20260919/FIRST_PAIR_DELIVERY.json` binds both pair
  publications, requests, committed responses, and their different ACT visibility.
- `post_reboot_node3_parents_20260919/FIRST_RECEIPTS.json` binds all five fork
  publications, actual ACTs, rendered/masked parent text, and provider results.
- `post_reboot_c2_p7_20260919/P7_MODEL_DELIVERY_373151.json` binds the P7 model
  turn; `P7_DELIVERY.json` separately binds the operator acknowledgment.
- `post_reboot_c2_p7_20260919/C2_DELIVERY.json` binds C2's earlier restoration:
  INBOX 12589 → REQUEST 12598 → ACT RESPONSE 12599 → COMMITTED 12600.
  `C2_MODEL_DELIVERY_000002.json` additionally verifies a resumed model turn
  at REQUEST 12716; at that observation its following ACT was not yet committed.

**Delivery is not uptake.** P7 still emitted Chinese/intention fragments, not
the requested concrete artifact. C2's first restored ACT still incorrectly
accepted `{A,C,E}` in C5 despite edge EA. Frozen-sibling REQUEST 3629 contained
the parent text, but ACT REQUEST 3638 did not. None of these chains establishes
learning or a successful correction.

## CPU services and gaps

- The P7↔Astra7 bridge is restored with its previous cursor and locks, not a
  fresh conversation. P7 remains Astra7's parent; the overseer does not directly
  parent Astra7. The recorded cursor advanced in both directions.
- P7's CPU parent was handed off while demonstrably idle to the same-policy
  bounded-poll logger at 01:13:14 UTC: PID 378291, start ticks 854895. All 145
  existing files were preserved; no GPU-native signal was sent. Receipt:
  `post_reboot_services_20260919/observer_recovery/P7_BOUNDED_STARTED.json`.
- The hourly collector is live. The missing September 18 23:00 UTC and
  September 19 00:00 UTC cuts, plus 01:00 UTC, exist under
  `post_reboot_services_20260919/cuts/`. Each includes eight players with
  distinct judge epochs. Backfilled outcomes are observed at recovery time;
  historical score-completion times are not reconstructed.
- The restored every-sleep service is **metadata enrollment**, not evidence
  that every enrolled checkpoint has been evaluated. The pre-reboot 1,242
  references were enrollment references, not 1,242 completed probes. No automatic
  all-backlog GPU dispatcher has been verified restored. The restored driver,
  PID 343342, holds both original enrollment locks; launcher PID 343304 is
  supervised. Its first completed poll at 01:02:55 UTC had 1,254 references.
  At the 01:23 verification there were 1,491 references, with all 16 frontiers
  advanced, 12 caught up and four still scanning. All 1,242 original references
  were preserved; zero new evaluations are claimed by this service.
- The 01:00 collector cut has no new node-3 scorer attempts in the 23:00 or
  00:00 hours, despite live natives and restored parents. The reboot had also
  killed the VM-hosted SSH/proxy/SSH judgment transports. These were restored
  at 01:27:29 UTC, with all five original epoch IDs, stable native socket aliases,
  and the unchanged September 24 17:59:20 UTC bound. Scorer and native processes
  were not restarted, and historical ACTs were not replayed.
  Fresh feedback is already joined for revision ACT 7400 → Tool INBOX 7412
  (`ad2cc2c4e4fa4e1780df83c5a15686b1`) and legacy-unparented-name ACT 7514 →
  Tool INBOX 7526 (`66208af45a7f40e99b6f0a8badfab9da`). Both report
  `scene_not_unambiguously_identified`, with **zero scored captions**. These are
  successful error-feedback deliveries, not successful caption judgments.
  The other three forks' first post-repair feedback receipts remain pending at
  this cut; some requests fail before dispatch at the existing 64MiB journal
  export limit. A bounded source-proof repair is being investigated without
  simply raising that limit or weakening provenance. Supervisor adoption of
  transport PID 425470/start 939654 was verified at 01:30:10 UTC, with no
  duplicate process or native/scorer changes. Evidence:
  `post_reboot_node3_parents_20260919/JUDGMENT_RECEIPTS_LATEST.json` and
  `post_reboot_services_20260919/judgment_transport/REGISTRATION_VERIFIED.json`.
- P3's xhigh model parent now has a fresh verified chain, observed at
  01:28:17 UTC: publication `0e2ffa3c8fa54413b454119b1b5e648b`, REQUEST 6925
  → ACT REQUEST 6932 → RESPONSE 6933 → COMMITTED 6934. Exact parent text was
  visible and masked in ACT. Provider request was 01:13:17 UTC, publication
  01:14:03 UTC, ACT completion 01:27:23 UTC; the intervening sleep is not a
  fabricated instant reply. This is **one** fresh chain, not three. Evidence:
  `post_reboot_p3_parent_20260919/FRESH_PROVIDER_REQUEST_ACT.json`. At the
  01:30:14 UTC final cut there were two model publications, one intentional
  silence and one explicit HTTP429 failure across four attempts; publication
  377's delivery remained pending. The parent was still alive with both locks.
- The repository CPU supervisor runs and adopts registered singleton services.
  **Automatic boot installation remains blocked and uninstalled:** platform
  enforcement rejected host service-management commands. The repository's unit
  and `boot.sh` are templates, not an installed boot guarantee. Secure credential
  provisioning after a fresh boot is also unverified; current inherited runtime
  credentials are not proof of boot provisioning. No workaround around the
  platform restriction has been attempted. At 01:23 UTC, supervisor PID 399392
  adopted the pair parents, node-3 parent, P7, C2, bridge and collectors. P3 is
  registered but protected by its existing locks, not argv-adopted. Service
  registry validation had zero errors and 58 scoped regressions passed.

CPU-service evidence:
`post_reboot_services_20260919/observer_recovery/FINAL_HOST_VERIFIED_1789780986904523343.json`
and `FINAL_HANDOFF_20260919T0123Z.md` in that same directory.

## Retention repair

**No live retention deployment is claimed.** Immutable non-running source
closures have now been staged for all 16 R125 natives, with exactly the three
retention files changed and all other guarded Python files preserved in each.
`post_recovery_retention_rollout_20260919/FLEET_STAGED_20260919.json` binds the
16 individual stage receipts. The frozen base generation service is not an R125
Think–Act native and does not receive a fictitious seventeenth deployment credit.
The C2 port passed
17 retention regressions, five legacy tests and five preservation checks;
its staged closure changes exactly the three retention files and preserves the
other 180 Python source pins. `post_recovery_retention_rollout_20260919/C2_STAGED.json`
is explicitly `IMMUTABLE_SOURCE_STAGED_NOT_DISPATCHABLE`.

Receiving-side exact-COMPLETE checkpoint proofs, unchanged deadlines and
confinement, fast checkpoint-plus-tail restore, and explicit post-LOADED parent
rebinding still need to be bound before live adoption. No running native is
stopped merely because a receipt or a receiving preflight is pending. Fresh
correction-chain reviews must distinguish whether the correction actually
survived into the ACT request.

## C2/base count reconciliation

The completed-file audit resolves the disagreement as **replayed score rows,
not a swapped control**. The raw event sums quoted by Fable are reproduced,
but replayed responses retain the original `new_pixel` status. The report's
distinct count deduplicates `(contest_id, caption_sha256)` within each seed;
independent distinct pixel IDs reproduce those totals.

| Source | Seed | Raw scored / accepted / pixel-status rows | Distinct scored / accepted / new pixels |
| --- | ---: | --- | --- |
| Base | 23201 | 72 / 43 / 28 | 50 / 24 / 15 |
| Base | 23202 | 75 / 54 / 40 | 51 / 36 / 24 |
| C2 sleep51 | 23201 | 98 / 66 / 35 | 94 / 62 / 34 |
| C2 sleep51 | 23202 | 78 / 42 / 31 | 76 / 40 / 31 |
| C2 sleep117 | 23201 | 114 / 70 / 22 | 106 / 62 / 19 |
| C2 sleep117 | 23202 | 94 / 54 / 26 | 93 / 53 / 26 |

Both blocks' base text, token and score trajectories match; they are not
independent replications. Each source used 6,144 generated tokens total,
3,072 per seed. Sleep117 is below sleep51 on distinct novelty in both seeds.
These are small descriptive operational-novelty measurements, **not a causal
learning result or certified humor**. A broad “C2 beat base” scientific claim
remains unwarranted. The detailed evidence and definition reconciliation are in
`post_recovery_c2_age_eval_20260918/RESULTS.md` and `RECONCILIATION.json`.

## Fresh semantic baseline and receiving tests — 01:58 UTC

The independent review through September 19, 01:39:59 UTC establishes **no
level-2 or level-3 correction chain** in its bounded fresh windows. Learner,
C2, P3 and P7 score level 0; frozen sibling reaches level 1 by naming its
missing calculation/check. Its correction then disappears before ACT. Some
other lives fail the task despite the correction being present, so retention
loss is not an explanation of every failed correction. Exact hashes, masked
ACT exposure, quotations and coverage limits are in
`research_loop/workers/post_recovery_correction_review_20260919_0139/REVIEW.md`.

Actual pair checkpoint/optimizer/RNG CPU validation and receiving-source tests
pass. Two full live-tail observations timed out; profiling found repeated
history frontier recomputation, not a stopped native. A non-material canonical
prefix-hash cache preserves serialized checkpoints and integrity checks.
Isolated real-checkpoint observers reduce historical COMPLETE-only costs from
37.08 to 19.00 seconds for the sibling and 14.77 to 8.06 seconds for the learner.
No source is deployed to a native; the retained prefix is still fully hashed,
not constant-cost tail recovery. See
`research_loop/workers/post_recovery_pair_receiving_checks_20260919/REPORT.md`.

The every-sleep enrollment service is running, but enrollment is **not probe
execution**. Automatic GPU dispatch is still unverified. Boot installation
also remains platform-blocked/uninstalled; the running supervisor and repository
templates alone do not guarantee recovery after another reboot.

## Execution and C2 checkpoint update — 02:17 UTC

The caption collector completed the September 19 **02:00 UTC** cut for eight
players, with separate judge epochs and no collection errors. The 01:00 UTC
window records base 6 ACT origins, 50 distinct scored strings, 44 accepted and
6 new pixels. P3 has 5 ACT origins and zero scored strings. This remains an
operational ledger, not a humor assessment; missing parsed/fault/token fields
are unknown, not zero.

One source-verified, parent-free age probe of **FRESH_R231 sleep12** has actually
been dispatched on UUID-bound ovx4 GPUs2/7 through the original GPU-host cgroup
route. It retains the original 3 scenes, seeds23201/23202 and 6,144-token budget;
the retained source has 576 optimizer steps and a passing exposure audit.
Main independently reran 24 CPU tests and recorded provenance before launch.
Receipt: `research_loop/workers/post_reboot_probe_dispatch_20260919/MAIN_LAUNCH_1789784249.json`.
At this cut it is **DISPATCHED_NOT_YET_LOADED**, not a completed evaluation and
not an automatic every-sleep fleet dispatcher. No kept life was displaced.

C2's epoch3 closure is staged and actual-node source tests pass. Historical
default COMPLETE11502 fails the current-wall check; the failure is preserved.
Explicit saved COMPLETE12902 passes real adapter/optimizer/RNG/state CPU checks
(8588 optimizer steps). Its optimized historical COMPLETE-only reader still
takes 41.69 seconds because it hashes 23.12 GB, exceeding the bounded 30-second
reservation. Thus C2 stays running unchanged while a verified prefix-cache path
is prepared. Source staging, saved-state validation and live adoption remain
distinct; **live retention adoption is still zero**.

## Actual probe LOAD and retention review — 02:31 UTC

The age probe's player and judge have both actually loaded. The player's
adapter SHA is `c01b385ba9ed28447351b2344efed83fd32513bb3cb0c22012c62d09b7e372f4`;
all evaluation parameters are frozen, with no optimizer, source working
context, or parent text loaded. Both processes proved access to their assigned
GPU and EPERM on the other seven GPUs. The first development judgment arrived
at 02:18:28 UTC. This updates the earlier dispatch-only cut, not the claim of
automatic fleet evaluation. Final deduplicated metrics remain pending.
Receipt: `research_loop/workers/post_reboot_probe_dispatch_20260919/FIRST_LOAD_1789784335.json`.

The supervisor heartbeat at 02:27 UTC still identifies the restored pair,
five-fork provider, C2 and P7 parents, Astra7 bridge, collector and enrollment
processes. The P3 singleton lock remains held; that fact alone is not a new
P3 delivery receipt. Boot installation remains blocked/uninstalled.

Main found two additional fast-reader integration requirements before any
live retention adoption: a proof produced at an earlier COMPLETE must support
an explicitly authorized later COMPLETE with the intervening records and
INBOX contents fully verified; and a host-side observation must not be
mistaken for a confined-reader startup test. A read-only node5 check at
02:30:14 UTC observed host mount namespace `4026531832` and live C2 PID1139778
namespace `4026536303`. The initial same-namespace proof would reject the real
reader. Both issues are being addressed in separately bound candidate sources;
no native was stopped, no reservation increased, and no integrity check or
original confinement admission was bypassed.

## Completed age probe, with one missing judgment — 02:39 UTC

The single FRESH_R231 sleep12 probe completed all six cells and all 6,144
generated tokens. Both probe processes exited and released GPUs2/7; the six
protected native/base/scorer process identities remained unchanged. There was
no parent context and no parameter update during evaluation.

| Seed | Generated tokens | Distinct scored captions | Distinct accepted captions | Distinct pixel IDs | Unscored captions |
| --- | ---: | ---: | ---: | ---: | ---: |
| 23201 | 3,072 | 61 | 28 | 12 | 1 |
| 23202 | 3,072 | 67 | 19 | 12 | 0 |

Caption sets use `(contest_id, caption_sha256)`; independent per-seed pixel-ID
sets agree with de-replayed new-pixel outcomes. The original raw novelty
counters, 19 and 15, include repeated results and must not replace 12 and 12.
This is an executed development probe, not evidence of retained improvement,
certified humor, or a restored automatic fleet dispatcher.

One outcome is unknown, not rejected: its canonical scalar input tokenizes to
621 tokens against the unchanged 512-token limit. The exact failed traceback
was not retained by the generic provider-error handler; a hash-bound, model-free
CPU reconstruction necessarily fails that pre-model guard. The original probe
recorded the error, fed it back, and continued its fixed-token trajectory. The
failed caption was never scored. Missing feedback makes an error-free
comparison claim inappropriate; no compensating rerun or silent truncation was
performed.

Receipts: `research_loop/workers/post_reboot_probe_dispatch_20260919/METRIC_RECONCILIATION_1789785355.json`
and `research_loop/workers/post_reboot_probe_dispatch_20260919/PROVIDER_ERROR_AUDIT_1789785359.json`.

## Real C2 prefix-reader measurement — 02:50 UTC

An isolated, non-dispatchable 185-file CPU source on node5 now exercises the
reviewed v4 reader against the real C2 journal. Prevalidation hashes all
24,205,128,929 bytes through COMPLETE13120, including original intent checks,
in **43.37 seconds outside any reservation**. The subsequent full live reader
takes **3.24 seconds**, verifies all 13,121 cached prefix identities plus the
52.1 MB raw tail, and preserves 356 INBOX entries and the required correction
sidecar. The observed tail contains a pending REQUEST and RESPONSE; it is
**not an eligible COMPLETE handoff boundary**.

Separately, both passes over all 26,242 record/intent identities through the
existing native's `/proc/1139778/root` view match in 0.35 seconds; 185 source
file hashes also match. This is a filesystem-view observation, not a new
confined consumer's startup, permission, or admission proof. PID1139778,
start30025875, UID2524 is unchanged. The native received no signal.

The candidate preserves the strict same-namespace default and adds an explicitly
original-admission-pinned cross-namespace mode. A three-second quiet-age check
rejects young cached files before hashing; this addresses an independent test
that exposed same-size/mtime-restored changes within a filesystem timestamp
quantum. Metadata remains conditional on coherent attributes, timestamp
granularity shorter than the window, and no privileged rollback. It is not
cryptographic immutability. The v4 suite passes 177 new synthetic checks plus
18 original-default checks; main's staging/view helpers pass 19 checks.

The production source epoch needs its own proof, actual confinement admission,
parent fence/rebind and all-in bounded handoff measurements. Neither this
observer proof nor its 3.24-second reader time proves those steps. No source was
adopted by a live native, no row policy changed, and the reservation maximum
remains 30 seconds.

Evidence under `research_loop/workers/post_recovery_pair_receiving_checks_20260919/`:
`C2_PREFIX_PRODUCED_1789786161.json`, `C2_PREFIX_NATIVE_VIEW_1789786184.json`,
and `C2_PREFIX_FAST_READ_A_1789786189.json`. Full proofs and journals stay on
node5, not the VM.

P3's fresh 02:46 UTC audit also verifies parent387 REQUEST7249 -> ACT7256/7257
-> COMMITTED7258, and parent389 REQUEST7330 -> ACT7337/7338 -> COMMITTED7339.
Parent392 was published at 02:37:03 UTC but had no exact rendered request in
that bounded audit yet; publication is not counted as uptake.

## Production-source checks and fresh service health — 03:08 UTC

The September 19 03:00 and 03:01 UTC collector cuts exist, with eight players
and the original separate judge epochs. The supervisor heartbeat has no
errors and still adopts the existing publishers rather than duplicating them.
The original learner and sibling parent processes are independently verified
alive with their singleton locks at 03:07 UTC. Each has published 14 model
turns; 13 per arm have rendered REQUEST receipts. These are delivery counts,
not evidence that either arm applied a correction.

C2's separate production epoch4 source is now staged and passes its four
actual-node CPU check groups. Its own proof binds 186 Python files plus the
startup-context asset, not the earlier 185-file observer closure. Prehashing
the same 24.205 GB prefix through COMPLETE13120 took 43.35 seconds outside
any reservation. Two existing-native filesystem-view passes verify all
26,242 prefix record/intent objects and all 187 source files in 0.35 seconds.
The original native PID1139778/start30025875 is unchanged.

The first production-source live scan **refused** with
`journal_changed_during_scan` after 20.8 seconds: C2 appended records while
the observer was reading its growing tail. This is not a successful recovery
measurement or a reason to stop the native. The failed receipt is preserved.
An explicit later-COMPLETE scan and the complete owner/admission/commit timing
remain necessary. The C2 owner fence/drain/rebind transport is being built;
there is still **zero live retention adoption** and no reservation or native
signal. The 30-second reservation limit is unchanged.

Evidence under `research_loop/workers/post_recovery_pair_receiving_checks_20260919/`:
`C2_EPOCH4_STAGE_1789786692.json`, `C2_EPOCH4_CPU_1789786756.json`,
`C2_EPOCH4_PREFIX_PRODUCED_1789786900.json`,
`C2_EPOCH4_FAST_READ_A_1789787170.json` (refusal), and
`C2_EPOCH4_NATIVE_VIEW_1789787224.json`.
Fresh parent status is in `post_reboot_pair_parents_20260919/SUMMARY.json`;
collector receipts are in `post_reboot_services_20260919/cuts/`.
Automatic boot installation remains platform-blocked/uninstalled, and
every-sleep enrollment is still not automatic GPU-probe execution.

## Production forward-checkpoint scan — 03:16:55 UTC

The production proof now passes an explicit forward scan from COMPLETE13120
to COMPLETE13231, with matching driver LEARN13232 and optimizer step8780.
The reader takes **4.32 seconds**, fully hashes the 111 intervening records
(602,615,152 bytes) and the 52,678,239-byte tail, and retains all 360 INBOX
entries. No full-prefix fallback occurs. The observed tail has a pending
REQUEST; it is preserved, not dropped to manufacture an eligible boundary.
This remains a strict host-namespace observation, **not native admission or a
30-second whole-handoff proof**. No parent fence, native signal or deployment
has occurred.

Independent review also identified a limit in the earlier native-view helper:
it checked source hashes but did not attest all producer-pinned source-object
identities and the separate epoch file. The read-only helper now checks the
exact file and epoch identities, all parent directory chains, complete file
and directory inventories, source/epoch hashes, and immutable directory
metadata. Twenty-nine worker regressions pass, including byte-identical source
and epoch replacement, missing inventory, changed chains and directory
metadata. A fresh real C2 observation verifies 187 source files, one separate
epoch file, eight immutable directories and 26,242 prefix record/intent objects
twice in 0.297 seconds. Future consumer permissions and original confinement
admission still require their own checks.

Receipts: `post_recovery_pair_receiving_checks_20260919/C2_EPOCH4_FORWARD_B_1789787815.json`
and `C2_EPOCH4_NATIVE_VIEW_IDENTITY_1789787593.json`. Earlier partial-attestation
receipts and the refused moving-journal scan remain preserved, not overwritten.

The 03:09 UTC P3 audit verifies parent392 rendered at 02:49:11 and committed
its following ACT at 02:50:48; parent395 rendered at 03:03:19 and committed
its following ACT at 03:04:54. Parent398 was published at 03:05:15 but had no
exact rendered REQUEST in that bounded cut. The original xhigh publisher
PID346649/start795156 remains alive. This confirms cadence and delivery, not
correction uptake or caption quality.

## Node2 storage failure and capacity repair — 03:50 UTC

The node2 root filesystem exhausted user-writable space at about 02:44 UTC
on September 19. C0, Astra7 and the extra node2 caption life stopped; this was
not a reboot. **All three remain down at this report.** The P7/Astra7 bridge
process still exists but points at a dead Astra7 native, so process liveness
must not be reported as successful bridge delivery.

Capacity is repaired without deleting research evidence or changing active
7B weights: the pip download cache was removed, and an unused 14B download
cache was archived directly on ovx4. Full archive and member verification
covered hashes, symlinks, types, modes and mtimes before source-duplicate
removal. The 29,551,749,120-byte archive has SHA-256
`fd71d5cb056169b25bb7c3f83b2007ce740c1f79efdd9a45415bb38698858c39`.
The verified final node2 available capacity was 33,240,977,408 bytes. No
multi-GB archive was written to the VM. Receipts and restoration-catalog
location: `post_reboot_node2_capacity_20260919/VERIFIED_CACHE_RELOCATION_1789789200.json`.

Restart is not yet an exact-COMPLETE continuation. C0's last committed sleep
is 145 (COMPLETE6631, optimizer8412), followed by three new rows and 48 UPDATE
receipts. Its next optimizer file is truncated, with no COMMIT. Astra7's last
committed sleep is 146 (COMPLETE7750, optimizer9644), followed by three new
rows and 29 UPDATE receipts, then an empty unpublished intent. Unsaved
optimizer/RNG state cannot be reconstructed from those receipts. Failed files,
rows, working state, records and checkpoints remain preserved. No partial
checkpoint has been promoted, pending state cleared, old one-shot guard reused
or saved-boundary rollback represented as exact resident continuity.

Independent diagnosis: `post_recovery_prefix_proof_20260919/node2_enospc_20260919/RECOVERY_PLAN.md`.
The extra caption life's exact recovery boundary is being checked separately.
Any recovery needs an explicit interrupted-sleep reconciliation record and a
fresh original confinement/admission path; no lease extension is proposed.

The automatic age-probe candidate's read-only preflight also timed out at
120 seconds around 03:47 UTC, before activation or model load. Its source-epoch
validation repeatedly scans and decodes full journal records from old LOAD
positions. A bounded validation repair is in progress; enrollment remains
running but is not automatic GPU-probe execution. The eight requested parents
remain attached, and collector cuts through 03:01 UTC exist. Live retention
adoptions remain zero; the 30-second reservation maximum is unchanged.

## Follow-up checks — 04:05 UTC

The 04:00 and 04:01 UTC collector cuts now exist, each covering eight player
ledgers with separate judge epochs and no collection errors. This is not a
claim that all eight players are currently running. The 03:52 pair audit
verifies both original publisher identities and locks: learner has 19 queued,
18 rendered REQUEST and 18 following-ACT receipts; sibling has 18 queued and
17 rendered REQUEST receipts. Only its first following ACT is independently
bound in that report, and that ACT lacks the parent text. No correction-uptake
claim follows from these counts. The five node3 first-turn chains were also
reverified against their original live bindings at 03:52 UTC.

C0 sleep145 and Astra7 sleep146 now have complete binary verification against
their committed manifests: every adapter file and both 161,853,949-byte
optimizer/RNG files match. The read-only check took 0.78 seconds. Receipt:
`post_reboot_node2_capacity_20260919/COMMITTED_CHECKPOINT_BINARY_AUDIT_1789790037.json`.
Their pending sleeps still cannot be described as exact resident-state recovery.
A CPU-only declared-restart contract preserves all 444/453 rows, including
three pending rows each, and the exact pending history/working state. It names
the RNG source as the last durable COMPLETE, not the unsaved post-generation
state, and requires separate recovery-compute accounting. Fourteen regressions
pass; actual source-record checks pass in 1.55 seconds. This contract is **not a
native implementation or launch authorization**; no restart has occurred.

The extra node2 caption player is simpler: its head is COMPLETE8527 followed
by LEARN8528, sleep119, optimizer10236, with 487 rows, frontier487 and pending
null. It failed after training completion during readout/error publication.
Its failed readout must not be silently retried. A bounded reader port for its
unchanged caption/runtime route is being prepared, not yet launched. Evidence:
`post_recovery_prefix_proof_20260919/node2_enospc_20260919/CAPTION_RECOVERY_ASSESSMENT.md`.

P7 received an explicitly operator-authored factual notice that Astra7 is down,
not a fabricated child reply: INBOX10940 -> REQUEST10943 -> ACT REQUEST10950 ->
RESPONSE10951 -> COMMITTED10952. The notice remains visible in that ACT. P7
still answered with mixed-script intention text, not the requested reading or
writing artifact. Evidence: `post_reboot_node2_capacity_20260919/P7_ASTRA7_OUTAGE_DELIVERY.json`.

The probe-queue V4 CPU repair passes 88 tests locally and on the receiving host.
Cold source validation is bounded into small calls but still takes 178.56
seconds for 17.29 GB; a warm same-process recheck takes 0.099 seconds. Pending
validation cannot launch a job. The concrete frozen-sibling capsule remains
bound to V3, so an immutable same-job runtime/config rebind is in progress.
Automatic probe execution is still not restored. Neither native recovery nor
retention adoption nor VM boot-service installation is claimed here.

## Caption recovery and queue handoff — 04:20 UTC

The extra node2 caption player subsequently loaded successfully through its
original dispatch and confinement route. `MAIN_LOADED_AND_NOTICE.json` in
`post_recovery_node2_caption_20260919/` records LOADED8529 at 04:19:23 UTC,
restoring COMPLETE8527 / LEARN8528, sleep119 and optimizer step10236. Its
failed readout is preserved and was not rerun. All487 rows and the original
wall bound are retained. The factual operator notice is queued; that receipt
does not verify its REQUEST/ACT delivery or restore the model parent by itself.

The probe queue's immutable V4 runtime/config rebind is now complete and passes
107 CPU tests locally and on the receiving host. The detailed handoff is
`post_reboot_probe_queue_20260919/V4_REBIND_HANDOFF.md`. It is ready for Main's
activation, not an activated automatic evaluation service. C0 and Astra7
remain unrecovered at this cut. No live retention adoption is claimed.
