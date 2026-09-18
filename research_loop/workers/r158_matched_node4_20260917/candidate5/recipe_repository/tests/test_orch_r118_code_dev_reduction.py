import json
from pathlib import Path
import tempfile
import unittest

from gpu import orch_r118_code_dev_reduction as reduction


class CodeDevReductionTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.checkpoint = "c" * 64
        self.make_snapshot(3, shared=False)
        self.make_snapshot(21, shared=True)

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def mutate(self, relative, function):
        path = self.root / relative
        value = json.loads(path.read_text())
        function(value)
        path.write_text(json.dumps(value))

    def make_snapshot(self, cycle, shared):
        name = f"C{cycle:03d}_DEV"
        self.write(f"readouts/{name}/COMPLETE.json", dict(cycle=cycle, scope="DEV",
                   fresh_process=True, optimizer_steps=0, sleep_buffer_rows=0))
        outcomes = []
        for index in range(8):
            identifier = f"R{cycle:03d}_DEV_DEV_{index}"
            raw = '{"expression":"sum(values)"}' if shared else '```json\n{"expression":"sum(values)"}\n```'
            response = dict(raw=raw, token_ids=[1, 2, 3] if shared else [1, 2, 3, 4],
                            messages=[dict(role="user", content=f"Task {index}")],
                            trainingAllowed=False, input_truncated=False, effective_generation_cap=2048,
                            prompt_tokens=100, terminal=True, truncated=False)
            row = dict(id=identifier, cycle=cycle, kind="NATIVE", split="DEV", phase="readout",
                       evaluation_origin="DEV", status="COMPLETE", response=response,
                       routes=dict(sleep=False, parent=False, optimizer=False, teacher_target=False))
            if shared:
                row.update(shared_checkpoint_sha256=self.checkpoint, shared_generation=1)
            self.write(f"reservations/{identifier}.json", row)
            outcomes.append(dict(task_id=f"DEV{index}", status="COMPLETE", outcome=dict(correct=shared)))
        self.write(f"readouts/{name}/DEV.json", dict(split="DEV", parent_visible=False,
                   sleep_eligible=False, outcomes=outcomes))
        if shared:
            checkpoint = dict(path_sha256=self.checkpoint)
            self.write(f"shared_readout_bindings/{name}.json", dict(checkpoint=checkpoint,
                       state=dict(checkpoint=checkpoint, generation=1), cycle=cycle, scope="DEV"))

    def reduce(self):
        return reduction.reduce_branch(self.root, "C003_DEV", "C021_DEV", self.checkpoint)

    def test_exact_eight_pairs_and_no_raw_export(self):
        result = self.reduce()
        self.assertEqual(result["comparison"]["completed_pairs"], 8)
        self.assertEqual(result["pre_shared"]["last_line_code_fence"], 8)
        self.assertEqual(result["first_shared"]["last_line_expression_json"], 8)
        self.assertEqual(result["comparison"]["pairs"][0]["token_delta"], -1)
        self.assertNotIn('sum(values)', json.dumps(result))
        self.assertNotIn('Task 0', json.dumps(result))

    def test_no_FINAL_path_even_when_present(self):
        with self.assertRaisesRegex(ValueError, "DEV_or_ZERO_only"):
            reduction.read_snapshot(self.root, "C021_FINAL")

    def test_no_readout_from_training_buffer(self):
        self.mutate("reservations/R021_DEV_DEV_0.json", lambda value: value["routes"].update(sleep=True))
        with self.assertRaisesRegex(ValueError, "excluded_from_training"):
            self.reduce()

    def test_checkpoint_identity_required(self):
        with self.assertRaisesRegex(ValueError, "exact_first_shared_checkpoint"):
            reduction.read_snapshot(self.root, "C021_DEV", checkpoint_sha256="wrong")

    def test_changed_prompt_not_matched(self):
        self.mutate("reservations/R021_DEV_DEV_0.json", lambda value: value["response"].update(messages=[]))
        with self.assertRaisesRegex(ValueError, "matched_saved_input"):
            self.reduce()

    def test_failed_row_preserved_not_retried_or_scored_zero(self):
        self.mutate("reservations/R003_DEV_DEV_0.json", lambda value: value.update(status="FAILED"))
        self.mutate("readouts/C003_DEV/DEV.json", lambda value: value["outcomes"][0].update(status="FAILED", outcome=None))
        result = self.reduce()
        self.assertEqual(result["pre_shared"]["coverage"], dict(COMPLETE=7, FAILED=1))
        self.assertEqual(result["comparison"]["completed_pairs"], 7)
        self.assertNotIn("before_recorded_correct", result["comparison"]["pairs"][0])

    def test_no_fake_fresh_process(self):
        self.mutate("readouts/C021_DEV/COMPLETE.json", lambda value: value.update(fresh_process=False))
        with self.assertRaisesRegex(ValueError, "fresh_nonlearning"):
            self.reduce()

    def test_no_partial_readout_success(self):
        self.mutate("readouts/C021_DEV/DEV.json", lambda value: value["outcomes"].pop())
        with self.assertRaisesRegex(ValueError, "fixed_eight_task_panel"):
            self.reduce()

    def test_failure_status_must_match(self):
        self.mutate("reservations/R021_DEV_DEV_0.json", lambda value: value.update(status="FAILED"))
        with self.assertRaisesRegex(ValueError, "task_status_join"):
            self.reduce()

    def test_repetition_is_lexical_only(self):
        self.assertEqual(reduction.repeated_fraction([1, 1, 1, 1, 1]), 0.5)
        self.assertEqual(reduction.repeated_fraction([1]), 0)
        self.assertEqual(self.reduce()["comparison"]["semantic_improvement"], "UNASSESSED")

    def test_multiline_json_diagnostic_does_not_change_recorded_score(self):
        self.mutate("reservations/R021_DEV_DEV_0.json", lambda value: value["response"].update(
                    raw='{\n"expression": "sum(values)"\n}'))
        result = self.reduce()
        response = result["first_shared"]["rows"][0]["response"]
        self.assertFalse(response["last_line_expression_json"])
        self.assertTrue(response["whole_response_expression_json"])
        self.assertTrue(response["expression_python_syntax_valid"])
        self.assertTrue(result["first_shared"]["rows"][0]["outcome"]["correct"])

    def test_expression_syntax_diagnostic_is_not_execution(self):
        self.mutate("reservations/R021_DEV_DEV_0.json", lambda value: value["response"].update(
                    raw='{"expression": "result = [1]"}'))
        response = self.reduce()["first_shared"]["rows"][0]["response"]
        self.assertTrue(response["whole_response_expression_json"])
        self.assertFalse(response["expression_python_syntax_valid"])


if __name__ == "__main__":
    unittest.main()
