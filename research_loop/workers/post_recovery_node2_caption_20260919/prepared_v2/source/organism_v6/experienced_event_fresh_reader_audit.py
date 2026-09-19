"""A3 reader audit v2: actual reads do not require a later valid route.

Pure captured replay; no model, teacher, fit, source mutation or missing outcome
substitution. The unchanged fresh-cycle helper authenticates collection contents;
the native caller authenticates actor and source bytes. Unavailable reader text
is diagnosed, never replaced with an invented response or scored audit case.
"""

from copy import deepcopy
from hashlib import sha256

from organism_v6 import experienced_event_actual_reader_audit as actual
from organism_v6 import experienced_event_adult_cycle as adult
from organism_v6 import experienced_event_fresh_reader_cycle as fresh
from organism_v6 import experienced_event_microloop as micro
from organism_v6 import experienced_event_read_route as controller


SCHEMA = "DEV_FRESH_READER_CYCLE_ACTUAL_AUDIT_V2"
MASTER = fresh.MASTER
MAX_CALLS = actual.MAX_CALLS
MAX_CONTEXT = actual.MAX_CONTEXT
MAX_NEW_TOKENS = actual.MAX_NEW_TOKENS
require = micro._require
document_sha256 = actual.document_sha256


def _replay_route(fact, record, bank):
    require(type(record) is dict and set(record) == {"event", "episode"}
            and record["event"] == fact["event"], "route_event_source_order_drift")
    episode = record["episode"]
    require(type(episode) is dict and type(episode.get("traces")) is list, "actual_route_traces_required")
    traces, cursor = episode["traces"], 0

    def consume(kind):
        nonlocal cursor
        require(cursor < len(traces) and traces[cursor].get("kind") == kind, "actual_trace_order_or_missing_call")
        trace = traces[cursor]
        cursor += 1
        return trace

    def response(trace):
        if "error" in trace:
            error = trace["error"]
            require(type(error) is dict and set(error) == {"type", "message"}
                    and type(error["type"]) is str and type(error["message"]) is str, "captured_callback_error_required")
            raise type(error["type"], (Exception,), {})(error["message"])
        require("response" in trace, "actual_response_unavailable_for_replay")
        return deepcopy(trace["response"])

    def actor(messages):
        trace = consume("actor")
        adult._same(trace["messages"], messages, "route_actor_prompt_drift")
        captured = trace.get("response")
        if type(captured) is dict and "messages" in captured:
            adult._same(captured["messages"], messages, "route_response_prompt_drift")
        return response(trace)

    def reader(address):
        trace = consume("memory")
        require(trace["address"] == address, "route_reader_address_drift")
        return response(trace)

    def transition(port):
        trace = consume("transition")
        require(trace.get("committed") is True and trace.get("port") == port, "captured_commit_required")
        if "error" in trace:
            return response(trace)
        require("outcome" in trace, "captured_transition_outcome_required")
        observed = [other for other in bank if other["node"] == fact["node"] and other["port"] == port]
        require(len(observed) == 1 and observed[0]["outcome"] == trace["outcome"],
                "actual_transition_disagrees_with_own_receipt")
        return deepcopy(trace["outcome"])

    replayed = controller.run_episode(controller.public_task(fact), actor, reader, transition)
    require(cursor == len(traces), "unused_actual_route_traces")
    adult._same(replayed, episode, "route_episode_replay_drift")
    return replayed


