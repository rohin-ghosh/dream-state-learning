"""CPU local-base fixtures; real gym/slot/teacher/source judges, no inference launch."""
from contextlib import contextmanager
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from organism_v6 import parent_material_diagnostic as diagnostic
from organism_v6 import preschool_reasoning as policy
from organism_v6.batch_loop import run_episodes_batch
from organism_v6.ledger import Ledger
from organism_v6.model_backend import configured_generation_identity
from organism_v6.reasoning_gym_gym import ReasoningGymGym


class FixtureTokenizer:
    def encode(self, text, add_special_tokens=False):
        return list(text.encode())

    def apply_chat_template(self, messages, tokenize=True, add_generation_prompt=True):
        text = "<user>" + messages[0]["content"] + "<assistant>"
        return {"input_ids": self.encode(text), "attention_mask": [1] * len(self.encode(text))} if tokenize else text


class FixtureGym(ReasoningGymGym):
    def __init__(self):
        super().__init__(require_package=False, strict_verifier=True)

    def _item(self, family, seed):
        return self, {"question": "Submit north.", "answer": "SEALED_NOT_FOR_TEACHER"}

    def score_answer(self, answer, entry):
        return .5


class FixtureModel:
    def __init__(self, path):
        self.path = path
        self.tok = FixtureTokenizer()
        self.note = 'I submitted "north"; the score was 0.50.'
        self.wake = "NOTE: I should inspect this attempt.\nACT: north"
        self.identity_change = False

    def generation_identity(self):
        return configured_generation_identity("WRONG" if self.identity_change else self.path, None)

    def batch(self, prompts, max_tokens=400, seeds=None, temperature=.7):
        return [self.note if prompt.endswith("NOTE_AFTER:") else self.wake for prompt in prompts]


