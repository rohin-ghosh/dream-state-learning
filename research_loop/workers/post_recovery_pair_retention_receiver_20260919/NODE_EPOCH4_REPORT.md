# Pair epoch4 — actual ovx4 staging and CPU evidence

September 19, 2026. Final original-native verification: **03:14:44 UTC**.
Scope completed: main-authorized new-path staging, exact-source tests, actual
saved-checkpoint CPU verification, own production-source prefix production,
full read-only diagnostics and existing-native filesystem-view checks.
**NOT receiving admission, current-boundary eligibility, or source adoption.**

## Staged, original sources preserved

Both declared `/localhome/local-rohing/orch_retention_20260919/{life}/epoch4/source`
closures contain the exact sealed 211 Python files plus unchanged context asset.
Operator closure: `/localhome/local-rohing/orch_retention_20260919/pair_operator_bundle_v4`.
Producer closure: `/localhome/local-rohing/orch_retention_20260919/pair_prefix_producer_v4`.
No existing destination was overwritten. A second staging pass verified the
identical source/operator/producer directories and created only a new diagnostic
directory. Epoch1/2/3 and all earlier archives/diagnostics remain preserved.

Exact old native identity, source closure, original guard, plan, allocation,
lease bytes, journal ID/root and deadline were checked before/after staging,
around every diagnostic and again at the final inspection:

| Life | Original PID | Start ticks | Final state |
| --- | ---: | ---: | --- |
| curriculum_learner | 493500 | 10070880 | R, unstopped |
| curriculum_frozen_sibling | 471737 | 9987073 | R, unstopped |

Boot remains `7c130f24-3105-4909-abfb-b669929e0b96`.
Deadline remains 1790791200, September 30, 2026 18:00 UTC.

## Actual CPU results

| Measurement | Learner | Frozen sibling |
| --- | ---: | ---: |
| Exact-source tests | 14 baseline + 19 prefix PASS | 14 baseline + 19 prefix PASS |
| Selected historical COMPLETE | 7285 | 4022 |
| Saved optimizer steps | 4368 | 0 |
| Saved checkpoint CPU operation | 1.607s | 1.313s |
| Saved checkpoint whole subprocess | 2.016s | 1.720s |
| Own-prefix bytes hashed | 5,594,715,637 | 13,104,603,798 |
| Own-prefix records | 7,286 | 4,023 |
| Producer measured work | 10.297s | 24.674s |
| Producer whole subprocess | 10.594s | 24.965s |
| **Full read-only scanner** | **5.412s** | **13.447s** |
| Reader whole subprocess | 5.626s | 13.667s |
| Full new tail records | 41 | 34 |
| Full raw tail bytes | 102,274,792 | 217,201,041 |
| Reader record count | 7,327 | 4,057 |
| Pending preserved | sleep request | none in this observation |

These are full diagnostic tails, NOT one-LEARN-tail boundary timings or the
whole reserved-operation cost. Producer work occurred entirely outside any
reservation. Pending state was permitted for observation, never cleared.
Both actual saved checkpoint probes verified adapter, optimizer and saved
Python/CPU/CUDA RNG payloads and saved working-state binding, with no GPU calls.

Every observer explicitly initialized `recovery.frozen.INITIAL` from
`orch_r232_curriculum_frozen_20260918/raw/checkpoints/initial/COMMIT.json`, SHA256
`6af901f325aeb665b6b3cece5376a91bf41d99a2c3f11b038efef48dbe7731a4`.
The frozen proof/scan family was **gpu.r232_recovery:FrozenJournal**, not plain
StreamJournal. Learner used **gpu.r232_recovery:LearnerJournal**.

## INBOX, tail and sidecar evidence

- Learner preserved 78 prefix registrations plus **1 new tail registration**,
  yielding 79 registered INBOX messages. All 79 INBOX files observed around
  the scan retained exact bytes and filesystem identities.
- Frozen preserved 106 prefix registrations plus **1 new tail registration**,
  yielding 107. All 107 observed INBOX files retained bytes and identities.
- No additional INBOX file arrived *during* either timed scan; no artificial
  arrival was injected. The new registrations above are real post-prefix
  tail evidence, not a claim of arrivals within the timing interval.
- Current `correction_ledger.json` was absent for each arm; the explicitly
  checked selection and reader receipts both contain `sidecars: []`.
- Both receipts report full raw extension/tail verification, pending preserved,
  no prefix rewrite, no writer lock and zero journal writes. No `read_inbox()`
  writer/register method was called by the actual observers.

## Own source-bound production proofs — all full data stays on node

