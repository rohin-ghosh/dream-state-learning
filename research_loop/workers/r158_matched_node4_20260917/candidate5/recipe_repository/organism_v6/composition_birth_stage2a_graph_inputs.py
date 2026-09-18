"""Partial, in-memory bridges from supplied Stage2A constructions to graphs.

Complete birth, ordinary, and held constructions are admitted.
Role inventories are checked symbolically; no opaque allocation occurs. Explicit
bindings and construction bytes are caller assertions, not authenticated roots.
Birth validation reuses the birth producer, not an independent scientific guard.
Public edges come only from retained authentic trace turns and task facts;
hidden rows are validated but never supply public vertices, edges, or alias ranks.
Each graph numbers its own typed owners. Only induced radii in the graph module
preserve full-world aliases. Alias strings are not cross-graph vertex identities.
The caller must name the first irreversible EVENT: no oracle root is chosen.
Held packets replay explicit held.Message prefixes from the original task,
without reading expected prefixes, witness traces, or semantic answers. CHECK
uses the member's fixed effective transition without changing its base world.
Packets and cross-graph alias maps are evaluator custody, not actor messages.
"""

from collections.abc import Mapping
import re
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_graph as graph
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_worlds as worlds


STATUS = "PARTIAL_SOURCE_ONLY"
MEMO_SHA256 = "ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1"
CLARIFICATION_PATH = "research_notes/analysis/2026-09-13_stage2a_builder_source_clarifications_v1.md"
CLARIFICATION_SHA256 = "5484567fdad924247c5371a7430a071c925c563b5375336e8bef86dc6a4a99f9"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(wire.SCIENCE_GATES, False))
GO_WRITE_ROOT = False
GO_MATERIALIZE = False
GO_MODEL_TOKENIZER = False
GO_FIT_OR_GPU = False
GO_CLAIM = False
_KINDS = MappingProxyType({"node": "STATE", "event": "EVENT", "port": "PORT",
                           "query": "QUERY", "receipt": "RECEIPT"})
_CONSTRUCTION_DOMAINS = MappingProxyType({
    "BIRTH_WORLD_ONLY": ("birth_train",),
    "ORDINARY_WORLD_ONLY": ("birth_train", "dose_chain"),
    "HELD_INTERVENTION_WORLD": ("dose_intervention",),
    "HELD_CHAIN_WORLD": ("dose_chain",),
})


