"""Read-only parent-prefix and actual RESPONSE joins for two proposed slots."""

import hashlib
import json
from pathlib import Path
import re
import socket
import time


CASES = {
    "teach_replay": {
        "physical": 2,
        "complete_index": 6646,
        "complete_sha256": "9a8ffe529d7f208a4534d66eb84d927342aa917d905218672490ec4a59c7f661",
        "segments": {14: "early5", 182: "previous5", 197: "latest5"},
    },
    "classroom_support": {
        "physical": 7,
        "complete_index": 4849,
        "complete_sha256": "580502e0b0005b4344001f69881629a910eefdeaa0ea1538c9f086533c44326a",
        "segments": {9: "early5", 125: "previous5", 135: "latest5"},
    },
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def inspect(label, case):
    root = Path("/localhome/local-rohing/orch_r136_a100_" + label + "_20260916_attempt1/run1")
    directory = root / "stream/records"
    saved_path = directory / ("%020d.json" % case["complete_index"])
    assert saved_path.is_file() and not saved_path.is_symlink() and saved_path.stat().st_size < 32 * 1024 * 1024
    raw = saved_path.read_bytes()
    saved = json.loads(raw)
    assert saved["sha256"] == case["complete_sha256"] == digest({key: value for key, value in saved.items() if key != "sha256"})
    envelope = saved["document"]["resume_state"]
    assert envelope["sha256"] == digest(envelope["state"])
    state = envelope["state"]
    events = state["history"]["events"]
    selected = {}
    for row in state["rows"]:
        if row["segment"] not in case["segments"]:
            continue
        position = next(position for position, event in enumerate(events) if event["event_id"] == row["event_id"])
        parent = next(event for event in reversed(events[:position]) if event["actor"] == "parent")
        present = any(parent["text"] in message.get("content", "") for message in row["prefix"])
        selected[row["source_sha256"]] = dict(window=case["segments"][row["segment"]],
            segment=row["segment"], source_sha256=row["source_sha256"], target_sha256=hashlib.sha256(row["target"].encode()).hexdigest(),
            terminal=row["terminal"], truncated=row["truncated"],
            latest_parent_event_id=parent["event_id"], latest_parent_source_sha256=parent["source_sha256"],
            exact_parent_text_in_recorded_prefix=present, actual_response=None)
    paths = sorted(path for path in directory.iterdir() if re.fullmatch(r"\d{20}\.json", path.name))
    assert len(paths) < 20000
    inspected_bytes = len(raw)
    inspected_files = 0
    for path in sorted(set(paths[:1024] + paths[-1536:])):
        if path.is_symlink() or path.stat().st_size > 128 * 1024:
            continue
        payload = path.read_bytes()
        inspected_bytes += len(payload)
        inspected_files += 1
        assert inspected_bytes < 128 * 1024 * 1024
        record = json.loads(payload)
        if record["kind"] != "RESPONSE":
            continue
        source_sha = digest(record["document"])
        if source_sha not in selected:
            continue
        assert selected[source_sha]["actual_response"] is None
        assert record["sha256"] == digest({key: value for key, value in record.items() if key != "sha256"})
        assert hashlib.sha256(record["document"]["response"]["raw"].encode()).hexdigest() == selected[source_sha]["target_sha256"]
        selected[source_sha]["actual_response"] = dict(path=str(path), index=record["index"],
            sha256=record["sha256"], file_sha256=hashlib.sha256(payload).hexdigest(),
            request_sha256=record["document"]["request_sha256"], finished_unix=record["document"]["finished_unix"])
    assert len(selected) == 3 and all(item["actual_response"] for item in selected.values())
    return dict(life=label, physical=case["physical"], saved_complete_sha256=case["complete_sha256"],
        inspected_files=inspected_files, inspected_bytes=inspected_bytes, joins=list(selected.values()))


assert socket.gethostname() == "[REDACTED_HOST]"
reports = [inspect(label, case) for label, case in CASES.items()]
print(json.dumps(dict(observed_unix=time.time(), reports=reports, signals=0, writes=0,
    whole_chain_audit=False, scope="existing TRAIN records for candidate slots2/7 only"), sort_keys=True))
