"""Synthetic CPU fixtures only; no native evidence, tokenizer, GPU or model."""
from contextlib import contextmanager
import copy
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from organism_v6 import constraint_check_diagnostic as diagnostic


class Tokenizer:
    def encode(self, text, add_special_tokens=False):
        return text.split()

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return "<user>\n" + messages[0]["content"] + "\n<assistant>"


class FixtureGym:
    strict_verifier = True

    def __init__(self):
        self.asked = []

    def benchmarks(self, split):
        return []

    def split_of(self, episode):
        return "train"

    def question(self, episode):
        self.asked.append(episode)
        return f"Native-question fixture {episode}\n1 _ 3 _\n_ 4 _ 2\n2 _ 4 _\n_ 3 _ 1"

    def reference_answer(self, episode):
        raise AssertionError("reference answer forbidden")


def record(case, checks=None):
    program = case["program"]
    return dict(case_id=case["case_id"], checks=checks if checks is not None else
                [dict(group="row", cells=program["cells"], digit=program["digit"])],
                lesson="Compare the displayed values before citing a duplicate.")


class Model:
    def __init__(self, model_path, cases, valid=True):
        self.path = model_path
        self.tok = Tokenizer()
        self.calls = []
        self.cases = cases
        self.valid = valid
        self.identity_changed = False

    def generation_identity(self):
        return diagnostic.model_backend.configured_generation_identity(
            "WRONG" if self.identity_changed else self.path, None)

    def batch(self, prompts, max_tokens, temperature, seeds):
        self.calls.append(dict(prompts=prompts, max_tokens=max_tokens, temperature=temperature, seeds=seeds))
        case = self.cases[len(self.calls) - 1]
        return [" \n" + json.dumps(record(case)) + "\n " if self.valid else "not JSON; preserved exactly\n"]


class ConstraintCheckTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.cleanup)
        self.base = self.root / "base"
        self.base.mkdir()
        (self.base / "config.json").write_text(json.dumps(dict(model_type="qwen2", num_hidden_layers=28, hidden_size=3584)))
        (self.base / "tokenizer.json").write_text("{}")
        (self.base / "tokenizer_config.json").write_text("{}")
        (self.base / "model.safetensors").write_bytes(b"SYNTHETIC NOT MODEL WEIGHTS")
        self.pins = diagnostic.formation.local_files(self.base)
        self.gym = FixtureGym()
        self.prep = self.root / "prep"
        self.prior = dict(schema="prior-source-ids-v1", episode_ids=[])

    def cleanup(self):
        for path in self.root.rglob("*"):
            if path.is_dir():
                path.chmod(0o755)
        self.temporary.cleanup()

    def prepare(self, **kwargs):
        arguments = dict(prior_ids=self.prior, gym=self.gym, tokenizer=Tokenizer())
        arguments.update(kwargs)
        return diagnostic.prepare(self.prep, self.base, self.pins, **arguments)

    def case(self):
        return diagnostic.make_case(diagnostic.IDS[0], self.gym.question(diagnostic.IDS[0]), 0)

    def score(self, value, case=None):
        return diagnostic.score_record(json.dumps(value), case or self.case())

    def run_pair(self):
        self.prepare()
        cases = diagnostic.read(self.prep / "cases.json")
        pair = self.root / "pair"
        pair.mkdir()
        models = []
        for mode in diagnostic.MODES:
            model = Model(str(self.base), cases, valid=mode == "process")
            models.append(model)

            @contextmanager
            def backend(model_path):
                self.assertEqual(model_path, str(self.base))
                yield model

            diagnostic.run_arm(self.prep, pair / mode, mode, backend_factory=backend, allow_synthetic=True)
        return pair, models

    def reseal_edit(self, root, name, change):
        root.chmod(0o755)
        target = root / name
        value = diagnostic.read(target)
        change(value)
        target.unlink()
        diagnostic.write(target, value)
        (root / "artifact_hashes.json").unlink()
        diagnostic.receipts.seal(root)

    def test_exact_eight_public_questions_guaranteed_duplicate_no_references(self):
        cases = diagnostic.cases_from_gym(self.gym, self.prior)
        self.assertEqual(self.gym.asked, list(diagnostic.IDS))
        self.assertEqual(len(cases), 8)
        for index, case in enumerate(cases):
            self.assertEqual(case, diagnostic.make_case(case["episode_id"], case["question"], index))
            self.assertEqual(self.score(record(case), case)["grounded"], 1)
            self.assertNotEqual(case["candidate"], case["filled_candidate"])
            self.assertFalse(case["program"]["reference_answer_accessed"])
            self.assertEqual(case["origin"], "externally_generated_observed_exercise")
            self.assertEqual(case["question_sha256"], diagnostic.sha(case["question"].encode()))
            for mode in diagnostic.MODES:
                prompt = diagnostic.prompt_for(case, mode)
                self.assertEqual(prompt.count(diagnostic.CARDS[mode]), 1)
                self.assertNotIn(case["question"], prompt)
                self.assertNotIn("filled_candidate", prompt)
        self.assertFalse(diagnostic.BOUNDARY["fit"])

    def test_no_collision_replacements_and_metadata_only(self):
        with self.assertRaisesRegex(ValueError, "collision"):
            diagnostic.cases_from_gym(self.gym, dict(self.prior, episode_ids=[diagnostic.IDS[3]]))
        self.assertEqual(self.gym.asked, [])
        with self.assertRaisesRegex(ValueError, "metadata-only"):
            diagnostic.cases_from_gym(self.gym, dict(self.prior, answer="forbidden"))
        with patch.object(self.gym, "split_of", return_value="canary"):
            with self.assertRaisesRegex(ValueError, "non-training"):
                diagnostic.cases_from_gym(self.gym, self.prior)

    def test_pending_inventory_and_synthetic_never_native_ready(self):
        self.assertEqual(self.prepare(prior_ids=None)["status"], "PENDING_COLLISION_CHECK")
        with self.assertRaisesRegex(ValueError, "pending"):
            diagnostic.validate_preparation(self.prep, allow_synthetic=True)

    def test_any_row_column_box_witness_not_canonical_or_prose_whitelist(self):
        case = self.case()
        case["candidate"] = [[1, 1, 3, 4], [1, 4, 2, 3], [2, 3, 4, 1], [4, 2, 1, 2]]
        checks = [dict(group="row", cells=[[4, 2], [4, 4]], digit=2),
                  dict(group="column", cells=[[1, 1], [2, 1]], digit=1),
                  dict(group="box", cells=[[1, 2], [2, 1]], digit=1)]
        value = record(case, checks)
        value["lesson"] = "Arbitrary unverified own prose, not used as truth evidence."
        score = self.score(value, case)
        self.assertEqual(score["grounded"], 1)
        self.assertEqual(score["valid_citations"], 3)
        self.assertEqual(score["reasons"], [])
        self.assertTrue(score["whole_structured_record_clean"])
        self.assertFalse(score["lesson_machine_verified"])
        self.assertFalse(score["training_approved"])

    def test_same_coordinate_wrong_group_digit_and_case_zero(self):
        case = self.case()
        mutations = [lambda value: value["checks"][0].update(cells=[[1, 1], [1, 1]]),
                     lambda value: value["checks"][0].update(group="column"),
                     lambda value: value["checks"][0].update(digit=4),
                     lambda value: value.update(case_id="wrong")]
        for mutate in mutations:
            value = record(case)
            mutate(value)
            score = self.score(value)
            self.assertEqual(score["grounded"], 0)
            self.assertTrue(score["format_valid"])
            self.assertTrue(score["reasons"])

    def test_duplicate_citation_deduplicated_valid_not_lost_to_incorrect(self):
        value = record(self.case())
        duplicate = copy.deepcopy(value["checks"][0])
        duplicate["cells"].reverse()
        wrong = dict(group="row", cells=[[1, 1], [1, 1]], digit=1)
        value["checks"].extend([duplicate, wrong])
        score = self.score(value)
        self.assertEqual((score["grounded"], score["valid_citations"], score["invalid_citations"]), (1, 1, 1))
        self.assertFalse(score["whole_structured_record_clean"])

    def test_malformed_raw_outputs_zero_no_salvage(self):
        text = json.dumps(record(self.case()))
        samples = ["ACT: " + text, "```json\n" + text + "\n```", text + text, "",
                   text.replace('"case_id":', '"case_id":"c01","case_id":'), "null"]
        for sample in samples:
            score = diagnostic.score_record(sample, self.case())
            self.assertFalse(score["format_valid"])
            self.assertEqual(score["grounded"], 0)
        mutations = [lambda value: value.update(extra=1), lambda value: value.update(checks=[]),
                     lambda value: value["checks"][0].update(digit=True),
                     lambda value: value["checks"][0].update(cells=[[0, 1], [1, 2]]),
                     lambda value: value["checks"][0].update(cells=[[1.0, 1], [1, 2]]),
                     lambda value: value.update(checks=value["checks"] * 4)]
        for mutate in mutations:
            value = record(self.case())
            mutate(value)
            self.assertFalse(self.score(value)["format_valid"])

    def test_actual_tokenizer_headroom_no_padding_and_frozen_prompts(self):
        check = self.prepare()
        self.assertEqual(check["status"], "SYNTHETIC_CPU_ONLY")
        for mode in diagnostic.MODES:
            self.assertEqual(check["card_tokens"][mode], len(Tokenizer().encode(diagnostic.CARDS[mode])))
            for row in check["prompts"][mode]:
                self.assertEqual(row["prompt_tokens"], len(Tokenizer().encode(row["rendered_prompt"])))
                self.assertLessEqual(row["prompt_tokens"] + 128, 4096)
        with self.assertRaisesRegex(ValueError, "synthetic/native"):
            diagnostic.validate_preparation(self.prep)
        tokenizer = Tokenizer()
        tokenizer.encode = lambda *args, **kwargs: [0] * 3969
        with self.assertRaisesRegex(ValueError, "no truncation"):
            diagnostic.preflight([self.case()], tokenizer)
        tokenizer.encode = lambda *args, **kwargs: [0] * 3968
        diagnostic.preflight([self.case()], tokenizer)

    def test_exact_sixteen_mock_calls_raw_outputs_and_recomputed_counts(self):
        pair, models = self.run_pair()
        result = diagnostic.analyze_pair(pair, self.prep)
        self.assertEqual(result["generation_calls"], 16)
        self.assertTrue(result["synthetic"])
        self.assertEqual(result["execution_backend"], "SYNTHETIC_CPU_FIXTURE")
        self.assertEqual(result["process_minus_format"], 8)
        self.assertEqual(result["arms"]["process"]["cases_with_valid_citation"], 8)
        self.assertEqual(result["arms"]["process"]["whole_structured_record_clean_count"], 8)
        self.assertIsNone(result["arms"]["process"]["actual_output_tokens"])
        self.assertEqual(result["arms"]["process"]["grounded_citation_count"], 8)
        self.assertEqual(result["arms"]["format"]["grounded_citation_count"], 0)
        for mode, model in zip(diagnostic.MODES, models):
            self.assertEqual(len(model.calls), 8)
            for call in model.calls:
                self.assertEqual(len(call["prompts"]), 1)
                self.assertEqual(call["max_tokens"], 128)
                self.assertEqual(call["temperature"], .7)
                self.assertEqual(call["seeds"], [7101])
            events = [json.loads(line) for line in (pair / mode / "generations.jsonl").read_text().splitlines()]
            outputs = [row for row in events if row["kind"] == "output"]
            self.assertEqual(len(outputs), 8)
            for output in outputs:
                self.assertEqual(output["output_sha256"], diagnostic.sha(output["text"].encode()))
                self.assertEqual(output["text"][-1], " " if mode == "process" else "\n")

    def test_summary_tamper_and_incomplete_arm_not_success(self):
        pair, _ = self.run_pair()
        self.reseal_edit(pair / "process", "results.json", lambda result: result.update(grounded_citation_count=7))
        with self.assertRaisesRegex(ValueError, "summary count mismatch"):
            diagnostic.analyze_pair(pair, self.prep)
        self.reseal_edit(pair / "process", "results.json", lambda result: result.update(status="INCOMPLETE"))
        with self.assertRaisesRegex(ValueError, "completion/arm/pair mismatch"):
            diagnostic.analyze_pair(pair, self.prep)

    def test_runtime_tokenizer_mismatch_before_any_generation(self):
        self.prepare()
        model = Model(str(self.base), diagnostic.read(self.prep / "cases.json"))
        model.tok.apply_chat_template = lambda *args, **kwargs: "changed runtime template"

        @contextmanager
        def backend(model_path):
            yield model

        with self.assertRaisesRegex(ValueError, "runtime tokenizer"):
            diagnostic.run_arm(self.prep, self.root / "bad", "process", backend_factory=backend, allow_synthetic=True)
        self.assertEqual(model.calls, [])
        self.assertTrue((self.root / "bad" / "failure.json").is_file())
        self.assertFalse((self.root / "bad" / "results.json").exists())

    def test_identity_failure_before_generation(self):
        self.prepare()
        model = Model(str(self.base), diagnostic.read(self.prep / "cases.json"))
        model.identity_changed = True

        @contextmanager
        def backend(model_path):
            yield model

        with self.assertRaisesRegex(ValueError, "identity changed"):
            diagnostic.run_arm(self.prep, self.root / "bad", "process", backend_factory=backend, allow_synthetic=True)
        self.assertEqual(model.calls, [])

    def test_pins_and_immutable_preparation_fail_closed(self):
        self.prepare()
        with patch.object(diagnostic, "source_pins", return_value={}):
            with self.assertRaisesRegex(ValueError, "source pins"):
                diagnostic.validate_preparation(self.prep, True)
        (self.base / "model.safetensors").write_bytes(b"CHANGED SYNTHETIC")
        with self.assertRaisesRegex(ValueError, "model pins"):
            diagnostic.validate_preparation(self.prep, True)

    def test_duplicate_question_and_candidate_hashes_fail_no_replacement(self):
        repeated = self.gym.question(diagnostic.IDS[0])
        with patch.object(self.gym, "question", return_value=repeated) as question:
            with self.assertRaisesRegex(ValueError, "duplicate actual question_sha256"):
                diagnostic.cases_from_gym(self.gym, self.prior)
            self.assertEqual(question.call_count, 8)
        original = diagnostic.make_case

        def repeat_candidate(episode, question, index):
            case = original(episode, question, index)
            case["candidate"] = [[1] * 4 for _ in range(4)]
            case["candidate_sha256"] = diagnostic.sha(diagnostic.formation.policy._encoded(case["candidate"]))
            return case

        with patch.object(diagnostic, "make_case", side_effect=repeat_candidate):
            with self.assertRaisesRegex(ValueError, "duplicate actual candidate_sha256"):
                diagnostic.cases_from_gym(self.gym, self.prior)

    def native_capture_fixture(self, finish_reason="stop", prompt_mismatch=False):
        case = self.case()
        model = Model(str(self.base), [case])
        model.tok.encode = lambda text, **kwargs: list(range(len(text.split())))
        row = diagnostic.preflight([case], model.tok)["prompts"]["process"][0]
        output = SimpleNamespace(text=" \n" + json.dumps(record(case)) + "\n ",
                                 token_ids=[101, 102], finish_reason=finish_reason, stop_reason=None)
        request = SimpleNamespace(request_id="SYNTHETIC_RAW_REQUEST_FIXTURE", prompt=row["rendered_prompt"],
                                  prompt_token_ids=model.tok.encode(row["rendered_prompt"]),
                                  finished=True, outputs=[output])
        if prompt_mismatch:
            request.prompt_token_ids = []
        calls = []

        def generate(chats, params, **kwargs):
            calls.append((chats, params, kwargs))
            return [request]

        model.llm = SimpleNamespace(generate=generate)
        root = self.root / f"raw-{finish_reason}-{prompt_mismatch}"
        root.mkdir()
        backend = diagnostic.CaptureBackend(model, str(self.base), root, diagnostic.CARDS["process"], synthetic=False)
        return backend, row, root, calls, output

    def test_native_raw_adapter_token_ids_stop_metadata_not_retokenized(self):
        backend, row, root, calls, output = self.native_capture_fixture()
        with patch.dict("sys.modules", {"vllm": SimpleNamespace(SamplingParams=lambda **kwargs: kwargs)}):
            capture = backend.generate_record(row)
        self.assertEqual(capture["actual_output_tokens"], 2)
        self.assertNotEqual(len(backend.tokenizer.encode(output.text)), capture["actual_output_tokens"])
        self.assertEqual(capture["finish_reason"], "stop")
        self.assertEqual(capture["usage_source"], "NATIVE_VLLM_TOKEN_IDS")
        self.assertNotIn("synthetic_retokenized_output_tokens", capture)
        self.assertEqual(backend.model.calls, [])
        self.assertEqual(calls, [([row["rendered_prompt"]],
                                [dict(max_tokens=128, temperature=.7, seed=7101)],
                                dict(lora_request=None, use_tqdm=False))])
        raw = [json.loads(line) for line in (root / "generations.jsonl").read_text().splitlines()][1]
        self.assertEqual(raw["requests"][0]["outputs"][0]["token_ids"], [101, 102])
        self.assertEqual(raw["requests"][0]["outputs"][0]["text"], output.text)

    def test_length_or_unknown_stop_preserves_raw_then_fails_even_valid_json(self):
        for finish in ("length", "abort", None):
            backend, row, root, _, output = self.native_capture_fixture(finish)
            with patch.dict("sys.modules", {"vllm": SimpleNamespace(SamplingParams=lambda **kwargs: kwargs)}):
                with self.assertRaisesRegex(ValueError, "protocol failure"):
                    backend.generate_record(row)
            events = [json.loads(line) for line in (root / "generations.jsonl").read_text().splitlines()]
            self.assertEqual([event["kind"] for event in events], ["request", "raw_return", "output"])
            self.assertEqual(events[-1]["text"], output.text)
            self.assertEqual(events[-1]["finish_reason"], finish)
            self.assertFalse((root / "results.json").exists())

    def test_native_prompt_token_mismatch_preserved_then_rejected(self):
        backend, row, root, _, _ = self.native_capture_fixture(prompt_mismatch=True)
        with patch.dict("sys.modules", {"vllm": SimpleNamespace(SamplingParams=lambda **kwargs: kwargs)}):
            with self.assertRaisesRegex(ValueError, "truncation or tokenizer mismatch"):
                backend.generate_record(row)
        self.assertEqual(len((root / "generations.jsonl").read_text().splitlines()), 3)

    def test_bounded_wall_clock_alarm(self):
        with self.assertRaisesRegex(TimeoutError, "wall-clock"):
            with diagnostic.time_budget(.01):
                time.sleep(.1)

    def test_controller_two_fresh_worker_commands_deadlines_no_gpu_in_test(self):
        self.prepare()
        prepared = diagnostic.validate_preparation(self.prep, True)
        calls = []

        def worker(command, **kwargs):
            calls.append((command, kwargs))

        with patch.object(diagnostic, "validate_preparation", return_value=prepared), \
                patch.object(diagnostic.supervisor, "selected_device", return_value="0"), \
                patch.dict(diagnostic.os.environ, {"V6_MODEL": str(self.base)}), \
                patch.object(diagnostic.model_backend, "MODEL", str(self.base)), \
                patch.object(diagnostic.supervisor, "run_worker", side_effect=worker), \
                patch.object(diagnostic, "analyze_pair", return_value=dict(status="SYNTHETIC_CONTROLLER_FIXTURE")):
            result = diagnostic.execute_pair(self.prep, self.root / "controller")
        self.assertEqual(result["status"], "SYNTHETIC_CONTROLLER_FIXTURE")
        self.assertEqual(len(calls), 2)
        for mode, (command, kwargs) in zip(diagnostic.MODES, calls):
            self.assertIn("organism_v6.constraint_check_diagnostic", command)
            self.assertEqual(command[command.index("--condition") + 1], mode)
            self.assertIn("--allow-gpu", command)
            self.assertLessEqual(kwargs["timeout"], 840)
            self.assertGreater(kwargs["timeout"], 0)
            self.assertEqual(kwargs["device"], "0")

    def test_arm_settings_mismatch_and_pending_replay_rejected(self):
        pair, _ = self.run_pair()
        self.reseal_edit(pair / "format", "config.json", lambda config: config.update(model_path="WRONG"))
        with self.assertRaisesRegex(ValueError, "model/panel/settings"):
            diagnostic.analyze_pair(pair, self.prep)
        self.reseal_edit(self.prep, "preflight.json", lambda check: check.update(status="PENDING_COLLISION_CHECK"))
        with self.assertRaisesRegex(ValueError, "preparation pending"):
            diagnostic.analyze_pair(pair, self.prep)

    def test_cli_gpu_never_default(self):
        with patch.object(diagnostic, "execute_pair") as execute:
            with self.assertRaisesRegex(ValueError, "opt-in"):
                diagnostic.main(["--preparation", str(self.prep), "--out", str(self.root / "out")])
            execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