class _Inputs:
    def __init__(self, construction, role_tokens, current, task_goal, root_event):
        if type(construction) is not worlds.OrdinaryConstruction:
            raise ValueError("typed_complete_construction_required")
        if (type(construction.scope) is not str or construction.scope not in _CONSTRUCTION_DOMAINS
                or construction.status != STATUS or construction.memo_sha256 != MEMO_SHA256
                or construction.domain not in _CONSTRUCTION_DOMAINS[construction.scope]
                or type(construction.skin) is not int or construction.skin not in (0, 1)):
            raise ValueError("unsupported_construction_scope_or_provenance")
        if not isinstance(role_tokens, Mapping):
            raise ValueError("explicit_role_bindings_required")
        self.tokens = dict(role_tokens)
        if any(type(role) is not str for role in self.tokens):
            raise ValueError("invalid_role_key")
        if construction.domain == "birth_train":
            expected = set(birth.required_birth_roles(construction.world))
        else:
            inventory = wire.enumerate_symbolic_role_inventory(construction.domain)
            prefix = construction.domain + "/" + construction.world + "/"
            expected = {role for roles in inventory.roles_by_kind.values()
                        for role in roles if role.startswith(prefix)}
        if not expected or set(self.tokens) != expected:
            raise ValueError("incomplete_or_foreign_role_inventory")
        self.owners = {}
        for role, token in self.tokens.items():
            kind = role.rsplit("/", 1)[1]
            if (type(token) is not str or re.fullmatch(wire.IDENTIFIERS[kind], token) is None
                    or token.endswith("_AAAAAAAAAAAA") or token in self.owners):
                raise ValueError("invalid_or_duplicate_role_token")
            self.owners[token] = role
        self.current = current
        self.goal = task_goal
        self.ref(current, "STATE")
        self.ref(task_goal, "GOAL")
        self.ref(root_event, "EVENT")
        self.root_event = root_event
        self.construction = construction
        if not all(isinstance(value, Mapping) for value in (
                construction.blocks, construction.registry, construction.world_edges)):
            raise ValueError("construction_mappings_required")
        if set(construction.blocks) != set(construction.registry):
            raise ValueError("registry_block_keys_mismatch")
        self.blocks = {}
        self.events = {}
        required_world_keys = set()
        for request, raw in construction.registry.items():
            action = wire.parse_action(request)
            if action.operation != "READ":
                raise ValueError("nonread_registry_key")
            block = wire.parse_service(raw, skin=construction.skin)
            if construction.blocks[request] != block:
                raise ValueError("registry_block_bytes_mismatch")
            expected_kind = "ROUTES" if action.verb == "INDEX" else "EVENTS"
            if block.kind != expected_kind:
                raise ValueError("registry_request_kind_mismatch")
            self.ref(action.operand, "STATE" if action.verb == "INDEX" else "QUERY")
            self.blocks[request] = block
            for row in block.rows:
                self.ref(row.node, "STATE")
                self.ref(row.goal, "GOAL")
                if block.kind == "ROUTES":
                    self.ref(row.query, "QUERY")
                    if self.owners.get(row.route, "").rsplit("/", 1)[-1] != "route":
                        raise ValueError("unbound_route_evidence")
                else:
                    for value, vertex_type in ((row.event, "EVENT"), (row.port, "PORT"),
                                               (row.got, "STATE"), (row.recover, "QUERY"),
                                               (row.receipt, "RECEIPT")):
                        self.ref(value, vertex_type)
                    if row.event in self.events:
                        raise ValueError("ambiguous_event_owner")
                    owner = self.owners[row.event].rsplit("/", 1)[0]
                    if any(self.owners[token].rsplit("/", 1)[0] != owner
                           for token in (row.port, row.receipt)):
                        raise ValueError("event_field_role_owner_mismatch")
                    self.events[row.event] = row
                    required_world_keys.add((row.node, row.port))
        if root_event not in self.events:
            raise ValueError("root_event_not_registered")
        self.root_port = self.events[root_event].port
        for key, destination in construction.world_edges.items():
            if type(key) is not tuple or len(key) != 2:
                raise ValueError("invalid_world_edge_key")
            self.ref(key[0], "STATE")
            self.ref(key[1], "PORT")
            self.ref(destination, "STATE")
        if set(construction.world_edges) != required_world_keys:
            raise ValueError("missing_or_extra_effective_world_edges")
        self.vertices = {}
        for token, role in self.owners.items():
            kind = role.rsplit("/", 1)[1]
            if kind in _KINDS:
                self.add_vertex(token, _KINDS[kind], self.vertices)
        self.add_vertex(task_goal, "GOAL", self.vertices)
        for block in self.blocks.values():
            for row in block.rows:
                self.add_vertex(row.goal, "GOAL", self.vertices)

    def ref(self, token, vertex_type):
        if type(token) is not str or token not in self.owners:
            raise ValueError("unbound_graph_identifier")
        role = self.owners[token]
        graph.local_owner_key(role, vertex_type)
        return (role, vertex_type)

    def add_vertex(self, token, vertex_type, vertices):
        reference = self.ref(token, vertex_type)
        flags = []
        if vertex_type == "STATE" and token == self.current:
            flags.append("CURRENT")
        if vertex_type == "GOAL" and token == self.goal:
            flags.append("GOAL")
        if vertex_type == "EVENT" and token == self.root_event:
            flags.append("ROOT_EVENT")
        if vertex_type == "PORT" and token == self.root_port:
            flags.append("ROOT_PORT")
        vertices[reference] = graph.RoleVertex(*reference, tuple(sorted(flags)))
        return reference

    def add_edge(self, label, tails, heads, vertices, edges):
        references = []
        for incidence, types in zip((tails, heads), graph.INCIDENCE[label]):
            references.append(tuple(self.add_vertex(token, vertex_type, vertices)
                                    for token, vertex_type in zip(incidence, types)))
        edges.add(graph.RoleEdge(label, references[0], references[1]))

    def add_block(self, request, block, vertices, edges):
        action = wire.parse_action(request)
        self.add_vertex(action.operand, "STATE" if action.verb == "INDEX" else "QUERY", vertices)
        for row in block.rows:
            if block.kind == "ROUTES":
                self.add_edge("INDEXES", (row.node, row.goal), (row.query,), vertices, edges)
            else:
                self.add_edge("CONTAINS", (action.operand,), (row.event,), vertices, edges)
                for label, value in (("FOR", row.goal), ("AT", row.node), ("DID", row.port),
                                     ("GOT", row.got), ("RECOVER", row.recover),
                                     ("EVIDENCE", row.receipt)):
                    self.add_edge(label, (row.event,), (value,), vertices, edges)

    def serialize(self, vertices, edges):
        return graph.canonical_graph(list(vertices.values()), list(edges))


