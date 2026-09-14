"""Non-material, read-only recovery of completed reduced D1/D2 screen custody.

Replay uses retained requests/generations and the frozen CPU drivers, never a
model, trainer, checkpoint loader or new scorer. BASE and ATOM_LOCAL trees use
the same interface; Main owns their distinct expected identities and provenance.
Only Message, DecodeRequest and Generation are decoded by fixed constructors.
Tensor sidecars are hash-verified by the existing custody verifier, never loaded.

Returned native_records are minimal replay joins, not reconstructed native
tensors or fresh native evidence. Keep the original tree: it remains authoritative
for native output, diagnostics and provenance. Counter provenance is retained,
not authenticated. Whole-bundle replacement cannot be detected by custody hashes.
No GPU, persistence, training, eligibility or scientific-claim gate is promoted.
"""

from dataclasses import replace
from types import SimpleNamespace

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_held as held_api
from organism_v6 import composition_birth_stage2a_rollout as rollout
from organism_v6 import composition_birth_stage2a_screen as screen
from organism_v6 import composition_birth_stage2a_screen_custody as custody
from organism_v6 import composition_birth_stage2a_screen_reduce as reducer
from organism_v6 import composition_birth_stage2a_screen_runtime as runtime


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _project(value, context):
    encoder = custody._Encoder(context)
    encoded = encoder.encode(value)
    _require(not encoder.issues, "unsupported_replay_projection")
    return encoded


def _request(value):
    fields = custody._record(value, rollout.DecodeRequest)
    messages = []
    for encoded in custody._tuple(fields["prefix"]):
        message = custody._record(encoded, held_api.Message)
        messages.append(held_api.Message(custody._scalar(message["role"], str),
                                         custody._scalar(message["content"], str)))
    return rollout.DecodeRequest(tuple(messages),
                                 custody._scalar(fields["max_new_tokens"], int),
                                 custody._scalar(fields["seed"], int),
                                 custody._scalar(fields["context_tokens"], int))


def _generation(value):
    fields = custody._record(value, rollout.Generation)
    return rollout.Generation(custody._scalar(fields["raw"], str),
                              custody._scalar(fields["declared_tokens"], int),
                              custody._scalar(fields["actual_tokens"], int),
                              custody._scalar(fields["truncated"], bool),
                              custody._scalar(fields["finish_reason"], str))


def _native_join(fields, generation, context):
    records = custody._tuple(fields["native_records"])
    _require(len(records) == 1, "one_native_record_per_call_required")
    encoded = records[0]
    _require(type(encoded) is list and len(encoded) == 2 and encoded[0] == "dict"
             and type(encoded[1]) is list, "encoded_native_dictionary_required")
    native = {}
    for pair in encoded[1]:
        _require(type(pair) is list and len(pair) == 2, "invalid_native_field")
        name = custody._scalar(pair[0], str)
        _require(name not in native, "duplicate_native_field")
        native[name] = pair[1]
    _require(native.get("request") == fields["request"]
             and native.get("generation") == fields["generation"]
             and native.get("error") == ["NoneType", None], "native_capture_join_mismatch")
    for name, value in (("raw", generation.raw), ("raw_bytes", wire._raw_bytes(generation.raw))):
        _require(name not in native or native[name] == _project(value, context),
                 "native_raw_join_mismatch")


