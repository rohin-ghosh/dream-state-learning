"""Read-only fixed-budget validation; unknown outcomes are never scores of zero."""

import hashlib
import math
from pathlib import Path

import admission as rules
import probe_runtime as runtime


def outcomes(root):
    rows = []
    for path in sorted((root / "queue").glob("*.result.json")):
        result = runtime.read(path)
        request = runtime.read(path.with_name(path.name.replace(".result.json", ".request.json")))
        rules.require(result["request_sha256"] == rules.digest(request), "result_request_join")
        rules.require(request["raw_sha256"] == hashlib.sha256(request["raw"].encode()).hexdigest()
            == request["origin"]["text_sha256"], "raw_generation_join")
        for ordinal, row in enumerate(result["results"]):
            rows.append(dict(identity=request["identity"], outcome=row["result"], path=str(path.relative_to(root)), ordinal=ordinal))
    return rows


def scoring_shortfall(rows):
    return [row for row in rows if row["outcome"].get("pause_required") is True
        or row["outcome"].get("ok") is not True or type(row["outcome"].get("rank")) is not int
        or not isinstance(row["outcome"].get("raw_score"), (int, float))
        or not math.isfinite(row["outcome"].get("raw_score", float("nan")))
        or type(row["outcome"].get("accepted")) is not bool]


