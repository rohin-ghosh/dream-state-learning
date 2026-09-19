# C2 retention receiver — local, non-material continuity repair

Scope: this directory only. Five retention ports and immutable source staging
are complete and are inputs, not work to repeat. No running sources, parents,
signals, remote dispatch, GPU calls, service-manager calls, or commits belong
to this worker. Banach owns the pair receiver; its files remain read-only.

This sidecar implements the boundary `ReceivingHooks` interface for learned C2
on physical GPU 1. It does not reuse the pair's physical-1-frozen semantics.
The hard end remains **1789927200**; the original life root/journal, r188 source
and confinement, R227 rows, preemption, prompts, and recipe remain unchanged.

CPU-ready does not mean dispatchable. Main must provide an exact historical
WALL_EXTENDED record and intent, a fresh COMPLETE/LEARN candidate and checkpoint,
real receiving-source CPU/guard evidence, an explicit source-change authority,
and an owner-approved r188/bridge/parent/adoption route. Missing route evidence
must fail `verify_prepared` before the coordinator reserves or stops a process.
This package contains no live dispatcher. Main supplies that separately reviewed
capability; a direct guard dispatcher is not an acceptable substitute for r188.

## Exact supported-route gap and proposed closure

The supplied `C2_STAGED.json` describes **epoch1 with only the three retention
edits**. Its exact native source does not emit `RETENTION_SOURCE_ADOPTED`.
It cannot satisfy the boundary's before-first-THINK source-epoch requirement.
`verify_prepared` therefore rejects epoch1 before any reservation/stop.

`ports.py:proposed_ports(source)` proposes two additional files for a NEW
immutable receiving closure: two entry-seam lines in
`gpu/orch_r125_continual_native.py` and new `gpu/c2_retention_runtime.py`.
It verifies native preimage
`1bf18d5f34d2f027be1c79120ec654afe9869e647150245a29c8a19ebda81ff6`
and refuses an overlapping runtime file. `C2_ADOPTION_PORT.json`, `ADOPTION.patch`
and `overlay/` contain exact bytes/hashes. None is applied to epoch1 or a live source.
The old r188, guard, journal and checkpoint-tail reader remain byte-identical.
The runtime acquires the existing writer lock through the original constructor,
restores the exact tail, verifies COMPLETE/LEARN and mailbox preservation, then
records the source epoch before model load/THINK. Duplicate adoption, unresolved
work, a living-old-native token, wrong source hashes or a rewritten mailbox refuse.

Main must stage and re-pin this separate receiving closure, keeping epoch1
immutable. The new stage receipt must retain the original live source/native
binding and include all five old-live-to-new changes, not merely the two additions.
Use `SOURCE_PINS.receiving.json`; bind the same complete delta in the boundary's
explicit source-change authority. The receiver allowlist permits precisely the
three retention changes plus these exact two adoption changes, nothing else.

## Integration (Main owns activation)

1. Obtain the old guard/plan, full source pins and **current exact** native
   boot/PID/start/UID/argv. The historical stage PID is not a liveness assertion.
2. Build `prepared.new_plan = plan_template(old_plan, new_source)`. The template
   retains the old COMPLETE anchor; `prepare_receiver` changes only its index/hash
   to the selected candidate. Do not change the old plan, root, recipe or deadline.
3. Provide `C2Receiver(..., consumed_wall_receipt={record, intent}, route=MainRoute(...))`.
   These are the exact original historical journal bytes, not a reconstructed
   plan authorization. The shared boundary checks the deadline-only prior-state
   transition and fsyncs/rechecks both original files; it never replays the extension.
4. Supply a real `ACTUAL_RECEIVING_SOURCE_CPU` receipt with `passed=true` and full
   receiving `source_pins`. This package's synthetic `TEST_RECEIPT.json` is rejected
   as that receipt. The fresh CPU probe uses `CUDA_VISIBLE_DEVICES=''`; learned
   physical-1 C2 requires positive optimizer steps, not the frozen-pair rule.
5. Main provides three callbacks in `MainRoute`: read-only `preflight(binding,
   prepared)`, `dependents_clear(handle)` and separately authorized `dispatch_once(token)`.
   The preflight result must be a durable `C2_RETENTION_MAIN_ROUTE_V1` receipt,
   bound to `digest(binding)`, `digest(prepared)`, `digest(new_source_pins)`, deadline,
   r188 module and explicit owner. It must contain every true `ROUTE_GATES` field,
   `automatic_parent_adoption=false`, `inflight_deliveries=0`, nonempty `evidence_pins`
   and existing `ledger_pins` with absolute file names and raw hashes. This is
   owner evidence, not self-certification; the code cannot infer omitted ledgers.
   Return identical bound receipt bytes throughout the attempt, not fresh timestamps.
6. Only Main may wire `receiver.hooks()` into the boundary coordinator with explicit
   execution approval and source authority. This worker does not call it on a host.
   The runtime token is written once only after the old-native-exited handoff;
   unknown dispatcher outcomes retain the claim and cannot be retried automatically.

Candidate controls are written under `new_source.parent/control/attempts/<digest>/`:
PLAN, LEASE, RECEIVING_CPU, TAIL_CPU, CHECKPOINT_CPU, MAIN_ROUTE,
PLAN_METADATA_RECEIPTS, ALLOCATION, GUARD, GUARD_CPU, OWNER_REBIND_REQUIRED and
RECEIVER JSON. Guard preservation permits only those file relocations and the
new full source pins. No direct guard dispatcher, r188 replacement, parent
rebinding, new PID adoption or bridge restart is implemented here.

## Actual-dispatch blockers

- Main's new immutable closure/stage/authority including the adoption seam.
- Exact original WALL_EXTENDED record+intent (not available in this local audit).
- Fresh COMPLETE+matching LEARN, durable adapter/optimizer/RNG bytes, sidecars,
  original mailbox and a real receiving-source CPU/guard check on the node.
- Source-bound CPU bridge guard/socket rebinding readiness, parent delivery fence,
  zero in-flight deliveries, preserved owner ledgers, source-epoch builder entry,
  allocation approval and uid2524 access to the receiving control files.
- Main's supported r188-only dispatcher and fresh privileged target admission;
  explicit post-LOADED native identity/source-adoption checks and owner rebind.
- Real-prefix latency approval. This exact reader hashes all retained bytes but
  does not replay historical stream bodies. It is **not O(tail)**; probes time out
  at 120 seconds without fallback. Local synthetic timing is not a live budget proof.

## Validation and limits

Run `python3 -B research_loop/workers/post_recovery_c2_retention_receiver_20260919/run_checks.py`.
`TEST_RECEIPT.json` binds test logs, code, original staged receipt, prior five-port
receipts, and exact reader/confinement sources. `READY.json` distinguishes
CPU integration readiness from dispatch permission. Local tests exercise real
pinned reader/adoption code on synthetic journals and mock the model/guard
subprocess in hook tests. Torch is absent in this interpreter; checkpoint-probe
logic tests use a synthetic Torch interface. No real optimizer payload or GPU
restore is certified by these tests. CUDA RNG validation in the probe checks
saved CPU tensor bytes, not a CUDA device restore or post-checkpoint resident RNG.

No message has been sent to Banach or a parent. This scope note is coordination
documentation, not an acknowledgement or permission from another worker.
