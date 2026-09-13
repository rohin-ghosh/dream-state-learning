"""Pinned CPU real-record formation, not native identity, training or learning.

Backend receives request dictionaries and returns raw response dictionaries.
Only public actual execution evidence reaches the child. No record targets are
authored here. Prompt/episode policy was declared in the handoff before tests.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace


SCHEMA = "astra_level1_real_record_20260913_v1"
STATES = ("OFF", "perception_seed0", "perception_seed1", "perception_seed2")
PROTOCOL = "interaction_v3"
DEFAULT_SOURCE_ROOT = "/data/home/rohing/dream-state"
PINS = {
    "organism_v6/rulegame.py": "88304996b00837ad1855e8a6661aad39e64f3beb0c0ab4491b63119e797226f3",
    "organism_v6/rulegame_parenting_diagnostic.py": "e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526",
}
WAKE_TEMPLATE = (
    "Fresh DEV mystery-box observation exercise. Choose your own three integers.\n"
    "Emit one ACT: TRY a,b,c line. You may put one PREDICT: T or PREDICT: F line before it, or omit a prediction.\n"
    "Do not emit an outcome, QUIZ, DONE, a record, or a hidden-rule claim. You have two scheduled attempts; no retries.\n"
    "Task: {eid}\nAttempt: {tick}/2\n{earlier_transcript}"
)
EARLIER_HEADER = "Earlier actual transcript (context only; not the selected execution):\n"
MAX_OUTPUT_TOKENS = {"wake": 96, "record": 192}
FIELDS = ("try", "observed", "predicted", "relation")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest(value):
    return sha_text(canonical(value))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def episode_ids():
    return tuple("real-record-dev-" + digest([SCHEMA, "fresh-dev", index])[:20] for index in range(8))


def load_dependencies(source_root=DEFAULT_SOURCE_ROOT):
    """Load pinned actual world and public parser functions, not runner imports."""
    texts = {}
    for relative, expected in PINS.items():
        path = Path(source_root) / relative
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == expected, "source pin mismatch: " + relative)
        texts[relative] = raw.decode("utf-8")
    world_namespace = {}
    game_path = "organism_v6/rulegame.py"
    exec(compile(texts[game_path], str(Path(source_root) / game_path), "exec"), world_namespace)
    interface_path = "organism_v6/rulegame_parenting_diagnostic.py"
    constants = {"PROTOCOLS", "RECORD", "RELATION_DEFINITION"}
    functions = {"require", "unique_object", "decode", "parse_action", "judge_record", "record_instruction", "record_prompt"}
    namespace = {"json": json, "re": re}
    selected, spans = [], {}
    for node in ast.parse(texts[interface_path]).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in constants:
                namespace[name] = ast.literal_eval(node.value)
                spans[name] = ast.get_source_segment(texts[interface_path], node)
        if isinstance(node, ast.FunctionDef) and node.name in functions:
            selected.append(node)
            spans[node.name] = ast.get_source_segment(texts[interface_path], node)
    require(set(spans) == constants | functions, "public interface inventory mismatch")
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(Path(source_root) / interface_path), "exec"), namespace)
    return SimpleNamespace(game_class=world_namespace["RuleGame"], interface=SimpleNamespace(**namespace),
                           manifest={"full_source_sha256": dict(PINS),
                                     "public_definitions_sha256": {name: sha_text(text) for name, text in sorted(spans.items())}})


def contract(dependencies):
    return {"schema": SCHEMA, "episode_ids": list(episode_ids()), "states": list(STATES),
            "episode_generation": "SHA256 compact sorted JSON [SCHEMA, fresh-dev, index0..7], first20hex; no rule selection",
            "protocol": PROTOCOL, "wake_template": WAKE_TEMPLATE,
            "record_template": "pinned record_prompt; turn2 prepends earlier actual transcript",
            "record_instruction": dependencies.interface.record_instruction(PROTOCOL),
            "first_history": "No earlier attempt in this episode.", "earlier_header": EARLIER_HEADER,
            "calls_per_episode": {"scheduled_wake": 2, "maximum_record": 2},
            "possible_records_per_state": 16, "max_output_tokens": dict(MAX_OUTPUT_TOKENS),
            "comparison": "interactive_record_formation_not_identical_experience",
            "qualification": "formation_only_no_fit_no_closed_loop_no_H1_P1",
            "dependencies": copy.deepcopy(dependencies.manifest)}


def earlier_transcript(previous):
    if previous is None:
        return "No earlier attempt in this episode."
    wake = previous["wake"]["response"]
    record = previous["record"]["response"] if previous["record"] is not None else None
    execution = previous["execution"]
    return EARLIER_HEADER + canonical({
        "attempt": previous["tick"], "wake_raw": wake.get("raw"), "wake_finish_reason": wake.get("finish_reason"),
        "outcome_raw": execution["outcome"] if execution else None,
        "record_raw": record.get("raw") if record else None,
        "record_finish_reason": record.get("finish_reason") if record else None,
        "status": previous["status"],
    })


def _event(events, payload):
    event = dict(payload, sequence=len(events), previous_sha256=events[-1]["sha256"] if events else None)
    event["sha256"] = digest(event)
    events.append(event)
    return event


def _request(state, eid, tick, kind, prompt, source_execution_sha256=None):
    request = {"state": state, "episode_id": eid, "tick": tick, "kind": kind,
               "input_messages": [{"role": "user", "content": prompt}],
               "max_output_tokens": MAX_OUTPUT_TOKENS[kind], "source_execution_sha256": source_execution_sha256}
    request["request_id"] = digest([SCHEMA, request])
    return request


def _call(backend, request, events):
    try:
        response = copy.deepcopy(backend(copy.deepcopy(request)))
        canonical(response)
    except Exception as error:
        response = {"backend_error": type(error).__name__ + ": " + str(error)}
    if type(response) is not dict:
        response = {"invalid_backend_response": response}
    errors = []
    if "backend_error" in response:
        errors.append("backend_error")
    if response.get("request_id") != request["request_id"]:
        errors.append("request_source_join_mismatch")
    if response.get("state") != request["state"]:
        errors.append("state_source_join_mismatch")
    if not isinstance(response.get("raw"), str):
        errors.append("missing_raw_text")
    if response.get("finish_reason") != "stop":
        errors.append("finish_reason_not_stop")
    return _event(events, {"kind": "call", "request": request, "response": response, "errors": errors})


def score_record(raw, finish_reason, execution, dependencies, source_errors=()):
    """No targets; judge existing raw bytes and expose separate diagnostic fields."""
    interface = dependencies.interface
    errors = list(source_errors)
    if finish_reason != "stop":
        errors.append("finish_reason_not_stop")
    field_correct = {field: False for field in FIELDS}
    parsed, format_kind, canonical_pass = None, "unparseable", False
    production = {"eligible": False, "failures": ["missing_raw_text"]}
    content = {"eligible": False, "failures": ["missing_raw_text"]}
    if isinstance(raw, str):
        production = interface.judge_record(raw, execution)
        text = raw.strip(" \t\r\n")
        fence = re.fullmatch(r"```(?:json)?[ \t]*\r?\n([\s\S]*?)\r?\n```", text)
        candidate = fence.group(1) if fence else text
        try:
            parsed = interface.decode(candidate)
            encoded = canonical(parsed)
        except (ValueError, TypeError, RecursionError) as error:
            content = {"eligible": False, "failures": ["invalid_json: " + str(error)]}
        else:
            format_kind = "fenced" if fence else "exact" if raw == encoded else "json_noncanonical"
            content = interface.judge_record(candidate, execution)
            canonical_pass = content["eligible"] and raw == encoded
            if type(parsed) is dict:
                values = parsed.get("try")
                field_correct["try"] = (type(values) is list and len(values) == 3 and
                                         all(type(value) is int for value in values) and values == execution["values"])
                observed = parsed.get("observed")
                field_correct["observed"] = type(observed) is bool and observed == execution["observed"]
                predicted = parsed.get("predicted")
                unambiguous = not execution["prediction_ambiguous"]
                field_correct["predicted"] = ("predicted" in parsed and unambiguous and
                                               (predicted is None or type(predicted) is bool) and predicted is execution["predicted"])
                relation = ("unavailable" if execution["predicted"] is None else
                            "matched" if execution["predicted"] == execution["observed"] else "mismatched")
                field_correct["relation"] = unambiguous and type(parsed.get("relation")) is str and parsed["relation"] == relation
    eligible_fields = {field: correct and not errors for field, correct in field_correct.items()}
    return {"raw": raw, "finish_reason": finish_reason, "format": format_kind,
            "production_eligible": production["eligible"] and not errors,
            "content_correct": content["eligible"] and not errors,
            "strict_canonical": canonical_pass and not errors,
            "field_correct": eligible_fields, "parsed_field_correct": field_correct,
            "source_completion_errors": errors, "production_errors": production["failures"],
            "content_errors": content["failures"], "parsed": parsed,
            "content_boundary": "typed public record agreement, not reasoning correctness; fences diagnostic only"}


def _execute(game, dependencies, wake, state, eid, tick, events):
    action = dependencies.interface.parse_action(wake["response"]["raw"], PROTOCOL)
    require(action["kind"] == "try", "only TRY is executable; no quiz/reveal/DONE")
    unused_reward, outcome = game.evaluate(SimpleNamespace(eid=eid), action["action"])
    match = re.fullmatch(r"the box says: (True|False) for \((-?[0-9]+),(-?[0-9]+),(-?[0-9]+)\)", outcome)
    require(match is not None and [int(value) for value in match.groups()[1:]] == action["values"], "world TRY outcome mismatch")
    return _event(events, dict(action, kind="execution", action_kind="try", state=state, eid=eid, tick=tick,
                              execution_id=f"{state}:{eid}#t{tick}", source_call_id=wake["request"]["request_id"],
                              source_call_sha256=wake["sha256"], raw_wake=wake["response"]["raw"],
                              wake_finish_reason=wake["response"]["finish_reason"], observed=match.group(1) == "True",
                              outcome=outcome, outcome_utf8_sha256=sha_text(outcome)))


def _summary(episodes):
    turns = [turn for episode in episodes for turn in episode["turns"]]
    counts = {"possible_records": 16, "scheduled_wake_calls": 16,
              "actual_wake_calls": len(turns), "actual_record_calls": sum(turn["record"] is not None for turn in turns),
              "world_executions": sum(turn["execution"] is not None for turn in turns),
              "missing_records": sum(turn["record"] is None or not isinstance(turn["record"]["response"].get("raw"), str) for turn in turns),
              "unfinished_records": sum(turn["record"] is not None and turn["record"]["response"].get("finish_reason") != "stop" for turn in turns)}
    for metric in ("production_eligible", "content_correct", "strict_canonical"):
        counts[metric] = sum(bool(turn["score"] and turn["score"][metric]) for turn in turns)
        counts[metric + "_rate_over16"] = counts[metric] / 16
    counts["field_correct_over16"] = {field: sum(bool(turn["score"] and turn["score"]["field_correct"][field]) for turn in turns) for field in FIELDS}
    counts["refusals"] = [{"episode_id": episode["episode_id"], "tick": turn["tick"], "status": turn["status"],
                           "errors": turn["errors"], "score": turn["score"]}
                          for episode in episodes for turn in episode["turns"]
                          if not turn["score"] or not turn["score"]["production_eligible"]]
    return counts


def run_state(state, backend, *, dependencies=None, binding=None):
    """Execute 16 scheduled wakes; record only valid completed actual TRYs.

    Backend(request) must return {request_id, state, raw, finish_reason}.
    Native tokens/route metadata may be retained as extra JSON response fields.
    Request/token budgets are declared, not proof the injected backend enforces them.
    """
    require(state in STATES, "unknown state")
    require(callable(backend), "backend must be callable")
    dependencies = dependencies or load_dependencies()
    binding = copy.deepcopy(binding if binding is not None else {"kind": "unverified_injected_backend"})
    canonical(binding)
    events, episodes = [], []
    for eid in episode_ids():
        game = dependencies.game_class()
        turns = []
        for tick in (1, 2):
            history = earlier_transcript(turns[-1] if turns else None)
            prompt = WAKE_TEMPLATE.format(eid=eid, tick=tick, earlier_transcript=history)
            wake = _call(backend, _request(state, eid, tick, "wake", prompt), events)
            turn = {"tick": tick, "wake": wake, "execution": None, "record": None, "score": None,
                    "status": "INVALID_WAKE", "errors": list(wake["errors"])}
            if not wake["errors"]:
                try:
                    execution = _execute(game, dependencies, wake, state, eid, tick, events)
                except (ValueError, TypeError, KeyError) as error:
                    turn["errors"].append(str(error))
                else:
                    turn["execution"] = execution
                    record_prompt = dependencies.interface.record_prompt(execution, wake["response"]["raw"], PROTOCOL)
                    if tick == 2:
                        record_prompt = history + "\n" + record_prompt
                    record = _call(backend, _request(state, eid, tick, "record", record_prompt, execution["sha256"]), events)
                    turn["record"] = record
                    response = record["response"]
                    turn["score"] = score_record(response.get("raw"), response.get("finish_reason"), execution,
                                                 dependencies, source_errors=record["errors"])
                    turn["errors"].extend(record["errors"])
                    turn["status"] = "PRODUCTION_RECORD" if turn["score"]["production_eligible"] else "RECORD_REJECTED"
            turns.append(turn)
        episodes.append({"episode_id": eid, "turns": turns})
    result = {"schema": SCHEMA, "state": state, "binding": binding, "contract": contract(dependencies),
              "episodes": episodes, "events": events, "summary": _summary(episodes),
              "native_identity_verified": False, "qualification": "interactive_formation_only_no_training_claim"}
    result["capture_sha256"] = digest(result)
    return result


def audit_capture(capture, *, dependencies=None):
    """CPU deterministic replay verifies prompts, source joins and world outcomes.

    Reads no model or held-out result. Replay re-evaluates the recorded TRYs,
    but cannot authenticate that an injected response came from a real child.
    """
    dependencies = dependencies or load_dependencies()
    supplied = copy.deepcopy(capture)
    pin = supplied.pop("capture_sha256")
    require(digest(supplied) == pin, "capture hash mismatch")
    calls = [event for event in capture["events"] if event["kind"] == "call"]
    index = 0
    def replay(request):
        nonlocal index
        require(index < len(calls), "missing replay call")
        event = calls[index]
        index += 1
        require(request == event["request"], "replay request/source join mismatch")
        return copy.deepcopy(event["response"])
    rebuilt = run_state(capture["state"], replay, dependencies=dependencies, binding=capture["binding"])
    require(index == len(calls) and rebuilt == capture, "capture differs from public execution replay")
    return {"consistent": True, "capture_sha256": pin, "calls_replayed": index,
            "native_identity_verified": False, "summary": copy.deepcopy(capture["summary"])}


def compare_states(captures, *, dependencies=None):
    """Audit supplied captures; missing states remain missing, never invented."""
    dependencies = dependencies or load_dependencies()
    require(type(captures) in (list, tuple) and captures, "provide nonempty captures")
    seen, summaries = set(), {}
    for capture in captures:
        state = capture["state"]
        require(state not in seen, "duplicate state")
        audit_capture(capture, dependencies=dependencies)
        require(capture["contract"] == contract(dependencies), "state contract differs")
        seen.add(state)
        summaries[state] = copy.deepcopy(capture["summary"])
    return {"comparison": "interactive_record_formation_not_identical_experience",
            "episode_ids": list(episode_ids()), "possible_records_per_state": 16,
            "states": summaries, "missing_states": [state for state in STATES if state not in seen],
            "native_identity_verified": False, "claim": "raw36 formation only; no writes or improved learning"}
