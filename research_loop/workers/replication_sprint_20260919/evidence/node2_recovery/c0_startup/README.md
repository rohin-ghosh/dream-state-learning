# C0 pending-sleep startup — isolated CPU handoff

**Non-material candidate only. Not staged, admitted, launched, or a claim that C0 is restored.**
Everything written by this workstream is under this directory. Original runtime/source,
PLAN/GUARD/lease, failed checkpoints, wall candidate, Astra7 partial-intent candidate,
and node3 files remain untouched. No remote writes, GPU/model calls or signals occurred.

## Immediate blocker: owner-available storage

`CAPACITY_145530.json` is a bounded node2 read at **2026-09-19 14:55:30 UTC**, using
the original `gpu/ovx_ssh.sh` route as UID2524, which is also C0's directory owner.

| Item | Bytes |
| --- | ---: |
| Owner-available (`f_bavail`, not `f_bfree`) | 947,650,560 |
| Filesystem total free including reserved blocks | 39,556,390,912 |
| Conservative additional-space budget | 2,981,136,864 |
| Shortfall against that budget | **2,033,486,304** |

The budget includes the pinned Python source copy and additions; two footprints
of the saved-size checkpoint (final payloads plus temporary serialization);
candidate/COMPLETE publication; atomic record headroom through the first next
THINK/ACT; small CPU payload/control files; and **2 GiB unallocated safety reserve**.
State envelopes use the larger observed COMPLETE/request plus 4 MiB growth.
This is a declared conservative estimate, not a measured GPU peak or reservation.
It does not fund an indefinite life. Available space fell from 1,875,496,960 bytes
at14:40:31UTC to947,650,560 at14:55:30UTC. Do not substitute root-reserved free space.
No cleanup/archive/coalesce was attempted. Main must resolve space and recheck it
before staging/dispatch; the preparer fails before creating its staging roots
if this budget cannot fit. Other users can still consume space after the check.

## Exact retained cut

`C0_CUT.json` binds the previously source-authenticated inventory; receiving
preparation must freshly hash/revalidate it, not assume it remains current:

- Actual raw root: `/localhome/local-rohing/orch_r216_C0_20260918_attempt2/raw`.
- Original namespace root remains
  `/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life`.
- COMPLETE6631: `c9d2aa785f44f81f80aa50b2dbcc04e734bc1f37c1c5743e73a32e12c9ccb587`.
- Pending request6660, sleep146; exact old UPDATE head6710:
  `ff9e7a71bba89d66b52b7457570f1751d6f0315dafea99ab8c0cbf416d5fb904`.
- Saved sleep145 optimizer **8412**; retain three pending rows and all48
  already-recorded unsaved UPDATE receipts. Run **48 new updates**, not zero or a
  remaining suffix, ending at8460, with separate recovery-compute attribution.
- Saved optimizer/RNG hash:
  `6e554cdf084ac3a9141f587e594361befb6bedae41ab50d0a9ce8e49a56f4ac4`.
  Adapter/COMMIT pins are in the cut. Receiving checks all payload bytes.
- **Unsaved post-generation/training RNG is lost.** Restore durable checkpoint
  RNG only. No bitwise resident-continuity, same future weights, or recovered
  missing tensors claim. The old failed sleep146 checkpoint stays untouched.

## Executable seam

`c0_pending_entry.py` is an addition loaded through the **preserved original
`r233_node2_recovery` wrapper → `r205_runtime` → original guard.native_entry**.
It uses original device/namespace confinement and privileged admission. The
wrapper's MODULE binding is explicitly propagated through both supervisor child
commands; only changing the outer runtime MODULE would not be sufficient.

After exclusive WRITER acquisition, the copied COMPLETE-tail reader hashes all
retained raw records and intent pairs, decodes the exact COMPLETE and semantic
tail using original journal transitions, retains the pending state and validates
the correction-ledger sidecar. Ordinary historical bodies are **not JSON replayed**.
Prefix INBOX records are decoded to retain delivery state. Raw I/O is still linear
in retained bytes; it is not a constant-time or zero-I/O restart claim.

