"""Fixed A3 offered experience and actual-reader audit, with no models or fits.

Replay checks consistency, not actor authenticity. The caller authenticates the
actor/source and disjointness from all earlier and reserved banks. This is an
external experience/audit scaffold, not autonomous selection or an H2 claim.
"""

from copy import deepcopy
from hashlib import sha256

from organism_v6 import experienced_event_actual_reader_audit as actual
from organism_v6 import experienced_event_adult_cycle as adult
from organism_v6 import experienced_event_corrective_replay as corrective
from organism_v6 import experienced_event_microloop as micro


MASTER = "ASTRA-READER-AUDIT-CONTINUATION-20260914-A3"
SCHEMA = "DEV_FRESH_READER_CYCLE_COLLECTION_V1"
AUDIT_SCHEMA = "DEV_FRESH_READER_CYCLE_ACTUAL_AUDIT_V1"
SERIALIZATION = "FINAL_LF_ONLY"
MAX_CALLS = 8
MAX_CONTEXT = actual.MAX_CONTEXT
MAX_NEW_TOKENS = actual.MAX_NEW_TOKENS
require = micro._require
document_sha256 = actual.document_sha256


def build_bank():
    return micro.build_bank(MASTER)


def _collect(invoke):
    bank, episodes, captures = build_bank(), [], []

    def generate(messages, episode_index, phase):
        require(len(captures) < MAX_CALLS, "fresh_collection_call_cap")
        outcome = invoke(adult._copy(messages))
        capture = dict(call_index=len(captures), episode_index=episode_index, phase=phase,
                       messages=adult._copy(messages), **adult._copy(outcome))
        captures.append(capture)
        return capture

    for episode_index, fact in enumerate(bank):
        episode = dict(fact=adult._copy(fact), exploration=None, event=None, accepted=False,
                       infrastructure_failure=False, error=None)
        episodes.append(episode)
        try:
            messages = micro.exploration_messages(fact)
            capture = generate(messages, episode_index, "exploration")
            episode["exploration"] = adult._copy(capture["response"])
            if capture["error"] is not None:
                episode.update(infrastructure_failure=True, error=adult._copy(capture["error"]))
            require(capture["error"] is None, "exploration_callback_failure")
            exploration = adult._generation(episode["exploration"], messages)
            messages = micro.observation_messages(fact, exploration["raw"])
            capture = generate(messages, episode_index, "event")
            episode["event"] = adult._copy(capture["response"])
            if capture["error"] is not None:
                episode.update(infrastructure_failure=True, error=adult._copy(capture["error"]))
            require(capture["error"] is None, "event_callback_failure")
            event = adult._generation(episode["event"], messages)
            micro.validate_episode(fact, exploration["raw"], micro.canonical_event(event["raw"]))
            episode["accepted"] = True
        except ValueError as error:
            if episode["error"] is None:
                episode["error"] = dict(type=type(error).__name__, message=str(error))
    accepted = sum(episode["accepted"] for episode in episodes)
    rows = micro.compile_rows(bank, episodes, serialization=SERIALIZATION) if accepted == 4 else []
    require(not rows or len(rows) == 32, "four_grounded_events_before_rows")
    return dict(schema=SCHEMA, master=MASTER, serialization=SERIALIZATION,
                claim="EXOGENOUS_OFFERED_EXPERIENCE_FORMAT_SCAFFOLD_NOT_AUTONOMOUS_SELECTION_OR_H2",
                new_material=True, clean_claim=False, parent_present=False, fits=0,
                bank=bank, episodes=episodes, rows=rows, captures=captures,
                count=len(captures), accepted_events=accepted, event_denominator=4,
                infrastructure_failures=sum(episode["infrastructure_failure"] for episode in episodes),
                status="COLLECTION_COMPLETE_NO_FIT" if accepted == 4 else "COLLECTION_FAILED_NO_FIT")


