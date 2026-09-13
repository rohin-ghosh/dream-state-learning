"""Inference-only fixed-lesson alignment; no native execution, writer or launch."""
from __future__ import annotations

from collections import Counter
import copy
import difflib
import hashlib
import json
from pathlib import Path
import re
from types import ModuleType, SimpleNamespace


SCHEMA = "astra_parenting_alignment_inference_20260913_v1"
SOURCE_ROOT = "/data/home/rohing/dream-state"
PROTOCOL_PATH = SOURCE_ROOT + "/research_notes/astra_memos/ASTRA_PARENTING_ALIGNMENT_DEV_2026-09-13.md"
PROTOCOL_SHA256 = "5c53d6aa850b3a3a409c255ab9b28ce3b090f7325f35688437e42a86b1cccce5"
PARENTED_PATH = "/tmp/astra_parented_record_core_20260913.py"
PARENTED_SHA256 = "68ef29fcc162dbbf5fe1becf4c09b86ed5bc1f8a79e373276dd8ba3cda88e688"
ARMS = ("ALIGNED", "SWAPPED", "NO_PARENT")
STATES = tuple(f"perception_seed{seed}_{arm}" for seed in range(3) for arm in ARMS)
MAX_OUTPUT_TOKENS = {"restate": 160, "wake": 256, "record": 384}
TEMPERATURE = {kind: 0.0 for kind in MAX_OUTPUT_TOKENS}
GENERATION_SEED = 0
ROOT_PLAN_PINS = (
    "3f4fd56868d2c42fe776c72ad4c5c93b15284ad16cd87c06849ba50419f67900",
    "563d6799cd4b4030844f9dc037b931856132771e8e66e005b139e3f9dae96b47",
    "bd4c5c4ec37da0a3e6611d430441d786beee2f338200f64ff64d2c40a8875910",
)
ROOT_WEIGHT_PINS = (
    "8bfe8b9d647b58b064733ed24d8aaa97cd79d7012795232305838a23ac415432",
    "c9700a2f46b36e64ce9e1845cd4601d3d0da086afbaba9efbc93012af936e0e2",
    "5d198acfc7bf2f2c552b6b180688bce5d7fe00b1afd2eea7d056fc44a2e505da",
)
LESSONS = {
    "P": "Keep the prediction made before an action separate from the observation returned afterward. Preserve both values from the public receipt and compare them to state whether they match or differ. Never replace the earlier prediction with the observed outcome.",
    "C": "Select the most recent actually executed event using the public receipt times, not the order of display. Keep its receipt identity, action and returned observation together. Never take the action from one receipt and the outcome from another receipt.",
}
RESTATE_TEMPLATE = "Message:\n{lesson}\n\nRestate this message in your own words."
WAKE_INSTRUCTION = (
    "Use the public task state below. Produce a relevant-state NOTE and choose one fresh action. "
    "Return only one JSON object with keys note, prediction, action. note is an object describing the relevant public state; "
    "prediction is your Boolean prediction for your fresh action; action is an object with kind set to TRY and values set to an array "
    "of exactly three integers between -9999 and 9999. No code fence or additional text."
)
RECORD_INSTRUCTION = (
    "Make a record of this task and your fresh action. Return only one JSON object with keys address, source, event. "
    "address is the given record address. source is your relevant-state NOTE about the original public task. "
    "event contains exactly receipt_id, try, predicted, observed, relation for your fresh action. "
    "try is its three integers; predicted is the Boolean you stated before acting; observed is its returned Boolean; "
    "relation is matched when those Booleans agree and mismatched otherwise. Keep source and event separate. "
    "No code fence or additional text."
)
RESTATE_PATTERNS = {
    "P": {
        "prior_scope": r"\b(prediction|predicted|prior)\b.*\b(before|earlier|prior)\b|\b(before|earlier|prior)\b.*\b(prediction|predicted|acting|action)\b",
        "outcome_scope": r"\b(observation|observed|outcome)\b.*\b(after|afterward|returned|later)\b|\b(after|afterward|returned|later)\b.*\b(observation|observed|outcome)\b",
        "separation": r"\b(separate|preserve|retain|keep both|keep them distinct)\b",
        "comparison": r"\b(compare|comparison|match|matches|agree|equal|differ)\b",
    },
    "C": {
        "chronology": r"\b(latest|most recent|newest)\b",
        "executed_scope": r"\b(executed|actually happened|actually performed)\b",
        "time_scope": r"\b(time|times|timestamp|timestamps|chronological|chronology)\b",
        "action": r"\b(action|try)\b",
        "outcome": r"\b(observation|observed|outcome)\b",
        "same_receipt": r"\b(same receipt|same event|together|one receipt)\b",
    },
}
RESTATE_CONTRADICTIONS = {
    "P": (r"\b(?:do not|don't|never|skip) compare\b", r"(?<!not )(?<!never )\breplace (?:the )?(?:earlier |prior )?prediction with (?:the )?(?:observed )?outcome\b"),
    "C": (r"\b(?:select|choose|use) (?:the )?(?:earliest|oldest|first displayed|last displayed)\b", r"\b(?:ignore|disregard) (?:the )?(?:times|timestamps|chronology)\b"),
}
NOTE_ALIASES = {
    "predicted": ("predicted", "prediction", "prior", "earlier_prediction"),
    "observed": ("observed", "observation", "outcome"),
    "relation": ("relation", "comparison"),
    "receipt_id": ("receipt_id", "event_id", "id", "latest_receipt_id"),
    "try": ("try", "action", "values"),
}
RELATION_ALIASES = {
    "matched": "matched", "match": "matched", "same": "matched", "equal": "matched", "agreement": "matched",
    "mismatched": "mismatched", "mismatch": "mismatched", "different": "mismatched", "unequal": "mismatched", "disagreement": "mismatched",
}
QUALIFICATION = "immediate_fixed_lesson_alignment_development_diagnostic_not_persistent_parenting_or_H1_H2"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def sha_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_dependencies(source_root=SOURCE_ROOT, *, protocol_path=PROTOCOL_PATH, parented_path=PARENTED_PATH):
    raw = Path(parented_path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PARENTED_SHA256, "frozen parented core differs")
    require(hashlib.sha256(Path(protocol_path).read_bytes()).hexdigest() == PROTOCOL_SHA256, "alignment protocol differs")
    parented = ModuleType("alignment_frozen_parented")
    exec(compile(raw, str(parented_path), "exec"), parented.__dict__)
    dependencies = parented._V2.load_dependencies(source_root)
    return SimpleNamespace(game_class=dependencies.game_class, interface=dependencies.interface, parented=parented,
        manifest=dict(copy.deepcopy(dependencies.manifest), parented_core_sha256=PARENTED_SHA256, protocol_sha256=PROTOCOL_SHA256))


