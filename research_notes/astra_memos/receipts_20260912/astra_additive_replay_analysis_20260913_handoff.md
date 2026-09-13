# Additive replay prospective cohort reducer — EDITSTOP

September 13, 2026. Ready for Main's independent CPU review and later LOCAL
reduction. No new additive native outcomes or receipts were read while developing
this reducer. No native, network, model, launch, collection, Git or repository
actions. Frozen core/runner/trainer/launcher remain untouched.

## Owned files and validation

- `/tmp/astra_additive_replay_analysis_20260913.py`
  SHA256 `df38efd210929ec21523d19daa8b65f98d50fef435b3fa23b719929bca6dc472`
- `/tmp/test_astra_additive_replay_analysis_20260913.py`
  SHA256 `cb59676941df9a4fbc13679c5b910333accd1edc5f7cd153ca73d6c163d38047`
- This handoff; its final byte hash is in the author's EDITSTOP message.

Final CPU command: **15 tests PASS in 22.375s**; CLI `--help` also passed.

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 180s python3 -B -m unittest discover \
  -s /tmp -p 'test_astra_additive_replay_analysis_20260913.py' -q
```

Fixtures use only preserved pre-additive own-repair input/history at
`/tmp/astra_own_replay_repair_native_20260913_attempt1/own_replay_repair_seedN_20260913_attempt1`
and its old collected scores. ALL new additive outputs, losses, adapter bytes,
identities and timing receipts in tests are synthetic, inside temporary roots.
The synthetic `.safetensors` file is explicitly nonmodel bytes: these are schema,
byte-custody and source-join tests, not a tensor-computation/native-training test.
The tests do not read current additive run roots. They exercise all three seeds,
noncompensatory per-item masks, altered raw/finish/timing/order/cost/masks, loss
sum versus mean, nonfinite norms, descendant parents, constant/history changes,
duplicate/bool seeds, bool return codes, JSON duplicate keys/NaN, pin/path errors,
write-once output, clean terminal chains, retained BrokenPipe, extra launcher
receipts, missing terminal receipts, PID conflicts and failed controllers.

## Stable API and closed manifest

`load_apis(module_dir, source_root, protocol_path, legacy_protocol_path)` loads
byte-pinned CPU helpers. `load_bundle(entry)` loads and hashes local evidence.
`reduce_seed(bundle, apis)` audits one complete pair. `reduce_cohort(bundles, apis)`
requires all three original seeds. `run(manifest_path, manifest_sha256, out, ...)`
is the write-once CLI entry. Use the loader before the in-memory reduction APIs;
manually constructed/mutated dictionaries do not themselves establish byte pins.

Input schema `astra_additive_replay_analysis_20260913_v1_inputs` has exactly
`schema,seeds`; `seeds` contains exactly three unique strict integer seeds 0/1/2.
Every entry has exactly:

```text
seed: 0 | 1 | 2
root: absolute LOCAL complete native-root mirror
plan_sha256: actual plan.json byte SHA256
completion_sha256: actual capture_complete.json byte SHA256
scores: {path: absolute LOCAL scores.json, sha256: actual file SHA256}
collection: {path: absolute LOCAL collection.json, sha256: actual file SHA256}
collection_claim: {path: absolute LOCAL preserved .collection_claim.json,
                   sha256: actual file SHA256}
launcher: {root: absolute LOCAL complete .launcher directory,
           files: {relative_filename: actual file SHA256, ...}}
```

`scores` and `collection` share one local directory. Preserve the native paths
inside JSON unchanged: the loader never follows those absolute native paths.
There is no discovery, native connection, collection, partial-cohort or bypass
mode. Preserve all prepared inputs/snapshots, full four-stage inventories
(including adapter bytes, DONE and steps.jsonl), and preparation/controller
receipts. Symlinks, extra stages and failed-native-stage evidence are rejected.
No teacher rewriting, repaired targets, normalized raw output or new evaluation
bank is created.

Launcher `files` must contain exactly these ten files, plus optional
`failure.json`: `precheck.json`, `stdout.log`, `launched.json`,
`holder_started.json`, `controller.json`, `controller_exit.json`,
`collection_started.json`, `collector.json`, `collector_exit.json`, `exit.json`.
It pins stdout without interpreting its contents. Unknown/retry receipts,
`holder_failure.json`, missing terminal receipts and nonzero or boolean return
codes fail reduction; they are never deleted, silently omitted or recollected.
The full cohort fails closed rather than excluding a failed seed from denominators.

Example invocation (Main supplies a real manifest and its byte hash):

```bash
python3 -B /tmp/astra_additive_replay_analysis_20260913.py \
  --manifest /tmp/LOCAL_ADDITIVE_MANIFEST.json \
  --manifest-sha256 EXACT_MANIFEST_SHA256 \
  --out /tmp/FRESH_ADDITIVE_REDUCTION \
  --module-dir /tmp \
  --source-root /tmp/astra_level1_real_record_source_20260913_attempt1 \
  --protocol-path /data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_ADDITIVE_REPLAY_DEV_2026-09-13.md \
  --legacy-protocol-path /data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_OWN_SOURCE_REPLAY_REPAIR_2026-09-13.md
