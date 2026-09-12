# EDITSTOP — terminal actual-record readout collector, 2026-09-12

Implemented only `/tmp/astra_collect_rulegame_record_readout_20260912.py`, `/tmp/test_astra_collect_rulegame_record_readout_20260912.py`, and this handoff. **22 synthetic-only tests PASS in34.426 seconds.** No live outputs, SSH/network, GPU queries, native tokenizer/model execution or Git were used. Frozen readout/write drivers, plans, source and tests were not edited. Main alone executes collection.

## Exact bindings

The collector is deliberately bound to Main's reported node3/GPU2 readout, not a generic result selector:
- Root `/localhome/local-rohing/astra_diagnostics/astra_rulegame_interaction_v3_record_readout_20260912_attempt1`; sibling `_launch` directory.
- Controller PID234660; launch `2026-09-12T21:39:20.620581+00:00`; full GPU UUID `GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1` inherited from the pinned launch/checker patterns.
- Readout plan `cdb71865359498ca0f75db57566e638b667d2e849cc11c9cbd45dd6bfbb97375`; write plan `48effd1ba154f497e5946d308f990624ada63bd905c198e0abfdf668131a8ee4` (attempt2); source directory `610c6edd05ce9c85720ee6e992889badecc2c158`.
- These are launch/source inputs, not a statement that this worker inspected the live node or its results.

SHA256:

| File | SHA256 |
|---|---|
| `/tmp/astra_collect_rulegame_record_readout_20260912.py` | `0101e975b8ca91dedf5d77e7a2720c181698ea79641928ad05e3d52fad22871f` |
| `/tmp/test_astra_collect_rulegame_record_readout_20260912.py` | `8c8caa6882778b38598591772b1b7543396cb44ca90697f465bba40924010627` |
| Frozen readout driver | `120e260a76395586736d47e4f8a55c425b090f9f8654208dcfbef7eac5cccbde` |
| Frozen readout tests (unchanged) | `e34cb5c9aa7e9c2339eb21a46428cb38e8d8401945a90b5e08f7514d44c8db11` |
| `/tmp/astra_launch_rulegame_record_readout_20260912.py` | `49178ed96a2404379af2cb511c111e91c399b77f84fd547618497744b02e5fef` |
| `/tmp/astra_collect_memory_only_20260912.py` (reused safe metadata/archive helper) | `d2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb` |
| Source `gpu/astra_mini_sudoku_diagnostic.py` (reused full-release checker) | `a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f` |

## Behavior and boundaries

`status` (line72) reports PID presence/file-existence markers only, never scores or raw outputs. `finish` refuses until the controller is absent **and** a terminal result/failure exists; audit requires exactly one terminal. There is no wait loop, automated relaunch, retry, reselect, training or generation. Main can call status separately while waiting; no collection begins during a live run. PID reuse is conservatively treated as present.

`bind` (line93) verifies plan/source/driver/launcher bytes, exact launch command/cell order/time/PID/device/interpreter/bounds and write-release hash. Reuses frozen `checked_plan` and `accepted_writes` to validate original base and paired-write identity. Stored readout lineage must match accepted writes. The launcher/test receipt remains archived evidence; this collector does not independently rerun the launch CPU tests.

`checked_cell` (line143) verifies exact minimal worker spec, adapter role, command/hash, distinct worker PID/PGID and supervisor ownership, recorded native header/isolation/readiness, process caps, cleanup, capture/terminal seals and stored provenance. Calls frozen `audit_cell` for raw world/call replay, then **reruns `audit_native_calls` using the actual local native tokenizer at Main's collection time**; the prior native-audit marker alone is insufficient. No model inference is involved. Preserve rules2–5 and four-task scoring denominator; absent/invalid quizzes stay zero. Check ≤20 wake and≤12 record calls/cell, ≤32/cell and≤96 total, correct role token caps and total generated-token ceiling≤27,600. Record count/allotted12 opportunities and quiz results remain separate; no new spontaneous-PREDICT metric or assay is added.

Successful aggregation must exactly match all three replayed cells and frozen P−OFF/A−OFF/P−A formulas. A failed terminal preserves every cell's available evidence and validation error; missing/unverified scores, token costs and clocks are **null**, not zero. A failed run has **no aggregate and no pooled token-cost total**, even if some/all cell captures validate. Available worker durations may be reported as an explicitly incomplete observed subtotal, with completeness flag. Missing controller receipt/clock is null; an observed failed overrun is reported rather than hidden. Successful-result corruption is a hard rejection, not a downgrade to an apparently successful capsule. Identity/source corruption similarly fails closed; original files remain untouched.

