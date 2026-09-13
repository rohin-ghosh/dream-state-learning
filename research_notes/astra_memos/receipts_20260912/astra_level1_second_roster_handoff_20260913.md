# SEQ146 EDITSTOP — complete12 evidence plus original frozen scorer replay

2026-09-13. All12 Main-collected cells copied, receipt-bound and archived. No pending cells. Node2 perception/self_reflection attempt1 and node1 repetition/meta_reflection attempt2 only. Original six A100 attempt1 missing-ninja failures are separately recorded, untouched and unscored here. Their payloads were not copied or freshly audited.

## Outcomes

| Skill | Held primary OFF→post seeds0/1/2 /48 | Strict OFF→post /48 | Canary OFF→post /12 |
|---|---|---|---|
| perception | 21→47,48,48 | 0→47,48,48 | 12→12,12,12 |
| repetition | 0→48,48,48 | 0→48,48,48 | 12→11,11,12 |
| self_reflection | 0→48,48,48 | 0→48,48,48 | 12→12,12,12 |
| meta_reflection | 9→48,48,48 | 9→48,48,48 | 12→12,12,11 |

Perception records16/24→23,24,24/24; abstentions5/24→24/24 each. Seed0 sole post error: scalar try rather than integer triple, despite exact JSON serialization. OFF44 fenced+4 unparseable; post48 exact each. Full field-error/availability counts retained in JSON/MD.

