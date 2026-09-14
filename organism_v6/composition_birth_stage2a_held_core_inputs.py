"""Evaluator-only intervention cores under the prospectively pinned binding.

Reconstructs exact held members; never changes their source, target or prefix.
Depth is the registered designated span, not a hypothetical complete route.
All output, including source and binding receipts, stays in evaluator custody.
No source/native readiness, separation, or scientific claim is certified.
"""

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from hashlib import sha256
import json
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_checker as checker
from organism_v6 import composition_birth_stage2a_graph as graph
from organism_v6 import composition_birth_stage2a_graph_inputs as graph_inputs
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_source_inputs as source_inputs
from organism_v6 import composition_birth_stage2a_worlds as worlds
from organism_v6.composition_birth_stage2a_primitives import canonical_json


STATUS = "PARTIAL_SOURCE_ONLY"
BINDING_PATH = "research_notes/analysis/2026-09-14_stage2a_held_core_binding_v1.md"
BINDING_SHA256 = "5d16106b64e3bd36772e0df9cbb70f249fb35da10e4b10cb058deb178ca81012"
BINDING_SCHEMA_VERSION = "M2A-HELD-CORE-BINDING-V1"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(wire.SCIENCE_GATES, False))
GO_WRITE_ROOT = False
GO_MATERIALIZE = False
GO_MODEL_TOKENIZER = False
GO_FIT_OR_GPU = False
GO_CLAIM = False
GO_SOURCE_READY = False


class HeldCoreInputError(ValueError):
    """The supplied member is not the exact bound intervention source."""


@dataclass(frozen=True)
class InterventionCoreInputs:
    world: str
    member: str
    core_bytes: bytes
    checker_payload: bytes
    receipt_bytes: bytes
    binding_receipt_bytes: bytes
    source_bytes: bytes
    role_bindings_bytes: bytes
    prefix_bytes: bytes
    target_bytes: bytes
    world_graph_bytes: bytes
    public_graph_bytes: bytes
    signature_bytes: bytes
    core_sha256: str
    world_graph_sha256: str
    public_graph_sha256: str
    signature_sha256: str

    status = STATUS
    binding_sha256 = BINDING_SHA256
    science_gates = SCIENCE_GATES

    @property
    def core(self):
        return json.loads(self.core_bytes)

    @property
    def receipt(self):
        return json.loads(self.receipt_bytes)

    @property
    def binding_receipt(self):
        return json.loads(self.binding_receipt_bytes)

    @property
    def hashes(self):
        return self.receipt["hashes"]


