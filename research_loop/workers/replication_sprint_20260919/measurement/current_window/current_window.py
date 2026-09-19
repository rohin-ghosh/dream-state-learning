"""Offline, bounded current-window selection and source-bound excerpt export."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
COLLECTOR = ROOT / "research_loop/workers/post_recovery_correction_hourly_20260918"
CUTS = ("20260919T120025.942165Z", "20260919T130025.160777Z")
CUTOFF = datetime(2026, 9, 19, 13, 40, tzinfo=timezone.utc).timestamp()
MAX_FILE = 12 * 1024 * 1024
MAX_TOTAL = 40 * 1024 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def utc(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


def reference(record):
    return {key: record[key] for key in ("index", "kind", "sha256")}


class Sources:
    def __init__(self):
        self.manifest = {}
        self.bytes_read = 0

    def read(self, path, expected=None, maximum=MAX_FILE):
        path = path.resolve()
        require(path.is_relative_to(ROOT) and path.suffix == ".json", "local_repo_json_only")
        require(path.stat().st_size <= maximum, "bounded_artifact_required")
        with path.open("rb") as stream:
            raw = stream.read(maximum + 1)
        require(len(raw) <= maximum, "bounded_artifact_required")
        require(expected is None or sha(raw) == expected, "source_hash_mismatch")
        name = str(path.relative_to(ROOT))
        if name not in self.manifest:
            self.bytes_read += len(raw)
        require(self.bytes_read <= MAX_TOTAL, "bounded_total_required")
        item = {"path": name, "sha256": sha(raw), "bytes": len(raw)}
        require(name not in self.manifest or item == self.manifest[name], "source_changed")
        self.manifest[name] = item
        return json.loads(raw)


def join_frames(records):
    requests, responses, commits, stages = {}, {}, {}, {}
    def bind(mapping, key, record):
        require(key not in mapping or mapping[key] == record, "ambiguous_source_link")
        mapping[key] = record
    for record in records:
        kind = record["kind"]
        if kind == "REQUEST":
            bind(requests, record["request_digest"], record)
        elif kind == "RESPONSE":
            bind(responses, record["document_sha256"], record)
        elif kind in ("COMMITTED", "CONTEXT_COMMITTED"):
            bind(commits, record["source_sha256"], record)
        elif kind == "R184_STAGE":
            bind(stages, record["source_sha256"], record)
    frames = []
    for source, response in responses.items():
        request = requests.get(response["request_digest"])
        commit, stage = commits.get(source), stages.get(source)
        if request is None or commit is None or stage is None:
            continue
        require(request["masked"] and request["index"] < response["index"] < commit["index"] < stage["index"],
                "source_bound_masked_stage_order")
        if max(commit["time_unix"], stage["time_unix"]) <= CUTOFF:
            frames.append({"request": request, "response": response, "committed": commit,
                           "stage_receipt": stage, "stage": stage["stage"]})
    return sorted(frames, key=lambda frame: frame["request"]["index"])


def covered(first, last, intervals):
    cursor = first
    for start, end in sorted(intervals):
        if start > cursor:
            return False
        if end >= cursor:
            cursor = end + 1
        if cursor > last:
            return True
    return False


def opportunities(frames, inboxes, intervals):
    acts = [frame for frame in frames if frame["stage"] == "ACT"]
    groups, unresolved = {}, []
    for inbox in sorted(inboxes, key=lambda item: item["index"]):
        following = next((frame for frame in acts if frame["request"]["index"] > inbox["index"]), None)
        if following is None:
            unresolved.append({"inbox": reference(inbox), "event_id": inbox["event_id"], "reason": "NO_NEXT_COMPLETE_ACT_IN_BOUNDED_INPUT"})
            continue
        if not covered(inbox["index"], following["request"]["index"], intervals):
            unresolved.append({"inbox": reference(inbox), "event_id": inbox["event_id"],
                               "first_observed_act": reference(following["response"]), "reason": "GAP_CANNOT_ESTABLISH_FIRST_NEXT_ACT"})
            continue
        group = groups.setdefault(following["response"]["index"], {"act": following, "parents": []})
        group["parents"].append(inbox)
    return list(sorted(groups.values(), key=lambda item: item["act"]["response"]["index"])), unresolved


def frame_metadata(frame):
    return {"stage": frame["stage"], **{key: reference(frame[key]) for key in
            ("request", "response", "committed", "stage_receipt")},
            "request_utc": utc(frame["request"]["time_unix"]),
            "response_utc": utc(frame["response"]["time_unix"]),
            "committed_utc": utc(frame["committed"]["time_unix"])}


def exact_exposure(request, parent):
    return any(event.get("actor") == "parent" and event.get("event_id") == parent["event_id"]
               and event.get("source_sha256") == parent["source_sha256"] for event in request["external"])


def bounded_excerpt(text, maximum=4096):
    selected = text[:maximum]
    return {"text": selected, "start": 0, "end": len(selected), "truncated": len(selected) != len(text),
            "full_characters": len(text), "full_text_sha256": sha(text.encode()), "excerpt_sha256": sha(selected.encode())}


def load_window(sources):
    targets = {}
    for cut in CUTS:
        cut_path = COLLECTOR / "public/cuts" / (cut + ".json")
        document = sources.read(cut_path, maximum=512 * 1024)
        for row in document["rows"]:
            if row["label"] not in ("C2", "GAME1_P3"):
                continue
            require(row["native_identity_verified"] is True, "current_source_binding_required")
            window = row["current_window"]
            projection_path = COLLECTOR / window["snapshot_relative"]
            evidence = sources.read(projection_path, window["snapshot_sha256"])
            require(evidence["readout_or_private_score_files_read"] == evidence["model_calls"] == evidence["remote_writes"] == evidence["signals"] == 0,
                    "read_only_TRAIN_projection_required")
            target = targets.setdefault(row["label"], {"epoch": row["source_epoch_id"], "journal_id": evidence["journal_id"],
                                                      "records": {}, "intervals": [], "cuts": [], "public_acts": {}})
            require(target["epoch"] == row["source_epoch_id"] and target["journal_id"] == evidence["journal_id"], "source_epoch_changed")
            target["intervals"].append((evidence["coverage_start"], evidence["through"]["index"]))
            target["cuts"].append({"cut": cut, "projection": str(projection_path.relative_to(ROOT)),
                                   "sha256": window["snapshot_sha256"], "caught_up": evidence["caught_up"],
                                   "observed_utc": utc(evidence["observed_unix"]), "first": evidence["coverage_start"],
                                   "through": evidence["through"]["index"], "head": evidence["head"]["index"]})
            for record in evidence["records"]:
                prior = target["records"].get(record["index"])
                require(prior is None or prior == record, "conflicting_duplicate_source_record")
                target["records"][record["index"]] = record
            for act in row["ACT_parent_exposure"]["acts"]:
                target["public_acts"][act["output"]["response"]["index"]] = act["output"]
    for target in targets.values():
        target["frames"] = join_frames(target["records"].values())
        for frame in target["frames"]:
            if frame["stage"] == "ACT":
                public = target["public_acts"][frame["response"]["index"]]
                require(all(public[key] == reference(frame[key]) for key in ("request", "response", "committed", "stage_receipt")),
                        "public_private_ACT_binding_mismatch")
        target["inboxes"] = [record for record in target["records"].values() if record["kind"] == "INBOX" and record.get("actor") == "parent"]
        target["groups"], target["unresolved"] = opportunities(target["frames"], target["inboxes"], target["intervals"])
    return targets


def parent_bodies(sources, targets):
    bodies = {}
    for target in targets.values():
        for frame in target["frames"]:
            for event in frame["request"]["external"]:
                if event.get("actor") == "parent":
                    key = (event["event_id"], event["source_sha256"])
                    body = {"text": event["text"], "origin": "EXACT_RENDERED_TRAIN_EVENT", "rendered_text_sha256": sha(event["text"].encode())}
                    require(key not in bodies or bodies[key]["text"] == body["text"], "parent_body_conflict")
                    bodies[key] = body
    inboxes = {inbox["event_id"].split(":")[-1]: inbox for inbox in targets["C2"]["inboxes"]}
    directory = ROOT / "research_loop/workers/post_reboot_c2_p7_20260919/c2_session1/parent"
    for number in range(75, 104):
        delivery_path = directory / f"parent_{number:06d}/DELIVERED.json"
        if not delivery_path.exists():
            continue
        delivery = sources.read(delivery_path, maximum=4096)
        inbox = inboxes.get(delivery["inbox_id"])
        if inbox is None:
            continue
        require(delivery["consumption"]["record_index"] == inbox["index"] and
                delivery["consumption"]["record_sha256"] == inbox["sha256"], "preserved_delivery_mismatch")
        result_path = delivery_path.parent / "RESULT.json"
        result = sources.read(result_path, delivery["result_sha256"], maximum=32768)
        publication = result["inbox_publication"]
        require(publication["id"] == delivery["inbox_id"] and publication["sha256"] == inbox["source_sha256"], "publication_binding_mismatch")
        key = (inbox["event_id"], inbox["source_sha256"])
        if key not in bodies:
            bodies[key] = {"text": result["response"]["message"], "origin": "PRESERVED_PARENT_RESULT_WITH_EXACT_INBOX_BINDING"}
        bodies[key]["preserved_delivery"] = str(delivery_path.relative_to(ROOT))
        bodies[key]["preserved_result"] = str(result_path.relative_to(ROOT))
    return bodies


def prepare():
    sources = Sources()
    targets = load_window(sources)
    bodies = parent_bodies(sources, targets)
    candidates = {"schema": "current_window_candidates_v1", "prepared_utc": datetime.now(timezone.utc).isoformat(),
                  "cutoff_utc": utc(CUTOFF), "child_response_text_exported": False, "targets": {}}
    for label, target in targets.items():
        groups = []
        for group in target["groups"]:
            parents = []
            for inbox in group["parents"]:
                body = bodies.get((inbox["event_id"], inbox["source_sha256"]))
                parents.append({"inbox": reference(inbox), "event_id": inbox["event_id"], "source_sha256": inbox["source_sha256"],
                                "delivered_utc": utc(inbox["time_unix"]), "parent_body": body})
            groups.append({"act": frame_metadata(group["act"]), "parents": parents})
        candidates["targets"][label] = {"epoch": target["epoch"], "journal_id": target["journal_id"], "cuts": target["cuts"],
                                        "groups": groups, "unresolved_deliveries": target["unresolved"]}
    manifest = {"schema": "current_window_source_manifest_v1", "created_utc": datetime.now(timezone.utc).isoformat(),
                "cutoff_utc": utc(CUTOFF), "sources": list(sources.manifest.values()), "bytes_read": sources.bytes_read,
                "remote_reads": 0, "remote_writes": 0, "messages": 0, "signals": 0, "parent_API_calls": 0,
                "sealed_score_files_read": 0, "full_journals_read": 0,
                "preregistration_sha256": sha((HERE / "PREREGISTRATION.md").read_bytes())}
    save("SOURCE_MANIFEST.json", manifest)
    save("CANDIDATES.json", candidates)
    print(json.dumps({"candidate_groups": {label: len(target["groups"]) for label, target in targets.items()},
                      "bytes_read": sources.bytes_read}))


def select_groups(target, decisions):
    require(set(decisions) == {str(group["act"]["response"]["index"]) for group in target["groups"]}, "all_candidates_must_be_classified")
    require(all(type(decision["actionable"]) is bool and decision["target"] for decision in decisions.values()), "explicit_parent_only_decision_required")
    eligible = [group for group in target["groups"] if decisions[str(group["act"]["response"]["index"])]["actionable"]]
    return eligible[-3:]


def extract():
    manifest = json.loads((HERE / "SOURCE_MANIFEST.json").read_text())
    selection = json.loads((HERE / "SELECTION.json").read_text())
    require(selection["child_outcomes_inspected_before_selection"] is False, "outcome_blind_selection_required")
    require(manifest["preregistration_sha256"] == sha((HERE / "PREREGISTRATION.md").read_bytes()), "preregistration_changed")
    sources = Sources()
    for source in manifest["sources"]:
        sources.read(ROOT / source["path"], source["sha256"])
    targets = load_window(sources)
    bodies = parent_bodies(sources, targets)
    evidence = {"schema": "current_window_evidence_v1", "cutoff_utc": utc(CUTOFF),
                "selection_sha256": sha((HERE / "SELECTION.json").read_bytes()),
                "source_manifest_sha256": sha((HERE / "SOURCE_MANIFEST.json").read_bytes()), "rows": []}
    for label, target in targets.items():
        selected = select_groups(target, selection["correction_targets"][label])
        require([group["act"]["response"]["index"] for group in selected] == selection["selected_ACT_responses"][label], "not_last_three_eligible")
        for group in selected:
            primary = group["parents"][-1]
            require((primary["event_id"], primary["source_sha256"]) in bodies, "selected_parent_body_unknown")
            act = group["act"]
            thoughts = [frame for frame in target["frames"] if frame["stage"] == "THINK" and
                        group["parents"][0]["index"] < frame["request"]["index"] < act["request"]["index"]]
            thoughts_output = []
            for frame in thoughts:
                visible = [parent for parent in group["parents"] if exact_exposure(frame["request"], parent)]
                thoughts_output.append({**frame_metadata(frame), "output": bounded_excerpt(frame["response"]["text"]),
                    "primary_parent_exactly_visible": exact_exposure(frame["request"], primary),
                    "group_correction_parents_visible": [parent["event_id"] for parent in visible],
                    "external_actor_counts": {actor: sum(event["actor"] == actor for event in frame["request"]["external"])
                                              for actor in ("parent", "environment", "human", "peer")}})
            evidence["rows"].append({"life": label, "source_epoch": target["epoch"], "journal_id": target["journal_id"],
                "target": selection["correction_targets"][label][str(act["response"]["index"])]["target"],
                "parents": [{"inbox": reference(parent), "event_id": parent["event_id"], "source_sha256": parent["source_sha256"],
                             "delivered_utc": utc(parent["time_unix"]), "body": bounded_excerpt(bodies[(parent["event_id"], parent["source_sha256"])]["text"])}
                            for parent in group["parents"]],
                "primary_parent": {"inbox": reference(primary), "event_id": primary["event_id"], "source_sha256": primary["source_sha256"]},
                "THINK": thoughts_output,
                "ACT": {**frame_metadata(act), "output": bounded_excerpt(act["response"]["text"]),
                        "primary_parent_exactly_visible": exact_exposure(act["request"], primary),
                        "group_correction_parents_visible": [parent["event_id"] for parent in group["parents"] if exact_exposure(act["request"], parent)]},
                "same_target_at_THINK_and_ACT": any(item["primary_parent_exactly_visible"] for item in thoughts_output)
                                                and exact_exposure(act["request"], primary),
                "no_reminder_reuse": "UNKNOWN", "post_sleep_retention": "UNKNOWN", "fresh_context_transfer": "UNKNOWN"})
    save("EVIDENCE.json", evidence)
    print(json.dumps({"selected_opportunities": len(evidence["rows"]), "output": "EVIDENCE.json"}))


SEMANTIC_METRICS = ("specific_recognition_of_primary_in_THINK", "specific_recognition_of_visible_group_feedback_in_THINK",
                    "specific_recognition_in_ACT", "correct_next_ACT", "requested_artifact_present",
                    "external_check", "task_correctness", "child_plan_to_artifact_fidelity")


def verify_annotation(row, annotation):
    require(row["life"] == annotation["life"] and row["ACT"]["response"]["index"] == annotation["ACT_response"], "annotation_identity_mismatch")
    outputs = row["THINK"] + [row["ACT"]]
    require(all(not output["output"]["truncated"] for output in outputs), "full_selected_outputs_required_for_negative_review")
    for output in outputs:
        text = output["output"]["text"]
        require(sha(text.encode()) == output["output"]["full_text_sha256"], "reviewed_output_hash_mismatch")
    require(annotation["ACT_quote"] in row["ACT"]["output"]["text"], "ACT_quote_mismatch")
    quoted_think = next(output for output in row["THINK"] if output["response"]["index"] == annotation["THINK_quote"]["response"])
    require(annotation["THINK_quote"]["text"] in quoted_think["output"]["text"], "THINK_quote_mismatch")
    require(all(annotation[metric] in ("YES", "NO", "UNKNOWN") for metric in SEMANTIC_METRICS), "explicit_tristate_required")
    if not any(thought["primary_parent_exactly_visible"] for thought in row["THINK"]):
        require(annotation["specific_recognition_of_primary_in_THINK"] == "UNKNOWN", "unexposed_THINK_recognition_must_stay_unknown")
    require(annotation["basis"], "semantic_rationale_required")


def metric_counts(values):
    counts = Counter(values)
    known = counts["YES"] + counts["NO"]
    return {"YES": counts["YES"], "NO": counts["NO"], "UNKNOWN": counts["UNKNOWN"],
            "assessed_denominator": known, "sampled_denominator": len(values),
            "YES_rate_among_assessed": counts["YES"] / known if known else None}


def report():
    manifest = json.loads((HERE / "SOURCE_MANIFEST.json").read_text())
    evidence = json.loads((HERE / "EVIDENCE.json").read_text())
    annotations = json.loads((HERE / "ANNOTATIONS.json").read_text())
    selection = json.loads((HERE / "SELECTION.json").read_text())
    require(annotations["evidence_sha256"] == sha((HERE / "EVIDENCE.json").read_bytes()), "reviewed_evidence_changed")
    require(evidence["source_manifest_sha256"] == sha((HERE / "SOURCE_MANIFEST.json").read_bytes()), "source_manifest_changed")
    require(evidence["selection_sha256"] == sha((HERE / "SELECTION.json").read_bytes()), "selection_changed")
    sources = Sources()
    for source in manifest["sources"]:
        sources.read(ROOT / source["path"], source["sha256"])
    by_key = {(entry["life"], entry["ACT_response"]): entry for entry in annotations["rows"]}
    require(len(by_key) == len(annotations["rows"]) == len(evidence["rows"]), "duplicate_or_missing_annotation")
    rows = []
    for row in evidence["rows"]:
        key = row["life"], row["ACT"]["response"]["index"]
        annotation = by_key[key]
        verify_annotation(row, annotation)
        rows.append({"life": row["life"], "source_epoch": row["source_epoch"], "journal_id": row["journal_id"],
                     "primary_parent": row["primary_parent"], "THINK_responses": [thought["response"] for thought in row["THINK"]],
                     "ACT": {name: value for name, value in row["ACT"].items() if name != "output"},
                     "same_target_at_THINK_and_ACT": row["same_target_at_THINK_and_ACT"],
                     "metrics": {metric: annotation[metric] for metric in SEMANTIC_METRICS},
                     "basis": annotation["basis"], "target": row["target"],
                     "no_reminder_reuse": "UNKNOWN", "post_sleep_retention": "UNKNOWN", "fresh_context_transfer": "UNKNOWN"})
    aggregates = {}
    for life in ("C2", "GAME1_P3"):
        subset = [row for row in rows if row["life"] == life]
        aggregates[life] = {"opportunities": len(subset), "metrics": {metric: metric_counts([row["metrics"][metric] for row in subset]) for metric in SEMANTIC_METRICS},
                            "exact_primary_visibility_at_ACT": metric_counts(["YES" if row["ACT"]["primary_parent_exactly_visible"] else "NO" for row in subset]),
                            "same_target_visible_in_THINK_and_ACT": metric_counts(["YES" if row["same_target_at_THINK_and_ACT"] else "NO" for row in subset])}
    candidates = json.loads((HERE / "CANDIDATES.json").read_text())
    result = {"schema": "current_window_review_v1", "reviewed_utc": annotations["reviewed_utc"],
              "outcome_cutoff_utc": evidence["cutoff_utc"], "historical_five_chain_analysis_reused": False,
              "source_manifest_sha256": evidence["source_manifest_sha256"], "evidence_sha256": annotations["evidence_sha256"],
              "annotations_sha256": sha((HERE / "ANNOTATIONS.json").read_bytes()),
              "selection_sha256": evidence["selection_sha256"], "code_sha256": sha(Path(__file__).read_bytes()),
              "source_coverage": {label: target["cuts"] for label, target in candidates["targets"].items()},
              "aggregates": aggregates, "rows": rows, "analysis_omissions_NOT_training": selection["analysis_omissions_NOT_training"],
              "unresolved_deliveries": {label: target["unresolved_deliveries"] for label, target in candidates["targets"].items()},
              "training_rows_excluded": 0, "remote_actions": 0, "sealed_scores_read": False,
              "independent_second_review": False,
              "limitations": [selection["comparison_limit"], "Six repeated observations of two existing lives, not independent training-seed replications.",
                              "C2's newest corrective target arrives after the THINK requests but is visible in ACT; these are not stable-target Think→Act trials.",
                              "P3 ACT10638 is unlinked across an unsampled gap. Its outcome is not judged or counted as success/failure.",
                              "One reviewer. No causal claim about adapter learning, parent quality, compaction, or retained independence.",
                              "No live coverage after the 13:00 collector cut is asserted; observed ACTs end at 12:47:53 UTC."]}
    save("CURRENT_EVIDENCE.json", result)
    lines = ["# Current C2/P3 Think→Act measurement", "",
             "Outcome cutoff: **2026-09-19 13:40 UTC**. Fixed source cuts: **12:00 and 13:00 UTC**.",
             "This is a fresh source-bound manual review, not a rerun of the historical five-chain analysis.", "",
             "## Result", "",
             "| Life | Complete selected opportunities | Primary correction visible at ACT | Same target visible during THINK and ACT | Correct next ACT | Requested artifact |",
             "|---|---:|---:|---:|---:|---:|"]
    for life, aggregate in aggregates.items():
        count = aggregate["opportunities"]
        lines.append(f"| {life} | {count} | {aggregate['exact_primary_visibility_at_ACT']['YES']}/{count} | "
                     f"{aggregate['same_target_visible_in_THINK_and_ACT']['YES']}/{count} | "
                     f"{aggregate['metrics']['correct_next_ACT']['YES']}/{count} | {aggregate['metrics']['requested_artifact_present']['YES']}/{count} |")
    lines += ["", "**No selected ACT implements its requested correction or produces its requested artifact.** This is a semantic review of complete outputs, not a regex or language filter.",
              "C2 primary-correction recognition in THINK is **UNKNOWN in all three**: the latest parent instruction was not in either THINK prompt. Earlier group feedback was visible, but those THINKs show no specific recognition of it.",
              "P3's same primary correction was visible in both stages: specific recognition is **0/3** in THINK and **0/3** in ACT. C2 ACT recognition is also **0/3**.",
              "External checks, intrinsic math/humor correctness, child-plan fidelity, reminder-free reuse, post-sleep retention and fresh-context transfer remain **UNKNOWN**, not measured zero success.", "",
              "## Source-linked cases", "",
              "| Life | Primary INBOX | THINK responses | ACT REQUEST → RESPONSE → COMMITTED | ACT response UTC | Finding |",
              "|---|---:|---|---|---|---|"]
    for row in rows:
        act = row["ACT"]
        finding = "V/print correctness assertions; requested graph evidence absent" if row["life"] == "C2" else "Repeated feedback promises; actual requested caption absent"
        lines.append(f"| {row['life']} | {row['primary_parent']['inbox']['index']} | "
                     f"{', '.join(str(reference['index']) for reference in row['THINK_responses'])} | "
                     f"{act['request']['index']} → {act['response']['index']} → {act['committed']['index']} | {act['response_utc']} | {finding} |")
    lines += ["", "The complete record hashes, publication IDs, journal IDs and source epochs are in CURRENT_EVIDENCE.json. EVIDENCE.json has bounded TRAIN-only parent/child excerpts and exact-visibility links; no Tool score bodies or sealed keys are exported.", "",
              "## What this says about current practicality", "",
              "- Delivery is working for these selected turns; the corrective parent text reaches every selected ACT.",
              "- C2 receives a changing target after its THINK prompts. The latest instruction is therefore not a fair test of whether the preceding THINK recognized that instruction. It still fails to supply the artifact once the instruction is visible in ACT.",
              "- P3 fails even with a stable, visible correction across both stages. Missing visibility alone cannot account for those three observations.",
              "- C2 THINK15088 does state V=3, but supplies no worked check; THINK15315 later assigns V=29 in a broken, unexecuted code fragment. An isolated correct value is not a verified correction chain.",
              "- This does not identify the cause of failure or estimate a treatment effect. No retention deployment, teacher modification or experiment launch is made here.", "",
              "## Selection and missing coverage", "",
              "Selection was fixed before inspecting child outputs in PREREGISTRATION.md and SELECTION.json. Each candidate was classified from parent text only; shared-ACT parents are grouped, and the latest three eligible source-linked opportunities per life are used.",
              "The 13:00 cut has only two ACTs per life, so the immediately preceding cut was added, prospectively, for a small window. C2 ACT14996 is older than the last three linked opportunities.",
              "**P3 ACT10638 is complete but unlinked**: its new parent-delivery/first-next-ACT chain crosses the missing interval 10467–10605. It remains UNKNOWN and explicitly outside the complete-opportunity denominator. Thus the P3 sample uses ACT10318,10398,10718, not a claim about its latest three raw ACTs.",
              "C2 also has an unsampled interval 15117–15128. Cross-gap deliveries are not treated as first-next-ACT proofs. Late INBOX events arriving after an ACT prompt are assigned only to a later request, never scored as failed uptake by the in-flight action.",
              "Neither collector cut is caught up. This is the last-three-available **bounded** source set; it does not certify coverage to 13:40. Reported outcomes range from 11:23:31 to 12:47:53 UTC on September 19, 2026.", "",
              "## Limits and reproducibility", "",
              "- Six opportunities from two lives, not six independent replications. One manual reviewer; no independent second review.",
              "- UNKNOWN is excluded only from the assessed metric denominator and remains in the sampled denominator. All analysis omissions are labeled; **zero training rows are excluded**.",
              "- Existing local bounded projections and small preserved C2 parent-delivery receipts only; no remote reads/writes, parent API calls, messages, signals, launches or full-journal reads.",
              "- SOURCE_MANIFEST.json pins every derivation input and the preregistration. It includes ignored local projections: no raw multi-MB copies were added to this workstream. EVIDENCE.json preserves the small reviewed outputs with hashes.",
              "- To revalidate source hashes, annotation spans and rebuild the report without any live action:", "",
              "```bash", "python3 -B research_loop/workers/replication_sprint_20260919/measurement/current_window/current_window.py report",
              "python3 -B -m unittest discover -s research_loop/workers/replication_sprint_20260919/measurement/current_window -p 'test_*.py' -v", "```", "",
              "`prepare` and `extract` are collection/rebuild phases, not a loop to rerun against a changing live target. Rebuilding provenance requires explicitly rebinding manual annotations; hash mismatches fail rather than silently carrying judgments forward.", ""]
    (HERE / "README.md").write_text("\n".join(lines))
    print(json.dumps({life: {"opportunities": data["opportunities"], "correct_next_ACT": data["metrics"]["correct_next_ACT"],
                            "same_target_visible_in_THINK_and_ACT": data["same_target_visible_in_THINK_and_ACT"]} for life, data in aggregates.items()}, indent=2))


def save(name, value):
    path = HERE / name
    require(path.resolve().is_relative_to(HERE), "scope_escape")
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "extract", "report"))
    args = parser.parse_args()
    {"prepare": prepare, "extract": extract, "report": report}[args.phase]()


if __name__ == "__main__":
    main()
