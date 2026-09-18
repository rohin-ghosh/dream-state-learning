"""Fixed worked-example -> own record -> parent-free application; 32 calls, no fits.

CPU: --out NEW --model-path LOCAL --pins PINS --prior-source-ids METADATA
     --prior-preparation V1_PREP --prior-preparation V2_PREP.
PINS: {"model_path": absolute_path, "files": local_file_sha256_map}.
Prior inventory: {"schema":"prior-source-ids-v1","episode_ids":[...]}.
Without prior IDs and actual v1/v2 preparation content, preparation remains pending. The captured
effective inventory also includes the previous 1851000..7 and 1851100..7 IDs.
Main alone runs --preparation PREP --out NEW --allow-gpu after reserving a
device and configuring V6_MODEL/offline flags. --condition is the internal
fresh-worker entrypoint. CPU replay: --analyze PAIR --out NEW.
One generation seed 7101, two fresh workers, 16 interleaved source/transfer
calls each; 128 tokens per call, 900 seconds per arm, 1800 per pair. Mandatory
supervisor cleanup gets a 60-second reserve. No response-based retries or fits.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import sys
import time

from . import constraint_check_diagnostic as base


SCHEMA = "constraint-demonstration-v1"
SOURCE_IDS = tuple(f"rg/mini_sudoku/{seed}" for seed in range(1851200, 1851208))
TRANSFER_IDS = tuple(f"rg/mini_sudoku/{seed}" for seed in range(1851300, 1851308))
ADDED_PRIOR_IDS = tuple(f"rg/mini_sudoku/{seed}" for start in (1851000, 1851100)
                        for seed in range(start, start + 8))
MODES = ("process", "format")
GROUPS = ("row", "column", "box", "row", "column", "box", "row", "column")
PROTOCOL = dict(pairs=8, calls_per_arm=16, total_calls=32, generation_seed=7101,
                generation_seed_role=base.SEED_ROLE, max_tokens=128, temperature=.7,
                max_input_and_output=4096, arm_seconds=900, total_seconds=1800,
                worker_wait_seconds=840, cleanup_reserve_seconds=60,
                order="source01,transfer01,...,source08,transfer08")
BOUNDARY = dict(base.BOUNDARY, stage="worked_example_own_record_parent_free_application",
                external_worked_example=True, independent_discovery_claim=False,
                persistence_claim=False, transfer_context="common task, new candidate, exact child note only",
                note_policy="all raw source outputs, including failures; never normalized, filtered or truncated")
SOURCE_INSTRUCTION = "Read the shared correct source example and explanation, then emit your own record for this source candidate."
TRANSFER_INSTRUCTION = (
    "Diagnose the new candidate below. The earlier source note is your own unmodified output about a different board. "
    "It is not a teacher instruction or a check of this board; verify the new board itself.")
EXAMPLE_LESSON = "Check equal values within the same group."
require, read, write, sha = base.require, base.read, base.write, base.sha


def source_pins(synthetic=False):
    return dict(base.source_pins(synthetic), **{str(Path(__file__).resolve()): base.formation._hash(__file__)})


def source_cells(index):
    group = GROUPS[index]
    if group == "row":
        return [[index % 4 + 1, (index // 4) * 2 + 1], [index % 4 + 1, (index // 4) * 2 + 2]]
    if group == "column":
        return [[(index // 4) * 2 + 1, index % 4 + 1], [(index // 4) * 2 + 2, index % 4 + 1]]
    top, left = (index % 4 // 2) * 2 + 1, (index % 2) * 2 + 1
    return [[top, left], [top + 1, left + 1]]


def record_text(case_id, group, cells, digit):
    return json.dumps(dict(case_id=case_id, checks=[dict(group=group, cells=cells, digit=digit)],
                           lesson=EXAMPLE_LESSON), separators=(",", ":"))


def initial_case(episode_id, question, index, stage):
    expected = SOURCE_IDS if stage == "source" else TRANSFER_IDS
    require(episode_id == expected[index], "fixed ordered native IDs required")
    puzzle = base.board_from_text(question, question=True)
    offset = index if stage == "source" else index + 8
    filled = [[value or 1 + (row * 2 + row // 2 + column + offset) % 4
               for column, value in enumerate(values)] for row, values in enumerate(puzzle)]
    return dict(case_id=f"{'s' if stage == 'source' else 't'}{index + 1:02}", episode_id=episode_id,
                split="train", origin=BOUNDARY["origin"], question=question,
                question_sha256=sha(question.encode()), source_board=puzzle,
                source_board_sha256=sha(base.formation.policy._encoded(puzzle)),
                filled_candidate=filled, candidate=copy.deepcopy(filled),
                program=dict(recipe="worked-pair-public-fill-break-copy-plant-v1", stage=stage,
                             index=index, edits=[], reference_answer_accessed=False, givens_may_be_corrupted=True))


def set_cell(case, cell, digit, reason):
    row, column = cell
    before = case["candidate"][row - 1][column - 1]
    case["candidate"][row - 1][column - 1] = digit
    case["program"]["edits"].append(dict(cell=cell, before=before, after=digit, reason=reason))


def make_pair(source_question, transfer_question, index):
    source = initial_case(SOURCE_IDS[index], source_question, index, "source")
    transfer = initial_case(TRANSFER_IDS[index], transfer_question, index, "transfer")
    cells = source_cells(index)
    row, column = cells[0]
    digit = source["candidate"][row - 1][column - 1] % 4 + 1
    for cell in cells:
        set_cell(source, cell, digit, "plant source worked witness")
    set_cell(transfer, cells[0], digit, "copied source pair: first value")
    set_cell(transfer, cells[1], digit % 4 + 1, "copied source pair: unequal second value")
    target_row = (index + 1) % 4 + 1
    target_cells = [[target_row, column] for column in range(1, 5) if [target_row, column] not in cells][:2]
    require(len(target_cells) == 2, "fixed target construction failed; no replacements")
    target_digit = 1 + (digit + index) % 4
    for cell in target_cells:
        set_cell(transfer, cell, target_digit, "plant disjoint transfer witness")
    for case in (source, transfer):
        case["candidate_sha256"] = sha(base.formation.policy._encoded(case["candidate"]))
    example = record_text(source["case_id"], GROUPS[index], cells, digit)
    copied = record_text(transfer["case_id"], GROUPS[index], cells, digit)
    target = record_text(transfer["case_id"], "row", target_cells, target_digit)
    source_score, copied_score, target_score = (base.score_record(text, case) for text, case in
                                               ((example, source), (copied, transfer), (target, transfer)))
    require(source_score["grounded"] == target_score["grounded"] == 1 and
            copied_score["format_valid"] and copied_score["grounded"] == 0,
            "source/transfer/copy predicate failed")
    require(transfer["candidate"][cells[0][0] - 1][cells[0][1] - 1] !=
            transfer["candidate"][cells[1][0] - 1][cells[1][1] - 1], "old cells remain equal")
    return dict(pair_id=f"p{index + 1:02}", source=source, transfer=transfer,
                example_text=example, example_sha256=sha(example.encode()),
                source_example_score=source_score, copied_witness_on_transfer_score=copied_score,
                copied_witness_test="same group/cells/digit with only case_id rebound for predicate; never a child rewrite",
                transfer_witness=dict(group="row", cells=target_cells, digit=target_digit),
                transfer_witness_score=target_score)


def verify_pairs(pairs):
    require(len(pairs) == 8, "exact eight source/transfer pairs required")
    require(pairs == [make_pair(pair["source"]["question"], pair["transfer"]["question"], index)
                      for index, pair in enumerate(pairs)], "pair construction/provenance differs")
    cases = [pair[stage] for pair in pairs for stage in ("source", "transfer")]
    for key in ("episode_id", "question_sha256", "candidate_sha256"):
        require(len({case[key] for case in cases}) == 16, f"source/transfer duplicate {key}; no replacements")


def effective_prior(prior_ids):
    supplied = []
    if prior_ids is not None:
        require(isinstance(prior_ids, dict) and set(prior_ids) == {"schema", "episode_ids"}
                and prior_ids["schema"] == "prior-source-ids-v1" and isinstance(prior_ids["episode_ids"], list)
                and all(isinstance(value, str) for value in prior_ids["episode_ids"]), "metadata-only prior inventory required")
        supplied = prior_ids["episode_ids"]
    return dict(schema="prior-source-ids-v1", episode_ids=sorted(set(supplied) | set(ADDED_PRIOR_IDS)))


def prepare_pairs(gym, prior_ids):
    require(gym.strict_verifier, "strict native gym required")
    excluded = set(effective_prior(prior_ids)["episode_ids"]) | set(base.TRAIN_IDS) | set(base.EVAL_IDS)
    for split in ("canary", "gate", "exam"):
        excluded.update(gym.benchmarks(split))
    require(not (set(SOURCE_IDS) | set(TRANSFER_IDS)) & excluded, "source/transfer ID collision; no replacements")
    require(all(gym.split_of(episode) == "train" for episode in SOURCE_IDS + TRANSFER_IDS), "training membership required")
    pairs = [make_pair(gym.question(source), gym.question(transfer), index)
             for index, (source, transfer) in enumerate(zip(SOURCE_IDS, TRANSFER_IDS))]
    verify_pairs(pairs)
    return pairs


def prior_content(preparations):
    records, receipts = {}, []
    for value in preparations:
        root = Path(value).resolve(strict=True)
        digest = base.receipts.verify_inventory(root)
        config = read(root / "config.json")
        require(config["schema"] in ("constraint-check-v1", "constraint-check-v2"), "prior v1/v2 preparation required")
        receipts.append(dict(path=str(root), inventory_sha256=digest, synthetic=config["synthetic"]))
        for case in read(root / "cases.json"):
            require(case["episode_id"] in ADDED_PRIOR_IDS, "unexpected prior source ID")
            row = dict(episode_id=case["episode_id"], question_sha256=sha(case["question"].encode()),
                       candidate_sha256=sha(base.formation.policy._encoded(case["candidate"])))
            require(all(row[key] == case[key] for key in row), "prior actual question/candidate hash mismatch")
            require(row["episode_id"] not in records or records[row["episode_id"]] == row, "conflicting prior content")
            records[row["episode_id"]] = row
    return dict(receipts=receipts, records=[records[key] for key in sorted(records)],
                scope="actual captured v1/v2 questions and candidates, metadata only; never included in learner prompts")


def check_prior_overlap(pairs, audit):
    records = audit["records"]
    require(len({row["episode_id"] for row in records}) == len(records), "duplicate prior inventory ID")
    for key in ("question_sha256", "candidate_sha256"):
        prior_hashes = {row[key] for row in records}
        current_hashes = {pair[stage][key] for pair in pairs for stage in ("source", "transfer")}
        require(not current_hashes & prior_hashes, f"prior actual {key} overlap; no replacements")
    return {row["episode_id"] for row in records} == set(ADDED_PRIOR_IDS)


def explanation(pair, mode):
    require(mode in MODES, "unknown arm")
    check = json.loads(pair["example_text"])["checks"][0]
    first, second = check["cells"]
    if mode == "format":
        return ("Read the example's JSON structure. Keep exactly the case_id, checks and lesson keys. "
                "Put one check object inside checks. Put two coordinate arrays inside cells, using unquoted integers. "
                "Use the group string and digit integer fields. Keep the lesson short; return JSON without a heading.")
    if check["group"] == "row":
        unit = f"row {first[0]}"
    elif check["group"] == "column":
        unit = f"column {first[1]}"
    else:
        top, left = (first[0] - 1) // 2 * 2 + 1, (first[1] - 1) // 2 * 2 + 1
        unit = f"the box covering rows {top}..{top + 1} and columns {left}..{left + 1}"
    return (f"Read the example against the candidate. Cells ({first[0]},{first[1]}) and ({second[0]},{second[1]}) "
            f"are distinct and both belong to {unit}. Read each displayed value: both are {check['digit']}. "
            "Equal values within that common unit establish this duplicate. On another board, recheck unit membership "
            "and both values rather than copying the old coordinates.")


def source_prompt(pair, mode):
    case = pair["source"]
    board = "\n".join(" ".join(map(str, row)) for row in case["candidate"])
    return (f"{base.TASK}\n\n{SOURCE_INSTRUCTION}\n\nShared correct source example:\n{pair['example_text']}"
            f"\n\nParent explanation:\n{explanation(pair, mode)}\n\ncase_id: {case['case_id']}\nCandidate:\n{board}")


def transfer_prompt(pair, note):
    require(isinstance(note, str), "raw child text required")
    prefix = f"{base.TASK}\n\n{TRANSFER_INSTRUCTION}\n\nBEGIN UNMODIFIED CHILD SOURCE NOTE\n"
    case = pair["transfer"]
    board = "\n".join(" ".join(map(str, row)) for row in case["candidate"])
    suffix = f"\nEND UNMODIFIED CHILD SOURCE NOTE\n\ncase_id: {case['case_id']}\nCandidate:\n{board}"
    prompt = prefix + note + suffix
    start = len(prefix.encode())
    return prompt, dict(start_byte=start, end_byte=start + len(note.encode()),
                        output_sha256=sha(note.encode()), bytes=len(note.encode()),
                        source_case_id=pair["source"]["case_id"], pair_id=pair["pair_id"],
                        scope="exact UTF8 raw child bytes; no filtering, parsing, stripping or rerendering")


def chat_envelope(tokenizer):
    marker = "ASTRA_LITERAL_DEMONSTRATION_PROMPT_BOUNDARY"
    rendered = tokenizer.apply_chat_template([dict(role="user", content=marker)], tokenize=False, add_generation_prompt=True)
    require(rendered.count(marker) == 1, "nontransparent chat template")
    prefix, suffix = rendered.split(marker)
    return dict(prefix=prefix, suffix=suffix)


def request_row(pair, mode, stage, tokenizer, envelope, note=None):
    if stage == "source":
        prompt, note_receipt = source_prompt(pair, mode), None
    else:
        require(stage == "transfer", "unknown stage")
        prompt, note_receipt = transfer_prompt(pair, note)
    rendered = tokenizer.apply_chat_template([dict(role="user", content=prompt)], tokenize=False, add_generation_prompt=True)
    require(rendered == envelope["prefix"] + prompt + envelope["suffix"], "chat template changed/reformatted prompt")
    tokens = len(tokenizer.encode(rendered, add_special_tokens=False))
    require(tokens + 128 <= 4096, "input/output headroom exceeded; no truncation")
    return dict(pair_id=pair["pair_id"], phase=stage, case_id=pair[stage]["case_id"], prompt=prompt,
                rendered_prompt=rendered, prompt_sha256=sha(prompt.encode()), rendered_sha256=sha(rendered.encode()),
                prompt_tokens=tokens, max_tokens=128, seed=7101, parent_presentations=int(stage == "source"),
                example_sha256=pair["example_sha256"] if stage == "source" else None, note=note_receipt)


def preflight(pairs, tokenizer):
    envelope = chat_envelope(tokenizer)
    sources = {mode: [request_row(pair, mode, "source", tokenizer, envelope) for pair in pairs] for mode in MODES}
    transfers = [request_row(pair, "process", "transfer", tokenizer, envelope, note="") for pair in pairs]
    require(all(row["prompt_tokens"] + 128 + 128 <= 4096 for row in transfers), "transfer baseline lacks note/output reserve")
    explanations = {mode: [dict(text=explanation(pair, mode), sha256=sha(explanation(pair, mode).encode()),
                         tokens=len(tokenizer.encode(explanation(pair, mode), add_special_tokens=False)))
                          for pair in pairs] for mode in MODES}
    return dict(envelope=envelope, source_requests=sources, transfer_empty_note_baselines=transfers,
                explanations=explanations,
                example_tokens=[len(tokenizer.encode(pair["example_text"], add_special_tokens=False)) for pair in pairs],
                explanation_tokens_equal=all(left["tokens"] == right["tokens"] for left, right in
                                             zip(explanations["process"], explanations["format"])),
                source_prompt_tokens_equal=all(left["prompt_tokens"] == right["prompt_tokens"] for left, right in
                                               zip(sources["process"], sources["format"])),
                transfer_token_policy="empty-note baseline plus reserve now; full actual note and tokenizer checked live before every call",
                matching="identical examples/caps/order/sampler; actual dose differences reported, no padding or readiness delay")


def prepare(out, model_path, expected_files, *, prior_ids=None, prior_preparations=(), gym=None, tokenizer=None):
    synthetic = gym is not None or tokenizer is not None
    model = Path(model_path).resolve(strict=True)
    require(base.formation.local_files(model) == expected_files, "local base pins mismatch")
    root = base.receipts.fresh_output(out, [model, Path(__file__).resolve().parents[1]])
    gym = gym if gym is not None else base.native.ReasoningGymGym(require_package=True, strict_verifier=True)
    tokenizer = tokenizer if tokenizer is not None else base._load_tokenizer(str(model))
    pairs = prepare_pairs(gym, prior_ids)
    audit = prior_content(prior_preparations)
    content_complete = check_prior_overlap(pairs, audit)
    require(synthetic or not any(row["synthetic"] for row in audit["receipts"]), "synthetic prior content forbidden for native preparation")
    check = preflight(pairs, tokenizer)
    check.update(status="PENDING_COLLISION_CHECK" if prior_ids is None else "PENDING_PRIOR_CONTENT_CHECK" if not content_complete
                 else "SYNTHETIC_CPU_ONLY" if synthetic else "READY",
                 prior_content_complete=content_complete,
                 overlap_scope="effective prior IDs; all16 current question/candidate hashes disjoint internally and from captured v1/v2 actual hashes; no global prior-question claim")
    config = dict(schema=SCHEMA, protocol=PROTOCOL, boundary=BOUNDARY, task=base.TASK,
                  model_path=str(model), expected_files=expected_files, sources=source_pins(synthetic), synthetic=synthetic,
                  source_ids=list(SOURCE_IDS), transfer_ids=list(TRANSFER_IDS), supplied_prior_ids=prior_ids,
                  effective_prior_ids=effective_prior(prior_ids), prior_content=audit)
    root.mkdir(parents=True)
    for name, value in (("config.json", config), ("pairs.json", pairs), ("preflight.json", check),
                        ("prior_ids.json", config["effective_prior_ids"]), ("runtime.json", base.runtime())):
        write(root / name, value)
    base.receipts.seal(root)
    return check


def validate_config(config, pairs, check):
    require(config["schema"] == SCHEMA and config["protocol"] == PROTOCOL and config["boundary"] == BOUNDARY
            and config["task"] == base.TASK and config["source_ids"] == list(SOURCE_IDS)
            and config["transfer_ids"] == list(TRANSFER_IDS), "prepared protocol mismatch")
    require(config["effective_prior_ids"] == effective_prior(config["supplied_prior_ids"]), "prior inventory differs")
    require(not (set(SOURCE_IDS) | set(TRANSFER_IDS)) & set(config["effective_prior_ids"]["episode_ids"]), "prior collision")
    require(config["supplied_prior_ids"] is not None and check["status"] ==
            ("SYNTHETIC_CPU_ONLY" if config["synthetic"] else "READY"), "preparation pending")
    verify_pairs(pairs)
    require(check_prior_overlap(pairs, config["prior_content"]) and check["prior_content_complete"], "prior content incomplete")
    require(config["synthetic"] or not any(row["synthetic"] for row in config["prior_content"]["receipts"]), "synthetic prior content")


def validate_preparation(preparation, allow_synthetic=False):
    prep = Path(preparation).resolve(strict=True)
    digest = base.receipts.verify_inventory(prep)
    config, pairs, check = read(prep / "config.json"), read(prep / "pairs.json"), read(prep / "preflight.json")
    validate_config(config, pairs, check)
    require(not config["synthetic"] or allow_synthetic, "synthetic preparation forbidden for native execution")
    require(config["sources"] == source_pins(config["synthetic"]), "source pins changed")
    require(base.formation.local_files(config["model_path"]) == config["expected_files"], "model pins changed")
    require(read(prep / "prior_ids.json") == config["effective_prior_ids"], "captured prior inventory differs")
    return prep, digest, config, pairs, check


def witness_key(check):
    return check["group"], check["digit"], tuple(sorted(map(tuple, check["cells"])))


def echo_analysis(text, pair, score):
    result = dict(exact_example_echo=text == pair["example_text"], example_verbatim_substring=pair["example_text"] in text,
                  same_example_check=False, valid_non_example_citations=0, independent_discovery_claim=False,
                  scope="byte echo and publicly valid check differences only; not cognitive independence or lesson truth")
    if not score["format_valid"]:
        return result
    record = json.loads(text, object_pairs_hook=base._unique_object)
    example = json.loads(pair["example_text"])["checks"][0]
    result["same_example_check"] = any(witness_key(check) == witness_key(example) for check in record["checks"])
    seen = set()
    for check in record["checks"]:
        key = witness_key(check)
        isolated = dict(case_id=record["case_id"], checks=[check], lesson=record["lesson"])
        valid = base.score_record(json.dumps(isolated), pair["source"])["grounded"]
        if valid and key != witness_key(example) and key not in seen:
            seen.add(key)
            result["valid_non_example_citations"] += 1
    return result


def summarized(records):
    result = {}
    for stage in ("source", "transfer"):
        selected = [record for record in records if record["phase"] == stage]
        require(len(selected) == 8, "eight records per stage required")
        result[stage] = dict(denominator=8, grounded=sum(row["score"]["grounded"] for row in selected),
                             format_count=sum(row["score"]["format_valid"] for row in selected),
                             invalid_citations=sum(row["score"]["invalid_citations"] for row in selected),
                             structured_clean=sum(row["score"]["whole_structured_record_clean"] for row in selected))
    result["source_echo"] = {key: sum(row["echo"][key] for row in records if row["phase"] == "source") for key in
                             ("exact_example_echo", "example_verbatim_substring", "same_example_check", "valid_non_example_citations")}
    return result


def run_arm(preparation, out, mode, *, backend_factory=base.formation.local_backend, allow_synthetic=False):
    with base.time_budget(900):
        return _run_arm(preparation, out, mode, backend_factory, allow_synthetic)


def _run_arm(preparation, out, mode, backend_factory, allow_synthetic):
    started = time.monotonic()
    require(mode in MODES and (allow_synthetic or backend_factory is base.formation.local_backend), "fresh native arm required")
    prep, digest, config, pairs, check = validate_preparation(preparation, allow_synthetic)
    root = base.receipts.fresh_output(out, [prep, config["model_path"], Path(__file__).resolve().parents[1]])
    root.mkdir(parents=True)
    write(root / "config.json", dict(config, mode=mode, preparation_sha256=digest))
    write(root / "runtime.json", dict(base.runtime(), generation_seed=7101, generation_seed_role=base.SEED_ROLE))
    try:
        records = []
        with backend_factory(config["model_path"]) as model:
            live = preflight(pairs, model.tok)
            require(all(live[key] == check[key] for key in live), "runtime tokenizer/preflight differs")
            capture = base.CaptureBackend(model, config["model_path"], root, "", synthetic=config["synthetic"])
            for index, pair in enumerate(pairs):
                note = None
                for stage in ("source", "transfer"):
                    require(time.monotonic() - started < 900, "arm time budget exhausted")
                    request = request_row(pair, mode, stage, model.tok, live["envelope"], note=note)
                    if stage == "source":
                        require(request == check["source_requests"][mode][index], "source request changed")
                    output = capture.generate_record(request)
                    score = base.score_record(output["text"], pair[stage])
                    record = dict(pair_id=pair["pair_id"], phase=stage, capture=output, score=score, note=request["note"],
                                  echo=echo_analysis(output["text"], pair, score) if stage == "source" else None)
                    records.append(record)
                    if stage == "source":
                        note = output["text"]
        require(capture.requests == 16 and time.monotonic() - started < 900, "incomplete or overtime arm")
        result = dict(status="COMPLETE", mode=mode, preparation_sha256=digest, generation_seed=7101,
                      synthetic=config["synthetic"], boundary=BOUNDARY, generation_calls=16, records=records,
                      counts=summarized(records), elapsed_seconds=time.monotonic() - started,
                      execution_backend="SYNTHETIC_CPU_FIXTURE" if config["synthetic"] else "LOCAL_GPU_BACKEND")
        write(root / "results.json", result)
        return result
    except BaseException as error:
        write(root / "failure.json", dict(status="FAILED", error=repr(error), raw_outputs="preserved when returned"))
        raise
    finally:
        base.receipts.seal(root)


def analyze_pair(pair_root, preparation):
    root, prep = Path(pair_root).resolve(strict=True), Path(preparation).resolve(strict=True)
    digest = base.receipts.verify_inventory(prep)
    config, pairs, check = read(prep / "config.json"), read(prep / "pairs.json"), read(prep / "preflight.json")
    validate_config(config, pairs, check)
    arms, pids = {}, []
    for mode in MODES:
        arm = root / mode
        base.receipts.verify_inventory(arm)
        require(not (arm / "failure.json").exists(), "failed arm cannot be scored complete")
        result, arm_config = read(arm / "results.json"), read(arm / "config.json")
        require(arm_config == dict(config, mode=mode, preparation_sha256=digest), "arm config/pair mismatch")
        require(result["status"] == "COMPLETE" and result["mode"] == mode and result["generation_calls"] == 16
                and result["generation_seed"] == 7101 and result["preparation_sha256"] == digest
                and result["synthetic"] == config["synthetic"] and result["boundary"] == BOUNDARY
                and len(result["records"]) == 16, "arm completion mismatch")
        runtime = read(arm / "runtime.json")
        require(runtime["generation_seed"] == 7101, "runtime sampling seed differs")
        pids.append(runtime["pid"])
        events = [json.loads(line) for line in (arm / "generations.jsonl").read_text().splitlines()]
        require([event["kind"] for event in events] == ["request", "raw_return", "output"] * 16, "exact sixteen calls per arm required")
        records, input_tokens, output_tokens = [], 0, 0
        for index, pair in enumerate(pairs):
            note = None
            for stage_index, stage in enumerate(("source", "transfer")):
                position = index * 2 + stage_index
                request, raw, output = events[position * 3:position * 3 + 3]
                require(all(event["request_index"] == position for event in (request, raw, output)), "request index/order mismatch")
                if stage == "source":
                    expected = check["source_requests"][mode][index]
                    require(expected["prompt"] == source_prompt(pair, mode) and all(request[key] == value for key, value in expected.items()),
                            "frozen source example/explanation differs")
                    expected_note = None
                else:
                    prompt, expected_note = transfer_prompt(pair, note)
                    require(request["prompt"] == prompt and request["note"] == expected_note and request["example_sha256"] is None,
                            "transfer child note altered or extra context introduced")
                    require(prompt.encode()[expected_note["start_byte"]:expected_note["end_byte"]] == note.encode(), "note bytes differ")
                require(request["phase"] == stage and request["pair_id"] == pair["pair_id"]
                        and request["case_id"] == pair[stage]["case_id"] and request["seed"] == 7101
                        and request["max_tokens"] == 128 and request["temperature"] == .7
                        and request["parent_presentations"] == int(stage == "source"), "request case/stage/settings mismatch")
                require(request["source_identity"] == base.model_backend.configured_generation_identity(config["model_path"], None), "model/adapter identity differs")
                require(request["prompt_sha256"] == sha(request["prompt"].encode()) and
                        request["rendered_prompt"] == check["envelope"]["prefix"] + request["prompt"] + check["envelope"]["suffix"]
                        and request["rendered_sha256"] == sha(request["rendered_prompt"].encode()), "rendered prompt mismatch")
                require(raw["synthetic"] == config["synthetic"], "raw synthetic/native mismatch")
                if config["synthetic"]:
                    require(raw["outputs"] == [output["text"]] and output["actual_output_tokens"] is None, "synthetic raw mismatch")
                else:
                    require(len(raw["requests"]) == 1 and len(raw["requests"][0]["outputs"]) == 1, "native cardinality")
                    native_request, native_output = raw["requests"][0], raw["requests"][0]["outputs"][0]
                    require(native_request["finished"] and native_request["prompt"] == request["rendered_prompt"]
                            and native_output["text"] == output["text"] and native_output["finish_reason"] == output["finish_reason"] == "stop"
                            and native_output["stop_reason"] == output["stop_reason"]
                            and len(native_output["token_ids"]) == output["actual_output_tokens"] <= 128
                            and len(native_request["prompt_token_ids"]) == request["prompt_tokens"] == output["actual_prompt_tokens"],
                            "native stop/text/token mismatch")
                    input_tokens += output["actual_prompt_tokens"]
                    output_tokens += output["actual_output_tokens"]
                require(request["prompt_tokens"] + 128 <= 4096 and output["output_sha256"] == sha(output["text"].encode())
                        and output["case_id"] == pair[stage]["case_id"] and output["generation_seed"] == 7101
                        and not output["input_truncated"] and not output["output_rewritten"], "output hash/headroom/case mismatch")
                score = base.score_record(output["text"], pair[stage])
                record = dict(pair_id=pair["pair_id"], phase=stage, capture={key: value for key, value in output.items() if key != "kind"},
                              score=score, note=expected_note, echo=echo_analysis(output["text"], pair, score) if stage == "source" else None)
                require(record == result["records"][position], "summary differs from raw output")
                records.append(record)
                if stage == "source":
                    note = output["text"]
        counts = summarized(records)
        require(counts == result["counts"], "summary count mismatch")
        arms[mode] = dict(counts=counts, actual_prompt_tokens=None if config["synthetic"] else input_tokens,
                          actual_output_tokens=None if config["synthetic"] else output_tokens,
                          source_example_presentations=8, parent_explanation_presentations=8, transfer_parent_presentations=0)
    require(config["synthetic"] or len(set(pids)) == 2, "two fresh native model workers required")
    return dict(status="COMPLETE", generation_calls=32, generation_seed=7101, synthetic=config["synthetic"],
                boundary=BOUNDARY, arms=arms,
                transfer_process_minus_format=arms["process"]["counts"]["transfer"]["grounded"] - arms["format"]["counts"]["transfer"]["grounded"],
                source_process_minus_format=arms["process"]["counts"]["source"]["grounded"] - arms["format"]["counts"]["source"]["grounded"],
                explanation_dose=check["explanations"], example_tokens=check["example_tokens"],
                explanation_tokens_equal=check["explanation_tokens_equal"], source_prompt_tokens_equal=check["source_prompt_tokens_equal"],
                verification_scope="captured inventories and byte-bound prompts/notes; remote model/source paths not rehashed by replay")


def execute_pair(preparation, out):
    with base.time_budget(1800):
        return _execute_pair(preparation, out)


def _execute_pair(preparation, out):
    started = time.monotonic()
    prep, digest, config, _, _ = validate_preparation(preparation)
    device = base.supervisor.selected_device()
    require(os.environ.get("V6_MODEL") == base.model_backend.MODEL == config["model_path"], "set pinned V6_MODEL before Python")
    root = base.receipts.fresh_output(out, [prep, config["model_path"], Path(__file__).resolve().parents[1]])
    root.mkdir(parents=True)
    write(root / "STARTED.json", dict(preparation=str(prep), preparation_sha256=digest, protocol=PROTOCOL, runtime=base.runtime()))
    try:
        for mode in MODES:
            remaining = 1800 - (time.monotonic() - started)
            require(remaining > 60, "pair deadline exhausted; retain cleanup reserve")
            command = [sys.executable, "-B", "-m", "organism_v6.constraint_demonstration_diagnostic", "--preparation", str(prep),
                       "--out", str(root / mode), "--condition", mode, "--allow-gpu"]
            base.supervisor.run_worker(command, log_path=root / f"{mode}.log", timeout=min(840, remaining - 60), device=device)
        result = analyze_pair(root, prep)
        require(time.monotonic() - started < 1800, "pair deadline exhausted")
        result["elapsed_seconds"] = time.monotonic() - started
        write(root / "COMPLETED.json", result)
        return result
    except BaseException as error:
        write(root / "FAILED.json", dict(error=repr(error), utc=base.receipts.utc()))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--model-path")
    parser.add_argument("--pins")
    parser.add_argument("--prior-source-ids")
    parser.add_argument("--prior-preparation", action="append", default=[], help="captured v1/v2 preparation root; repeat for both panels")
    parser.add_argument("--preparation")
    parser.add_argument("--condition", choices=MODES)
    parser.add_argument("--allow-gpu", action="store_true")
    parser.add_argument("--analyze")
    args = parser.parse_args(argv)
    if args.analyze:
        require(not any((args.allow_gpu, args.condition, args.model_path, args.pins, args.prior_source_ids, args.prior_preparation)), "CPU analysis only")
        prep = args.preparation or read(Path(args.analyze) / "STARTED.json")["preparation"]
        result = analyze_pair(args.analyze, prep)
        root = base.receipts.fresh_output(args.out, [args.analyze, prep, Path(__file__).resolve().parents[1]])
        root.mkdir(parents=True)
        write(root / "analysis.json", result)
        base.receipts.seal(root)
    elif args.preparation:
        require(args.allow_gpu and not any((args.model_path, args.pins, args.prior_source_ids, args.prior_preparation)), "explicit GPU opt-in required")
        if args.condition:
            base.supervisor.selected_device()
            result = run_arm(args.preparation, args.out, args.condition)
        else:
            result = execute_pair(args.preparation, args.out)
    else:
        require(args.model_path and args.pins and not args.allow_gpu and not args.condition, "CPU preparation needs model and pins")
        pins = read(args.pins)
        require(pins["model_path"] == str(Path(args.model_path).resolve(strict=True)), "pin model path mismatch")
        result = prepare(args.out, args.model_path, pins["files"], prior_ids=read(args.prior_source_ids) if args.prior_source_ids else None,
                         prior_preparations=args.prior_preparation)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
