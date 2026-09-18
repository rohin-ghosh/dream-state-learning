"""Bounded independent CPU checks: non-material v6 qualification repair.

The caller supplies an independently authenticated, immutable source. These
oracles do not authenticate allocation or authorize a launch. Only wire parsers,
primitive serialization and passive field schemas are shared with production;
no binder, future/route producer or scanner private basis supplies expectations.
"""

from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import fields, is_dataclass, replace
from hashlib import sha256
import re

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_scan_inputs as schemas
from organism_v6 import composition_birth_stage2a_scanner as scanner
from organism_v6 import composition_birth_stage2a_source_inputs as sources
from organism_v6 import composition_birth_stage2a_targets as targets


def _require(condition, message):
    if not condition:
        raise ValueError("cpu_oracle: " + message)


def _canonical_value(value):
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is bytes:
        return {"bytes_hex": value.hex()}
    if isinstance(value, Mapping):
        if all(type(key) is str for key in value):
            return {key: _canonical_value(item) for key, item in value.items()}
        return {"entries": [[_canonical_value(key), _canonical_value(value[key])]
                            for key in sorted(value)]}
    if type(value) in (set, frozenset):
        return [_canonical_value(item) for item in sorted(value)]
    if type(value) in (tuple, list):
        return [_canonical_value(item) for item in value]
    if is_dataclass(value):
        return {field.name: _canonical_value(getattr(value, field.name)) for field in fields(value)}
    raise ValueError("cpu_oracle: unsupported canonical value")


def _encoded(value):
    return primitives.canonical_json(_canonical_value(value))


def _bounded_source(source):
    _require(type(source) is sources.ValidatedBirthSource, "validated source required")
    _require(len(source.role_tokens) <= sources.BOUNDS["role_entries"], "role bound")
    _require(len(source.case.trace) <= 128 and len(source.case.targets) == 4, "trace/target bound")
    _require(len(source.case.construction.blocks) <= sources.BOUNDS["role_entries"], "block bound")
    _require(sum(len(block.rows) for block in source.case.construction.blocks.values())
             <= 4 * sources.BOUNDS["role_entries"], "row bound")


def _public_source(source):
    case, record = source.case, source.record
    case_key = f"{case.descriptor.world}/{case.descriptor.member}"
    matching = [target for target in case.targets
                if record.unit.unit_id == f"{case_key}/u{target.ordinal}"]
    _require(len(matching) == 1, "target ownership")
    target = matching[0]
    expected_unit = targets.TargetUnit(
        f"{case_key}/u{target.ordinal}", target.phase, target.target_bytes,
        target.target_sha256, target.command, target.operand, target.selection_index,
    )
    _require(record.unit == expected_unit, "target source mismatch")
    stop = target.trace_index
    _require(0 <= stop < len(case.trace), "target trace index")
    if record.arm == "CLOSED":
        retained = tuple(range(stop))
        task_text = case.task_text
    else:
        _require(record.arm == "ATOM_LOCAL", "unknown arm")
        if target.phase == "CONTINUE":
            retained = ()
        elif target.phase in ("READ_CHECK", "PROSPECT"):
            retained = (stop - 1,)
        elif target.phase == "STEP_CHECK":
            retained = (stop - 2, stop - 1)
        elif target.phase == "SEEK":
            retained = (tuple(range(stop - 3, stop))
                        if case.descriptor.recovery_subtype == "STEP_OUTCOME_MISMATCH" else (0,))
        else:
            raise ValueError("cpu_oracle: unknown phase")
        _require(all(0 <= index < stop for index in retained), "retained trace bounds")
        current = case.trace[retained[0]].current_before if retained else target.current_before
        task_text = f"TASK\nSTART {case.task.start}\nGOAL {case.task.goal}\nCURRENT {current}"
    messages = [targets.Message("system", wire.SYSTEM_MESSAGE), targets.Message("user", task_text)]
    for trace_index in retained:
        turn = case.trace[trace_index]
        messages.extend((targets.Message("assistant", turn.action), targets.Message("user", turn.response)))
    messages = tuple(messages)
    _require(messages == record.prefix, "retained public messages")
    raw = _encoded([{"role": message.role, "content": message.content} for message in messages])
    _require(record.prefix_sha256 == sha256(raw).hexdigest(), "source prefix hash")
    _require(record.serialized_bytes == len(raw)
             and record.content_bytes == sum(len(message.content) for message in messages), "record byte counts")
    return messages, retained, target