The wall-compatible copied kernel restores the saved child, finishes the full
pending sleep into a uniquely named new checkpoint, publishes one COMPLETE and
one original-shaped `R184_LEARN_COMPLETE`, then publishes LOADED and a source-bound
startup receipt. It passes those same resident child/stream objects into the
**original `run_loop`**, rather than replaying old generations/tools or birthing
an empty stream. Failure consumes the durable attempt claim. A failure between
COMPLETE and paired LEARN needs explicit reconciliation; it never retries sleep.

There is **no Astra7 partial-intent dependency**. A partial appearing in C0 is
strictly rejected, not ignored, unlinked or reconciled by this candidate.

## Original plan versus execution location

Original PLAN bytes and authorization are immutable and hash-checked by the
existing wall compatibility code. Deadline stays **1789927200 = September20,
2026 18:00 UTC**; lease, original authorization scope and namespace stay fixed.
No new extension event is emitted and no authorization field is removed.

The separately bound execution PLAN has precisely two *location* deltas:
`source_root`, and `startup_context.path` relocated under that source root with
the **same bytes and SHA**. The real original validator requires the startup
file to reside under the execution source root; changing only source_root fails.
All prompts, training settings, GPU, root, deadline, lease and authorization stay
equal to the original. Both PLAN hashes and the path mapping are in the manifest.

The execution source consists of the entire unchanged original Python closure
plus **six new modules**; no original module is patched on disk. A new control
directory holds execution PLAN/GUARD/allocation/receipts, never replacing originals.
`SOURCE_DELTA.json` describes the local candidate; the preparer writes an exact
receiving SOURCE_DELTA with both PLAN hashes and source closure.

## CPU evidence and its limits

Run `python3 -B run_cpu_tests.py` from this directory, or use its repo-relative path.
See `HANDOFF.json` for the final test receipt and synthetic trace paths/hashes.

- Real copied original wrapper/native-entry/driver functions, original native
  PLAN validator and journal transitions run with a **synthetic child**, journal,
  checkpoint and optimizer/RNG payloads. The unchanged raw observed C0 PLAN is used.
- Full chain tests reach original THINK/ACT after48 new synthetic updates,
  paired LEARN and LOADED. Failed artifact bytes/inode and prior records survive.
- Wrong source/authorization/deadline/GPU, changed head, missing intent, partials,
  missing admission, occupied WRITER, corrupted prefix, tail overflow and failed
  checkpoint/LEARN publication reject. Original nonroot/stale/busy/wrong-device
  admission rejection is exercised. Original full source/lease/allocation
  validation is also exercised separately with synthetic filesystem receipts.
- Native-chain tests mock the outer `guard.validate` host/source environment
  boundary; actual original `native_entry` admission predicates still execute.
  OS namespace/process operations, tokenizer/anchor inventory and training are
  simulated. The next original driver cycle stops just after its first ACT.
- Fixture indices/hashes are synthetic; they are not live6631/6710 receipts.
  The live preparer requires the real cut. Full-fixture semantic replay tests
  remain regression tests, **not the production restart algorithm**.
- Preparing/finalizing a real receiving tree and real host/lease/admission have
  **not** been performed. This is CPU integration evidence, not receiving readiness.

## Narrow next action for Main

1. Review these exact bytes and the raw-plan/source-location mapping.
2. Resolve node2 owner-available storage without changing/deleting this retained
   state; obtain a fresh capacity cut. This workstream performed no such action.
3. Follow `RECEIVING_COMMANDS.md`: unique source/control staging, receiving CPU
   tests, truthful publication/allocation receipts, then original guard validation.
4. Only after Main's separate live review may the original privileged admission
   and confined dispatch run. The finalizer does **not** dispatch anything.
5. Inspect new COMPLETE→paired LEARN→LOADED→REQUEST/ACT receipts and rebind the
   parent only to the actual live incarnation. Recheck storage for continued life.

No commit/push, native or parent action is part of this handoff.
