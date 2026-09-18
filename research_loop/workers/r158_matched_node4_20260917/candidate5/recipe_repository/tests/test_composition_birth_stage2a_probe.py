"""Synthetic one-call custody checks, not model or tokenizer validation."""

from dataclasses import replace
import unittest

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_probe as source
from organism_v6 import composition_birth_stage2a_rollout as rollout


class ProbeTests(unittest.TestCase):
    def run_fixture(self, generation=None, **overrides):
        options = dict(
            slot=primitives.canary_slot("D1", 0), master=b"synthetic-probe",
            actor=lambda request: generation or rollout.Generation("unchanged raw\n", 1, 1, False, "stop"),
            count_context=lambda prefix: 1, counter_provenance="synthetic-counter",
        )
        options.update(overrides)
        return source.run_probe((held.Message("system", "copy"), held.Message("user", "public bytes")), **options)

    def test_raw_preserved_unscored_not_trimmed(self):
        result = self.run_fixture()
        self.assertTrue(result.called)
        self.assertTrue(result.generation_valid)
        self.assertEqual(result.raw_bytes, b"unchanged raw\n")
        self.assertEqual(result.reason, "completed_unscored")
        self.assertEqual(set(vars(result.request)), {"prefix", "max_new_tokens", "seed", "context_tokens"})
        self.assertFalse(any(source.SCIENCE_GATES.values()))

    def test_no_call_when_context_exhausted(self):
        result = self.run_fixture(actor=lambda request: self.fail("no generation allowed"),
                                  count_context=lambda prefix: wire.CONTEXT_CAP)
        self.assertFalse(result.called)
        self.assertFalse(result.generation_valid)
        self.assertEqual(result.reason, "zero_allowance")

    def test_metadata_failures_keep_raw_and_fixed_call(self):
        valid = rollout.Generation("STOP", 1, 1, False, "stop")
        for changes in (dict(truncated=True), dict(finish_reason="length"), dict(finish_reason="error"),
                        dict(actual_tokens=True), dict(declared_tokens=2), dict(actual_tokens=257)):
            with self.subTest(changes=changes):
                result = self.run_fixture(replace(valid, **changes))
                self.assertTrue(result.called)
                self.assertFalse(result.generation_valid)
                self.assertEqual(result.raw_bytes, b"STOP")
                self.assertIsNotNone(result.generation_capture)

    def test_uncapturable_metadata_still_preserves_raw(self):
        result = self.run_fixture(rollout.Generation("STOP", object(), 1, False, "stop"))
        self.assertEqual(result.reason, "unsupported_custody_transport")
        self.assertEqual(result.raw_bytes, b"STOP")
        self.assertTrue(result.called)
        self.assertIsNone(result.generation_capture)

    def test_chain_slot_rejected(self):
        with self.assertRaisesRegex(ValueError, "one_turn_logical_slot"):
            self.run_fixture(slot=primitives.chain_slot("D1", 0, 0, 0))

    def test_intervention_slot_preserves_original_seed(self):
        slot = primitives.intervention_slot("D2", "CHECK", 6, 1)
        result = self.run_fixture(slot=slot)
        self.assertEqual(result.request.seed,
                         primitives.decode_seed(b"synthetic-probe", slot.panel_label, slot.global_ordinal))

    def test_callback_exception_not_a_fake_output(self):
        def failed(request):
            raise RuntimeError("fixture")

        result = self.run_fixture(actor=failed)
        self.assertTrue(result.called)
        self.assertFalse(result.generation_valid)
        self.assertIsNone(result.raw_bytes)
        self.assertEqual(result.error_type, "RuntimeError")


if __name__ == "__main__":
    unittest.main()
