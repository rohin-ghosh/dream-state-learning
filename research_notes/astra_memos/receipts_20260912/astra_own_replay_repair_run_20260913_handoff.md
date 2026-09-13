# Own replay repair runner — EDITSTOP

For Beauvoir / Main, September 13, 2026. Final runner source/tests are frozen
against the exact tested core pin below. No native prepare, GPU/model execution,
network, launch, capture collection or outcome retrieval by this author. Main
owns native CPU prepare, allocation/reservation, launch, and new pair collection.

| Owned file | SHA256 |
| --- | --- |
| `/tmp/astra_own_replay_repair_run_20260913.py` | `f1e3782378959f0c2552eaf9646a6b8827b876652a535d3248e38fe28371c4fe` |
| `/tmp/test_astra_own_replay_repair_run_20260913.py` | `cf39af12395b47bb9ae413ee0b6040703d06dc9a856f50e9418f6c58b22a1139` |

Bound Beauvoir core `/tmp/astra_own_replay_repair_core_20260913.py` SHA256
`9d8777ea3bfdcf92bace3b1a459644b9249dae108db9d5d6a3e35433e0bcff93`.
Runner23testsPASS0.846s; core15testsPASS6.796s on those core bytes. Beauvoir's
separate core handoff now declares EDITSTOP at the same code hash. This runner
freeze certifies compatibility only with that exact tested hash, not permission
to silently consume a later revision. CLI help passes.

Acknowledged Beauvoir's published seam. Runner now consumes
`build(memory_plan, bound, capture_plan, capture_report, seed,
protocol_path=..., capture_runtime_path=...)`. `capture_report` is the FULL
once-collected `replay_report.json`, not the seed admission report. `bound`
remains the original frozen memory context; no second core.admit.

LOCKED runner seam after reading your revised handoff:
`encode(mixture, arm, tokenizer, trainer, helper, probe, fit_seed)`
returns the flat per-arm object, containing (`items`, `encoding`, `epoch_order`,
`rows`, `updates`, `presentations`, `total_tokens`, `target_tokens`,
`context_tokens`, `train_tokens_seen`, `actual_supervised_tokens`,
`actual_context_tokens`, `actual_padded_tokens`, `padding_tokens`, `fit_seed`),
plus source-family/occurrence accounting as needed. Runner uses its own new
fit check, not the old <=128 update check. Please pin your final exact API/hash.

Runner API is prepare(root,spec_path,spec_sha256,allow_native=False),
worker(root,plan_sha256,stage,allow_gpu=False), controller(root,plan_sha256,
allow_gpu=False), collect(root,plan_sha256,completion_sha256,out).
Stages REPLAY_fit/REPLAY_readout/EXTRA_MEMORY_fit/EXTRA_MEMORY_readout. No LR0
stage. Main-only native CPU prepare; no native actions by author.

## Stable CLOSED spec for Main outer integration

All paths absolute native paths; every file binding has exactly `path` and
`sha256`. Runner and core hashes below are final; other placeholders are Main inputs.
`memory_history` must equal `history` in the bound original lower-LR plan/spec.
`lower_history` binds that lower-LR candidate's own completed run, not its HIGH
parent. Historical lower specs are usable by Main to obtain original-history
and deployment bindings; this runner does not rewrite/use them as its new spec.

