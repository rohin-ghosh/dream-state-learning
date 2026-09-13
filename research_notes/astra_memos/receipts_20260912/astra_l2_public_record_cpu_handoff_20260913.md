# L2 public-record DEV: CPU core / native-wrapper handoff

2026-09-13, verified at 05:20:56 UTC. Scope is the latest accepted **base-start,
PROMOTE/SHADOW-only two-SLEEP exploratory slice**, not the proposed five-fit
comparison. Main owns the native wrapper, launch and final recipe. No live Q0,
final-C11 guard, old relay/compiler/runtime or manuscript changes.

## Fixed scope before native data

- Sixteen independent opaque keys, slots 0–7 then 8–15, one action/feedback/record
  episode per slot. This is deliberately **not** eight keys × two modes and makes
  no equivalence claim. Two global opaque action names; private truth is balanced
  four/four per block. Vocabulary and truth seeds are separate; public prompts
  are invariant to truth seed. Pin the private world separately: a public root
  intentionally identifies vocabulary, not hidden truth.
- Three intended actual fits: one shared SLEEP1 candidate, then separate
  cumulative SLEEP2 candidates from each branch's own authentic old+new records.
  Every fit initializes from the same frozen base with fresh optimizer. PROMOTE
  publishes its candidate; SHADOW computes but never publishes, remaining base.
  Reuse the actual shared first candidate SHA in both states; do not fit twice.
- MISBOUND is a marked, deterministic corpus-only permutation helper for a
  separately logged follow-up. No third live arm or hidden state mutation.
  Empty formation stops as `FORMATION_SHORTAGE`, not a fabricated fit or success.

## Stable public API

Module: `organism_v6.l2_public_record_dev`; schema `l2_public_record_dev_v0`.
All functions are pure stdlib operations. Exact callable signatures:

```python
build_world(vocab_seed: int, truth_seed: int) -> World
public_view(world: World) -> PublicWorld
action_prompt(public: PublicWorld, slot_id: str, *, view="wake") -> str
make_receipt(public: PublicWorld, slot_id: str, kind: str, raw: bytes, *,
             sequence: int, lineage: str, previous=None) -> Receipt
feedback(world: World, action: Receipt, *, sequence: int) -> Receipt
process_prompt(public: PublicWorld, action: Receipt, outcome: Receipt) -> str
capture_block(public: PublicWorld, block: int, lineage: str,
              episodes: tuple[Episode, ...]) -> CapturedBlock
compile_corpus(public: PublicWorld, captures: tuple[CapturedBlock, ...], *,
               expected_hashes: tuple[str, ...]) -> Corpus
misbind_corpus(public: PublicWorld, corpus: Corpus, *, expected_sha256: str) -> Corpus
training_items(public: PublicWorld, corpus: Corpus, *, expected_sha256: str) -> list[dict]
start_pair(public: PublicWorld, base_sha256: str) -> dict[str, LoopState]
close_block(public: PublicWorld, state: LoopState, capture: CapturedBlock, *,
            expected_sha256: str) -> LoopState
complete_sleep(public: PublicWorld, state: LoopState, *, corpus_sha256: str,
               candidate_sha256: str | None, initialized_from_sha256: str) -> LoopState
routing(state: LoopState) -> dict
check_pair(public: PublicWorld, states: dict[str, LoopState]) -> None
reduce_pair(world: World, states: dict[str, LoopState],
            readouts: dict[str, tuple[Receipt | None, ...]]) -> dict
canonical(value)  # canonical ASCII JSON bytes, for hashing; NOT the wire codec
digest(value)     # SHA256 hex of canonical(value)
to_data(value) -> dict
from_data(payload: dict, *, expected_type: type | None = None)
```

`view` accepts `wake`, `train`, `readout`. Wake/train share the natural bare-action
grammar; readout rephrases the question, not the answer format. Native child
outputs must be retained whole: exactly one listed action, optionally one LF.
No trimming, prose extraction, JSON record or compiler-generated replacement.

