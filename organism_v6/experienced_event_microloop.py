"""Researcher-authored DEV transitions; not endogenous exploration or lineage.

Callers retain every episode's raw outputs, including failures. These pure
validators check grounding, not whether strings really came from a model.
"""

import base64
import hashlib
import json
import re

from organism_v6.pcfl_vertical_dev import (
    EVENT_TEMPLATE, FORMATION_SYSTEM, MEMORY_SYSTEM, RECEIPT_WIRE, WRAPPERS,
    parse_event_line, parse_explore,
)


FACT_KEYS = frozenset((
    "world", "event", "node", "port", "outcome", "receipt", "public_ports",
    "public_events",
))
ACTION_SYSTEM = (
    "Use only the public task and your own learned memory. Identifiers are opaque "
    "and case-sensitive. You have no external memory tool. Choose the port whose "
    "experienced outcome matches GOAL. Output exactly ROUTE <port> followed by "
    "one newline, with no explanation. There is no retry."
)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _opaque(master, prefix, *address):
    payload = json.dumps(
        ["experienced_event_microloop_DEV_v1", master, prefix, *address],
        separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")
    suffix = base64.b32encode(hashlib.sha256(payload).digest()).decode("ascii")[:10]
    return prefix + "_" + suffix


def _event(fact):
    return (
        f"EVENT {fact['event']} AT {fact['node']} DID {fact['port']} "
        f"GOT {fact['outcome']} EVIDENCE {fact['receipt']}\n"
    )


def _check_fact(fact):
    _require(isinstance(fact, dict) and set(fact) == FACT_KEYS, "invalid fact keys")
    parse_event_line(_event(fact))
    _require(isinstance(fact["world"], str) and re.fullmatch(
        r"W_[A-Z2-7]{10}", fact["world"]), "invalid world")
    for key, prefix, selected in (("public_ports", "P", "port"),
                                  ("public_events", "E", "event")):
        values = fact[key]
        _require(type(values) is list and len(values) == 2, "two public choices required")
        _require(all(isinstance(value, str) and re.fullmatch(
            prefix + r"_[A-Z2-7]{10}", value) for value in values), "invalid public ID")
        _require(len(set(values)) == 2 and fact[selected] in values, "invalid public choices")


def build_bank(master: str) -> list[dict]:
    """One fresh four-fact DEV bank; target display positions alternate 0,1,1,0."""
    _require(type(master) is str and bool(master.strip()), "explicit nonempty master required")
    bank = []
    for world_index in range(2):
        world = _opaque(master, "W", world_index)
        node = _opaque(master, "N", world_index, "source")
        ports = sorted(_opaque(master, "P", world_index, member) for member in range(2))
        events = [_opaque(master, "E", world_index, member) for member in range(2)]
        for member in range(2):
            bank.append(dict(
                world=world, event=events[member], node=node,
                port=ports[member ^ world_index],
                outcome=_opaque(master, "N", world_index, "outcome", member),
                receipt=_opaque(master, "R", world_index, member),
                public_ports=list(ports), public_events=sorted(events),
            ))
    _check_bank(bank)
    return bank


def _check_bank(bank):
    _require(type(bank) is list and len(bank) == 4, "one four-fact bank required")
    for fact in bank:
        _check_fact(fact)
    worlds = {fact["world"] for fact in bank}
    _require(len(worlds) == 2, "two worlds required")
    for world in worlds:
        pair = [fact for fact in bank if fact["world"] == world]
        _require(len(pair) == 2 and pair[0]["node"] == pair[1]["node"], "invalid world pair")
        for public, field in (("public_ports", "port"), ("public_events", "event")):
            _require(pair[0][public] == pair[1][public] and
                     set(pair[0][public]) == {fact[field] for fact in pair},
                     "pair display differs from bank")
    for key in ("event", "port", "outcome", "receipt"):
        _require(len({fact[key] for fact in bank}) == 4, "duplicate " + key)
    sources = {fact["node"] for fact in bank}
    _require(len(sources) == 2 and not sources.intersection(
        fact["outcome"] for fact in bank), "source/outcome collision")


def exploration_messages(fact) -> list[dict]:
    """Externally scheduled singleton offer, without its hidden outcome."""
    _check_fact(fact)
    return [
        dict(role="system", content=FORMATION_SYSTEM),
        dict(role="user", content=(
            f"EXPLORE TASK\nSOURCE {fact['node']}\nAVAILABLE PORTS {fact['port']}\n"
            "Only this source/port tuple is offered. Output exactly "
            "EXPLORE <source> <port> with no trailing newline or other text."
        )),
    ]


def _check_explore(fact, raw):
    _require(parse_explore(raw) == (fact["node"], fact["port"]), "unoffered EXPLORE")


def observation_messages(fact, actual_explore) -> list[dict]:
    """Emit the DEV transition receipt only after the offered action was taken."""
    messages = exploration_messages(fact)
    _check_explore(fact, actual_explore)
    receipt = RECEIPT_WIRE.format(
        receipt=fact["receipt"], source=fact["node"], port=fact["port"],
        destination=fact["outcome"],
    )
    messages.extend([
        dict(role="assistant", content=actual_explore),
        dict(role="user", content=receipt + EVENT_TEMPLATE.replace(
            "{FRESH_EVENT_ID}", fact["event"]) + "\nEnd the EVENT with exactly one newline."),
    ])
    return messages


def validate_episode(fact, exploration_raw, event_raw) -> bool:
    """Return True only for grounded outputs; every invalid episode raises ValueError."""
    _check_fact(fact)
    _check_explore(fact, exploration_raw)
    observed = parse_event_line(event_raw)
    _require(observed == dict(
        event=fact["event"], source=fact["node"], port=fact["port"],
        destination=fact["outcome"], receipt=fact["receipt"],
    ), "EVENT is not grounded in the observed transition")
    return True


def compile_rows(bank, episodes) -> list[dict]:
    """Episodes: fact, exploration generation, event generation (or None).

    Require all four attempts so failures cannot disappear from the denominator.
    Failed outputs produce no rows. Missing/unknown/duplicate source records raise.
    Success produces eight W0-W7 rows; targets are the actual unmodified raw text.
    Rows are wrapper-major, then bank order, keeping four distinct facts per
    batch of four when all attempts succeed.
    """
    _check_bank(bank)
    _require(type(episodes) is list and len(episodes) == 4, "retain all four attempts")
    indexed = {}
    for episode in episodes:
        _require(isinstance(episode, dict) and all(key in episode for key in (
            "fact", "exploration", "event")), "unsourced episode")
        _check_fact(episode["fact"])
        identity = episode["fact"]["event"]
        _require(isinstance(identity, str) and identity not in indexed, "duplicate/invalid episode")
        indexed[identity] = episode
    _require(set(indexed) == {fact["event"] for fact in bank}, "episode bank mismatch")
    rows = []
    for fact in bank:
        episode = indexed[fact["event"]]
        _require(episode["fact"] == fact, "episode fact differs from bank")
        generations = (episode["exploration"], episode["event"])
        for generation in generations:
            _require(generation is None or (isinstance(generation, dict) and
                     all(key in generation for key in ("raw", "terminal", "truncated"))),
                     "unsourced generation")
        if any(generation is None or generation["terminal"] is not True or
               generation["truncated"] is not False for generation in generations):
            continue
        try:
            validate_episode(fact, episode["exploration"]["raw"], episode["event"]["raw"])
        except ValueError:
            continue
        for wrapper_index, wrapper in enumerate(WRAPPERS[:8]):
            rows.append(dict(
                world=fact["world"], event=fact["event"], wrapper=f"W{wrapper_index}",
                messages=[
                    dict(role="system", content=MEMORY_SYSTEM),
                    dict(role="user", content=wrapper.format(REQUEST="READ EVENT " + fact["event"])),
                    dict(role="assistant", content=episode["event"]["raw"]),
                ],
            ))
    bank_index = {fact["event"]: index for index, fact in enumerate(bank)}
    return sorted(rows, key=lambda row: (int(row["wrapper"][1:]), bank_index[row["event"]]))


def action_messages(fact, memory_text=None, *, ceiling=False) -> list[dict]:
    """memory_text is caller-supplied actual model-read text, never synthesized.

    ceiling=True instead requires caller-supplied exact facts for BOTH ports and
    labels the condition explicitly; it never falls back to expected text.
    """
    _check_fact(fact)
    _require(memory_text is None or type(memory_text) is str, "memory text must be raw text")
    if ceiling:
        _require(memory_text is not None, "ceiling requires explicit exact-facts text")
        fields = [parse_event_line(line) for line in memory_text.splitlines(keepends=True)
                  if line != "\n"]
        _require(len(fields) == 2 and {row["event"] for row in fields} == set(fact["public_events"])
                 and {row["port"] for row in fields} == set(fact["public_ports"])
                 and all(row["source"] == fact["node"] for row in fields)
                 and _event(fact) in memory_text.splitlines(keepends=True), "invalid ceiling pair")
    prompt = (
        f"ROUTE TASK\nSTART {fact['node']}\nGOAL {fact['outcome']}\n"
        f"AVAILABLE PORTS {','.join(fact['public_ports'])}\n"
        f"EVENT ADDRESSES {','.join(fact['public_events'])}\n"
        "Lists are unordered sets, not corresponding rows. Use remembered EVENT "
        "facts to choose the port. Required final grammar: ROUTE <port> followed by one newline."
    )
    if memory_text is not None:
        label = "EXACT-FACTS CEILING" if ceiling else "ACTUAL MODEL-READ TEXT"
        prompt += f"\n{label}\n" + memory_text
    return [dict(role="system", content=ACTION_SYSTEM), dict(role="user", content=prompt)]


def expected_action(fact) -> str:
    """Researcher-only scoring target; never inserted into a native task prompt."""
    _check_fact(fact)
    return f"ROUTE {fact['port']}\n"


def parse_action(raw) -> str:
    """Short diagnostic grammar; deliberately distinct from PCFL multi-hop ROUTE."""
    _require(type(raw) is str, "raw action text required")
    match = re.fullmatch(r"ROUTE (P_[A-Z2-7]{10})\n", raw)
    _require(match is not None, "not exact short ROUTE")
    return match.group(1)
