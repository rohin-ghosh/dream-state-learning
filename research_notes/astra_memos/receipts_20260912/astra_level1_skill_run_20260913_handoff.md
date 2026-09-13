# Authored Level1 runner — bounded coding handoff, 2026-09-13

## Scope and status

Only `/tmp/astra_level1_skill_run_20260913.py`, `/tmp/test_astra_level1_skill_run_20260913.py`, and this handoff are owned/edited. No repository edits, Git, network, native tokenizer/model calls, GPU queries, deployments, launches, or live-root reads performed. Public/reflection helpers and archived encoder remain unchanged. Main owns final source/material/protocol binding and native execution. This is prospective infrastructure, not a scientific approval or result.

CPU command: `python3 -B -m unittest discover -s /tmp -p test_astra_level1_skill_run_20260913.py -v` — **15 tests PASS, 14.659s**, after the final1024 ceiling change. Tests use real stdlib trainer encoding and material APIs, mocked tokenizer/model/processes; two collection aggregation tests explicitly mock scorer outputs. The revised prediction/goal material was available for scorer preflight tests; discrimination's final revised scoring freeze remains owner/Main-controlled. A native prepare with an old scoring API now fails before model loading.

## Treatment and methodological boundary

- One skill per fresh root; `skill` selects the pinned module's API. Intended roster is prediction, goal_completion, contradiction, update_judgement × learner seeds 0/1/2, twelve independent roots; there is no scheduler or roster launcher here.
- `material_seed=0` by default, independently fixed across learner seeds. `learner_seed` affects fit initialization/order only; OFF/post engine and generation seed remain 0. Material is rebuilt twice at prepare, byte-bound in `material.json`, and rebuilt at collection.
- 96 distinct sourced training rows, 48 held, 12 canary. Source identity uses `source_id`, otherwise `situation_id`, otherwise canonical source-object hash. Duplicated/cross-panel source IDs or row IDs fail. Skins do not count as new independent sources.
- Cold frozen base, fresh rank8 LoRA, alpha16, dropout0.05, LR3e-4, AdamW, bf16, batch4 distinct sources, grad accumulation1, no packing, max sequence1024, exactly320 updates. Fourteen configured epochs terminate after13 full epochs plus8 batches:1280 presentations;64 rows seen13 times,32 seen14 times. This seed-dependent last partial epoch is explicitly costed, not rounded to14 complete epochs. Main selected the1024 ceiling for source-rich material; actual batches pad only to their longest row, and actual padded token cost is recorded. No new native memory evidence was obtained by this sidecar.
- Per-row encoder preserves archived TrainingItem context/target/EOS/tail masks; full target bytes and exactly one supervised EOS, masked context/template tail/padding, no truncation/splitting. `add_eos=False` because EOS is already an explicit supervised span. Any native row exceeding1024 fails prepare; no silent shortening or config change.
- SEQ113-inspired, **not faithful SEQ113 replication**. Prior plan `research_notes/astra_memos/receipts_20260912/astra_interleaved_memory_pair_plan_20260912.json` SHA256 `4cad487a53d0e992b896eb4324ff2de1adb24ccc176856de7043d1132c0ee388` used warm80 parents +320 new updates=400 cumulative, mixed2memory+2arithmetic batches. This branch deliberately omits inherited parents and unrelated arithmetic replay, substitutes96 independent skill sources, and uses explicit assistant EOS masks.
- Prior timing reference: `research_notes/astra_memos/ASTRA_INTERLEAVED_MEMORY_READOUT_2026-09-12.md` lines49–50: controller1308.918702s; launch-to-observed-release1395.898451s. These clocks nest, not add. Prior workload/material/hardware is not a throughput guarantee for this fresh branch.

## Native layout and exact spec shape

Main deploys byte-identical runner and selected final material/public/reflection modules at absolute paths outside a **fresh, immutable, .git-free source snapshot**. Suggested layout (paths are choices, not deployment claims):