def collect(generate):
    """Attempt all four experiences; retain failures and make at most eight calls."""
    require(callable(generate), "generation_callback_required")

    def invoke(messages):
        response = None
        try:
            response = generate(adult._copy(messages))
            return dict(response=adult._copy(response), error=None)
        except Exception as error:
            available = None
            if type(response) is dict:
                available = {key: response.get(key) for key in ("raw", "terminal", "truncated")
                             if type(response.get(key)) in (str, bool, int, type(None))}
            return dict(response=available, error=dict(type=type(error).__name__, message=str(error)))

    return _collect(invoke)


def replay_collection(record):
    """Recompute exact prompts, admission, raw failures and all 32 rows (or none)."""
    require(type(record) is dict and record.get("schema") == SCHEMA and record.get("master") == MASTER
            and type(record.get("captures")) is list, "fresh_collection_required")
    captures = adult._copy(record["captures"])
    require(4 <= len(captures) <= MAX_CALLS, "bounded_actual_calls_required")
    cursor = 0

    def invoke(messages):
        nonlocal cursor
        require(cursor < len(captures), "missing_actual_call")
        capture = captures[cursor]
        cursor += 1
        require(type(capture) is dict and all(key in capture for key in ("messages", "response", "error")),
                "actual_call_record_required")
        adult._same(capture["messages"], messages, "captured_prompt_drift")
        return dict(response=capture["response"], error=capture["error"])

    replayed = _collect(invoke)
    require(cursor == len(captures), "unused_actual_calls")
    adult._same(record, replayed, "fresh_collection_replay_drift")
    return replayed["rows"]


def build_cases(collection, route_records):
    """Bind the fresh collection and four actual routes; audit every reader call."""
    rows = replay_collection(collection)
    require(collection["accepted_events"] == 4 and len(rows) == 32, "complete_fresh_collection_required")
    require(type(route_records) is list and len(route_records) == 4, "four_own_routes_required")
    sources = []
    for source_index, episode in enumerate(collection["episodes"]):
        raw = episode["event"]["raw"]
        messages = collection["captures"][2 * source_index + 1]["messages"]
        row_indexes = [index for index, row in enumerate(rows) if row["event"] == episode["fact"]["event"]]
        require(len(row_indexes) == 8, "eight_source_views_required")
        sources.append(dict(source_index=source_index, event=episode["fact"]["event"], raw=raw,
                            canonical=micro.canonical_event(raw), receipt=messages[-1]["content"].split("\n", 1)[0],
                            row_source_indexes=row_indexes, source_raw_sha256=sha256(raw.encode("utf-8")).hexdigest()))
    table = "".join(entry["canonical"] for entry in sources)
    cases = []
    for episode_index, (fact, record) in enumerate(zip(collection["bank"], route_records)):
        task, episode = corrective._replay_route(fact, record)
        observed = [other for other in collection["bank"]
                    if other["node"] == task["node"] and other["port"] == episode["chosen_port"]]
        require(len(observed) == 1 and observed[0]["outcome"] == episode["outcome"],
                "actual_transition_disagrees_with_own_receipt")
        read_index = 0
        for trace_index, trace in enumerate(episode["traces"]):
            if trace["kind"] != "memory":
                continue
            require(len(cases) < MAX_CALLS, "actual_reader_call_cap")
            address, response = trace["address"], trace["response"]
            matches = [entry for entry in sources if entry["event"] == address]
            require(len(matches) == 1, "queried_address_must_have_own_source")
            raw = response["raw"]
            try:
                canonical = micro.canonical_event(raw)
            except ValueError:
                canonical = None
            mismatch = canonical != matches[0]["canonical"]
            user = (actual.SKIN + "\nREQUESTED EVENT: " + address + "\nRECEIPT-GROUNDED SOURCE TABLE\n"
                    + table + "UNTRUSTED READER REPLY\n" + raw)
            case = dict(case_index=len(cases), episode_index=episode_index, read_index=read_index,
                trace_index=trace_index, address=address, reader_raw=raw,
                reader_terminal=response["terminal"], reader_truncated=response["truncated"],
                kind="fault" if mismatch else "true", expected=address if mismatch else "NONE",
                stimulus_origin="ACTUAL_CAPTURED_READER_RESPONSE_NOT_VERIFIED_EXPERIENCE",
                transcript_sha256=document_sha256(episode["messages"]), episode_sha256=document_sha256(record),
                trace_sha256=document_sha256(trace), response_sha256=document_sha256(response),
                reader_raw_sha256=sha256(raw.encode("utf-8")).hexdigest(),
                messages=[dict(role="system", content=actual.SYSTEM), dict(role="user", content=user)])
            cases.append(actual._seal(case, "case_sha256"))
            read_index += 1
        require(read_index == episode["memory_calls"], "actual_reader_count_drift")
    return actual._seal(dict(schema=AUDIT_SCHEMA, master=MASTER, fits=0, collection=deepcopy(collection),
        route_records=deepcopy(route_records), sources=sources, cases=cases, expected_calls=len(cases), task_denominator=4,
        source_document_sha256=dict(collection=document_sha256(collection), route_records=document_sha256(route_records))),
        "cases_sha256")


