# Acquisition terminal collector — EDITSTOP, 2026-09-12

## Frozen delivery and scope

Only these new sidecars were authored:

- `/tmp/astra_rulegame_record_acquisition_collect_20260912.py`
  SHA256 `422c2fd2efcc2e8c315d6082c05a803353ee8b67f0b31e23eab19fe0119ae951`
- `/tmp/test_astra_rulegame_record_acquisition_collect_20260912.py`
  SHA256 `e0eb7af2cb7b90ba9db46e8fa222996cbb9b622ccf076ac6a57d8b48dde5c2d8`
- This handoff.

**22 CPU mock tests PASS in 43.143s.** No native tokenizer/model, GPU query/scoring, SSH, network, Git, or score/outcome inspection was performed. Only the provided launch receipt and launcher source were inspected for actual schema/layout. Ephemeral synthetic test fixtures were confined to `/tmp`; no frozen driver, source, material, or legacy test was edited.

The collector is read-only with respect to acquisition/write/formation/source roots. Main alone executes it. It creates one **fresh sibling collection directory**, not `run/main_release.json`; does not alter any run artifact, retry a run, replace a selected record, generate text, load a scoring model, train, or signal/kill processes.

## Exact Main invocation

Main's announced acquisition plan is `79fad7b32e88f8dffda5f96214fbc511d702167610c613527daa68d024952bfc`, controller PID 243383, launched at `2026-09-12T22:15:30.012944+00:00`, node3/device2. The actual launcher creates `ROOT_launch/launch.json`, `gpu.xml`, and `controller.log`; **not** a readout layout.

The local launch-receipt copy hashes to `1c47d841a1e93e3beb3249bb5fcec9abba53bf17c365a51052a324417f4ca2f3`. Verify that the native `ROOT_launch/launch.json` has those exact bytes before using this pin. Do not silently substitute a changed receipt hash. The collector is parameterized by acquisition root/plan pin and launch-root/launch pin, rather than hardcoded PID/root.

```bash
ROOT="$HOME/astra_diagnostics/astra_rulegame_record_acquisition_20260912_attempt1"
LOGS="${ROOT}_launch"
OUT="${ROOT}_collection_attempt1"
PLAN=79fad7b32e88f8dffda5f96214fbc511d702167610c613527daa68d024952bfc
LAUNCH=1c47d841a1e93e3beb3249bb5fcec9abba53bf17c365a51052a324417f4ca2f3
SOURCE="$HOME/astra_sources/610c6edd05ce9c85720ee6e992889badecc2c158"

env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH="$SOURCE" \
  ASTRA_SOURCE_ROOT="$SOURCE" \
  "${NATIVE_PYTHON:?exact write-plan venv interpreter}" -B \
  /tmp/astra_rulegame_record_acquisition_collect_20260912.py status \
  --root "$ROOT" --plan-sha256 "$PLAN" \
  --launch-root "$LOGS" --launch-sha256 "$LAUNCH"

# Only after status reports ready=true; OUT must not exist.
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH="$SOURCE" \
  ASTRA_SOURCE_ROOT="$SOURCE" \
  "${NATIVE_PYTHON:?exact write-plan venv interpreter}" -B \
  /tmp/astra_rulegame_record_acquisition_collect_20260912.py finish \
  --root "$ROOT" --plan-sha256 "$PLAN" \
  --launch-root "$LOGS" --launch-sha256 "$LAUNCH" --out "$OUT"
```

Use the absolute venv interpreter spelling without resolving its symlink. There is no `--allow-gpu` flag: finish performs CPU-native token reconstruction and the full-release GPU/process/queue **query**, never model execution. It must run unmasked (`CUDA_VISIBLE_DEVICES` absent). Status does not load the acquisition driver or native tokenizer and creates no output. It checks readiness once; there is no automatic polling/retry.

## Custody and blindness

Before opening **any score body**, status/finish require exactly one terminal marker (`run/result.json` XOR `run/failure.json`) and absence of the launch controller plus all recorded OFF/P/A worker PIDs, PGIDs, and sessions in a full `/proc/*/stat` snapshot. An unexpected process receipt, reused PID, surviving session member, both markers, or missing terminal stops collection. PID reuse conservatively blocks; the collector never kills or assumes an unrelated PID is safe. Status exposes markers/process presence only, not score vectors, per-cell reductions, or the controller's summary. A failed terminal may have later cells unstarted: after all owned scopes stop, preserve that failure rather than invent missing scores.

Finish uses the actual acquisition `checked_plan` and `replay`, not readout `audit_cell`, evaluation tasks, generations, P_ON/A_ON labels, or nonexistent acquisition `lineage.json`. It binds:

- Native venv, original fixed write-plan/material/fit/base/adapter inventories, all source/scorer pins, unchanged raw records and native full/ablated contexts/offsets/masks/EOS through `checked_plan(..., tokenizer)`.
- Actual launch command, source, write release hash, launcher bytes, GPU UUID/XML, OFF/P/A order, 1800/600/140/300 bounds, 24/48/0 workload, zero updates, and no adaptation.
- Each worker spec/nonce/command, fresh PID/session and controller parent, runtime frozen-eval/no-cache/adapter-count receipts, capture seal, backend cleanup, native audit, exact request/response hashes and forward IDs/masks/positions, raw score vectors and whole-target sum/mean/counts/margins through existing replay. No rescoring is done.
- Exactly eight requests/two candidate forwards per request per cell, no extra call files or generation response fields, request timing <=120s, readiness <=180s, worker execution timeout <=600s, inherited supervisor receipt <=timeout+140s, nonoverlapping OFF/P/A supervised windows, and successful controller <=1800s including cleanup.

