# Real-record formation core — declared contract before new results

2026-09-13. Only this handoff, matching `/tmp` core and tests are owned here.
No repository/native/GPU/network/Git operations; Main owns runtime and launch.

## Source dependencies and reuse

Use `organism_v6/rulegame.py` RuleGame.evaluate verbatim, full-file SHA256
`88304996b00837ad1855e8a6661aad39e64f3beb0c0ab4491b63119e797226f3`.
Use public definitions from `organism_v6/rulegame_parenting_diagnostic.py`
verbatim, full-file SHA256
`e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`:
`parse_action`, `judge_record`, `record_prompt`, `record_instruction`,
`decode`, `unique_object`, `require`, and their public protocol constants.
Select these definitions through AST as the existing birth_skill_corpus does;
do not import the native runner or silently reproduce its parser.
Pin files before execution; a changed dependency is an error, not an upgrade.

## Exact episode, prompt and budget declaration

Eight NEW DEV episode IDs are generated once by the core schema/domain string
`astra_level1_real_record_20260913_v1`, literal `fresh-dev`, and indices 0–7,
SHA256 compact sorted JSON, taking the first 20 hexadecimal digits, prefixed
`real-record-dev-`. No `ruleN/` prefix, quiz instance, score or private rule name
is disclosed. No rule inspection, outcome balancing, result-based seed search,
or retries. Existing RuleGame chooses its rule deterministically from the eid.
All four declared states share these exact IDs: OFF, perception_seed0,
perception_seed1, perception_seed2. State labels are routes, not proof of a
native model or adapter load.

Exactly TWO scheduled wake calls per episode, in order, regardless of invalid
first output. One record call after each valid stop-completed TRY; otherwise
no execution and no record call for that turn. Thus at most 2 wake + 2 record
calls/episode, 16 wake and at most 16 record calls/state. The denominator is
always SIXTEEN possible records/state. Wake output budget96 and record
output budget192 tokens are fixed request parameters; Main's runtime must
enforce those native token caps. No quiz, DONE execution, parent, fit or write.

Controlled wake prompt, exact literal text (IDs/turn/transcript substituted):

```
Fresh DEV mystery-box observation exercise. Choose your own three integers.
Emit one ACT: TRY a,b,c line. You may put one PREDICT: T or PREDICT: F line before it, or omit a prediction.
Do not emit an outcome, QUIZ, DONE, a record, or a hidden-rule claim. You have two scheduled attempts; no retries.
Task: {eid}
Attempt: {tick}/2
{earlier_transcript}
```

For the first attempt `{earlier_transcript}` is exactly
`No earlier attempt in this episode.` For the second, it is a JSON rendering
under `Earlier actual transcript (context only; not the selected execution):`
of first-turn raw wake, actual outcome (null if no execution), raw record
(null if not returned), and completion/status data. Raw embedded strings are
preserved, not corrected; the null is an absence marker, not invented feedback.
No previous episode or other state's transcript is provided.

Record request: exact pinned `record_prompt(execution, raw_wake,
"interaction_v3")`. On attempt TWO ONLY, prepend that same earlier actual
transcript plus a newline. This makes the earlier actual execution a distractor
while keeping the selected current execution, actual world outcome and public
record instruction explicit. The public observed fields are facts supplied by
the existing prompt, not an assistant target. The CHILD must emit its own raw
`try/observed/predicted/relation` JSON. No host record target is generated.

## Declared acceptance and comparison

Call the pinned parser on the untouched wake. Existing interaction_v3 aliases
remain existing parser behavior, not a new rewrite. Only parsed kind=try and
finish_reason=stop, with a valid response/request source join, reaches
RuleGame.evaluate. Ambiguous prior prediction does not invalidate a parsed
TRY: execute it, request a record, then reject it under the unchanged pinned
judge_record ambiguity rule. Preserve its evidence; do not repair the prior.

All outcomes come from actual RuleGame.evaluate calls; rewards are discarded,
quizzes never executed, and output triples must match the parsed child triple.
No host-selected triple, no teacher target, no forcing correct records.

Report field/content correctness separately from UNCHANGED production record
grammar. Production eligibility uses judge_record(raw, execution) directly;
JSON whitespace/key order are already permitted, Markdown fences are not.
A separate diagnostic content view may parse one enclosing plain/json fence;
it never rewrites stored raw or production admission. Both views require stop
completion, valid source joins, and unambiguous source evidence. Add canonical
format classification without calling it learning or grammar admission.

Compare rates over16possible records for every state; also report actual
execution/record-call counts, missing and unfinished records, per-field scores
and all refusals. Same IDs/budgets but differing child actions and transcripts
means INTERACTIVE RECORD FORMATION, not identical-experience contrast.

## Scope and authenticity boundary

This is raw36 formation only. No successful write, improved learning,
closed-loop result, H1/P1 qualification, or two-action L2 admission claim.
Backend-injected tests simulate child responses and cannot count as native
child evidence. Hash/replay checks bind source joins and consistency, not
external identity; Main must bind actual route/adapter and retain native raw
requests, token IDs and finish reasons. No C11 guard or runtime pause is added.

