import datetime
import hashlib
import json
import pathlib
import re
import statistics


def hashed(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


result = {"observed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "scope": "existing TRAIN open turns and DEV captures only; no FINAL reads",
          "new_model_calls": 0, "branches": {}}
for branch, physical in (("F1", 0), ("A1", 4)):
    root = pathlib.Path(f"/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_{physical}_attempt1")
    branch_result = {"root": str(root), "train_open": [], "parent_free_open": [], "dev": []}
    for pattern, key in (("cycle_*/OPEN_TRAIN_*.json", "train_open"),
                         ("open_readouts/readout_*/OPEN.json", "parent_free_open")):
        for path in sorted(root.glob(pattern)):
            data = json.loads(path.read_text())
            calls = data.get("environment_calls", [])
            branch_result[key].append({"path": str(path.relative_to(root)), "sha256": hashed(path),
                "mtime_utc": datetime.datetime.fromtimestamp(path.stat().st_mtime, datetime.timezone.utc).isoformat(),
                "captures": len(data.get("captures", [])), "environment_calls": len(calls),
                "verified_environment_responses": sum(call.get("actual_environment_call") is True
                    and hashlib.sha256(json.dumps(call.get("response", ""), sort_keys=True,
                        separators=(",", ":")).encode()).hexdigest() == call.get("response_sha256")
                    for call in calls), "observed_stop": data.get("observed_stop"),
                "parent_free": data.get("parent_free"), "training_buffer": data.get("training_buffer")})
    for path in sorted(root.glob("readout_*/HELD.json")):
        data = json.loads(path.read_text())
        responses = [response for trajectory in data["cached_responses"] for response in trajectory]
        native = sorted(path.parent.glob("CALL_*.json"))
        matched = 0
        raw_lengths = []
        completed = []
        for capture in native:
            saved = json.loads(capture.read_text())
            if saved.get("status") == "COMPLETE" and isinstance(saved.get("response"), dict):
                completed.append(saved["response"])
        for response in responses:
            matched += any(response == item for item in completed)
            raw_lengths.append(len(response.get("raw", "")))
        branch_result["dev"].append({"path": str(path.relative_to(root)), "sha256": hashed(path),
            "tasks": len(data["cached_responses"]), "responses": len(responses), "matched_native_captures": matched,
            "all_have_raw_and_token_ids": all(isinstance(response.get("raw"), str)
                and isinstance(response.get("token_ids"), list) for response in responses),
            "command_only_responses": sum(bool(re.fullmatch(r"(?:READ EVENT|ROUTE)\s+\S+", response.get("raw", "").strip()))
                for response in responses),
            "response_tokens_median_including_eos": statistics.median(len(response["token_ids"]) for response in responses) if responses else None,
            "task_tokens_median_including_eos": statistics.median(sum(len(response["token_ids"]) for response in trajectory)
                for trajectory in data["cached_responses"]),
            "semantic_labels": "not inferred from length or command regex"})
    result["branches"][branch] = branch_result
print(json.dumps(result, indent=2, sort_keys=True))
