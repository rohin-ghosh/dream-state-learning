# Executable CPU-parent retention sidecar

Non-material operational implementation of `PARENT_REBIND_CONTRACT.md`.
**IMPLEMENTED, NOT EXECUTED AGAINST LIVE PARENTS.** Only new worker files were
added. `parent_service.py`, `remote_io.py`, provider/scaffold sources, live
ledgers, supervisor entries, natives, checkpoints, weights and leases were not
edited. No real signal, SSH probe, fence, rebind, provider call or successor
launch was used to develop/test this sidecar. Main's actual checkpoint/source
tests remain main's work and are not replaced by these synthetic tests.

## What the executable does

`retention_sidecar.py` exposes five explicit operations:

| Command | Actual behavior when main executes it |
| --- | --- |
| `prepare` | Read-only real-host identity/lock/drain/source checks; write a new immutable plan in this worker. No signals. |
| `fence` | Require exact plan bytes, disabled owner registry, idle/drained ledger, sole lock and no CPU subprocess/thread work; check existing remote acknowledgements read-only; pidfd-SIGSTOP only the exact CPU publisher. Recheck everything while it retains its lock, fsync/pin the ledgers, then emit the real receiver dependency receipt. |
| `verify-fence` | Read-only fresh CPU stop/PID/start/boot/UID/argv/lock, registry, complete ledger inventory and drain recheck. No native/checkpoint scan. |
| `rebind` | Require separately approved post-LOADED bytes and the still-effective fence. Verify actual receiver journal evidence remotely, then retire only the stopped exact CPU using pidfd-SIGKILL, take its publisher lock, recheck evidence, and atomically change only `STATE.native`. Write a committed receipt. Does NOT start a successor. |
| `serve` | Require the exact committed receipt and unchanged CPU-parent source pins. Acquire the original publisher lock through the unchanged `parent_service.run`, recheck actual receiver evidence, and run the original curriculum/provider/scaffold/loop with only receipt-bound remote I/O and truthful wrapper-process provenance. |

No command signals, launches, stops, resumes or modifies a GPU native. The old
CPU is intentionally retained stopped between fence and rebind so it keeps the
existing lock. Do not mistake this for stopping the learner. No SIGCONT or
automatic rollback is implemented: a failed or ambiguous operation requires
explicit owner reconciliation, not unpausing or retrying blindly.

The two arms remain separate transactions. Preparing/fencing one arm neither
signals nor changes the other. Current hardcoded native targets remain intact
in the original transport. The successor overlay validates a single exact new
identity instead of enabling native discovery or arbitrary PID adoption.

## Preconditions and bounded invocation

Execute on the real CPU host, not the private sandbox `/proc`. Main/Averroes
must first disable **only that arm's old registry entry** without terminating
the live CPU or changing its horizon. This sidecar never edits the registry.
The existing stopped publisher lock prevents another original publisher from
starting during the handoff; the entry must remain disabled through commit.

Use the current exact `PROCESS_*.json`, the same boundary binding object passed
to Banach, and the exact prepared receiver `epoch_id`. Do not use a stale PID
from these notes. The boundary binding's `command` must match the original
native argv; its boot/PID/start/UID/journal and `hard_end_unix=1790791200` are
checked. `REMOTE_TRANSPORT_PINS` is a main-reviewed JSON map of absolute remote
file paths to raw SHA256s covering the unchanged `root/parent_io.py` and its
publication/journal import closure. It is not a command or an alternate source.

Main supplies these variables; placeholders are not executable authorization:

```sh
WORKER=/data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_pair_parents_20260919
cd /data/home/rohing/dream-state-orch
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B "$WORKER/retention_sidecar.py" prepare \
  --arm "$ARM" --transaction-id "$TX_ID" --process-receipt "$PROCESS_RECEIPT" \
  --life-binding "$EXACT_LIFE_BINDING" --source-epoch "$SOURCE_EPOCH" --owner "$OWNER" \
  --transport-pins "$REMOTE_TRANSPORT_PINS" --disabled-registry "$DISABLED_MANIFEST" \
  --not-after-unix "$NOT_AFTER_UNIX"
```

The activation window must be positive and at most **600 seconds** from plan
creation, never later than1790791200. `prepare` prints `path` and the raw-file
`execute_sha256`. Review those exact bytes before executing `fence` once:

```sh
timeout --signal=TERM 240s /usr/bin/python3 -B "$WORKER/retention_sidecar.py" fence \
  --plan "$PLAN" --execute-sha256 "$REVIEWED_PLAN_FILE_SHA256"
```

Each SSH call has a90-second timeout, CPU stop wait3 seconds, CPU exit wait5
seconds, bounded inventories, and no transport redispatch loop. `serve` is the
finite foreground service through the unchanged original deadline, not a
240-second job. A timeout of `fence`/`rebind` may leave the CPU stopped or retired;
inspect the **same transaction's claim/blocked/committed files**. Do not launch
a replacement transaction, remove a claim, or infer that an interrupted command
did nothing. Pre-signal idle/cursor races refuse rather than wait for work or
drain by generating new model calls. Replan only after confirming no claim or
effect was created.

## Receiver interface, before handoff

The successful output is exactly:

`retention_transactions/<TX_ID>/PARENT_DEPENDENCIES.json`

It has schema `PAIR_RETENTION_PARENT_DEPENDENCIES_V1`, canonical
`life_binding_sha256`, exact `source_epoch`, owner, `delivery_fenced=true`,
`inflight_deliveries=0`, `durable=true`, `preserve_existing_ledgers=true`,
`automatic_pid_adoption=false`, `replay_delivered_messages=false`, and nonempty
absolute-path/raw-SHA256 `ledger_pins`. It pins every regular non-log artifact
under the arm directory, excluding the lock inode. Partials/symlinks/orphan
results, uncommitted publications, unknown provider attempts and unknown remote
dispatch markers are refusals. Existing explicit429 attempts and their retry
budget are preserved; the sidecar does not perform provider retries.

Call `PairReceiver(..., parent_dependency_receipt_path=dependency_path)`.
The regression suite calls Banach's actual `verify_parent_dependencies` method
with a sidecar-generated synthetic receipt, not a duplicate schema checker.
Before main arms native handoff/dispatch, recheck the actual CPU fence:

```sh
/usr/bin/python3 -B "$WORKER/retention_sidecar.py" verify-fence \
  --receipt "$DEPENDENCY_RECEIPT" --execute-sha256 "$DEPENDENCY_FILE_SHA256"
```

**Host boundary:** `PairReceiver` currently opens the receipt and its ledger
paths directly. It must be able to read the original pinned CPU files. If its
hooks execute solely on ovx4 without that filesystem, do not copy a JSON receipt
and pretend verification succeeded. Main/Banach must provide verified access
to those exact bytes and route the fresh owner fence check to the CPU host.
`verify_fence(path, hash, LinuxCPU())` is the implemented read-only owner hook;
filesystem/RPC wiring belongs to the receiving integration, not permission to
weaken its gate. See `TO_BANACH_SIDECAR.md`.

## Exact post-LOADED approval

Main writes a fresh, separately reviewed approval JSON only after its actual
checkpoint/source gates and actual receiver LOADED. The required shape is:

```json
{
  "schema": "PAIR_PARENT_POST_LOADED_APPROVAL_V1",
  "transaction_id": "same-transaction-id",
  "plan_sha256": "canonical digest of PLAN object, not raw file SHA",
  "dependency_sha256": "raw SHA256 of PARENT_DEPENDENCIES.json",
  "owner": "same explicit owner",
  "source_epoch": "same prepared epoch_id",
  "until_unix": 1790791200,
  "created_unix": 0,
  "not_after_unix": 0,
  "checkpoint_gate_receipt": {"path": "/absolute/main/actual-gate.json", "sha256": "raw SHA256"},
  "checkpoint_gate_passed": true,
  "new_native": {
    "pid": 0, "start_ticks": "exact", "boot_id": "same native host boot", "uid": 0,
    "argv": ["exact", "actual", "native", "argv"],
    "cwd": "/exact/receiving/source", "root": "/unchanged/life/root", "journal_id": "unchanged"
  },
  "guard_path": "/remote/exact/GUARD.json",
  "handoff_path": "/remote/exact/RETENTION_HANDOFF.json",
  "receiver_pins": {
    "/remote/exact/GUARD.json": "raw SHA256",
    "/remote/exact/RETENTION_HANDOFF.json": "raw SHA256"
  },
  "source_adoption": {"index": 0, "sha256": "canonical record SHA256"},
  "loaded": {"index": 0, "sha256": "canonical record SHA256"}
}
```

