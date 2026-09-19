# Exact-COMPLETE source adoption: main integration contract

## Status and scope

2026-09-19 UTC: non-material repair of the existing boundary coordinator, with
CPU-only regression coverage. All edits are confined to this worker. No live
signals, GPU work, native restarts, dispatches, source staging, plan integration,
commits, or pushes were performed. The VM reboot is not an adoption boundary:
historical bindings must not be rebound to a new boot, PID, or start time.

`continue_pair.py` and `finish_pair_boundary.py` in the recovery worker were read
for compatibility, not modified or executed. Their older selectors are not this
gate: a lone SLEEP_COMPLETE is insufficient here, and INBOX-only arrivals are
preserved rather than rejected or removed. No deadline-extension authority is
reused as permission for a source change.

There is deliberately no rollout CLI. Main owns the staged immutable source,
receiving plan/guard, checkpoint proof implementation, source-epoch consumer,
and idempotent admission/dispatch hooks. This code must not be activated before
those hooks and their evidence exist. Passing these CPU tests is not evidence
of a successful live reservation or deployment.

## Public interface

Use package imports from the repository root:

```python
from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import digest
from research_loop.workers.post_recovery_retention_boundary_20260918.coordinator import coordinate
from research_loop.workers.post_recovery_retention_boundary_20260918.operations import LinuxOperations, ReceivingHooks
```

Main constructs `ReceivingHooks` with all seven callbacks below, then constructs
`LinuxOperations(binding, hooks, approved_execution_sha256=..., control_root=...)`.
The existing, absolute control directory holds append-only audit receipts.
`approved_execution_sha256` must be main's explicitly approved digest of
`dict(binding=binding, prepared=prepared, authority=authority)`, not inferred from
test success or model agreement. Only main's separately activated entry point
may call `coordinate(binding, prepared, authority, operations)`.

`binding` is one exact currently running life:

- `pid`: integer greater than one; `start_ticks`: decimal string; `uid`: integer.
- `boot_id`: original `/proc/sys/kernel/random/boot_id`, captured with the live
  identity. A different boot refuses before pidfd opening. Never fill a missing
  historical boot ID with the rebooted machine's ID.
- `command`: exact decoded `/proc/PID/cmdline` list, including `guard_path` as an
  entire argument; no substring PID discovery, wildcard match, or fallback PID.
- `guard_path`, `guard_sha256`, `source_pins`: original immutable guard and pins.
- `journal_root`, `journal_id`: original absolute journal and manifest identity.
  `Path(guard.get('copy_raw', plan['root'])) / 'stream'` must be this journal.
  Copied forks retain the original logical `plan.root`, which need not exist on
  this host; neither plan root nor the guard's copy mapping is rewritten.
  Directory and WRITER.lock inode identities are retained for the whole attempt.
- `hard_end_unix`: already admitted deadline, unchanged throughout adoption.

`prepared` retains the existing fields: `old_guard_sha256`, `old_source_pins`,
`new_source_pins`, `old_plan`, `new_plan`, `epoch_id`, and literal-true
`cpu_passed`, `same_journal`, `same_checkpoint_payloads`, `same_confinement`.
Plan equality permits a different absolute `source_root`, relocation of the same
relative `startup_context.path`, and the explicitly proven continuation metadata
normalizations below. Deadlines, targets, recipes, row policy, prompts, controls,
logical root, and all remaining fields compare equal. Any nonempty exact approved
source delta is allowed, including separately authorized/tested recovery reader
additions; there is no fixed three-file count. Source removals remain refused.

`authority` contains `schema="RETENTION_SOURCE_CHANGE_AUTHORITY_V1"`,
`life_binding_sha256=digest(binding)`, `wall_extension_authorized=False`, the
same `epoch_id`, and `approved_source_changes`, an exact map from each of the
approved paths to `{"before": old_hash, "after": new_hash}` (an added file has
`before=null`). No unlisted change is accepted. These are source
adoption receipts, never a WALL_EXTENDED event or lease authorization.

## Required receiving hooks

