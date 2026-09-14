"""Evaluator-only complete-chain witness cores; no native actor supervision."""

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from hashlib import sha256
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_checker as checker
from organism_v6 import composition_birth_stage2a_graph as graph
from organism_v6 import composition_birth_stage2a_graph_inputs as graph_inputs
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_worlds as worlds
from organism_v6.composition_birth_stage2a_primitives import canonical_json


STATUS = "PARTIAL_SOURCE_ONLY"
BINDING_PATH = "research_notes/analysis/2026-09-14_stage2a_chain_core_binding_v1.md"
BINDING_SHA256 = "e4ff807927a09b7523092c3df89d8d44c9938847aea0e66f1dd9062e2a67f10a"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(wire.SCIENCE_GATES, False))


class ChainCoreInputError(ValueError):
    """Exact source replay or evaluator-boundary construction failed."""


def _encode(value):
    if is_dataclass(value):
        return {"dataclass": type(value).__module__ + "." + type(value).__qualname__,
                "fields": [[field.name, _encode(getattr(value, field.name))] for field in fields(value)]}
    if isinstance(value, Mapping):
        return {"mapping": [[_encode(key), _encode(item)] for key, item in sorted(value.items())]}
    if type(value) is tuple:
        return {"tuple": [_encode(item) for item in value]}
    if type(value) is frozenset:
        return {"frozenset": [_encode(item) for item in sorted(value)]}
    if value is None or type(value) in (str, int, bool):
        return value
    raise ChainCoreInputError("unsupported_source_type")


@dataclass(frozen=True)
class ChainCoreBoundary:
    world: str
    member: str
    decision_index: int
    core_bytes: bytes
    checker_payload: bytes
    receipt_bytes: bytes
    binding_receipt_bytes: bytes
    prefix_bytes: bytes
    target_bytes: bytes
    signature_bytes: bytes
    core_sha256: str
    signature_sha256: str


@dataclass(frozen=True)
class ChainCoreInputs:
    world: str
    source_bytes: bytes
    role_bindings_bytes: bytes
    boundaries: tuple[ChainCoreBoundary, ...]

    status = STATUS
    science_gates = SCIENCE_GATES
    native_ready = False
    held_birth_separation_checked = False


def _unique(rows, predicate):
    selected = [(position, row) for position, row in enumerate(rows) if predicate(row)]
    if len(selected) != 1:
        raise ChainCoreInputError("unique_retained_row_required")
    return selected[0]


def _replay(chain, member):
    current = member.task.current
    prefix = list(chain.public_view(member.member).prefix)
    directory = None
    events = None
    latest = None
    root = None
    boundaries = []
    steps = 0
    for ordinal, turn in enumerate(member.expected_trace):
        if turn.current_before != current:
            raise ChainCoreInputError("witness_current_before_mismatch")
        action = wire.parse_action(turn.action)
        phase, position = "CONTINUE", None
        if action.operation == "READ" and turn.action.startswith("READ RELATION "):
            phase = "SEEK"
            if latest is not None and latest[1].got != latest[2] and action.operand == latest[1].recover:
                position = latest[0]
            else:
                if directory is None:
                    raise ChainCoreInputError("missing_retained_directory")
                position, unused = _unique(directory.rows, lambda row: row.node == current
                                          and row.goal == member.task.goal and row.query == action.operand)
        elif action.operation == "STEP":
            phase = "PROSPECT"
            if events is None:
                raise ChainCoreInputError("missing_retained_event")
            position, selected = _unique(events.rows, lambda row: row.node == current
                                         and row.goal == member.task.goal and row.port == action.operand)
            if root is None:
                root = selected
        elif action.operation == "THINK":
            phase = "STEP_CHECK"
            if latest is None or action.operand != latest[1].event:
                raise ChainCoreInputError("unowned_think")
            position = latest[0]
            expected = "THINK " + ("KEEP " if latest[1].got == latest[2] else "REVISE ") + latest[1].event
            if turn.action != expected:
                raise ChainCoreInputError("witness_think_outcome_mismatch")
        observed = latest is not None
        match = latest[1].got == latest[2] if observed else None
        boundaries.append((ordinal, tuple(prefix), current, phase, position, observed, match, turn.action))
        after = current
        if action.operation == "READ":
            response = "SERVICE\n" + chain.read(turn.action)
            block = wire.parse_service(response[len("SERVICE\n"):], skin=chain.skin)
            if block.kind == "ROUTES":
                directory = block
            elif block.kind == "EVENTS":
                events = block
        elif action.operation == "STEP":
            after = chain.transition(current, action.operand)
            response = "WORLD\nCURRENT " + after
            latest = position, selected, after
            steps += 1
        elif action.operation == "THINK":
            response = "ACK"
        elif action.operation == "STOP":
            if current != member.task.goal or ordinal != len(member.expected_trace) - 1:
                raise ChainCoreInputError("nonterminal_or_unreached_stop")
            response = None
        else:
            raise ChainCoreInputError("unsupported_witness_action")
        if (turn.response, turn.current_after) != (response, after):
            raise ChainCoreInputError("witness_response_or_destination_mismatch")
        if response is not None:
            prefix.extend((held.Message("assistant", turn.action), held.Message("user", response)))
        current = after
    if steps != 2 or root is None or current != member.task.goal or member.expected_trace[-1].action != "STOP":
        raise ChainCoreInputError("complete_two_step_witness_required")
    return root, tuple(boundaries), steps


