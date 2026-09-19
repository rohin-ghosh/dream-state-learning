# Main: exact live route and immutable continuation closure checklist

Read-only pre-closure cut: **2026-09-19 02:36:19.482254UTC**.
Existing LISTENING receipt and process reverified02:39:35.685892UTC.
**Admission is OPEN. This is not a drained-endpoint or restorable closure claim.**
No socket request, mutation, restart, source application or signal was performed.

## Exact scorer authority

- Host wrapper: `gpu/ovx4_ssh.sh` (not the native-node `ovx2_ssh.sh`).
- Original scorer **499900**, start ticks **10094999**, UID1352, boot
  `7c130f24-3105-4909-abfb-b669929e0b96`. It is `kind=shared`, **physical GPU4**;
  `shared2` is a service/group label, not a physical-GPU2 instruction.
- Python entrypoint:
  `research_loop.workers.rohin233_ovx4_recovery_20260918.judge_service`.
- Original deployment root:
  `/localhome/local-rohing/orch_r233_judge15625_20260918/judge15625-shared2-v1`.
- `CONFIG.private.json` SHA256:
  `a7f14a4dae4595f1d8056665cb450d78387387b81694c7c3e52286641d4d06c1`.
- `SOURCE_MANIFEST.json` SHA256:
  `499831e0fb0330cf916c814ff2a3b7820c9678a1fa7a4839bfd7b1d0455e4797`;
  **all129 named source files freshly verified**, not inferred from local code.
- Deployed `judge_service.py` SHA256:
  `c5ea88e80e520fe35dc3df9c5b442060bd86ced4453e779c5cfe585cc552ef0c`.
  Copy this deployed source closure into the new namespace; local judge main is
  different and must not silently substitute for it.
- Original `LOADED.json` remains pinned to
  `7326a438c9ab9613a2a0e8d6e8f94f043b3cbd3499d293377c802cbd3d383848`.
- Actual readiness artifact is `sockets/LISTENING.json`, SHA256
  `350ff02bea76a2b8c776b99d76b19639fff68ba4daecb609c011c4aef27c905f`.
  It names499900, the five sessions and `serialized_GPU_calls=true`.
  A mistaken read of nonexistent `sockets/READY.json` is preserved as a
  FileNotFoundError in `SCORER_LISTENING_AUTHORITY.json`; no connection was made.

**Different deadlines must remain different:** the original scorer and both
scorer-host bridges retain1790791170 = **September30 17:59:30UTC**. The node3
CPU/native-source transport remains1790272760 = **September24 17:59:20UTC**.
Do not extend the latter to the scorer lease or shorten/reconfigure the scorer
by copying the source-transport deadline into its config.

## Current route, with no inferred queue count

Node3 slots0/3/5/6/7 use `/tmp/r226-caption-{slot}.sock`, symlinks to
`/tmp/n3cap-17897812456785859204349e8-{slot}.sock`. Existing downstream SSH forwards
reach VM `/tmp/n3cap-17897812456785859204349e8/proxy/{slot}.sock`.

The CPU proxy uses VM `/tmp/n3cap-17897812456785859204349e8/shared.sock`, upstream
SSH-forwarded through this existing scorer-host chain:

| Endpoint | Owner process / next target | Observed socket-file inode |
|---|---|---|
| `/localhome/local-rohing/orch_r226_shared_caption_20260918/attempt2/native.sock` | Bridge448173/start9898014 -> lease-renewal socket | 28185681 |
| `/localhome/local-rohing/orch_r233_lease_renewal_20260918/attempt2/shared2/sockets/native.sock` | Bridge502015/start10101591 -> original scorer socket | 31721356 |
| `/localhome/local-rohing/orch_r233_judge15625_20260918/judge15625-shared2-v1/sockets/native.sock` | Original serialized scorer499900 | 31851457 |

These are observed0600, UID1352 socket files, device66307, plus pinned route and
LISTENING metadata. They are **not kernel backlog or active-connection counts**.
Original controller425470 and its recorded CPU children425573/425574/425638
remain live; the latter are timeout-wrapper identities, not asserted inner
Python/SSH PIDs. Parent330973, error reporter459421 and supervisor399392 were
reverified in the real VM namespace, boot80d71f45-6f0c-4479-b0e5-77a9611c793e.

## Fresh saved-state / durable queue evidence

Two read-only cuts two seconds apart have identical saved-state hashes. Every
seen ID equals an existing complete attempt directory with REQUEST, BEFORE,
RESULT and AFTER bytes retained; no incomplete directory was observed.

| Fork | Phase | Seen = retained attempt count | Original epoch JSON files |
|---|---|---|---|
| observation | COMPLETE | 128 | 83 |
| perspective | COMPLETE | 131 | 71 |
| revision | COMPLETE | 124 | 77 |
| selfderive | COMPLETE | 102 | 52 |
| historical unparented, R233 parented | COMPLETE | 120 | 65 |

These605 are retained session attempts, not605 new or successful caption
judgments. Exact seen lists, source bindings, full state/game/policy hashes,
attempt-file hashes and complete original epoch-file manifests are in the cut.
The VM cut retains78 completed TRANSPORT logs and their original bytes' hashes.

**Drain limitation:** the deployed VM proxy logs TRANSPORT only after an outcome;
it has no durable request-admission intent for calls still in flight. Existing
bridges have TARGET routing files, not a transactional drain/queue API. The
original scorer has LISTENING plus per-session state, not a drain acknowledgement.
Consequently neither stable COMPLETE snapshots nor the78 completed logs prove
that no request is waiting in an SSH/Unix backlog or an unlogged proxy handler.
No lossless drain can be certified from this audit alone. Do not stop499900 on
the strength of these snapshots, a sleep interval, or an absence in `ps`.