Callbacks raise on failed validation; no permissive defaults are supplied.
Only `dispatch_once` may launch anything. All prior hooks are CPU/file checks
and receiving-side preparation, with no GPU/model load or native journal edits.

| Callback | Obligation / return value |
| --- | --- |
| `verify_prepared(prepared)` | Rehash the complete immutable source trees, CPU receipts, receiving plan/guard, confinement and allocation evidence; enforce the exact approved per-file delta, including tested reader additions. Called before waiting and again while reserved. |
| `dependents_clear(handle)` | Return literal `True` only when this exact native has no active readout, subprocess work, or other dependent that would be discarded. Never signal a dependent. |
| `verify_checkpoint(candidate)` | Fully validate saved adapter files, optimizer payload/counters, Python/CPU/CUDA RNG payloads, working state and native journal semantics; fsync checkpoint payloads/COMMIT/directories. Return the proof below. Hashes alone are not a substitute for validating restoreability. |
| `prepare_receiver(candidate, prepared, proof)` | Prepare immutable receiving artifacts against this exact candidate without loading a model or opening a second writer; return the receiver below. A new candidate must get new bound artifacts, not reuse an old preservation sidecar. |
| `recheck_checkpoint(proof, frozen)` | Revalidate proof binding and unchanged checkpoint payloads during the reservation; fail if any prepared evidence changed. |
| `verify_receiver(receiver, frozen)` | Validate all receiving artifact hashes and compatibility with the exact saved state and current INBOX tail, both while reserved and after old exit. The original mailbox remains append-only and is rescanned by the successor. |
| `dispatch_once(token)` | Persistently deduplicate by life/source epoch, admit the same journal with the new source only, and honor the original deadline. Validate token/authority/receiving hashes and acquire the native WRITER.lock before model load. Recheck journal boundary plus permissible INBOX additions under that lock; durably record a distinct source-adoption epoch before the first THINK. Never emit/apply a wall extension, replay unresolved work, cold-start, or infer a reboot recovery. |

Checkpoint proof fields:

```text
complete_sha256 = candidate.complete_sha256
checkpoint_sha256 = digest(candidate.checkpoint)
adapter_verified = optimizer_verified = python_cpu_cuda_rng_verified = True
working_state_verified = durable_files_and_directories = True
```

Receiver fields checked by the coordinator:

```text
source_epoch = prepared.epoch_id
resume_state_sha256 = candidate.resume_state.sha256
checkpoint_sha256 = digest(candidate.checkpoint)
same_journal_root = binding.journal_root
deadline_unix = binding.hard_end_unix
rescans_original_inbox = no_model_load_before_writer_lock = True
source_adoption_not_wall_extension = True
```

When continuation metadata exists, the receiver additionally supplies `plan`,
`plan_sha256=digest(plan)`, and `plan_metadata_receipts` as specified below.
This canonical plan digest is not the raw-file SHA used by GUARD.plan_sha256;
main must verify both bindings, not interchange them.

Main should include receiving artifact paths/hashes in that receiver object;
the object is preserved in both the durable handoff intent and token. Preserve
all artifacts from refused/raced attempts; do not overwrite prior evidence.
Main must preserve any existing `copy_raw` mapping in the receiving guard and
check the effective journal against `binding.journal_root`; a retained C2 plan
identity is not a request to resume a different journal. If the current receiving
path cannot meet this contract, refuse adoption; do not relax the source-only gate.

## Proven continuation metadata

This is a same-deadline continuity repair, not a WALL_EXTENDED action. Use these
helpers from `boundary.py`:

```python
required = required_plan_metadata_receipts(old_plan, new_plan_template)
stamp = plan_metadata_binding(binding, candidate, old_plan, effective_new_plan)
verify_source_only_plans(old_plan, effective_new_plan,
    binding=binding, candidate=candidate, receipts=plan_metadata_receipts)
normalized = normalize_source_only_plan(old_plan, effective_new_plan,
    binding=binding, candidate=candidate, receipts=plan_metadata_receipts)
```

