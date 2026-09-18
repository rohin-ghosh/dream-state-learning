# Calibrated real similarity integration

This public bundle contains no pair/caption/label records, private receipts, or private pair references. The encoder weights/tokenizer are the original public sentence-trained MiniLM snapshot. All thresholds are an exact extraction from the existing frozen calibration, never a synthetic fallback. `BUNDLE_MANIFEST.json` hashes every exported file except itself; pin its SHA separately.

## Existing CLI-compatible config

`similarity_runtime.json` is a new public, hash-bound `NY_FROZEN_SIMILARITY_RUNTIME_V1` config for Main's `gpu.ny_caption_stage1_tools` bundle field `similarity_runtime`. It retains the exact instrument/config, drops private references, and points to the actual copied embedding snapshot. The original campaign config and its pin remain unchanged. `pixel_config.json` is the plain `PixelConfig` constructor mapping.

`embedding_snapshot.json` is portable: its nine exactly pinned files must remain in sibling `embedding/`. `similarity_runtime.json` contains an absolute snapshot reference for the current checkout. After moving the bundle, create a new explicitly hash-bound local config changing only that path; do not alter thresholds, snapshot bytes, original receipts, or any active config. Direct constructor integration can instead bind the new snapshot location without creating a full config.

```python
import json
from pathlib import Path
from gpu.ny_caption_pixels import PixelArchive, PixelConfig
from gpu.ny_caption_similarity import FrozenCPUEncoder, make_same_joke_verifier

bundle = Path("ABSOLUTE_PUBLIC_BUNDLE_PATH").resolve()
pixel_config = PixelConfig(**json.loads((bundle / "pixel_config.json").read_bytes()))
encoder = FrozenCPUEncoder({"path": str(bundle / "embedding_snapshot.json"),
    "sha256": "EXACT_SNAPSHOT_SHA_FROM_HANDOFF"}, threads=2)
verifier = make_same_joke_verifier(
    lane_id=agent_id,
    budget_root=private_lane_budget_directory,
    scope_ref={"path": absolute_Main_scope_path, "sha256": exact_Main_scope_sha256},
    resolution=pixel_config.resolution,
)
archive = PixelArchive(agent_id, contest_id, canonical_scene, pixel_config,
    encoder, same_joke_verifier=verifier)
```

The factory signature is `make_same_joke_verifier(*, lane_id, budget_root, scope_ref, resolution='primary', api_key=None)`. It constructs a callable `(scene, candidate_caption, representative_caption) -> bool` without any provider call. It also works as the existing `CaptionGame(..., embed=encoder, same_joke_verifier=verifier)` injection. Main's existing `CallBudget` + `AstraAnnotator` + `SameJokeVerifier` construction is equivalent and accepts the new scope.

## Separate development verifier budget

Do **not** relabel development captions as TRAIN. Main binds a separately allocated scope using these fields (this documentation is not a provider-call authorization):

```text
schema: NY_SIMILARITY_DEVELOPMENT_VERIFIER_SCOPE_V1
issuer: Main/Astra
no_reset: true
allowed_pool: agent_development
lane_id: exact agent namespace, 1–60 ASCII letters/digits/underscores/hyphens
label_call_cap: 0
pair_label_cap: 0
verification_call_cap: integer 0–32, drawn from Main's admitted development allowance
active_seconds_max: integer 1–3600
absolute_end_unix: actual fixed admitted deadline as numeric Unix seconds
retries: 0
provider_model: openai/openai/gpt-6-astra
locked_validation_reads: 0
FINAL_reads: 0
```

Each verifier call reserves one verification request for one pair. Label/variant operations and multi-pair verification batches are refused under this scope. The unchanged verifier asks for all three same-joke resolutions, returning the configured resolution; default completion maximum is4096 per request (at32 calls,131072 maximum completion tokens). Payloads and per-call time are independently bounded. The effective deadline is the earlier of the fixed absolute wall or first reservation plus active seconds; no deadline reset, refunds, hidden retries, or scope rebinding. Main must preserve each lane's existing budget root across restarts and allocate disjoint finite allowances across lanes; copying a scope to another root is not permission for a new allowance. Ambiguity, timeout, exhausted budget, or invalid JSON fail closed; they are never silently interpreted as novelty. Keep all request/response/label receipts private.

All32 earlier calibration verification smokes are consumed. The completed TRAIN scope `NY_SIMILARITY_BOUNDED_SCOPE_V1` is preserved and is not the development scope. This export grants **zero** additional calls. Source the current `~/.codex/nvidia.env` privately before Main's authorized real launch; the factory reads `NVIDIA_API_KEY` at construction if `api_key` is omitted. Never log that value. CPU-only encoder dependencies are in `RUNTIME_DEPENDENCIES.txt`; model loading is local-only with remote code disabled.

## Empirical limits

300 provisional model-annotated pairs;24 fitting whole contests /6 heldout contests;240 fitting slots (239 binary per resolution) /60 heldout. Primary/fine rho is0.9765189220557066; coarse rho is0.9759382047403884. Primary heldout false merges0/30 and false splits8/30. The latter26.67% retrieval misses cannot be repaired by the verifier, which is called only above rho, so apparent novelty can be inflated by paraphrases. These are provisional retrieval metrics, not end-to-end archive error or human truth.

30 reversed-order verification checks observed0/15 false merges and0/15 false splits against previous annotations from the same model/instruction, not independent ground truth. Two actual archive smokes passed, using synthetic acceptance fixtures rather than a judge-quality claim. TRAIN factual scene wording, generated/balanced pairs, six-contest holdout and one-nearest-representative retrieval limit generalization to live game text. No FINAL, locked-validation, R176 output or cross-arm state is included. No new labels or provider calls accompany the portability/factory CPU tests.