## Minimal deployment route Main can own

1. Stage a new hash-pinned source namespace containing the **deployed129-file
   closure**, the sealed projected-wire package, and only the explicit receiver /
   preserved-epoch continuation edits. Do not overwrite the old snapshot. Bind
   unchanged weights, panels, parser/session modules, allocation and physical4.
2. Stage a CPU-only no-judgment admission gate and its authenticated Tool failure
   publication path. Main owns the later activation. Fence **all five** stable
   native ingress routes against new calls to the old proxy, preserving exact
   before/after alias identities and a closure timestamp. Children, parent
   publishers and old result/Tool relays continue running. Do not signal them.
3. Drain the old accepted path while leaving499900 alive. Reconcile each known
   VM dispatch with its original scorer attempt/result and native ACT/Tool
   receipt. An approved owner-level observation must establish that the old
   accepted handlers/forwarded connections and listener backlogs are empty after
   the ingress fence; existing file metadata cannot provide that observation.
   Keep every unknown as UNKNOWN_NO_REPLAY. If empty in-flight/queue state cannot
   be established, retain the old scorer and explicit no-judgment route rather
   than asserting `inflight=0` or performing a synthetic scoring/barrier call.
4. Only after that fence/drain proof, preserve the immutable closure described
   below and coordinate sole-writer shutdown with Averroes. Do not let the
   supervisor relaunch an obsolete controller/entrypoint during handoff. The old
   transport singleton is `locks/TRANSPORT.lock`, inherited by CPU children;
   acquire the new owner only after the old drained CPU family releases it.
5. Main continues the **original** scorer on physical4, with original session
   output/mirror paths, full saved game/policy/seen state and existing epoch
   ledgers. Reattach original BINDING/ACTIVE with `reattach_existing_epoch`;
   do not call old `attach_epoch` with a new handoff hash. Wrap the restored Hub
   with `ProjectedHub` and use original `serve`. No second model/scorer writer
   overlaps. Keep admission in explicit no-judgment mode until it is ready.
6. Minimal route option avoiding old immutable source/TARGET edits: use fresh
   private scorer/CPU socket names and a new authenticated VM forward to the
   continued scorer's socket; point only the new CPU projected proxy at it.
   After gates pass, Main switches the five stable native aliases from the
   no-judgment gate to the new private forwards. Original route/socket artifacts
   and old source remain retained. No native socket argument/source changes.
7. Open future natural admission only; preserve original frontier, no historical
   retry or prepared-receipt backfill. Verify actual source -> scorer result ->
   native ACT -> Tool INBOX -> masked REQUEST separately from a scored caption
   or learned uptake. The existing no-judgment path remains available on failure.

Step3 is a real prerequisite, not another external permission request: Main is
the endpoint owner. The original application simply lacks a queue/drain API.
Do not bypass tool guards to manufacture a claim of empty kernel queues.

## Immutable closure checklist (to capture AFTER fencing/draining)

- OWNER_AUTHORITY: this exact scope, accepted source diff and dependency
  manifests; old/new transport epoch; same original judge epochs and weights.
- IDENTITY_ROUTE: real host boot/PID/start/command hashes; full original/new
  configs; alias and socket identities; original bridge TARGET/config bytes;
  actual verified absence of a second scorer writer and closed-admission proof.
- QUEUE: complete old ingress/dispatch inventory and timestamps; approved
  zero-in-flight/backlog evidence; every request disposition and original bytes;
  preserve completed replies, incomplete/unknown evidence and future-expired
  prepared entries, never just counts. Retain original no-judgment/Tool
  publication ledgers; no delivery acknowledgement is treated as permission to
  recompute a score.
- STATE: **copy full raw saved session bytes**, not just this audit's hashes,
  into an immutable owner cut. Require COMPLETE, same exact scene/source/mirror
  binding, game/policy snapshot and seen set. Preserve all attempt artifacts,
  including raw REQUEST/RESULT and BEFORE/AFTER. Record files atomically while
  the sole writer is quiescent, with full file-set/hash manifests.
- EPOCH: copy/retain all original BINDING, ACTIVE, admissions, completions and ACT
  receipts byte-for-byte; original shadow end, counters and dedup entries intact.
  Preserve projected receipt/claim/complete custody files on later continuations.
- FREEZE: original129-file source closure, unchanged parser/format/benchmark
  modules, weights/panels/configs and both distinct deadline values. The new
  collector/receiver must be bound to the sealed package and strict-owner
  custody/confinement assumption before it can authorize a callback.
- VERIFY: compare actual preserved artifacts against the immutable manifest;
  then pass those proven before/after values to `continuation.gate`. The pure
  gate validates equality, not the truth of caller-supplied `inflight=0`.

Current evidence is read-only **pre-closure metadata**, not copied full restorable
state, closed admission, deployment approval, or proof that future native calls
will score. Existing files can continue changing while children run.

## Evidence and unchanged sealed patch

Immutable audit: `INTEGRATION_CUT_1789785379507492424.json`, SHA256
`639a423c18551e44c5feba769693a116aadf666104f7493d0e61503a5189be08`.
Readiness authority: `SCORER_LISTENING_AUTHORITY.json`.
The129-source-file hashes and all original five epoch digests are included in
the cut; no sealed benchmark score/key is included in this handoff.

`projected_wire/MANIFEST.json` remains
`21ae68138181485352efc2d964d46d5096e2cde9d3c6659a96a8a79af2c1f952`;
69 CPU tests /26 new tests remain the sealed result. No implementation/service
file changed while collecting this integration proof. The new read-only audit
helper is outside the sealed runtime package.