Zeros/text in this example are placeholders and do not pass checks. The second
activation window is also at most600 seconds. The main checkpoint gate is an
explicit owner verdict pinned to its actual receipt; the sidecar does not run
torch, restore model weights, or replace main's checkpoint/RNG tests. It joins
actual canonical COMPLETE/LEARN/intents, handoff token/dependency digest, source
adoption, LOADED, saved adapter/optimizer/base identity, unchanged guard/physical
allocation and fresh remote PID/start/boot/UID/argv/cwd. It hashes source pins
but does not rerun source suites. LOADED-to-source chain validation is bounded
to512 records and rejects intervening child work or duplicate receiver events.

```sh
timeout --signal=TERM 240s /usr/bin/python3 -B "$WORKER/retention_sidecar.py" rebind \
  --plan "$PLAN" --approval "$POST_LOADED_APPROVAL" \
  --execute-sha256 "$REVIEWED_APPROVAL_FILE_SHA256"
```

The command emits `REBIND_RECEIPT.json`; an absent committed receipt never
authorizes `serve`. It does not discard old evidence, reseed a parent, change
stages/cursors/budgets, regenerate a pending result, replay delivered messages,
or start a GPU/CPU successor. All old author identities remain in the ledger.

## Same-source successor and supervisor handoff

After reviewing the committed receipt, main starts precisely this foreground
service (credentials inherited; never insert secrets in argv/receipts):

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES= \
  /usr/bin/python3 -B "$WORKER/retention_sidecar.py" serve \
  --receipt "$COMMITTED_REBIND_RECEIPT" --execute-sha256 "$COMMITTED_RECEIPT_FILE_SHA256"
```

It requires sole ownership of the same `private/<arm>/PUBLISHER.lock` and an
exact initial carried-state hash. The original source/scaffold/provider files
must still match the old CPU process's pins. It calls the unchanged
`parent_service.run(arm)`, not a copied learning loop. Only the remote identity
adapter, original process-receipt argv, and durable publication-dispatch guard
are overlaid in memory. Parent-visible records use the unchanged projection;
sealed score documents are never passed to the model.

A durable dispatch intent is written **before** every successor remote publish.
If a call dies or times out without a durable acknowledgement, later attempts
fail closed; existing remote/local ambiguous markers are never removed. A
durable exact acknowledgement can be returned without another send. Provider
HTTP429 handling remains the original bounded policy; no model/scaffold fallback
or provider replay is added. Following ACT and literal ACT-text exposure remain
separate; a frozen correction compacted out of ACT is not failed restoration.

Main/Averroes may then replace only this arm's registry command with that exact
`serve` argv, same lock, same `operator_block_state`, same original1790791200
horizon and the new sidecar entrypoint hash. Initial admission accepts the
original disabled manifest; later supervised restarts accept only an enabled
manifest whose argv exactly equals the receipt-bound successor command. The
existing old command must never be re-enabled after native handoff. Record the
new real CPU identity separately from every old publication author. No
supervisor mutation or installation was done by this implementation.

## Failure recovery

- `FENCE_CLAIM` without dependency: CPU may be stopped; inspect exact identity,
  lock, provider/dispatch outcomes and `FENCE_BLOCKED`. No automatic resume.
- Changed dependency/ledger/registry: no native handoff and no old-CPU retirement.
- `REBIND_CLAIM` without commit: old CPU may be retired; inspect prepared receipt
  and both state hashes under the lock. Do not rerun rebind or start legacy code.
- Missing/wrong LOADED, source/guard/PID mismatch, old native still present,
  missing cursor or competing publisher lock: fail closed, no alternate receiver.
- Ambiguous send: preserve its claim/RESULT/ledger and require read-only owner
  reconciliation. Never mark it unsent because a command timed out.

Tests and pinned-source/no-live-action attestations are recorded separately in
`RETENTION_SIDECAR_TEST_RECEIPT.json`; historical restoration receipts are not
rewritten. Actual rollout acceptance still requires real dependency, committed
rebind, new CPU lock identity and fresh model INBOX→REQUEST→ACT receipts.