```

Outputs are `analysis.json` (schema `astra_additive_replay_analysis_20260913_v1`)
and `analysis.md`; the CLI returns both byte hashes. No files are written before
successful full validation. Use a fresh output outside the source/launcher mirrors.

## Launcher anomaly treatment

A preserved optional launcher `failure.json` is a separate field from native
failure. A post-spawn error with `holder_may_be_running=true` is retained with
its exact file hash and decoded error only when the complete receipt chain joins
the same holder identity, controller PID, seed/root/plan, frozen source and tiny
gate pins, once-collection claim, completion and collection hashes. Controller,
collector and holder-written terminal receipts must each report strict integer
rc0. Stage raw validations and release receipts must still pass. This permits
the frozen launcher's post-write BrokenPipe without treating it as a failed fit.
No whitelist of favorable scores or seed-specific exception is used.

The report exposes `launcher_failure`, `launcher_failure_sha256`, classification,
terminal codes, identity/receipt pins, and one-chain consistency. It preserves
raw error bytes in their original file (never rewrites them). Classification is
`post_spawn_launcher_error_with_terminal_success`, not an assertion that every
possible launcher error was a network transport error.

Main reported before outcome reads: combined SSH timed out after seed0 started;
seed1 wrote launched/controller receipts then its stdout print raised BrokenPipe;
holders 135911/135927 were reconciled without retry; seed2 was proven unlaunched
then first launched as holder136095. These are operator-provided launch context,
not independently inspected evidence. Preserve Main's transport logs alongside
the reduction; an SSH timeout with no local receipt cannot be inferred by this
reducer, and `none_recorded` does NOT mean no transport anomaly occurred.

Main supplied prospective plan hashes (not locally inspected in this task):
- seed0 `77a7e3f39005e10c0f3085dc68aabdebc31f33f9684925125c2a261039555c45`
- seed1 `7d426da11e418d0b23a2513b9b76b1b0acf49bfaf544132ee1760e4bcadcff2b`
- seed2 `9d0fbcc9d8b40184348f849477a502250c385037eb297b24225793f804cfa3c6`

Receipt limits: exclusive writes in the pinned launcher plus one consistent
local chain support no retry within that root, not proof of no other launch/root.
Holder `exit.json` is written before returning, not an independent OS wait/reap
receipt. CVD holder-UUID/children-empty policy is checked through pinned source,
not sampled anew. Current native process absence/UUID/lease state is NOT verified.

## Reduction and unchanged interpretation

Per seed: ADDITIVE and fresh MEMORY_ONLY plus five historical endpoints
LOWER/HIGH/LR0/REPLAY/EXTRA_MEMORY; exact/paraphrase denominators14/8/8, held48,
canary12 and original possible-record denominator16. Original exact eligible
floors8/7/5 AND no lost LR0-correct held/canary remain unchanged. No gain offsets
a loss. Paraphrase is descriptive, not a replacement threshold.

Reports include per-item/metric gains and losses against LR0, the fresh control,
and historical EXTRA_MEMORY; LR0-correct restoration of EXTRA_MEMORY losses;
raw/finish drift of fresh MEMORY_ONLY versus old EXTRA_MEMORY; raw formats,
errors, constants, component loss traces, update/tensor-norm receipts, exact
executed order, peak memory where measured, memory/replay supervised/context
token counts and timings. Historical drift requires diagnosis before attribution,
not exclusion of an otherwise intact cell or an invented outcome gate.

Both arms must retain EXACT old EXTRA_MEMORY occurrences AND epoch order,
original parents (never repair descendants), fresh optimizer/warm-start invariants,
masked context and target/EOS, actual original encoding FILE-byte pins and
frozen source/call routes. Component loss must be summed, not averaged. The new
runner's pure `check_fit` is reused without a native lifecycle import. New raw
request/response/token/finish/timing receipts are independently joined and
rescored; historical pinned raw cells are rescored but not regenerated.

Fresh cohort costs:6 fits,1632 updates,480 cold calls, zero capture/teacher calls;
historical controls have zero incremental cost. Controller<=7200s,
prepare<=180s, collection<=180s; preparation plus logged holder spans must be<=8
aggregate hours. Nested timing spans must NOT be added twice. Unlogged reservation
gaps are not metered, and elapsed spans are not GPU-active time. MEMORY_ONLY and
ADDITIVE match full memory occurrence exposure, not compute, RNG, timing or
realized gradients. Numeric norm receipts are checked, not recomputed with Torch.

`automatic_promotion=false`, `scientific_pass=null`, `fit_authorized=false` always.
This is a single-write development objective contrast, not parenting, repeated
learning, H1/H2, G3, clean-lineage qualification or authorization for another fit.

## Frozen dependency pins

- Protocol `724d5a6e1aea7dca4b0ae42aec6e2fd0252b98646f7c903432927263f2c391e9`
- Core `b58e4c90e2abdd26648475c9fb1fe92e3bc3fef2fa7664ecaaa69fc93591076a`
- Runner `ca54e7e1971d89224bb8dec8f3518d0a6a73ec4d1abe6f29278bab335b1618a5`
- Trainer `3f2e73ef69b12c8db211e1d3043e4559713e036ffe09571ab8bc4c5199a426a0`
- Main launcher `1ed1b383f2a36855f53e7b165dc9d75fe99620e930a3ae89332fcbe22c7ce05c`
- Tiny CPU gate receipt `ff2346a72f7e4fed9f4cdb51c90bb701c736557add56f0462f2b1e7ef2bc0b7d`
- Order-fixed legacy reducer `4c06d8ded8ab58814a94f0aab40780a54fa2cf76ca0c7d858d1ab639483b03ab`
  (`/tmp/astra_own_replay_repair_analysis_20260913_orderfix.py`), whose existing
  pinned loader supplies the original scorer/source/projector/utility dependencies.
- Legacy protocol `fb523ee6d96ef6186ae187c3c9b4482b25084fa49f292aae15a34affa87103c7`