def root_binding(seed):
    return dict(learner_seed=seed, parent_plan_sha256=ROOT_PLAN_PINS[seed],
        adapter=f"/localhome/local-rohing/astra_diagnostics/level1_perception_seed{seed}_20260913_attempt1/run/fit/adapter",
        adapter_model_sha256=ROOT_WEIGHT_PINS[seed])


def state_parts(state):
    require(state in STATES, "original perception alignment state required")
    for seed in range(3):
        for arm in ARMS:
            if state == f"perception_seed{seed}_{arm}":
                return seed, arm
    raise ValueError("unknown state")


def opaque(kind, *parts):
    return "pa-" + digest([SCHEMA, kind, *parts])[:28]


def world_result(game, deps, world_id, values, predicted):
    require(type(values) is list and len(values) == 3 and all(type(value) is int and -9999 <= value <= 9999 for value in values), "strict bounded integer action required")
    require(predicted is None or type(predicted) is bool, "typed prior required")
    text = ("" if predicted is None else "PREDICT: " + ("T" if predicted else "F") + "\n") + "ACT: TRY " + ",".join(map(str, values))
    action = deps.interface.parse_action(text, "interaction_v3")
    require(action["kind"] == "try" and action["values"] == values and action["predicted"] is predicted and not action["prediction_ambiguous"], "frozen action adapter mismatch")
    unused_reward, outcome = game.evaluate(SimpleNamespace(eid=world_id), action["action"])
    match = re.fullmatch(r"the box says: (True|False) for \((-?[0-9]+),(-?[0-9]+),(-?[0-9]+)\)", outcome)
    require(match is not None and [int(value) for value in match.groups()[1:]] == values, "real world receipt/action mismatch")
    return dict(values=list(values), predicted=predicted, observed=match.group(1) == "True", outcome=outcome,
                outcome_sha256=sha_text(outcome), dispatched_action=action["action"])


