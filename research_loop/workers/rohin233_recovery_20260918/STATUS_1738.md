# Kept-fleet recovery — September 18, 2026, 17:36 UTC evidence cut

This is an interim operational report, not completion. A live PID, a LOADED record,
a delivered parent turn, and successful learning are distinct facts. Dates below
are UTC. Reported lease dates are not independently verified provider timestamps.

## Per-life status

| Life | Node / GPU | Actual state | Actual parenting evidence after recovery | Resident deadline, not a staged plan |
| --- | --- | --- | --- | --- |
| C2 | node5 | Alive, native3624513 | Parented previously; current turn not re-audited in this cut | Sep19 00:00; renewal unresolved |
| C0 | node2 / 4 | LOADED2871,17:21:10, native745118 | New recall publication ba7926e14cb34bb1a0cfbd6bc6d49598; REQUEST2953 17:32:59 -> RESPONSE2954 17:33:20 | Sep18 22:55:15; parent renewed to Sep20 17:59 |
| Astra7 | node2 / 1 | LOADED3128,17:26:46, native762967 | P7 bridge rebinding pending; historical replies are not new receipts | Sep18 22:59:36; renewal unresolved |
| Additional caption arm | node2 / 2 | Native787115 starting; no LOADED yet | Parent continuation pending LOAD | New launch bound Sep20 18:00 |
| P3 | node4 / 3 | Native237705 continuously alive | xhigh turns293,296,299 rendered; REQUEST5062 17:21:59 -> ACT5103 17:30:26 | Sep18 18:00 remains; lease-parent successor armed, not native renewal |
| P7 | node4 / 7 | Native1100592 alive | Overseer2805259; actual THINK6413/ACT6420 ignored requested leaf artifact | Sep18 18:00 remains; renewal unresolved |
| Curriculum learner r231 | ovx4 / 0 | LOADED1875,17:02:26, native399101; resumed training | Publication7c6e5a5135f6479baa3afec5d5845115 renderedREQUEST1959; parent renewed | Sep18 23:30 remains; obsolete18:00 cutoff CANCELLED |
| Frozen sibling r232 | ovx4 / 1 | LOADED1595,17:33:46, native412570, optimizer0 | New publication f8b89ebbae8b4f799a552cb90e8e3f67; rendering pending; parent renewed | Sep18 18:00 remains; urgent renewal unresolved |
| Frozen base caption player | ovx4 / 4 | LOADED17:03:04, native401005; six new ACTs through17:27 | Parent bridge restored; exact new parent turn not audited here; actual feedback rendered | Sep18 17:59:30 remains |
| Caption observation | node3 / 0 | LOADED3111, native1941202 | Parent31df98f2bc40412a9eb5ce0545394ce2 -> REQUEST3303 -> RESPONSE3304 | Sep19 04:51:09 remains |
| Math A | node3 / 1 | Reconciled, NOT newly LOADED | No new delivered turn while down | Longer-horizon dispatch pending |
| Math B | node3 / 2 | Reconciled, NOT newly LOADED | No new delivered turn while down | Longer-horizon dispatch pending |
| Caption perspective | node3 / 3 | LOADED3361, native1944402 | Parente1b4efbda45b44cb8929c223bd4daf1f -> REQUEST3512 -> RESPONSE3513 | Sep19 04:54:40 remains |
| Math C | node3 / 4 | Dispatched, NOT newly LOADED | No new delivered turn while starting | New lease-bound dispatch; verify actual LOAD before claiming adoption |
| Caption revision | node3 / 5 | LOADED2878, native1946892 | Parent42c9ed33293f4f528779a1379577966b -> REQUEST3007 -> RESPONSE3008 | Sep19 04:54:40 remains |
| Caption selfderive | node3 / 6 | LOADED3036, native1948574 | Parentae12efdf10ce4b6b82f2d368a5579273 -> REQUEST3120 -> RESPONSE3121 | Sep19 04:54:40 remains |
| Caption historical-unparented | node3 / 7 | Reconciled, NOT newly LOADED | Current R233 arm is to be parented, not an unparented control | Longer-horizon dispatch pending |