def build_world_graph(construction, *, role_tokens, current, task_goal, root_event):
    """Full effective world, including allocated isolated non-route vertices.

    current is an explicit task-boundary assertion for this low-level API.
    ROOT_PORT is derived from the unique registered row for root_event.
    """
    inputs = _Inputs(construction, role_tokens, current, task_goal, root_event)
    return _world_graph(inputs, construction.world_edges)


def _world_graph(inputs, world_edges):
    vertices = dict(inputs.vertices)
    edges = set()
    for request, block in inputs.blocks.items():
        inputs.add_block(request, block, vertices, edges)
    for (state, port), destination in world_edges.items():
        inputs.add_edge("WORLD", (state, port), (destination,), vertices, edges)
    return inputs.serialize(vertices, edges)


def _retained_indices(case, target, arm):
    boundary = target.trace_index
    if arm == "CLOSED":
        return tuple(range(boundary))
    if arm != "ATOM_LOCAL":
        raise ValueError("unsupported_public_arm")
    if target.phase == "CONTINUE":
        return ()
    if target.phase in ("READ_CHECK", "PROSPECT"):
        return (boundary - 1,)
    if target.phase == "STEP_CHECK":
        return (boundary - 2, boundary - 1)
    if target.phase == "SEEK":
        return ((boundary - 3, boundary - 2, boundary - 1)
                if case.descriptor.recovery_subtype == "STEP_OUTCOME_MISMATCH" else (0,))
    raise ValueError("unsupported_target_phase")


def _birth_boundary(case, role_tokens, target_ordinal):
    birth.validate_birth_case(case, role_tokens=role_tokens)
    if (type(target_ordinal) is not int or not 0 <= target_ordinal < len(case.targets)
            or case.targets[target_ordinal].ordinal != target_ordinal):
        raise ValueError("invalid_target_ordinal")
    target = case.targets[target_ordinal]
    if type(target.trace_index) is not int or not 0 <= target.trace_index < len(case.trace):
        raise ValueError("invalid_target_boundary")
    return target


def _public_inputs(case, *, role_tokens, target_ordinal, root_event, arm):
    target = _birth_boundary(case, role_tokens, target_ordinal)
    inputs = _Inputs(case.construction, role_tokens, target.current_before, case.task.goal, root_event)
    first_step = next((turn for turn in case.trace if wire.parse_action(turn.action).operation == "STEP"), None)
    root_row = inputs.events[root_event]
    if (first_step is None or root_row.port != wire.parse_action(first_step.action).operand
            or root_row.node != first_step.current_before or root_row.goal != case.task.goal):
        raise ValueError("explicit_root_does_not_match_first_irreversible_step")
    indices = _retained_indices(case, target, arm)
    if any(index < 0 or index >= target.trace_index for index in indices):
        raise ValueError("invalid_retained_trace_boundary")
    current = case.task.current if arm == "CLOSED" else (
        case.trace[indices[0]].current_before if indices else target.current_before)
    vertices, edges = {}, set()
    inputs.add_vertex(case.task.start, "STATE", vertices)
    inputs.add_vertex(case.task.goal, "GOAL", vertices)
    inputs.add_vertex(current, "STATE", vertices)
    for index in indices:
        turn = case.trace[index]
        if turn.current_before != current:
            raise ValueError("retained_current_before_mismatch")
        action = wire.parse_action(turn.action)
        if action.operation == "READ":
            expected = "SERVICE\n" + case.construction.read(turn.action)
            if turn.response != expected or turn.current_after != current:
                raise ValueError("inauthentic_read_response")
            block = wire.parse_service(turn.response[len("SERVICE\n"):], skin=case.construction.skin)
            inputs.add_block(turn.action, block, vertices, edges)
        elif action.operation == "STEP":
            observed = wire.parse_world(turn.response)
            if (case.construction.transition(current, action.operand) != observed
                    or turn.current_after != observed):
                raise ValueError("inauthentic_world_outcome")
            inputs.add_edge("WORLD", (current, action.operand), (observed,), vertices, edges)
            current = observed
        elif action.operation == "THINK":
            if turn.response != "ACK" or turn.current_after != current:
                raise ValueError("inauthentic_think_response")
            vertex_type = "EVENT" if action.operand.startswith("M2AE_") else "QUERY"
            inputs.add_vertex(action.operand, vertex_type, vertices)
        else:
            raise ValueError("terminal_action_inside_prefix")
    if current != target.current_before:
        raise ValueError("target_public_current_mismatch")
    return inputs, vertices, edges


