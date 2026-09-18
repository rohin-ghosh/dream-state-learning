# Node5 insurance references — September18,2026 03:43 UTC

**No evacuation at04:00.** Rohin confirms node5 through **September21,2026 21:04PDT = September22,2026 04:04UTC**. This is user-confirmed; this operator has not independently read a provider CLI extension receipt and made no purchase. Existing native runtime wall values are recorded, not extended by this manifest task.

No emergency relocation/04:00 timer was ever armed by this operator. The prior original-only R205 pause watcher3196822 was cancelled at03:41:32.918UTC, with zero native or parent signals; it is absent at03:43:36.878UTC. C2 native3179563 and Astra2600320 continue. Do not use historical R205 ARMED.json as current status.

## Artifact Main should use

`NODE5_20260918T0343Z.json`

- Full-file SHA256: `8cbf8f5b3e4a2a32eb256c5ad092bcc1de9ec22169020e5d33f97a6dc81db6db`.
- Internal canonical manifest digest: `bdc11b4c6b22aaabfbb7c5474b921712e34354ed34e98085b9b2f299349cdd64`.
- Captured03:43:08.739–03:43:13.875UTC, host **[REDACTED_HOST]**, via `bash gpu/ovx3_ssh.sh`.
- Eight live PID/start-tick bindings, exact physical/logical roots and process mount proof; latest COMPLETE/COMMIT, adapter/optimizer/RNG file hashes; separately pinned current committed context/working state; finite journal prefix heads and inbox hashes; source closure, guard/plan/allocation/old lease references.
- All eight complete-record/COMMIT comparisons, adapter/optimizer/RNG hashes, process-view/storage matches, and receiving source pins verified. No source-pin mismatches.
- **Main owns actual off-node transfer.** This operator transferred only the metadata manifest and cancellation receipt, not model/checkpoint/journal archives. Main's copy completion is not claimed here.

## Physical copy roots and finite cuts

For each root the exact COMMIT is `checkpoints/sleep_NNNNNN/COMMIT.json`; the manifest supplies its full path and SHA256.

|GPU|Life / native PID|Physical host storage root|Latest complete / AdamW|Bounded journal head|
|---|---|---|---|---|
|0|C1 /2707975|`/localhome/local-rohing/orch_r153_community_C1_20260916_attempt1/life`|72 /6007|7227 UPDATE|
|1|C2 /3179563|`/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life`|54 /5068|6176 UPDATE|
|2|run1 /2495635|`/localhome/local-rohing/orch_r125_continual_20260916_attempt1/run1`|84 /6970|8192 SLEEP_COMPLETE|
|3|C3 /2668022|`/localhome/local-rohing/orch_r153_community_C3_20260916_attempt1/life`|67 /5359|6496 UPDATE|
|4|C4 /2606742|`/localhome/local-rohing/orch_r153_community_C4_20260916_attempt1/life`|68 /5325|6432 UPDATE|
|5|C5 /2761060|`/localhome/local-rohing/orch_r153_community_C5_20260916_attempt1/life`|81 /5981|7247 SLEEP_COMPLETE|
|6|pilot /2757295|`/localhome/local-rohing/orch_r127_pilot_20260916_attempt1/run1`|73 /6407|7496 SLEEP_COMPLETE|
|7|repo_reader /2761360|`/localhome/local-rohing/orch_r136_repo_reader_20260916_attempt1/recovery_r154_saved30_20260916_attempt2/run1`|70 /6069|7129 UPDATE|

**repo_reader is the sole namespace alias:** its live process binds the physical storage above onto logical `/localhome/local-rohing/orch_r136_repo_reader_20260916_attempt1/run1`. This is **not a symlink**. The host-visible logical root is stale at checkpoint30; do not copy it as the current life. All seven other logical roots match physical storage.

## Restore semantics

The exact source/root/control references are under each row's `restore_source`. Preserve the listed complete checkpoint with its matched complete-state envelope. Preserve the separately bounded later journal/context/inboxes as evidence; do not silently pair an old completed adapter with a newer in-flight training state and call it exact live continuation. Include only record and matching intent indices0 through that row's fixed head; do not sweep an unbounded growing directory or include a later orphan intent. Preserve the manifested inbox source bytes without republishing them. A destination must bind its actual GPU/UUID, namespace aliases, CPU tool gate, wall, and lease; node5 guards are source references, not authorization to launch unchanged on node3.

C2's context cut is COMMITTED6145 separately from COMPLETE54/6122. Live resident sampling RNG is not claimed captured. Previous source52 retained real learning including corrupt exposure; no rollback, retroactive unlearning, or repaired-weight claim.

## Clone ownership and console work

At03:43:36.878UTC all six clone receiving roots still have **zero matching processes** and no retirement/launch/READY receipts. This operator remains frozen on GPUs0/2/3/4/5/6; Copernicus can receive them without a race. No clone claim/execution IDs were issued here. Full roots and unfinished receiver caveats: `../COPERNICUS_NODE5_FROZEN_HANDOFF.md`; authoritative assignment bindings: `../R203_SCALE_ASSIGNMENT.json`.

Original C2/GPU1 stays with this operator; repo_reader/GPU7 remains protected. No human inbox writes. Rohin retry637c5468 remains unanswered by6063; next real retry remains Fable-owned after Main's dedicated console-ACT overlay is verified live. Console patching did not displace this manifest task.
