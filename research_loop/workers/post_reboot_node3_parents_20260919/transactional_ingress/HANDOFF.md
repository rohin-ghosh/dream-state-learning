# Offline transactional ingress / original-scorer continuation

Non-material transport repair candidate. **Not deployed. No live requests,
signals, alias changes, source edits, scorer/model loads, or service changes were
performed in this task.** The earlier sealed `projected_wire` package is unchanged.
All additions are in this directory. This is a runnable implementation, not a
claim that the legacy route is drained.

## Executables

Run from the new, owner-pinned source closure; use the original scorer venv for
the scorer, and CPU Python for the relay. The following are **handoff commands,
not commands executed against production here**:

```sh
MODULE=research_loop.workers.post_reboot_node3_parents_20260919.transactional_ingress
python3 -B -m "$MODULE.relay" serve --config "$OWNER_RELAY_CONFIG" --sha256 "$RELAY_CONFIG_SHA256"
python3 -B -m "$MODULE.relay" admin --socket "$RELAY_ROOT/admin.sock" --operation close
python3 -B -m "$MODULE.relay" admin --socket "$RELAY_ROOT/admin.sock" --operation status
python3 -B -m "$MODULE.relay" admin --socket "$RELAY_ROOT/admin.sock" --operation open --expected-fence "$FENCE_SEQUENCE" --readiness-sha256 "$READINESS_SHA256"
python3 -B -m "$MODULE.candidate" --owner-plan "$OWNER_PLAN" --sha256 "$OWNER_PLAN_SHA256"
```

The first is a **single foreground CPU supervisor command**, never a nohup
child. Every start/restart is CLOSED. The last is preflight only: no model load.
Only the endpoint owner, after retiring the old writer and validating all gates,
may add `--serve-after-owner-retirement` to continue the sole scorer. Do not invoke
that flag now. No launch command in this package switches aliases or stops an
old process. Services owner Averroes must adopt the eventual command and inhibit
old respawn; no acknowledgment or registration is claimed by this file.

### Relay config, custody and socket layout

An externally SHA-pinned 0600 config in a strict 0700 owner directory contains:

- `root`: fresh private listener runtime directory; `journal_root`: the stable
  0700 owner journal directory retained across listener runtime changes (defaults
  to `root/ledger`). Precreate both directories.
- `transport_epoch`: new SHA256 identity, not a new judge epoch.
- `deadline_unix` and `original_transport_deadline_unix`: both **1790272760**
  (September 24, 2026 17:59:20 UTC), not the scorer deadline.
- `upstream`: the new authenticated forward to the sole continued scorer.
- `routes`: exactly five rows. Each row has `slot`, `stable_alias`,
  `parent_policy: R233_PARENTED`, a validated full `binding`, and `node`/`scorer`
  collect/install parameters used by the existing sealed `projected_wire.relay`.
  `node` has `source`, `binding_path`, `binding_sha256`; `scorer` has those plus
  `store`. These are operator SSH/custody parameters, never child-provided authority.

| Slot | Stable alias | Session suffix | Policy |
|---|---|---|---|
| 0 | `/tmp/r226-caption-0.sock` | observation_fork | R233_PARENTED |
| 3 | `/tmp/r226-caption-3.sock` | perspective_fork | R233_PARENTED |
| 5 | `/tmp/r226-caption-5.sock` | revision_fork | R233_PARENTED |
| 6 | `/tmp/r226-caption-6.sock` | selfderive_fork | R233_PARENTED |
| 7 | `/tmp/r226-caption-7.sock` | unparented_fork | **R233_PARENTED despite historical name** |

The session prefix is `r213_r226_caption_`. The relay binds new
`root/{0,3,5,6,7}.sock` and `root/admin.sock`. It does not touch the aliases.
Existing socket artifacts are not unlinked on restart: retain the old runtime
socket directory, use fresh listener paths and the **same `journal_root`** for
the same relay epoch (or retain/reconcile it in the owner handoff). Never
initialize an empty ledger to evade unknowns. The same stable journal flock
prevents two listener namespaces from running this relay concurrently.

