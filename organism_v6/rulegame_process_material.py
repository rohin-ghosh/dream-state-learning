"""Prospective rulegame_grounded_process_pair_v1; raw wake context distillation only."""
from __future__ import annotations

import ctypes
import copy
import errno
import os
from pathlib import Path
import re

from . import rulegame_parenting_diagnostic as diagnostic
from . import rulegame_record_material as records
from . import train_adapter_v3 as trainer


PROTOCOL = "rulegame_grounded_process_pair_v1"
DECISION = "Main prospective decision 11417838, 2026-09-12"
TRANSFORMATION = "remove_source_bound_temporary_restatement_utf8_v1"
SLOTS = tuple((arm, lesson) for arm in diagnostic.ARMS for lesson in range(2))
RESTATEMENT_MARKER = "\nTemporary parent restatement:\n"
POLICY = dict(protocol=PROTOCOL, decision=DECISION,
    selection="first executed TRY after an earlier public TRY and before quiz reveal, per apply lesson0/1 and P/A",
    eligibility="single canonical ACT TRY and single explicit unambiguous pre-ACT PREDICT T/F; no correctness selection",
    shortage="any unavailable/invalid/copied-teacher slot blocks both arms; no later replacement",
    transformation=TRANSFORMATION, target="complete unchanged own raw wake output",
    literal_copy_check="rulegame_record_material._payload_spans/_check_payload over all formation parent/restatement texts",
    conditioning="CONTEXT_DISTILLATION_NOT_UNCHANGED_NATIVE_CONTEXT",
    rows_per_arm=2, semantic_certification=False, heldout_scores_used_for_selection=False,
    model_calls=0, training_calls=0, new_record_targets=0)
require = diagnostic.require


def source_hashes():
    return dict(diagnostic.sources(), **{Path(module.__file__).name: diagnostic.digest(module.__file__)
        for module in (records, trainer)}, rulegame_process_material=diagnostic.digest(__file__))


def _path(path):
    path = Path(path).expanduser().absolute()
    require(not any(part.is_symlink() for part in (path, *path.parents)), "aliased source/output forbidden")
    return path


def select_slots(events):
    """Position only: neither predictions, records nor outcome/quiz correctness select a slot."""
    result = []
    for arm, lesson in SLOTS:
        eid = diagnostic.task_id(lesson, "apply")
        preceding, selected, stopped = [], None, []
        for index, event in enumerate(events):
            if event.get("arm") != arm or event.get("eid") != eid:
                continue
            if event["kind"] == "protocol_invalid":
                stopped.append(dict(event_index=index, call_id=event["call_id"], failure=event["failure"]))
            if event["kind"] != "execution":
                continue
            if event["action_kind"] in ("reveal", "quiz"):
                break
            if event["action_kind"] == "try" and preceding:
                selected = dict(event_index=index, execution_id=event["execution_id"], call_id=event["call_id"], tick=event["tick"])
                break
            if event["action_kind"] == "try":
                preceding.append(dict(event_index=index, execution_id=event["execution_id"], call_id=event["call_id"], tick=event["tick"]))
        result.append(dict(slot_id=f"{arm}:lesson{lesson}", arm=arm, lesson=lesson, eid=eid,
            selected=selected, preceding_public_executions=preceding, stopped_before_slot=stopped))
    return result


def validate_wake(text):
    action = diagnostic.parse_action(text, "interaction_v3")
    canonical = diagnostic.parse_action(text, "strict_v1")
    require(action == canonical and action["kind"] == "try", "one canonical ACT TRY required, not an alias")
    predictions = list(re.finditer(r"^[ \t]*PREDICT\b[^\n]*", text, re.MULTILINE))
    require(len(predictions) == 1 and re.fullmatch(r"PREDICT:[ \t]*[TF][ \t]*", predictions[0].group()) is not None,
        "single explicit unambiguous PREDICT T/F required")
    act = re.search(r"^ACT: ", text, re.MULTILINE)
    require(act is not None and predictions[0].start() < act.start() and type(action["predicted"]) is bool and
        action["prediction_ambiguous"] is False, "PREDICT must precede the single ACT")
    return action


