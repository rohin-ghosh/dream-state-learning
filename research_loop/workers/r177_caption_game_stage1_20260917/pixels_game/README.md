# Stage 1 pixel archive + game tool core

Use `API_CONTRACT.md` for Main's integration surface and `STATUS.json` for the
current handoff. Rohin161 supersedes the older FROZEN/LEARNER lane assumption:
lane IDs are generic; Main configures PARENTED/UNPARENTED learning lineages and
LOCAL Qwen vision. This component never configures learning, parenting or FINAL.

## CPU contract smoke

From the repository root, choose a new output directory on every run:

```bash
python3 -m research_loop.workers.r177_caption_game_stage1_20260917.pixels_game.cpu_smoke \
  --output-dir /tmp/ny-caption-stage1-cpu-smoke-NEW
```

This creates 300 synthetic labeled pairs, synthetic coordinate vectors, a
provisional calibration report and isolated PARENTED/UNPARENTED game snapshots.
It tests the data flow, not real model quality. No dataset, GPU, provider,
gateway, plugin or image-inference call is made. Synthetic scores, labels and
thresholds are fixture values, not usable evidence of humor/similarity quality.

## Focused tests

```bash
UV_CACHE_DIR=/tmp/r177-caption-pixels-game-uv-cache UV_PYTHON_DOWNLOADS=never \
  uv run --no-project --with pytest python3 -m pytest -q \
  tests/test_ny_caption_pixels.py tests/test_ny_caption_game.py
```

The core and smoke command themselves require only Python's standard library.
Use the project's Python environment directly when it already has pytest.

## Evaluator-only calibration CLI

```bash
python3 -m gpu.ny_caption_pixels calibrate \
  --pairs /path/to/local/scene_caption_pairs.json \
  --vectors /path/to/local/precomputed_vectors.json \
  --config /path/to/local/input_pixel_config.json \
  --heldout-fraction 0.3333333333333333 --seed 177 \
  --output-dir /path/to/new/calibration-output
```

`--pairs` contains a JSON list (or `{"pairs": [...]}`) of `LabeledPair` objects
from the API contract. Caption pairs and their labels are evaluator-private;
never pass this input to a game, child or parent. Use around 300 annotated pairs
to start, with same/different joke labels rather than top-N distances or arm
wins. LLM/automatic labels plus a small optional human spotcheck are supported;
automatic-only status remains provisional and creates no human-panel gate.

`--config` is a `PixelConfig` JSON object with explicit model ID, immutable model
revision, input format and provisional thresholds. Calibration ignores its
initial threshold values. `--vectors` is:

```json
{
  "embedding_model_id": "exact-frozen-pretrained-model-id",
  "embedding_revision": "exact-immutable-revision",
  "input_format": "scene_caption_v1",
  "source_kind": "frozen_pretrained",
  "vectors": {"sha256-of-embedding_text(scene,caption)": [0.4, 0.8]}
}
```

Use `embedding_text`/`embedding_key` from `gpu.ny_caption_pixels` so the exact
JSON input format is shared. Main supplies the frozen pretrained encoder;
the CLI verifies declared vector/config provenance and normalizes vectors but
does not prove a particular model produced them. `source_kind=synthetic_fixture`
is only for fixtures and cannot be presented as human embedding validation.
Record the actual encoder's producer receipt outside this contract.

The split is seeded and grouped by contest (or a declared shared-scene group).
Only training labels choose thresholds. Selection minimizes the sum of balanced
false-merge/false-split rates at the three resolutions, constrained to ordered
coarse <= primary <= fine. Held-out FPmerge/FNsplit counts, rates, pair IDs and
spotcheck-only metrics are reported separately. Missing label classes or
holdout groups are explicit warnings; unavailable thresholds remain null.
No output directory is overwritten. The report includes input file hashes.

## Boundaries and limitations

### Same-lineage restart (ready for Main)

Persist `game.snapshot()` privately and atomically alongside the native stream
checkpoint. Recreate explicit bindings and call:

```python
restored = CaptionGame.from_snapshot(
    saved_snapshot,
    agent_id=agent_id,
    lane=lane,
    manifest=manifest,
    config=game_config,
    pixel_config=pixel_config,
    embed=frozen_encoder,
    judge=scene_caption_judge,
    inspect_provider=local_qwen_vision,
    count_tokens=local_token_counter,
)
```

