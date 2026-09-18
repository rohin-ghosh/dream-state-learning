"""One-turn public-message capture for held interventions and copy canaries.

No scoring answer, world or service is passed to the actor. Counter/generator
authenticity remains a caller responsibility. This source does not load a
tokenizer/model, schedule a dose, write material or authorize native execution.
"""

from dataclasses import dataclass
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_rollout as rollout


STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(rollout.SCIENCE_GATES, False))


@dataclass(frozen=True)
class ProbeRun:
    slot: primitives.LogicalSlot
    request: rollout.DecodeRequest | None
    raw_bytes: bytes | None
    generation_capture: tuple | None
    called: bool
    generation_valid: bool
    reason: str
    error_type: str | None
    counter_provenance: str
    status: str = STATUS


def _prefix(messages):
    if type(messages) is not tuple or not messages or len(messages) > 60:
        raise ValueError("bounded_immutable_public_prefix_required")
    projected = []
    for message in messages:
        role, content = getattr(message, "role", None), getattr(message, "content", None)
        if (type(role) is not str or role not in ("system", "user", "assistant")
                or type(content) is not str or not content.isascii() or "\x00" in content or "\r" in content):
            raise ValueError("exact_ascii_public_message_required")
        projected.append(held.Message(role, content))
    if (projected[0].role != "system" or len(projected) < 2
            or any(message.role != ("user" if index % 2 else "assistant")
                   for index, message in enumerate(projected[1:], 1))
            or projected[-1].role != "user"):
        raise ValueError("public_prefix_role_order")
    return tuple(projected)


def run_probe(messages, *, slot, master, actor, count_context, counter_provenance):
    """Capture exactly one call, or retain a pre-call failure; never retry."""
    if type(slot) is not primitives.LogicalSlot or "CHAIN" in slot.panel_label:
        raise ValueError("one_turn_logical_slot_required")
    seed = primitives.decode_seed(master, slot.panel_label, slot.global_ordinal)
    prefix = _prefix(messages)
    if not callable(actor) or not callable(count_context):
        raise ValueError("actor_and_context_counter_required")
    if type(counter_provenance) is not str or not counter_provenance.strip():
        raise ValueError("explicit_counter_provenance_required")

    def result(reason, *, request=None, raw=None, capture=None, called=False, valid=False, error=None):
        return ProbeRun(slot, request, raw, capture, called, valid, reason, error, counter_provenance)

    try:
        context = count_context(prefix)
    except Exception as error:
        return result("context_counter_error", error=type(error).__name__)
    if type(context) is not int or not 0 <= context <= wire.CONTEXT_CAP:
        return result("invalid_context_count")
    allowance = min(256, wire.CONTEXT_CAP - context)
    if allowance <= 0:
        return result("zero_allowance")
    request = rollout.DecodeRequest(prefix, allowance, seed, context)
    try:
        generation = actor(request)
    except Exception as error:
        return result("actor_callback_error", request=request, called=True, error=type(error).__name__)
    if type(generation) is not rollout.Generation:
        return result("invalid_generation_transport", request=request, called=True)
    raw = wire._raw_bytes(generation.raw)
    try:
        capture = wire._freeze((generation.raw, generation.declared_tokens, generation.actual_tokens,
                                generation.truncated, generation.finish_reason))
    except (ValueError, RecursionError) as error:
        return result("unsupported_custody_transport", request=request, raw=raw, called=True,
                      error=type(error).__name__)
    options = dict(request=request, raw=raw, capture=capture, called=True)
    if type(generation.raw) is not str or raw is None:
        return result("invalid_output_transport", **options)
    if (type(generation.declared_tokens) is not int or type(generation.actual_tokens) is not int
            or not 0 < generation.actual_tokens <= allowance
            or generation.declared_tokens != generation.actual_tokens):
        return result("invalid_token_accounting", **options)
    if type(generation.truncated) is not bool or type(generation.finish_reason) is not str:
        return result("invalid_generation_metadata", **options)
    if generation.truncated or generation.finish_reason == "length":
        return result("length_limited", **options)
    if generation.finish_reason != "stop":
        return result("unbound_finish_reason", **options)
    return result("completed_unscored", valid=True, **options)
