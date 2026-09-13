import copy
import hashlib
from pathlib import Path
import random
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from gpu import astra_additive_native_parity_probe as probe


TRAINER = '''
def _warm_initialize(model, cfg, warm):
    random.random()
    return model, {"initialized": True}

def _run_training(model, cfg, opt, events):
    random.seed(cfg.seed)
    model, receipt = _warm_initialize(model, cfg, None)
    for index in range(2):
        t = {"input_ids": [1, 2], "labels": [-100, 2]}
        out = model(**t)
        loss = out.loss
        (loss / cfg.grad_accum).backward()
        events.append("after_backward_body")
        opt.step()
    model.save_pretrained("forbidden")
'''

ADDITIVE = '''
def backward_components(model, memory_tensors, replay_tensors=None):
    losses = []
    for tensors in (memory_tensors,) if replay_tensors is None else (memory_tensors, replay_tensors):
        loss = model(**tensors).loss
        loss.backward()
        losses.append(loss.item())
    return losses

def run_training(model, cfg, opt, events):
    random.seed(cfg.seed)
    model, receipt = _warm_initialize(model, cfg, None)
    for index in range(2):
        backward_components(model, {"input_ids": [1, 2], "labels": [-100, 2]})
        opt.step()
    model.save_pretrained("forbidden")
'''


class Loss:
    def __init__(self, events, error=None):
        self.events, self.error = events, error

    def __truediv__(self, divisor):
        self.events.append(("divide", divisor))
        return self

    def backward(self):
        self.events.append("backward")
        random.random()
        if self.error:
            raise self.error

    def item(self):
        return 1.25


