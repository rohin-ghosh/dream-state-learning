# R158 final closure — September 17, 2026

## Actual termination and custody release

Both phase2 services stopped **WALL_LIMIT at05:02:39UTC**. Supervisor FINISHED
at05:02:39.537UTC records WORKERS_EXITED, exit codes[0,0]. At05:02:51.286UTC,
the observer verified matching terminal/state receipts, no pending fields,
all three service/supervisor PIDs gone and all22 existing custody/service/
executor locks available nonblocking. Locks were immediately released without
changing their bytes. This is actual closure evidence, not inference from wall.
It is a custody-release observation, not an unperformed GPU-memory census.

ObserverV2 ended normally at05:02:51.289UTC after51 polls. Final independent
read-only check **05:03:50.777UTC** confirms supervisor4042560, workers4048159/
4048160, failed observer4134329 and repaired observer159584 all absent.
Local collector3332017 also exited after downloading closure receipts.
Original child0/4 PID/starttick/command identities and runtime source pins
still match activation. Retired5 and Main's separate5/6/7 work were untouched.
No further service, retry, renewal, fixture or console message is scheduled.

## Publication, rendering, child request, execution

- **Kernel0:** exact Astra nudge remains published once. No registration or
  rendered inclusion was observed through closure; it continued ordinary sleep
  UPDATEs. Calls0; final scanner cursor3613. No child kernel execution.
- **Kernel4:** nudge registered INBOX3474 and actually rendered in TRAIN
  REQUEST3475, started04:53:21.666UTC. Genuine child RESPONSE3476/COMMITTED3477
  produced request`86ce6cf07fd79949931b2ae4d892d0ddbfc2d4c550895cd37934b6976b4c2118`.
  Its first closed fence was C++ (`int idx = threadIdx.x + blockIdx.x * blockDim.x;`).
  Actual result: **REQUEST_REJECTED / invalid_kernel_AST / launch_attempted=false**.
  The Tool rejection was published and its exact attributed text appeared in
  REQUEST3479, started04:56:23.648UTC. Subsequent responses3480 and3484 were
  incomplete/truncated; both have INCOMPLETE_GENERATION_NO_EXECUTION receipts.
  Calls1 (a handled child request, not GPU execution); final cursor3487.
- **No genuine child GPU kernel executed in this bounded renewal.** The concrete
  blocker is invalid child C++ followed by truncated generations, not a missing
  live sidecar or unnoticed nudge rendering. No translation, replay, policy
  broadening, fixed solution body, fixture result or expired-gate bypass occurred.

## Final counter deltas, not cumulative totals mistaken for new I/O

The unchanged service charges bounded read reservations; these are not measured
disk traffic. Phase2 inherits phase1, which inherits R155; subtract only once.

| Life | Inherited read_bytes | Phase1 delta | Phase2 delta | Total new R158 reservation |
|---|---:|---:|---:|---:|
|kernel0|2,887,123,992,576|57,378,078,720|57,378,078,720|114,756,157,440 (106.875GiB)|
|kernel4|69,625,446,400|57,545,850,880|74,959,314,002|132,505,164,882 (~123.405GiB)|

Kernel0's final3,001,880,150,016 bytes are mostly inherited, not3TB new physical
reads. Kernel4 additionally incurred per-request admission/runtime reservations.
Final counters and empty pending fields are in `FINAL_COUNTER_DELTAS.json`.
At05:00:34.898UTC, separate `/proc/io` showed worker0/4 rchar1,781,897,576/
6,981,989,443 bytes and read_bytes0 each; supervisor rchar10,270,805,387/read_bytes0.
These are process-lifetime observations before shutdown, not final node-wide I/O
measurements or proof that polling costs nothing.

## Preserved receipts and repair

Old observer's04:26:53 atomic STATE-read race, unchanged old source and stale
snapshots remain preserved. Observer-only repair passed18 CPU tests; bounded
retries apply only to mutable STATE, not immutable evidence or service guards.

- `final_closure_receipts/`: original campaign/worker terminals and final states.
- `final_observer_receipts/`: observer terminal, final status, truncation refusals.
- `first_child_attempt/`: original source request, origin/admission/bridge/result.
- `FINAL_IDENTITY_OBSERVED.json`: final actual process/child/source verification.
- `observer_v2_collection/`: dated snapshots; FINISHED.txt records verified closure.

| Artifact | SHA256 |
|---|---|
|`FINAL_CLOSURE_RECEIPTS.tar.gz`|`9f195a36f408bc0d1f13dbc21e51f644b9a4364f34dd1d479910b6a149605107`|
|`FINAL_OBSERVER_AND_REFUSALS.tar.gz`|`ab777d2166b7d413f2456bd9f4de88334562cc879f571fe5f3b5294c1b014e53`|
|`FINAL_COUNTER_DELTAS.json`|`976f2388e440e649e1d66cd031a193acd3ee207586f922b7fe607b8771d3c719`|
|`final_closure_receipts/FINISHED.json`|`66e1a7906d88587e9a5f18fb3b58843f80b674218db6926b62d4bbffff4cce16`|
|`final_closure_receipts/astra_nudge_observation_v2/STATUS.json`|`386377be631fa80eecc4277c4a365f07da79e51bb7f45329915ccfec3c5fe1ea`|
