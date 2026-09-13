# EDITSTOP — conditional CPU-only endogenous action-relay preparation

Final CPU validation recorded at 2026-09-13T02:54:39Z.

## Scope and non-claims

This is bounded future-path preparation, not a scientific runner, launch
authorization, Q0 result, native-tokenizer proof, or model result. Q0 is still
running according to the supervisor; no Q0 outcome was supplied or inspected.
The admission/compiler does not receive or consult any hidden world
orientation/map. Independent world scoring is deliberately outside this
module and must remain separate.

Only these three files were created/edited:

- `organism_v6/endogenous_action_relay.py`
- `tests/test_endogenous_action_relay.py`
- `/tmp/astra_endogenous_action_relay_handoff_20260913.md`

No Git commands, network calls, GPU work, model calls, fits, experiments,
launches, notebook edits, or changes to another agent's files were performed.
No Q0 live output, helper source, manifest, or evidence was read or edited.
Original Q0 helpers were left untouched; no baseline or after-the-fact Q0 hash
claim is made. Applicable AGENTS.md/CLAUDE.md and the requested design memo
were read. The supervisor's explicit three-file/no-Git/no-notebook scope
controls over broader standing workflow instructions.

## Delivered contract

- Eight ordered key blocks, exactly two committed action/public-outcome pairs
  plus one DREAM receipt per block: 16 action calls and eight record calls.
- Exact byte grammar; no stripping, trailing LF, CRLF, fences, extra text,
  repair, retry, fallback target, or record completion. Identifiers are ASCII
  `[A-Za-z0-9_][A-Za-z0-9_.-]*`. `DREAM: NULL` means NO_ADMISSION.
- Raw receipt SHA-256, external source seal, unique receipt IDs, globally
  ordered event sequences, per-key/mode/object matching, and earlier same-block
  action citations with public outcomes preceding the record.
- `EXECUTED_ACT` is checked against committed raw ACT bytes.
  `SUPPORTED_FUTURE_ACT` is copied from an exact raw-record byte span and
  verified against SUCCESS/FAILURE under the public two-action law. FAILURE
  does not cause the compiler to author the other action; the child must have
  already authored that supported action.
- ALL8/16 or `ENDOGENOUS_FORMATION_SHORTAGE`, with no training rows, schedule,
  control plan, or fits on shortage. Partial admissions are audit diagnostics
  only. Material preflight errors raise ValueError rather than yielding a
  reportable source-formation result; neither path fits anything.
- Complete formation also requires complementary authored modes, four
  authored bindings of each action per mode, and opposite authored bindings
  in each presealed key pair. These checks use public supported child records,
  never hidden orientation. Pairs are rejected, never reselected.
- 128 natural rows: eight views x eight keys x two modes. Quartets are ordered
  by supplied view order, supplied pair order, then mode order with the two
  keys interleaved. Each quartet has two rows of each action. The 32-quartet
  sequence repeats four times: 128 schedule entries, 512 row presentations,
  32 presentations per key/mode relation.
- Training prefixes are presealed bytes ending exactly `ACT: -`. Targets are
  raw child-record suffix slices (`mem2reg` or `gvn`); the shared hyphen is
  already in the input. Full authored action bytes, original receipt, span,
  and cited execution remain attached for auditing.
- E_SWAP uses the complementary presealed mode input while retaining every
  child target byte, source citation, record, and target span. E_AUTH/E_SWAP
  are the two descriptive candidate-producing controls; E_OFF has no
  candidate; E_SHADOW references E_AUTH without another fit or mounting.
  These are plan metadata, not execution or permission.

## Exact outstanding integration interfaces

### 1. Presealed public rendering/material adapter

Supply `Material(root_id, generation_seed, sealed_sequence, keys, modes,
pairs, views, source_objects, surfaces)` and the independently anchored
`expected_material_sha256 = digest(material)` from the pre-child seal.
There are no fresh root, seed, alias, tokenizer, or lexical-view defaults.

- keys: eight distinct byte identifiers; modes: two distinct byte identifiers;
  views: eight predeclared view IDs; pairs: four ordered, disjoint key pairs.