## Implemented API and Main runtime integration

Standalone CPU module (stdlib only). It reads only the two explicitly pinned
source dependencies; it does not import any native/model/runner dependency.
Main may supply a fresh source snapshot root containing those same bytes to
`load_dependencies(source_root=...)`. Do not update a pin silently.

Public entry points:

- `load_dependencies(source_root=DEFAULT_SOURCE_ROOT)`: actual pinned RuleGame
  and AST-selected public parser/record functions, plus full-source and
  selected-definition hashes. Pass this trusted return value as `dependencies`.
- `episode_ids()`: exact same eight IDs for every state.
- `contract(dependencies)`: complete prompts, policy, IDs, budgets and source
  manifest, independent of new child results.
- `run_state(state, backend, *, dependencies=None, binding=None)`: fixed
  two-turn schedules, actual game execution, raw record capture and scores.
- `score_record(raw, finish_reason, execution, dependencies, source_errors=())`:
  production/content/field diagnostics; no target construction.
- `audit_capture(capture, *, dependencies=None)`: CPU deterministic replay of
  recorded calls and game outcomes, rebuilding the whole capture and joins.
- `compare_states(captures, *, dependencies=None)`: validates same contracts,
  audits captures, reports per-state denominators and leaves absent states
  explicitly absent. Does not run missing states or invent their results.

Backend signature: `backend(request) -> response`. Request fields are
`request_id`, `state`, `episode_id`, `tick`, `kind` (wake/record),
`input_messages`, `max_output_tokens`, and `source_execution_sha256` (record
only; null for wake). Responses MUST echo `request_id` and `state` and provide
the untouched string `raw` and native `finish_reason`. Extra JSON-safe native
token/route/timing metadata can be returned and is preserved. The backend must
feed ONLY `input_messages` to the child, not route metadata or the core/world
objects; select the runtime route using the state and binding separately.

Example integration shape (not executed here):

```python
import astra_level1_real_record_core_20260913 as core
deps = core.load_dependencies(source_root=main_source_snapshot)
capture = core.run_state("perception_seed0", main_native_backend,
                         dependencies=deps, binding=main_adapter_binding)
audit = core.audit_capture(capture, dependencies=deps)
```

Main owns native route proof, enforcing96/192token caps, model scheduling,
process cleanup and writing returned capture artifacts. `binding` is preserved
provenance, not a verified adapter load. `native_identity_verified` deliberately
remains false everywhere. Source-hash checks/replay do not authenticate a
model-origin claim; even a host-authored fake backend can be internally
consistent. CPU test captures must never be submitted as native evidence.

## Raw capture, admission and replay details

Every backend call and actual world execution is an event with sequence,
previous-event hash and event hash. An execution records the original wake,
finish, parsed action/values/prior/ambiguity, actual outcome bytes and digest,
eid/tick, source call ID and source call hash. A record request binds its
source execution hash; request IDs bind state, prompt, turn and that source.
Responses with wrong request/state joins cannot be used even if text is right.

Each turn retains wake, optional execution, optional record, score, status and
errors. First-turn actual raw/outcome/record strings are preserved in the
second-turn distractor, including a wrong prior record. Actual outcome strings
come solely from RuleGame.evaluate; no reward, hidden rule, quiz or evaluation
score is sent to the child. No writes, record corpus, training targets,
replacement labels or host-created assistant responses are exported.

Pinned parser behavior is unchanged, including its existing interaction_v3
action aliases and ambiguity detection. The core does not strip or repair wake
fences; whatever syntax the pinned parser actually accepts remains its grammar.
Only parsed TRY proceeds; even valid QUIZ/DONE syntax cannot execute. Backend
errors, nontext, wrong joins and unfinished wakes cannot execute. The second
scheduled wake still happens: it is a planned turn, not a retry of the first.

Summary fields include possible_records=16, actual wake/record calls,
world_executions, missing_records, unfinished_records, production_eligible,
content_correct, strict_canonical, each numerator/rate_over16, per-field
correct counts over16, and refusals. Missing records includes a skipped record
call or a record response lacking raw text; a returned length-terminated record
is unfinished, not silently removed from the denominator.

`production_eligible` calls the pinned judge on ORIGINAL raw bytes and requires
valid joins/stop. `content_correct` is a separately labeled permissive view:
one whole plain/json fence can be parsed for diagnosis, but NEVER replaces the
raw or production result. `strict_canonical` additionally requires exact
compact sorted JSON bytes. `format` is exact/json_noncanonical/fenced/
unparseable. No key/value/type repair occurs. Fields are try, observed,
predicted, relation; `parsed_field_correct` is descriptive, while
`field_correct` also requires completion/source integrity. Ambiguous source
priors never qualify for whole-record admission even if the child writes null.

