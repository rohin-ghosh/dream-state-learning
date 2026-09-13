"""Fresh explicit-contract DEV measurement; CPU world/callbacks, no training."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import re
from types import ModuleType, SimpleNamespace


SCHEMA = "astra_parenting_contract_dev_20260913_v1"
SOURCE_ROOT = "/data/home/rohing/dream-state"
PROTOCOL_PATH = SOURCE_ROOT + "/research_notes/astra_memos/ASTRA_PARENTING_CONTRACT_DEV_2026-09-13.md"
PROTOCOL_SHA256 = "74b62e8ca4ba79e796f8fc666e065613758297fbd4610fd5bf3788d4da772572"
ALIGNMENT_PATH = "/tmp/astra_parenting_alignment_core_20260913.py"
ALIGNMENT_SHA256 = "71311d3d9add1f485289c6ee6824ef758393193ee05bcc088674d12697b11010"
PARENTED_PATH = "/tmp/astra_parented_record_core_20260913.py"
PARENTED_SHA256 = "68ef29fcc162dbbf5fe1becf4c09b86ed5bc1f8a79e373276dd8ba3cda88e688"
ARMS = ("ALIGNED", "SWAPPED", "ACTIVE_NEUTRAL")
STATES = tuple(f"perception_seed{seed}_{arm}" for seed in range(3) for arm in ARMS)
MAX_OUTPUT_TOKENS = {"restate": 160, "wake": 256, "record": 384}
TEMPERATURE = {kind: 0.0 for kind in MAX_OUTPUT_TOKENS}
GENERATION_SEED = 0
CONTROLLER_SECONDS = 1800
COLLECTION_SECONDS = 180
AGGREGATE_A40_HOURS = 2
QUALIFICATION = "explicit_contract_DEV_measurement_not_parenting_qualification_SEQ160_rescue_or_H1_H2"
NEUTRAL = "Continue with the next scheduled tasks using their instructions. Briefly acknowledge this message before proceeding."
RESTATE_TEMPLATE = "Message:\n{lesson}\n\nRestate this message in your own words."
WAKE_OUTPUT_TEMPLATE = '{"note": OBJECT, "prediction": BOOLEAN, "action": {"kind": "TRY", "values": [INTEGER, INTEGER, INTEGER]}}'
NOTE_OUTPUT_TEMPLATES = {
    "P": '{"predicted": BOOLEAN, "observed": BOOLEAN, "relation": "matched" | "mismatched"}',
    "C": '{"receipt_id": STRING, "try": [INTEGER, INTEGER, INTEGER], "observed": BOOLEAN}',
}
RECORD_OUTPUT_TEMPLATE = '{"address": STRING, "source": OBJECT, "event": {"receipt_id": STRING, "try": [INTEGER, INTEGER, INTEGER], "predicted": BOOLEAN, "observed": BOOLEAN, "relation": "matched" | "mismatched"}}'
WAKE_INSTRUCTION = (
    "Use the public task below and choose one fresh action. Return only one JSON object with exactly keys note, prediction, action. "
    "prediction is a Boolean prediction for YOUR NEW action, even if an earlier public prediction is null. "
    "action has exactly kind and values: kind is TRY; values is an array of exactly three integers between -9999 and 9999. "
    "Use JSON Booleans true/false, not strings or null for your fresh prediction. No code fence or additional text. "
    "Do not add metadata fields. Whitespace and key order are immaterial. "
    "Typed output template (uppercase words denote types, not literal output values): "+WAKE_OUTPUT_TEMPLATE+". "
)
NOTE_INSTRUCTIONS = {
    "P": (
        "For the public receipt, report its prediction as stated before that action, its returned observation, and whether those values match. "
        "These are not your new action's prediction or outcome. "
        "note has exactly the fields in this typed template: "+NOTE_OUTPUT_TEMPLATES["P"]+". "
        "Preserve both Booleans unchanged. relation is the string matched if they agree, mismatched otherwise."
    ),
    "C": (
        "Select the executed public receipt with greatest time, not the last receipt displayed. "
        "Report that receipt's ID, action and observation together. "
        "note has exactly the fields in this typed template: "+NOTE_OUTPUT_TEMPLATES["C"]+". "
        "receipt_id is that same receipt's string ID, try its three-integer array, observed its Boolean outcome. "
        "Return one selected receipt, not a list of receipts."
    ),
}
RECORD_INSTRUCTION = (
    "Record the original public source AND your actual fresh experience separately. Return only one JSON object with exactly address, source, event. "
    "address is the supplied task address string. source is the original public note OBJECT with the family-specific fields below, "
    "not the receipt-origin prose string and not your fresh receipt. "
    "event has exactly receipt_id, try, predicted, observed, relation for YOUR fresh receipt. "
    "receipt_id is its string ID; try is your three-integer action; predicted is the Boolean you stated before that action; "
    "observed is the returned Boolean; relation is the string matched if those Booleans agree, mismatched otherwise. "
    "Keep original public receipt and fresh receipt identities separate even if actions or outcomes coincide. "
    "Do not add metadata fields. No code fence or additional text. Whitespace and key order are immaterial. "
    "Typed output template (uppercase words denote types, not literal output values): "+RECORD_OUTPUT_TEMPLATE+". "
)
ENDPOINTS = ("PROCESS_USE", "EXECUTED", "RECORD_SOURCE", "OWN_EVENT", "ADDRESS", "RECORD_FAITHFUL", "FULL_MATERIAL", "WAKE_SCHEMA", "RECORD_SCHEMA", "SCHEMA_FULL_MATERIAL")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _load(path, pin, name):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == pin, "frozen helper pin differs: " + str(path))
    module = ModuleType(name)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


_BASE = _load(ALIGNMENT_PATH, ALIGNMENT_SHA256, "contract_frozen_alignment")
canonical, digest, sha_text = _BASE.canonical, _BASE.digest, _BASE.sha_text
triple, relation = _BASE.triple, _BASE.relation
ROOT_PLAN_PINS, ROOT_WEIGHT_PINS = _BASE.ROOT_PLAN_PINS, _BASE.ROOT_WEIGHT_PINS
LESSONS = dict(_BASE.LESSONS, NEUTRAL=NEUTRAL)
world_result = _BASE.world_result


def load_dependencies(source_root=SOURCE_ROOT, *, protocol_path=None, protocol_sha256=None,
                      parented_path=PARENTED_PATH, alignment_path=ALIGNMENT_PATH):
    path = protocol_path if protocol_path is not None else PROTOCOL_PATH
    pin = protocol_sha256 if protocol_sha256 is not None else PROTOCOL_SHA256
    require(path is not None and type(pin) is str and re.fullmatch(r"[0-9a-f]{64}", pin), "explicit canonical protocol path/pin required")
    require(pin == PROTOCOL_SHA256, "canonical protocol pin differs")
    require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == pin, "protocol bytes differ")
    _load(alignment_path, ALIGNMENT_SHA256, "contract_checked_alignment")
    parented = _load(parented_path, PARENTED_SHA256, "contract_frozen_parented")
    dependencies = parented._V2.load_dependencies(source_root)
    return SimpleNamespace(game_class=dependencies.game_class, interface=dependencies.interface, parented=parented,
        manifest=dict(copy.deepcopy(dependencies.manifest), parented_core_sha256=PARENTED_SHA256,
                      alignment_core_sha256=ALIGNMENT_SHA256, protocol_sha256=pin))


def root_binding(seed):
    require(type(seed) is int and seed in (0, 1, 2), "original learner seed required")
    return _BASE.root_binding(seed)


def state_parts(state):
    require(state in STATES, "original explicit-contract state required")
    return next((seed, arm) for seed in range(3) for arm in ARMS if state == f"perception_seed{seed}_{arm}")


def opaque(kind, *parts):
    return "pc-" + digest([SCHEMA, kind, *parts])[:28]


def make_task(family, position, deps):
    task_id = opaque("dev-task", family, position)
    world_id = opaque("dev-world", family, position)
    game = deps.game_class()
    desired = [bool(position % 2)] if family == "P" else [not bool(position % 2), bool(position % 2)]
    receipts, probes = [], []
    for receipt_index, observed in enumerate(desired):
        predicted = bool(position // 2) if family == "P" else None
        for attempt in range(512):
            bits = bytes.fromhex(digest([SCHEMA, "public-action", family, position, receipt_index, attempt]))
            values = [int(value) % 19 - 9 for value in bits[:3]]
            outcome = world_result(game, deps, world_id, values, predicted)
            probes.append(dict(receipt_index=receipt_index, attempt=attempt, **outcome))
            if outcome["observed"] is observed and not any(receipt["try"] == values for receipt in receipts):
                break
        else:
            raise ValueError("bounded public source construction failed")
        receipts.append(dict(receipt_id=opaque("public-receipt", task_id, receipt_index), time=receipt_index+1,
                             **{"try": values}, predicted=predicted, observed=observed))
    display = list(reversed(receipts)) if family == "C" and position // 2 else list(receipts)
    address = opaque("address", task_id)
    public = dict(task_id=task_id, address=address, receipts=display,
                  receipt_origin="Harness-provided earlier public environment events; not your own actions.")
    fingerprint = digest(dict(family=family, receipts=[{key: value for key, value in receipt.items() if key != "receipt_id"} for receipt in display]))
    return dict(task_id=task_id, address=address, world_id=world_id, family=family, position=position, variant=0,
        public=public, public_receipts=receipts, public_world_evaluations=probes, source_fingerprint=fingerprint,
        ordinary_prompt=WAKE_INSTRUCTION+NOTE_INSTRUCTIONS[family]+"\nPublic task:\n"+canonical(public))


def tasks_for_seed(seed, deps):
    root_binding(seed)
    positions = {"P": 0, "C": 0}
    tasks = []
    for block_index, family in enumerate(("P", "C", "C", "P")):
        for unused_slot in range(2):
            position = positions[family]
            positions[family] += 1
            tasks.append(dict(make_task(family, position, deps), block_index=block_index,
                              delivery=block_index // 2, task_index=len(tasks)))
    return tasks


def build_manifest(dependencies, *, prior_task_ids=(), prior_ids=None, prior_task_fingerprints=()):
    deps = dependencies
    require(deps.manifest["parented_core_sha256"] == PARENTED_SHA256 and deps.manifest["alignment_core_sha256"] == ALIGNMENT_SHA256
            and deps.manifest["full_source_sha256"] == deps.parented.PINS, "frozen dependency manifest differs")
    require(type(deps.manifest["protocol_sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", deps.manifest["protocol_sha256"]), "protocol pin required")
    require(deps.manifest["protocol_sha256"] == PROTOCOL_SHA256, "canonical protocol differs")
    require(prior_ids is None or not prior_task_ids, "supply only one prior-ID argument")
    supplied = prior_task_ids if prior_ids is None else prior_ids
    for values in (supplied, prior_task_fingerprints):
        require(type(values) in (tuple, list) and all(type(value) is str and value for value in values)
                and len(set(values)) == len(values), "unique explicit prior inventory required")
    tasks = tasks_for_seed(0, deps)
    identifiers = []
    for task in tasks:
        identifiers.extend([task["task_id"], task["address"], task["world_id"]])
        identifiers.extend(receipt["receipt_id"] for receipt in task["public_receipts"])
        identifiers.extend(opaque("child-receipt", state, task["task_id"]) for state in STATES)
    known = set(supplied) | set(deps.parented._V2.episode_ids())
    for split in ("dev", "confirm"):
        for phase in ("formation", "held"):
            known.update(deps.parented.episode_ids(split, phase))
    require(len(set(identifiers)) == len(identifiers) and not set(identifiers) & known, "new source/receipt namespace collision")
    require(not {task["source_fingerprint"] for task in tasks} & set(prior_task_fingerprints), "prior source instance reused")
    result = dict(schema=SCHEMA, states=list(STATES), arms=list(ARMS), roots=[root_binding(seed) for seed in range(3)],
        protocol_sha256=deps.manifest["protocol_sha256"], dependencies=copy.deepcopy(deps.manifest),
        schedules={str(seed): copy.deepcopy(tasks) for seed in range(3)}, shared_roster_sha256=digest(tasks),
        lessons=dict(LESSONS), lesson_sha256={key: sha_text(value) for key, value in LESSONS.items()},
        restate_template=RESTATE_TEMPLATE, wake_instruction=WAKE_INSTRUCTION, note_instructions=dict(NOTE_INSTRUCTIONS),
        record_instruction=RECORD_INSTRUCTION, max_output_tokens=dict(MAX_OUTPUT_TOKENS), temperature=dict(TEMPERATURE), generation_seed=GENERATION_SEED,
        output_templates=dict(wake=WAKE_OUTPUT_TEMPLATE, note=dict(NOTE_OUTPUT_TEMPLATES), record=RECORD_OUTPUT_TEMPLATE),
        parser=dict(paths="exact declared note/source/event fields; no aliases, recursive search or repair", extra_keys="schema false, required-path content assessed independently",
                    duplicate_keys="reject entire JSON", nonfinite="reject", fences="reject", maximum_raw_bytes=65536,
                    canonical="compact sorted UTF8 separately from content", action="unchanged closed strict action dispatch", lexical_restate_gate=False),
        limits=dict(tasks_per_state=8, restatements_per_lesson_state=4, calls_per_arm={arm: 20 for arm in ARMS},
                    calls_per_seed=60, calls_total=180, fits=0, updates=0, parent_model_calls=0,
                    controller_seconds=CONTROLLER_SECONDS, collection_seconds=COLLECTION_SECONDS, aggregate_a40_hours_including_preparation=AGGREGATE_A40_HOURS),
        disjointness=dict(prior_task_ids=sorted(supplied), prior_task_fingerprints=sorted(prior_task_fingerprints), distinct_new_ids=len(identifiers),
                          limitation="New shared DEV namespace plus supplied prior inventories; not unseen-exposure certification. No CONF tasks generated."),
        public_receipt_origin="Actual frozen CPU world; harness public receipts are not the child's new actions.",
        lesson_token_lengths_verified=False, native_identity_verified=False, native_execution_authorized=False,
        automatic_pass=False, fit_authorized=False, qualification=QUALIFICATION)
    result["manifest_sha256"] = digest(result)
    return result


def expected_note(task):
    return _BASE.expected_note(task)


def decode(raw):
    require(type(raw) is str and len(raw.encode()) <= 65536, "bounded raw JSON text required")
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, "duplicate JSON key")
            value[key] = item
        return value
    def finite(text):
        value = float(text)
        require(math.isfinite(value), "nonfinite JSON")
        return value
    return json.loads(raw, object_pairs_hook=unique, parse_float=finite,
                      parse_constant=lambda value: require(False, "nonfinite JSON"))


def field_score(value, expected):
    object_valid = type(value) is dict
    fields = {}
    for key, target in expected.items():
        present = object_valid and key in value
        actual = value[key] if present else None
        typed = present and (triple(actual) if key == "try" else type(actual) is type(target))
        correct = typed and actual == target
        status = "unassessable" if not object_valid else "missing" if not present else "wrong_type" if not typed else "correct" if correct else "wrong_value"
        fields[key] = dict(present=present, type_valid=typed, correct=correct, status=status)
    extra = sorted(set(value)-set(expected)) if object_valid else []
    missing = sorted(set(expected)-set(value)) if object_valid else list(expected)
    enum_valid = not object_valid or "relation" not in expected or value.get("relation") in ("matched", "mismatched")
    schema = object_valid and not extra and not missing and all(item["type_valid"] for item in fields.values()) and enum_valid
    correct = object_valid and all(item["correct"] for item in fields.values())
    return dict(content_correct=correct, schema_valid=schema, shape_valid=schema, object_valid=object_valid,
        fields=fields, field_correct={key: item["correct"] for key, item in fields.items()}, extra_keys=extra, missing_keys=missing,
        binding_errors=[key+"_binding" for key, item in fields.items() if item["present"] and not item["correct"]],
        parse_errors=[] if object_valid else ["object_required"], canonical_note=schema,
        normalized=copy.deepcopy(value) if object_valid else None)


def score_note(note, task):
    return field_score(note, expected_note(task))


def parsed_output(raw):
    try:
        value = decode(raw)
        if type(value) is not dict:
            return None, ["outer_object_required"]
        return value, []
    except (ValueError, TypeError, RecursionError) as error:
        return None, [str(error)]


def score_wake(raw, finish_reason, task, errors=()):
    parsed, parse_errors = parsed_output(raw)
    note = score_note(parsed.get("note") if parsed is not None else None, task)
    outer = parsed is not None and set(parsed) == {"note", "prediction", "action"}
    action = parsed.get("action") if parsed is not None else None
    action_valid = (outer and type(parsed["prediction"]) is bool and type(action) is dict and
                    set(action) == {"kind", "values"} and action["kind"] == "TRY" and triple(action["values"]))
    completed = finish_reason == "stop" and not errors
    schema = action_valid and note["schema_valid"]
    return dict(parsed=parsed, json_valid=parsed is not None, note=note, schema_valid=schema, format_valid=schema,
        canonical_form=parsed is not None and raw == canonical(parsed), PROCESS_USE=completed and note["content_correct"],
        action_valid=completed and action_valid, parse_errors=parse_errors, schema_errors=[] if schema else ["wake_schema"],
        errors=list(errors)+parse_errors+([] if outer else ["wake_outer_schema"])+([] if action_valid else ["strict_action"]))


def score_record(raw, finish_reason, task, execution, deps, errors=()):
    parsed, parse_errors = parsed_output(raw)
    source = score_note(parsed.get("source") if parsed is not None else None, task)
    event = parsed.get("event") if parsed is not None else None
    expected = dict(receipt_id=execution["receipt"]["receipt_id"], **{"try": execution["values"]}, predicted=execution["predicted"],
                    observed=execution["observed"], relation=relation(execution["predicted"], execution["observed"]))
    event_score = field_score(event, expected)
    address = field_score({"address": parsed["address"]} if parsed is not None and "address" in parsed else {} if parsed is not None else None,
                          {"address": task["address"]})
    outer = parsed is not None and set(parsed) == {"address", "source", "event"}
    completed = finish_reason == "stop" and not errors
    content = source["content_correct"] and event_score["content_correct"] and address["content_correct"]
    schema = outer and source["schema_valid"] and event_score["schema_valid"] and address["schema_valid"]
    frozen = dict(eligible=False, failures=["required_event_fields_untyped_or_missing"])
    if all(item["type_valid"] for item in event_score["fields"].values()):
        frozen = deps.interface.judge_record(canonical({key: event[key] for key in expected if key != "receipt_id"}),
            dict(values=execution["values"], predicted=execution["predicted"], observed=execution["observed"], prediction_ambiguous=False))
    return dict(parsed=parsed, json_valid=parsed is not None, source=source, event=event_score, event_fields=event_score["field_correct"],
        address=address, address_correct=address["content_correct"], schema_valid=schema, format_valid=schema,
        canonical_form=parsed is not None and raw == canonical(parsed), RECORD_FAITHFUL=completed and content,
        RECORD_SOURCE=completed and source["content_correct"], OWN_EVENT=completed and event_score["content_correct"], ADDRESS=completed and address["content_correct"],
        frozen_event_judge=frozen, frozen_event_judge_scope="Required event field projection for diagnostic only, never raw output repair or native replay.",
        parse_errors=parse_errors, schema_errors=[] if schema else ["record_schema"],
        errors=list(errors)+parse_errors+source["binding_errors"]+event_score["binding_errors"]+address["binding_errors"])


def request(state, task, kind, prompt, *, contact=None, execution=None):
    value = dict(state=state, kind=kind, episode_id=task["task_id"], block_index=task["block_index"], task_index=task["task_index"],
        input_messages=[dict(role="user", content=prompt)], max_output_tokens=MAX_OUTPUT_TOKENS[kind], temperature=TEMPERATURE[kind],
        seed=GENERATION_SEED, source_execution_sha256=execution, contact_sha256=contact)
    value["request_id"] = digest([SCHEMA, value])
    return value


def call(backend, value, events, deps):
    return _BASE.call(backend, value, events, deps)


def score_restate(raw, finish_reason, lesson, errors=()):
    return dict(completed=type(raw) is str and finish_reason == "stop" and not errors, nonempty=type(raw) is str and bool(raw.strip()),
                content_correct=None, lexical_gate=False, errors=list(errors), delivered_lesson=lesson,
                limitation="Delivery/completion only; no lexical or semantic restatement qualification.")


def readout(records, contacts, events):
    require(type(records) is list and len(records) <= 8, "bounded record slots required")
    indexed = {}
    for row in records:
        index = row["task_index"]
        require(type(index) is int and 0 <= index < 8 and index not in indexed, "duplicate or invalid task slot")
        require(row["family"] == ("P" if index in (0, 1, 6, 7) else "C") and row["delivery"] == index // 4, "slot source family/delivery differs")
        require(all(type(row[name]) is bool for name in ENDPOINTS), "endpoint Boolean required")
        indexed[index] = row
    masks = {name: [indexed[index][name] if index in indexed else False for index in range(8)] for name in ENDPOINTS}
    counts = {name: sum(mask) for name, mask in masks.items()}
    counts.update(opportunities=8, attempted_slots=len(records), missing_slots=[index for index in range(8) if index not in indexed],
        complete=len(records) == 8 and len(contacts) == 4, contacts=len(contacts), RESTATE=None, restate_denominator=4,
        restate_mask=None, restate_completed=sum(contact["score"]["completed"] for contact in contacts),
        restate_completion_mask=[contact["score"]["completed"] for contact in contacts], endpoint_masks=masks)
    for group, selections in (("by_delivery", {str(part): list(range(part*4, part*4+4)) for part in (0, 1)}),
                              ("by_family", {"P": [0, 1, 6, 7], "C": [2, 3, 4, 5]})):
        counts[group] = {key: dict(denominator=4, **{name: sum(masks[name][index] for index in indices) for name in ENDPOINTS}) for key, indices in selections.items()}
    counts["by_family_delivery"] = {family: {str(delivery): dict(denominator=2,
        **{name: sum(masks[name][index] for index in range(delivery*4, delivery*4+4)
                     if (index in (0, 1, 6, 7)) == (family == "P")) for name in ENDPOINTS})
        for delivery in (0, 1)} for family in ("P", "C")}
    counts["per_field"] = {}
    for section in ("public_note", "record_source", "own_event", "address"):
        entries = []
        for index in range(8):
            row = indexed.get(index)
            score = None
            if row is not None:
                if section == "public_note":
                    score = row["wake_score"]["note"]
                elif row["record_score"] is not None:
                    score = row["record_score"][("source" if section == "record_source" else "event" if section == "own_event" else "address")]
            entries.append(dict(task_index=index, fields=copy.deepcopy(score["fields"]) if score is not None else None,
                                status="scored" if score is not None else "unattempted" if row is None else "record_uncalled"))
        counts["per_field"][section] = entries
    calls = [event for event in events if event["kind"] == "call"]
    counts.update(calls=len(calls), updates=0, fits=0, parent_model_calls=0, record_not_called=8-sum(row["record"] is not None for row in records),
        finishes=dict(Counter(str(event["response"].get("finish_reason", "MISSING")) for event in calls)),
        input_utf8_bytes=sum(len(message["content"].encode()) for event in calls for message in event["request"]["input_messages"]),
        output_utf8_bytes=sum(len(event["response"]["raw"].encode()) for event in calls if type(event["response"].get("raw")) is str),
        raw_unique={kind: len({event["response"]["raw"] for event in calls if event["request"]["kind"] == kind and type(event["response"].get("raw")) is str}) for kind in MAX_OUTPUT_TOKENS},
        token_costs="Native runner must report actual per-kind token counts; UTF8 bytes are not tokens.")
    return counts


def run_phase(state, backend, deps, *, binding=None):
    seed, arm = state_parts(state)
    require(callable(backend), "backend callback required")
    if binding is not None:
        producer, expected = binding["producer"], root_binding(seed)
        require(all(type(producer[key]) is type(expected[key]) and producer[key] == expected[key] for key in ("learner_seed", "parent_plan_sha256", "adapter")) and
                producer["adapter_files"]["adapter_model.safetensors"] == expected["adapter_model_sha256"], "original producer binding required")
    manifest = build_manifest(deps)
    tasks = manifest["schedules"][str(seed)]
    events, records, contacts = [], [], []
    event = deps.parented._V2._event
    for block_index in range(4):
        block = tasks[2*block_index:2*block_index+2]
        family = block[0]["family"]
        lesson = "NEUTRAL" if arm == "ACTIVE_NEUTRAL" else family if arm == "ALIGNED" else "C" if family == "P" else "P"
        contact_hash = sha_text(LESSONS[lesson])
        parent_event = event(events, dict(kind="fixed_contact", state=state, block_index=block_index, lesson=lesson,
                                         raw=LESSONS[lesson], contact_sha256=contact_hash))
        restatement = call(backend, request(state, block[0], "restate", RESTATE_TEMPLATE.format(lesson=LESSONS[lesson]), contact=contact_hash), events, deps)
        response = restatement["response"]
        note = response.get("raw") if type(response.get("raw")) is str else None
        contacts.append(dict(block_index=block_index, lesson=lesson, contact=parent_event, restatement=restatement,
            score=score_restate(note, response.get("finish_reason"), lesson, restatement["errors"])))
        context = "" if note is None else "Current child NOTE (verbatim):\n"+note+"\nEnd child NOTE.\n\n"
        for task in block:
            public = event(events, dict(kind="harness_public_receipts", state=state, task_id=task["task_id"], receipts=copy.deepcopy(task["public_receipts"]),
                evaluations=copy.deepcopy(task["public_world_evaluations"]), origin="harness_provided_not_child_actions"))
            wake = call(backend, request(state, task, "wake", context+task["ordinary_prompt"], contact=contact_hash), events, deps)
            response = wake["response"]
            score = score_wake(response.get("raw"), response.get("finish_reason"), task, wake["errors"])
            row = dict(task_id=task["task_id"], address=task["address"], task_index=task["task_index"], block_index=block_index, family=family,
                variant=task["variant"], delivery=task["delivery"], public_event_sha256=public["sha256"], wake=wake, wake_score=score,
                execution=None, record=None, record_score=None, status="RECORD_NOT_CALLED_INVALID_WAKE", **{name: False for name in ENDPOINTS})
            row.update(PROCESS_USE=score["PROCESS_USE"], WAKE_SCHEMA=score["schema_valid"])
            if score["action_valid"]:
                parsed = score["parsed"]
                actual = world_result(deps.game_class(), deps, task["world_id"], parsed["action"]["values"], parsed["prediction"])
                receipt = dict(receipt_id=opaque("child-receipt", state, task["task_id"]), time=len(task["public_receipts"])+1,
                               **{"try": actual["values"]}, predicted=actual["predicted"], observed=actual["observed"])
                execution = event(events, dict(actual, kind="execution", state=state, task_id=task["task_id"], receipt=receipt,
                    source_call_id=wake["request"]["request_id"], source_call_sha256=wake["sha256"], origin="current_child_fresh_action"))
                prompt = context+RECORD_INSTRUCTION+"Public source fields: "+NOTE_INSTRUCTIONS[family]+"\nOriginal public task:\n"+canonical(task["public"])+"\nYour pre-action output (verbatim):\n"+response["raw"]+"\nFresh receipt:\n"+canonical(receipt)
                record = call(backend, request(state, task, "record", prompt, contact=contact_hash, execution=execution["sha256"]), events, deps)
                reply = record["response"]
                record_score = score_record(reply.get("raw"), reply.get("finish_reason"), task, execution, deps, record["errors"])
                row.update(EXECUTED=True, execution=execution, record=record, record_score=record_score,
                    RECORD_FAITHFUL=record_score["RECORD_FAITHFUL"], RECORD_SOURCE=record_score["RECORD_SOURCE"], OWN_EVENT=record_score["OWN_EVENT"],
                    ADDRESS=record_score["ADDRESS"], RECORD_SCHEMA=record_score["schema_valid"],
                    FULL_MATERIAL=row["PROCESS_USE"] and record_score["RECORD_FAITHFUL"], status="RECORD_OBSERVED")
                row["SCHEMA_FULL_MATERIAL"] = row["FULL_MATERIAL"] and row["WAKE_SCHEMA"] and row["RECORD_SCHEMA"]
            records.append(row)
    summary = readout(records, contacts, events)
    require(summary["complete"] and summary["calls"] <= 20, "fixed task/contact/call ceiling differs")
    result = dict(schema=SCHEMA, state=state, seed=seed, arm=arm, phase="inference", binding=copy.deepcopy(binding), original_root=root_binding(seed),
        manifest_sha256=manifest["manifest_sha256"], events=events, contacts=contacts, records=records, readout=summary, summary=copy.deepcopy(summary),
        native_identity_verified=False, automatic_pass=False, fit_authorized=False, updates=0, qualification=QUALIFICATION)
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
    require(index == len(calls) and canonical(rebuilt) == canonical(capture), "deterministic call/world/score replay differs")
    return dict(consistent=True, capture_sha256=pin, calls_replayed=index, readout=copy.deepcopy(capture["readout"]), native_identity_verified=False)


def audit_capture(capture, *, dependencies):
    return replay_validate(capture, dependencies)


def threshold_vector(cells):
    require(type(cells) is dict and set(cells) <= set(STATES), "unknown measurement cell")
    complete = set(cells) == set(STATES) and all(cell["complete"] for cell in cells.values())
    roots = []
    for seed in range(3):
        if not all(f"perception_seed{seed}_{arm}" in cells for arm in ARMS):
            continue
        selected = {arm: cells[f"perception_seed{seed}_{arm}"] for arm in ARMS}
        roots.append(dict(seed=seed, arms={arm: {name: cell[name] for name in ENDPOINTS} for arm, cell in selected.items()},
            paired={arm: {name: selected["ALIGNED"][name]-selected[arm][name] for name in ENDPOINTS} for arm in ("SWAPPED", "ACTIVE_NEUTRAL")}))
    return dict(complete=complete, missing=sorted(set(STATES)-set(cells)), incomplete=sorted(state for state, cell in cells.items() if not cell["complete"]), roots=roots, vector={}, root_masks={},
        feasibility_pass=None, thresholds_adopted=False, automatic_pass=False, fit_authorized=False, updates=0,
        interpretation="Descriptive explicit-contract DEV measurement only; no parenting qualification or automatic scientific pass.")


def summarize(captures, deps):
    require(type(captures) in (list, tuple), "capture list required")
    cells = {}
    for capture in captures:
        require(capture["state"] not in cells, "duplicate measurement state")
        replay_validate(capture, deps)
        cells[capture["state"]] = capture["readout"]
    require(sum(cell["calls"] for cell in cells.values()) <= 180, "campaign call ceiling exceeded")
    return dict(schema=SCHEMA, cells=copy.deepcopy(cells), gate=threshold_vector(cells), updates=0, fits=0,
                native_identity_verified=False, automatic_pass=False, fit_authorized=False, qualification=QUALIFICATION)
