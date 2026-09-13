"""CPU fixed-guidance formation/replay/projector; no native identity, fitting or launch."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from types import ModuleType, SimpleNamespace


SCHEMA = "astra_fixed_guidance_record_20260913_v1"
COMPILER = "astra_fixed_guidance_source_withdrawn_20260913_v1"
V2_PATH = "/tmp/astra_level1_real_record_core_20260913_v2.py"
V2_SHA256 = "b023a4321d0a20e465c96914316a730fbb2dd897c11369a9eb62d2d8f1248ef5"
MEMORY_PATH = "/tmp/astra_real_record_memory_core_20260913.py"
MEMORY_SHA256 = "2c5538f5b63cbb4e592f40822561b4d62595ab3c9d7d193f084b91f9a064e8ef"
SOURCE_ROOT = "/data/home/rohing/dream-state"
PROTOCOL_RELATIVE = "research_notes/astra_memos/ASTRA_PARENTED_RECORD_DEV_2026-09-13.md"
PROTOCOL_SHA256 = "bae29cfc48d9ae0922531d306bef1434bcc7296f2ae71a4ad6493da2a5dfb964"
SCHEDULE_SHA256 = "b251dec197f94d35960367f723f833f5ef0689396da36a8bff6e1d5400cb08c2"
ARMS = ("P", "N")
STATES = tuple(f"perception_seed{seed}_{arm}" for seed in range(3) for arm in (*ARMS, "INITIAL"))
CONTACTS = {
    "P": "Keep the prediction you stated before acting separate from the observation returned afterward. Record that prior unchanged; do not replace it with the outcome or with null. Derive the relation by comparing those two values. If no prediction was stated, record null and unavailable.",
    "N": "This part of the session is complete. Continue with the next scheduled exercises using the task instructions. You may briefly acknowledge this message before proceeding.",
}
RESTATE_TEMPLATE = "Session contact:\n{contact}\n\nRestate this message in your own words in 2-3 sentences."
CONTEXT_TEMPLATE = "Temporary session contact:\n{contact}\nChild's own restatement (verbatim):\n{restatement}\nEnd temporary session context.\n\n"
MAX_OUTPUT_TOKENS = {"wake": 96, "record": 192, "restate": 120}
TEMPERATURE = {"wake": 0.0, "record": 0.0, "restate": 0.5}
GENERATION_SEED = 0
EXAMPLE_BLOCK = "Syntax example only (these numbers and this prediction are arbitrary, not a known answer):\nPREDICT: T\nACT: TRY 2,5,9\n"
QUALIFICATION = "fixed_author_guidance_amortization_not_adaptive_parenting_no_H1_H2_or_automatic_pass"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _load(path, pin, name):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == pin, "frozen dependency pin mismatch: " + str(path))
    module = ModuleType(name)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


_V2 = _load(V2_PATH, V2_SHA256, "fixed_guidance_v2")
_MEMORY = _load(MEMORY_PATH, MEMORY_SHA256, "fixed_guidance_memory")
canonical = _V2.canonical
digest = _V2.digest
sha_text = _V2.sha_text
score_record = _V2.score_record
PROTOCOL = _V2.PROTOCOL
PINS = dict(_V2.PINS)
WAKE_TEMPLATE = _V2.WAKE_TEMPLATE.replace("Fresh DEV mystery-box", "Fresh mystery-box", 1)
require(WAKE_TEMPLATE.count(EXAMPLE_BLOCK) == 1, "frozen comma example differs")


def load_dependencies(source_root=SOURCE_ROOT, *, core_path=V2_PATH, memory_path=MEMORY_PATH, protocol_path=None):
    frozen = _load(core_path, V2_SHA256, "fixed_guidance_verified_v2")
    _load(memory_path, MEMORY_SHA256, "fixed_guidance_verified_memory")
    protocol_bytes = Path(protocol_path if protocol_path is not None else Path(source_root) / PROTOCOL_RELATIVE).read_bytes()
    require(hashlib.sha256(protocol_bytes).hexdigest() == PROTOCOL_SHA256, "fixed-guidance protocol pin mismatch")
    dependencies = frozen.load_dependencies(source_root)
    return SimpleNamespace(game_class=dependencies.game_class, interface=dependencies.interface,
        manifest={**copy.deepcopy(dependencies.manifest), "formation_v2_core_sha256": V2_SHA256,
                  "memory_projector_sha256": MEMORY_SHA256, "protocol_sha256": PROTOCOL_SHA256})


def schedule():
    result = {}
    for split in ("dev", "confirm"):
        prefix = f"rrparent-20260913-v1/{split}"
        result[split] = {
            "pre": [f"{prefix}/pre/lesson{lesson}" for lesson in range(2)],
            "apply": [[f"{prefix}/apply/lesson{lesson}/episode{episode}" for episode in range(4)] for lesson in range(2)],
            "held": [f"{prefix}/held/episode{episode}" for episode in range(8)],
        }
    require(digest(result) == SCHEDULE_SHA256, "frozen schedule differs")
    return result


def episode_ids(split="dev", phase="formation"):
    require(type(split) is str and split in ("dev", "confirm"), "unknown split")
    require(type(phase) is str and phase in ("formation", "held"), "unknown phase")
    partition = schedule()[split]
    if phase == "held":
        return tuple(partition["held"])
    return tuple(eid for lesson in range(2) for eid in (partition["pre"][lesson], *partition["apply"][lesson]))


def check_disjointness(prior_episode_ids=()):
    require(type(prior_episode_ids) in (tuple, list) and all(type(eid) is str and eid for eid in prior_episode_ids),
            "prior IDs must be explicit strings")
    ids = [eid for split in ("dev", "confirm") for phase in ("formation", "held") for eid in episode_ids(split, phase)]
    require(len(ids) == len(set(ids)) == 36, "source namespace overlap")
    require(not set(ids) & (set(prior_episode_ids) | set(_V2.episode_ids())), "previous exposure ID collision")
    return dict(schedule_sha256=SCHEDULE_SHA256, distinct_ids=36, disjoint=True,
                prior_episode_ids_sha256=digest(sorted(prior_episode_ids)),
                scope="listed IDs only; not unseen-rule/triple/model exposure certification")


def contract(dependencies):
    require(dependencies.manifest.get("protocol_sha256") == PROTOCOL_SHA256, "unbound protocol dependencies")
    return dict(schema=SCHEMA, compiler=COMPILER, states=list(STATES), arms=list(ARMS), schedule=schedule(),
        protocol_document=dict(logical_path=PROTOCOL_RELATIVE, sha256=PROTOCOL_SHA256),
        schedule_sha256=SCHEDULE_SHA256, contacts=dict(CONTACTS), contact_sha256={arm: sha_text(text) for arm, text in CONTACTS.items()},
        restate_template=RESTATE_TEMPLATE, temporary_context_template=CONTEXT_TEMPLATE,
        context_scope="current lesson apply wake and record only; pre and held have none; raw restatement retained even on length",
        wake_template=WAKE_TEMPLATE, syntax_example=EXAMPLE_BLOCK,
        record_instruction=dependencies.interface.record_instruction(PROTOCOL), protocol=PROTOCOL,
        record_template="unchanged production record_prompt plus score-free within-episode earlier transcript; apply also prepends temporary context",
        history_visibility="raw wake, raw world outcome, raw child record, finish reasons and attempt only; no eligibility/status/field scores",
        first_history=_V2.earlier_transcript(None), max_output_tokens=dict(MAX_OUTPUT_TOKENS),
        temperature=dict(TEMPERATURE), generation_seed=GENERATION_SEED,
        formation=dict(lessons=2, pre_episodes=2, apply_episodes=8, wake_calls=20, maximum_record_calls=20,
                       restatement_calls=2, parent_model_calls=0, fixed_contacts=2, maximum_calls=42, sleep_slots=16),
        held=dict(episodes=8, wake_calls=16, maximum_record_calls=16, maximum_calls=32,
                  parent_model_calls=0, fixed_contacts=0, restatement_calls=0),
        campaign_limits=dict(calls_per_seed=300, calls_three_seeds=900, maximum_updates_per_arm=128,
                             maximum_updates_three_seeds=768, native_seconds_per_seed=7200, collection_seconds=180,
                             old_retention="two descendants only; pinned historical original baseline imported, not rerun",
                             enforcement="native lifecycle responsibility; CPU core does not run fits/retention/controllers"),
        dependencies=copy.deepcopy(dependencies.manifest), native_identity_verified=False,
        qualification=QUALIFICATION, automatic_pass=False, outcome_gate=None)


def build_manifest(dependencies=None, *, prior_episode_ids=()):
    dependencies = dependencies or load_dependencies()
    return dict(contract=contract(dependencies), disjointness=check_disjointness(prior_episode_ids))


def _state(state, phase):
    require(type(state) is str and state in STATES, "unknown state")
    arm = state.rsplit("_", 1)[1]
    require(phase == "held" or arm in ARMS, "INITIAL is held-only")
    return arm


def _request(state, split, phase, case, tick, kind, prompt, source_execution_sha256=None, contact_sha256=None):
    request = dict(state=state, split=split, phase=phase, episode_id=case["episode_id"],
                   stage=case["stage"], lesson=case["lesson"], episode_index=case["episode_index"], tick=tick, kind=kind,
                   input_messages=[dict(role="user", content=prompt)], max_output_tokens=MAX_OUTPUT_TOKENS[kind],
                   temperature=TEMPERATURE[kind], seed=GENERATION_SEED,
                   source_execution_sha256=source_execution_sha256, contact_sha256=contact_sha256)
    request["request_id"] = digest([SCHEMA, request])
    return request


def _history(previous):
    if previous is None:
        return _V2.earlier_transcript(None)
    wake = previous["wake"]["response"]
    record = previous["record"]["response"] if previous["record"] else None
    execution = previous["execution"]
    return _V2.EARLIER_HEADER + canonical(dict(attempt=previous["tick"], wake_raw=wake.get("raw"),
        wake_finish_reason=wake.get("finish_reason"), outcome_raw=execution["outcome"] if execution else None,
        record_raw=record.get("raw") if record else None, record_finish_reason=record.get("finish_reason") if record else None))


def _episode(state, split, phase, case, backend, dependencies, events, context="", contact_pin=None):
    game = dependencies.game_class()
    turns = []
    for tick in (1, 2):
        history = _history(turns[-1] if turns else None)
        prompt = context + WAKE_TEMPLATE.format(eid=case["episode_id"], tick=tick, earlier_transcript=history)
        wake = _V2._call(backend, _request(state, split, phase, case, tick, "wake", prompt, contact_sha256=contact_pin), events)
        turn = dict(tick=tick, wake=wake, execution=None, record=None, score=None,
                    status="INVALID_WAKE", errors=list(wake["errors"]))
        if not wake["errors"]:
            try:
                execution = _V2._execute(game, dependencies, wake, state, case["episode_id"], tick, events)
            except (ValueError, TypeError, KeyError) as error:
                turn["errors"].append(str(error))
            else:
                turn["execution"] = execution
                prompt = dependencies.interface.record_prompt(execution, wake["response"]["raw"], PROTOCOL)
                if tick == 2:
                    prompt = history + "\n" + prompt
                record = _V2._call(backend, _request(state, split, phase, case, tick, "record", context + prompt,
                                   source_execution_sha256=execution["sha256"], contact_sha256=contact_pin), events)
                turn["record"] = record
                response = record["response"]
                turn["score"] = score_record(response.get("raw"), response.get("finish_reason"), execution,
                                               dependencies, source_errors=record["errors"])
                turn["errors"].extend(record["errors"])
                turn["status"] = "PRODUCTION_RECORD" if turn["score"]["production_eligible"] else "RECORD_REJECTED"
        turns.append(turn)
    return dict(case, turns=turns)


def _counts(episodes):
    turns = [turn for episode in episodes for turn in episode["turns"]]
    result = dict(possible_records=len(turns), wake_calls=len(turns),
        world_executions=sum(turn["execution"] is not None for turn in turns),
        record_calls=sum(turn["record"] is not None for turn in turns),
        invalid_wakes=sum(turn["execution"] is None for turn in turns),
        unfinished_wakes=sum(turn["wake"]["response"].get("finish_reason") != "stop" for turn in turns),
        unfinished_records=sum(turn["record"] is not None and turn["record"]["response"].get("finish_reason") != "stop" for turn in turns))
    for metric in ("production_eligible", "content_correct", "strict_canonical"):
        value = sum(turn["score"] is not None and turn["score"][metric] is True for turn in turns)
        result[metric] = value
        result[metric + "_over_possible"] = value / len(turns) if turns else None
        result[metric + "_over_records"] = value / result["record_calls"] if result["record_calls"] else None
    result["field_correct"] = {field: sum(turn["score"] is not None and turn["score"]["field_correct"][field] is True for turn in turns)
                               for field in _V2.FIELDS}
    return result


def run_state(state, backend, *, phase="formation", split="dev", dependencies=None, binding=None):
    """One bounded child state. Confirmation requires explicit split='confirm'."""
    episode_ids(split, phase)
    arm = _state(state, phase)
    require(callable(backend), "backend must accept one request dictionary")
    dependencies = dependencies or load_dependencies()
    binding = copy.deepcopy(binding if binding is not None else dict(kind="unverified_injected_backend"))
    canonical(binding)
    partition = schedule()[split]
    events, episodes, contacts = [], [], []
    if phase == "formation":
        for lesson in range(2):
            pre_case = dict(episode_id=partition["pre"][lesson], stage="pre", lesson=lesson, episode_index=0)
            episodes.append(_episode(state, split, phase, pre_case, backend, dependencies, events))
            contact = _V2._event(events, dict(kind="fixed_contact", state=state, split=split, lesson=lesson,
                source="author_supplied_exact_literal", arm=arm, raw=CONTACTS[arm], text_sha256=sha_text(CONTACTS[arm]),
                parent_model_calls=0, preceding_episode_id=pre_case["episode_id"]))
            restate_case = dict(pre_case, stage="restate")
            restatement = _V2._call(backend, _request(state, split, phase, restate_case, 0, "restate",
                RESTATE_TEMPLATE.format(contact=CONTACTS[arm]), contact_sha256=contact["sha256"]), events)
            raw = restatement["response"].get("raw")
            context = CONTEXT_TEMPLATE.format(contact=CONTACTS[arm], restatement=raw if type(raw) is str else "")
            contacts.append(dict(lesson=lesson, contact=contact, restatement=restatement,
                                 apply_context_sha256=sha_text(context)))
            for index, eid in enumerate(partition["apply"][lesson]):
                case = dict(episode_id=eid, stage="apply", lesson=lesson, episode_index=index)
                episodes.append(_episode(state, split, phase, case, backend, dependencies, events, context, contact["sha256"]))
    else:
        for index, eid in enumerate(partition["held"]):
            case = dict(episode_id=eid, stage="held", lesson=None, episode_index=index)
            episodes.append(_episode(state, split, phase, case, backend, dependencies, events))
    require([episode["episode_id"] for episode in episodes] == list(episode_ids(split, phase)), "episode order differs")
    calls = [event for event in events if event["kind"] == "call"]
    summary = _counts(episodes)
    summary.update(calls=len(calls), parent_model_calls=0, fixed_contacts=len(contacts),
        restatement_calls=sum(event["request"]["kind"] == "restate" for event in calls),
        input_utf8_bytes=sum(len(message["content"].encode("utf-8")) for event in calls for message in event["request"]["input_messages"]),
        output_utf8_bytes=sum(len(event["response"]["raw"].encode("utf-8")) for event in calls if type(event["response"].get("raw")) is str),
        token_accounting="not tokenized; native lifecycle must report actual prompt/output tokens, not equate bytes with tokens",
        stages={stage: _counts([episode for episode in episodes if episode["stage"] == stage]) for stage in ("pre", "apply", "held")},
        turn={str(tick): _counts([dict(turns=[turn for turn in episode["turns"] if turn["tick"] == tick]) for episode in episodes]) for tick in (1, 2)})
    require(len(calls) <= (42 if phase == "formation" else 32), "call cap exceeded")
    result = dict(schema=SCHEMA, state=state, arm=arm, phase=phase, split=split, binding=binding,
        contract=contract(dependencies), episodes=episodes, contacts=contacts, events=events, summary=summary,
        qualification=QUALIFICATION, native_identity_verified=False, automatic_pass=False)
    result["capture_sha256"] = digest(result)
    return result


def run_formation(state, backend, *, split="dev", dependencies=None, binding=None):
    return run_state(state, backend, phase="formation", split=split, dependencies=dependencies, binding=binding)


def run_held(state, backend, *, split="dev", dependencies=None, binding=None):
    return run_state(state, backend, phase="held", split=split, dependencies=dependencies, binding=binding)


def audit_capture(capture, *, dependencies=None):
    """CPU replay of the exact fixed contacts, requests, failures, events and scores."""
    require(type(capture) is dict and capture.get("schema") == SCHEMA, "capture schema differs")
    dependencies = dependencies or load_dependencies()
    supplied = copy.deepcopy(capture)
    pin = supplied.pop("capture_sha256")
    require(digest(supplied) == pin, "capture hash differs")
    calls = [event for event in capture["events"] if event["kind"] == "call"]
    index = 0
    def replay(request):
        nonlocal index
        require(index < len(calls), "missing replay call")
        event = calls[index]
        index += 1
        require(canonical(request) == canonical(event["request"]), "exact request/source join differs")
        return copy.deepcopy(event["response"])
    rebuilt = run_state(capture["state"], replay, phase=capture["phase"], split=capture["split"],
                        dependencies=dependencies, binding=capture["binding"])
    require(index == len(calls) and canonical(rebuilt) == canonical(capture), "capture differs from deterministic execution replay")
    return dict(consistent=True, capture_sha256=pin, calls_replayed=index,
                summary=copy.deepcopy(capture["summary"]), native_identity_verified=False)


def project_capture(capture, *, dependencies=None):
    """All eligible apply slots, exact targets; never pre, restatement or held."""
    dependencies = dependencies or load_dependencies()
    audit = audit_capture(capture, dependencies=dependencies)
    require(capture["phase"] == "formation", "held capture cannot supply sleep material")
    rows, refused, triples = [], [], set()
    for episode in capture["episodes"]:
        if episode["stage"] != "apply":
            continue
        task_id = episode["episode_id"]
        for turn in episode["turns"]:
            public_id = f"{task_id}#t{turn['tick']}"
            execution, record, score = turn["execution"], turn["record"], turn["score"]
            if record is None or score["production_eligible"] is not True:
                refused.append(dict(task_id=task_id, tick=turn["tick"], reason="no_record_call" if record is None else "record_not_production_eligible",
                    errors=copy.deepcopy(turn["errors"] if record is None else score["source_completion_errors"] + score["production_errors"])))
                continue
            raw = record["response"]["raw"]
            require(type(raw) is str and record["response"]["finish_reason"] == "stop" and not record["errors"], "invalid admitted response")
            require(record["request"]["source_execution_sha256"] == execution["sha256"] and
                    execution["execution_id"] == f"{capture['state']}:{public_id}", "record execution join differs")
            rows.append(dict(row_id=f"{capture['state']}:{public_id}",
                input_messages=_MEMORY._messages(task_id, public_id, "exact"),
                paraphrase_input_messages=_MEMORY._messages(task_id, public_id, "paraphrase"),
                raw_target=raw, target_sha256=sha_text(raw), encoding_contract=copy.deepcopy(_MEMORY.ENCODING_CONTRACT),
                source=dict(state=capture["state"], split=capture["split"], task_id=task_id, tick=turn["tick"],
                    lesson=episode["lesson"], public_execution_id=public_id, execution_id=execution["execution_id"],
                    execution_sha256=execution["sha256"], wake_request_id=turn["wake"]["request"]["request_id"],
                    record_request_id=record["request"]["request_id"], record_event_sha256=record["sha256"],
                    capture_sha256=capture["capture_sha256"])))
            triples.add(tuple(execution["values"]))
    require(len(rows) + len(refused) == 16 and len({row["row_id"] for row in rows}) == len(rows), "apply slot count/identity differs")
    return dict(schema=COMPILER, status="WRITE_AVAILABLE" if rows else "NO_WRITE", state=capture["state"], split=capture["split"],
        reason="admitted_apply_records_not_authorization" if rows else "no_eligible_apply_records", rows=rows, refused=refused,
        counts=dict(possible_slots=16, admitted_rows=len(rows), refused_slots=len(refused),
                    distinct_raw_targets=len({row["target_sha256"] for row in rows}), distinct_triples=len(triples),
                    episodes_with_admissions=len({row["source"]["task_id"] for row in rows}), excluded_pre_slots=4, excluded_restatements=2),
        source_proof=dict(capture_sha256=capture["capture_sha256"], contract_sha256=digest(capture["contract"]),
                          binding_sha256=digest(capture["binding"]), audit_consistent=audit["consistent"],
                          schedule_sha256=SCHEDULE_SHA256, dependencies=copy.deepcopy(dependencies.manifest)),
        qualification=dict(compiler_choice="source-withdrawn public ID cue, exact raw child target; not unchanged native context",
            order="all eligible apply rows in source order; no selection, rewrite, deduplication or replacement",
            excluded="pre, held, contact and restatement text never enters training input or target",
            independence="repeated targets/triples/turns are not independent learners", native_identity_verified=False,
            tokenizer_verified=False, automatic_pass=False))


def compare_states(captures, *, dependencies=None):
    """Descriptive common-schedule summaries; does not certify a complete cohort."""
    require(type(captures) in (list, tuple) and len(captures) > 0, "captures required")
    dependencies = dependencies or load_dependencies()
    first = captures[0]
    states = {}
    for capture in captures:
        require(capture["state"] not in states, "duplicate state")
        require(capture["phase"] == first["phase"] and capture["split"] == first["split"], "mixed phase/split")
        audit_capture(capture, dependencies=dependencies)
        states[capture["state"]] = copy.deepcopy(capture["summary"])
    pairs = {}
    for seed in range(3):
        coached, neutral = (f"perception_seed{seed}_{arm}" for arm in ARMS)
        available = coached in states and neutral in states
        metric_source = (lambda summary: summary["stages"]["apply"]) if first["phase"] == "formation" else (lambda summary: summary)
        pairs[str(seed)] = dict(available=available, P_minus_N={metric: metric_source(states[coached])[metric] - metric_source(states[neutral])[metric]
            for metric in ("production_eligible", "content_correct", "strict_canonical")} if available else None)
    return dict(schema=SCHEMA, phase=first["phase"], split=first["split"], states=states, paired_by_seed=pairs,
        missing_states=[state for state in STATES if (first["phase"] == "held" or not state.endswith("_INITIAL")) and state not in states],
        comparison="matched initial tasks and budgets, not identical child experience/material or equal actual compute",
        parent_model_calls=0, native_identity_verified=False, automatic_pass=False, qualification=QUALIFICATION)
