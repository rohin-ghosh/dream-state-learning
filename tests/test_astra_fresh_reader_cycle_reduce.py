"""CPU synthetic captures, including the driver's file-formatting-only evaluator."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from gpu import astra_fresh_reader_cycle as driver
from gpu import astra_selected_reader_repair_train as trainer
from organism_v6 import experienced_event_adult_cycle as adult
from organism_v6 import experienced_event_fresh_reader_cycle as fresh
from organism_v6 import experienced_event_fresh_reader_audit as audit
from organism_v6 import experienced_event_reader_audit_lesson as lesson
from organism_v6 import experienced_event_microloop as micro
from organism_v6 import experienced_event_read_route as controller
from organism_v6 import pcfl_vertical_dev as world
from tests.test_astra_fresh_reader_cycle import FakeEngine
from tests.test_astra_selected_reader_repair_reduce import collection, generation
from tools import astra_fresh_reader_cycle_reduce as reduce


ROOT = Path(__file__).resolve().parents[1]
POINTERS = [1, 0, 1, 0, 3, 2, 3, 2]


def schedule(arm):
    masks = []
    for index in range(210):
        targets = [7] * (1 + index % 3) + [151645]
        masks.append(dict(input_ids=[151644] + targets + [198], labels=[-100] + targets + [-100], target_ids=targets))
    losses = []
    for update in range(1, 101):
        actual, reference = reduce.indexes(update, arm, POINTERS)
        active = sum(len(masks[index]["target_ids"]) for index in actual)
        original = sum(len(masks[index]["target_ids"]) for index in reference)
        scale = active / original
        losses.append(dict(update=update, row_indexes=actual, reference_row_indexes=reference,
                           actual_label_count=active, active_label_count=active, reference_label_count=original,
                           original_label_count=original, loss_scale=scale, actual_mean_loss=0.5, loss=0.5 * scale))
    return masks, losses


class ScheduleTests(unittest.TestCase):
    def test_all_actual_reference_indexes_match_frozen_pure_trainer(self):
        for arm in reduce.ARMS:
            for update in range(1, 101):
                actual, reference = trainer.training_indexes(update, arm, POINTERS, memory_count=96)
                self.assertEqual(reduce.indexes(update, arm, POINTERS), (list(actual), list(reference)))
            summary = reduce.audit_schedule(*schedule(arm), arm, POINTERS)
            self.assertEqual(list(summary["budgets"].values()), [100, 100, 38, 62, 200])
            self.assertEqual(summary["old_bank_presentations"], [36, 32, 32])
            self.assertTrue(all(dose > 0 for dose in summary["new_fact_presentations"]))
        selected = reduce.audit_schedule(*schedule("SELECTED"), "SELECTED", POINTERS)
        uniform = reduce.audit_schedule(*schedule("UNIFORM"), "UNIFORM", POINTERS)
        self.assertEqual(selected["new_fact_presentations"], [48, 56, 48, 48])
        self.assertEqual(uniform["new_fact_presentations"], [50] * 4)
        self.assertEqual(selected["reference_supervised_tokens"], uniform["reference_supervised_tokens"])

    def test_masks_incomplete_updates_nonfinite_scale_and_denominator(self):
        masks, losses = schedule("SELECTED")
        for changed_masks, changed_losses in ((masks[:-1], losses), (masks, losses[:-1])):
            with self.assertRaises(ValueError):
                reduce.audit_schedule(changed_masks, changed_losses, "SELECTED", POINTERS)
        changed = deepcopy(masks)
        changed[0]["labels"][0] = 151644
        with self.assertRaises(ValueError):
            reduce.audit_schedule(changed, losses, "SELECTED", POINTERS)
        for field, value in (("reference_label_count", 1), ("loss_scale", 2), ("loss", float("nan")),
                             ("actual_mean_loss", float("inf")), ("row_indexes", [0, 96, 178, 179])):
            changed = deepcopy(losses)
            changed[0][field] = value
            with self.assertRaises(ValueError):
                reduce.audit_schedule(masks, changed, "SELECTED", POINTERS)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.a1, self.a2 = collection(1), collection(2)
        bank = fresh.build_bank()
        def generate(messages):
            fact = next(fact for fact in bank if fact["port"] in messages[1]["content"])
            return generation("EXPLORE " + fact["node"] + " " + fact["port"] if len(messages) == 2 else micro._event(fact), messages)
        self.collection = fresh.collect(generate)
        self.runtime = SimpleNamespace(root=ROOT, adult=adult, fresh=fresh, audit=audit, lesson=lesson, trainer=trainer,
                                       micro=micro, controller=controller, world=world, source=adult.source, development=adult.cue_sleep)
        self.old_bank = micro.build_bank(adult.source.MASTER) + self.a1["bank"] + self.a2["bank"]
        original_episodes = [dict(fact=fact, exploration=generation("EXPLORE " + fact["node"] + " " + fact["port"]),
                                  event=generation(micro._event(fact))) for fact in self.old_bank[:4]]
        self.memory = micro.compile_rows(self.old_bank[:4], original_episodes, serialization="FINAL_LF_ONLY") + self.a1["rows"] + self.a2["rows"]
        cases = lesson.build_cases([dict(event=fact["event"], raw=micro._event(fact)) for fact in self.old_bank[:8]], "DEV")
        outputs = iter(case["expected"] for case in cases["cases"])
        self.lessons = lesson.collect_cases(cases, lambda messages: generation(next(outputs), messages), coached=True)["rows"][:62]
        self.source = dict(initial_adapter_state_sha256="parent", master=fresh.MASTER,
                           fresh_helper_sha256=reduce.digest(ROOT / "organism_v6/experienced_event_fresh_reader_cycle.py"),
                           prior_event_ids=[fact["event"] for fact in self.old_bank],
                           memory_rows_sha256=sha256(reduce.adult.canonical(self.memory) + b"\n").hexdigest())

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def receipt(self, directory, phase, arm=None, **changes):
        request = dict(schema=reduce.SCHEMA, phase=phase, arm=arm, arguments={}, started_unix=100, fits=0,
                       model_calls=0, parent_present=False, entry_sha256=reduce.digest(ROOT / "gpu/astra_fresh_reader_cycle.py"))
        result = dict(request, status="COMPLETE", finished_unix=200, source=self.source, frozen_base_unchanged=True,
                      loaded_adapter_state_sha256="parent", audit_policy=reduce.AUDIT_POLICY,
                      audit_helper_sha256=reduce.digest(ROOT / "organism_v6/experienced_event_fresh_reader_audit.py"))
        result.update(changes)
        for name, value in (("REQUEST.json", request), ("INPUTS.json", self.source), ("RESULT.json", result)):
            self.write(directory / name, value)
        return result

    def collect(self):
        directory = self.root / "collect"
        self.write(directory / "COLLECTION.json", self.collection)
        for index, capture in enumerate(self.collection["captures"]):
            self.write(directory / ("CALL_%03d.json" % index), {key: capture[key] for key in ("messages", "response", "error")})
        return self.receipt(directory, "collect", collection_sha256=reduce.digest(directory / "COLLECTION.json"),
                            accepted_events=4, model_calls=8)

    def readout(self, phase="before", arm=None, invalid=False):
        directory = self.root / phase if arm is None else self.root / arm / phase
        directory.mkdir(parents=True, exist_ok=True)
        inputs = dict(old_bank=self.old_bank, old_episodes=[dict(fact=fact, event=generation(micro._event(fact))) for fact in self.old_bank])
        engine = FakeEngine(inputs, self.collection)
        generated = engine.generate
        def generate(messages, **kwargs):
            response = generated(messages, **kwargs)
            if invalid and messages[0]["content"] == controller.PUBLIC_SYSTEM and response["raw"].startswith("ROUTE"):
                response["raw"] = "ROUTE " + self.old_bank[0]["port"]
            response.update(prompt_tokens=10, token_ids=[7, 151645])
            return response
        engine.generate = generate
        evaluated = driver.evaluate(engine, self.collection, inputs, directory)
        held_cases = lesson.build_cases([dict(event=fact["event"], raw=micro._event(fact)) for fact in self.a2["bank"]], "HELD")
        outputs = iter(case["expected"] for case in held_cases["cases"])
        held = lesson.collect_cases(held_cases, lambda messages: generation(next(outputs), messages), coached=False)
        cases = audit.build_cases(self.collection, evaluated["panels"]["OWN_PARAMETRIC"]["episodes"])
        choices = iter(POINTERS)
        audited = audit.collect_audit(cases, lambda messages: generation(self.collection["bank"][next(choices)]["event"], messages))
        for name, value in (("HELD_AUDIT.json", held), ("ACTUAL_CASES.json", cases), ("ACTUAL_READERS.json", audited)):
            self.write(directory / name, value)
        captures = held["captures"] + audited["captures"]
        for index, capture in enumerate(captures):
            self.write(directory / ("CALL_%03d.json" % index), {key: capture[key] for key in ("messages", "response", "error")})
        evaluated["model_calls"] += len(captures)
        changes = dict(collection_result_sha256=reduce.digest(self.root / "collect/RESULT.json"), **evaluated)
        if arm:
            changes.update(before_result_sha256=reduce.digest(self.root / "before/RESULT.json"),
                           training_result_sha256=reduce.digest(self.root / arm / "train/RESULT.json"),
                           loaded_adapter_state_sha256=arm + "final")
        return self.receipt(directory, phase, arm, **changes)

    def train(self, arm):
        directory = self.root / arm / "train"
        masks, losses = schedule(arm)
        rows = dict(memory_rows=self.memory, cue_rows=[{}] * 20, lesson_rows=self.lessons, new_rows=self.collection["rows"])
        config = trainer.recipe(arm, POINTERS, memory_count=96)
        config["new_source_events"] = [fact["event"] for fact in self.collection["bank"]]
        for name, value in (("TRAINING_ROWS.json", rows), ("RECIPE.json", config), ("MASKS.json", masks)):
            self.write(directory / name, value)
        (directory / "LOSSES.jsonl").write_text("\n".join(json.dumps(loss) for loss in losses) + "\n")
        provenance = dict(schema=trainer.SCHEMA, material_arm=arm, adapter_state_before="parent", adapter_state_after=arm + "final",
                          training_artifact_sha256={name: reduce.digest(directory / name) for name in ("MASKS.json", "RECIPE.json", "LOSSES.jsonl")})
        self.write(directory / "ADAPTER_PROVENANCE.json", provenance)
        result = dict(provenance)
        result.pop("schema")
        summary = reduce.audit_schedule(masks, losses, arm, POINTERS)
        result.update(summary)
        result.update(summary["budgets"])
        result.update(recipe=config, fits=1, selected_source_indexes=POINTERS,
                      train_seed=0, learning_rate=3e-5, optimizer="FRESH_ADAMW", new_source_events=config["new_source_events"],
                      supervised_tokens=summary["actual_supervised_tokens"], original_supervised_tokens=summary["reference_supervised_tokens"],
                      loss_normalization=reduce.repair.NORMALIZATION,
                      trainer_sha256=reduce.digest(ROOT / "gpu/astra_selected_reader_repair_train.py"),
                      collection_result_sha256=reduce.digest(self.root / "collect/RESULT.json"),
                      before_result_sha256=reduce.digest(self.root / "before/RESULT.json"))
        return self.receipt(directory, "train", arm, **result)

    def reduce(self):
        return reduce.reduce(self.root, self.runtime, self.a1, self.a2)

    def test_complete_six_stages_pair_twelve_old_and_A2_classifier(self):
        self.collect()
        self.readout(invalid=True)
        for arm in reduce.ARMS:
            self.train(arm)
            self.readout("after", arm)
        report = self.reduce()
        self.assertEqual(report["status"], "COMPLETE", {key: stage.get("error") for key, stage in report["stages"].items()})
        self.assertEqual(report["pair"]["status"], "MATCH")
        self.assertEqual(len(report["stages"]), 6)
        self.assertEqual(report["before_pointers"], POINTERS)
        self.assertTrue(report["both_materials_cover_all_four"])
        before = report["stages"]["before"]
        self.assertEqual(before["actual_audit"]["invalid_route_count"], 4)
        self.assertEqual(before["actual_audit"]["actual_reader_calls"], 8)
        self.assertEqual(before["panels"]["OWN_PARAMETRIC"]["reached_goal"], 0)
        self.assertEqual(before["panels"]["OLD_RECALL_W8"]["correct"], 12)
        self.assertEqual(before["classifier"]["bank"], "A2_HELD_NOT_A3")
        self.assertEqual(before["classifier"]["summary"]["overall"], dict(correct=16, denominator=16))
        self.assertEqual(before["model_calls"], before["routing_model_calls"] + 24)
        self.assertEqual(before["total_prompt_tokens"], 10 * before["model_calls"])
        self.assertEqual(report["stages"]["SELECTED/train"]["updates_per_receipt_second"], 1)

    def test_pending_no_fabricated_measurements(self):
        report = reduce.reduce(self.root)
        self.assertEqual(report["status"], "PARTIAL_EVIDENCE")
        self.assertEqual(len(report["pending"]), 6)
        self.assertNotIn("panels", report["stages"]["before"])

    def test_failed_before_preserves_replayable_invalid_routes_and_failure(self):
        self.collect()
        result = self.readout(invalid=True)
        failure = dict(result, status="FAILED", error="post-panel failure")
        failure.pop("frozen_base_unchanged")
        self.write(self.root / "before/FAILED.json", failure)
        report = self.reduce()
        before = report["stages"]["before"]
        self.assertEqual(before["status"], "FAILED")
        self.assertEqual(before["partial_routing"]["panels"]["OWN_PARAMETRIC"]["reached_goal"], 0)
        self.assertTrue(before["partial_only_no_terminal_base_verification"])

    def test_source_state_or_receipt_drift_is_invalid(self):
        self.collect()
        result = self.readout()
        result["loaded_adapter_state_sha256"] = "other"
        self.write(self.root / "before/RESULT.json", result)
        self.assertIn("before_initial_actor", self.reduce()["stages"]["before"]["error"])

    def test_actual_v2_case_drift_and_twelve_fact_missing_file(self):
        self.collect()
        self.readout()
        path = self.root / "before/ACTUAL_CASES.json"
        cases = reduce.read(path)
        cases["cases"][0]["messages"][0]["content"] = "changed"
        self.write(path, cases)
        self.assertIn("actual_v2_case_join", self.reduce()["stages"]["before"]["error"])
        (self.root / "before/OLD_RECALL_W8_12.json").unlink()
        self.assertEqual(self.reduce()["stages"]["before"]["status"], "INVALID")

    def test_read_only_collection_directory_symlink(self):
        self.collect()
        moved = self.root / "original_collect"
        (self.root / "collect").rename(moved)
        (self.root / "collect").symlink_to(moved, target_is_directory=True)
        self.assertEqual(self.reduce()["stages"]["collect"]["status"], "COMPLETE")

    def test_failed_collection_replays_without_promoting_partial_material(self):
        def fail(messages):
            raise RuntimeError("captured CUDA error")
        self.collection = fresh.collect(fail)
        self.write(self.root / "collect/COLLECTION.json", self.collection)
        self.write(self.root / "collect/FAILED.json", dict(status="FAILED", error="incomplete_collection", captured_calls=4))
        stage = self.reduce()["stages"]["collect"]
        self.assertEqual(stage["status"], "FAILED")
        self.assertEqual(stage["failed_collection"]["replayed_rows"], 0)
        self.assertEqual(stage["failed_collection"]["record"]["infrastructure_failures"], 4)

    def test_training_parent_source_and_mask_hash_drift_rejected(self):
        self.collect()
        self.readout()
        self.train("SELECTED")
        result_path = self.root / "SELECTED/train/RESULT.json"
        original = reduce.read(result_path)
        changed = deepcopy(original)
        changed["before_result_sha256"] = "wrong"
        self.write(result_path, changed)
        self.assertIn("before_receipt_join", self.reduce()["stages"]["SELECTED/train"]["error"])
        self.write(result_path, original)
        masks_path = self.root / "SELECTED/train/MASKS.json"
        masks = reduce.read(masks_path)
        masks[0]["target_ids"][0] = 99
        self.write(masks_path, masks)
        self.assertIn("training_hash_drift", self.reduce()["stages"]["SELECTED/train"]["error"])


if __name__ == "__main__":
    unittest.main()
