"""Pure PCFL DEV world and byte boundaries; no model, writer, or launch path."""
from __future__ import annotations

import base64
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
from itertools import product
import json
import re


SCHEMA = "pcfl_vertical_cpu_v1"
BINDING_MEMO = "2026-09-13_pcfl_distractor_and_opaque_id_production_bindings.md"
BINDING_MEMO_SHA256 = "bcdae11f3eb5c0653b842f16bbf5ba1e34cc5ffdbdc62689aca1ce2ca0f6eecf"
SOURCE_PINS = {
    "2026-09-13_pcfl_vertical_dev_v2_synthesis.md": "222677395031224e5bb645a18ada975a571db28ae9c818f12fa396e09a394456",
    "2026-09-13_pcfl_vertical_dev_v2_2_writer_repair.md": "683fcba7762b69f408e5371cd9525e62c7ba6c8aa25494542f3041fec275dfca",
    "2026-09-13_pcfl_vertical_dev_v2_prospective_binding_register.md": "5d7920ea8e515794c57d19a9bd0d4793c835848727266aa0cb41ed729e5abadd",
    "2026-09-13_pcfl_vertical_dev_v2_exact_build_ledger.md": "f3fe13058b86cc0af4863abd5a54bdaa98bf3e846761a8e87230a3d5f2c53679",
    "2026-09-13_pcfl_vertical_dev_v2_exact_inference_inventory.md": "599944f3f351d3d9fe19c7257c4d540d188d728d6eb9f14869c20fb5c80c492b",
    "2026-09-13_pcfl_v22_execution_readiness_audit.md": "deb3b51abde362a0d35f41295b565c9b5ef02d7d77757644ae5834294e539c13",
    "2026-09-13_pcfl_v22_minimum_execution_closure_contract.md": "f9b9891761c47e6d8047e7a9161a827d00fae464df91940c523b40f85af535d0",
}
PREFIXES = dict(node="N", port="P", event="E", link="L", probe="Q", receipt="R", goal="G")
SLOTS = {
    "node": ("S_L", "A", "H", "G_L", "S_R", "B", "G_R0", "G_R1", "X", "Z", "Y"),
    "port": ("a0", "a1", "b", "c", "d", "f0", "f1", "u", "q0", "q1"),
    "event": tuple(f"e{index}" for index in range(9)),
    "link": tuple(f"l{index}" for index in range(6)),
    "probe": ("relevant", "distractor"),
    "receipt": tuple(f"r{index}" for index in range(11)),
    "goal": ("old_left", "old_right", "delayed0", "delayed1"),
}
ROOT_LABELS = tuple(f"excluded/{index}" for index in range(4)) + ("disposable/0", "dev/0", "dev/1")
OLD_SOURCES = ("S_L", "A", "H", "S_R", "B", "Z", "S_L", "B")
LINK_PAIRS = ((0, 1, "A"), (1, 2, "H"), (3, 4, "B"), (3, 5, "B"), (1, 8, "H"), (8, 3, "S_R"))
PROJECTIONS = (
    "EXACT_WITNESSED_GRAPH", "FULL_CHILD_TEXT", "EVENT_ATOMS_TEXT", "ACTIVE_LINKED_TEXT",
    "NATIVE_CONTEXT", "RAW_EPISODIC", "OLD_ONLY_TEXT", "NEW_ONLY_TEXT", "NONE_OFF", "WRONG_ROOT",
)
WRAPPERS = (
    "Retrieve the exact stored memory for this request.\n{REQUEST}\nReply with only the stored memory block.",
    "Personal memory query:\n{REQUEST}\nReturn only the exact stored block.",
    "{REQUEST}\nRead personal memory and output only its exact stored block.",
    "Use personal memory for the request below. Output the stored block only.\n{REQUEST}",
    "Lookup request: {REQUEST}\nRespond only with the exact memory block.",
    "Return the exact personal-memory block matching:\n{REQUEST}\nNo explanation.",
    "Read this local memory address and emit only the stored block.\nAddress request: {REQUEST}",
    "For this personal memory lookup, give only the exact stored block.\n{REQUEST}",
    "Provide the exact stored personal-memory block at this address.\n{REQUEST}\nOutput only the block.",
)
MEMORY_SYSTEM = "You are the child's local personal-memory reader. You receive one opaque address request and no task. Return only the exact stored memory block associated with that address. Do not explain, infer, repair, or invent. If nothing usable is remembered, return exactly MISS."
MODULAR_SYSTEM = "You operate a deterministic directed route system. Identifiers are opaque and case-sensitive. Use only public information in this conversation and exact local-memory reads. Never invent, rename, or repair an identifier. On each turn output exactly one line: a permitted READ request or one final ROUTE. At most 12 READs are allowed. The environment gives no route feedback before the complete ROUTE is committed, and there is no retry."
NATIVE_SYSTEM = "You operate a deterministic directed route system. Identifiers are opaque and case-sensitive. Use only public information in this conversation and your own learned memory. You have no external memory tool. Never invent, rename, or repair an identifier. Commit exactly one ROUTE line. The environment gives no route feedback before the complete ROUTE is committed, and there is no retry."
FORMATION_SYSTEM = "You are exploring a deterministic public route system and recording what you personally observe. Identifiers are opaque and case-sensitive. Never invent, rename, infer, or repair an identifier. An EXPLORE action can use only a listed public source and port. A memory commitment may use public receipts and accepted commitments visible in this wake context. After a reset, it may also use exact identifiers recalled from your own learned memory; no external memory text or hidden information is provided."
REACHOUT_SYSTEM = "Choose one public experiment that is useful for the stated route goal. Identifiers are opaque and case-sensitive. Use only the public task and your own learned memory. The result is not shown until after commitment. Output exactly one line: PROBE <probe_id>. There is no retry."
TASK_TEMPLATE = "ROUTE TASK\nSTART {START_ID}\nGOAL {GOAL_ID}\nRequired final grammar:\nROUTE <start> <goal> : <comma-separated ports>"
EXPLORE_TEMPLATE = "EXPLORE TASK\nSOURCE {SOURCE_ID}\nAVAILABLE PORTS {COMMA_SEPARATED_PUBLIC_PORT_IDS}\nChoose one still-untried port and output exactly:\nEXPLORE <source> <port>"
EVENT_TEMPLATE = "COMMIT EVENT\nUsing only the public receipt just observed, output exactly one physical line in this grammar:\nEVENT <event_id> AT <source> DID <port> GOT <destination> EVIDENCE <receipt_id>\nAVAILABLE EVENT ADDRESS {FRESH_EVENT_ID}\nUse that fresh address as event_id. Copy every other identifier exactly. Output no other text."
LINK_TEMPLATE = "COMMIT LINK\nUsing only public EVENT commitments visible in this wake context and exact identifiers you recall from your own learned memory, output one not-yet-recorded directly chained pair in exactly this grammar:\nLINK <link_id> FROM <event_id_1> THEN <event_id_2> VIA <shared_node> EVIDENCE <receipt_id_1>,<receipt_id_2>\nAVAILABLE LINK ADDRESS {FRESH_LINK_ID}\nUse that fresh address as link_id. Output no other text."
REACHOUT_TEMPLATES = {
    "RA": "PROBE TASK\nSTART {START_ID}\nGOAL {GOAL_ID}\nAVAILABLE PROBES\n1. {PROBE_0} TESTS {SOURCE_0} TO {DESTINATION_0}\n2. {PROBE_1} TESTS {SOURCE_1} TO {DESTINATION_1}\nCommit exactly: PROBE <probe_id>",
    "RB": "PROBE TASK\nSTART {START_ID}\nGOAL {GOAL_ID}\nPROBE OPTIONS\n1. TEST {SOURCE_1} TO {DESTINATION_1} USING {PROBE_1}\n2. TEST {SOURCE_0} TO {DESTINATION_0} USING {PROBE_0}\nCommit exactly: PROBE <probe_id>",
}
PATTERNS = {
    "EVENT": r"EVENT (E_[A-Z2-7]{10}) AT (N_[A-Z2-7]{10}) DID (P_[A-Z2-7]{10}) GOT (N_[A-Z2-7]{10}) EVIDENCE (R_[A-Z2-7]{10})\n",
    "LINK": r"LINK (L_[A-Z2-7]{10}) FROM (E_[A-Z2-7]{10}) THEN (E_[A-Z2-7]{10}) VIA (N_[A-Z2-7]{10}) EVIDENCE (R_[A-Z2-7]{10}),(R_[A-Z2-7]{10})\n",
    "READ": r"READ (EVENT E_[A-Z2-7]{10}|EVENTS_AT N_[A-Z2-7]{10}|LINKS_FROM E_[A-Z2-7]{10})",
    "ROUTE": r"ROUTE (N_[A-Z2-7]{10}) (N_[A-Z2-7]{10}) : (P_[A-Z2-7]{10}(?:,P_[A-Z2-7]{10})*)",
    "EXPLORE": r"EXPLORE (N_[A-Z2-7]{10}) (P_[A-Z2-7]{10})",
    "PROBE": r"PROBE (Q_[A-Z2-7]{10})",
}
EVENT_WIRE = "EVENT {event} AT {source} DID {port} GOT {destination} EVIDENCE {receipt}\n"
LINK_WIRE = "LINK {link} FROM {first} THEN {second} VIA {via} EVIDENCE {receipt_first},{receipt_second}\n"
RECEIPT_WIRE = "RECEIPT {receipt} AT {source} DID {port} GOT {destination}\n"
PROBE_WIRE = "PROBE RESULT {probe} TESTED {source} TO {destination} AVAILABLE PORT {port}\n"


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
        raise ValueError("closed JSON requires explicit dict/list, no floats or private objects")
    check(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def byte_hash(raw):
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def detached(value):
    return json.loads(canonical(value))


def production_binding_status():
    return {"status": "VS_ASSAY_INVALID", "execution_contract_valid": False,
            "source": BINDING_MEMO, "source_sha256": BINDING_MEMO_SHA256,
            "distractor": {"endpoints": None, "port_semantics": None, "public_outcomes": None,
                           "receipt_schema": None, "post_commit_transition": None},
            "relevant_public_result": None, "production_inventory_complete": False,
            "pending": ["distractor topology and result/receipt/port semantics", "relevant public result bytes",
                        "production probe receipt slots", "G_ visibility and root metadata typing",
                        "real tokenizer joint inventory qualification", "profile/device-time gates"]}


def require_production_bindings():
    raise ValueError("VS_ASSAY_INVALID: production distractor and probe-result bindings unresolved")


def seed(label):
    require(type(label) is str and label.isascii(), "ASCII seed label required")
    return int.from_bytes(hashlib.sha256(b"PCFL-V2.1-PREP\0" + label.encode("ascii")).digest()[:8], "big") & ((1 << 63) - 1)


def opaque_candidate(label, namespace, index, salt=0):
    require(label in ROOT_LABELS and namespace in SLOTS, "unknown root/namespace")
    require(type(index) is int and 0 <= index < len(SLOTS[namespace]), "unknown inventory index")
    require(type(salt) is int and 0 <= salt < 1000000, "salt outside fixed search")
    payload = seed("opaque/" + label).to_bytes(8, "big") + b"\0" + namespace.encode("ascii") + b"\0" + str(index).encode("ascii") + b"\0" + str(salt).encode("ascii")
    return PREFIXES[namespace] + "_" + base64.b32encode(hashlib.sha256(payload).digest()).decode("ascii")[:10]


@dataclass(frozen=True)
class Root:
    label: str
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
class WorldCell:
    root: Root
    old: int
    relevant: int
    distractor: int

    @property
    def edges(self):
        definitions = (("S_L", f"a{self.old}", "A"), ("A", "b", "H"), ("H", "c", "G_L"),
                       ("S_R", "d", "B"), ("B", "f0", "G_R0"), ("B", "f1", "G_R1"),
                       ("S_L", f"a{1-self.old}", "X"), ("Z", "u", "Y"), ("H", f"q{self.relevant}", "S_R"))
        return tuple(Edge(self.root.lookup("event", f"e{index}"), self.root.lookup("node", source),
                          self.root.lookup("port", port), self.root.lookup("node", destination),
                          self.root.lookup("receipt", f"r{index}"))
                     for index, (source, port, destination) in enumerate(definitions))


def build_root(label, inventory=None):
    require(label in ROOT_LABELS, "unregistered root")
    if inventory is None:
        inventory = {namespace: {slot: opaque_candidate(label, namespace, index) for index, slot in enumerate(slots)}
                     for namespace, slots in SLOTS.items()}
    require(type(inventory) is dict and set(inventory) == set(SLOTS), "inventory namespaces differ")
    identifiers = []
    for namespace, slots in SLOTS.items():
        require(type(inventory[namespace]) is dict and set(inventory[namespace]) == set(slots), "inventory slots differ")
        for identifier in inventory[namespace].values():
            require(type(identifier) is str and re.fullmatch(PREFIXES[namespace] + r"_[A-Z2-7]{10}", identifier), "invalid opaque identifier")
            identifiers.append(identifier)
    require(len(identifiers) == len(set(identifiers)), "duplicate inventory identifier")
    return Root(label, tuple((namespace, tuple((slot, inventory[namespace][slot]) for slot in slots)) for namespace, slots in SLOTS.items()))


def to_data(value):
    if type(value) is Root:
        return {"schema": SCHEMA, "kind": "root", "label": value.label,
                "inventory": {namespace: dict(entries) for namespace, entries in value.inventory}}
    require(type(value) is WorldCell, "explicit root or private cell required")
    return {"schema": SCHEMA, "kind": "private_cell", "root": to_data(value.root),
            "old": value.old, "relevant": value.relevant, "distractor": value.distractor}


def from_data(value):
    require(type(value) is dict and value.get("schema") == SCHEMA, "schema differs")
    if value.get("kind") == "root":
        require(set(value) == {"schema", "kind", "label", "inventory"}, "root fields differ")
        return build_root(value["label"], value["inventory"])
    require(set(value) == {"schema", "kind", "root", "old", "relevant", "distractor"} and value["kind"] == "private_cell", "cell fields differ")
    cell = WorldCell(from_data(value["root"]), value["old"], value["relevant"], value["distractor"])
    validate_cell(cell)
    return cell


def validate_cell(cell):
    require(type(cell) is WorldCell and type(cell.root) is Root, "private WorldCell required")
    require(build_root(cell.root.label, to_data(cell.root)["inventory"]) == cell.root, "root differs")
    require(all(type(value) is int and value in (0, 1) for value in (cell.old, cell.relevant, cell.distractor)), "strict bits required")


def expand_cube(root):
    require(type(root) is Root, "Root required")
    return tuple(WorldCell(root, *bits) for bits in product((0, 1), repeat=3))


def _parse(kind, raw):
    require(type(raw) is str, "raw UTF-8 text required")
    match = re.fullmatch(PATTERNS[kind], raw)
    require(match is not None, "not exact " + kind)
    return match.groups()


def parse_event_line(raw):
    return dict(zip(("event", "source", "port", "destination", "receipt"), _parse("EVENT", raw)))


def parse_link_line(raw):
    return dict(zip(("link", "first", "second", "via", "receipt_first", "receipt_second"), _parse("LINK", raw)))


def parse_read(raw):
    operation, address = _parse("READ", raw)[0].split(" ")
    return operation, address


def parse_route(raw):
    start, goal, ports = _parse("ROUTE", raw)
    return start, goal, tuple(ports.split(","))


def parse_explore(raw):
    return _parse("EXPLORE", raw)


def parse_probe(raw):
    return _parse("PROBE", raw)[0]


def _task_nodes(cell, goal):
    validate_cell(cell)
    if type(goal) is int and goal in (0, 1):
        return cell.root.lookup("node", "S_L"), cell.root.lookup("node", f"G_R{goal}")
    require(goal in ("old_left", "old_right"), "unregistered goal")
    return tuple(cell.root.lookup("node", slot) for slot in (("S_L", "G_L") if goal == "old_left" else ("S_R", "G_R0")))


def format_route(start, goal, ports):
    raw = "ROUTE " + start + " " + goal + " : " + ",".join(ports)
    parse_route(raw)
    return raw


def _cut_event(cell, cut):
    require(cut in (None, "OLD", "NEW"), "unknown graph cut")
    return None if cut is None else cell.root.lookup("event", "e0" if cut == "OLD" else "e8")


def oracle_route_v1(cell, goal, cut=None):
    """Closed-form specified path, independent of search oracle."""
    start, target = _task_nodes(cell, goal)
    removed = _cut_event(cell, cut)
    if type(goal) is int:
        if removed is not None:
            return None
        slots = (f"a{cell.old}", "b", f"q{cell.relevant}", "d", f"f{goal}")
    elif goal == "old_left":
        if cut == "OLD":
            return None
        slots = (f"a{cell.old}", "b", "c")
    else:
        slots = ("d", "f0")
    return format_route(start, target, tuple(cell.root.lookup("port", slot) for slot in slots))


def oracle_routes_v2(cell, goal, cut=None):
    """Enumerate every simple path using edges, not the route formula."""
    start, target = _task_nodes(cell, goal)
    removed = _cut_event(cell, cut)
    pending, routes = [(start, (start,), ())], []
    while pending:
        current, visited, ports = pending.pop()
        if current == target:
            routes.append(format_route(start, target, ports))
            continue
        for edge in cell.edges:
            if edge.event != removed and edge.source == current and edge.destination not in visited:
                pending.append((edge.destination, visited + (edge.destination,), ports + (edge.port,)))
    return tuple(sorted(routes))


def execute_route(edges, parsed):
    start, goal, ports = parsed
    current, traversed = start, []
    for port in ports:
        matches = [edge for edge in edges if edge.source == current and edge.port == port]
        if len(matches) != 1:
            return {"legal": False, "graph_success": False, "events": traversed}
        current = matches[0].destination
        traversed.append(matches[0].event)
    return {"legal": True, "graph_success": current == goal, "events": traversed}


def score_route(cell, goal, raw, cut=None):
    start, target = _task_nodes(cell, goal)
    removed = _cut_event(cell, cut)
    result = dict(strict=False, legal=False, graph_success=False, used_old=False, used_new=False)
    try:
        parsed = parse_route(raw)
    except ValueError:
        return result
    result["strict"] = True
    if parsed[:2] != (start, target):
        return result
    execution = execute_route(tuple(edge for edge in cell.edges if edge.event != removed), parsed)
    result.update(legal=execution["legal"], graph_success=execution["graph_success"],
                  used_old=cell.root.lookup("event", "e0") in execution["events"],
                  used_new=cell.root.lookup("event", "e8") in execution["events"])
    return result


class RouteSession:
    def __init__(self, cell, goal):
        _task_nodes(cell, goal)
        self._cell, self._goal, self._used = cell, goal, False

    def commit(self, raw):
        require(not self._used, "one-shot route consumed")
        self._used = True
        return {"terminal": True, "arrived": score_route(self._cell, self._goal, raw)["graph_success"]}


def _row(raw, root, taint, provenance):
    kind = "EVENT" if raw.startswith("EVENT ") else "LINK"
    fields = parse_event_line(raw) if kind == "EVENT" else parse_link_line(raw)
    return dict(kind=kind, raw=raw, sha256=byte_hash(raw), root=root, fields=fields,
                taint=taint, provenance=detached(provenance))


def validate_row(row):
    require(type(row) is dict and set(row) == {"kind", "raw", "sha256", "root", "fields", "taint", "provenance"}, "row fields differ")
    require(row["root"] in ROOT_LABELS and row["taint"] in ("CHILD_SUBMISSION", "CEILING_FIXTURE", "CONTROL"), "row origin differs")
    require(row == _row(row["raw"], row["root"], row["taint"], row["provenance"]), "row bytes/fields/hash differ")
    return True


def ideal_rows(cell):
    """Researcher-authored ceiling fixture, not child experience or fit material."""
    validate_cell(cell)
    provenance = {"origin": "IDEAL_CPU_CEILING", "cell_sha256": digest(to_data(cell))}
    witnessed = ceiling_fixture(cell)["receipts"]
    evidence = {(receipt["source"], receipt["port"], receipt["destination"]): receipt["receipt"]
                for receipt in witnessed if receipt["kind"] == "EXPLORE"}
    events = [_row(EVENT_WIRE.format(**dict(event=edge.event, source=edge.source, port=edge.port,
                                          destination=edge.destination, receipt=evidence[(edge.source, edge.port, edge.destination)])),
                   cell.root.label, "CEILING_FIXTURE", provenance) for edge in cell.edges]
    links = []
    for index, (first, second, via) in enumerate(LINK_PAIRS):
        fields = dict(link=cell.root.lookup("link", f"l{index}"), first=cell.edges[first].event,
                      second=cell.edges[second].event, via=cell.root.lookup("node", via),
                      receipt_first=events[first]["fields"]["receipt"], receipt_second=events[second]["fields"]["receipt"])
        links.append(_row(LINK_WIRE.format(**fields), cell.root.label, "CEILING_FIXTURE", provenance))
    return events[:8] + links[:4] + events[8:] + links[4:]


def ceiling_fixture(cell):
    """Actual CPU transitions under a fixed harness policy, never a child life."""
    old = WorldSession(cell, "OLD")
    transcript = []
    for _ in OLD_SOURCES:
        source, ports = old._affordances()
        action = "EXPLORE " + source + " " + ports[0]
        result = old.explore(action)
        require(result["ok"], "scripted public action failed")
        transcript.extend((action + "\n", result["public"]))
    new = WorldSession(cell, "NEW", fixture_only=True)
    action = "PROBE " + cell.root.lookup("probe", "relevant")
    result = new.probe(action)
    transcript.extend((action + "\n", result["public"]))
    source, ports = new._affordances()
    action = "EXPLORE " + source + " " + ports[0]
    result = new.explore(action)
    require(result["ok"], "scripted new action failed")
    transcript.extend((action + "\n", result["public"]))
    return {"origin": "HARNESS_SCRIPTED_CPU_CEILING_NOT_CHILD", "receipts": old.receipts + new.receipts,
            "raw_public": "".join(transcript), "policy": "first listed OLD port; relevant probe; revealed NEW port"}


def render_reachout(cell, goal, render_id="RA", *, fixture_only=False):
    require(type(fixture_only) is bool, "explicit fixture flag required")
    if not fixture_only:
        require_production_bindings()
    start, target = _task_nodes(cell, goal)
    require(render_id in REACHOUT_TEMPLATES, "unknown reachout render")
    root = cell.root
    return REACHOUT_TEMPLATES[render_id].format(START_ID=start, GOAL_ID=target,
        PROBE_0=root.lookup("probe", "relevant"), SOURCE_0=root.lookup("node", "H"), DESTINATION_0=root.lookup("node", "S_R"),
        PROBE_1=root.lookup("probe", "distractor"), SOURCE_1=root.lookup("node", "Z"), DESTINATION_1=root.lookup("node", "Y"))


def render_task(cell, goal, render_id="NATIVE_CONTEXT", projection=None, rows=(), wrong_rows=(), *, fixture_only=False):
    start, target = _task_nodes(cell, goal)
    projection = render_id if projection is None else projection
    require(projection in PROJECTIONS, "unknown projection")
    for row in rows:
        validate_row(row)
        require(row["root"] == cell.root.label, "cross-root visible row")
    ordered_ids = ([cell.root.lookup("event", f"e{index}") for index in range(8)] +
                   [cell.root.lookup("link", f"l{index}") for index in range(4)] +
                   [cell.root.lookup("event", "e8")] + [cell.root.lookup("link", f"l{index}") for index in (4, 5)])
    identities = [row["fields"].get("event", row["fields"].get("link")) for row in rows]
    require(len(identities) == len(set(identities)) and set(identities) <= set(ordered_ids), "duplicate/unregistered render row")
    rows = sorted(rows, key=lambda row: ordered_ids.index(row["fields"].get("event", row["fields"].get("link"))))
    task = TASK_TEMPLATE.format(START_ID=start, GOAL_ID=target)
    memory = ""
    if projection == "EXACT_WITNESSED_GRAPH":
        memory = "".join("EDGE " + edge.source + " " + edge.port + " " + edge.destination + "\n" for edge in cell.edges)
    elif projection == "RAW_EPISODIC":
        require(type(fixture_only) is bool, "explicit fixture flag required")
        if not fixture_only:
            require_production_bindings()
        memory = ceiling_fixture(cell)["raw_public"]
    elif projection == "WRONG_ROOT":
        require(bool(wrong_rows), "wrong-root material required")
        for row in wrong_rows:
            validate_row(row)
            require(row["root"] != cell.root.label, "wrong-root matches task root")
        require(len({row["root"] for row in wrong_rows}) == 1, "mixed wrong roots")
        require(Counter(row["kind"] for row in wrong_rows) == Counter(EVENT=9, LINK=6), "incomplete wrong-root full projection")
        require(len({row["fields"].get("event", row["fields"].get("link")) for row in wrong_rows}) == 15, "duplicate wrong-root row")
        memory = "".join(row["raw"] for row in wrong_rows)
    elif projection not in ("NONE_OFF", "ACTIVE_LINKED_TEXT"):
        selected = list(rows)
        if projection == "EVENT_ATOMS_TEXT":
            selected = [row for row in selected if row["kind"] == "EVENT"]
        elif projection == "OLD_ONLY_TEXT":
            old_ids = {cell.root.lookup("event", f"e{index}") for index in range(8)} | {cell.root.lookup("link", f"l{index}") for index in range(4)}
            selected = [row for row in selected if row["fields"].get("event", row["fields"].get("link")) in old_ids]
        elif projection == "NEW_ONLY_TEXT":
            selected = [row for row in selected if row["kind"] == "EVENT" and row["fields"]["event"] == cell.root.lookup("event", "e8")]
        count = {"EVENT_ATOMS_TEXT": 9, "OLD_ONLY_TEXT": 12, "NEW_ONLY_TEXT": 1}.get(projection, 15)
        require(len(selected) == count, "incomplete registered context projection")
        memory = "".join(row["raw"] for row in selected)
    return {"system": MODULAR_SYSTEM if projection == "ACTIVE_LINKED_TEXT" else NATIVE_SYSTEM,
            "user": ("MEMORY\n" + memory + "\n" if memory else "") + task,
            "service_enabled": projection == "ACTIVE_LINKED_TEXT"}


class WorldSession:
    """Finite CPU transitions; receipts issued here are not model generations."""
    def __init__(self, cell, stage, prior_session=None, *, fixture_only=False):
        validate_cell(cell)
        require(stage in ("OLD", "NEW"), "unknown stage")
        require(type(fixture_only) is bool, "explicit fixture flag required")
        if stage == "NEW" and not fixture_only:
            require_production_bindings()
        self._fixture_only = fixture_only
        self._cell, self.stage = cell, stage
        self._receipts, self._attempts, self._events, self._links = [], [], [], []
        self._old_events, self._old_receipts = [], []
        self._explore_turn, self._probe_used, self._probe_result = 0, False, None
        self._event_attempts, self._link_attempts = set(), 0
        if prior_session is not None:
            require(stage == "NEW" and type(prior_session) is WorldSession and prior_session.stage == "OLD", "invalid parent session")
            require(prior_session._cell.root == cell.root and prior_session._cell.old == cell.old, "parent life differs")
            self._old_events = detached(prior_session._events)
            self._old_receipts = detached(prior_session._receipts)

    @property
    def receipts(self):
        return detached(self._receipts)

    @property
    def attempts(self):
        return detached(self._attempts)

    def explore_prompt(self):
        source, ports = self._affordances()
        return EXPLORE_TEMPLATE.format(SOURCE_ID=source, COMMA_SEPARATED_PUBLIC_PORT_IDS=",".join(ports))

    def public_affordances(self):
        source, ports = self._affordances()
        return {"source": source, "ports": list(ports)}

    def _affordances(self):
        root = self._cell.root
        if self.stage == "OLD":
            require(self._explore_turn < 8, "OLD opportunities consumed")
            source = root.lookup("node", OLD_SOURCES[self._explore_turn])
            tried = {(receipt["source"], receipt["port"]) for receipt in self._receipts if receipt["kind"] == "EXPLORE"}
            available = {edge.port for edge in self._cell.edges[:8] if edge.source == source and (source, edge.port) not in tried}
            return source, tuple(root.lookup("port", slot) for slot in SLOTS["port"] if root.lookup("port", slot) in available)
        require(self._explore_turn == 0 and self._probe_result is not None, "NEW requires one committed successful probe")
        return self._probe_result["source"], (self._probe_result["port"],)

    def _issue(self, fields):
        receipt = dict(fields, root=self._cell.root.label, stage=self.stage, turn=len(self._receipts),
                       previous_sha256=self._receipts[-1]["sha256"] if self._receipts else None,
                       fixture_only=self._fixture_only)
        receipt["sha256"] = digest(receipt)
        self._receipts.append(receipt)
        return detached(receipt)

    def probe(self, raw):
        if not self._fixture_only:
            require_production_bindings()
        require(self.stage == "NEW" and not self._probe_used, "probe unavailable/consumed")
        self._probe_used = True
        attempt = {"kind": "PROBE", "raw": raw, "ok": False}
        self._attempts.append(attempt)
        try:
            probe_id = parse_probe(raw)
            root = self._cell.root
            require(probe_id in [root.lookup("probe", name) for name in SLOTS["probe"]], "unlisted probe")
            relevant = probe_id == root.lookup("probe", "relevant")
            fields = dict(kind="PROBE", probe=probe_id, receipt=root.lookup("receipt", "r9" if relevant else "r10"),
                          source=root.lookup("node", "H" if relevant else "Z"), destination=root.lookup("node", "S_R" if relevant else "Y"),
                          port=root.lookup("port", f"q{self._cell.relevant if relevant else self._cell.distractor}"))
            self._probe_result = fields
            receipt = self._issue(fields)
            attempt["ok"] = True
            return {"ok": True, "receipt": receipt, "public": PROBE_WIRE.format(**fields)}
        except ValueError as error:
            attempt["error"] = str(error)
            return {"ok": False, "error": str(error)}

    def explore(self, raw):
        source, ports = self._affordances()
        opportunity = self._explore_turn
        self._explore_turn += 1
        attempt = {"kind": "EXPLORE", "raw": raw, "opportunity": opportunity, "ok": False}
        self._attempts.append(attempt)
        try:
            parsed_source, port = parse_explore(raw)
            require(parsed_source == source and port in ports, "unlisted or previously tried action")
            if self.stage == "OLD":
                matches = [edge for edge in self._cell.edges[:8] if edge.source == source and edge.port == port]
                require(len(matches) == 1, "not a unique registered transition")
                destination = matches[0].destination
            else:
                destination = self._probe_result["destination"]
            receipt = self._issue(dict(kind="EXPLORE", receipt=self._cell.root.lookup("receipt", f"r{opportunity if self.stage == 'OLD' else 8}"),
                                       source=source, port=port, destination=destination, opportunity=opportunity))
            attempt["ok"] = True
            return {"ok": True, "receipt": receipt, "public": RECEIPT_WIRE.format(**receipt)}
        except ValueError as error:
            attempt["error"] = str(error)
            return {"ok": False, "error": str(error)}

    def event_prompt(self, receipt):
        self.check_receipt(receipt)
        require(receipt["kind"] == "EXPLORE", "event needs executed action")
        fresh = self._cell.root.lookup("event", f"e{receipt['opportunity'] if self.stage == 'OLD' else 8}")
        return EVENT_TEMPLATE.format(FRESH_EVENT_ID=fresh)

    def link_prompt(self):
        require(self._explore_turn == (8 if self.stage == "OLD" else 1), "link phase before exploration completes")
        require(self._link_attempts < (4 if self.stage == "OLD" else 2), "LINK opportunities consumed")
        fresh = self._cell.root.lookup("link", f"l{self._link_attempts + (0 if self.stage == 'OLD' else 4)}")
        return LINK_TEMPLATE.format(FRESH_LINK_ID=fresh)

    def check_receipt(self, receipt, include_old=False):
        require(type(receipt) is dict, "receipt must be issued object")
        pool = self._receipts + (self._old_receipts if include_old else [])
        require(receipt in pool, "receipt not issued in this life/stage")
        require(receipt["sha256"] == digest({key: value for key, value in receipt.items() if key != "sha256"}), "receipt hash differs")
        return True


def _admission(raw, kind, action):
    require(type(raw) is str, "raw generation text required; missing call must use empty text")
    result = dict(kind=kind, raw=raw, generation_sha256=byte_hash(raw), byte_start=0,
                  byte_end=len(raw.encode("utf-8")), accepted=False, row=None,
                  origin="CALLER_SUPPLIED_GENERATION", native_generation_verified=False)
    try:
        result["row"] = action()
        result["accepted"] = True
    except ValueError as error:
        result["error"] = str(error)
    return result


def admit_event(raw, receipt, session, fresh_id):
    require(type(session) is WorldSession, "issuing session required")
    def admit():
        session.check_receipt(receipt)
        require(receipt["kind"] == "EXPLORE", "probe result is not an executed event")
        opportunity = receipt["opportunity"]
        require(opportunity not in session._event_attempts, "event opportunity consumed")
        session._event_attempts.add(opportunity)
        require(session._receipts[-1] == receipt, "EVENT not immediately after own action")
        expected = session._cell.root.lookup("event", f"e{opportunity if session.stage == 'OLD' else 8}")
        require(fresh_id == expected, "fresh handle is not chronologically presealed")
        fields = parse_event_line(raw)
        require(fields["event"] == fresh_id, "event handle differs")
        require(all(fields[key] == receipt[key] for key in ("source", "port", "destination", "receipt")), "event not exact own executed receipt")
        row = _row(raw, session._cell.root.label, "CHILD_SUBMISSION",
                   {"receipt_sha256": receipt["sha256"], "generation_sha256": byte_hash(raw), "byte_start": 0,
                    "byte_end": len(raw.encode("utf-8")), "native_generation_verified": False,
                    "fixture_only": session._fixture_only})
        session._events.append(detached(row))
        return row
    return _admission(raw, "EVENT", admit)


def admit_link(raw, receipts, session, fresh_id, events):
    require(type(session) is WorldSession, "issuing session required")
    def admit():
        prompt = session.link_prompt()
        session._link_attempts += 1
        require("AVAILABLE LINK ADDRESS " + fresh_id + "\n" in prompt, "fresh link handle differs")
        require(type(receipts) in (tuple, list) and len(receipts) == 2, "two issued receipts required")
        for receipt in receipts:
            session.check_receipt(receipt, include_old=True)
            require(receipt["kind"] == "EXPLORE", "link needs executed events")
        require(type(events) in (tuple, list) and len(events) == 2, "two own admitted EVENTs required")
        pool = session._events + session._old_events
        for row in events:
            validate_row(row)
            require(row in pool and row["kind"] == "EVENT" and row["taint"] == "CHILD_SUBMISSION", "not own admitted event; control/fixture forbidden")
        if session.stage == "NEW":
            require(any(row in session._events for row in events), "NEW LINK must include own NEW event")
        first, second = (row["fields"] for row in events)
        fields = parse_link_line(raw)
        expected = dict(link=fresh_id, first=first["event"], second=second["event"], via=first["destination"],
                        receipt_first=first["receipt"], receipt_second=second["receipt"])
        require(first["destination"] == second["source"] and fields == expected, "not exact directly chained events")
        require([receipt["receipt"] for receipt in receipts] == [first["receipt"], second["receipt"]], "receipt splice/order differs")
        require(all((row["fields"]["first"], row["fields"]["second"]) != (fields["first"], fields["second"]) for row in session._links), "duplicate pair")
        row = _row(raw, session._cell.root.label, "CHILD_SUBMISSION",
                   {"event_sha256": [row["sha256"] for row in events], "receipt_sha256": [receipt["sha256"] for receipt in receipts],
                    "generation_sha256": byte_hash(raw), "byte_start": 0, "byte_end": len(raw.encode("utf-8")), "native_generation_verified": False,
                    "fixture_only": session._fixture_only})
        session._links.append(detached(row))
        return row
    return _admission(raw, "LINK", admit)


def formation_report(admissions, expected_events=8, expected_links=4, required_bank=None):
    require(type(expected_events) is int and type(expected_links) is int and expected_events >= 0 and expected_links >= 0, "invalid scheduled denominators")
    identities = set()
    for item in admissions:
        require(type(item["accepted"]) is bool and item["generation_sha256"] == byte_hash(item["raw"]), "admission bytes/status differ")
        if item["accepted"]:
            validate_row(item["row"])
            require(item["row"]["raw"] == item["raw"] and item["row"]["taint"] == "CHILD_SUBMISSION", "not exact child submission")
            fields = item["row"]["fields"]
            identity = fields.get("event", fields.get("link"))
            require(identity not in identities, "duplicate admitted address in formation report")
            identities.add(identity)
    attempted = Counter(item["kind"] for item in admissions)
    require(set(attempted) <= {"EVENT", "LINK"}, "unknown admission kind")
    accepted = Counter(item["kind"] for item in admissions if item["accepted"])
    link_denominator = max(expected_links, attempted["LINK"])
    structural_complete = attempted == Counter(EVENT=expected_events, LINK=expected_links) and accepted == attempted
    bank_missing, bank_different, bank_extra = [], [], []
    if required_bank is not None:
        require(type(required_bank) is dict and len(required_bank) == expected_events + expected_links, "presealed bank cardinality differs")
        bank_kinds = Counter()
        for identity, fields in required_bank.items():
            require(type(fields) is dict, "typed bank fields required")
            if "event" in fields:
                require(set(fields) == {"event", "source", "port", "destination", "receipt"} and fields["event"] == identity, "bank EVENT fields differ")
                parse_event_line(EVENT_WIRE.format(**fields))
                bank_kinds["EVENT"] += 1
            else:
                require(set(fields) == {"link", "first", "second", "via", "receipt_first", "receipt_second"} and fields["link"] == identity, "bank LINK fields differ")
                parse_link_line(LINK_WIRE.format(**fields))
                bank_kinds["LINK"] += 1
        require(bank_kinds == Counter(EVENT=expected_events, LINK=expected_links), "bank kind counts differ")
        actual = {item["row"]["fields"].get("event", item["row"]["fields"].get("link")): item["row"]["fields"]
                  for item in admissions if item["accepted"]}
        bank_missing = sorted(set(required_bank) - set(actual))
        bank_extra = sorted(set(actual) - set(required_bank))
        bank_different = sorted(identity for identity in set(required_bank) & set(actual) if required_bank[identity] != actual[identity])
    bank_verified = required_bank is not None and not (bank_missing or bank_extra or bank_different)
    return {"scheduled_events": expected_events, "scheduled_links": expected_links,
            "attempted_events": attempted["EVENT"], "attempted_links": attempted["LINK"],
            "accepted_events": accepted["EVENT"], "accepted_links": accepted["LINK"],
            "missing_calls": max(0, expected_events-attempted["EVENT"]) + max(0, expected_links-attempted["LINK"]),
            "link_precision": [accepted["LINK"], link_denominator],
            "structural_complete": structural_complete, "required_bank_verified": bank_verified,
            "required_bank_sha256": digest(required_bank) if required_bank is not None else None,
            "bank_missing": bank_missing, "bank_different": bank_different, "bank_extra": bank_extra,
            "formation_complete": structural_complete and bank_verified,
            "status": "CPU_FORMATION_BANK_PASS" if structural_complete and bank_verified else
                      ("REQUIRED_BANK_UNBOUND" if required_bank is None else "VS_FORMATION_BANK_MISMATCH"),
            "native_generation_verified": False}


def materialize_queries(rows):
    require(type(rows) in (tuple, list), "finite row sequence required")
    groups, identities = defaultdict(list), set()
    for row in rows:
        validate_row(row)
        fields = row["fields"]
        identity = fields["event"] if row["kind"] == "EVENT" else fields["link"]
        require(identity not in identities, "duplicate row address")
        identities.add(identity)
        requests = ["READ EVENT " + identity, "READ EVENTS_AT " + fields["source"]] if row["kind"] == "EVENT" else ["READ LINKS_FROM " + fields["first"]]
        for request in requests:
            groups[request].append(row)
    require(len({row["root"] for row in rows}) <= 1, "mixed root corpus")
    queries = {}
    for request, members in sorted(groups.items()):
        members.sort(key=lambda row: row["fields"].get("event", row["fields"].get("link")))
        require(len(members) <= 2, "maximum adjacency exceeded")
        target = "".join(row["raw"] for row in members)
        queries[request] = {"request": request, "target": target, "target_sha256": byte_hash(target),
                            "support": [row["fields"].get("event", row["fields"].get("link")) for row in members],
                            "source_sha256": [row["sha256"] for row in members], "taint": sorted({row["taint"] for row in members})}
    return queries


def _block_rows(raw):
    require(type(raw) is str and raw.endswith("\n") and raw != "\n", "nonempty terminal-LF block required")
    rows = raw.splitlines(keepends=True)
    kinds = []
    for row in rows:
        if row.startswith("EVENT "):
            parse_event_line(row)
            kinds.append("EVENT")
        else:
            parse_link_line(row)
            kinds.append("LINK")
    require(len(set(kinds)) == 1 and len(rows) <= 2, "mixed/oversized block")
    return rows, kinds[0]


def score_memory_response(raw, expected):
    require(type(raw) is str and (expected is None or type(expected) is str), "raw/expected text required")
    expected_rows = [] if expected is None else _block_rows(expected)[0]
    allowed = set(expected_rows)
    false_rows = []
    for kind in ("EVENT", "LINK"):
        pattern = PATTERNS[kind][:-2]
        for match in re.finditer(r"(?<![A-Za-z0-9_])" + pattern + r"(?![A-Za-z0-9_])", raw):
            candidate = match.group(0) + "\n"
            if candidate not in allowed:
                false_rows.append(candidate)
    semantic = False
    if expected is not None:
        candidates = {expected, expected[:-1]}
        for opener in ("```\n", "```text\n"):
            candidates.update((opener + expected + "```", opener + expected + "```\n"))
        semantic = raw in candidates
    return {"strict": expected is not None and raw == expected, "semantic": semantic,
            "refusal": raw in ("MISS", "MISS\n"), "usable_false_row": bool(false_rows),
            "false_rows": false_rows}


def make_event_twin(rows, root):
    """Other coherent OLD world: swap a0/a1 on S_L event atoms only."""
    result = []
    for row in rows:
        validate_row(row)
        require(row["root"] == root.label, "control root differs")
        fields = dict(row["fields"])
        if row["kind"] == "EVENT" and fields["source"] == root.lookup("node", "S_L"):
            choices = [root.lookup("port", slot) for slot in ("a0", "a1")]
            require(fields["port"] in choices, "unexpected OLD port")
            fields["port"] = choices[1-choices.index(fields["port"]) ]
        raw = (EVENT_WIRE if row["kind"] == "EVENT" else LINK_WIRE).format(**fields)
        result.append(_row(raw, root.label, "CONTROL", {"control": "EVENT_TWIN", "source_sha256": row["sha256"], "source_taint": row["taint"]}))
    return result


def make_link_permute(rows, root):
    links = {row["fields"]["link"]: row for row in rows if row["kind"] == "LINK"}
    mapping = (2, 3, 0, 1)
    required = [root.lookup("link", f"l{index}") for index in range(4)]
    require(set(required) <= set(links), "four old links required")
    for index, (first, second, via) in enumerate(LINK_PAIRS[:4]):
        fields = links[required[index]]["fields"]
        require((fields["first"], fields["second"], fields["via"]) ==
                (root.lookup("event", f"e{first}"), root.lookup("event", f"e{second}"), root.lookup("node", via)),
                "LINK_PERMUTE requires prebound structural bank; no inferred relabeling of live chronology")
    result = []
    for row in rows:
        validate_row(row)
        require(row["root"] == root.label, "control root differs")
        fields = dict(row["fields"])
        if row["kind"] == "LINK" and fields["link"] in required:
            donor = links[required[mapping[required.index(fields["link"])]]]["fields"]
            for key in ("second", "via", "receipt_second"):
                fields[key] = donor[key]
        raw = (EVENT_WIRE if row["kind"] == "EVENT" else LINK_WIRE).format(**fields)
        result.append(_row(raw, root.label, "CONTROL", {"control": "LINK_PERMUTE", "source_sha256": row["sha256"], "source_taint": row["taint"]}))
    return result


def cut_queries(queries, root, cut):
    require(cut in ("OLD", "NEW", "LINK"), "unknown read cut")
    carrier = root.lookup("event", "e0" if cut == "OLD" else "e8") if cut != "LINK" else None
    result = detached(queries)
    affected = []
    for request, query in result.items():
        rows, kind = _block_rows(query["target"])
        if cut == "LINK":
            touched = kind == "LINK"
        else:
            touched = any(carrier in ((parse_event_line(row)["event"],) if kind == "EVENT" else
                                     (parse_link_line(row)["first"], parse_link_line(row)["second"])) for row in rows)
        if touched:
            query["uncut_target_sha256"] = query["target_sha256"]
            query["target"] = "MISS"
            query["target_sha256"] = byte_hash("MISS")
            query["intervention"] = cut
            affected.append(request)
    return {"queries": result, "affected": sorted(affected), "cut": cut, "carrier": carrier,
            "role": "EVALUATION_ONLY_NOT_TRAINING", "source_sha256": digest(queries)}


def paired_cuts(cell, goal, rows):
    queries = materialize_queries(rows)
    return {"task": render_task(cell, goal, "ACTIVE_LINKED_TEXT"), "uncut": queries,
            "cuts": {cut: cut_queries(queries, cell.root, cut) for cut in ("OLD", "NEW", "LINK")},
            "expected_graph": {cut: oracle_routes_v2(cell, goal, cut) != () for cut in ("OLD", "NEW")},
            "link_information_necessary": False, "role": "EVALUATION_ONLY_NOT_TRAINING"}


def render_views(cell, goal, rows, wrong_rows, *, fixture_only=False):
    return {name: render_task(cell, goal, name, rows=rows, wrong_rows=wrong_rows, fixture_only=fixture_only) for name in PROJECTIONS}


def read_query(queries, request):
    parse_read(request)
    if request not in queries:
        return {"request": request, "raw": "MISS", "source_sha256": [], "role": "CEILING_SERVICE_ONLY"}
    query = queries[request]
    require(query["request"] == request and byte_hash(query["target"]) == query["target_sha256"], "query bytes differ")
    if "intervention" in query:
        require(query["target"] == "MISS" and query["intervention"] in ("OLD", "NEW", "LINK"), "invalid cut replacement")
        return {"request": request, "raw": "MISS", "source_sha256": [], "role": "EVALUATION_CUT_ONLY"}
    raw_rows, kind = _block_rows(query["target"])
    fields = [parse_event_line(raw) if kind == "EVENT" else parse_link_line(raw) for raw in raw_rows]
    operation, address = parse_read(request)
    field = {"EVENT": "event", "EVENTS_AT": "source", "LINKS_FROM": "first"}[operation]
    require((kind == "LINK") == (operation == "LINKS_FROM") and all(row[field] == address for row in fields), "query target answers a different address")
    identities = [row["event"] if kind == "EVENT" else row["link"] for row in fields]
    require(identities == sorted(set(identities)) and identities == query["support"], "query order/support differs")
    require(query["source_sha256"] == [byte_hash(raw) for raw in raw_rows], "query source byte hash differs")
    return {"request": request, "raw": query["target"], "source_sha256": list(query["source_sha256"]),
            "role": "CEILING_SERVICE_ONLY"}


def routes_from_rows(rows, start, goal, use_links=False):
    events, links = {}, defaultdict(set)
    for row in rows:
        validate_row(row)
        fields = row["fields"]
        if row["kind"] == "EVENT":
            require(fields["event"] not in events, "duplicate EVENT")
            events[fields["event"]] = fields
        else:
            links[fields["first"]].add(fields["second"])
    pending = [(start, (start,), (), None)]
    routes = []
    while pending:
        current, visited, ports, previous = pending.pop()
        if current == goal:
            routes.append(format_route(start, goal, ports))
            continue
        for event_id, fields in events.items():
            if fields["source"] != current or fields["destination"] in visited:
                continue
            if use_links and previous is not None and event_id not in links[previous]:
                continue
            pending.append((fields["destination"], visited + (fields["destination"],), ports + (fields["port"],), event_id))
    return tuple(sorted(routes))


def diagnostic_registry(queries, candidate_blocks):
    universe = sorted(set(candidate_blocks))
    parsed = {block: _block_rows(block) for block in universe}
    result = {}
    for request, query in queries.items():
        rows, kind = _block_rows(query["target"])
        wrong = [block for block in universe if block != query["target"] and parsed[block][1] == kind and len(parsed[block][0]) == len(rows)]
        require(bool(wrong), "empty eligible wrong-block universe")
        result[request] = [{"target": block, "sha256": byte_hash(block)} for block in wrong]
    return {"role": "SCORER_ONLY_NEVER_PROMPT", "universe_sha256": digest(universe), "addresses": result}


def classify_offsets(target, offsets):
    _block_rows(target)
    opaque = [match.span() for match in re.finditer(r"[NPELQRG]_[A-Z2-7]{10}", target)]
    result = []
    for offset in offsets:
        require(type(offset) in (list, tuple) and len(offset) == 2 and all(type(value) is int for value in offset), "invalid byte offset")
        start, end = offset
        require(0 <= start <= end <= len(target.encode("utf-8")), "offset outside target")
        result.append("content" if any(start < right and end > left for left, right in opaque) else "grammar")
    return result


def registries():
    """Detached literal registry for the separate execution-contract preparer."""
    renders = {name: {"placement": "before_task", "header": "MEMORY\n", "row_separator": "",
                      "task_join": "\n", "task_template": TASK_TEMPLATE, "terminal_lf": False,
                      "row_order": "OLD_EVENTS_e0-e7,OLD_LINKS_l0-l3,NEW_EVENT_e8,NEW_LINKS_l4-l5",
                      "service": name == "ACTIVE_LINKED_TEXT"} for name in PROJECTIONS}
    for name in ("NONE_OFF", "ACTIVE_LINKED_TEXT"):
        renders[name].update(header="", task_join="", row_order="none")
    renders["EXACT_WITNESSED_GRAPH"]["row_template"] = "EDGE {source} {port} {destination}\n"
    renders["RAW_EPISODIC"].update(row_template=RECEIPT_WIRE,
        row_order="chronological OLD actions/receipts,PROBE/result,NEW action/receipt",
        action_join="{action}\n{public_result}", origin="HARNESS_SCRIPTED_CPU_CEILING_NOT_CHILD")
    renders["EVENT_ATOMS_TEXT"]["selection"] = "EVENT only"
    renders["OLD_ONLY_TEXT"]["selection"] = "e0-e7,l0-l3"
    renders["NEW_ONLY_TEXT"]["selection"] = "e8 only; no OLD-dependent LINK fields"
    renders["WRONG_ROOT"].update(selection="one distinct root; caller prebinds counterpart",
                                row_order="exact caller-presealed counterpart sequence; 9 EVENT and 6 LINK unique rows")
    return detached({
        "schema": SCHEMA, "source_pins": SOURCE_PINS,
        "root_schema": {"labels": list(ROOT_LABELS), "slots": {key: list(value) for key, value in SLOTS.items()},
                        "prefixes": PREFIXES, "seed_prefix": "PCFL-V2.1-PREP\u0000", "tokenizer_qualified": False,
                        "dev_realized_old": [0, 1], "dev_canonical_relevant": [0, 1], "dev_primary_reachout": ["RA", "RB"]},
        "world_registry": {"old_sources": list(OLD_SOURCES), "visible_port_order": list(SLOTS["port"]),
                           "probe_endpoints": [["H", "S_R"], None], "probe_result": None,
                           "distractor": production_binding_status(),
                           "receipt": RECEIPT_WIRE, "probe_receipt_slots": None,
                           "fresh_handles": "chronological e0..e7 then e8; l0..l3 then l4,l5",
                           "ideal_edge_handles_not_live_chronology": True},
        "render_registry": {"projections": renders, "wrappers": {f"W{index}": wrapper for index, wrapper in enumerate(WRAPPERS)},
                            "systems": dict(memory=MEMORY_SYSTEM, modular=MODULAR_SYSTEM, native=NATIVE_SYSTEM,
                                            formation=FORMATION_SYSTEM, reachout=REACHOUT_SYSTEM),
                            "prompts": dict(task=TASK_TEMPLATE, explore=EXPLORE_TEMPLATE, event=EVENT_TEMPLATE,
                                            link=LINK_TEMPLATE, **REACHOUT_TEMPLATES),
                            "retention": {"projection": "NATIVE_CONTEXT", "template": TASK_TEMPLATE, "items": 64},
                            "substitution_classes": dict(START_ID="node", GOAL_ID="node", REQUEST="strict READ",
                                                         SOURCE_ID="node", FRESH_EVENT_ID="event", FRESH_LINK_ID="link",
                                                         COMMA_SEPARATED_PUBLIC_PORT_IDS="listed unique ports in structural order"),
                            "no_memory_join": TASK_TEMPLATE},
        "parser_registry": {"fullmatch_patterns": PATTERNS, "strict_memory": "exact target UTF-8 bytes",
                            "semantic": {"bare": "canonical rows with optional final LF", "fence_open": ["```\n", "```text\n"],
                                         "fence_close": ["```", "```\n"], "row_body": "exact canonical terminal-LF block",
                                         "no_prose_extra_missing_duplicate_reordered_rows": True},
                            "refusals": ["MISS", "MISS\n"], "false_row": "any parsable EVENT/LINK span not in expected rows even alongside prose/refusal",
                            "event_template": EVENT_WIRE, "link_template": LINK_WIRE},
        "intervention_registry": {"graph_cuts": {"OLD": "e0", "NEW": "e8"},
                                  "read_cuts": {"OLD": "all blocks containing e0 EVENT or incident LINK", "NEW": "all blocks containing e8 EVENT or incident LINK", "LINK": "all LINK blocks"},
                                  "paired": "same task/generation seed; unchanged uncut blocks; no training of MISS",
                                  "event_twin": "swap a0/a1 on S_L EVENT fields; other OLD fields unchanged",
                                  "link_permute_tail_donors": [2, 3, 0, 1], "derivative_taint": "CONTROL"},
    })


def validate_registries(value):
    require(value == registries(), "core registry literal/schema drift")
    return True


def audit_construct(roots):
    require(len(roots) == 4 and {root.label for root in roots} == {f"excluded/{index}" for index in range(4)}, "four distinct excluded roots required")
    all_ids = [identifier for root in roots for _, entries in root.inventory for _, identifier in entries]
    require(len(all_ids) == len(set(all_ids)), "cross-root ID collision")
    checks, atoms, link_support, quartets, projections = [], [], [], [], defaultdict(list)
    for root in roots:
        for old in (0, 1):
            for goal in (0, 1):
                quartet = [cell for cell in expand_cube(root) if cell.old == old]
                before = [render_reachout(cell, goal, fixture_only=True) + "\n" + render_task(cell, goal, "OLD_ONLY_TEXT", rows=ideal_rows(cell))["user"] for cell in quartet]
                require(len(set(before)) == 1, "pre-outcome visible bytes leak R/D")
                labels = [oracle_route_v1(cell, goal) for cell in quartet]
                require(all(len({labels[index] for index, cell in enumerate(quartet) if cell.relevant == relevant}) == 1 for relevant in (0, 1)), "R not sufficient within quartet")
                require(all(len({labels[index] for index, cell in enumerate(quartet) if cell.distractor == distractor}) == 2 for distractor in (0, 1)), "D informative within quartet")
                quartets.append({"root": root.label, "old": old, "goal": goal, "table": [[cell.relevant, cell.distractor] for cell in quartet],
                                  "bits": [1, 1, 1, 0], "pre_outcome_sha256": byte_hash(before[0])})
            cell = WorldCell(root, old, 0, 0)
            rows = ideal_rows(cell)[:12]
            fixture = ceiling_fixture(cell)
            receipt_edges = tuple(Edge(str(index), receipt["source"], receipt["port"], receipt["destination"], receipt["receipt"])
                                  for index, receipt in enumerate(fixture["receipts"]) if receipt["stage"] == "OLD")
            for goal in ("old_left", "old_right"):
                route = oracle_route_v1(cell, goal)
                start, target = _task_nodes(cell, goal)
                outcomes = {"receipts": execute_route(receipt_edges, parse_route(route))["graph_success"],
                            "EVENT": routes_from_rows(rows, start, target) == (route,),
                            "EVENT_LINK": routes_from_rows(rows, start, target, True) == (route,)}
                require(all(outcomes.values()), "old receipt/atom/link projection mismatch")
                atoms.extend({"root": root.label, "old": old, "goal": goal, "projection": projection, "success": success}
                             for projection, success in outcomes.items())
            events = {row["fields"]["event"]: row["fields"] for row in rows if row["kind"] == "EVENT"}
            for row in rows[8:]:
                first = events[row["fields"]["first"]]
                successors = sorted(event_id for event_id, fields in events.items() if fields["source"] == first["destination"])
                require(row["fields"]["second"] in successors, "unsupported LINK fixture")
                link_support.append({"root": root.label, "old": old, "link": row["fields"]["link"],
                                     "successors": successors, "count": len(successors), "derivable": len(successors) == 1})
        for cell in expand_cube(root):
            for goal in (0, 1):
                route = oracle_route_v1(cell, goal)
                require(oracle_routes_v2(cell, goal) == (route,), "independent oracles disagree")
                for cut in (None, "OLD", "NEW"):
                    result = score_route(cell, goal, route, cut)
                    require(result["graph_success"] == (cut is None), "route/cut mismatch")
                    require(oracle_routes_v2(cell, goal, cut) == (() if cut else (route,)), "cut oracle mismatch")
                    checks.append({"root": root.label, "old": cell.old, "relevant": cell.relevant, "distractor": cell.distractor,
                                   "goal": goal, "cut": cut, "success": result["graph_success"]})
                rows = ideal_rows(cell)
                for projection in ("OLD_ONLY_TEXT", "NEW_ONLY_TEXT", "NONE_OFF"):
                    public = render_task(cell, goal, projection, rows=rows)
                    projections[projection].append((digest(public), route))
    ceilings = {}
    for projection, entries in projections.items():
        groups = defaultdict(Counter)
        for public_hash, route in entries:
            groups[public_hash][route] += 1
        ceilings[projection] = {"groups": len(groups), "covered": len(entries),
                                "bayes_correct": sum(max(counts.values()) for counts in groups.values()),
                                "minimum_labels": min(len(counts) for counts in groups.values())}
        require(ceilings[projection]["bayes_correct"] == (16 if projection == "NONE_OFF" else 32), "projection leaks or drops information")
    return {"schema": SCHEMA, "worlds": 32, "delayed_tasks": 64, "route_cut_decisions": checks,
            "scope": "CPU_FIXTURE_ONLY_NOT_PRODUCTION_D_CERTIFICATE", "production_binding": production_binding_status(),
            "projection_ceilings": ceilings, "route_construct_passed": True,
            "atoms_link_decisions": atoms, "link_successor_support": link_support, "entropy_quartets": quartets,
            "full_construct_passed": False, "ready_for_model_calls": False,
            "remaining": ["production D topology/probe-result/receipt/port bindings", "tokenizer-qualified inventories", "complete rendered shortcut certificate",
                          "prepared render/diagnostic/schedule/cut contract", "native custody and runtime binding", "model ceiling tests"]}
