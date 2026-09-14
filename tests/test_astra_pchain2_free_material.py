"""Focused synthetic-tokenizer tests; no native tokenizer, solver, or model."""

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from gpu import astra_pchain2_free_material as free
from gpu import astra_pchain2_native as native
from gpu import astra_pchain2_prepare as source
from test_astra_pchain2_native import FakeTokenizer, canary_fixture


def saved_fixture():
    return dict(master=source.MATERIAL_MASTER.decode("ascii"), native_length=8, salt_limit=4096,
                identifiers=[native.identifier_candidate(serial, 0) for serial in range(192)], accepted_salts=[0] * 192)


class FreeMaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = FakeTokenizer()
        cls.saved = saved_fixture()
        with patch.object(native, "allocate_identifiers", side_effect=AssertionError("no redraw")), \
                patch.object(native.nulls, "solve_assignment", side_effect=AssertionError("no solver")), \
                patch.object(native, "HFState", side_effect=AssertionError("no model")):
            cls.material = free.generate_material(cls.tokenizer, saved_identifiers=cls.saved, canaries=canary_fixture())
        facts, prompts, skills = native._domain_roles(tuple(cls.saved["identifiers"]))
        cls.facts = tuple(source.Chain(facts[index], facts[16 + index], facts[32 + index]) for index in range(16))
        cls.prompts = tuple(source.Chain(prompts[index], prompts[16 + index], prompts[32 + index]) for index in range(16))
        cls.skills = tuple(source.Chain(skills[index], skills[32 + index], skills[64 + index]) for index in range(32))

    def test_saved_identifiers_validate_once_without_allocation(self):
        with patch.object(native, "allocate_identifiers", side_effect=AssertionError("no redraw")), \
                patch.object(native, "identifier_candidate", wraps=native.identifier_candidate) as candidate:
            identifiers = free.validate_saved_identifiers(self.saved, self.tokenizer)
        self.assertEqual(identifiers, tuple(self.saved["identifiers"]))
        self.assertEqual([call.args for call in candidate.call_args_list], [(serial, 0) for serial in range(192)])

    def test_bad_saved_receipts_fail_without_repair(self):
        mutations = []
        for key, value in (("master", "other"), ("native_length", 7), ("identifiers", self.saved["identifiers"][:-1]),
                           ("accepted_salts", [False] * 192), ("salt_limit", 0)):
            changed = deepcopy(self.saved)
            changed[key] = value
            mutations.append(changed)
        for replacement in (self.saved["identifiers"][1], "UPPERCASEINVALID!", "abcdefghijklmnop"):
            changed = deepcopy(self.saved)
            changed["identifiers"][0] = replacement
            mutations.append(changed)
        with patch.object(native, "allocate_identifiers", side_effect=AssertionError("no redraw")):
            for changed in mutations:
                with self.subTest(receipt=changed), self.assertRaises(ValueError):
                    free.validate_saved_identifiers(changed, self.tokenizer)

    def test_native_L8_roundtrip_and_deadline_fail_closed(self):
        with patch.object(self.tokenizer, "encode", return_value=[5] * 7), \
                self.assertRaisesRegex(ValueError, "not_native_L8"):
            free.validate_saved_identifiers(self.saved, self.tokenizer)
        with patch.object(self.tokenizer, "decode", return_value="wrong"), \
                self.assertRaisesRegex(ValueError, "roundtrip"):
            free.validate_saved_identifiers(self.saved, self.tokenizer)
        with self.assertRaisesRegex(TimeoutError, "bounded"):
            free.validate_saved_identifiers(self.saved, self.tokenizer,
                                            check=lambda: (_ for _ in ()).throw(TimeoutError("bounded")))

    def test_successor_kind_budget_and_simple_endpoint_assignment(self):
        summary = self.material["summary"]
        self.assertEqual(summary["material_kind"], "PCHAIN2_FREE_ENDPOINT_DEV_V1")
        self.assertEqual(summary["budget"], source.build_d1_plan()["budget"])
        self.assertEqual((summary["solver_calls"], summary["identifier_allocation_calls"], summary["model_calls"], summary["fits"]),
                         (0, 0, 0, 0))
        self.assertFalse(summary["claim_boundary"]["original_pchain2_protocol_compliance"])
        self.assertFalse(summary["claim_boundary"]["null_clearance"])
        self.assertEqual(sum(len(manifest["calls"]) for manifest in self.material["evaluation"].values()), 448)
        for index, chain in enumerate(self.facts):
            rows = self.material["training"]["ATOM-JUNCTION"]["rows"]
            self.assertEqual(rows[2 * index + 1]["messages"][-1]["content"], source._memory(chain.middle, chain.endpoint))
        for namespace in ("training", "evaluation"):
            for manifest in self.material[namespace].values():
                self.assertEqual(manifest["material_kind"], free.MATERIAL_KIND)
                self.assertNotIn("ENDPOINT CANDIDATES", json.dumps(manifest))
                self.assertNotIn("DIAGNOSTIC_INJECTED_SOLVER", json.dumps(manifest))

    def test_only_candidate_blocks_change_and_onehop_is_identical(self):
        orders = lambda chains: tuple(tuple(chain.endpoint for chain in chains[index // 8 * 8:index // 8 * 8 + 8])
                                     for index in range(16))
        previous = source.prepare_evaluation(fact_chains=self.facts, prompt_chains=self.prompts,
                                             permutation=source.SECOND_HOP_PERMUTATION,
                                             fact_candidates=orders(self.facts), prompt_candidates=orders(self.prompts))
        successor = free.prepare_free_evaluation(fact_chains=self.facts, prompt_chains=self.prompts)
        for before, after in zip(previous.calls, successor.calls):
            self.assertEqual(before.slot, after.slot)
            self.assertEqual(before.expected, after.expected)
            if before.user is None or before.slot.panel == "one_hop":
                self.assertEqual(before.user, after.user)
            else:
                expected = re.sub(r"ENDPOINT CANDIDATES\n(?:[a-z]{16}\n){8}", "", before.user)
                self.assertEqual(after.user, expected)
                self.assertNotIn("ENDPOINT CANDIDATES", after.user)
                self.assertTrue(after.user.endswith("\n"))
                self.assertFalse(after.user.endswith("\n\n"))

    def test_same_ID_permutation_redirects_only_endpoint_and_second_hop(self):
        evaluation = free.prepare_free_evaluation(fact_chains=self.facts, prompt_chains=self.prompts)
        calls = {(call.slot.state, call.slot.panel, call.slot.index): call for call in evaluation.calls}
        for index, chain in enumerate(self.facts):
            redirected = self.facts[index ^ 1].endpoint
            for panel in ("eval_trace", "eval_direct"):
                original = calls["ATOM-JUNCTION", panel, index]
                changed = calls["DERANGED-JUNCTION", panel, index]
                self.assertEqual(original.user, changed.user)
                self.assertEqual(changed.expected, original.expected.replace(chain.endpoint.encode(), redirected.encode()))
                self.assertNotIn(chain.endpoint, original.user)
                self.assertNotIn(redirected, changed.user)
            self.assertEqual(calls["ATOM-JUNCTION", "one_hop", index],
                             source.ReadoutCall(calls["ATOM-JUNCTION", "one_hop", index].slot,
                                                calls["DERANGED-JUNCTION", "one_hop", index].user,
                                                calls["DERANGED-JUNCTION", "one_hop", index].expected))

    def test_training_unchanged_marginals_masks_tape_and_domains(self):
        prepared = source.prepare_training(fact_chains=self.facts, junction_examples=self.skills)
        prompt_ids = {identifier for chain in self.prompts for identifier in chain.identifiers}
        for state in prepared.states:
            manifest = json.loads(json.dumps(self.material["training"][state.name]))
            self.assertEqual(manifest["rows"], state.trainer_manifest()["rows"])
            self.assertFalse(any(identifier in json.dumps(manifest) for identifier in prompt_ids))
            rows, tape = native.validate_training_manifest(manifest, self.tokenizer, state=state.name, max_context=16384)
            self.assertEqual(len(tape), 384)
            self.assertEqual(sum(len(batch.row_ids) for batch in tape), 1536)
            for row in rows:
                self.assertEqual(tuple(token for token in row.labels if token != -100), row.target_ids)
                self.assertEqual(row.labels[-1], -100)
        def counts(state, assistant_only):
            return Counter(identifier for row in self.material["training"][state]["rows"][32:]
                           for message in row["messages"] if not assistant_only or message["role"] == "assistant"
                           for identifier in re.findall(r"[a-z]{16}", message["content"]))
        for assistant_only in (False, True):
            authentic = counts("ATOM-JUNCTION", assistant_only)
            self.assertEqual(authentic, counts("ATOM-LOCAL", assistant_only))
            for chain in self.skills:
                self.assertEqual(tuple(authentic[identifier] for identifier in chain.identifiers),
                                 (1, 2, 2) if assistant_only else (3, 4, 3))

    def test_native_readout_context_and_strict_free_scoring(self):
        for state, manifest in self.material["evaluation"].items():
            prompts = native.validate_readout_manifest(manifest, self.tokenizer, state=state, max_context=16384)
            self.assertEqual(len(prompts), len(manifest["calls"]))
            with self.assertRaisesRegex(ValueError, "context_overflow"):
                native.validate_readout_manifest(manifest, self.tokenizer, state=state, max_context=1)
        evaluation = free.prepare_free_evaluation(fact_chains=self.facts, prompt_chains=self.prompts)
        call = next(call for call in evaluation.calls if call.slot.panel == "eval_trace")
        self.assertTrue(source.strict_match(call, call.expected, terminal=True, truncated=False))
        self.assertFalse(source.strict_match(call, call.expected.rstrip(), terminal=True, truncated=False))
        self.assertFalse(source.strict_match(call, call.expected, terminal=False, truncated=False))

    def test_material_checks_held_context_not_only_training_context(self):
        original = self.tokenizer.apply_chat_template

        def overflowing(messages, **kwargs):
            result = original(messages, **kwargs)
            if kwargs["tokenize"] and len(messages) == 2:
                return result + [1000] * 16384
            return result

        with patch.object(self.tokenizer, "apply_chat_template", side_effect=overflowing), \
                self.assertRaisesRegex(ValueError, "readout_context_overflow"):
            free.generate_material(self.tokenizer, saved_identifiers=self.saved)

    def test_missing_canaries_block_readout_not_material(self):
        material = free.generate_material(self.tokenizer, saved_identifiers=self.saved)
        self.assertEqual(material["summary"]["missing_canary_calls"], 48)
        with self.assertRaisesRegex(ValueError, "bind_canaries"):
            native.validate_readout_manifest(material["evaluation"]["ATOM-JUNCTION"], self.tokenizer,
                                             state="ATOM-JUNCTION", max_context=16384)

    def test_free_kind_does_not_bypass_native_mask_tape_or_roster_checks(self):
        for field in ("encoded_rows", "dropout_seeds", "recipe"):
            manifest = json.loads(json.dumps(self.material["training"]["ATOM-JUNCTION"]))
            if field == "encoded_rows":
                manifest[field][0]["labels"][0] = 1000
            elif field == "dropout_seeds":
                manifest[field][0] += 1
            else:
                manifest[field]["learning_rate"] = "0.1"
            with self.subTest(field=field), self.assertRaises(ValueError):
                native.validate_training_manifest(manifest, self.tokenizer, state="ATOM-JUNCTION", max_context=16384)
        manifest = deepcopy(self.material["evaluation"]["ATOM-JUNCTION"])
        manifest["calls"].pop()
        with self.assertRaisesRegex(ValueError, "exact_state_readout_roster"):
            native.validate_readout_manifest(manifest, self.tokenizer, state="ATOM-JUNCTION", max_context=16384)

    def test_CLI_deadline_records_failure_without_redraw(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            native._write(root / "identifiers.json", self.saved)
            output = root / "free"
            argv = ["--identifiers-file", str(root / "identifiers.json"), "--model-dir", directory, "--output", str(output)]
            with patch.object(free.signal, "signal", return_value=free.signal.SIG_DFL) as handler, \
                    patch.object(free.signal, "setitimer", return_value=(0, 0)) as timer, \
                    patch.object(native, "allocate_identifiers", side_effect=AssertionError("no redraw")):
                def stalled_load(path):
                    timer.assert_called_once_with(free.signal.ITIMER_REAL, 180)
                    handler.call_args.args[1](free.signal.SIGALRM, None)

                with patch.object(native, "load_local_tokenizer", side_effect=stalled_load), \
                        self.assertRaisesRegex(TimeoutError, "caller_deadline_exceeded"):
                    free.main(argv)
                timer.assert_called_with(free.signal.ITIMER_REAL, 0)
                handler.assert_called_with(free.signal.SIGALRM, free.signal.SIG_DFL)
            self.assertFalse((output / "RESULT.json").exists())
            failure = native._read(output / "FAILED.json")
            self.assertEqual(failure["material_kind"], free.MATERIAL_KIND)
            self.assertFalse(failure["retried"])

    def test_CLI_reuses_exact_input_bytes_no_solver_no_model_no_overwrite(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            raw = json.dumps(self.saved, indent=2).encode()
            saved_path = root / "identifiers.json"
            saved_path.write_bytes(raw)
            output = root / "free"
            argv = ["--identifiers-file", str(saved_path), "--model-dir", directory, "--output", str(output)]
            with patch.object(native, "load_local_tokenizer", return_value=self.tokenizer), \
                    patch.object(native, "allocate_identifiers", side_effect=AssertionError("no redraw")), \
                    patch.object(native.nulls, "build_null_registry", side_effect=AssertionError("no registry")), \
                    patch.object(native.nulls, "solve_assignment", side_effect=AssertionError("no solver")), \
                    patch.object(native, "HFState", side_effect=AssertionError("no model")):
                free.main(argv)
                with self.assertRaises(FileExistsError):
                    free.main(argv)
            self.assertEqual(saved_path.read_bytes(), raw)
            self.assertEqual((output / "identifiers.json").read_bytes(), raw)
            self.assertEqual(native._read(output / "RESULT.json")["material_kind"], free.MATERIAL_KIND)
            self.assertEqual(len(list((output / "training").glob("*.json"))), 4)
            self.assertEqual(len(list((output / "evaluation").glob("*.json"))), 5)
            self.assertFalse((output / "null_registry.json").exists())


if __name__ == "__main__":
    unittest.main()
