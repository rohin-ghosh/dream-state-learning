"""Synthetic CPU formation plus tokenizer fixtures; no training or GPU use."""
from contextlib import contextmanager
from dataclasses import replace
import json
from pathlib import Path
import re
import shutil
import sys
import unittest
from unittest.mock import patch

from organism_v6 import parent_material_diagnostic as formation
from organism_v6 import parent_material_write as writer
from organism_v6 import preschool_reasoning as policy
import test_parent_material_diagnostic as fixtures


class EndingGym(fixtures.FixtureGym):
    def offers_end_token(self):
        return True


class ShortDiagnosticDriver(formation.DiagnosticDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.st.budget_ticks = 1


class MaterialModel(fixtures.FixtureModel):
    def __init__(self, path, unique=128, teacher=False):
        super().__init__(path)
        self.counter = 0
        self.unique = unique
        self.teacher = teacher

    def batch(self, prompts, max_tokens=400, seeds=None, temperature=.7):
        outputs = []
        for prompt in prompts:
            if prompt.endswith("NOTE_AFTER:"):
                action = json.loads(re.findall(r"^ACT submitted: (.+)$", prompt, re.M)[-1])
                outputs.append(policy.LESSON_EXAMPLES[0] if self.teacher else
                               f'I submitted "{action}"; the score was 0.50.')
            else:
                actions = []
                for _ in range(2):
                    action = "blue amber" if self.teacher else f"child-{self.counter % self.unique:03d}"
                    self.counter += 1
                    actions.append("ACT: " + action)
                outputs.append("\n".join([*actions, "DONE: yes"]))
        return outputs


class OffsetTokenizer:
    pad_token = None
    eos_token = "<eos>"

    def __call__(self, texts, *, padding, truncation, return_offsets_mapping, return_attention_mask):
        assert padding and not truncation and return_offsets_mapping and return_attention_mask
        width = max(map(len, texts))
        result = dict(input_ids=[], attention_mask=[], offset_mapping=[])
        for text in texts:
            length = len(text)
            result["input_ids"].append([ord(char) + 1 for char in text] + [0] * (width - length))
            result["attention_mask"].append([1] * length + [0] * (width - length))
            result["offset_mapping"].append([(index, index + 1) for index in range(length)]
                                            + [(0, 0)] * (width - length))
        return result


class ParentMaterialWriteTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.DiagnosticTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.formation = self.make_formation("formation")
        self.output = self.root / "prep"
        self.adapter = self.root / "adapter"
        self.log = self.root / "trainer.log"

    def make_formation(self, name, unique=128, teacher=False, *, schedule_seed=6101, generation_seed=7101):
        model = MaterialModel(str(self.fixture.model_dir), unique=unique, teacher=teacher)

        @contextmanager
        def backend(model_path):
            self.assertEqual(model_path, str(self.fixture.model_dir))
            yield model

        config = replace(self.fixture.config, out=str(self.root / name),
                         schedule_seed=schedule_seed, generation_seed=generation_seed)
        with patch.object(formation, "DiagnosticDriver", ShortDiagnosticDriver):
            formation.run(config, gym=EndingGym(), backend_factory=backend)
        return Path(config.out)

    def prepare(self, **kwargs):
        with patch.object(writer, "_load_tokenizer", return_value=OffsetTokenizer()) as load:
            result = writer.prepare_write(kwargs.pop("formation_out", self.formation),
                kwargs.pop("output_dir", self.output), adapter_dir=kwargs.pop("adapter_dir", self.adapter),
                trainer_log=kwargs.pop("trainer_log", self.log), **kwargs)
        return result, load

    @staticmethod
    def read(path):
        return json.loads(path.read_bytes())

    @staticmethod
    def rewrite(path, value):
        path.chmod(0o644)
        path.write_bytes(policy._encoded(value))

    def reseal_formation(self):
        path = self.formation / "artifact_hashes.json"
        manifest = self.read(path)
        manifest["files"] = {name: formation._hash(self.formation / name) for name in manifest["files"]}
        self.rewrite(path, manifest)

    def test_actual_formation_first64_and_exact_command(self):
        with patch.object(writer.trainer, "main", side_effect=AssertionError("no execute")):
            result, load = self.prepare()
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["selected_records"], 64)
        self.assertEqual(result["available_unique_grounded"], 128)
        load.assert_called_once_with(str(self.fixture.model_dir))
        corpus = self.read(self.output / "corpus.json")
        mapping = self.read(self.output / "source_map.json")
        summary = formation.summarize(self.formation)
        lines, rows = policy._lines((self.formation / "ledger.jsonl").read_bytes())
        expected = [item for item in summary["judgments"] if item["unique_grounded"]][:64]
        self.assertEqual([row["record_line"] for row in mapping["records"]],
                         [row["record_line"] for row in expected])
        for text, source in zip(corpus["corpus"], mapping["records"]):
            record = rows[source["record_line"]]
            self.assertEqual(text, policy.RECORD_ITEM.format(eid=record["episode_id"], text=record["text"]))
            self.assertEqual(source["record_sha256"], policy._sha(lines[source["record_line"]]))
            self.assertEqual(source["source_sha256"], policy._sha(lines[source["source_line"]]))
        command = self.read(self.output / "training_command.json")
        self.assertEqual(command["argv"], [sys.executable, "-B", "-m", "organism_v6.train_adapter",
            "--corpus", str(self.output / "corpus.json"), "--out", str(self.adapter),
            "--rank", "8", "--epochs", "3", "--lr", "1e-4", "--seed", "6102"])
        self.assertFalse(command["shell"])
        self.assertFalse(set(command["omitted_arguments"]) & set(command["argv"]))
        self.assertEqual(command["stdout_path"], str(self.log))
        self.assertEqual(result["metadata_equals"]["steps"], 48)
        self.assertEqual(result["metadata_equals"]["source_corpus_sha256"], formation._hash(self.output / "corpus.json"))
        self.assertFalse(self.adapter.exists())
        self.assertFalse(self.log.exists())
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o555)
        manifest = self.read(self.output / "artifact_hashes.json")
        for name, digest in manifest["files"].items():
            self.assertEqual(formation._hash(self.output / name), digest)
            self.assertEqual((self.output / name).stat().st_mode & 0o777, 0o444)
        self.assertFalse(result["clean_lineage"])
        self.assertFalse(result["training_executed"])
        self.assertFalse((self.output / "gate_receipt.json").exists())

    def test_short_count_skips_without_tokenizer_or_command(self):
        short = self.make_formation("short", unique=63)
        result, load = self.prepare(formation_out=short)
        self.assertEqual(result["status"], "SKIPPED_INSUFFICIENT_MATERIAL")
        self.assertEqual(result["available_unique_grounded"], 63)
        self.assertEqual(result["selected_records"], 0)
        load.assert_not_called()
        self.assertFalse((self.output / "corpus.json").exists())
        self.assertFalse((self.output / "training_command.json").exists())

    def test_custom_formation_seeds_prepare_without_changing_writer_seed(self):
        source = self.make_formation("replication", schedule_seed=6201, generation_seed=7201)
        report, _ = self.prepare(formation_out=source)
        expected = dict(schedule_seed=6201, generation_seed=7201)
        self.assertEqual(report["status"], "READY")
        self.assertEqual(report["formation_seeds"], expected)
        self.assertEqual(self.read(self.output / "formation_inputs.json")["formation_seeds"], expected)
        self.assertEqual(report["metadata_equals"]["seed"], 6102)
        command = self.read(self.output / "training_command.json")["argv"]
        self.assertEqual(command[command.index("--seed") + 1], "6102")
        self.assertEqual(formation.summarize(source)["n_unique_grounded_records"], 128)

    def test_omitted_seed_fields_use_legacy_defaults_not_historical_byte_bypass(self):
        path = self.formation / "config.json"
        config = self.read(path)
        del config["schedule_seed"], config["generation_seed"]
        self.rewrite(path, config)
        self.reseal_formation()
        report, _ = self.prepare()
        self.assertEqual(report["formation_seeds"], dict(schedule_seed=6101, generation_seed=7101))

    def test_config_seed_protocol_disagreement_rejected(self):
        path = self.formation / "config.json"
        config = self.read(path)
        config["generation_seed"] = 7201
        self.rewrite(path, config)
        self.reseal_formation()
        with self.assertRaisesRegex(ValueError, "protocol changed"):
            self.prepare()

    def test_changed_declared_schedule_seed_without_actual_schedule_rejected(self):
        path = self.formation / "config.json"
        config = self.read(path)
        config["schedule_seed"] = 6201
        config["protocol"] = formation.protocol(6201, 7101)
        self.rewrite(path, config)
        self.reseal_formation()
        with self.assertRaisesRegex(ValueError, "schedule mismatch"):
            self.prepare()

    def test_teacher_examples_rejected_not_training_targets(self):
        teacher = self.make_formation("teacher", teacher=True)
        result, load = self.prepare(formation_out=teacher)
        self.assertEqual(result["available_unique_grounded"], 0)
        self.assertEqual(result["status"], "SKIPPED_INSUFFICIENT_MATERIAL")
        load.assert_not_called()

    def test_results_recomputed_not_trusted_even_if_rehashed(self):
        path = self.formation / "results.json"
        result = self.read(path)
        result["n_unique_grounded_records"] = 64
        self.rewrite(path, result)
        self.reseal_formation()
        with self.assertRaisesRegex(ValueError, "recomputation"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_source_join_tamper_rejected(self):
        path = self.formation / "ledger.jsonl"
        rows = [json.loads(line) for line in path.read_bytes().splitlines()]
        next(row for row in rows if row["kind"] == "act")["action"] = "different action"
        path.chmod(0o644)
        path.write_bytes(b"".join(policy._encoded(row) for row in rows))
        self.reseal_formation()
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_raw_generation_tamper_rejected(self):
        path = self.formation / "generations.jsonl"
        path.chmod(0o644)
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "artifact hash"):
            self.prepare()

    def test_model_file_drift_rejected(self):
        (self.fixture.model_dir / "model.safetensors").write_bytes(b"changed local base")
        with self.assertRaisesRegex(ValueError, "pins changed"):
            self.prepare()

    def test_formation_source_hash_drift_rejected(self):
        path = self.formation / "config.json"
        config = self.read(path)
        config["source_hashes"][next(iter(config["source_hashes"]))] = "0" * 64
        self.rewrite(path, config)
        self.reseal_formation()
        with self.assertRaisesRegex(ValueError, "source code changed"):
            self.prepare()

    def copied_producer_sources(self, name):
        inventory = {}
        for original, digest in formation._sources().items():
            relative = Path(*Path(original).parts[-2:])
            target = self.root / name / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, target)
            inventory[str(target)] = digest
        return inventory

    def test_identical_producer_relocated_without_rewriting_formation(self):
        recorded = self.copied_producer_sources("astra_sources/911e08877bac83613a62ca58bdb032f22cc61681")
        with patch.object(formation, "_sources", return_value=recorded):
            original_out = self.make_formation("old_checkout_formation")
        before = {path.name: formation._hash(path) for path in original_out.iterdir()}
        result, _ = self.prepare(formation_out=original_out)
        self.assertEqual(result["status"], "READY")
        inputs = self.read(self.output / "formation_inputs.json")
        self.assertEqual(inputs["source_hashes"], recorded)
        self.assertEqual(inputs["producer_sources"]["recorded"], recorded)
        self.assertEqual(inputs["producer_sources"]["executing"], formation._sources())
        self.assertEqual(set(inputs["producer_sources"]["files"]), writer._PRODUCER_FILES)
        for binding in inputs["producer_sources"]["files"].values():
            self.assertNotEqual(binding["recorded_path"], binding["executing_path"])
            self.assertEqual(formation._hash(Path(binding["recorded_path"])), binding["sha256"])
            self.assertEqual(formation._hash(Path(binding["executing_path"])), binding["sha256"])
        self.assertEqual(before, {path.name: formation._hash(path) for path in original_out.iterdir()})

    def test_changed_recorded_producer_still_rejected_after_relocation(self):
        recorded = self.copied_producer_sources("old_checkout")
        with patch.object(formation, "_sources", return_value=recorded):
            original_out = self.make_formation("relocated_formation")
        source = Path(next(iter(recorded)))
        source.write_bytes(source.read_bytes() + b"\nchanged original")
        with self.assertRaisesRegex(ValueError, "source code changed: recorded bytes"):
            self.prepare(formation_out=original_out)

    def test_missing_recorded_producer_rejected(self):
        recorded = self.copied_producer_sources("missing_original")
        Path(next(iter(recorded))).unlink()
        with self.assertRaisesRegex(ValueError, "missing recorded producer source"):
            writer._producer_sources(recorded)

    def test_changed_executing_bytes_rejected_despite_current_hash(self):
        original = formation._sources()
        executing = self.copied_producer_sources("changed_checkout")
        source = Path(next(iter(executing)))
        source.write_bytes(source.read_bytes() + b"\nchanged execution")
        executing[str(source)] = formation._hash(source)
        with patch.object(formation, "_sources", return_value=executing):
            with self.assertRaisesRegex(ValueError, "source code changed across checkouts"):
                writer._producer_sources(original)

    def test_ambiguous_relocated_module_rejected(self):
        recorded = dict(formation._sources())
        duplicate = self.copied_producer_sources("other_checkout")
        name, digest = next(iter(duplicate.items()))
        recorded[name] = digest
        with self.assertRaisesRegex(ValueError, "ambiguous producer source"):
            writer._producer_sources(recorded)

    def test_missing_or_unknown_producer_module_rejected(self):
        recorded = dict(formation._sources())
        recorded.pop(next(iter(recorded)))
        with self.assertRaisesRegex(ValueError, "incomplete producer source"):
            writer._producer_sources(recorded)
        source = self.root / "unknown.py"
        source.write_text("not a permitted producer dependency")
        recorded = dict(formation._sources(), **{str(source): formation._hash(source)})
        with self.assertRaisesRegex(ValueError, "unsupported producer source"):
            writer._producer_sources(recorded)

    def test_output_conflicts_rejected(self):
        for name in ("output_dir", "adapter_dir", "trainer_log"):
            path = self.root / ("existing-" + name)
            path.write_text("preserve")
            with self.subTest(name=name), self.assertRaises(FileExistsError):
                self.prepare(**{name: path})
            self.assertEqual(path.read_text(), "preserve")

    def test_log_inside_prep_or_adapter_rejected(self):
        with self.assertRaises(ValueError):
            self.prepare(trainer_log=self.output / "trainer.log")
        with self.assertRaises(ValueError):
            self.prepare(trainer_log=self.adapter / "trainer.log")

    def test_existing_prep_cannot_be_retried(self):
        self.prepare()
        with self.assertRaises(FileExistsError):
            self.prepare()

    def test_wrong_recipe_rejected_before_tokenization(self):
        corpus = dict(recipe="ordinary", corpus=["Situation rg/x/1.\nMy measured action record: child"] * 64)
        with self.assertRaisesRegex(ValueError, "child-only recipe"):
            writer.tokenizer_preflight(corpus, OffsetTokenizer())

    def test_first64_corpus_is_deterministic(self):
        self.prepare()
        second = self.root / "prep_second"
        self.prepare(output_dir=second)
        self.assertEqual((self.output / "corpus.json").read_bytes(), (second / "corpus.json").read_bytes())
        self.assertEqual((self.output / "source_map.json").read_bytes(), (second / "source_map.json").read_bytes())

    def test_failed_formation_cannot_prepare(self):
        self.formation.chmod(0o755)
        formation._write(self.formation / "failure.json", {"error": "synthetic failure"})
        path = self.formation / "artifact_hashes.json"
        manifest = self.read(path)
        manifest["files"]["failure.json"] = formation._hash(self.formation / "failure.json")
        self.rewrite(path, manifest)
        with self.assertRaisesRegex(ValueError, "failed formation"):
            self.prepare()

    def test_schedule_drift_cannot_prepare(self):
        self.rewrite(self.formation / "schedule.json", ["rg/n_queens/2000001"] * 64)
        self.reseal_formation()
        with self.assertRaisesRegex(ValueError, "training schedule mismatch"):
            self.prepare()

    def test_local_tokenizer_loader_never_downloads(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        loader = Mock(return_value=OffsetTokenizer())
        with patch.dict(sys.modules, transformers=SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=loader))):
            writer._load_tokenizer(str(self.fixture.model_dir))
        loader.assert_called_once_with(str(self.fixture.model_dir), local_files_only=True)

    def test_no_truncation_or_reselection_after_tokenizer_failure(self):
        class LongTokenizer(OffsetTokenizer):
            def __call__(self, texts, **kwargs):
                result = super().__call__(texts, **kwargs)
                result["input_ids"][0] = [1] * 513
                result["attention_mask"][0] = [1] * 513
                result["offset_mapping"][0] = [(0, 0)] * 513
                return result

        with patch.object(writer, "_load_tokenizer", return_value=LongTokenizer()):
            with self.assertRaisesRegex(ValueError, "512 tokens"):
                writer.prepare_write(self.formation, self.output, adapter_dir=self.adapter, trainer_log=self.log)
        self.assertFalse(self.output.exists())

    def test_no_child_label_tokens_rejected(self):
        class NoChildTokenizer(OffsetTokenizer):
            def __call__(self, texts, **kwargs):
                result = super().__call__(texts, **kwargs)
                result["offset_mapping"] = [[(0, 1)] * len(row) for row in result["input_ids"]]
                return result

        with patch.object(writer, "_load_tokenizer", return_value=NoChildTokenizer()):
            with self.assertRaisesRegex(ValueError, "no child target"):
                writer.prepare_write(self.formation, self.output, adapter_dir=self.adapter, trainer_log=self.log)

    def test_child_token_budgets_reported_not_called_equal(self):
        self.prepare()
        preflight = self.read(self.output / "tokenizer_preflight.json")
        self.assertEqual(preflight["examples"], 64)
        self.assertEqual(preflight["steps"], 48)
        self.assertGreater(preflight["expected_supervised_tokens"], 0)
        self.assertIn("NOT_ASSERTED", preflight["token_budget_equivalence"])
        for row in preflight["rows"]:
            self.assertEqual(row["supervised_prefix_tokens"], 0)
            self.assertEqual(row["supervised_padding_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