```text
/tmp/astra_level1_skill_run_20260913.py
/tmp/astra_level1_prediction_goal_material_20260913.py     # or final discrimination module
/tmp/astra_birth_skill_probe_run_20260913.py
/tmp/astra_reflection_fit_run_20260913.py
/tmp/astra_level1_source_20260913/organism_v6/__init__.py
/tmp/astra_level1_source_20260913/organism_v6/birth_skill_corpus.py
/tmp/astra_level1_source_20260913/organism_v6/rulegame_parenting_diagnostic.py
/tmp/astra_level1_source_20260913/organism_v6/train_adapter_v3.py
/tmp/astra_level1_protocol_20260913.md                     # Main's final protocol bytes
/tmp/astra_level1_binding_20260913.json                    # Main's native public model binding
/tmp/astra_level1_prediction_seed0_spec_20260913.json
/tmp/astra_level1_prediction_seed0_attempt1/               # must not yet exist
```

Every file in source snapshot must appear in `source_files`; extra pinned dependencies are supported, unlisted files/symlinks are rejected. The four listed modules are required. No archive deployment is necessary: only the per-row mask logic was shape-adapted. Archived encoder provenance: `research_notes/astra_memos/receipts_20260912/astra_perception_fit_run_20260913.py`, SHA256 `f62da57d1a66cd287b72ac8ad8b8724601062813653a63d3dcd6cd8a3b69cd51`.

Spec template: replace every uppercase placeholder with Main-observed absolute paths/hashes/lease/UUID; GPU index0 here is illustrative, not an allocation assertion. Spec itself must be outside root and is hashed after final substitutions. Hashes below for original helpers/source were observed locally; Main must independently verify deployed bytes.

```json
{
  "source": "/tmp/astra_level1_source_20260913",
  "source_files": {
    "organism_v6/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "organism_v6/birth_skill_corpus.py": "078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6",
    "organism_v6/rulegame_parenting_diagnostic.py": "e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526",
    "organism_v6/train_adapter_v3.py": "7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7"
  },
  "model": "MAIN_ABSOLUTE_OFFICIAL_MODEL_PATH",
  "runner_sha256": "MAIN_FINAL_RUNNER_SHA256",
  "material": {"path": "/tmp/astra_level1_prediction_goal_material_20260913.py", "sha256": "MAIN_FINAL_REVISED_MATERIAL_SHA256"},
  "reflection": {"path": "/tmp/astra_reflection_fit_run_20260913.py", "sha256": "0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc"},
  "public": {"path": "/tmp/astra_birth_skill_probe_run_20260913.py", "sha256": "59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c"},
  "protocol": {"path": "/tmp/astra_level1_protocol_20260913.md", "sha256": "MAIN_FINAL_PROTOCOL_SHA256"},
  "binding": {"path": "/tmp/astra_level1_binding_20260913.json", "sha256": "MAIN_NATIVE_BINDING_SHA256"},
  "skill": "prediction",
  "learner_seed": 0,
  "material_seed": 0,
  "gpu_index": 0,
  "gpu_uuid": "MAIN_OBSERVED_GPU_UUID",
  "lease_end": "REPLACE_WITH_NUMERIC_UNIX_UTC_SECONDS"
}
```

`binding` is the existing public helper's model-only binding schema, not a new authority document. Its original `NO_FIT` scope describes upstream file identity only; this runner's plan/config explicitly declares a fit. Official revision/file equality is not a clean-ancestry certificate.

Discrimination material's supported `ASTRA_LEVEL1_SOURCE_ROOT` is set to spec.source **only during module import** and restored afterward; module captures the source path. No helper monkeypatch or source edit. Its internal corpus pins must match snapshot files. Prediction/goal needs no source-root override. Use final revised material pins, **not** pre-07:25 scoring pins.

## Exact CLI / native preflight before GPU

Run only under Main's chosen native interpreter; the executable path and SHA are bound into the prepared plan and must remain unchanged. CPU preflight imports no model, hides CUDA, uses the actual local tokenizer, validates official model/source/environment binding, checks exact masks and exposure through original trainer pack/order/collate, and self-checks the revised scorer on authored reference targets (not model outputs). No inference or scoring of native outputs occurs before collection.