def build_chain_core_inputs(*, chain_world, role_tokens):
    """Rebuild one complete world and check every offline witness boundary."""
    try:
        if type(chain_world) is not held.ChainWorld or type(chain_world.construction) is not worlds.OrdinaryConstruction:
            raise ChainCoreInputError("typed_chain_world_required")
        if (not isinstance(role_tokens, Mapping) or len(role_tokens) > 32768
                or any(type(role) is not str or len(role) > 256 or not role.isascii()
                       or type(token) is not str or len(token) != 17 or not token.isascii()
                       for role, token in role_tokens.items())):
            raise ChainCoreInputError("bounded_per_world_roles_required")
        tokens = dict(role_tokens)
        exact = held.build_chain_world(world=chain_world.world, role_tokens=tokens)
        source_bytes = canonical_json(_encode(exact))
        if canonical_json(_encode(chain_world)) != source_bytes:
            raise ChainCoreInputError("exact_constructor_chain_mismatch")
        role_bytes = canonical_json(tokens)
        owners = {token: role for role, token in tokens.items()}
        scored_goals = tuple(goal for goal, unused in worlds.chain_scored_positions(exact.world))
        results = []
        for member in exact.members:
            root, boundaries, depth = _replay(exact, member)
            goal_role = owners[member.task.goal]
            side = ("LEFT", "RIGHT")[scored_goals.index(int(goal_role.split("/")[3]))]
            for ordinal, prefix, current, phase, position, observed, match, target in boundaries:
                packet = graph_inputs.build_chain_graph_packet(
                    exact, member_id=member.member, role_tokens=tokens, observed_prefix=prefix,
                    root_event=root.event, world_current=current)
                mismatch = observed and not match
                core = graph.decision_core(
                    packet["public_graph"], actual_route_depth=depth, family_motif="C_CROSSING_WEAVE",
                    flow="RECOVERY" if mismatch else "ORDINARY", goal_side=side, phase=phase,
                    predicted_actual_match=match,
                    recovery_subtype="STEP_OUTCOME_MISMATCH" if mismatch else "NONE",
                    relevant_candidate_display_position=position, skin=exact.skin,
                    terminal_class="REACHED" if current == member.task.goal else "UNRESOLVED",
                    step_outcome_observed=observed)
                world = packet["world_graph"]
                radii = {f"r{radius}": graph.radius_graph(world, radius) for radius in range(4)}
                hashes = {"world_graph": graph.graph_hash(world), "public_graph": graph.graph_hash(packet["public_graph"]),
                          "radii": graph.signature(world), "signature": graph.signature_hash(world),
                          "core": graph.core_hash(core, step_outcome_observed=observed)}
                payload = checker.canonical_json_bytes({"schema_version": checker.SCHEMA_VERSION,
                    "world_graph": world, "core": core, "public_to_world_aliases": packet["public_to_world_aliases"],
                    "step_outcome_observed": observed, "radius_graphs": radii, "expected_hashes": hashes})
                receipt = canonical_json(checker.check_graph_core_json(payload))
                prefix_bytes = canonical_json(_encode(prefix))
                target_bytes = target.encode("ascii")
                binding = canonical_json({"schema_version": "M2A-CHAIN-CORE-BINDING-V1", "status": STATUS,
                    "binding_sha256": BINDING_SHA256, "world": exact.world, "member": member.member,
                    "decision_index": ordinal, "source_sha256": sha256(source_bytes).hexdigest(),
                    "role_bindings_sha256": sha256(role_bytes).hexdigest(),
                    "prefix_sha256": sha256(prefix_bytes).hexdigest(), "target_sha256": sha256(target_bytes).hexdigest(),
                    "checker_payload_sha256": sha256(payload).hexdigest(), "checker_receipt_sha256": sha256(receipt).hexdigest(),
                    "root_event": root.event, "root_port": root.port, "root_event_role": owners[root.event],
                    "root_port_role": owners[root.port], "root_basis": "FIRST_IRREVERSIBLE_EVENT",
                    "goal_role": goal_role, "goal_side_basis": "CONSTRUCTOR_SCORED_GOALS",
                    "depth_basis": "COMPLETE_EFFECTIVE_REPLAY", "actual_route_depth": depth,
                    "hashes": hashes, "native_ready": False, "held_birth_separation_checked": False})
                results.append(ChainCoreBoundary(exact.world, member.member, ordinal,
                    graph.core_bytes(core, step_outcome_observed=observed), payload, receipt, binding,
                    prefix_bytes, target_bytes, graph.signature_bytes(world), hashes["core"], hashes["signature"]))
        return ChainCoreInputs(exact.world, source_bytes, role_bytes, tuple(results))
    except (ValueError, KeyError, TypeError, AttributeError, IndexError) as error:
        raise ChainCoreInputError("chain_core_source_validation_failed: " + str(error)) from error
