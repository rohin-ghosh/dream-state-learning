# LOCAL Qwen V-tool — Gauss / Main coordination

Rohin167 resumes the local V-tool independently of Ampere's neutral-description
judge training on node4 physical2. No judge or training dependency is asserted.

Requested device: node4/a40r physical5,
`GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30`.
Proposed bound model/service budget: at most one GPU-hour, inside the existing
lease and strict single-device service. Gauss: please bind the current physical5
reservation/admission and receiving CPU/device/lease evidence before model load.
No physical2,6,7 allocation is requested. CPU implementation, official pinned
metadata retrieval, read-only capacity checks and own-root public-weight staging
can proceed without starting a GPU model. No hosted endpoint or fallback.

Provider API: `inspect_provider(image_handle, question) -> gpu.ny_caption_game.VisualResult`.
Only verified image pixels and the question reach Qwen, with fixed instructions,
processor and decoding. No judge, references, descriptions, arm IDs or history.
Responses contain strictly parsed `observations` and `uncertainty`; failures and
policy refusals are explicit errors, never invented visual observations.

Ampere image-only packet needed: DEVELOPMENT-only opaque handles, absolute local
image paths, SHA256 and byte counts, including two actual images for the admitted
factual smoke. Do not send reference captions, neutral training descriptions,
ratings, FINAL IDs/images or historical caption data. Model loading and actual
two-image smoke remain unclaimed until measured receipts exist.

Frozen model: `Qwen/Qwen2.5-VL-7B-Instruct`, revision
`cc594898137f460bfe9f0759e9844b3ce807cfb5`.
Question cap128 and generation cap256; no silent input truncation or JSON repair.
Implementation write set: `gpu/ny_caption_vision.py`,
`tests/test_ny_caption_vision.py`, and this directory. Main owns runner/parent
bridging; Ampere can continue judge training independently.