class Model:
    def __init__(self, events, forward_error=None, backward_error=None):
        self.events, self.forward_error, self.backward_error = events, forward_error, backward_error

    def __call__(self, **inputs):
        self.events.append("forward")
        random.random()
        if self.forward_error:
            raise self.forward_error
        return types.SimpleNamespace(loss=Loss(self.events, self.backward_error))

    def save_pretrained(self, path):
        self.events.append("save")


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.trainer = self.root/"trainer.py"
        self.additive = self.root/"additive.py"
        self.trainer.write_text(TRAINER)
        self.additive.write_text(ADDITIVE)
        self.locations = probe.anchors(self.trainer, self.additive)
        self.events = []
        self.observations = []
        self.cfg = types.SimpleNamespace(seed=0, grad_accum=1)
        optimizer_globals = {"__name__": "torch.optim.fixture", "events": self.events}
        exec(compile('def step():\n    events.append("step")\n', str(self.root/"optimizer.py"), "exec"), optimizer_globals)
        self.optimizer = types.SimpleNamespace(step=optimizer_globals["step"])
        self.model = Model(self.events)
        old_globals = {"__name__": "fixture_old", "random": random}
        exec(compile(TRAINER, str(self.trainer), "exec"), old_globals)
        new_globals = {"__name__": "fixture_new", "random": random, "_warm_initialize": old_globals["_warm_initialize"]}
        exec(compile(ADDITIVE, str(self.additive), "exec"), new_globals)
        self.functions = {"OLD": old_globals["_run_training"], "NEW": new_globals["run_training"]}
        state = random.getstate()
        self.addCleanup(random.setstate, state)

    def observe(self, phase, frame, value):
        self.observations.append((phase, random.getstate()))

    def invoke(self, path, observer=None):
        return probe.intercept(lambda: self.functions[path](self.model, self.cfg, self.optimizer, self.events),
                               self.locations, path, observer or self.observe)

    def test_old_first_backward_never_steps_or_saves(self):
        result = self.invoke("OLD")
        self.assertEqual(self.events, ["forward", ("divide", 1), "backward"])
        self.assertEqual(result.phases, list(probe.PHASES))
        self.assertIsNone(sys.gettrace())

    def test_new_first_backward_never_steps_or_saves(self):
        result = self.invoke("NEW")
        self.assertEqual(self.events, ["forward", "backward"])
        self.assertEqual(result.phases, list(probe.PHASES))

    def test_natural_rng_preserved_without_equalization(self):
        self.invoke("OLD")
        observed = dict(self.observations)
        natural = random.Random(0)
        self.assertEqual(observed["before_init"], natural.getstate())
        natural.random()
        self.assertEqual(observed["after_init"], natural.getstate())
        self.assertEqual(observed["before_forward"], natural.getstate())
        natural.random()
        self.assertEqual(observed["after_forward"], natural.getstate())
        self.assertEqual(observed["before_backward"], natural.getstate())
        natural.random()
        self.assertEqual(observed["after_backward"], natural.getstate())
        self.assertEqual(random.getstate(), natural.getstate())

    def test_nested_forward_during_backward_not_extra_phase(self):
        def backward():
            self.events.append("backward")
            self.model(input_ids=[3], labels=[3])
        with patch.object(Loss, "backward", lambda instance: backward()):
            result = self.invoke("NEW")
        self.assertEqual(self.events, ["forward", "backward", "forward"])
        self.assertEqual(result.phases, list(probe.PHASES))

    def test_forward_or_backward_failure_not_captured(self):
        for path in ("OLD", "NEW"):
            for operation in ("forward", "backward"):
                with self.subTest(path=path, operation=operation):
                    self.model = Model(self.events, **{operation+"_error": RuntimeError("fixture")})
                    with self.assertRaisesRegex(ValueError, "frozen operation failed"):
                        self.invoke(path)
                    self.assertIsNone(sys.gettrace())
                    self.assertNotIn("step", self.events)

    def test_observer_error_propagates_and_restores_trace(self):
        def broken(phase, frame, value):
            raise RuntimeError("observer failed")
        with self.assertRaisesRegex(RuntimeError, "observer failed"):
            self.invoke("OLD", broken)
        self.assertIsNone(sys.gettrace())
        self.assertEqual(self.events, [])

    def test_existing_trace_not_replaced(self):
        def existing(frame, event, value):
            return None
        sys.settrace(existing)
        try:
            with self.assertRaisesRegex(ValueError, "existing tracer"):
                self.invoke("OLD")
            self.assertIs(sys.gettrace(), existing)
        finally:
            sys.settrace(None)

    def test_optimizer_step_and_save_trapped_before_body(self):
        for action in (self.optimizer.step, lambda: self.model.save_pretrained("unused")):
            with self.assertRaises(probe.ForbiddenMutation):
                probe.intercept(action, self.locations, "OLD", self.observe)
            self.assertIsNone(sys.gettrace())
        self.assertEqual(self.events, [])

    def test_return_without_first_backward_rejected(self):
        with self.assertRaisesRegex(ValueError, "without zero-step"):
            probe.intercept(lambda: None, self.locations, "OLD", self.observe)

    def test_anchor_changes_and_multiline_rejected(self):
        for replacement in ("out = model.forward(**t)", "out = model(\n            **t)", "out = model(**t)\n        out = model(**t)"):
            self.trainer.write_text(TRAINER.replace("out = model(**t)", replacement))
            with self.assertRaisesRegex(ValueError, "trace seam"):
                probe.anchors(self.trainer, self.additive)

    def test_worker_without_authorization_never_reads_or_imports(self):
        with patch.object(probe, "read") as read, patch.object(probe, "load_module") as loader:
            with self.assertRaisesRegex(ValueError, "allow-native"):
                probe.worker("absent", "absent", "OLD")
            read.assert_not_called()
            loader.assert_not_called()

    def test_scalar_tensor_hash_reshapes_before_byte_view(self):
        events = []
        class Scalar:
            shape, dtype, device = (), "float32", "cpu"

            def detach(self):
                return self

            def contiguous(self):
                return self

            def reshape(self, *shape):
                events.append(("reshape", shape))
                return self

            def view(self, dtype):
                self_test.assertEqual(events, [("reshape", (-1,))])
                return self

            def cpu(self):
                return self

            def numpy(self):
                return self

            def tobytes(self):
                return b"\x00\x00\x80?"
        self_test = self
        result = probe.tensor_record(Scalar(), types.SimpleNamespace(uint8="uint8"))
        self.assertEqual(result["shape"], [])
        self.assertEqual(result["sha256"], hashlib.sha256(b"\x00\x00\x80?").hexdigest())

    def test_observer_rejects_rng_consumption_and_failed_init(self):
        observer = probe.NativeObserver(None, self.root, {})
        with patch.object(probe, "rng_record", side_effect=[{"state": 1}, {"state": 2}]):
            with self.assertRaisesRegex(ValueError, "observer consumed RNG"):
                observer("before_init", None, None)
        self.assertFalse((self.root/"before_init.json").exists())
        with patch.object(probe, "rng_record", return_value={}):
            with self.assertRaisesRegex(ValueError, "warm initializer"):
                observer("after_init", None, None)

    def test_strict_json_and_write_once(self):
        path = self.root/"strict.json"
        for content in ('{"key": 1, "key": 2}', '{"key": NaN}', '{"key": 1e999}', '{"key": Infinity}'):
            path.write_text(content)
            with self.assertRaises(ValueError):
                probe.read(path)
        target = self.root/"once.json"
        probe.write(target, {"finite": 1})
        before = target.read_bytes()
        with self.assertRaises(FileExistsError):
            probe.write(target, {"finite": 2})
        self.assertEqual(target.read_bytes(), before)

    def input_fixture(self):
        config = dict(seed=0, grad_accum=1, batch_size=1, device="cuda", dtype="bf16", grad_checkpoint=True, max_steps=0)
        old = dict(environment={}, python="native-python", python_sha256="native-pin", model=str(self.root/"base"),
                   model_files={}, chat_template="template", engine={}, params={}, parent={"adapter": str(self.root/"parent")},
                   configs={"EXTRA_MEMORY": config})
        new = dict(old, configs={"MEMORY_ONLY": config})
        primary = dict(seed=0, fit_seed=0, epoch_order=[["row0"]], encoding=[dict(row_id="row0", input_ids=[1, 2], labels=[-100, 2])])
        warm = {key: {} for key in ("initialized_state", "source_state", "trainable_names", "optimizer_defaults", "parent_files")}
        fit = dict(config=config, warm_start=warm)
        objects = dict(old_plan=old, new_plan=new, old_training=primary, paired=dict(seed=0, fit_seed=0, primary=primary),
                       old_manifest=fit, new_manifest=fit)
        inputs = {}
        for name, value in objects.items():
            path = self.root/(name+".json")
            probe.write(path, value)
            inputs[name] = dict(path=str(path), sha256=probe.digest(path))
        reflection = self.root/"reflection.py"
        reflection.write_text("NATIVE_NOT_IMPORTED = True\n")
        for name, path in (("trainer", self.trainer), ("additive", self.additive), ("reflection", reflection)):
            inputs[name] = dict(path=str(path), sha256=probe.digest(path))
        return inputs

    def test_pinned_config_and_seed0_first_row_binding(self):
        inputs = self.input_fixture()
        pins = {key: value["sha256"] for key, value in inputs.items()}
        with patch.dict(probe.PINS, pins, clear=True):
            bound = probe.bind_inputs(inputs)
            self.assertEqual(bound["first"]["row_id"], "row0")
            changed = dict(inputs)
            changed.pop("old_manifest")
            with self.assertRaisesRegex(ValueError, "closed input"):
                probe.bind_inputs(changed)
            Path(inputs["old_plan"]["path"]).write_text("{}")
            with self.assertRaisesRegex(ValueError, "file bytes differ"):
                probe.bind_inputs(inputs)

    def test_changed_config_rejected_even_if_repinned(self):
        inputs = self.input_fixture()
        path = Path(inputs["new_plan"]["path"])
        plan = probe.read(path)
        plan["configs"]["MEMORY_ONLY"]["grad_checkpoint"] = False
        path.write_bytes(probe.encoded(plan))
        inputs["new_plan"]["sha256"] = probe.digest(path)
        with patch.dict(probe.PINS, {key: value["sha256"] for key, value in inputs.items()}, clear=True):
            with self.assertRaisesRegex(ValueError, "configuration differs"):
                probe.bind_inputs(inputs)

    def test_prepare_cpu_only_and_no_overwrite(self):
        inputs = self.input_fixture()
        with patch.dict(probe.PINS, {key: value["sha256"] for key, value in inputs.items()}, clear=True):
            bound = probe.bind_inputs(inputs)
        out = self.root/"fresh"
        with patch.object(probe, "bind_inputs", return_value=bound), patch.object(probe, "load_module") as loader:
            result = probe.prepare(self.root/"old", self.root/"new", self.trainer, self.additive,
                                   self.root/"reflection.py", out, "GPU-fixture-not-real", "0"*36)
            self.assertIs(result["native_authorized"], False)
            self.assertEqual(probe.read(out/"plan.json")["optimizer_steps"], 0)
            loader.assert_not_called()
            with self.assertRaisesRegex(ValueError, "fresh scratch"):
                probe.prepare(self.root/"old", self.root/"new", self.trainer, self.additive,
                              self.root/"reflection.py", out, "GPU-fixture-not-real", "0"*36)

    def test_native_observer_first_tokens_and_optimizer_seams(self):
        class Tokens:
            def __init__(self, values):
                self.values = values

            def tolist(self):
                return self.values
        model = types.SimpleNamespace(parameters=lambda: [])
        optimizer = types.SimpleNamespace(state={}, defaults={"lr": 0.01})
        tensors = {key: Tokens(value) for key, value in dict(input_ids=[[1, 2]], labels=[[-100, 2]], attention_mask=[[1, 1]]).items()}
        bound = dict(first=dict(input_ids=[1, 2], labels=[-100, 2]), old_fit={"warm_start": {"optimizer_defaults": {"lr": 0.01}}})
        observer = probe.NativeObserver(None, self.root, bound)
        observer.model = model
        parent = types.SimpleNamespace(f_locals={"optimizer": optimizer})
        frame = types.SimpleNamespace(f_locals={"model": model, "tensors": tensors}, f_back=parent)
        with patch.object(probe, "rng_record", return_value={}), patch.object(probe, "tensor_record", return_value={}), patch.object(probe, "model_settings", return_value={}):
            observer("before_forward", frame, None)
            self.assertEqual(probe.read(self.root/"before_forward.json")["optimizer"]["state_entries"], 0)
            tensors["labels"] = Tokens([[1, 2]])
            with self.assertRaisesRegex(ValueError, "tokens/masks differ"):
                observer("before_forward", frame, None)
            tensors["labels"] = Tokens([[-100, 2]])
            tensors["position_ids"] = Tokens([[0, 1]])
            with self.assertRaisesRegex(ValueError, "input keys differ"):
                observer("before_forward", frame, None)

    def test_after_backward_requires_finite_gradients_and_no_parameter_change(self):
        for failure in (None, "missing", "nonfinite", "changed", "base_gradient"):
            with self.subTest(failure=failure):
                root = self.root/str(failure)
                root.mkdir()
                observer = probe.NativeObserver(None, root, {})
                observer.initial = {"lora_weight": {"sha256": "initial"}}
                trainable = types.SimpleNamespace(requires_grad=True, grad=None if failure == "missing" else "gradient")
                base = types.SimpleNamespace(requires_grad=False, grad="unexpected" if failure == "base_gradient" else None)
                observer.model = types.SimpleNamespace(named_parameters=lambda: [("lora_weight", trainable), ("base", base)])
                observer.torch = types.SimpleNamespace(isfinite=lambda value: types.SimpleNamespace(all=lambda: failure != "nonfinite"))
                loss = types.SimpleNamespace(detach=lambda: types.SimpleNamespace(item=lambda: 1.0))
                frame = types.SimpleNamespace(f_locals={"loss": loss})
                def hashes(tensor, torch):
                    return {"sha256": "changed" if failure == "changed" else "initial"} if tensor is trainable else {"sha256": "fixture"}
                with patch.object(probe, "rng_record", return_value={}), patch.object(probe, "tensor_record", side_effect=hashes):
                    if failure is None:
                        observer("after_backward", frame, None)
                        self.assertIs(probe.read(root/"after_backward.json")["trainable_parameters_unchanged"], True)
                    else:
                        with self.assertRaises(ValueError):
                            observer("after_backward", frame, None)
                        self.assertFalse((root/"after_backward.json").exists())

    def fixture_receipts(self):
        receipts = []
        for index, path in enumerate(("OLD", "NEW")):
            root = self.root/path
            root.mkdir()
            observations = {}
            for phase in probe.PHASES:
                record = dict(phase=phase, rng={"cpu": phase}, observer_rng_unchanged=True)
                if phase == "after_init":
                    record["initial_tensors"] = {"lora_a": {"sha256": "initial"}}
                if phase == "before_forward":
                    record.update(inputs={"tokens": "same"}, settings={"checkpoint": True}, optimizer={"defaults": "same"})
                if phase in ("after_forward", "before_backward", "after_backward"):
                    record["loss"] = 1.0+index
                if phase == "after_backward":
                    record.update(gradients={"lora_a": {"sha256": str(index)}}, trainable_parameters_unchanged=True, base_gradients_absent=True)
                probe.write(root/(phase+".json"), record)
                observations[phase] = dict(path=str(root/(phase+".json")), sha256=probe.digest(root/(phase+".json")))
            probe.write(root/"environment.json", {"cuda": "fixture"})
            receipt = dict(schema=probe.SCHEMA, path=path, pid=100+index, status="FIRST_BACKWARD_CAPTURED_ZERO_UPDATES",
                plan_sha256="plan", probe_sha256=probe.digest(probe.SELF), first_row_id="row", phases=list(probe.PHASES),
                parent_unchanged=True, optimizer_steps=0, adapter_saves=0, readouts=0, observations=observations,
                environment=dict(path=str(root/"environment.json"), sha256=probe.digest(root/"environment.json")))
            probe.write(root/"receipt.json", receipt)
            receipts.append(root/"receipt.json")
        return receipts

    def compare(self, receipts):
        return probe.compare(str(receipts[0]), probe.digest(receipts[0]), str(receipts[1]), probe.digest(receipts[1]), self.root/"comparison.json")

    def test_compare_reports_difference_without_automatic_pass(self):
        receipts = self.fixture_receipts()
        self.compare(receipts)
        result = probe.read(self.root/"comparison.json")
        self.assertTrue(result["initial_tensors_equal"])
        self.assertTrue(result["inputs_equal"])
        self.assertTrue(result["environment_equal"])
        self.assertFalse(result["gradients_equal"])
        self.assertFalse(result["automatic_pass"])
        self.assertEqual(result["losses"], {"OLD": 1.0, "NEW": 2.0})
        with self.assertRaises(FileExistsError):
            self.compare(receipts)

    def test_compare_rejects_partial_mutated_or_same_process(self):
        receipts = self.fixture_receipts()
        original = probe.read(receipts[1])
        for field, value in (("optimizer_steps", False), ("adapter_saves", 1), ("pid", 100), ("pid", True),
                             ("plan_sha256", "other"), ("phases", list(probe.PHASES[:-1])), ("parent_unchanged", False)):
            changed = dict(original, **{field: value})
            receipts[1].write_bytes(probe.encoded(changed))
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.compare(receipts)
        self.assertFalse((self.root/"comparison.json").exists())

    def test_compare_phase_splicing_and_observer_mutation_rejected(self):
        receipts = self.fixture_receipts()
        original = probe.read(receipts[1])
        changed = copy.deepcopy(original)
        changed["observations"]["before_init"] = changed["observations"]["after_init"]
        receipts[1].write_bytes(probe.encoded(changed))
        with self.assertRaisesRegex(ValueError, "phase/RNG"):
            self.compare(receipts)
        path = Path(original["observations"]["before_init"]["path"])
        record = probe.read(path)
        record["observer_rng_unchanged"] = False
        path.write_bytes(probe.encoded(record))
        original["observations"]["before_init"]["sha256"] = probe.digest(path)
        receipts[1].write_bytes(probe.encoded(original))
        with self.assertRaisesRegex(ValueError, "phase/RNG"):
            self.compare(receipts)

    def test_compare_changed_observation_bytes_rejected(self):
        receipts = self.fixture_receipts()
        record = probe.read(receipts[0])
        Path(record["observations"]["after_backward"]["path"]).write_text("{}")
        with self.assertRaisesRegex(ValueError, "file bytes differ"):
            self.compare(receipts)


if __name__ == "__main__":
    unittest.main()
