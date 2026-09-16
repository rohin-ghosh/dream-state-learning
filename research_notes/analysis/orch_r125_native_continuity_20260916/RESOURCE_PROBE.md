# R125 resource sidecar — resident first, read-only

September 16, 2026; observations 05:43–05:53 UTC. Corrected scope: **one
continuous CHILD inference GPU plus four experiment GPUs**, not a skill study.
No sizing expansion, allocation, reservation, launch, signal, source edit, Git,
or shared-ledger write. Only this document is owned by this sidecar.

## Resident: ovx3 physical2

**Best requested resident candidate:** physical2,
`GPU-d62ba12e-ff08-9e5e-ba35-14c723f6e05b`, kernel device minor **2**.
At **05:51:13 UTC**, privileged existing scanner: `clear=true`, no blocking
reasons, zero target compute processes, 1 MiB / 0% utilization. All-UID `/proc`
inspection covered 83 processes. Only the identity-verified persistence service
PID2988 opened the target device, with CVD unset; no application target owner.
This is stronger than a momentary empty-memory observation, but expires as
other work can start. Main must perform fresh admission immediately before use.

**Node-local paths, ready for Main's separate runtime preparation:**

- Qwen2.5-7B-Instruct:
  `/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28`
  exists with four safetensor shards. Presence checked; this probe did not
  rehash the approximately 15 GB weights or load a model.
- Broad42 anchor root:
  `/localhome/local-rohing/orch_r107_base_anchors_20260915_attempt1`.
  `ANCHOR_MANIFEST.json` SHA256
  `2ad09dbe9673f95cbe92cd41e70d83635702b615fb7295b8b3f850e9ee674753`;
  `ANCHOR_ROWS.json` SHA256
  `c7e70846fa8adf18555b793912acf5dc85c53cc0fd1905f61501d295ef91d264`.
  Actual row count42 and row-file hash match; manifest status
  `VERIFIED_ANCHOR_MANIFEST_READY`, before/after verified, adapter null, held
  false. `readout/COMPLETE.json` says COMPLETE,64 calls, matching manifest hash.
  Metadata/hash verification only here, not fresh native-token/scorer replay.
- Existing immutable scanner dependency source:
  `/localhome/local-rohing/orch_r142_base_reasoning_20260916_attempt1/source_r142_v1`.
  This is reusable **scanner source**, not a proposed R125 runtime or permission
  to invoke the historical R142 guard/producer.
- Existing valid persistence-service identity:
  `/localhome/local-rohing/orch_r142_base_reasoning_20260916_attempt3/run1/SERVICE_IDENTITY.json`,
  SHA256 `b85ed1ceebccf0526a4c8770a01d75d3e8e44ee42b29a017bece7ff5d572fda5`.

## Requested experiment slots

| Role / candidate | UTC scan | Memory / utilization | Kernel minor | Privileged ownership result | Availability qualification |
|---|---|---|---:|---|---|
| Resident ovx3 physical2 | 05:51:13 | 1 MiB /0% | 2 | Clear;0 compute owners | Candidate now; new Main plan and fresh gate required |
| Experiment ovx3 physical6 | 05:51:13 | 1 MiB /0% | 6 | Clear;0 compute owners | Candidate now; no reservation granted here |
| Experiment ovx3 physical7 | 05:51:14 | 1 MiB /0% | 7 | Clear;0 compute owners | **NOT available:06:00 FINAL custody persists** |
| Experiment a40r physical0 | 05:48:43 | 0 MiB /0% | **3** | Clear;0 compute or target-FD owners | Candidate now; not `/dev/nvidia0` |
| Experiment a40r physical2 | 05:48:44 | 0 MiB /0% | **1** | Clear;0 compute or target-FD owners | Candidate now; not `/dev/nvidia2` |

All successful scans had EUID0 and empty blocking lists. ovx3 physical6/7 had
only the verified persistence service opening the target, CVD unset. a40r scans
covered92/88 processes respectively. No visible current life was displaced.
No a40r FINAL/timer/custody keyword process was found in the supplementary
all-UID check; bounded current plan-metadata inspection found no new physical0/2
timer assignment. This is not a global future-reservation guarantee.

