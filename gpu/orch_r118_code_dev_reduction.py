"""Read-only, text-free reduction of explicitly selected CODE DEV captures."""

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import statistics


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def read_reference(path):
    payload = Path(path).read_bytes()
    return json.loads(payload), dict(path=str(path), sha256=hashlib.sha256(payload).hexdigest())


def repeated_fraction(sequence, width=4):
    grams = [tuple(sequence[index:index + width]) for index in range(len(sequence) - width + 1)]
    return (len(grams) - len(set(grams))) / len(grams) if grams else 0.0


def response_summary(response):
    raw, tokens = response["raw"], response["token_ids"]
    require(isinstance(raw, str) and isinstance(tokens, list)
            and all(type(token) is int and token >= 0 for token in tokens), "native_response_types")
    require(isinstance(response.get("messages"), list), "saved_messages_required")
    require(response.get("trainingAllowed") is False, "readout_training_disabled")
    require(response.get("input_truncated") is False, "uncropped_readout_required")
    require(type(response.get("effective_generation_cap")) is int, "saved_generation_cap")
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    last_expression_json = False
    if lines:
        try:
            value = json.loads(lines[-1])
            last_expression_json = (isinstance(value, dict) and set(value) == {"expression"}
                                    and isinstance(value["expression"], str))
        except ValueError:
            pass
    whole_expression_json, expression_syntax_valid = False, None
    try:
        value = json.loads(raw)
        whole_expression_json = (isinstance(value, dict) and set(value) == {"expression"}
                                 and isinstance(value["expression"], str))
        if whole_expression_json:
            try:
                ast.parse(value["expression"], mode="eval")
                expression_syntax_valid = True
            except (SyntaxError, ValueError, RecursionError):
                expression_syntax_valid = False
    except ValueError:
        pass
    return dict(tokens_including_eos=len(tokens), utf8_bytes=len(raw.encode()),
                nonempty_lines=len(lines), raw_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                token_ids_sha256=digest(tokens), messages_sha256=digest(response["messages"]),
                prompt_tokens=response.get("prompt_tokens"),
                effective_generation_cap=response["effective_generation_cap"],
                terminal=response.get("terminal"), truncated=response.get("truncated"),
                repeated_token_fourgram_fraction=repeated_fraction(tokens),
                repeated_word_fourgram_fraction=repeated_fraction(raw.split()),
                last_line_expression_json=last_expression_json,
                whole_response_expression_json=whole_expression_json,
                expression_python_syntax_valid=expression_syntax_valid,
                last_line_code_fence=bool(lines and lines[-1].startswith("```")),
                semantic_reasoning_quality="UNASSESSED")