def _binding_from_public(source):
    messages, retained, target = _public_source(source)
    projection = b"\n".join(message.content.encode("ascii") for message in messages)
    _require(len(projection) <= scanner.BOUNDS["bytes"], "projection bound")
    decision = 2 * target.trace_index + 2
    task_time = (1 if source.record.arm == "CLOSED" else
                 2 * (retained[0] if retained else target.trace_index) + 1)
    spans, offset = [], 0
    for message_index, message in enumerate(messages):
        raw = message.content.encode("ascii")
        original = retained[(message_index - 2) // 2] if message_index >= 2 else None
        observed = (0 if message_index == 0 else task_time if message_index == 1
                    else 2 * original + 2 + message_index % 2)
        _require(observed < decision, "observation chronology")
        spans.append(schemas.MessageSpan(message_index, message.role, offset, offset + len(raw),
                                         original, observed, sha256(raw).hexdigest()))
        offset += len(raw) + 1
    observations = []

    def add(message_index, start, end, suffix, kind, origin, owner=None, exemption=None):
        span = spans[message_index]
        observations.append(schemas.FieldObservation(
            f"/messages/{message_index}/{suffix}", span.start + start, span.start + end,
            projection[span.start + start:span.start + end], kind, origin, span.observed_at,
            span.source_trace_index, f"source-message:{message_index}:sha256:{span.content_sha256}",
            owner, exemption,
        ))

    def operand(message_index, kind, exemption=None):
        content = messages[message_index].content
        add(message_index, content.rindex(" ") + 1, len(content), "action/operand", kind,
            "actor", exemption=exemption)

    add(0, 0, len(wire.SYSTEM_MESSAGE), "protocol", "protocol", "system", exemption="protocol")
    task = wire.parse_task(messages[1].content)
    for match, kind in zip(re.finditer(r"(?m)^(START|GOAL|CURRENT) (\S+)$", messages[1].content),
                           ("task_start", "task_goal", "task_current")):
        add(1, match.start(2), match.end(2), "TASK/" + match[1], kind, "task",
            exemption=kind if kind != "task_current" else None)
    current, latest_current = task.current, len(observations) - 1
    events, selected, selected_time, implicated_query, contradiction = {}, None, None, None, False
    for retained_position, original in enumerate(retained):
        action_index = 2 + 2 * retained_position
        response_index = action_index + 1
        turn = source.case.trace[original]
        _require(current == turn.current_before, "action current ownership")
        action = wire.parse_action(turn.action)
        if action.operation == "READ":
            operand(action_index, "issued_query" if action.verb == "RELATION" else "read_index_operand",
                    "issued_query" if action.verb == "RELATION" else None)
            _require(turn.response == "SERVICE\n" + source.case.construction.read(turn.action),
                     "service registry ownership")
            block = wire.parse_service(turn.response[len("SERVICE\n"):], skin=source.case.descriptor.skin)
            _require(block.kind in ("MISS", "ROUTES" if action.verb == "INDEX" else "EVENTS"),
                     "service kind ownership")
            if action.verb == "RELATION":
                implicated_query = (None if any(row.node == current and row.goal == task.goal
                                               for row in block.rows) else action.operand)
            row_lines = turn.response.splitlines(keepends=True)
            row_start = sum(map(len, row_lines[:2]))
            for row_index, row in enumerate(block.rows):
                owner = row.event.encode("ascii") if block.kind == "EVENTS" else None
                if block.kind == "EVENTS":
                    events[row.event] = row
                line = row_lines[row_index + 2]
                for match in re.finditer(r"(\S+) (\S+)", line):
                    label = match[1]
                    kind = ("route_" if block.kind == "ROUTES" else "event_") + label.lower()
                    if label in ("ROUTE", "EVENT"):
                        kind = "route_id" if label == "ROUTE" else "event_id"
                    exemption = kind if kind in ("route_query", "event_did", "event_got", "event_recover") else None
                    add(response_index, row_start + match.start(2), row_start + match.end(2),
                        f"SERVICE/{block.kind}/rows/{row_index}/{label}", kind, "service", owner, exemption)
                row_start += len(line)
        elif action.operation == "STEP":
            choices = [row for row in events.values()
                       if (row.node, row.goal, row.port) == (current, task.goal, action.operand)]
            _require(len(choices) == 1, "retained STEP event ownership")
            selected, selected_time, implicated_query = choices[0], spans[action_index].observed_at, None
            operand(action_index, "step_operand")
            destination = wire.parse_world(turn.response)
            _require(source.case.construction.world_edges[current, action.operand] == destination,
                     "WORLD transition ownership")
            current, contradiction = destination, destination != selected.got
            add(response_index, len("WORLD\nCURRENT "), len(turn.response), "WORLD/CURRENT", "current", "host")
            latest_current = len(observations) - 1
        elif action.operation == "THINK":
            _require((selected is not None and action.operand == selected.event
                      and action.verb == ("REVISE" if contradiction else "KEEP"))
                     or (action.operand == implicated_query and action.verb == "REVISE"),
                     "THINK operand ownership")
            _require(turn.response == "ACK", "THINK acknowledgment")
            operand(action_index, "think_implicated", "think_implicated")
        else:
            raise ValueError("cpu_oracle: unsupported retained action")
        _require(current == turn.current_after, "response current ownership")
    _require(current == target.current_before, "decision current ownership")
    observations[latest_current] = replace(observations[latest_current], is_latest_current=True,
                                            exemption_kind=observations[latest_current].kind)
    if selected is not None:
        observations = [replace(item, exemption_kind="selected_event")
                        if item.kind == "event_id" and item.value == selected.event.encode("ascii")
                        and item.observed_at < selected_time else item for item in observations]
    public_fields = tuple(scanner.PublicField(item.path, item.start, item.end, item.exemption_kind,
                                             item.origin, item.observed_at, item.evidence, item.owner)
                          for item in observations if item.exemption_kind is not None)
    _require(len(public_fields) <= scanner.BOUNDS["fields"], "field bound")
    return schemas.BoundScanInputs(
        messages, projection, sha256(projection).hexdigest(), source.record.prefix_sha256,
        tuple(spans), tuple(observations), public_fields, retained, decision, target.target_bytes,
        target.phase, task.start.encode("ascii"), task.goal.encode("ascii"), current.encode("ascii"),
        implicated_query.encode("ascii") if implicated_query is not None else None,
        selected.event.encode("ascii") if selected is not None else None, contradiction,
    )


def _candidate_origins(source):
    owners = {token: role for role, token in source.role_tokens.items()}
    _require(len(owners) == len(source.role_tokens), "nonunique role ownership")
    origins = defaultdict(set)

    def add(token, path, kinds):
        role = owners.get(token)
        _require(role is not None and role.rsplit("/", 1)[-1] in kinds, "candidate role ownership")
        origins[token.encode("ascii")].update(((role, ("role_tokens", role)), (role, path)))

    for role, token in source.role_tokens.items():
        if role.rsplit("/", 1)[-1] in ("query", "event", "port"):
            add(token, ("role_tokens", role), ("query", "event", "port"))
    for request, block in source.case.construction.blocks.items():
        if block.kind == "EVENTS":
            for row_index, row in enumerate(block.rows):
                add(row.got, ("case", "construction", "blocks", request, "rows", str(row_index), "got"), ("node",))
    for (current, port), destination in source.case.construction.world_edges.items():
        add(destination, ("case", "construction", "world_edges", current, port), ("node",))
    return {token: tuple({"role_key": role, "source_path": path} for role, path in sorted(entries))
            for token, entries in sorted(origins.items())}


def _route_basis(source):
    registered, recoveries, queries = {}, {}, set()
    for request, block in source.case.construction.blocks.items():
        if block.kind != "EVENTS":
            continue
        action = wire.parse_action(request)
        _require((action.operation, action.verb) == ("READ", "RELATION"), "route request ownership")
        queries.add(action.operand)
        for row_index, row in enumerate(block.rows):
            _require(row.port not in registered and row.recover not in recoveries, "ambiguous route ownership")
            registered[row.port] = (action.operand, row, request, row_index)
            recoveries[row.recover] = row.port
    _require(set(source.case.construction.world_edges)
             == {(row.node, row.port) for query, row, request, row_index in registered.values()},
             "route world coverage")
    transitions, by_current, by_query = {}, defaultdict(list), defaultdict(list)
    for port, (query, row, request, row_index) in sorted(registered.items()):
        transitions[port] = dict(
            query=query, event=row.event, current=row.node, goal=row.goal, port=port, predicted=row.got,
            actual=source.case.construction.world_edges[row.node, port], recover=row.recover, receipt=row.receipt,
            source_path=("case", "construction", "blocks", request, "rows", str(row_index)),
            recovery_owner_port=recoveries.get(query),
        )
        by_current[row.node].append(port)
        by_query[query].append(port)
    return dict(schema_version="BIRTH_EFFECTIVE_ROUTE_BASIS_V1", transitions=transitions,
                ports_by_current={key: tuple(value) for key, value in by_current.items()},
                ports_by_query={key: tuple(value) for key, value in by_query.items()},
                unavailable_recover_queries=frozenset(recoveries) - queries)


def expected_route_probes(source) -> dict[str, dict]:
    """Derive six unchanged route probes and exact relative endpoint spans.

    Select the lexicographically first physically/recovery-compatible source
    pair, independently of production route inputs and successor methods.
    Missing compatible pairs fail qualification rather than erase probes.
    """
    _bounded_source(source)
    basis = _route_basis(source)
    transitions = basis["transitions"]
    pair = next(((first, second)
                 for first, edge in sorted(transitions.items())
                 for second in basis["ports_by_current"].get(edge["actual"], ())
                 if transitions[second]["recovery_owner_port"] is None
                 or (transitions[second]["recovery_owner_port"] == first
                     and edge["actual"] != edge["predicted"])), None)
    _require(pair is not None, "source route probes require a compatible pair")
    first_port, second_port = pair

    def source_row(port):
        path = transitions[port]["source_path"]
        request, position = path[3], int(path[5])
        construction = source.case.construction
        block = construction.blocks[request]
        parsed = wire.parse_service(block.raw, skin=construction.skin)
        _require(parsed == block and construction.registry.get(request) == block.raw,
                 "route probe raw block ownership")
        _require(parsed.rows[position].port == port, "route probe row ownership")
        return block.raw.encode("ascii").split(b"\n")[position + 1]

    def probe(raw, grammar, first_span, second_span):
        return dict(raw=raw, grammar=grammar, first_port=first_port, second_port=second_port,
                    first_span=first_span, second_span=second_span)

    def lines(first, second, grammar):
        raw = first + b"\n" + second
        return probe(raw, grammar, (0, len(first)), (len(first) + 1, len(raw)))

    first_action = ("STEP " + first_port).encode("ascii")
    second_action = ("STEP " + second_port).encode("ascii")
    identifiers = (first_port + "," + second_port).encode("ascii")
    first_row, second_row = source_row(first_port), source_row(second_port)
    return {
        "route_actions_literal": lines(first_action, second_action, "actions"),
        "route_actions_spacing": lines(first_action.replace(b" ", b"  "),
                                       second_action.replace(b" ", b"  "), "actions"),
        "route_actions_compact": lines(first_action.replace(b" ", b"").replace(b"_", b""),
                                       second_action.replace(b" ", b"").replace(b"_", b""), "actions"),
        "route_ordered_ids": probe(identifiers, "ordered_ids", (0, len(identifiers)),
                                   (0, len(identifiers))),
        "route_event_rows": lines(first_row, second_row, "event_rows"),
        "route_mixed": lines(first_row, second_action, "mixed"),
    }


def verify_inventory_ownership(source, result) -> None:
    """Raise ValueError on source-derived binding, inventory, byte or hash drift.

    Checks all binding fields, both inventory source owners, future binding,
    candidates and every origin value, disclosure receipts, complete route
    indexes, canonical inventory bytes and their boundary hash/count references.
    The source's authority and unrelated core/scan assertions remain the caller's.
    """
    _bounded_source(source)
    binding = _binding_from_public(source)
    _require(result.binding == binding, "binding ownership")
    future, route = result.future_inputs, result.route_inputs
    _require(future.source == source and route.source == source, "inventory source ownership")
    _require(future.binding == binding, "future binding ownership")
    origins = _candidate_origins(source)
    candidates = frozenset(origins)
    disclosures = defaultdict(list)
    for item in binding.observations:
        if item.value in candidates and (item.origin in ("service", "actor")
                                         or (item.origin == "host" and item.path.endswith("/WORLD/CURRENT"))):
            disclosures[item.value].append(item)
    disclosed = frozenset(disclosures)
    future_ids = candidates - disclosed
    expected_future = dict(candidates=candidates, candidate_provenance=origins, disclosed=disclosed,
                           future_identifiers=future_ids,
                           disclosure_provenance={key: tuple(value) for key, value in disclosures.items()})
    for name, expected in expected_future.items():
        _require(_canonical_value(getattr(future, name)) == _canonical_value(expected), "future " + name)
    expected_route = _route_basis(source)
    for name, expected in expected_route.items():
        _require(_canonical_value(getattr(route, name)) == _canonical_value(expected), "route " + name)
    _require(future.schema_version == "BIRTH_RETAINED_FUTURE_IDS_V1", "future schema")
    candidate_raw = _encoded(dict(schema_version="BIRTH_RETAINED_FUTURE_IDS_V1",
                                 candidates=candidates, candidate_provenance=origins))
    retained_raw = _encoded({name: expected_future[name] for name in
                             ("disclosed", "future_identifiers", "disclosure_provenance")})
    route_raw = _encoded(expected_route)
    document = primitives.parse_canonical_json(result.boundary_bytes)
    for field_name, document_name, expected, count in (
        ("candidate_inventory_bytes", "candidate_inventory", candidate_raw, len(candidates)),
        ("retained_inventory_bytes", "retained_inventory", retained_raw, len(future_ids)),
        ("route_basis_bytes", "route_basis", route_raw, len(expected_route["transitions"])),
    ):
        _require(getattr(result, field_name) == expected, field_name)
        _require(document.get(document_name) == dict(sha256=sha256(expected).hexdigest(),
                                                    bytes=len(expected), count=count), document_name + " reference")
    expected_envelope = dict(
        source_provenance=source.provenance_bytes, source_provenance_sha256=source.provenance_sha256,
        case_sha256=source.case_sha256, record_sha256=source.record_sha256,
        world=source.case.descriptor.world, member=source.case.descriptor.member,
        unit_id=source.record.unit.unit_id, arm=source.record.arm, target=source.record.unit,
        disclosed_count=len(disclosed), public_projection=binding.projection_bytes,
        field_observations=binding.observations, scanner_fields=binding.fields, latest_current=binding.current,
    )
    for name in ("phase", "decision_index", "retained_trace_indices", "public_messages", "projection_sha256",
                 "source_prefix_sha256", "message_spans", "task_start", "task_goal", "implicated_query",
                 "implicated_event", "observed_contradiction"):
        expected_envelope[name] = getattr(binding, name)
    for name, expected in expected_envelope.items():
        _require(name in document and document[name] == _canonical_value(expected), "boundary " + name)


def expected_private_probes(source, record) -> dict[str, bytes]:
    """Return source-owned complete values, keyed as category:source-location.

    Locations label probes only; their bytes are never injected. Includes every
    role key, case/recovery-case key, all four unit keys, and every categorical
    descriptor/case/construction/target/record value, retaining duplicate owners.
    No fragments, pointer encodings, numeric atoms or scanner basis are used.
    """
    _bounded_source(source)
    _require(record == source.record, "private probe record ownership")
    case, probes = source.case, {}

    def add(category, location, value):
        _require(type(value) is str and bool(value) and value.isascii(), "private source text")
        probes[category + ":" + location] = value.encode("ascii")

    for name in ("pair_type", "family", "family_motif", "flow", "recovery_subtype",
                 "terminal_class", "goal_side", "domain"):
        add("private_category", "case/descriptor/" + name, getattr(case.descriptor, name))
    add("private_category", "case/status", case.status)
    for name in ("domain", "scope", "status"):
        add("private_category", "case/construction/" + name, getattr(case.construction, name))
    add("private_category", "record/arm", record.arm)
    add("private_category", "record/unit/phase", record.unit.phase)
    case_key = f"{case.descriptor.world}/{case.descriptor.member}"
    add("private_case_key", "case/descriptor/case_id", case_key)
    if case.descriptor.recovery_match_id is not None:
        add("private_case_key", "case/descriptor/recovery_match_id", "/".join(case.descriptor.recovery_match_id))
    add("private_unit_key", "record/unit/unit_id", record.unit.unit_id)
    for index, target in enumerate(case.targets):
        add("private_category", f"case/targets/{index}/phase", target.phase)
        add("private_unit_key", f"case/targets/{index}/ordinal", f"{case_key}/u{target.ordinal}")
    for role in sorted(source.role_tokens):
        add("private_role_key", "role_tokens/" + role, role)
    return probes


def assert_private_basis_totality(source, record, private_basis) -> None:
    """Compare every (category, full value, exact source path), with multiplicity."""
    expected = Counter()
    for key, value in expected_private_probes(source, record).items():
        category, location = key.split(":", 1)
        path = (("role_tokens", location[len("role_tokens/"):]) if category == "private_role_key"
                else tuple(location.split("/")))
        expected[category, value, path] += 1
    _require(type(private_basis) is tuple and len(private_basis) == sum(expected.values()),
             "private basis cardinality")
    actual = Counter((item.category, item.value, item.source_path) for item in private_basis)
    _require(actual == expected, "private basis totality/ownership")