def build_public_graph(case, *, role_tokens, target_ordinal, root_event, arm="CLOSED"):
    """Public task/returned-row/executed-WORLD facts before one BirthTarget.

    CLOSED retains the entire authentic prefix. ATOM_LOCAL follows the bound
    retention table and clarification's first-retained-action CURRENT rule.
    Neither target bytes nor future turns contribute vertices or edges.
    Aliases are dense within this visible graph, not inherited from the world.
    """
    inputs, vertices, edges = _public_inputs(
        case, role_tokens=role_tokens, target_ordinal=target_ordinal, root_event=root_event, arm=arm,
    )
    return inputs.serialize(vertices, edges)


def public_to_world_aliases(case, *, role_tokens, target_ordinal, root_event, arm="CLOSED"):
    """Evaluator-custody public-alias -> world-alias map for the same boundary.

    Every visible typed owner appears exactly once. No private owner keys or
    public tokens are returned. This map is not actor-prefix content and must
    not be inserted into the graph/core JSON hashed by the v3/v4 contract.
    The map establishes supplied-owner correspondence, not scientific validity.
    """
    inputs, vertices, edges = _public_inputs(
        case, role_tokens=role_tokens, target_ordinal=target_ordinal, root_event=root_event, arm=arm,
    )
    return _alias_mapping(inputs, vertices)


def _alias_mapping(inputs, vertices):
    public_aliases = graph.typed_aliases(list(vertices.values()))
    world_aliases = graph.typed_aliases(list(inputs.vertices.values()))
    return dict(sorted((public_aliases[reference], world_aliases[reference]) for reference in vertices))


def _held_task(inputs, task):
    if type(task) is not wire.TaskState:
        raise ValueError("typed_held_task_required")
    start_role = f"{inputs.construction.domain}/{inputs.construction.world}/s/-/state/-/node"
    if task.start != inputs.tokens[start_role] or task.current != task.start:
        raise ValueError("held_initial_task_state_mismatch")
    raw = f"TASK\nSTART {task.start}\nGOAL {task.goal}\nCURRENT {task.current}"
    if wire.parse_task(raw) != task:
        raise ValueError("invalid_held_task")
    inputs.ref(task.start, "STATE")
    inputs.ref(task.goal, "GOAL")
    return raw


def _observed_held_prefix(inputs, task, observed_prefix, world_edges):
    task_text = _held_task(inputs, task)
    if (type(observed_prefix) not in (tuple, list) or len(observed_prefix) < 2
            or len(observed_prefix) % 2 or len(observed_prefix) > 2 + 2 * wire.CALL_CAP):
        raise ValueError("bounded_complete_message_prefix_required")
    if any(type(message) is not held.Message or type(message.role) is not str
           or type(message.content) is not str for message in observed_prefix):
        raise ValueError("typed_held_messages_required")
    if (observed_prefix[0] != held.Message("system", wire.SYSTEM_MESSAGE)
            or observed_prefix[1] != held.Message("user", task_text)):
        raise ValueError("observed_initial_task_mismatch")
    current = task.current
    vertices, edges = {}, set()
    inputs.add_vertex(task.start, "STATE", vertices)
    inputs.add_vertex(task.goal, "GOAL", vertices)
    inputs.add_vertex(current, "STATE", vertices)
    for offset in range(2, len(observed_prefix), 2):
        actor, host = observed_prefix[offset:offset + 2]
        if (actor.role, host.role) != ("assistant", "user"):
            raise ValueError("invalid_observed_role_sequence")
        action = wire.parse_action(actor.content)
        if action.operation == "READ":
            response = inputs.construction.read(actor.content)
            if host.content != "SERVICE\n" + response:
                raise ValueError("forged_observed_service_response")
            block = wire.parse_service(response, skin=inputs.construction.skin)
            inputs.add_block(actor.content, block, vertices, edges)
        elif action.operation == "STEP":
            inputs.ref(action.operand, "PORT")
            destination = wire.parse_world(host.content)
            key = (current, action.operand)
            if key not in world_edges or destination != world_edges[key]:
                raise ValueError("forged_observed_world_response")
            inputs.add_edge("WORLD", key, (destination,), vertices, edges)
            current = destination
        elif action.operation == "THINK":
            if host.content != "ACK":
                raise ValueError("forged_observed_ack_response")
            vertex_type = "EVENT" if action.operand.startswith("M2AE_") else "QUERY"
            inputs.add_vertex(action.operand, vertex_type, vertices)
        else:
            raise ValueError("terminal_action_inside_observed_prefix")
    if current != inputs.current:
        raise ValueError("observed_world_current_snapshot_mismatch")
    return vertices, edges


