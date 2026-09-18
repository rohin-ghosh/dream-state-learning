# Main's disjoint standalone service interface — R223/R224

Main's 07:36 follow-up reassigns the NEW `gpu/ny_caption_generation_service.py`
to this worker; Main instead owns disjoint `rohin224_caption_adoption` and P3
deployment. The standalone CLI is now implemented here. Callback/validator lives in
`research_loop.workers.rohin221_continuous_caption_20260918/generation_origin.py`.
CPU integration: 29 focused tests PASS at 07:32 UTC; no GPU deployment claimed.

## Minimal service construction

Main loads the existing approved scoring game/private panels once PER CONDITION,
then creates a session. `binding` is the controller's actual `controller.binding`;
`backend` is its actual `backend.state_receipt()` after loading. These are public
metadata, not captions/private panels, and must be operator-pinned, not accepted
from each untrusted request. The controller's private state file has both fields.

```python
from gpu.ny_caption_life_service import LifeSession
from research_loop.workers.rohin221_continuous_caption_20260918.generation_origin import (
    KIND, process_generation,
)

session = LifeSession(game, receipt_root, new_output, scene_descriptors,
    source_mode=KIND, session_binding={"controller": binding, "backend": backend},
    resume_state=complete_matching_snapshot_or_none)

def score(message):
    return process_generation(session, message, receipt_root=receipt_root,
        expected_binding=binding, expected_backend_state=backend)
```

`receipt_root` is exactly this condition's `private/generations` directory.
Use the existing `serve(session, socket_path, seconds)` only with a subclass that
overrides `process` to call `score`; the base `process` deliberately remains
native-journal-only. Alternatively Main can use its own owner-local transport.
No public raw-text endpoint. No native RESPONSE is manufactured. Serialize calls
within each condition; one game/session and output directory per condition.

Implemented CLI: `python -m gpu.ny_caption_generation_service`, with the same
game/data/image/judge/encoder/pixel/relevance/agent-id/output/socket arguments as
the native scorer, but `--receipt-root`, `--binding-config`, and
`--binding-config-sha256` instead of `--life-root`. `--top-k` is50. The controller
writes `BINDING.public.json` after actual base initialization; it contains exactly
`controller` and `backend`. Owner pins that file/hash to the generation service.
The service's LOADED is explicitly a scorer load, NEVER a learner load.

## Wire schema

```text
{
  origin: {
    kind: "STANDALONE_GENERATION",
    request_id: SHA256(canonical controller generation request),
    request_sha256: same request hash,
    response_sha256: SHA256(canonical actual generated response),
    generation: {path: absolute confined receipt file, sha256: actual file SHA},
    think?: {kind, request_id, request_sha256, response_sha256, generation}
  },
  metrics: {THINK: actual tokens charged once, ACT: actual current tokens, LEARN: 0}
}
```

Canonical request/response hashing is `controller.digest`: sorted JSON,
UTF-8, ensure_ascii=False, compact comma/colon separators. The receipt file binds
`request`, `generated`, and `finished_unix`. Request includes exact input messages,
stage, condition, opportunity, attempt, max_new_tokens, controller/parser file
hashes, plan, scene-roster hash and actual backend identity. Generated response
includes exact messages, raw text, token_ids, prompt_tokens, terminal, truncated.
The validator rejects escaping/symlinked paths, files >1MiB, source/model/condition
mismatch, wrong stage/hash/tokens and non-prior/nonmatching-opportunity THINK.

No bearer credentials are invented. Authentication is the OS owner boundary:
private receipt directory + owner-only socket (0600); source/hash validation is
provenance, not proof against a compromised owner. Do not mount scorer private
panels/data into the learner or expose raw scored reference examples.

## Reply and controller

The callback returns the native-style envelope plus `request_id`, `condition`,
`rule_sha256`. `report.feedback[].result` is the per-caption result; `receipt_sha256`
binds the completed private attempt RESULT. Clarifications remain in the same
opportunity. Actual salvaged THINK counts/sources are explicit. No parsed actions
are trusted from the caller; the service re-extracts source text itself.

`adapters.SocketScorer` is the implemented controller bridge. Its binding file is:
`{condition, rule_sha256, top_k:50, reference_count:64, relevance:true, novelty:true}`.
`--scorer-output` optionally permits the trusted OPERATOR to recover a completed
RESULT+AFTER after a lost reply without scoring again; never expose that directory
to child prompts. Without a completed receipt, preserve pending, never redispatch.

`adapters.BaseBackend` reuses ONLY the verified FrozenBase loader/generate methods,
NOT the old fixed-field one-shot opener. It retains a single plain frozen base,
no LoRA/optimizer, plus persistent controller history and independent game state.
It is NOT a learner. `controller.py` now dispatches every source-bound ACT,
including malformed ones, so the service can recover the same generation's THINK.

Native node2GPU6 remains a distinct real learner on the native journal API in
`SERVICE_API.md`; do not substitute frozen C2 inference and relabel it learning.
