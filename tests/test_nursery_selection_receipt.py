"""Synthetic CPU custody fixtures; never model authentication or measured science."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import nursery_selection_receipt as selection
from organism_v6 import run_life_v2
from organism_v6.batch_loop import driver_class_for
from organism_v6.gym_backend import Episode
from organism_v6.model_backend import configured_generation_identity


class CPUGym:
    name = "reasoning_gym"

    def __init__(self, end_token=True, ids=None):
        self.end_token = end_token
        self.ids = ids if ids is not None else ["rg/countdown/1800001", "rg/countdown/1800002"]

    def offers_end_token(self):
        return self.end_token

    def canary_set(self):
        return list(self.ids)

    def birth_prompt(self):
        return "CPU canary fixture: respond with ACT."

    def episode_from_id(self, episode_id, budget):
        return Episode(episode_id, goal="Synthetic answer", metric="fixture only", intro=episode_id)

    def evaluate(self, episode, action):
        return 0.5, "Explicit synthetic fixture outcome, not a measured science result"


class CPUModel:
    def __init__(self, model_input, adapter, outputs):
        self.identity = configured_generation_identity(model_input, adapter)
        self.outputs = outputs
        self.calls = []

    def generation_identity(self):
        return deepcopy(self.identity)

    def batch(self, prompts, **kwargs):
        index = len(self.calls)
        self.calls.append((list(prompts), deepcopy(kwargs)))
        return list(self.outputs[index])


def synthetic_selection(adapter_dir, model_input, previous_sha256):
    """Construct new synthetic acceptance using the actual evaluator, never GPU evidence.

    Existing test DONE bytes are staging completion, not historical acceptance.
    They become CANDIDATE until the actual helper/evaluator publishes custody.
    """
    import uuid

    adapter = Path(adapter_dir)
    done = adapter / "DONE"
    selection._marker(adapter, "DONE")
    selection._adapter_files(adapter)
    done.rename(adapter / "CANDIDATE")
    try:
        gym = CPUGym(end_token=False)
        model = CPUModel(str(model_input), str(adapter), [["ACT: 1", "ACT: 2"]] * 3)
        recorder = selection.SelectionRecorder(
            model, model_input=str(model_input), adapter_dir=str(adapter),
            config=selection.evaluation_config(gym), previous_manifest_sha256=previous_sha256)
        ok, rate = run_life_v2.format_canary(model, gym, selection=recorder)
        binding = recorder.write(adapter.parent / ("synthetic_selection_" + uuid.uuid4().hex), ok=ok, rate=rate)
        selection.verify_selected(binding["selection_path"], expected_selection_sha256=binding["selection_sha256"],
                                  adapter_dir=adapter, previous_manifest_sha256=previous_sha256)
    finally:
        (adapter / "CANDIDATE").rename(done)
    return {key: binding[key] for key in ("selection_path", "selection_sha256")}


class NurserySelectionReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.adapter = self.root / "adapter"
        self.adapter.mkdir()
        (self.adapter / "adapter_config.json").write_text('{"peft_type":"LORA"}')
        (self.adapter / "adapter_model.safetensors").write_bytes(b"SYNTHETIC CPU ADAPTER BYTES")
        (self.adapter / "CANDIDATE").write_text("synthetic trainer completed\n")
        self.model_input = str(self.root / "lineage/birth/model")
        self.previous = "a" * 64
        self.directory = self.root / "canary_selection"
        self.gym = CPUGym()
        self.config = selection.evaluation_config(self.gym)

    def recorder(self, outputs=None, config=None):
        model = CPUModel(self.model_input, str(self.adapter),
                         outputs if outputs is not None else [["ACT: 1", "not parseable"]] * 3)
        recorder = selection.SelectionRecorder(model, model_input=self.model_input,
                                               adapter_dir=str(self.adapter), config=config or self.config,
                                               previous_manifest_sha256=self.previous)
        return recorder, model

    def run_recorded_original(self, recorder, gym=None):
        gym = gym or self.gym
        drivers = []
        active = []
        parent = driver_class_for(gym)
        if not recorder.setup_checked:
            recorder.check_setup(episode_ids=gym.canary_set(), birth_prompt=gym.birth_prompt(),
                                 driver=parent, threshold=recorder.config["threshold"])

        class CapturedDriver(parent):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                drivers.append(self)

        class ObservedModel:
            def batch(self, prompts, seeds=None):
                if recorder.pending is not None:
                    recorder.finish_round(active)
                active[:] = [driver for driver in drivers if not driver.done]
                return recorder.batch(active, prompts, seeds)

        with patch.object(run_life_v2, "driver_class_for", return_value=CapturedDriver), \
                patch("organism_v6.state.time.time", return_value=1000.0):
            result = run_life_v2.format_canary(ObservedModel(), gym, recorder.config["threshold"])
        if recorder.pending is not None:
            recorder.finish_round(active)
        return result

    def publish(self, outputs=None):
        recorder, model = self.recorder(outputs)
        ok, rate = self.run_recorded_original(recorder)
        binding = recorder.write(self.directory, ok=ok, rate=rate)
        return recorder, model, binding

    def verify(self, binding, **overrides):
        arguments = dict(expected_receipt_sha256=binding["receipt_sha256"], adapter_dir=self.adapter,
                         expected_model_input=self.model_input, expected_adapter_input=str(self.adapter),
                         expected_config=self.config, previous_manifest_sha256=self.previous)
        arguments.update(overrides)
        return selection.verify_selection(binding["receipt_path"], **arguments)

    def replace_json(self, path, change):
        path = Path(path)
        data = json.loads(path.read_bytes())
        change(data)
        path.chmod(0o600)
        content = selection._encoded(data)
        path.write_bytes(content)
        return selection._sha(content)

    def test_exact_original_canary_parity_and_trace_custody(self):
        recorder, model, binding = self.publish()
        plain = CPUModel(self.model_input, str(self.adapter), model.outputs)
        with patch("organism_v6.state.time.time", return_value=1000.0):
            actual = run_life_v2.format_canary(plain, self.gym)
        self.assertEqual(actual, (True, 0.5))
        self.assertEqual(plain.calls, model.calls)
        receipt = self.verify(binding)
        self.assertEqual((receipt["parse_ok"], receipt["total"], receipt["rate"]), (3, 6, 0.5))
        self.assertEqual(receipt["candidate"], model.identity)
        trace = json.loads(Path(binding["trace_path"]).read_bytes())
        self.assertEqual(trace["rounds"], recorder.rounds)
        self.assertEqual(trace["rounds"][0]["episode_ids"], self.gym.canary_set())
        self.assertTrue((self.adapter / "CANDIDATE").exists())
        self.assertFalse((self.adapter / "DONE").exists())
        self.assertFalse(any("score" in key for batch in trace["rounds"] for key in batch))
        for name in ("trace.json", "receipt.json"):
            self.assertEqual((self.directory / name).stat().st_mode & 0o777, 0o444)
        before = Path(binding["receipt_path"]).read_bytes()
        with self.assertRaises(selection.SelectionReceiptError):
            recorder.write(self.directory, ok=True, rate=0.5)
        self.assertEqual(Path(binding["receipt_path"]).read_bytes(), before)

    def test_original_regex_early_exit_and_reindexed_seeds(self):
        outputs = [["### ACT: 1\nDONE", "ACT : 1"], ["ACT:\n 1"], ["ACT: \t"]]
        recorder, model = self.recorder(outputs)
        result = self.run_recorded_original(recorder)
        plain = CPUModel(self.model_input, str(self.adapter), outputs)
        with patch("organism_v6.state.time.time", return_value=1000.0):
            self.assertEqual(run_life_v2.format_canary(plain, self.gym), result)
        self.assertEqual(result, (False, 0.25))
        self.assertEqual(model.calls, plain.calls)
        self.assertEqual(recorder.rounds[1]["seeds"], [4242])
        binding = recorder.write(self.directory, ok=False, rate=0.25)
        with self.assertRaisesRegex(selection.SelectionReceiptError, "selection rejected"):
            self.verify(binding)
        self.assertEqual(self.verify(binding, require_acceptance=False)["decision"], "REJECTED_CANARY")

    def test_no_end_token_driver_and_original_zip_denominator(self):
        gym = CPUGym(end_token=False)
        config = selection.evaluation_config(gym)
        outputs = [["ACT: 1\nDONE"], ["bad", "ACT: 1", "ACT: ignored excess"], []]
        recorder, model = self.recorder(outputs, config)
        result = self.run_recorded_original(recorder, gym)
        plain = CPUModel(self.model_input, str(self.adapter), outputs)
        with patch("organism_v6.state.time.time", return_value=1000.0):
            self.assertEqual(run_life_v2.format_canary(plain, gym), result)
        self.assertEqual(model.calls, plain.calls)
        self.assertEqual(result, (True, 2 / 3))
        binding = recorder.write(self.directory, ok=result[0], rate=result[1])
        self.assertEqual(self.verify(binding, expected_config=config)["total"], 3)

    def test_empty_canary_preserves_zero_denominator_semantics(self):
        gym = CPUGym(ids=[])
        config = selection.evaluation_config(gym, threshold=0)
        recorder, model = self.recorder([], config)
        self.assertEqual(self.run_recorded_original(recorder, gym), (True, 0.0))
        self.assertEqual(model.calls, [])
        binding = recorder.write(self.directory, ok=True, rate=0.0)
        self.assertEqual(self.verify(binding, expected_config=config)["total"], 0)

    def test_false_verdict_or_incomplete_evaluation_never_publishes(self):
        recorder, _model = self.recorder()
        with self.assertRaisesRegex(selection.SelectionReceiptError, "setup not recorded"):
            recorder.write(self.directory, ok=True, rate=1.0)
        recorder.check_setup(episode_ids=self.gym.canary_set(), birth_prompt=self.gym.birth_prompt(),
                             driver=driver_class_for(self.gym), threshold=0.5)
        with self.assertRaisesRegex(selection.SelectionReceiptError, "incomplete"):
            recorder.write(self.directory, ok=True, rate=1.0)
        self.run_recorded_original(recorder)
        for ok, rate in ((False, 0.5), (True, 1.0), (1, 0.5), (True, float("nan"))):
            with self.subTest(ok=ok, rate=rate), self.assertRaises(selection.SelectionReceiptError):
                recorder.write(self.directory, ok=ok, rate=rate)
        self.assertFalse(self.directory.exists())

    def test_trace_tampering_and_rebound_false_parseability_reject(self):
        _recorder, _model, binding = self.publish()
        original = Path(binding["trace_path"]).read_bytes()
        original_receipt = Path(binding["receipt_path"]).read_bytes()
        changes = (lambda trace: trace["rounds"][0]["outputs"].__setitem__(0, "tampered"),
                   lambda trace: trace["rounds"][0]["prompts"].__setitem__(0, "tampered"),
                   lambda trace: trace["rounds"][0]["episode_ids"].reverse(),
                   lambda trace: trace["rounds"][0]["seeds"].__setitem__(0, 4243),
                   lambda trace: trace["rounds"][0]["done_after"].__setitem__(0, True),
                   lambda trace: trace["rounds"][0]["parseable"].__setitem__(1, True))
        for change in changes:
            with self.subTest(change=change):
                trace_hash = self.replace_json(binding["trace_path"], change)
                with self.assertRaises(selection.SelectionReceiptError):
                    self.verify(binding)
                rebound = dict(binding, receipt_sha256=self.replace_json(binding["receipt_path"],
                               lambda receipt: receipt.update(trace_sha256=trace_hash)))
                with self.assertRaises(selection.SelectionReceiptError):
                    self.verify(rebound)
                Path(binding["trace_path"]).write_bytes(original)
                Path(binding["receipt_path"]).write_bytes(original_receipt)

    def test_rebound_receipt_verdict_and_eval_config_reject(self):
        _recorder, _model, binding = self.publish()
        original = Path(binding["receipt_path"]).read_bytes()
        changes = (lambda receipt: receipt.update(decision="REJECTED_CANARY"),
                   lambda receipt: receipt.update(rate=1.0),
                   lambda receipt: receipt.update(parse_ok=True),
                   lambda receipt: receipt["config"].update(threshold=0.1),
                   lambda receipt: receipt["config"].update(rounds=1),
                   lambda receipt: receipt["config"].update(evaluator_sha256="b" * 64),
                   lambda receipt: receipt["candidate"].update(model_input="other model"))
        for change in changes:
            with self.subTest(change=change):
                digest = self.replace_json(binding["receipt_path"], change)
                with self.assertRaises(selection.SelectionReceiptError):
                    self.verify(dict(binding, receipt_sha256=digest))
                Path(binding["receipt_path"]).write_bytes(original)
        for config in (dict(self.config, threshold=0.1), dict(self.config, birth_prompt="changed")):
            with self.assertRaisesRegex(selection.SelectionReceiptError, "config mismatch"):
                self.verify(binding, expected_config=config)

    def test_effective_evaluator_setup_must_match_selected_config(self):
        for change in ({"birth_prompt": "changed"}, {"episode_ids": ["other"]}, {"threshold": 0.1}):
            recorder, model = self.recorder()
            setup = dict(episode_ids=self.gym.canary_set(), birth_prompt=self.gym.birth_prompt(),
                         driver=driver_class_for(self.gym), threshold=0.5)
            setup.update(change)
            with self.subTest(change=change), self.assertRaises(selection.SelectionReceiptError):
                recorder.check_setup(**setup)
            self.assertEqual(model.calls, [])

    def test_fully_rehashed_output_cannot_override_external_pin(self):
        _recorder, _model, binding = self.publish()

        def change_trace(trace):
            batch = trace["rounds"][0]
            batch["outputs"][1] = "ACT: replaced"
            batch["output_sha256"][1] = selection._sha(batch["outputs"][1].encode())
            batch["parseable"][1] = True

        trace_hash = self.replace_json(binding["trace_path"], change_trace)
        self.replace_json(binding["receipt_path"], lambda receipt: receipt.update(
            trace_sha256=trace_hash, parse_ok=4, rate=4 / 6))
        with self.assertRaisesRegex(selection.SelectionReceiptError, "external selection receipt pin"):
            self.verify(binding)

    def test_adapter_and_marker_tampering_reject(self):
        _recorder, _model, binding = self.publish()
        for filename in ("adapter_config.json", "adapter_model.safetensors", "CANDIDATE"):
            path = self.adapter / filename
            original = path.read_bytes()
            path.write_bytes(original + b"changed")
            with self.subTest(filename=filename), self.assertRaises(selection.SelectionReceiptError):
                self.verify(binding)
            path.write_bytes(original)
        with self.assertRaises(selection.SelectionReceiptError):
            self.verify(binding, previous_manifest_sha256="b" * 64)
        with self.assertRaises(selection.SelectionReceiptError):
            self.verify(binding, expected_adapter_input="other candidate")

    def test_identity_drift_and_missing_identity_reject_before_publication(self):
        recorder, model = self.recorder()
        model.identity["model_input"] = "wrong model"
        with self.assertRaises(selection.SelectionReceiptError):
            self.run_recorded_original(recorder)
        self.assertEqual(model.calls, [])
        model.identity = configured_generation_identity(self.model_input, str(self.adapter))
        self.run_recorded_original(recorder)
        (self.adapter / "adapter_model.safetensors").write_bytes(b"replacement")
        with self.assertRaises(selection.SelectionReceiptError):
            recorder.write(self.directory, ok=True, rate=0.5)
        self.assertFalse(self.directory.exists())
        with self.assertRaises(selection.SelectionReceiptError):
            selection.SelectionRecorder(SimpleNamespace(), model_input=self.model_input,
                                        adapter_dir=self.adapter, config=self.config,
                                        previous_manifest_sha256=self.previous)

    def test_receipt_commit_failure_preserves_trace_and_blocks_retry(self):
        recorder, _model = self.recorder()
        self.run_recorded_original(recorder)
        write = selection.custody._write

        def interrupt(path, content):
            if path.name == "receipt.json":
                raise OSError("synthetic interruption")
            return write(path, content)

        with patch.object(selection.custody, "_write", side_effect=interrupt):
            with self.assertRaises(selection.SelectionReceiptError):
                recorder.write(self.directory, ok=True, rate=0.5)
        trace = (self.directory / "trace.json").read_bytes()
        self.assertFalse((self.directory / "receipt.json").exists())
        with self.assertRaises(selection.SelectionReceiptError):
            recorder.write(self.directory, ok=True, rate=0.5)
        self.assertEqual((self.directory / "trace.json").read_bytes(), trace)

    def test_selected_intent_is_required_and_bound(self):
        _recorder, _model, binding = self.publish()
        expected = dict(expected_selection_sha256=binding["selection_sha256"], adapter_dir=self.adapter,
                        previous_manifest_sha256=self.previous, expected_model_input=self.model_input,
                        expected_adapter_input=str(self.adapter))
        receipt = selection.verify_selected(binding["selection_path"], **expected)
        self.assertEqual(receipt["decision"], "DONE")
        path = Path(binding["selection_path"])
        self.assertEqual(path.stat().st_mode & 0o777, 0o444)
        self.replace_json(path, lambda selected: selected["config"].update(threshold=0.1))
        with self.assertRaisesRegex(selection.SelectionReceiptError, "intent pin mismatch"):
            selection.verify_selected(path, **expected)

    def test_actual_observer_hook_matches_default_canary(self):
        recorder, model = self.recorder()
        with patch("organism_v6.state.time.time", return_value=1000.0):
            observed = run_life_v2.format_canary(model, self.gym, selection=recorder)
        plain = CPUModel(self.model_input, str(self.adapter), model.outputs)
        with patch("organism_v6.state.time.time", return_value=1000.0):
            self.assertEqual(run_life_v2.format_canary(plain, self.gym), observed)
        self.assertEqual(plain.calls, model.calls)
        binding = recorder.write(self.directory, ok=observed[0], rate=observed[1])
        self.verify(binding)

    def test_receipt_precedes_done_and_verifies_after_snapshot_copy(self):
        import shutil

        _recorder, _model, binding = self.publish()
        (self.adapter / "CANDIDATE").rename(self.adapter / "DONE")
        self.verify(binding, stage="DONE")
        with self.assertRaises(selection.SelectionReceiptError):
            self.recorder()
        snapshot = self.root / "snapshot"
        shutil.copytree(self.adapter, snapshot)
        self.verify(binding, adapter_dir=snapshot, stage="DONE")
        with self.assertRaises(selection.SelectionReceiptError):
            self.verify(binding)

    def test_symlinks_unknown_files_and_duplicate_json_fail_closed(self):
        _recorder, _model, binding = self.publish()
        extra = self.adapter / "unrecorded.bin"
        extra.write_bytes(b"unknown")
        with self.assertRaises(selection.SelectionReceiptError):
            self.verify(binding)
        extra.unlink()
        alias = self.root / "linked_adapter"
        alias.symlink_to(self.adapter, target_is_directory=True)
        with self.assertRaises(selection.SelectionReceiptError):
            self.verify(binding, adapter_dir=alias)
        path = Path(binding["receipt_path"])
        path.chmod(0o600)
        path.write_bytes(b'{"schema":"one","schema":"two"}\n')
        with self.assertRaisesRegex(selection.SelectionReceiptError, "duplicate"):
            self.verify(binding)


if __name__ == "__main__":
    unittest.main()
