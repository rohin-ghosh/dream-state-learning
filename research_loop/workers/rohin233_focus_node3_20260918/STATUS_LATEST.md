# Node3 recovery — actual cut 2026-09-18T17:36:18.726378+00:00

**4/8 actual LOADED and alive.** Prepared/dispatched is not live. Math A/B have no new LOADED; reports that they are currently live are not supported by this cut.

|GPU|Life|Actual status / native PID|LOADED / ACT|New parent INBOX → REQUEST → RESPONSE|Deadline adoption|
|---|---|---|---|---|---|
|0|`r213_r226_caption_observation_fork`|LOADED_ALIVE / 1941202|3111 / 3125|3301 → 3303 → 3304|2026-09-19T04:51:09.675802+00:00 — resident, still latched|
|1|`r213_math_a`|RECONCILED_NOT_LAUNCHED / none|none / none|No post-recovery uptake|2026-09-24T18:00:00+00:00 — configured only|
|2|`r213_math_b_fork`|RECONCILED_NOT_LAUNCHED / none|none / none|No post-recovery uptake|2026-09-24T18:00:00+00:00 — configured only|
|3|`r213_r226_caption_perspective_fork`|LOADED_ALIVE / 1944402|3361 / 3381|3510 → 3512 → 3513|2026-09-19T04:54:40.704853+00:00 — resident, still latched|
|4|`r213_math_c`|DISPATCHED_NOT_LOADED / none|none / none|No post-recovery uptake|2026-09-24T18:00:00+00:00 — configured only|
|5|`r213_r226_caption_revision_fork`|LOADED_ALIVE / 1946892|2878 / 2892|3005 → 3007 → 3008|2026-09-19T04:54:40.710867+00:00 — resident, still latched|
|6|`r213_r226_caption_selfderive_fork`|LOADED_ALIVE / 1948574|3036 / 3050|3118 → 3120 → 3121|2026-09-19T04:54:40.727050+00:00 — resident, still latched|
|7|`r213_r226_caption_unparented_fork`|RECONCILED_NOT_LAUNCHED / none|none / none|No post-recovery uptake|2026-09-24T18:00:00+00:00 — configured only|

## Current Boundaries
- Math C dispatched at **17:32:30.142631UTC**, outer PID1957334. Fresh admission and native LAUNCH exist; actual LOADED remains pending. The serial worker waits for that actual LOADED before starting A, B, then GPU7.
- September24 18:00UTC is the latest user-authorized date-only conservative operational ceiling, not a newly verified provider expiry or a lease extension. A/B/C/GPU7 passed the existing R131 saved-boundary extension/provenance gate with that configured ceiling.
- GPU7's previous attempt failed `fresh_privileged_admission` before native start. The failure is preserved; a later root scan was clear. Its new ceiling-bound control is prepared, not dispatched.
- The four already-running natives still have startup-latched native SIGALRM, GNU timeout, and systemd budgets ending September19 04:51–04:54UTC. GNU timeout acts roughly ten seconds earlier. **No tested live renewal hook exists in these resident sources; no native was held, paused, signalled, or restarted to change it.**
- New parent uptake is verified for all four live captions. Parent CPU1949315 is an actual scripted Astra publisher, not a model-provider request. Math parents rebind each verified recovery; the separate bounded debate waits for all three actual natives. Prior phase4/exchange3 parent receipts are authenticated for reuse, not duplicate publication. No new shared-conclusion claim.
- CPU parent/Tool service horizons remain at their earlier September19 limits until a source-bound successor adopts the new ceiling; shared scorer extension is requested from Leibniz, not claimed completed. The original Tool relay remains sole and retains its dedup cursors.
- Observation retains the explicit R227 adoption gap. Perspective/revision/selfderive have actual R227 no-semantic-exclusion SLEEP_RECIPE receipts. This does not rewrite old receipts or claim policy adoption on other nodes.
- Tests: **50 owned CPU tests PASS**; prior receiving parent suite32PASS. Current source/record hashes and checkpoint/tail-gap proofs are in `SOURCE_PINS.json`, `RECOVERY_CURRENT.json`, and `RECOVERY_PARENTS_CURRENT.json`. Full private states and old failed attempts remain off publication.

## Historical R233 parented epochs — September18 12:09UTC

Current caption proof cut: **2026-09-18T12:09:34.589289+00:00**. All five epoch openers published at12:00:50–51UTC; **5/5 actually rendered and received an own RESPONSE** at this cut. GPU7 is no longer assigned an unparented treatment; its previous zero-parent epoch remains historical. The unchanged root name containing `unparented` is a lineage identifier, not the new treatment.