def make_task(seed, family, variant, position, deps):
    task_id = opaque("task", seed, family, variant, position)
    world_id = opaque("world", seed, family, variant, position)
    game = deps.game_class()
    desired = [bool(position % 2)] if family == "P" else [bool(position % 2), not bool(position % 2)]
    receipts, probes = [], []
    for receipt_index, desired_observed in enumerate(desired):
        predicted = bool(position // 2) if family == "P" else None
        for attempt in range(512):
            bits = bytes.fromhex(digest([SCHEMA, "public-action", seed, family, variant, position, receipt_index, attempt]))
            values = [int(value) % 19 - 9 for value in bits[:3]]
            outcome = world_result(game, deps, world_id, values, predicted)
            probes.append(dict(receipt_index=receipt_index, attempt=attempt, **outcome))
            if outcome["observed"] is desired_observed:
                break
        else:
            raise ValueError("bounded public world schedule construction failed")
        receipts.append(dict(receipt_id=opaque("public-receipt", task_id, receipt_index), time=receipt_index+1,
                             **{"try": values}, predicted=predicted, observed=outcome["observed"]))
    display = list(reversed(receipts)) if family == "C" and position // 2 else list(receipts)
    address = opaque("address", task_id)
    public = dict(task_id=task_id, address=address, receipts=display,
                  receipt_origin="Harness-provided earlier public environment events; not your own actions.")
    return dict(task_id=task_id, address=address, family=family, variant=variant, position=position, world_id=world_id,
                public=public, ordinary_prompt=WAKE_INSTRUCTION+"\nPublic task:\n"+canonical(public),
                public_world_evaluations=probes, public_receipts=receipts)


def tasks_for_seed(seed, deps):
    require(type(seed) is int and seed in (0, 1, 2), "original seed required")
    families = ("C", "P", "C", "P") if seed == 1 else ("P", "C", "P", "C")
    tasks = []
    for block_index, family in enumerate(families):
        delivery = block_index // 2
        variant = 1-delivery if seed == 1 else delivery
        for position in range(4):
            tasks.append(dict(make_task(seed, family, variant, position, deps), block_index=block_index,
                              delivery=delivery, task_index=4*block_index+position))
    return tasks


def build_manifest(dependencies, *, prior_task_ids=(), prior_ids=None):
    deps = dependencies
    require(deps.manifest["parented_core_sha256"] == PARENTED_SHA256 and deps.manifest["protocol_sha256"] == PROTOCOL_SHA256 and
            deps.manifest["full_source_sha256"] == deps.parented.PINS, "frozen dependency manifest differs")
    require(prior_ids is None or not prior_task_ids, "supply one prior-ID parameter")
    supplied = prior_task_ids if prior_ids is None else prior_ids
    require(type(supplied) in (tuple, list) and all(type(value) is str and value for value in supplied) and len(set(supplied)) == len(supplied), "explicit unique prior task IDs required")
    prior = set(supplied) | set(deps.parented._V2.episode_ids())
    for split in ("dev", "confirm"):
        for phase in ("formation", "held"):
            prior.update(deps.parented.episode_ids(split, phase))
    schedules = {str(seed): tasks_for_seed(seed, deps) for seed in range(3)}
    identifiers = []
    for seed, tasks in schedules.items():
        for task in tasks:
            identifiers.extend([task["task_id"], task["address"], task["world_id"]])
            identifiers.extend(receipt["receipt_id"] for receipt in task["public_receipts"])
            identifiers.extend(opaque("child-receipt", f"perception_seed{seed}_{arm}", task["task_id"]) for arm in ARMS)
    require(len(set(identifiers)) == len(identifiers) and not set(identifiers) & prior, "new task/address/receipt namespace collision")
    result = dict(schema=SCHEMA, states=list(STATES), arms=list(ARMS), roots=[root_binding(seed) for seed in range(3)],
        protocol_sha256=PROTOCOL_SHA256, dependencies=copy.deepcopy(deps.manifest), schedules=schedules,
        lessons=dict(LESSONS), lesson_sha256={key: sha_text(value) for key, value in LESSONS.items()},
        restate_template=RESTATE_TEMPLATE, wake_instruction=WAKE_INSTRUCTION, record_instruction=RECORD_INSTRUCTION,
        max_output_tokens=dict(MAX_OUTPUT_TOKENS), temperature=dict(TEMPERATURE), generation_seed=GENERATION_SEED,
        parser=dict(wake_keys=["note", "prediction", "action"], action=dict(kind="TRY", values="three strict integers [-9999,9999]"),
            P_note=["predicted", "observed", "relation"], P_optional=["receipt_id"], C_note=["receipt_id", "try", "observed"],
            note_field_aliases=copy.deepcopy(NOTE_ALIASES), relation_aliases=dict(RELATION_ALIASES),
            aliases="Predeclared aliases may mix; conflicting synonyms/unknown keys reject shape, not silently ignored.",
            note_action_shapes="integer array, or object with kind TRY and values integer array",
            record_keys=["address", "source", "event"], event_keys=["receipt_id", "try", "predicted", "observed", "relation"],
            whitespace_and_key_order="content accepted; compact sorted serialization canonical separately",
            duplicate_keys="reject", nonfinite="reject", fences="reject", maximum_raw_bytes=65536,
            restate_patterns=copy.deepcopy(RESTATE_PATTERNS), restate_contradictions=copy.deepcopy(RESTATE_CONTRADICTIONS)),
        limits=dict(tasks_per_state=16, restatements_per_lesson_state=4, calls_per_arm=dict(ALIGNED=36, SWAPPED=36, NO_PARENT=32),
                    calls_per_seed=104, calls_total=312, fits=0, updates=0, parent_model_calls=0),
        disjointness=dict(prior_task_ids=sorted(supplied), prior_ids_sha256=digest(sorted(prior)), distinct_new_ids=len(identifiers),
                          limitation="Explicit supplied inventory plus known original formation/parenting IDs; not unseen exposure certification."),
        public_receipt_origin="Harness-provided prior world events, never current-child actions; deterministic prospective balanced actual-world selection.",
        lesson_token_lengths_verified=False, native_identity_verified=False, automatic_pass=False, fit_authorized=False,
        qualification=QUALIFICATION)
    result["manifest_sha256"] = digest(result)
    return result


def decode(raw):
    require(type(raw) is str and len(raw.encode()) <= 65536, "bounded raw JSON text required")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique, parse_constant=lambda value: require(False, "nonfinite JSON"))