`readiness-<digest>.json` is installed in the ledger by the authenticated owner,
not supplied inline by a child. Its canonical digest must match the command;
fields are `transport_epoch`, `deadline_unix`, `projected_receiver_ready: true`,
`sole_scorer_proved: true`, and a fresh `expires_unix`. Administrative calls also
require the Unix peer UID to be the expected owner. A file containing hashes or
booleans is **not** independent evidence: Main installs it only after actual
receiver/sole-writer proof. Same-UID unrestricted child execution is outside the
accepted custody contract; 0700/0600 alone cannot isolate it.

## Transactional guarantees and limits

`ledger.py` uses a singleton flock and immutable, fsynced, hash-chained events.
The dispatch-intent commit precedes any upstream connect/send. Completion
persists the **actual response** before any downstream reply. Connection events
cover accept, incomplete frames, upstream socket inode/lifetime, and downstream
FD closure after stream wrappers close. WRITE_RETURNED is not a Tool receipt or
uptake. A returned scorer error can complete a transport while yielding no
judgment; no score/success is fabricated.

Close/open and dispatch reservation share one lock. A preparation concurrent
with close cannot dispatch afterwards. Previously reserved dispatches remain
visible until completion or UNKNOWN; close does not cancel them. All fenced,
expired, failed and quarantined requests get the existing no-judgment protocol
(`ok=false`, empty feedback, `next_stage=ACT`, original origin). Native frame and
feedback bounds remain 262144 bytes; the projection/transfer bound stays 64MiB.
Original 115-second read / 110-second forward timeouts are retained, clipped to
the original source deadline. No timer is interpreted as a GPU timeout.

Crash after intent, including the before-send crash window, becomes UNKNOWN.
Crash before intent becomes explicit never-dispatched. Neither automatically
replays. Duplicate requests can retrieve a previously retained exact response
without re-scoring; changed metrics for the same origin are rejected. Completed
and unknown histories remain in the journal across restart.

`status.drained` means **this fenced relay's** pre-fence sockets, admitted work,
dispatches and unresolved unknowns are finished. It explicitly reports
`kernel_backlog_count: null` and `legacy_drain_proved: false`. New queued sockets
are not retroactively inventoried as admitted work; while closed they cannot
reserve dispatch. Calls admitted after a later open still undergo the original
source/frontier/deadline validation. This is not a statement about old SSH or
kernel queues.

Unknowns require an owner-installed `resolution-<digest>.json` and
`admin --operation resolve-unknown --resolution-sha256 ...`, while closed. The
resolution binds the original request digest, transport epoch, journal key,
actual upstream-callback quiescence and owner evidence. It either retains an
authenticated exact completion response or settles as UNKNOWN_NO_REPLAY; it
never authorizes resend. Quiet logs or a disconnected caller are not evidence.

## Legacy drain: what original code actually permits

`LEGACY_CODE_WITNESS.json` pins the exact deployed protocol sources.

The three inspected `transport_proxy`, `lease_bridge` and `shared_scorer` files
match the deployed closure byte-for-byte. The local `native_proxy.py` does not:
local `f84ea3ea82d2855edbbc4ff1653046493b356942517d0beeb12cc98a587c9d10`
versus deployed `a017a86dd3ec8082d09219d01240daac550cd47d52f24f747cd949789917a793`.
This mismatch is retained in the witness, not hidden. Stage the actual pinned
deployed dependency, not this checkout copy; the candidate verifies all129 files.
The witness does not assert deployed `native_proxy.forward` AST parity from a
hash-only inventory. The decisive synchronous accepted-socket lifetime is
proved from the byte-matching original `shared_scorer.serve` and its CPU test.

- `transport_proxy.py` is threaded/non-daemon. It records TRANSPORT only after
  the outcome, not at admission. An accepted slow frame, export subprocess or
  forwarding thread can exist without any log.