def _source_value(value):
    if is_dataclass(value):
        return {field.name: _source_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        if all(type(key) is str for key in value):
            return {key: _source_value(item) for key, item in value.items()}
        return [{"key": _source_value(key), "value": _source_value(item)}
                for key, item in sorted(value.items())]
    if type(value) is tuple:
        return [_source_value(item) for item in value]
    return value


def _reconstruct(member, role_tokens):
    if (type(member) is not held.InterventionMember
            or type(member.construction) is not worlds.OrdinaryConstruction
            or type(member.member) is not str or member.member not in ("m0", "m1")):
        raise HeldCoreInputError("typed_intervention_source_required")
    if (not isinstance(role_tokens, Mapping) or len(role_tokens) > 32768
            or any(type(role) is not str or len(role) > 256 or not role.isascii()
                   or type(token) is not str or len(token) != 17 or not token.isascii()
                   for role, token in role_tokens.items())):
        raise HeldCoreInputError("bounded_per_world_role_bindings_required")
    tokens = MappingProxyType(dict(role_tokens))
    pair = held.build_intervention_pair(world=member.construction.world, role_tokens=tokens)
    exact = next(candidate for candidate in pair.members if candidate.member == member.member)
    if not source_inputs._same_source(member, exact):
        raise HeldCoreInputError("exact_constructor_member_mismatch")
    return pair, exact, tokens


def _owned_event(member):
    selected = member.selected_event
    owners = [(request, position, row)
              for request, block in member.construction.blocks.items() if block.kind == "EVENTS"
              for position, row in enumerate(block.rows) if row.event == selected.event]
    if len(owners) != 1 or owners[0][2] != selected or selected.node != member.task.start:
        raise HeldCoreInputError("registered_selected_event_required")
    key = (selected.node, selected.port)
    if key not in member.world_edges or member.world_edges[key] != selected.got:
        raise HeldCoreInputError("registered_selected_did_transition_required")
    effective = member.execute_step(*key)
    return owners[0], effective


def _replay(member):
    prefix = member.expected_causal_prefix
    task = wire.parse_task(prefix[1].content)
    current = task.current
    retained_events = {}
    retained_routes = []
    latest_step = None
    for offset in range(2, len(prefix), 2):
        actor, host = prefix[offset:offset + 2]
        if (actor.role, host.role) != ("assistant", "user"):
            raise HeldCoreInputError("invalid_retained_roles")
        action = wire.parse_action(actor.content)
        if action.operation == "READ":
            raw = member.read(actor.content)
            if host.content != "SERVICE\n" + raw:
                raise HeldCoreInputError("inauthentic_retained_service")
            block = wire.parse_service(raw, skin=member.construction.skin)
            if block.kind == "ROUTES":
                retained_routes.extend(enumerate(block.rows))
            elif block.kind == "EVENTS":
                retained_events.update((row.event, (position, row))
                                       for position, row in enumerate(block.rows))
        elif action.operation == "STEP":
            owners = [(position, row) for position, row in retained_events.values()
                      if row.node == current and row.port == action.operand]
            if len(owners) != 1 or owners[0][1] != member.selected_event:
                raise HeldCoreInputError("retained_step_event_ownership_mismatch")
            effective = member.execute_step(current, action.operand)
            if host.content != effective.world_message:
                raise HeldCoreInputError("inauthentic_retained_world")
            current = wire.parse_world(host.content)
            latest_step = (*owners[0], current)
        else:
            raise HeldCoreInputError("unexpected_intervention_prefix_action")
    transition = member.transition_name
    if transition == "seek":
        candidates = [(position, row) for position, row in retained_routes
                      if row.node == current and row.goal == task.goal]
        if len(candidates) != 1:
            raise HeldCoreInputError("retained_route_position_required")
        position = candidates[0][0]
    elif transition == "prospect":
        candidates = [(position, row) for position, row in retained_events.values()
                      if row.node == current and row.goal == task.goal]
        if len(candidates) != 1 or candidates[0][1] != member.selected_event:
            raise HeldCoreInputError("retained_event_position_required")
        position = candidates[0][0]
    elif transition == "check":
        if latest_step is None:
            raise HeldCoreInputError("check_requires_retained_step")
        position = latest_step[0]
    else:
        position = None
    observed = latest_step is not None
    if observed != (transition == "check"):
        raise HeldCoreInputError("unexpected_retained_outcome")
    match = latest_step[1].got == latest_step[2] if observed else None
    return current, position, observed, match


def build_intervention_core_inputs(*, member, role_tokens):
    """Assemble one exact member without caller-supplied core annotations.

    The caller supplies only a member and its exact per-world token bindings.
    These are source-consistency inputs, not authenticated allocation roots.
    """
    try:
        pair, exact, tokens = _reconstruct(member, role_tokens)
        (request, registered_position, root), effective = _owned_event(exact)
        current, position, observed, match = _replay(exact)
        reached = exact.task.start == exact.task.goal
        goal_role = next(role for role, token in tokens.items() if token == exact.task.goal)
        if reached:
            if exact.transition_name != "continue" or root != pair.members[0].selected_event:
                raise HeldCoreInputError("reached_pair_reference_required")
            side, root_basis, side_basis = "LEFT", "PAIR_REFERENCE_EVENT", "PAIR_REFERENCE"
        else:
            if root.goal != exact.task.goal:
                raise HeldCoreInputError("designated_event_goal_mismatch")
            goal_index = int(goal_role.split("/")[2][1:])
            pins = held.intervention_pins(exact.transition_name, exact.pair_index)
            if goal_index not in (pins[0][1], pins[1][1]):
                raise HeldCoreInputError("unbound_goal_role")
            side = "LEFT" if goal_index == pins[0][1] else "RIGHT"
            root_basis, side_basis = "DESIGNATED_SOURCE_EVENT", "BOUND_GOAL_ROLE"
        packet = graph_inputs.build_intervention_graph_packet(
            exact, role_tokens=tokens, observed_prefix=exact.expected_causal_prefix,
            root_event=root.event, world_current=current)
        mismatch = observed and not match
        core = graph.decision_core(
            packet["public_graph"], actual_route_depth=0 if reached else 1,
            family_motif="C_CROSSING_WEAVE", flow="RECOVERY" if mismatch else "ORDINARY",
            goal_side=side, phase="STEP_CHECK" if exact.transition_name == "check"
            else exact.transition_name.upper(), predicted_actual_match=match,
            recovery_subtype="STEP_OUTCOME_MISMATCH" if mismatch else "NONE",
            relevant_candidate_display_position=position, skin=exact.construction.skin,
            terminal_class="REACHED" if current == exact.task.goal else "UNRESOLVED",
            step_outcome_observed=observed)
        world = packet["world_graph"]
        radii = {f"r{radius}": graph.radius_graph(world, radius) for radius in range(4)}
        hashes = {"world_graph": graph.graph_hash(world),
                  "public_graph": graph.graph_hash(packet["public_graph"]),
                  "radii": graph.signature(world), "signature": graph.signature_hash(world),
                  "core": graph.core_hash(core, step_outcome_observed=observed)}
        envelope = {"schema_version": checker.SCHEMA_VERSION, "world_graph": world,
                    "core": core, "public_to_world_aliases": packet["public_to_world_aliases"],
                    "step_outcome_observed": observed, "radius_graphs": radii,
                    "expected_hashes": hashes}
        payload = checker.canonical_json_bytes(envelope)
        receipt_bytes = canonical_json(checker.check_graph_core_json(payload))
        source_bytes = canonical_json(_source_value(exact))
        role_bytes = canonical_json(dict(tokens))
        prefix_bytes = canonical_json(_source_value(exact.expected_causal_prefix))
        target_bytes = exact.expected_target.bytes.encode("ascii")
        owners = {token: role for role, token in tokens.items()}
        binding = {
            "schema_version": BINDING_SCHEMA_VERSION, "status": STATUS,
            "binding_path": BINDING_PATH, "binding_sha256": BINDING_SHA256,
            "contract_sha256": held.MEMO_SHA256,
            "clarification_sha256": held.CLARIFICATION_SHA256,
            "route_corrigendum_sha256": held.ROUTE_CORRIGENDUM_SHA256,
            "checker_schema_version": checker.SCHEMA_VERSION,
            "world": exact.construction.world, "member": exact.member,
            "transition": exact.transition_name,
            "depth_basis": "REGISTERED_DESIGNATED_SPAN",
            "continuation_status": "ALREADY_REACHED" if reached else "UNREGISTERED_AFTER_SPAN",
            "root_basis": root_basis, "goal_side_basis": side_basis, "goal_role": goal_role,
            "actual_route_depth": core["actual_route_depth"], "goal_side": side,
            "source_ownership": {
                "event": root.event, "event_role": owners[root.event],
                "port": root.port, "port_role": owners[root.port],
                "node": root.node, "node_role": owners[root.node],
                "event_goal": root.goal, "event_goal_role": owners[root.goal],
                "registered_request": request, "registered_display_position": registered_position,
                "base_destination": exact.world_edges[root.node, root.port],
                "effective_destination": effective.destination,
                "effective_destination_role": owners[effective.destination],
                "outcome_receipt": _source_value(effective.receipt)},
            "current": current, "step_outcome_observed": observed,
            "predicted_actual_match": match,
            "allowed_pair_differences": sorted(pair.allowed_differences),
            "source_sha256": sha256(source_bytes).hexdigest(),
            "role_bindings_sha256": sha256(role_bytes).hexdigest(),
            "prefix_sha256": sha256(prefix_bytes).hexdigest(),
            "target_sha256": sha256(target_bytes).hexdigest(),
            "checker_payload_sha256": sha256(payload).hexdigest(),
            "checker_receipt_sha256": sha256(receipt_bytes).hexdigest(),
            "hashes": hashes, "science_gates": dict(SCIENCE_GATES),
            "source_ready": False, "native_ready": False,
            "held_birth_separation_checked": False}
        return InterventionCoreInputs(
            exact.construction.world, exact.member,
            graph.core_bytes(core, step_outcome_observed=observed), payload, receipt_bytes,
            canonical_json(binding), source_bytes, role_bytes, prefix_bytes, target_bytes,
            graph.graph_bytes(world), graph.graph_bytes(packet["public_graph"]),
            graph.signature_bytes(world), hashes["core"], hashes["world_graph"],
            hashes["public_graph"], hashes["signature"])
    except (ValueError, TypeError, KeyError, AttributeError, StopIteration) as error:
        raise HeldCoreInputError("intervention_core_source_validation_failed: " + str(error)) from error
