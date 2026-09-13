"""Source-only bounded held rollout; counters and generation are supplied.

This in-memory driver does not load models, authenticate counters, create
material, or confer execution authority. Only immutable public messages and
decode settings cross the actor callback. Registry, world and witnesses stay
host-side. A caller-provided actor remains a trusted in-process callback, not
a security sandbox. Physical attempt numbering across runs belongs upstream.
"""

from dataclasses import dataclass
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_nulls as nulls
from organism_v6 import composition_birth_stage2a_primitives as primitives


STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(nulls.SCIENCE_GATES, False))


@dataclass(frozen=True)
class DecodeRequest:
    prefix: tuple[held.Message, ...]
    max_new_tokens: int
    seed: int
    context_tokens: int


@dataclass(frozen=True)
class Generation:
    raw: str
    declared_tokens: int
    actual_tokens: int
    truncated: bool
    finish_reason: str


@dataclass(frozen=True)
class CallRecord:
    slot: primitives.LogicalSlot
    seed: int
    disposition: str
    request: DecodeRequest | None
    attempt: wire.Attempt | None
    error_type: str | None = None


@dataclass(frozen=True)
class ChainRun:
    calls: tuple[CallRecord, ...]
    attempts: tuple[wire.Attempt, ...]
    prefix: tuple[held.Message, ...]
    state: wire.Snapshot
    terminal_reason: str
    counter_provenance: str
    status: str = STATUS


class _ScheduleStopped(Exception):
    pass


def _initial(world, member):
    if type(world) is not held.ChainWorld:
        raise ValueError("typed_held_chain_world_required")
    if type(member) is not str or member not in ("m0", "m1"):
        raise ValueError("invalid_chain_member")
    index = int(world.world[1:])
    primitives.chain_slot("D1", index, int(member[1:]), 0)
    view = world.public_view(member)
    registry = wire.PassiveRegistry(world.registry, skin=world.skin)
    return index, view.prefix, wire.Session(view.prefix[1].content, world.world_edges, registry)


def run_chain(world, member, *, actor, count_context, counter_provenance, master, stage="D1"):
    """Execute at most 29 supplied generations, retaining every reserved slot.

    Counter provenance is an explicit caller assertion, not validation of
    tokenization. Callback failure or malformed return halts without inventing
    an action receipt or retry. Generated malformed text enters Session custody
    before any parse. No scorer, oracle action, or automatic READ is supplied.
    """
    if not callable(actor) or not callable(count_context):
        raise ValueError("actor_and_context_counter_required")
    if type(counter_provenance) is not str or not counter_provenance.strip():
        raise ValueError("explicit_counter_provenance_required")
    world_index, prefix, session = _initial(world, member)
    slots = tuple(primitives.chain_slot(stage, world_index, int(member[1:]), index)
                  for index in range(wire.CALL_CAP))
    seeds = tuple(primitives.decode_seed(master, slot.panel_label, slot.global_ordinal)
                  for slot in slots)
    records = []
    reason = None
    for slot, seed in zip(slots, seeds):
        if reason is not None:
            records.append(CallRecord(slot, seed, "UNUSED", None, None))
            continue
        try:
            context_tokens = count_context(prefix)
        except Exception as error:
            reason = "context_counter_error"
            records.append(CallRecord(slot, seed, "NOT_CALLED", None, None, type(error).__name__))
            continue
        if type(context_tokens) is not int or not 0 <= context_tokens <= wire.CONTEXT_CAP:
            reason = "invalid_context_count"
            records.append(CallRecord(slot, seed, "NOT_CALLED", None, None))
            continue
        allowance = min(256, wire.TOKEN_CAP - session.state.actual_tokens,
                        wire.CONTEXT_CAP - context_tokens)
        if allowance <= 0:
            reason = "zero_allowance"
            records.append(CallRecord(slot, seed, "NOT_CALLED", None, None))
            continue
        request = DecodeRequest(prefix, allowance, seed, context_tokens)
        try:
            generation = actor(request)
        except _ScheduleStopped as error:
            reason = "schedule_" + str(error)
            records.append(CallRecord(slot, seed, "POLICY_HALTED", request, None))
            continue
        except Exception as error:
            reason = "actor_callback_error"
            records.append(CallRecord(slot, seed, "ERROR", request, None, type(error).__name__))
            continue
        if type(generation) is not Generation:
            reason = "invalid_generation_transport"
            records.append(CallRecord(slot, seed, "ERROR", request, None))
            continue
        try:
            attempt = session.turn(
                generation.raw, generation_request={"max_new_tokens": allowance, "seed": seed},
                declared_tokens=generation.declared_tokens, actual_tokens=generation.actual_tokens,
                context_tokens=context_tokens, truncated=generation.truncated,
                finish_reason=generation.finish_reason,
            )
        except ValueError as error:
            reason = "unsupported_custody_transport"
            records.append(CallRecord(slot, seed, "ERROR", request, None, type(error).__name__))
            continue
        records.append(CallRecord(slot, seed, "EXECUTED", request, attempt))
        if attempt.accepted:
            prefix += (held.Message("assistant", generation.raw),)
            if attempt.response_bytes:
                prefix += (held.Message("user", attempt.response_bytes.decode("ascii")),)
        if session.state.terminated:
            reason = session.state.terminal_reason
    return ChainRun(tuple(records), session.attempts, prefix, session.state,
                    reason or "call_cap", counter_provenance)


def run_schedule(world, member, *, name, count_context, count_action,
                 counter_provenance, master, stage="D1"):
    """Adapt one public-only schedule to the same driver, without fake defaults.

    Counts must be supplied; synthetic fixture counts remain synthetic. A
    schedule may halt without emitting an action. That halt is recorded as
    POLICY_HALTED, never as a fabricated STOP or a successful chain.
    """
    if not callable(count_action):
        raise ValueError("action_counter_required")
    _, prefix, _ = _initial(world, member)
    policy = nulls.BoundedSchedule(name, tuple(
        nulls.PublicMessage(message.role, message.content.encode("ascii")) for message in prefix
    ), skin=world.skin)

    def actor(request):
        if policy.pending is not None:
            if len(request.prefix) < 2 or request.prefix[-1].role != "user":
                raise ValueError("missing_public_host_response")
            policy.observe(request.prefix[-1].content.encode("ascii"))
        decision = policy.next_action()
        if decision.action is None:
            raise _ScheduleStopped(decision.terminal_reason)
        count = count_action(decision.action)
        return Generation(decision.action.decode("ascii"), count, count, False, "stop")

    result = run_chain(world, member, actor=actor, count_context=count_context,
                       counter_provenance=counter_provenance, master=master, stage=stage)
    if policy.pending is not None:
        policy.observe(b"")
    return result