def read_snapshot(root, name, *, checkpoint_sha256=None):
    root = Path(root).resolve(strict=True)
    matched = re.fullmatch(r"C([0-9]{3})_(ZERO|DEV)", name)
    require(matched is not None, "DEV_or_ZERO_only_no_FINAL")
    cycle, scope = int(matched[1]), matched[2]
    directory = root / "readouts" / name
    terminal, terminal_ref = read_reference(directory / "COMPLETE.json")
    require(terminal.get("fresh_process") is True and terminal.get("optimizer_steps") == 0
            and terminal.get("sleep_buffer_rows") == 0 and terminal.get("cycle") == cycle
            and terminal.get("scope") == scope, "fresh_nonlearning_DEV_receipt")
    outcomes, outcomes_ref = read_reference(directory / "DEV.json")
    require(outcomes.get("split") == "DEV" and outcomes.get("parent_visible") is False
            and outcomes.get("sleep_eligible") is False, "DEV_visibility")
    require(len(outcomes["outcomes"]) == 8, "fixed_eight_task_panel")
    rows, seen = [], set()
    for index, outcome in enumerate(outcomes["outcomes"]):
        identifier = f"R{cycle:03d}_{scope}_DEV_{index}"
        row, reference = read_reference(root / "reservations" / (identifier + ".json"))
        require(row.get("id") == identifier and row.get("cycle") == cycle
                and row.get("kind") == "NATIVE" and row.get("split") == "DEV"
                and row.get("phase") == "readout" and row.get("evaluation_origin") == "DEV",
                "exact_DEV_reservation")
        routes = row["routes"]
        require(all(routes.get(key) is False for key in ("sleep", "parent", "optimizer", "teacher_target")),
                "excluded_from_training_and_parenting")
        require(outcome["task_id"] not in seen and row["status"] == outcome["status"], "task_status_join")
        seen.add(outcome["task_id"])
        if checkpoint_sha256 is not None:
            require(row.get("shared_checkpoint_sha256") == checkpoint_sha256
                    and row.get("shared_generation") == 1, "exact_first_shared_checkpoint")
        else:
            require("shared_checkpoint_sha256" not in row, "pre_shared_reference_only")
        item = dict(task_id=outcome["task_id"], status=row["status"], source=reference,
                    finished_unix=row.get("finished_unix"), outcome=outcome.get("outcome"))
        if row["status"] == "COMPLETE":
            item["response"] = response_summary(row["response"])
        else:
            item["error_type"] = row.get("error_type")
        rows.append(item)
    binding_ref = None
    if checkpoint_sha256 is not None:
        binding, binding_ref = read_reference(root / "shared_readout_bindings" / f"C{cycle:03d}_DEV.json")
        require(binding["checkpoint"] == binding["state"]["checkpoint"]
                and binding["checkpoint"]["path_sha256"] == checkpoint_sha256
                and binding["state"]["generation"] == 1 and binding["cycle"] == cycle
                and binding["scope"] == "DEV", "canonical_shared_binding")
    completed = [row["response"] for row in rows if row["status"] == "COMPLETE"]
    return dict(root=str(root), name=name, terminal=terminal_ref, outcomes=outcomes_ref,
                checkpoint_sha256=checkpoint_sha256, binding=binding_ref, rows=rows,
                coverage=dict(Counter(row["status"] for row in rows)),
                median_tokens_including_eos=statistics.median(item["tokens_including_eos"] for item in completed)
                if completed else None,
                total_tokens_including_eos=sum(item["tokens_including_eos"] for item in completed),
                last_line_expression_json=sum(item["last_line_expression_json"] for item in completed),
                whole_response_expression_json=sum(item["whole_response_expression_json"] for item in completed),
                last_line_code_fence=sum(item["last_line_code_fence"] for item in completed),
                truncated=sum(item["truncated"] is True for item in completed))


def compare(before, after):
    require([row["task_id"] for row in before["rows"]] == [row["task_id"] for row in after["rows"]],
            "same_ordered_DEV_task_ids")
    pairs = []
    for old, new in zip(before["rows"], after["rows"]):
        result = dict(task_id=old["task_id"], paired_complete=False)
        if old["status"] == new["status"] == "COMPLETE":
            old_response, new_response = old["response"], new["response"]
            require(all(old_response[key] == new_response[key] for key in
                        ("messages_sha256", "effective_generation_cap", "prompt_tokens")), "matched_saved_input_and_cap")
            result.update(paired_complete=True,
                token_delta=new_response["tokens_including_eos"] - old_response["tokens_including_eos"],
                exact_output_changed=old_response["raw_sha256"] != new_response["raw_sha256"],
                exact_token_ids_changed=old_response["token_ids_sha256"] != new_response["token_ids_sha256"],
                before_last_line_expression_json=old_response["last_line_expression_json"],
                after_last_line_expression_json=new_response["last_line_expression_json"],
                before_recorded_correct=old["outcome"].get("correct"),
                after_recorded_correct=new["outcome"].get("correct"))
        pairs.append(result)
    return dict(expected_pairs=len(pairs), completed_pairs=sum(row["paired_complete"] for row in pairs),
                pairs=pairs, semantic_improvement="UNASSESSED",
                causal_parenting_effect="NOT_IDENTIFIED")


def reduce_branch(root, before, after, checkpoint_sha256):
    pre_shared = read_snapshot(root, before)
    first_shared = read_snapshot(root, after, checkpoint_sha256=checkpoint_sha256)
    return dict(pre_shared=pre_shared, first_shared=first_shared, comparison=compare(pre_shared, first_shared))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--checkpoint-sha256", required=True)
    args = parser.parse_args()
    result = reduce_branch(args.root, args.before, args.after, args.checkpoint_sha256)
    result.update(schema="R118_CODE_DEV_REDUCTION_V1", observed_utc=datetime.now(timezone.utc).isoformat(),
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  new_inference_calls=0, sealed_FINAL_read=False,
                  limitations=["Pre-shared snapshot is not an adapter-matched frozen control.",
                               "One pooled child: F3/A3 are not independent model samples.",
                               "Saved input/cap equality is not an independent decoder provenance audit.",
                               "Fourgram repetition is lexical, not a measure of useful thought."])
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
