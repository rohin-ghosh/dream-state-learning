"""Synthetic CPU material tests; no package, tokenizer weights or model execution."""
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
import copy
import io
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import batch_loop, reasoning_gym_gym, train_adapter_v3
from organism_v6 import mini_sudoku_behavior_material as material


class FixtureTokenizer:
    eos_token_id = 900000

    def encode(self, text, add_special_tokens=False):
        return [ord(character) for character in text]

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return "<user>" + messages[0]["content"] + "</user><assistant>"


class FixtureDataset:
    def score_answer(self, *, answer, entry):
        return 1.0 if answer == entry["answer"] else 0.25


class FixtureGym(reasoning_gym_gym.ReasoningGymGym):
    def __init__(self):
        super().__init__(require_package=False, strict_verifier=True)
        self.entries = {}
        self.dataset = FixtureDataset()
        base = [[1, 2, 3, 4], [3, 4, 1, 2], [2, 1, 4, 3], [4, 3, 2, 1]]
        grids = []
        for digits in itertools.permutations((1, 2, 3, 4)):
            for order in ((0, 1, 2, 3), (1, 0, 2, 3)):
                grids.append([[digits[cell - 1] for cell in base[row]] for row in order])
        for index, episode_id in enumerate(material.TRAIN_IDS + material.EVAL_IDS):
            solution = grids[index]
            puzzle = copy.deepcopy(solution)
            puzzle[index % 4][(index // 4) % 4] = 0
            self.entries[episode_id] = self.entry(puzzle, solution)

    @staticmethod
    def entry(puzzle, solution):
        return dict(question="Complete the mini sudoku.\n" + "\n".join(
            " ".join(str(cell) if cell else "_" for cell in row) for row in puzzle),
            answer="\n".join(" ".join(map(str, row)) for row in solution),
            metadata=dict(puzzle=puzzle, solution=solution,
                          num_empty=sum(cell == 0 for row in puzzle for cell in row),
                          source_dataset="mini_sudoku", source_index=0))

    def _item(self, family, seed):
        return self.dataset, self.entries[f"rg/{family}/{seed}"]


class MaterialTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.model = self.root / "model"
        self.model.mkdir()
        (self.model / "config.json").write_text(json.dumps(dict(
            model_type="qwen2", num_hidden_layers=28, hidden_size=3584)))
        for name in ("tokenizer.json", "tokenizer_config.json"):
            (self.model / name).write_text("{}")
        (self.model / "model.safetensors").write_bytes(b"synthetic-not-real-weights")
        self.gym = FixtureGym()
        self.tokenizer = FixtureTokenizer()
        self.out = self.root / "inputs"
        self.training = self.root / "training"

    def tearDown(self):
        self.temporary.cleanup()

    def prepare(self, **kwargs):
        return material.prepare(self.out, self.model, self.training,
                                gym=self.gym, tokenizer=kwargs.pop("tokenizer", self.tokenizer), **kwargs)

    def read(self, name):
        return json.loads((self.out / name).read_bytes())

    def test_real_helpers_prepare_fixed_native_prompts_and_loss(self):
        before = copy.deepcopy(self.gym.entries)
        result = self.prepare()
        useful = self.read("useful.json")["corpus"]
        corrupt = self.read("corrupt.json")["corpus"]
        self.assertEqual(len(useful), 32)
        self.assertEqual([row["episode_id"] for row in useful], list(material.TRAIN_IDS))
        self.assertEqual([row["q"] for row in useful], [row["q"] for row in corrupt])
        self.assertEqual(Counter(row["a"] for row in useful), Counter(row["a"] for row in corrupt))
        self.assertEqual(self.gym.entries, before)
        for index, row in enumerate(useful):
            episode = self.gym.episode_from_id(row["episode_id"], 1)
            driver = batch_loop.driver_class_for(self.gym)(episode, self.gym.birth_prompt(), self.gym, None, 1)
            self.assertEqual(row["q"], driver.prompt())
            self.assertTrue(row["q"].endswith("\n"))
            self.assertIn("CLOCK: chunk 1/1 | alive 0s", row["q"])
            self.assertEqual(corrupt[index]["a"], useful[(index + 1) % 32]["a"])
            item = train_adapter_v3.normalize_items(dict(corpus=[row]))[0]
            encoded = train_adapter_v3.encode_item(item, self.tokenizer, 4096, chat_template=False)
            context_ids = self.tokenizer.encode(row["rendered_q"])
            self.assertEqual(encoded.ids[:len(context_ids)], context_ids)
            self.assertEqual(encoded.labels[:len(context_ids)], [-100] * len(context_ids))
            self.assertEqual(encoded.labels[len(context_ids):], self.tokenizer.encode(row["a"]) +
                             [self.tokenizer.eos_token_id])
        self.assertEqual(result["boundary"]["validation_backend"], "SYNTHETIC_CPU_FIXTURE")
        self.assertFalse(result["boundary"]["child_authored_targets"])
        self.assertEqual(self.read("validation.json")["expected_steps_per_fit"], 96)
        self.assertEqual(len(self.read("oracle_sources.json")["records"]), 48)

    def test_no_rstrip_or_double_template(self):
        self.prepare()
        row = self.read("useful.json")["corpus"][0]
        rendered = self.tokenizer.apply_chat_template([dict(role="user", content=row["q"])])
        stripped = self.tokenizer.apply_chat_template([dict(role="user", content=row["q"].rstrip("\n"))])
        self.assertNotEqual(rendered, stripped)
        self.assertEqual(row["spans"][0], [rendered, False, "native_context"])
        self.assertEqual(rendered.count("<user>"), 1)
        commands = self.read("trainer_commands.json")["commands"]
        self.assertTrue(all("--chat-template" not in command["argv"] for command in commands.values()))

    def test_native_clock_is_not_overridden(self):
        with patch("organism_v6.batch_loop.time.time", side_effect=[100.0, 102.0]):
            prompt = material.one_tick_prompt(self.gym, material.TRAIN_IDS[0])
        self.assertIn("CLOCK: chunk 1/1 | alive 2s", prompt)

    def test_command_recipe_is_two_seed_zero_fits_only(self):
        with patch("subprocess.Popen", side_effect=AssertionError("must not launch")):
            self.prepare()
        spec = self.read("trainer_commands.json")
        self.assertEqual(set(spec["commands"]), {"useful", "corrupt"})
        self.assertFalse(spec["future_seeds_scheduled"])
        for command in spec["commands"].values():
            argv = command["argv"]
            args = train_adapter_v3.build_parser().parse_args(argv[argv.index("--corpus"):])
            config = train_adapter_v3.config_from_args(args)
            self.assertEqual((config.rank, config.lr, config.epochs, config.seed,
                              config.batch_size, config.max_len), (8, 1e-4, 3, 0, 1, 4096))
            self.assertFalse(config.pack)
            self.assertFalse(config.chat_template)
            self.assertEqual(command["expected_steps"], 96)
            self.assertFalse(command["execute"])
            self.assertFalse(command["shell"])
            self.assertNotIn(self.out, Path(command["exclusive_stdout_stderr_log"]).parents)
        self.assertFalse(self.training.exists())

    def test_virtualenv_python_symlink_is_not_resolved_to_system_python(self):
        target = self.root / "system_python"
        target.write_text("synthetic executable identity")
        interpreter = self.root / "venv" / "bin" / "python"
        interpreter.parent.mkdir(parents=True)
        interpreter.symlink_to(target)
        self.prepare(python_executable=interpreter)
        for command in self.read("trainer_commands.json")["commands"].values():
            self.assertEqual(command["argv"][0], str(interpreter))
            self.assertNotEqual(command["argv"][0], str(target))

    def test_training_seed_commands_paths_and_default_unchanged(self):
        interpreter = self.root / "venv" / "bin" / "python"
        defaults = material.trainer_commands(self.out, self.training, self.model, interpreter)
        self.assertEqual(defaults, material.trainer_commands(
            self.out, self.training, self.model, interpreter, training_seed=0))
        for seed in (1, 2):
            commands = material.trainer_commands(self.out, self.training, self.model, interpreter,
                                                 training_seed=seed)
            for arm, command in commands.items():
                expected = copy.deepcopy(defaults[arm])
                expected["argv"][expected["argv"].index("--seed") + 1] = str(seed)
                expected["argv"][expected["argv"].index("--out") + 1] = str(
                    self.training / f"{arm}_seed{seed}")
                expected["exclusive_stdout_stderr_log"] = str(self.training / f"{arm}_seed{seed}.log")
                expected["seed"] = seed
                self.assertEqual(command, expected)

    def test_training_seed_does_not_change_corpus_ids_or_token_validation(self):
        baseline = None
        for seed in (None, 0, 1, 2):
            self.out = self.root / f"inputs_{seed}"
            kwargs = {} if seed is None else dict(training_seed=seed)
            with patch("organism_v6.batch_loop.time.time", return_value=100.0):
                self.prepare(**kwargs)
            content = {name: (self.out / name).read_bytes() for name in
                       ("useful.json", "corrupt.json", "ids.json", "oracle_sources.json")}
            validation = self.read("validation.json")
            self.assertEqual(validation.pop("training_seed"), 0 if seed is None else seed)
            content["validation_without_seed"] = material._encoded(validation)
            if baseline is None:
                baseline = content
            self.assertEqual(content, baseline)
            actual_seed = seed if seed is not None else 0
            spec = self.read("trainer_commands.json")
            self.assertEqual(spec["training_seed"], actual_seed)
            for arm, command in spec["commands"].items():
                self.assertEqual(command["seed"], actual_seed)
                self.assertEqual(command["argv"][command["argv"].index("--seed") + 1], str(actual_seed))
                self.assertEqual(command["argv"][command["argv"].index("--out") + 1],
                                 str(self.training / f"{arm}_seed{actual_seed}"))
            self.assertFalse(spec["future_seeds_scheduled"])
            self.assertEqual(spec["future_seeds"], [value for value in (1, 2) if value > actual_seed])
            self.assertIn(f"seed{actual_seed} ", spec["after_training_required"][1])

    def test_invalid_training_seeds_rejected_before_material_reads(self):
        for seed in (-1, 3, 100, True, False, 1.0, "1", None):
            with self.subTest(seed=seed):
                with patch.object(material.parent_material_diagnostic, "local_files",
                                  side_effect=AssertionError("must reject seed first")):
                    with self.assertRaisesRegex(ValueError, "training_seed"):
                        self.prepare(training_seed=seed)
                with self.assertRaisesRegex(ValueError, "training_seed"):
                    material.trainer_commands(self.out, self.training, self.model, self.root / "python",
                                              training_seed=seed)
        self.assertFalse(self.out.exists())

    def test_seed_specific_output_and_log_conflicts(self):
        self.training.mkdir()
        for seed in (1, 2):
            destination = self.training / f"useful_seed{seed}"
            destination.mkdir()
            with self.assertRaisesRegex(ValueError, "trainer destination"):
                material.trainer_commands(self.out, self.training, self.model, self.root / "python", seed)
            log = self.training / f"corrupt_seed{seed}.log"
            log.write_text("preserved attempt")
        material.trainer_commands(self.out, self.training, self.model, self.root / "python")
        separate = self.root / "only_logs"
        separate.mkdir()
        (separate / "corrupt_seed2.log").write_text("preserved log")
        with self.assertRaisesRegex(ValueError, "external trainer log"):
            material.trainer_commands(self.out, separate, self.model, self.root / "python", training_seed=2)

    def test_cli_training_seed_default_choices_and_forwarding(self):
        argv = ["--out", str(self.out), "--model-path", str(self.model),
                "--training-root", str(self.training)]
        for seed in (None, 0, 1, 2):
            extra = [] if seed is None else ["--training-seed", str(seed)]
            with patch.object(material, "prepare", return_value={}) as prepare, redirect_stdout(io.StringIO()):
                material.main(argv + extra)
            self.assertEqual(prepare.call_args.kwargs["training_seed"], 0 if seed is None else seed)
        for value in ("-1", "3", "1.0", "true"):
            with patch.object(material, "prepare") as prepare, redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    material.main(argv + ["--training-seed", value])
            self.assertEqual(error.exception.code, 2)
            prepare.assert_not_called()

    def test_ids_history_and_no_eval_targets_in_training(self):
        self.prepare()
        ids = self.read("ids.json")
        self.assertEqual(ids["canary"], list(material.EVAL_IDS))
        self.assertIn("rg/mini_sudoku/1900069", ids["declared_prior_cpu_examined_ids"])
        self.assertIn("rg/mini_sudoku/1001000", ids["declared_prior_cpu_examined_ids"])
        self.assertIn("rg/mini_sudoku/1002015", ids["declared_prior_cpu_examined_ids"])
        self.assertIn("rg/mini_sudoku/1900042", ids["declared_prior_cpu_examined_ids"])
        for arm in ("useful", "corrupt"):
            self.assertFalse(set(row["episode_id"] for row in self.read(arm + ".json")["corpus"])
                             & set(material.EVAL_IDS))

    def test_duplicate_actual_board_rejects_without_replacement(self):
        self.gym.entries[material.EVAL_IDS[0]] = copy.deepcopy(self.gym.entries[material.TRAIN_IDS[0]])
        with self.assertRaisesRegex(ValueError, "duplicate actual board"):
            self.prepare()
        self.assertFalse(self.out.exists())

    def test_solution_overlap_is_disclosed_not_rerolled(self):
        solution = self.gym.entries[material.TRAIN_IDS[0]]["metadata"]["solution"]
        puzzle = copy.deepcopy(solution)
        puzzle[1][1] = 0
        self.gym.entries[material.EVAL_IDS[0]] = self.gym.entry(puzzle, solution)
        self.prepare()
        self.assertIn(material.EVAL_IDS[0], self.read("validation.json")["solution_overlap_eval_ids"])

    def test_wrong_donor_native_acceptance_rejects(self):
        with patch.object(self.gym.dataset, "score_answer", return_value=1.0):
            with self.assertRaisesRegex(ValueError, "donor accepted"):
                self.prepare()

    def test_independent_given_check_even_if_native_rejects(self):
        previous = self.gym.entries[material.TRAIN_IDS[0]]
        donor = self.gym.entries[material.TRAIN_IDS[1]]["metadata"]["solution"]
        puzzle = [[0] * 4 for _ in range(4)]
        for row in range(4):
            for col in range(4):
                if previous["metadata"]["solution"][row][col] == donor[row][col]:
                    puzzle[row][col] = donor[row][col]
        self.gym.entries[material.TRAIN_IDS[0]] = self.gym.entry(puzzle, previous["metadata"]["solution"])
        with self.assertRaisesRegex(ValueError, "does not violate recipient givens"):
            self.prepare()

    def test_native_bad_score_fails_closed(self):
        for value in (float("nan"), float("inf"), -1, True, 0.5):
            with self.subTest(value=value):
                with patch.object(self.gym.dataset, "score_answer", return_value=value):
                    with self.assertRaises(ValueError):
                        self.prepare()

    def test_metadata_question_and_answer_binding(self):
        self.gym.entries[material.TRAIN_IDS[0]]["metadata"]["puzzle"][0][0] = 4
        with self.assertRaisesRegex(ValueError, "disagree with native metadata"):
            self.prepare()

    def test_independent_rows_columns_boxes_and_givens(self):
        empty = [[0] * 4 for _ in range(4)]
        solution = self.gym.entries[material.TRAIN_IDS[0]]["metadata"]["solution"]
        material.validate_solution(empty, solution)
        with self.assertRaisesRegex(ValueError, "row"):
            material.validate_solution(empty, [[1] * 4 for _ in range(4)])
        with self.assertRaisesRegex(ValueError, "column"):
            material.validate_solution(empty, [[1, 2, 3, 4] for _ in range(4)])
        with self.assertRaisesRegex(ValueError, "2x2"):
            material.validate_solution(empty, [[1, 2, 3, 4], [2, 3, 4, 1],
                                                [3, 4, 1, 2], [4, 1, 2, 3]])
        empty[0][0] = 4
        with self.assertRaisesRegex(ValueError, "givens"):
            material.validate_solution(empty, solution)

    def test_truncation_and_missing_eos_fail_preflight(self):
        class LongTokenizer(FixtureTokenizer):
            def encode(self, text, add_special_tokens=False):
                return super().encode(text) * 10
        with self.assertRaisesRegex(ValueError, "would truncate"):
            self.prepare(tokenizer=LongTokenizer())
        tokenizer = FixtureTokenizer()
        tokenizer.eos_token_id = None
        with self.assertRaisesRegex(ValueError, "EOS required"):
            self.prepare(tokenizer=tokenizer)
        self.assertFalse(self.out.exists())

    def test_actual_collated_context_loss_tamper_rejects(self):
        real = train_adapter_v3.collate
        def bad_collate(*args, **kwargs):
            result = real(*args, **kwargs)
            result["labels"][0][1] = result["input_ids"][0][1]
            return result
        with patch.object(train_adapter_v3, "collate", side_effect=bad_collate):
            with self.assertRaisesRegex(ValueError, "context supervision"):
                self.prepare()

    def test_files_hashes_readonly_and_output_conflict(self):
        manifest = self.prepare()
        for name, digest in manifest["files"].items():
            path = self.out / name
            self.assertEqual(material._sha(path.read_bytes()), digest)
            self.assertEqual(path.stat().st_mode & 0o222, 0)
        self.assertEqual(self.out.stat().st_mode & 0o222, 0)
        before = (self.out / "manifest.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "output already exists"):
            self.prepare()
        self.assertEqual((self.out / "manifest.json").read_bytes(), before)

    def test_trainer_output_conflict_and_overlapping_roots(self):
        self.training.mkdir()
        (self.training / "useful_seed0").mkdir()
        with self.assertRaisesRegex(ValueError, "trainer destination"):
            self.prepare()
        with self.assertRaisesRegex(ValueError, "must be disjoint"):
            material.prepare(self.out, self.model, self.out / "adapters",
                             gym=self.gym, tokenizer=self.tokenizer)

    def test_source_and_model_drift_reject(self):
        real = material._sources
        calls = []
        def changed(gym):
            snapshot = real(gym)
            calls.append(True)
            if len(calls) > 1:
                snapshot[__file__] = "changed"
            return snapshot
        with patch.object(material, "_sources", side_effect=changed):
            with self.assertRaisesRegex(ValueError, "implementation changed"):
                self.prepare()
        pins = material.parent_material_diagnostic.local_files(self.model)
        with patch.object(material.parent_material_diagnostic, "local_files",
                          side_effect=[pins, dict(pins, changed="changed")]):
            with self.assertRaisesRegex(ValueError, "local base changed"):
                self.prepare()

    def test_missing_native_package_cannot_claim_prepared(self):
        with patch.object(reasoning_gym_gym, "installed_version", return_value=None):
            with self.assertRaisesRegex(ValueError, "actual node CPU preflight"):
                material.prepare(self.out, self.model, self.training)
        self.assertFalse(self.out.exists())

    def test_ambiguous_or_noncanonical_board_text_rejects(self):
        with self.assertRaises(ValueError):
            material.board_from_text("1 2 3 4\n" * 5, question=True)
        with self.assertRaises(ValueError):
            material.board_from_text("garbage\n" + "1 2 3 4\n" * 4)


if __name__ == "__main__":
    unittest.main()
