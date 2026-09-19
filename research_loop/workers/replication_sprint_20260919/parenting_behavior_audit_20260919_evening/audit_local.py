"""Verify only saved, bounded TRAIN receipts; emit a sidecar patch, never collect."""

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SPRINT = HERE.parent
LIVE = SPRINT / "measurement/c2_refinement_live"
INDEX = SPRINT / "evidence/EVIDENCE_INDEX.json"
STOP_SHA = "9a87ebed18b9cdbc7159b83def560b2e94b4be49da46c712381ce25b44acb432"
HISTORICAL_KEYS = (
    "birth_schedule", "diverse_curriculum", "pair_continuation", "withdrawal",
    "historical_levels", "postcut", "learner_projection", "frozen_projection",
    "c2_early_projection", "historical_c2_derivation", "c2_snapshot_manifest",
    "c2_console5840", "c2_console5842", "c2_story", "later_review_text",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


def stamp(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def receipt(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(raw), "sha256": sha(raw)}


def verify_receipt(expected):
    path = ROOT / expected["path"]
    require(path.resolve().is_relative_to(ROOT), "receipt outside repository")
    actual = receipt(path)
    require(actual == expected, "changed receipt: " + expected["path"])
    return actual


def load_module(path, name):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def build():
    stop_path = LIVE / "continuation_run/STOP.json"
    require(sha(stop_path.read_bytes()) == STOP_SHA, "fixed terminal cut changed")
    stop = read_json(stop_path)
    require(stop["status"] == "PARTIAL_BYTE_LIMIT", "unexpected stop reason")
    require(stop["observer_stopped"] and stop["eligible_ACT_count"] == 4, "wrong cut")
    captures = [verify_receipt(item) for item in stop["captures"]]
    terminal_files = [verify_receipt(item) for item in stop["files"]]
    selection = read_json(ROOT / verify_receipt(stop["selection"])["path"])
    binding_path = ROOT / terminal_files[0]["path"]
    binding = read_json(binding_path)
    observer_path = LIVE / "observe.py"
    observer = load_module(observer_path, "saved_c2_observer_read_only")
    evidence = observer.merged_evidence([ROOT / item["path"] for item in captures])
    turns = [
        {"attempt": item["attempt"], "publication": item["result"]["inbox_publication"],
         "result_receipt": item["files"]["RESULT.json"],
         "message": item["result"]["response"]["message"]}
        for item in binding["attempts"] if item.get("result", {}).get("status") == "PUBLISHED"
    ]
    regenerated = observer.select(evidence, turns[0]["publication"], turns)
    require(regenerated == selection, "saved selection not reproducible")
    records = {item["index"]: item for item in evidence["records"]}
    chain = {item["index"]: item for item in evidence["continuity"]}
    for record in records.values():
        require(record["sha256"] == chain[record["index"]]["sha256"], "projection/header mismatch")
    sources = []
    parents = []
    selected_attempts = {
        turn["attempt"] for item in selection["opportunities"]
        for turn in item["grouped_parent_turns"]
    }
    for attempt in binding["attempts"]:
        if attempt["attempt"] not in selected_attempts:
            continue
        files = {name: verify_receipt(item) for name, item in attempt["files"].items()}
        result = read_json(ROOT / files["RESULT.json"]["path"])
        require(result == attempt["result"], "parent result differs from frozen binding")
        source = read_json(ROOT / files["SOURCE.json"]["path"])
        events = [event for event in source["events"] if event.get("actor") == "child"]
        latest = events[-1] if events else None
        if latest and latest["record_index"] in records:
            require(latest["record_sha256"] == records[latest["record_index"]]["sha256"],
                    "parent latest child source mismatch")
        parents.append({
            "attempt": attempt["attempt"], "files": files,
            "publication": result["inbox_publication"],
            "published_utc": stamp(result["sent_unix"]),
            "schedule_on": result["schedule_on"],
            "message_words": len(result["response"]["message"].split()),
            "latest_child_source": None if latest is None else {
                name: latest.get(name) for name in ("record_index", "record_sha256", "stage")
            },
            "policy_inclusion_flags_in_bound_receipt": {
                name: attempt[name] for name in (
                    "exact_combined_addendum_in_api_request",
                    "exact_combined_addendum_in_provider_receipt",
                    "exact_combined_addendum_in_system",
                )
            },
        })
    opportunities = []
    for selected in selection["opportunities"]:
        linked = {name: records[selected[name]["index"]]
                  for name in ("request", "response", "commit", "stage_receipt")}
        require(linked["stage_receipt"]["stage"] == "ACT", "not an ACT")
        require(sha(selected["response_text"].encode()) == selected["response_text_sha256"],
                "response text hash mismatch")
        previous = selected["previous_think"]
        for turn in selected["grouped_parent_turns"]:
            require(all(event["text"].endswith(turn["message"])
                        for event in turn["rendered_events"]), "visible parent text differs")
        opportunities.append({
            **{name: selected[name] for name in (
                "opportunity", "cycle", "request", "response", "commit", "stage_receipt",
                "response_text_sha256", "external_events_sha256", "external_event_count",
            )},
            "request_file_mtime_utc": stamp(selected["request_time_unix"]),
            "response_file_mtime_utc": stamp(linked["response"]["time_unix"]),
            "response_document_sha256": linked["response"]["document_sha256"],
            "request_digest": linked["request"]["request_digest"],
            "selected_previous_THINK": {
                name: previous[name] for name in ("request", "response", "commit", "stage_receipt")
            },
            "previous_THINK_text_sha256": sha(previous["text"].encode()),
            "parent_exposure": [{
                name: turn[name] for name in (
                    "attempt", "publication", "inbox", "exact_visible_at_ACT",
                    "exact_visible_at_previous_THINK", "arrived_after_previous_THINK_request",
                )
            } for turn in selected["grouped_parent_turns"]],
            "same_exact_grouped_parent_visible_in_both_requests": any(
                turn["exact_visible_at_ACT"] and turn["exact_visible_at_previous_THINK"]
                for turn in selected["grouped_parent_turns"]
            ),
        })
    index = read_json(INDEX)
    history = {}
    for name in HISTORICAL_KEYS:
        expected = index["sources"][name]
        if expected["read_from"] == "git_object":
            raw = subprocess.run(
                ["git", "show", index["reference_commit"] + ":" + expected["path"]],
                cwd=ROOT, check=True, capture_output=True,
            ).stdout
        else:
            raw = (ROOT / expected["path"]).read_bytes()
        require(sha(raw) == expected["file_sha256"] and len(raw) == expected["bytes"],
                "historical evidence changed: " + name)
        sources.append({"name": name, **expected, "verified_this_audit": True})
        if expected["path"].endswith(".json"):
            history[name] = json.loads(raw)
    early = {item["index"]: item for item in history["c2_early_projection"]["records"]}
    require(early[5823]["time_unix"] < early[5840]["time_unix"] < early[5875]["time_unix"],
            "checkpoint chronology")
    require([early[number]["stage"] for number in (5865, 5870, 5877)] == ["THINK", "THINK", "ACT"],
            "Byte stage labels")
    require(Fraction(84 * (26 + 3 * 3), 30) == 98, "console algebra check")
    history_frames = observer.load_audit().frames(history["c2_early_projection"])
    frame_map = {item["response"]["index"]: item for item in history_frames}
    old_records = []
    for number in (5554, 5560, 5623, 5629, 5823, 5838, 5839, 5840, 5858, 5863, 5868, 5875, 5884):
        row = early[number]
        old_records.append({
            "index": number, "kind": row["kind"], "sha256": row["sha256"],
            "document_sha256": row.get("document_sha256"),
            "file_mtime_utc": stamp(row["time_unix"]),
            "native_stage_if_joined": frame_map[number]["stage"] if number in frame_map else None,
            "text_sha256": sha(row["text"].encode()) if "text" in row else None,
        })
    relevant = [row for row in evidence["records"] if row["index"] > 15859]
    boundaries = [{**row, "projected_details": {
        key: records.get(row["index"], {}).get(key)
        for key in ("time_unix", "cycle", "optimizer_steps")
    }} for row in evidence["continuity"] if row["index"] > 15859 and row["kind"] in (
        "SLEEP_COMPLETE", "SLEEP_REQUEST", "SLEEP_RECIPE", "COMPACTION",
    )]
    header_counts = {}
    for row in evidence["continuity"]:
        header_counts[row["kind"]] = header_counts.get(row["kind"], 0) + 1
    snapshot = history["c2_snapshot_manifest"]
    return {
        "schema": "c2_parenting_local_receipt_validation_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "LOCAL_SAVED_TRAIN_RECEIPTS_ONLY",
        "actions": {"remote_reads": 0, "provider_calls": 0, "observer_resets": 0,
                    "recollections": 0, "signals": 0, "source_mutations": 0,
                    "sealed_files_read": 0, "parent_messages": 0, "commits": 0, "pushes": 0},
        "fixed_inputs": [receipt(path) for path in (
            stop_path, INDEX, SPRINT / "evidence/EVIDENCE.md", observer_path,
            ROOT / "research_loop/workers/post_recovery_correction_hourly_20260918/contract/audit.py",
            SPRINT / "operations/C2_REFINEMENT_MEASUREMENT_PLAN.md",
            SPRINT / "parenting/c2_refinement/COMBINED_ADDENDUM.md", LIVE / "OPPORTUNITY_01.json",
            HERE / "audit_local.py",
        )],
        "terminal_files": terminal_files, "capture_receipts": captures,
        "validation": {"capture_count": len(captures), "all_capture_hashes_match": True,
                       "lossless_expansion_and_continuity_passed": True,
                       "saved_selection_reproduced_exactly": True,
                       "projected_record_hashes_match_headers": True,
                       "parent_files_match_bound_receipts": True,
                       "historical_sources_match_index": True},
        "window": {"observer_status": stop["status"], "observer_stopped": True,
                   "observer_cutoff_utc": stamp(stop["observed_unix"]),
                   "source_cursor": stop["cursor"], "charged_bytes": stop["charged_bytes"],
                   "first_header": evidence["continuity"][0],
                   "last_header": evidence["continuity"][-1],
                   "planned_ACTs": 6, "available_ACTs": 4, "unknown_outcomes": 2},
        "opportunities": opportunities, "parents": parents,
        "awaiting_next_ACT": [{"attempt": turn["attempt"], "inbox": turn["inbox"]}
                              for turn in selection["delivered_turns_awaiting_next_ACT"]],
        "publications_without_INBOX": [turn["attempt"]
                                       for turn in selection["publications_without_INBOX_in_capture"]],
        "headers_by_kind": header_counts, "sleep_and_compaction_boundaries": boundaries,
        "post_epoch_nonparent_inbox": [observer.load_audit().ref(row) for row in relevant
                                      if row["kind"] == "INBOX" and row["actor"] != "parent"],
        "historical_sources": sources, "historical_record_refs": old_records,
        "historical_console_turn": history["c2_console5842"],
        "checkpoint51": {"adapter_state_sha256": snapshot["checkpoint"]["adapter_state_sha256"],
                         "optimizer_steps": snapshot["optimizer_steps"],
                         "learned_rows": snapshot["learned_rows"],
                         "console_new_training_rows": snapshot["console_new_training_rows"],
                         "weights_learned_console": snapshot["weights_learned_console"],
                         "model_state_unchanged": snapshot["model_state_unchanged"]},
        "taper_stage_cut": {"utc": history["pair_continuation"]["summarized_utc"],
                            "parents": {name: parent["latest"]["stage"] for name, parent
                                        in history["pair_continuation"]["parents"].items()}},
        "limits": ["Hashes verify saved projections, not a fresh remote recapture.",
                   "Only four selected preceding THINKs are used; no full hidden thought sequence.",
                   "Raw REQUEST bodies and parent journals are not copied into this sidecar.",
                   "No caption probe scoring or new-seed trajectory analysis.",
                   "Source timestamps are collector file mtimes, not exact internal ingestion times.",
                   "Manual behavior grading is separate from mechanical provenance verification."],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch", action="store_true")
    arguments = parser.parse_args()
    result = build()
    if arguments.patch:
        target = HERE / "RECEIPTS.json"
        require(not target.exists(), "refuse to replace receipt")
        print("*** Begin Patch\n*** Add File: " + str(target.relative_to(ROOT)))
        for line in json.dumps(result, indent=2, ensure_ascii=False).splitlines():
            print("+" + line)
        print("*** End Patch")
    else:
        print(json.dumps({name: result[name] for name in (
            "validation", "window", "headers_by_kind", "sleep_and_compaction_boundaries",
            "post_epoch_nonparent_inbox", "checkpoint51", "taper_stage_cut",
        )}, indent=2))


if __name__ == "__main__":
    main()