def triple(value):
    return type(value) is list and len(value) == 3 and all(type(part) is int and -9999 <= part <= 9999 for part in value)


def relation(predicted, observed):
    return "unavailable" if predicted is None else "matched" if predicted == observed else "mismatched"


def expected_note(task):
    if task["family"] == "P":
        receipt = task["public_receipts"][0]
        return dict(predicted=receipt["predicted"], observed=receipt["observed"], relation=relation(receipt["predicted"], receipt["observed"]))
    receipt = max(task["public_receipts"], key=lambda item: item["time"])
    return dict(receipt_id=receipt["receipt_id"], **{"try": receipt["try"]}, observed=receipt["observed"])


def normalize_note(note):
    require(type(note) is dict, "note_object_required")
    aliases = {alias: name for name, names in NOTE_ALIASES.items() for alias in names}
    result = {}
    for key, value in note.items():
        require(key in aliases and aliases[key] not in result, "unknown_or_conflicting_note_alias")
        result[aliases[key]] = value
    if type(result.get("relation")) is str:
        result["relation"] = RELATION_ALIASES.get(result["relation"], result["relation"])
    if type(result.get("try")) is dict:
        action = result["try"]
        require(set(action) == {"kind", "values"} and action["kind"] == "TRY", "note_action_shape")
        result["try"] = action["values"]
    return result


def score_note(note, task):
    expected = expected_note(task)
    fields = {key: False for key in expected}
    normalized, shape = None, False
    parse_errors = []
    try:
        normalized = normalize_note(note)
    except (ValueError, TypeError) as error:
        parse_errors.append(str(error))
    if normalized is not None:
        if task["family"] == "P":
            shape = set(normalized) in (set(expected), set(expected) | {"receipt_id"})
            if "receipt_id" in normalized:
                fields["receipt_id"] = type(normalized["receipt_id"]) is str and normalized["receipt_id"] == task["public_receipts"][0]["receipt_id"]
            for key in ("predicted", "observed"):
                fields[key] = type(normalized.get(key)) is bool and normalized[key] is expected[key]
            fields["relation"] = type(normalized.get("relation")) is str and normalized["relation"] == expected["relation"]
        else:
            shape = set(normalized) == set(expected)
            fields["receipt_id"] = type(normalized.get("receipt_id")) is str and normalized["receipt_id"] == expected["receipt_id"]
            fields["try"] = triple(normalized.get("try")) and normalized["try"] == expected["try"]
            fields["observed"] = type(normalized.get("observed")) is bool and normalized["observed"] is expected["observed"]
    correct = shape and all(fields.values())
    canonical_shape = shape and set(note) == set(expected) and note == normalized and all(type(note[key]) is type(value) for key, value in expected.items())
    return dict(content_correct=correct, shape_valid=shape, canonical_note=canonical_shape,
                field_correct=fields, parse_errors=parse_errors+([] if shape else ["note_schema"]),
                binding_errors=[key+"_binding" for key, valid in fields.items() if not valid] if shape else [],
                errors=parse_errors+(["note_schema"] if not shape else [key+"_binding" for key, valid in fields.items() if not valid]),
                normalized=normalized)


