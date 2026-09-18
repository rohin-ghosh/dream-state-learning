"""Pure source replay, cue masks and fixed 2+2 second-sleep indexes.

The caller authenticates the selected adapter/archive and owns native execution.
This module loads no model, tokenizer or native library, and writes no files.
Recorded original-file/code hashes are retained, not independent authentication.
"""

from hashlib import sha256
import json
from pathlib import Path
import re

from gpu import astra_experienced_event_cue_collect as collector
from gpu import astra_experienced_event_microloop as memory_source
from gpu import astra_pchain2_native as native
from organism_v6 import experienced_event_cue_collection as cue
from organism_v6 import experienced_event_microloop as micro
from organism_v6 import experienced_event_read_route as controller


UPDATES = 200
MEMORY_ROW_COUNT = 32
MAX_CUE_CALLS = 24
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_CONTEXT = memory_source.MAX_CONTEXT
LOSS_POLICY = dict(prefix="MASK_ALL", assistant="TRAIN", eot="TRAIN")
DEFAULT_GUIDANCE = cue.GUIDANCE
TEACHING_MODES = (cue.PUBLIC_FEEDBACK_MODE, cue.LAST_TURN_FEEDBACK_MODE)
require = micro._require


def _bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                      separators=(",", ":")).encode("ascii")


def _same(actual, expected, reason):
    require(_bytes(actual) == _bytes(expected), reason)


