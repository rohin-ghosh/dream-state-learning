"""Bounded, evaluator-only birth cores from exact source arm records.

One producer snapshots one supplied case and its bindings, validates the source
trace/renderer, and reuses full-world graphs across its eight decisions. Private
completion never changes a target, prefix, or public graph. Graph assembly uses
the existing graph-input primitives; every returned envelope passes the existing
independent JSON checker. No global case cache or external I/O is used.

This is supplied-source consistency, not constructor reconstruction or source
authentication: no display master is supplied. Neither the partial checker nor
this bridge certifies inventories, route coverage, native bytes, or readiness.
All returned bytes, including world graphs and receipts, are evaluator custody.
"""

from collections.abc import Mapping
from copy import copy
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_birth as birth
from organism_v6 import composition_birth_stage2a_checker as checker
from organism_v6 import composition_birth_stage2a_graph as graph
from organism_v6 import composition_birth_stage2a_graph_inputs as graph_inputs
from organism_v6 import composition_birth_stage2a_source_inputs as source_inputs
from organism_v6 import composition_birth_stage2a_targets as targets
from organism_v6 import composition_birth_stage2a_worlds as worlds
from organism_v6.composition_birth_stage2a_primitives import canonical_json


STATUS = "PARTIAL_SOURCE_ONLY"
BINDING_PATH = "research_notes/analysis/2026-09-14_stage2a_builder_core_bindings_v1.md"
BINDING_SHA256 = "04b214f3ade98bc9f1464a869791def711beaf3b143af4ca51d70f43e82250ff"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(wire.SCIENCE_GATES, False))
GO_WRITE_ROOT = False
GO_MATERIALIZE = False
GO_MODEL_TOKENIZER = False
GO_FIT_OR_GPU = False
GO_CLAIM = False
BOUNDS = MappingProxyType({"role_entries": 32768, "services": 1024,
                          "service_bytes": 16384, "trace_turns": wire.CALL_CAP,
                          "message_bytes": 32768, "world_edges": 4096})


class CoreInputError(ValueError):
    """The supplied birth source or exact arm boundary cannot produce a core."""


@dataclass(frozen=True)
class BirthCoreInputs:
    unit_id: str
    arm: str
    core_bytes: bytes
    checker_payload: bytes
    receipt_bytes: bytes
    semantic_route_depth: int

    status = STATUS
    binding_sha256 = BINDING_SHA256
    science_gates = SCIENCE_GATES

    @property
    def core(self):
        return json.loads(self.core_bytes)

    @property
    def receipt(self):
        return json.loads(self.receipt_bytes)


def _ascii(value, limit):
    return type(value) is str and len(value) <= limit and value.isascii()