Experiment UUIDs:
- ovx3 physical6: `GPU-67a989f7-2660-a76b-40e8-3619b9fa2987`
- ovx3 physical7: `GPU-9e6cdf73-7181-4405-2aec-787cc73a3e5b`
- a40r physical0: `GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d`
- a40r physical2: `GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8`

The a40r model exists at the same snapshot path, four shards; config SHA256
`7463bb0ea78315365e6c6b74de4e73bbcc8359dfb0c5a737584e077d42c0b03c`.
Its byte-identical broad42 copy is at
`/localhome/local-rohing/orch_r109_l1_20260915/input/anchors`, with matching
manifest/rows hashes,42 rows and bound COMPLETE64/before-after evidence.
**Relocation caveat:** that manifest still names the original absolute anchor
root, which is absent on a40r. Do not rewrite the manifest or assume the strict
original-root inventory loader accepts this relocated copy. ovx3's original-root
copy avoids that issue; Main owns any separately validated experiment loading.

## Reservation and lease references

**ovx3 physical7:** verified unchanged plan
`/localhome/local-rohing/orch_r115_grid_pair_20260915/A4/final_20260916T060000Z_r119_v1/PLAN.json`,
SHA256 `2508596564302bb3cd783d02fb113aa4f71d30d59c8910ba33cdb7bb14924f0f`.
06:00 trigger,06:10 boundary deadline,06:20 evaluation ceiling; source describes
**same-life TRAIN resumption afterward**. Therefore neither R142 completion nor
06:20 by itself frees this slot. Require actual FINAL disposition, custody
clearance and fresh ownership admission; no existing life may be displaced.
Only three of four requested experiment slots are presently resource-clear
without this known reservation condition.

ovx3 lease reference, reached through that pinned timer plan's `budget`:
`/localhome/local-rohing/orch_r115_grid_pair_20260915/A4/independent_r119_recovery_v2/LEASE_BUDGET.json`,
SHA256 `287e36bc9b646401f5382b06c8bda4e71748a5f94d6eb011d436c1ead7b246a5`,
hash checked. Lease end **September17 04:04 UTC** (`1789617840`), existing
six-hour-margin hard wall **September16 22:04 UTC** (`1789596240`). No extension
inferred from wrapper comments. R142 GUARD uses22:04 as its conservative
`lease_end_unix` bound; do not confuse that field with the actual lease expiry.

a40r lease reference:
`/localhome/local-rohing/orch_rich_hot_node1_20260915_attempt1/LEASE.json`,
SHA256 `ac20665cb03ba0e2f8eebb0f7e441383334fbbf20b4a4e7125757ce7413ea8e6`.
Conservative date-only expiry **September19 00:00 UTC**,21600-second margin:
hard wall no later than **September18 18:00 UTC**. No extension/onboarding.

These clocks leave more than60 minutes for resident2 and the three unreserved
experiment candidates, conditional on Main's allocation and fresh admission.
This is a lease-headroom statement, not an exclusive hour-long reservation or
a promise of continuous availability. No such hour is claimed for physical7.

## Exact fresh resident admission command

Reusable API: `gpu.orch_r111_route_admission.scan(index, service_path)`;
its frozen R110 reconciliation + minor-aware all-UID scanner preserves CVD,
UUID, compute-owner, process-identity and actual `/dev/nvidia<minor>` FD gates.
R111 accepts the documented one-MiB idle baseline; it does not waive ownership.
The in-memory policy below binds only resident2; it does not edit any source or
reserve the device. It emits compact metadata, not raw process environments.
This command is read-only and is **not** a launch command:

