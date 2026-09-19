# Epoch4 sealed offline handoff — September 19, 2026 02:56 UTC

**LOCAL_PREPARED_CPU_TESTED_NOT_ADMITTED.** Non-material repair within the
explicitly authorized checkpoint/tail/source scope. No native/parent signal,
reservation, transport, namespace entry, privileged/service action, model load
or GPU dispatch. No real new-native admission claim.

## Frozen artifacts and results

- `prepared_epoch4_v1/{curriculum_learner,curriculum_frozen_sibling}/epoch4/source`:
  211-Python-file closures; files 0444 / directories 0555.
- Per-arm `EPOCH4_SOURCE.json`: every exact source hash, original-to-new and
  epoch3-to-epoch4 allowlists, original identities/assets and deadline.
- Per-arm `cpu/LOCAL_SOURCE_CPU.json`, `cpu/SOURCE_TESTS.{stdout,stderr}` and
  `cpu/prefix/PREFIX_TESTS.{stdout,stderr}`: actual local-source synthetic tests.
- `prepared_epoch4_v1/operator_prefix_producer`: separately pinned v4 CLI,
  helper and port provenance. Producer not in child source and never invoked
  on real journals here. Each staged source needs a FRESH proof.
- `operator_bundle_v4/MANIFEST.json`: complete tested operator closure and
  standalone source-test dependencies. SHA256
  `a6a62f8d498d5a6a84b66443e72324293dd2d5d149e72592433023eadb9ab781`.
- `PREFIX_CPU_RECEIPT_v1.json`: SHA256
  `1b1d7b0f2d119b12c36ffd682f414b819c1dd30112e79670cde6f88b97047e84`.
- Dated local Builder provenance exists in the prepared epoch and bundle.
  Old sealed epochs/bundles are untouched. `epoch4_cpu_trial_01` is retained
  failed-development evidence, NOT a candidate.

Executed tests (all PASS):

| Suite | Tests | Unittest / process seconds |
| --- | ---: | --- |
| Worker/operator discovery | 75 | 1.533 / 1.680 |
| Unchanged boundary discovery | 83 | 0.210 / 0.329 |
| Learner exact source baseline | 14 | process 1.202 |
| Learner exact source prefix | 19 | process 70.296 |
| Frozen exact source baseline | 14 | process 1.476 |
| Frozen exact source prefix | 19 | process 70.579 |

Prefix tests deliberately wait the actual v4 3-second metadata quiet age per
fixture. These suite runtimes are NOT reserved-preflight timings. Coverage:
forward A→B COMPLETE, INBOX preservation, raw extension/tail parity, mutation,
source/epoch identical-byte inode replacement, cloned-journal rejection,
changed namespace only under original admission, reboot rejection, B-clause/
CPU-evidence tampering, writer lock, expiry, no retry/fallback and parent gates.

## Exact source delta, same for both arms

The five-file epoch3 delta is listed with exact before/after hashes in each
`EPOCH4_SOURCE.json`. Two files added, three existing files changed:

| File | New SHA256 |
| --- | --- |
| `gpu/checkpoint_tail_runtime.py` | `4e7746a8da7f99cb0354beb8d489a92e8fcb387e1409256901d1a9b0a033803c` |
| `gpu/immutable_prefix_proof.py` (added) | `ce5542e08f463cac4d795100bdc409480b4aef162632dc2aa6642bed9d08960b` |
| `gpu/pair_prefix_authority.py` (added) | `26570ad4df4fe9ee3e8fe4801b30e0baba31d3643aead076c15008bff97b23bf` |
| `gpu/pair_retention_runtime.py` | `fc038ad7e727f15a11cff74c3b5ebfeee81d912b09a98f8949e7941f9d4f1504` |
| `gpu/r205_runtime.py` | `119a8f409a31f9b1d21366b3d398d5a68dd16172b800e2e70c30929945b55468` |

History remains `8d44b45941228b229340a1546d3bf984965b0f9d2acfab12967c829d48f16315`.
Deadline remains **1790791200, September 30, 2026 18:00 UTC**. Original r232
binding, management admission, confinement and writer-lock-before-model remain.

## Safe node source tests

After MAIN stages/verifies source and operator bundle, set `BUNDLE` to the
directory containing that exact bundle's MANIFEST.json. No repository checkout
or peer installation is required. These commands create only disposable local
synthetic journals and never inspect either real pair journal:

```bash
: "${BUNDLE:?set main-verified operator_bundle_v4 directory}"
TOOLS="$BUNDLE/research_loop/workers/post_recovery_pair_retention_receiver_20260919"
SOURCE=/localhome/local-rohing/orch_retention_20260919/curriculum_learner/epoch4/source
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 python3 -B "$TOOLS/source_checks.py" --source "$SOURCE"
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 python3 -B "$TOOLS/prefix_source_checks.py" --source "$SOURCE"
```