def score_wake(raw, finish_reason, task, errors=()):
    parsed, parse_errors = None, []
    try:
        parsed = decode(raw)
    except (ValueError, TypeError, RecursionError) as error:
        parse_errors.append(str(error))
    outer = type(parsed) is dict and set(parsed) == {"note", "prediction", "action"}
    action = parsed.get("action") if type(parsed) is dict else None
    action_valid = (outer and type(parsed["prediction"]) is bool and type(action) is dict and
                    set(action) == {"kind", "values"} and action["kind"] == "TRY" and triple(action["values"]))
    note = score_note(parsed.get("note") if type(parsed) is dict else None, task)
    completed = finish_reason == "stop" and not errors
    return dict(parsed=parsed, format_valid=outer and type(parsed["note"]) is dict and action_valid,
                canonical_form=outer and raw == canonical(parsed), note=note,
                PROCESS_USE=completed and note["content_correct"], action_valid=completed and action_valid,
                parse_errors=parse_errors, schema_errors=[] if outer else ["wake_schema"],
                errors=list(errors)+parse_errors+([] if outer else ["wake_schema"])+([] if action_valid else ["strict_action"]))


def score_restate(raw, finish_reason, lesson, errors=()):
    text = raw.lower() if type(raw) is str else ""
    fields = {key: bool(re.search(pattern, text, re.S)) for key, pattern in RESTATE_PATTERNS[lesson].items()}
    contradictions = [pattern for pattern in RESTATE_CONTRADICTIONS[lesson] if re.search(pattern, text)]
    return dict(content_correct=finish_reason == "stop" and not errors and all(fields.values()) and not contradictions,
                operation_scope=fields, contradictions=contradictions, errors=list(errors),
                limitation="Frozen conservative lexical operation/scope screen; not an unrestricted semantic judge.")


def phrase_overlap(raw, lesson):
    text = raw if type(raw) is str else ""
    words, parent = text.split(), lesson.split()
    match = difflib.SequenceMatcher(None, words, parent, autojunk=False).find_longest_match()
    return dict(exact_parent_substring=lesson in text, exact_raw_equals_parent=text == lesson,
                longest_exact_word_span=match.size, phrase=" ".join(words[match.a:match.a+match.size]),
                method="case-sensitive contiguous word equality; whitespace-separated words, not token counts")


def score_record(raw, finish_reason, task, execution, deps, errors=()):
    parsed, parse_errors = None, []
    try:
        parsed = decode(raw)
    except (ValueError, TypeError, RecursionError) as error:
        parse_errors.append(str(error))
    outer = type(parsed) is dict and set(parsed) == {"address", "source", "event"}
    source = score_note(parsed.get("source") if type(parsed) is dict else None, task)
    event = parsed.get("event") if type(parsed) is dict else None
    event_shape = type(event) is dict and set(event) == {"receipt_id", "try", "predicted", "observed", "relation"}
    expected = dict(receipt_id=execution["receipt"]["receipt_id"], **{"try": execution["values"]},
                    predicted=execution["predicted"], observed=execution["observed"], relation=relation(execution["predicted"], execution["observed"]))
    fields = {key: type(event) is dict and type(event.get(key)) is type(value) and event.get(key) == value for key, value in expected.items()}
    fields["try"] = type(event) is dict and triple(event.get("try")) and event["try"] == expected["try"]
    address_ok = outer and type(parsed["address"]) is str and parsed["address"] == task["address"]
    frozen = deps.interface.judge_record(canonical({key: value for key, value in event.items() if key != "receipt_id"}),
        dict(values=execution["values"], predicted=execution["predicted"], observed=execution["observed"], prediction_ambiguous=False)) if event_shape else dict(eligible=False, failures=["event_schema"])
    correct = outer and source["content_correct"] and event_shape and all(fields.values()) and address_ok and frozen["eligible"] and finish_reason == "stop" and not errors
    typed_event = event_shape and type(event["receipt_id"]) is str and triple(event["try"]) and type(event["predicted"]) is bool and type(event["observed"]) is bool and type(event["relation"]) is str
    return dict(RECORD_FAITHFUL=correct, format_valid=outer and type(parsed["address"]) is str and type(parsed["source"]) is dict and typed_event, canonical_form=outer and raw == canonical(parsed),
        source=source, event_fields=fields, address_correct=address_ok, frozen_event_judge=frozen, parsed=parsed,
        parse_errors=parse_errors, schema_errors=[] if outer and event_shape else ["record_schema"],
        errors=list(errors)+parse_errors+([] if outer and event_shape else ["record_schema"])+([] if address_ok else ["address_binding"])+
               [key+"_binding" for key, valid in fields.items() if not valid])


