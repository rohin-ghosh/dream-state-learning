# LOCAL vision API — R177, resumed by Rohin167

## Actual runtime status — 2026-09-17

The pinned local model is loaded and the sanctioned local forward is listening
at `http://[REDACTED_ADDRESS]:8177`, but the visual tool is **not integration-ready**.
Seven actual generations on Main's exact three released images yielded five
strict JSON parse failures and two exact-schema failures. No accepted visual
result or canonical scene was produced; no output was repaired. The live source
SHA256 is `b6170ddf186860ae5bf3d4aa8db2d7f0816b1b52b7703efc31a00f443b466e9f`.
The client must use those same bytes. Exact load/listening, device, admission,
failed-request and smoke receipt pins are in `SERVICE_STATUS_20260917T1938Z.json`.
The original service deadline is 2026-09-17 20:30:25 UTC; no process was stopped
and the live source was not changed after launch. Judge work remains independent.

The old `DEVICE_SERVICE_CPU_1789671774507616770.json` is preserved but invalid
for physical5 admission: it tested minor5. The repaired receiving source passes
37 CPU tests and an actual strict-slot probe: physical5's UUID maps through NVML
and the kernel to minor6; minor6 opens and `[0,1,2,3,4,5,7]` are denied.

Judge training does not wait for this service. This is a separate V-tool for
both DEVELOPMENT learning lineages; no FINAL implementation or parent bridge.

```python
from gpu.ny_caption_vision import ImagePacket, LocalVisionProvider, LocalHTTPProvider, ReceiptWriter, QwenBackend

packet = ImagePacket.load(development_image_only_packet_path)
backend = QwenBackend.load(snapshot_path, development_image_only_packet_path,
                           bound_admission_path, bound_admission_sha256)
inspect_provider = LocalVisionProvider(packet, backend, receipt_sink=ReceiptWriter(receipt_directory))
visual = inspect_provider(opaque_image_handle, factual_question)
```

`visual` is exactly `gpu.ny_caption_game.VisualResult(observations, uncertainty)`.
`provider.inspect(image, question)` additionally returns the measured receipt.
Game integration uses the callable unchanged; no arm/judge/history is accepted.
Errors raise `VisionError`, explicit policy refusals raise `VisionRefusal`.
Neither contains a fabricated visual result. Only actual local network faults
raise the game's retryable `TransportError`; there is no fallback or automatic
retry in either adapter. Main owns game caching, budgets and parent/masking.

For a separate GPU service, run `python -B -m gpu.ny_caption_vision --help`.
The CLI requires packet, pinned snapshot, exact admission file/hash, receipt
directory and a local port. Bind is only `[REDACTED_ADDRESS]`. Reach it through an approved
SSH local forward, then inject `LocalHTTPProvider('http://[REDACTED_ADDRESS]:8177', packet,
receipt_sink=ReceiptWriter(client_receipt_directory))`. Hostnames, external IPs,
HTTPS gateways, redirects and environment proxy routing are not supported.
Server payload is exactly `{"image": "opaque_handle", "question": "factual question"}`.

## Released game image-only packet

Main supplied and receiving-verified the exact three-image release at
`/localhome/local-rohing/orch_r177_main_game_images_20260917_v1/IMAGE_PACKET.json`,
SHA256 `b897b91143f18212ff280f2773c84cd01dfecab25e89b13e9ce0b6b7b2aae211`.
No different selection was made. The schema below describes this interface;
placeholder values are not additional images or an alternative release.

```json
{
  "schema": "R177_VISION_IMAGES_V1",
  "mode": "DEVELOPMENT",
  "images": [
    {"handle": "opaque_handle", "path": "/absolute/local/image.png", "sha256": "ACTUAL_64_HEX_SHA256", "bytes": 123}
  ]
}
```

The uppercase hash and byte count above are schema placeholders, not runnable
data. Supply exactly three released agent-development images for Main's game
manifest; the factual smoke uses the first two. This game-only release is
separate from Ampere's judge-training descriptions. Image
paths must refer to server-local files; client packet paths are not sent.
Packets reject extra fields: no canonical descriptions, captions, judgments,
ratings, arm/history metadata or FINAL identifiers. Every inference rereads
and hashes the bytes, rejects symlinks/nonfiles/size mismatches, and decodes that
same in-memory byte copy. Only RGB pixels and the question enter the model.

## Frozen inference and accounting

Model `Qwen/Qwen2.5-VL-7B-Instruct`, HF commit
`cc594898137f460bfe9f0759e9844b3ce807cfb5`. Official primary retrieval and hashes
are in `PRIMARY_SOURCE_RECEIPT.json`; all five weight shards are checked against
official LFS SHA256, processor/tokenizer files against their official Git blobs.
The module fixes processor pixel limits, slow processor, RGB decoding,
system/question template, greedy generation, BF16, eager attention, one GPU,
library versions, EOS tokens and max256 new tokens. Max128 question tokens are
measured using that processor's tokenizer, not estimated or truncated.