def _snapshot(case, role_tokens):
    if (type(case) is not birth.BirthCase
            or type(case.descriptor) is not birth.BirthCaseDescriptor
            or type(case.task) is not wire.TaskState
            or type(case.facts) is not birth.BirthTraceFacts
            or type(case.construction) is not worlds.OrdinaryConstruction):
        raise CoreInputError("typed_birth_source_required")
    descriptor = birth.describe_birth_case(case.descriptor.world, case.descriptor.member)
    if not source_inputs._same_source(case.descriptor, descriptor):
        raise CoreInputError("exact_birth_descriptor_required")
    if (not isinstance(role_tokens, Mapping) or len(role_tokens) > BOUNDS["role_entries"]
            or any(not _ascii(role, 256) or not _ascii(token, 17) or len(token) != 17
                   for role, token in role_tokens.items())):
        raise CoreInputError("bounded_role_bindings_required")
    tokens = MappingProxyType(dict(role_tokens))
    if not _ascii(case.task_text, BOUNDS["message_bytes"]):
        raise CoreInputError("bounded_task_required")
    if (type(case.trace) is not tuple or not 0 < len(case.trace) <= BOUNDS["trace_turns"]
            or any(type(turn) is not birth.BirthTraceTurn
                   or not _ascii(turn.action, BOUNDS["message_bytes"])
                   or not _ascii(turn.response, BOUNDS["message_bytes"])
                   or (turn.target_ordinal is not None and type(turn.target_ordinal) is not int)
                   for turn in case.trace)
            or type(case.targets) is not tuple or len(case.targets) != 4
            or any(type(target) is not birth.BirthTarget
                   or type(target.ordinal) is not int or type(target.trace_index) is not int
                   or type(target.target_bytes) is not bytes
                   or (target.selection_index is not None and type(target.selection_index) is not int)
                   for target in case.targets)):
        raise CoreInputError("bounded_typed_trace_and_four_targets_required")
    construction = case.construction
    for mapping, limit in ((construction.registry, BOUNDS["services"]),
                           (construction.blocks, BOUNDS["services"]),
                           (construction.world_edges, BOUNDS["world_edges"])):
        if not isinstance(mapping, Mapping) or len(mapping) > limit:
            raise CoreInputError("bounded_construction_mappings_required")
    registry = dict(construction.registry)
    blocks = {}
    if set(registry) != set(construction.blocks):
        raise CoreInputError("registry_block_keys_mismatch")
    for request, raw in registry.items():
        if not _ascii(request, 256) or not _ascii(raw, BOUNDS["service_bytes"]):
            raise CoreInputError("bounded_service_required")
        parsed = wire.parse_service(raw, skin=construction.skin)
        if not source_inputs._same_source(construction.blocks[request], parsed):
            raise CoreInputError("exact_registry_block_required")
        blocks[request] = parsed
    snapshot = replace(case, construction=replace(
        construction, registry=MappingProxyType(registry), blocks=MappingProxyType(blocks),
        world_edges=MappingProxyType(dict(construction.world_edges))))
    return snapshot, tokens


def _unique(rows, current, goal):
    matches = [(position, row) for position, row in enumerate(rows)
               if row.node == current and row.goal == goal]
    if len(matches) != 1:
        raise CoreInputError("missing_or_ambiguous_route_match")
    return matches[0]


def _observe(prefix, inputs):
    task = targets.latest_public_task(prefix)
    initial = wire.parse_task(prefix[1].content)
    current = initial.current
    vertices, edges, retained_events = {}, set(), {}
    visited = {current}
    steps = 0
    mismatches = 0
    latest_step = None
    for token, kind in ((initial.start, "STATE"), (initial.goal, "GOAL"), (current, "STATE")):
        inputs.add_vertex(token, kind, vertices)
    for action_message, response_message in zip(prefix[2::2], prefix[3::2]):
        action = wire.parse_action(action_message.content)
        response = response_message.content
        if action.operation == "READ":
            request = action_message.content
            if response != "SERVICE\n" + inputs.construction.read(request):
                raise CoreInputError("inauthentic_service")
            block = inputs.blocks.get(request)
            if block is None:
                block = wire.parse_service(response[len("SERVICE\n"):], skin=inputs.construction.skin)
            inputs.add_block(request, block, vertices, edges)
            if block.kind == "EVENTS":
                for position, row in enumerate(block.rows):
                    retained_events[row.event] = (position, row)
        elif action.operation == "STEP":
            owners = [(position, row) for position, row in retained_events.values()
                      if row.node == current and row.port == action.operand and row.goal == initial.goal]
            if len(owners) != 1:
                raise CoreInputError("retained_step_missing_or_ambiguous_event_owner")
            position, event = owners[0]
            observed = wire.parse_world(response)
            if inputs.construction.world_edges.get((current, action.operand)) != observed:
                raise CoreInputError("missing_or_altered_effective_transition")
            if observed in visited:
                raise CoreInputError("effective_path_cycle")
            inputs.add_edge("WORLD", (current, action.operand), (observed,), vertices, edges)
            latest_step = (position, event, observed)
            mismatches += event.got != observed
            steps += 1
            current = observed
            visited.add(current)
        elif action.operation == "THINK":
            if response != "ACK":
                raise CoreInputError("inauthentic_think_response")
            inputs.add_vertex(action.operand, "EVENT" if action.operand.startswith("M2AE_") else "QUERY", vertices)
        else:
            raise CoreInputError("terminal_action_inside_prefix")
    if task.current != current:
        raise CoreInputError("public_current_mismatch")
    return vertices, edges, latest_step, current, steps, mismatches, visited


