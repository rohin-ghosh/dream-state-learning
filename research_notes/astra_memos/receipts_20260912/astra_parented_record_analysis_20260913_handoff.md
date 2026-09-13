# Fixed-coaching DEV analysis preparation — 2026-09-13

**EDITSTOP. Fixture-only preparation; Main controls outcome reveal.** No live/completed experiment outputs were discovered, opened, monitored or collected. Only frozen core, runner, protocol and test source were inspected. No node, model/tokenizer, GPU, network, Git or repository operation. No core/runner/protocol or other agent file was changed.

## Delivery and validation

- `/tmp/astra_parented_record_analysis_20260913.py` SHA256 `fc700e79f277615cbb2128b9a77253f3db1b225065e20d9cb3ae2b89ea6dbc42`.
- `/tmp/test_astra_parented_record_analysis_20260913.py` SHA256 `3622f2f71a204cbe7f82d8b7d6186c7e90252d1f4790122a84f7869efe617a25`.
- **13 synthetic CPU tests PASS in3.492s**. No previous experiment/core/runner test suite was rerun. Tests generate synthetic DEV captures with the frozen core and fabricated native receipts, not real tokenizer/model calls or reserved CONF execution.

Test command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 /tmp/test_astra_parented_record_analysis_20260913.py -v
```

Coverage: exact three seeds, unequal material/dose acceptance, zero-admission NO_WRITE, missing nonempty fit/held/retention stages, admission/source mismatch, protocol mismatch, failed release, inserted native guidance on held prompts, old-retention row/loss/response-pin mismatches, incorrect eight-pass dose, duplicate/nonfinite JSON and Boolean-count substitution. Synthetic fixtures include all three held states and original historical retention. Nothing in these test outputs is an experimental result.

## Input boundary: scores alone are insufficient

The frozen collector does **not** embed raw formation/held captures, launches/releases, fit manifests or the complete old-retention baseline in scores.json. Consequently the reducer requires all three scores plus byte-preserved local completed roots and historical original scores. Main supplies these **after explicit outcome reveal**. No root discovery, polling, native verification, collection or remote fetching exists in this tool.

Freeze a local JSON manifest with this schema, expanding the one shown entry into exactly seeds0,1,2:

```json
{
  "schema": "astra_parented_record_analysis_inputs_v1",
  "seeds": [
    {
      "seed": 0,
      "root": "/tmp/LOCAL_COMPLETED_SEED0_ROOT",
      "scores": {"path": "/tmp/LOCAL_COLLECTED_SEED0/scores.json", "sha256": "EXACT_SCORE_SHA256"},
      "plan_sha256": "EXACT_PLAN_SHA256",
      "completion_sha256": "EXACT_CAPTURE_COMPLETE_SHA256",
      "collection": {"path": "/tmp/LOCAL_COLLECTED_SEED0/collection.json", "sha256": "EXACT_COLLECTION_SHA256"},
      "original_scores": {"path": "/tmp/PINNED_ORIGINAL_LEVEL1_SEED0_SCORES.json", "sha256": "EXACT_PARENT_SCORES_SHA256"}
    }
  ]
}
```

These strings are placeholders, not purported actual pins. `original_scores` is the historical **original Level1 perception** report named by `plan.parent.scores_sha256`, not the SEQ153 memory report. Preserve native path strings inside every artifact; only the outer manifest uses local mirror paths. Use unchanged raw JSON serialization so byte pins still match.

Required root paths are the frozen runner's actual layout:

- `plan.json`, `capture_complete.json`, every executed `<stage>.stage.json`.
- `run/{P,N}_formation/`, `run/{ORIGINAL,P,N}_held/`, `run/{P,N}_retention/`: capture where applicable, identity/launch/started/worker_done/exit/released/cost JSON and every original request/response JSON.
- `arms/{P,N}/{capture,dataset}.json`, and either `no_write.json`, or `{training,prepared}.json` plus `run/WRITE_fit/` fit stage JSON and adapter JSON manifests.
- JSON members are authenticated against the pinned completion inventory, and sealed stage inventory receipts must agree. Binary model/adapter payloads and logs are not read/rehashed; their inventory claims are inherited native attestations, not independently re-proven tensor/hardware checks. No file extraction is performed by the reducer.

The reducer pins runner `54cad8a6eeb5ae8af08213efe60f4c8047879991ca77f7a30d8be548659699f8`, core `68ef29fcc162dbbf5fe1becf4c09b86ed5bc1f8a79e373276dd8ba3cda88e688`, and protocol `bae29cfc48d9ae0922531d306bef1434bcc7296f2ae71a4ad6493da2a5dfb964`. It **does not import the native runner**. Frozen core import needs the previously deployed v2 core and memory projector at their original `/tmp` paths; `--source-root` supplies pinned RuleGame/parser sources, and optional `--protocol-path` supplies an exact separately copied protocol. Otherwise protocol defaults under the source root.

## Execute only when Main releases the evidence

```bash
PYTHONDONTWRITEBYTECODE=1 python3 /tmp/astra_parented_record_analysis_20260913.py \
  --manifest /tmp/MAIN_SUPPLIED_INPUT_MANIFEST.json \
  --manifest-sha256 EXACT_MANIFEST_SHA256 \
  --source-root /tmp/PINNED_SOURCE_SNAPSHOT \
  --protocol-path /tmp/PINNED_PARENTED_RECORD_DEV_PROTOCOL.md \
  --out /tmp/FRESH_PARENTED_RECORD_ANALYSIS_DIRECTORY