```json
{
  "runner_sha256": "f1e3782378959f0c2552eaf9646a6b8827b876652a535d3248e38fe28371c4fe",
  "runtime": {"path": "/tmp/astra_real_record_memory_run_20260913.py", "sha256": "7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e"},
  "lower_runtime": {"path": "/tmp/astra_memory_lower_lr_run_20260913.py", "sha256": "80467204aa7ccb4a1cbf4f8d85c7be4e7347263f98f4f7b8fef5739980fcf413"},
  "capture_runtime": {"path": "/tmp/astra_own_source_replay_capture_20260913.py", "sha256": "1142593afb544dec2344c77788f6dbb624f519897b0bb65e135a9e8eb1910107"},
  "core": {"path": "/tmp/astra_own_replay_repair_core_20260913.py", "sha256": "9d8777ea3bfdcf92bace3b1a459644b9249dae108db9d5d6a3e35433e0bcff93"},
  "protocol": {"path": "/MAIN_NATIVE_PROTOCOL_COPY", "sha256": "fb523ee6d96ef6186ae187c3c9b4482b25084fa49f292aae15a34affa87103c7"},
  "memory_history": {
    "root": "/ORIGINAL_MEMORY_ROOT",
    "plan_sha256": "ORIGINAL_MEMORY_PLAN_SHA",
    "completion_sha256": "ORIGINAL_MEMORY_COMPLETION_SHA",
    "collection": {"path": "/ORIGINAL_MEMORY_COLLECTED/collection.json", "sha256": "ORIGINAL_MEMORY_COLLECTION_SHA"},
    "scores_sha256": "ORIGINAL_MEMORY_SCORES_SHA"
  },
  "lower_history": {
    "root": "/LOWER_LR_ROOT",
    "plan_sha256": "LOWER_PLAN_SHA",
    "completion_sha256": "LOWER_COMPLETION_SHA",
    "collection": {"path": "/LOWER_COLLECTED/collection.json", "sha256": "LOWER_COLLECTION_SHA"},
    "scores_sha256": "LOWER_SCORES_SHA"
  },
  "capture": {
    "root": "/localhome/local-rohing/astra_diagnostics/own_source_replay_capture_20260913_attempt1",
    "plan_sha256": "7b008f95a21ca7e01b1e72d83cf3ed8e319fbee9cc5b8af60320e65159c9c882",
    "completion_sha256": "81b94e4f4b3c43ba7e0dc96e42fb8bfd6b58d090e3944b97eb1d68b5e3a4f876",
    "collection": {"path": "/localhome/local-rohing/astra_diagnostics/own_source_replay_capture_20260913_attempt1_collected/collection.json", "sha256": "f0ff7f520a308f54318433f64c881c65a17da7cef68f1ada020d9f7c6637530c"},
    "report_sha256": "6648c0bc85589dea4e2a7ea498bf547f5313bd38efcd14c15a7d3eee228124c4"
  },
  "seed": 0,
  "fit_seed": 0,
  "gpu_index": 0,
  "gpu_uuid": "MAIN_FRESH_CHECKED_UUID",
  "expected_boot_id": "MAIN_CURRENT_BOOT_ID",
  "lease_end": 0
}
```

Main selects seed/fit_seed0/1/2, intended GPU0/1/2 with fresh checks; illustrative
lease0 and identity placeholders must be replaced. Main-reported capture pins
are copied above, not newly fetched or collected. Per seed r24 gives
304/256/256steps **per arm**,176/152/152cold calls **per pair**. Total6fits,
1632steps,480calls. Controller7200s including release, collector180s separately.

Prepare/controller require empty CVD; Main's outer reservation holder stays
alive with assigned CVD, and runner spawns fresh per-stage children with the
spec UUID. Stage order is REPLAY_fit, REPLAY_readout, EXTRA_MEMORY_fit,
EXTRA_MEMORY_readout. Return fields: prepare `plan_sha256`, `availability`,
`counts`, `limits`; controller `completion_sha256`; collector `scores_sha256`.
No historical LR0 stage. Captured once-collection is read-only input.

## Implementation and verification status

23 runner tests pass (0.846s in the final bounded CPU run), including the
actual pinned Beauvoir encoder with frozen trainer/helper/probe and a mock
tokenizer. Core build custody is tested by Beauvoir; runner additionally has a
synthetic complete LOWER/capture receipt-binding test, source/raw mutation
rejection, and preservation of the memory-projector namespace. Frozen source
pin regressions prevent substituting a later core/runner/helper silently.

New `check_fit(manifest, prepared, config, parent, arm, counts)` allows exactly
8(m+r), at most304updates/arm, retaining the old exact-manifest/token/packing,
no-skip/no-truncation, finite-loss, fresh-optimizer, same-original-parent,
frozen-base, LoRA-only trainables, unchanged-parent and nonzero parameter-delta
invariants. Initial/source tensor inventories must also equal historical
LOWER/HIGH/LR0 and the paired arm. No old128step check is called or modified.
The original parent has320prior steps; cumulative steps are320+new steps.

Reuse is explicit: frozen lower `verify`/`validate_completed` binds historical
memory and lower-LR custody; frozen capture `verify`/`validate_completed` plus
new core validate saved replay without another admission/collection; frozen
trainer `run_training(...,init_adapter=original_parent)` performs each fresh
fit; frozen memory `tensor_diagnostics`, `route_for`, `build_calls`,
`capture_readout`, and `score_calls` retain their semantics. Old fit/worker/
controller/collect code is never invoked with a changed plan. No globals are
monkeypatched by production code.

