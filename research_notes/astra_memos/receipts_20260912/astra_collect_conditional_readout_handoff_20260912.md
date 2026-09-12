# Conditional readout root0 collector — EDIT-STOP

Only the assigned collector and this handoff were written. No GPU, native execution, network, Git, source edits, live score inspection, or relaunch. Main owns execution/allocation. The live controller remains PID **220273**, node3 GPU0, launched **2026-09-12T20:41:19.619663+00:00**.

## Files / binding

- Collector: `/tmp/astra_collect_conditional_readout_20260912.py` (320 lines).
- Collector SHA256: `cee3f8a50b934f1fb0f9d6fbc7ecaecbf7769640a2ec1f6bba315028ca8c4a14`.
- Fixed native root: `/localhome/local-rohing/astra_diagnostics/astra_conditional_behavior_20260912_attempt2/readouts_root0_attempt1`.
- Source: `/localhome/local-rohing/astra_sources/90e181a4b0a02cfe655bc76ba480eac9166222b4`.
- Manifest: `5a26f0da17d53518aa00c80bce3bfbfbe76ef61e65ea5ebc781f797dd33190a6`.
- Driver: `e7a42bf3644d6e4ce5fbd1f129b37008cc455ea2088d3f65dbc18d27bd1ccd74`.
- Readout source: `b4cd06137e3743186b885a809e1f2d3316fffd420a75c8c24838d6df72fa80df`.
- Reuses `/tmp/astra_collect_memory_only_20260912.py`, pin `d2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb`, and native `gpu/astra_mini_sudoku_diagnostic.py`, pin `a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f`. Both remain untouched.

## Main-only commands, on node3

```bash
env -u CUDA_VISIBLE_DEVICES /localhome/local-rohing/v2/venv/bin/python -B /tmp/astra_collect_conditional_readout_20260912.py status
env -u CUDA_VISIBLE_DEVICES /localhome/local-rohing/v2/venv/bin/python -B /tmp/astra_collect_conditional_readout_20260912.py finish
```

`status` reads existence markers and `/proc/220273` only: no source imports, receipt/results reads, reductions, scoring, or GPU probe. `finish` refuses until controller absence AND terminal existence. Do not use an SSH timeout as permission to retry: inspect existing artifacts/collector process first.

## Checks / outputs

Fixed OFF_generate/OFF_score/AUTH_generate/AUTH_score/DERANGED_generate/DERANGED_score order. Uses **driver.manifest, not driver.verify**; imports the pinned API only after source checks. Verifies six plan hashes, source hashes, material receipts, shared base/lease/device contract, state identities, and same gen/score adapter. Exactly one current base inventory and one current inventory for each AUTH/DERANGED adapter, through the existing fit contract; OFF has no adapter. No tokenizers, models, native reducers, scientific contrasts, or summary recomputation.

For complete phases: compares stored controller attempt/process/supervision/reduction identities; validates raw capture file hashes and exact request/response seals, causal input IDs/rendered prefix, structural token/candidate responses, monotonic call intervals, caps, token/forward/padding counts, and generation usage. Compares resource counts to existing reduction costs; compares stored summary/reductions and summed costs. Does not decode output IDs again or independently rederive scientific scores. Full raw metadata remains available for later independent analysis.

PARTIAL terminals retain per-phase missing/error entries and `cost: null` for unverifiable phases; never scientific zero or an invented COMPLETE. Corrupt COMPLETE evidence, source/custody failure, or invalid aggregate accounting refuses certification and leaves originals untouched. No automatic retry or repair.

Runs the existing full `check_free('0')` once, requiring launched UUID `GPU-0ee6f753-c61e-e18a-8aea-acccd3042939` and empty matching XML. It also checks own CUDA reservations and queue reconciliation through that helper. Writes exclusive `controller/main_release.json` and `controller/main_release.xml`; packages all run-root nonweight/non-pyc metadata into NEW `/tmp/astra_conditional_readout_root0_terminal_20260912.tgz` and `.tgz.validation.json`. Existing common path/member/hash validation rejects unsafe paths, links, duplicates, unexpected members and changed metadata; no extraction. Weights stay native, inventoried but excluded. Sources/material outside this run root are bound by receipts/inventories, not silently copied into the capsule.

Completed repeat collection verifies the existing archive/hash/current metadata without new writes or GPU checks. Orphan capsule/validation or release evidence refuses retry/overwrite and requires Main reconciliation. Repeated verification does not assert present GPU vacancy.

## Cost and bounds

Collection has a 300-second real-time alarm; initial collection is additionally capped at launch +4500 controller +300 external seconds. The timeout bypasses per-phase PARTIAL handling, so it cannot be swallowed as an ordinary missing phase. Full hashing, vacancy check, packaging and validation are within this bound; no checks are omitted to fit. A timeout can leave incomplete exclusive evidence, never permission to overwrite it.

Release JSON records launch-to-observed-vacancy, controller/worker subset costs and collection time at vacancy. Validation separately records collection elapsed, terminal-to-collection (including Main's collection-start lag), launch-to-collection, and conservative fit+launch-to-collection accounting. `postterminal_margin_met` explicitly exposes lag beyond 300 seconds; starting late does not erase that cost. Packaging completion time is recorded after archive validation/hash and immediately before writing the final validation receipt, whose write remains alarm-bounded. Prior fit reservation is 464.397178s; allocated 464.397178 +4500 +300 =5264.397178s, below Main's 5400s ceiling. This is an allocation, not a throughput or price prediction.

## Local CPU checks

**33/33 mock/in-memory checks PASS**, executed with `python3 -B` from stdin; no third test file or filesystem fixtures written. Coverage: status without reads/imports; live/no-terminal refusal; 300s alarm/finally and uncatchable timeout; UUID/empty-GPU rejection; exact/tolerant/nonfinite cost cases; raw generation/HF costs, identity/hash/timing/prefix tampering; one-pass inventories; safe archive/hash/traversal checks; six complete phases, PARTIAL/unattempted/missing evidence, corrupt COMPLETE, summary cost and worker identity/cost mismatches; verified repeat with no writes/native calls, orphan capsule/release refusal, expired allocation refusal, absence of prohibited native verification/reducer/tokenizer calls. GPU check and native APIs were mocked, not executed. Native end-to-end collection remains Main's check.

Authorship disclosure: this collector's author also authored the readout controller. This is technical custody/resource verification, not a fresh-author independent scientific review or L1 verdict.

**EDIT-STOP.** No edits to the live driver, source, phase plans, captures, or other owned files.
