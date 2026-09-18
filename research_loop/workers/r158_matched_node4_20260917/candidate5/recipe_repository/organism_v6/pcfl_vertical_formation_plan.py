"""Pre-output OLD structure only; never manufacture child memory targets.

The caller must retain the seal before generation. CPU replay cannot establish
that chronology or native custody, and this is not an execution contract.
"""

from collections import defaultdict
from hashlib import sha256
from pathlib import Path

from organism_v6 import pcfl_vertical_dev as core
from organism_v6 import pcfl_vertical_prepare as prepare


SCHEMA = "pcfl_old_formation_plan_v1"
PURPOSE = "EXPECTED_STRUCTURE_NOT_CHILD_TARGETS_OR_TRAINING_MATERIAL"


def source_pins():
    """Byte pins, checked again on binding; no source snapshots are modified."""
    return {name: sha256(Path(path).read_bytes()).hexdigest() for name, path in (
        ("planner", __file__), ("core", core.__file__), ("preparer", prepare.__file__))}


def _strings(values, count, name):
    core.require(type(values) is list and len(values) == count
                 and all(type(value) is str for value in values),
                 f"{name}: exactly {count} raw strings required")


def _first_blocks(bank):
    groups = defaultdict(list)
    for handle, fields in bank.items():
        requests = (["READ EVENT " + handle, "READ EVENTS_AT " + fields["source"]]
                    if "event" in fields else ["READ LINKS_FROM " + fields["first"]])
        for request in requests:
            groups[request].append(handle)
    slots = []
    for index, (request, handles) in enumerate(sorted(groups.items())):
        support = sorted(handles)
        core.require(len(support) <= 2, "maximum query adjacency exceeded")
        slots.append({"id": f"s{index:02}", "source": None,
                      "row_type": "EVENT" if "event" in bank[support[0]] else "LINK",
                      "phase": "OLD", "support": support,
                      "bank": {handle: core.detached(bank[handle]) for handle in support},
                      "taint": "AUTHENTIC", "request": request})
    return slots


def build_plan(cell, actions, link_choices):
    """Seal eight exact EXPLORE strings and four ordered event-handle pairs.

    Choices have no defaults. Event handles refer to OLD opportunity numbers,
    not WorldCell.edges/ideal_rows indices. Only successful public transitions
    can have a complete expected bank. No EVENT/LINK raw strings are authored.
    The returned private structure must not be supplied as a child prompt.
    """
    core.validate_cell(cell)
    _strings(actions, 8, "actions")
    core.require(type(link_choices) is list and len(link_choices) == 4,
                 "four explicit link choices required")
    for choice in link_choices:
        _strings(choice, 2, "link choice")
    session = core.WorldSession(cell, "OLD")
    bank, opportunities = {}, []
    for index, raw in enumerate(actions):
        public = session.public_affordances()
        prompt = session.explore_prompt()
        result = session.explore(raw)
        core.require(result["ok"], f"action {index}: {result.get('error')}")
        receipt = result["receipt"]
        handle = cell.root.lookup("event", f"e{index}")
        fields = {"event": handle, **{key: receipt[key] for key in
                  ("source", "port", "destination", "receipt")}}
        bank[handle] = fields
        opportunities.append({"opportunity": index, "source_slot": core.OLD_SOURCES[index],
                              "affordances": public, "explore_prompt": prompt,
                              "action": raw, "event_handle": handle,
                              "event_prompt": session.event_prompt(receipt),
                              "expected_receipt": receipt})
    pairs, links = set(), []
    event_handles = set(bank)
    for index, choice in enumerate(link_choices):
        core.require(all(handle in event_handles for handle in choice),
                     "link must name chronological OLD event handles")
        core.require(tuple(choice) not in pairs, "duplicate link pair")
        pairs.add(tuple(choice))
        first, second = (bank[handle] for handle in choice)
        core.require(first["destination"] == second["source"],
                     "link choice is not directly chained")
        handle = cell.root.lookup("link", f"l{index}")
        bank[handle] = {"link": handle, "first": choice[0], "second": choice[1],
                        "via": first["destination"], "receipt_first": first["receipt"],
                        "receipt_second": second["receipt"]}
        links.append({"opportunity": index, "link_handle": handle, "events": choice[:]})
    plan = {"schema": SCHEMA, "purpose": PURPOSE, "stage": "OLD",
            "source_pins": source_pins(), "cell": core.to_data(cell),
            "old_sources": list(core.OLD_SOURCES), "actions": actions[:],
            "link_choices": core.detached(link_choices), "opportunities": opportunities,
            "links": links, "expected_bank": bank, "first_blocks": _first_blocks(bank),
            "native_custody_verified": False, "execution_contract_valid": False}
    return {**plan, "plan_sha256": core.digest(plan)}


