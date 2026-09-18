# Main integration handoff — 2026-09-17

This describes the interface, not an available runnable manifest. The model is
now loaded and the service is reachable, but all seven actual requests failed
strict output validation; no canonical scenes are available. Current exact pins
and failure evidence are in `SERVICE_STATUS_20260917T1938Z.json`, superseding
the historical `MAIN_BINDINGS_20260917T1915Z.json`. Main owns
`gpu/ny_caption_stage1_tools.py` and the real-component smoke glue.

## Portable public game manifest

`DevelopmentManifest.from_mapping(document)` accepts these game-only fields:

- `mode`: `DEVELOPMENT`.
- `development_contest_ids`: exactly three distinct released development IDs.
- `contests`: exactly three records with `contest_id`, `canonical_scene`, `image`,
  and `split`. The IDs must match the allowlist; `split` is `agent_development`.
- `image`: the released opaque handle, not a machine-local path.
- `canonical_scene`: neutral factual text derived from the actual pinned local
  Qwen response, retaining its uncertainty. No fabricated substitute, judge-only
  training description, reference caption, score or label is acceptable.

Omit `reserved_final_contest_ids`: the game supplies its empty default. Do not
fetch FINAL identifiers to populate an optional field. Do not add provenance
keys to the strict game manifest. Keep code/model/prompt, image and actual result
receipt pins in a separate metadata sidecar. Preserve exact raw observations and
uncertainty there; no silent repair or unrecorded paraphrase.

No canonical scene descriptions are available yet, so no runnable three-record
game manifest has been manufactured. Main's exact released image packet is now
available, pinned to `b897b91143f18212ff280f2773c84cd01dfecab25e89b13e9ce0b6b7b2aae211`.
This is a separate explicit game-development release, not Ampere's judge-training
descriptions. The remaining blocker is actual output-schema compliance, not
image data, allocation or another conceptual approval.

## Vision packet and transport

`ImagePacket.load(packet_path)` consumes exactly `schema`, `mode`, and `images`.
Use `schema=R177_VISION_IMAGES_V1`, `mode=DEVELOPMENT`, and three released image
records, each with exactly `handle`, `path`, `sha256`, `bytes`. The server verifies
the bytes from each absolute local PNG/JPEG path before every model call. The
client only needs the matching allowlist and image pins; its packet paths are
not dereferenced by `LocalHTTPProvider` and are never transmitted.

```python
from gpu.ny_caption_vision import ImagePacket, LocalHTTPProvider, ReceiptWriter

provider = LocalHTTPProvider(
    endpoint,
    ImagePacket.load(packet_path),
    receipt_sink=ReceiptWriter(client_receipt_directory),
)
visual = provider(image_handle, factual_question)
```

The return is exactly `gpu.ny_caption_game.VisualResult(observations, uncertainty)`.
Only `image` and `question` are sent to `POST /v1/inspect`. The configured endpoint
is `http://[REDACTED_ADDRESS]:8177`; a sanctioned SSH local forward is required from another
machine. The bounded forward is now running; its exact launch receipt is
`runtime1_client/FORWARD_STARTED.json`. Do not create a duplicate forward on the
occupied port or stop its owner. An approved forward on another client can use
`bash gpu/a40r_ssh.sh -N -o ExitOnForwardFailure=yes -L [REDACTED_ADDRESS]:8177:[REDACTED_ADDRESS]:8177`
after the actual bounded service is listening; do not claim reachability from
the configured address alone. If that local port is occupied, bind a distinct
loopback port and report its actual endpoint without interrupting its owner.

The client requires the exact pinned `gpu/ny_caption_vision.py` bytes used by the
server. It validates actual model, image, question, prompt, decoding and token
receipt bindings. Staged CPU tests, a TCP connection alone or a configured model
name do not constitute a successful image result.