Replay regenerates actual public outcomes from each recorded legal child TRY,
rebuilds exact prompts (including previous-turn distractors), request hashes,
execution/record joins, event chain, scores and summary, and requires exact
capture equality. This is CPU replay, not additional child attempts. Rehashing
a corrupted outcome/source join alone cannot make it pass reconstruction.
No model is called by replay or comparison.

## Fixed episode and contract pins

Generation follows the declaration above without consulting outcomes. IDs:

1. `real-record-dev-fc4788038f8df29edf0a`
2. `real-record-dev-7dcb40debdad64acee07`
3. `real-record-dev-8e0fbeb3e7a5012ad7e8`
4. `real-record-dev-68d54fa047a1f2262a6a`
5. `real-record-dev-00af88051b5c8530d45f`
6. `real-record-dev-9e711dc90f1ac92f90df`
7. `real-record-dev-d4a7ddd8a896bed75c29`
8. `real-record-dev-189289eeb97434095252`

`digest(contract(load_dependencies()))`:
`15a84ecaf729a53d99a779e062ea8a51529f4321cd1f6b53ada394ecfea269e3`.
These are new namespaced DEV instances, not a claim of unseen rule families
or a repository-wide statistical independence audit.

## Test receipt and EDITSTOP hashes

Single suite invocation from `/tmp`:

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_astra_level1_real_record_core_20260913`

**9 tests passed, 0.175 seconds** on the final96/192budget revision. Tests exercise actual pinned RuleGame
execution with scripted child callbacks; exact prompt and source links;
wrong observed outcomes; copying earlier record as distractor; ambiguous
priors; invalid ACT/QUIZ/DONE; wake length versus record length; unchanged
production grammar versus fenced content; integer/Boolean type errors;
source-join/capture corruption including rehashed corruption; source pin
mismatch; backend exceptions without retry; same IDs/budgets with differing
state actions; and repeatable replay. No native model result was produced,
read, selected or used to tune this contract.

- `/tmp/astra_level1_real_record_core_20260913.py`
  SHA256 `1c7723fcbb07ad75464d9ceae9fbd1cb8953f6dc0cb7a2e22d3046421167a15c`
- `/tmp/test_astra_level1_real_record_core_20260913.py`
  SHA256 `0fd661e63cdb818b78f32ba279a1719c79d9e1464db43ffd14929e23235fb1b9`
- `/tmp/astra_level1_real_record_handoff_20260913.md`
  SHA256 reported separately, not self-embedded.

Frozen source hashes were rechecked after tests and match the declaration.
Previous prediction/goal and repetition/meta material hashes also remain
unchanged. Only the three owned files were written. Main owns final source
freeze, native OFF/perception-seed0/1/2 captures and launch; no runtime pause
or extra C11 gate is introduced. Formation only: no teacher rewriting,
two-action L2 admission comparison, fit, closed loop or H1/P1 claim.

## Final interface relay — Main's pre-freeze96/192 ruling

Read `/tmp/astra_level1_real_record_run_20260913_handoff.md`. Retain the
ALREADY IMPLEMENTED API rather than introducing build_episodes/run_episode.
The only core behavioral change is wake/action token cap64→96; record remains
192. Exact prompts, eight episode IDs, parser, game, scorer and call counts
are unchanged. Contract/request/capture hashes necessarily reflect the new
declared cap. This is interface coordination before native results, not a
result-driven corpus or policy change. One suite invocation after this amendment
passed all nine tests, including an explicit96/192 request-cap assertion.

Concrete final callable signatures:

```python
deps = core.load_dependencies(source_root=source_snapshot_root)
ids = core.episode_ids()
declared = core.contract(deps)
capture = core.run_state(state, backend, dependencies=deps, binding=route_binding)
audit = core.audit_capture(capture, dependencies=deps)
comparison = core.compare_states(captures, dependencies=deps)
```

`source_snapshot_root` contains `organism_v6/rulegame.py` and
`organism_v6/rulegame_parenting_diagnostic.py` at the declared pins. State
strings are exactly OFF/perception_seed0/perception_seed1/perception_seed2.
`run_state` owns all eight episodes and16wake calls; do not call it once per
episode. It is synchronous and does not manage native processes. Lovelace's
one-fresh-process-per-state design can wrap it without changing core.

Callback is `backend(request_dict)`, NOT `generate(messages, kind)` directly.
If adapting that proposed runner callback, the mapping is:

```python
def backend(request):
    kind = "action" if request["kind"] == "wake" else "record"
    response = generate(request["input_messages"], kind)
    return {
        "request_id": request["request_id"],
        "state": request["state"],
        "raw": response["text"],
        "finish_reason": response["finish_reason"],
        "native": response,
    }
```

Runner must enforce action96/record192, retain exact text/token/route metadata,
and verify the actual selected state route; echoing state alone proves nothing.
Never strip fences/text or supply missing finish reasons. Core request kinds
remain `wake`/`record`, while the runner may name its native call `action`.
`max_output_tokens` is96/192 respectively. Per-state actual callbacks are16
wakes +0–16records, never more than32. The core supplies no teacher answer and
the adapter layer must not either. Existing frozen source pins remain unchanged.
