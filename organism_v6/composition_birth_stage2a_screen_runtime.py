"""Bounded single-state reduced-screen dispatch, never native qualification.

This non-material composition of frozen drivers constructs no material, loads
nothing, selects no checkpoint, scores nothing, and admits neither D1 nor D2.
The supplied stage selects existing logical slots only. State/attempt identity,
input admission, native provenance, deadlines, devices, thread pins and durable
custody remain caller responsibilities. Supplied objects/callbacks are trusted
in-process collaborators with exclusive actor/custody access, not a sandbox.

The sink receives (event, payload): SCREEN_RESERVED, CALL_RESERVED,
CALL_CAPTURED, SCREEN_FINISHED. These are in-memory notifications, not a material
serialization schema. Native records, return values and original exceptions
are retained by reference: JSON/repr is not a lossless serialization contract.
The caller must retain the returned ScreenRun even if the sink fails. A sink
exception is never retried; no later sink or actor calls follow it. Process
death before a callback returns is outside this synchronous custody boundary.
"""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_canaries as canary_api
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_probe as probe
from organism_v6 import composition_birth_stage2a_rollout as rollout
from organism_v6 import composition_birth_stage2a_screen as screen


STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(screen.SCIENCE_GATES, False))
_DRIVER_FAULTS = frozenset((
    "context_counter_error", "invalid_context_count", "actor_callback_error",
    "invalid_generation_transport", "unsupported_custody_transport", "invalid_output_transport",
    "invalid_token_accounting", "invalid_generation_metadata", "unbound_finish_reason",
    "invalid_generation_request", "session_terminated",
))


@dataclass(frozen=True)
class CallCustody:
    state_id: str
    slot: primitives.LogicalSlot
    request: rollout.DecodeRequest
    physical_call: int | None = None
    actor_call_index: int | None = None
    generation: object = None
    native_records: tuple = ()
    actor_error: BaseException | None = None
    capture_error: BaseException | None = None
    sink_error: BaseException | None = None


@dataclass(frozen=True)
class Reservation:
    entry: screen.ScreenEntry
    seed: int
    disposition: str = "NOT_REACHED"
    driver_record: object = None
    custody: CallCustody | None = None


@dataclass(frozen=True)
class Failure:
    phase: str
    slot: primitives.LogicalSlot | None
    error: BaseException


@dataclass(frozen=True)
class ScreenRun:
    state_id: str
    stage: str
    reservations: tuple[Reservation, ...]
    chain_runs: tuple[rollout.ChainRun, ...]
    probe_runs: tuple[probe.ProbeRun, ...]
    failures: tuple[Failure, ...]
    terminal_reason: str
    counter_provenance: str
    status: str = STATUS

    @property
    def calls(self):
        return tuple(reservation.custody for reservation in self.reservations
                     if reservation.custody is not None)


def _transport_fault(capture):
    """Apply the frozen probe transport rules even if a chain parsed first."""
    if capture is None or type(capture.generation) is not rollout.Generation:
        return None
    generation = capture.generation
    if type(generation.raw) is not str or wire._raw_bytes(generation.raw) is None:
        return "invalid_output_transport"
    if (type(generation.declared_tokens) is not int or type(generation.actual_tokens) is not int
            or not 0 < generation.actual_tokens <= capture.request.max_new_tokens
            or generation.declared_tokens != generation.actual_tokens):
        return "invalid_token_accounting"
    if type(generation.truncated) is not bool or type(generation.finish_reason) is not str:
        return "invalid_generation_metadata"
    if not generation.truncated and generation.finish_reason not in ("stop", "length"):
        return "unbound_finish_reason"
    return None


def _bindings(roster, chains, interventions, canaries):
    if not isinstance(chains, Mapping) or not isinstance(interventions, Mapping):
        raise ValueError("explicit_reduced_object_mappings_required")
    chains, interventions = dict(chains), dict(interventions)
    tasks = {entry.index for entry in roster if entry.kind == "CHAIN"}
    pairs = {(entry.transition, entry.index) for entry in roster if entry.kind == "INTERVENTION"}
    if set(chains) != tasks or any(type(key) is not int for key in chains):
        raise ValueError("exact_reduced_chain_bindings_required")
    for task, world in chains.items():
        if type(world) is not held.ChainWorld or world.world != f"h{task // 2:02d}":
            raise ValueError("chain_world_binding_mismatch")
    if (set(interventions) != pairs
            or any(type(key) is not tuple or len(key) != 2
                   or type(key[0]) is not str or type(key[1]) is not int for key in interventions)):
        raise ValueError("exact_reduced_intervention_bindings_required")
    for (transition, index), pair in interventions.items():
        if (type(pair) is not held.InterventionPair or pair.world != f"{transition.lower()}_k{index}"
                or type(pair.members) is not tuple or len(pair.members) != 2
                or any(type(member) is not held.InterventionMember
                       or member.transition_name != transition.lower()
                       or type(member.pair_index) is not int or member.pair_index != index
                       or member.member != f"m{position}" for position, member in enumerate(pair.members))):
            raise ValueError("intervention_pair_binding_mismatch")
    if (type(canaries) is not tuple or len(canaries) != 16
            or any(type(item) is not canary_api.Canary or type(item.index) is not int
                   or item.index != index for index, item in enumerate(canaries))):
        raise ValueError("exact_ordered_canary_bindings_required")
    return chains, interventions, canaries