```

Output directory must not exist. It writes `analysis.json` and `analysis.md` once and prints their SHA256s. No actual reduction/output artifact has been produced by this sidecar yet. Input SHA/seed/stage errors stop rather than score incomplete work or silently drop a learner. Complete zero-admission arms remain results and must still have held and retention stages; only their fit stage is absent.

Pure integration API: `load_core(source_root, protocol_path=None)`, `load_bundle(entry)`, `reduce_bundle(bundle, core, dependencies)`, `reduce_cohort(bundles, core, dependencies)`, `markdown(report)`. `reduce_bundle` takes explicit report/plan/completion/history/stage-document/capture dictionaries; tests construct these entirely in memory. `load_bundle` adds byte-hash checks for real supplied files. The direct dictionary API does not itself authenticate file bytes.

## What is independently reduced

- Every formation and held capture is replayed through frozen CPU `audit_capture`. Native request messages, raw responses, routes and prefix-token receipts join back to exact replayed requests. Held contacts must be empty, contact hashes null, and restatement requests absent. No native hardware/tokenizer identity is rechecked.
- All16 apply opportunities per P/N arm, all16 fresh-held opportunities per P/N/ORIGINAL state, reached executions and record calls remain distinct denominators. Missing record calls have conditional rate N/A, not fabricated failed-record accuracy. Core compares are checked, while fresh totals/fields/formats/errors/paired slot wins/losses and turn splits are independently tallied from raw turn cells.
- Reprojected apply-only datasets must equal collected material and material receipts. NO_WRITE requires n=0, zero fits/updates, absent fit stage and original checkpoint routing. Nonempty arms require the same eight-pass policy,8n updates, warm-start inventory agreement and written checkpoint routing. Unequal n and token exposure are preserved, not rejected or called matched realized compute.
- Retention cells join their native raw responses, response hashes and row IDs; content/strict totals and gains/losses are recalculated against pinned original48held/12canary cells. Raw changed rows, errors and format counts are retained. **The material scorer is not independently rerun**; supplied score Booleans are type/completion-consistency checked and tallied. Historical baseline remains noncontemporaneous/exploratory.
- Costs reproduce call/prompt/output-token/time receipts and contact-literal token counts; full cohort limits remain300calls/256updates per seed and three fixed seeds. Fit dose token totals,8n presentations and source/init/final inventory claims are checked without reading tensors. Actual fit timing is not supplied in collector scores and is not invented.
- JSON contains P-vs-N and P/N-vs-ORIGINAL paired labels, identical-prompt/fact diagnostics, per-arm source counts, retention losses and apply-relative source novelty. Only three independent learner pairs contribute to the mean/range of P-minus-N/16. No episode-level independent-trial inference, pooled significance, adaptive-parenting claim, stable-substrate assertion or automatic pass. Fixed scaffolding, different child experiences/material/doses and already exposed retention remain explicit limits.
