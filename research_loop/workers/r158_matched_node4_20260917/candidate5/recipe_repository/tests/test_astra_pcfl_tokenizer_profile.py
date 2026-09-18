"""Synthetic CPU-only tokenizer timing tests; no real tokenizer or model load."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import astra_pcfl_tokenizer_profile as profile_api
from organism_v6 import pcfl_tokenizer_qualification as qualifier_api


class Clock:
    def __init__(self):
        self.value = 0

    def __call__(self):
        self.value += 1000
        return self.value


class Tokenizer:
    chat_template = "SYNTHETIC_TEMPLATE"

    def __init__(self, model):
        self.name_or_path = str(model)
        self.calls = []
        self.output = lambda text: [ord(character) for character in text]

    def encode(self, text, *, add_special_tokens, truncation):
        assert add_special_tokens is False and truncation is False
        self.calls.append(text)
        return self.output(text)


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="pcfl_token_profile_test_")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.model = self.root / "model"
        self.model.mkdir()
        for name in ("config.json", "tokenizer_config.json", "tokenizer.json", "vocab.json", "merges.txt"):
            (self.model / name).write_text("SYNTHETIC/" + name)
        (self.model / "model.safetensors").write_bytes(b"NEVER_READ_TEST_SENTINEL")
        self.output = self.root / "profile"
        self.tokenizer = Tokenizer(self.model)
        self.loader = Mock(return_value=self.tokenizer)
        self.clock = Clock()
        self.flags = {"CUDA_VISIBLE_DEVICES": "", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1"}
        self.environment_patch = patch.dict(os.environ, self.flags)
        self.environment_patch.start()
        self.addCleanup(self.environment_patch.stop)

    def run_profile(self, **kwargs):
        return profile_api.run_profile(str(self.model), str(self.output), tokenizer_loader=self.loader,
                                       environment_reader=lambda: {"python": "SYNTHETIC", "packages": {}},
                                       clock_ns=self.clock, **kwargs)

    def records(self, filename="candidates.jsonl"):
        return [json.loads(line) for line in (self.output / filename).read_bytes().splitlines()]

    def test_exact_4096_real_candidate_generator_and_token_receipts(self):
        with (
            patch.object(qualifier_api, "opaque_candidate", wraps=qualifier_api.opaque_candidate) as candidate,
            patch.object(qualifier_api, "qualify_opaque_ids", side_effect=AssertionError("no qualification")),
        ):
            report = self.run_profile()
        self.assertEqual(candidate.call_count, 4096)
        self.assertEqual(candidate.call_args_list[0].args, ("excluded/0", "node", 0, 0))
        self.assertEqual(candidate.call_args_list[-1].args, ("excluded/0", "node", 0, 4095))
        records = self.records()
        self.assertEqual([record["salt"] for record in records], list(range(4096)))
        self.assertEqual(self.tokenizer.calls, [record["text"] for record in records])
        for record in records:
            self.assertEqual(record["text"], qualifier_api.opaque_candidate("excluded/0", "node", 0, record["salt"]))
            self.assertEqual(record["token_ids_sha256"], profile_api.digest(record["token_ids"]))
            self.assertEqual(record["token_ids"], [ord(character) for character in record["text"]])
            self.assertEqual(record["encode_elapsed_ns"], 1000)
        self.assertEqual(report["candidate_summary"]["distinct_candidates"], 4096)
        self.assertEqual(report["candidate_summary"]["token_length_distribution"], {"12": 4096})
        self.assertEqual(report["candidate_summary"]["encode_elapsed_ns_total"], 4096000)
        self.assertEqual(report["candidate_receipts_sha256"], profile_api.file_hash(self.output / "candidates.jsonl"))
        self.assertEqual(report["kind"], "SYNTHETIC_CPU_FIXTURE")
        self.assertFalse(report["qualified"])
        self.assertFalse(report["ready_for_model_calls"])
        self.assertFalse(report["selection_performed"])
        self.assertFalse(report["allocator_changed"])
        self.assertIsNone(report["provisional_roots"])

    def test_no_filtering_even_when_all_lengths_outside_qualifier_band(self):
        self.tokenizer.output = lambda text: [7]
        report = self.run_profile()
        self.assertEqual(len(self.tokenizer.calls), 4096)
        self.assertEqual(report["candidate_summary"]["token_length_distribution"], {"1": 4096})
        self.assertEqual(report["candidate_summary"]["distinct_candidates"], 4096)
        self.assertEqual(report["candidate_summary"]["distinct_token_sequences"], 1)

    def test_mixed_distribution_is_observed_not_selected(self):
        self.tokenizer.output = lambda text: [9] * (2 + ord(text[-1]) % 3)
        report = self.run_profile()
        distribution = report["candidate_summary"]["token_length_distribution"]
        self.assertEqual(sum(distribution.values()), 4096)
        self.assertEqual(set(distribution), {"2", "3", "4"})
        self.assertEqual(report["encode_attempts"], 4096)

    def test_optional_raw_roots_are_separate_and_unqualified(self):
        from organism_v6 import pcfl_vertical_dev as core_api

        expected_count = 4 * sum(len(slots) for slots in core_api.SLOTS.values())
        report = self.run_profile(include_provisional_roots=True)
        self.assertEqual(len(self.tokenizer.calls), 4096 + expected_count)
        self.assertEqual(report["candidate_summary"]["records"], 4096)
        provisional = self.records("provisional_tokens.jsonl")
        self.assertEqual(len(provisional), expected_count)
        self.assertEqual({record["root"] for record in provisional}, {f"excluded/{index}" for index in range(4)})
        self.assertTrue(all(record["status"] == "UNQUALIFIED" for record in provisional))
        self.assertEqual(report["provisional_roots"]["status"], "UNQUALIFIED")
        self.assertEqual(set(report["provisional_roots"]["per_namespace"]), set(core_api.SLOTS))
        self.assertEqual(report["provisional_roots"]["total"]["records"], expected_count)
        raw = json.loads((self.output / "provisional_roots.json").read_bytes())
        self.assertEqual(raw["roots"], [core_api.to_data(core_api.build_root(f"excluded/{index}")) for index in range(4)])

    def test_output_directory_cannot_be_reused(self):
        self.run_profile()
        before = (self.output / "profile.json").read_bytes()
        with self.assertRaisesRegex(profile_api.ProfileError, "fresh"):
            self.run_profile()
        self.assertEqual((self.output / "profile.json").read_bytes(), before)
        self.assertEqual(self.loader.call_count, 1)

    def test_existing_empty_or_symlink_output_is_rejected(self):
        self.output.mkdir()
        with self.assertRaises(profile_api.ProfileError):
            self.run_profile()
        self.output.rmdir()
        self.output.symlink_to(self.model, target_is_directory=True)
        with self.assertRaises(profile_api.ProfileError):
            self.run_profile()
        self.loader.assert_not_called()

    def test_gpu_visibility_or_missing_offline_flags_rejected_before_load(self):
        for key, value in (("CUDA_VISIBLE_DEVICES", "GPU-test"), ("HF_HUB_OFFLINE", "0"),
                           ("TRANSFORMERS_OFFLINE", "0"), ("HF_HUB_DISABLE_TELEMETRY", "0")):
            with self.subTest(key=key), patch.dict(os.environ, {key: value}), self.assertRaises(profile_api.ProfileError):
                self.run_profile()
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(profile_api.ProfileError):
            self.run_profile()
        self.loader.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_default_loader_uses_local_only_with_fake_transformers(self):
        constructor = Mock(return_value=self.tokenizer)
        module = SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=constructor))
        with patch.dict("sys.modules", {"transformers": module}):
            result = profile_api.load_offline_tokenizer(str(self.model))
        self.assertIs(result, self.tokenizer)
        constructor.assert_called_once_with(str(self.model), local_files_only=True, trust_remote_code=False)

    def test_files_template_and_environment_are_pinned(self):
        expected = {"files": profile_api.tokenizer_file_pins(self.model),
                    "chat_template_sha256": profile_api.hashlib.sha256(self.tokenizer.chat_template.encode()).hexdigest()}
        report = self.run_profile(expected_pins=expected)
        self.assertEqual(report["tokenizer_pins"], expected)
        identity = json.loads((self.output / "identity.json").read_bytes())
        self.assertEqual(identity["offline_flags"], self.flags)
        self.assertIn("profile", identity["sources"])
        self.assertIn("qualifier", identity["sources"])
        self.assertEqual(identity["environment"]["python"], "SYNTHETIC")

    def test_file_pin_mismatch_rejects_before_tokenizer_load(self):
        expected = {"files": {}, "chat_template_sha256": "0" * 64}
        with self.assertRaisesRegex(profile_api.ProfileError, "file pins differ"):
            self.run_profile(expected_pins=expected)
        self.loader.assert_not_called()
        self.assertTrue((self.output / "failure.json").exists())

    def test_template_pin_mismatch_rejects_before_encode(self):
        expected = {"files": profile_api.tokenizer_file_pins(self.model), "chat_template_sha256": "0" * 64}
        with self.assertRaisesRegex(profile_api.ProfileError, "template differs"):
            self.run_profile(expected_pins=expected)
        self.assertEqual(self.tokenizer.calls, [])

    def test_weights_are_never_hashed(self):
        original = profile_api.file_hash
        def checked(path):
            self.assertNotEqual(Path(path).suffix, ".safetensors")
            return original(path)
        with patch.object(profile_api, "file_hash", side_effect=checked):
            self.run_profile()

    def test_encoder_failure_keeps_denominator_and_no_retry(self):
        def encode(text):
            if len(self.tokenizer.calls) == 8:
                raise RuntimeError("synthetic encoder failure")
            return [1, 2]
        self.tokenizer.output = encode
        with self.assertRaises(RuntimeError):
            self.run_profile()
        failure = json.loads((self.output / "failure.json").read_bytes())
        self.assertEqual(failure["planned_candidates"], 4096)
        self.assertEqual(failure["candidate_encode_attempts"], 8)
        self.assertEqual(failure["candidate_records_written"], 7)
        self.assertEqual(len(self.records()), 7)
        self.assertFalse((self.output / "profile.json").exists())
        self.assertEqual(self.loader.call_count, 1)

    def test_bad_token_ids_fail_not_redraw(self):
        self.tokenizer.output = lambda text: [True]
        with self.assertRaisesRegex(profile_api.ProfileError, "tokenizer IDs"):
            self.run_profile()
        self.assertEqual(len(self.tokenizer.calls), 1)
        self.assertEqual(self.records(), [])

    def test_identity_drift_invalidates_complete_pool(self):
        def encode(text):
            if len(self.tokenizer.calls) == 4096:
                (self.model / "vocab.json").write_text("CHANGED")
            return [1]
        self.tokenizer.output = encode
        with self.assertRaisesRegex(profile_api.ProfileError, "changed during profiling"):
            self.run_profile()
        self.assertEqual(len(self.records()), 4096)
        self.assertFalse((self.output / "profile.json").exists())

    def test_wrong_loaded_tokenizer_path_is_rejected(self):
        self.tokenizer.name_or_path = str(self.root / "other")
        with self.assertRaisesRegex(profile_api.ProfileError, "loaded tokenizer path"):
            self.run_profile()
        self.assertEqual(self.tokenizer.calls, [])

    def test_output_inside_model_is_rejected(self):
        self.output = self.model / "profile"
        with self.assertRaisesRegex(profile_api.ProfileError, "disjoint"):
            self.run_profile()
        self.loader.assert_not_called()

    def test_cli_has_no_salt_count_or_selection_option(self):
        with redirect_stdout(io.StringIO()) as output, self.assertRaises(SystemExit) as exited:
            profile_api.main(["--help"])
        self.assertEqual(exited.exception.code, 0)
        self.assertIn("4096", output.getvalue())
        self.assertNotIn("--salt-count", output.getvalue())
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            profile_api.main(["--model", str(self.model), "--output", str(self.output), "--salt-count", "10"])

    def test_cli_dispatch_and_summary_use_injected_profile(self):
        original = profile_api.run_profile
        def run(model, output, **kwargs):
            return original(model, output, tokenizer_loader=self.loader, environment_reader=lambda: {}, clock_ns=self.clock, **kwargs)
        with patch.object(profile_api, "run_profile", side_effect=run), redirect_stdout(io.StringIO()) as stdout:
            status = profile_api.main(["--model", str(self.model), "--output", str(self.output)])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(stdout.getvalue())["profile_sha256"], profile_api.file_hash(self.output / "profile.json"))

    def test_environment_identity_is_python_and_tokenizer_packages_only(self):
        with patch.object(profile_api.importlib.metadata, "version", side_effect=lambda name: "synthetic/" + name):
            environment = profile_api.environment_identity()
        self.assertEqual(set(environment["packages"]), {"transformers", "tokenizers", "huggingface-hub"})
        self.assertTrue(Path(environment["python"]).is_absolute())
        self.assertTrue(environment["version"])


if __name__ == "__main__":
    unittest.main()
