"""Local synthetic captures only: no tokenizer, model, network or training."""

import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from gpu import astra_selected_reader_repair_train as trainer
from organism_v6 import experienced_event_actual_reader_audit as actual
from organism_v6 import experienced_event_adult_cycle as adult
from organism_v6 import experienced_event_microloop as micro
from organism_v6 import experienced_event_reader_audit_lesson as lesson
from organism_v6 import experienced_event_read_route as controller
from organism_v6 import pcfl_vertical_dev as world
from tests.test_experienced_event_actual_reader_audit import actual_fixture
from tools import astra_selected_reader_repair_reduce as reduce


ROOT = Path(__file__).resolve().parents[1]


def generation(raw, messages=None):
    result = dict(raw=raw, terminal=True, truncated=False, prompt_tokens=10, token_ids=[7, 151645])
    if messages is not None:
        result["messages"] = copy.deepcopy(messages)
    return result


def collection(cycle):
    bank = adult.build_bank(cycle)

    def generate(messages):
        fact = next(fact for fact in bank if fact["port"] in messages[1]["content"])
        raw = "EXPLORE " + fact["node"] + " " + fact["port"] if len(messages) == 2 else micro._event(fact)
        return generation(raw, messages)

    return adult.collect(generate, cycle=cycle)


def schedule(material, selected):
    masks = []
    for index in range(194):
        target = [7] * (1 + index % 3) + [151645]
        masks.append(dict(input_ids=[151644] + target + [198], labels=[-100] + target + [-100], target_ids=target))
    losses = []
    for update in range(1, 101):
        actual_indexes, reference_indexes = reduce.indexes(update, material, selected)
        actual_count = sum(len(masks[index]["target_ids"]) for index in actual_indexes)
        reference_count = sum(len(masks[index]["target_ids"]) for index in reference_indexes)
        scale = actual_count / reference_count
        losses.append(dict(update=update, row_indexes=actual_indexes, reference_row_indexes=reference_indexes,
                           actual_label_count=actual_count, active_label_count=actual_count,
                           reference_label_count=reference_count, original_label_count=reference_count,
                           loss_scale=scale, actual_mean_loss=0.5, loss=0.5 * scale))
    return masks, losses


class ScheduleTests(unittest.TestCase):
    def test_four_schedules_native_equivalence_and_duplicate_doses(self):
        for parent, selected in reduce.SELECTED.items():
            for material in reduce.MATERIALS:
                for update in range(1, 101):
                    actual_indexes, reference = trainer.training_indexes(update, material, selected)
                    self.assertEqual(reduce.indexes(update, material, selected), (list(actual_indexes), list(reference)))
                masks, losses = schedule(material, selected)
                result = reduce.audit_schedule(masks, losses, material, selected)
                expected = [50] * 4 if material == "UNIFORM" else ([0, 72, 0, 128] if parent == "AUDIT_SFT" else [0, 200, 0, 0])
                self.assertEqual(result["new_fact_presentations"], expected)
                self.assertEqual(list(result["budgets"].values()), [100, 100, 38, 62, 200])

    def test_deduplicating_changes_dose(self):
        masks, losses = schedule("SELECTED", [1, 3, 3])
        with self.assertRaisesRegex(ValueError, "schedule_drift"):
            reduce.audit_schedule(masks, losses, "SELECTED", [1, 3])

    def test_schedule_bounds_and_boolean_index(self):
        for update, selected in ((0, [1]), (101, [1]), (1, []), (1, [True]), (1, [4]), (1, [1] * 9)):
            with self.assertRaises(ValueError):
                reduce.indexes(update, "SELECTED", selected)

    def test_partial_losses_masks_prefix_span_and_eot_rejected(self):
        masks, losses = schedule("SELECTED", [1])
        for changed_masks, changed_losses in ((masks[:-1], losses), (masks, losses[:-1])):
            with self.assertRaises(ValueError):
                reduce.audit_schedule(changed_masks, changed_losses, "SELECTED", [1])
        for field, value in (("labels", [151644, 7, 151645, -100]), ("target_ids", [7]),
                             ("input_ids", [151644, 7, 151645, 19]), ("labels", [-100, 7, -100, 198])):
            changed = copy.deepcopy(masks)
            changed[0][field] = value
            with self.assertRaises(ValueError):
                reduce.audit_schedule(changed, losses, "SELECTED", [1])

    def test_denominator_scale_and_nonfinite_rejected(self):
        masks, losses = schedule("SELECTED", [1])
        for field, value in (("reference_label_count", 99), ("loss_scale", 1.23),
                             ("loss", float("nan")), ("actual_mean_loss", float("inf"))):
            changed = copy.deepcopy(losses)
            changed[1][field] = value
            with self.assertRaises(ValueError):
                reduce.audit_schedule(masks, changed, "SELECTED", [1])


class CaptureTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.collection, self.prior = collection(2), collection(1)
        self.runtime = SimpleNamespace(root=ROOT, adult=adult, micro=micro, lesson=lesson, actual=actual,
                                       world=world, controller=controller, source=adult.source, development=adult.cue_sleep)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def reduce(self):
        return reduce.reduce(self.root, self.collection, self.prior, self.runtime)

    def train(self, parent="AUDIT_SFT", material="SELECTED"):
        directory = self.root / (parent + "_" + material) / "train"
        masks, losses = schedule(material, reduce.SELECTED[parent])
        new_rows = self.collection["rows"]
        old_events = [dict(event=fact["event"], raw=micro._event(fact)) for fact in
                      micro.build_bank(adult.source.MASTER) + self.prior["bank"]]
        cases = lesson.build_cases(old_events, "DEV")
        responses = iter(case["expected"] for case in cases["cases"])
        learned = lesson.collect_cases(cases, lambda messages: generation(next(responses), messages), coached=True)
        rows = dict(memory_rows=self.prior["rows"] + self.prior["rows"] + [row for row in new_rows
                     if row["event"] in {self.collection["bank"][index]["event"] for index in (0, 2)}],
                    cue_rows=[{}] * 20, lesson_rows=learned["rows"][:62], new_rows=new_rows)
        recipe = trainer.recipe(material, reduce.SELECTED[parent])
        recipe["new_source_events"] = [row["event"] for row in new_rows[:4]]
        self.write(directory / "TRAINING_ROWS.json", rows)
        self.write(directory / "MASKS.json", masks)
        self.write(directory / "RECIPE.json", recipe)
        (directory / "LOSSES.jsonl").write_text("\n".join(json.dumps(loss) for loss in losses) + "\n")
        provenance = dict(schema=trainer.SCHEMA, material_arm=material, adapter_state_before=parent + "initial",
                          adapter_state_after=parent + material + "final", adapter_files={"adapter_model.safetensors": "receipt-only"},
                          training_artifact_sha256={name: reduce.digest(directory / name)
                                                   for name in ("MASKS.json", "RECIPE.json", "LOSSES.jsonl")})
        self.write(directory / "ADAPTER_PROVENANCE.json", provenance)
        source = dict(parent_arm=parent, selected_source_indexes=reduce.SELECTED[parent],
                      initial_adapter_state_sha256=provenance["adapter_state_before"])
        request = dict(schema=reduce.SCHEMA, parent_arm=parent, material_arm=material, phase="train", arguments={},
                       started_unix=100, entry_sha256=reduce.digest(ROOT / "gpu/astra_selected_reader_repair.py"),
                       parent_present=False, fits=0, model_calls=0)
        summary = reduce.audit_schedule(masks, losses, material, reduce.SELECTED[parent])
        result = dict(request, **{key: value for key, value in provenance.items() if key not in request})
        result.update(summary)
        result.update(summary["budgets"])
        result.update(recipe=recipe, status="COMPLETE", finished_unix=200, frozen_base_unchanged=True, fits=1,
                      trainer_sha256=reduce.digest(ROOT / "gpu/astra_selected_reader_repair_train.py"), source=source,
                      train_seed=0, learning_rate=3e-5, optimizer="FRESH_ADAMW", loss_normalization=reduce.NORMALIZATION,
                      selected_source_indexes=reduce.SELECTED[parent], new_source_events=recipe["new_source_events"],
                      supervised_tokens=summary["actual_supervised_tokens"], original_supervised_tokens=summary["reference_supervised_tokens"],
                      loaded_adapter_state_sha256=provenance["adapter_state_before"])
        for name, value in (("RESULT.json", result), ("REQUEST.json", request), ("INPUTS.json", source)):
            self.write(directory / name, value)
        return directory, result

    def after(self, train_dir, trained):
        directory = train_dir.parent / "after"
        panels, calls = {}, []

        def capture(panel, role, messages, raw):
            response = generation(raw, messages)
            calls.append(dict(panel=panel, role=role, reader_adapter_disabled=panel == "OWN_READER_OFF" and role == "reader",
                              generation=response))
            return response

        banks = dict(OWN_PARAMETRIC=self.collection["bank"], OWN_READER_OFF=self.collection["bank"])
        banks.update({"HELD_TEXT_" + str(index): micro.build_bank(adult.cue_sleep.HELD_MASTER + "-" + str(index)) for index in range(2)})
        for name, bank in banks.items():
            records = []
            for number, fact in enumerate(bank, 1):
                commands = iter(["READ EVENT " + fact["event"], "ROUTE " + fact["port"]] if name == "OWN_PARAMETRIC"
                                else ["ROUTE " + fact["public_ports"][0]])
                transitions = {other["port"]: other["outcome"] for other in bank if other["node"] == fact["node"]}
                episode = controller.run_episode(controller.public_task(fact),
                    lambda messages: capture(name, "actor", messages, next(commands)),
                    lambda address: capture(name, "reader", reduce.adult_reduce.memory_messages(self.runtime, address, 0), micro._event(fact)),
                    transitions.__getitem__)
                records.append(dict(event=fact["event"], episode=episode))
                self.write(directory / "new_task" / (name + "_EPISODE_%02d.json" % number), records[-1])
            panels[name] = dict(denominator=4, reached_goal=4 if name == "OWN_PARAMETRIC" else 2,
                                with_reads=4 if name == "OWN_PARAMETRIC" else 0, second_reads=0, episodes=records)
        for name, wrapper, bank in (("RECALL_W0", 0, self.collection["bank"]), ("RECALL_W8", 8, self.collection["bank"]),
                                    ("UNSEEN_MISS", 8, micro.build_bank(adult.source.MASTER + "-UNSEEN-MISS"))):
            rows = []
            for fact in bank:
                expected = "MISS\n" if name == "UNSEEN_MISS" else micro._event(fact)
                rows.append(dict(event=fact["event"], expected=expected, correct=True, generation=capture(name, "memory_probe",
                    reduce.adult_reduce.memory_messages(self.runtime, fact["event"], wrapper), expected)))
            panels[name] = dict(denominator=4, correct=4, rows=rows)
        self.write(directory / "new_task/PANELS.json", copy.deepcopy(panels))
        for index, call in enumerate(calls, 1):
            self.write(directory / "new_task" / ("CALL_%03d.json" % index), call)
        for wrapper in (0, 8):
            name, rows = "OLD_RECALL_W" + str(wrapper), []
            for number, fact in enumerate(micro.build_bank(adult.source.MASTER) + self.prior["bank"], 1):
                expected = micro._event(fact)
                rows.append(dict(event=fact["event"], expected=expected, correct=True, generation=generation(expected,
                    reduce.adult_reduce.memory_messages(self.runtime, fact["event"], wrapper))))
                self.write(directory / (name + "_%02d.json" % number), rows[-1])
            panels[name] = dict(denominator=8, correct=8, rows=rows)
        cases = lesson.build_cases([dict(event=fact["event"], raw=micro._event(fact)) for fact in self.collection["bank"]], "HELD")
        outputs = iter(case["expected"] for case in cases["cases"])
        held = lesson.collect_cases(cases, lambda messages: generation(next(outputs), messages), coached=False)
        bundle = actual.build_cases(self.collection, panels["OWN_PARAMETRIC"]["episodes"])
        audit = actual.collect_cases(bundle, lambda messages: generation("NONE", messages))
        captures = held["captures"] + audit["captures"]
        for index, record in enumerate(captures):
            self.write(directory / ("CALL_%03d.json" % index), {key: record[key] for key in ("messages", "response", "error")})
        for name, value in (("AFTER_HELD.json", held), ("NEXT_ACTUAL_CASES.json", bundle), ("NEXT_ACTUAL_READERS.json", audit)):
            self.write(directory / name, value)
        request = dict(reduce.read(train_dir / "REQUEST.json"), phase="after", started_unix=201)
        result = dict(request, status="COMPLETE", finished_unix=220, frozen_base_unchanged=True, reader_wrapper=0,
                      source=trained["source"], loaded_adapter_state_sha256=trained["adapter_state_after"],
                      training_result_sha256=reduce.digest(train_dir / "RESULT.json"), panels=panels,
                      model_calls=len(calls) + 16 + len(captures))
        for name, value in (("RESULT.json", result), ("REQUEST.json", request), ("INPUTS.json", result["source"])):
            self.write(directory / name, value)
        return directory, result

    def test_pending_does_not_invent_metrics(self):
        report = reduce.reduce(self.root)
        self.assertEqual(len(report["pending"]), 8)
        self.assertEqual(report["status"], "PARTIAL_EVIDENCE")
        self.assertNotIn("panels", report["cells"]["AUDIT_SFT"]["SELECTED"]["after"])

    def test_four_complete_cells_pair_matches_and_separate_initial_states(self):
        for parent in reduce.PARENTS:
            for material in reduce.MATERIALS:
                self.after(*self.train(parent, material))
        report = self.reduce()
        self.assertEqual(report["status"], "COMPLETE", report)
        self.assertEqual([pair["status"] for pair in report["pairs"].values()], ["MATCH", "MATCH"])
        self.assertNotEqual(report["pairs"]["AUDIT_SFT"]["initial_state"], report["pairs"]["AUDIT_LOSS_OFF"]["initial_state"])
        after = report["cells"]["AUDIT_SFT"]["SELECTED"]["after"]
        self.assertEqual(after["classifier"]["summary"]["overall"], dict(correct=16, denominator=16))
        self.assertEqual(after["next_actual_readers"]["chosen_source_indexes"], [None] * 4)
        self.assertEqual(after["panels"]["OLD_RECALL_W8"]["correct"], 8)
        self.assertEqual(after["model_calls"], after["routing_model_calls"] + 20)
        self.assertEqual(after["total_prompt_tokens"], after["model_calls"] * 10)
        train = report["cells"]["AUDIT_SFT"]["SELECTED"]["train"]
        self.assertEqual(train["seconds"], 100)
        self.assertEqual(train["updates_per_receipt_second"], 1)
        self.assertEqual(after["seconds"], 19)

    def test_invalid_or_zero_timestamps_do_not_invent_rate(self):
        directory, result = self.train()
        for finished in (None, 99, 100):
            result["finished_unix"] = finished
            self.write(directory / "RESULT.json", result)
            train = self.reduce()["cells"]["AUDIT_SFT"]["SELECTED"]["train"]
            self.assertEqual(train["status"], "COMPLETE", train)
            self.assertNotIn("updates_per_receipt_second", train)

    def test_failed_after_keeps_saved_panels_not_complete(self):
        directory, result = self.after(*self.train())
        failure = dict(result, status="FAILED", error="unsupported actual trace", captured_audit_calls=16,
                       model_calls=result["model_calls"] - 20)
        failure.pop("frozen_base_unchanged")
        self.write(directory / "FAILED.json", failure)
        report = self.reduce()
        after = report["cells"]["AUDIT_SFT"]["SELECTED"]["after"]
        self.assertEqual(after["status"], "FAILED")
        self.assertEqual(after["partial_evidence"]["routing"]["panels"]["RECALL_W8"]["correct"], 4)
        self.assertFalse(after["partial_evidence"]["terminal_base_verification"])
        self.assertEqual(report["status"], "FAILED_CELLS")

    def test_inference_failure_retained_before_any_result(self):
        directory = self.root / "AUDIT_SFT_SELECTED/after"
        self.write(directory / "FAILED.json", dict(status="FAILED", error="RuntimeError CUDA", captured_audit_calls=1))
        report = self.reduce()
        self.assertEqual(report["cells"]["AUDIT_SFT"]["SELECTED"]["after"]["failure"]["error"], "RuntimeError CUDA")

    def test_after_wrong_loaded_adapter_is_invalid(self):
        directory, result = self.after(*self.train())
        result["loaded_adapter_state_sha256"] = "other"
        self.write(directory / "RESULT.json", result)
        report = self.reduce()
        self.assertIn("saved_after_reload_join", report["cells"]["AUDIT_SFT"]["SELECTED"]["after"]["error"])

    def test_top_level_call_drift_rejected(self):
        directory, result = self.after(*self.train())
        path = directory / "CALL_000.json"
        call = reduce.read(path)
        call["response"]["raw"] = "wrong"
        self.write(path, call)
        report = self.reduce()
        self.assertIn("audit_call_join", report["cells"]["AUDIT_SFT"]["SELECTED"]["after"]["error"])

    def test_bad_cell_does_not_hide_other_cells(self):
        self.train("AUDIT_LOSS_OFF", "UNIFORM")
        self.write(self.root / "AUDIT_SFT_SELECTED/train/RESULT.json", dict(status="BOGUS"))
        report = self.reduce()
        self.assertEqual(report["cells"]["AUDIT_LOSS_OFF"]["UNIFORM"]["train"]["status"], "COMPLETE")
        self.assertEqual(report["cells"]["AUDIT_SFT"]["SELECTED"]["train"]["status"], "INVALID")

    def test_source_rows_and_loss_hash_tampering_rejected(self):
        directory, result = self.train()
        path = directory / "TRAINING_ROWS.json"
        rows = reduce.read(path)
        rows["new_rows"][0]["event"] = "other"
        self.write(path, rows)
        self.assertIn("source_memory_rows_drift", self.reduce()["cells"]["AUDIT_SFT"]["SELECTED"]["train"]["error"])

    def test_pair_mismatch_not_silently_matched(self):
        cell = dict(status="COMPLETE", initial_state="same", source={}, masks_sha256="m", rows_sha256="r",
                    reference_supervised_tokens=100)
        for key in ("initial_state", "source", "masks_sha256", "rows_sha256", "reference_supervised_tokens"):
            changed = dict(cell, **{key: "different"})
            summary = reduce.pair_summary(dict(SELECTED=dict(train=cell), UNIFORM=dict(train=changed)))
            self.assertEqual(summary["status"], "MISMATCH")
            self.assertEqual(summary["mismatches"], [key])

    def test_actual_pointer_duplicates_independent_of_correctness(self):
        collected, routes = actual_fixture()
        bundle = actual.build_cases(collected, routes)
        record = actual.collect_cases(bundle, lambda messages: generation(collected["bank"][1]["event"], messages))
        summary = reduce.audit_readers(bundle, record, self.runtime)
        self.assertEqual(summary["chosen_source_indexes"], [1] * 8)
        self.assertEqual(len(summary["row_source_indexes"]), 64)
        self.assertLess(summary["summary"]["overall"]["correct"], summary["admitted_selections"])
        record["captures"][0]["messages"][0]["content"] = "changed"
        with self.assertRaises(ValueError):
            reduce.audit_readers(bundle, record, self.runtime)

    def test_no_actual_reads_is_zero_denominator_not_four_misses(self):
        collected, routes = actual_fixture(no_reads=True)
        bundle = actual.build_cases(collected, routes)
        record = actual.collect_cases(bundle, lambda messages: self.fail("no calls"))
        summary = reduce.audit_readers(bundle, record, self.runtime)
        self.assertEqual(summary["summary"]["overall"], dict(correct=0, denominator=0))
        self.assertEqual(summary["chosen_source_indexes"], [])

    def test_text_format_receipt_and_node_errors_do_not_override_strict(self):
        fact = self.collection["bank"][0]
        donor = self.collection["bank"][3]
        expected = micro._event(fact)
        for raw, field in ((expected.rstrip("\n"), None), (expected.replace(fact["receipt"], donor["receipt"]), "receipt"),
                           (expected.replace(fact["node"], donor["node"]), "node")):
            row = dict(event=fact["event"], expected=expected, correct=False, generation=generation(raw))
            error = reduce.text_errors([row], micro)[0]
            self.assertFalse(error["strict_correct"])
            if field is None:
                self.assertTrue(error["format_only"])
            else:
                self.assertEqual(error["different_fields"], [field])


if __name__ == "__main__":
    unittest.main()