Fresh fit views/arm metadata come from Beauvoir's core. Both full per-arm
`training_ARM.json` manifests (raw span, mask, EOS, deterministic epoch order,
source-family exposures and costs) are frozen at prepare. The actual native
tokenizer re-encodes the selected arm before writing and demands exact equality.
Only original memory rows remain in `bound["dataset"]`, so unchanged cold
readout still has exact+paraphrase+48held+12canary and no replay observations.

Main-only commands, after native paths/spec and final hashes are supplied:

```bash
PY=/localhome/local-rohing/v2/venv/bin/python
RUNNER=/tmp/astra_own_replay_repair_run_20260913.py
CUDA_VISIBLE_DEVICES='' "$PY" -B "$RUNNER" prepare \
  --root "$ROOT" --spec-path "$SPEC" --spec-sha256 "$SPEC_SHA" --allow-native
CUDA_VISIBLE_DEVICES='' "$PY" -B "$RUNNER" controller \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA" --allow-gpu
CUDA_VISIBLE_DEVICES='' "$PY" -B "$RUNNER" collect \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA" \
  --completion-sha256 "$COMPLETION_SHA" --out "$OUT"
```

Prepare is capped180s and performs CPU native tokenization and warm-parent
compatibility checks without loading a model or querying a GPU. Original
native base/adapter files, all frozen source paths and original/lower/capture
roots and once-collected directories must remain available read-only. It
copies protocol/core/helper sources and the explicitly bound history inputs
into a new nonsymlink root, not a live original root. Controller requires
fresh all-process GPU vacancy before every stage and owned group cleanup plus
vacancy after every stage. Worker timeout reserves40s for cleanup. Raw native
responses are saved before validation; both worker and cleanup failures are
preserved. Four distinct process groups with ordered launch/start/release
receipts are required. Main's outer custodian is separate and remains required.

Collector verifies all new stages/releases and upstream pins before an
exclusive sibling `.collection_claim.json`, then scores exactly once into
fresh `scores.json` and `collection.json`. A failed scoring attempt consumes
the claim, with failure preserved; do not retry. No loss/score gate decides
whether EXTRA_MEMORY executes. r0 yields no training files, fits/readouts,
or screen; an explicit unavailable completion/collection can still be recorded.

## Score schema for independent reducer

`scores.json` uses scope `astra_own_replay_repair_paired_20260913_v1`:

- `status`, `seed`, `parent`, `counts`, `plan_sha256`, `completion_sha256`,
  `source_bindings`, `input_hashes` identify exact prepared inputs and custody.
- `cells.REPLAY` / `cells.EXTRA_MEMORY` have unchanged original scorer rows in
  `exact`, `paraphrase`, `held`, `canary`; each raw text/finish/hash/score/cost is
  retained. `historical_cells.LOWER/HIGH/LR0` preserve the stored controls.
- `fits`, `parameter_diagnostics`, `training_costs` expose manifests, warm/delta
  checks and per-kind token/memory exposure. `historical_manifests`,
  `historical_bindings`, `reused_endpoints` explicitly mark imports as
  noncontemporaneous and zero incremental fits/updates/calls.
- `incremental_cost` separates new calls/steps/fits/controller time from zero
  new source/teacher/historical calls. Stored historical row generation costs
  are old observation costs, not new costs. Upstream capture72calls are shared
  source acquisition, not charged as72new calls for each arm.
- `screen[arm]`: exact production-eligible threshold8/7/5 and no lost
  LR0-correct held/canary IDs; gains never offset losses. This is exploratory,
  not execution gating or scientific promotion; `automatic_pass=false`.
- `best_constant` is evaluator-only: each distinct unchanged **original memory**
  raw target is hypothetically supplied for every row with stop, scored by the
  original `score_readback` separately for exact/paraphrase. It reports all
  candidate hashes/counts, content-correct maximizing ties and actual counts
  per new arm. No alternative target enters training or native generation.
  This is the inherited same-panel oracle alternative, not a causal mechanism
  test or executed baseline. Independent reducer can reconstruct it.

No new48held panel is claimed: these remain exposed exploratory DEV. REPLAY
uses already-trained external observations, not fresh TRY experience.
Equal-step comparison deliberately differs in memory exposure and token cost.
No automatic adoption, dose ladder, winner certification, H1/H2 or clean
confirmation claim. Source/rejected provenance remains in frozen mixture and
upstream admission artifacts. Main owns artifact archiving and lifecycle.

CPU test command (no native outcomes or model calls):

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 90s python3 -B -m unittest discover \
  -s /tmp -p 'test_astra_own_replay_repair_run_20260913.py' -q
```
