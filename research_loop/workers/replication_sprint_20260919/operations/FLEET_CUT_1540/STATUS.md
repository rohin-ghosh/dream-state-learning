# Morning fleet status — bounded read-only cut

**2026-09-19: native cut 15:41:52–15:41:53 UTC (08:41 PDT); local process/status cut 15:42:53–15:42:59 UTC.** Later local linkage reads are timestamped in `EVIDENCE_LINKS.json`; no remote refresh or polling loop. The folder name FLEET_CUT_1540 is a label, not an assertion that observation occurred at 15:40.

**4/4 requested learning/control natives are alive at their source-bound PID/start identities and GPU-resident. The curriculum pair is NOT currently receiving new model-parent turns: both publishers remain blocked on original HTTP401/auth_error attempts. Original probe activation is alive, but its latest log records a persistent admission pause and zero active probes. Collector files exist; they do not certify a complete current-hour fleet window.**

## Per-life cut

Start timestamps below are kernel boot-time + start-ticks, UTC; journal times are file mtimes, not independently verified generation times. A fresh journal record proves activity, not semantic progress.

| Life / host | Native PID / start ticks | Native started UTC | Last record at cut | Parent delivery / visibility |
|---|---|---|---|---|
| CURRENT_learner / ovx4 | `493500 / 10070880` | 2026-09-18 18:12:03.800000 | UPDATE 12499, 15:41:48 | Publisher 345404 alive but BLOCKED_PROVIDER. Latest local proof: INBOX8099 → REQUEST8157 → ACT stage8167, finished 04:59:53; no new parent delivery established after that historical proof. |
| r232_frozen_sibling / ovx4 | `471737 / 9987073` | 2026-09-18 17:58:05.730000 | R191_DATASET_ROW 5810, 15:41:22 | Publisher 345405 alive but BLOCKED_PROVIDER. Latest parent-ledger INBOX4378 → REQUEST4388, 05:04:14; following-ACT/ACT-prompt exposure for this latest message not established. |
| P3 / node4 | `699464 / 33078516` | 2026-09-18 20:16:54.160000 | REQUEST 11678, 15:41:48 | Parent 346649 alive. Hash-matched INBOX11606 at 15:27:15. Newer turn553 PUBLISHED at 15:41:30 is not registered in this native cut; no latest-message ACT rendering verified. |
| P7 / node4 | `563796 / 32330897` | 2026-09-18 18:12:17.970000 | UPDATE 15859, 15:40:49 | Parent 378291 alive. Hash-matched INBOX15799 at 15:33:50. Newer sequence283 published 15:34:53 is not registered in this native cut; no latest-message ACT rendering verified. |

Latest COMPLETE records are metadata-only (no restore verification): learner12444 at15:32:10; frozen5793 at15:32:12; P7 15780 at15:30:15. P3 latest COMPLETE is pinned in `NODE4.json`. Parent ledger/proof files are historical evidence; the pair has no INBOX record in the bounded newest-96-record windows.

## Services and observation coverage

| Component | Actual identity / newest file | Operational finding |
|---|---|---|
| base_player_generation (ovx4) | `459712 / 9942311`; start 2026-09-18 17:50:38.110000 UTC | Frozen-base role alive and GPU-resident; latest saved attempt268/1 at15:28:23. That is the last observed attempt, not proof of delivery in the current minute. |
| shared_node3_scorer (ovx4) | `499900 / 10094999`; start 2026-09-18 18:16:04.990000 UTC | Alive, expected start and command hash match, GPU-resident; shared caption/scoring role on ovx4. No endpoint or scoring call made; process liveness is not current feedback delivery. |
| shared_node2_scorer (ovx4) | `499905 / 10095034`; start 2026-09-18 18:16:05.340000 UTC | Alive, expected start and command hash match, GPU-resident; shared caption/scoring role on ovx4. No endpoint or scoring call made; process liveness is not current feedback delivery. |
| base_scorer (ovx4) | `506797 / 10120809`; start 2026-09-18 18:20:23.090000 UTC | Alive, expected start and command hash match, GPU-resident; shared caption/scoring role on ovx4. No endpoint or scoring call made; process liveness is not current feedback delivery. |
| original_probe_activation (ovx4) | `1221703 / 13926322`; start 2026-09-19 04:54:38.220000 UTC | Original process alive; latest log mtime13:59:42, active=[], pending1638, retained1646. Pause: `ADMISSION_OR_INPUT_FAILED:ValueError:source_record_changed_during_read`. Log is change-driven, not a current heartbeat; no fresh dispatch inferred. |
| P3 scorer (original node4) | `573479 / 32379360` | Alive with expected command; GPU resident. Judge bridge570041 also identity-matched. |
| Every-sleep enrollment | Launcher`343304 / 788315`; driver`343342 / 788324`; LATEST mtime15:42:33 | Alive;1976 enrolled;new_evaluations=0;backlog_dispatcher_started=false. Enrollment is not capture, probe completion, or current-hour metrics. |
| Caption hourly collector | `311631 / 717211`; last success15:01:05, cut15:01:04 | Successful report exists, errors=[]; latest recorded ACT-origin bucket is14:00 for base but08:00 for P3. Outcomes are observed at collection, not certified completed by the origin-hour boundary. No15:00–16:00 completed-window claim. |
| Correction hourly collector | `298357 / 687734`; CURRENT mtime15:00:45; next scheduled cut16:00 | Partial fleet. CURRENT learner = FRESH_R231: caught_up=true, through=head12234 at that cut. P3:11374/11473 and frozen:5626/5730, both caught_up=false. P7 unresolved/not collected. Do not mislabel unresolved R232_SIBLING_LEARNER alias as the CURRENT learner. |

