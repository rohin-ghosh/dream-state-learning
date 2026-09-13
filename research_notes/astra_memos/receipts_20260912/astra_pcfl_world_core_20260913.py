"""Partial PCFL route algebra on CPU fixtures, never an approved model-call world."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
import hashlib
from itertools import combinations, product
import json
import math
from pathlib import Path
import re


SCHEMA = "astra_pcfl_partial_world_20260913_v1"
SOURCE_PINS = {
    "research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_synthesis.md": "222677395031224e5bb645a18ada975a571db28ae9c818f12fa396e09a394456",
    "research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_exact_build_ledger.md": "f3fe13058b86cc0af4863abd5a54bdaa98bf3e846761a8e87230a3d5f2c53679",
    "research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_implementation_reuse_map.md": "9f96d8699f6088e872e56263f8a325a7849191a853a03093df479045919d13f5",
    "research_notes/analysis/2026-09-13_full_objective_evidence_and_pcfl_redteam.md": "01d1b8355bfe094c92bb5ddf50a2152f701d0af44efc41803f912dba74ea118c",
}
SLOTS = {
    "node": ("S_L", "A", "H", "G_L", "S_R", "B", "G_R0", "G_R1", "X", "Z", "Y"),
    "port": ("a0", "a1", "b", "c", "d", "f0", "f1", "u", "q0", "q1"),
    "event": tuple(f"e{index}" for index in range(9)),
    "link": tuple(f"l{index}" for index in range(6)),
    "probe": ("relevant", "distractor"),
    "receipt": tuple(f"r{index}" for index in range(9)),
    "goal": ("old_left", "old_right", "delayed0", "delayed1"),
}
UNBOUND = (
    "Exact two DEV, four excluded and disposable root seed/manifests; only realized DEV O=0/1 is declared (ledger section9.8).",
    "Tokenizer-qualified opaque inventory/search seed and registered-row/control token-equality acceptance receipt (ledger9.7; reuse2.1).",
    "Exact global task/ROUTE prompt bytes and both probe render/order schemas plus primary render (ledger9.2,9.6).",
    "Concrete isolated distractor frontier endpoints/ports, D outcome/receipt schema, and reachout action protocol are not enumerated in synthesis4.1.",
    "Exact projections for goal text, outcome frequencies and affordance order, including cryptographic receipt metadata visibility, are not bound.",
    "Full 48-decision receipt/EVENT/LINK projection audit and 32-link successor-support audit need exact witnessed/child-row interfaces; no child rows are authored here.",
)
ID_PATTERN = r"[0-9a-f]{24}"
ROUTE_PATTERN = re.compile(r"ROUTE (" + ID_PATTERN + r") (" + ID_PATTERN + r") : (" + ID_PATTERN + r"(?:," + ID_PATTERN + r")*)")
PUBLIC_RECEIPT_FIELDS = {"root", "stage", "turn", "receipt", "source", "port", "destination", "previous_sha256", "sha256"}
PUBLIC_TASK_FIELDS = {"start", "goal", "candidates", "commits", "retries", "intermediate_returns"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    def check(item):
        if item is None or type(item) in (str, bool, int):
            return
        if type(item) is list:
            for child in item:
                check(child)
            return
        if type(item) is dict and all(type(key) is str for key in item):
            for child in item.values():
                check(child)
            return
        raise ValueError("closed JSON wire requires explicit lists/dicts; no floats or implicit dataclass/private export")
    check(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def bit(value):
    require(type(value) is int and value in (0, 1), "strict bit required")
    return value


@dataclass(frozen=True)
class FixtureRoot:
    seed: int
    realized_old: int
    identifier: str
    inventory: tuple

    def lookup(self, namespace, slot):
        return dict(dict(self.inventory)[namespace])[slot]


@dataclass(frozen=True)
class Edge:
    event: str
    source: str
    port: str
    destination: str
    receipt: str


@dataclass(frozen=True)
class PrivateCell:
    root: FixtureRoot
    old: int
    relevant: int
    distractor: int
    edges: tuple


def build_fixture_root(seed, realized_old):
    """Proposed fixed-width ASCII inventory, explicitly NOT token-qualified DEV IDs."""
    require(type(seed) is int and seed >= 0, "explicit nonnegative fixture seed required")
    bit(realized_old)
    def identifier(namespace, index):
        return digest([SCHEMA, "CPU_FIXTURE_ONLY", seed, namespace, index])[:24]
    inventory = tuple((namespace, tuple((slot, identifier(namespace, index)) for index, slot in enumerate(slots)))
                      for namespace, slots in SLOTS.items())
    root = FixtureRoot(seed, realized_old, identifier("root", 0), inventory)
    validate_inventory(root)
    return root


def validate_inventory(root):
    require(type(root) is FixtureRoot and type(root.seed) is int and root.seed >= 0, "fixture root required")
    bit(root.realized_old)
    require(type(root.inventory) is tuple and all(type(entry) is tuple and len(entry) == 2 and
            type(entry[1]) is tuple and all(type(pair) is tuple and len(pair) == 2 for pair in entry[1])
            for entry in root.inventory), "immutable namespace records required")
    require(tuple(namespace for namespace, values in root.inventory) == tuple(SLOTS), "namespace inventory differs")
    identifiers = [root.identifier]
    for namespace, values in root.inventory:
        require(tuple(slot for slot, identifier in values) == SLOTS[namespace], "slot inventory differs")
        identifiers.extend(identifier for slot, identifier in values)
    require(all(type(value) is str and re.fullmatch(ID_PATTERN, value) for value in identifiers), "fixed-width ASCII ID required")
    require(len(set(identifiers)) == len(identifiers), "namespace collision; no redraw")
    return {"identifier_count": len(identifiers), "fixed_ascii_width": 24, "namespace_disjoint": True,
            "tokenizer_equality_verified": False, "scientific_inventory_bound": False}


def _edges(root, old, relevant):
    nodes = lambda slot: root.lookup("node", slot)
    ports = lambda slot: root.lookup("port", slot)
    definitions = (
        ("S_L", f"a{old}", "A"), ("A", "b", "H"), ("H", "c", "G_L"),
        ("S_R", "d", "B"), ("B", "f0", "G_R0"), ("B", "f1", "G_R1"),
        ("S_L", f"a{1 - old}", "X"), ("Z", "u", "Y"), ("H", f"q{relevant}", "S_R"),
    )
    return tuple(Edge(root.lookup("event", f"e{index}"), nodes(source), ports(port), nodes(destination),
                      root.lookup("receipt", f"r{index}")) for index, (source, port, destination) in enumerate(definitions))


def expand_cube(root):
    validate_inventory(root)
    return tuple(PrivateCell(root, old, relevant, distractor, _edges(root, old, relevant))
                 for old, relevant, distractor in product((0, 1), repeat=3))


def validate_cell(cell):
    require(type(cell) is PrivateCell, "private cell required, not a public/model wire")
    validate_inventory(cell.root)
    for value in (cell.old, cell.relevant, cell.distractor):
        bit(value)
    require(cell.edges == _edges(cell.root, cell.old, cell.relevant), "registered edge topology differs")
    return True


def _goal(cell, goal):
    bit(goal)
    return cell.root.lookup("node", "S_L"), cell.root.lookup("node", f"G_R{goal}")


def task_fields(cell, goal):
    """Target-free structural fields only; exact native prompt/render remains unbound."""
    validate_cell(cell)
    start, target = _goal(cell, goal)
    return dict(start=start, goal=target, candidates=[], commits=1, retries=0, intermediate_returns=0)


def format_route(start, goal, ports):
    require(type(ports) is tuple and ports and len(ports) <= 10, "bounded port tuple required")
    require(all(type(value) is str and re.fullmatch(ID_PATTERN, value) for value in (start, goal, *ports)), "opaque route identifiers required")
    return f"ROUTE {start} {goal} : " + ",".join(ports)


def parse_route(raw):
    """CPU fixture grammar: exact single command, no normalization or terminal LF."""
    require(type(raw) is str, "route must be text")
    match = ROUTE_PATTERN.fullmatch(raw)
    require(match is not None, "not one exact candidate-free ROUTE")
    ports = tuple(match.group(3).split(","))
    require(1 <= len(ports) <= 10, "route exceeds simple-path fixture bound")
    return match.group(1), match.group(2), ports


def _cut(cell, cut):
    require(cut in (None, "OLD", "NEW"), "registered cut must be OLD or NEW")
    return None if cut is None else cell.root.lookup("event", "e0" if cut == "OLD" else "e8")


def oracle_route_v1(cell, goal, cut=None):
    """Closed-form oracle from the specified topology, independent of graph search."""
    validate_cell(cell)
    start, target = _goal(cell, goal)
    if _cut(cell, cut) is not None:
        return None
    ports = tuple(cell.root.lookup("port", name) for name in (f"a{cell.old}", "b", f"q{cell.relevant}", "d", f"f{goal}"))
    return format_route(start, target, ports)


def oracle_routes_v2(cell, goal, cut=None):
    """Enumerate EVERY simple directed path, not a shortest-path or target formula."""
    validate_cell(cell)
    start, target = _goal(cell, goal)
    removed = _cut(cell, cut)
    pending = [(start, (start,), ())]
    routes = []
    while pending:
        current, visited, ports = pending.pop()
        if current == target:
            routes.append(format_route(start, target, ports))
            continue
        for edge in cell.edges:
            if edge.event != removed and edge.source == current and edge.destination not in visited:
                pending.append((edge.destination, visited + (edge.destination,), ports + (edge.port,)))
    return tuple(sorted(routes))


def score_route(cell, goal, raw, cut=None):
    """Private post-commit evaluator; do not send this diagnostic to the actor."""
    validate_cell(cell)
    expected_start, expected_goal = _goal(cell, goal)
    removed = _cut(cell, cut)
    result = dict(syntax_valid=False, legal=False, graph_success=False, used_old=False, used_new=False,
                  retries=0, intermediate_returns=0)
    try:
        start, target, ports = parse_route(raw)
    except ValueError:
        return result
    result["syntax_valid"] = True
    if start != expected_start or target != expected_goal:
        return result
    current, traversed = start, []
    for port in ports:
        matches = [edge for edge in cell.edges if edge.event != removed and edge.source == current and edge.port == port]
        if len(matches) != 1:
            return result
        current = matches[0].destination
        traversed.append(matches[0].event)
        result["used_old"] = cell.root.lookup("event", "e0") in traversed
        result["used_new"] = cell.root.lookup("event", "e8") in traversed
    result.update(legal=True, graph_success=current == target,
                  used_old=cell.root.lookup("event", "e0") in traversed,
                  used_new=cell.root.lookup("event", "e8") in traversed)
    return result


class RouteSession:
    """One committed command, one final public receipt; no intermediate return."""

    def __init__(self, cell, goal):
        validate_cell(cell)
        bit(goal)
        self._cell, self._goal, self._used = cell, goal, False
        self._diagnostic = None

    def public_task(self):
        return task_fields(self._cell, self._goal)

    def commit(self, raw):
        require(not self._used, "one-shot session consumed; no retry")
        self._used = True
        self._diagnostic = score_route(self._cell, self._goal, raw)
        return {"terminal": True, "arrived": self._diagnostic["graph_success"]}


def execute_action(cell, action, *, stage, history=()):
    """Issued edge receipt for a committed CPU action, not an EVENT/LINK target.

    Addressed source/port actions and stage-local chains are fixture scaffolding;
    no reachout/probe action semantics or integrated world are claimed.
    """
    validate_cell(cell)
    require(type(action) is dict and set(action) == {"source", "port"}, "action allowlist differs")
    require(stage in ("OLD", "NEW") and type(history) is tuple, "explicit stage and immutable receipt chain required")
    for index, receipt in enumerate(history):
        check_receipt(cell, receipt, history[:index])
        require(receipt["stage"] == stage, "cross-stage chain unsupported until visibility is bound")
    allowed = cell.edges[:8] if stage == "OLD" else cell.edges[8:]
    matches = [edge for edge in allowed if edge.source == action["source"] and edge.port == action["port"]]
    require(len(matches) == 1, "action has no witnessed transition; no invented destination")
    edge = matches[0]
    require(edge.receipt not in {receipt["receipt"] for receipt in history}, "duplicate issued receipt")
    receipt = dict(root=cell.root.identifier, stage=stage, turn=len(history), receipt=edge.receipt,
                   source=edge.source, port=edge.port, destination=edge.destination,
                   previous_sha256=history[-1]["sha256"] if history else None)
    receipt["sha256"] = digest(receipt)
    return history + (receipt,)


def check_receipt(cell, receipt, prior=()):
    validate_cell(cell)
    require(type(receipt) is dict and set(receipt) == PUBLIC_RECEIPT_FIELDS and type(prior) is tuple, "receipt allowlist differs")
    stage = receipt["stage"]
    require(stage in ("OLD", "NEW") and len(prior) < (8 if stage == "OLD" else 1), "stage-local receipt bound differs")
    allowed = cell.edges[:8] if stage == "OLD" else cell.edges[8:]
    previous, seen = None, set()
    for index, item in enumerate(prior + (receipt,)):
        require(type(item) is dict and set(item) == PUBLIC_RECEIPT_FIELDS, "prior receipt allowlist differs")
        require(type(item["turn"]) is int and item["turn"] == index and item["root"] == cell.root.identifier and
                item["stage"] == stage, "receipt chronology/root differs")
        require(item["previous_sha256"] == previous, "receipt predecessor differs")
        payload = {key: value for key, value in item.items() if key != "sha256"}
        require(digest(payload) == item["sha256"], "receipt bytes/hash differ")
        require(any((item["receipt"], item["source"], item["port"], item["destination"]) ==
                    (edge.receipt, edge.source, edge.port, edge.destination) for edge in allowed), "receipt not actual registered transition")
        require(item["receipt"] not in seen, "duplicate receipt")
        seen.add(item["receipt"])
        previous = item["sha256"]
    return True


def structural_projection(cell, goal, projection):
    """Unrendered mathematical evidence, NOT an approved model prompt or child rows."""
    validate_cell(cell)
    require(projection in ("TASK", "PRE_OUTCOME_KNOWN", "OLD_ONLY", "NEW_ONLY", "FULL"), "unknown projection")
    result = {"task_fields": task_fields(cell, goal)}
    if projection in ("PRE_OUTCOME_KNOWN", "OLD_ONLY", "FULL"):
        result["old_observations"] = [[edge.source, edge.port, edge.destination] for edge in cell.edges[:8]]
    if projection in ("NEW_ONLY", "FULL"):
        edge = cell.edges[8]
        result["new_observation"] = [edge.source, edge.port, edge.destination]
    return result


def entropy(values):
    counts = Counter(values)
    total = len(values)
    require(total > 0, "empty entropy input")
    result = -sum((count / total) * math.log2(count / total) for count in counts.values())
    require(result.is_integer(), "fixture entropies must be exact integer bits")
    return int(result)


def mutual_information(first, second):
    require(len(first) == len(second) and len(first) > 0, "entropy columns differ")
    return entropy(first) + entropy(second) - entropy(list(zip(first, second)))


def entropy_v2(first, second):
    """Independent direct joint-probability MI calculation, not entropy subtraction."""
    count = len(first)
    require(count == len(second) and count > 0, "invalid joint sample")
    left, right = set(first), set(second)
    entropy_left = 0.0
    information = 0.0
    for left_value in left:
        probability_left = Fraction(sum(value == left_value for value in first), count)
        entropy_left -= float(probability_left) * math.log2(float(probability_left))
        for right_value in right:
            probability_right = Fraction(sum(value == right_value for value in second), count)
            joint = Fraction(sum(first[index] == left_value and second[index] == right_value for index in range(count)), count)
            if joint:
                information += float(joint) * math.log2(float(joint / (probability_left * probability_right)))
    require(entropy_left.is_integer() and information.is_integer(), "nonintegral fixture result")
    return int(entropy_left), int(information)


def shortcut_report(records, fields):
    require(records and fields and len(set(fields)) == len(fields), "explicit nonempty projections required")
    groups = defaultdict(list)
    for index, record in enumerate(records):
        groups[canonical([record["features"][field] for field in fields])].append(index)
    maximum = sum(max(Counter(records[index]["label"] for index in members).values()) for members in groups.values())
    deterministic = [members for members in groups.values() if len({records[index]["label"] for index in members}) == 1]
    return dict(fields=list(fields), key_count=len(groups), coverage=len(records),
                minimum_support=min(map(len, groups.values())),
                minimum_labels=min(len({records[index]["label"] for index in members}) for members in groups.values()),
                deterministic_keys=len(deterministic), decoded_occurrences=sum(map(len, deterministic)),
                bayes_best_exact_route={"numerator": maximum, "denominator": len(records)},
                membership=sorted(sorted(members) for members in groups.values()))


def _membership_v2(records, fields):
    remaining = list(range(len(records)))
    groups = []
    while remaining:
        first = remaining[0]
        group = [index for index in remaining if all(records[index]["features"][field] == records[first]["features"][field] for field in fields)]
        groups.append(group)
        remaining = [index for index in remaining if index not in group]
    return sorted(groups)


def _features(cell, goal):
    root = cell.root
    frequencies = Counter(edge.port for edge in cell.edges)
    return dict(goal_id=root.lookup("goal", f"delayed{goal}"), start_id=root.lookup("node", "S_L"),
                target_id=root.lookup("node", f"G_R{goal}"), event_handles=[edge.event for edge in cell.edges],
                link_handles=[identifier for slot, identifier in dict(root.inventory)["link"]],
                row_order_positions=list(range(9)), port_frequencies=[[port, count] for port, count in sorted(frequencies.items())],
                route_length=5)


def audit_structural_fixtures(roots):
    """Exhaustive partial certificate; its PASS cannot authorize PCFL model calls."""
    require(type(roots) is tuple and roots, "explicit fixture roots required")
    for root in roots:
        validate_inventory(root)
    require(len({root.identifier for root in roots}) == len(roots), "duplicate fixture root")
    identifiers = [root.identifier for root in roots]
    identifiers.extend(identifier for root in roots for namespace, values in root.inventory for slot, identifier in values)
    require(len(set(identifiers)) == len(identifiers), "cross-root namespace collision")
    records, route_decisions, quartets, collisions = [], [], [], []
    for root in roots:
        cells = expand_cube(root)
        for cell in cells:
            for goal in (0, 1):
                route = oracle_route_v1(cell, goal)
                routes = oracle_routes_v2(cell, goal)
                require(routes == (route,), "exact/exhaustive route oracle disagreement")
                for cut in (None, "OLD", "NEW"):
                    expected = oracle_route_v1(cell, goal, cut)
                    paths = oracle_routes_v2(cell, goal, cut)
                    require(paths == (() if expected is None else (expected,)), "independent cut oracle disagreement")
                    score = score_route(cell, goal, route, cut)
                    require(score["syntax_valid"] and score["graph_success"] == (cut is None), "committed route/cut execution differs")
                    route_decisions.append(dict(root=root.identifier, bits=[cell.old, cell.relevant, cell.distractor], goal=goal,
                                                cut=cut, route_sha256=digest(route), score=score))
                public = task_fields(cell, goal)
                require(set(public) == PUBLIC_TASK_FIELDS and public["candidates"] == [], "public task allowlist/candidate leak")
                records.append(dict(label=route, independent_label=routes[0], features=_features(cell, goal)))
        for old, goal in product((0, 1), repeat=2):
            quartet = [cell for cell in cells if cell.old == old]
            relevant = [cell.relevant for cell in quartet]
            distractor = [cell.distractor for cell in quartet]
            labels = [oracle_route_v1(cell, goal) for cell in quartet]
            values = [entropy(relevant), entropy(distractor), mutual_information(relevant, labels), mutual_information(distractor, labels)]
            require(values == [1, 1, 1, 0] and entropy_v2(relevant, labels) == (1, 1) and
                    entropy_v2(distractor, labels) == (1, 0), "symbolic R/D entropy disagreement")
            views = [structural_projection(cell, goal, "PRE_OUTCOME_KNOWN") for cell in quartet]
            require(len({digest(view) for view in views}) == 1 and all(view == views[0] for view in views), "known pre-outcome collision differs")
            quartets.append(dict(root=root.identifier, old=old, goal=goal, table=[[cell.relevant, cell.distractor] for cell in quartet],
                                 bits=values, known_visible_sha256=digest(views[0]), probe_schema_verified=False))
        for projection, varying in (("OLD_ONLY", "relevant"), ("NEW_ONLY", "old"), ("TASK", None)):
            for goal in (0, 1):
                groups = defaultdict(list)
                for index, cell in enumerate(cells):
                    if varying == "relevant":
                        key = (cell.old, cell.distractor)
                    elif varying == "old":
                        key = (cell.relevant, cell.distractor)
                    else:
                        key = ()
                    groups[key].append(index)
                for members in groups.values():
                    views = [structural_projection(cells[index], goal, projection) for index in members]
                    labels = [oracle_route_v1(cells[index], goal) for index in members]
                    independent = [oracle_routes_v2(cells[index], goal)[0] for index in members]
                    expected_count, expected_labels = (8, 4) if projection == "TASK" else (2, 2)
                    require(len(members) == expected_count and len(set(labels)) == expected_labels and labels == independent and
                            len({digest(view) for view in views}) == 1 and all(view == views[0] for view in views), "structural collision/labels differ")
                    require(all(count == (2 if projection == "TASK" else 1) for count in Counter(labels).values()), "collision multiplicities differ")
                    collisions.append(dict(root=root.identifier, projection=projection, goal=goal, members=members,
                                           labels=expected_labels, visible_sha256=digest(views[0])))
    fields = tuple(records[0]["features"])
    shortcuts = []
    for size in (1, 2):
        for selection in combinations(fields, size):
            report = shortcut_report(records, selection)
            require(report["membership"] == _membership_v2(records, selection), "independent projection membership differs")
            require(report["coverage"] == len(records) and report["minimum_support"] >= 2 and report["minimum_labels"] >= 2 and
                    report["deterministic_keys"] == report["decoded_occurrences"] == 0, "structural shortcut leak")
            shortcuts.append(report)
    result = dict(scope="CPU_FIXTURE_STRUCTURAL_ONLY", roots=len(roots), worlds=8 * len(roots), delayed_tasks=len(records),
                  parse_execute_decisions=len(route_decisions), old_only_groups=sum(row["projection"] == "OLD_ONLY" for row in collisions),
                  new_only_groups=sum(row["projection"] == "NEW_ONLY" for row in collisions),
                  task_groups=sum(row["projection"] == "TASK" for row in collisions), entropy_quartets=len(quartets),
                  structural_checks_passed=True, full_construct_passed=False, ready_for_model_calls=False,
                  oracle_decisions=route_decisions, symbolic_entropy=quartets, structural_collisions=collisions,
                  structural_shortcuts=shortcuts, missing_native_projections=["goal_text", "outcome_frequencies", "affordance_order"])
    result["sha256"] = digest(result)
    return result


def construct_gate(source_root="/data/home/rohing/dream-state"):
    """Two declared DEV slots remain unbound; six seeded CPU fixtures are not them."""
    for name, expected in SOURCE_PINS.items():
        require(hashlib.sha256((Path(source_root) / name).read_bytes()).hexdigest() == expected, "controlling document pin changed: " + name)
    two = tuple(build_fixture_root(seed, seed) for seed in (0, 1))
    four = tuple(build_fixture_root(seed, seed % 2) for seed in (2, 3, 4, 5))
    result = dict(schema=SCHEMA, status="VS_ASSAY_INVALID", reason="UNBOUND_SCIENTIFIC_CONSTRUCT_NOT_A_FAILED_MODEL",
                  ready_for_model_calls=False, full_construct_passed=False,
                  declared_dev_slots=[dict(slot=0, realized_old=0, root_manifest=None), dict(slot=1, realized_old=1, root_manifest=None)],
                  source_pins=dict(SOURCE_PINS), unresolved_bindings=list(UNBOUND),
                  fixture_seed_declaration={"two_slot_illustration": [0, 1], "four_root_count_illustration": [2, 3, 4, 5],
                                            "qualification": "CPU golden fixtures only; not DEV/excluded/disposable scientific seeds"},
                  two_slot_fixture=audit_structural_fixtures(two), four_root_fixture=audit_structural_fixtures(four))
    result["sha256"] = digest(result)
    return result
