# R177 LOCAL vision WIP preserved — 2026-09-17

Actual state at reassignment: specification review and public model-identity
verification only. No vision code or CPU tests had been written. The proposed
paths `gpu/ny_caption_vision.py`, `tests/test_ny_caption_vision.py`, and
`research_loop/workers/r177_caption_game_stage1_20260917/vision/` did not exist
at the final read-only check. Do not report them as ready implementation.

Verified using the official Hugging Face model metadata API:

- Model: `Qwen/Qwen2.5-VL-7B-Instruct`.
- Resolved revision: `cc594898137f460bfe9f0759e9844b3ce807cfb5`.
- API: `https://[REDACTED_HOST]/api/models/Qwen/Qwen2.5-VL-7B-Instruct`.
- Metadata reported five safetensors shards and 8,292,166,656 BF16 parameters.
- Official pinned README, processor configuration and generation configuration
  still require successful retrieval; those follow-up requests were interrupted.
- Mandatory web-tool retrieval was attempted but returned no usable content;
  the metadata identity above was retrieved by HTTPS directly. No invented
  source citations or claim of a completed processor/API validation.

Reviewed contracts:
`research_notes/forwarded/final_run_2026-09-17/AGED_AGENT_CLONE_EVALUATION_AND_PARENTING_HANDOFF.md`
revision 5, section 7, and
`research_loop/workers/r177_caption_game_stage1_20260917/pixels_game/API_CONTRACT.md`.
Rohin161 overrides: DEVELOPMENT PARENTED/UNPARENTED are both learning lineages;
FINAL both parent-free; Stage3 deferred. Required callable injection:
`inspect_provider(image, question) -> gpu.ny_caption_game.VisualResult`, whose
`observations` and `uncertainty` fields are nonempty strings.

Remaining work: stateless local-only provider and optional private local HTTP
transport, byte-hash allowlisted development images, frozen processor/prompt/
decoding settings, exact 128-question/256-response token limits, strict JSON
without repair, explicit refusal of caption/joke/ranking requests, measured
token/latency/truncation receipts, mocked CPU tests. No GPU model was loaded,
no weights were downloaded, no credential settings were changed, and no
real-image smoke was attempted. Main must bind CPU/device/lease budget first.

Image-only packet needed from Ampere: explicit DEVELOPMENT-only allowlisted
opaque handles, local image file paths, SHA-256 and byte counts, with at least
two actual development images for the post-admission factual smoke. No FINAL
identifiers, references, historical captions, judgments, scores, or arm history.

Boundary incident: an initial overly broad recursive search unintentionally
printed private dataset-manifest metadata. The search was immediately narrowed;
that metadata was not used in any code, image selection, or observation. No
dataset/images were subsequently opened. Preserve this disclosure rather than
claiming a completely clean read boundary.
