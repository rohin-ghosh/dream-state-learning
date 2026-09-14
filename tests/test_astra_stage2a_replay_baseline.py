"""Synthetic persisted replay only: no GPU, model, tokenizer or native tensor load."""

from dataclasses import replace
import builtins
from hashlib import sha256
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_stage2a_replay_baseline as replay
from organism_v6 import composition_birth_stage2a_canaries as canary_api
from organism_v6 import composition_birth_stage2a_checkpoint as checkpoint
from organism_v6 import composition_birth_stage2a_held as held_api
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_rollout as rollout
from organism_v6 import composition_birth_stage2a_scoring as scoring
from organism_v6 import composition_birth_stage2a_screen as screen
from organism_v6 import composition_birth_stage2a_screen_custody as custody
from organism_v6 import composition_birth_stage2a_screen_reduce as reducer
from organism_v6 import composition_birth_stage2a_screen_runtime as runtime
from tests.test_composition_birth_stage2a_held import fixtures


MASTER = b"synthetic-retained-screen-replay"
BASE_ID = "synthetic-BASE-replay-attempt-1"
ATOM_ID = "synthetic-ATOM-replay-attempt-1"


class ReplayStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chain_tokens = fixtures("dose_chain")
        intervention_tokens = fixtures("dose_intervention")
        cls.held = SimpleNamespace(
            chains={task: held_api.build_chain_world(world=f"h{task // 2:02d}",
                    role_tokens=chain_tokens[f"h{task // 2:02d}"]) for task in screen.CHAIN_TASKS},
            interventions={(transition, index): held_api.build_intervention_pair(
                world=f"{transition.lower()}_k{index}",
                role_tokens=intervention_tokens[f"{transition.lower()}_k{index}"])
                for transition in primitives.TRANSITIONS for index in screen.INTERVENTION_PAIRS},
            canaries=canary_api.build_canaries(role_tokens={role: token
                for tokens in fixtures("generic_canary").values() for role, token in tokens.items()}))

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def capture(self, name="BASE", state_id=BASE_ID, *, successful=False,
                malformed=False, actor_offset=0, abort=False, mutate=None, stage="D1"):
        outputs = {}
        seeds = screen.reduced_decode_seeds(stage, master=MASTER)
        for position, task in enumerate(screen.CHAIN_TASKS):
            script = ([turn.action for turn in self.held.chains[task].members[0].expected_trace]
                      if successful else ["STOP"])
            for ordinal, raw in enumerate(script):
                outputs[seeds[position * 29 + ordinal]] = raw
        for position, pair in enumerate(self.held.interventions.values()):
            for member, world in enumerate(pair.members):
                outputs[seeds[232 + position * 2 + member]] = world.expected_target.bytes
        for index, canary in enumerate(self.held.canaries):
            outputs[seeds[264 + index]] = canary.target
        records = [{} for unused in range(actor_offset)]

        def actor(request):
            generation = rollout.Generation("bad output" if malformed else outputs[request.seed],
                                            1, 1, malformed, "length" if malformed else "stop")
            record = dict(request=request, generation=generation, error=None,
                          raw=generation.raw, raw_bytes=generation.raw.encode("utf-8"))
            records.append(record)
            if abort:
                error = ValueError("synthetic actor failure")
                record["error"] = error
                raise error
            return generation

        directory = self.root / name
        with custody.ScreenCustodySink(directory) as storage:
            def sink(event, payload):
                storage(event, mutate(event, payload) if mutate else payload)

            run = runtime.run_reduced_state(state_id=state_id, stage=stage, master=MASTER,
                chains=self.held.chains, interventions=self.held.interventions,
                canaries=self.held.canaries, actor=actor, actor_calls=records,
                count_context=lambda prefix: len(prefix) + 7,
                counter_provenance="SYNTHETIC_RETAINED_COUNTS", custody_sink=sink)
        self.assertEqual(storage.status, "complete", run.failures)
        return directory, run

    def replay(self, directory, state_id=BASE_ID, **options):
        return replay.replay_state(directory, state_id=state_id, master=MASTER,
                                   held=self.held, **options)

    def reduce(self, base, atom, *, stage="D1"):
        reduce_state = reducer.reduce_base_d1 if stage == "D1" else reducer.reduce_base_d2
        return reduce_state(base=base, atom_local=atom, base_state_id=BASE_ID,
            atom_local_state_id=ATOM_ID, master=MASTER, chains=self.held.chains,
            interventions=self.held.interventions, canaries=self.held.canaries)

    def test_d2_replay_keeps_separate_stage_slots_seeds_and_unchanged_thresholds(self):
        base_dir, unused = self.capture()
        atom_d1_dir, unused = self.capture("ATOM_D1", ATOM_ID, successful=True)
        atom_d2_dir, original = self.capture("ATOM_D2", ATOM_ID, successful=True, stage="D2")
        base = self.replay(base_dir)
        atom_d1 = self.replay(atom_d1_dir, ATOM_ID)
        atom_d2 = self.replay(atom_d2_dir, ATOM_ID, stage="D2")
        self.assertEqual(atom_d2.stage, "D2")
        self.assertEqual(atom_d2.chain_runs, original.chain_runs)
        self.assertEqual(atom_d2.probe_runs, original.probe_runs)
        for stage, run in (("D1", base), ("D2", atom_d2)):
            self.assertEqual(tuple(row.entry for row in run.reservations), screen.reduced_screen(stage))
            self.assertEqual(tuple(row.seed for row in run.reservations),
                             screen.reduced_decode_seeds(stage, master=MASTER))
        self.assertTrue(set(row.seed for row in base.reservations).isdisjoint(
                        row.seed for row in atom_d2.reservations))
        first = self.reduce(base, atom_d1)
        second = self.reduce(base, atom_d2, stage="D2")
        self.assertTrue(second.reportable, (second.base.issues, second.atom_local.issues))
        self.assertTrue(second.criteria_passed)
        self.assertEqual(first.criteria, second.criteria)
        self.assertEqual([(item.name, item.denominator, item.minimum) for item in second.criteria],
            [(name, 4, 3) for name in primitives.TRANSITIONS] + [
                ("typed_interventions", 32, 30), ("whole_chains", 8, 6), ("useful_reads", 8, 7),
                ("typed_steps", 8, 7), ("canaries", 16, 15), ("chain_gain", 8, 2)])
        self.assertIs(second.base.run, base)
        self.assertIs(second.atom_local.run, atom_d2)
        self.assertFalse(second.native_authorized)
        self.assertFalse(second.persisted_custody_verified)

    def test_d2_requires_explicit_stage_and_d1_default_stays_strict(self):
        base_dir, base = self.capture()
        atom_dir, atom = self.capture("ATOM_D2", ATOM_ID, successful=True, stage="D2")
        with self.assertRaisesRegex(ValueError, "state_or_stage_identity_mismatch"):
            self.replay(atom_dir, ATOM_ID)
        with self.assertRaisesRegex(ValueError, "state_or_stage_identity_mismatch"):
            self.replay(base_dir, stage="D2")
        with self.assertRaisesRegex(ValueError, "explicit_D1_or_D2_stage_required"):
            self.replay(atom_dir, ATOM_ID, stage="D3")
        d1 = self.reduce(base, atom)
        self.assertFalse(d1.reportable)
        self.assertIn("state_or_stage_identity_mismatch", d1.atom_local.issues)
        default = reducer._reduce_state(atom, ATOM_ID, screen.reduced_decode_seeds("D2", master=MASTER),
            set(), master=MASTER, chains=self.held.chains, interventions=self.held.interventions,
            canaries=self.held.canaries)
        self.assertFalse(default.reportable)

    def test_d2_rejects_relabeling_d1_and_foreign_stage_baseline(self):
        unused, base = self.capture()
        unused, atom_d1 = self.capture("ATOM_D1", ATOM_ID, successful=True)
        unused, atom_d2 = self.capture("ATOM_D2", ATOM_ID, successful=True, stage="D2")
        for candidate, issue in ((atom_d1, "state_or_stage_identity_mismatch"),
                                 (replace(atom_d1, stage="D2"), "ordered_slot_identity_mismatch")):
            with self.subTest(issue=issue):
                result = self.reduce(base, candidate, stage="D2")
                self.assertFalse(result.reportable)
                self.assertIn(issue, result.atom_local.issues)
                self.assertEqual(result.criteria, ())
                self.assertIsNone(result.criteria_passed)
        result = self.reduce(replace(base, stage="D2"), atom_d2, stage="D2")
        self.assertFalse(result.reportable)
        self.assertIn("state_or_stage_identity_mismatch", result.base.issues)
        self.assertTrue(result.atom_local.reportable)

    def test_d2_rejects_d1_seed_or_request_and_terminal_drift(self):
        unused, base = self.capture()
        unused, atom = self.capture("ATOM_D2", ATOM_ID, successful=True, stage="D2")
        first = atom.reservations[0]
        seed = screen.reduced_decode_seeds("D1", master=MASTER)[0]
        request = replace(first.custody.request, seed=seed)
        native = dict(first.custody.native_records[0], request=request)
        capture = replace(first.custody, request=request, native_records=(native,))
        rows = ((replace(first, seed=seed), "reservation_seed_mismatch"),
                (replace(first, custody=capture), "request_seed_mismatch"))
        for row, issue in rows:
            with self.subTest(issue=issue):
                tampered = replace(atom, reservations=(row,) + atom.reservations[1:])
                result = self.reduce(base, tampered, stage="D2")
                self.assertFalse(result.reportable)
                self.assertIn(issue, result.atom_local.issues)
        drifted = replace(atom, chain_runs=())
        result = self.reduce(base, drifted, stage="D2")
        self.assertFalse(result.reportable)
        self.assertIn("driver_run_join_mismatch", result.atom_local.issues)

    def rewrite(self, directory, mutate):
        previous = None
        for path in sorted(directory.glob("event-*.json")):
            document = json.loads(path.read_text())
            mutate(document)
            document["previous_sha256"] = previous
            raw = checkpoint._json_bytes(document)
            path.write_bytes(raw)
            previous = sha256(raw).hexdigest()
        marker_path = directory / "COMPLETE"
        marker = json.loads(marker_path.read_text())
        marker["last_sha256"] = previous
        marker_path.write_bytes(checkpoint._json_bytes(marker))

    def test_base_and_atom_replay_feed_existing_scorer_without_changing_files(self):
        base_dir, baseline = self.capture(actor_offset=5)
        atom_dir, fitted = self.capture("ATOM", ATOM_ID, successful=True)
        before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        base = self.replay(base_dir, count_context=lambda prefix: len(prefix) + 7)
        atom = self.replay(atom_dir, ATOM_ID)
        self.assertEqual(base.chain_runs, baseline.chain_runs)
        self.assertEqual(atom.probe_runs, fitted.probe_runs)
        self.assertEqual([call.actor_call_index for call in base.calls],
                         [call.actor_call_index for call in baseline.calls])
        self.assertTrue(any(row.disposition == "UNUSED" for row in base.reservations))
        for run in (base, atom):
            for row in run.reservations:
                if row.custody is not None:
                    self.assertIs(row.driver_record.request, row.custody.request)
                    self.assertIs(row.custody.native_records[0]["generation"], row.custody.generation)
        with patch.object(scoring, "score_chain", wraps=scoring.score_chain) as scorer:
            result = reducer.reduce_base_d1(base=base, atom_local=atom,
                base_state_id=BASE_ID, atom_local_state_id=ATOM_ID, master=MASTER,
                chains=self.held.chains, interventions=self.held.interventions, canaries=self.held.canaries)
        self.assertTrue(result.reportable, (result.base.issues, result.atom_local.issues))
        self.assertTrue(result.criteria_passed)
        self.assertEqual(scorer.call_count, 16)
        self.assertFalse(result.native_authorized)
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_malformed_length_outputs_are_retained_not_retried(self):
        directory, original = self.capture(malformed=True)
        run = self.replay(directory)
        self.assertEqual(len(run.calls), len(original.calls))
        self.assertEqual(run.chain_runs, original.chain_runs)
        self.assertTrue(all(call.generation.truncated for call in run.calls))

    def test_wrong_identity_master_and_context_rejected(self):
        directory, unused = self.capture()
        with self.assertRaisesRegex(ValueError, "state_or_stage_identity_mismatch"):
            self.replay(directory, "foreign-BASE")
        with self.assertRaisesRegex(ValueError, "replay_ledger_mismatch"):
            replay.replay_state(directory, state_id=BASE_ID, master=b"wrong", held=self.held)
        for counter in (lambda prefix: 0, lambda prefix: True):
            with self.subTest(counter=counter), self.assertRaisesRegex(ValueError, "context_count_mismatch"):
                self.replay(directory, count_context=counter)

    def test_wrong_held_public_prefix_rejected(self):
        directory, unused = self.capture()
        altered = SimpleNamespace(chains=self.held.chains, interventions=self.held.interventions,
            canaries=(replace(self.held.canaries[0], user_text="foreign prompt"),) + self.held.canaries[1:])
        with self.assertRaisesRegex(ValueError, "captured_public_prefix_mismatch"):
            replay.replay_state(directory, state_id=BASE_ID, master=MASTER, held=altered)

    def test_incomplete_corrupt_and_aborted_trees_rejected(self):
        directory, unused = self.capture()
        marker = (directory / "COMPLETE").read_bytes()
        (directory / "COMPLETE").unlink()
        with self.assertRaises(FileNotFoundError):
            self.replay(directory)
        (directory / "COMPLETE").write_bytes(marker)
        (directory / "event-0002.json").write_text("{}")
        with self.assertRaises(ValueError):
            self.replay(directory)
        aborted, unused = self.capture("aborted", abort=True)
        with self.assertRaisesRegex(ValueError, "failed_or_incomplete_run"):
            self.replay(aborted)

    def test_native_generation_mismatch_rejected_even_with_valid_hashes(self):
        def mutate(event, payload):
            if event == "CALL_CAPTURED":
                payload.native_records[0]["generation"] = rollout.Generation("foreign", 1, 1, False, "stop")
            return payload

        directory, unused = self.capture(mutate=mutate)
        with self.assertRaisesRegex(ValueError, "native_capture_join_mismatch"):
            self.replay(directory)

    def test_terminal_driver_tampering_rejected_even_with_valid_hashes(self):
        def mutate(event, payload):
            if event == "SCREEN_FINISHED":
                return replace(payload, chain_runs=())
            return payload

        directory, unused = self.capture(mutate=mutate)
        with self.assertRaisesRegex(ValueError, "replay_ledger_mismatch:SCREEN_FINISHED"):
            self.replay(directory)

    def test_opaque_tensor_sidecar_is_hashed_but_never_deserialized(self):
        directory, unused = self.capture()
        name = "event-0002-tensor-0000.pt"
        raw = b"synthetic opaque sidecar; not a serialized tensor"
        (directory / name).write_bytes(raw)

        def mutate(document):
            if document["index"] == 2:
                fields = custody._record(document["payload"], runtime.CallCustody)
                native = custody._tuple(fields["native_records"])[0]
                native[1].append([["str", "native_output"], ["tensor", dict(
                    name=name, size_bytes=len(raw), sha256=sha256(raw).hexdigest(),
                    shape=[1], dtype="torch.int64")]])

        self.rewrite(directory, mutate)
        original_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            if name.split(".")[0] in ("torch", "pickle", "transformers"):
                raise AssertionError("model or deserialization import forbidden")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=guarded_import):
            run = self.replay(directory)
        self.assertNotIn("native_output", run.calls[0].native_records[0])
        (directory / name).write_bytes(b"x" * len(raw))
        with self.assertRaisesRegex(ValueError, "tensor_integrity_mismatch"):
            self.replay(directory)

    def test_extra_missing_and_reordered_events_rejected(self):
        directory, unused = self.capture()
        extra = directory / "unexpected.json"
        extra.write_text("{}")
        with self.assertRaisesRegex(ValueError, "unexpected_or_missing_receipt_files"):
            self.replay(directory)
        extra.unlink()
        first, second = directory / "event-0001.json", directory / "event-0002.json"
        reserved, captured = first.read_bytes(), second.read_bytes()
        first.write_bytes(captured)
        second.write_bytes(reserved)
        with self.assertRaisesRegex(ValueError, "event_order_or_hash_mismatch"):
            self.replay(directory)
        first.write_bytes(reserved)
        second.unlink()
        with self.assertRaises(FileNotFoundError):
            self.replay(directory)

    def test_native_raw_mismatch_and_limits_rejected(self):
        def mutate(event, payload):
            if event == "CALL_CAPTURED":
                payload.native_records[0]["raw_bytes"] = b"foreign"
            return payload

        directory, unused = self.capture(mutate=mutate)
        with self.assertRaisesRegex(ValueError, "native_raw_join_mismatch"):
            self.replay(directory)
        with self.assertRaises(ValueError):
            self.replay(directory, limits=custody.ReceiptLimits(event_bytes=100))

    def test_strict_request_caps_and_record_allowlist(self):
        for name, value in (("max_new_tokens", ["bool", True]),
                            ("max_new_tokens", ["int", 1]),
                            ("prefix", ["record", "os.system", []])):
            with self.subTest(value=value):
                directory, unused = self.capture("case-" + str(len(list(self.root.iterdir()))))

                def mutate(document):
                    if document["event"] in ("CALL_RESERVED", "CALL_CAPTURED"):
                        fields = custody._record(document["payload"], runtime.CallCustody)
                        request = fields["request"]
                        for pair in request[2]:
                            if pair[0] == name:
                                pair[1] = value
                        if document["event"] == "CALL_CAPTURED":
                            native = custody._tuple(fields["native_records"])[0]
                            for pair in native[1]:
                                if pair[0] == ["str", "request"]:
                                    pair[1] = request

                self.rewrite(directory, mutate)
                with self.assertRaises(ValueError):
                    self.replay(directory)


if __name__ == "__main__":
    unittest.main()