```sh
"$PY" -B /tmp/astra_level1_skill_run_20260913.py prepare \
  --root "$ROOT" --spec-path "$SPEC" --spec-sha256 "$SPEC_SHA" --allow-native

"$PY" -B /tmp/astra_level1_skill_run_20260913.py controller \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA" --allow-gpu

"$PY" -B /tmp/astra_level1_skill_run_20260913.py collect \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA" \
  --completion-sha256 "$COMPLETION_SHA" --out "$FRESH_EXTERNAL_COLLECTION_DIR"
```

Main's existing simple guarded launch pattern can launch controller directly; no new launcher helper. `worker` is internal only, fresh-session-owned and isolated to planned UUID. Root/spec/source/model/helper paths must be absolute and disjoint. Prepare emits `plan_sha256`; controller emits `completion_sha256`. CPU success explicitly says NOT_GPU_APPROVAL.

## Runtime, custody, cost, collection

- Order OFF → fit → post. OFF and post each instantiate one fresh inference engine, held48 then canary12 sequentially. Both use exactly the same60 prompt records and generation budgets, no targets/proofs in call prompts. Total120 calls, at most192 output tokens each. post alone routes its immutable fresh adapter. No shared mutable adapters or evaluation-fed fitting.
- Three distinct fresh processes. Existing **all-process XML** vacancy checks and30-second query budget are unchanged, including graphics processes; no CSV substitute. Planned index/UUID checked before stage and after owned cleanup. No foreign process kills or automatic retry.
- Controller5400s total (including verification/stages/cleanup); fit3600s and each readout600s are ceilings within remaining total. Cleanup reserve40s covers owned group cleanup plus30s XML release query. Collection180s. Six-hour lease margin beyond controller+collection required. Per-stage full model/environment verification counts against these limits. Exhaustion/failure preserves artifacts; it does not silently reduce updates, rows or calls. 5400 is a finite initial envelope, not a measured new-native throughput claim.
- `train.json` retains exact encoding masks, epoch orders, actual320 batch row IDs. `costs.json` retains per-row input/target lengths, presentations, actual supervised/input/padded token sums including the partial epoch. Fit manifest validates320 updates,14 epochs run, no skipped/truncated/split/nonfinite batches, exact dataset and actual exposure totals, no warm parent.
- Complete collection verifies plan/interpreter/source/helper/protocol pins, native request/response metadata, exact LoRA routes, adapter inventory and all120 captures/process receipts. It writes externally, claims once via `ROOT.collection_claim.json`, and never modifies the completed root. Failed/incomplete roots do not get fabricated zero scores; preserve their partial raw evidence and failure records for Main.
- Native output scoring is delegated unmodified to pinned `score_row(row, raw, finish_reason)`. Required final API: boolean `passed`, `content_correct`, `strict`, and nonempty string `format`; `passed == content_correct`, strict implies content success, non-stop cannot pass. All extra errors/fields are retained unmodified; bool-as-count, nonfinite JSON and contradictory success metadata reject.
- **Primary** per-panel content/total; paired post-minus-OFF integer numerator with explicit held48/canary12 denominators. **Secondary** canonical `strict` totals and `format_counts`; full typed errors and raw captures preserved. JSON whitespace/key order and sole optional JSON fence policy belongs to revised material scorer, never runner repair. No value/type/key repair or spontaneous-reasoning claim. Canary copy/arithmetic remains its scorer's declared contract.
- `scores.json` contains cells OFF/post × held/canary,120 calls, fit manifest/receipt, generation prompt/output tokens and elapsed sums, training costs, material provenance/qualification and controller wall time. `automatic_pass=false`, `scientific_pass=null` always. These are verified native-collection summaries, not a new independent byte-level native replay or a claim about clean ancestry, mechanism freeze, P1/H1/H2 or production grammar.

## Freeze

Final exact owned-file SHA256 values are delivered in the accompanying EDITSTOP message. Main retests once against both final revised material modules/protocol before binding the prospective12-root roster. No active contrastive/LR/public-helper changes are part of this work.
