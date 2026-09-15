import argparse
import ast
import csv
import hashlib
import json
import operator
import subprocess
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path


FOLDER = Path(__file__).resolve().parent
ROOT = FOLDER.parents[2]
PACKET_SHA256 = "4a459a9bea6415ef43c0db936587f50d713e7096cbafca83d7f2074d7a5214c9"
STATUSES = {"PASS", "FAIL", "UNRESOLVED"}
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
FINAL_PATTERN = r"(?m)^FINAL: ([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*\Z"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def arithmetic(expression):
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return Fraction(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](visit(node.left), visit(node.right))
        raise ValueError("Only literal integer arithmetic is allowed")

    return visit(ast.parse(expression, mode="eval").body)


def load_tsv(name):
    with (FOLDER / name).open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def add_artifact(path, content):
    if path.exists():
        raise FileExistsError(f"Refusing to replace existing artifact: {path}")
    relative = path.relative_to(ROOT)
    patch = f"*** Begin Patch\n*** Add File: {relative}\n"
    patch += "".join(f"+{line}\n" for line in content.splitlines())
    patch += "*** End Patch\n"
    subprocess.run(["apply_patch"], input=patch, text=True, cwd=ROOT, check=True)


def serialize(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def build():
    import re

    packet_path = FOLDER / "BLIND_PACKET.json"
    assert digest(packet_path) == PACKET_SHA256
    packet = json.loads(packet_path.read_text())
    assert len(packet) == 190
    decisions = load_tsv("decisions.tsv")
    assert [int(item["index"]) for item in decisions] == list(range(190))
    mathematics = {}
    for item in load_tsv("mathematics.tsv"):
        representative = packet[int(item["representative_index"])]
        assert arithmetic(item["expression"]) == Fraction(item["derived_value"])
        assert representative["task_id"] not in mathematics
        mathematics[representative["task_id"]] = item
    assert set(mathematics) == {row["task_id"] for row in packet}
    targets = {row["target"] for row in packet}
    rows = []
    for index, (source, decision) in enumerate(zip(packet, decisions)):
        target = source["target"]
        assert hashlib.sha256(target.encode()).hexdigest() == source["row_id"]
        assert decision["evidence_quote"] in target, (index, decision["evidence_quote"])
        codes = decision["semantic_code"].split("+")
        semantic_status = "PASS" if codes == ["P"] else "UNRESOLVED" if codes == ["W"] else "FAIL"
        mathematical = mathematics[source["task_id"]]
        final_match = re.search(FINAL_PATTERN, target)
        answer = final_match.group(1) if final_match else "115" if index == 137 else None
        assert answer is not None
        outcome_status = mathematical["status"]
        if Fraction(answer) != Fraction(mathematical["derived_value"]):
            outcome_status = "FAIL"
        neutral_status = "PASS"
        final_quote = final_match.group(0).strip() if final_match else "115"
        neutral_quote = final_quote
        neutral_reason = (
            mathematical["reason"] + " Under the explicitly recorded modeling assumptions, "
            "this outcome follows from the neutral question. The target does not assert a "
            "delivered external checker verdict; arithmetic checks can be made locally. "
            "Missing ownership or weak checking is assessed separately under semantics."
        )
        feedback_basis = "No delivered external feedback claimed; numerical self-check is inferable."
        if "I" in codes:
            neutral_status = "FAIL"
            neutral_quote = decision["evidence_quote"]
            neutral_reason = mathematical["reason"] + " A repeated prior solution is not evidence for an unqualified missing premise."
        if "R" in codes:
            neutral_status = "FAIL"
            neutral_quote = decision["evidence_quote"]
            neutral_reason = decision["note"] + " This is contradicted by the neutral quantities and cannot be licensed by recalling the previous solution."
        if index == 94:
            neutral_status = "FAIL"
            neutral_quote = decision["evidence_quote"]
            neutral_reason = (
                "The neutral prefix supplies the question, a worked 100+200=300 answer, "
                "and a request for an owned record, but no checker event. Only the removed "
                "generation guidance says the final value passed the exact-answer checker. "
                "Recomputing 300 supports numerical correctness, not a claim that an "
                "external checker delivered a verdict."
            )
            feedback_basis = "External checker-event assertion supported only by removed generation guidance."
        if index == 56:
            neutral_status = "UNRESOLVED"
            neutral_quote = "0.5 + 2/3 = 0.5 + 0.6667 = 1.1667 feet."
            neutral_reason = "The exact outcome is two feet, but rounded thirds are written as exact equalities without an approximation qualifier. Ordinary rounding makes the intended calculation recoverable; literal equality truth is not established. This is not external-feedback leakage."
        prior_solution = source["student_prefix"][1]["content"] if len(source["student_prefix"]) == 3 else None
        if prior_solution is not None:
            assert prior_solution in targets
        narrative_status = "FAIL" if "R" in codes else "UNRESOLVED" if "I" in codes or index == 56 else "PASS"
        narrative_reason = decision["note"] if narrative_status != "PASS" else "No additional mathematical contradiction found in the full target under the recorded assumptions."
        if index == 56:
            narrative_reason = "Correct exact final value, but 2/3=0.6667 and 1/6=0.1667 are displayed with equality rather than approximation; precision notation is not exact."
        rows.append({
            "packet_index": index,
            "target_sha256": source["row_id"],
            "task_id": source["task_id"],
            "full_target_read": True,
            "semantics": {
                "status": semantic_status,
                "codes": codes,
                "quote": decision["evidence_quote"],
                "reason": decision["note"],
                "scope": "Substantive semantic contract in generation context; token count and neutral visibility are separate.",
            },
            "neutral_prefix_support": {
                "status": neutral_status,
                "quote": neutral_quote,
                "reason": neutral_reason,
                "question_quote": source["student_prefix"][0]["content"],
                "feedback_distinction": feedback_basis,
                "prior_solution_is_already_read_packet_target": prior_solution in targets if prior_solution else None,
                "recalled_event_policy": "The assistant solution may be recalled as one's own calculation, but not as proof of unseen feedback or missing premises.",
            },
            "mathematical_outcome": {
                "status": outcome_status,
                "target_value": answer,
                "answer_quote": final_quote,
                "answer_location": "FINAL line" if final_match else "Body only; target ends mid-sentence without FINAL line",
                "independent_expression": mathematical["expression"],
                "independent_value": mathematical["derived_value"],
                "reason": mathematical["reason"],
                "assumptions": mathematical["assumptions"],
                "preserved_gold": source["gold"],
                "matches_preserved_gold": Fraction(answer) == Fraction(source["gold"]),
                "gold_modified_or_rescored": False,
            },
            "mathematical_narrative": {"status": narrative_status, "reason": narrative_reason},
            "token_contract": {
                "status": "PASS" if 150 <= source["generated_tokens"] <= 400 else "FAIL",
                "generated_tokens": source["generated_tokens"],
                "minimum": 150,
                "maximum": 400,
                "measurement": "Packet-supplied count; tokenizer not independently rerun",
            },
            "final_line_format": {"status": "PASS" if final_match else "FAIL"},
        })
    summary = {
        "total_targets": len(rows),
        "unique_tasks": len(mathematics),
        "statuses": {
            axis: dict(Counter(row[axis]["status"] for row in rows))
            for axis in ("semantics", "neutral_prefix_support", "mathematical_outcome", "mathematical_narrative", "token_contract", "final_line_format")
        },
        "all_separate_contract_axes_pass": sum(
            all(row[axis]["status"] == "PASS" for axis in ("semantics", "neutral_prefix_support", "mathematical_outcome", "mathematical_narrative", "token_contract", "final_line_format"))
            for row in rows
        ),
        "gold_discrepancy_indices": [row["packet_index"] for row in rows if not row["mathematical_outcome"]["matches_preserved_gold"]],
        "neutral_failure_indices": [row["packet_index"] for row in rows if row["neutral_prefix_support"]["status"] == "FAIL"],
        "semantic_unresolved_indices": [row["packet_index"] for row in rows if row["semantics"]["status"] == "UNRESOLVED"],
        "token_below_minimum_indices": [row["packet_index"] for row in rows if row["token_contract"]["generated_tokens"] < 150],
        "token_above_maximum_indices": [row["packet_index"] for row in rows if row["token_contract"]["generated_tokens"] > 400],
        "missing_final_line_indices": [row["packet_index"] for row in rows if row["final_line_format"]["status"] != "PASS"],
    }
    audit = {
        "schema_version": 1,
        "assessment_type": "Independent blind full-content audit; not author-label comparison or experiment execution",
        "packet_sha256": PACKET_SHA256,
        "author_labels_consulted": False,
        "original_reports_or_reviews_consulted": False,
        "model_calls": 0,
        "gpu_allocations": 0,
        "native_cells": 0,
        "rubric": {
            "P": "PASS: substantive first-person singular/plural owned operations, facts/unknown, task-specific goal connection, and a concrete check or explicit checkable expectation; reusable content, not headings alone.",
            "A": "FAIL: impersonal or only a first-person goal/variable naming, without substantive owned reasoning.",
            "C": "FAIL: only forward computations without concrete check or explicitly stated checkable expectation.",
            "I": "FAIL: materially missing/uncertain premise stated as fact without qualification.",
            "R": "FAIL: purported reusable rule or quantity meaning contradicts its own correct arithmetic.",
            "W": "UNRESOLVED: owned useful reasoning but a generic check assertion or equation-as-expectation boundary does not establish a definite concrete check. Main should adjudicate the boundary, not infer PASS.",
            "concrete_check": "Numerical re-evaluation need not be independent. A problem-specific recombination, unit/exclusion check, or proposed action is sufficient when operands/constraint are identifiable. Mere 'correct'/'matches the problem' is not automatically sufficient.",
            "expectation": "An explicit operation-result expectation may satisfy the user's alternative even without a separate verification. Merely solving an equation is a recorded borderline, not automatically checking it.",
            "first_person_plural": "Accepted when it owns an actual operation; examples include rows 21 and 164. Goal-only 'we need' and variable-only 'let us call' do not suffice.",
            "neutral_prefix": "Truth under neutral prompt, not literal token overlap. Valid self-checks are inferable. Removed guidance cannot support claims of delivered external feedback. Recalled assistant solution is allowed as own event but does not prove an omitted premise.",
            "numerical_independence": "Gold and supplied token count are separate metadata. Manual mathematical derivations preserve mismatches and conditional outcomes; no original target, gold, benchmark or condition labels modified.",
            "conditional_models": "Ordinary word-problem conventions are recorded per task; missing second wage and explicitly rumored growth are not silently treated as established facts.",
        },
        "summary": summary,
        "rows": rows,
    }
    add_artifact(FOLDER / "ASSESSMENT.json", serialize(audit))
    add_artifact(FOLDER / "SUMMARY.json", serialize(summary))
    print(serialize(summary))


def freeze():
    paths = [
        FOLDER / name for name in (
            "BLIND_PACKET.json", "decisions.tsv", "mathematics.tsv", "build_evidence.py",
            "validate_evidence.py", "ASSESSMENT.json", "SUMMARY.json", "REPORT.md", "VALIDATION.txt",
        )
    ]
    paths.append(ROOT / "research_loop/workers/MATH_SEMANTIC_AUDIT.md")
    assert digest(FOLDER / "BLIND_PACKET.json") == PACKET_SHA256
    assert all(path.exists() for path in paths)
    manifest = {
        "state": "FROZEN_BEFORE_ANY_AUTHOR_LABEL_COMPARISON",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "packet_sha256": PACKET_SHA256,
        "author_labels_consulted": False,
        "all_190_targets_read_in_full": True,
        "new_seq_assigned": False,
        "files": {str(path.relative_to(ROOT)): digest(path) for path in paths},
        "scope": "Assessment, report, manual ledgers, evidence-structure code/tests and owned worker handoff only; packet read-only.",
    }
    add_artifact(FOLDER / "FREEZE.json", serialize(manifest))
    print("FREEZE_SHA256", digest(FOLDER / "FREEZE.json"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    arguments = parser.parse_args()
    freeze() if arguments.freeze else build()
