from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile

from prepare_packet import add_file, SEED


OUTPUT = Path(__file__).resolve().parent
ROOT = OUTPUT.parents[2]


def expected_answer(question):
    quantities = [Fraction(value) for value in re.findall(r"\d+(?:\.\d+)?", question)]
    if "students play soccer" in question:
        total, sports_percent, soccer_percent = quantities
        sports = total * sports_percent / 100
        answer = sports * soccer_percent / 100
        assert answer / total == sports_percent * soccer_percent / 10000
    elif "tins of beans are left" in question:
        cases, tins_per_case, discarded_percent = quantities
        total = cases * tins_per_case
        discarded = total * discarded_percent / 100
        answer = total - discarded
        assert answer == total * (100 - discarded_percent) / 100
    elif "living room set" in question:
        first_cost, second_cost, other_cost, discount_percent = quantities
        total = first_cost + second_cost + other_cost
        answer = total - total * discount_percent / 100
        assert answer == sum(cost * (100 - discount_percent) / 100 for cost in quantities[:3])
    elif "buying DVDs" in question:
        discount_percent, discount_amount = quantities
        original = discount_amount * 100 / discount_percent
        answer = original - discount_amount
        assert original * discount_percent / 100 == discount_amount
        wrong_original = discount_amount * 100 / (100 - discount_percent)
        assert wrong_original * discount_percent / 100 != discount_amount
    elif "final cost of the dress" in question:
        original, discount_percent = quantities
        answer = original * (100 - discount_percent) / 100
        assert answer == original - original * discount_percent / 100
    elif "Philip" in question and "one-fifth" in question:
        cows, extra_ducks_percent = quantities
        ducks = cows * (100 + extra_ducks_percent) / 100
        pigs = (cows + ducks) / 5
        answer = cows + ducks + pigs
        assert (ducks - cows) / cows == extra_ducks_percent / 100
        assert pigs / (cows + ducks) == Fraction(1, 5)
    else:
        raise AssertionError("Unexpected question outside the bounded packet")
    assert answer.denominator == 1
    return answer.numerator


