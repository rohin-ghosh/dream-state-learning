"""Synthetic CPU fixtures; no model executions or held examples are sources."""

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import unittest

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import outcome_action_replay as replay


def source_rows():
    rows = []
    for repetition in range(3):
        suffix = chr(ord("B") + repetition) * 12
        actions = (
            "READ INDEX M2AN_" + suffix, "READ RELATION M2AQ_" + suffix,
            "STEP M2AP_" + suffix, "THINK KEEP M2AE_" + suffix,
            "THINK REVISE M2AE_" + suffix, "STOP",
        )
        for action in actions:
            rows.append(dict(
                status="DRAFT_NOT_RELEASED", episode_id=f"synthetic-training-{repetition}",
                source_call_index=len(rows) * 3,
                prefix=[dict(role="system", content=wire.SYSTEM_MESSAGE),
                        dict(role="user", content="Synthetic original public history, not a copy task.")],
                assistant=action, target_eot="<|im_end|>",
                loss_policy=dict(prefix="MASK_ALL", assistant="TRAIN", eot="TRAIN"),
            ))
    return rows


class OutcomeActionReplayTests(unittest.TestCase):
    def test_exact_prompt_target_origin_and_family_order(self):
        sources = source_rows()
        rows, metadata = replay.compile_copy_rows(sources)
        self.assertIsInstance(rows, tuple)
        self.assertEqual(metadata["kind"], "ACTUAL_TRAINING_ACTION_AUTHORED_COPY_PROMPT")
        self.assertEqual(metadata["copy_rows"], 12)
        self.assertEqual(metadata["source_rows"], len(sources))
        self.assertEqual(len(rows), 12)
        self.assertEqual([origin["family"] for origin in metadata["rows"]],
                         [family for family in replay.FAMILIES for unused in range(2)])
        for family_index in range(6):
            for repetition in range(2):
                row = rows[family_index * 2 + repetition]
                source_index = repetition * 6 + family_index
                source = sources[source_index]
                self.assertEqual(row["prefix"], [
                    dict(role="system", content=wire.SYSTEM_MESSAGE),
                    dict(role="user", content="Return the following text verbatim, without explanation:\n" + source["assistant"]),
                ])
                self.assertEqual(row["assistant"], source["assistant"])
                self.assertEqual(row["episode_id"], source["episode_id"])
                self.assertEqual(row["source_call_index"], source["source_call_index"])
                self.assertEqual(row["target_eot"], "<|im_end|>")
                self.assertEqual(row["loss_policy"], {"prefix": "MASK_ALL", "assistant": "TRAIN", "eot": "TRAIN"})
                raw = json.dumps(source, sort_keys=True, ensure_ascii=True, allow_nan=False,
                                 separators=(",", ":")).encode("ascii")
                self.assertEqual(set(row), set(source))
                origin = metadata["rows"][family_index * 2 + repetition]
                self.assertEqual(origin["row_index"], family_index * 2 + repetition)
                self.assertEqual(origin["source_row_sha256"], sha256(raw).hexdigest())
                self.assertEqual(origin["source_assistant_sha256"], sha256(source["assistant"].encode()).hexdigest())
                self.assertEqual(origin["source_row_index"], source_index)
                self.assertEqual(origin["source_episode_id"], source["episode_id"])
                self.assertEqual(origin["source_call_index"], source["source_call_index"])
                self.assertEqual(row["status"], source["status"])

    def test_first_means_actual_call_order_not_input_order(self):
        sources = source_rows()[::-1]
        rows, metadata = replay.compile_copy_rows(tuple(sources))
        self.assertEqual([row["source_call_index"] for row in rows],
                         [index * 3 for family in range(6) for index in (family, family + 6)])
        for row, origin in zip(rows, metadata["rows"]):
            self.assertEqual(sources[origin["source_row_index"]]["source_call_index"],
                             row["source_call_index"])

    def test_source_not_mutated_or_aliased_and_teacher_not_copied(self):
        sources = source_rows()
        sources[0]["prefix"][-1]["content"] += "\nSynthetic teacher marker in source data"
        saved = deepcopy(sources)
        rows, metadata = replay.compile_copy_rows(sources)
        self.assertEqual(sources, saved)
        self.assertNotIn("Synthetic teacher marker", json.dumps([row["prefix"] for row in rows]))
        rows[0]["prefix"][0]["content"] = "changed"
        rows[0]["loss_policy"]["prefix"] = "changed"
        metadata["rows"][0]["source_episode_id"] = "changed"
        self.assertEqual(sources, saved)
        self.assertEqual(rows[1]["loss_policy"], replay.LOSS_POLICY)

    def test_missing_or_single_call_family_fails_without_invented_rows(self):
        sources = source_rows()
        for family_index in range(6):
            for count in (0, 1):
                removed = {family_index + repetition * 6 for repetition in range(count, 3)}
                with self.assertRaisesRegex(ValueError, "two_actual_calls"):
                    replay.compile_copy_rows([row for index, row in enumerate(sources) if index not in removed])

    def test_equal_stop_bytes_require_two_distinct_calls(self):
        compiled, metadata = replay.compile_copy_rows(source_rows())
        rows = compiled[-2:]
        self.assertEqual([row["assistant"] for row in rows], ["STOP", "STOP"])
        self.assertNotEqual(rows[0]["source_call_index"], rows[1]["source_call_index"])
        sources = source_rows()
        sources[6]["source_call_index"] = sources[0]["source_call_index"]
        with self.assertRaisesRegex(ValueError, "duplicate_source_call"):
            replay.compile_copy_rows(sources)

    def test_malformed_or_unsourced_rows_rejected_even_if_not_selected(self):
        for field, invalid in (("status", "EVALUATION"), ("episode_id", ""),
                               ("source_call_index", True), ("source_call_index", -1),
                               ("assistant", "STOP\n"), ("assistant", "STEP M2AP_BAD"),
                               ("target_eot", ""), ("loss_policy", {}), ("prefix", [])):
            with self.subTest(field=field, invalid=invalid):
                sources = source_rows()
                sources[-1][field] = invalid
                with self.assertRaises(ValueError):
                    replay.compile_copy_rows(sources)
        for sources in ([], None, {}, [None]):
            with self.assertRaises(ValueError):
                replay.compile_copy_rows(sources)
        sources = source_rows()
        sources[0]["prefix"][0]["content"] += " teacher guidance"
        with self.assertRaises(ValueError):
            replay.compile_copy_rows(sources)

    def test_source_hash_binds_history_not_only_target(self):
        sources = source_rows()
        before, before_metadata = replay.compile_copy_rows(sources)
        sources[0]["prefix"][-1]["content"] += " changed history"
        after, after_metadata = replay.compile_copy_rows(sources)
        self.assertEqual(before[0]["assistant"], after[0]["assistant"])
        self.assertNotEqual(before_metadata["rows"][0]["source_row_sha256"],
                            after_metadata["rows"][0]["source_row_sha256"])

    def test_schedule_preserves_original_first_three_slots_exactly(self):
        for count in (1, 7, 12, 30, 42):
            for update in range(1, 257):
                indexes = replay.scheduled_indexes(count, 12, update)
                original = tuple(((update - 1) * 4 + slot) % count for slot in range(4))
                self.assertEqual(indexes[:3], original[:3])
                self.assertEqual(indexes[3], count + (update - 1) % 12)
        self.assertEqual(replay.scheduled_indexes(30, 12, 1), (0, 1, 2, 30))
        self.assertEqual(replay.scheduled_indexes(30, 12, 8), (28, 29, 0, 37))
        self.assertEqual(replay.scheduled_indexes(30, 12, 256), (0, 1, 2, 33))
        self.assertEqual(replay.scheduled_indexes(outcome_count=30, replay_count=12, update_number=256),
                         (0, 1, 2, 33))

    def test_schedule_exact_quotas_and_copy_cycle(self):
        indexes = [index for update in range(1, 257)
                   for index in replay.scheduled_indexes(30, 12, update)]
        self.assertEqual(len(indexes), 1024)
        self.assertEqual(sum(index < 30 for index in indexes), 768)
        self.assertEqual(sum(index >= 30 for index in indexes), 256)
        self.assertEqual(Counter(index - 30 for index in indexes if index >= 30),
                         Counter({index: 22 if index < 4 else 21 for index in range(12)}))

    def test_schedule_bounds_and_exact_integer_types(self):
        for count, replay_count, update in ((0, 12, 1), (-1, 12, 1), (True, 12, 1),
                                          (30.0, 12, 1), (30, 0, 1), (30, 11, 1),
                                          (30, 13, 1), (30, 12.0, 1), (30, True, 1),
                                          (30, 12, 0), (30, 12, 257), (30, 12, True),
                                          (30, 12, 1.0)):
            with self.assertRaises(ValueError):
                replay.scheduled_indexes(count, replay_count, update)

    def test_import_does_not_load_native_or_evaluation_modules(self):
        script = (
            "import sys; from organism_v6 import outcome_action_replay; "
            "assert not any(name.split('.')[0] in ('torch', 'peft', 'transformers', 'gpu') "
            "or name.endswith(('composition_birth_stage2a_held', 'composition_birth_stage2a_canaries')) "
            "for name in sys.modules)"
        )
        result = subprocess.run([sys.executable, "-B", "-c", script],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