def _complete_depth(case, inputs):
    prefix = (targets.Message("system", wire.SYSTEM_MESSAGE), targets.Message("user", case.task_text))
    prefix += tuple(message for turn in case.trace if turn.action != "STOP"
                    for message in (targets.Message("assistant", turn.action), targets.Message("user", turn.response)))
    _, _, _, current, steps, mismatches, visited = _observe(prefix, inputs)
    while current != case.task.goal:
        directory = inputs.blocks.get("READ INDEX " + current)
        if directory is None or directory.kind != "ROUTES":
            raise CoreInputError("private_completion_missing_directory")
        _, route = _unique(directory.rows, current, case.task.goal)
        relation = inputs.blocks.get("READ RELATION " + route.query)
        if relation is None or relation.kind != "EVENTS":
            raise CoreInputError("private_completion_missing_relation")
        _, event = _unique(relation.rows, current, case.task.goal)
        observed = inputs.construction.world_edges.get((current, event.port))
        if observed is None:
            raise CoreInputError("private_completion_missing_transition")
        if observed in visited:
            raise CoreInputError("effective_path_cycle")
        if observed != event.got:
            raise CoreInputError("private_completion_altered_transition")
        current = observed
        visited.add(current)
        steps += 1
    return steps, steps - mismatches


class BirthCoreInputProducer:
    """Snapshot and validate once; build any of this case's eight exact records.

    Local graph reuse is scoped to this producer's private immutable source
    snapshot. Create a new producer to validate changed external source inputs.
    """

    def __init__(self, *, case, role_tokens):
        try:
            self._case, self._tokens = _snapshot(case, role_tokens)
            pairs = targets.serialize_birth_case(self._case, role_tokens=self._tokens)
            trace, expected_targets, facts = birth._oracle(
                self._case.descriptor, self._case.task, self._case.construction, self._tokens)
            normalized = replace(self._case, task=wire.parse_task(self._case.task_text), trace=trace,
                                 targets=expected_targets, facts=facts, status=birth.STATUS,
                                 memo_sha256=birth.MEMO_SHA256, clarification_sha256=birth.CLARIFICATION_SHA256)
            if not source_inputs._same_source(self._case, normalized):
                raise CoreInputError("exact_birth_source_required")
            self._records = tuple(record for pair in pairs for record in (pair.closed, pair.atom_local))
            first_step = next(index for index, turn in enumerate(self._case.trace)
                              if wire.parse_action(turn.action).operation == "STEP")
            turn = self._case.trace[first_step]
            preceding = self._case.trace[first_step - 1]
            block = self._case.construction.blocks.get(preceding.action)
            if first_step == 0 or block is None or block.kind != "EVENTS":
                raise CoreInputError("first_step_requires_owning_events")
            _, event = _unique(block.rows, turn.current_before, self._case.task.goal)
            if event.port != wire.parse_action(turn.action).operand:
                raise CoreInputError("first_step_event_port_mismatch")
            self._inputs = graph_inputs._Inputs(self._case.construction, self._tokens,
                                               self._case.task.current, self._case.task.goal, event.event)
            self.actual_route_depth, self.semantic_route_depth = _complete_depth(self._case, self._inputs)
            self._world_aliases = graph.typed_aliases(list(self._inputs.vertices.values()))
            self._worlds = {}
        except (ValueError, TypeError, KeyError, AttributeError, StopIteration) as error:
            raise CoreInputError("birth_core_source_validation_failed: " + str(error)) from error

    def _boundary_world(self, current):
        if current not in self._worlds:
            inputs = copy(self._inputs)
            inputs.current = current
            inputs.vertices = {reference: replace(vertex, flags=tuple(flag for flag in vertex.flags if flag != "CURRENT"))
                               for reference, vertex in self._inputs.vertices.items()}
            inputs.add_vertex(current, "STATE", inputs.vertices)
            world = graph_inputs._world_graph(inputs, inputs.construction.world_edges)
            radii = {f"r{radius}": graph.radius_graph(world, radius) for radius in range(4)}
            radius_hashes = {name: sha256(b"M2A-RADIUS-V3\0" + name[1:].encode("ascii") + b"\0"
                                         + graph.graph_bytes(value)).hexdigest() for name, value in radii.items()}
            hashes = {"world_graph": graph.graph_hash(world), "radii": radius_hashes,
                      "signature": sha256(b"M2A-SIGNATURE-V3\0" + canonical_json(radius_hashes)).hexdigest()}
            self._worlds[current] = inputs, world, radii, hashes
        return self._worlds[current]

    def build(self, record):
        """Return private core/envelope/receipt bytes for an exact ArmRecord."""
        try:
            if type(record) is not targets.ArmRecord:
                raise CoreInputError("typed_arm_record_required")
            selected = next((candidate for candidate in self._records
                             if source_inputs._same_source(record, candidate)), None)
            if selected is None:
                raise CoreInputError("exact_constructor_record_mismatch")
            current = targets.latest_public_task(selected.prefix).current
            inputs, world, radii, world_hashes = self._boundary_world(current)
            vertices, edges, latest_step, _, _, _, _ = _observe(selected.prefix, inputs)
            observed = latest_step is not None
            match = latest_step[1].got == latest_step[2] if observed else None
            position = selected.unit.selection_index
            descriptor = self._case.descriptor
            if selected.unit.phase == "SEEK" and descriptor.recovery_subtype == "STEP_OUTCOME_MISMATCH":
                if latest_step is None or match or latest_step[1].recover != selected.unit.operand:
                    raise CoreInputError("recovery_seek_event_ownership_mismatch")
                position = latest_step[0]
            public = inputs.serialize(vertices, edges)
            aliases = graph.typed_aliases(list(vertices.values()))
            alias_map = dict(sorted((aliases[reference], self._world_aliases[reference]) for reference in vertices))
            core = graph.decision_core(
                public, actual_route_depth=self.actual_route_depth, family_motif=descriptor.family_motif,
                flow=descriptor.flow, goal_side=descriptor.goal_side, phase=selected.unit.phase,
                predicted_actual_match=match, recovery_subtype=descriptor.recovery_subtype,
                relevant_candidate_display_position=position, skin=descriptor.skin,
                terminal_class=descriptor.terminal_class, step_outcome_observed=observed)
            hashes = dict(world_hashes, public_graph=graph.graph_hash(public),
                          core=graph.core_hash(core, step_outcome_observed=observed))
            envelope = {"schema_version": checker.SCHEMA_VERSION, "world_graph": world, "core": core,
                        "public_to_world_aliases": alias_map, "step_outcome_observed": observed,
                        "radius_graphs": radii, "expected_hashes": hashes}
            payload = checker.canonical_json_bytes(envelope)
            receipt = checker.check_graph_core_json(payload)
            return BirthCoreInputs(selected.unit.unit_id, selected.arm, graph.core_bytes(core, step_outcome_observed=observed),
                                   payload, canonical_json(receipt), self.semantic_route_depth)
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            raise CoreInputError("birth_core_record_validation_failed: " + str(error)) from error


def build_birth_core_inputs(*, case, record, role_tokens):
    """One-shot source validation; reuse BirthCoreInputProducer for all decisions."""
    return BirthCoreInputProducer(case=case, role_tokens=role_tokens).build(record)
