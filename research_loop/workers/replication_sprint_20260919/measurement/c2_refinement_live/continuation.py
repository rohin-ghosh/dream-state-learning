"""Finite read-only observer; explicit Main approval is required for run."""

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SCOPE = "C2_READ_ONLY_FIRST_SIX_ACT_CONTINUATION"
HELPER_SHA = "8ca38854496d5a4e571cc50cdff76c24f617af8af5250d3578bb1e33ea0fe68d"
LIMIT = 1_900_000
OVERHEAD = 65_536
RESERVATION = 3 * LIMIT + OVERHEAD
CALL_MARGIN = 300
MAX_SECONDS = 7200
MAX_BYTES = 25_000_000
INTERVAL = 90


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    require(not path.is_symlink() and path.is_file() and path.stat().st_size < LIMIT, "bounded_regular_input")
    raw = path.read_bytes()
    require(len(raw) < LIMIT, "bounded_input")
    return raw


def reference(path):
    raw = read(path)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(raw), "bytes": len(raw)}


def verify_reference(proof):
    path = ROOT / proof["path"]
    require(path.resolve().is_relative_to(ROOT) and ".." not in Path(proof["path"]).parts, "repo_reference_only")
    raw = read(path)
    require(sha(raw) == proof["sha256"] and len(raw) == proof["bytes"], "pinned_file_changed:" + proof["path"])
    return path


