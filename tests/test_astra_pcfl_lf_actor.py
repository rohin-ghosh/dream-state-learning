"""CPU/injected tests only; no installed constraint engine or native model."""

import copy
import hashlib
from pathlib import Path
import re
import unittest

import test_astra_pcfl_native_actor as fixtures
from gpu import astra_pcfl_lf_actor as scoped
from gpu import astra_pcfl_native_actor as native
from organism_v6 import pcfl_vertical_dev as core


class SamplingTests(unittest.TestCase):
    def test_exact_twelve_commitments_only(self):
        self.assertEqual(scoped.REGEX, r"[^\r\n]+\n")
        self.assertEqual(len(scoped.COMMITMENT_IDS), 12)
        limits = {"output_tokens": 2048}
        for index in range(20):
            request = {"id": f"old/formation/{index:02d}", "seed": 0}
            expected = {**native.SAMPLING, "seed": 0, "max_tokens": 2048}
            if index % 2 or index >= 16:
                expected["structured_outputs"] = {"regex": scoped.REGEX}
            self.assertEqual(scoped.sampling_for(request, limits), expected)

    def test_nonformation_and_malformed_ids_unchanged(self):
        for name in ("old/formation/1", "old/formation/001", "old/formation/20", "old/formation/01/extra",
                     "old/formation/01\n", "new/formation/01", "READ/01", "task/0/actor/0"):
            with self.subTest(name=name):
                self.assertEqual(scoped.sampling_for({"id": name, "seed": 71}, {"output_tokens": 100}),
                                 {**native.SAMPLING, "seed": 71, "max_tokens": 100})

    def test_sampling_is_target_blind_and_detached(self):
        request = {"id": "old/formation/01", "seed": 0, "messages": "arbitrary wrong public content"}
        limits = {"output_tokens": 2048}
        original = copy.deepcopy(request)
        sampling = scoped.sampling_for(request, limits)
        sampling["structured_outputs"]["regex"] = "changed caller copy"
        self.assertEqual(request, original)
        self.assertEqual(limits, {"output_tokens": 2048})
        request["messages"] = "different public content"
        self.assertEqual(scoped.sampling_for(request, limits)["structured_outputs"], {"regex": scoped.REGEX})
        self.assertNotIn("structured_outputs", native.SAMPLING)

    def test_regex_is_only_a_line_envelope_not_a_semantic_or_syntax_answer(self):
        for raw in ("totally wrong content\n", "EVENT wrong identifiers\n", "LINK unsupported pair\n", "x\n"):
            with self.subTest(raw=raw):
                self.assertIsNotNone(re.fullmatch(scoped.REGEX, raw))
                with self.assertRaises(ValueError):
                    core.parse_event_line(raw)
        for raw in ("", "\n", "x", "x\\n", "x\r\n", "x\n\n", "x\ny\n", "x\nprose"):
            with self.subTest(raw=raw):
                self.assertIsNone(re.fullmatch(scoped.REGEX, raw))


class LFActorTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ActorTests("test_real_actor_public_api_captures_exact_tokens_and_bytes")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.config = copy.deepcopy(self.fixture.config)
        source = Path(scoped.__file__).resolve()
        self.config["source_files"][str(source)] = hashlib.sha256(source.read_bytes()).hexdigest()
        self.request = {**self.fixture.request, "id": "old/formation/01"}

    def actor(self):
        actor = scoped.LFNativeActor(self.config, loader=self.fixture.loader,
                                     environment_reader=lambda: copy.deepcopy(self.fixture.environment),
                                     clock=self.fixture.clock)
        self.addCleanup(actor.close)
        return actor

    def test_own_source_pin_required_before_loading(self):
        del self.config["source_files"][str(Path(scoped.__file__).resolve())]
        with self.assertRaisesRegex(native.ActorError, "LF actor source"):
            self.actor()
        self.fixture.loader.assert_not_called()
        self.assertFalse(Path(self.config["output_dir"]).exists())

    def test_wrong_own_source_hash_fails_before_loading(self):
        self.config["source_files"][str(Path(scoped.__file__).resolve())] = "0" * 64
        actor = self.actor()
        with self.assertRaisesRegex(native.ActorError, "source identity drift"):
            actor.generate(self.request, self.fixture.limits)
        self.fixture.loader.assert_not_called()
        self.assertEqual(self.fixture.session.calls, [])

    def test_exact_sampling_and_raw_capture_no_repair_or_retry(self):
        actor = self.actor()
        raw = "EVENT E_AAAAAAAAAA AT N_AAAAAAAAAA DID P_AAAAAAAAAA GOT N_BBBBBBBBBB EVIDENCE R_AAAAAAAAAA"
        self.fixture.session.text = raw
        response = actor.generate(self.request, self.fixture.limits)
        self.assertEqual(response["text"], raw)
        expected = scoped.sampling_for(self.request, self.fixture.limits)
        self.assertEqual(self.fixture.session.calls[0][1], expected)
        self.assertEqual(self.fixture.read("call_0000.render.json")["sampling"], expected)
        self.assertEqual(self.fixture.read("call_0000.raw.json")["raw"]["text"], raw)
        self.assertEqual(self.fixture.read("call_0000.response.json")["raw_hex"], raw.encode().hex())
        with self.assertRaises(ValueError):
            core.parse_event_line(response["text"])
        with self.assertRaisesRegex(native.ActorError, "already consumed"):
            actor.generate(self.request, self.fixture.limits)
        self.assertEqual(len(self.fixture.session.calls), 1)
        self.assertIn(str(Path(scoped.__file__).resolve()), self.fixture.read("identity.json")["identity"]["source_files"])

    def test_explore_is_unconstrained_even_with_commitment_words_in_prompt(self):
        actor = self.actor()
        self.request["id"] = "old/formation/00"
        self.request["messages"][1]["content"] = "COMMIT EVENT COMMIT LINK"
        actor.generate(self.request, self.fixture.limits)
        self.assertEqual(self.fixture.session.calls[0][1],
                         {**native.SAMPLING, "seed": 71, "max_tokens": 100})

    def test_length_finish_is_preserved_not_promoted_to_stop(self):
        actor = self.actor()
        self.fixture.session.text = "wrong\n"
        self.fixture.session.mutate = lambda raw: {**raw, "finish_reason": "length"}
        response = actor.generate(self.request, self.fixture.limits)
        self.assertEqual(response["text"], "wrong\n")
        self.assertEqual(self.fixture.read("call_0000.raw.json")["raw"]["finish_reason"], "length")


if __name__ == "__main__":
    unittest.main()