def main():
    provenance = json.loads((OUTPUT / "provenance.json").read_text())
    mapping = json.loads((OUTPUT / "source_mapping.json").read_text())
    packet = json.loads((OUTPUT / "blind_packet.json").read_text())
    report = (OUTPUT / "review.md").read_text()
    archive_path = ROOT / provenance["archive"]
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == provenance["archive_sha256"]
    names = [f"run/shard{shard}/CALL_{call:04d}.json" for shard in range(6) for call in range(1, 5)]
    names.sort(key=lambda name: hashlib.sha256((SEED + name).encode()).hexdigest())
    assert [entry["archive_member"] for entry in mapping["rows"]] == names
    assert len(packet) == len(provenance["rows"]) == len(names) == 24
    assert [row["opaque_id"] for row in packet] == [f"R{index:02d}" for index in range(1, 25)]
    with tarfile.open(archive_path, "r:gz") as archive:
        for row, entry in zip(packet, provenance["rows"]):
            assert row["opaque_id"] == entry["opaque_id"]
            original = archive.extractfile(entry["archive_member"]).read()
            snapshot = (OUTPUT / "raw" / (row["opaque_id"] + ".json")).read_bytes()
            assert hashlib.sha256(original).hexdigest() == entry["original_sha256"]
            assert hashlib.sha256(snapshot).hexdigest() == entry["snapshot_sha256"]
            assert snapshot == original or snapshot == original + b"\n"
            capture = json.loads(snapshot)
            assert row["generated_text"] == capture["call"]["raw"] == capture["target"]
            assert row["neutral_training_prefix"] == capture["student_prefix"]
            assert capture["generation_messages"] == capture["call"]["messages"]
            evidence = capture["student_prefix"] if len(capture["student_prefix"]) == 1 else capture["student_prefix"][:-1]
            assert all(message in capture["generation_messages"] for message in evidence)
            assert row["generated_tokens_capture"] == capture["generated_tokens"]
            assert row["token_ids_count"] == len(capture["call"]["token_ids"])
            assert row["token_ids_count"] - row["generated_tokens_capture"] == 1
            for forbidden in ("condition", "family", "kind", "gold", "task_id", "admitted", "candidate", "semantic_status", "outcome_pass", "token_contract_pass"):
                assert forbidden not in row
    ledger_pattern = r"^\| (R\d{2}) \| (PASS|FAIL|UNRESOLVED) \| (PASS|FAIL|UNRESOLVED) \| (\d+) \| (PASS|FAIL|UNRESOLVED) \| (PASS|FAIL|UNRESOLVED) \|$"
    ledger = re.findall(ledger_pattern, report, re.MULTILINE)
    sections = re.findall(r"^### (R\d{2}) — (PASS|FAIL|UNRESOLVED)\n(.*?)(?=^### R\d{2} — |^## |\Z)", report, re.MULTILINE | re.DOTALL)
    assert len(ledger) == len(sections) == 24
    results = []
    for row, table, section in zip(packet, ledger, sections):
        opaque_id, disposition, semantic, tokens, length_status, format_status = table
        assert opaque_id == row["opaque_id"] == section[0]
        assert disposition == section[1]
        assert int(tokens) == row["generated_tokens_capture"]
        quotes = re.findall(r"^> (.+)$", section[2], re.MULTILINE)
        assert len(quotes) >= 2
        for quote in quotes:
            assert quote in row["generated_text"], f"Nonliteral quote in {opaque_id}: {quote}"
        axes = dict(re.findall(r"\b([OGERPST])=(PASS|FAIL|UNRESOLVED)\b", section[2]))
        assert set(axes) == set("OGERPST")
        calculated_semantic = "PASS" if all(axes[axis] == "PASS" for axis in "OGERPS") else "FAIL"
        assert calculated_semantic == semantic
        assert length_status == axes["T"] == ("PASS" if 150 <= int(tokens) <= 400 else "FAIL")
        assert disposition == ("PASS" if semantic == length_status == "PASS" else "FAIL")
        answer = expected_answer(row["neutral_training_prefix"][0]["content"])
        terminal_number = re.search(r"(\d+)\s*$", row["generated_text"])
        assert terminal_number and int(terminal_number.group(1)) == answer
        exact_format = bool(re.fullmatch(r"FINAL: \d+", row["generated_text"].strip().splitlines()[-1]))
        assert format_status == ("PASS" if exact_format else "FAIL")
        results.append({
            "opaque_id": opaque_id,
            "disposition": disposition,
            "semantic": semantic,
            "axes": axes,
            "content_tokens_capture": int(tokens),
            "independent_numeric_answer": answer,
            "numeric_status": "PASS",
            "exact_final_format": format_status,
            "literal_quotes_verified": len(quotes),
        })
    current_clock = subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], check=True, capture_output=True, text=True).stdout.strip()
    audit_path = OUTPUT / "validation.json"
    if audit_path.exists():
        recorded_at = json.loads(audit_path.read_text())["recorded_at_tool_clock_utc"]
    else:
        recorded_at = current_clock
    audit = {
        "recorded_at_tool_clock_utc": recorded_at,
        "review_sha256": hashlib.sha256((OUTPUT / "review.md").read_bytes()).hexdigest(),
        "blind_packet_sha256": hashlib.sha256((OUTPUT / "blind_packet.json").read_bytes()).hexdigest(),
        "archive_sha256": provenance["archive_sha256"],
        "checks": ["fixed first24 coverage", "original and snapshot hashes", "unaltered targets", "exact neutral evidence in generation", "excluded label keys", "token metadata", "24 verdicts and all axes", "48 literal quotes", "independent question arithmetic", "separate exact final format"],
        "disposition_counts": dict(Counter(row["disposition"] for row in results)),
        "semantic_counts": dict(Counter(row["semantic"] for row in results)),
        "rows": results,
    }
    assert audit["disposition_counts"] == {"PASS": 18, "FAIL": 6}
    assert audit["semantic_counts"] == {"PASS": 19, "FAIL": 5}
    add_file(audit_path, json.dumps(audit, indent=2) + "\n")
    print(json.dumps({"checked_at_tool_clock_utc": current_clock, "checks_passed": audit["checks"], "dispositions": audit["disposition_counts"], "semantic": audit["semantic_counts"]}, indent=2))


if __name__ == "__main__":
    main()