The acquisition summary is recomputed **only for a complete, fully verified three-cell run**, compared exactly with the terminal, and made available only with verified full release. It retains the prospective own-record-versus-OFF and stronger P-specific-versus-OFF-and-A distinctions, all cross-arm rows, both context conditions, full sums/means/counts/margins, and conditional-prefix/ablation caveats. Failed/incomplete/unverifiable runs have `aggregate=null` and `totals=null`; missing costs are null, not imputed zero. Individually verified cells and untouched failed captures remain available diagnostically. Raw archived terminal files may contain a claimed summary; only the separate collector audit decides whether it was verified.

## Release, archive, and reuse constraints

Full release reuses hash-pinned `gpu/astra_mini_sudoku_diagnostic.py::check_free` only: selected-device full NVIDIA XML, exact launch GPU UUID, no NVIDIA processes, same-user `/proc` reservation reconciliation, and both `~/queue/pending` and `~/queue/running` empty of `.job` files. It checks ownership again before/after that query. Foreign occupancy/reservations/queue entries or unreadable process evidence are failures, never killed/ignored. This inherited checker has **node-specific permitted service PID/command exceptions** and a particular SSH-ancestor exception; an unfamiliar inaccessible process fails closed. It does not mean all other GPUs are idle, and release is a timestamped observation, not a promise of future vacancy.

Only the generic immutable collector's `validate_archive`/path-validation logic is reused, via pinned source import; none of its memory/readout experiment-specific collection, reduction, release layout, or CLI is called. Its broad metadata walker is deliberately **not** reused. This collector has its own bounded allowlist inventory: regular unaliased non-hardlinked text metadata, <=32MiB/file, <=256MiB payload total, <=2048 filesystem entries and archive files; source snapshots accept pinned `.py` and `.txt` (the frozen source includes `parent_prompt.txt`). Weight/checkpoint/bytecode suffixes are excluded and listed; unknown file types, special files, invalid UTF-8, credential filenames/known credential keys or patterns fail closed, with no redaction or string surgery. Known-pattern rejection is not a universal secret detector. No environment dump is saved.

Output contains `started.json`, `audit.json`, `release.json`, optional successful `release.xml`, `custody.json`, `metadata.tgz`, and final `validation.json`; a fatal error instead leaves `failure.json` and any partial files, with no validation marker. Everything is exclusively created (0700 directory/0600 files); a second finish cannot overwrite/reuse it. Safe USTAR includes all permitted acquisition-root and launch-root metadata, exact direct pinned source snapshots, and collection receipts. No weights, adapter contents, full external formation/write trees, or unrelated external logs are copied. Their required identities are revalidated through the acquisition driver and launch binding; references remain in the pinned plan. The native test-log hash already present in the launch receipt is preserved, not independently promoted as test evidence.

Every archive member/hash and the entire archive hash are checked, as are dependency/lineage pins and unchanged source metadata before/after packing; traversal, links, duplicate/unexpected members, and changes fail. There is no extraction. `COLLECTED_PARTIAL_NO_AGGREGATE` can preserve an audit/release failure capsule but is **not** a science/full-release success. A fundamental pin/safety failure stops with partial evidence in place instead of blessing an archive.

The 300s external alarm is a non-swallowable exception, including native reconstruction, release query and archive validation. Costs distinguish controller seconds, observed verified supervised-worker seconds, launch-to-observed-release seconds, and collection seconds. Load/score/cleanup/controller/full-release/collection intervals are nested or overlapping and **must not be added**. The 600s worker execution cap plus inherited cleanup receipt tolerance is not a newly lengthened experiment budget; controller remains <=1800s.

## CPU verification and outstanding Main checks

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
CUDA_VISIBLE_DEVICES='' ASTRA_SOURCE_ROOT=/data/home/rohing/dream-state \
python3 -B -m unittest discover -s /tmp \
  -p test_astra_rulegame_record_acquisition_collect_20260912.py -v
```

The 22 tests exercise synthetic end-to-end acquisition raw replay plus archive, blind live/session barrier, absent/ambiguous terminal, failed middle cell, native reencoding failure, forward/generation/selection/call/PID/cap tamper, plan and actual saved-adapter mutation, launch/write-release custody, foreign resource refusal without kills, metadata mutation, non-swallowed expiry, exclusive creation, credential/unknown/oversize/duplicate JSON refusal, weight exclusion, symlink/hardlink/FIFO rejection, and archive traversal/link/duplicate/hash checks. The read-only acquisition/write fixture dependencies must be present; on native Main tests set `ASTRA_SOURCE_ROOT` to the existing frozen source path rather than the local default.

Remaining acceptance risks: real native reconstruction must fit the 300s window (repeated immutable model/adapter hashing can be substantial); actual process/service permissions and queue state must satisfy the inherited full-release checker; all external pinned helper/source files must exist exactly. Metadata allowlist or size failures preserve the run and collection attempt, with no automatic retry or fallback. No native collector acceptance or acquisition outcome is claimed here.

Direct unchanged dependencies rechecked locally: acquisition `ae3bbad045a7ec205ed2d711e03fcdcd08aa3b2bde8b529decda597d6e9888ea`; readout `120e260a76395586736d47e4f8a55c425b090f9f8654208dcfbef7eac5cccbde`; write-v2 `183b48be6193da953f699d718575f9227fd946d9f8111d2d1647ae5dd431ec7c`; archive helper `d2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb`; release checker `a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f`; launcher `273c8bd297ab4bec98287771c2910bf6f759194b8686f41dfd3ae5c1f6eebf19`.

This remains trained-record conditional acquisition custody, not heldout learning, pre-TRY skill, parenting/P1/G5/H1/H2, model-origin authentication, or automatic semantic-nonleakage certification. **EDITSTOP. Main sole integration/execution operator.**