def _sha(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _student_row(row):
    require(type(row) is dict and row.get("status") == "DRAFT_NOT_RELEASED",
            "actual_cue_draft_required")
    require(type(row.get("source_call_index")) is int and row["source_call_index"] >= 0
            and type(row.get("episode_index")) is int and 0 <= row["episode_index"] < 4,
            "bank_local_source_identity_required")
    prefix = row.get("prefix")
    require(type(prefix) is list and len(prefix) in (2, 4, 6), "bounded_cue_history_required")
    roles = ["system", "user"] + ["assistant", "user"] * ((len(prefix) - 2) // 2)
    require(all(type(message) is dict and set(message) == {"role", "content"}
                and message["role"] == role and type(message["content"]) is str
                for message, role in zip(prefix, roles))
            and prefix[0]["content"] == controller.PUBLIC_SYSTEM, "public_cue_prefix_required")
    require(all(marker not in message["content"] for message in prefix
                for marker in (DEFAULT_GUIDANCE, collector.EXPLICIT_GUIDANCE, cue.PUBLIC_FEEDBACK_PREFIX)),
            "teacher_forbidden_in_student_prefix")
    require(row.get("target_eot") == "<|im_end|>" and row.get("loss_policy") == LOSS_POLICY,
            "assistant_eot_only_policy_required")
    controller.parse_command(row.get("assistant"))


def _actor_binding(result, request, expected):
    require(_sha(expected), "expected_actor_sha256_required")
    require(result.get("schema") == "DEV_GUIDED_EXTERNAL_EVENT_CUE_REUSE_V1"
            and result.get("status") == "COLLECTION_COMPLETE_NO_FIT", "terminal_cue_collection_required")
    require(result.get("actor_kind") == "FROZEN_SAVED_MEMORY_LEARNER"
            and result.get("actor_adapter_file_sha256") == expected, "same_saved_actor_required")
    before = result.get("actor_adapter_state_before")
    require(_sha(before) and result.get("actor_adapter_state_after") == before
            and result.get("frozen_base_unchanged") is True, "unchanged_actor_and_base_required")
    require(_sha(result.get("actor_training_result_sha256")), "actor_training_receipt_required")
    require(type(request) is dict and all(key in result and _bytes(result[key]) == _bytes(value)
                for key, value in request.items()), "request_result_mismatch")
    for document in (request, result):
        require(document.get("master") == collector.MASTER
                and document.get("teaching_mode") in TEACHING_MODES,
                "public_feedback_training_source_required")
        arguments = document.get("arguments")
        require(type(arguments) is dict and arguments.get("phase") == "readout"
                and arguments.get("public_feedback", False) is (document["teaching_mode"] == cue.PUBLIC_FEEDBACK_MODE)
                and arguments.get("last_turn_feedback", False) is (document["teaching_mode"] == cue.LAST_TURN_FEEDBACK_MODE)
                and arguments.get("explicit_cue_strategy") is True
                and all(type(arguments.get(key)) is str and bool(arguments[key])
                        for key in ("cue_adapter_dir", "adapter_collection", "reuse_experiences"))
                and arguments.get("adapter_dir") == arguments["cue_adapter_dir"],
                "saved_actor_request_required")
    require(result.get("guidance") == collector.EXPLICIT_GUIDANCE
            and result.get("guidance_sha256") == sha256(collector.EXPLICIT_GUIDANCE.encode()).hexdigest(),
            "explicit_guidance_binding_required")
    for name, count in dict(banks=2, admitted_events=8, event_denominator=8,
                            cue_task_denominator=8, experiences_reused=8,
                            new_exploration_event_calls=0, fits=0).items():
        require(type(result.get(name)) is int and result[name] == count, "collection_count_mismatch:" + name)
    require(type(result.get("student_rows")) is int and result["student_rows"] > 0
            and type(result.get("selected_successes")) is int and result["selected_successes"] > 0,
            "nonempty_selected_source_required_no_fit")


def load_cue_rows(directory, *, expected_actor_sha256):
    """Replay both banks/all native calls, requiring a mismatch continuation each.

    Returned rows preserve the original bank-local indices and bytes. row_origins
    supplies the bank/global join; no IDs or targets are rewritten for uniqueness.
    This temporary guidance binding is restored on every exit; use sequentially.
    """
    root = Path(directory).resolve()
    require(not (root / "FAILED.json").exists(), "failed_collection_forbidden")
    pins = {}

    def read(name):
        path = root / name
        require(path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_FILE_BYTES,
                "bounded_source_file_required:" + name)
        raw = path.read_bytes()
        pins[name] = sha256(raw).hexdigest()
        return json.loads(raw)

    result, request = read("RESULT.json"), read("REQUEST.json")
    _actor_binding(result, request, expected_actor_sha256)
    count = result.get("physical_model_calls")
    require(type(count) is int and 0 < count <= MAX_CUE_CALLS
            and type(result.get("physical_actor_calls")) is int
            and result["physical_actor_calls"] == count, "bounded_actual_cue_calls_required")
    names = [f"CALL_{index:03d}.json" for index in range(count)]
    require(sorted(path.name for path in root.glob("CALL_*.json")) == names,
            "complete_native_call_inventory_required")
    calls = [read(name) for name in names]
    for index, call in enumerate(calls):
        require(type(call) is dict and type(call.get("call_index")) is int
                and call["call_index"] == index and call.get("error") is None,
                "ordered_native_call_required")
        response = call.get("response")
        require(type(response) is dict and type(response.get("raw")) is str
                and type(response.get("terminal")) is bool and type(response.get("truncated")) is bool
                and response.get("messages") == call.get("messages"), "actual_native_response_required")
        if "token_ids" in response:
            token_ids = response["token_ids"]
            require(type(token_ids) is list and bool(token_ids)
                    and all(type(token) is int and token >= 0 for token in token_ids)
                    and (not response["terminal"] or token_ids[-1] == result["tokenizer"]["eos_token_id"]),
                    "native_terminal_token_mismatch")
    reused = read("REUSED_EXPERIENCES.json")
    _same(reused["input_file_sha256"], result["input_file_sha256"], "reused_input_hashes_mismatch")
    require(reused.get("source_directory") == request["arguments"]["reuse_experiences"]
            and reused.get("source_cue_rows_used") is False and reused.get("source_cue_scores_used") is False
            and type(reused.get("banks")) is list and len(reused["banks"]) == 2,
            "unselected_original_experiences_required")
    require(reused.get("expected_base_sha256") == request["arguments"].get("expected_base_sha256")
            and _sha(reused.get("expected_base_sha256")), "reused_base_binding_mismatch")
    require(all(_sha(value) for value in reused["input_file_sha256"].values()), "original_input_hash_required")
    reports, rows, origins, coverage = [], [], [], []
    cursor = 0

    def captured_actor(messages):
        nonlocal cursor
        require(cursor < len(calls), "missing_native_call")
        record = calls[cursor]
        _same(record["messages"], messages, "native_guided_prompt_replay_mismatch")
        cursor += 1
        return controller._copy(record["response"])

    previous_guidance = cue.GUIDANCE
    try:
        cue.GUIDANCE = result["guidance"]
        for bank_index, bank in enumerate(collector.training_banks()):
            prefix = f"BANK_{bank_index:02d}/"
            captured_bank, experiences = read(prefix + "BANK.json"), read(prefix + "EXPERIENCES.json")
            _same(captured_bank, bank, "fixed_training_bank_mismatch")
            original = reused["banks"][bank_index]
            _same(original["bank"], bank, "reused_bank_mismatch")
            _same(original["experiences"], experiences, "reused_experience_mismatch")
            require(type(experiences) is list and len(experiences) == 4, "four_original_experiences_required")
            memory = {}
            for index, (fact, experience) in enumerate(zip(bank, experiences), 1):
                _same(read(prefix + f"EXPERIENCE_{index:02d}.json"), experience, "individual_experience_mismatch")
                require(experience.get("fact") == fact and experience.get("admitted") is True
                        and experience.get("error") is None, "admitted_original_event_required")
                exploration, event = experience["exploration"], experience["event"]
                require(all(response.get("terminal") is True and response.get("truncated") is False
                            for response in (exploration, event)), "terminal_original_experience_required")
                expected_messages = micro.observation_messages(fact, exploration["raw"])
                for response, messages in ((exploration, micro.exploration_messages(fact)), (event, expected_messages)):
                    if "messages" in response:
                        _same(response["messages"], messages, "original_experience_prompt_mismatch")
                require(micro.canonical_event(event["raw"]) == micro._event(fact), "original_event_grounding_mismatch")
                memory[fact["event"]] = event["raw"]
            for name in ("BANK.json", "EXPERIENCES.json", *(f"EXPERIENCE_{index:02d}.json" for index in range(1, 5))):
                require(pins[prefix + name] == reused["input_file_sha256"].get(prefix + name), "copied_experience_hash_mismatch")
            _same(memory, original["raw_memory_by_address"], "raw_memory_changed")
            start = cursor
            recorded = read(prefix + "CUE_COLLECTION.json")
            replayed = cue.run_collection(bank, memory, captured_actor, teaching_mode=result["teaching_mode"])
            _same(replayed, recorded, "complete_cue_report_replay_mismatch")
            require(replayed["infrastructure_failures"] == 0, "cue_infrastructure_failure")
            first_reads, second_reads = 0, 0
            for record in replayed["episodes"]:
                memory_traces = [trace for trace in record["episode"]["traces"] if trace["kind"] == "memory"]
                if record["selected"] and len(memory_traces) == 1:
                    first_reads += 1
                if not record["selected"] or len(memory_traces) != 2:
                    continue
                first, second = (micro.parse_event_line(micro.canonical_event(trace["raw"])) for trace in memory_traces)
                task = record["task"]
                if ((first["source"], first["destination"]) != (task["node"], task["goal"])
                        and (second["source"], second["destination"], second["port"])
                        == (task["node"], task["goal"], record["episode"]["chosen_port"])):
                    second_reads += 1
            require(second_reads > 0, f"successful_mismatch_second_read_required_bank_{bank_index}")
            require(first_reads > 0, f"successful_one_read_required_bank_{bank_index}")
            for row in replayed["student_rows"]:
                _student_row(row)
                global_index = start + row["source_call_index"]
                require(row["assistant"] == calls[global_index]["response"]["raw"], "actual_target_mismatch")
                origins.append(dict(row_index=len(rows), bank_index=bank_index,
                    episode_index=row["episode_index"], source_call_index=row["source_call_index"],
                    global_call_index=global_index, source_row_sha256=sha256(_bytes(row)).hexdigest()))
                rows.append(controller._copy(row))
            coverage.append(dict(bank_index=bank_index, selected_successes=replayed["selected_successes"],
                successful_one_reads=first_reads, successful_mismatch_second_reads=second_reads,
                student_rows=len(replayed["student_rows"])))
            reports.append(dict(bank=bank_index, admitted_events=4, collection=replayed))
    finally:
        cue.GUIDANCE = previous_guidance
    require(cursor == count, "unused_native_calls")
    _same(read("BANK_RESULTS.json"), reports, "combined_bank_report_mismatch")
    require(len(rows) == result["student_rows"] and sum(item["selected_successes"] for item in coverage)
            == result["selected_successes"], "selected_totals_mismatch")
    return tuple(rows), dict(source_directory=str(root), result_sha256=pins["RESULT.json"],
        source_files=dict(pins), input_file_sha256=dict(pins), rows_sha256=sha256(_bytes(rows)).hexdigest(),
        actor_adapter_sha256=expected_actor_sha256, actor_state_sha256=result["actor_adapter_state_before"],
        actor_training_result_sha256=result["actor_training_result_sha256"],
        recorded_source_sha256=result.get("source_sha256", {}), original_input_file_sha256=reused["input_file_sha256"],
        teaching_mode=result["teaching_mode"], guidance_sha256=result["guidance_sha256"],
        row_origins=origins, coverage=coverage, successful_rows=len(rows), physical_actor_calls=count)


def encode_cue_rows(rows, tokenizer):
    """Encode final captured action/EOT only; all earlier assistant turns are masked."""
    require(type(rows) in (list, tuple) and 0 < len(rows) <= MAX_CUE_CALLS, "nonempty_bounded_cue_rows_required")
    require(tokenizer.eos_token == "<|im_end|>" and type(tokenizer.eos_token_id) is int
            and native._encode(tokenizer, tokenizer.eos_token) == (tokenizer.eos_token_id,), "exact_cue_eot_required")
    encoded = []
    for row in rows:
        _student_row(row)
        messages = row["prefix"] + [dict(role="assistant", content=row["assistant"])]
        context = tokenizer.apply_chat_template(row["prefix"], tokenize=False, add_generation_prompt=True, return_dict=False)
        full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, return_dict=False)
        require(full == context + row["assistant"] + tokenizer.eos_token + "\n", "exact_cue_template_boundary_required")
        prefix_ids, target = native._encode(tokenizer, context), native._encode(tokenizer, row["assistant"])
        suffix = native._encode(tokenizer, "\n")
        require(not set(tokenizer.all_special_ids).intersection(target), "cue_target_special_token_forbidden")
        supervised = target + (tokenizer.eos_token_id,)
        sequence = native._encode(tokenizer, full)
        require(sequence == prefix_ids + supervised + suffix and len(sequence) <= MAX_CONTEXT,
                "untruncated_exact_cue_sequence_required")
        require(native._decode(tokenizer, sequence) == full
                and native._decode(tokenizer, supervised) == row["assistant"] + tokenizer.eos_token,
                "cue_token_roundtrip_failed")
        require(tuple(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False,
                    return_dict=False, truncation=False, padding=False)) == sequence, "cue_template_token_ids_mismatch")
        encoded.append(native.EncodedRow(sequence,
            (-100,) * len(prefix_ids) + supervised + (-100,) * len(suffix), supervised))
    return tuple(encoded)


def mixed_indexes(update, cue_count):
    """Two cyclic original-memory rows plus two cyclic cue rows; 400 of each."""
    require(type(update) is int and 1 <= update <= UPDATES, "fixed_200_update_range")
    require(type(cue_count) is int and 0 < cue_count <= MAX_CUE_CALLS, "positive_bounded_cue_count_required")
    start = 2 * (update - 1)
    return (start % MEMORY_ROW_COUNT, (start + 1) % MEMORY_ROW_COUNT,
            MEMORY_ROW_COUNT + start % cue_count, MEMORY_ROW_COUNT + (start + 1) % cue_count)