def transform_context(prompt, slot, restatement, preceding):
    """Reconstruct source first, then remove one exact UTF-8 interval; never sanitize history."""
    require(isinstance(restatement, str) and restatement, "missing source-bound restatement")
    require(len(preceding) == slot["selected"]["tick"] - 1 and preceding, "missing preceding public history")
    header = (f"{diagnostic.BOOT}\nTask: {slot['eid']}\nGoal: Induce the hidden rule and answer the quiz.\n"
        f"Response: {slot['selected']['tick']}/5\nA fresh mystery box.")
    block = RESTATEMENT_MARKER + restatement
    history = "".join("\n" + row["raw_wake"] + "\n[OUTCOME] " + row["outcome"] for row in preceding)
    suffix = (f"\nHarness state: remaining TRY budget: {3 - len(preceding)}. "
        "Quiz reveal still needed before scoring: ACT: QUIZ ?."
        "\nEmit one action only; never supply [OUTCOME] or simulate a world reply.")
    require(prompt == header + block + history + suffix, "original wake reconstruction mismatch")
    source = prompt.encode("utf-8")
    start, end = len(header.encode("utf-8")), len((header + block).encode("utf-8"))
    require(source[start:end] == block.encode("utf-8"), "source deletion interval mismatch")
    transformed = (source[:start] + source[end:]).decode("utf-8")
    require(transformed == header + history + suffix, "non-restatement bytes changed")
    return transformed, dict(version=TRANSFORMATION, start_byte=start, end_byte=end,
        removed_utf8_sha256=records._text_hash(block), removed_utf8_bytes=end-start,
        original_utf8_sha256=records._text_hash(prompt), transformed_utf8_sha256=records._text_hash(transformed),
        retained_prefix_sha256=records._text_hash(header), retained_suffix_sha256=records._text_hash(history + suffix))