def collect_audit(cases, generate):
    """Keep source-valid pointers, even wrong/repeated choices; NONE substitutes nothing."""
    require(type(cases) is dict and callable(generate), "case_bundle_and_callback_required")
    adult._same(cases, build_cases(cases["collection"], cases["route_records"]), "fresh_reader_case_source_drift")
    cases = deepcopy(cases)
    captures, selected, row_indexes, origins = [], [], [], []
    summary = {kind: dict(correct=0, denominator=0) for kind in ("overall", "true", "fault")}
    for case in cases["cases"]:
        response = error = None
        try:
            response = deepcopy(generate(deepcopy(case["messages"])))
        except Exception as failure:
            error = dict(type=type(failure).__name__, message=str(failure))
        capture = dict(call_index=len(captures), case_sha256=case["case_sha256"],
                       messages=deepcopy(case["messages"]), response=response, error=error)
        correct, source_index, status = actual._score(case, capture, cases["sources"])
        capture.update(correct=correct, admitted=source_index is not None, source_index=source_index, status=status)
        capture = actual._seal(capture, "call_sha256")
        captures.append(capture)
        selected.append(source_index)
        for kind in ("overall", case["kind"]):
            summary[kind]["denominator"] += 1
            summary[kind]["correct"] += int(correct)
        if source_index is not None:
            entry = cases["sources"][source_index]
            for source_row_index in entry["row_source_indexes"]:
                row_indexes.append(source_row_index)
                origins.append(dict(call_index=capture["call_index"], case_sha256=case["case_sha256"],
                    call_sha256=capture["call_sha256"], episode_index=case["episode_index"],
                    trace_index=case["trace_index"], source_index=source_index, source_row_index=source_row_index,
                    source_raw_sha256=entry["source_raw_sha256"], event=entry["event"],
                    mapping="EXISTING_OWN_EVENT_QUERY_ROW_NOT_NEW_CHILD_CONTENT"))
    return actual._seal(dict(schema=AUDIT_SCHEMA, master=MASTER, status="ACTUAL_READER_AUDIT_CAPTURED_NO_FIT",
        fits=0, parent_present=False, source_document_sha256=cases["source_document_sha256"],
        cases_sha256=cases["cases_sha256"], cases=cases["cases"], sources=cases["sources"], captures=captures,
        chosen_source_indexes=selected, admitted_selections=sum(index is not None for index in selected),
        row_source_indexes=row_indexes, material_origins=origins, model_calls=len(captures),
        expected_calls=cases["expected_calls"], task_denominator=4, summary=summary,
        correct=summary["overall"]["correct"], denominator=summary["overall"]["denominator"],
        claim="PUBLIC_ACTUAL_READER_CLASSIFICATION_AND_SOURCE_POINTER_NOT_GOAL_UTILITY_OR_NEW_EXPERIENCE"),
        "audit_sha256")
