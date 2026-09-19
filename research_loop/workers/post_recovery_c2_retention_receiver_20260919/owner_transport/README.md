# C2 executable owner transport — offline candidate, not dispatch permission

Write scope: this new `owner_transport/` subtree only. This is a non-material
transport repair implementing the requested existing C2 owner/receiving contract;
it does not ratify source adoption, broaden visibility, change learning behavior,
or authorize an operation. No live commands have been run by this worker.
Epoch2/3/4 source, all original owners, their registry, and the old r188 route
remain untouched. Parent prompts and sealed evidence are not delivered anywhere.

## What is executable

- `owner.py`: authenticate exact CPU service/publisher PID/start/UID/boot/argv/cwd,
  original three lock objects and holders, single thread, no active provider or
  remote subprocess and no GPU descriptors. Disable only the C2 registry entry;
  fully inventory ancestry, all ledger files/sidecars and reserved SOURCE cursors;
  stop only idle CPU owners after a read-only delivery drain, then recheck both.
  The existing publisher may be the service's child or a pre-existing orphan.
- `transport.py`: authenticated Main-selected owner command with nonce, exact
  dependency bytes/hash, original-owner proc/lock/ledger verification; maximum
  two seconds per owner RPC, additionally limited by the shared reserved budget.
  The original `gpu/ovx3_ssh.sh` carries only explicit read-only drain/LOADED RPCs.
  This worker did not invoke it. Its future helper source must match local bytes.
- `c2_owner_binding.py`: read-only verification of original consumed INBOX
  record+intent+mailbox bytes, or actual source-bound post-LOADED successor. The
  latter authenticates the exact COMPLETE/LEARN/adoption/LOADED chain, original
  r188, unchanged root/wall and native incarnation. It does not accept a launcher
  PID or boolean claiming LOADED. It reads at most 256 post-COMPLETE records and
  512 MiB, not the historical prefix.
- `successor.py`: only after explicit Main approval and actual LOADED, retire the
  two fenced CPU owners, acquire all original locks, create append-only successor
  manifests, preserve every predecessor ledger/cursor, and restart the same parent
  policy. The original publisher is executed in memory with exactly one remote
  verifier import changed. Its existing policy validator still runs, normalizing
  only the two already-approved native-binding fields for that validator. Original
  files are never edited. The service retains the original locks and 10s restart
  cadence; reenabling C2 requires the actual new CPU service identity/lock receipt.
- `coordinator.py` + `integration.py`: concrete original ReceivingHooks, guardian,
  writer-lock checks, sealed epoch4 C2Receiver/PrefixPreflight, original owner RPC,
  source-pinned Main route receipt, and exact `gpu.r188_node5_confinement dispatch`.
  One monotonic budget covers reserved proof/guard work, commit, post-exit checks
  and outer-launch handoff. No cold replay or slow-prefix fallback is provided.

The owner fence is distinct from a native reservation. Disabling registry
admission alone does not mean a publisher is idle, drained, or stopped. `MISSING`
is refused unless it is the exact terminal original pre-publication error shape
with no `sent_unix` or `inbox_publication`. A PUBLISHED call requires DELIVERED and
an authenticated original INBOX consumption. A partial provider call refuses.
Busy/queued work is allowed to drain under its original running owner; this code
does not kill a provider to manufacture an idle window.

A failed or timed-out CPU stop records every attempted role, attempts recovery
only for those authenticated CPU roles, and records unknown outcomes explicitly.
It never falsely claims a timed-out role was resumed. A sticky claim prevents
blind retry. Main must reconcile any `FENCE_REFUSED.json` or incomplete rebind.

## Preserved invariants and limits

- C2 only; original root `/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life`,
  journal `260be8b8710a42559b291797c6e14983`, hard end `1789927200`.
- Exact original r188 SHA256
  `75eed0e5e57cd7463e46fa10adeeebdb80b9ef1ce5e76a9b527c034d1e8e6481`.
  No alternate GPU route, modified `copy_raw`, relaxed admission, new wall
  authorization or second ABI. The sealed epoch4 v4 prefix ABI is reused intact.
- The native observer deliberately accepts only an **adjacent final
  COMPLETE+LEARN** (`max_records=2`). An intervening INBOX or later REQUEST makes
  that observation ineligible; it is not skipped or replayed. All mailbox files
  are still checked, and the pinned full prefix/tail reader preserves history and
  sidecars. This is a stricter eligible window, not permission to ignore records.
- The native guardian remains capped at 30 seconds. The shared coordinator
  budget also reserves the Main-pinned commit margin. Static source-specific
  readiness evidence is required **before** any native reservation. After an
  attempt begins, failure creates a sticky review requirement; after exit there
  is no automatic relaunch, retry, parent adoption or full-prefix fallback.
