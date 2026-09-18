# Actual frozen readmission — September17 06:42 UTC / September16 23:42 PDT

New GO verified and dispatched exactly once. Original frozen/unparented GO, once-marker and refusal hashes were verified unchanged; both initial keys were unreserved and attempt-free before launch. No retry of the old GOs occurred. Unparented has not been redispatched.

Frozen actual privileged admission passed at06:41:44.196UTC, physical1, zero memory/utilization, no blockers. The full actual report is persisted at receiving `control/frozen_readmission_generation2/operator1/ACTUAL_ADMISSION.private.json`, SHA`6ef3b9e17dfac2d147f1797eb4cefa39e1bd33c284cfe6ce417fda5ccd28924b`. This is the actual new dispatcher scan, not a separate precheck or historical reconstruction. Its unchanged report was captured with a tested fail-closed profiling wrapper; no frozen source/config pins or scanner logic changed. Local and receiving stdlib tests:3 PASS each; receiving CPU gate SHA`9ddc05f90b7b6998d02e0a1ef1b28f7049fa5d1ce050be7379675b09ddfd937a`. Exact runtime3 CLI validation passed. Initiator identity was gone after5s before admission.

Wrapper PID1704179/start85573721; native timeout PID1704195/start85574399; boot8ff7b0dc-fbdf-4945-9044-3dffe94b5407, UID2524. Frozen reservation created06:41:44.838UTC, SHA`4ccc6218a7001e272bead405b7e33b2310838a06f5ce7ced32df77b043825ee2`,56 charged calls. At06:42:07UTC ledger2 reserved/1 complete/0 failed/1 unresolved,112/672 charged,560 remaining. Learning remains complete56; frozen is not yet claimed complete. Initial3 controls remain incomplete. No held contents or scores read or disclosed.

## Unparented proposal — new GO required, no launch

Exact new target:
`/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1/control/unparented_readmission_generation2/unparented_learning.EXECUTION.proposed.json`

SHA`ab43c8725d027826b15e3a1db8b595ef70ea4fd81e032167f352184fabfa80a0`.

Same original config bytes/runtime3, physical0, new path requiring a new exact Main GO. Source/candidate/plan CPU validation passed. Receiving `control/unparented_readmission_generation2/PROPOSAL.json` SHA`74478547593a145eb1ebd94c1533d9ae047c7f068eec50587ef2594ccfd96900`. Original once SHA`eb118c66ce09fe0eedbf6d9f980a2c8c029e5b11f27e128b6a2f571f3b620fac`; original refusal SHA`bd1f76e9d27ed73296518c1b62a0daa2509117bb77f328e7de6ab30021c1737a` preserved. No reservation/sample at proposal time. Proposed serial release of the current evaluator, fresh full unchanged admission with actual-report persistence, new once-marker and new GO. Do not waive blockers if physical0 looks vacant.

All original672-call/12-slot caps,08:00UTC hard/read ceiling, and strict06:59:45UTC latest dispatch with3615s full window remain. No node5 authority or old campaign changes.

## Metadata update —06:42:48UTC

Actual GPU evaluator PID1704196 on physical1,15250MiB. Six output-artifact receipts and seven per-item reservation filenames now exist; contents remain sealed. No dispatcher error/terminal completion yet. Ledger remains112/672 charged,1 completed/1 unresolved. Local and receiving unparented PROPOSAL bytes match SHA74478547593a145eb1ebd94c1533d9ae047c7f068eec50587ef2594ccfd96900. COORDINATION's earlier wrapper-gate manual06:43 label was premature; actual tests preceded06:41:38 spawn, and receiving CPU receipt time is authoritative. Original artifacts remain unchanged.