Node3 MathA/B live reports are not corroborated by actual new-incarnation LOADED
receipts at this cut; the table deliberately does not promote stale records to live status.

## Timers: changed versus unresolved

- CANCELLED only obsolete learner cutoff418521/start9776388 at17:30:08; exact
  daemon exit and learner399101 survival verified. Native signals: none. Original
  ARMED receipt retained beside CANCELLED. No PAUSED marker or SIGSTOP.
- Learner and sibling CPU parents renewed to Sep30 18:00; C0 CPU parent renewed
  to Sep20 17:59. P3 CPU successor2973135 is armed through Sep25 18:00, waiting
  for its predecessor's natural exit without pausing the child or duplicating writers.
- P3 live systemd RuntimeMax update was rejected as unsupported. No property
  change is claimed. Its GNU timeout and resident Python alarm/wall also remain.
- Shared scorers400982/400990, base scorer400997/player401005, P3 scorer254441
  and feedback relay are alive, but their17:59:30 deadlines remain at this cut.
- Native walls are startup-latched in the resident plan/stream and SIGALRM,
  with additional GNU timeout/systemd limits. File edits alone do not renew them.
  Existing supported wall extension is checkpoint-resume-only. No undocumented
  debugger injection or false hot-adoption claim is used. This remains an urgent
  unresolved incompatibility with a strictly zero-reload-gap renewal.
- Conservative target bounds from the reported existing leases: ovx4 Sep30
  18:00; node3 Sep24 18:00; node2/node5 Sep20 18:00; node4 Sep25 18:00.

## Feedback and measurement

- P3 new feedback af6c5a3f50ec4e8180fdb2ec682db287 actually rendered in REQUEST5062.
  It says no score because scene identity was ambiguous: zero scoring calls,
  not a fabricated rank. Feedback delivery is repaired; caption competence is not.
- P3 recovered parent293 -> REQUEST4965 -> ACT4989; parent296 -> REQUEST4998
  -> ACT5052; parent299 -> REQUEST5062 -> ACT5103. Parent301 also maps to
  ACT5103 and must not be counted as an additional independent ACT.
- Base since recovery through17:27: six ACTs,2261 generated tokens,43 parsed,
  42 scored,26 accepted,4 novel,1 cached. These are raw scorer results, not an
  independently certified count of literal jokes or distinct ideas.
- Every-sleep enrollment resumed; fresh learner sleep24 captured. A new GPU
  age-probe result is not yet verified; enrollment is not evaluation.
- P7 recommendation is in COORDINATION: preserved retirement preferred to
  endless reminders, or one bounded genuine Astra7 exchange if Rohin chooses.
  No retirement action taken; language alone is not the failure criterion.

## Evidence paths

- `PAIR_CUTOFF_CANCELLED.json`, `P3_REQUEST_ACT.json`, `P3_LEASE_PARENT_ARMED.json` in this directory.
- `../rohin231_curriculum_birth_20260918/recovery_20260918T1646Z/CURRENT.json`.
- `../rohin233_focus_node2_20260918/recovery_20260918T1646Z/LIVE_1735.public.json` and `C0_NEW_PARENT_0021.public.json`.
- `../rohin233_focus_node3_20260918/RECOVERY_CURRENT.json` and `RECOVERY_PARENTS_CURRENT.json`.
- `../rohin233_recovery_node4_20260918/DEADLINES_1733.json` and `ORDINARY_FOLLOWUP.json`.
- `../rohin233_ovx4_recovery_20260918/TABLE_CUT_1735.json` and `P3_FUTURE_DELIVERY_1725.json`.

Recovery remains in progress. Historical evidence, interrupted tails and
checkpoint RNG are preserved; uninterrupted resident RNG continuity is not claimed.
