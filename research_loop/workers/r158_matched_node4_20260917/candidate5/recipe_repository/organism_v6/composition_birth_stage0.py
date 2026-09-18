"""External-authored CPU source fixture, not birth material or a launch gate.

Only the staged memo's explicit tiny-interface topology is generated. Rich
train/DEV/confirmation/writer worlds remain disabled. This does not install or
demonstrate model composition skills. No scored model output is consumed.

The EVENT wire spelling is recovered from the public pcfl_vertical_dev interface;
that module is deliberately NOT imported (it also contains target-world data).
Actor turns have exactly one terminal LF; the static grammar applies to its body.
Synthetic oracle calls count one placeholder token each, never tokenizer evidence.
"""

from __future__ import annotations

import base64
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations, product
import json
import re


PROVENANCE = "external_authored_synthetic_cpu_only"
SEED = "composition-birth-stage0/2026-09-13/v1"
DOMAINS = (
    "tiny_interface_dev", "birth_train", "birth_dose_dev",
    "birth_confirmation", "writer_dev", "writer_release",
)
DISABLED_DOMAINS = DOMAINS[1:]
ACTION_PATTERN = (
    r"(?:THINK [^\r\n]*[^\s\r\n][^\r\n]*"
    r"|READ (?:EVENT E_[A-Z2-7]{10}|EVENTS_AT N_[A-Z2-7]{10}"
    r"|LINKS_FROM E_[A-Z2-7]{10})|STEP P_[A-Z2-7]{10}|STOP)"
)
EVENT_PATTERN = (
    r"EVENT (E_[A-Z2-7]{10}) AT (N_[A-Z2-7]{10}) DID (P_[A-Z2-7]{10})"
    r" GOT (N_[A-Z2-7]{10}) EVIDENCE (R_[A-Z2-7]{10})\n"
)
LIMITS = {"THINK": 4, "READ": 3, "STEP": 2, "STOP": 1}
TOKEN_CAP = 1536
NULL_NAMES = (
    "constant_action", "lexicographic_action", "first_displayed_row",
    "direct_goal", "local_outdegree", "link_presence", "action_position",
    "fixed_read_schedule", "fixed_stop_depth",
)
PAIRWISE_NULLS = tuple(combinations(NULL_NAMES, 2))
NULL_INTERPRETATIONS = {
    "constant_action": "Always STEP P_AAAAAAAAAA, independent of task and service.",
    "lexicographic_action": "Choose least port at first choice; exact-row-assisted suffix.",
    "first_displayed_row": "Choose first returned row; exact-row-assisted suffix.",
    "direct_goal": "Prefer an immediate goal, else first row; exact-row-assisted suffix.",
    "local_outdegree": "Prefer smallest child outdegree, ties first row; assisted suffix.",
    "link_presence": "No LINK rows exist in tiny worlds; tie first row; assisted suffix.",
    "action_position": "Choose displayed position zero; exact-row-assisted suffix.",
    "fixed_read_schedule": "READ start then both children in lexical order; oracle choice.",
    "fixed_stop_depth": "Oracle READ/STEP choice; always STOP after two STEPs.",
}
SEAMS = (
    "Rich three-family generators, fourth held family, remainder rotation and "
    "C/S target-length/batch coupling are not concretely bound; no birth units emitted.",
    "Pairwise null composition/tie rules are unspecified; all 36 pairs disabled.",
    "Fixed READ/STOP ablations are diagnostic interpretations, not registered nulls: "
    "reading start and both children and stopping at depth two can solve all tiny tasks.",
    "Tiny two-corridor topology conflicts with the original blanket exclusion; "
    "kept tiny-interface-only, never copied to birth train/DEV/test.",
    "Cross-domain content/core and forbidden-spec motif exclusion are unverified; "
    "reserved namespaces are not proof of topology disjointness.",
    "Token totals require a separately authorized tokenizer/runner; CPU counts are synthetic.",
)


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def identifier(prefix, world_id, slot):
    payload = f"{SEED}/{world_id}/{prefix}/{slot}".encode()
    return prefix + "_" + base64.b32encode(sha256(payload).digest()).decode()[:10]


def parse_action(raw):
    if (type(raw) is not str or not raw.endswith("\n")
            or re.fullmatch(ACTION_PATTERN, raw[:-1]) is None):
        raise ValueError("malformed_action")
    return raw[:-1].split(" ", 1)[0], raw[:-1]


@dataclass(frozen=True)
class Event:
    event: str
    source: str
    port: str
    destination: str
    receipt: str

    @property
    def raw(self):
        return (f"EVENT {self.event} AT {self.source} DID {self.port} "
                f"GOT {self.destination} EVIDENCE {self.receipt}\n")


def parse_events(raw):
    if raw == "MISS":
        return ()
    events = []
    for line in raw.splitlines(keepends=True):
        match = re.fullmatch(EVENT_PATTERN, line)
        if match is None:
            raise ValueError("malformed_service_row")
        events.append(Event(*match.groups()))
    return tuple(events)