def run_reduced_state(*, state_id, stage, master, chains, interventions, canaries,
                      actor, actor_calls, count_context, counter_provenance, custody_sink):
    """Dispatch exactly one supplied state; retain all 280 logical reservations.

    chains maps reduced task indices to existing ChainWorlds. interventions maps
    (uppercase transition, pair index) to existing InterventionPairs; canaries
    is the ordered existing 16-Canary tuple. No targets reach the actor except
    the already-public canary copy prompt. actor_calls is the caller's actual
    append-only list (e.g. ReadoutActor.calls): each invocation must append one
    fresh dict whose request is the same DecodeRequest object it received.

    state_id is an opaque caller binding, not an authenticated checkpoint. The
    caller owns uniqueness across attempts. physical_call is zero-based within
    this dispatch and is None if the native actor was never entered;
    actor_call_index separately indexes its supplied, possibly prepopulated list.
    Raw captures precede join/transport validation and survive sink failures.

    Bad bindings raise before callbacks. Operational errors instead abort the
    screen and return original exceptions in failures; callers must inspect
    them. Returned driver transport/accounting faults also abort after retaining
    the unchanged driver record and native capture. Their ValueError reasons
    are dispatcher diagnostics, not reconstructed original native exceptions.
    Wrong actions, length stops and unused slots with valid transport remain
    ordinary outcomes, not retries or new acceptance decisions.
    """
    if type(state_id) is not str or not state_id.strip() or not state_id.isascii() or "\0" in state_id:
        raise ValueError("explicit_state_identity_required")
    if not all(callable(callback) for callback in (actor, count_context, custody_sink)):
        raise ValueError("actor_counter_and_custody_sink_required")
    if type(actor_calls) is not list:
        raise ValueError("explicit_append_only_actor_custody_list_required")
    if type(counter_provenance) is not str or not counter_provenance.strip():
        raise ValueError("explicit_counter_provenance_required")
    roster = screen.reduced_screen(stage)
    seeds = screen.reduced_decode_seeds(stage, master=master)
    chains, interventions, canaries = _bindings(roster, chains, interventions, canaries)
    reservations = [Reservation(entry, seed) for entry, seed in zip(roster, seeds)]
    chain_runs, probe_runs, failures = [], [], []
    history = tuple(actor_calls)
    physical_count = 0
    sink_broken = False
    active, position = (), 0

    def snapshot(reason):
        return ScreenRun(state_id, stage, tuple(reservations), tuple(chain_runs), tuple(probe_runs),
                         tuple(failures), reason, counter_provenance)

    def fail(phase, error, index=None):
        failures.append(Failure(phase, None if index is None else roster[index].slot, error))

    def driver_result(reason, index):
        if any(failure.slot == roster[index].slot for failure in failures):
            return
        custody = reservations[index].custody
        fault = reason if reason in _DRIVER_FAULTS else _transport_fault(custody)
        if fault is not None:
            if custody is not None and custody.physical_call is not None:
                reservations[index] = replace(reservations[index], disposition="ERROR")
            fail("driver_result", ValueError(fault), index)

    def emit(event, payload, index=None):
        nonlocal sink_broken
        if sink_broken:
            return False
        try:
            custody_sink(event, payload)
        except BaseException as error:
            sink_broken = True
            fail(event, error, index)
            return False
        return True

    def counter(prefix):
        index = active[position]
        try:
            value = count_context(prefix)
            if type(value) is not int or not 0 <= value <= wire.CONTEXT_CAP:
                raise ValueError("invalid_context_count", value)
            return value
        except BaseException as error:
            reservations[index] = replace(reservations[index], disposition="NOT_CALLED")
            fail("count_context", error, index)
            raise

    def invoke(request):
        nonlocal position, physical_count, history
        index = active[position]
        position += 1
        capture = CallCustody(state_id, roster[index].slot, request)
        reservations[index] = replace(reservations[index], disposition="NOT_CALLED", custody=capture)
        if not emit("CALL_RESERVED", capture, index):
            capture = replace(capture, sink_error=failures[-1].error)
            reservations[index] = replace(reservations[index], custody=capture)
            raise capture.sink_error
        before = history
        try:
            if type(request) is not rollout.DecodeRequest or request.seed != reservations[index].seed:
                raise ValueError("logical_request_seed_binding_mismatch")
            if len(actor_calls) != len(before) or any(current is not old for current, old in zip(actor_calls, before)):
                raise ValueError("actor_custody_changed_outside_call")
            capture = replace(capture, physical_call=physical_count, actor_call_index=len(before))
            physical_count += 1
            try:
                capture = replace(capture, generation=actor(request))
            except BaseException as error:
                capture = replace(capture, actor_error=error)
                fail("actor", error, index)
        except BaseException as error:
            capture = replace(capture, capture_error=error)
            fail("call_binding", error, index)
        finally:
            observed = tuple(actor_calls)
            appended = (len(observed) >= len(before)
                        and all(current is old for current, old in zip(observed, before)))
            native_records = observed[len(before):] if appended else observed
            capture = replace(capture, native_records=native_records)
            if capture.physical_call is not None:
                try:
                    if (not appended or len(native_records) != 1
                            or any(native_records[0] is old for old in before)):
                        raise ValueError("actor_custody_not_one_fresh_append")
                    record = native_records[0]
                    if type(record) is not dict or record.get("request") is not request:
                        raise ValueError("actor_custody_request_binding_mismatch")
                    if capture.actor_error is None and type(capture.generation) is not rollout.Generation:
                        raise ValueError("invalid_generation_transport")
                except BaseException as error:
                    capture = replace(capture, capture_error=error)
                    fail("actor_custody", error, index)
            history = observed
            reservations[index] = replace(reservations[index], custody=capture)
            if not emit("CALL_CAPTURED", capture, index):
                capture = replace(capture, sink_error=failures[-1].error)
                reservations[index] = replace(reservations[index], custody=capture)
        error = capture.actor_error or capture.capture_error or capture.sink_error
        if error is not None:
            reservations[index] = replace(reservations[index],
                                          disposition="ERROR" if capture.physical_call is not None else "NOT_CALLED")
            raise error
        reservations[index] = replace(reservations[index], disposition="CALLED")
        return capture.generation

    if not emit("SCREEN_RESERVED", snapshot("pending")):
        return snapshot("aborted")
    cursor = 0
    while cursor < len(roster):
        entry = roster[cursor]
        width = wire.CALL_CAP if entry.kind == "CHAIN" else 1
        active, position = tuple(range(cursor, cursor + width)), 0
        try:
            if entry.kind == "CHAIN":
                run = rollout.run_chain(chains[entry.index], f"m{entry.member}", actor=invoke,
                                        count_context=counter, counter_provenance=counter_provenance,
                                        master=master, stage=stage)
                chain_runs.append(run)
                if tuple(record.slot for record in run.calls) != tuple(roster[index].slot for index in active):
                    raise ValueError("chain_driver_reservation_mismatch")
                for index, record in zip(active, run.calls):
                    custody = reservations[index].custody
                    disposition = ("NOT_CALLED" if custody is not None and custody.physical_call is None
                                   else record.disposition)
                    reservations[index] = replace(reservations[index], disposition=disposition, driver_record=record)
                terminal_index = next((index for index in reversed(active)
                                       if reservations[index].driver_record.disposition != "UNUSED"), cursor)
                driver_result(run.terminal_reason, terminal_index)
            else:
                if entry.kind == "INTERVENTION":
                    member = interventions[(entry.transition, entry.index)].members[entry.member]
                    messages = member.public_view().prefix
                else:
                    canary = canaries[entry.index]
                    messages = (held.Message("system", canary.system_text), held.Message("user", canary.user_text))
                run = probe.run_probe(messages, slot=entry.slot, master=master, actor=invoke,
                                      count_context=counter, counter_provenance=counter_provenance)
                probe_runs.append(run)
                custody = reservations[cursor].custody
                called = custody is not None and custody.physical_call is not None
                disposition = ("EXECUTED" if run.generation_valid else "ERROR") if called else "NOT_CALLED"
                reservations[cursor] = replace(reservations[cursor], disposition=disposition, driver_record=run)
                driver_result(run.reason, cursor)
        except BaseException as error:
            if not any(failure.error is error for failure in failures):
                index = active[max(position - 1, 0)]
                if reservations[index].disposition == "NOT_REACHED":
                    reservations[index] = replace(reservations[index], disposition="NOT_CALLED")
                fail("driver", error, index)
            break
        if failures:
            break
        cursor += width
    emit("SCREEN_FINISHED", snapshot("aborted" if failures else "completed_unscored"))
    return snapshot("aborted" if failures else "completed_unscored")
