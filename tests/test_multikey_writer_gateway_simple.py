"""CPU-only adversarial V10R1 contract tests; no tokenizer/model downloads."""

import copy
from contextlib import contextmanager
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from organism_v6 import multikey_writer_gateway_simple as scout


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.material = scout.build_material()
        cls.identity = dict(model=scout.MODEL, model_sha256="1" * 64,
                            tokenizer_sha256="2" * 64, run_sha256="3" * 64)
        cls.adapters = {f"{root}/{mapping}": scout.digest([root, mapping])
                        for root in range(2) for mapping in scout.MAPS}
        cls.requests = scout.build_requests(cls.material, cls.identity, cls.adapters, scout.FixtureTokenizer())
        cls.records = scout.fixture_records(cls.material, cls.requests)

    def modified(self, predicate, update):
        records = copy.deepcopy(self.records)
        for request in self.requests:
            if predicate(request):
                update(records[request["id"]]["attempts"][-1], request)
        return records

    def reduce(self, records):
        return scout.reduce_records(self.material, self.requests, records)

    def test_canonical_bytes_and_nonfinite(self):
        self.assertEqual(scout.canonical({"z": "é", "a": 1}), b'{"a":1,"z":"\xc3\xa9"}\n')
        with self.assertRaises(ValueError):
            scout.canonical({"value": float("nan")})

    def test_full_geometry_and_shortcut_maxima(self):
        receipt = scout.validate_material(self.material)
        self.assertEqual(receipt["training_rows"], 512)
        self.assertEqual(receipt["primary_items"], 384)
        self.assertTrue(all(2 * row[-2] == row[-1] for row in receipt["shortcut_counts"]))
        self.assertEqual(len(self.requests), 1504)
        self.assertEqual(self.material["fit_cap"], 4)
        self.assertEqual(self.material["A40_hours_cap"], 3.0)
        self.assertFalse(self.material["training_run_replication"])
        self.assertTrue(self.material["root_seed_confounded"])

    def test_deterministic_material_and_identifier_independence(self):
        self.assertEqual(scout.canonical(self.material), scout.canonical(scout.build_material()))
        changed = scout.build_material(identifier_seed=901)
        self.assertNotEqual(scout.digest(changed), scout.digest(self.material))
        for original, mutated in zip(self.material["roots"], changed["roots"]):
            self.assertEqual(original["orientation"], mutated["orientation"])
            self.assertTrue(all(left != right for left, right in zip(original["tools"], mutated["tools"])))
            for tool, neighbour in zip(original["tools"], original["neighbours"]):
                self.assertEqual(sum(left != right for left, right in zip(tool, neighbour)), 1)

    def test_complement_maps_identical_order_mask_and_seeds(self):
        for root_index, root in enumerate(self.material["roots"]):
            plus = scout.fit_projection(root["train"]["W+"], root_index)
            minus = scout.fit_projection(root["train"]["W-"], root_index)
            for left, right in zip(plus, minus):
                self.assertEqual(set(left), {"context", "target", "mask", "order", "seed", "recipe"})
                self.assertNotEqual(left["target"], right["target"])
                self.assertEqual(len(left["target"]), len(right["target"]))
                self.assertEqual({key: value for key, value in left.items() if key != "target"},
                                 {key: value for key, value in right.items() if key != "target"})
            self.assertEqual(len(plus) * scout.RECIPE["epochs"], 256)
        with self.assertRaises(scout.ContractError):
            scout.build_material(fit_seeds=(0, 0))

    def test_material_mutation_fails_closed(self):
        for field, value in (("context", "injected held oracle"), ("target", 9), ("stratum", 2)):
            mutated = copy.deepcopy(self.material)
            mutated["roots"][0]["train"]["W+"][0][field] = value
            with self.assertRaises(scout.ContractError):
                scout.validate_material(mutated)
        mutated = copy.deepcopy(self.material)
        mutated["roots"][0]["held"].pop()
        with self.assertRaises(scout.ContractError):
            scout.validate_material(mutated)

    def test_strict_parser_table(self):
        cases = [
            ("ACT: a0", 0, False), ("ACT: a1\n", 1, False),
            (" \t\r\nACT: a0\t\r\n", 0, False),
            ("ACT: a0\nACT: a1", None, True),
            ("ACT: a0\nACT: malformed", None, True),
            ("\t ACT: a0\n  ACT: bad", None, True),
            ("prose ACT: a0", None, False), ("act: a0", None, False),
            ("ACT: a0 ACT: a1", None, False), ("ACT: a0\nprose", None, False),
            ("```\nACT: a0\n```", None, False), ("", None, False),
            (None, None, False), ("\u00a0ACT: a0", None, False),
            ("ACT: a0\u00a0", None, False), ("ACT:  a0", None, False),
        ]
        for text, action, multiple in cases:
            with self.subTest(text=text):
                self.assertEqual(scout.parse_output(text), {"action": action, "multiple_ACT": multiple})
        self.assertIsNone(scout.parse_output("ACT: a0", truncated=True)["action"])

    def test_native_parser_uses_own_exact_expected_bytes(self):
        expected = "ACT: native_0"
        self.assertTrue(scout.native_correct(" \tACT: native_0\r\n", expected))
        for text in (None, "ACT: a0", "act: native_0", "ACT:  native_0", "ACT: native_1",
                     "ACT: native_0.", "ACT: native_0\nextra", "\u00a0ACT: native_0", "ACT: native_0\u00a0"):
            self.assertFalse(scout.native_correct(text, expected), text)
        self.assertFalse(scout.native_correct(expected, expected, truncated=True))

    def test_fake_joint_token_stream_and_eos(self):
        pair = scout.token_pair(scout.FixtureTokenizer(), "Context\n")
        self.assertEqual(pair[0]["labels"][:8], [-100] * 8)
        self.assertEqual(pair[0]["labels"][-1], 0)
        self.assertEqual(sum(label != -100 for label in pair[0]["labels"]), len(scout.CANDIDATES[0]) + 1)
        self.assertEqual(len(pair[0]["input_ids"]), len(pair[1]["input_ids"]))

    def test_fake_tokenizer_failures(self):
        class MissingEOS(scout.FixtureTokenizer):
            eos_token_id = None

        class DuplicateEOS(scout.FixtureTokenizer):
            def __call__(self, text, **kwargs):
                result = super().__call__(text, **kwargs)
                result["input_ids"][0] = 0
                return result

        class Truncated(scout.FixtureTokenizer):
            def __call__(self, text, **kwargs):
                result = super().__call__(text, **kwargs)
                return {key: values[:-1] for key, values in result.items()}

        class Straddled(scout.FixtureTokenizer):
            def __call__(self, text, **kwargs):
                result = super().__call__(text, **kwargs)
                result["offset_mapping"][0] = (0, 2)
                return result

        for tokenizer, context in ((MissingEOS(), "X"), (DuplicateEOS(), "X"),
                                   (Truncated(), "X"), (Straddled(), "X"),
                                   (scout.FixtureTokenizer(), "X" * 2048)):
            with self.subTest(tokenizer=type(tokenizer).__name__):
                with self.assertRaises(scout.ContractError):
                    scout.token_pair(tokenizer, context)

    def test_multitoken_fake_and_unequal_candidate_lengths(self):
        class PairedTokenizer(scout.FixtureTokenizer):
            def __init__(self, unequal=False):
                self.unequal = unequal
                self.tokens = {}

            def __call__(self, text, **kwargs):
                result = super().__call__(text, **kwargs)
                start = text.index("ACT:")
                if not self.unequal or "a0" in text:
                    result["input_ids"][start:start + 2] = [5000]
                    result["offset_mapping"][start:start + 2] = [(start, start + 2)]
                self.tokens[tuple(result["input_ids"])] = text
                return result

            def decode(self, ids):
                return self.tokens[tuple(ids)]

        pair = scout.token_pair(PairedTokenizer(), "Context\n")
        self.assertEqual(len(pair[0]["input_ids"]), len("Context\nACT: a0\n"))
        with self.assertRaises(scout.ContractError):
            scout.token_pair(PairedTokenizer(unequal=True), "Context\n")

    def test_operation_allowlists_and_oracle_antiflow(self):
        primary_prompts = set()
        oracle_prompts = set()
        for request in self.requests:
            payload = request["payload"]
            self.assertEqual(set(payload), {"kind", "identity", "adapter", "prompt", "seed", "candidates", "parameters"})
            if payload["kind"] == "oracle_generate":
                self.assertEqual(payload["adapter"], "OFF")
                oracle_prompts.add(payload["prompt"])
                self.assertIn("Explicit action table:", payload["prompt"])
            else:
                self.assertNotIn("Explicit action table:", payload["prompt"])
                primary_prompts.add(payload["prompt"])
            if payload["kind"].endswith("generate"):
                self.assertEqual(payload["candidates"], [])
        self.assertFalse(primary_prompts & oracle_prompts)
        training = {row["context"] for root in self.material["roots"] for row in root["train"]["W+"]}
        self.assertFalse(training & primary_prompts)
        self.assertFalse(training & oracle_prompts)
        request = self.requests[0]["payload"]
        for key, value in (("kind", "oracle_generate"), ("adapter", "9" * 64), ("seed", 0),
                           ("prompt", request["prompt"] + "extra"), ("identity", dict(self.identity, run_sha256="4" * 64))):
            self.assertNotEqual(scout.digest(request), scout.digest(dict(request, **{key: value})))
        with self.assertRaises(scout.ContractError):
            scout.request_payload("oracle_generate", self.identity, "4" * 64, "prompt", 1)

    def test_complete_synthetic_pass_not_scientific_run(self):
        report = self.reduce(self.records)
        self.assertEqual(report["label"], "MULTIKEY_BINDING_PASS")
        self.assertTrue(all(report["gates"].values()))
        for root in report["roots"]:
            for cell in root["cells"].values():
                self.assertEqual(cell["BA"], 1)
                self.assertEqual(cell["OFF_gain"], .5)
                self.assertEqual(len(cell["key_NLL_gains"]), 16)
                self.assertAlmostEqual(cell["mean_NLL_gain"], math.log(2) - math.log1p(math.exp(-4)))
                self.assertEqual(cell["oracle_BA"], 1)

    def test_total_boolean_partition_and_precedence(self):
        names = ("oracle_ok", "optimization_ok", "binding_ok", "interface_ok", "spill_ok")
        labels = set()
        for values in itertools.product((False, True), repeat=5):
            gates = dict(zip(names, values))
            expected = ("ASSAY_INVALID" if not values[0] else
                        "OPTIMIZATION_INCONCLUSIVE" if not values[1] else
                        "INTERFACE_INVALID" if not values[3] else
                        "BINDING_WITH_SPILL" if values[2] and not values[4] else
                        "MULTIKEY_BINDING_PASS" if all(values) else "GATEWAY_NEGATIVE")
            self.assertEqual(scout.classify(gates), expected)
            labels.add(expected)
        self.assertEqual(len(labels), 6)

    def test_every_scalar_threshold_inclusive_and_adjacent_failure(self):
        baseline = self.reduce(self.records)["roots"][0]["cells"]["W+"]
        for field, gate, threshold in (("oracle_BA", "oracle_ok", .9),
                                       ("BA", "binding_ok", .8),
                                       ("OFF_gain", "binding_ok", .2),
                                       ("validity", "interface_ok", .95)):
            cell = copy.deepcopy(baseline)
            cell[field] = threshold
            self.assertTrue(scout.cell_gates(cell)[gate], field)
            cell[field] = math.nextafter(threshold, -math.inf)
            self.assertFalse(scout.cell_gates(cell)[gate], field)
        cell = copy.deepcopy(baseline)
        cell["BA"], cell["opposite_BA"] = 1.0, .5
        self.assertTrue(scout.cell_gates(cell)["binding_ok"])
        cell["opposite_BA"] = math.nextafter(.5, math.inf)
        self.assertFalse(scout.cell_gates(cell)["binding_ok"])
        for field, gate, threshold in (("accuracy", "binding_ok", .75), ("validity", "interface_ok", .875)):
            cell = copy.deepcopy(baseline)
            cell["strata"][0][field] = threshold
            self.assertTrue(scout.cell_gates(cell)[gate])
            cell["strata"][0][field] = math.nextafter(threshold, -math.inf)
            self.assertFalse(scout.cell_gates(cell)[gate])
        for field in ("mean_binary_TV", "legal_ACT_rate_change"):
            cell = copy.deepcopy(baseline)
            cell["spill"]["missing"][field] = .05
            self.assertTrue(scout.cell_gates(cell)["spill_ok"])
            cell["spill"]["missing"][field] = math.nextafter(.05, math.inf)
            self.assertFalse(scout.cell_gates(cell)["spill_ok"])
        self.assertTrue(scout.asymmetry_ok(.25, 0))
        self.assertFalse(scout.asymmetry_ok(math.nextafter(.25, math.inf), 0))
        cell = copy.deepcopy(baseline)
        cell["multiple_ACT_rate"] = 1 / 64
        self.assertFalse(scout.cell_gates(cell)["interface_ok"])

    def test_key_gains_margins_counts_and_inherited_signed_rate_bound(self):
        cell = self.reduce(self.records)["roots"][0]["cells"]["W+"]
        cell["key_NLL_gains"] = [.5] * 16
        self.assertTrue(scout.cell_gates(cell)["optimization_ok"])
        cell["key_NLL_gains"][0] = math.nextafter(.5, -math.inf)
        self.assertFalse(scout.cell_gates(cell)["optimization_ok"])
        cell["key_margins"] = [.5] * 12 + [0] * 4
        cell["strata"][0]["margin_keys"] = cell["strata"][1]["margin_keys"] = 6
        self.assertTrue(scout.cell_gates(cell)["binding_ok"])
        cell["key_margins"][0] = math.nextafter(.5, -math.inf)
        self.assertFalse(scout.cell_gates(cell)["binding_ok"])
        cell["key_margins"][0] = .5
        cell["strata"][1]["margin_keys"] = 5
        self.assertFalse(scout.cell_gates(cell)["binding_ok"])
        cell["spill"]["missing"]["legal_ACT_rate_change"] = -1
        self.assertTrue(scout.cell_gates(cell)["spill_ok"])

    def test_serialized_schedule_rejects_leaks_even_with_rehashed_requests(self):
        for mutation in ("oracle_leak", "seed", "coordinate", "adapter", "extra"):
            requests = copy.deepcopy(self.requests)
            request = requests[0]
            if mutation == "oracle_leak":
                request["payload"]["prompt"] = scout.oracle_prompt(self.material["roots"][0], "W+", request["payload"]["prompt"])
            elif mutation == "seed":
                request["payload"]["seed"] += 1
            elif mutation == "coordinate":
                request["audit"][3] = 63
            elif mutation == "adapter":
                request["payload"]["adapter"] = "8" * 64
            else:
                request["payload"]["orientation"] = 1
            request["id"] = scout.digest(request["payload"])
            with self.subTest(mutation=mutation):
                with self.assertRaises(scout.ContractError):
                    scout.validate_requests(self.material, requests)

    def test_cross_root_cofailure_precedence(self):
        records = copy.deepcopy(self.records)
        for request in self.requests:
            output = records[request["id"]]["attempts"][-1]
            if request["audit"][0] == 0 and request["payload"]["kind"] == "oracle_generate":
                output["text"] = "invalid oracle"
            if request["audit"][0] == 1 and request["payload"]["kind"] == "primary_score":
                output["token_logprobs"] = [[-3 / count] * count for count in request["payload"]["parameters"]["token_counts"]]
        report = self.reduce(records)
        self.assertEqual(report["label"], "ASSAY_INVALID")
        self.assertFalse(report["gates"]["optimization_ok"])

    def test_no_learning_precedes_binding_failure(self):
        records = self.modified(lambda request: request["payload"]["kind"] == "primary_score",
                                lambda output, request: output.update(token_logprobs=[[-3 / count] * count for count in request["payload"]["parameters"]["token_counts"]]))
        self.assertEqual(self.reduce(records)["label"], "OPTIMIZATION_INCONCLUSIVE")

    def test_failed_oracle_precedes_other_failures(self):
        records = self.modified(lambda request: request["payload"]["kind"] == "oracle_generate",
                                lambda output, request: output.update(text="bad"))
        self.assertEqual(self.reduce(records)["label"], "ASSAY_INVALID")

    def test_off_multiple_act_is_diagnostic_adapter_is_gate_bearing(self):
        records = self.modified(lambda request: request["audit"][1] == "OFF" and request["payload"]["kind"] == "primary_generate",
                                lambda output, request: output.update(text="ACT: a0\nACT: a1"))
        report = self.reduce(records)
        self.assertEqual(report["label"], "MULTIKEY_BINDING_PASS")
        self.assertEqual(report["roots"][0]["OFF_multiple_ACT_rate"], 1)
        records = self.modified(lambda request: request["audit"][1] != "OFF" and request["payload"]["kind"] == "primary_generate",
                                lambda output, request: output.update(text="ACT: a0\n ACT: malformed"))
        self.assertEqual(self.reduce(records)["label"], "INTERFACE_INVALID")

    def test_off_native_panel_is_gate_bearing(self):
        def select(request):
            root, condition, panel, index = request["audit"]
            return (condition == "OFF" and request["payload"]["kind"] == "spill_generate" and
                    self.material["roots"][root]["spill"][index]["family"] == "unrelated")
        records = self.modified(select, lambda output, request: output.update(text="ACT: wrong"))
        self.assertEqual(self.reduce(records)["label"], "INTERFACE_INVALID")

    def test_binding_negative_and_spill_precedence(self):
        records = self.modified(lambda request: request["audit"][1] != "OFF" and request["payload"]["kind"] == "primary_generate",
                                lambda output, request: output.update(text="ACT: a0"))
        self.assertEqual(self.reduce(records)["label"], "GATEWAY_NEGATIVE")
        records = self.modified(lambda request: request["audit"][1] != "OFF" and request["payload"]["kind"] == "spill_score",
                                lambda output, request: output.update(token_logprobs=[[-value / count] * count for value, count in zip((1, 5), request["payload"]["parameters"]["token_counts"])]))
        self.assertEqual(self.reduce(records)["label"], "BINDING_WITH_SPILL")

    def test_fixed_denominators_and_truncated_outputs(self):
        self.assertEqual(scout.balanced_accuracy([0, None, 1, None], [0, 0, 1, 1]), .5)
        records = self.modified(lambda request: request["payload"]["kind"] == "primary_generate" and request["audit"][1] != "OFF",
                                lambda output, request: output.update(truncated=True))
        self.assertEqual(self.reduce(records)["label"], "INTERFACE_INVALID")

    def test_even_median_and_logsumexp_multitoken(self):
        self.assertEqual(scout.statistics.median([0, 2, 4, 200]), 3)
        self.assertAlmostEqual(scout.log_q([-10000, -10000], 0), -math.log(2))
        self.assertAlmostEqual(scout.log_q([-10000, -10001], 1), -1 - math.log1p(math.exp(-1)))
        request = next(row for row in self.requests if row["payload"]["kind"].endswith("score"))
        record = copy.deepcopy(self.records[request["id"]])
        logs = scout.validate_record(request, record)
        self.assertAlmostEqual(logs[0], -3)
        record["attempts"][0]["token_logprobs"][0].pop()
        with self.assertRaises(scout.ContractError):
            scout.validate_record(request, record)

    def test_missing_nonfinite_extra_and_wrong_payload_abort(self):
        records = copy.deepcopy(self.records)
        records.pop(next(iter(records)))
        with self.assertRaises(scout.ContractError):
            self.reduce(records)
        request = next(row for row in self.requests if row["payload"]["kind"].endswith("score"))
        for value in (float("nan"), float("inf"), -float("inf"), 1.0):
            record = copy.deepcopy(self.records[request["id"]])
            record["attempts"][0]["token_logprobs"][0][0] = value
            with self.assertRaises(scout.ContractError):
                scout.validate_record(request, record)
        record = copy.deepcopy(self.records[request["id"]])
        record["request"]["seed"] += 1
        with self.assertRaises(scout.ContractError):
            scout.validate_record(request, record)
        record = copy.deepcopy(self.records[request["id"]])
        record["unexpected"] = 1
        with self.assertRaises(scout.ContractError):
            scout.validate_record(request, record)

    def test_retry_only_after_preserved_infrastructure_failure(self):
        request = self.requests[0]
        record = copy.deepcopy(self.records[request["id"]])
        record["attempts"].insert(0, dict(infrastructure_failure="before output", output=None))
        scout.validate_record(request, record)
        for bad in ({"infrastructure_failure": "error", "output": "ACT: a0"},
                    {"text": "bad", "truncated": False},
                    {"infrastructure_failure": "", "output": None}):
            record["attempts"][0] = bad
            with self.assertRaises(scout.ContractError):
                scout.validate_record(request, record)
        record["attempts"].append(record["attempts"][-1])
        with self.assertRaises(scout.ContractError):
            scout.validate_record(request, record)

    def test_scoped_output_exclusive_contained_and_symlink_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            protected = {kind: str(base / kind) for kind in scout.PROTECTED_KINDS}
            root = scout.create_run(base / "run", protected)
            scout.write_once(root, "record.json", {"value": 1})
            with self.assertRaises(FileExistsError):
                scout.write_once(root, "record.json", {"value": 2})
            with self.assertRaises(FileExistsError):
                scout.create_run(root, protected)
            with self.assertRaises(scout.ContractError):
                scout.write_once(root, "../escape.json", {})
            with self.assertRaises(scout.ContractError):
                scout.create_run(base / "child" / "bad", protected)
            (base / "link").symlink_to(root, target_is_directory=True)
            with self.assertRaises(scout.ContractError):
                scout.write_once(base / "link", "new.json", {})

    def test_adapter_tree_hash_binds_paths_bytes_and_rejects_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "weights"
            path.write_bytes(b"one")
            original = scout.tree_hash(root)
            path.write_bytes(b"two")
            self.assertNotEqual(scout.tree_hash(root), original)
            path.write_bytes(b"one")
            path.rename(root / "other")
            self.assertNotEqual(scout.tree_hash(root), original)
            path.symlink_to(root / "other")
            with self.assertRaises(scout.ContractError):
                scout.tree_hash(root)

    def test_complete_fixture_seal_readonly_replay_and_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            protected = {kind: str(base / kind) for kind in scout.PROTECTED_KINDS}
            root = base / "run"
            report = scout.cpu_fixture(root, protected)
            original = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
            self.assertEqual(scout.canonical(scout.replay_fixture(root)), scout.canonical(report))
            self.assertEqual(original, {path: path.read_bytes() for path in original})
            self.assertIsNone(report["scientific_label"])
            self.assertEqual(report["evidence"], "CPU_FIXTURE_ONLY")
            self.assertIn("four_real_HF_fits", report["pending"])
            for name in ("raw.json", "report.json", "manifest.json", "fits.json", "fixture_adapter_0_0/NOT_A_REAL_ADAPTER.json"):
                path = root / name
                raw = path.read_bytes()
                path.write_bytes(raw + b" ")
                with self.assertRaises(scout.ContractError):
                    scout.replay_fixture(root)
                path.write_bytes(raw)
            with self.assertRaises(FileExistsError):
                scout.cpu_fixture(root, protected)

    def test_inherited_scope_bytes_bound_without_metadata_ratification_gate(self):
        self.assertEqual(scout.scope_receipt(), scout.SCOPE_HASHES)
        receipt = scout.inheritance_receipt()
        self.assertEqual(len(receipt["decision_hashes"]), 6)
        self.assertEqual(receipt["scopes"], scout.SCOPE_HASHES)
        with patch.object(scout, "SCOPE_HASHES", {"v9": "0" * 64}):
            with self.assertRaises(scout.ContractError):
                scout.scope_receipt()

    def test_fit_artifact_has_four_exact_nonexecuted_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "run"
            scout.cpu_fixture(root, {kind: str(base / kind) for kind in scout.PROTECTED_KINDS})
            fits = json.loads((root / "fits.json").read_bytes())
            self.assertEqual(set(fits), {"0/W+", "0/W-", "1/W+", "1/W-"})
            for fit in fits.values():
                self.assertEqual(len(fit["input"]), 128)
                self.assertEqual(fit["planned_optimizer_steps"], 256)
                self.assertEqual(fit["tokenizer_kind"], "CPU_FAKE_CHARACTER")
                self.assertEqual(fit["input_sha256"], scout.digest(fit["input"]))
            for root_index in range(2):
                for mapping in scout.MAPS:
                    self.assertEqual({row["seed"] for row in fits[f"{root_index}/{mapping}"]["input"]}, {root_index})

    def test_aggregate_likelihood_overflow_is_nonreportable(self):
        request = next(row for row in self.requests if row["payload"]["kind"].endswith("score"))
        record = copy.deepcopy(self.records[request["id"]])
        record["attempts"][0]["token_logprobs"][0] = [-1e308] * request["payload"]["parameters"]["token_counts"][0]
        with self.assertRaises(scout.ContractError):
            scout.validate_record(request, record)

    def test_cli_fixture_and_replay_cannot_claim_scientific_success(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "run"
            command = ["bash", "gpu/multikey_writer_gateway_simple.sh", "fixture", "--out", str(root)]
            for kind in sorted(scout.PROTECTED_KINDS):
                command.extend([f"--protected-{kind}", str(base / kind)])
            result = subprocess.run(command, capture_output=True, text=True,
                                    cwd=Path(__file__).resolve().parents[1])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIsNone(json.loads(result.stdout)["scientific_label"])
            replay = subprocess.run(["bash", "gpu/multikey_writer_gateway_simple.sh", "replay", "--run", str(root)],
                                    capture_output=True, text=True, cwd=Path(__file__).resolve().parents[1])
            self.assertEqual(replay.returncode, 0, replay.stderr)
            self.assertEqual(replay.stdout, result.stdout)

    def test_real_execution_fails_closed(self):
        result = subprocess.run(["bash", "gpu/multikey_writer_gateway_simple.sh", "execute", "--run", "/not-a-run"],
                                capture_output=True, text=True, cwd=Path(__file__).resolve().parents[1])
        self.assertEqual(result.returncode, 2)
        self.assertIn("requires explicit --allow-gpu", result.stderr)
        self.assertEqual(result.stdout, "")


class NativeBuildPreflightTests(unittest.TestCase):
    @contextmanager
    def prerequisites(self):
        compiler = scout.shutil.which("gcc") or scout.shutil.which("clang")
        if compiler is None:
            self.skipTest("positive native compilation requires a local C compiler")
        with tempfile.TemporaryDirectory() as directory:
            include = Path(directory)
            (include / "Python.h").write_text('#include "pyconfig.h"\n#define PY_MAJOR_VERSION 3\n')
            (include / "pyconfig.h").write_text("\n")
            paths = dict(scout.sysconfig.get_paths(), include=directory, platinclude=directory)
            with patch.object(scout.sysconfig, "get_paths", return_value=paths), \
                    patch.dict(scout.os.environ, {"CC": compiler}), \
                    patch.object(scout.importlib.metadata, "version", return_value="fixture-triton"):
                yield include

    def test_real_compiler_with_fake_header_interface_and_stable_evidence(self):
        with self.prerequisites() as include:
            receipt = scout.native_build_preflight()
            self.assertEqual(receipt, scout.native_build_preflight())
            self.assertEqual(receipt["headers"], [[str(header), scout.file_hash(header)]
                                                 for header in sorted(include.glob("*.h"))])
            self.assertEqual(receipt["compiler_sha256"], scout.file_hash(receipt["compiler"]))
            self.assertTrue(receipt["compiler_version"])
            self.assertEqual(receipt["triton_version"], "fixture-triton")
            self.assertEqual(receipt["returncode"], 0)
            self.assertFalse(receipt["model_loaded"])
            self.assertFalse(receipt["real_GPU_executed"])

    def test_missing_compiler_fails_before_any_subprocess(self):
        with patch.object(scout.shutil, "which", return_value=None), \
                patch.object(scout.subprocess, "run") as run:
            with self.assertRaisesRegex(scout.ContractError, "compiler missing"):
                scout.native_build_preflight()
            run.assert_not_called()

    def test_missing_headers_fail_before_any_subprocess(self):
        for filename in ("Python.h", "pyconfig.h"):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                include = Path(directory)
                for other in {"Python.h", "pyconfig.h"} - {filename}:
                    (include / other).write_text("\n")
                with patch.object(scout.shutil, "which", return_value=sys.executable), \
                        patch.object(scout.sysconfig, "get_paths", return_value=dict(include=directory, platinclude=directory)), \
                        patch.object(scout.subprocess, "run") as run:
                    with self.assertRaisesRegex(scout.ContractError, filename):
                        scout.native_build_preflight()
                    run.assert_not_called()

    def test_unusable_transitive_header_fails_actual_compilation(self):
        with self.prerequisites() as include:
            (include / "pyconfig.h").write_text("#error broken development headers\n")
            with self.assertRaisesRegex(scout.ContractError, "compilation failed"):
                scout.native_build_preflight()

    def test_header_byte_change_changes_receipt(self):
        with self.prerequisites() as include:
            before = scout.native_build_preflight()
            (include / "pyconfig.h").write_text("#define PREFLIGHT_FIXTURE 1\n")
            self.assertNotEqual(before["headers"], scout.native_build_preflight()["headers"])

    def test_triton_metadata_version_is_pinned_without_import(self):
        with self.prerequisites():
            before = scout.native_build_preflight()
            with patch.object(scout.importlib.metadata, "version", return_value="changed-triton") as version:
                after = scout.native_build_preflight()
                version.assert_called_once_with("triton")
            self.assertNotEqual(before, after)
            self.assertEqual(after["triton_version"], "changed-triton")


class RealExecutorTests(unittest.TestCase):
    def native_receipt(self):
        return dict(kind="CPU_NATIVE_BUILD_PREFLIGHT", compiler="/fixture/cc",
                    triton_version="fixture-triton",
                    compiler_sha256=scout.digest("fixture compiler"), compiler_version="fixture cc",
                    headers=[["/fixture/Python.h", scout.digest("fixture header")]],
                    returncode=0, model_loaded=False, real_GPU_executed=False)
    """Executor wiring tests use fake snapshots/workers, never real HF or CUDA."""

    def config(self, base):
        config = scout.config_template()
        config.update(model_path=str(base / "model"), tokenizer_path=str(base / "model"),
                      model_revision="a" * 40, tokenizer_revision="a" * 40,
                      model_sha256="1" * 64, tokenizer_sha256="1" * 64,
                      node=scout.sha(b"cpu-test-node"), gpu_uuid="GPU-00000000-0000-0000-0000-000000000000",
                      driver_version="580.173.02", lease_end_unix=time.time() + 8 * 3600,
                      lease_cutoff_unix=time.time() + 3600,
                      environment=dict(python="3.12.3", packages={name: "mock" for name in scout.PACKAGES}),
                      protected={kind: str(base / kind) for kind in scout.PROTECTED_KINDS},
                      builder_preflight_reference="[Builder] CPU test fixture; NOT a launch authorization")
        return config

    def pins(self, config):
        return dict(model=dict(sha256=config["model_sha256"]),
                    tokenizer=dict(sha256=config["tokenizer_sha256"]), environment=config["environment"])

    def hardware(self, config):
        return dict(node=config["node"], gpu_uuid=config["gpu_uuid"], gpu_name="NVIDIA A40",
                    driver_version=config["driver_version"])

    def prepare(self, root, config):
        completed = subprocess.CompletedProcess([], 0, b"mock CPU-suite stdout", b"mock CPU-suite stderr")
        with patch.object(scout, "native_build_preflight", return_value=self.native_receipt()), \
                patch.object(scout, "pin_local_inputs", return_value=self.pins(config)), \
                patch.object(scout, "load_local_tokenizer", return_value=scout.FixtureTokenizer()), \
                patch.object(scout.subprocess, "run", return_value=completed):
            return scout.prepare_real(root, config)

    def test_prepare_native_failure_precedes_snapshot_tokenizer_and_gpu_access(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            with patch.object(scout.shutil, "which", return_value=None), \
                    patch.object(scout, "pin_local_inputs") as pins, \
                    patch.object(scout, "load_local_tokenizer") as tokenizer, \
                    patch.object(scout, "gpu_identity") as hardware, \
                    patch.object(scout, "launch_worker") as worker:
                with self.assertRaisesRegex(scout.ContractError, "compiler missing"):
                    scout.prepare_real(base / "run", self.config(base))
                for mocked in (pins, tokenizer, hardware, worker):
                    mocked.assert_not_called()
            self.assertFalse((base / "run").exists())

    def test_execute_native_drift_or_failure_precedes_gpu_and_attempt_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "run"
            self.prepare(root, self.config(base))
            for failure in (None, scout.ContractError("native build compiler missing"),
                            scout.ContractError("native build Python.h missing")):
                with self.subTest(failure=failure), \
                        patch.object(scout, "native_build_preflight", return_value=dict(self.native_receipt(),
                                     compiler_sha256=scout.digest("changed compiler")), side_effect=failure) as native, \
                        patch.object(scout, "pin_local_inputs") as pins, \
                        patch.object(scout, "load_local_tokenizer") as tokenizer, \
                        patch.object(scout, "gpu_identity") as hardware, \
                        patch.object(scout, "assert_gpu_idle") as idle, \
                        patch.object(scout, "launch_worker") as worker:
                    with self.assertRaisesRegex(scout.ContractError, "native build"):
                        scout.execute_real(root, allow_gpu=True)
                    native.assert_called_once_with()
                    for mocked in (pins, tokenizer, hardware, idle, worker):
                        mocked.assert_not_called()
                self.assertFalse((root / "EXECUTION_STARTED.json").exists())
            receipt = root / "native_build_preflight.json"
            receipt.write_bytes(receipt.read_bytes() + b" ")
            with self.assertRaisesRegex(scout.ContractError, "prepared artifact changed"):
                scout.validate_prepared(root)

    def test_cli_missing_compiler_and_no_gpu_opt_in_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            config = base / "config.json"
            config.write_bytes(scout.canonical(self.config(base)))
            command = [sys.executable, "-B", "-m", "organism_v6.multikey_writer_gateway_simple"]
            result = subprocess.run(command + ["prepare", "--config", str(config), "--out", str(base / "run")],
                                    capture_output=True, text=True, timeout=30,
                                    env=dict(scout.os.environ, CC=str(base / "missing-cc"), PYTHONDONTWRITEBYTECODE="1"))
            self.assertEqual(result.returncode, 2)
            self.assertIn("NONREPORTABLE_ABORT: native build compiler missing", result.stderr)
            self.assertFalse((base / "run").exists())
            result = subprocess.run(command + ["execute", "--run", str(base / "run")],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 2)
            self.assertIn("requires explicit --allow-gpu", result.stderr)

    def test_config_requires_pins_explicit_scope_seeds_and_protected_roots(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(Path(directory))
            scout.validate_config(config)
            for key, value in (("model", "other"), ("model_revision", "main"),
                               ("model_sha256", "unbound"), ("gpu_uuid", "0"),
                               ("approved_intake", "other"), ("requested_scope", "expanded"),
                               ("lease_cutoff_unix", float("nan"))):
                with self.subTest(key=key):
                    with self.assertRaises(scout.ContractError):
                        scout.validate_config(dict(config, **{key: value}))
            config["seeds"]["fit_seeds"] = [0, 0]
            with self.assertRaises(scout.ContractError):
                scout.validate_config(config)

    def test_snapshot_hash_covers_cache_symlink_target_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "snapshot"
            root.mkdir()
            blob = base / "blob"
            blob.write_bytes(b"not-real-model")
            (root / "weights.safetensors").symlink_to(blob)
            before = scout.snapshot_inventory(root)
            blob.write_bytes(b"changed-not-real-model")
            self.assertNotEqual(before["sha256"], scout.snapshot_inventory(root)["sha256"])
            (root / "directory_link").symlink_to(base, target_is_directory=True)
            with self.assertRaises(scout.ContractError):
                scout.snapshot_inventory(root)

    def test_lease_six_hour_boundary_and_earlier_cutoff(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(Path(directory))
            config["lease_end_unix"] = 1790391780
            for cutoff in (1790370180, 1790370179):
                with self.subTest(cutoff=cutoff):
                    scout.validate_config(dict(config, lease_cutoff_unix=cutoff))
            for cutoff in (1790370181, 1790391180, 1790391780, 1790391781):
                with self.subTest(cutoff=cutoff):
                    with self.assertRaisesRegex(scout.ContractError, "six hours"):
                        scout.validate_config(dict(config, lease_cutoff_unix=cutoff))

    def test_lease_end_and_cutoff_must_be_explicit_finite_timestamps(self):
        template = scout.config_template()
        self.assertEqual(template["lease_end_unix"], 0)
        self.assertEqual(template["lease_cutoff_unix"], 0)
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(Path(directory))
            for key in ("lease_end_unix", "lease_cutoff_unix"):
                for value in (0, -1, True, None, "1790391780", float("nan"), float("inf")):
                    with self.subTest(key=key, value=value):
                        with self.assertRaises(scout.ContractError):
                            scout.validate_config(dict(config, **{key: value}))
                missing = dict(config)
                del missing[key]
                with self.assertRaises(scout.ContractError):
                    scout.validate_config(missing)

    def test_prepare_rejects_ten_minute_buffer_before_io(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            config = self.config(base)
            config["lease_cutoff_unix"] = config["lease_end_unix"] - 600
            with patch.object(scout, "pin_local_inputs") as pins, \
                    patch.object(scout, "load_local_tokenizer") as tokenizer:
                with self.assertRaisesRegex(scout.ContractError, "six hours"):
                    scout.prepare_real(base / "run", config)
                pins.assert_not_called()
                tokenizer.assert_not_called()
            self.assertFalse((base / "run").exists())

    def test_execute_rejects_sealed_unsafe_lease_before_gpu_access(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "run"
            self.prepare(root, self.config(base))
            manifest = scout.load_json(root / "manifest.json")
            manifest["config"]["lease_cutoff_unix"] = manifest["config"]["lease_end_unix"] - 600
            (root / "manifest.json").write_bytes(scout.canonical(manifest))
            seal = scout.load_json(root / "PREPARED_SEAL.json")
            seal["manifest_sha256"] = scout.digest(manifest)
            (root / "PREPARED_SEAL.json").write_bytes(scout.canonical(seal))
            with patch.object(scout, "pin_local_inputs") as pins, \
                    patch.object(scout, "gpu_identity") as hardware, \
                    patch.object(scout, "launch_worker") as worker:
                with self.assertRaisesRegex(scout.ContractError, "six hours"):
                    scout.execute_real(root, allow_gpu=True)
                pins.assert_not_called()
                hardware.assert_not_called()
                worker.assert_not_called()
            self.assertFalse((root / "EXECUTION_STARTED.json").exists())

    def test_real_tokenizer_contract_covers_four_fit_and_all_generation_surfaces(self):
        material = scout.build_material()
        preflight = scout.real_preflight(material, scout.FixtureTokenizer())
        self.assertEqual(preflight["kind"], "REAL_LOCAL_TOKENIZER")
        self.assertEqual(len(preflight["encoded_fits"]), 4)
        self.assertEqual(sum(len(rows) for rows in preflight["encoded_fits"].values()), 512)
        self.assertEqual(len(preflight["generation_encodings"]), 464)
        self.assertEqual(len(preflight["context_pairs"]), 464)
        self.assertFalse(preflight["model_loaded"])

    def test_prepare_bindings_and_refusal_to_bypass_CPU_suite(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "run"
            config = self.config(base)
            with self.assertRaises(scout.ContractError):
                scout.prepare_real(root, config, run_tests=False)
            result = self.prepare(root, config)
            self.assertFalse(result["real_GPU_executed"])
            manifest = scout.validate_prepared(root)
            self.assertEqual(scout.load_json(root / "native_build_preflight.json"), self.native_receipt())
            self.assertEqual(manifest["artifact_hashes"]["native_build_preflight.json"],
                             scout.digest(self.native_receipt()))
            self.assertEqual(len(manifest["fits"]), 4)
            for key, value in scout.EVIDENCE_BOUNDARY.items():
                self.assertEqual(manifest[key], value)
            self.assertEqual(manifest["recipe"], scout.EXECUTION_RECIPE)
            with patch.object(scout, "source_hashes", return_value={}):
                with self.assertRaises(scout.ContractError):
                    scout.validate_prepared(root)
            path = root / "tokenizer_preflight.json"
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaises(scout.ContractError):
                scout.validate_prepared(root)

    def test_prepare_preserves_failed_CPU_receipt_without_ready_seal(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "run"
            config = self.config(base)
            completed = subprocess.CompletedProcess([], 1, b"", b"mock suite failure")
            with patch.object(scout, "native_build_preflight", return_value=self.native_receipt()), \
                    patch.object(scout, "pin_local_inputs", return_value=self.pins(config)), \
                    patch.object(scout, "load_local_tokenizer", return_value=scout.FixtureTokenizer()), \
                    patch.object(scout.subprocess, "run", return_value=completed):
                with self.assertRaises(scout.ContractError):
                    scout.prepare_real(root, config)
            self.assertTrue((root / "mwg10r1_cpu_suite_receipt.json").is_file())
            self.assertFalse((root / "PREPARED_SEAL.json").exists())

    def test_profile_budget_is_four_fits_without_extra_profile_fit(self):
        plan = scout.profile_plan()
        self.assertEqual(plan["fits"], 4)
        self.assertEqual(plan["total_optimizer_steps"], 1024)
        self.assertEqual(sum(plan["requests"].values()), 1504)
        self.assertIsNone(plan["actual_GPU_seconds"])
        self.assertEqual(plan["lease_finish_buffer_seconds"], 21600)
        self.assertEqual(plan["A40_hours_cap"], 3.0)
        self.assertFalse(plan["clean_lineage"])
        self.assertEqual(plan["official_model_authentication"], "UNRESOLVED_LOCAL_HASHES_ONLY")
        self.assertEqual(scout.remaining_budget(100, 50000, now_monotonic=200, now_wall=20000), 10700)
        self.assertEqual(scout.remaining_budget(100, 20005, now_monotonic=200, now_wall=20000), 5)
        self.assertLess(scout.remaining_budget(100, 50000, now_monotonic=10901, now_wall=20000), 0)

    def test_worker_cannot_run_without_controller_start_record(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scout.write_once(root, "job.json", {"stage": "fit_0_0"})
            with patch.object(scout, "configure_torch") as cuda:
                with self.assertRaises(FileNotFoundError):
                    scout.worker_main(root / "job.json")
                cuda.assert_not_called()

    def test_GPU_inventory_rejects_wrong_device_and_busy_GPU(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(Path(directory))
            output = subprocess.CompletedProcess([], 0, f"{config['gpu_uuid']}, NVIDIA A40, {config['driver_version']}\n", "")
            with patch.object(scout.platform, "node", return_value="cpu-test-node"), \
                    patch.object(scout.subprocess, "run", return_value=output):
                self.assertEqual(scout.gpu_identity(config), self.hardware(config))
                with self.assertRaises(scout.ContractError):
                    scout.assert_gpu_idle(config)
            output.stdout = output.stdout.replace("A40", "A100")
            with patch.object(scout.platform, "node", return_value="cpu-test-node"), \
                    patch.object(scout.subprocess, "run", return_value=output):
                with self.assertRaises(scout.ContractError):
                    scout.gpu_identity(config)

    def test_expired_budget_never_spawns_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(Path(directory))
            with patch.object(scout, "remaining_budget", return_value=0), \
                    patch.object(scout.subprocess, "Popen") as spawn:
                with self.assertRaises(scout.ContractError):
                    scout.launch_worker(Path(directory), {"stage": "fit_0_0"}, time.monotonic(), config)
                spawn.assert_not_called()

    def test_real_job_paths_must_stay_inside_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(scout.run_path(root, "adapter_fit_0_0"), root / "adapter_fit_0_0")
            for relative in ("/tmp/escape", "../escape", "nested/../../escape", "", "."):
                with self.subTest(relative=relative):
                    with self.assertRaises(scout.ContractError):
                        scout.run_path(root, relative)

    def test_watchdog_signals_only_its_owned_process_group(self):
        class Process:
            pid = 54321

            def __init__(self):
                self.wait_count = 0

            def poll(self):
                return None

            def wait(self, timeout):
                self.wait_count += 1
                if self.wait_count < 3:
                    raise subprocess.TimeoutExpired("mock-worker", timeout)
                return -9

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self.config(root)
            process = Process()
            job = {"stage": "fit_0_0", "seed": 0}
            with patch.object(scout, "remaining_budget", return_value=6), \
                    patch.object(scout.subprocess, "Popen", return_value=process) as spawn, \
                    patch.object(scout.os, "killpg") as kill:
                with self.assertRaises(subprocess.TimeoutExpired):
                    scout.launch_worker(root, job, time.monotonic(), config)
                self.assertTrue(spawn.call_args.kwargs["start_new_session"])
                self.assertEqual([call.args for call in kill.call_args_list],
                                 [(54321, scout.signal.SIGTERM), (54321, scout.signal.SIGKILL)])
            self.assertTrue((root / "fit_0_0_STARTED.json").exists())
            self.assertFalse((root / "fit_0_0_DONE.json").exists())

    def fake_worker(self, root, job, begin, config):
        stage = job["stage"]
        stage_index = len(list(root.glob("*_PROCESS.json")))
        pid = 50000 + stage_index
        base = dict(backend="HF_LOCAL_PINNED", worker_pid=pid, job_sha256=scout.digest(job),
                    manifest_sha256=job["manifest_sha256"], environment_sha256=scout.digest(config["environment"]),
                    model_sha256=config["model_sha256"], tokenizer_sha256=config["tokenizer_sha256"],
                    hardware=self.hardware(config), seed=job["seed"], source_hashes=job["source_hashes"])
        scout.write_once(root, f"{stage}_job.json", job)
        scout.write_once(root, f"{stage}_STARTED.json", dict(stage=stage, job_sha256=scout.digest(job), wall_start=time.time()))
        (root / f"{stage}.log").write_bytes(b"MOCK CPU WORKER: not real HF execution\n")
        if job["operation"] == "fit":
            adapter = root / job["adapter_directory"]
            adapter.mkdir()
            scout.write_once(adapter, "NOT_A_REAL_ADAPTER.json", {"stage": stage})
            steps = [dict(step=index + 1, epoch=index // 128, row=index % 128, loss=1.0, seconds=0.0) for index in range(256)]
            (root / f"{stage}_steps.jsonl").write_bytes(b"".join(scout.canonical(row) for row in steps))
            scout.write_once(root, f"{stage}_PROFILE.json", dict(steps=8, seconds=.001, extra_fits=0))
            scout.write_once(root, f"{stage}_LOAD.json", dict(base, adapter="OFF_CLEAN_BASE"))
            receipt = dict(base, optimizer_steps=256, recipe=scout.EXECUTION_RECIPE, update_norm=.1,
                           fit_input_sha256=job["input_sha256"], encoded_sha256=job["encoded_sha256"],
                           adapter_sha256=scout.tree_hash(adapter), final_lora_sha256=scout.digest(stage),
                           steps_sha256=scout.file_hash(root / f"{stage}_steps.jsonl"))
        else:
            material = scout.load_json(root / "material.json")
            requests = scout.load_json(root / "requests.json")
            fake = scout.fixture_records(material, requests)
            payloads = scout.load_json(root / job["requests_file"])
            preflight = scout.load_json(root / "tokenizer_preflight.json")
            output = root / job["raw_directory"]
            output.mkdir()
            for payload in payloads:
                request_id = scout.digest(payload)
                scout.write_once(output, request_id + ".json", fake[request_id])
                if job["operation"] == "score":
                    pairs = preflight["context_pairs"][scout.digest(payload["prompt"])]
                    trace = dict(candidate_input_ids=[pair["input_ids"] for pair in pairs],
                                 candidate_labels=[pair["labels"] for pair in pairs])
                else:
                    trace = dict(prompt_input_ids=preflight["generation_encodings"][scout.digest(payload["prompt"])])
                scout.write_once(output, request_id + "_trace.json", dict(request_sha256=request_id, **trace))
            scout.write_once(root, f"{stage}_LOAD.json", dict(base, adapter=job["adapter_sha256"], training=False))
            receipt = dict(base, requests_sha256=job["requests_sha256"], request_count=len(payloads),
                           raw_tree_sha256=scout.tree_hash(output))
        scout.write_once(root, f"{stage}_DONE.json", receipt)
        scout.write_once(root, f"{stage}_PROCESS.json", dict(
            stage=stage, job_sha256=scout.digest(job), worker_pid=pid, returncode=0,
            elapsed_seconds=.00001, log_sha256=scout.file_hash(root / f"{stage}.log")))
        return receipt

    def execute_mock(self, root, config, worker=None):
        with patch.object(scout, "native_build_preflight", return_value=self.native_receipt()), \
                patch.object(scout, "pin_local_inputs", return_value=self.pins(config)), \
                patch.object(scout, "load_local_tokenizer", return_value=scout.FixtureTokenizer()), \
                patch.object(scout, "gpu_identity", return_value=self.hardware(config)), \
                patch.object(scout, "assert_gpu_idle"), \
                patch.object(scout, "launch_worker", side_effect=worker or self.fake_worker):
            return scout.execute_real(root, allow_gpu=True)

    def test_mock_four_fit_controller_full_replay_and_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "run"
            config = self.config(base)
            self.prepare(root, config)
            report = self.execute_mock(root, config)
            self.assertEqual(report["scientific_label"], "MULTIKEY_BINDING_PASS")
            self.assertEqual(report["request_count"], 1504)
            for key, value in scout.EVIDENCE_BOUNDARY.items():
                self.assertEqual(report[key], value)
            self.assertEqual(len(list(root.glob("fit_*_DONE.json"))), 4)
            self.assertEqual(len(list(root.glob("eval_*_DONE.json"))), 10)
            self.assertEqual(scout.replay_real(root), report)
            with self.assertRaises(scout.ContractError):
                self.execute_mock(root, config)
            raw = next((root / "raw_eval_OFF_generate").glob("*.json"))
            raw.write_bytes(raw.read_bytes() + b" ")
            with self.assertRaises(scout.ContractError):
                scout.replay_real(root)

    def test_failed_worker_aborts_no_retries_or_scientific_label(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "run"
            config = self.config(base)
            self.prepare(root, config)
            calls = []

            def failure(root, job, begin, config):
                calls.append(job["stage"])
                raise scout.ContractError("MOCK failure before GPU")

            with self.assertRaises(scout.ContractError):
                self.execute_mock(root, config, failure)
            self.assertEqual(calls, ["fit_0_0"])
            self.assertIsNone(scout.load_json(root / "NONREPORTABLE_ABORT.json")["scientific_label"])
            self.assertFalse((root / "REAL_EXECUTION_SEAL.json").exists())


if __name__ == "__main__":
    unittest.main()