@dataclass(frozen=True)
class Task:
    world_id: str
    structure_id: str
    task_id: str
    start: str
    goal: str
    events: tuple[Event, ...]
    crossings: tuple[int, ...]
    goal_side: int
    domain: str = DOMAINS[0]
    provenance: str = PROVENANCE

    @property
    def prompt(self):
        return f"START {self.start}\nGOAL {self.goal}\nCURRENT {self.start}\n"


def generate(domain=DOMAINS[0]):
    """One fixed-seed 16-pair factorial, with no acceptance-driven retries."""
    if domain not in DOMAINS:
        raise ValueError("unknown_domain")
    if domain != DOMAINS[0]:
        raise ValueError("disabled_unbound_material_domain")
    tasks = []
    for pair_index, crossings in enumerate(product((0, 1), repeat=4)):
        port_swap, node_swap, goal_swap, row_swap = crossings
        world_id = f"{domain}/world/{pair_index:02d}"
        nodes = sorted(identifier("N", world_id, slot) for slot in range(5))
        ports = sorted(identifier("P", world_id, slot) for slot in range(4))
        start = nodes[2]
        children = (nodes[node_swap], nodes[1 - node_swap])
        goals = (nodes[3 + goal_swap], nodes[4 - goal_swap])
        edges = ((start, ports[port_swap], children[0]),
                 (start, ports[1 - port_swap], children[1]),
                 (children[0], ports[2], goals[0]),
                 (children[1], ports[3], goals[1]))
        events = tuple(Event(identifier("E", world_id, index), source, port,
                             destination, identifier("R", world_id, index))
                       for index, (source, port, destination) in enumerate(edges))
        if row_swap:
            events = tuple(reversed(events))
        for goal_side, goal in enumerate(goals):
            tasks.append(Task(world_id, f"{domain}/structure/{pair_index:02d}",
                              f"{world_id}/goal/{goal_side}", start, goal, events,
                              crossings, goal_side))
    return tuple(tasks)


class ExactMemory:
    """Passive registered lookups only; no goal input, path search or fallback."""

    def __init__(self, events):
        self._blocks = {}
        for event in events:
            request = "READ EVENT " + event.event
            if request in self._blocks:
                raise ValueError("duplicate_event")
            self._blocks[request] = event.raw
            index = "READ EVENTS_AT " + event.source
            self._blocks[index] = self._blocks.get(index, "") + event.raw

    def read(self, raw):
        operation, body = parse_action(raw)
        if operation != "READ":
            raise ValueError("not_read")
        return self._blocks.get(body, "MISS")


class Session:
    """CPU-only irreversible world; invalid turns terminate without repair."""

    def __init__(self, task):
        self._task = task
        self._memory = ExactMemory(task.events)
        self.current = task.start
        self.counts = Counter()
        self.tokens = 0
        self.terminated = False
        self.success = False
        self.reason = None
        self.receipts = []

    def _fail(self, reason):
        self.terminated = True
        self.reason = reason
        return ""

    def turn(self, raw, *, generated_tokens, truncated=False):
        if self.terminated:
            raise ValueError("session_terminated")
        if type(generated_tokens) is not int or generated_tokens < 1:
            return self._fail("invalid_token_accounting")
        self.tokens += generated_tokens
        if truncated:
            return self._fail("length_limited")
        try:
            operation, body = parse_action(raw)
        except ValueError:
            return self._fail("malformed_action")
        self.counts[operation] += 1
        if self.tokens > TOKEN_CAP or self.counts[operation] > LIMITS[operation]:
            return self._fail("over_budget")
        response = ""
        if operation == "READ":
            response = self._memory.read(raw)
        elif operation == "STEP":
            candidates = [event for event in self._task.events
                          if event.source == self.current and event.port == body[5:]]
            if len(candidates) != 1:
                return self._fail("invalid_step")
            self.current = candidates[0].destination
            response = f"CURRENT {self.current}\n"
        elif operation == "STOP":
            self.terminated = True
            self.success = self.current == self._task.goal
            self.reason = "success" if self.success else "premature_stop"
        self.receipts.append((raw, response))
        return response