`required_plan_metadata_receipts` performs structural preflight only; it grants
no adoption permission. `normalize_source_only_plan` returns a comparison copy
equal to the old plan, not a plan to write or deploy: normalization restores old
metadata only for equality checking. `verify_source_only_plans` retains its
previous return value, `digest(old_plan)`, but refuses unproven metadata edits.

The candidate must retain `records` and their parallel `record_intents` from
`read_boundary`, plus the bound journal identity, complete/learn references,
checkpoint and saved state. The helper revalidates the exact COMPLETE+LEARN pair
and state/intent hashes; a bare claimed index/hash or pending REQUEST is not
proof. `stamp` binds that pair, saved state, checkpoint, original deadline,
life/guard binding, old and effective plan digests, retained logical plan root,
and actual journal identity. It deliberately excludes the mutable INBOX head.

Receipts are a dictionary with exactly the required keys. Each receipt contains
`binding=stamp` and literal `durable=True`, plus the following evidence:

- **`consumed_wall_extension`** is required when the old plan has a non-null
  `authorized_wall_extension`. The receiving plan must omit that key entirely;
  leaving it unchanged, replacing it, or setting it to null is refused. Supply
  the original `WALL_EXTENDED` journal `record` and its exact `intent`. The record
  must precede the selected COMPLETE in the same journal and contain exactly
  the old authorization. Its saved deadline must already equal the admitted
  deadline. Replacing only that saved state's deadline with the authorization's
  previous deadline must reproduce the ancient `previous_stream_sha256`; this
  proves the consumed transition without applying it again. LinuxOperations
  point-reads and fsyncs that one record/intent pair while checking the receiver,
  including after exit. Main obtains the known reference from retained evidence;
  there is no full-prefix replay or history search in this helper.
- **`checkpoint_tail_recovery`** is required whenever the old plan has that
  selection, even if its pins happen to equal the current candidate. Keep the
  reader enabled and all root/journal/life/policy/bounds/sidecars/durability fields
  unchanged. Only `complete_index` and `complete_sha256` may be re-anchored, and
  they must name the actual selected COMPLETE, never the old stale tail or an
  arbitrary checkpoint. No rollback or rewritten old anchor is accepted.
  Supply this normalized receiving-reader receipt:

```text
binding = stamp
durable = True
selection_sha256 = digest(effective_new_plan.checkpoint_tail_recovery)
restored_state_sha256 = candidate.resume_state.sha256
head_index / head_sha256 = the reader's verified head on this exact chain
pending = None
historical_body_replay = False
sidecars_verified = inbox_preserved = True
reader_source_pins_sha256 = digest(prepared.new_source_pins)
cpu_receipt_sha256 = SHA256 of the actual receiving-reader CPU receipt file
```

Main's hook produces that receipt from the tested checkpoint+tail reader, checks
the CPU receipt's bytes and source-pin binding, and rechecks sidecars and INBOX
continuity. Do not supply flags without evidence, disable the reader, or replace
it with slow historical body replay. Additional INBOX-only records/files after
the reader's captured head are allowed: the boundary checks preserve them and
the receiving reader rescans the original mailbox. Other intervening work is
still a race, not permission to kill or replay it.

`prepared.new_plan` is the approved structural template. On every
`prepare_receiver(candidate, prepared, proof)` call, return a freshly anchored
`receiver.plan`, its canonical digest, and newly bound receipts. Only the two
tail pin fields may differ from the template. The coordinator validates the
effective plan before reservation, while stopped, against the durable final
boundary, and after old exit. A race can therefore retry the same pidfd at a new
COMPLETE with a new receiver plan; it never reuses the stale C2 tail. The effective
plan and receipts are retained in INTENT/READY/token evidence. Hooks and staging
remain main-owned; none are dispatched by these CPU tests.

## Reservation and failure behavior

LinuxOperations checks boot/PID/start/UID/full command, guard bytes, plan bytes,
source pins/deadline and journal identity. It refuses an already stopped or
exited native. A separate per-journal RETENTION_BOUNDARY.lock serializes
coordinators; the existing native WRITER.lock is neither replaced nor unlocked.