- source_objects: 16 distinct IDs in key-major/mode-major order.
- surfaces: exactly 128 `Surface(key, mode, view, object_id, prefix, key_span,
  mode_span)` cells. Spans are half-open byte offsets. Modes within a
  key/view share the training object and differ only at the registered mode
  slot. Source/training objects must be disjoint. The material must be sealed
  before the first action commitment.
- Prefix bytes must be independently approved, target-free frozen renderings.
  Literal action stems, outcome labels, and DREAM/evidence fields are rejected
  by this module. Lexical rejection does not prove absence of arbitrary coded
  hints; provenance and the full rendering/visibility audit remain upstream.
- Supply only this public projection. Do not pass a full world manifest,
  orientation vector, scores, held answers, Q0 material, raw conversation,
  or audit-only state to the compiler.

### 2. Immutable public capture adapter

Supply eight `Block(key, executions, dream)` values in the material's key
order. Each `Execution(key, mode, object_id, EXECUTED_ACT, commit, outcome)`
uses two immutable `Receipt(receipt_id, sequence, raw, raw_sha256)` values;
the DREAM receipt is the third child turn. Event sequence integers must
order commit0 < outcome0 < commit1 < outcome1 < DREAM and continue strictly
across blocks. Raw action bytes are exactly `ACT: -mem2reg` or `ACT: -gvn`;
public outcome bytes are exactly `SUCCESS` or `FAILURE`.

Pass the independently recorded source seal as `expected_source_sha256`.
Capture must bind raw bytes and metadata at generation/outcome time and
preserve the external anchor. Recomputing an expected seal from modified
inputs is not provenance. These hashes detect disagreement with a trusted
capture; they do not authenticate a model or world by themselves.

Call `build_replay(material, blocks, expected_material_sha256=...,
expected_source_sha256=...)`. The lower-level `admit_block` uses public data
only and rejects with ValueError; `check_formation` aggregates admissions and
NO_ADMISSION reasons. Use the full builder for material validation and the
all-record boundary, not individual successful admissions as a subset corpus.

### 3. Separate, independent world-scoring boundary

The hidden pre-child truth map stays in the world/scoring owner, not Material,
admission, compiler, or training inputs. That owner must independently verify
the balanced XOR world and public outcome generation, retain a private binding
to the public material seal, and eventually score held raw actions against
world truth, not against child records. This component neither implements
nor calls that scorer. A consistently falsified public outcome stream with a
newly falsified trusted capture cannot be detected from public evidence alone.

### 4. Caller-supplied tokenizer/collator shape interface

`check_native_shapes(replay, expected_replay_sha256=..., modes=..., tokenizer_sha256=...,
collation_sha256=..., encode=..., collate=...)` requires every argument;
there is no fallback tokenizer or fabricated proof.

- Immediately after a trusted `build_replay` result constructed from the
  externally anchored material/source seals, compute `digest(trusted_replay)`
  and retain it independently as `expected_replay_sha256`. Pass that retained
  value across any transfer, deserialization, or reconstruction boundary.
  The checker validates its SHA-256 syntax and compares the supplied Replay's
  digest against it before status/shape checks or either callback. Omission
  raises TypeError; malformed or mismatched anchors raise ValueError. There is
  no self-hash default. Do not recompute the expected hash from the replay
  being checked: a newly forged matching anchor would defeat this boundary.
  Downstream consumers must preserve this same trusted replay binding.
- `encode(raw_bytes) -> tuple[int, ...]`: exact caller-controlled tokenization,
  with its special-token policy frozen externally. The checker verifies
  distinct single-token mode aliases, equal prefix lengths, exactly one
  differing registered mode-token identity, stable joint prefix/target
  boundaries, and identical target token order in corresponding rows.
- `collate(tuple[NativeRow, ...]) -> BatchShape(attention_mask, position_ids,
  target_positions)`: actual caller collator outputs for four rows, represented
  as tuples of tuples of nonnegative integers. Corresponding AUTH/SWAP
  attention/position/target-position structures must match exactly.
