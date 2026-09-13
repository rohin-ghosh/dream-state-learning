"""Pure CPU fresh interaction after memory writes; native custody is external."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from types import ModuleType, SimpleNamespace


SCHEMA = "astra_post_memory_formation_20260913_v1"
V2_PATH = "/tmp/astra_level1_real_record_core_20260913_v2.py"
V2_SHA256 = "b023a4321d0a20e465c96914316a730fbb2dd897c11369a9eb62d2d8f1248ef5"
DEFAULT_SOURCE_ROOT = "/data/home/rohing/dream-state"
EPISODE_NAMESPACE = "astra-next-l2-20260913"
EPISODE_IDS_SHA256 = "c45edf52b71d84e547264251abcb34305199f30e8dd3af1e41caa7346c4dca6e"
STATES = tuple(f"perception_seed{seed}_{arm}" for seed in range(3) for arm in ("WRITE", "LR0"))
EXAMPLE_BLOCK = (
    "Syntax example only (these numbers and this prediction are arbitrary, not a known answer):\n"
    "PREDICT: T\nACT: TRY 2,5,9\n"
)
QUALIFICATION = "post_memory_fresh_interaction_only_no_new_fit_no_teacher_no_closed_loop_no_H1_H2"


def load_v2(core_path=V2_PATH):
    raw = Path(core_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != V2_SHA256:
        raise ValueError("frozen v2 core pin mismatch")
    module = ModuleType("post_memory_frozen_v2")
    exec(compile(raw, str(core_path), "exec"), module.__dict__)
    return module


_V2 = load_v2()
canonical = _V2.canonical
sha_text = _V2.sha_text
digest = _V2.digest
require = _V2.require
earlier_transcript = _V2.earlier_transcript
score_record = _V2.score_record
PROTOCOL = _V2.PROTOCOL
PINS = dict(_V2.PINS)
MAX_OUTPUT_TOKENS = dict(_V2.MAX_OUTPUT_TOKENS)
FIELDS = tuple(_V2.FIELDS)
require(_V2.WAKE_TEMPLATE.count(EXAMPLE_BLOCK) == 1, "frozen example block differs")
WAKE_TEMPLATES = {
    "example_present": _V2.WAKE_TEMPLATE,
    "example_absent": _V2.WAKE_TEMPLATE.replace(EXAMPLE_BLOCK, "", 1),
}


def episode_ids():
    return tuple("next-record-dev-" + digest([EPISODE_NAMESPACE, index])[:20] for index in range(8))


def check_disjointness(prior_episode_ids=()):
    require(type(prior_episode_ids) in (tuple, list) and all(type(value) is str and value for value in prior_episode_ids),
            "prior episode IDs must be an explicit list/tuple of strings")
    ids = episode_ids()
    prior = set(_V2.episode_ids()) | set(prior_episode_ids)
    require(len(set(ids)) == 8 and digest(list(ids)) == EPISODE_IDS_SHA256, "fixed fresh schedule differs")
    require(not set(ids) & prior, "fresh IDs overlap original formation/training IDs")
    return {"disjoint": True, "episode_ids_sha256": EPISODE_IDS_SHA256,
            "prior_episode_ids": sorted(prior), "prior_episode_ids_sha256": digest(sorted(prior)),
            "scope": "original v2 formation IDs plus explicitly supplied prior IDs; not hidden exposure certification"}


def schedule():
    check_disjointness()
    return tuple({"episode_id": eid, "index": index,
                  "cue_stratum": "example_present" if index % 2 == 0 else "example_absent"}
                 for index, eid in enumerate(episode_ids()))


def load_dependencies(source_root=DEFAULT_SOURCE_ROOT, *, core_path=V2_PATH):
    frozen = load_v2(core_path)
    dependencies = frozen.load_dependencies(source_root)
    return SimpleNamespace(game_class=dependencies.game_class, interface=dependencies.interface,
        manifest={**copy.deepcopy(dependencies.manifest), "formation_v2_core_sha256": V2_SHA256})


def contract(dependencies):
    return {"schema": SCHEMA, "states": list(STATES), "episode_ids": list(episode_ids()),
            "episode_generation": "next-record-dev- + SHA256 compact JSON [astra-next-l2-20260913,index0..7], first20hex",
            "episode_ids_sha256": EPISODE_IDS_SHA256, "schedule": list(schedule()),
            "disjointness": check_disjointness(), "wake_templates": dict(WAKE_TEMPLATES),
            "syntax_example_block": EXAMPLE_BLOCK,
            "cue_assignment": "even indices retain frozen v2 example; odd remove only entire example block",
            "protocol": PROTOCOL, "record_instruction": dependencies.interface.record_instruction(PROTOCOL),
            "record_template": "unchanged pinned v2 record_prompt; turn2 prepends unchanged earlier actual transcript",
            "first_history": earlier_transcript(None), "earlier_header": _V2.EARLIER_HEADER,
            "max_output_tokens": dict(MAX_OUTPUT_TOKENS), "calls_per_episode": {"scheduled_wake": 2, "maximum_record": 2},
            "possible_records_per_state": 16, "maximum_calls_per_state": 32, "maximum_calls_all_states": 192,
            "maximum_generated_tokens_all_states": 27648, "new_fits": 0, "parent_calls": 0,
            "prerequisite": "Main must verify engineering validity/custody of all three completed memory pairs; not verified by this core",
            "outcome_gate": None, "gain_or_canary_harm_is_gate": False,
            "comparison": "paired_schedule_interactive_record_formation_not_identical_experience",
            "qualification": QUALIFICATION, "native_identity_verified": False,
            "dependencies": copy.deepcopy(dependencies.manifest)}


def _request(state, case, tick, kind, prompt, source_execution_sha256=None):
    request = {"state": state, "episode_id": case["episode_id"], "episode_index": case["index"],
               "cue_stratum": case["cue_stratum"], "tick": tick, "kind": kind,
               "input_messages": [{"role": "user", "content": prompt}],
               "max_output_tokens": MAX_OUTPUT_TOKENS[kind], "source_execution_sha256": source_execution_sha256}
    request["request_id"] = digest([SCHEMA, request])
    return request


def _counts(turns):
    possible = len(turns)
    result = {"possible_records": possible, "scheduled_wake_calls": possible, "actual_wake_calls": possible,
              "actual_record_calls": sum(turn["record"] is not None for turn in turns),
              "world_executions": sum(turn["execution"] is not None for turn in turns),
              "invalid_wakes": sum(turn["execution"] is None for turn in turns),
              "unfinished_wakes": sum(turn["wake"]["response"].get("finish_reason") != "stop" for turn in turns),
              "missing_records": sum(turn["record"] is None or not isinstance(turn["record"]["response"].get("raw"), str) for turn in turns),
              "unfinished_records": sum(turn["record"] is not None and turn["record"]["response"].get("finish_reason") != "stop" for turn in turns),
              "coverage": "observed" if possible else "untested"}
    for metric in ("production_eligible", "content_correct", "strict_canonical"):
        numerator = sum(bool(turn["score"] and turn["score"][metric]) for turn in turns)
        result[metric] = numerator
        result[metric + "_rate_over_possible"] = numerator / possible if possible else None
        result[metric + "_rate_over_executions"] = numerator / result["world_executions"] if result["world_executions"] else None
        result[metric + "_rate_over_record_calls"] = numerator / result["actual_record_calls"] if result["actual_record_calls"] else None
    result["field_correct"] = {field: sum(bool(turn["score"] and turn["score"]["field_correct"][field]) for turn in turns) for field in FIELDS}
    result["format_counts"] = {name: sum(turn["score"] is not None and turn["score"]["format"] == name for turn in turns)
                               for name in ("exact", "json_noncanonical", "fenced", "unparseable")}
    return result


def _prior(turn):
    execution = turn["execution"]
    if execution is None:
        return "no_execution"
    if execution["prediction_ambiguous"]:
        return "ambiguous"
    return "absent" if execution["predicted"] is None else "available"


def _relation(turn):
    prior = _prior(turn)
    if prior != "available":
        return "unavailable" if prior == "absent" else prior
    execution = turn["execution"]
    return "matched" if execution["predicted"] == execution["observed"] else "mismatched"


def _summary(episodes):
    turns = [turn for episode in episodes for turn in episode["turns"]]
    result = _V2._summary(episodes)
    result.update(_counts(turns))
    result["strata"] = {
        "cue": {cue: _counts([turn for episode in episodes if episode["cue_stratum"] == cue for turn in episode["turns"]])
                for cue in WAKE_TEMPLATES},
        "tick": {str(tick): _counts([turn for turn in turns if turn["tick"] == tick]) for tick in (1, 2)},
        "prior": {name: _counts([turn for turn in turns if _prior(turn) == name]) for name in ("available", "absent", "ambiguous", "no_execution")},
        "relation": {name: _counts([turn for turn in turns if _relation(turn) == name]) for name in ("matched", "mismatched", "unavailable", "ambiguous", "no_execution")},
        "observed": {name: _counts([turn for turn in turns if ("no_execution" if turn["execution"] is None else
                           "true" if turn["execution"]["observed"] else "false") == name]) for name in ("true", "false", "no_execution")},
    }
    return result


def run_state(state, backend, *, dependencies=None, binding=None):
    """Six fixed cells, actual TRY execution, raw records; no eligibility gate."""
    require(state in STATES, "unknown post-memory state")
    require(callable(backend), "backend must be callable")
    dependencies = dependencies or load_dependencies()
    binding = copy.deepcopy(binding if binding is not None else {"kind": "unverified_injected_backend"})
    canonical(binding)
    events, episodes = [], []
    for case in schedule():
        eid = case["episode_id"]
        game = dependencies.game_class()
        turns = []
        for tick in (1, 2):
            history = earlier_transcript(turns[-1] if turns else None)
            prompt = WAKE_TEMPLATES[case["cue_stratum"]].format(eid=eid, tick=tick, earlier_transcript=history)
            wake = _V2._call(backend, _request(state, case, tick, "wake", prompt), events)
            turn = {"tick": tick, "wake": wake, "execution": None, "record": None, "score": None,
                    "status": "INVALID_WAKE", "errors": list(wake["errors"])}
            if not wake["errors"]:
                try:
                    execution = _V2._execute(game, dependencies, wake, state, eid, tick, events)
                except (ValueError, TypeError, KeyError) as error:
                    turn["errors"].append(str(error))
                else:
                    turn["execution"] = execution
                    record_prompt = dependencies.interface.record_prompt(execution, wake["response"]["raw"], PROTOCOL)
                    if tick == 2:
                        record_prompt = history + "\n" + record_prompt
                    record = _V2._call(backend, _request(state, case, tick, "record", record_prompt, execution["sha256"]), events)
                    turn["record"] = record
                    response = record["response"]
                    turn["score"] = score_record(response.get("raw"), response.get("finish_reason"), execution,
                                                 dependencies, source_errors=record["errors"])
                    turn["errors"].extend(record["errors"])
                    turn["status"] = "PRODUCTION_RECORD" if turn["score"]["production_eligible"] else "RECORD_REJECTED"
            turns.append(turn)
        episodes.append(dict(case, turns=turns))
    result = {"schema": SCHEMA, "state": state, "binding": binding, "contract": contract(dependencies),
              "episodes": episodes, "events": events, "summary": _summary(episodes),
              "native_identity_verified": False, "qualification": QUALIFICATION}
    result["capture_sha256"] = digest(result)
    return result


def audit_capture(capture, *, dependencies=None):
    """Reexecute captured TRYs and check exact requests/raw failures/source joins."""
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
    """Describe complete or partial cells; signs/harms never gate this report."""
    dependencies = dependencies or load_dependencies()
    require(type(captures) in (list, tuple) and captures, "provide nonempty captures")
    summaries = {}
    for capture in captures:
        state = capture["state"]
        require(state not in summaries, "duplicate state")
        audit_capture(capture, dependencies=dependencies)
        require(capture["contract"] == contract(dependencies), "state contract differs")
        summaries[state] = copy.deepcopy(capture["summary"])
    paired = {}
    for seed in range(3):
        write, control = (f"perception_seed{seed}_{arm}" for arm in ("WRITE", "LR0"))
        present = write in summaries and control in summaries
        paired[str(seed)] = {"available": present, "possible_records_per_arm": 16,
            "WRITE_minus_LR0": {metric: summaries[write][metric] - summaries[control][metric]
                                for metric in ("production_eligible", "content_correct", "strict_canonical")} if present else None}
    return {"schema": SCHEMA, "comparison": "paired_schedule_interactive_record_formation_not_identical_experience",
            "episode_ids": list(episode_ids()), "episode_ids_sha256": EPISODE_IDS_SHA256,
            "possible_records_per_state": 16, "states": summaries, "paired_by_seed": paired,
            "missing_states": [state for state in STATES if state not in summaries],
            "native_identity_verified": False, "engineering_prerequisite_verified": False,
            "outcome_gate": None, "automatic_pass": False, "claim": QUALIFICATION}
