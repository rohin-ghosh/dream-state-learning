"""Finite, evaluator-only route basis from the complete selected birth world.

All registered EVENT rows are retained, including off-oracle branches. Physical
successors use effective WORLD destinations, not predicted GOT. A registered
RECOVER continuation additionally records its owning mismatching STEP. Missing
RECOVER registrations stay unavailable. Cycles require no path-length cutoff:
this module indexes transitions and checks supplied adjacent pairs only.

This is not a byte-language leak detector. In particular, rendering two edges
as one literal needle does not cover interleaved actions/services or authorize
historical occurrences. A future route matcher must preserve occurrence-level
prefix provenance and the independent target/future/semantic checks. No complete
ScanInventory, corpus, model, GPU, source certification or science gate opens.
"""

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_source_inputs as source_inputs


STATUS = "PARTIAL_SOURCE_ONLY"
SCHEMA_VERSION = "BIRTH_EFFECTIVE_ROUTE_BASIS_V1"
SCIENCE_GATES = MappingProxyType(dict(source_inputs.SCIENCE_GATES))


class RouteInputError(ValueError):
    """A registered route component lacks consistent typed source ownership."""


@dataclass(frozen=True)
class RouteTransition:
    query: str
    event: str
    current: str
    goal: str
    port: str
    predicted: str
    actual: str
    recover: str
    receipt: str
    source_path: tuple[str, ...]
    recovery_owner_port: str | None

    @property
    def mismatches(self):
        return self.actual != self.predicted


@dataclass(frozen=True)
class BirthRouteInputs:
    source: source_inputs.ValidatedBirthSource
    transitions: Mapping[str, RouteTransition]
    ports_by_current: Mapping[str, tuple[str, ...]]
    ports_by_query: Mapping[str, tuple[str, ...]]
    unavailable_recover_queries: frozenset[str]

    status = STATUS
    schema_version = SCHEMA_VERSION
    science_gates = SCIENCE_GATES
    inventory_completeness_verified = False
    rendering_coverage_verified = False

    def successors(self, port):
        """Return every static physically/contingently compatible next edge.

        The mismatch guard is hypothetical source truth, not evidence that the
        actor observed a contradiction. A matcher must authenticate occurrence
        visibility independently; this method grants no public-field exemption.
        """
        if type(port) is not str or port not in self.transitions:
            raise RouteInputError("unregistered_route_port")
        previous = self.transitions[port]
        return tuple(candidate for candidate in self.ports_by_current.get(previous.actual, ())
                     if self.transitions[candidate].recovery_owner_port is None
                     or (self.transitions[candidate].recovery_owner_port == port
                         and previous.mismatches))

    def contains_pair(self, first_port, second_port):
        if type(second_port) is not str or second_port not in self.transitions:
            raise RouteInputError("unregistered_route_port")
        return second_port in self.successors(first_port)


def derive_birth_route_inputs(*, case, record, role_tokens, display_master):
    """Reconstruct source before indexing every registered transition once."""
    source = source_inputs.validate_birth_source(
        case=case, record=record, role_tokens=role_tokens, display_master=display_master,
    )
    construction = source.case.construction
    rows_by_port = {}
    recovery_owners = {}
    relation_queries = set()
    for request, block in sorted(construction.blocks.items()):
        if block.kind != "EVENTS":
            continue
        action = wire.parse_action(request)
        if (action.operation, action.verb) != ("READ", "RELATION"):
            raise RouteInputError("event_block_without_relation_query")
        relation_queries.add(action.operand)
        for position, row in enumerate(block.rows):
            if row.port in rows_by_port:
                raise RouteInputError("duplicate_route_port")
            if row.recover in recovery_owners:
                raise RouteInputError("ambiguous_recovery_owner")
            rows_by_port[row.port] = (action.operand, row, request, position)
            recovery_owners[row.recover] = row.port
    if set(construction.world_edges) != {(row.node, row.port)
                                        for query, row, request, position in rows_by_port.values()}:
        raise RouteInputError("incomplete_effective_transition_coverage")
    transitions, by_current, by_query = {}, defaultdict(list), defaultdict(list)
    for port, (query, row, request, position) in sorted(rows_by_port.items()):
        transition = RouteTransition(
            query, row.event, row.node, row.goal, port, row.got,
            construction.world_edges[row.node, port], row.recover, row.receipt,
            ("case", "construction", "blocks", request, "rows", str(position)),
            recovery_owners.get(query),
        )
        transitions[port] = transition
        by_current[row.node].append(port)
        by_query[query].append(port)
    return BirthRouteInputs(
        source, MappingProxyType(transitions),
        MappingProxyType({current: tuple(ports) for current, ports in sorted(by_current.items())}),
        MappingProxyType({query: tuple(ports) for query, ports in sorted(by_query.items())}),
        frozenset(recovery_owners) - relation_queries,
    )
