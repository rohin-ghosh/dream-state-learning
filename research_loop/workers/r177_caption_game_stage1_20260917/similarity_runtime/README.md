# R177 frozen sentence similarity runtime

## Public integration handoff (12:20 PDT, September17)

`public_bundle1/pixel_config.json` is the exact plain frozen mapping. The nine original encoder files are copied and hash-verified in `public_bundle1/embedding/`, with portable `embedding_snapshot.json`. `public_bundle1/similarity_runtime.json` is a separately pinned, private-reference-free config compatible with Main's existing real-tools CLI; original calibration config/pins are unchanged. The actual offline CPU portability proof found identical384-dimensional vectors and deterministic repeats, with no new annotations/provider calls.

The explicit development-only scope is `NY_SIMILARITY_DEVELOPMENT_VERIFIER_SCOPE_V1`, `allowed_pool=agent_development`, label/pair caps0, finite verification cap<=32, fixed admitted wall, no retries/resets. It is not a TRAIN scope; `make_same_joke_verifier(*, lane_id, budget_root, scope_ref, resolution='primary', api_key=None)` constructs the actual verifier without dispatching. Existing `CallBudget` + `AstraAnnotator` + `SameJokeVerifier` wiring also accepts it. Every development call is one pair only; labels, variants and batches are refused. Main binds its separate finite allowance; none is granted by this export, and the original32 smokes remain consumed. Full signature, schema, decoder accounting and relocation instructions: `public_bundle1/INTEGRATION_API.md`.

Current CPU regressions:175 PASS, including Main's real-tools CLI tests; `PUBLIC_BUNDLE_CPU_TESTS1.txt`. These are implementation/transport-identity checks, not new scientific calibration. Runnable zero-provider verification from repo root:

```bash
research_loop/workers/r177_caption_game_stage1_20260917/similarity_runtime/.venv/bin/python \
  research_loop/workers/r177_caption_game_stage1_20260917/similarity_runtime/check_public_bundle.py
```

The command checks immutable inventory/source/config/prompt/pins and the actual saved CPU proof. It does not reread private labels, mutate a budget, dispatch a model, retune rho or rewrite the bundle. Canonical safe handoff: `PUBLIC_INTEGRATION_HANDOFF1.json`. All scientific limitations and original evidence below remain in force.

Status: **real CPU encoder, 300 provisional model-labelled pairs, frozen calibration, and real verifier/PixelArchive smokes completed**. This is a Stage1 development instrument, not validated human joke identity or demonstrated child novelty. No R176 artifacts, locked validation, FINAL, learned judge checkpoint or child/arm state were consumed.

## Actual bindings

- Sentence-trained encoder: `sentence-transformers/all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
- All nine weight/tokenizer/model/pooling files pinned in `encoder_acquisition1/ENCODER_MANIFEST.json`, SHA256 `110116b20f71ecbd1149332d0fabbeb1bf15a48d51ff8bc0f80b52eee1f1e2a6`.
- Original masked mean pooling, L2 normalization, 384 dimensions, original 256-token limit; overflow is an explicit error, never silent truncation. CPU-only frozen pretrained backbone, no optimizer, no shared arm cache. The unused BERT pooler is deliberately excluded because sentence mean pooling does not use it.
- Factual scenes and captions came from Ampere's exact TRAIN-only handoff. Its private input SHA256 is `ab14d9424a5d998e7fb64afbee34dc14d35ffbd111e1fb6776e31c5d0cff0d06`; canonical factual fields are canny/location/entities, never uncanny.
- Verifier/labeler route: `openai/openai/gpt-6-astra`; private receipts bind the actual returned model/request/usage, immutable instruction hash and exact request/response bytes. A hosted model route is not an immutable provider weight revision. Every annotation remains provisional, not human truth.
- Runtime config: `campaign1/calibration1/FROZEN_RUNTIME_CONFIG.json`, SHA256 `e2619a1ca22b7d934f317b05ba0dc2ae6708b42562edb66c03ae7920dfa5f27b`.

## Frozen calibration and actual errors

Thirty whole TRAIN contests were selected before label calls: 24 fitting and six calibration holdout, preserving Ampere's disjoint partition. The sample comprises 150 pairs of independently sampled historical captions and 150 model-generated paraphrase-intent pairs; intended paraphrases were subsequently labelled, not assumed true. There are 300 annotation records, including one unresolved fitting pair per resolution. Training has 240 pair slots / 239 binary labels per resolution; holdout has 60 / 60.

The unchanged PixelArchive calibrator selects all three ordered thresholds from fitting labels only. Before any labels, a bijective opaque alias map makes its seeded group split reproduce Ampere's exact fitting/holdout groups. No group is merged or split, no heldout threshold tuning occurs, and an assertion checks exact heldout membership after calibration.

| Resolution | Frozen rho | Holdout false merge | Holdout false split |
| --- | ---: | ---: | ---: |
| Coarse | 0.9759382047403884 | 1/26 (3.85%) | 12/34 (35.29%) |
| Primary | 0.9765189220557066 | 0/30 (0%) | 8/30 (26.67%) |
| Fine | 0.9765189220557066 | 0/30 (0%) | 8/30 (26.67%) |

Thirty separate verification smokes, with caption order reversed, observed 0/15 false merges and 0/15 false splits **against the earlier provisional model labels**. They use the same provider/model/instruction, so they are consistency checks, not independent human validation. Two additional actual PixelArchive integrations passed, including verifier dispatch and exact-caption replay without extra calls; their acceptance flags/scores were synthetic fixtures, not judge validation.

**Important limitation:** the primary retrieval gate misses 8/30 heldout same-joke pairs. The verifier is invoked only above rho and cannot repair those false splits. Novel-pixel counts can therefore be inflated by paraphrases. This is an explicitly provisional Stage1 threshold, not validated novelty. The small six-contest holdout, balanced/generated pair mix, repeated-labeler dependence, one-nearest-representative retrieval and scene-description domain shift all limit generalization. Released TRAIN factual scenes are not an empirical calibration on later local-Qwen scene wording. No threshold was retuned after holdout or verifier results.

## Runtime API

`gpu.ny_caption_similarity` supplies:

- `FrozenCPUEncoder(manifest_ref)`: callable `embed(text) -> vector`, matching PixelArchive. `encode_many()` is bounded, CPU-only and deterministic in the observed proof.
- `CallBudget(root, scope_ref)`: durable pre-dispatch reservations, <=360 label-related calls / <=360 labelled pairs and <=32 verification calls, <=60 minutes, a fixed absolute wall, no refunds or post-dispatch retries. Each lane uses its own root and exact scope binding.
- `AstraAnnotator(budget)`: strict batched JSON annotation with private attributed receipts; secrets never enter request receipts. Generation requests also count against the label-call cap. Failed, incomplete, invalid or ambiguous labels never silently become novelty decisions.
- `SameJokeVerifier(annotator, lane_id=..., resolution='primary')`: callable `(scene, candidate_caption, representative_caption) -> bool`, with lane-bound state and explicit failure on unavailable/ambiguous annotation.
- `archive_from_config(config_ref, encoder, verifier, agent_id=..., contest_id=..., scene=...)`: validates frozen config/encoder/instruction/lane bindings and returns the unchanged `PixelArchive`.

In game integration, pass the encoder callable and the lane's verifier to existing archive/game constructors. Keep classifier/judge scores and visual tools separate. Never share a verifier budget/root or archive state across arms. The completed calibration-smoke scope is **not** an ongoing game-call allowance: all 32 verification smokes are consumed. This implementation does not silently create a new scope, renew a wall, retry failed calls or borrow another lane's budget.

## Runnable commands

From the repository root, this integration-binding command uses the actual encoder and frozen config without reading captions, submitting an archive item, or making another provider call:

```bash
research_loop/workers/r177_caption_game_stage1_20260917/similarity_runtime/.venv/bin/python \
  research_loop/workers/r177_caption_game_stage1_20260917/similarity_runtime/check_integration.py