def completion(config, deadline, diagnose=None):
    root = Path(config["root"])
    output = root / "players" / config["condition"]
    final = runtime.read(output / "COMPLETE.json")
    loaded = runtime.read(output / "LOADED.json")
    judge_loaded = runtime.read(root / "JUDGE_LOADED.json")
    judge_exit = runtime.read(root / "JUDGE_EXIT.json")
    for role, actual_loaded in (("player", loaded), ("judge", judge_loaded)):
        start = runtime.read(runtime.runtime_directory(config) / (role + "_START_INTENT.json"))
        rules.require(start["pid"] == actual_loaded["pid"] and start["unix"] <= actual_loaded["unix"] <= deadline, "actual_load_process_join")
        assigned = config["role_devices"][role]
        runtime.validate_confinement(assigned["physical"], runtime.read(root / (role + "_DEVICE_PROOF.json")), assigned["uuid"], assigned["uuid"])
    rules.require(loaded["actual_visible_device"] == config["role_devices"]["player"]["uuid"]
        and judge_loaded["top_k"] == 50 and judge_loaded["reference_count"] == 64
        and judge_loaded["existing_games_modified"] is False and judge_exit["pid"] == judge_loaded["pid"], "unchanged_loaded_judge_and_device")
    expected_identity = dict(base_sha256=rules.BASE_SHA,
        adapter_state_sha256=config["source_identity"]["adapter_state_sha256"], all_parameters_frozen=True)
    rules.require(final["condition"] == config["condition"] and final["unchanged_identity"] == expected_identity,
        "frozen_final_identity")
    rules.require(all(loaded["identity"].get(key) == value for key, value in expected_identity.items())
        and loaded["identity"]["optimizer_created"] is False and loaded["parent_tokens"] == 0
        and loaded["snapshot_context_used"] is False and loaded["source_parent_text_loaded"] is False, "actual_frozen_parent_free_load")
    rules.require(loaded["unix"] <= final["unix"] <= deadline, "completed_within_original_deadline")
    scenes = {row["contest_id"] for row in runtime.read(root / "GAME_MANIFEST.json")["contests"]}
    expected_cells = {(scene, seed) for scene in scenes for seed in rules.BATTERY["seeds"]}
    rules.require(len(scenes) == 3 and len(final["cells"]) == 6
        and {(row["contest_id"], row["seed"]) for row in final["cells"]} == expected_cells, "six_unique_registered_cells")
    tokens = 0
    event_requests = set()
    canonical_results = {row["request_sha256"]: row for row in
        (runtime.read(path) for path in (root / "queue").glob("*.result.json"))}
    for cell in final["cells"]:
        directory = output / f'{cell["contest_id"]}_{cell["seed"]}'
        rules.require(runtime.read(directory / "RESULT.json") == cell, "cell_final_nested_copy")
        rules.require(cell["status"] == "COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET" and cell["generated_tokens"] == 1024
            and cell["budget"] == 1024 and cell["no_updates"] is True and cell["parent_tokens"] == 0
            and cell["learn_or_other_reply_tokens"] == 0, "exact_original_cell_budget")
        events = [runtime.read(path) for path in sorted(directory.glob("[0-9][0-9][0-9][0-9].json"))]
        rules.require([item["event"] for item in events] == cell["events"], "canonical_events_not_nested_replay")
        generated = 0
        for ordinal, item in enumerate(events):
            generation, event = item["generation"], item["event"]
            actual = generation["token_ids"]
            rules.require(generation["messages"] == item["request"] and all(type(token) is int and token >= 0 for token in actual)
                and 0 < len(actual) <= event["requested_max_new_tokens"] and len(actual) == event["actual_generated_tokens"], "actual_generated_tokens")
            origin = event["origin"]
            stage = "THINK" if ordinal % 2 == 0 else "ACT"
            rules.require(origin["stage"] == stage
                and event["requested_max_new_tokens"] == min(128 if stage == "THINK" else 256, 1024 - generated), "original_think_act_budget_steps")
            rules.require(origin["generated_tokens_before"] == generated
                and origin["generated_tokens_after"] == generated + len(actual)
                and origin["request_sha256"] == rules.digest(item["request"])
                and origin["response_sha256"] == rules.digest(generation), "generation_origin_join")
            request = dict(identity=dict(condition=config["condition"], seed=cell["seed"], contest_id=cell["contest_id"]),
                raw=generation["raw"], raw_sha256=hashlib.sha256(generation["raw"].encode()).hexdigest(), origin=origin)
            key = rules.digest(request)
            rules.require(key not in event_requests and event["score"]["request_sha256"] == key, "one_generation_one_request")
            rules.require(canonical_results.get(key) == event["score"], "event_score_matches_canonical_result")
            event_requests.add(key)
            generated += len(actual)
        rules.require(generated == 1024, "actual_per_cell_token_ids")
        tokens += generated
    requests = list((root / "queue").glob("*.request.json"))
    results = list((root / "queue").glob("*.result.json"))
    rules.require(len(requests) == len(results) == len(event_requests)
        and {rules.digest(runtime.read(path)) for path in requests} == event_requests, "all_canonical_requests_accounted")
    rules.require(tokens == final["actual_generated_tokens"] == 6144, "exact_6144_actual_tokens")
    rows = outcomes(root)
    shortfall = scoring_shortfall(rows)
    diagnostic = None
    verified_length_guard = False
    if shortfall:
        if diagnose is None:
            from shortfall import authenticate
            diagnose = authenticate
        try:
            diagnostic = diagnose(config, shortfall)
            verified_length_guard = diagnostic.get("all_verified") is True and diagnostic.get("model_loaded") is False
            verified_length_guard = verified_length_guard and diagnostic.get("scoring_called") is False
        except Exception as error:
            diagnostic = dict(all_verified=False, error_type=type(error).__name__, generic_fault_not_assumed_safe=True)
    return dict(status="COMPLETED_WITH_SCORING_SHORTFALL" if shortfall else "SUCCEEDED",
        pause_reason="UNCLASSIFIED_SCORING_FAULT_REVIEW" if shortfall and not verified_length_guard else None,
        complete_sha256=runtime.sha(output / "COMPLETE.json"), generated_tokens=tokens, cells=6,
        canonical_requests=len(requests), caption_outcomes=len(rows), unscored_or_pause_required=len(shortfall),
        unknown_is_zero=False, metrics_published_to_parents=False, clean_all_scored=not shortfall,
        diagnostic=diagnostic, verified_model_free_shortfall=verified_length_guard,
        later_independent_age_admissible_after_claims_clear=not shortfall or verified_length_guard)