def request(state, task, kind, prompt, *, contact=None, execution=None):
    value = dict(state=state, kind=kind, episode_id=task["task_id"], block_index=task["block_index"], task_index=task["task_index"],
        input_messages=[dict(role="user", content=prompt)], max_output_tokens=MAX_OUTPUT_TOKENS[kind], temperature=TEMPERATURE[kind],
        seed=GENERATION_SEED, source_execution_sha256=execution, contact_sha256=contact)
    value["request_id"] = digest([SCHEMA, value])
    return value


def call(backend, value, events, deps):
    event = deps.parented._V2._call(backend, value, events)
    response = event["response"]
    if "backend_error" not in response and "invalid_backend_response" not in response:
        require(response.get("request_id") == value["request_id"] and response.get("state") == value["state"], "fatal response source/state join mismatch")
    return event


def readout(records, contacts, events):
    names = ("PROCESS_USE", "EXECUTED", "RECORD_FAITHFUL", "FULL_MATERIAL")
    counts = {name: sum(record[name] for record in records) for name in names}
    counts.update(RESTATE=sum(contact["score"]["content_correct"] for contact in contacts) if contacts else None,
                  restate_denominator=4 if contacts else None, contacts=len(contacts), opportunities=len(records))
    counts["by_delivery"] = {str(delivery): {name: sum(record[name] for record in records if record["delivery"] == delivery) for name in names} for delivery in (0, 1)}
    counts["by_family"] = {family: {name: sum(record[name] for record in records if record["family"] == family) for name in names} for family in ("P", "C")}
    counts["by_family_delivery"] = {family: {str(delivery): dict(denominator=4,
        **{name: sum(record[name] for record in records if record["family"] == family and record["delivery"] == delivery) for name in names})
        for delivery in (0, 1)} for family in ("P", "C")}
    counts["endpoint_masks"] = {name: [record[name] for record in records] for name in names}
    counts["restate_mask"] = [contact["score"]["content_correct"] for contact in contacts] if contacts else None
    calls = [event for event in events if event["kind"] == "call"]
    counts.update(calls=len(calls), updates=0, fits=0, parent_model_calls=0,
        record_not_called=sum(record["record"] is None for record in records), finishes=dict(Counter(str(event["response"].get("finish_reason", "MISSING")) for event in calls)),
        input_utf8_bytes=sum(len(message["content"].encode()) for event in calls for message in event["request"]["input_messages"]),
        output_utf8_bytes=sum(len(event["response"]["raw"].encode()) for event in calls if type(event["response"].get("raw")) is str),
        raw_unique={kind: len({event["response"]["raw"] for event in calls if event["request"]["kind"] == kind and type(event["response"].get("raw")) is str}) for kind in MAX_OUTPUT_TOKENS},
        token_costs="Native wrapper must report actual token counts; UTF8 bytes are not tokens.")
    return counts


