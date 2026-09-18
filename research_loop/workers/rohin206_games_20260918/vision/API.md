# R209 current node4 integration — September 18, 2026 04:41 UTC

**READY for Main's development game.** Three actual local image→scene HTTP replies completed at 04:40:52 UTC. GPU0 is released to Main and was verified 0MiB at 04:41:02 UTC. The new combined service runs one frozen VLM on physical1, UUID `GPU-4b071167-a06a-773c-f947-60cb8c2f7512`, actual kernel minor2, child PID3987161, approximately19,289MiB. Vision and the private comparator have separate interfaces but serialize requests through the same model. Neither blocks on new training or weight transfer.

Root: `/localhome/local-rohing/rohin206_games_20260918/vision_node4_r209`.

| Artifact/interface | Exact path or value |
| --- | --- |
| Game manifest | `GAME_MANIFEST.json`, SHA256 `b3ccd7f7956d62f622f4af571ed22ba28e2fef4961013bcf45abd7b7b23ebc83` |
| Image packet | `IMAGE_PACKET.json`, SHA256 `2974b6947e9355fe0d4b88c889d2d6816f07d46e7256e5bd2b55207a2923a111` |
| Scene evidence | `GAME_MANIFEST_RECEIPT.json`, SHA256 `56defbd32b6b4169f6123ec7d486727326686d1230363e50c890b9b08b197a12` |
| Vision POST | `http://[REDACTED_ADDRESS]:8178/v1/inspect` |
| `LocalHTTPProvider` constructor endpoint | `http://[REDACTED_ADDRESS]:8178` (without route suffix) |
| Private comparator POST | `runtime_combined/comparator.sock`, route `/v1/compare` |
| Source | `source/gpu/ny_caption_vision.py`, SHA256 `aa49c3e2bf7c7495e8629b7a3fe16f830afc6e48d77042fe9f7eec110dde3f18` |
| Sidecar source | `source/research_loop/workers/rohin206_games_20260918/vision/service.py`, SHA256 `39471b0cc521a309e34b69ef869d236f8e24e00f44da9a4b88e21c91cbbdfa7b` |
| Native receipts | `runtime_combined/incarnation_1789706403745689652/{LOADED,IMAGE_TO_SCENE,LISTENING,MODEL_MANIFEST}.json` |

Use the exact receiving vision client source: its receipt validation deliberately rejects a mismatched source hash or prompt. The scene manifest has only documented game fields; receipt metadata is separate. Raw observations are unedited model descriptions, not independently verified scene truth. Actual HTTP outputs were73,84,149 tokens; no private scalar references or captions were consulted. Comparator is LOADED/listening, not yet an actual caption-comparison receipt.

The first service's malformed JSON was preserved, not repaired. The new factual prompt requests short plain prose with uncertainty; the existing canonicalizer preserves it verbatim and identifies absent separate uncertainty as an operator format notice. All safety refusals, measured token caps, EOS checks and raw hash bindings remain. **41 focused receiving tests passed.** Exact Qwen revision remains `cc594898137f460bfe9f0759e9844b3ce807cfb5`; packages remain as recorded below. Model is the existing node4 snapshot, not another16GB transfer.

Current hard wall is **September18,2026 18:00UTC**, inherited from node4's existing lease budget; external runtime and cleanup end before it. There is no one-hour self-kill. Old node4 source/runtime directories and failed receipts remain preserved. Whole ovx5 is reserved to Leibniz; its vision/comparator were never dispatched, and its launcher remains stopped. Do not use the historical allocation/endpoint/cutoff below.

## Historical, superseded ovx5 plan

Only physical4 (comparator) and5 (vision) are assigned to this operator. Both use frozen local Qwen2.5-VL-7B-Instruct revision `cc594898137f460bfe9f0759e9844b3ce807cfb5`; actual receiving versions are Torch2.13.0, Transformers5.5.3, Pillow12.3.0, huggingface-hub1.30.0, safetensors0.8.0.

Remote worker root: `/localhome/local-rohing/rohin206_games_20260918/vision`.

## Vision5

Loopback POST `http://[REDACTED_ADDRESS]:8177/v1/inspect` accepts exactly `{"image":"released_handle","question":"factual question"}`. Core `LocalHTTPProvider` remains the client. Copy the exact corrected `gpu/ny_caption_vision.py` to its source closure because clients verify source hashes and replay raw-to-canonical binding. Output contains observations, uncertainty and actual measured receipt. Raw output is preserved, never syntax/semantic repaired; format canonicalization is disclosed. Unstructured plaintext retains the raw observations verbatim and labels absent model uncertainty with an operator notice. Invalid/unsafe/truncated structured output still fails closed.

`runtime_vision/incarnation_*/IMAGE_TO_SCENE.json` is required evidence of the real image→scene call. LOADED or LISTENING alone is not that evidence. Startup probes only the first of the three already-released R177 development images, with a fixed factual question. No synthetic success claim. The immutable image allowlist currently contains three released handles; a larger released-development packet must be explicitly bound before serving additional images. No LOCKED/FINAL images or hidden panel data are read.

## Comparator4

Private Unix-domain HTTP endpoint: `runtime_comparator/comparator.sock`, POST `/v1/compare`. Input exactly `{"case_key":"64-lowercase-hex","image":"released_handle","caption":"candidate data"}`. Rejects lane, source/origin, prior scores, panel, history and additional fields before model invocation. Only image and caption enter the model prompt; case_key is a join key, not prompt content.

Returns the R168-style three provisional humor probabilities, scene-fit probability and uncertainty. This is not an acceptance, tau, percentile or calibrated-truth gate. No normalization of invalid probabilities and no proposed caption repair. Main owns scalar rankers, contrast construction and aggregation. The source-bound `MODEL_MANIFEST.json` supplies Qwen/local/frozen identity for Main's existing blind-comparator aggregation. All comparator receipts/socket directories are private; do not forward case text, raw results or private panels to parents. No comparator requests or success claims exist merely because its server is listening.

## Lifetime and supervision

External systemd control-group device confinement permits only the role's one actual GPU plus shared control/UVM devices. Each child verifies all seven foreign GPU minors are inaccessible. A persistent CPU supervisor restarts only the exited service process, never replays a request, and remains inside one finite external RuntimeMaxSec. There is no one-hour self-kill and no use of the nominal training deadline.

Current conservative cutoff: **September18,2026 10:00UTC**, including cleanup. This is earlier than the earliest date-only September19 lease report in every civil timezone; the newer authoritative hardware receipt reports September29 but supplies no exact lease timestamp. The cutoff is deliberately conservative, not a claim that the real lease ends10:00. No lease extension or purchase is performed. Main/Fable can supply the exact existing lease bound for a later scoped configuration; this uncertainty does not block current operation.

## Receiving record

39 targeted tests passed on the actual ovx5 venv before dispatch. Three image byte hashes verified. Exact pinned16GB model transfer/hash completion remains distinct from GPU dispatch, model LOADED, actual IMAGE_TO_SCENE and first comparator inference. No Main judge/game files modified.