def build_cases(collection, records):
    """Replay all four routes and inspect real reader responses before any audit."""
    rows = fresh.replay_collection(collection)
    require(collection["accepted_events"] == 4 and len(rows) == 32, "complete_fresh_collection_required")
    require(type(records) is list and len(records) == 4, "four_own_routes_required")
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
    cases, routes, unavailable = [], [], []
    for episode_index, (fact, record) in enumerate(zip(collection["bank"], records)):
        episode = _replay_route(fact, record, collection["bank"])
        routes.append(dict(episode_index=episode_index, event=fact["event"], terminal_reason=episode["terminal_reason"],
                           chosen_port=episode["chosen_port"], outcome=episode["outcome"],
                           memory_calls=episode["memory_calls"],
                           transition_calls=sum(trace["kind"] == "transition" for trace in episode["traces"])))
        read_index = 0
        for trace_index, trace in enumerate(episode["traces"]):
            if trace["kind"] != "memory":
                continue
            require(sum(route["memory_calls"] for route in routes) <= MAX_CALLS, "actual_reader_call_cap")
            address, response = trace["address"], trace.get("response")
            matches = [entry for entry in sources if entry["event"] == address]
            require(len(matches) == 1, "queried_address_must_have_own_source")
            current_read = read_index
            read_index += 1
            if (type(response) is not dict or type(response.get("raw")) is not str
                    or type(response.get("terminal")) is not bool or type(response.get("truncated")) is not bool):
                unavailable.append(dict(episode_index=episode_index, read_index=current_read, trace_index=trace_index,
                                        address=address, trace=deepcopy(trace), reason="NO_AUDITABLE_CAPTURED_READER_TEXT"))
                continue
            raw = response["raw"]
            try:
                canonical = micro.canonical_event(raw)
            except ValueError:
                canonical = None
            mismatch = canonical != matches[0]["canonical"]
            user = (actual.SKIN + "\nREQUESTED EVENT: " + address + "\nRECEIPT-GROUNDED SOURCE TABLE\n"
                    + table + "UNTRUSTED READER REPLY\n" + raw)
            case = dict(case_index=len(cases), episode_index=episode_index, read_index=current_read,
                trace_index=trace_index, address=address, reader_raw=raw,
                reader_terminal=response["terminal"], reader_truncated=response["truncated"],
                kind="fault" if mismatch else "true", expected=address if mismatch else "NONE",
                stimulus_origin="ACTUAL_CAPTURED_READER_RESPONSE_NOT_VERIFIED_EXPERIENCE",
                transcript_sha256=document_sha256(episode["messages"]), episode_sha256=document_sha256(record),
                trace_sha256=document_sha256(trace), response_sha256=document_sha256(response),
                reader_raw_sha256=sha256(raw.encode("utf-8")).hexdigest(),
                messages=[dict(role="system", content=actual.SYSTEM), dict(role="user", content=user)])
            cases.append(actual._seal(case, "case_sha256"))
        require(read_index == episode["memory_calls"], "actual_reader_count_drift")
    return actual._seal(dict(schema=SCHEMA, master=MASTER, fits=0, collection=deepcopy(collection),
        route_records=deepcopy(records), sources=sources, cases=cases, expected_calls=len(cases), task_denominator=4,
        source_document_sha256=dict(collection=document_sha256(collection), route_records=document_sha256(records)),
        route_diagnostics=routes, invalid_route_count=sum(route["terminal_reason"] == "invalid_route" for route in routes),
        actual_reader_calls=sum(route["memory_calls"] for route in routes), unavailable_readers=unavailable), "cases_sha256")


def collect_audit(cases, generate):
    """Same actual-reader prompt/scoring/admission; preserve wrong/duplicate pointers."""
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
    return actual._seal(dict(schema=SCHEMA, master=MASTER, status="ACTUAL_READER_AUDIT_CAPTURED_NO_FIT",
        fits=0, parent_present=False, source_document_sha256=cases["source_document_sha256"],
        cases_sha256=cases["cases_sha256"], cases=cases["cases"], sources=cases["sources"], captures=captures,
        chosen_source_indexes=selected, admitted_selections=sum(index is not None for index in selected),
        row_source_indexes=row_indexes, material_origins=origins, model_calls=len(captures),
        expected_calls=cases["expected_calls"], task_denominator=4, summary=summary,
        correct=summary["overall"]["correct"], denominator=summary["overall"]["denominator"],
        route_diagnostics=cases["route_diagnostics"], invalid_route_count=cases["invalid_route_count"],
        actual_reader_calls=cases["actual_reader_calls"], unavailable_readers=cases["unavailable_readers"],
        claim="PUBLIC_ACTUAL_READER_CLASSIFICATION_AND_SOURCE_POINTER_NOT_GOAL_UTILITY_OR_NEW_EXPERIENCE"), "audit_sha256")