Repeat with `curriculum_frozen_sibling`. Required test files together:

- `source_checks.py`: `1f1c96fa6fcdd25ce99e96bc0737440f2b4ff929de49fdef214debf5bea105a9`
- `prefix_source_checks.py`: `cedec6e4d19950ddf5c66ab68ed3a6742da7d972c5bb28f1cceac8183b3b4f70`

The preparation command used was:

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 python3 -B research_loop/workers/post_recovery_pair_retention_receiver_20260919/prepare_epoch4.py --output research_loop/workers/post_recovery_pair_retention_receiver_20260919/prepared_epoch4_v1
```

It now refuses that existing output. Use a new own-worker directory to reproduce;
never overwrite a sealed epoch. Regression commands are recorded verbatim in
PREFIX_CPU_RECEIPT_v1.json. `cpu_probe_prefix.py` is standalone alongside
`cpu_probe.py`, with runtime imports from exact source. Neither of its modes
is a live authorization or source test; real candidate use requires main's
complete authority/admission chain.

## Single canonical v4 integration

`prefix_receiver.build_prefix_operations(...)` constructs the receiver and
operations, without activation. All seven hooks remain. It reuses the current
optional reserved coordinator, bounded original-owner bridge and distinct
main-pinned execution digest. Old default behavior/source remains unchanged.

`prefix_authority.load_authority` defines the strict approval schema: exact
life/epoch/source, producer+receipt/proof, selection policy/caps, deadline/control
and original confinement digest. Explicit mode:
SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE. Explicit permitted derivation:
EXACT_B_AND_PREAPPROVED_CAPS_IN_ORIGINAL_CPU_ALLOCATION_GUARD_V1.
The producer CANDIDATE cannot grant approval. Control templates lack real
proof/identity/approval deliberately and cannot be admitted.

The candidate flow adds only `pair_prefix_admission`, `pair_prefix_selection`
and `pair_prefix_cpu_parent` to an unchanged original tested CPU receipt. The
canonical Kuhn clause binds selected B and its already approved caps; no mode,
source/path/proof authority is invented. Allocation pins derivative CPU; guard
pins allocation. Original guard validation precedes tail scan. Startup repeats
the original validation and independently reconstructs the exact derivation.

Both scans receive only canonical `prefix_proof={guard_path,guard_sha256}` and
`prefix_admission={path,sha256,field_path:["pair_prefix_admission"]}`. The
provisional NamespaceAdmission adapter is deleted. Missing original-chain
authority or an arbitrary guard field refuses. Same original objects and boot
remain mandatory, full raw A→B/B→head is verified, and arriving INBOX remains.
Host and consumer namespaces are recorded, not assumed equal. No journal clone
is admissible. Default helper mode remains SAME_MOUNT_NAMESPACE.

Saved-payload proof still precedes destructive commit. PRESERVATION is published
only after exact tail/state proof. Owner, source, identity, durability and guard
checks remain; observation expiry resumes the same handle, never dispatches.

## Remaining main-owned gates

1. Verify staged epoch4 bytes/FS identities and produce fresh per-arm proofs
   after final file ownership/modes and quiet age. Explicitly pin the complete
   authority. Reported C2 evidence is separate, not either pair epoch4 proof.
2. Verify actual original receiving admission/confinement/management route.
   Host observer / old-native FS-view equality does not by itself establish
   `actual_confined_prefix_route_CPU=True`. The reserved static gate requires
   bound real-route evidence; no privilege workaround is supplied here.
3. Bound the WHOLE reserved operation: saved payload, metadata/tail, source,
   guard, repeated owner RPC, fsyncs and margin. Reader timings alone are
   insufficient. Reservation stays **≤30s**. Expiry/failure leaves a durable
   review gate, no blind repeated attempt or replay fallback. Prehash is still
   O(prefix bytes) outside the cap; rechecks are O(prefix metadata + new tail),
   not O(1) and not a guaranteed live latency bound.
4. Kuhn's actual effective fence/zero-inflight/original-ledger dependency must
   bind this old native and epoch4. Original CPU-host `verify_fence` is checked
   via the unchanged bounded owner bridge; copied receipts/ledgers do not count.
5. Only after actual LOADED and durable RETENTION_SOURCE_ADOPTED: separate
   owner approval/rebind to exact new pid/start/boot/guard. The receiving
   PARENT_REBIND_REQUIRED.json exposes this pending contract. No automatic PID
   adoption, duplicate message replay or ledger reset. Main keeps the original
   parent registry disabled while fenced.

New task code: `prefix_authority.py`, `prefix_ports.py`, `prefix_receiver.py`,
`cpu_probe_prefix.py`, `prefix_source_checks.py`, `prepare_epoch4.py`,
`package_prefix_operator.py`, `test_prefix_receiver.py`, `test_prepare_epoch4.py`.
No shared/C2/history/coordinator/parent-owner code was edited by this task.
