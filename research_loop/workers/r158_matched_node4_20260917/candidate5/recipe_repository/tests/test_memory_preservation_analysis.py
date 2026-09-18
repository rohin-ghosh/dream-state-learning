"""Synthetic CPU capsules with patched input pins; never evidence of real fits."""
import contextlib
import copy
import io
import json
import math
from pathlib import Path
import random
import shutil
import tempfile
import unittest
from unittest import mock

from organism_v6 import memory_dose as native
from organism_v6 import memory_preservation as producer
from organism_v6 import memory_preservation_analysis as analysis

try:
    import torch
except ImportError:
    torch = None


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


@unittest.skipIf(torch is None, "Use the CPU PyTorch test environment to validate captured tensors")
class PreservationAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.temporary = tempfile.TemporaryDirectory()
        cls.template = Path(cls.temporary.name)
        cls.contents = {"manifest.json": {"seed": 1}, "distractor.json": {"text": "Mock distractor."}}
        taken = set()
        for index in range(3):
            owners = native.make_owner_ids(random.Random(92 + index), 64, taken)
            cls.contents[f"banks/bank{index}.json"] = native.generate_bank(index, 92, owners, {}, {}, taken)
        cls.contents[producer.CORPUS] = dict(corpus=[dict(context="", target="fixture only", weight=1.0,
            mask_context=False, chat=False, kind="filler")], sha="fixture-corpus", items_sha="fixture-items")
        cls.inventory = {"config.json": "a" * 64, "model.safetensors": "b" * 64, "tokenizer.json": "c" * 64}
        cls.token_rows = [[1, 2, 3, 4, 5, 6, 7, 8] for index in range(48)]
        zero = cls.template / "zero"
        for name, content in cls.contents.items():
            write(zero / name, content)
        cls.input_hashes = {name: producer.digest(zero / name) for name in cls.contents}
        with mock.patch.object(producer, "INPUT_HASHES", cls.input_hashes):
            anchors = producer.make_anchors(cls.contents)
        write(zero / "anchors.json", anchors)
        cls.anchor_hash = producer.digest(zero / "anchors.json")
        cues = native.build_cues(cls.contents["banks/bank0.json"], "Mock distractor.", adjacent_subset=4)
        scores = native.score_cues(native.MockScorer(seed=92), cues, [1.0])
        cls.rows = []
        for cue, off, on in zip(cues, scores["off"], scores["on"][1.0]):
            row = {key: value for key, value in cue.items() if key not in ("prompt", "candidates")}
            for side, score in (("OFF", off), ("ON", on)):
                row[side] = dict(p_raw={key: round(value, 7) for key, value in score["p_raw"].items()},
                                 logp={key: round(value, 5) for key, value in score["logp"].items()}, mass=round(score["mass"], 7))
                if "p_abstain" in score:
                    row[side]["p_abstain"] = round(score["p_abstain"], 7)
            cls.rows.append(row)
        for label, strength in (("zero", 0.0), ("positive", 0.1)):
            root = cls.template / label
            for name, content in cls.contents.items():
                write(root / name, content)
            write(root / "anchors.json", anchors)
            remote = "/remote/" + label
            plan = dict(status="PREPARED_NOT_TRAINED", root=remote, original="/remote/original",
                        model="/remote/model", source="/remote/source290a9ea0", model_files=cls.inventory,
                        coefficient=strength, source_files=analysis.SOURCE_FILES, anchors_sha256=cls.anchor_hash,
                        worker_cap_seconds=3600, clean_lineage=False, model_authentication="UNRESOLVED_LOCAL_HASHES_ONLY",
                        token_preflight=dict(memory_order_sha256=analysis.ORDER_SHA, anchor_input_ids=cls.token_rows,
                                             input_tokens_per_epoch=249995, supervised_tokens_per_epoch=237071,
                                             truncated_items=0, boundary_straddles=0))
            write(root / "plan.json", plan)
            setup = dict(producer.BOUNDARY, recipe=producer.RECIPE, coefficient=strength,
                         source_inputs=cls.input_hashes, native_source_sha256=producer.SOURCE_SHA,
                         implementation_sha256=analysis.SOURCE_FILES["organism_v6/memory_preservation.py"],
                         anchors_sha256=cls.anchor_hash, model_files=cls.inventory, model_path=plan["model"],
                         seed=2, rank=8, lr=1e-4, epochs=3, batch_size=4, expected_steps=9693)
            write(root / analysis.ADAPTER / "setup.json", setup)
            cache = None
            if strength:
                cache_root = root / "off_cache"
                cache_root.mkdir()
                torch.save(torch.zeros(48, 13), cache_root / "off_logits.pt")
                cache = dict(producer.BOUNDARY, model_files=cls.inventory, model_path=plan["model"],
                             anchors_sha256=cls.anchor_hash, input_ids=cls.token_rows,
                             native_source_sha256=producer.SOURCE_SHA,
                             implementation_sha256=analysis.SOURCE_FILES["organism_v6/memory_preservation.py"],
                             shape=[48, 13], dtype="torch.float32", model_dtype="torch.bfloat16", adapter=None,
                             temperature=1.0, position="last input token", seconds=5.0, torch_version="mock-cpu",
                             logits_sha256=producer.digest(cache_root / "off_logits.pt"))
                write(cache_root / "cache.json", cache)
            ce_sum = kl_sum = 0.0
            with (root / analysis.ADAPTER / "losses.jsonl").open("w") as stream:
                for index in range(9693):
                    tokens = 78 if index % 3231 < 1208 else 77
                    kl = 0.2 if strength else None
                    row = dict(step=index + 1, epoch=index // 3231, item_offset=(index % 3231) * 4,
                               anchor_index=index % 48 if strength else None, ce=1.0, kl=kl,
                               objective=1.0 + strength * (kl or 0.0), tokens=tokens, supervised_tokens=tokens - 4, seconds=0.001)
                    stream.write(json.dumps(row) + "\n")
                    ce_sum += row["ce"]
                    kl_sum += kl or 0.0
            visits = [9693 // 48 + int(index < 9693 % 48) for index in range(48)] if strength else [0] * 48
            fit = dict(analysis.RECIPE_FIELDS)
            fit.update(producer.BOUNDARY)
            fit.update(recipe=producer.RECIPE, native_ce_recipe="memory_dose_v1 (mirrors train_adapter.py v1)",
                       coefficient=strength, ce_coefficient=1.0, corpus_sha="fixture-corpus", items_sha="fixture-items",
                       model="Qwen/Qwen2.5-7B-Instruct", model_path=plan["model"], source_inputs=cls.input_hashes,
                       native_source_sha256=producer.SOURCE_SHA,
                       implementation_sha256=analysis.SOURCE_FILES["organism_v6/memory_preservation.py"],
                       anchors_sha256=cls.anchor_hash, memory_order_sha256=analysis.ORDER_SHA,
                       final_loss=1.0, final_kl=0.2 if strength else None, final_objective=1.02 if strength else 1.0,
                       mean_ce=ce_sum / 9693, mean_kl=kl_sum / 9693 if strength else None,
                       wall_seconds=30.0, throughput=dict(grad_checkpoint=False, sec_per_step=30 / 9693),
                       anchor_visits=visits, anchor_forward_count=sum(visits), anchor_distribution_positions=sum(visits),
                       anchor_input_tokens=sum(visits) * 8, cache_used=bool(strength), cache_metadata=cache,
                       kl_dtype="torch.float32" if strength else None, model_dtype="torch.bfloat16", trainable_dtypes=["torch.float32"],
                       trainable_names=["base.q_proj.lora_A.default.weight", "base.q_proj.lora_B.default.weight"],
                       initial_lora_sha256="d" * 64, torch_version="mock-cpu", losses_sha256=producer.digest(root / analysis.ADAPTER / "losses.jsonl"))
            write(root / analysis.ADAPTER / "train_meta.json", fit)
            (root / analysis.ADAPTER / "DONE").write_text("ok\n")
            evaluation = dict(analysis.shared.EVAL_META, cues=copy.deepcopy(cls.rows), seconds=2.0,
                              adapter=remote + "/" + analysis.ADAPTER, adapter_arg=remote + "/" + analysis.ADAPTER,
                              adapter_meta={key: fit[key] for key in analysis.shared.ADAPTER_FIELDS}, abstain_check=dict(ok=True, fixture=True))
            write(root / analysis.EVAL, evaluation)
            write(root / "report/report.json", cls.report(evaluation))

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @classmethod
    def report(cls, evaluation, banks=None):
        summary = native.summarize_eval(evaluation, cls.contents["banks/bank0.json"])
        gates = native.evaluate_gates(summary, seed=0)
        dose = summary["per_dose"][16]
        return dict(gates_thresholds=json.loads(json.dumps(native.GATES)), n_evals=len(banks or [0]),
                    evals_used={"F_r16k16__across__8__1.0__4__0": analysis.TAG},
                    results={analysis.KEY: dict(banks=banks or [0], ref_sleep=4, sleeps=[4], gates=gates, frame=gates,
                        per_bank={"0": dict(gates=gates)}, headline={**{key: dose[key] for key in ("frame_p_off", "frame_p_on", "frame_d_p", "I_d_frame")},
                                                                    "frame_spill": summary["controls"]["frame_spill"]})})

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(self.template / "zero", self.root / "zero")
        shutil.copytree(self.template / "positive", self.root / "positive")
        self.zero, self.positive = self.root / "zero", self.root / "positive"
        for module, name, value in ((producer, "INPUT_HASHES", self.input_hashes),
                                     (analysis, "MODEL_INVENTORY_SHA", producer.object_hash(self.inventory)),
                                     (analysis, "ANCHORS_SHA", self.anchor_hash),
                                     (analysis, "ANCHOR_TOKENS_SHA", producer.object_hash(self.token_rows)),
                                     (analysis, "VOCAB_SIZE", 13)):
            patcher = mock.patch.object(module, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def change(self, root, name, operation):
        value = producer.load(root / name)
        operation(value)
        write(root / name, value)

    def compare(self, historical=None):
        return analysis.compare_runs(self.zero, self.positive, historical)

    def assert_invalid(self, result, text=None):
        self.assertFalse(result["valid"], result)
        self.assertNotIn("paired_effect", result)
        if text:
            self.assertIn(text, json.dumps(result))

    def test_complete_pair_negative_gates_are_valid_and_native(self):
        result = self.compare()
        self.assertTrue(result["valid"], result)
        self.assertFalse(result["lambda0"]["metrics"]["G9"]["passed"])
        self.assertTrue(result["comparison"]["off_exact_at_serialized_precision"])
        self.assertEqual(result["paired_effect"]["dose16"]["I_d_frame"], 0)
        self.assertEqual(result["paired_effect"]["paired_owner_I_d_change"]["n"], 16)
        self.assertEqual(result["lambda01"]["fit"]["anchor_forward_count"], 9693)
        self.assertEqual(result["lambda01"]["costs"]["captured_stage_seconds"], 37)
        self.assertEqual(result["lambda0"]["costs"]["captured_stage_seconds"], 32)
        self.assertFalse(result["lambda0"]["adapter_weights"]["present"])

    def test_changed_on_distribution_has_native_paired_effect_not_off_drift(self):
        evaluation = producer.load(self.positive / analysis.EVAL)
        row = next(row for row in evaluation["cues"] if row["kind"] == "frame" and row["dose"] == 16)
        row["ON"]["p_raw"][row["a"]] *= 1.5
        row["ON"]["mass"] = sum(row["ON"]["p_raw"].values())
        row["ON"]["logp"] = {key: math.log(value) for key, value in row["ON"]["p_raw"].items()}
        write(self.positive / analysis.EVAL, evaluation)
        write(self.positive / "report/report.json", self.report(evaluation))
        result = self.compare()
        self.assertTrue(result["valid"], result)
        delta = result["paired_effect"]["dose16"]["I_d_frame"]
        self.assertGreater(delta, 0)
        self.assertAlmostEqual(delta, result["lambda01"]["metrics"]["G9"]["value"] - result["lambda0"]["metrics"]["G9"]["value"])
        self.assertAlmostEqual(delta, result["paired_effect"]["paired_owner_I_d_change"]["mean"])
        self.assertEqual(result["comparison"]["off_changed_count"], 0)

    def test_current_plan_model_source_order_and_anchor_refusals(self):
        original = producer.load(self.positive / "plan.json")
        mutations = [lambda value: value.update(coefficient=0.0),
                     lambda value: value["model_files"].update(**{"model.safetensors": "0" * 64}),
                     lambda value: value["source_files"].update(**{"organism_v6/memory_dose.py": "0" * 64}),
                     lambda value: value["token_preflight"].update(memory_order_sha256="0" * 64),
                     lambda value: value["token_preflight"]["anchor_input_ids"][0].append(9),
                     lambda value: value.update(anchors_sha256="0" * 64)]
        for operation in mutations:
            with self.subTest(operation=operation):
                value = copy.deepcopy(original)
                operation(value)
                write(self.positive / "plan.json", value)
                self.assert_invalid(self.compare())

    def test_fit_recipe_counts_visits_model_and_identity_refusals(self):
        original = producer.load(self.positive / analysis.ADAPTER / "train_meta.json")
        mutations = dict(steps=9692, supervised_tokens=422925, lr=3e-5, recipe="mask", cache_used=False,
                         anchor_visits=[0] * 48, anchor_input_tokens=1, mean_ce=2.0,
                         corpus_sha="wrong", model_path="/different/model", trainable_names=["base.weight"])
        for key, value in mutations.items():
            with self.subTest(key=key):
                write(self.positive / analysis.ADAPTER / "train_meta.json", dict(original, **{key: value}))
                self.assert_invalid(self.compare())

    def test_initialization_or_dtype_pair_drift_not_a_matched_effect(self):
        self.change(self.positive, analysis.ADAPTER + "/train_meta.json", lambda value: value.update(initial_lora_sha256="e" * 64))
        result = self.compare()
        self.assert_invalid(result)
        self.assertFalse(result["matched_fit_controls"]["initial_lora_sha256"])

    def test_loss_truncation_and_order_or_nonfinite_even_if_rehashed(self):
        path = self.positive / analysis.ADAPTER / "losses.jsonl"
        original = path.read_text().splitlines()
        for variant in ("missing", "order", "nan", "objective"):
            with self.subTest(variant=variant):
                lines = list(original)
                if variant == "missing":
                    lines.pop()
                else:
                    row = json.loads(lines[0])
                    row.update({"order": {"anchor_index": 1}, "nan": {"kl": float("nan")}, "objective": {"objective": 9.0}}[variant])
                    lines[0] = json.dumps(row)
                path.write_text("\n".join(lines) + "\n")
                self.change(self.positive, analysis.ADAPTER + "/train_meta.json", lambda value: value.update(losses_sha256=producer.digest(path)))
                self.assert_invalid(self.compare())

    def test_cache_missing_corrupt_or_unbound_metadata_refused(self):
        path = self.positive / "off_cache/off_logits.pt"
        original = path.read_bytes()
        path.write_bytes(original + b"tampered")
        self.assert_invalid(self.compare(), "cache hash")
        path.unlink()
        self.assert_invalid(self.compare(), "FileNotFoundError")

    def test_lambda0_must_skip_cache(self):
        (self.zero / "off_cache").mkdir()
        self.assert_invalid(self.compare(), "unexpected cache")

    def test_cue_missing_duplicate_off_drift_and_order(self):
        original = producer.load(self.positive / analysis.EVAL)
        for operation in (lambda value: value["cues"].pop(),
                          lambda value: value["cues"].__setitem__(1, value["cues"][0]),
                          lambda value: value["cues"].reverse()):
            with self.subTest(operation=operation):
                value = copy.deepcopy(original)
                operation(value)
                write(self.positive / analysis.EVAL, value)
                self.assert_invalid(self.compare())
        value = copy.deepcopy(original)
        value["cues"][0]["OFF"]["mass"] += 1e-7
        write(self.positive / analysis.EVAL, value)
        result = self.compare()
        self.assert_invalid(result)
        self.assertEqual(result["comparison"]["off_changed_count"], 1)
        self.assertAlmostEqual(result["comparison"]["off_max_abs"]["mass"], 1e-7)

    def test_report_g11_threshold_and_native_gate_disagreements_refused(self):
        original = producer.load(self.positive / "report/report.json")
        for operation in (lambda value: value["gates_thresholds"].update(abstain_min=0.01),
                          lambda value: value["results"][analysis.KEY]["per_bank"]["0"]["gates"]["G11_abstention"].update(passed=True),
                          lambda value: value["results"][analysis.KEY]["headline"].update(frame_p_on=0.99),
                          lambda value: value.update(n_evals=2)):
            with self.subTest(operation=operation):
                value = copy.deepcopy(original)
                operation(value)
                write(self.positive / "report/report.json", value)
                self.assert_invalid(self.compare(), "report")

    def make_historical(self):
        root = self.root / "historical"
        shutil.copytree(self.zero, root)
        fit = producer.load(root / analysis.ADAPTER / "train_meta.json")
        fit["recipe"] = "memory_dose_v1 (mirrors train_adapter.py v1)"
        fit["model"] = "/older/local/model/location"
        write(root / analysis.ADAPTER / "train_meta.json", fit)
        write(root / "seed_run_receipt.json", dict(destination_run="/remote/historical"))
        evaluation = producer.load(root / analysis.EVAL)
        evaluation.update(adapter="/remote/historical/" + analysis.ADAPTER, adapter_arg="/remote/historical/" + analysis.ADAPTER,
                          model="/older/local/model/location")
        evaluation["adapter_meta"]["recipe"] = fit["recipe"]
        write(root / analysis.EVAL, evaluation)
        write(root / "report/report.json", self.report(evaluation, [0, 1, 2]))
        return root

    def test_historical_paths_and_three_bank_report_are_descriptive_bridge(self):
        root = self.make_historical()
        result = self.compare(root)
        self.assertTrue(result["valid"], result)
        bridge = result["historical_bridge"]
        self.assertTrue(bridge["valid_artifacts"], bridge)
        self.assertTrue(bridge["comparison"]["off_exact_at_serialized_precision"])
        self.assertTrue(bridge["report"]["pooled_ignored"])
        self.assertIn("model", bridge["fit_metadata_differences"])
        self.assertIn("unavailable", bridge["historical_weight_inventory"])
        self.assertEqual(bridge["current_lambda0_minus_historical"]["direction"], "current lambda0 minus historical native CE")

    def test_historical_inventory_comparison_uses_file_hashes_not_names(self):
        root = self.make_historical()
        write(root / "local_base_pins.json", dict(model_path="a third location", files=self.inventory))
        result = self.compare(root)
        self.assertTrue(result["historical_bridge"]["historical_weight_inventory"]["recorded_current_files_match"])
        self.change(root, "local_base_pins.json", lambda value: value["files"].update(**{"model.safetensors": "e" * 64}))
        result = self.compare(root)
        self.assertFalse(result["historical_bridge"]["historical_weight_inventory"]["recorded_current_files_match"])
        self.assertTrue(result["valid"])

    def test_unavailable_historical_does_not_invalidate_current_pair(self):
        result = self.compare(self.root / "missing-history")
        self.assertTrue(result["valid"], result)
        self.assertFalse(result["historical_bridge"]["valid_artifacts"])

    def test_remote_adapter_paths_must_not_be_rewritten_for_capture(self):
        self.change(self.positive, analysis.EVAL, lambda value: value.update(adapter=str(self.positive / analysis.ADAPTER)))
        self.assert_invalid(self.compare(), "remote adapter")

    def test_cli_exclusive_output_no_input_changes_and_failure_json(self):
        before = {str(path): producer.digest(path) for path in self.root.rglob("*") if path.is_file()}
        output = self.root / "reduction.json"
        args = [str(self.zero), str(self.positive), "--output-new", str(output)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(analysis.main(args), 0)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            analysis.main(args)
        for name, checksum in before.items():
            self.assertEqual(producer.digest(name), checksum)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            analysis.main([str(self.zero), str(self.positive), "--output-new", str(self.zero / "bad.json")])
        (self.positive / "report/report.json").unlink()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(analysis.main([str(self.zero), str(self.positive), "--output-new", str(self.root / "failed.json")]), 1)
        self.assert_invalid(producer.load(self.root / "failed.json"))

    def test_source_hash_change_is_not_silently_accepted(self):
        with mock.patch.object(analysis, "HELPER_SHA", "0" * 64):
            self.assert_invalid(self.compare(), "helper source")

    def test_retry_implementation_requires_explicit_hash_and_reports_difference(self):
        repair = analysis.READER_PRODUCER_SHA
        self.change(self.positive, "plan.json", lambda value: value["source_files"].update(**{"organism_v6/memory_preservation.py": repair}))
        for name in ("train_meta.json", "setup.json"):
            self.change(self.positive, analysis.ADAPTER + "/" + name, lambda value: value.update(implementation_sha256=repair))
        self.assert_invalid(self.compare(), "repair hash must be explicit")
        result = analysis.compare_runs(self.zero, self.positive, positive_implementation=repair)
        self.assertTrue(result["valid"], result)
        self.assertFalse(result["implementation_provenance"]["equal"])
        self.assertFalse(result["lambda01"]["cache"]["implementation_matches_fit"])

    def test_full_vocabulary_float64_cache_validation_does_not_rewrite_float32(self):
        path = self.root / "full-vocabulary.pt"
        vocabulary = 152064
        tensor = torch.linspace(-19.875, 16.5, vocabulary).repeat(48, 1).float()
        torch.save(tensor, path)
        checksum = producer.digest(path)
        result = analysis.validate_cache_tensor(path, checksum, vocabulary)
        self.assertLessEqual(result["normalization_max_error"], 1e-10)
        self.assertEqual(producer.digest(path), checksum)
        self.assertEqual(torch.load(path, weights_only=True).dtype, torch.float32)


if __name__ == "__main__":
    unittest.main()
