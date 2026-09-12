# W0 terminal custody — node3, 2026-09-12 08:24 UTC

## Disposition

**Execution complete; ASSAY_INVALID; frozen replay FAILED. No scientific gate pass or parent qualification.** Frozen source: `27743d0a99b827450f794dbe0c1ab45f0b07bd51`. Four fits plus ten evaluation phases have fourteen DONE receipts; launch status alone was not used as completion evidence. The unmodified report and resource receipt both record **0.47178089486611147 A40-hours**, with 1698.4112215180012 reserved GPU-seconds and 1024 optimizer steps.

Read-only terminal capture occurred 08:22:04–08:22:07 UTC. Full local base-file hash inventory and main's supplemental diagnosis were added before freezing. Archive validation finished by 08:24:24 UTC; filename labels are capsule identifiers, not asserted capture timestamps. No notebooks, SEQ, Git operations, existing files, source edits, remote writes, experiment launches/kills, resealing/truncation, or external fetches.

## Failed replay and exact hashes

Actual frozen `replay-real` was invoked with the recorded node3 venv and frozen source; exit **2**, empty stdout, stderr **`NONREPORTABLE_ABORT: sealed bytes changed`**. Exact command/environment/result and independent full audit are inside the capsule. All **3161** sealed files were checked: **3160 match**, no missing/extra files, only **launcher.out** mismatches. Current logger bytes equal report_real.json bytes; this does not repair or validate replay.

| Artifact | SHA256 |
|---|---|
| launcher.out expected empty | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| launcher.out actual, 6099 bytes; report_real.json | 407af1ff9ab3ca2865744e64155431cb00be8e21ab4025eb2fc4ac4d56bfb999 |
| PREPARED_SEAL.json | 22bec9b3f191504135d96c957b07a91959d2d3b09d7a42ef00c73e1dd15fa906 |
| REAL_EXECUTION_SEAL.json | f75999b705adc3443a7ca5d964a24fb3ae76606c0dfbda87949da78141ca4fd1 |
| RESOURCE_RECEIPT.json | 1e45e59b0874397475b3232794bea7e5f8b0595217b0ef36e0bc70b3045cb618 |

Parent/predecessor attempt raw files are included: its PREPARED_SEAL and NONREPORTABLE_ABORT survive; it never emitted a report_real or REAL_EXECUTION_SEAL. Attempt2's W0 report and execution seal are included unmodified, without promoting them to valid parent evidence. No optional forensic report recomputation was performed.

Main's exact `/tmp/astra_W0_oracle_diagnosis_20260912T0821Z.json` is preserved with its four early examples, SHA256 **b8e6dd99920058158bcf099a7d36f3e2f80a25c2d1f45ce34f79e91002ef4a9f**. Main reports each of four root/map groups: 64 requests, 64 truncated, 0 legal ACT, 0 multiple ACT. This capture did not regenerate/duplicate oracle analysis. Main's planned five-condition inference-only DEVELOPMENT calibration is separate, not a rescue/rerun of W0.

## Immutable local capsule and raw custody archive

- Frozen local capsule: `/tmp/astra_W0_terminal_20260912T0818Z` (all write bits removed; not WORM).
- New raw archive: `research_notes/astra_memos/receipts_20260912/astra_W0_terminal_20260912T0818Z_raw_20260912T0825Z.tgz` — **3705921 bytes**.
- Archive SHA256: **1ef045e5e18e0747b6429e9f08c32702dab09bd03d53f1752950794b90a46608**.
- Capsule `SHA256SUMS` SHA256: **69aa352155df3478bbeedc8818889d61ab7fe28cbd33b3f1325284dec069a26a**.
- All **3223** copied non-weight remote file hashes/lengths verified before archival; all **3242** capsule payload hashes plus SHA256SUMS itself verified from archive. All three execution-manifest source bindings match the captured frozen source. There are **3008** attempt2 raw output/trace files and **36** frozen-source files.
- The archive includes raw traces, receipts, complete non-weight run trees, source, configs, both seals/report where present, commands/results, mismatch audit, main's supplement and full inventories—not merely adjacent JSON. No Git staging/commit performed; owner main must retain this archive with the future commit. Adjacent `.sha256` and `.validation.json` do not replace raw custody.

## Explicit nonbundled dependencies

Four adapter safetensors, each **80792096 bytes**, remain at the original node3 run's `adapter_fit_{0_0,0_1,1_0,1_1}/adapter_model.safetensors`. Exact absolute locations and complete hashes are in `audit/excluded_weights.json`; all four were rehashed and confirmed retained remotely. They are absent from the archive by design.

Base/tokenizer snapshot `/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28` is also nonbundled. All **14** files (**15242807270 bytes**) have fresh local-on-node SHA256/existence/stability evidence in `audit/base_snapshot_inventory.json`, including resolved locations. No external authentication: **UNRESOLVED_LOCAL_HASHES_ONLY**.

Other runtime dependencies are node3 `/localhome/local-rohing/v2/venv/bin/python`, recorded package environment, `/usr/bin/x86_64-linux-gnu-gcc-13`, `/usr/include/python3.12`, and protected child/parent/compilergym/pcfl/c11 roots (all `/localhome/local-rohing/v6_out` in config). Their receipts/configurations are bundled, not the installations/trees themselves. Retention is observed at capture, not guaranteed indefinitely. Even with these dependencies, the original failed seal remains failed. This is non-weight raw custody, not a self-contained executable replay bundle.

## Verification commands

```bash
(cd /tmp/astra_W0_terminal_20260912T0818Z && sha256sum -c SHA256SUMS)
(cd research_notes/astra_memos/receipts_20260912 && sha256sum -c astra_W0_terminal_20260912T0818Z_raw_20260912T0825Z.tgz.sha256)
```

To verify archive payloads independently, extract into a **new** local directory, then run `sha256sum -c SHA256SUMS` inside its `astra_W0_terminal_20260912T0818Z` subdirectory. Do not extract over the frozen capsule or any production run.
