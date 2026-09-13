from collections import Counter
from dataclasses import FrozenInstanceError
from hashlib import sha256
import unittest

from organism_v6 import composition_birth_stage2a_curriculum as source
from tests.test_composition_birth_stage2a_birth import synthetic_bindings


class BirthCurriculumTests(unittest.TestCase):
    MASTER = b"SYNTHETIC-CURRICULUM-COMPILER"

    @classmethod
    def setUpClass(cls):
        cls.bindings = {f"p{pair:02d}": synthetic_bindings(pair) for pair in range(32)}
        cls.result = source.compile_birth_curriculum(role_tokens_by_world=cls.bindings, master=cls.MASTER)

    def test_complete_case_target_and_update_chain(self):
        result = self.result
        self.assertEqual(len(result.pairs), 32)
        self.assertEqual(sum(len(pair.cases) for pair in result.pairs), 64)
        self.assertEqual(len(result.paired_targets), 256)
        self.assertEqual(dict(result.command_counts), {"READ": 96, "STEP": 64, "THINK": 64, "STOP": 32})
        self.assertEqual(len(result.batches), 512)
        self.assertEqual(result.batches[255].update_number, 256)
        self.assertEqual(result.batches[256].update_number, 257)
        self.assertEqual(result.batches[256].stage, "D2")
        for batches, dose in ((result.batches[:256], 4), (result.batches, 8)):
            self.assertEqual(Counter(unit for batch in batches for unit in batch.unit_ids),
                             {unit: dose for unit in result.target_hashes})

    def test_shared_master_and_targets_no_model_measurements(self):
        self.assertEqual(self.result.master_sha256, sha256(self.MASTER).hexdigest())
        self.assertEqual(self.result.adapter_initialization_seed,
                         int.from_bytes(sha256(self.MASTER + b"\0adapter-init").digest()[-8:], "big"))
        for pair in self.result.paired_targets:
            self.assertIs(pair.closed.unit, pair.atom_local.unit)
            self.assertEqual(self.result.target_hashes[pair.closed.unit.unit_id],
                             sha256(pair.closed.unit.target_bytes).hexdigest())
        self.assertFalse(any(source.SCIENCE_GATES.values()))
        self.assertEqual(self.result.status, "PARTIAL_SOURCE_ONLY")
        self.assertNotIn("tokens", repr(self.result.prefix_accounting))

    def test_prefix_residuals_are_reported_not_padded_away(self):
        accounting = self.result.prefix_accounting
        residual = accounting["CLOSED_MINUS_ATOM_LOCAL"]
        self.assertEqual(residual["unit_count"], 0)
        self.assertEqual(residual["target_content_bytes"], 0)
        self.assertGreater(residual["prefix_messages"], 0)
        self.assertGreater(residual["prefix_content_bytes"], 0)
        self.assertGreater(residual["prefix_serialized_bytes"], 0)
        for name, select in (("CLOSED", lambda pair: pair.closed), ("ATOM_LOCAL", lambda pair: pair.atom_local)):
            records = tuple(select(pair) for pair in self.result.paired_targets)
            self.assertEqual(accounting[name]["prefix_messages"], sum(len(record.prefix) for record in records))
            self.assertEqual(accounting[name]["prefix_content_bytes"],
                             sum(len(message.content.encode("ascii")) for record in records for message in record.prefix))

    def test_complete_roster_and_early_collision_rejection(self):
        missing = dict(self.bindings)
        missing.pop("p31")
        for mapping in (missing, dict(self.bindings, p32={}), None):
            with self.assertRaises(ValueError):
                source.compile_birth_curriculum(role_tokens_by_world=mapping, master=self.MASTER)
        collision = dict(self.bindings)
        collision["p01"] = dict(collision["p01"])
        first = next(iter(collision["p00"]))
        second = next(iter(collision["p01"]))
        collision["p01"][second] = collision["p00"][first]
        with self.assertRaisesRegex(ValueError, "cross_world_duplicate"):
            source.compile_birth_curriculum(role_tokens_by_world=collision, master=self.MASTER)
        with self.assertRaises(ValueError):
            source.compile_birth_curriculum(role_tokens_by_world=self.bindings, master=None)

    def test_bound_outputs_are_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            self.result.status = "PASS"
        with self.assertRaises(TypeError):
            self.result.target_hashes["p00/m0/u0"] = "changed"
        with self.assertRaises(TypeError):
            self.result.prefix_accounting["CLOSED"]["unit_count"] = 1


if __name__ == "__main__":
    unittest.main()