`PixelArchive.from_snapshot(snapshot, agent_id, contest_id, scene, config, embed,
*, max_submissions=10000, same_joke_verifier=None)` is available separately.
Both classes also expose `restore(snapshot)` on an empty constructed instance.
Nonempty restores are rejected rather than silently replacing live state.
Optional-verifier presence must match the persisted implementation.

Restoration performs no encoder, judge, visual, verifier or tokenizer call. It
reconstructs chronological membership from the stored vectors, checks nearest
matches and immutable representatives, and compares the reconstructed closure
with persisted pixels. It validates scene/agent/lane/config/image-handle
bindings, cached responses, acceptance conjunction, visual cache/history,
bounded retry sequences, budgets and accounting. All state is committed only
after checks pass. Errors are `SnapshotError`; the target stays empty.

Existing game schema 1 is read without replay; schema 2 records accounting
deltas for every counter-changing operation. Schema-1 counters are retained as
an explicit legacy baseline, checked against events and known token bounds;
old logs cannot reconstruct exact failed-call token counts that were never
recorded. No such observations or missing ledger rows are invented. New actions
are exactly accounted, and another reload preserves the migrated baseline.
Main must bind actual model/tokenizer revisions and image contents externally:
the core can compare handles/configs but cannot identify a callable's weights
or authenticate a modified checkpoint file. This is closure validation, not
cryptographic authentication of untrusted state.

### Remaining limits

- Exact caption **bytes**, per instance and cartoon, identify a submission.
  Retries return the original result with `replayed=true`; they do not earn
  discoveries, consume unique-caption capacity, embed again or score again.
  Pixel configuration/encoder changes require new archives and consistent
  offline rescoring, never editing a running archive's representatives.
- All accepted captions compare only with immutable representatives. A better
  delivery is a member, not a replacement representative. Ties use the oldest
  representative. Optional contextual verification only checks the nearest
  above-threshold representative; it is not a mandatory second model or an
  excuse to use the subordinate v2 archive algorithm instead of rev5.
  Stored trace distances are nearest-only to avoid quadratic history size;
  every immutable representative is searched, and stored vectors permit
  offline reconstruction of other distances. Sequential order can change
  counts; the CPU suite explicitly demonstrates this limitation.
- Judge adapters receive only `(canonical_scene, candidate_caption)`. LOCAL
  Qwen vision adapters receive only `(image_handle_or_bytes, question)`. Main
  owns the frozen factual-only instructions, actual tokenizer/model and image
  hash checks. The core does not load images or call any network/model service.
- The lexical injection guard rejects recognized tool-control attacks and
  never executes submitted text. It is conservative and not a complete
  semantic attack classifier. Quoted attacks can be false positives; unseen
  attacks require adapter-side safeguards and automatic challenge checks.
- Malformed/oversized visual results are withheld, not truncated into invented
  observations. Explicit `TransportError` permits at most two retries. Faults
  return `pause_required=true`; no fallback observation or fabricated score is
  created. Main must honor the pause signal. Logical cache access is charged.
  The response-token check counts observations plus uncertainty joined by a
  newline using Main's injected tokenizer; Main also caps the actual LOCAL
  Qwen generation at 256 tokens, including any provider formatting overhead.
- Snapshots preserve per-instance archives, trace/membership, result cache,
  budget counters and events. Main owns private atomic persistence and restart
  binding; this core has no shared filesystem state. Restore APIs do not reset
  budgets or call models to reproduce old responses.
  Event history is capped; exhaustion stops new work rather than evicting
  evidence. Invalid or failed attempts do not become behavioral rejections.
- `external_visual_tokens` means measured provider-response tokens distinct
  from child output, **not a gateway call**; the provider must be local Qwen.
  It cannot estimate unknown tokens from failed transport attempts; those are
  counted as failed attempts. Main records real local compute/cost separately.
- No real encoder, judge or visual model was exercised here. Held-out
  human-rated dataset validation belongs to Ampere; actual local adapters,
  image routing checks, continual-learning/sleep and run orchestration belong
  to Main. A new human panel is not a Stage 1 requirement. This handoff makes
  no validated scoring, LoRA-learning, final-evaluation or scientific claim.