- `lease_bridge.py` is threaded/non-daemon, with one upstream socket per call.
  TARGET is only routing. A waiting handler or child SSH channel is not a drain
  acknowledgment. Its 108/115-second socket limits do not stop scorer callbacks.
- Original `shared_scorer.serve` is synchronous per accepted connection. Its
  accepted socket remains owned through callback and response write. The CPU
  regression actually disconnects a caller during this original callback:
  the callback keeps running, then the old write encounters BrokenPipe.

Therefore a **complete, authoritative** inventory after irrevocably fencing
every creator of new old-route connections can prove drain: no accepted scorer
FD, no queued listener connection, no proxy/bridge handler or retained SSH
channel capable of forwarding, and no base-listener side ingress. Filesystem
socket inode metadata, a ps snapshot, one empty queue sampled before fencing,
stable COMPLETE states, timeout wrappers or quiet logs cannot prove this.
Switching five aliases alone leaves private old targets and already-established
SSH channels reachable. Do not retire the scorer based only on that switch.

`legacy.verify_drain` is executable and rejects omitted edges, nonzero queues,
accepted FDs, unresolved callbacks, stale observations and sandbox-only proof.
It verifies a **fresh owner-custody evidence bundle**, not the truth of invented
zeroes. It does not collect privileged kernel queue evidence or bypass the
earlier network-tool guard. That separately authorized real-host observation
and an effective fence over retained routes are still necessary readiness work.
If they cannot be obtained under current controls, keep the old scorer and
explicit no-judgment fence running; no synthetic barrier call or guessed sleep.

`LEGACY_PENDING.json` reconciles the immutable **02:36:19.482254 UTC** cut, not a
fresh drain: 78 logged origins; 52 have complete original attempts/seen entries,
26 are logged never-dispatched. These 52 are **not 52 newly scored captions**.
Unlogged accepted/queued work is an explicit unenumerated blocker, not counted
as zero. Per-origin hashes and exact dispositions are retained in that file.
It cannot serve as the final queue handoff until missing lifetimes are resolved.

## Sole-scorer executable and immutable closure

`candidate.py` uses the **actual deployed** 129-file source manifest and original
`judge_service` loader classes; it rejects the different current checkout main.
It restores existing NativeEpoch sessions, calls `reattach_existing_epoch`,
wraps `ProjectedHub`, applies a no-replay quarantine for every legacy queued
origin, and calls the **original serialized `serve`**. There is one model loader,
not another judge implementation. Existing primary panel values are reused
without re-scoring or rewriting old deployment metadata. Game/parser/policy/
seen state, output/mirror paths, weights, deadlines, judge BINDING/ACTIVE and
shadow clocks remain original. The historical `unparented` session stays parented.

The SHA-pinned owner plan has schema `R233_SINGLE_SCORER_CONTINUATION_V1` and:

- `source_root`, `original_source_manifest`, `candidate_source_manifest`: new
  source namespace with all 129 original bytes plus all projected/new runtime
  files. Manifest references are `{path, sha256}`. All loaded project modules
  must resolve inside that namespace; no mixed-checkout imports.
- `original_config`, `original_loaded`, `primary_scalar`, `primary_panels`,
  `weight_proofs`: preserved original owner references. Original config remains
  physical **4**, `kind=shared`, scorer deadline **1790791170** (September 30,
  2026 17:59:30 UTC), distinct from the source deadline.
- `old_identity`: freshly captured PID/start/boot/UID/command identity **plus
  `pid_namespace`**. PID absence from a different namespace cannot release the
  writer gate. Last read-only evidence names PID499900/start10094999/boot
  `7c130f24-3105-4909-abfb-b669929e0b96`; this is not a new live check.
- `legacy_code_witness`: pinned reference to the retained original-code witness;
  its hash must match the drain proof and its source hashes the deployed manifest.
- `drain_proof`: owner artifact with every `legacy.REQUIRED_EDGES` queue, all
  `REQUIRED_ROLES` exact identities/FD inventories, two post-fence observations,
  raw evidence digests and resolved callback/channel lifetimes. It binds
  `digest(preserved_trees)` and the exact queue artifact SHA.
