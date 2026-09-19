"""Offline aggregation of bounded, source-bound Think→Act observations."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
STATES = ("YES", "NO", "UNKNOWN")
METRICS = (
    "feedback_delivered", "exact_visibility_at_recognition", "exact_visibility_at_act",
    "specific_recognition", "next_act_observed", "next_act_committed", "next_act_correct",
    "external_check_performed", "external_check_passed", "no_reminder_reuse",
    "post_sleep_retention", "fresh_context_transfer", "artifact_plan_established",
    "planned_artifact_emitted",
)
PREREQUISITES = {
    "next_act_correct": ("next_act_observed", "next_act_committed"),
    "external_check_passed": ("external_check_performed",),
    "planned_artifact_emitted": ("artifact_plan_established", "next_act_observed"),
    "no_reminder_reuse": ("specific_recognition", "next_act_correct"),
    "post_sleep_retention": ("specific_recognition", "next_act_correct"),
    "fresh_context_transfer": ("specific_recognition", "next_act_correct"),
}
REQUIRED_CRITERIA = {
    "no_reminder_reuse": ("later_relevant_action", "intervening_context_complete", "no_reminder"),
    "post_sleep_retention": ("sleep_boundary", "post_sleep_action", "no_reteaching"),
    "fresh_context_transfer": ("fresh_context", "novel_instance", "no_parent_help"),
    "planned_artifact_emitted": ("plan_response", "artifact_specification", "next_action_response"),
    "external_check_performed": ("external_result",),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return digest_bytes(canonical(value).encode())


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate_json_key: " + key)
        result[key] = value
    return result


def sha_valid(value):
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value)


def pointer_value(document, pointer):
    require(isinstance(pointer, str) and (pointer == "" or pointer.startswith("/")), "json_pointer_required")
    current = document
    for component in pointer.split("/")[1:]:
        component = component.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            require(component.isdigit(), "array_pointer_index_required")
            current = current[int(component)]
        else:
            current = current[component]
    return current


class Artifacts:
    def __init__(self):
        self.documents = {}
        self.receipts = {}
        self.bytes_read = 0

    def load(self, path, expected=None):
        path = Path(path).resolve()
        if path not in self.documents:
            require(path.suffix == ".json", "only_explicit_small_json_artifacts_allowed")
            require(path.stat().st_size <= MAX_FILE_BYTES, "artifact_size_limit")
            with path.open("rb") as stream:
                raw = stream.read(MAX_FILE_BYTES + 1)
            require(len(raw) <= MAX_FILE_BYTES, "artifact_size_limit")
            require(self.bytes_read + len(raw) <= MAX_TOTAL_BYTES, "total_artifact_size_limit")
            self.bytes_read += len(raw)
            self.documents[path] = json.loads(raw, object_pairs_hook=unique_object)
            self.receipts[path] = {"path": self.name(path), "sha256": digest_bytes(raw), "bytes": len(raw)}
        if expected is not None:
            require(self.receipts[path]["sha256"] == expected, "artifact_sha256_mismatch: " + self.name(path))
        return self.documents[path]

    @staticmethod
    def name(path):
        return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)

    def ref(self, path, pointer=""):
        path = Path(path).resolve()
        document = self.load(path)
        pointer_value(document, pointer)
        return {"artifact": self.name(path), "sha256": self.receipts[path]["sha256"], "pointer": pointer}

    def verify_ref(self, reference):
        path = ROOT / reference["artifact"]
        require(sha_valid(reference["sha256"]), "source_hash_required")
        return pointer_value(self.load(path, reference["sha256"]), reference["pointer"])


def receipt(reference, kind):
    require(isinstance(reference, dict), "record_receipt_required")
    require(reference.get("kind") == kind and type(reference.get("index")) is int
            and reference["index"] >= 0 and sha_valid(reference.get("sha256")), "invalid_record_receipt")
    return reference


def validate_frame(frame):
    require(frame["stage"] in ("THINK", "ACT", "LEARN"), "actual_stage_required")
    references = [receipt(frame[key], kind) for key, kind in (
        ("request", "REQUEST"), ("response", "RESPONSE"),
        ("committed", "COMMITTED"), ("stage_receipt", "R184_STAGE"))]
    indices = [reference["index"] for reference in references]
    require(all(left < right for left, right in zip(indices, indices[1:])), "record_order_invalid")


def new_case(unit, label, epoch, namespace, frame, origin, assistance="UNKNOWN"):
    require(isinstance(namespace, str) and namespace, "record_namespace_required")
    receipt(frame["response"], "RESPONSE")
    return {
        "unit": unit, "label": label, "epoch": epoch, "record_namespace": namespace,
        "anchor": frame["response"], "frame": frame, "assistance": assistance,
        "visibility_scope": "selected_correction", "origins": [origin],
        "metrics": {name: {"state": "UNKNOWN", "basis": "No explicit evidence/annotation supplied.",
                           "evidence": []} for name in METRICS},
        "reported_level": "UNKNOWN", "limitations": [],
    }


def annotate(case, name, value, basis, evidence):
    require(name in METRICS, "unknown_metric")
    require(value is True or value is False or value is None, "tristate_boolean_required")
    require(value is None or bool(evidence), "known_decision_requires_evidence")
    case["metrics"][name] = {
        "state": "UNKNOWN" if value is None else "YES" if value else "NO",
        "basis": basis, "evidence": evidence,
    }


def verify_review_row(row, document):
    require(row["source_epoch"] == document["source_epoch"] and
            row["source_epoch_sha256"] == document["source_epoch_sha256"], "review_epoch_mismatch")
    frames = {}
    for frame in document["frames"]:
        record_index = frame["response"]["index"]
        require(record_index not in frames or frames[record_index] == frame, "conflicting_projection_record")
        frames[record_index] = frame
    for proof in row["proofs"]:
        validate_frame(proof)
        actual = frames[proof["response"]["index"]]
        require(all(actual.get(key) == value for key, value in proof.items()), "proof_projection_mismatch")
        require(proof["response_utc"] <= document["cutoff_unix"], "proof_outside_cutoff")
    for quote in row["quotes"]:
        reference = quote["reference"]
        if "publication_id" in reference:
            parent = next(parent for parent in document["parents"] if parent["id"] == reference["publication_id"])
            require(parent["sha256"] == reference["source_sha256"], "quote_parent_mismatch")
            excerpt = parent["text"]
        else:
            frame = frames[reference["index"]]
            require(frame["response"] == reference, "quote_response_mismatch")
            excerpt = frame["output"]
        require(not excerpt["truncated"], "complete_quote_source_required")
        text = excerpt["text"]
        require(text[quote["start"]:quote["end"]] == quote["text"] and
                digest_bytes(text.encode()) == quote["full_text_sha256"] and
                digest_bytes(quote["text"].encode()) == quote["span_sha256"], "quote_hash_or_span_mismatch")
    require(row["semantic_review"] == "MANUAL_SOURCE_BOUND_NOT_PARENT_SELF_REPORT", "explicit_review_required")
    level, flags = row["best_supported_level"], row["flags"]
    require(type(level) is int and level in range(4), "invalid_source_level")
    if level >= 1:
        require(flags["identifies_actual_correction"] is True and flags["identification_exposed"] is True,
                "source_level_requires_specific_exposed_recognition")
    if level >= 2:
        require(flags["next_ACT_implements"] is True and flags["next_ACT_exact_exposure"] is True,
                "source_level_requires_correct_visible_next_act")
    if level >= 3:
        require(flags["another_relevant_ACT_implements"] is True and flags["intervening_context_complete"] is True
                and flags["no_intervening_reminder"] is True, "source_level_requires_reuse_proof")


def import_review(store, path, document):
    cases = []
    predecessor = document.get("frozen_predecessor_evidence")
    if predecessor:
        store.load(path.parent / predecessor["path"], predecessor["sha256"])
    for position, row in enumerate(document["rows"]):
        pointer = f"/rows/{position}"
        evidence_path = (path.parent / row["evidence_path"]).resolve()
        require(evidence_path.is_relative_to(path.parent), "review_evidence_path_escape")
        evidence = store.load(evidence_path, row["evidence_sha256"])
        verify_review_row(row, evidence)
        frame = row["proofs"][0]
        require(frame["stage"] == "ACT", "selected_next_act_required")
        parent_ref = row["quotes"][0]["reference"]
        publication = parent_ref["publication_id"]
        observed_visibility = publication in frame["visible_publications"]
        require(observed_visibility is row["flags"]["next_ACT_exact_exposure"], "visibility_flag_mismatch")
        case = new_case("reviewed_correction_chain", row["label"], row["source_epoch_sha256"],
                        row["source_epoch"]["journal_id"], frame, store.ref(path, pointer),
                        "PARENT_CORRECTION_PRESENT_IN_SAMPLED_HISTORY")
        case["reported_level"] = row["best_supported_level"]
        case["limitations"] = [row["unknowns"], "One selected chain per life, not every reviewed ACT.",
                                "Source semantic review has no independent second-reviewer signoff."]
        case["reviewed_ACTs_in_source_window"] = row["window"]["reviewed_ACTs"]
        for metric, flag in (("specific_recognition", "identifies_actual_correction"),
                             ("exact_visibility_at_act", "next_ACT_exact_exposure"),
                             ("next_act_correct", "next_ACT_implements")):
            annotate(case, metric, row["flags"][flag], "Explicit selected-chain reviewer flag; not a text classifier.",
                     [store.ref(path, pointer + "/flags/" + flag)])
        if row["flags"]["identifies_actual_correction"]:
            annotate(case, "exact_visibility_at_recognition", row["flags"]["identification_exposed"],
                     "Specific recognition frame exposure reviewed.", [store.ref(path, pointer + "/proofs")])
        for metric in ("next_act_observed", "next_act_committed"):
            annotate(case, metric, True, "Source-bound REQUEST→RESPONSE→COMMITTED→ACT stage.",
                     [store.ref(path, pointer + "/proofs/0")])
        delivered = [(position, inbox) for position, inbox in enumerate(evidence["inboxes"])
                     if inbox.get("event_id") == "parent:inbox:" + publication and
                     inbox.get("source_sha256") == parent_ref["source_sha256"] and
                     inbox["index"] < frame["request"]["index"]]
        if delivered:
            inbox_position, inbox = delivered[0]
            receipt(inbox, "INBOX")
            annotate(case, "feedback_delivered", True, "Matching source-hashed INBOX before selected ACT.",
                     [store.ref(evidence_path, f"/inboxes/{inbox_position}")])
        if row["flags"].get("intervening_context_complete") is True and row["flags"].get("no_intervening_reminder") is True:
            annotate(case, "no_reminder_reuse", row["flags"]["another_relevant_ACT_implements"],
                     "Explicit later-action review with complete no-reminder proof.", [store.ref(path, pointer + "/flags")])
        cases.append(case)
    return cases, []


def import_hourly(store, path, document):
    cases, exclusions = [], []
    for position, row in enumerate(document["rows"]):
        pointer = f"/rows/{position}"
        if row.get("native_identity_verified") is not True or not row.get("source_epoch_id"):
            exclusions.append({"label": row["label"], "reason": row["status"],
                               "unit": "uncollected_fleet_registration", "source": store.ref(path, pointer)})
            continue
        namespace = row["current_window"]["head"]["journal_id"]
        for act_position, act in enumerate(row.get("ACT_parent_exposure", {}).get("acts", [])):
            act_pointer = pointer + f"/ACT_parent_exposure/acts/{act_position}"
            frame = act["output"]
            validate_frame(frame)
            require(frame["stage"] == "ACT" and act["source_epoch_id"] == row["source_epoch_id"], "hourly_act_epoch_mismatch")
            require(act["parent_count"] == len(act["parents"]), "parent_count_mismatch")
            values = [parent.get("exact_parent_text_in_ACT") for parent in act["parents"]]
            require(all(value is None or type(value) is bool for value in values), "literal_visibility_boolean_required")
            visible = True if True in values else False if not values or all(value is False for value in values) else None
            case = new_case("unreviewed_ACT", row["label"], row["source_epoch_id"], namespace,
                            frame, store.ref(path, act_pointer),
                            "PARENT_TEXT_VISIBLE" if visible else "ASSISTANCE_UNKNOWN_NOT_PROVEN_ABSENT")
            case["visibility_scope"] = "any_parent_in_bounded_TRAIN_reader_NOT_selected_correction"
            case["limitations"] = ["Unadjudicated ACT: exposure is neither semantic uptake nor correctness.",
                                    "No literal parent text does not establish independence or no prior help."]
            annotate(case, "exact_visibility_at_act", visible, "Explicit observer literal-body exposure result.",
                     [store.ref(path, act_pointer)])
            for metric in ("next_act_observed", "next_act_committed"):
                annotate(case, metric, True, "Observer source-bound committed ACT; no correction link inferred.",
                         [store.ref(path, act_pointer + "/output")])
            cases.append(case)
    return cases, exclusions


def import_withdrawal(store, path, document):
    require(document["manual_assessment_covers_entire_epoch"] is True and document["partial_interval"] is False,
            "complete_withdrawal_assessment_required")
    chain = document["source_bound_chain"]
    require([frame["stage"] for frame in chain] == ["THINK", "ACT", "LEARN"], "withdrawal_stage_chain_required")
    for frame in chain:
        for key, kind in (("REQUEST", "REQUEST"), ("RESPONSE", "RESPONSE"), ("R184_STAGE", "R184_STAGE")):
            receipt(frame[key], kind)
        require(frame["REQUEST"]["index"] < frame["RESPONSE"]["index"] < frame["R184_STAGE"]["index"], "withdrawal_stage_order")
    actual_act = receipt(document["actual_ACT"], "R184_ACT")
    require(chain[1]["R184_STAGE"]["index"] < actual_act["index"], "withdrawal_actual_act_order")
    require(document["no_new_Astra_or_Rohin_or_peer_input_before_these_outputs"] is True
            and document["no_parent_or_human_or_peer_inbox_during_cycle"] is True
            and document["prior_parent_and_Tool_context_visible"] is True, "withdrawal_assistance_annotation_required")
    frame = {"stage": "ACT", "request": chain[1]["REQUEST"], "response": chain[1]["RESPONSE"],
             "stage_receipt": chain[1]["R184_STAGE"], "actual_act": actual_act}
    case = new_case("reviewed_withdrawal_cycle", document["life"], "UNKNOWN",
                    "artifact_local_interval:" + document["raw_interval_sha256"], frame,
                    store.ref(path), "NO_NEW_PARENT_HUMAN_PEER_INPUT_PRIOR_CONTEXT_VISIBLE")
    case["visibility_scope"] = "prior_parent_context_not_selected_correction"
    case["limitations"] = [document["prior_aid_caveat"],
                            "No journal/incarnation ID: deduplication only within this bound interval.",
                            "A completed sleep is not a post-sleep retention test.",
                            "Tool acceptance is not a verified correction or humor judgment."]
    assessment = document["manual_read_only_assessment"]
    if assessment.get("error_identification") == "No concrete error identification or deciding check in the three source-bound responses.":
        annotate(case, "specific_recognition", False, "Existing full-interval manual assessment, not regex inference.",
                 [store.ref(path, "/manual_read_only_assessment/error_identification")])
    annotate(case, "next_act_observed", True, "Source-bound ACT stage and actual R184_ACT receipt.",
             [store.ref(path, "/source_bound_chain/1"), store.ref(path, "/actual_ACT")])
    return [case], []


def verify_criteria(store, name, decision, frame):
    values = {}
    criteria = REQUIRED_CRITERIA.get(name, ())
    if name == "external_check_performed" and decision["state"] == "NO":
        criteria = ("complete_check_window", "no_external_check_observed")
    for criterion in criteria:
        require(criterion in decision.get("criteria", {}), "missing_criterion: " + criterion)
        values[criterion] = store.verify_ref(decision["criteria"][criterion])
    for criterion in ("intervening_context_complete", "no_reminder", "no_reteaching",
                      "fresh_context", "novel_instance", "no_parent_help",
                      "complete_check_window", "no_external_check_observed"):
        if criterion in values:
            require(values[criterion] is True, "unestablished_criterion: " + criterion)
    for criterion in ("later_relevant_action", "post_sleep_action"):
        if criterion in values:
            validate_frame(values[criterion])
            require(values[criterion]["stage"] == "ACT" and
                    values[criterion]["response"]["index"] > frame["response"]["index"], "later_ACT_required")
    if "sleep_boundary" in values:
        boundary = receipt(values["sleep_boundary"], "SLEEP_COMPLETE")
        require(frame["response"]["index"] < boundary["index"] < values["post_sleep_action"]["request"]["index"],
                "post_sleep_order_required")
    if "plan_response" in values:
        plan = receipt(values["plan_response"], "RESPONSE")
        require(plan["index"] < frame["request"]["index"] and
                values["next_action_response"] == frame["response"] and
                isinstance(values["artifact_specification"], str) and values["artifact_specification"].strip(),
                "specific_prior_plan_and_matching_next_action_required")
    if "external_result" in values:
        require(isinstance(values["external_result"], dict) and values["external_result"].get("result") is not None
                and isinstance(values["external_result"].get("record"), dict), "external_result_not_delivery_required")
        reference = values["external_result"]["record"]
        require(reference.get("kind") not in ("REQUEST", "RESPONSE", "INBOX", None), "external_result_not_child_or_delivery")
        receipt(reference, reference["kind"])


def import_annotations(store, path, document):
    require(document.get("schema") == "think_act_annotations_v1" and document.get("reviewer"), "named_annotation_schema_required")
    cases = []
    for position, entry in enumerate(document["cases"]):
        frame = store.verify_ref(entry["frame_evidence"])
        validate_frame(frame)
        require(frame["stage"] == "ACT", "annotation_actual_ACT_required")
        binding = store.verify_ref(entry["identity_evidence"])
        require(binding["journal_id"] == entry["journal_id"] and binding["epoch"] == entry["epoch"], "annotation_identity_mismatch")
        case = new_case("annotated_correction_chain", entry["label"], entry["epoch"], entry["journal_id"],
                        frame, store.ref(path, f"/cases/{position}"))
        case["limitations"] = ["Named annotation is evidence attestation, not independent scientific adjudication."]
        for name in ("next_act_observed", "next_act_committed"):
            annotate(case, name, True, "Source-bound committed ACT frame verified.", [entry["frame_evidence"]])
        for name, decision in entry["metrics"].items():
            require(name in METRICS and decision["state"] in STATES and decision.get("basis"), "invalid_annotation_metric")
            sources = decision.get("evidence", [])
            for source in sources:
                store.verify_ref(source)
            known = decision["state"] != "UNKNOWN"
            if name in ("next_act_observed", "next_act_committed"):
                require(decision["state"] == "YES", "annotation_contradicts_committed_frame")
            require(not known or bool(sources), "annotation_evidence_required")
            if known:
                verify_criteria(store, name, decision, frame)
            annotate(case, name, None if not known else decision["state"] == "YES",
                     decision["basis"], sources + list(decision.get("criteria", {}).values()))
        for name, prerequisites in PREREQUISITES.items():
            if case["metrics"][name]["state"] != "UNKNOWN":
                require(all(case["metrics"][prior]["state"] == "YES" for prior in prerequisites),
                        "unestablished_prerequisite: " + name)
        if "assistance" in entry:
            require(store.verify_ref(entry["assistance_evidence"]) == entry["assistance"], "assistance_annotation_mismatch")
            case["assistance"] = entry["assistance"]
        cases.append(case)
    return cases, []


def deduplicate(cases):
    claims = defaultdict(list)
    for position, case in enumerate(cases):
        for value in case["frame"].values():
            if isinstance(value, dict) and {"index", "kind", "sha256"} <= value.keys():
                claims[(case["record_namespace"], value["index"])].append((position, value["kind"], value["sha256"]))
    conflicted = set()
    exclusions = []
    for key, versions in sorted(claims.items()):
        if len({(kind, sha256) for position, kind, sha256 in versions}) > 1:
            positions = sorted({position for position, kind, sha256 in versions})
            conflicted.update(positions)
            exclusions.append({"reason": "conflicting_record_hash_or_kind", "record_namespace": key[0],
                               "record_index": key[1], "input_positions": positions,
                               "source_cases": [cases[position] for position in positions]})
    groups = defaultdict(list)
    for position, case in enumerate(cases):
        if position not in conflicted:
            groups[(case["record_namespace"], case["anchor"]["index"])].append(case)
    kept = []
    for key, group in sorted(groups.items()):
        comparable = [{field: value for field, value in case.items() if field != "origins"} for case in group]
        hashes = {case["anchor"]["sha256"] for case in group}
        same = all(value == comparable[0] for value in comparable)
        if len(hashes) != 1 or not same:
            exclusions.append({"reason": "conflicting_record_hash_or_annotation_or_epoch",
                               "record_namespace": key[0], "record_index": key[1], "input_rows": len(group),
                               "source_cases": group})
            continue
        kept.append(group[0])
        if len(group) > 1:
            exclusions.append({"reason": "duplicate_record_observation_not_an_independent_trial",
                               "record_namespace": key[0], "record_index": key[1], "input_rows": len(group) - 1})
    return kept, exclusions


def counts(cases, metric):
    totals = Counter(case["metrics"][metric]["state"] for case in cases)
    known = totals["YES"] + totals["NO"]
    return {"yes": totals["YES"], "no": totals["NO"], "unknown": totals["UNKNOWN"],
            "assessed_denominator": known, "sampled_denominator": len(cases),
            "yes_rate_among_assessed": totals["YES"] / known if known else None}


def summarize_group(cases):
    recognition = [case for case in cases if case["metrics"]["specific_recognition"]["state"] == "YES"]
    visible = [case for case in cases if case["metrics"]["exact_visibility_at_act"]["state"] == "YES"]
    plans = [case for case in cases if case["metrics"]["artifact_plan_established"]["state"] == "YES"]
    return {"sampled_units": len(cases), "metrics": {name: counts(cases, name) for name in METRICS},
            "source_reported_levels_not_inferred": dict(Counter(str(case["reported_level"]) for case in cases)),
            "conditional": {"next_act_correct_given_specific_recognition": counts(recognition, "next_act_correct"),
                            "next_act_correct_given_exact_visibility": counts(visible, "next_act_correct"),
                            "emitted_given_established_plan": counts(plans, "planned_artifact_emitted")}}


def aggregate(cases, exclusions=()):
    kept, duplicates = deduplicate(cases)
    cohorts, strata = defaultdict(list), defaultdict(list)
    for case in kept:
        cohorts[case["unit"]].append(case)
        key = (case["unit"], case["label"], case["epoch"], case["assistance"], case["visibility_scope"],
               case["metrics"]["exact_visibility_at_act"]["state"])
        strata[key].append(case)
    return {"schema": "think_act_measurement_v1", "input_case_count": len(cases), "unique_case_count": len(kept),
            "input_rows_omitted_from_analysis": len(cases) - len(kept),
            "cohorts": {unit: summarize_group(group) for unit, group in sorted(cohorts.items())},
            "strata": [{"unit": key[0], "label": key[1], "epoch": key[2], "assistance": key[3],
                        "visibility_scope": key[4], "visibility": key[5], **summarize_group(group)}
                       for key, group in sorted(strata.items())],
            "analysis_exclusions_NOT_training": list(exclusions) + duplicates,
            "training_rows_excluded": 0, "live_actions": 0, "cases": kept,
            "interpretation": "Descriptive bounded observations only. No pooled causal, fleet-wide, independence, retention or transfer claim."}


def run(manifest_path):
    store = Artifacts()
    manifest = store.load(manifest_path)
    require(manifest.get("schema") == "think_act_inputs_v1", "input_manifest_schema_required")
    adapters = {"review": import_review, "hourly": import_hourly,
                "withdrawal": import_withdrawal, "annotations": import_annotations}
    cases, exclusions = [], []
    for entry in manifest["inputs"]:
        require(sha_valid(entry.get("sha256")), "pinned_input_hash_required")
        path = (ROOT / entry["path"]).resolve()
        document = store.load(path, entry["sha256"])
        imported, omitted = adapters[entry["kind"]](store, path, document)
        cases.extend(imported)
        exclusions.extend(omitted)
    report = aggregate(cases, exclusions)
    report["source_artifacts"] = sorted(store.receipts.values(), key=lambda item: item["path"])
    report["input_bytes_read"] = store.bytes_read
    report["input_cuts"] = [{"kind": entry["kind"], "path": entry["path"],
                             "observed_or_reviewed_utc": store.documents[(ROOT / entry["path"]).resolve()].get(
                                 "observed_utc", store.documents[(ROOT / entry["path"]).resolve()].get("reviewed_utc")),
                             "cutoff_utc": store.documents[(ROOT / entry["path"]).resolve()].get("cutoff_utc")}
                            for entry in manifest["inputs"]]
    return report


def markdown(report):
    lines = ["# Think→Act measurement — bounded offline review", "", report["interpretation"], "",
             "YES/NO are explicit evidence or reviewer annotations; missing evidence is UNKNOWN, not failure.",
             "All omissions below are exclusions from analysis only. No authentic training rows are removed.", ""]
    for unit, cohort in report["cohorts"].items():
        lines += ["## " + unit, "", f"Sampled units: **{cohort['sampled_units']}**. Units are not independent training replications.", "",
                  "| Measure | YES | NO | UNKNOWN | Assessed denominator |",
                  "|---|---:|---:|---:|---:|"]
        for name, values in cohort["metrics"].items():
            lines.append(f"| {name} | {values['yes']} | {values['no']} | {values['unknown']} | {values['assessed_denominator']} |")
        lines += ["", "Source-reported levels (not inferred): `" + canonical(cohort["source_reported_levels_not_inferred"]) + "`.", ""]
        for name, values in cohort["conditional"].items():
            lines.append(f"- {name}: {values['yes']} YES / {values['assessed_denominator']} assessed; "
                         f"{values['unknown']} UNKNOWN of {values['sampled_denominator']} eligible observations.")
        lines.append("")
    lines += ["## Assistance / visibility / epoch strata", "",
              "Full epoch hashes and all metric denominators are in SUMMARY.json; truncated hashes below are display-only.", "",
              "| Unit / life | Epoch | Assistance | Visibility scope / result | N | Recognition YES/assessed | Next correct YES/assessed |",
              "|---|---|---|---|---:|---:|---:|"]
    for row in report["strata"]:
        recognition, correct = row["metrics"]["specific_recognition"], row["metrics"]["next_act_correct"]
        recognition_text = f"{recognition['yes']}/{recognition['assessed_denominator']}" if recognition["assessed_denominator"] else "UNKNOWN (0 assessed)"
        correct_text = f"{correct['yes']}/{correct['assessed_denominator']}" if correct["assessed_denominator"] else "UNKNOWN (0 assessed)"
        lines.append(f"| {row['unit']} / {row['label']} | {row['epoch'][:12]} | {row['assistance']} | "
                     f"{row['visibility_scope']} / {row['visibility']} | {row['sampled_units']} | "
                     f"{recognition_text} | {correct_text} |")
    lines += ["", "## Analysis omissions and limitations", "",
              f"- Input rows: {report['input_case_count']}; unique retained observations: {report['unique_case_count']}.",
              f"- Analysis omission entries: {len(report['analysis_exclusions_NOT_training'])}; training exclusions: **0**.",
              "- Missing/unresolved fleet registrations are not failed children or zero-scoring ACTs.",
              "- Review windows select one chain each; their other ACTs are not independent adjudicated trials.",
              "- Correctness is imported from explicit review, never from intention words, parent delivery, or judge acceptance.",
              "- The manual review has no independent second-reviewer signoff. Task histories and guidance differ.",
              "- Post-sleep retention, fresh-context transfer and plan→artifact fidelity require additional explicit annotations.",
              "- File hashes bind these small projections; original remote journals are not replayed or re-attested.", "",
              "## Analysis omission reasons", ""]
    reasons = Counter(entry["reason"] for entry in report["analysis_exclusions_NOT_training"])
    lines.extend(f"- `{reason}`: {count} ledger entries." for reason, count in sorted(reasons.items()))
    lines += ["", "## Input provenance", ""]
    lines.extend(f"- `{item['path']}` — `{item['sha256']}` ({item['bytes']} bytes)." for item in report["source_artifacts"])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=HERE / "inputs.json")
    parser.add_argument("--output-dir", type=Path, help="Optional output directory inside this measurement workstream only.")
    args = parser.parse_args()
    report = run(args.manifest)
    if args.output_dir:
        destination = args.output_dir.resolve()
        require(destination.is_relative_to(HERE), "output_must_stay_inside_measurement_scope")
        destination.mkdir(parents=True, exist_ok=True)
        for filename in ("SUMMARY.json", "SUMMARY.md"):
            require((destination / filename).resolve().is_relative_to(HERE), "output_symlink_escape")
            require(str((destination / filename).resolve()) not in
                    {str((ROOT / item["path"]).resolve()) for item in report["source_artifacts"]}, "cannot_overwrite_input_artifact")
        (destination / "SUMMARY.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        (destination / "SUMMARY.md").write_text(markdown(report))
    print(json.dumps({"unique_cases": report["unique_case_count"], "cohorts": report["cohorts"]}, indent=2))


if __name__ == "__main__":
    main()