```

The exact calibration command already run was:

```bash
research_loop/workers/r177_caption_game_stage1_20260917/similarity_runtime/.venv/bin/python -m gpu.ny_caption_similarity calibrate \
  --encoder-manifest research_loop/workers/r177_caption_game_stage1_20260917/similarity_runtime/encoder_acquisition1/ENCODER_MANIFEST.json \
  --encoder-manifest-sha 110116b20f71ecbd1149332d0fabbeb1bf15a48d51ff8bc0f80b52eee1f1e2a6 \
  --pairs research_loop/workers/r177_caption_game_stage1_20260917/similarity_runtime/campaign1/LABELED_PAIRS.private.json \
  --output research_loop/workers/r177_caption_game_stage1_20260917/similarity_runtime/campaign1/calibration1
```

Outputs are exclusive: the completed command cannot overwrite its prior report. CPU-only reproduction requires an explicitly new output directory; do not replay the once-only annotation or verifier-smoke commands. Source the current credential privately only before a separately in-scope real provider invocation; never print or persist it.

Tests: `.venv/bin/python -m pytest -q tests/test_ny_caption_similarity.py tests/test_ny_caption_pixels.py tests/test_ny_caption_game.py` from the repository root, using this runtime's interpreter path. Actual results: 150 PASS before real provider calls, 152 PASS after two non-material reporting/insufficient-label guard regressions. The latter require an actual encoder-verification flag and prevent null labels from counting toward the labelled-pair minimum; the completed calibration also passes these stricter checks, without retuning or additional calls. `campaign1/CPU_GATE.json` pins the pre-provider source and actual CPU provenance. Its exact original source bytes are retained in `empirical_source1/ny_caption_similarity.py`, verified against that SHA; current source and the late snapshot provenance are separately bound in `PUBLIC_READINESS_20260917.json`. Full labelled calibration/call receipts remain private.

## Spend and safe evidence

- 45 label-related requests: 15 variant-generation batches plus 30 ten-pair label batches; 300 pairs charged.
- 32 verification requests: 30 repeat-label checks plus two actual archive integrations.
- 77/77 terminal requests complete, zero failures, retries or missing calls; provider-reported usage 79,509 prompt + 29,839 completion = 109,348 tokens.
- First request 18:56:12 UTC; final terminal 19:02:46 UTC, September17. R177's independent fixed wall is 19:30 UTC; task preparation began 18:40:17 UTC. No GPU used.
- Safe aggregate artifacts: `campaign1/ANNOTATION_PUBLIC.json`, `campaign1/calibration1/PUBLIC_METADATA.json`, and `campaign1/VERIFIER_SMOKES_PUBLIC.json`. Do not open `.private.json` files or `campaign1/calls/` from Main/parenting contexts.

Changed code is confined to `gpu/ny_caption_similarity.py`, `tests/test_ny_caption_similarity.py`, and this `similarity_runtime/` tree. Only explicitly requested operational milestones are appended to COORDINATION. The existing pixel core, game, and API contract remain untouched.