def validate_plan(plan, preoutput_sha256):
    """Require the independently retained seal and unchanged source semantics."""
    core.require(type(plan) is dict and type(preoutput_sha256) is str,
                 "plan and independently retained pre-output seal required")
    core.require(plan.get("plan_sha256") == preoutput_sha256
                 and core.digest({key: value for key, value in plan.items()
                                  if key != "plan_sha256"}) == preoutput_sha256,
                 "pre-output seal mismatch")
    rebuilt = build_plan(core.from_data(plan["cell"]), plan["actions"], plan["link_choices"])
    core.require(core.canonical(plan) == core.canonical(rebuilt),
                 "source/expected structure mismatch")
    return True


def first_block_slots(plan, preoutput_sha256):
    """Detached preparer SLOT_FIELDS inputs only; no replays/release contract."""
    validate_plan(plan, preoutput_sha256)
    return core.detached(plan["first_blocks"])


def bind_child(plan, preoutput_sha256, actions, event_raw, link_raw, *,
               contract=None, corpus_id=None):
    """Replay exact caller spans through real admissions, then bind the bank.

    Failure raises without replacement, repair, or modifying input bytes. The
    caller retains failed outputs/call receipts; no writes or model calls occur.
    Returned targets are made only by core.materialize_queries from admitted
    caller bytes. A supplied full contract also uses the real preparer seam.
    """
    validate_plan(plan, preoutput_sha256)
    _strings(actions, 8, "actual actions")
    _strings(event_raw, 8, "child EVENT spans")
    _strings(link_raw, 4, "child LINK spans")
    core.require(actions == plan["actions"], "actual actions differ from pre-output choices")
    core.require((contract is None) == (corpus_id is None), "contract/corpus must be paired")
    if contract is not None:
        prepare.validate_execution_contract(contract)
        corpora = [corpus for corpus in contract["bindings"]["slot_registry"]
                   if corpus["id"] == corpus_id]
        core.require(len(corpora) == 1, "unknown/ambiguous preparer corpus")
        corpus = corpora[0]
        core.require(corpus["root"] == plan["cell"]["root"]["label"]
                     and [slot for slot in corpus["slots"] if slot["source"] is None]
                     == plan["first_blocks"], "preparer first blocks differ from pre-output plan")
    cell = core.from_data(plan["cell"])
    session = core.WorldSession(cell, "OLD")
    receipts, events, admissions = {}, {}, []
    for index, raw in enumerate(actions):
        result = session.explore(raw)
        core.require(result["ok"], "actual transition failed")
        expected = plan["opportunities"][index]
        core.require(result["receipt"] == expected["expected_receipt"], "receipt replay differs")
        handle = expected["event_handle"]
        admission = core.admit_event(event_raw[index], result["receipt"], session, handle)
        core.require(admission["accepted"], f"child EVENT {index}: {admission.get('error')}")
        admissions.append(admission)
        receipts[handle], events[handle] = result["receipt"], admission["row"]
    for index, choice in enumerate(plan["link_choices"]):
        handle = plan["links"][index]["link_handle"]
        admission = core.admit_link(link_raw[index], [receipts[event] for event in choice],
                                    session, handle, [events[event] for event in choice])
        core.require(admission["accepted"], f"child LINK {index}: {admission.get('error')}")
        admissions.append(admission)
    report = core.formation_report(admissions, required_bank=plan["expected_bank"])
    core.require(report["formation_complete"], "child chronological bank mismatch")
    rows = [admission["row"] for admission in admissions]
    queries = core.materialize_queries(rows)
    expected_queries = {slot["request"]: slot["support"] for slot in plan["first_blocks"]}
    core.require({request: query["support"] for request, query in queries.items()} == expected_queries,
                 "child query structure mismatch")
    binding = (prepare.validate_formation_binding(contract, corpus_id, queries, rows)
               if contract is not None else None)
    return {"schema": SCHEMA + "/child_binding", "plan_sha256": preoutput_sha256,
            "actions": actions[:], "admissions": admissions, "rows": rows, "queries": queries,
            "formation": report, "preparer_binding": binding, "native_custody_verified": False}