def inspect_capture(capture_root):
    """CPU availability only. Audit-only return contains teacher-visible sources, never a corpus."""
    path = _path(capture_root)
    sources = source_hashes()
    inventory = diagnostic.tree_hashes(path)
    files = diagnostic.read(path / "manifest.json")["files"]
    header = diagnostic.read(path / "identity.json")
    require(header["stage"] == "formation" and header.get("protocol") == "interaction_v3", "only interaction_v3 formation, never P0/evaluation")
    require(isinstance(header["model_files"], dict) and header["model_files"] and
        isinstance(header["backend"].get("adapter_files"), dict), "captured model/adapter hash inventory required")
    replay = diagnostic.check_capture(path, protocol="interaction_v3")
    require(replay["ok"], "source replay failed: " + str(replay["failures"]))
    require(replay["result"]["status"] == "AWAITING_MAIN_AUDIT", "complete formation required")
    interactions = replay["result"]["interactions"]
    require([(row["arm"], row["lesson"]) for row in interactions] == list(SLOTS), "four source interaction slots required")
    teacher_sources, texts = [], []
    for interaction in interactions:
        for field, id_field, role in (("parent", "parent_call_id", "parent"), ("restatement", "restatement_call_id", "restate")):
            request, response, hashes = records._call(path, interaction[id_field], files)
            require(request["request"]["role"] == role and request["request"]["arm"] == interaction["arm"] and
                request["request"]["eid"] == diagnostic.task_id(interaction["lesson"], "pre") and
                response["response"]["text"] == interaction[field], "parent/restatement source join differs")
            texts.append(interaction[field])
            teacher_sources.append(dict(arm=interaction["arm"], lesson=interaction["lesson"], role=role,
                call_id=interaction[id_field], files=hashes, raw_text=interaction[field], utf8_sha256=records._text_hash(interaction[field])))
    spans = records._payload_spans(texts, "interaction_v3")
    slots = select_slots(replay["events"])
    candidates = []
    for slot, interaction in zip(slots, interactions, strict=True):
        row = dict(slot, failures=[], eligible=False)
        if slot["selected"] is None:
            row["failures"].append("missing first executed TRY after prior public TRY before quiz reveal")
            candidates.append(row)
            continue
        selected = slot["selected"]
        execution = replay["events"][selected["event_index"]]
        sent, received, hashes = records._call(path, selected["call_id"], files)
        request, response = sent["request"], received["response"]
        require(request["role"] == "wake" and all(request[key] == execution[key] for key in ("arm", "eid", "tick")) and
            response["text"] == execution["raw_response"], "selected execution/wake join differs")
        prior = []
        for earlier in slot["preceding_public_executions"]:
            event = replay["events"][earlier["event_index"]]
            prior_sent, prior_received, prior_hashes = records._call(path, earlier["call_id"], files)
            require(prior_received["ended"] <= sent["started"] and event["action_kind"] == "try" and
                prior_received["response"]["text"] == event["raw_response"] and
                all(prior_sent["request"][key] == event[key] for key in ("arm", "eid", "tick")), "prior public wake/event differs")
            prior.append(dict(earlier, raw_wake=prior_received["response"]["text"], outcome=event["outcome"],
                files=prior_hashes, event_sha256=diagnostic.value_hash(event)))
        transformed, interval = transform_context(request["prompt"], slot, interaction["restatement"], prior)
        row.update(context=transformed, target=response["text"], preceding_public_history=prior,
            source=dict(request_receipt=sent, response_receipt=received, files=hashes, execution=execution,
                execution_event_sha256=diagnostic.value_hash(execution)), removed_intervals=[dict(interval,
                    source_restatement_call_id=interaction["restatement_call_id"])])
        try:
            action = validate_wake(row["target"])
            require(all(action[key] == execution[key] for key in ("action", "values", "predicted", "prediction_ambiguous")), "wake action/prediction join differs")
        except ValueError as error:
            row["failures"].append(str(error))
        for name, text in (("retained wake context/history", transformed), ("complete raw wake target", row["target"])):
            try:
                records._check_payload(text, spans, name)
            except ValueError as error:
                row["failures"].append(str(error))
        row["eligible"] = not row["failures"]
        candidates.append(row)
    source_plan = None
    plan_path = path.parents[1] / "plan.json"
    if plan_path.is_file():
        plan = diagnostic.read(plan_path)
        require(diagnostic.digest(plan_path) == diagnostic.read(plan_path.with_name("plan.sha256.json"))["sha256"] and
            plan.get("protocol") == "interaction_v3" and plan["model_files"] == header["model_files"] and
            plan["model"] == header["backend"]["model_input"], "formation plan/identity differs")
        source_plan = dict(path=str(plan_path), sha256=diagnostic.digest(plan_path), source_hashes=plan["source_hashes"])
    result = dict(protocol=PROTOCOL, policy=POLICY, status="AVAILABLE_PENDING_MAIN_REVIEW" if all(row["eligible"] for row in candidates) else "PAIRED_SHORTAGE",
        source_hashes=sources, source_binding=dict(capture_root=str(path), files=inventory,
            formation_sha256=inventory["manifest.json"], identity=header, source_plan=source_plan,
            replay_sha256=diagnostic.value_hash(replay), native_token_validation="PENDING_CALLBACK", model_origin="UNRESOLVED_LOCAL_HASHES_ONLY"),
        fixed_slots=slots, selection_sha256=diagnostic.value_hash(slots), candidates=candidates,
        teacher_sources_audit_only=teacher_sources, semantic_certification=False,
        full_pair_required=True, heldout_scores_used_for_selection=False)
    require(diagnostic.tree_hashes(path) == inventory and source_hashes() == sources, "source changed during availability audit")
    result["candidate_sha256"] = diagnostic.value_hash(result)
    return result


def review_template(candidate):
    return dict(actor="Main", protocol=PROTOCOL, candidate_sha256=candidate["candidate_sha256"],
        scope="transformed_context_and_complete_raw_wake", context_distillation_acknowledged=False,
        reviews=[dict(slot_id=row["slot_id"], call_id=row["selected"]["call_id"] if row["selected"] else None,
            decision="pending", notes="") for row in candidate["candidates"]])


def _review(candidate, review):
    template = review_template(candidate)
    require(isinstance(review, dict) and all(review.get(key) == template[key] for key in ("actor", "protocol", "candidate_sha256", "scope")) and
        review.get("context_distillation_acknowledged") is True, "bound Main context-distillation review required")
    require(isinstance(review.get("reviews"), list) and len(review["reviews"]) == 4, "Main must review four rows")
    for actual, expected in zip(review["reviews"], template["reviews"], strict=True):
        require(isinstance(actual, dict) and all(actual.get(key) == expected[key] for key in ("slot_id", "call_id")) and actual.get("decision") == "accept" and
            isinstance(actual.get("notes"), str) and actual["notes"].strip(), "Main four-row acceptance/notes required; not a semantic certificate")