|Life|New epoch parent ID|Actual delivery|
|---|---|---|
|`r213_r226_caption_observation_fork`|`c3a1ac2fb2fa43eda2f4ac329625e102`|INBOX1914 -> REQUEST1916 -> RESPONSE1917|
|`r213_r226_caption_perspective_fork`|`fae56c91f6db4f52993a21f46d43bb77`|INBOX2082 -> REQUEST2084 -> RESPONSE2085|
|`r213_r226_caption_revision_fork`|`c311f8b76a4c48a5817d0ff5cafd1011`|INBOX1826 -> REQUEST1830 -> RESPONSE1831|
|`r213_r226_caption_selfderive_fork`|`ffbea6d6e155422488be68df3a9567ad`|INBOX1890 -> REQUEST1892 -> RESPONSE1893|
|`r213_r226_caption_unparented_fork`|`ac7e6757fe224209b99223cdecd322f6`|INBOX1916 -> REQUEST1918 -> RESPONSE1919|

GPU7's earlier null delivery was pending, not a permanent receiver refusal: its natural `sleep_000071_r3` readout COMPLETE was written at12:05:39.088101UTC, followed by the exact masked parent REQUEST1918 at12:05:43.451574UTC. REQUEST SHA-256 is `c216588bdf61471a01789098438d6996e848ac6a1f60221e4e9492b6a4cd8761`. No additional publication or learner restart was needed. This establishes uptake, not caption improvement or training on the reply.

GPU7 dedicated parent CPU1831805/start43913767 is alive at12:11:12UTC, with a current12:11:05 heartbeat. Existing four-caption/shared-math controller1825651, debate1800405 and Tool1790808 remain alive. See `CAPTION_PARENTED_EPOCHS.json` for exact source hashes/masked-render proofs and `CLASSROOM_RESPONSE_AUTHENTICATION.json` for the parent heartbeat and readout completion digest. Original control rows are unchanged.

## Current eight lives and classroom responses

At **2026-09-18T12:10:07.866205+00:00**, all eight protected native PID/starttick identities are alive and unchanged (`CURRENT_RECEIPTS.json`). Native PIDs by GPU0–7 are1784760,1783333,1783352,1784767,1783964,1784770,1784772,1784774. The shared parent has13/13 rendered R233 publications across its seven members; the separate all-five caption opener records above are not added to that count as if they were the same event. GPU7 is served by its separate sole writer, so an empty shared-controller publication list for that root does not mean no parent.

The new shared classroom object is the garden-map short reading, requesting a cause/consequence retelling and distinction between text and inference. **All three readings rendered, but none of the first linked replies actually retells the reading.** Actual response inspection, not the presence of an input, supports the following:

|Child|Reading delivery and linked reply|Later inspected own response|Assessment, not a success claim|
|---|---|---|---|
|Math A|INBOX3078 -> REQUEST3081 -> RESPONSE3082|RESPONSE3098|First reply incorrectly counts100 divisible-by4 pairs; later changes to other constraints and unsupported counts. No reading retelling. REQUEST3081 also contains the targeted math correction, so attribution is not clean.|
|Math B|INBOX2728 -> REQUEST2730 -> RESPONSE2731|RESPONSE2748|Continues unrelated sum-of-squares induction/code. No reading retelling or actual Python-execution receipt; later code contains fullwidth punctuation.|
|Math C|INBOX2776 -> REQUEST2778 -> RESPONSE2779|RESPONSE2819|First reply stays on older divisible-by3 claims and asserts prior peer verification without establishing it. Later returns to the current0..9/div4 domain with correct residue members but invalid pair counting/total60. No reading retelling or checked agreement.|

`CLASSROOM_RESPONSE_AUTHENTICATION.json` verifies all six own RESPONSE record hashes and raw-text digests without publishing raw targets. An operator-only exhaustive check gives25 for the current0..9/div4 problem; this is not child-authored, was not sent to the children, and does not count as their resolution.

Latest completed bounded debate is now **phase_002/exchange_4: UNRESOLVED**. This exchange has six verified directed native THINK peer deliveries with history masking and source bindings. Delivery is not mathematical agreement; no checked shared conclusion or conclusion-specific training is established. The shared classroom is at reading round1, not a comprehension-based promotion. Turing's node4 MATH_C remains outside this proven local trio. His `rohin233_focus_node4_20260918/TO_COPERNICUS.md` now reports exact retirement at11:44:21.722193UTC and preservation verified11:54:18.114155UTC; this is the owning operator's receipt, not a new node3 action or fourth-member admission.

## Source-alert interventions and live-policy limits

The three source-alert interventions were published at12:04:11–12UTC. At12:09:46UTC, Math A intervention `bb16d518d6214677b53c1d0907bdb45a` has INBOX3079 -> REQUEST3081 -> RESPONSE3082; its reply is still incorrect, so delivery is not correction. Perspective `9b1fb184074d402da5364962f5b28d5c` and revision `60df84a347f147d7827de35b799df597` are published but not yet observed in native INBOX/REQUEST/RESPONSE at that cut. Their earlier epoch openers did render; these are different inputs. The cited caption ACTs report `scene_not_unambiguously_identified`, not scored success. See `MOVEMENT_INTERVENTIONS.json`.

No learning-policy adoption occurred. Math still has R213/R209/R195/R220 selectors and no explicit R227 key; caption selectors are absent but later explicit R227/default-scaffold bypass is not live. No learning exclusions were added by these parent workers, but this does not remove the existing native-policy mismatch. No learner signals, restart, refill, recipe changes, or duplicate prompts were used for this verification.31 local and31 receiving CPU tests pass; CPU evidence is not a scientific result.