Frozen schemas: `PublicWorld(root_id, actions, slots, law)`;
`Slot(slot_id, key, block, index)`; private `World(public, success_actions)`;
`Receipt(root_id, slot_id, lineage, kind, sequence, raw, previous_sha256, sha256)`;
`Episode(action, outcome=None, record=None)`;
`CapturedBlock(root_id, block, lineage, episodes)`.
`Corpus` retains captures/pins, accepted rows, rejection reasons, kind, permutation,
changed-target count and no-op flag. `LoopState` retains public hash, policy,
base/mounted hashes, phase, cumulative corpus and immutable SLEEP history.
Use named fields, rather than constructing state or corpus objects manually.

JSON persistence: `json.dumps(to_data(value))`; recover with
`from_data(json.loads(text), expected_type=CapturedBlock)` (or `dict` for the
pair). Wire version 1 preserves dataclasses, tuples and exact bytes via tagged
data; only allowlisted classes decode. Verify retained hashes and `check_pair`
after decoding: decoding alone does not validate scientific/state invariants.

## Wrapper lifecycle / evidence boundary

1. Environment privately builds and pins `World`; child and compiler receive
   **only** `PublicWorld`. Pin seeds/protocol/source before collection. Never pass
   private truth or fixture target-selection code to the child.
2. Start pair; collect block1 once with lineage `SHARED`. For each scheduled slot,
   capture fresh child action bytes using `make_receipt(..., "action", ...)`.
   Environment calls `feedback`; capture a fresh child response to
   `process_prompt(public, action, outcome)` as kind `record`, `previous=outcome`.
   This fixed process tape is never fitted. Use `Episode(action, outcome, record)`.
   An invalid action has no binary outcome: retain `Episode(action)`. Missing or
   unsupported child records remain explicit rejections; never synthesize them.
3. Assemble eight episodes in slot order with `capture_block`; independently
   retain `digest(capture)`. Sequence integers strictly increase action → outcome
   → record → next action, and continue across blocks within each branch.
   `Receipt.sha256` binds the framed receipt with its hash field blank, **not**
   merely the raw output bytes; predecessor hashes enforce event order.
4. `close_block` each initial state against the same capture/pin. Export
   `training_items(public, state.corpus, expected_sha256=digest(state.corpus))`.
   Fit once. `complete_sleep` both states with the same actual candidate SHA,
   their corpus SHA and the frozen base SHA; `check_pair`; honor `routing`.
5. Independently collect block2, lineage matching `PROMOTE` or `SHADOW`, from
   its requested mounted artifact. `close_block` reconstructs that branch's
   authentic old+new union. Export/fit each union separately from frozen base;
   complete each SLEEP2. Do not append PROMOTE material to SHADOW or vice versa.
6. Fresh source-withdrawn final readouts: 16 ordered receipt-or-None entries per
   policy, kind `readout`, matching lineage, sequence after the last capture.
   Call `reduce_pair` in the private scoring environment. Report fixed-denominator
   legal/correct/missing counts, old/new counts and paired flips. Missing entries
   contribute false to descriptive counts but invalidate endpoint accuracy.

Compiler admission consults only binary public feedback and the explicit
deterministic two-action law. After FAILURE, it verifies the **child-authored**
other action; it never emits that action on the child's behalf. Targets preserve
the entire raw record span `[0, len(raw)]`, with receipt/episode/raw-target hashes.
Export consists of `spans=[[prompt, False, "context"],
[target, True, "child_action"]]` plus provenance metadata. Neither parent/process
tape nor the event's observed outcome is fitted; the common public law remains
in masked prompts. MISBOUND rotates admitted targets by one position, preserves
their multiset and donor provenance, and marks semantic changed-target count and
`no_op` (including identical actions with different optional LF bytes).

## Validation, runtime duties and limits

`python3 -B -m unittest tests.test_l2_public_record_dev -q`: **28 passed**, 0.838s.
Source-only fixtures cover visibility/truth independence, balance, exact LF bytes,
unsupported/missing records, cross-root/slot/lineage support, chronology, external
pins, forged rows, no fitted parent tape, authentic cumulative branch state,
shared first candidate, SHADOW routing, frozen-base initialization, shortage,
MISBOUND/no-op, descriptive readouts and strict JSON round trips. Scripted fixture
behavior is not evidence of learning, native process freshness or successful loads.