def helper():
    path = HERE / "observe.py"
    require(sha(read(path)) == HELPER_SHA, "frozen_observe_changed")
    spec = importlib.util.spec_from_file_location("fixed_c2_observe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def select_existing(module, captures, binding):
    attempts = binding["attempts"]
    require(attempts[0]["result"]["status"] == "PUBLISHED", "first_policy_publication_required")
    turns = [{"attempt": row["attempt"], "publication": row["result"]["inbox_publication"],
              "result_receipt": row["files"]["RESULT.json"], "message": row["result"]["response"]["message"]}
             for row in attempts if row.get("result", {}).get("status") == "PUBLISHED"]
    return module.select(module.merged_evidence(captures), attempts[0]["result"]["inbox_publication"], turns)


def advance(previous, capture, identity, journal):
    require(capture["identity"] == identity, "source_identity_changed")
    evidence = capture["evidence"]
    require(evidence["journal_id"] == journal, "journal_changed")
    require(capture["after"] == previous["index"], "exact_cursor_required")
    for key in ("remote_writes", "signals", "model_calls", "readout_or_private_score_files_read"):
        require(evidence[key] == 0, "read_only_TRAIN_projection_required")
    current = previous
    for row in evidence["continuity"]:
        require(row["index"] == current["index"] + 1 and row["previous_sha256"] == current["sha256"], "contiguous_cursor_chain_required")
        require(row["journal_id"] == journal, "continuity_journal_changed")
        current = row
    require(evidence["through"] == (current if evidence["continuity"] else None), "through_binding")
    head = evidence["head"]
    require(head["index"] >= current["index"], "head_regression")
    if head["index"] == current["index"]:
        require(head["sha256"] == current["sha256"], "head_hash_changed")
    return current


def validate(review_path, expected):
    raw = read(review_path)
    require(sha(raw) == expected, "exact_review_hash_required")
    review = json.loads(raw)
    require(review["scope"] == SCOPE and review["status"] == "READY_NOT_AUTHORIZATION", "review_scope")
    require(review["limits"] == {"seconds": MAX_SECONDS, "new_receipt_bytes": MAX_BYTES, "interval_seconds": INTERVAL, "ACTs": 6}, "fixed_limits")
    for proof in review["pins"] + review["captures"] + [review["binding"], review["selection"]]:
        verify_reference(proof)
    require(review["monitor_sha256"] == sha(read(Path(__file__))), "reviewed_monitor_hash")
    module = helper()
    paths = [verify_reference(proof) for proof in review["captures"]]
    require(paths == sorted(HERE.glob("CAPTURE_[0-9][0-9].json")), "all_existing_captures_must_be_bound")
    evidence = module.merged_evidence(paths)
    require(evidence["continuity"][-1] == review["cursor"], "reviewed_cursor_mismatch")
    first = json.loads(read(paths[0]))
    require(first["identity"] == review["identity"], "reviewed_identity_mismatch")
    selection = select_existing(module, paths, json.loads(read(verify_reference(review["binding"]))))
    require(selection["first_inbox"]["index"] == 15859 and len(selection["opportunities"]) == 1, "reviewed_first_opportunity")
    saved_selection = json.loads(read(verify_reference(review["selection"])))
    require(selection["opportunities"] == saved_selection["opportunities"], "reviewed_selection_mismatch")
    return review, module


def approve(path, expected, review_sha, monitor_sha):
    raw = read(path)
    require(sha(raw) == expected, "exact_Main_approval_hash_required")
    approval = json.loads(raw)
    require(approval.get("status") == "APPROVED_TO_RUN" and approval.get("approved_by") == "Main"
            and approval.get("scope") == SCOPE and approval.get("review_sha256") == review_sha
            and approval.get("monitor_sha256") == monitor_sha, "Main_must_bind_exact_reviewed_monitor")


def sync_directory(directory):
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def snapshot(directory, name, value):
    require(Path(name).name == name, "local_snapshot_name")
    raw = encode(value)
    require(len(raw) < LIMIT, "receipt_under_2MB")
    path = directory / name
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    sync_directory(directory)
    return reference(path)


def point(directory, proof):
    temporary = directory / ("LATEST." + sha(encode(proof))[:16] + ".next")
    snapshot(directory, temporary.name, {"snapshot": proof})
    os.replace(temporary, directory / "LATEST.json")
    sync_directory(directory)


@contextmanager
def exclusive(path):
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(descriptor)


def no_direct_collector():
    for process in Path("/proc").iterdir():
        if not process.name.isdigit() or int(process.name) == os.getpid():
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            argv = process.joinpath("cmdline").read_bytes().decode().rstrip("\0").split("\0")
            for position, argument in enumerate(argv[:-1]):
                if Path(argument).name == "observe.py" and argv[position + 1] in ("capture", "select"):
                    candidate = Path(argument)
                    if not candidate.is_absolute():
                        candidate = process.joinpath("cwd").resolve() / candidate
                    require(candidate.resolve() != HERE / "observe.py", "direct_collector_already_active")
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue


def initial(review, review_sha, now, monotonic_now):
    return {"review_sha256": review_sha, "started_unix": now, "deadline_unix": now + MAX_SECONDS,
            "deadline_monotonic": monotonic_now + MAX_SECONDS,
            "local_boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
            "charged_bytes": OVERHEAD, "sequence": 0, "status": "RUNNING", "cursor": review["cursor"],
            "captures": review["captures"], "eligible_ACT_count": 1, "selection": review["selection"],
            "semantic_grading": "MANUAL_ONLY_NEW_OUTCOMES_UNKNOWN", "previous_state": None}


def restore(directory, review, review_sha, now, monotonic_now):
    if (directory / "STOP.json").exists():
        stopped = json.loads(read(directory / "STOP.json"))
        require(stopped["review_sha256"] == review_sha, "same_review_on_resume")
        return stopped, None
    start = directory / "START.json"
    if not start.exists():
        require(not any(directory.iterdir()), "unknown_existing_run_files")
        proof = snapshot(directory, start.name, initial(review, review_sha, now, monotonic_now))
    else:
        proof = reference(start)
    state = json.loads(read(start))
    require(state["review_sha256"] == review_sha, "same_review_on_resume")
    require(state["local_boot_id"] == Path("/proc/sys/kernel/random/boot_id").read_text().strip(), "local_reboot_requires_review")
    for path in sorted(directory.glob("STATE_*.json")):
        candidate = json.loads(read(path))
        require(candidate["sequence"] == state["sequence"] + 1 and candidate["previous_state"] == proof, "durable_state_chain")
        intent = json.loads(read(directory / f'INTENT_{candidate["sequence"]:04d}.json'))
        require(intent["previous_state"] == proof and intent["cursor"] == state["cursor"], "durable_intent_chain")
        for item in candidate["files"]:
            verify_reference(item)
        require(candidate["charged_bytes"] == state["charged_bytes"] + sum(item["bytes"] for item in candidate["files"]) + OVERHEAD, "durable_byte_accounting")
        require(candidate["deadline_unix"] == state["deadline_unix"] and candidate["deadline_monotonic"] == state["deadline_monotonic"], "deadline_cannot_reset")
        require(candidate["captures"] == state["captures"] + [candidate["files"][1]], "all_captures_preserved")
        projected = json.loads(read(verify_reference(candidate["files"][1])))
        require(candidate["cursor"] == advance(state["cursor"], projected, review["identity"], review["cursor"]["journal_id"]), "resumed_cursor_binding")
        state, proof = candidate, reference(path)
    require(len(list(directory.glob("INTENT_*.json"))) == state["sequence"], "incomplete_slot_preserved_manual_reconciliation_required")
    for item in state["captures"]:
        verify_reference(item)
    return state, proof


def stop(directory, state, reason, error=None):
    result = dict(state, status=reason, observer_stopped=True, native_or_service_signals=0,
                  error=None if error is None else {"type": type(error).__name__, "message": str(error)[:1000]},
                  semantic_grading="MANUAL_ONLY_NEW_OUTCOMES_UNKNOWN")
    proof = snapshot(directory, "STOP.json", result)
    point(directory, proof)
    return result


def run_loop(directory, review, review_sha, backend, now=time.time, monotonic=time.monotonic, sleep=time.sleep, guard=no_direct_collector):
    directory.mkdir(mode=0o700, exist_ok=True)
    state = initial(review, review_sha, now(), monotonic())
    try:
        state, previous = restore(directory, review, review_sha, now(), monotonic())
    except Exception as error:
        state["charged_bytes"] = min(MAX_BYTES, OVERHEAD + len(list(directory.glob("INTENT_*.json"))) * RESERVATION)
        state["preserved_files"] = sorted(path.name for path in directory.iterdir())
        return stop(directory, state, "PARTIAL_INCOMPLETE_RESUME", error)
    if state["status"] != "RUNNING":
        return state
    monotonic_end = state["deadline_monotonic"]
    if state["sequence"]:
        try:
            restored_binding = json.loads(read(verify_reference(state["files"][0])))
            verified_selection = select_existing(backend, [verify_reference(item) for item in state["captures"]], restored_binding)
            saved_selection = json.loads(read(verify_reference(state["selection"])))
            require(verified_selection["opportunities"] == saved_selection["opportunities"], "resumed_selection_binding")
        except Exception as error:
            return stop(directory, state, "PARTIAL_RESUME_VALIDATION_FAILED", error)
        delay = state["next_observation_not_before_unix"] - now()
        sleep(max(0, min(delay, state["deadline_unix"] - now() - CALL_MARGIN, monotonic_end - monotonic() - CALL_MARGIN)))
    while True:
        if state["eligible_ACT_count"] >= 6:
            return stop(directory, state, "SIX_HASH_LINKED_ACTS_MANUAL_REVIEW_REQUIRED")
        remaining = min(state["deadline_unix"] - now(), monotonic_end - monotonic())
        if remaining <= CALL_MARGIN:
            return stop(directory, state, "PARTIAL_TIME_LIMIT")
        if state["charged_bytes"] + RESERVATION > MAX_BYTES:
            return stop(directory, state, "PARTIAL_BYTE_LIMIT")
        sequence = state["sequence"] + 1
        charge_before = state["charged_bytes"]
        files = []
        capture = None
        try:
            guard()
            for item in review["pins"]:
                verify_reference(item)
            snapshot(directory, f"INTENT_{sequence:04d}.json", {"sequence": sequence, "cursor": state["cursor"],
                     "previous_state": previous, "reserved_bytes": RESERVATION, "started_unix": now()})
            binding = backend.binding()
            files.append(snapshot(directory, f"BINDING_{sequence:04d}.json", binding))
            require(min(state["deadline_unix"] - now(), monotonic_end - monotonic()) > CALL_MARGIN, "time_budget_before_capture")
            capture = backend.capture(state["cursor"]["index"], 12)
            files.append(snapshot(directory, f"CAPTURE_{sequence:04d}.json", capture))
            cursor = advance(state["cursor"], capture, review["identity"], review["cursor"]["journal_id"])
            captures = state["captures"] + [files[-1]]
            selection = select_existing(backend, [verify_reference(item) for item in captures], binding)
            files.append(snapshot(directory, f"SELECTION_{sequence:04d}.json", selection))
            count = len(selection["opportunities"])
            require(state["eligible_ACT_count"] <= count <= 6, "no_selected_ACT_disappears")
            next_state = dict(state, sequence=sequence, cursor=cursor, captures=captures, files=files,
                              previous_state=previous, selection=files[-1], eligible_ACT_count=count,
                              charged_bytes=state["charged_bytes"] + sum(item["bytes"] for item in files) + OVERHEAD,
                              observed_unix=now(), next_observation_not_before_unix=now() + INTERVAL)
            require(len(encode(next_state)) < OVERHEAD // 2, "bounded_checkpoint_metadata")
            previous = snapshot(directory, f"STATE_{sequence:04d}.json", next_state)
            state = next_state
            point(directory, previous)
        except Exception as error:
            state = dict(state, charged_bytes=charge_before + RESERVATION,
                         failed_slot={"sequence": sequence, "files": files, "outcome": "UNKNOWN_NOT_REPLACED",
                                      "ACT_stage_receipts": [] if capture is None else [row for row in capture["evidence"]["records"] if row["kind"] == "R184_STAGE" and row.get("stage") == "ACT"]})
            return stop(directory, state, "PARTIAL_FAILED_SLOT", error)
        if state["eligible_ACT_count"] < 6:
            remaining = min(state["deadline_unix"] - now(), monotonic_end - monotonic())
            sleep(max(0, min(INTERVAL, remaining - CALL_MARGIN)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("validate", "run"))
    parser.add_argument("--review", default="CONTINUATION_REVIEW.json")
    parser.add_argument("--review-sha256", required=True)
    parser.add_argument("--approval")
    parser.add_argument("--approval-sha256")
    arguments = parser.parse_args()
    require(Path(arguments.review).name == arguments.review, "sidecar_review_only")
    review, module = validate(HERE / arguments.review, arguments.review_sha256)
    if arguments.mode == "validate":
        print(json.dumps({"status": "READY_NOT_LAUNCHED", "eligible_ACT_count": 1, "scope": SCOPE, "limits": review["limits"]}))
        return
    require(arguments.approval and arguments.approval_sha256 and Path(arguments.approval).name == arguments.approval, "Main_approval_required_before_launch")
    approve(HERE / arguments.approval, arguments.approval_sha256, arguments.review_sha256, review["monitor_sha256"])
    with exclusive(HERE / "CONTINUATION.lock"):
        no_direct_collector()
        result = run_loop(HERE / "continuation_run", review, arguments.review_sha256, module)
    print(json.dumps({"status": result["status"], "eligible_ACT_count": result["eligible_ACT_count"], "cursor": result["cursor"], "charged_bytes": result["charged_bytes"]}))


if __name__ == "__main__":
    main()