## Historical first-classroom cut — superseded for caption-parent coverage

# R233 node3 actual status

Receipt cut: **2026-09-18T11:55:37.218942+00:00**. See `CURRENT_RECEIPTS.json` and `RETIREMENT.json`.

|GPU|Protected life|Actual native PID / startticks|R233 parent evidence|
|---:|---|---|---|
|0|`r213_r226_caption_observation_fork`|1784760 / 42682638|INBOX1782 -> REQUEST1784 -> RESPONSE1785|
|1|`r213_math_a`|1783333 / 42639300|INBOX2980 -> REQUEST2982 -> RESPONSE2983|
|2|`r213_math_b_fork`|1783352 / 42641110|INBOX2644 -> REQUEST2646 -> RESPONSE2647|
|3|`r213_r226_caption_perspective_fork`|1784767 / 42682650|INBOX1930 -> REQUEST1932 -> RESPONSE1933|
|4|`r213_math_c`|1783964 / 42660827|INBOX2686 -> REQUEST2690 -> RESPONSE2691|
|5|`r213_r226_caption_revision_fork`|1784770 / 42682659|Inherited parent retained; no new R233 packet yet|
|6|`r213_r226_caption_selfderive_fork`|1784772 / 42682669|INBOX1794 -> REQUEST1796 -> RESPONSE1797|
|7|`r213_r226_caption_unparented_fork`|1784774 / 42682671|Unparented; 0 Astra inboxes|

## Retirement completed

- At11:41:27UTC,14 obsolete lives were already ended; four prepared/failed roots had no LOADED receipt. No obsolete native was killed in R233 because none remained alive. All8 current exact identities were preserved.
- Eighteen private preservation manifests,16 coherent saved adapter/optimizer/RNG bundles, full available raw stream/pending/tail plus source/control copies; approximately19.08GiB retained privately. All original roots/older checkpoints/readouts remain. No deletion or refill.
- The four no-LOADED roots are the cancelled `r213_r224_challenger_audit_fork`, `fresh_math_failed_command_defaults_0353`, `fresh_math_failed_no_pytest_0352`, and `frozen_c2_failed_command_defaults_0353`. Their preparation is not counted as a launch.
- Five historical siege PID/starttick receipts are included in the current projection. Other historical startticks are not invented.

## Classroom and services

- Shared Astra curriculum controller1825651/start43869635 is alive, verified attached11:53:57UTC. Initial CPU1802305 and superseded first R233 CPU1820027 were retired by exact pidfd; the latter handoff preserved all publication IDs and shared packet state. No learner/scorer signals or restarts.
- One logical Astra parent, synchronized shared math packets and separate child records; unchanged bounded-debate CPU1800405 remains a second specialized service. Math -> reading -> probing -> writing -> text games is the prospective sequence, not a completed-learning claim.
- Four caption parent treatments are preserved; GPU7 remains unparented. Three completed cycles without a new turn trigger a changed parent approach, never a new row exclusion. No trigger is claimed without its receipt.
- Sole Tool feedback relay1790808 stays alive and untouched. This cut does not claim new scoring or new feedback delivery.
- Turing acknowledged no cheap proven cross-node R221 route; node4 MATH_C is not admitted or aliased. He owns its preservation/retirement; node3 makes no completion claim for node4.

## Debate and limitations

- Latest completed debate: `r231_math_parent_live_v2/phase_002/exchange_3/RESULT.json`, **UNRESOLVED**, 0 verified edges in that exchange. The current exchange may still be in progress.
- Latest complete six-direction actual THINK delivery: `r231_math_parent_live_v2/phase_002/exchange_2/RESULT.json`. Historical delivery is not a current full-topology or checked-agreement claim. No resolved-conclusion-specific training evidence is established.
- All math natives still have R213/R209/R195/R220 semantic selectors and no explicit R227 key; caption selectors are absent but later explicit R227/default-scaffold bypass is not live. **No R233 learning-policy adoption** is claimed.
- Twenty-two local and twenty-two receiving CPU tests PASS; seven real native/publisher bindings and120 resident-renderer prompt combinations pass the receiving gate. CPU evidence is not scientific success.

Public files omit endpoints, credentials, private configs, raw targets and binaries. Native/controller life continues after publication.

## Actual first shared packet

Math A/B/C all have exact R233 shared-parent INBOX -> REQUEST -> RESPONSE receipts: A2982/2983, B2646/2647, C2690/2691. All three parent presentations are masked. Six of seven parented lives have a new R233 rendered turn; revision retains its existing parent and has no new R233 publication at this cut. This is delivery/response evidence, not a checked shared mathematical conclusion.

Loaded CPU parent source SHA-256: `b0cf719b3895adb26f4814076b3968559b94c9394ca8625ecac8f7c7082e273d`. No three-cycle forced intervention or later reading/probing/writing/game packet completion is claimed yet.