Active diagnostic root:
`/localhome/local-rohing/orch_retention_20260919/pair_epoch4_cpu_20260919_1789787359751234852`.
Each life has its own `PROOF.json`, `GUARD_A.json`, `PRODUCER.json`,
`PRODUCED.json`, full checkpoint request and detailed local logs there.

| Life | Own proof SHA256 | Canonical producer-receipt SHA256 |
| --- | --- | --- |
| learner | `9ebc26318bbe327fe36263226a5eb1a18ee1d81ecade280ef94b3d0815ae999e` | `f08455dc1cc85ead98dc279482dd92d87d19309ad09836f1038b88e4fd1e640b` |
| frozen sibling | `09f56a3b2ee50f40fa5e8c355ab6050cf5a86b83351652a50890258e1810586c` | `0cae2f7b60ac51fc10c729787af12b95b94f276949ab41e29e43bc5d85304d8b` |

PRODUCED.json preserves the actual producer result with
`status=CANDIDATE_NOT_AUTHORIZATION`; it is not a main approval.
Each proof binds that arm's declared epoch4 production source and newly pinned
SOURCE_EPOCH.json. No observer-source proof or C2 proof was reused. Full proofs,
real journals and full saved-state requests were **not transferred to the VM**.

## Existing native namespace evidence, not new admission

Old native `/proc/PID/root` reads verified 14,572 learner and 8,046 frozen
original prefix record/intent identities plus all 211 source hashes **twice**.
Those checks took 0.216s and 0.142s respectively. A supplemental two-pass check
also verified all **212 source+epoch filesystem objects** and all **8 immutable
source directories** against the proof in each old native's own view.

The timed scans used the default **SAME_MOUNT_NAMESPACE** host diagnostic mode.
They did not fabricate a cross-namespace original-admission clause. Existing
native view equality is additional evidence only: the original receiving
admission/management route and next consumer's own rechecks remain unproven.
No guard/CPU/allocation handoff authority was created or installed.

## VM receipts and implementation provenance

Small receipts are retained under:

- `node_epoch4_20260919T0305Z/`: first stage, passing node source tests, and the
  preserved initial selector refusal caused by a research_loop package-name
  collision. No native/source action resulted from that refusal.
- `node_epoch4_20260919T0309Z/`: exact-existing staging verification, successful
  SELECT/CHECKPOINT/PRODUCE/READ/NATIVE-VIEW results for both arms, final audit,
  and `INSPECT_1789787684318335533.json` (03:14:44 UTC).
- `node_epoch4_20260919T0309Z/FINAL_READONLY_AUDIT.json`: consolidated proof/
  producer references, INBOX deltas and supplemental old-native object checks.
  SHA256 `79e5a4f8b6624ca6e083ba0870aa9cc81a1d94a1a400958af136595ebffb5bdb`.
- `NODE_STAGE_CPU_RECEIPT_v1.json`: **82 worker tests PASS (2.398s)** plus
  **83 unchanged boundary tests PASS (0.288s)**. Includes seven new staging,
  path/mismatch, frozen-initialization, INBOX and package-shadow regressions.
  SHA256 `39a37ee79953b5c1a4a99167a70deb8b4baa225c264e7e5073ca808441ddb504`.

The selector repair loads the exact manifest-pinned operator boundary module
by filename, preventing the receiving source's unrelated research_loop package
from shadowing it. Only new diagnostic code changed; neither sealed sources nor
the prior node diagnostic code was edited. The corrected wrapper was staged
in a new directory, with its own CODE_PINS.json and archive receipt.

New task code files: `remote_epoch4_stage.py`, `node_epoch4_probe.py`,
`node_epoch4_driver.py`, `epoch4_node_runner.py`, `node_epoch4_finalize.py`,
`test_node_epoch4.py`. No shared coordinator, parent, C2 or sealed epoch edits.

## Remaining gates

Main must still pin explicit bounded prefix authority through the original
CPU/allocation/guard chain, verify the actual confined receiving/management
route, bind and measure the full <=30s reserved path (not just this reader),
obtain Kuhn's effective parent dependency fence, and separately approve the
post-LOADED owner rebind. No activation has occurred or is implied.

[Builder] 2026-09-19 03:14:44 UTC — Non-material, explicitly authorized pair
epoch4 staging/CPU diagnostics on ovx4 only. Exact production closures and
original live identities/source/guard/deadline verified before and after;
both actual saved checkpoints and source-specific prefix readers passed.
Full live data remains node-local. No native/parent signals, fence, reservation,
GPU/confinement dispatch, privileged/service operation, wall extension,
scientific-claim change, commit or push.
