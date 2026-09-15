import hashlib
import json
from pathlib import Path

from prepare_packet import add_file


OUTPUT = Path(__file__).resolve().parent


def main():
    rows = []
    for source in sorted((OUTPUT / "raw").glob("R[0-9][0-9].json")):
        capture = json.loads(source.read_text())
        prefix = capture["student_prefix"]
        generation = capture["generation_messages"]
        if generation != capture["call"]["messages"]:
            raise RuntimeError(f"Generation history differs from actual captured call: {source.stem}")
        evidence = prefix if len(prefix) == 1 else prefix[:-1]
        if not all(message in generation for message in evidence):
            raise RuntimeError(f"Neutral evidence not present verbatim in generation: {source.stem}")
        rows.append({
            "opaque_id": source.stem,
            "neutral_training_prefix": prefix,
            "generated_text": capture["call"]["raw"],
            "generated_tokens_capture": capture["generated_tokens"],
            "token_ids_count": len(capture["call"]["token_ids"]),
            "raw_equals_target": capture["call"]["raw"] == capture["target"],
            "neutral_evidence_verbatim_in_generation": True,
            "neutral_prefix_sha256_canonical": hashlib.sha256(json.dumps(prefix, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "withheld_prompt_context": {
                "generation_message_count": len(generation),
                "neutral_message_count": len(prefix),
                "excluded_or_replaced_generation_messages": sum(message not in prefix for message in generation),
                "preservation": "Original generation_messages and call.messages remain untouched in raw/<opaque_id>.json; not review evidence",
            },
        })
    if len(rows) != 24:
        raise RuntimeError("Expected exactly 24 opaque rows")
    add_file(OUTPUT / "blind_packet.json", json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    header = "# Blinded first24 packet\n\n"
    header += "Only captured neutral training prefixes and raw generated text are presented. "
    header += "Original instruction context is preserved separately in raw snapshots, not used as neutral evidence. "
    header += "No condition, family, kind, task ID, gold, admission, outcome, or prior semantic labels are presented.\n\n"
    sections = [header]
    for row in rows:
        sections.append(f"## {row['opaque_id']}\n\nCapture generated tokens: {row['generated_tokens_capture']}; token ID count: {row['token_ids_count']}.\n\n### Exact neutral training prefix\n\n")
        for index, message in enumerate(row["neutral_training_prefix"], 1):
            sections.append(f"#### Message {index}: {message['role']}\n\n```text\n{message['content']}\n```\n\n")
        sections.append(f"### Raw generated text\n\n```text\n{row['generated_text']}\n```\n\n")
    add_file(OUTPUT / "blind_packet.md", "".join(sections))
    print(json.dumps({
        "rows": len(rows),
        "all_neutral_evidence_verbatim_in_generation": all(row["neutral_evidence_verbatim_in_generation"] for row in rows),
        "all_raw_equals_target": all(row["raw_equals_target"] for row in rows),
        "all_content_counts_one_below_token_ids": all(row["generated_tokens_capture"] + 1 == row["token_ids_count"] for row in rows),
    }, indent=2))


if __name__ == "__main__":
    main()