def _encode(row, tokenizer, max_len, spans):
    response = row["source"]["response_receipt"]["response"]
    original_prompt = row["source"]["request_receipt"]["request"]["prompt"]
    original_rendered = tokenizer.apply_chat_template([dict(role="user", content=original_prompt)], tokenize=False, add_generation_prompt=True)
    require(original_rendered == response["rendered_prompt"] and
        tokenizer.encode(original_rendered, add_special_tokens=False) == response["prompt_token_ids"], "original source rendering/input IDs differ")
    rendered = tokenizer.apply_chat_template([dict(role="user", content=row["context"])], tokenize=False, add_generation_prompt=True)
    require(isinstance(rendered, str) and rendered.count(row["context"]) == 1, "transformed context must render once")
    records._check_payload(rendered, spans, "new rendered training input")
    prefix = tokenizer.encode(rendered, add_special_tokens=False)
    target = tokenizer.encode(row["target"], add_special_tokens=False)
    eos = tokenizer.eos_token_id
    require(prefix and target and all(type(token) is int and token >= 0 for token in prefix + target) and eos not in target,
        "invalid token IDs or EOS already in unchanged raw target")
    require(len(prefix) + len(target) + 1 <= max_len, "overlength; no truncation/splits/replacement")
    item = dict(spans=[[rendered, False, "parent_removed_wake_context"], [row["target"], True, "complete_own_raw_wake"]],
        group=row["eid"], view=PROTOCOL, order=row["lesson"],
        meta=dict(protocol=PROTOCOL, slot_id=row["slot_id"], execution_id=row["selected"]["execution_id"],
            source_call_id=row["selected"]["call_id"], arm=row["arm"], lesson=row["lesson"]))
    segments = trainer.encode_item_segments(trainer.normalize_items([item])[0], tokenizer, max_len,
        chat_template=False, add_eos=True, item_index=row["lesson"], overflow="split")
    require(len(segments) == 1 and segments[0].n_splits == 1 and
        segments[0].context_dropped == segments[0].target_dropped == 0, "trainer dropped/split material")
    ids, labels = prefix + target + [eos], [trainer.IGNORE] * len(prefix) + target + [eos]
    batch = trainer.collate([segments], tokenizer.pad_token_id)
    require(batch["input_ids"] == [ids] and batch["labels"] == [labels] and batch["n_target"] == len(target) + 1 and
        batch["position_ids"] == [list(range(len(ids)))] and batch["segment_ids"] == [[0] * len(ids)], "full causal mask/offset/EOS mismatch")
    predictors = [index for index, label in enumerate(labels[1:]) if label != trainer.IGNORE]
    require(predictors == list(range(len(prefix)-1, len(ids)-1)), "shifted target predictor offsets differ")
    return item, dict(slot_id=row["slot_id"],
        original_native_capture=dict(rendered_prompt=response["rendered_prompt"], prompt_token_ids=response["prompt_token_ids"],
            output_token_ids=response["output_token_ids"], raw_text=response["text"], native_output_decode_verified=True),
        transformed_training=dict(context=row["context"], rendered_context=rendered, context_token_ids=prefix,
            raw_target_token_ids=target, input_ids=ids, labels=labels, target_with_eos=target+[eos],
            first_target_predictor=len(prefix)-1, predictor_positions=predictors,
            input_tokens=len(ids), context_tokens=len(prefix), target_tokens=len(target)+1,
            raw_target_utf8_sha256=records._text_hash(row["target"]), source_output_token_ids_reused_as_targets=False),
        same_conditioning_as_native=False, packing=False, truncation=False, splitting=False)