**No blanket no-harm:** repetition0/1 each return {"answer":"rehearse"} for {"answer":"rehearse? wait"}; meta_reflection2 returns malformed {"answer":241"} instead of {"answer":241}. Three measured canary regressions, zero held content regressions. No outcome-based seed selection or tuning.

Self-reflection OFF47 fenced+1 unparseable, post48 exact each. Repetition and meta held outputs exact before/after, showing content/format separation. Every self-reflection and meta score file matches Main’s supplied pin.

## Archive scope and verification

Four fresh, separate tar files preserve existing archive bytes. All12 full roots, actual adapters, collected directories, driver logs/results, once-only claims, launch directories, batch starts, pinned specs/runtime/helpers/source archived. Frozen base-weight payloads and installed dependency payloads not copied or newly audited; their saved bindings preserved.

Native guards retain exact roster/precheck/boot/UID/node/cell/device/plan checks, original controller absence, no failure receipt, completion120calls/unscored marker, successful collection-result and one-shot claim, plan/completion/score hash agreement. Source fingerprints and membership stable through hashing, tar creation and native payload verification. On VM, entire tar hashes plus every member hash/size/type/exact listing verified; no extraction. Actual adapters checked against score file identities and plan input hashes checked against manifests.

Total3496 file instances/3604 members/104 priority-copy file instances across archives (shared roster/start receipts intentionally repeat by snapshot). All PASS. Previous3/6/9-cell JSON snapshots keep their exact original pins; corresponding MD and handoffs preserved when available.

## Commands and validation

All authored helpers live beneath `/tmp/astra_level1_second_scores_20260913/`. Native snapshot variants `copy_snapshot.py`, `copy_snapshot_node1.py`, `copy_snapshot_self_reflection.py`, `copy_snapshot_meta_reflection.py` run via existing `bash gpu/ovx_ssh.sh` or `bash gpu/a40_ssh.sh` with `python3 -B -` and source on stdin. They read existing scores/metadata only; never collect.

Native archive variants `archive_worker.py`, `archive_worker_node1.py`, `archive_worker_self_reflection.py`, `archive_worker_meta_reflection.py` ran once via the same wrappers as `python3 -B - NODE DESTINATION`. Destinations are fresh native_archive/node1_native_archive/self_reflection_native_archive/meta_reflection_native_archive under the owned native /tmp directory. Root/source snapshots never receive writes. Native stdout/stderr receipts preserved. Tar, listing and manifest transfer used read-only `cat` through SSH.

Local validation/reduction commands, each using already-scored data only:
- `python3 -B /tmp/astra_level1_second_scores_20260913/analyze_verify.py` (initial perception).
- `python3 -B /tmp/astra_level1_second_scores_20260913/extend_repetition.py`.
- `python3 -B /tmp/astra_level1_second_scores_20260913/extend_self_reflection.py`.
- `python3 -B /tmp/astra_level1_second_scores_20260913/extend_meta_reflection.py` (reverified all four archives).
- Final independent12-cell assertions PASS: counts/content/strict, native/supplementary field denominators, exact three canary regressions, 320updates/1280presentations per fit, Main pins, no pending, six separate A100 originals, all archive cardinalities and partial JSON pins. `final_validation.json` records the result.

Exclusive snapshot outputs prevent overwrite; do not rerun reducers into completed destinations. Main-facing analysis replacement used apply_patch only after preserving partial snapshots. Initial local reducer error on non-JSON canary was repaired by split handling; transient patch-size/hunk-format errors left evidence unchanged. No native collection or scoring-function retry occurred during evidence copying/reduction. The later explicitly authorized original-protocol CPU replay is documented below.

## Original frozen scorer replay — SEQ146 PASS

All1440 exact archived responses/material rows replayed through the original frozen material.score_row functions:1440/1440 complete score objects and48/48 panel summaries exactly match the saved originals; zero mismatches. This covers content/strict/format and all saved per-field/error diagnostics, not just totals. Completed in13.478567seconds. No dependency blocker and no model-framework import.

Original scorer pins: perception/self_reflection4648f8542b1babb10f6ffda4bf023024d71b8c9834a32e2242a7f064a94a8941; repetition/meta498e841af8c65654b3f090a1c9f951b6d0aa0e040fd3d757d320f69cba007700. Exact archived source dependencies staged locally; original supported ASTRA_LEVEL1_SOURCE_ROOT binding points to those copies. No monkeypatch, scorer modification, alternate protocol, target rewrite, dataset regeneration, model, tokenizer, native collection or network action in this replay. Saved scores and existing tar bytes unchanged.

Executed command:

`timeout 180s env CUDA_VISIBLE_DEVICES= ASTRA_LEVEL1_SOURCE_ROOT=/tmp/astra_level1_second_scores_20260913/scorer_replay/sources HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/astra_level1_second_scores_20260913/replay_frozen_scorers.py`

Receipt retains each response SHA256 and saved/replayed full-score object hash plus all matched panel counts. Original pre-replay full12 report is preserved as full_analysis.json/md; pre_replay_HANDOFF.md preserves the previous handoff. final_validation.json describes the pre-replay12-cell archive/count validation; current JSON additionally binds original_scorer_replay. No overwrite of original scores. This confirms deterministic original-protocol scoring, not an independent scoring standard, fresh model evidence, compiler admission, or a remedy for observed canary harm. Fresh replay output directory is exclusive; do not rerun into the completed destination.

## Exact pins

| File | SHA256 |
|---|---|
| `/tmp/astra_level1_second_scores_20260913/replay_frozen_scorers.py` | `26c1bb02abdc55ccdc98c8977ddcedbec03ce79ec400135f93e664b960a0162c` |
| `/tmp/astra_level1_second_scores_20260913/scorer_replay/receipt.json` | `7daa501567354293697e17f1fe8681d37faceb96c1af7d89b796e1c709b616af` |
| `/tmp/astra_level1_second_roster_analysis_20260913.json` | `1d2247c77bc582d2a0e3c8c69749ba541cfdf17fb04ec001fdfe11efc6b194a2` |
| `/tmp/astra_level1_second_roster_analysis_20260913.md` | `3d42de3bff3bc5a52c120d6d4dc34fbd424170a143610ca6e7e4ef4c78330b33` |
| `/tmp/astra_level1_second_scores_20260913/final_validation.json` | `a6e131912f1a00ff17a65ef721d8da678118abe45d34f93c7087f9fbe70f2a59` |
| `/tmp/astra_level1_second_scores_20260913/analyze_verify.py` | `3609c04cad54e2bd745c81836ad1878ea0762ab6fdacfac0aaf10be690af50a1` |
| `/tmp/astra_level1_second_scores_20260913/archive_worker.py` | `17abb66336905e02426818c589441156c37cfce83697649e202020048e756cde` |
| `/tmp/astra_level1_second_scores_20260913/archive_worker_meta_reflection.py` | `089383f629f9d0e57a38bb30d941722cebdf4810d458dfa0aa87e15550b5ed1f` |
| `/tmp/astra_level1_second_scores_20260913/archive_worker_node1.py` | `fb5966a473d826cf30ea027a048e9d479e217f2b23d2b343d2b70dc7a4a47b8a` |
| `/tmp/astra_level1_second_scores_20260913/archive_worker_self_reflection.py` | `58d0e7064c56b8a2f43fc90be6b6e18b5982fa4b39e906d284ac83719df86213` |
| `/tmp/astra_level1_second_scores_20260913/copy_snapshot.py` | `a60ddcca01ea2ef729dfe6536a427b5bc21d0e9dc933b3c518e452d64a741aa4` |
| `/tmp/astra_level1_second_scores_20260913/copy_snapshot_meta_reflection.py` | `8d748dd26369f0fe5e1f3bf44e3b2fa3d6bfd7df5f03874ae3b0b767517cd290` |
| `/tmp/astra_level1_second_scores_20260913/copy_snapshot_node1.py` | `c8e8283290e8591e670dfec1780c8a805442ae5ca1acc54c3c4e74388264b88e` |
| `/tmp/astra_level1_second_scores_20260913/copy_snapshot_self_reflection.py` | `e08f635db5182a56bfc484a1d9a8e681e44cbf25e5577895a6d732b0cf5e4892` |
| `/tmp/astra_level1_second_scores_20260913/extend_meta_reflection.py` | `18aef9cf940aeb3aef6d9bf23d6c2d87a39eb98b4426db766ee9b1dfd3b1f180` |
| `/tmp/astra_level1_second_scores_20260913/extend_repetition.py` | `776a2cf5a092fcde34f9ab9e68e50043cf76cb2438c201fcb93d9801ba7150da` |
| `/tmp/astra_level1_second_scores_20260913/extend_self_reflection.py` | `4844553d6552c64660d949db7ed90d1423b5534bc8d84e992e126fbb6b0dc573` |
| `/tmp/astra_level1_second_scores_20260913/copy_verified.json` | `540c2b9c2e292dc6a345e2f5067422359c000028e4252af1edc8ac7d45d20a74` |
| `/tmp/astra_level1_second_scores_20260913/meta_reflection_copy_verified.json` | `55a720e1fd921e2f5fa792cb25e0a4402aa2d8a1589a5aec171fefa80e36b502` |
| `/tmp/astra_level1_second_scores_20260913/node1_copy_verified.json` | `cac28f0e87b87b63cd94b57ca1708a7fb594bd10aaf102c24e3b4207a248f9e9` |
| `/tmp/astra_level1_second_scores_20260913/self_reflection_copy_verified.json` | `b7dc84f5aa646b48b8e7e993dac0f905c342c94d9a1a2aa126f3eca26efb09bd` |
| `/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/vm_verification.json` | `032c232c31a984b6492250828eb74a46ca00d626e3442b8567c44b0e3d21c480` |
| `/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/node1_vm_verification.json` | `4b460be91626c221572698fce32e2a541950a0975f9e031137c407065b4f0285` |
| `/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/self_reflection/vm_verification.json` | `b2388229b3b34466cf7b1836c3a6297ae191932a4180fbec5105506392ff630f` |
| `/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/meta_reflection/node1_vm_verification.json` | `a12971cdce41fd3c48b79066aeeee0bf8c953d01eefd053c4888a81ab2c00313` |
| `/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/meta_reflection/node1_second_meta_reflection.tar` | `1b69ccab8dd8612767dc0fa2139f934acc09e0ee5bde48181345044879599dc9` |
| `node1_meta_reflection` native manifest | `58ec5a49440b1fedd925d2b2535edf6409c9002596b42f4a4787259ab46fe03e` |
| `/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/node1_second_repetition.tar` | `b2e4cf8931afa5fb03768658d4e5cd2aef07db563476c53d2a16f3bb1e7ca6f6` |
| `node1_repetition` native manifest | `7d4656318dd2a4d825834d6eed6db612a5b542fb428bc60518ba2bdf61b165e4` |
| `/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/node2_second_perception.tar` | `addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a` |
| `node2_perception` native manifest | `4cc0a9e544523e55c1aa81a519597d903740de4fd8e61d546b9023614fe537e6` |
| `/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/self_reflection/node2_second_self_reflection.tar` | `e472f483529ae37e6105557ef4ca2b779f3691e183f3ad7008352852a2382ac5` |
| `node2_self_reflection` native manifest | `5475be7658afcf03a512e8ba9e2adb09707de77ce7067c95fb387a9d86c64243` |
| `node2/perception_seed0/scores.json` | `23d7cd4a3cbb0d677eb54c1e76ebc60c618a2fe4a2aed71b76c08ad77d45687f` |
| `node2/perception_seed0/collection.json` | `f175bff1ce2c0854225b4dbab0fee64beeab522b753c45db1d786a343701c268` |
| `node2/perception_seed1/scores.json` | `aac2327e083eecf6f09d5a507a7ca061ba2dbeef34861292bfd06ecab8687db7` |
| `node2/perception_seed1/collection.json` | `38987bb36fb655dcf90fac72d03c6bc492a98223d1b76c4f9b8ccdd5c33f8cbc` |
| `node2/perception_seed2/scores.json` | `114529b500893136998b4c2aa5791a5540911e0e3dbff6478a575a5e250b286c` |
| `node2/perception_seed2/collection.json` | `13a568bbcce3a24e73d2ea7ac335239118bbcd97e6f01fd673d33f43e3e58f5a` |
| `node1/repetition_seed0/scores.json` | `40d2b5df595c347bd2fca7417ba06fb99ad7220289ab5f26060f625d2d16def7` |
| `node1/repetition_seed0/collection.json` | `cf84208ffcc9d3ae704e9c5f5282b3c092bc60ae893155233d61a10f7548e32c` |
| `node1/repetition_seed1/scores.json` | `c03cdf1815e91031d2e308a98db4b0ae57681c460ce8e5cbf1019c0354a5dcdd` |
| `node1/repetition_seed1/collection.json` | `e3ec6c8f07ac5db83abcd6c4a7fc96f5d9b8b02ffb9c6b1b9ae2ca13ebd611b5` |
| `node1/repetition_seed2/scores.json` | `67703f3b84d27d5eb4ada9d64d8903ebc805490bf273134fd43e070f7e7de02b` |
| `node1/repetition_seed2/collection.json` | `001ea6906d81842686432998a4e958e7d4dd554dd0c82cb3617992a0bf05c4af` |
| `node2/self_reflection_seed0/scores.json` | `6db2ea03bbff6b51886c0c54350c1d62fcf87b6f73167651b6976407bc58b834` |
| `node2/self_reflection_seed0/collection.json` | `9009b2d038aef360605ca5097ac6bfdb6db8c3273aae3a149156e9c07d183af4` |
| `node2/self_reflection_seed1/scores.json` | `f4bb78ad47bdcd581956e3b12c6ac7f078d6d04555c61479d4354d4dcecaad4f` |
| `node2/self_reflection_seed1/collection.json` | `6119da6de6b140f3eb45b50bce91bc11891bfe721708e9f65a8351e3271c9646` |
| `node2/self_reflection_seed2/scores.json` | `e2aa101d68e1ebcfcecc53581262b7bef1b1a09c506ae4023a12e887d988f339` |
| `node2/self_reflection_seed2/collection.json` | `f7bc716d157329653bd6542a060f43cd5dcfba3150caf2d40d5e79246b1276af` |
| `node1/meta_reflection_seed0/scores.json` | `15b4a2876de4f9c5c0dd493d9ca0677ee1b99130a79c99a532fada5a5f8e5d3e` |
| `node1/meta_reflection_seed0/collection.json` | `5f9045881d5f6bbbacfca3b3a50ff3a7344918076c1dfc71bc56f79bf47a798e` |
| `node1/meta_reflection_seed1/scores.json` | `298c940b57a4eecdc2c9e95698e4ac8bad866ccbaf644e22a82e6ad045272081` |
| `node1/meta_reflection_seed1/collection.json` | `06eab66a970428f8a0aa51ec1eefa6a9848100b7a70e61ef95dcbb8fbe75ca29` |
| `node1/meta_reflection_seed2/scores.json` | `e4293175b7d23d917dd9f7f3f5a7ff54b48bd0ccb2ce1881801d8f125730f806` |
| `node1/meta_reflection_seed2/collection.json` | `e53bf29a58008d9f68a6525fbb99bf1b447c106d1703c3b20e77be03a149dc3a` |

Rosters: node2 clockfix `2bca9e4a66cc576993119fc1d5fddcac77de7cc3f93686327b962c45c2d17c69`; node1 fallback `781b9a3e21786c3b5ff5a78f97933fcf738b6e5d18720cb447c5e06140fb6179`.

## Ownership and limitations

Only `/tmp/astra_level1_second_scores_20260913/`, `/tmp/astra_level1_second_roster_analysis_20260913.{json,md}`, and already-ignored `gpu_artifacts_local/level1_second_roster_20260913/` written. No tracked repo edits, Git, reruns, model/GPU execution, kills, native collection, source/root mutations, manuscript access, or modifications to other agents’ artifacts.

Authored Level1 behavioral screens, not child SLEEP, broad H1/H2, full self-reflection, mental truth, recursive learning or executed next actions. Same held sources across learner seeds are not independent-source pooling. Simple canaries expose specific harm, not comprehensive safety/preservation. Exact JSON formatting, typed content, source correctness and actual compiler admission remain distinct. Repetition/meta field comparisons are supplementary typed diagnostics on saved parsed outputs, not new scores. Fresh320 recipe is inspired by, not a faithful SEQ113 replication.

No pending cells and no native preparation/launch required. Main retains all experimentation and selection authority.
