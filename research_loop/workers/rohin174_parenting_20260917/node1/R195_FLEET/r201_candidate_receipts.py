"""Bounded read-only saved TRAIN evidence; excludes frozen/creative/repo lives."""

import ast
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import time
import unicodedata

from gpu import orch_r153_code_blocks as blocks


LIVES = {
    2: ("teach_replay", 273681, "40858962"),
    3: ("teach_perception", 418870, "40957164"),
    4: ("teach_parenting", 43557, "40702162"),
    5: ("classroom_brain", 574750, "41061383"),
    7: ("classroom_support", 159864, "40781479"),
}
MAX_BYTES = 256 * 1024 * 1024
MAX_FILE_BYTES = 32 * 1024 * 1024


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


class Reader:
    def __init__(self):
        self.total = 0

    def load(self, path):
        path = Path(path)
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_FILE_BYTES:
            raise ValueError("not_bounded_regular_metadata")
        self.total += metadata.st_size
        if self.total > MAX_BYTES:
            raise ValueError("per_life_read_budget")
        raw = path.read_bytes()
        return json.loads(raw), hashlib.sha256(raw).hexdigest()


def glyphs(text):
    return {
        "characters": len(text),
        "fullwidth_ascii": sum(0xFF01 <= ord(character) <= 0xFF5E for character in text),
        "replacement": text.count("\ufffd"),
        "private_use": sum(unicodedata.category(character) == "Co" for character in text),
        "super_subscript": sum(0x2070 <= ord(character) <= 0x209F for character in text),
        "format_controls": sum(unicodedata.category(character) == "Cf" for character in text),
    }


def parses(source):
    try:
        ast.parse(source)
        return True
    except (SyntaxError, ValueError):
        return False


