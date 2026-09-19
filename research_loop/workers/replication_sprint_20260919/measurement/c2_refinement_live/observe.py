"""Bounded read-only C2 observation; writes only beside this file."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SPRINT = HERE.parents[1]
SESSION = ROOT / "research_loop/workers/post_reboot_c2_p7_20260919/c2_session_1789831723944764223"
COLLECTOR = ROOT / "research_loop/workers/post_recovery_correction_hourly_20260918"
EXPECTED_ADDENDUM = "14515a0a0306a40846540c647d565e17885a93b64d7a0f0b4472f36c21a1402f"
LIMIT = 1_900_000


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def contains_exact(value, text):
    if isinstance(value, str):
        return text in value
    if isinstance(value, dict):
        return any(contains_exact(child, text) for child in value.values())
    if isinstance(value, list):
        return any(contains_exact(child, text) for child in value)
    return False


def utc():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    require(path.stat().st_size < LIMIT, "bounded_local_input")
    raw = path.read_bytes()
    require(len(raw) < LIMIT, "bounded_local_input")
    return raw


def receipt(path):
    raw = read(path)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(raw), "bytes": len(raw)}


def save(name, document):
    require(Path(name).name == name and name.endswith(".json"), "sidecar_filename_only")
    raw = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()
    require(len(raw) < LIMIT, "projection_under_2MB")
    with (HERE / name).open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"path": str((HERE / name).relative_to(ROOT)), "sha256": sha(raw), "bytes": len(raw)}))


def local_process(pid):
    process = Path("/proc") / str(pid)
    fields = process.joinpath("stat").read_text().rsplit(") ", 1)[1].split()
    return {"pid": pid, "ppid": int(fields[1]), "start_ticks": fields[19], "state": fields[0],
            "argv": process.joinpath("cmdline").read_bytes().decode().rstrip("\0").split("\0")}


def binding():
    manifest = json.loads(read(SESSION / "MANIFEST.json"))
    config = json.loads(read(SESSION / "CONFIG.json"))
    started = json.loads(read(SESSION / "parent/STARTED.json"))
    addendum = Path(manifest["policy_addendum"])
    addendum_raw = read(addendum)
    process = local_process(2774221)
    manifest_sha = sha(read(SESSION / "MANIFEST.json"))
    config_sha = sha(read(SESSION / "CONFIG.json"))
    require(process["ppid"] == 361010 and process["state"] != "Z", "supervisor_owned_parent")
    require(process["argv"][process["argv"].index("--manifest") + 1] == str(SESSION / "MANIFEST.json"), "same_manifest")
    require(process["argv"][process["argv"].index("--manifest-sha256") + 1] == manifest_sha, "process_manifest_hash")
    require(config_sha == started["config_sha256"] == manifest["local_source_sha256"][str(SESSION / "CONFIG.json")], "config_binding")
    require(sha(addendum_raw) == EXPECTED_ADDENDUM == manifest["local_source_sha256"][str(addendum)], "combined_addendum_binding")
    attempts = []
    for directory in sorted((SESSION / "parent").glob("parent_[0-9]*")):
        row = {"attempt": directory.name, "files": {}}
        for name in ("RESULT.json", "DISPATCH.json", "DISPATCH_INTENT.json", "OUTBOUND_ROUTE.json", "SYSTEM.txt", "API_REQUEST.json", "SOURCE.json", "stdout.json"):
            path = directory / name
            if path.exists():
                row["files"][name] = receipt(path)
        result_path = directory / "RESULT.json"
        if result_path.exists():
            row["result"] = json.loads(read(result_path))
        system_path = directory / "SYSTEM.txt"
        if system_path.exists():
            row["exact_combined_addendum_in_system"] = addendum_raw.decode().strip() in read(system_path).decode()
        api_path = directory / "API_REQUEST.json"
        if api_path.exists():
            api = json.loads(read(api_path))
            row["exact_combined_addendum_in_api_request"] = contains_exact(api, addendum_raw.decode().strip())
        provider_path = directory / "stdout.json"
        if provider_path.exists():
            provider = json.loads(read(provider_path))
            row["provider"] = {key: provider.get(key) for key in ("id", "status", "model", "created_at", "completed_at", "error", "usage")}
            row["exact_combined_addendum_in_provider_receipt"] = contains_exact(provider.get("instructions"), addendum_raw.decode().strip())
        attempts.append(row)
    source_paths = [SESSION / "MANIFEST.json", SESSION / "CONFIG.json", SESSION / "parent/STARTED.json", addendum,
                    SPRINT / "operations/C2_REFINEMENT_MEASUREMENT_PLAN.md", SPRINT / "operations/C2_REFINEMENT_NATIVE_PREFLIGHT_1454.json",
                    SPRINT / "operations/C2_HANDOFF_BOUNDARY_WAIT2/ONE_EXECUTION_RESULT.json"]
    return {"schema": "c2_refinement_local_binding_v1", "observed_utc": utc(), "parent_process": process,
            "combined_addendum_sha256": EXPECTED_ADDENDUM, "config_sha256": config_sha, "manifest_sha256": manifest_sha,
            "native_binding_path": config["native_binding_path"], "native_binding_sha256": config["native_binding_sha256"],
            "sources": [receipt(path) for path in source_paths], "attempts": attempts,
            "started_is_delivery": False, "provider_calls": 0, "signals": 0}


def capture(after, maximum):
    require(type(after) is int and after >= 11505, "bounded_current_native_start")
    require(1 <= maximum <= 80, "bounded_record_count")
    local = binding()
    config = json.loads(read(COLLECTOR / "private/CONFIG.json"))
    target = next(entry["binding"] for entry in config["entries"] if entry["label"] == "C2")
    require(target["pid"] == 1139778 and target["start_ticks"] == "30025875" and target["wrapper"] == "ovx3_ssh.sh", "original_native_route")
    manifest = json.loads(read(SESSION / "MANIFEST.json"))
    paths = [COLLECTOR / "contract/reader.py", COLLECTOR / "remote.py"]
    code = "\n".join(read(path).decode() for path in paths)
    code += "\nimport sys\n"
    code += "for filename, expected in " + repr(manifest["remote_helper_sha256"]) + ".items():\n"
    code += "    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected, 'original_helper_hash'\n"
    code += "sys.path.insert(0, " + repr(manifest["remote_operator"]) + ")\n"
    code += "from checkpoint_tail_parent_binding import verify\n"
    code += "native = verify(" + repr(local["native_binding_path"]) + ", " + repr(local["native_binding_sha256"]) + ")\n"
    code += "target = " + repr(target) + "\n"
    code += "before = identity(target)\n"
    code += "evidence = collect(target['root'], target['journal_id'], maximum=" + str(maximum) + ", after=" + str(after) + ")\n"
    code += "assert before == identity(target), 'native_identity_changed'\n"
    code += "original_digest = digest(evidence)\nevents = {}\n"
    code += "for record in evidence['records']:\n"
    code += "    if record['kind'] == 'REQUEST':\n"
    code += "        external = record.pop('external')\n"
    code += "        record['external_refs'] = [digest(event) for event in external]\n"
    code += "        events.update({digest(event): event for event in external})\n"
    code += "result = dict(native=native, identity=before, target=target, evidence=evidence, external_events=events, expanded_collector_sha256=original_digest)\n"
    code += "encoded = json.dumps(result, indent=2, sort_keys=True)\n"
    code += "assert len(encoded.encode()) < " + str(LIMIT - 20000) + ", 'bounded_projection_only'\nprint(encoded)\n"
    result = subprocess.run(["bash", str(ROOT / "gpu/ovx3_ssh.sh"), "CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -"],
                            input=code, text=True, capture_output=True, timeout=240, check=True)
    require(len(result.stdout.encode()) < LIMIT, "bounded_transport")
    document = json.loads(result.stdout)
    document.update(schema="c2_refinement_native_projection_v1", observed_utc=utc(), after=after, maximum=maximum,
                    collector_sources=[receipt(path) for path in paths], sidecar_source=receipt(Path(__file__)),
                    parent_manifest_sha256=local["manifest_sha256"], combined_addendum_sha256=EXPECTED_ADDENDUM)
    return document


def load_audit():
    path = COLLECTOR / "contract/audit.py"
    spec = importlib.util.spec_from_file_location("c2_existing_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def merged_evidence(paths):
    records, continuity, identity = {}, {}, None
    for path in paths:
        document = json.loads(read(path))
        require(identity is None or identity == document["identity"], "same_native_epoch")
        identity = document["identity"]
        if "external_events" in document:
            for key, event in document["external_events"].items():
                require(key == digest(event), "external_event_hash")
            for record in document["evidence"]["records"]:
                if record["kind"] == "REQUEST":
                    record["external"] = [document["external_events"][key] for key in record.pop("external_refs")]
            require(digest(document["evidence"]) == document["expanded_collector_sha256"], "lossless_collector_projection")
        for record in document["evidence"]["records"]:
            require(record["index"] not in records or record == records[record["index"]], "conflicting_records")
            records[record["index"]] = record
        for record in document["evidence"]["continuity"]:
            require(record["index"] not in continuity or record == continuity[record["index"]], "conflicting_chain")
            continuity[record["index"]] = record
    ordered = sorted(continuity.values(), key=lambda row: row["index"])
    for previous, current in zip(ordered, ordered[1:]):
        require(current["index"] == previous["index"] + 1 and current["previous_sha256"] == previous["sha256"], "unbroken_capture_chain")
    return {"records": sorted(records.values(), key=lambda row: row["index"]), "continuity": ordered}


def select(evidence, publication, published_turns=None):
    inboxes = [row for row in evidence["records"] if row["kind"] == "INBOX" and row["event_id"] == "parent:inbox:" + publication["id"]
               and row["source_sha256"] == publication["sha256"]]
    require(len(inboxes) <= 1, "unique_first_policy_inbox")
    if not inboxes:
        return {"first_inbox": None, "opportunities": [], "status": "PUBLICATION_ONLY_INBOX_UNVERIFIED"}
    inbox = inboxes[0]
    frames = load_audit().frames(evidence)
    selected = [frame for frame in frames if frame["stage"] == "ACT" and frame["request"]["index"] > inbox["index"]][:6]
    audit = load_audit()
    published_turns = published_turns or [{"publication": publication}]
    delivered = []
    pending = []
    for turn in published_turns:
        source = turn["publication"]
        matches = [row for row in evidence["records"] if row["kind"] == "INBOX" and row["event_id"] == "parent:inbox:" + source["id"]
                   and row["source_sha256"] == source["sha256"]]
        require(len(matches) <= 1, "unique_publication_consumption")
        if matches:
            delivered.append(dict(turn, inbox=matches[0]))
        else:
            pending.append(dict(turn, status="PUBLICATION_ONLY_NO_INBOX_IN_CAPTURE"))
    projected = []
    previous_request = inbox["index"] - 1
    for position, frame in enumerate(selected):
        think = next((earlier for earlier in reversed(frames) if earlier["stage"] == "THINK" and earlier["request"]["index"] < frame["request"]["index"]), None)
        events = frame["request"]["external"]
        visible = [event for event in events if event["event_id"] == "parent:inbox:" + publication["id"] and event["source_sha256"] == publication["sha256"]]
        grouped = []
        for turn in delivered:
            if not previous_request < turn["inbox"]["index"] < frame["request"]["index"]:
                continue
            actual_events = [event for event in events if event["event_id"] == turn["inbox"]["event_id"] and event["source_sha256"] == turn["publication"]["sha256"]]
            think_events = [] if think is None else [event for event in think["request"]["external"] if event["event_id"] == turn["inbox"]["event_id"] and event["source_sha256"] == turn["publication"]["sha256"]]
            grouped.append(dict(turn, exact_visible_at_ACT=bool(actual_events), rendered_events=actual_events,
                                exact_visible_at_previous_THINK=bool(think_events),
                                arrived_after_previous_THINK_request=None if think is None else turn["inbox"]["index"] > think["request"]["index"]))
        projected.append({"opportunity": position + 1, "request": audit.ref(frame["request"]), "response": audit.ref(frame["response"]),
                          "commit": audit.ref(frame["commit"]), "stage_receipt": audit.ref(frame["stage_receipt"]),
                          "cycle": frame["request"]["cycle"], "request_time_unix": frame["request"]["time_unix"],
                          "response_text": frame["response"]["text"], "response_text_sha256": sha(frame["response"]["text"].encode()),
                          "first_policy_exact_visible": bool(visible), "first_policy_visible_event": visible,
                          "grouped_parent_turns": grouped,
                          "external_events_sha256": digest(events), "external_event_count": len(events),
                          "previous_think": None if think is None else {"request": audit.ref(think["request"]), "response": audit.ref(think["response"]),
                          "commit": audit.ref(think["commit"]), "stage_receipt": audit.ref(think["stage_receipt"]), "text": think["response"]["text"],
                          "first_policy_arrived_after_think_request": think["request"]["index"] < inbox["index"]}})
        previous_request = frame["request"]["index"]
    excluded = [{"request": audit.ref(frame["request"]), "response": audit.ref(frame["response"]), "commit": audit.ref(frame["commit"]),
                 "stage_receipt": audit.ref(frame["stage_receipt"]), "reason": "INBOX_ARRIVED_AFTER_REQUEST_NOT_AN_ELIGIBLE_OPPORTUNITY"}
                for frame in frames if frame["stage"] == "ACT" and frame["request"]["index"] < inbox["index"] < frame["commit"]["index"]]
    complete_stages = {frame["stage_receipt"]["index"] for frame in frames}
    unjoined = [audit.ref(row) for row in evidence["records"] if row["kind"] == "R184_STAGE" and row["stage"] == "ACT"
                and row["index"] > inbox["index"] and row["index"] not in complete_stages]
    require(not unjoined, "unjoined_ACT_receipt_requires_unknown_slot_review_not_silent_exclusion")
    awaiting = [turn for turn in delivered if turn["inbox"]["index"] > previous_request]
    return {"first_inbox": inbox, "opportunities": projected, "excluded_pre_INBOX_requests": excluded,
            "delivered_turns_awaiting_next_ACT": awaiting, "publications_without_INBOX_in_capture": pending,
            "status": "SIX_AVAILABLE" if len(selected) == 6 else "PARTIAL", "selection_rule": "first_six_committed_ACT_requests_after_first_actual_new_policy_INBOX"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("binding", "capture", "select"))
    parser.add_argument("--output", required=True)
    parser.add_argument("--after", type=int, default=15840)
    parser.add_argument("--maximum", type=int, default=12)
    parser.add_argument("--inputs", nargs="*")
    arguments = parser.parse_args()
    if arguments.mode == "binding":
        document = binding()
    elif arguments.mode == "capture":
        document = capture(arguments.after, arguments.maximum)
    else:
        require(arguments.inputs and all(Path(name).name == name for name in arguments.inputs), "sidecar_input_filenames")
        local = binding()
        first = local["attempts"][0]["result"]
        require(first["status"] == "PUBLISHED", "first_attempt_published")
        turns = [{"attempt": row["attempt"], "publication": row["result"]["inbox_publication"], "result_receipt": row["files"]["RESULT.json"],
                  "message": row["result"]["response"]["message"]} for row in local["attempts"] if row.get("result", {}).get("status") == "PUBLISHED"]
        document = select(merged_evidence([HERE / name for name in arguments.inputs]), first["inbox_publication"], turns)
        document.update(observed_utc=utc(), inputs=[receipt(HERE / name) for name in arguments.inputs])
    save(arguments.output, document)


if __name__ == "__main__":
    main()