- The returned check binds supplied implementation hashes, the replay, token
  evidence, and quartet shapes. It only checks supplied values, not the
  authenticity of implementations or runtime tensors. All tests here use
  explicitly synthetic encoders/collators; none is native or model evidence.
- Actual tokenizer/model identity, tensor authenticity, dropout RNG equality,
  initialization, optimizer state, recipe/work identity, and native branch
  behavior still require independent integration evidence. No such evidence
  was produced here.

### Narrow F1 repair disposition

The independent review at
`/tmp/astra_endogenous_action_relay_review_20260913.md` reported that equal
supplied shapes alone admitted symmetric wrong-mode target substitution and
32 repetitions of the first quartet in both arms. Neither mutation comes
from the builder. The required independently retained replay digest now rejects
both before any encoder/collator callback. The returned replay hash is the
same digest that passed the anchor comparison, not a new unverified self-hash.

This is a non-material repair of that supplied-replay validation boundary.
Formation, byte admission, compiler ordering, controls, scientific claims,
and hidden-map separation are unchanged. It adds no formal C11 machinery or
new science, and does not establish runtime/native authenticity. The review
artifact was read but not edited. No independent post-repair approval is
claimed; the new regressions are author-side synthetic CPU evidence only.

### 5. Future writer/reset/readout interfaces — not implemented

Any future authorized integration must use only `TrainingRow.prefix` as
model-visible input and the copied `target` as the supervised completion.
Never stringify or expose the whole TrainingRow: `.record`, `.execution`,
and the surrounding Replay are audit data, not model input. Consume the
registered quartet order without shuffling, selecting, padding target text,
or resampling a shortage.

Actual writer selection after any externally established Q0 condition,
frozen model/LoRA recipe binding, canaries, fits, finite-loss and work checks,
fresh-process reset, sterile visibility, all evaluation panels, native copy,
OFF/SHADOW model-visible projection and raw-output equality, independent
scoring, scientific gates, and any launch authority are outstanding. Nothing
in `CONDITIONAL_REPLAY_PREPARED` grants those permissions or establishes a pass.

## CPU test evidence

Command:

```text
python3 -B -m unittest discover -s tests -p test_endogenous_action_relay.py -v
```

Final result after F1 repair: `Ran 25 tests in 0.707s` / `OK`.
Main reported reproducing the prior 22-test version as PASS in 0.350s.
`-B` avoids creating bytecode artifacts outside the three-file scope.
Coverage includes exact 8/16/24 counts; SUCCESS and FAILURE provenance;
unchanged raw record slices; deterministic 32x4 balanced replay; exact arms
and E_SWAP bytes; NULL/no-subset policy; corrupt and cross-block citations;
invalid ACT/DREAM/outcome grammars; missing/extra calls; sequence and seal
violations; wrong key/mode/object; duplicate IDs; tampered raw bytes and
source seals; bad material/pair balance; literal target leaks in both mode
inputs; explicit synthetic shape interfaces; corrupted token boundaries,
collation shapes, replay schedules, targets, and control provenance. New F1
regressions cover symmetric wrong-mode target substitution, symmetric first-
quartet repetition, omitted expected replay hash, malformed expected hashes,
and a well-formed mismatched hash. Mock callbacks verify anchor failures stop
before encoding/collation; the trusted baseline still passes synthetic checks.

An initial test-harness assertion compared two dict_values views directly;
that redundant assertion was removed, retaining the real [2,2] key-count
assertion. Subsequent runs passed (21 tests, then the prior 22 tests), followed
by the final 25-test F1 regression run above.

## SHA-256 of final code and tests

```text
b7e489143841a83a58b46a8897108b885ea4e6f8caf062a10c25d2eeeceafe53  organism_v6/endogenous_action_relay.py
1a728166c9a48c328901a2d591ed13eac1408fc6e1567019c30e2e7ebc5607a8  tests/test_endogenous_action_relay.py
```

The handoff's own SHA-256 is reported separately after writing this file to
avoid a self-referential digest. EDITSTOP: no additional integration, files,
model/native claims, or launches are undertaken by this bounded task.
