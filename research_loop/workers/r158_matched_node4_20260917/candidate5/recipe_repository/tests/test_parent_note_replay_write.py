"""Synthetic CPU fixtures only: real replay revalidation, no replay/trainer launch."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

from organism_v6 import parent_note_replay_write as preparation
from organism_v6 import parent_note_replay_diagnostic as replay
from organism_v6 import parent_material_write as writer
import test_parent_note_replay_diagnostic as replay_fixtures
import test_parent_material_write as write_fixtures


class Tokenizer(write_fixtures.OffsetTokenizer, replay_fixtures.fixtures.FixtureTokenizer):
    pass


class ReplayWriteTests(unittest.TestCase):
    def setUp(self):
        self.fixture = replay_fixtures.ReplayTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.replay_out = self.root / "synthetic_replay"
        self.output = self.root / "preparation"
        self.adapters = {arm: self.root / (arm + "_adapter") for arm in replay.ARMS}
        self.logs = {arm: self.root / (arm + ".trainer.log") for arm in replay.ARMS}
        self.tokenizer = Tokenizer()
        self.sources = {arm: replay.inspect_source(getattr(self.fixture, arm), arm) for arm in replay.ARMS}
        for module, name in ((replay, "run"), (writer.trainer, "main"), (writer, "_formation_snapshot"),
                             (writer.formation, "local_backend")):
            guard = patch.object(module, name, side_effect=AssertionError("not a preparation action"))
            guard.start()
            self.addCleanup(guard.stop)
        load = patch.object(writer, "_load_tokenizer", return_value=self.tokenizer)
        self.load = load.start()
        self.addCleanup(load.stop)

    def make_replay(self, transform=None):
        self.replay_out.mkdir()
        model = str(self.fixture.fixture.model_dir)
        config = dict(**replay.BOUNDARY, model_path=model,
            model_pins=self.sources["lesson"]["local_pins"]["files"],
            source_roots={arm: source["root"] for arm, source in self.sources.items()},
            implementation=replay._implementation(), coach=replay.COACH,
            coach_sha256=writer.policy._sha(replay.COACH.encode()), selected_per_arm=256,
            batch_size=8, max_tokens=100, temperature=.7, maximum_note_generations=512,
            timeout_seconds=replay.TIMEOUT, max_model_len=replay.MAX_MODEL_LEN,
            device=None, selection="first four measured ACTs per schedule, physical ledger order")
        writer.formation._write(self.replay_out / "config.json", config)
        prepared, records, events = {}, [], []
        identity = replay.model_backend.configured_generation_identity(model, None)
        for arm in replay.ARMS:
            source = self.sources[arm]
            writer.formation._write(self.replay_out / (arm + "_sources.json"), source)
            prepared[arm] = [replay._token_info(row, self.tokenizer) for row in source["sources"]]
            for start in range(0, 256, 8):
                outputs = []
                for offset in range(8):
                    index = start + offset
                    entry = source["sources"][index]
                    action = entry["source_act"]["action"]
                    text = f'I submitted "{action}"; the score was 0.50.'
                    if transform is not None:
                        text = transform(arm, index, text)
                    outputs.append(text)
                    events.append(dict(kind="request", output_id=f"{arm}/{index:04d}",
                        source_id=entry["source_id"], prompt=entry["replay_prompt"],
                        prompt_sha256=writer.policy._sha(entry["replay_prompt"].encode()),
                        seed=entry["original_seed"], max_tokens=100, temperature=.7, identity=identity,
                        tokens=prepared[arm][index]))
                    records.append(dict(arm=arm, output_id=f"{arm}/{index:04d}", source_id=entry["source_id"],
                        episode_id=entry["episode_id"], execution_id=entry["execution_id"], old_text=entry["old_text"],
                        text=text, output_sha256=writer.policy._sha(text.encode()), tokens=prepared[arm][index],
                        output_retokenized_tokens=len(self.tokenizer.encode(text, add_special_tokens=False)),
                        judgment=replay._judgment(text, entry, source["teacher"]["text"])))
                events.append(dict(kind="batch_return", arm=arm, start=start, outputs=outputs, elapsed_seconds=0.0))
        writer.formation._write(self.replay_out / "token_preflight.json", prepared)
        writer.formation._write(self.replay_out / "results.json", replay._summary(records, self.sources))
        for name, rows in (("records.jsonl", records), ("generations.jsonl", events)):
            (self.replay_out / name).write_bytes(b"".join(writer.policy._encoded(row) for row in rows))
        writer.formation._write(self.replay_out / "artifact_hashes.json",
            dict(**replay.BOUNDARY, files={path.name: writer._hash(path) for path in self.replay_out.iterdir()}))

    def prepare(self):
        return preparation.prepare_write(self.replay_out, self.output,
            adapter_dirs=self.adapters, trainer_logs=self.logs)

    def read(self, name):
        return writer._read(self.output / name)

    def assert_no_training(self):
        self.assertTrue(all(not path.exists() for path in [*self.adapters.values(), *self.logs.values()]))

    def assert_paired_skip(self, report):
        self.assertEqual(report["status"], "PAIRED_SKIP_INSUFFICIENT_MATERIAL")
        for arm in replay.ARMS:
            self.assertEqual(report["reports"][arm]["selected_records"], 0)
            self.assertEqual(self.read(arm + "/source_map.json")["records"], [])
            for name in ("corpus.json", "training_command.json", "tokenizer_preflight.json"):
                self.assertFalse((self.output / arm / name).exists())
        self.assert_no_training()

    def rewrite_rows(self, root, name, change, *, reseal=True):
        path = root / name
        _, rows = writer.policy._lines(path.read_bytes())
        change(rows)
        path.chmod(0o644)
        path.write_bytes(b"".join(writer.policy._encoded(row) for row in rows))
        if reseal:
            self.fixture.reseal(root)

    def test_ready_preserves_raw_child_bytes_source_order_recipe_and_digests(self):
        self.make_replay(lambda arm, index, text: "\n  " + text + "  \n")
        before = {str(path): writer._hash(path) for root in
                  (self.replay_out, self.fixture.lesson, self.fixture.sham) for path in root.iterdir()}
        with patch.object(replay, "validate_replay", wraps=replay.validate_replay) as validate:
            report = self.prepare()
        self.assertEqual(validate.call_count, 2)
        self.assertEqual(report["status"], "READY")
        self.assertEqual(before, {name: writer._hash(Path(name)) for name in before})
        self.load.assert_called_once_with(str(self.fixture.fixture.model_dir))
        raw, rows = writer.policy._lines((self.replay_out / "records.jsonl").read_bytes())
        manifest = self.read("artifact_hashes.json")["files"]
        for name, digest in manifest.items():
            self.assertEqual(digest, writer._hash(self.output / name))
            self.assertEqual((self.output / name).stat().st_mode & 0o222, 0)
        for arm in replay.ARMS:
            corpus = self.read(arm + "/corpus.json")
            mappings = self.read(arm + "/source_map.json")["records"]
            self.assertEqual(len(corpus["corpus"]), 64)
            self.assertEqual(corpus["recipe"], writer.RECIPE)
            self.assertEqual(corpus["principles"], [])
            self.assertEqual([row["replay_source_index"] for row in mappings], list(range(64)))
            for item, mapping in zip(corpus["corpus"], mappings):
                record = rows[mapping["replay_record_line"]]
                source = self.sources[arm]["sources"][mapping["replay_source_index"]]
                prefix = writer.trainer.child_record_prefix_length(item)
                self.assertEqual(item[prefix:], record["text"])
                self.assertEqual(mapping["replay_record_sha256"], writer.policy._sha(raw[mapping["replay_record_line"]]))
                self.assertEqual(mapping["child_text_sha256"], writer.policy._sha(record["text"].encode()))
                self.assertEqual(mapping["source_act_sha256"], source["act_sha256"])
                self.assertEqual(mapping["original_wake_trace"], source["wake_trace"])
            command = self.read(arm + "/training_command.json")
            self.assertEqual(command["argv"], [sys.executable, "-B", "-m", "organism_v6.train_adapter",
                "--corpus", str(self.output / arm / "corpus.json"), "--out", str(self.adapters[arm]),
                "--rank", "8", "--epochs", "3", "--lr", "1e-4", "--seed", "6102"])
            self.assertFalse(command["shell"])
            self.assertNotIn("CUDA_VISIBLE_DEVICES", command["env"])
            preflight = self.read(arm + "/tokenizer_preflight.json")
            self.assertEqual(preflight["steps"], 48)
            self.assertFalse(preflight["truncation"])
            for row in preflight["rows"]:
                self.assertEqual(row["supervised_prefix_tokens"], 0)
                self.assertEqual(row["supervised_padding_tokens"], 0)
                self.assertGreater(row["supervised_child_tokens"], 0)
            metadata = report["reports"][arm]["metadata_equals"]
            self.assertEqual(metadata["source_corpus_sha256"], writer._hash(self.output / arm / "corpus.json"))
            self.assertEqual(metadata["supervised_tokens"], preflight["expected_supervised_tokens"])
        self.assertFalse(report["clean_lineage"])
        self.assertFalse(report["h1_claim"])
        self.assertFalse(report["training_executed"])
        self.assertEqual(report["official_base_authentication"], "UNRESOLVED")
        self.assertEqual(report["model_provenance"], "LOCAL_HASHES_ONLY")
        self.assertFalse((self.output / "formation_inputs.json").exists())
        self.assert_no_training()

    def test_insufficient_either_arm_skips_both_without_preflight(self):
        for arm in replay.ARMS:
            with self.subTest(arm=arm):
                self.replay_out = self.root / (arm + "_short_replay")
                self.output = self.root / (arm + "_short_preparation")
                self.make_replay(lambda mode, index, text: "ACT: guess again" if mode == arm and index >= 63 else text)
                with patch.object(writer, "tokenizer_preflight", side_effect=AssertionError("paired skip")):
                    report = self.prepare()
                self.assert_paired_skip(report)
                self.assertEqual(report["reports"][arm]["available_unique_faithful"], 63)
                self.assertEqual(report["reports"]["sham" if arm == "lesson" else "lesson"]["available_unique_faithful"], 256)

    def test_echoes_excluded_by_real_revalidation_no_child_editing(self):
        echoes = {arm: (replay.COACH, replay.COACH.split(". ")[1] + ".", source["teacher"]["text"])
                  for arm, source in self.sources.items()}
        self.make_replay(lambda arm, index, text: text + " " + echoes[arm][index % 3] if index < 192 else text)
        report = self.prepare()
        for arm in replay.ARMS:
            self.assertEqual(report["reports"][arm]["available_unique_faithful"], 64)
            mappings = self.read(arm + "/source_map.json")["records"]
            self.assertEqual([row["replay_source_index"] for row in mappings], list(range(192, 256)))

    def test_duplicate_faithful_texts_do_not_inflate_unique_threshold(self):
        actual_batch = replay_fixtures.SourceModel.batch

        def repeated(model, *args, **kwargs):
            return [re.sub(r"source-action-(\d+)", lambda match: "source-action-" + str(int(match[1]) % 63), text)
                    for text in actual_batch(model, *args, **kwargs)]

        with patch.object(replay_fixtures.SourceModel, "batch", repeated):
            original = self.fixture.make_source("lesson", name="duplicate_text_source")
        self.sources["lesson"] = replay.inspect_source(original, "lesson")
        self.make_replay()
        result = writer._read(self.replay_out / "results.json")["arms"]["lesson"]
        self.assertEqual(result["faithful"], 256)
        self.assertEqual(result["unique_faithful"], 63)
        self.assert_paired_skip(self.prepare())

    def test_missing_replay_row_rejected_even_with_resealed_manifest(self):
        self.make_replay()
        self.rewrite_rows(self.replay_out, "records.jsonl", lambda rows: rows.pop())
        with self.assertRaisesRegex(ValueError, "incomplete or excess"):
            self.prepare()
        self.assertFalse(self.output.exists())
        self.assert_no_training()

    def test_duplicate_replay_record_rejected_even_with_resealed_manifest(self):
        self.make_replay()
        self.rewrite_rows(self.replay_out, "records.jsonl", lambda rows: rows.__setitem__(1, rows[0]))
        with self.assertRaisesRegex(ValueError, "output/source/judgment mismatch"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_changed_original_raw_bytes_rejected(self):
        self.make_replay()
        path = self.fixture.lesson / "ledger.jsonl"
        path.chmod(0o644)
        path.write_bytes(path.read_bytes().replace(b'"kind":', b'"kind" :', 1))
        with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_missing_original_act_rejected_after_resealing(self):
        self.make_replay()
        self.rewrite_rows(self.fixture.lesson, "ledger.jsonl",
            lambda rows: rows.pop(next(index for index, row in enumerate(rows) if row["kind"] == "act")))
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_changed_replay_raw_bytes_rejected(self):
        self.make_replay()
        path = self.replay_out / "records.jsonl"
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_changed_source_during_tokenization_leaves_no_preparation(self):
        self.make_replay()
        actual = writer.tokenizer_preflight

        def change(corpus, tokenizer):
            result = actual(corpus, tokenizer)
            path = self.fixture.sham / "ledger.jsonl"
            path.chmod(0o644)
            path.write_bytes(path.read_bytes() + b"\n")
            return result

        with patch.object(writer, "tokenizer_preflight", side_effect=change):
            with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
                self.prepare()
        self.assertFalse(self.output.exists())

    def test_tokenizer_overlength_or_mask_failure_cannot_publish_one_arm(self):
        self.make_replay()

        class BrokenTokenizer(Tokenizer):
            def __init__(self, fail_after, kind):
                self.calls = 0
                self.fail_after = fail_after
                self.kind = kind

            def __call__(self, texts, **kwargs):
                encoded = super().__call__(texts, **kwargs)
                self.calls += 1
                if self.calls > self.fail_after:
                    if self.kind == "overlength":
                        encoded["input_ids"][0] = [1] * 513
                        encoded["attention_mask"][0] = [1] * 513
                        encoded["offset_mapping"][0] = [(0, 1)] * 513
                    else:
                        encoded["offset_mapping"][0] = [(0, 0)] * len(encoded["input_ids"][0])
                return encoded

        for fail_after in (0, 16):
            for kind in ("overlength", "mask"):
                with self.subTest(fail_after=fail_after, kind=kind):
                    with patch.object(writer, "_load_tokenizer", return_value=BrokenTokenizer(fail_after, kind)):
                        with self.assertRaises(ValueError):
                            self.prepare()
                    self.assertFalse(self.output.exists())
                    self.assert_no_training()

    def test_existing_output_or_adapter_is_never_overwritten(self):
        self.make_replay()
        self.adapters["sham"].mkdir()
        sentinel = self.adapters["sham"] / "keep"
        sentinel.write_bytes(b"another owner's work")
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual(sentinel.read_bytes(), b"another owner's work")
        self.assertFalse(self.output.exists())

    def test_cli_is_preparation_only(self):
        self.make_replay(lambda arm, index, text: "ACT: guess again")
        args = ["--replay-out", str(self.replay_out), "--out", str(self.output), "--python", sys.executable]
        for arm in replay.ARMS:
            args.extend(["--" + arm + "-adapter-out", str(self.adapters[arm]),
                         "--" + arm + "-trainer-log", str(self.logs[arm])])
        output = io.StringIO()
        with redirect_stdout(output):
            preparation.main(args)
        self.assert_paired_skip(json.loads(output.getvalue()))


if __name__ == "__main__":
    unittest.main()