Receipts report actual expanded input IDs, generated IDs (including EOS),
visible-context token count, synchronized generation latency, preprocessing and
decoding latency, total wall latency, termination/truncation and content hashes.
Question/image data is not logged as text. Mock tests label their backend as a
mock, require an explicit test-only constructor flag, and cannot be accepted as
actual Qwen by the loopback client. Malformed/duplicate/extra-key JSON,
nonstring/missing uncertainty, unsafe output and cap termination yield errors;
there is no JSON repair or partial-observation delivery. Lexical refusal tests
and a fixed prompt are not claims of complete adversarial robustness. Actual
image factual accuracy is not graded; current real-image output-contract
failures are recorded separately from CPU tests and successful model loading.
The game separately counts visible result strings using its child tokenizer;
the receipt's generated-ID count additionally includes JSON syntax and EOS.
Main should retain both counters rather than equating visible context with
actual external generation compute.

## Post-admission factual smoke

`PYTHONPATH=. python -B research_loop/workers/r177_caption_game_stage1_20260917/vision/smoke_client.py
--packet RELEASED_IMAGE_PACKET --endpoint http://[REDACTED_ADDRESS]:8177 --output FRESH_SMOKE_DIRECTORY`
is a client command, not a model launcher. It requests the first two handles in
the released packet order with the same preregistered factual question, preserves
actual service receipts/results, and never repairs or automatically retries.
An existing output directory is refused. Functional success is not independent
factual-accuracy validation or judge calibration. The initial smoke ran and
failed closed. Two separately recorded question variants also failed; all
attempts remain under `runtime1_client/`, with seven exact server-side receipts
mirrored under `runtime1_receiving/runtime1/receipts/`. No further requests are
being issued by this worker. Rejected raw response text was not retained by this
revision, so hashes/error codes do not identify the exact syntax or unexpected
keys; do not invent that diagnosis or a canonical scene.

## Existing admission/budget binding

Main's 2026-09-17 update confirms node4 physical5 and at most one GPU-hour under
the existing lease, with Builder execution after CPU/provenance and fresh strict
device checks. No additional conceptual review is pending. The earlier request
for an allocation is superseded, not evidence that a service is live.
The strict-slot handoff and exact image release subsequently resolved both
missing inputs. `MAIN_BINDINGS_20260917T1915Z.json` is historical, superseded by
`SERVICE_STATUS_20260917T1938Z.json`. The actual admission is mirrored at
`runtime1_receiving/runtime1/ADMISSION.json`, SHA256
`e82577571c3b4741cb37f6dcd9d6f91074d91b95ddc74f73d96f4677fd3b6770`.

`validate_admission` checks exact code/packet/snapshot evidence hashes,
host/UUID, receiving CPU proof, unchanged lease wall, fresh privileged-clear
device report, UUID-only visibility and actual denial of seven foreign minors.
The loader verifies membership in its exact bound service, either the own
`orch-r177-vision-*.service` or an exact source/configuration-bound
`orch-r177-slot5-<32 hex>.service` from Main's unchanged strict-slot wrapper, active
closed/strict DevicePolicy, control-group cleanup and SendSIGKILL. It reads the
actual systemd RuntimeMaxUSec plus at-most-30-second TimeoutStopUSec and requires
their sum inside the bound hour and existing lease. For a one-hour allocation,
an example is RuntimeMaxSec=3570 and TimeoutStopSec=30, not a 3600-second runtime
plus an unaccounted cleanup interval. The request loop also checks the verified
service deadline; it is not the sole timeout during a stalled model call.

Admission schema: `R177_LOCAL_VISION_ADMISSION_V1`, `approved: true`,
`physical: 5`, `kernel_minor: 6`, `gpu_uuid`, `host_sha256`, `code_sha256`, `packet_sha256`,
`snapshot_manifest_sha256`, `not_before_unix`, `hard_end_unix`,
`max_gpu_seconds <= 3600`, `device_checked_unix`, `service_unit`, and `cpu_receipt`,
`device_receipt`, `lease_receipt` objects each containing exact `path`/`sha256`.
Strict-slot units additionally require `outer_slot_config` with exact path/hash
and the actual source, owner, device and cleanup-budget bindings. The owner entry
is `owner_entry.py`; its `serve` action consumes the exact metadata path/hash,
revalidates the untouched wrapper, fresh scan, kernel cgroup, owner-exec PID and
containment proof, writes a one-shot admission, and then calls the local loader.
CPU receipt must include PASS, bound code hash and `gpu_model_loaded: false`.
Device receipt is the unchanged strict privileged scan (`clear`, `scanner_euid`,
`blocking_reasons`, `gpu.uuid`). Lease receipt must expose its existing
`hard_end_unix`; the model deadline may not exceed it. This binds the existing
requested admission, not a new architecture or scientific approval gate.