- Owner rebind is a separate actual post-LOADED action, never triggered by an
  outer dispatch return. The single import relocation is a deliberate new owner
  binding to an authenticated successor, not a claim the old 11502 verifier works
  unchanged. All other parent treatment/configuration fields remain exact.

## Real blockers; no invented readiness

1. Actual service/publisher identities, idle provider/drained publication state,
   original locks and all ancestor CONFIG paths must be freshly authenticated on
   the **original owner**. They were not observed or fenced by this worker. The
   whole ledger rehash plus authenticated bridge must fit its real two-second RPC
   limit. A local mirrored dependency JSON is not that evidence.
2. The Main-pinned complete all-in reserved-cost/context/route receipts are not
   generated here. Strict host read success is not original r188 consumer-context
   admission or a measured all-in reservation. The approved cross-namespace mode
   remains pinned by original admission, never selected by this transport.
3. **Original r188 still contains two 100s probe/admission timeouts and a
   long-lived child service.** The adapter asynchronously starts the exact original
   outer command; its result proves neither completion of privileged admission nor
   LOADED within 30s. CPU fake-clock tests prove budget refusal/order, not the full
   original-route latency or a hard startup deadline. Main must not approve the
   static all-in receipt from these tests. If the required 30s bound includes
   privileged dispatch/startup, this is an unresolved route/deadline integration
   gap, not something this worker fixes by changing r188 or extending reservation.
4. As recorded in Main's local receipt
   `post_recovery_pair_receiving_checks_20260919/C2_EPOCH4_FORWARD_B_1789787815.json`
   (2026-09-19 03:16:55 UTC), B=13231 SHA
   `8715c6a9c27d97ed1a8dbf14abc6c73d044d7a733f868678806152b86a705d54`
   plus LEARN13232 validates optimizer8780. Its 4.319s reader result preserves 360
   INBOX and a pending REQUEST: **not a handoff-eligible head**. It is strictly a
   same-host-namespace read observation, not new-native startup proof. No scan is
   repeated by this worker.

The producer proof remains Main's own production epoch4 proof at
`/localhome/local-rohing/orch_retention_20260919/C2/epoch4/prefix_evidence_1789786841504428364`.
Forward-B guard is `forward_B_1789787810895205220/GUARD_B.json`, SHA
`1b306e25143491ee974e68748b137ab0a4edab6bfba91a5f870c385f5d64f87b`.
This is a source pointer, not a choice of authorization for a future boundary.

## Exact inputs

Every reference is `{ "path": "ABSOLUTE_LITERAL_PATH", "sha256": "EXACT_FILE_SHA256" }`.
`digest()` refers to canonical JSON SHA256, distinct from a file SHA256.
No sample identity, boolean receipt, approval or live transaction is fabricated.

`C2_OWNER_TRANSPORT_PLAN_V1` requires:

- `deadline_unix`, `created_unix`, `not_after_unix` (at most 600s, no later than
  the original wall), `owner_root`, `transaction_dir` (new direct child of this
  adapter's `transactions/`), and exact original C2 `registry` reference.
- `old_life` = the exact original boundary binding; `source_epoch` = prepared
  epoch ID; `manifest` = actual running publisher's original manifest reference.
- `service` and `publisher` identities (`pid`, `uid`, `start_ticks`, `boot_id`,
  `argv`, `cwd`, plus publisher `ppid`) read on original owner; no native PID.
- `locks` mapping `service/controller/publisher` to the three original absolute
  paths; `lock_identities` = each original file's `dev/ino/mode`.
- `ancestry_configs` maps **every** actual ledger output directory to its exact
  CONFIG reference. Do not guess sibling locations: the historical r233 output
  and its control CONFIG reside in different directories. Follow existing
  predecessor STARTED hashes to the end and reserve the max SOURCE response count.
- `source_pins` contains all original manifest local-source pins, original
  c2_service/c2_restore/strong/c2_parent_continue/programme-parent/SSH wrapper and
  **every `owner_transport/*.py`** byte. `remote_adapter_directory` and
  `remote_files` pin exactly the same `common.py` and `c2_owner_binding.py` bytes
  in a separate Main-staged read-only directory, never production native sources.

`C2_OWNER_ACTION_APPROVAL_V1` requires exact `plan_sha256` = `digest(plan)`,
`operation`, `deadline_unix`, `created_unix` and `not_after_unix`. `rebind` also
pins `dependency` and `successor_binding`; `enable-successor` also pins `rebound`
and `service_receipt`. Each operation requires its own Main approval.

The coordinator configuration contains the existing sealed epoch4 inputs:
`binding`, `prepared`, `authority`, `bundle`, `bundle_manifest`, `staged`,
`cpu_receipt_path`, `consumed_wall_receipt`, `python_executable`, `control_root`,
`prefix_authority`, `prefix_policy`. It adds:

- `coordinator_source_pins`: all local adapter Python files plus the actual loaded
  original boundary.py/coordinator.py/operations.py, with relocated absolute paths
  where necessary. These are verified before constructing receiving hooks.
- `owner_bridge`: `command` (Main-selected authenticated original-owner execution
  transport; no shell inference), `dependency` and original owner `source_pins`.
- `route_receipt`: existing `C2_RETENTION_MAIN_ROUTE_V1` exact reference, additionally
  carrying `owner_dependency` equal to that actual fence dependency;
  `route_evidence_pins`: exact source-specific supporting evidence. The route
  adapter adds **no** readiness fields; sealed C2Receiver rejects missing gates.

`C2_POST_LOADED_OWNER_BINDING_V1` requires exact `deadline_unix`, `handoff`
reference to the actual unwrapped token, `source_epoch`, `life_binding_sha256`,
actual `native` identity and actual `loaded` record index/hash. Use the receiving
control's `RETENTION_HANDOFF.json`, not an audit wrapper or a launch PID.

## Commands — CPU checks now; action templates for Main only

From repository root, safe offline verification:

```bash
W=research_loop/workers/post_recovery_c2_retention_receiver_20260919/owner_transport
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B "$W/run_checks.py"
python3 -B "$W/cli.py" --help
```

The check runner creates a new scoped `checks_*` directory with source/input
hashes, individual test logs, test receipt and a **node-coordinator overlay**
archive. The archive includes unchanged original boundary modules and package
initializer in repository-relative layout. It does not contain native source,
authority, running-owner configuration or live receipts. Main may stage it into
a new root; then `common.REPO` resolves to that overlay root. Run original-owner
operations only from this original repository's adapter, not a copied owner.
The node separately needs the already-staged sealed epoch4 bundle/tools, and
Main must relocate/re-pin coordinator paths without changing their bytes.

After Main has independently approved exact current inputs, these are the
entrypoints, **not commands executed or authorized by this handoff**:

```bash
python3 -B "$W/cli.py" prepare --plan "$PLAN_INPUT" --plan-sha256 "$PLAN_INPUT_SHA"
python3 -B "$W/cli.py" inspect --plan "$PLAN" --plan-sha256 "$PLAN_SHA"
python3 -B "$W/cli.py" disable --plan "$PLAN" --plan-sha256 "$PLAN_SHA" --approval "$DISABLE_APPROVAL" --approval-sha256 "$DISABLE_APPROVAL_SHA"
python3 -B "$W/cli.py" fence --plan "$PLAN" --plan-sha256 "$PLAN_SHA" --approval "$FENCE_APPROVAL" --approval-sha256 "$FENCE_APPROVAL_SHA"
python3 -B "$W/cli.py" owner-check --dependency "$DEPENDENCY" --dependency-sha256 "$DEPENDENCY_SHA"
python3 -B "$W/cli.py" coordinate --configuration "$CONFIGURATION" --configuration-sha256 "$CONFIGURATION_SHA" --execution-sha256 "$MAIN_EXECUTION_SHA"
python3 -B "$W/cli.py" rebind --plan "$PLAN" --plan-sha256 "$PLAN_SHA" --approval "$REBIND_APPROVAL" --approval-sha256 "$REBIND_APPROVAL_SHA" --dependency "$DEPENDENCY" --dependency-sha256 "$DEPENDENCY_SHA" --binding "$ACTUAL_LOADED_BINDING" --binding-sha256 "$ACTUAL_LOADED_BINDING_SHA"
python3 -B "$W/cli.py" serve --receipt "$REBOUND" --receipt-sha256 "$REBOUND_SHA"
python3 -B "$W/cli.py" enable-successor --plan "$PLAN" --plan-sha256 "$PLAN_SHA" --approval "$ENABLE_APPROVAL" --approval-sha256 "$ENABLE_APPROVAL_SHA" --receipt "$REBOUND" --receipt-sha256 "$REBOUND_SHA" --service-receipt "$SERVICE_RECEIPT" --service-receipt-sha256 "$SERVICE_RECEIPT_SHA"
```

`owner-check` consumes its nonce request on stdin from the bridge; it is not a
standalone fabricated acknowledgement. `serve` is the explicit foreground CPU
service; Main owns its actual launch/registry reenable. `MAIN_EXECUTION_SHA` is
`coordinator.execution_digest(configuration)` over **all** fields; calculation
alone is not approval. No service-manager operation is added to the owner adapter.
