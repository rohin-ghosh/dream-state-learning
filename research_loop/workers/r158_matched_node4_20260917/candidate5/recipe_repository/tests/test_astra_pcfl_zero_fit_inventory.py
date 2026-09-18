"""Synthetic-only inventory and custody checks; no actual tokenizer load."""

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from gpu import astra_pcfl_zero_fit_inventory as inventory


class Tokenizer:
    chat_template = "SYNTHETIC_ONLY"

    def __init__(self, model):
        self.name_or_path = str(model)

    def encode(self, text, add_special_tokens=False, truncation=False):
        if add_special_tokens or truncation:
            raise AssertionError("specials/truncation prohibited")
        hashed = hashlib.sha256(text.encode()).digest()
        return [int.from_bytes(hashed[index:index + 4], "big") for index in range(0, 32, 4)]

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        text = "\n".join(message["role"] + ":" + message["content"] for message in messages) + "\nassistant:"
        return self.encode(text) if tokenize else text


class InventoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="pcfl_inventory_cpu_")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.model = self.root / "model"
        self.model.mkdir()
        for name in ("config.json", *sorted(inventory.driver.native.TOKENIZER_FILES)):
            (self.model / name).write_text("SYNTHETIC/" + name)
        self.tokenizer = Tokenizer(self.model)
        self.policy = self.root / "policy.md"
        self.policy.write_text("SYNTHETIC_CPU_POLICY")
        self.pins = self.root / "pins.json"
        self.pins.write_bytes(inventory.canonical({"files": inventory.profile.tokenizer_file_pins(self.model),
                              "chat_template_sha256": hashlib.sha256(self.tokenizer.chat_template.encode()).hexdigest()}))
        files = {name: {"sha256": inventory.file_hash(self.model / name), "size": (self.model / name).stat().st_size,
                        "public_match": "GIT_BLOB_SHA1"} for name in json.loads(self.pins.read_bytes())["files"]}
        for index in range(14 - len(files)):
            files[f"NOT_PRESENT_WEIGHT_{index}.safetensors"] = {"sha256": "1" * 64, "size": 999999,
                                                                "public_match": "LFS_SHA256"}
        self.public = self.root / "public.json"
        self.public.write_bytes(inventory.canonical({"repository": inventory.driver.native.MODEL_NAME,
                "revision": inventory.driver.native.REVISION, "status": "PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING",
                "model": str(self.model), "file_count": 14, "files": files}))
        self.output = self.root / "out"
        self.loader = Mock(return_value=self.tokenizer)
        flags = patch.dict(os.environ, CUDA_VISIBLE_DEVICES="", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
        flags.start()
        self.addCleanup(flags.stop)

    def run_inventory(self, **overrides):
        args = dict(model_path=str(self.model), policy_path=str(self.policy), policy_sha256=inventory.file_hash(self.policy),
                    tokenizer_pins_path=str(self.pins), tokenizer_pins_sha256=inventory.file_hash(self.pins),
                    public_receipt_path=str(self.public), public_receipt_sha256=inventory.file_hash(self.public),
                    output_dir=str(self.output), tokenizer_loader=self.loader)
        args.update(overrides)
        return inventory.run_inventory(**args)

    def rows(self, name):
        return [json.loads(line) for line in (self.output / name).read_bytes().splitlines()]

    def test_fixed_order_first_eligible_salts_and_repeatable_bytes(self):
        reports = []
        for _ in range(2):
            candidates, choices = [], []
            roots = inventory.allocate(self.tokenizer, candidates.append, lambda row: None, choices)
            reports.append((roots, candidates, choices))
        self.assertEqual(reports[0], reports[1])
        roots, candidates, choices = reports[0]
        self.assertEqual([root["label"] for root in roots], list(inventory.ROOTS))
        expected = [(root, namespace, index, slot) for root in inventory.ROOTS
                    for namespace, slots in inventory.driver.core.SLOTS.items() for index, slot in enumerate(slots)]
        self.assertEqual(len(expected), 212)
        self.assertEqual([(row["root"], row["namespace"], row["index"], row["slot"]) for row in choices], expected)
        self.assertEqual(len({row["text"] for row in choices}), 212)
        self.assertEqual(len({tuple(row["token_ids"]) for row in choices}), 212)
        offset = 0
        for choice in choices:
            self.assertEqual(choice["text"], inventory.driver.core.opaque_candidate(
                choice["root"], choice["namespace"], choice["index"], choice["salt"]))
            examined = candidates[offset:offset + choice["salt"] + 1]
            self.assertEqual([row["salt"] for row in examined], list(range(choice["salt"] + 1)))
            self.assertTrue(all(not row["accepted"] for row in examined[:-1]))
            self.assertTrue(examined[-1]["accepted"])
            self.assertEqual(choice["candidate_sha256"], inventory.digest(examined[-1]))
            self.assertEqual(choice["choice_sha256"], inventory.digest({key: value for key, value in choice.items() if key != "choice_sha256"}))
            offset += len(examined)
        self.assertEqual(offset, len(candidates))

    def test_one_all800_measurement_and_no_weights_or_native_load(self):
        with patch.object(inventory.driver, "measure_tokenizer", wraps=inventory.driver.measure_tokenizer) as measure:
            report = self.run_inventory()
        self.assertEqual(measure.call_count, 1)
        self.assertEqual(len(measure.call_args.args[0]["tasks"]), 800)
        self.assertEqual(len(measure.call_args.args[0]["call_slots"]), 1952)
        self.assertEqual(report["selected_ids"], 212)
        self.assertEqual(report["kind"], "SYNTHETIC_CPU_FIXTURE")
        self.assertFalse(report["full_allocator_qualified"])
        self.assertFalse(report["ready_for_model_calls"])
        for name, expected in report["files"].items():
            self.assertEqual(inventory.file_hash(self.output / name), expected)
        self.loader.assert_called_once_with(str(self.model))

    def test_used_surface_failure_preserves_complete_fixed_inventory_no_retry(self):
        with patch.object(inventory.driver, "measure_tokenizer", side_effect=ValueError("unequal actual surface")) as measure:
            with self.assertRaisesRegex(ValueError, "unequal actual surface"):
                self.run_inventory()
        self.assertEqual(measure.call_count, 1)
        self.assertEqual(len(json.loads((self.output / "roots.json").read_bytes())), 4)
        self.assertEqual(len(self.rows("choices.jsonl")), 212)
        failure = json.loads((self.output / "failure.json").read_bytes())
        self.assertEqual(failure["phase"], "USED_SURFACE_MEASUREMENT")
        self.assertEqual(failure["status"], "UNQUALIFIED_NO_RESELECTION")
        self.assertIn("ValueError: unequal actual surface", failure["traceback"])
        self.assertFalse((self.output / "receipt.json").exists())
        before = inventory.file_hash(self.output / "roots.json")
        with self.assertRaisesRegex(ValueError, "fresh absolute output"):
            self.run_inventory()
        self.assertEqual(before, inventory.file_hash(self.output / "roots.json"))
        self.assertEqual(self.loader.call_count, 1)

    def test_reject_length_raw_token_and_reserved_collisions(self):
        candidates, choices = [], []
        real = inventory.qualifier.opaque_candidate
        first = real("excluded/0", "node", 0, 0)
        second = real("excluded/0", "node", 1, 0)
        short = real("excluded/0", "node", 2, 0)
        original_encode = self.tokenizer.encode
        def encode(text, **kwargs):
            if text == short:
                return [1] * 7
            if text == second:
                return original_encode(first, **kwargs)
            return original_encode(text, **kwargs)
        self.tokenizer.encode = encode
        def candidate(root, namespace, index, salt):
            if root == "excluded/0" and namespace == "node" and index == 3 and salt == 0:
                return first
            if root == "excluded/0" and namespace == "node" and index == 4 and salt == 0:
                return "N_ATESTABCDE"
            return real(root, namespace, index, salt)
        with patch.object(inventory.qualifier, "opaque_candidate", side_effect=candidate):
            inventory.allocate(self.tokenizer, candidates.append, lambda row: None, choices)
        rejected = {reason for row in candidates for reason in row["reasons"]}
        self.assertTrue({"NOT_L8", "RAW_COLLISION", "TOKEN_COLLISION", "RESERVED_COLLISION"} <= rejected)

    def test_encoding_exception_records_attempt_and_stops(self):
        self.tokenizer.encode = Mock(side_effect=RuntimeError("encoder failure"))
        with self.assertRaisesRegex(RuntimeError, "encoder failure"):
            self.run_inventory()
        candidates = self.rows("candidates.jsonl")
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["reasons"], ["ENCODING_ERROR"])
        self.assertIn("RuntimeError: encoder failure", candidates[0]["traceback"])
        self.assertEqual(json.loads((self.output / "unqualified_choices.json").read_bytes()), [])

    def test_exhaustion_stops_without_backtracking(self):
        self.tokenizer.encode = lambda *args, **kwargs: [7]
        candidates, choices = [], []
        with patch.object(inventory, "SALT_LIMIT", 3):
            with self.assertRaisesRegex(ValueError, "SALT_EXHAUSTED"):
                inventory.allocate(self.tokenizer, candidates.append, lambda row: None, choices)
        self.assertEqual([row["salt"] for row in candidates], [0, 1, 2])
        self.assertEqual(choices, [])
        self.assertEqual(inventory.SALT_LIMIT, 1000000)

    def test_policy_pin_bound_and_exact_reserved_list(self):
        self.assertEqual(inventory.file_hash(inventory.POLICY_PATH), inventory.POLICY_SHA256)
        policy = inventory.POLICY_PATH.read_text()
        reserved = policy.split("Reserved literals are exactly ")[1].split(". This scoped task")[0]
        self.assertEqual(tuple("".join(reserved.split()).split(",")), inventory.RESERVED)
        self.assertEqual(inventory.reserved_literals()["canary_ids"], [])
        self.assertEqual(inventory.reserved_literals()["parser_prefixes"], [])

    def test_bad_hashes_fail_before_loading_and_claim(self):
        for field in ("policy_sha256", "tokenizer_pins_sha256", "public_receipt_sha256"):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "bound input hash differs"):
                    self.run_inventory(**{field: "0" * 64})
        self.assertFalse(self.output.exists())
        self.loader.assert_not_called()

    def test_wrong_public_receipt_and_tokenizer_files_rejected(self):
        public = json.loads(self.public.read_bytes())
        public["revision"] = "wrong"
        self.public.write_bytes(inventory.canonical(public))
        with self.assertRaisesRegex(ValueError, "public C0 receipt binding differs"):
            self.run_inventory()
        self.loader.assert_not_called()
        self.assertTrue((self.output / "failure.json").is_file())

    def test_pin_map_must_match_all_local_tokenizer_files(self):
        (self.model / "added_tokens.json").write_text("unexpected")
        with self.assertRaisesRegex(ValueError, "exact tokenizer file inventory/hash differs"):
            self.run_inventory()
        self.loader.assert_not_called()

    def test_loaded_template_drift_stops_before_allocation(self):
        self.tokenizer.chat_template = "CHANGED"
        with self.assertRaisesRegex(ValueError, "loaded chat template differs"):
            self.run_inventory()
        self.assertFalse((self.output / "candidates.jsonl").exists())

    def test_public_tokenizer_hash_disagreement_stops_before_load(self):
        public = json.loads(self.public.read_bytes())
        public["files"]["tokenizer.json"]["sha256"] = "0" * 64
        self.public.write_bytes(inventory.canonical(public))
        with self.assertRaisesRegex(ValueError, "tokenizer/public receipt mismatch"):
            self.run_inventory()
        self.loader.assert_not_called()

    def test_file_change_during_measurement_invalidates_without_reselection(self):
        original = inventory.driver.measure_tokenizer
        def measure(*args, **kwargs):
            result = original(*args, **kwargs)
            (self.model / "tokenizer.json").write_text("DRIFT")
            return result
        with patch.object(inventory.driver, "measure_tokenizer", side_effect=measure) as measured:
            with self.assertRaisesRegex(ValueError, "exact tokenizer file inventory/hash differs"):
                self.run_inventory()
        self.assertEqual(measured.call_count, 1)
        failure = json.loads((self.output / "failure.json").read_bytes())
        self.assertEqual(failure["phase"], "FINAL_CUSTODY")
        self.assertEqual(failure["selected_ids"], 212)

    def test_initial_context_cap_failure_preserves_measurement(self):
        original = inventory.driver.measure_tokenizer
        def measure(*args, **kwargs):
            result = original(*args, **kwargs)
            next(row for row in result["measurements"] if row["id"].startswith("initial/"))["token_ids"] = [1] * 14337
            return result
        with patch.object(inventory.driver, "measure_tokenizer", side_effect=measure) as measured:
            with self.assertRaisesRegex(ValueError, "initial context/output budget exceeded"):
                self.run_inventory()
        self.assertEqual(measured.call_count, 1)
        self.assertTrue((self.output / "measurements.json").exists())
        self.assertFalse((self.output / "receipt.json").exists())

    def test_native_path_refuses_unbound_policy_before_load(self):
        with patch.object(inventory.profile, "load_offline_tokenizer") as loader:
            with self.assertRaisesRegex(ValueError, "policy not frozen or hash differs"):
                self.run_inventory(tokenizer_loader=None)
        loader.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_cuda_and_offline_flags_required(self):
        for key, value in (("CUDA_VISIBLE_DEVICES", "0"), ("HF_HUB_OFFLINE", "0"),
                           ("TRANSFORMERS_OFFLINE", "0"), ("HF_HUB_DISABLE_TELEMETRY", "0")):
            with self.subTest(key=key), patch.dict(os.environ, {key: value}):
                with self.assertRaises(ValueError):
                    self.run_inventory()
        self.loader.assert_not_called()

    def test_typed_tokens_reject_bool_negative_and_empty(self):
        for tokens in ([True] * 8, [-1] * 8, [], "12345678"):
            with self.subTest(tokens=tokens):
                tokenizer = Mock()
                tokenizer.encode.return_value = tokens
                with self.assertRaisesRegex(ValueError, "invalid token IDs"):
                    inventory._tokens(tokenizer, "fixture")

    def test_expired_allocation_deadline_makes_no_encode_call(self):
        tokenizer = Mock()
        with self.assertRaisesRegex(ValueError, "180s preparation envelope exhausted"):
            inventory.allocate(tokenizer, lambda row: None, lambda row: None, [], deadline=0)
        tokenizer.encode.assert_not_called()

    def test_cli_passes_required_explicit_bindings(self):
        args = dict(model="/model", policy="/policy", policy_sha256="1" * 64, tokenizer_pins="/pins",
                    tokenizer_pins_sha256="2" * 64, public_receipt="/public", public_receipt_sha256="3" * 64, output="/fresh")
        argv = [part for name, value in args.items() for part in ("--" + name.replace("_", "-"), value)]
        with patch.object(inventory, "run_inventory", return_value={"model_calls": 0}) as run:
            self.assertEqual(inventory.main(argv), 0)
        self.assertEqual(run.call_args.args, tuple(args.values()))


if __name__ == "__main__":
    unittest.main()