The unchanged trainer's `organism_v6/train_adapter_v3.py:152` and `:215` accept
these spans and can chat-template the leading masked context. Runtime must verify
matching inference rendering, actual response-only token masks/EOS, no packing,
no truncation/splitting, fresh optimizer/process captures, frozen-base starts and
actual adapter routing. Native stop/finish reasons, capture process IDs and artifact
manifests belong in the wrapper's linked evidence, not fabricated CPU attestations.
Hashes detect changes against independently retained pins, not a malicious or
misconfigured environment that invents and rehashes feedback. Keep private world
and receipt custody bound in the runtime; never expose truth to the writer.

Abort the affected diagnostic on contradictory source pins, wrong-world feedback,
cross-branch capture, phase/chronology/routing mismatch or failed native masking;
retain evidence. Reject individual invalid actions/records without repairing them.
Small balanced binary DEV task, optional LF tolerance and paraphrased readout limit
identification: this tests partial closed-loop publication, not general semantic
internalization. No operational pass, birth promotion, parent promotion or H1/H2
claim; reducer deliberately returns `scientific_pass=None`, `native_verified=False`.
No new release gate is imposed on unrelated ongoing work.

SHA256 (implementation/test bytes verified above):

- `organism_v6/l2_public_record_dev.py`:
  `0bb33988f003a0111e14cdfb53b3dc86a695e8e20656c90e71cfadb5ad28d352`
- `tests/test_l2_public_record_dev.py`:
  `9691e1c2b97d25a8a5bc0747bb5937ecd9281b0c52a041efbdfc9cc63499a4aa`

Only these two new files and this handoff are owned. No old source, Git, network,
native/model/GPU operation, launch or kill was used for this implementation.

## Carver handoff / EDITSTOP — 2026-09-13 05:26 UTC

For Carver `01a0986e-79f4-7780-b165-61ad39766413`: no direct agent-message tool
is exposed in this session; these instructions are ready for Main to relay.
Serialize using the wire codec, not `canonical` or `dataclasses.asdict`:

```python
import json
from organism_v6 import l2_public_record_dev as core

capture_pin = core.digest(capture)
capture_json = json.dumps(core.to_data(capture))
restored_capture = core.from_data(json.loads(capture_json), expected_type=core.CapturedBlock)
assert core.digest(restored_capture) == capture_pin

states_pin = core.digest(states)
states_json = json.dumps(core.to_data(states))
restored_states = core.from_data(json.loads(states_json), expected_type=dict)
assert core.digest(restored_states) == states_pin
core.check_pair(public, restored_states)
```

Persist the JSON and independently retained expected pins in the runtime's own
artifacts. In production replace illustrative assertions with explicit errors.
Before collection-close, supply the retained capture pin to
`close_block(public, restored_states[policy], restored_capture,
expected_sha256=capture_pin)`; replace that policy's state with its returned value.
For direct compiler use, restore captures and call
`compile_corpus(public, captures_tuple, expected_hashes=retained_pins_tuple)`.
Corpus restoration uses `expected_type=core.Corpus`; export with
`training_items(public, restored_corpus, expected_sha256=retained_corpus_pin)`.
Public-view restoration uses `expected_type=core.PublicWorld`; bind its retained
digest before use. Never send serialized private `World` to child/compiler.
Byte arrays and tuple types are restored by the codec; do not manually decode,
trim or normalize targets. Routing is still intent, not proof of native loading.

Final focused rerun: **28 tests passed, 0.902s**, started 05:26:47 UTC. Source/test
hashes above remain unchanged. CPU implementation/test work remaining: **none**.
Native timing is not estimated here. Main's stated protocol `ae304738` owns the
128 calls / 3 fits / 100 updates and its specified seeds; this core does not choose
or override them. Fixed pair only, no additional guards or optional live arms.
**EDITSTOP:** these owned implementation/test files are complete; this append is
the final handoff update. Main/Carver own subsequent integration and runtime work.
