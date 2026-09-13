# Post-memory fresh formation CPU core — EDITSTOP

September13,2026. Implementation and scripted CPU replay only. No native/model/
GPU/remote queries, launches, source-result inspection, fits, repository/Git
edits or old-source changes. Main/another worker owns the separate native runner.

## Stable API, schema and pins

- `/tmp/astra_post_memory_formation_core_20260913.py`:
  `030c97c57a962a74a5b97bd66550096dedc2bab288d690b2c89808d2ec84474b`.
- `/tmp/test_astra_post_memory_formation_core_20260913.py`:
  `647b07947604b395687aedb4537f1ccc8fe3fde4c6d26f38c126c3670d840e28`.
- `/tmp/astra_post_memory_formation_core_20260913_handoff.md`: hash supplied separately.
- Schema `astra_post_memory_formation_20260913_v1`.
- Contract digest, using core.digest (compact sorted JSON, UTF-8, no newline):
  `52be1db897cb07739b28fddab4112e8f32209ff878a1b836a9351e611cc4c8d7`.

```python
dependencies = core.load_dependencies(source_root=PINNED_SOURCE_ROOT)
policy = core.contract(dependencies)
ids = core.episode_ids()
cases = core.schedule()
core.check_disjointness(prior_episode_ids=original_training_task_ids)
capture = core.run_state(state, backend, dependencies=dependencies, binding=declared_binding)
audit = core.audit_capture(capture, dependencies=dependencies)
comparison = core.compare_states(captures, dependencies=dependencies)
```

`canonical`, `sha_text`, `digest`, `earlier_transcript`, `score_record`, `PINS`,
`PROTOCOL`, `FIELDS`, `MAX_OUTPUT_TOKENS`, `WAKE_TEMPLATES` are also exposed.
The module requires the exact frozen v2 core at its default `/tmp` path at
import. `load_dependencies(..., core_path=...)` also supports an explicit
byte-identical dependency copy; it does not change IDs/state globals.

States in fixed order:

```text
perception_seed0_WRITE
perception_seed0_LR0
perception_seed1_WRITE
perception_seed1_LR0
perception_seed2_WRITE
perception_seed2_LR0
```

## Main's adopted scope — no outcome gate

Read `/tmp/astra_next_l2_decision_20260913.md`, SHA256
`fd81b33e648d5751cb7ecaa98c5ef45fb04d011c9381cc9d677ce081f0f304f4`.
Its schedule, endpoints and cue strata are implemented; Main's subsequent
instruction overrides its proposed favorable-recall/no-canary-harm readiness
rule. **No positive-seed, gain, summed-win or absence-of-harm gate exists here.**

All three engineering-valid completed memory pairs are a native-runner
prerequisite. This core cannot authenticate checkpoints/collections and does
not pretend to enforce that prerequisite from a caller's assertion. Contract
explicitly says Main must check all three; comparison returns
`engineering_prerequisite_verified=False`, `native_identity_verified=False`,
`outcome_gate=None`, `automatic_pass=False`. A negative gain or reported harm
does not prevent capture or comparison. Missing states remain missing, not
substituted with favorable states or silently treated as complete.

## Exact fresh schedule and disjointness

`next-record-dev-` + first20hex of SHA256 over UTF-8 compact JSON
`["astra-next-l2-20260913", index]`, index0..7. No trailing newline, rule search,
balancing, forced `ruleN/` prefixes or outcome-based replacement.

```text
0 next-record-dev-627e2b39856014cb44d1  example_present
1 next-record-dev-d055881cde5825a1a9e1  example_absent
2 next-record-dev-427e7a31a18b9c3c101a  example_present
3 next-record-dev-dc8b25747ee2391b1b50  example_absent
4 next-record-dev-108d90929358b84c6264  example_present
5 next-record-dev-1741425738c394a89a34  example_absent
6 next-record-dev-6cf84cecdaa9fe5f7e2d  example_present
7 next-record-dev-b6766a9df5e9088443a9  example_absent
```

Ordered ID list compact-JSON digest:
`c45edf52b71d84e547264251abcb34305199f30e8dd3af1e41caa7346c4dca6e`.
Every schedule/contract checks uniqueness and disjointness from all eight
frozen original v2 formation IDs; original memory-training task IDs are a
subset of those. `check_disjointness` accepts additional explicit prior task
IDs for native checks, allows repeated prior IDs and rejects any overlap.
Additional prior-ID checks return a separate receipt; the fixed contract does
not silently absorb caller-dependent history. This is not universal unseen-
exposure certification. Fresh IDs do not imply novel triples or raw targets.

## Frozen literal cue templates

Even episodes use the exact unchanged v2 WAKE_TEMPLATE. Its SHA256:
`090f99d55be7c96affbf73804f39a0a457936d1546c71bae95d4185684013ebd`.
Odd episodes delete exactly this one complete block, including its final newline:

```text
Syntax example only (these numbers and this prediction are arbitrary, not a known answer):
PREDICT: T
ACT: TRY 2,5,9
```