- `session_snapshots`: five complete full state references; `preserved_trees`:
  `{root, files: {relative_path: sha256}}` for all original session outputs,
  attempts and epochs, plus `owner_custody`. Retain immutable backup bytes, not
  only this inventory. The loader checks complete sets, not selected files.
- `epochs`: five `{files, epoch_sha256}` original ledgers, including BINDING,
  ACTIVE, admissions/completions; `bindings`: five pinned projected bindings.
- `queue_dispositions`: actual original request objects/metrics, exact session,
  disposition in COMPLETE / PREPARED_NEVER_DISPATCHED / UNKNOWN_NO_REPLAY /
  NO_JUDGMENT_EXPIRED; no remaining unenumerated admissions; no replay authorized.
  Set `origin_request_authority: ORIGINAL_OWNER_REQUEST_ARTIFACTS` and
  `unattributed_connections_disposed: true` only when proved. Do not invent metrics
  from the abbreviated legacy transport logs. Unknown origins are also denied
  at the new receiver, independently of the CPU relay's ledger.
- `transport_epoch`, `previous_transport_epoch`, `candidate_runtime` (new 0700
  directory), `owner_custody` (preserved 0700 owner receipt store).
- `original_environment`: owner-captured original source identity/environment,
  including exact GPU UUID, offline flags, thread counts and tokenizer flag.
  Preserve original DevicePolicy/DeviceAllow, UID and NoNewPrivileges confinement.
  The loader checks environment and NoNewPrivs before any model load.
- `sole_writer_release`: Main/Averroes owner evidence of original writer retired,
  supervisor hold, same device/child confinement and exclusive physical4,
  binding drain and candidate-source hashes. Precreate the stable 0700
  `<old-config-root-parent>/node3-caption-continuation-owner` lock directory.
  The new flock is stable across candidate runtime namespaces, not per-version.
  It complements, but does not pretend to lock out, the unmodified old process.

## Minimal later integration order / remaining real checks

1. Stage pinned source/config and start only the new CPU relay CLOSED. Verify its
   foreground supervisor ownership, native-source live identities and strict
   owner custody. Main may switch the five stable source aliases to this fence;
   preserve old sockets/targets and all old accepted-result paths.
2. Obtain an effective fence over **all** old connection creators and real-host
   accepted/backlog/SSH lifetime proof. Reconcile exact pending requests/results.
   Keep the old scorer alive until proved; no inference from quiet artifacts.
3. Seal full restorable state/queue/seen/epoch/custody bytes and original source,
   environment/confinement. Coordinate the original writer's retirement and
   supervisor hold with Averroes. No child or parent is stopped.
4. Run candidate preflight, then owner-authorized sole-writer continuation in
   the preserved device confinement. Verify new PID/start/boot/namespace,
   original epoch/state/weight proof and new private socket. Keep relay closed
   and explicit no-judgment delivery operating throughout the outage.
5. Install owner readiness, CAS-open the relay, and observe **fresh natural**
   scorer response -> native Tool INBOX -> REQUEST/ACT receipts. No such live
   receipt or supervisor registration is asserted by this offline handoff.

## CPU validation

```sh
python3 -B -m unittest discover -s research_loop/workers/post_reboot_node3_parents_20260919 -p 'test_*.py' -v
```

See `CPU_TESTS.txt` and `MANIFEST.json` for the final run and sealed hashes.
Coverage includes dispatch fsync ordering, before/after-intent crashes,
concurrent fencing, incomplete frames, timeout ambiguity, retained response
versus delivery, owner-only resolution, journal tamper, same-origin metric
binding, deadlines, five-alias/parented policy, original callback-after-disconnect,
namespace ambiguity, preserved epoch/state, one-loader/original-serve wiring,
and temp-socket relay -> projected custody -> original serialized server end to end.
All scoring fixtures are CPU synthetic; none are production or historical replay.