def scripted_oracle(start, goal, turn, *, null=None):
    """Test-only oracle consumes public task fields and actual service returns.

    Shallow nulls fix the first irreversible choice; the suffix is assisted by
    exact observed rows. Fixed READ schedule and STOP-depth diagnostics retain
    the oracle's relation-based choice. These are not scientific actor policies.
    """
    if null is not None and null not in NULL_NAMES:
        raise ValueError("unknown_null")
    if null == "constant_action":
        turn("STEP P_AAAAAAAAAA\n", generated_tokens=1)
        return
    outgoing = parse_events(turn(f"READ EVENTS_AT {start}\n", generated_tokens=1))
    if len(outgoing) != 2:
        raise ValueError("not_tiny_topology")
    tails = {}
    for event in sorted(outgoing, key=lambda edge: edge.destination):
        tails[event.destination] = parse_events(
            turn(f"READ EVENTS_AT {event.destination}\n", generated_tokens=1))
    if null == "lexicographic_action":
        chosen = min(outgoing, key=lambda edge: edge.port)
    elif null in ("first_displayed_row", "action_position", "link_presence"):
        chosen = outgoing[0]
    elif null == "direct_goal":
        chosen = next((edge for edge in outgoing if edge.destination == goal), outgoing[0])
    elif null == "local_outdegree":
        chosen = min(outgoing, key=lambda edge: len(tails[edge.destination]))
    else:
        chosen = next(edge for edge in outgoing
                      if any(tail.destination == goal for tail in tails[edge.destination]))
    suffix = tails[chosen.destination]
    if len(suffix) != 1:
        raise ValueError("not_tiny_suffix")
    for edge in (chosen, suffix[0]):
        observed = turn(f"STEP {edge.port}\n", generated_tokens=1)
        if observed != f"CURRENT {edge.destination}\n":
            raise ValueError("unexpected_current")
    turn("STOP\n", generated_tokens=1)


def evaluate(tasks, null=None):
    successes = 0
    for task in tasks:
        session = Session(task)
        scripted_oracle(task.start, task.goal, session.turn, null=null)
        successes += session.success
    return successes


def decision_core(task):
    """Canonical role-labelled core computed from rows, never namespace labels."""
    outgoing = sorted((edge for edge in task.events if edge.source == task.start),
                      key=lambda edge: edge.port)
    if len(task.events) != 4 or len(outgoing) != 2:
        raise ValueError("not_tiny_topology")
    roles = {task.start: "start"}
    edge_roles = []
    signatures = []
    for index, edge in enumerate(outgoing):
        tails = [tail for tail in task.events if tail.source == edge.destination]
        if len(tails) != 1:
            raise ValueError("not_tiny_suffix")
        tail = tails[0]
        roles[edge.destination] = f"child_{index}"
        roles[tail.destination] = f"terminal_{index}"
        signatures.append([len(tails), sum(
            candidate.source == tail.destination for candidate in task.events)])
        edge_roles.extend((("start", f"port_{index}", f"child_{index}"),
                           (f"child_{index}", f"port_{index + 2}", f"terminal_{index}")))
    if (len(roles) != 5 or task.goal not in roles
            or not roles[task.goal].startswith("terminal_")
            or signatures != [[1, 0], [1, 0]]
            or len({edge.port for edge in task.events}) != 4):
        raise ValueError("not_tiny_topology")
    return {"edges": sorted(edge_roles), "goal_role": roles[task.goal],
            "rooted_depth_one_signatures": signatures}


def source_report():
    """Partial executable source check; deliberately never emits Stage0 GO."""
    tasks = generate()
    nulls = {name: evaluate(tasks, name) for name in NULL_NAMES}
    panels = []
    for task in tasks:
        rows = "".join(event.raw for event in task.events)
        role_core = decision_core(task)
        panels.append({"task_id": task.task_id, "world_id": task.world_id,
                       "structure_id": task.structure_id,
                       "prompt_bytes": len(task.prompt.encode()),
                       "row_bytes": len(rows.encode()),
                       "prompt_sha256": sha256(task.prompt.encode()).hexdigest(),
                       "rows_sha256": sha256(rows.encode()).hexdigest(),
                       "role_core_sha256": digest(role_core),
                       "rooted_depth_one_signatures": role_core["rooted_depth_one_signatures"]})
    return {
        "status": "NO_GO_PARTIAL_SOURCE_ONLY", "provenance": PROVENANCE,
        "seed": SEED, "model_calls": 0, "fits": 0, "gpu_work": 0,
        "launch_authorized": False, "birth_units_emitted": 0,
        "task_count": len(tasks), "oracle_successes": evaluate(tasks),
        "null_diagnostic_successes": nulls,
        "null_interpretations": NULL_INTERPRETATIONS,
        "registered_null_suite_complete": False,
        "nulls_over_half": [name for name, count in nulls.items() if count * 2 > len(tasks)],
        "disabled_pairwise_nulls": PAIRWISE_NULLS,
        "reserved_domains": DOMAINS, "disabled_domains": DISABLED_DOMAINS,
        "cross_domain_intersections": "UNVERIFIED_NOT_MATERIALIZED",
        "forbidden_motif_overlap": "UNVERIFIED",
        "goal_side_counts": dict(Counter(task.goal_side for task in tasks)),
        "route_depth_counts": {2: len(tasks)},
        "crossing_counts": [dict(Counter(task.crossings[index] for task in tasks))
                            for index in range(4)],
        "manifests": panels, "manifest_sha256": digest(panels), "seams": SEAMS,
    }


if __name__ == "__main__":
    print(json.dumps(source_report(), indent=2, sort_keys=True))
    raise SystemExit(1)
