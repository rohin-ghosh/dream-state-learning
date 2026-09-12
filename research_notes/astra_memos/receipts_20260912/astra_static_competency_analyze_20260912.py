import argparse
import hashlib
import json
from pathlib import Path

from organism_v6 import batch_loop
from organism_v6 import parent_competency_diagnostic as diagnostic


def read(path):
    return json.loads(path.read_text())


def analyze(root, prep):
    prepared_hash = diagnostic.verify_inventory(prep)
    config = read(prep / "config.json")
    preflight = read(prep / "preflight.json")
    completed = read(root / "COMPLETED.json")
    started = read(root / "STARTED.json")
    assert started["preparation_sha256"] == prepared_hash
    assert preflight["status"] == "READY" and preflight["exact_token_match"] and preflight["context_fits"]
    assert config["protocol"] == diagnostic.PROTOCOL and config["packages"] == diagnostic.PACKAGES
    result = dict(label="EXPLORATORY_TEACHER_PRESENT_NO_WRITE", prepared_hash=prepared_hash,
                  started=started, completed_utc=completed["completed_utc"], arms={},
                  limitations=["One fixed generation seed and existing training questions, not held-out transfer.",
                               "Teacher remains present; no parameter update, internalization, P1 or H1/H2 claim.",
                               "Combined process package, not separate competency effects.",
                               "At-cap retokenized output length is a diagnostic, not a recorded finish reason.",
                               "Local hashes do not authenticate official model origin."])
    for mode in diagnostic.MODES:
        folder = root / mode
        inventory = diagnostic.verify_inventory(folder)
        report = read(folder / "results.json")
        assert completed["arms"][mode] == report
        assert report["status"] == "COMPLETE" and report["execution_backend"] == "LOCAL_GPU_BACKEND"
        assert report["mode"] == mode and report["denominator"] == report["presentations"] == 16
        assert report["package_tokens_per_presentation"] == 97 and report["cumulative_package_tokens"] == 1552
        cleanup = read(root / (mode + ".cleanup.json"))
        assert cleanup["owned_group_empty"] and cleanup["gpu_processes_absent"]
        assert cleanup["reservation_release_verified"] and cleanup["cleanup_error"] is None
        rows = []
        for index, (episode_id, expected) in enumerate(zip(config["episode_ids"], preflight["rows"][mode])):
            request = read(folder / f"request_{index:02d}.json")
            output = read(folder / f"output_{index:02d}.json")
            ledger = [json.loads(line) for line in (folder / f"episode_{index:02d}.jsonl").read_text().splitlines() if line.strip()]
            assert all(request[key] == value for key, value in expected.items())
            assert request["mode"] == mode and request["package_presentations"] == 1
            assert request["max_tokens"] == 400 and request["temperature"] == 0.7
            assert request["prompt"].count(config["packages"][mode]) == 1
            assert request["seed"] == batch_loop._seed_for(episode_id, 1, 7101)
            assert output["output_sha256"] == hashlib.sha256(output["text"].encode()).hexdigest()
            assert output["episode_id"] == episode_id and output["request_index"] == index
            assert output["output_tokens"] <= 400
            expected_row = dict(episode_id=episode_id, request_index=index, **diagnostic.action_summary(ledger))
            assert report["episodes"][index] == expected_row
            parsed_actions = [match.group(2).strip() for match in batch_loop._MARK.finditer(output["text"])
                              if match.group(1) == "ACT"]
            assert parsed_actions == [row["action"] for row in ledger if row["kind"] == "act"]
            rows.append(dict(expected_row, output_tokens=output["output_tokens"],
                             output_sha256=output["output_sha256"], prompt_sha256=request["prompt_sha256"]))
        assert len(report["episodes"]) == 16 and report["first_action_solves"] == sum(row["first_action_solved"] for row in rows)
        result["arms"][mode] = dict(artifact_hash=inventory, cleanup=cleanup, episodes=rows,
            solves=sum(row["first_action_solved"] for row in rows),
            available=sum(row["first_action_available"] for row in rows),
            format_valid=sum(row["first_action_format_valid"] for row in rows),
            score_mean=sum(row["first_action_score"] for row in rows) / 16,
            raw_native_first_score_mean=sum(row["first_action"]["score"] if row["first_action"] else 0 for row in rows) / 16,
            total_actions=sum(row["n_actions"] for row in rows),
            output_tokens=sum(row["output_tokens"] for row in rows),
            outputs_at_retokenized_cap=sum(row["output_tokens"] == 400 for row in rows))
    result["process_minus_sham"] = {key: result["arms"]["process"][key] - result["arms"]["sham"][key]
                                   for key in ("solves", "available", "format_valid", "score_mean")}
    result["valid"] = True
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("preparation", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = analyze(args.root, args.preparation)
    with args.output.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"valid": result["valid"], "process_minus_sham": result["process_minus_sham"]}))