```bash
bash gpu/ovx3_ssh.sh 'sudo -n env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r142_base_reasoning_20260916_attempt1/source_r142_v1 python3 -B -' <<'PY'
import hashlib
import json
import time
from pathlib import Path
from types import SimpleNamespace
from gpu import orch_r111_route_admission as admission
minor = admission.original.minor
def require(value, message):
    if not value:
        raise ValueError(message)
def allocation(index):
    require(index == 2, 'resident2_only')
minor.pinned.policy = SimpleNamespace(
    HOST_SHA='0cb7eb43862102b79ae0a30d2babfedfbf9598b31967a1a04122c3cf849c746d',
    DEVICES={2: 'GPU-d62ba12e-ff08-9e5e-ba35-14c723f6e05b'},
    require=require, allocation=allocation)
service = Path('/localhome/local-rohing/orch_r142_base_reasoning_20260916_attempt3/run1/SERVICE_IDENTITY.json')
require(hashlib.sha256(service.read_bytes()).hexdigest() ==
        'b85ed1ceebccf0526a4c8770a01d75d3e8e44ee42b29a017bece7ff5d572fda5',
        'pinned_service_bytes')
report = admission.scan(2, service)
print(json.dumps(dict(observed_unix=time.time(), clear=report['clear'],
    scanner_euid=report['scanner_euid'], gpu=report['gpu'],
    device_minor=report['device_minor'], blocking_reasons=report['blocking_reasons'],
    report_sha256=hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest())))
require(report['clear'] and report['scanner_euid'] == 0, 'fresh_admission_required')
PY
```

Main must pin the following scanner bytes and its new runtime/config separately.
Do not invoke R142's historical guard to admit R125, fabricate a persistence
receipt, reinterpret a rejected report, or replace current ownership gates.

| Scanner file | SHA256 |
|---|---|
| `orch_r111_route_admission.py` | `c79f08d18eb2dd989b13555b90ad289d98937c8662b9c01cc1899d80429228b1` |
| `orch_r110_admission.py` | `91027037bf98aa391afe5d89da9814502da57d6b15ad16574b2a7cdef9976c3f` |
| `orch_rich_hot_a100_minor_scan.py` | `f7136608f4b3fca051b3852a006abf86b704dbf1cfe882f6b8c3b43704ec387e` |
| `orch_rich_hot_a100_scan.py` | `9902c38ecadeaa06bc02abf184f6a04025a289868f809b63aace5148cd95575e` |
| `orch_math_replication_guard.py` | `389521b8a291292c386fd874faa40ff8767b38da8e088985f6f6659e5f971ac2` |

a40r's already-tested scanner source is
`/localhome/local-rohing/orch_math_feedback_uptake_r122_oldfleet_source_20260915_v1`;
use `gpu.orch_r110_admission.scan` with the same last four pins, its own
hash-host binding `e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b`,
and its existing validated service record
`/localhome/local-rohing/orch_r126_code_capacity_20260915_v3/a40r_4/SERVICE_IDENTITY.json`.
Bind only the exact target index/UUID above; never assume physical index equals
kernel minor. Raw process reports and anchor content remained node-local;
only compact hashes/counts/metadata were returned. No node files were written.

## Compact scan evidence and superseded candidates

SHA256 of sorted-JSON full reports computed on-node, without exporting them:

| Slot | Report SHA256 |
|---|---|
| ovx3 physical2 | `416ac3869598d761924d1a6be9d5a5c6a36e87031eb7672bbbd73cb4483adea7` |
| ovx3 physical6 | `3a34103983c25b170c33f17fe691bbbe1b987c4c38152195681f699d13571db9` |
| ovx3 physical7 | `779e566d486ae93ee99fefe546649d3712b29ee0e2ff51ea59d1937eb7c9b858` |
| a40r physical0 | `3746f198bb55e7c0226794aed9102f1f14fe1445f3337187745689701a722f96` |
| a40r physical2 | `b3c49d6d7992d357e1385ba7173d26b9ef769e8bdd2dffd6bbf7b3e3f18ae9c9` |

Prior work reused, not repeated: A100 physical1 was empty05:43:48 but occupied
at05:45:11,30325 MiB/75%, PID3663649 with matching UUID CVD, compute record and
target-device FD. **Excluded**, no process touched. ovx2 physical2 passed at
05:47:39 (1 MiB, no compute/application owner), but is not part of the corrected
resident+experiment proposal. An initial ovx2 scan failed before admission
because an old service record lacked `boot_id`; the subsequent successful scan
used an existing complete service record, without modifying either or any gate.