def run_phase(state, backend, deps, *, binding=None):
    seed, arm = state_parts(state)
    if binding is not None:
        producer = binding["producer"]
        expected = root_binding(seed)
        require(all(producer[key] == expected[key] for key in ("learner_seed", "parent_plan_sha256", "adapter")) and
                producer["adapter_files"]["adapter_model.safetensors"] == expected["adapter_model_sha256"], "original producer binding required; descendants forbidden")
    manifest = build_manifest(deps)
    tasks = manifest["schedules"][str(seed)]
    events, records, contacts = [], [], []
    event = deps.parented._V2._event
    for block_index in range(4):
        block = tasks[4*block_index:4*block_index+4]
        current_note, contact_hash = None, None
        if arm != "NO_PARENT":
            family = block[0]["family"]
            lesson = family if arm == "ALIGNED" else "C" if family == "P" else "P"
            contact_hash = sha_text(LESSONS[lesson])
            parent_event = event(events, dict(kind="fixed_contact", state=state, block_index=block_index, lesson=lesson,
                                             raw=LESSONS[lesson], contact_sha256=contact_hash))
            restatement = call(backend, request(state, block[0], "restate", RESTATE_TEMPLATE.format(lesson=LESSONS[lesson]), contact=contact_hash), events, deps)
            response = restatement["response"]
            current_note = response.get("raw") if type(response.get("raw")) is str else None
            contacts.append(dict(block_index=block_index, lesson=lesson, contact=parent_event, restatement=restatement,
                score=score_restate(response.get("raw"), response.get("finish_reason"), lesson, restatement["errors"]),
                phrase_overlap=phrase_overlap(response.get("raw"), LESSONS[lesson])))
        for task in block:
            public_event = event(events, dict(kind="harness_public_receipts", state=state, task_id=task["task_id"],
                receipts=copy.deepcopy(task["public_receipts"]), evaluations=copy.deepcopy(task["public_world_evaluations"]),
                origin="harness_provided_not_child_actions"))
            context = "" if current_note is None else "Current child NOTE (verbatim):\n"+current_note+"\nEnd child NOTE.\n\n"
            wake = call(backend, request(state, task, "wake", context+task["ordinary_prompt"], contact=contact_hash), events, deps)
            response = wake["response"]
            wake_score = score_wake(response.get("raw"), response.get("finish_reason"), task, wake["errors"])
            row = dict(task_id=task["task_id"], address=task["address"], task_index=task["task_index"], block_index=block_index,
                family=task["family"], variant=task["variant"], delivery=task["delivery"], public_event_sha256=public_event["sha256"],
                wake=wake, wake_score=wake_score, execution=None, record=None, record_score=None,
                PROCESS_USE=wake_score["PROCESS_USE"], EXECUTED=False, RECORD_FAITHFUL=False, FULL_MATERIAL=False,
                status="RECORD_NOT_CALLED_INVALID_WAKE")
            if wake_score["action_valid"]:
                parsed = wake_score["parsed"]
                actual = world_result(deps.game_class(), deps, task["world_id"], parsed["action"]["values"], parsed["prediction"])
                receipt = dict(receipt_id=opaque("child-receipt", state, task["task_id"]), time=len(task["public_receipts"])+1,
                    **{"try": actual["values"]}, predicted=actual["predicted"], observed=actual["observed"])
                execution = event(events, dict(actual, kind="execution", state=state, task_id=task["task_id"], receipt=receipt,
                    source_call_id=wake["request"]["request_id"], source_call_sha256=wake["sha256"], origin="current_child_fresh_action"))
                row.update(EXECUTED=True, execution=execution)
                prompt = context+RECORD_INSTRUCTION+"\nOriginal public task:\n"+canonical(task["public"])+"\nYour pre-action output (verbatim):\n"+response["raw"]+"\nFresh receipt:\n"+canonical(receipt)
                record = call(backend, request(state, task, "record", prompt, execution=execution["sha256"]), events, deps)
                record_response = record["response"]
                score = score_record(record_response.get("raw"), record_response.get("finish_reason"), task, execution, deps, record["errors"])
                row.update(record=record, record_score=score, RECORD_FAITHFUL=score["RECORD_FAITHFUL"],
                    FULL_MATERIAL=row["PROCESS_USE"] and score["RECORD_FAITHFUL"], status="RECORD_OBSERVED")
            records.append(row)
    summary = readout(records, contacts, events)
    require(len(records) == 16 and summary["calls"] <= (32 if arm == "NO_PARENT" else 36), "fixed call/task bound exceeded")
    result = dict(schema=SCHEMA, state=state, seed=seed, arm=arm, phase="inference", binding=copy.deepcopy(binding),
        original_root=root_binding(seed), manifest_sha256=manifest["manifest_sha256"], events=events, contacts=contacts, records=records,
        readout=summary, summary=copy.deepcopy(summary), native_identity_verified=False, automatic_pass=False, fit_authorized=False,
        updates=0, qualification=QUALIFICATION)
    result["capture_sha256"] = digest(result)
    return result


