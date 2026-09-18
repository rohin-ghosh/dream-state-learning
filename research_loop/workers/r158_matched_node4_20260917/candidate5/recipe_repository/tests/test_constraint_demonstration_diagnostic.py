"""Synthetic CPU fixtures only: no real native generation, GPU or training."""
from contextlib import contextmanager, redirect_stdout
import copy
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import constraint_demonstration_diagnostic as diagnostic


class Tokenizer:
    def encode(self, text, add_special_tokens=False):
        return list(range(len(text.split())))

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return "<user>\n" + messages[0]["content"] + "\n<assistant>"


class Gym:
    strict_verifier = True

    def __init__(self):
        self.asked = []

    def benchmarks(self, split):
        return []

    def split_of(self, episode):
        return "train"

    def question(self, episode):
        self.asked.append(episode)
        return f"SYNTHETIC public question {episode}\n1 _ 3 _\n_ 4 _ 2\n2 _ 4 _\n_ 3 _ 1"

    def reference_answer(self, episode):
        raise AssertionError("reference answers forbidden")


class Model:
    def __init__(self, path, pairs, source_outputs=None):
        self.path, self.pairs = path, pairs
        self.tok = Tokenizer()
        self.calls = []
        self.source_outputs = source_outputs

    def generation_identity(self):
        return diagnostic.base.model_backend.configured_generation_identity(self.path, None)

    def batch(self, prompts, max_tokens, temperature, seeds):
        self.calls.append(dict(prompts=prompts, max_tokens=max_tokens, temperature=temperature, seeds=seeds))
        position = len(self.calls) - 1
        index, stage = position // 2, "source" if position % 2 == 0 else "transfer"
        pair = self.pairs[index]
        if stage == "source":
            return [pair["example_text"] if self.source_outputs is None else self.source_outputs[index]]
        witness = pair["transfer_witness"]
        return [diagnostic.record_text(pair["transfer"]["case_id"], witness["group"], witness["cells"], witness["digit"])]


class DemonstrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.cleanup)
        self.base = self.root / "base"
        self.base.mkdir()
        (self.base / "config.json").write_text(json.dumps(dict(model_type="qwen2", num_hidden_layers=28, hidden_size=3584)))
        (self.base / "tokenizer.json").write_text("{}")
        (self.base / "tokenizer_config.json").write_text("{}")
        (self.base / "model.safetensors").write_bytes(b"SYNTHETIC NOT WEIGHTS")
        self.pins = diagnostic.base.formation.local_files(self.base)
        self.gym = Gym()
        self.prep = self.root / "prep"
        self.prior = dict(schema="prior-source-ids-v1", episode_ids=["rg/mini_sudoku/1850001"])
        self.closed = 0
        self.prior_preparations = []
        for version, start in ((1, 1851000), (2, 1851100)):
            root = self.root / f"prior-v{version}"
            root.mkdir()
            cases = []
            for seed in range(start, start + 8):
                question = f"SYNTHETIC prior public question {seed}\n4 3 _ 1\n2 _ _ 3\n3 2 1 4\n1 4 3 2"
                candidate = [[4, 3, 2, 1], [2, 1, 4, 3], [3, 2, 1, 4], [1, 4, 3, 2]]
                cases.append(dict(episode_id=f"rg/mini_sudoku/{seed}", question=question, candidate=candidate,
                                  question_sha256=diagnostic.sha(question.encode()),
                                  candidate_sha256=diagnostic.sha(diagnostic.base.formation.policy._encoded(candidate))))
            diagnostic.write(root / "config.json", dict(schema=f"constraint-check-v{version}", synthetic=True))
            diagnostic.write(root / "cases.json", cases)
            diagnostic.base.receipts.seal(root)
            self.prior_preparations.append(root)

    def cleanup(self):
        for path in self.root.rglob("*"):
            if path.is_dir():
                path.chmod(0o755)
        self.temporary.cleanup()

    def pairs(self):
        return diagnostic.prepare_pairs(self.gym, self.prior)

    def prepare(self, **kwargs):
        arguments = dict(prior_ids=self.prior, prior_preparations=self.prior_preparations, gym=self.gym, tokenizer=Tokenizer())
        arguments.update(kwargs)
        return diagnostic.prepare(self.prep, self.base, self.pins, **arguments)

    def run_model(self, model, mode, out):
        @contextmanager
        def backend(model_path):
            self.assertEqual(model_path, str(self.base))
            try:
                yield model
            finally:
                self.closed += 1

        return diagnostic.run_arm(self.prep, out, mode, backend_factory=backend, allow_synthetic=True)

    def run_pair(self):
        self.prepare()
        pairs = diagnostic.read(self.prep / "pairs.json")
        root = self.root / "pair"
        root.mkdir()
        outputs = [f" \ninvalid child {pair['source']['case_id']} λ\nParent explanation: child-echo-only\n " for pair in pairs]
        models = []
        for mode in diagnostic.MODES:
            model = Model(str(self.base), pairs, outputs if mode == "process" else None)
            models.append(model)
            self.run_model(model, mode, root / mode)
        return root, pairs, models

    def reseal(self, root, name, change):
        root.chmod(0o755)
        path = root / name
        value = diagnostic.read(path)
        change(value)
        path.unlink()
        diagnostic.write(path, value)
        (root / "artifact_hashes.json").unlink()
        diagnostic.base.receipts.seal(root)

    def test_fixed_16_questions_balanced_source_and_copied_witness_really_invalid(self):
        pairs = self.pairs()
        self.assertEqual(diagnostic.SOURCE_IDS, tuple(f"rg/mini_sudoku/{seed}" for seed in range(1851200, 1851208)))
        self.assertEqual(diagnostic.TRANSFER_IDS, tuple(f"rg/mini_sudoku/{seed}" for seed in range(1851300, 1851308)))
        expected_order = [episode for pair in zip(diagnostic.SOURCE_IDS, diagnostic.TRANSFER_IDS) for episode in pair]
        self.assertEqual(self.gym.asked, expected_order)
        groups = []
        for pair in pairs:
            record = json.loads(pair["example_text"])
            groups.append(record["checks"][0]["group"])
            self.assertEqual(diagnostic.base.score_record(pair["example_text"], pair["source"])["grounded"], 1)
            record["case_id"] = pair["transfer"]["case_id"]
            copied = diagnostic.base.score_record(json.dumps(record), pair["transfer"])
            self.assertTrue(copied["format_valid"])
            self.assertEqual(copied["grounded"], 0)
            cells = record["checks"][0]["cells"]
            values = [pair["transfer"]["candidate"][row - 1][column - 1] for row, column in cells]
            self.assertNotEqual(*values)
            witness = pair["transfer_witness"]
            target = diagnostic.record_text(pair["transfer"]["case_id"], witness["group"], witness["cells"], witness["digit"])
            self.assertEqual(diagnostic.base.score_record(target, pair["transfer"])["grounded"], 1)
            self.assertTrue(all(cell not in cells for cell in witness["cells"]))
            for stage in ("source", "transfer"):
                case = pair[stage]
                self.assertFalse(case["program"]["reference_answer_accessed"])
                self.assertEqual(case["question_sha256"], diagnostic.sha(case["question"].encode()))
                self.assertEqual(case["candidate_sha256"], diagnostic.sha(diagnostic.base.formation.policy._encoded(case["candidate"])))
        self.assertEqual([groups.count(group) for group in ("row", "column", "box")], [3, 3, 2])
        self.assertEqual(len({pair[stage]["candidate_sha256"] for pair in pairs for stage in ("source", "transfer")}), 16)

    def test_captured_prior_union_preserves_input_and_pending_is_not_ready(self):
        original = copy.deepcopy(self.prior)
        self.prepare()
        captured = diagnostic.read(self.prep / "prior_ids.json")
        self.assertEqual(self.prior, original)
        self.assertTrue(set(diagnostic.ADDED_PRIOR_IDS) <= set(captured["episode_ids"]))
        self.assertIn(original["episode_ids"][0], captured["episode_ids"])
        self.assertEqual(diagnostic.read(self.prep / "preflight.json")["status"], "SYNTHETIC_CPU_ONLY")
        with self.assertRaisesRegex(ValueError, "synthetic preparation"):
            diagnostic.validate_preparation(self.prep)
        self.prep = self.root / "pending"
        self.assertEqual(self.prepare(prior_ids=None)["status"], "PENDING_COLLISION_CHECK")
        with self.assertRaisesRegex(ValueError, "pending"):
            diagnostic.validate_preparation(self.prep, True)

    def test_id_collision_or_nontraining_stops_before_reading_questions(self):
        for episode in (diagnostic.SOURCE_IDS[0], diagnostic.TRANSFER_IDS[-1]):
            with self.assertRaisesRegex(ValueError, "collision"):
                diagnostic.prepare_pairs(self.gym, dict(self.prior, episode_ids=[episode]))
        self.assertEqual(self.gym.asked, [])
        with patch.object(self.gym, "split_of", return_value="canary"):
            with self.assertRaisesRegex(ValueError, "training membership"):
                self.pairs()
        with self.assertRaisesRegex(ValueError, "metadata-only"):
            diagnostic.effective_prior(dict(self.prior, answer="forbidden"))

    def test_duplicate_question_and_candidate_hashes_fail_without_replacement(self):
        question = self.gym.question(diagnostic.SOURCE_IDS[0])
        with patch.object(self.gym, "question", return_value=question) as getter:
            with self.assertRaisesRegex(ValueError, "duplicate question_sha256"):
                self.pairs()
            self.assertEqual(getter.call_count, 16)
        original = diagnostic.make_pair

        def duplicate(source, transfer, index):
            pair = original(source, transfer, index)
            pair["transfer"]["candidate"] = copy.deepcopy(pair["source"]["candidate"])
            pair["transfer"]["candidate_sha256"] = pair["source"]["candidate_sha256"]
            return pair

        with patch.object(diagnostic, "make_pair", side_effect=duplicate):
            with self.assertRaisesRegex(ValueError, "duplicate candidate_sha256"):
                self.pairs()

    def test_same_correct_examples_both_arms_and_source_specific_truth(self):
        pairs = self.pairs()
        check = diagnostic.preflight(pairs, Tokenizer())
        for index, pair in enumerate(pairs):
            source_record = json.loads(pair["example_text"])["checks"][0]
            first, second = source_record["cells"]
            process = diagnostic.explanation(pair, "process")
            self.assertIn(f"({first[0]},{first[1]})", process)
            self.assertIn(f"({second[0]},{second[1]})", process)
            self.assertIn(f"both are {source_record['digit']}", process)
            for mode in diagnostic.MODES:
                prompt = diagnostic.source_prompt(pair, mode)
                self.assertEqual(prompt.count(pair["example_text"]), 1)
                self.assertEqual(prompt, check["source_requests"][mode][index]["prompt"])
                self.assertNotIn(pair["transfer"]["case_id"], prompt)
                self.assertNotIn(pair["source"]["question"], prompt)
        self.assertFalse(check["explanation_tokens_equal"])
        self.assertIn("no padding", check["matching"])

    def test_transfer_exact_note_including_invalid_syntax_unicode_and_child_echo(self):
        pair = self.pairs()[0]
        note = " \n{ invalid JSON λ\n" + diagnostic.explanation(pair, "process") + "\n\n "
        prompt, receipt = diagnostic.transfer_prompt(pair, note)
        raw = prompt.encode()
        self.assertEqual(raw[receipt["start_byte"]:receipt["end_byte"]], note.encode())
        self.assertEqual(receipt["bytes"], len(note.encode()))
        self.assertEqual(receipt["output_sha256"], diagnostic.sha(note.encode()))
        outside = (raw[:receipt["start_byte"]] + raw[receipt["end_byte"]:]).decode()
        self.assertNotIn(diagnostic.explanation(pair, "process"), outside)
        self.assertNotIn(pair["example_text"], outside)
        self.assertNotIn(pair["source"]["case_id"], outside)
        source_board = "\n".join(" ".join(map(str, row)) for row in pair["source"]["candidate"])
        self.assertNotIn(source_board, outside)

    def test_all32_calls_all_source_failures_still_transfer_no_note_rerender(self):
        root, pairs, models = self.run_pair()
        result = diagnostic.analyze_pair(root, self.prep)
        self.assertTrue(result["synthetic"])
        self.assertEqual(result["generation_calls"], 32)
        self.assertEqual(self.closed, 2)
        self.assertEqual(result["arms"]["process"]["counts"]["source"]["grounded"], 0)
        self.assertEqual(result["arms"]["process"]["counts"]["transfer"]["grounded"], 8)
        self.assertEqual(result["arms"]["format"]["counts"]["source_echo"]["exact_example_echo"], 8)
        self.assertIsNone(result["arms"]["process"]["actual_output_tokens"])
        for mode, model in zip(diagnostic.MODES, models):
            self.assertEqual(len(model.calls), 16)
            for index, pair in enumerate(pairs):
                source_call, transfer_call = model.calls[index * 2:index * 2 + 2]
                expected_note = model.source_outputs[index] if mode == "process" else pair["example_text"]
                self.assertEqual(source_call["prompts"], [diagnostic.source_prompt(pair, mode)])
                self.assertEqual(transfer_call["prompts"], [diagnostic.transfer_prompt(pair, expected_note)[0]])
                for call in (source_call, transfer_call):
                    self.assertEqual((call["max_tokens"], call["temperature"], call["seeds"]), (128, .7, [7101]))
            events = [json.loads(line) for line in (root / mode / "generations.jsonl").read_text().splitlines()]
            requests = [event for event in events if event["kind"] == "request"]
            self.assertEqual([row["phase"] for row in requests], ["source", "transfer"] * 8)
            self.assertEqual([row["parent_presentations"] for row in requests], [1, 0] * 8)
        self.assertFalse(result["boundary"]["fit"])
        self.assertFalse(result["boundary"]["training_approved"])

    def test_echo_distinguished_from_reformatted_same_check_and_other_valid_witness(self):
        pair = self.pairs()[0]
        example = pair["example_text"]
        exact = diagnostic.echo_analysis(example, pair, diagnostic.base.score_record(example, pair["source"]))
        self.assertTrue(exact["exact_example_echo"])
        self.assertFalse(exact["independent_discovery_claim"])
        reformatted = json.dumps(json.loads(example), indent=2)
        same = diagnostic.echo_analysis(reformatted, pair, diagnostic.base.score_record(reformatted, pair["source"]))
        self.assertFalse(same["exact_example_echo"])
        self.assertTrue(same["same_example_check"])
        alternative = json.loads(example)
        alternative["checks"][0]["group"] = "box"
        text = json.dumps(alternative)
        score = diagnostic.base.score_record(text, pair["source"])
        self.assertEqual(score["grounded"], 1)
        other = diagnostic.echo_analysis(text, pair, score)
        self.assertEqual(other["valid_non_example_citations"], 1)
        self.assertFalse(other["same_example_check"])
        self.assertFalse(other["independent_discovery_claim"])
        bad = example + "\nMore text"
        bad_echo = diagnostic.echo_analysis(bad, pair, diagnostic.base.score_record(bad, pair["source"]))
        self.assertTrue(bad_echo["example_verbatim_substring"])
        self.assertEqual(bad_echo["valid_non_example_citations"], 0)

    def test_original_checker_rejects_coordinate_strings_no_salvage(self):
        pair = self.pairs()[0]
        value = json.loads(pair["example_text"])
        value["checks"][0]["cells"] = [[str(axis) for axis in cell] for cell in value["checks"][0]["cells"]]
        score = diagnostic.base.score_record(json.dumps(value), pair["source"])
        self.assertFalse(score["format_valid"])
        self.assertEqual(score["grounded"], 0)

    def test_actual_tokenizer_live_note_headroom_and_nontransparent_template(self):
        pair = self.pairs()[0]
        tokenizer = Tokenizer()
        envelope = diagnostic.chat_envelope(tokenizer)
        with self.assertRaisesRegex(ValueError, "no truncation"):
            diagnostic.request_row(pair, "process", "transfer", tokenizer, envelope, note="word " * 4100)
        tokenizer.apply_chat_template = lambda messages, **kwargs: messages[0]["content"].replace("Candidate:", "Rewritten:")
        with self.assertRaisesRegex(ValueError, "changed/reformatted"):
            diagnostic.request_row(pair, "process", "source", tokenizer, envelope)

    def test_runtime_tokenizer_change_before_any_call_fails(self):
        self.prepare()
        model = Model(str(self.base), diagnostic.read(self.prep / "pairs.json"))
        model.tok.encode = lambda text, **kwargs: list(range(len(text.split()) + 1))
        with self.assertRaisesRegex(ValueError, "runtime tokenizer"):
            self.run_model(model, "process", self.root / "failed")
        self.assertEqual(model.calls, [])
        self.assertTrue((self.root / "failed" / "failure.json").exists())

    def test_incomplete_raw_generation_is_preserved_and_not_complete(self):
        self.prepare()
        model = Model(str(self.base), diagnostic.read(self.prep / "pairs.json"))
        model.batch = lambda *args, **kwargs: []
        with self.assertRaisesRegex(ValueError, "incomplete generation"):
            self.run_model(model, "process", self.root / "failed")
        events = [json.loads(line) for line in (self.root / "failed" / "generations.jsonl").read_text().splitlines()]
        self.assertEqual([row["kind"] for row in events], ["request", "raw_return"])
        self.assertFalse((self.root / "failed" / "results.json").exists())

    def test_replay_counts_and_note_provenance_fail_closed(self):
        root, _, _ = self.run_pair()
        self.reseal(root / "process", "results.json", lambda result: result["counts"]["transfer"].update(grounded=7))
        with self.assertRaisesRegex(ValueError, "summary count mismatch"):
            diagnostic.analyze_pair(root, self.prep)
        self.reseal(root / "process", "results.json", lambda result: result["records"][1]["note"].update(output_sha256="wrong"))
        with self.assertRaisesRegex(ValueError, "summary differs from raw"):
            diagnostic.analyze_pair(root, self.prep)

    def test_changed_pair_model_or_source_hash_fails(self):
        self.prepare()
        with patch.object(diagnostic, "source_pins", return_value={}):
            with self.assertRaisesRegex(ValueError, "source pins changed"):
                diagnostic.validate_preparation(self.prep, True)
        self.reseal(self.prep, "pairs.json", lambda pairs: pairs[0]["transfer"]["candidate"][0].__setitem__(0, 4))
        with self.assertRaisesRegex(ValueError, "construction/provenance"):
            diagnostic.validate_preparation(self.prep, True)

    def test_two_fresh_bounded_worker_commands_only_when_requested(self):
        self.prepare()
        validated = diagnostic.validate_preparation(self.prep, True)
        calls = []

        def worker(command, **kwargs):
            calls.append((command, kwargs))

        with patch.object(diagnostic, "validate_preparation", return_value=validated), \
                patch.object(diagnostic.base.supervisor, "selected_device", return_value="1"), \
                patch.dict(diagnostic.os.environ, {"V6_MODEL": str(self.base)}), \
                patch.object(diagnostic.base.model_backend, "MODEL", str(self.base)), \
                patch.object(diagnostic.base.supervisor, "run_worker", side_effect=worker), \
                patch.object(diagnostic, "analyze_pair", return_value=dict(status="SYNTHETIC_CONTROLLER_FIXTURE")):
            diagnostic.execute_pair(self.prep, self.root / "controller")
        self.assertEqual(len(calls), 2)
        for mode, (command, kwargs) in zip(diagnostic.MODES, calls):
            self.assertIn("organism_v6.constraint_demonstration_diagnostic", command)
            self.assertEqual(command[command.index("--condition") + 1], mode)
            self.assertLessEqual(kwargs["timeout"], 840)
            self.assertEqual(kwargs["device"], "1")
        with patch.object(diagnostic, "execute_pair") as execute:
            with self.assertRaisesRegex(ValueError, "GPU opt-in"):
                diagnostic.main(["--preparation", str(self.prep), "--out", str(self.root / "unsafe")])
            execute.assert_not_called()

    def test_native_preparation_cli_no_gpu_and_fixed_sampler(self):
        pins = self.root / "pins.json"
        pins.write_text(json.dumps(dict(model_path=str(self.base), files=self.pins)))
        with patch.object(diagnostic, "prepare", return_value={}) as prepare, redirect_stdout(io.StringIO()):
            diagnostic.main(["--model-path", str(self.base), "--pins", str(pins), "--out", str(self.prep)])
            prepare.assert_called_once_with(str(self.prep), str(self.base), self.pins, prior_ids=None, prior_preparations=[])
        self.assertEqual(diagnostic.PROTOCOL["generation_seed"], 7101)
        self.assertEqual(diagnostic.PROTOCOL["total_calls"], 32)

    def test_prior_actual_content_required_and_captured_without_prompt_exposure(self):
        check = self.prepare(prior_preparations=[])
        self.assertEqual(check["status"], "PENDING_PRIOR_CONTENT_CHECK")
        with self.assertRaisesRegex(ValueError, "pending"):
            diagnostic.validate_preparation(self.prep, True)
        self.prep = self.root / "complete"
        self.assertEqual(self.prepare()["status"], "SYNTHETIC_CPU_ONLY")
        config = diagnostic.read(self.prep / "config.json")
        self.assertEqual(len(config["prior_content"]["records"]), 16)
        self.assertEqual(len(config["prior_content"]["receipts"]), 2)
        for pair in diagnostic.read(self.prep / "pairs.json"):
            for mode in diagnostic.MODES:
                self.assertNotIn("SYNTHETIC prior public question", diagnostic.source_prompt(pair, mode))

    def test_prior_actual_question_or_candidate_collision_fails_no_replacement(self):
        pair = self.pairs()[0]
        root = self.prior_preparations[0]

        def reuse_question(cases):
            cases[0]["question"] = pair["source"]["question"]
            cases[0]["question_sha256"] = pair["source"]["question_sha256"]

        self.reseal(root, "cases.json", reuse_question)
        with self.assertRaisesRegex(ValueError, "prior actual question_sha256 overlap"):
            self.prepare()

        def reuse_candidate(cases):
            cases[0]["question"] = "SYNTHETIC distinct prior question"
            cases[0]["question_sha256"] = diagnostic.sha(cases[0]["question"].encode())
            cases[0]["candidate"] = pair["transfer"]["candidate"]
            cases[0]["candidate_sha256"] = pair["transfer"]["candidate_sha256"]

        self.reseal(root, "cases.json", reuse_candidate)
        with self.assertRaisesRegex(ValueError, "prior actual candidate_sha256 overlap"):
            self.prepare()

    def test_prior_content_cli_paths_pass_through(self):
        pins = self.root / "pins.json"
        pins.write_text(json.dumps(dict(model_path=str(self.base), files=self.pins)))
        paths = list(map(str, self.prior_preparations))
        with patch.object(diagnostic, "prepare", return_value={}) as prepare, redirect_stdout(io.StringIO()):
            diagnostic.main(["--model-path", str(self.base), "--pins", str(pins), "--out", str(self.prep),
                             "--prior-preparation", paths[0], "--prior-preparation", paths[1]])
            self.assertEqual(prepare.call_args.kwargs["prior_preparations"], paths)


if __name__ == "__main__":
    unittest.main()