The selector requires matching hashed SLEEP_COMPLETE and R184_LEARN_COMPLETE
records with their exact intents. Saved state must be fully trained, with no
pending work, the same complete checkpoint, and the admitted deadline. Only
INBOX records may follow that pair. Partial publication is retried without a
signal; any pending REQUEST or other new work makes the candidate ineligible.
The bounded tail defaults to 128 records; absence of COMPLETE in that tail
means wait, never fall back to an older or incomplete state.

After expensive CPU preparation, one guardian owns SIGSTOP/CONT/TERM through
the original pidfd. The parent verifies actual stopped identity and rescans the
boundary, checkpoint and receiver. Before commit it fsyncs both receipts and
their intents, mailbox JSON files, manifest and directories and rechecks
identities. All registered and unregistered published INBOX files are retained;
identical duplicate files are allowed like the native reader. Temporary/non-JSON
arrivals are untouched. New arrivals need not stop, and the successor rescans
the same original mailbox rather than a frozen copy.

A raced boundary resumes the same pidfd and retries; it never opens a new
handle or sends TERM to a pending REQUEST. The guardian serializes watchdog
expiry with commit: expiry/disconnect resumes; a late commit cannot terminate
the resumed native. An irreversible commit sends TERM then CONT to that exact
handle only; no SIGKILL fallback exists. No dispatch occurs without observed
pidfd exit, exclusive native writer-lock acquisition, unchanged post-exit
boundary, a durable READY token and a still-live original deadline. The writer
lock is released before dispatch so the receiver must acquire and revalidate
it itself. Independent actors must not bypass these life/writer locks.

On unknown exit or any post-TERM failure, retain the intent/evidence and refuse
automatic dispatch. Main must reconcile the old handle, READY token and its
durable dispatch ledger; never blindly retry a failed dispatch. Guardian process
crash/host reboot and storage stalls are not made safe by a live test here;
these regressions exercise simulated signal/clock/transport behavior only.

## CPU regression commands

Recorded results, 2026-09-19 01:08:40 UTC: worker suite **83 tests, OK,
0.230s**; legacy pure subset rerun **9 tests, OK, 0.001s**. Package-import smoke
for the metadata helpers and operations passed without activation. The earlier
59-test baseline is included in the expanded suite. No real-process signal test
was run.

From the repository root (no Python bytecode or pytest cache writes):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s research_loop/workers/post_recovery_retention_boundary_20260918 -p 'test_*.py' -v
```

All signals, forks, live pidfds and dispatches in the worker suite are mocked;
filesystem fixtures stay inside this worker and are removed by unittest cleanup.
It covers pending/raced work, journal/intent corruption and partial publication,
INBOX races/preservation, source-only authorization, pid reuse/reboot, exact
guard/plan/journal identity, exclusive locks, watchdog expiry/disconnect, failed
entry cleanup, same-handle retries, deadline expiry and no-dispatch failure paths.
Metadata regressions additionally cover consumed-wall proof, stale/forged C2
anchors, immutable reader settings, candidate-specific re-anchoring after a race,
exact source allowlists with reader additions, and copy_raw/retained-root mapping.

Legacy CPU-only compatibility command (intentionally excludes the real-process
`test_cpu_exception_resumes_exact_process`):

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=research_loop/workers/rohin231_curriculum_birth_20260918/recovery_20260918T1646Z \
python3 -B -m unittest -v test_continue_pair \
  test_finish_pair_boundary.CompleteBoundaryTests.test_complete_and_learn_tail \
  test_finish_pair_boundary.CompleteBoundaryTests.test_no_generation_or_update_tail \
  test_finish_pair_boundary.CompleteBoundaryTests.test_bad_hash_fails_closed \
  test_finish_pair_boundary.CompleteBoundaryTests.test_pending_not_complete \
  test_finish_pair_boundary.CompleteBoundaryTests.test_mismatched_learn_cycle
```