class OneTickDriver(diagnostic.DiagnosticDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.st.budget_ticks = 1


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.cleanup)
        self.model_dir = self.root / "base"
        self.model_dir.mkdir()
        (self.model_dir / "config.json").write_text(json.dumps(dict(model_type="qwen2", num_hidden_layers=28, hidden_size=3584)))
        (self.model_dir / "tokenizer.json").write_text('{}')
        (self.model_dir / "tokenizer_config.json").write_text('{}')
        (self.model_dir / "model.safetensors").write_bytes(b"EXPLICIT SYNTHETIC CPU BASE")
        self.config = diagnostic.Config(str(self.root / "lesson"), "lesson", str(self.model_dir), diagnostic.local_files(self.model_dir))
        self.gym = FixtureGym()
        self.model = FixtureModel(str(self.model_dir))
        self.closed = 0
        self.loaded = 0

    def cleanup(self):
        for path in self.root.rglob("*"):
            if path.is_dir():
                path.chmod(0o755)
        self.temporary.cleanup()

    @contextmanager
    def backend(self, model_path):
        self.assertEqual(model_path, str(self.model_dir))
        self.loaded += 1
        try:
            yield self.model
        finally:
            self.closed += 1

    def stage(self, name="sample", mode="lesson", note=None, wake=None):
        out = self.root / name
        out.mkdir()
        ledger = Ledger(str(out / "ledger.jsonl"))
        Path(ledger.path).touch()
        (out / "generations.jsonl").touch()
        teacher = policy.deliver_lesson(str(out), mode, 0, ledger=ledger)
        if note is not None:
            self.model.note = note
        if wake is not None:
            self.model.wake = wake
        observed = diagnostic.ObservedBackend(self.model, str(self.model_dir), out, teacher)
        episode = self.gym.episode_from_id(self.gym.training_schedule(64, 6101)[0], 1)
        run_episodes_batch(observed, self.gym, [episode], self.gym.birth_prompt() + "\n\n" + teacher,
            ledger, 1, log=lambda message: None, gen_seed=7101, driver_cls=diagnostic.DiagnosticDriver,
            note_after=policy.PostOutcomeSlot(max_tokens=100))
        return out

    def test_rendered_clock_ignores_birth_and_elapsed_walltime(self):
        episode = self.gym.episode_from_id(self.gym.training_schedule(64, 6101)[0], 16)
        driver = diagnostic.DiagnosticDriver(episode, self.gym.birth_prompt(), self.gym,
                                             Ledger(str(self.root / "clock.jsonl")), 16)
        self.assertIsInstance(driver.st, diagnostic.DiagnosticState)
        self.assertGreater(driver.st.born_at, 0)
        driver.st.tick = 6
        driver.st.last_progress_tick = 3
        first = driver.prompt()
        before = time.time_ns()
        time.sleep(.002)
        self.assertGreater(time.time_ns(), before)
        driver.st.born_at -= 100000
        driver.st.tick = 6
        second = driver.prompt()
        self.assertEqual(first, second)
        self.assertIn("CLOCK: chunk 7/16 | chunks since last progress: 4", second)
        self.assertNotIn("alive", second)
        self.assertIn("alive", diagnostic.State(tick=7, budget_ticks=16).clock_line())

    def test_full_fixed_pair_no_training_or_lineage_and_same_schedule(self):
        from organism_v6 import train_adapter, life_lineage, lineage_guard
        with patch.object(policy, "gate_sleep", side_effect=AssertionError("no clean gate")) as gate, \
                patch.object(train_adapter, "main", side_effect=AssertionError("no training")) as training, \
                patch.object(life_lineage, "record_sleep", side_effect=AssertionError("no lineage")) as lineage, \
                patch.object(lineage_guard, "validate_manifest", side_effect=AssertionError("no eligibility")) as guard:
            results = []
            for mode in ("lesson", "sham"):
                results.append(diagnostic.run(replace(self.config, mode=mode, out=str(self.root / mode)),
                                              gym=self.gym, backend_factory=self.backend))
            for forbidden in (gate, training, lineage, guard):
                forbidden.assert_not_called()
        self.assertEqual((self.loaded, self.closed), (2, 2))
        self.assertEqual((self.root / "lesson/schedule.json").read_bytes(), (self.root / "sham/schedule.json").read_bytes())
        for mode, result in zip(("lesson", "sham"), results):
            self.assertEqual(result["n_actions"], 1024)
            self.assertEqual(result["n_measured_actions"], 1024)
            self.assertEqual(result["n_post_outcome_records"], 1024)
            self.assertEqual(result["n_grounded_records"], 1024)
            self.assertEqual(result["n_unique_grounded_records"], 1)
            self.assertEqual(result["actual_teacher_presentations"], 2048)
            self.assertEqual(result["teacher_receipts"], 1)
            self.assertEqual(result["evaluation"], "NONE")
            self.assertFalse(result["clean_lineage"])
            self.assertEqual(result["label"], "EXPLORATORY_LOCAL_BASE")
            root = self.root / mode
            rows = [json.loads(line) for line in (root / "ledger.jsonl").read_bytes().splitlines()]
            self.assertEqual(sum(row["kind"] == "note" for row in rows), 1024)
            self.assertTrue(all(self.gym.split_of(row["episode_id"]) == "train" for row in rows if "episode_id" in row))
            self.assertFalse((root / "corpus.json").exists())
            self.assertFalse((root / "manifest.json").exists())
            self.assertEqual((root / "config.json").stat().st_mode & 0o222, 0)
            self.assertEqual(json.loads((root / "config.json").read_bytes())["protocol"], diagnostic.SCHEDULE)

    def test_real_source_join_and_missing_source_rejection(self):
        out = self.stage()
        result = diagnostic.summarize(out)
        self.assertEqual(result["n_unique_grounded_records"], 1)
        rows = [json.loads(line) for line in (out / "ledger.jsonl").read_bytes().splitlines()]
        rows = [row for row in rows if row["kind"] != "act"]
        (out / "ledger.jsonl").write_bytes(b"".join(policy._encoded(row) for row in rows))
        result = diagnostic.summarize(out)
        self.assertEqual(result["n_unique_grounded_records"], 0)
        self.assertEqual(result["rejection_reasons"]["provenance-orphan"], 1)
        self.assertIsNone(result["unique_per_measured_action"])

    def test_default_and_explicit_seeds_preserve_protocol_teacher_and_generation(self):
        implicit = replace(self.config, out=str(self.root / "implicit"))
        explicit = replace(self.config, out=str(self.root / "explicit"), schedule_seed=6101, generation_seed=7101)
        self.assertEqual(diagnostic.protocol(), diagnostic.SCHEDULE)
        for config in (implicit, explicit):
            with patch.object(diagnostic, "DiagnosticDriver", OneTickDriver):
                diagnostic.run(config, gym=self.gym, backend_factory=self.backend)
            stored = json.loads((Path(config.out) / "config.json").read_bytes())
            self.assertEqual(stored["protocol"], diagnostic.SCHEDULE)
            self.assertEqual((stored["schedule_seed"], stored["generation_seed"]), (6101, 7101))
        for name in ("schedule.json", "lesson_deliveries.jsonl", "teaching_dose.json"):
            self.assertEqual((Path(implicit.out) / name).read_bytes(), (Path(explicit.out) / name).read_bytes())
        events = [[json.loads(line) for line in (Path(config.out) / "generations.jsonl").read_bytes().splitlines()]
                  for config in (implicit, explicit)]
        for field, kind in (("seed", "request"), ("prompt", "request"), ("text", "output")):
            self.assertEqual([event[field] for event in events[0] if event["kind"] == kind],
                             [event[field] for event in events[1] if event["kind"] == kind])
        replication = replace(self.config, out=str(self.root / "generation_only"), generation_seed=7201)
        with patch.object(diagnostic, "DiagnosticDriver", OneTickDriver):
            diagnostic.run(replication, gym=self.gym, backend_factory=self.backend)
        self.assertEqual((Path(implicit.out) / "schedule.json").read_bytes(),
                         (Path(replication.out) / "schedule.json").read_bytes())
        changed = [json.loads(line) for line in (Path(replication.out) / "generations.jsonl").read_bytes().splitlines()]
        self.assertNotEqual([event["seed"] for event in events[0] if event["kind"] == "request"],
                            [event["seed"] for event in changed if event["kind"] == "request"])

    def test_custom_seeds_drive_actual_training_schedule_and_generation(self):
        config = replace(self.config, schedule_seed=6201, generation_seed=7201)
        with patch.object(diagnostic, "DiagnosticDriver", OneTickDriver), \
                patch.object(diagnostic.batch_loop, "run_episodes_batch", wraps=run_episodes_batch) as batches:
            diagnostic.run(config, gym=self.gym, backend_factory=self.backend)
        out = Path(config.out)
        schedule = json.loads((out / "schedule.json").read_bytes())
        self.assertEqual(schedule, self.gym.training_schedule(64, 6201))
        self.assertNotEqual(schedule, self.gym.training_schedule(64, 6101))
        self.assertTrue(all(self.gym.split_of(episode) == "train" for episode in schedule))
        self.assertEqual(len(batches.call_args_list), 8)
        self.assertTrue(all(call.kwargs["gen_seed"] == 7201 for call in batches.call_args_list))
        events = [json.loads(line) for line in (out / "generations.jsonl").read_bytes().splitlines()]
        wakes = [event for event in events if event["kind"] == "request" and event["max_tokens"] == 400]
        self.assertEqual([event["seed"] for event in wakes],
                         [diagnostic.batch_loop._seed_for(episode, 1, 7201) for episode in schedule])
        self.assertEqual(json.loads((out / "config.json").read_bytes())["protocol"], diagnostic.protocol(6201, 7201))
        receipt = policy._lesson_rows((out / "lesson_deliveries.jsonl").read_bytes())[0]
        self.assertEqual(receipt, policy.lesson_receipt("lesson", 0))

    def test_invalid_seeds_rejected_before_input_reads_or_backend(self):
        for name in ("schedule_seed", "generation_seed"):
            for value in (True, False, -1, 0x80000000, 1.0, "7101", None):
                with self.subTest(name=name, value=value), self.assertRaisesRegex(ValueError, "invalid " + name):
                    replace(self.config, **{name: value})
        self.assertEqual((self.loaded, self.closed), (0, 0))
        self.assertFalse(Path(self.config.out).exists())
        self.assertEqual(diagnostic.protocol(0, 0x7fffffff)["generation_seed"], 0x7fffffff)

    def test_config_cli_accepts_explicit_seeds_without_new_flags(self):
        path = self.root / "replication.json"
        payload = dict(out=self.config.out, mode="lesson", model_path=self.config.model_path,
                       expected_files=self.config.expected_files, schedule_seed=6201, generation_seed=7201)
        path.write_text(json.dumps(payload))
        with patch.object(diagnostic, "ReasoningGymGym", return_value=self.gym), \
                patch.object(diagnostic, "run", return_value={}) as run:
            diagnostic.main(["--config", str(path), "--execute"])
        self.assertEqual(run.call_args.args[0], diagnostic.Config(**payload))
        with self.assertRaises(TypeError):
            diagnostic.Config(**dict(payload, teacher_variant="matched_sham"))

    def test_actual_wake_output_required(self):
        out = self.stage()
        events = [json.loads(line) for line in (out / "generations.jsonl").read_bytes().splitlines()]
        events = [row for row in events if not (row["kind"] == "output" and row["request_index"] == 0)]
        (out / "generations.jsonl").write_bytes(b"".join(policy._encoded(row) for row in events))
        result = diagnostic.summarize(out)
        self.assertEqual(result["rejection_reasons"]["source-not-in-actual-wake-generation"], 1)

    def test_teacher_echo_invalid_record_and_null_denominator(self):
        for index, text in enumerate((policy.lesson_block("lesson", 0), "I plan to reflect.",
                                      'I submitted "north"; the score was 1.00.')):
            result = diagnostic.summarize(self.stage(str(index), note=text))
            self.assertTrue(result["no_writer_qualified"])
            self.assertEqual(result["n_measured_actions"], 1)
            self.assertEqual(result["n_unique_grounded_records"], 0)
        result = diagnostic.summarize(self.stage("empty", wake="NOTE: I should think."))
        self.assertEqual(result["n_actions"], 0)
        self.assertIsNone(result["unique_per_measured_action"])

    def test_actual_note_output_required_and_hash_checked(self):
        out = self.stage()
        events = [json.loads(line) for line in (out / "generations.jsonl").read_bytes().splitlines()]
        missing = [row for row in events if not (row["kind"] == "output" and row["request_index"] == 1)]
        (out / "generations.jsonl").write_bytes(b"".join(policy._encoded(row) for row in missing))
        result = diagnostic.summarize(out)
        self.assertEqual(result["rejection_reasons"]["record-not-in-actual-note-generation"], 1)
        events[-1]["text"] = "changed actual output"
        (out / "generations.jsonl").write_bytes(b"".join(policy._encoded(row) for row in events))
        with self.assertRaisesRegex(ValueError, "actual generation hash mismatch"):
            diagnostic.summarize(out)

    def test_transformers_dict_is_not_token_count(self):
        out = self.stage()
        events = [json.loads(line) for line in (out / "generations.jsonl").read_bytes().splitlines()]
        for entry in events:
            if entry["kind"] == "request":
                self.assertGreater(entry["prompt_tokens"], 2)
                self.assertEqual(entry["prompt_tokens"], len(self.model.tok.encode(entry["rendered_prompt"], add_special_tokens=False)))
                self.assertNotIn("SEALED_NOT_FOR_TEACHER", entry["prompt"])

    def test_pins_identity_existing_output_and_strict_verifier(self):
        with self.assertRaisesRegex(ValueError, "pins mismatch"):
            diagnostic.run(replace(self.config, expected_files={}), gym=self.gym, backend_factory=self.backend)
        self.assertEqual(self.loaded, 0)
        self.gym.strict_verifier = False
        with self.assertRaisesRegex(ValueError, "strict"):
            diagnostic.run(self.config, gym=self.gym, backend_factory=self.backend)
        self.gym.strict_verifier = True
        self.model.identity_change = True
        with self.assertRaisesRegex(ValueError, "identity changed"):
            diagnostic.run(self.config, gym=self.gym, backend_factory=self.backend)
        self.assertEqual(self.closed, 1)
        self.assertTrue((self.root / "lesson/failure.json").is_file())
        self.assertTrue((self.root / "lesson/partial_results.json").is_file())
        with self.assertRaises(FileExistsError):
            diagnostic.run(self.config, gym=self.gym, backend_factory=self.backend)

    def test_no_execute_means_no_model_load(self):
        with patch.object(diagnostic, "local_backend") as backend:
            with self.assertRaises(SystemExit):
                diagnostic.main(["--config", "/not/read"])
            backend.assert_not_called()


if __name__ == "__main__":
    unittest.main()
