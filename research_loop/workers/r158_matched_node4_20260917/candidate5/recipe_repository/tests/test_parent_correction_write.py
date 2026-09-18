"""CPU fixtures: real collector/replay and V3 masks, no model fitting."""
import copy
import json
import sys
import unittest
from unittest.mock import patch

import test_parent_correction_diagnostic as fixtures
from organism_v6 import parent_correction_write as write


QUESTION = (
    "In 4x4 Mini Sudoku:\n"
    "- Each row must contain each number from 1-4 exactly once\n"
    "- Each column must contain each number 1-4 exactly once\n"
    "- Each 2x2 subgrid must contain each number 1-4 exactly once\n"
    "Solve this 4x4 Mini Sudoku puzzle:\n_ 4 1 _\n_ _ _ 2\n4 3 _ _\n_ _ _ _\n"
    "Format your response as the puzzle above, with spaces separating each number within a row, "
    "and newlines separating rows.\n"
)
FAILED = "2 4 1 3 ; 3 2 4 1 ; 4 3 2 1 ; 1 5 3 2"
ACT = "ACT: 2 4 1 3 ; 3 1 4 2 ; 4 3 2 1 ; 1 2 3 4"
RAW = (
    "NOTE: The previous attempt had some numbers in the right place but wasn't fully correct. "
    "I need to ensure each row, column, and 2x2 subgrid contains the numbers 1-4 exactly once.\n\n"
    + ACT + "\nPREDICT: 0.85"
)


class Tokenizer:
    eos_token_id = 0
    pad_token_id = 0

    def encode(self, text, add_special_tokens=False):
        return [ord(character) + 1 for character in text]

    def decode(self, tokens, skip_special_tokens=False, clean_up_tokenization_spaces=False):
        return "".join(chr(token - 1) for token in tokens)

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return "<user>\n" + messages[0]["content"] + "\n<assistant>\n"


class CorrectionWriteTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.CorrectionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        original_item = self.fixture.gym._item

        def item(family, seed):
            if seed == 1850124:
                return self.fixture.gym, dict(question=QUESTION, answer="SEALED_REFERENCE_NEVER_VISIBLE")
            return original_item(family, seed)

        self.fixture.gym._item = item
        self.fixture.gym.score_answer = lambda answer, entry: 1.0 if answer == ACT[5:].replace(" ; ", "\n") else .25
        self.fixture.model.first = "PREDICT: 0.3\n" + "ACT: " + FAILED
        self.fixture.model.second = ACT + "\nPREDICT: 0.85"
        self.fixture.model.scratchpad = RAW
        self.fixture.prepare()
        self.source = self.root / "sham"
        self.fixture.run_arm(mode="sham", out=self.source)
        self.capsule = self.root / "fixture_capsule.tgz"
        self.capsule.write_bytes(b"SYNTHETIC CPU FIXTURE; NOT A NATIVE CAPSULE")
        self.output = self.root / "write"
        self.recipients = self.root / "recipients"
        records = write.writer._read(self.source / "captures.json")
        self.prompt = records[24]["scratchpads"][0]["capture"]["prompt"]
        self.approved = dict(write.APPROVED,
            capsule_sha256=write.writer._hash(self.capsule),
            inventory_sha256=write.writer._hash(self.source / "artifact_hashes.json"),
            prompt_sha256=write.sha(self.prompt.encode()), synthetic=True)
        self.addCleanup(patch.stopall)
        patch.object(write, "APPROVED", self.approved).start()
        self.loader = patch.object(write.writer, "_load_tokenizer", return_value=Tokenizer()).start()
        patch.object(write.trainer, "run_training", side_effect=AssertionError("no fitting")).start()
        patch.object(write.correction, "execute_pair", side_effect=AssertionError("no GPU collection")).start()

    def prepare(self):
        return write.prepare_write(self.source, self.capsule, self.output,
            model_path=self.fixture.base, recipient_root=self.recipients, python_executable=sys.executable)

    def read(self, relative):
        return write.writer._read(self.output / relative)

    def rewrite(self, relative, value):
        path = self.source / relative
        path.chmod(0o644)
        path.write_bytes(write.writer._bytes(value))
        path.chmod(0o444)

    def reseal_fixture(self):
        inventory = write.writer._read(self.source / "artifact_hashes.json")
        inventory["files"] = {name: write.writer._hash(self.source / name) for name in inventory["files"]}
        self.rewrite("artifact_hashes.json", inventory)

    def test_single_event_32_replays_six_seed_specs_and_frozen_outputs(self):
        before = {path.name: write.writer._hash(path) for path in self.source.iterdir()}
        report = self.prepare()
        self.assertEqual(report["status"], "READY_CPU_PREPARATION_ONLY")
        self.assertEqual(report["unique_events"], 1)
        self.assertEqual(report["explicit_replays_per_arm"], 32)
        self.assertEqual(report["optimizer_steps_per_recipient"], 96)
        self.assertTrue(report["synthetic"])
        self.assertFalse(report["boundary"]["training_executed"])
        self.assertFalse(report["boundary"]["parenting_advantage"])
        self.assertFalse(report["boundary"]["clean_lineage"])
        self.assertFalse(report["token_matched"])
        self.loader.assert_called_once_with(str(self.fixture.base))
        self.assertFalse(self.recipients.exists())
        context = None
        for arm, target in (("whole_raw", RAW), ("act_only", ACT)):
            corpus = self.read(arm + "/corpus.json")
            source_map = self.read(arm + "/source_map.json")
            self.assertEqual(len(corpus["corpus"]), 32)
            self.assertEqual(corpus["unique_events"], 1)
            self.assertEqual(corpus["total_event_presentations"], 96)
            self.assertEqual(len({item["group"] for item in corpus["corpus"]}), 1)
            self.assertEqual([item["meta"]["replay_index"] for item in corpus["corpus"]], list(range(32)))
            self.assertEqual(len(source_map["records"]), 32)
            for item, mapping in zip(corpus["corpus"], source_map["records"]):
                self.assertEqual(item["spans"][1], [target, True, "own_output"])
                self.assertFalse(item["spans"][0][1])
                if context is None:
                    context = item["spans"][0][0]
                self.assertEqual(item["spans"][0][0], context)
                span = mapping["target"]
                raw_field = RAW if arm == "whole_raw" else ACT + "\nPREDICT: 0.85"
                self.assertEqual(raw_field.encode()[span["start_byte"]:span["end_byte"]], target.encode())
                self.assertEqual(span["span_sha256"], write.sha(target.encode()))
                pointer = "/24/scratchpads/0/capture/text" if arm == "whole_raw" else "/24/wakes/1/generation/text"
                self.assertEqual(span["field"], pointer)
                self.assertEqual(span["output_sha256"], write.sha(raw_field.encode()))
                if arm == "act_only":
                    self.assertEqual((span["start_byte"], span["end_byte"]), (0, 42))
                    self.assertNotEqual(span["span_sha256"], span["output_sha256"])
            commands = self.read(arm + "/training_commands.json")["commands"]
            self.assertEqual([command["seed"] for command in commands], [0, 1, 2])
            for command in commands:
                config = write.trainer.config_from_args(write.trainer.build_parser().parse_args(command["argv"][4:]))
                self.assertEqual(config.rank, 8)
                self.assertEqual(config.alpha, 16)
                self.assertEqual(config.epochs, 3)
                self.assertEqual(config.lr, 1e-4)
                self.assertEqual(config.max_steps, 96)
                self.assertEqual(config.max_len, 4096)
                self.assertEqual(config.batch_size, 1)
                self.assertTrue(config.grad_checkpoint)
                self.assertFalse(config.pack)
                self.assertIsNone(command["adapter_input"])
                self.assertFalse(command["execute"])
                self.assertFalse(command["shell"])
                self.assertNotIn("CUDA_VISIBLE_DEVICES", command["env"])
                self.assertEqual(command["corpus_sha256"], write.writer._hash(self.output / arm / "corpus.json"))
        preflights = {arm: self.read(arm + "/tokenizer_preflight.json") for arm in write.ARMS}
        self.assertEqual(preflights["whole_raw"]["raw_target_tokens_per_item"], 236)
        self.assertEqual(preflights["act_only"]["raw_target_tokens_per_item"], 42)
        self.assertNotEqual(preflights["whole_raw"]["input_tokens_all_epochs"], preflights["act_only"]["input_tokens_all_epochs"])
        manifest = self.read("artifact_hashes.json")
        for name, digest in manifest["files"].items():
            self.assertEqual(digest, write.writer._hash(self.output / name))
        for path in [self.output, *self.output.rglob("*")]:
            self.assertEqual(path.stat().st_mode & 0o222, 0)
        self.assertEqual(before, {path.name: write.writer._hash(path) for path in self.source.iterdir()})

    def test_exact_teacher_removal_and_original_public_feedback_not_wake2(self):
        context, deletion = write.strip_teacher(self.prompt)
        raw = self.prompt.encode()
        retained = b"".join(raw[start:end] for start, end in deletion["retained_byte_ranges"])
        self.assertEqual(context.encode(), retained)
        self.assertEqual(raw[deletion["start_byte"]:deletion["end_byte"]],
                         write.correction.packages.PACKAGES["sham"].encode())
        self.assertIn(QUESTION, context)
        self.assertIn("ACT submitted: " + json.dumps(FAILED), context)
        self.assertIn("Displayed verifier score: 0.25", context)
        self.assertTrue(context.endswith("Scratchpad:"))
        self.assertNotIn(ACT, context)
        self.assertNotIn("SEALED_REFERENCE", context)
        self.assertNotIn("CLOCK: chunk 2/2", context)
        self.assertNotIn("[Scratchpad from ", context)
        self.assertFalse(write.teacher_echo(context))
        self.assertFalse(write.teacher_echo(RAW))

    def test_missing_duplicate_changed_or_residual_teacher_rejected(self):
        package = write.correction.packages.PACKAGES["sham"]
        for prompt in (self.prompt.replace(package, ""), self.prompt + package,
                       self.prompt.replace("First, notice", "First, NOTICE"),
                       self.prompt + "\n" + write.correction.packages.PACKAGES["process"].splitlines()[1]):
            with self.subTest(prompt=prompt[-100:]), self.assertRaises(ValueError):
                write.strip_teacher(prompt)

    def test_process_false_candidate_rejected(self):
        config = write.writer._read(self.source / "config.json")
        config["mode"] = "process"
        self.rewrite("config.json", config)
        with self.assertRaisesRegex(ValueError, "process false diagnosis"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_resealed_source_drift_does_not_reselect_or_relabel(self):
        records = write.writer._read(self.source / "captures.json")
        records[24]["scratchpads"][0]["capture"]["text"] += "\n"
        self.rewrite("captures.json", records)
        self.reseal_fixture()
        with self.assertRaisesRegex(ValueError, "approved source inventory drift"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_capsule_drift_rejected(self):
        self.capsule.write_bytes(b"CHANGED")
        with self.assertRaisesRegex(ValueError, "capsule hash drift"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_wake2_act_line_requires_exact_0_42_and_newline_boundary(self):
        records = write.writer._read(self.source / "captures.json")
        reduction = write.correction.reduce_captures(records)
        for text in (ACT, ACT + " \nPREDICT: 0.85", "\n" + ACT + "\nPREDICT: 0.85"):
            with self.subTest(text=text):
                changed = copy.deepcopy(records)
                changed[24]["wakes"][1]["generation"]["text"] = text
                self.rewrite("captures.json", changed)
                self.approved["wake2_sha256"] = write.sha(text.encode())
                with patch.object(write.correction, "reduce_captures", return_value=reduction):
                    with self.assertRaisesRegex(ValueError, "exact wake2 0:42 line"):
                        write.select_event(self.source)

    def test_whole_wake2_drift_rejected_even_if_first_42_bytes_unchanged(self):
        records = write.writer._read(self.source / "captures.json")
        reduction = write.correction.reduce_captures(records)
        records[24]["wakes"][1]["generation"]["text"] += "\nNOTE: changed tail"
        self.rewrite("captures.json", records)
        with patch.object(write.correction, "reduce_captures", return_value=reduction):
            with self.assertRaisesRegex(ValueError, "whole wake2 generation drift"):
                write.select_event(self.source)

    def test_pinned_producer_drift_rejected(self):
        config = write.writer._read(self.source / "config.json")
        path = next(path for path in config["sources"] if path.endswith("parent_correction_diagnostic.py"))
        config["sources"][path] = "0" * 64
        self.rewrite("config.json", config)
        self.reseal_fixture()
        self.approved["inventory_sha256"] = write.writer._hash(self.source / "artifact_hashes.json")
        with self.assertRaisesRegex(ValueError, "pinned producer source drift"):
            self.prepare()

    def test_unrelated_source_drift_is_not_revalidated_or_claimed_identical(self):
        config = write.writer._read(self.source / "config.json")
        for name in config["sources"]:
            relative = "organism_v6/" + name.split("/organism_v6/", 1)[1] if "/organism_v6/" in name else None
            if relative not in write.REQUIRED_PRODUCER_FILES:
                config["sources"][name] = "0" * 64
        config["sources"]["/newer/unrelated/organism_v6/unrelated_launcher.py"] = "1" * 64
        self.rewrite("config.json", config)
        self.reseal_fixture()
        self.approved["inventory_sha256"] = write.writer._hash(self.source / "artifact_hashes.json")
        _config, source = write.check_source(self.source, self.capsule)
        self.assertEqual(set(source["producer_sources"]), write.REQUIRED_PRODUCER_FILES)
        self.assertFalse(source["current_checkout_identity_asserted"])
        self.assertFalse(source["unrelated_recorded_sources_revalidated"])
        self.assertEqual(source["producer_pin_scope"], "REQUIRED_CPU_REPLAY_AND_MATERIAL_PRIMITIVES_ONLY")

    def test_missing_required_replay_primitive_pin_rejected(self):
        config = write.writer._read(self.source / "config.json")
        name = next(name for name in config["sources"] if name.endswith("batch_loop.py"))
        del config["sources"][name]
        self.rewrite("config.json", config)
        self.reseal_fixture()
        self.approved["inventory_sha256"] = write.writer._hash(self.source / "artifact_hashes.json")
        with self.assertRaisesRegex(ValueError, "missing required CPU replay/material source pin"):
            write.check_source(self.source, self.capsule)

    def test_actual_capture_ledger_replay_failure_is_preserved_not_ready(self):
        rows = [json.loads(line) for line in (self.source / "ledger.jsonl").read_bytes().splitlines()]
        next(row for row in rows if row["kind"] == "act")["action"] = "UNJOINED"
        path = self.source / "ledger.jsonl"
        path.chmod(0o644)
        path.write_bytes(b"".join(write.writer._bytes(row) for row in rows))
        path.chmod(0o444)
        self.reseal_fixture()
        self.approved["inventory_sha256"] = write.writer._hash(self.source / "artifact_hashes.json")
        with self.assertRaisesRegex(ValueError, "ACT/real ledger mismatch"):
            self.prepare()
        self.assertTrue((self.output / "failure.json").exists())
        self.assertTrue((self.output / "artifact_hashes.json").exists())
        self.assertFalse((self.output / "preparation.json").exists())
        self.assertFalse(self.recipients.exists())

    def test_no_answer_injection_even_if_local_removal_helper_is_wrong(self):
        original = write.strip_teacher

        def inject(prompt):
            context, evidence = original(prompt)
            return ACT + "\n" + context, evidence

        with patch.object(write, "strip_teacher", side_effect=inject):
            with self.assertRaisesRegex(ValueError, "answer-bearing or wake2"):
                self.prepare()
        self.assertFalse(self.output.exists())

    def test_all_raw_target_labels_survive_real_v3_and_causal_shift(self):
        context, targets, mapping, _reduction = write.select_event(self.source)
        for arm in write.ARMS:
            corpus = write.make_corpus(context, targets[arm], arm, mapping)
            evidence = write.tokenizer_preflight(corpus, Tokenizer())
            for row in evidence["rows"]:
                self.assertEqual(row["supervised_target_tokens"], len(targets[arm]) + 1)
                self.assertEqual(row["supervised_context_tokens"], 0)
                self.assertEqual(row["supervised_padding_tokens"], 0)
                self.assertTrue(row["target_roundtrip_exact"])
                self.assertFalse(row["truncation"])
            self.assertEqual(evidence["supervised_tokens_all_epochs"], 96 * (len(targets[arm]) + 1))

    def test_corrupted_actual_collate_target_label_rejected(self):
        original = write.trainer.collate

        def corrupt(packs, pad_id):
            batch = original(packs, pad_id)
            labels = batch["labels"][0]
            first_target = next(index for index, label in enumerate(labels) if label != -100)
            labels[first_target] = -100
            return batch

        with patch.object(write.trainer, "collate", side_effect=corrupt):
            with self.assertRaisesRegex(ValueError, "collate masked or changed target"):
                self.prepare()
        self.assertFalse(self.output.exists())

    def test_no_truncation_or_target_normalization(self):
        context, targets, mapping, _reduction = write.select_event(self.source)
        corpus = write.make_corpus("x" * 4096 + context, targets["whole_raw"], "whole_raw", mapping)
        with self.assertRaisesRegex(ValueError, "exceeds 4096"):
            write.tokenizer_preflight(corpus, Tokenizer())
        tokenizer = Tokenizer()
        tokenizer.decode = lambda *args, **kwargs: RAW + "\n"
        corpus = write.make_corpus(context, RAW, "whole_raw", mapping)
        with self.assertRaisesRegex(ValueError, "roundtrip changed bytes"):
            write.tokenizer_preflight(corpus, tokenizer)

    def test_missing_actual_tokenizer_never_reports_ready(self):
        self.loader.side_effect = ImportError("no local transformers")
        with self.assertRaises(ImportError):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_existing_output_or_recipient_root_never_overwritten(self):
        self.prepare()
        digest = write.writer._hash(self.output / "artifact_hashes.json")
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual(digest, write.writer._hash(self.output / "artifact_hashes.json"))
        self.output = self.root / "another_write"
        self.recipients.mkdir()
        sentinel = self.recipients / "existing_adapter"
        sentinel.write_bytes(b"preserve")
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual(sentinel.read_bytes(), b"preserve")
        self.assertFalse(self.output.exists())

    def test_no_recipe_drift_in_counts(self):
        context, targets, mapping, _reduction = write.select_event(self.source)
        corpus = write.make_corpus(context, targets["whole_raw"], "whole_raw", mapping)
        corpus["corpus"].pop()
        with self.assertRaisesRegex(ValueError, "one event, 32 replays"):
            write.tokenizer_preflight(corpus, Tokenizer())
        corpus = write.make_corpus(context, targets["whole_raw"], "whole_raw", mapping)
        changed = copy.deepcopy(corpus)
        changed["corpus"][1]["spans"][1][0] += " "
        with self.assertRaisesRegex(ValueError, "replays differ"):
            write.tokenizer_preflight(changed, Tokenizer())


if __name__ == "__main__":
    unittest.main()