def build_process_pair(capture_root, main_review, tokenizer, *, fixed_candidate=None, max_len=4096):
    require(type(max_len) is int and 1 <= max_len <= diagnostic.MAX_MODEL_LEN, "bounded max_len required")
    main_review = copy.deepcopy(main_review)
    candidate = inspect_capture(capture_root)
    require(fixed_candidate is None or diagnostic.value_hash(candidate) == diagnostic.value_hash(fixed_candidate), "fixed candidate changed; no reselection")
    require(candidate["status"] == "AVAILABLE_PENDING_MAIN_REVIEW", "paired shortage; no partial corpus or later replacement")
    _review(candidate, main_review)
    require(type(getattr(tokenizer, "eos_token_id", None)) is int and tokenizer.eos_token_id >= 0 and
        type(getattr(tokenizer, "pad_token_id", None)) is int and tokenizer.pad_token_id >= 0, "tokenizer EOS/pad required")
    path = _path(capture_root)
    diagnostic.audit_native_calls(tokenizer, path)
    spans = records._payload_spans([row["raw_text"] for row in candidate["teacher_sources_audit_only"]], "interaction_v3")
    corpora = {arm: dict(corpus=[]) for arm in diagnostic.ARMS}
    receipts = {arm: [] for arm in diagnostic.ARMS}
    for row in candidate["candidates"]:
        item, receipt = _encode(row, tokenizer, max_len, spans)
        corpora[row["arm"]]["corpus"].append(item)
        receipts[row["arm"]].append(receipt)
    require(all(len(corpora[arm]["corpus"]) == 2 for arm in diagnostic.ARMS), "full paired cardinality required")
    require(inspect_capture(path) == candidate, "source changed during native callback audit")
    return dict(protocol=PROTOCOL, status="PAIRED_CPU_TOKEN_AUDITED_MAIN_REVIEWED", corpora=corpora,
        audit=dict(candidate=candidate, main_review=main_review, receipts=receipts, max_len=max_len,
            tokenizer_class=type(tokenizer).__module__ + "." + type(tokenizer).__name__, native_identity_authenticated=False,
            source_native_token_audit=True, conditioning="CONTEXT_DISTILLATION_NOT_UNCHANGED_NATIVE_CONTEXT",
            token_totals={arm: {key: sum(row["transformed_training"][key] for row in receipts[arm])
                for key in ("input_tokens", "context_tokens", "target_tokens")} for arm in diagnostic.ARMS},
            teacher_sources_audit_only=True, semantic_certification=False, model_calls=0, training_calls=0,
            target_tokens_matched=False, input_tokens_matched=False, no_target_join=True))


def _publish(staging, destination):
    """Linux atomic directory publication, never replace even an empty racing destination."""
    library = ctypes.CDLL(None, use_errno=True)
    rename = getattr(library, "renameat2", None)
    require(rename is not None, "atomic no-replace directory publication unavailable")
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(staging), -100, os.fsencode(destination), 1) != 0:
        error = ctypes.get_errno()
        if error == errno.EEXIST:
            raise FileExistsError(destination)
        raise OSError(error, os.strerror(error))


def export_pair(capture_root, out, main_review, tokenizer, *, fixed_candidate=None, max_len=4096):
    source, destination = _path(capture_root), _path(out)
    require(destination != source and destination not in source.parents and source not in destination.parents,
        "source/output overlap forbidden")
    staging = destination.with_name("." + destination.name + ".pending")
    require(not destination.exists() and not staging.exists() and not staging.is_symlink(), "fresh pair output required; no overwrite/retry")
    result = build_process_pair(source, main_review, tokenizer, fixed_candidate=fixed_candidate, max_len=max_len)
    staging.mkdir(mode=0o700)
    (staging / "corpora").mkdir()
    (staging / "audit").mkdir()
    for arm in diagnostic.ARMS:
        diagnostic.write_json(staging / "corpora" / (arm + ".json"), result["corpora"][arm])
    diagnostic.write_json(staging / "audit/candidate.json", result["audit"]["candidate"])
    diagnostic.write_json(staging / "audit/main_review.json", result["audit"]["main_review"])
    diagnostic.write_json(staging / "audit/token_receipts.json", {key: value for key, value in result["audit"].items() if key not in ("candidate", "main_review")})
    manifest = dict(protocol=PROTOCOL, status=result["status"], source_hashes=source_hashes(),
        candidate_sha256=result["audit"]["candidate"]["candidate_sha256"], corpus_files={arm: f"corpora/{arm}.json" for arm in diagnostic.ARMS},
        files=diagnostic.tree_hashes(staging), token_totals=result["audit"]["token_totals"], max_len=max_len,
        conditioning="CONTEXT_DISTILLATION_NOT_UNCHANGED_NATIVE_CONTEXT", semantic_certification=False,
        model_origin="UNRESOLVED_LOCAL_HASHES_ONLY", model_calls=0, training_calls=0,
        writer_note="two raw rows per arm; no training recipe is executed; never enumerate audit files as corpus")
    diagnostic.write_json(staging / "manifest.json", manifest)
    require(inspect_capture(source) == result["audit"]["candidate"], "source changed before pair publication; preserve pending files")
    require(diagnostic.tree_hashes(staging, ("manifest.json",)) == manifest["files"], "staged pair changed")
    _publish(staging, destination)
    return manifest