No-example template SHA256:
`a7458bef4b2572bd6dafac42e724b0a2f122c3568937fa9a1e7a64cb88920cfa`.
Everything else is byte-identical: public task/attempt, verbal three-integer
and two-line instructions, mandatory ACT prefix wording, history position and
final stop instruction. A child's own earlier output can still contain2,5,9;
only the instruction example block is removed, not actual historical bytes.
Both templates are exposed literally in core.contract, fixed before outputs.

Record instruction/prompt is unchanged. On turn2, both wake and record include
only that state's earlier actual transcript, through unchanged v2 history
rendering. Earlier malformed/fenced/wrong record text is retained, not fixed.
No original memory-corpus records/IDs, lesson, teacher, parent, hidden rule,
reward or quiz content is inserted. Stratum/state/proof metadata stays outside
`input_messages`; native code must render only those messages.

## Semantic reuse and callback contract

Frozen v2 core SHA256:
`b023a4321d0a20e465c96914316a730fbb2dd897c11369a9eb62d2d8f1248ef5`.
Its source-pinned RuleGame and AST-selected public parser/judge/prompt helpers
are loaded unchanged:

- `organism_v6/rulegame.py`:
  `88304996b00837ad1855e8a6661aad39e64f3beb0c0ab4491b63119e797226f3`.
- `organism_v6/rulegame_parenting_diagnostic.py`:
  `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`.

Directly reused: canonical/hash functions, earlier_transcript, score_record,
raw `_call` error preservation, `_execute` public TRY execution/event/source
joins, and original full16turn summary. Only new fixed orchestration/request
namespace and descriptive strata/comparison are implemented. The loaded v2
module's STATES, IDs, SCHEMA and WAKE_TEMPLATE are never assigned or patched.
New module globals are separate copies where relevant.

Backend receives:

```text
{request_id, state, episode_id, episode_index, cue_stratum, tick, kind,
 input_messages, max_output_tokens, source_execution_sha256}
```

Return `{request_id, state, raw, finish_reason}`; additional native metadata
is retained. Only stop-completed, source-joined valid TRY calls execute the
actual pinned world. Invalid/unfinished wakes produce no execution or record
call; their slots remain in the denominator. Backend ordinary exceptions are
recorded exactly as v2 backend-error evidence; infrastructure BaseException
may abort in a native wrapper as before. No retries, action salvage, repaired
JSON/fences, host-authored record targets or reward/quiz calls.

Capture retains `{schema,state,binding,contract,episodes,events,summary,
native_identity_verified,qualification,capture_sha256}`. Episodes add fixed
`index`/`cue_stratum` metadata beside `episode_id` and original two turns.
Original response objects, failure envelopes, raw text, finish reasons,
execution fields/outcome bytes and source hashes are preserved. New request
IDs bind the new schema plus exact request, including stratum and source join.
Native token/time evidence can be included by the backend, but is not
authenticated or bounded by this CPU core. All native identity flags stay false.

## Endpoints, replay and native integration

Primary count is source-faithful production records/16scheduled turns per
state, WRITE−LR0 per seed. Also expose actual-execution and actual-record-call
denominators, invalid/unfinished wakes, missing/unfinished records, content,
canonical format, all four fields, format categories and original nested
refusals. Strata partition by cue, tick, prior availability/ambiguity, expected
relation and actual observed value. No-execution slots stay explicit. Empty
strata have `coverage="untested"` and null rates, never a pass.

Replay regenerates the exact new requests and public world outcomes from
captured responses, checking the complete event chain, chronology, source
joins, raw errors, cue schedule, summaries and digest. Rehashed outcome/source/
stratum/order tampering is rejected. It does not prove a model generated the
responses. `compare_states` audits supplied captures and reports partial
coverage honestly, without enforcing any outcome gate.

Per-state maximum32calls (16wake96 +16record192), six-state maximum192calls and
27,648generated tokens; zero fits/updates/parent calls. Native runner must enforce
actual tokens, all-three-pair engineering custody, six cold checkpoint routes,
all-process/lease checks, per-cell900s and per-pair1800s/collection180s envelopes.
The old four-state native runner will correctly reject this schema/states;
do not monkeypatch it. This core contains no native controller or collector.

Training-target/triple overlap, copying2,5,9, novel-triple fidelity, differing
earlier/final outcomes, prediction accuracy and changed/repeated actions are
analyzer work. Their source evidence is retained but no training corpus or
outcome-selected subgroup/gate is added to this core. Source-present field
copying is not reasoning correctness; a new-ID record gain alone is not
internalization, repeated learning, a closed-loop or H1/H2 result.

## CPU checks

12tests PASS on the first run in0.270seconds. Tests cover independent exact
ID derivation, overlap rejection, literal template hashes/strata, untouched
old globals, actual RuleGame calls without quiz, unchanged record prompts,
source/event joins, raw fence/history preservation, invalid/unfinished/wrong-
join wakes, replayed exceptions, wrong outcome/ambiguous prior, six cells/caps/
differing actions, explicit no outcome gate, missing states, empty strata and
rehashed tampering. Scripts are fixtures, not actual child/model results.
AST/whitespace checks pass. Frozen v2 source rehashed unchanged after testing.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s /tmp \
  -p test_astra_post_memory_formation_core_20260913.py -v
```

EDITSTOP. API, ID/template/contract/source hashes above are final for Main's
separately versioned native integration. No favorable-outcome gate was adopted.