def _held_packet(inputs, task, observed_prefix, world_edges):
    vertices, edges = _observed_held_prefix(inputs, task, observed_prefix, world_edges)
    return {
        "status": STATUS,
        "world_graph": _world_graph(inputs, world_edges),
        "public_graph": inputs.serialize(vertices, edges),
        "public_to_world_aliases": _alias_mapping(inputs, vertices),
        "science_gates": dict(SCIENCE_GATES),
    }


def build_intervention_graph_packet(member, *, role_tokens, observed_prefix, root_event, world_current):
    """Evaluator-only packet for one of 64 held intervention members.

    observed_prefix must contain the original system/task and complete observed
    actor/host pairs before a decision. Replay checks facts, not actor optimality.
    No expected_target, expected_causal_prefix, or semantic_object is read.
    CHECK substitutes only its designated effective WORLD head in a private
    graph snapshot; construction.world_edges and observed_prefix stay unchanged.
    Root designation remains an explicit evaluator assertion, not a witness read.
    """
    if type(member) is not held.InterventionMember or member.status != STATUS:
        raise ValueError("partial_intervention_member_required")
    if (type(member.transition_name) is not str or member.transition_name not in held.TRANSITIONS
            or type(member.pair_index) is not int or not 0 <= member.pair_index < 8
            or type(member.member) is not str or member.member not in ("m0", "m1")
            or type(member.task) is not wire.TaskState
            or type(member.construction) is not worlds.OrdinaryConstruction):
        raise ValueError("invalid_intervention_member_metadata")
    construction = member.construction
    if (construction.scope != "HELD_INTERVENTION_WORLD"
            or construction.world != f"{member.transition_name}_k{member.pair_index}"
            or construction.skin != member.pair_index // 4):
        raise ValueError("intervention_construction_mismatch")
    inputs = _Inputs(construction, role_tokens, world_current, member.task.goal, root_event)
    world_edges = dict(construction.world_edges)
    if type(member.intervention) is not held.OutcomeIntervention:
        raise ValueError("typed_outcome_intervention_required")
    if member.transition_name == "check":
        selected = member.selected_event
        if (type(selected) is not wire.EventRow or inputs.events.get(selected.event) != selected
                or selected.node != member.task.start or selected.goal != member.task.goal
                or member.intervention.kind != "OUTCOME_DESTINATION"):
            raise ValueError("unbound_check_transition")
        destination = member.intervention.outcome_destination
        inputs.ref(destination, "STATE")
        key = (selected.node, selected.port)
        if key not in world_edges:
            raise ValueError("check_transition_has_no_base_edge")
        world_edges[key] = destination
    elif member.intervention.kind != "IDENTITY" or member.intervention.outcome_destination is not None:
        raise ValueError("outcome_override_outside_check")
    return _held_packet(inputs, member.task, observed_prefix, world_edges)


def build_chain_graph_packet(chain_world, *, member_id, role_tokens, observed_prefix, root_event, world_current):
    """Evaluator-only packet for one of 32 chain tasks over its effective world.

    Replays supplied observations; never reads expected_trace, sufficient_reads,
    or a witness-derived action list. Legal off-witness observations are allowed.
    Only full prefixes from the original task are supported, not trimmed ATOM
    prefixes or prefixes after terminal STOP. No model/runtime guard is claimed.
    """
    if (type(chain_world) is not held.ChainWorld or chain_world.status != STATUS
            or chain_world.memo_sha256 != MEMO_SHA256
            or chain_world.clarification_sha256 != CLARIFICATION_SHA256
            or type(chain_world.construction) is not worlds.OrdinaryConstruction):
        raise ValueError("partial_chain_world_required")
    construction = chain_world.construction
    if (construction.scope != "HELD_CHAIN_WORLD" or type(chain_world.skin) is not int
            or chain_world.skin != construction.skin):
        raise ValueError("chain_construction_mismatch")
    if type(member_id) is not str or member_id not in ("m0", "m1"):
        raise ValueError("invalid_chain_member_id")
    if (type(chain_world.members) is not tuple or len(chain_world.members) != 2
            or any(type(member) is not held.ChainMember or member.status != STATUS
                   or type(member.member) is not str or type(member.task) is not wire.TaskState
                   for member in chain_world.members)
            or {member.member for member in chain_world.members} != {"m0", "m1"}):
        raise ValueError("ambiguous_chain_members")
    member = next(member for member in chain_world.members if member.member == member_id)
    inputs = _Inputs(construction, role_tokens, world_current, member.task.goal, root_event)
    return _held_packet(inputs, member.task, observed_prefix, construction.world_edges)
