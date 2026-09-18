# R223 native caption service — CPU implementation, not live adoption

Owner: this worker owns `gpu/ny_caption_life.py`, `gpu/ny_caption_life_service.py`,
freeform extraction, continuous controller and tests. Turing confirmed no shared
library edits. Turing/Main alone coordinate P3/scorer adoption; Jason/Main own
node2 GPU6. No existing life, pinned source or novelty archive was changed here.

## Native learner on node2 GPU6

The implemented Unix-socket API stays compatible with the native hook:

```python
from gpu.ny_caption_life import request
reply = request(socket_path, {
    "kind": "TRAIN_CHILD_RESPONSE",
    "record_index": actual_response_index,
    "record_sha256": actual_response_record_sha256,
}, {"THINK": actual_think_tokens, "ACT": actual_act_tokens, "LEARN": actual_learn_tokens})
```

The service reads the actual journal RESPONSE and verifies the contiguous,
hash-linked COMMITTED + R184_STAGE ACT chain. No caller-provided caption text or
fabricated native origin is accepted. Start a separate service/session per life,
using the existing `python -m gpu.ny_caption_life_service` deployment arguments;
`--life-root` must be that learner's actual journal root and `--top-k 50`.
Game/data/image/judge/encoder/pixel/relevance manifests remain Main's exact approved
bindings. No private panel or data manifest enters the child environment.

The response has `policy`, `origin`, `receipt_sha256` and `report`. Per-caption
outcomes are `report.feedback[].result` (NOT `.receipt`), with actual rank,
acceptance and novelty. `report.caption_sources` records ACT/THINK origin and
literal text spans. `report.next_stage == "ACT"` requests clarification on the
same opportunity. Updated `activate(socket_path, max_act_attempts=3)` renders
feedback, generates a new ACT, charges incremental tokens and logs an
R223_CAPTION_OPPORTUNITY receipt. Three attempts is a resource allowance, not a
caption count. Exhaustion does not kill the life. Old pinned clients remain wire
compatible but need safe source adoption for this retry wrapper.
`ok:false` for unparsed text is not a fatal transport failure or scored rejection.

Freeform named/numbered scenes, multiple scenes, bare/quoted/labelled captions
and questions work without mandatory fields or a fixed caption count. Optional
Count is advisory only. "captions for Scene1" with two Caption lines and closing
commentary yields exactly two candidates. The old ACT701/765 are NOT resubmitted.
Only the same child's latest committed THINK can supply explicit salvaged
candidates when ACT is unclear; no cross-load/sleep/stage ancestry is accepted.

## State-preserving adoption

No hot-swap or empty novelty restart. The new service persists
`SESSION_STATE.private.json`; a completed snapshot can be supplied with
`--resume-state PATH --resume-state-sha256 SHA` into a NEW output directory with
the same life/game/scene bindings. Pending dispatch is not safe to repeat.
Existing pre-R223 services have only per-attempt BEFORE/AFTER snapshots: adoption
must first export a complete old state plus ALL seen ACT hashes at an owner-chosen
quiescent scorer boundary. A bare AFTER file alone is insufficient replay state.
The child need not be stopped. Main/Turing control the endpoint switch.

## Standalone base on ovx4

Standalone generations are NOT native RESPONSE origins. The receipt-bound adapter
and validator are implemented/tested: see `GENERATION_API.md`. The latest handoff
assigns the standalone service to this worker; Main owns P3 adoption. Do not route
base text through the native endpoint or
claim a frozen C2 proposal backend is a learning life.
Persistent base inference retains history and scoring state, not an optimizer.

## CPU receipt

At 2026-09-18 07:28 UTC: 25 focused tests PASS, 1.57s, using the cached CPU environment:

```sh
UV_CACHE_DIR=/data/home/rohing/.cache/uv uv run --offline --with pytest python -B -m pytest -q tests/test_ny_caption_r223_freeform.py tests/test_ny_caption_life.py tests/test_ny_caption_matched_players.py
```

These are synthetic/source-validation CPU tests, not live scoring or LOADED proof.
No GPU work, historical resubmission, source hot-swap or judge interruption.
