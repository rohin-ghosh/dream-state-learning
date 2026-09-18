"""Read-only, bounded post-handoff context custody; never output child text."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


REMOTE = Path("/localhome/local-rohing/orch_r179_node1_20260917_attempt2")
HERE = Path(__file__).resolve().parent if "__file__" in globals() else REMOTE / "operator"
MAX_RECORD_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
MAX_RECORDS = 512


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def load(path, budget):
    size = path.stat().st_size
    require(size <= MAX_RECORD_BYTES and size <= budget[0], "precharged_journal_observation_budget")
    budget[0] -= size
    with path.open("rb") as stream:
        raw = stream.read(size + 1)
    require(len(raw) == size, "stable_observed_record_size")
    return json.loads(raw)


def retention_chain(records):
    retained = None
    pending_history = None
    complete_history = None
    complete = None
    for record in records:
        document = record["document"]
        if record["kind"] == "CONTEXT_RETAINED":
            require(document["history_sha256_before"] == document["history_sha256_after"]
                    and document["visible_prompt_tokens"] < document["threshold_tokens"]
                    and document["action"] == "RETAIN_CONTEXT_ACROSS_SLEEP", "actual_retention_decision")
            retained = record
            pending_history = None
            complete_history = None
            complete = None
        elif retained and record["kind"] in ("COMPACTION", "EVICTION"):
            retained = None
        elif retained and record["kind"] == "SLEEP_REQUEST":
            envelope = document["resume_state"]
            require(envelope["sha256"] == digest(envelope["state"]), "presleep_envelope_integrity")
            pending_history = envelope["state"]["history"]
            require(pending_history["state_sha256"] == retained["document"]["history_sha256_after"],
                    "retention_decision_saved_history_binding")
        elif retained and pending_history and record["kind"] == "SLEEP_COMPLETE":
            envelope = document["resume_state"]
            require(envelope["sha256"] == digest(envelope["state"]), "postsleep_envelope_integrity")
            state = envelope["state"]
            require(document["status"] == "COMPLETE" and document["cycle"] == retained["document"]["cycle"]
                    and state["pending"] is None and state["sleep_frontier"] == len(state["rows"]),
                    "actual_completed_saved_sleep")
            require(state["history"] == pending_history, "full_raw_history_and_active_view_equal_across_sleep")
            complete_history = state["history"]
            complete = record
        elif complete_history and record["kind"] == "REQUEST":
            envelope = document["resume_state"]
            require(envelope["sha256"] == digest(envelope["state"]), "post_sleep_request_state_integrity")
            history = envelope["state"]["history"]
            for name in ("system_prompt", "birth_prompt", "operations"):
                require(history[name] == complete_history[name], "unchanged_post_sleep_visible_view")
            require(history["events"][:len(complete_history["events"])] == complete_history["events"],
                    "all_prior_history_events_in_post_sleep_request")
            require(document["history_sha256"] == digest(history), "actual_request_history_binding")
            return retained, complete, record
    return None


def remote(physical):
    require(physical in range(2, 7), "five_handoff_learners_only")
    output = REMOTE / "lanes" / ("lane" + str(physical))
    budget = [MAX_TOTAL_BYTES]
    readmission = output / "readmission1"
    readmitted = (readmission / "LOADED_RECEIPT.json").exists()
    if not (output / "LOADED_RECEIPT.json").exists() and not readmitted:
        return dict(physical=physical, status="NO_LOADED_RECEIPT_YET")
    staged = load(output / "STAGED.json", budget)
    boundary = load(output / "BOUNDARY.json", budget)["saved"]
    original = load(Path(boundary["record_path"]), budget)
    root = Path(staged["old_plan"]["root"]) / "stream/records"
    paths = sorted(path for path in root.iterdir() if re.fullmatch(r"[0-9]{20}\.json", path.name)
                   and int(path.stem) > original["index"])
    require(len(paths) <= MAX_RECORDS, "bounded_post_handoff_record_window")
    records = []
    previous = original
    for path in paths:
        record = load(path, budget)
        require(record["index"] == previous["index"] + 1
                and record["previous_sha256"] == previous["sha256"]
                and record["journal_id"] == previous["journal_id"]
                and record["sha256"] == digest({key: value for key, value in record.items() if key != "sha256"}),
                "exact_post_handoff_journal_chain")
        records.append(record)
        previous = record
    chain = retention_chain(records)
    if chain is None:
        return dict(physical=physical, status="WAITING_RETAINED_SLEEP_AND_POST_SLEEP_REQUEST",
                    observed_kinds=sorted({record["kind"] for record in records}),
                    last_index=previous["index"], bytes_read=MAX_TOTAL_BYTES - budget[0])
    retained, complete, request = chain
    source = Path(staged["source_root"])
    config = load(readmission / "GUARD.json" if readmitted else Path(staged["new_config"]), budget)
    relative = "organism_v6/orch_r124_train_history.py"
    require(hashlib.sha256((source / relative).read_bytes()).hexdigest() == config["source_pins"][relative],
            "actual_history_renderer_source")
    sys.path.insert(0, str(source))
    from organism_v6.orch_r124_train_history import TrainHistory
    require(Path(sys.modules[TrainHistory.__module__].__file__).resolve() == source / relative,
            "actual_source_renderer_import")
    document = request["document"]
    state = document["resume_state"]["state"]
    history = TrainHistory.restore(state["history"])
    rendered = history.render(lambda messages: 0, state["context_limit"], presentation=state.get("presentation"))
    require(list(rendered.messages) == document["messages"], "recorded_post_sleep_prompt_equals_exact_history_render")
    require(history.checkpoint() == state["history"], "observer_did_not_mutate_history")
    committed = next((record for record in records if record["index"] > request["index"]
                      and record["kind"] == "COMMITTED"), None)
    return dict(physical=physical, status="POST_SLEEP_PROMPT_HISTORY_CUSTODY_VERIFIED",
        retained_record_sha256=retained["sha256"], sleep_complete_sha256=complete["sha256"],
        post_sleep_request_sha256=request["sha256"], cycle=complete["document"]["cycle"],
        post_sleep_messages_sha256=digest(document["messages"]),
        completed_history_sha256=complete["document"]["resume_state"]["state"]["history"]["state_sha256"],
        post_sleep_commit_sha256=committed["sha256"] if committed else None,
        full_raw_and_visible_history_preserved=True, child_text_exported=False, sealed_content_reads=0,
        bytes_read=MAX_TOTAL_BYTES - budget[0], observed_unix=time.time())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--physical", type=int, required=True)
    parser.add_argument("--remote", action="store_true")
    arguments = parser.parse_args()
    if arguments.remote:
        print(json.dumps(remote(arguments.physical), sort_keys=True))
        return
    command = shlex.join(["env", "CUDA_VISIBLE_DEVICES=", "PYTHONDONTWRITEBYTECODE=1",
        "/localhome/local-rohing/v2/venv/bin/python", "-B", "-c", Path(__file__).read_text(),
        "--remote", "--physical", str(arguments.physical)])
    result = subprocess.run(["bash", "gpu/a100_ssh.sh", command], cwd=HERE.parents[3],
                            text=True, capture_output=True, timeout=90)
    path = HERE / ("CONTEXT_CUSTODY_LANE" + str(arguments.physical) + "_" + str(time.time_ns()) + ".json")
    with path.open("x") as stream:
        json.dump(dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr), stream, indent=2)
    print(json.dumps(dict(path=str(path), returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)))


if __name__ == "__main__":
    main()