def inspect_life(physical, label, pid, start_ticks):
    reader = Reader()
    process = Path("/proc") / str(pid)
    identity = (process / "stat").read_text().rsplit(") ", 1)[1].split()
    arguments = (process / "cmdline").read_bytes().decode().split("\0")
    assert identity[19] == start_ticks and process.stat().st_uid == 1395
    assert "gpu.orch_r125_continual_guard" in arguments and "native" in arguments
    guard_path = Path(arguments[arguments.index("--config") + 1])
    guard, guard_sha = reader.load(guard_path)
    plan, plan_sha = reader.load(guard["plan_path"])
    root = Path("/localhome/local-rohing/orch_r136_a100_" + label + "_20260916_attempt1/run1")
    assert plan["root"] == str(root) and plan["physical"] == physical
    assert plan_sha == guard["plan_sha256"] and os.readlink(process / "cwd") == plan["source_root"]
    paths = sorted(path for path in (root / "stream/records").iterdir()
                   if re.fullmatch(r"\d{20}\.json", path.name))
    assert len(paths) <= 20000
    head = None
    for path in reversed(paths[-192:]):
        record, file_sha = reader.load(path)
        if head is None:
            head = {key: record[key] for key in ("index", "kind", "sha256")}
        if record["kind"] == "SLEEP_COMPLETE":
            break
    else:
        raise ValueError("no_complete_within_192_records")
    assert record["sha256"] == digest({key: value for key, value in record.items() if key != "sha256"})
    document = record["document"]
    envelope = document["resume_state"]
    state = envelope["state"]
    assert document["status"] == "COMPLETE" and digest(state) == envelope["sha256"]
    assert state["pending"] is None and state["sleep_frontier"] == len(state["rows"])
    checkpoint_path = root / "checkpoints" / ("sleep_%06d" % document["cycle"]) / "COMMIT.json"
    checkpoint, checkpoint_sha = reader.load(checkpoint_path)
    assert digest(checkpoint["checkpoint_sha256"]) == state["model_state_sha256"]
    events = state["history"]["events"]
    positions = {event["event_id"]: position for position, event in enumerate(events)}
    source_rows = {row["source_sha256"]: row for row in state["rows"]}
    assert len(source_rows) == len(state["rows"])
    sleeps = state["sleep_receipts"]
    assert len(sleeps) >= 15 and all(sleep["status"] == "COMPLETE" for sleep in sleeps)
    windows = {"early5": sleeps[:5], "previous5": sleeps[-10:-5], "latest5": sleeps[-5:]}
    outcomes = []
    parent_events = []
    for position, event in enumerate(events):
        if event["actor"] == "parent":
            parent_events.append((position, event))
        if event["actor"] != "environment" or not event.get("source_id"):
            continue
        inbox_path = Path(event["source_id"])
        if inbox_path.parent != root / "stream/inbox":
            continue
        message, message_sha = reader.load(inbox_path)
        assert message_sha == event["source_sha256"]
        peer = message.get("text", "").startswith("Peer ")
        outcomes.append(dict(event_id=event["event_id"], position=position,
            source_id=str(inbox_path), source_sha256=message_sha, speaker=message.get("speaker"),
            source_receipt=message.get("source_receipt"), peer_message=peer,
            text_excerpt=message.get("text", "")[:1200]))
    reports = {}
    for name, window in windows.items():
        rows = []
        totals = Counter()
        previous_text = None
        for sleep in window:
            for source_sha in sleep["new_row_sha256"]:
                row = source_rows[source_sha]
                assert row["actor"] == "child" and row["split"] == "TRAIN"
                text = row["target"]
                selected = blocks.extract(text, policy=blocks.NFKC_POLICY)
                raw_code = selected.get("raw_source")
                indicators = glyphs(text)
                totals.update(indicators)
                totals["responses"] += 1
                totals["responses_fullwidth"] += bool(indicators["fullwidth_ascii"])
                totals["responses_replacement"] += bool(indicators["replacement"])
                totals["responses_private_use"] += bool(indicators["private_use"])
                code = None
                if raw_code is not None:
                    code = dict(glyphs=glyphs(raw_code), raw_source_sha256=selected["raw_source_sha256"],
                        language=selected.get("language"), raw_python_parses=parses(raw_code),
                        normalized_python_parses=parses(selected["source"]))
                    totals["first_code_blocks"] += 1
                    totals["first_code_blocks_fullwidth"] += bool(code["glyphs"]["fullwidth_ascii"])
                position = positions[row["event_id"]]
                event = events[position]
                assert event["text"] == text and event["source_sha256"] == source_sha
                parents = [parent for parent_position, parent in parent_events if parent_position < position]
                rows.append(dict(cycle=sleep["cycle"], segment=row["segment"], event_id=row["event_id"],
                    source_sha256=source_sha, target_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    truncated=row["truncated"], glyphs=indicators, first_code=code,
                    first_code_selection_reason=selected["reason"],
                    previous_similarity=None if previous_text is None else round(SequenceMatcher(
                        None, previous_text[:6000], text[:6000]).ratio(), 4),
                    preceding_parent=None if not parents else dict(event_id=parents[-1]["event_id"],
                        source_sha256=parents[-1]["source_sha256"], text_excerpt=parents[-1]["text"][:1200]),
                    raw_excerpt=text[:4500], excerpt_truncated=len(text) > 4500))
                previous_text = text
        reports[name] = dict(cycles=[sleep["cycle"] for sleep in window], totals=dict(totals), rows=rows)
    final_identity = (process / "stat").read_text().rsplit(") ", 1)[1].split()
    assert final_identity[19] == start_ticks
    current_paths = sorted(path for path in (root / "stream/records").iterdir()
                           if re.fullmatch(r"\d{20}\.json", path.name))
    final_head, unused_sha = reader.load(current_paths[-1])
    return dict(physical=physical, life=label, pid=pid, start_ticks=start_ticks,
        root=str(root), guard_path=str(guard_path), guard_sha256=guard_sha,
        plan_path=guard["plan_path"], plan_sha256=plan_sha, source_root=plan["source_root"],
        source_pins=guard["source_pins"], hard_end_unix=plan["hard_end_unix"],
        lease_end_unix=plan["lease_end_unix"], gpu_uuid=plan["gpu_uuid"],
        device_minor=guard["device_containment"]["minor"],
        sampled_head=head, current_head={key: final_head[key] for key in ("index", "kind", "sha256")},
        boundary=dict(path=str(path), record_index=record["index"], record_sha256=record["sha256"],
            file_sha256=file_sha, state_sha256=envelope["sha256"], history_sha256=state["history"]["state_sha256"],
            cycle=document["cycle"], optimizer_steps=checkpoint["optimizer_steps"],
            checkpoint_path=str(checkpoint_path), checkpoint_commit_sha256=checkpoint_sha,
            adapter_state_sha256=checkpoint["adapter_state_sha256"], bundle_sha256=checkpoint["checkpoint_sha256"],
            optimizer_rng_path=checkpoint["optimizer_rng_path"], saved_rows=len(state["rows"]),
            saved_events=len(events), still_terminal_at_end=final_head["sha256"] == record["sha256"],
            quiescent_or_preserved=False, full_checkpoint_payload_read=False),
        windows=reports, attributed_environment_receipts=outcomes, bytes_read=reader.total,
        signals=0, writes=0, scope="saved TRAIN state; metadata/sample audit, not retirement readiness")


def main():
    assert socket.gethostname() == "[REDACTED_HOST]" and os.getuid() == 1395
    assert hashlib.sha256(Path(blocks.__file__).read_bytes()).hexdigest() == "95854d7c223d08931793ef86c7a64c119283fc86e270725dc40e967e389b38bd"
    reports = []
    for physical, (label, pid, ticks) in LIVES.items():
        try:
            reports.append(inspect_life(physical, label, pid, ticks))
        except Exception as error:
            reports.append(dict(physical=physical, life=label, status="INCOMPLETE_NO_RECOMMENDATION",
                error_type=type(error).__name__, reason=str(error) if isinstance(error, ValueError) else None))
    print(json.dumps(dict(observed_unix=time.time(), hostname=socket.gethostname(), lives=reports,
        excluded_slots=[0, 1, 6], no_other_hosts=True, no_retirement=True,
        method="first5 vs prior5 vs latest5 saved sleeps; raw glyph counts are descriptive, not language or capability scores"),
        sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