def replay_state(directory, *, state_id, master, held, stage="D1", count_context=None,
                 limits=custody.ReceiptLimits()):
    """Return a validated ScreenRun for one copied, completed D1 or D2 event tree.

    held has .chains, .interventions and .canaries, as native_prepare.ReducedHeld
    does. Supply the original master and expected state_id (never infer these
    from a receipt). Optional count_context(prefix) is a trusted CPU tokenizer
    callback; its exact integer count must match every retained request. Without
    it, replay uses captured counts without claiming tokenizer verification.

    Verification, exact ordered request matching, native request/generation joins
    and complete regenerated reservation/driver ledger equality are mandatory.
    Missing, surplus, reordered, aborted, incomplete or mismatched evidence raises
    ValueError (filesystem errors propagate). No partial run is returned as valid.
    stage defaults to D1; D2 requires stage="D2" and uses its own slots/seeds.
    Stage is never inferred from the tree or relabeled. Malformed model answers
    remain scored misses, not replay failures. Pass BASE D1 and ATOM results
    unchanged to screen_reduce.reduce_base_d1 or reduce_base_d2 as appropriate,
    with the same master and held bindings.

    This reads but never writes the supplied tree. Caller owns exclusive access
    during verification; original native tensors remain only in that tree.
    """
    _require(reducer._identity(state_id), "explicit_state_identity_required")
    _require(type(stage) is str and stage in ("D1", "D2"), "explicit_D1_or_D2_stage_required")
    _require(count_context is None or callable(count_context), "context_counter_must_be_callable")
    receipt = custody.verify_receipt(directory, limits=limits)
    _require(receipt.state_id == state_id and receipt.stage == stage,
             "state_or_stage_identity_mismatch")
    _require(receipt.terminal_reason == "completed_unscored", "failed_or_incomplete_run")
    bindings = runtime._bindings(screen.reduced_screen(stage), held.chains,
                                 held.interventions, held.canaries)
    initial = custody._record(receipt.events[0]["payload"], runtime.ScreenRun)
    provenance = custody._scalar(initial["counter_provenance"], str)
    context = SimpleNamespace(_captures={}, limits=limits, torch=None)
    captures = []
    for document in receipt.events:
        if document["event"] != "CALL_CAPTURED":
            continue
        fields = custody._record(document["payload"], runtime.CallCustody)
        _require(all(fields[name] == ["NoneType", None]
                     for name in ("actor_error", "capture_error", "sink_error")), "capture_failure")
        _require(custody._scalar(fields["physical_call"], int) == len(captures),
                 "physical_calls_not_contiguous")
        actor_index = custody._scalar(fields["actor_call_index"], int)
        request, generation = _request(fields["request"]), _generation(fields["generation"])
        _native_join(fields, generation, context)
        captures.append((request, generation, actor_index))
    _require(bool(captures), "missing_replay_capture")
    position = event_position = 0
    records = []

    def counter(prefix):
        _require(position < len(captures), "missing_replay_capture")
        request = captures[position][0]
        _require(prefix == request.prefix, "captured_public_prefix_mismatch")
        if count_context is not None:
            measured = count_context(prefix)
            _require(type(measured) is int and measured == request.context_tokens,
                     "captured_context_count_mismatch")
        return request.context_tokens

    def actor(request):
        nonlocal position
        _require(position < len(captures), "extra_replay_call")
        captured, generation, unused_index = captures[position]
        _require(request == captured, "captured_request_mismatch")
        position += 1
        records.append(dict(request=request, generation=generation, error=None,
                            raw=generation.raw, raw_bytes=wire._raw_bytes(generation.raw)))
        return generation

    def sink(event, payload):
        nonlocal event_position
        _require(event_position < len(receipt.events), "extra_replay_event")
        document = receipt.events[event_position]
        _require(event == document["event"], "replay_event_order_mismatch")
        actual, expected = _project(payload, context), document["payload"]
        if event == "CALL_CAPTURED":
            actual_fields = custody._record(actual, runtime.CallCustody)
            expected_fields = custody._record(expected, runtime.CallCustody)
            for name in ("native_records", "actor_call_index"):
                actual_fields.pop(name)
                expected_fields.pop(name)
            _require(actual_fields == expected_fields, "captured_call_mismatch")
            context._captures[id(payload)] = (payload, event_position)
        else:
            _require(actual == expected, "replay_ledger_mismatch:" + event)
        event_position += 1

    run = runtime.run_reduced_state(
        state_id=state_id, stage=stage, master=master, chains=bindings[0],
        interventions=bindings[1], canaries=bindings[2], actor=actor,
        actor_calls=records, count_context=counter, counter_provenance=provenance,
        custody_sink=sink)
    if run.failures:
        error = run.failures[0].error
        raise ValueError("captured_replay_failed:" + str(error)) from error
    _require(run.terminal_reason == "completed_unscored" and position == len(captures)
             and event_position == len(receipt.events), "captured_replay_incomplete")
    indexes = iter(capture[2] for capture in captures)
    run = replace(run, reservations=tuple(
        replace(row, custody=replace(row.custody, actor_call_index=next(indexes)))
        if row.custody is not None else row for row in run.reservations))
    reducer._captures(run, state_id, screen.reduced_decode_seeds(stage, master=master), set(), stage=stage)
    return run