Shared ovx4 judge bridges502015,502012 and507837 are also identity-matched. Shared scorer names mention node2/node3 origins; those nodes and their lives were not remotely audited. No C2 measurement.

The correction collector reports exact parent-text exposure in0/3 sampled CURRENT learner ACTs,0/4 frozen ACTs and2/2 P3 ACTs at its earlier cut. These are bounded existing receipts, not a new semantic evaluation, whole-hour uptake estimate, or evidence that the latest parent message was rendered.

## Actionable blockers — owner/main only

- **Parenting:** restore valid authorization for the original pair provider through its existing secure owner workflow. Original learner/frozen attempts logged HTTP401/auth_error at05:00:08 /05:08:31 UTC and remain `AMBIGUOUS_OR_UNVALIDATED_NO_REDISPATCH`, retry_permitted=false. Do not treat a live publisher as delivering or bypass the no-redispatch disposition. This audit did not read credential values, inspect process environments, test credentials, retry, or call any provider. Current credential validity remains untested.
- **Probe pipeline:** original activation process1221703 remains present, but the latest recorded admission pause names `source_record_changed_during_read`. Queue owner should reconcile source identity/immutability and existing pause disposition before reporting resumed probes; sidecar performs no unpause, reset or repair.
- **Metrics:** owner should account for lagging P3/frozen bounded snapshots, unresolved P7 binding and the P3 caption-origin gap before calling the fleet currently measured. File freshness and successful bounded collection do not establish a completed15:00–16:00 UTC window.

## Exact receipts

All new receipts are confined to this directory:
- `research_loop/workers/replication_sprint_20260919/operations/FLEET_CUT_1540/OVX4.json` — actual pair/base/scorer/probe identities, source hashes, latest record paths/hashes, probe log tail hash and timestamp.
- `research_loop/workers/replication_sprint_20260919/operations/FLEET_CUT_1540/NODE4.json` — actual P3/P7 identities, newest records and hash-verified INBOX registrations.
- `research_loop/workers/replication_sprint_20260919/operations/FLEET_CUT_1540/LOCAL.json` — actual local parent/collector/queue identities, bounded parent state/proofs, collector file references. Top-level generic HTTPError receipts omit the status code; use the original response logs pinned in EVIDENCE_LINKS for401/auth_error.
- `research_loop/workers/replication_sprint_20260919/operations/FLEET_CUT_1540/EVIDENCE_LINKS.json` — original authentication-log refs/hashes, matching P3/P7 publication refs, CURRENT alias resolution and collector-origin-hour coverage.

Primary source paths:
- `research_loop/workers/post_reboot_pair_parents_20260919/private/learner/turn_000104_1789794006756564934/http_error_response.txt`
- `research_loop/workers/post_reboot_pair_parents_20260919/private/frozen/turn_000134_1789794506916730728/http_error_response.txt`
- `research_loop/workers/post_reboot_pair_parents_20260919/private/learner/DELIVERY_3d350707f1044b66b93ec5ce0dd2743c.json`
- `research_loop/workers/post_reboot_pair_parents_20260919/private/frozen/STATE.json` (only bounded metadata projected; no parent text copied)
- `research_loop/workers/rohin174_parenting_20260917/node4/R195_FLEET/r210_parent3/turns/parent_000000000550/RESULT.json` (matches native INBOX11606)
- `research_loop/workers/post_reboot_c2_p7_20260919/p7/turn_1789831996243795857/NEXT.json` (matches native INBOX15799)
- `research_loop/workers/post_reboot_services_20260919/observer_recovery/runs/1789779728873833849/LATEST.json`
- `research_loop/workers/post_reboot_services_20260919/cuts/20260919T150104Z.json`
- `research_loop/workers/post_recovery_correction_hourly_20260918/public/CURRENT.json`
- Remote ovx4: `/localhome/local-rohing/post_reboot_probe_queue_20260919/MAIN_ACTIVATION_20260919T045438Z.log` (16KiB tail only)

## Bounds and non-actions

One observational pass per remote host; newest96 record trailers per life,4KiB maximum each; only small INBOX records decoded and canonically hash-checked. Remote read accounting: ovx4 498756 bytes; node4 352029 bytes. Largest local metadata file in the local pass: 1670147 bytes (<2MB). Large REQUEST/COMPLETE bodies were not pulled or replayed; their stated canonical hashes were not recomputed. No secrets/process environments, provider calls, signals, native/parent restarts, config changes, new daemons, leases, commits, pushes or scientific runs. Only JSON/MD receipts in this folder were written, via apply_patch. Front page remains untouched for main to integrate.