`release_check` (line267) reuses the hash-pinned **full** checker: nvidia-smi XML for the selected full UUID and empty process table; own-user process-environment reservations and explicit exception reconciliation; pending/running queue checks. It is not merely an empty compute-app query or a worker's release flag. Collector invocation must unset CUDA_VISIBLE_DEVICES so the collector does not claim the device. If the checker fails, no new release or archive is written.

`collect` (line273) inventories **all nonweight metadata** under readout root plus launch sibling, rechecks custody and absent controller, writes the observed full-release XML/JSON, and creates `/tmp/astra_rulegame_record_readout_terminal_20260912.tgz` plus `.tgz.validation.json`. Full maps of captured files/hashes, per-cell audits, costs, bounds and exclusions are retained. Base/adapter weight bytes remain at original roots; accepted saved-adapter inventories are verified, not copied. The collector does not archive source/model/write-root trees outside the two requested metadata scopes.

Reuse common safe traversal and regular-file reads: reject symlinks/special files, changed file identity, unsafe member paths, traversal, links, duplicate/unexpected members, sparse/extended entries and wrong content hashes. Build a USTAR metadata archive and validate exact inventory/hashes without extracting. Source payload hashes are checked before executing dependency code; launcher bytes are only hashed. Recheck original metadata, controller absence and accepted-write/source identity after packing. A partial release/archive is preserved and cannot be overwritten/retried automatically. An already-complete capsule can only be verified read-only; that is not a fresh release observation.

## Clock accounting

- Existing readout controller≤1800s; worker≤600s; nested140s cleanup reserve; backend readiness≤180s. Worker supervised duration includes owned cleanup and is bounded by its assigned timeout+140s. No new readout schedule or bound is introduced.
- Each verified cell reports raw request/input/output counts, output ceiling, generation seconds, maximum observed call duration and worker reserved seconds. Generation intervals sit inside worker windows; supervised workers sit inside controller elapsed time. They are **not additive**.
- Full reservation is launch→fresh observed full GPU vacancy, including CPU gaps, cleanup and time waiting for collection; it is not the terminal's internal elapsed field.
- Collection has a separate **300-second external alarm**, covering custody/native-token checks, full release and packaging. It is not added to the old1800s controller budget. Its early portion overlaps launch-to-observed-release time; report both rather than summing. An alarm cannot be swallowed as a per-cell partial exception. Timeouts preserve partial artifacts for Main reconciliation, not retries.

## Tests and Main commands

Tests exercise real frozen replay/token logic with synthetic captures/tokenizer and mocked fits/backends/processes/GPU checker. Cases cover complete96-call custody, retained invalid quizzes, partial/null/no-aggregate behavior, missing controller clocks, failed overruns, exact launch/write-release binding, wrong identity/spec/PID/role/caps/native rendering, source-hash/symlink rejection, occupied GPU/queue refusal, complete/partial metadata archives, safe archive validation, no-overwrite and marker-only live refusal, and timer cleanup. No native/GPU operation was executed here.

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES='' \
python3 -B -m unittest discover -s /tmp -p test_astra_collect_rulegame_record_readout_20260912.py -v
```

Tests reuse existing read-only `/tmp/test_astra_rulegame_record_readout_20260912.py` fixtures and their dependencies. Main should keep all hash-pinned helper/driver/launcher paths available natively. Do not resolve the native venv interpreter symlink:

```bash
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /localhome/local-rohing/v2/venv/bin/python -B \
  /tmp/astra_collect_rulegame_record_readout_20260912.py status

# Main only, after absent controller plus terminal:
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /localhome/local-rohing/v2/venv/bin/python -B \
  /tmp/astra_collect_rulegame_record_readout_20260912.py finish
```

**Remaining native check:** Main's terminal collection must verify actual capture/token identities, all selected cells or preserved failure state, current accepted adapters, full UUID/process/queue release and archive custody. This handoff asserts none of those live results. A valid collection is evidence custody, not learning, pre-TRY information-selection improvement, autonomous adult updates, longitudinal G5/H2, semantic nonleakage certification or model-origin authentication. EDITSTOP.