def run_state(state, backend, *, dependencies, binding=None):
    return run_phase(state, backend, dependencies, binding=binding)


def replay_validate(capture, deps):
    require(capture["schema"] == SCHEMA, "capture schema differs")
    supplied = copy.deepcopy(capture)
    pin = supplied.pop("capture_sha256")
    require(digest(supplied) == pin, "capture hash differs")
    calls = [event for event in capture["events"] if event["kind"] == "call"]
    index = 0
    def replay(value):
        nonlocal index
        require(index < len(calls), "missing captured call")
        saved = calls[index]
        index += 1
        require(canonical(value) == canonical(saved["request"]), "replay request/source differs")
        return copy.deepcopy(saved["response"])
    rebuilt = run_phase(capture["state"], replay, deps, binding=capture["binding"])
    require(index == len(calls) and canonical(rebuilt) == canonical(capture), "deterministic call/world/record replay differs")
    return dict(consistent=True, capture_sha256=pin, calls_replayed=index, readout=copy.deepcopy(capture["readout"]), native_identity_verified=False)


def audit_capture(capture, *, dependencies):
    return replay_validate(capture, dependencies)


def threshold_vector(cells):
    required = set(STATES)
    require(set(cells) <= required, "unknown feasibility cell")
    if set(cells) != required:
        return dict(complete=False, missing=sorted(required-set(cells)), feasibility_pass=False, fit_authorized=False, updates=0)
    roots = []
    for seed in range(3):
        aligned, swapped, anchor = (cells[f"perception_seed{seed}_{arm}"] for arm in ARMS)
        roots.append(dict(seed=seed, restate=aligned["RESTATE"], aligned=aligned["PROCESS_USE"], swapped=swapped["PROCESS_USE"], no_parent=anchor["PROCESS_USE"],
            aligned_minus_swapped=aligned["PROCESS_USE"]-swapped["PROCESS_USE"], aligned_minus_no_parent=aligned["PROCESS_USE"]-anchor["PROCESS_USE"],
            first=aligned["by_delivery"]["0"]["PROCESS_USE"], second=aligned["by_delivery"]["1"]["PROCESS_USE"], full_material=aligned["FULL_MATERIAL"]))
    vector = dict(restatement=sum(root["restate"] >= 3 for root in roots) >= 2,
        swapped_advantage=sum(root["aligned_minus_swapped"] >= 4 for root in roots) >= 2,
        swapped_no_large_harm=all(root["aligned_minus_swapped"] > -4 for root in roots),
        anchor_advantage=sum(root["aligned_minus_no_parent"] >= 2 for root in roots) >= 2,
        anchor_no_large_harm=all(root["aligned_minus_no_parent"] >= -2 for root in roots),
        repeated_activation=sum(root["second"] >= root["first"] for root in roots) >= 2,
        faithful_material=sum(root["full_material"] >= 8 for root in roots) >= 2)
    root_masks = dict(restatement=[root["restate"] >= 3 for root in roots],
        swapped_advantage=[root["aligned_minus_swapped"] >= 4 for root in roots],
        swapped_no_large_harm=[root["aligned_minus_swapped"] > -4 for root in roots],
        anchor_advantage=[root["aligned_minus_no_parent"] >= 2 for root in roots],
        anchor_no_large_harm=[root["aligned_minus_no_parent"] >= -2 for root in roots],
        repeated_activation=[root["second"] >= root["first"] for root in roots],
        faithful_material=[root["full_material"] >= 8 for root in roots])
    return dict(complete=True, roots=roots, vector=vector, root_masks=root_masks, feasibility_pass=all(vector.values()), fit_authorized=False, updates=0,
        interpretation="Immediate developmental feasibility only; correlated task counts, three root replication units; no writer adopted.")


def summarize(captures, deps):
    require(type(captures) in (list, tuple), "capture list required")
    cells = {}
    for capture in captures:
        require(capture["state"] not in cells, "duplicate feasibility state")
        replay_validate(capture, deps)
        cells[capture["state"]] = capture["readout"]
    require(sum(cell["calls"] for cell in cells.values()) <= 312, "campaign call bound exceeded")
    return dict(schema=SCHEMA, cells=copy.deepcopy(cells), gate=threshold_vector(cells), updates=0, fits=0,
                native_identity_verified=False, automatic_pass=False, fit_authorized=False, qualification=QUALIFICATION)
