"""CPU-only role routing and real RuleGame replay; no native/model evidence."""
import copy
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import test_rulegame_parenting_diagnostic as fixtures
from organism_v6 import born_rulegame_formation as formation
from organism_v6 import model_backend, rulegame_parenting_diagnostic as diagnostic
from organism_v6 import rulegame_action_projection as projection


class RoleBackend(fixtures.ScriptedBackend):
    def __init__(self, binding, **kwargs):
        super().__init__(binding["role_identities"]["wake"], **kwargs)
        self.binding = copy.deepcopy(binding)
        self.verifications = 0

    def verify(self):
        self.verifications += 1

    def identity(self, role):
        return copy.deepcopy(self.binding["role_identities"][role])

    def generate(self, request):
        identity = self.identity(request["role"])
        return dict(response=super().generate(request), loader_identity=identity,
                    loader_identity_sha256=diagnostic.value_hash(identity),
                    lora_request=formation._route(self.binding, request["role"]))


class BornFormationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.model = self.root / "model"
        self.adapter = self.root / "AUTH"
        self.model.mkdir()
        self.adapter.mkdir()
        (self.model / "config.json").write_text('{"model_type":"qwen2"}')
        (self.model / "weights.fixture").write_bytes(b"CPU model fixture only")
        (self.adapter / "adapter_config.json").write_text('{"r":8,"lora_alpha":16}')
        (self.adapter / "adapter_model.safetensors").write_bytes(b"CPU adapter fixture only")
        self.pin = dict(schema=formation.BIRTH_PIN_SCHEMA, status="COMPLETE", birth_arm="AUTH",
                        birth_plan_sha256="a" * 64, completion_receipt_sha256="b" * 64,
                        child_identity=model_backend.configured_generation_identity(str(self.model), str(self.adapter)),
                        model_files=diagnostic.model_hashes(self.model), origin=formation.ORIGIN,
                        model_origin=formation.MODEL_ORIGIN)
        self.binding = formation.make_binding(self.pin, expected_birth_pin_sha256=diagnostic.value_hash(self.pin))
        self.binding_hash = diagnostic.value_hash(self.binding)
        self.cutoff = 1000

    def capture(self, backend=None, **kwargs):
        backend = backend or RoleBackend(self.binding, **kwargs)
        result = formation.capture_formation(backend, self.binding, expected_binding_sha256=self.binding_hash,
                                            cutoff=self.cutoff, clock=lambda: 1)
        return result, backend

    def replay(self, capture):
        return formation.replay_formation(capture, self.binding, expected_binding_sha256=self.binding_hash, cutoff=self.cutoff)

    def reseal(self, row):
        row["envelope_sha256"] = diagnostic.value_hash(row["envelope"])
        row["prompt_sha256"] = diagnostic.value_hash(row["request"]["prompt"])

    def native(self):
        tokenizer = fixtures.Tokenizer()
        engine = Mock()
        def lora(name, number, path):
            return SimpleNamespace(lora_name=name, lora_int_id=number, lora_path=path)
        child = self.binding["role_identities"]["wake"]
        loaded = SimpleNamespace(tok=tokenizer, llm=engine, adapter_path=child["adapter_input"],
                                 _LoRARequest=Mock(side_effect=lora),
                                 generation_identity=lambda: copy.deepcopy(child))
        with patch.object(model_backend, "MODEL", str(self.model)), patch.object(diagnostic, "NativeBackend",
                return_value=SimpleNamespace(backend=loaded)) as constructor:
            backend = formation.NativeRoleBackend(self.binding, expected_binding_sha256=self.binding_hash, allow_gpu=True)
        constructor.assert_called_once_with(str(self.model), child["adapter_input"])
        if child["adapter_input"] is None:
            loaded._LoRARequest.assert_not_called()
        else:
            loaded._LoRARequest.assert_called_once_with("born_child", 1, child["adapter_input"])
        return backend, engine, tokenizer

    def output(self, engine, tokenizer, request, text="unchanged raw  \n", **kwargs):
        rendered = tokenizer.apply_chat_template([{"content": request["prompt"]}])
        native = SimpleNamespace(text=text, token_ids=tokenizer.encode(text), finish_reason="stop", stop_reason=None)
        for field, value in kwargs.items():
            setattr(native, field, value)
        engine.generate.return_value = [SimpleNamespace(outputs=[native], prompt_token_ids=tokenizer.encode(rendered))]

    def test_complete_capture_real_replay_all_sixty_calls_and_role_event_joins(self):
        capture, backend = self.capture()
        checked = self.replay(capture)
        self.assertTrue(checked["ok"])
        self.assertEqual(checked["calls"], 60)
        self.assertEqual(checked["roles"], {"wake": 40, "record": 12, "parent": 4, "restate": 4})
        self.assertEqual(backend.verifications, 2)
        self.assertEqual(len(capture["result"]["interactions"]), 4)
        self.assertEqual(capture["result"]["main_audit_contract"], diagnostic.main_audit_contract("interaction_v3"))
        self.assertFalse(capture["result"]["semantic_no_answer_certification"])
        for row in capture["calls"]:
            role = row["request"]["role"]
            self.assertEqual(row["identity"], row["envelope"]["loader_identity"])
            self.assertEqual(row["identity"]["adapter_input"], None if role == "parent" else str(self.adapter))
        for event in capture["events"]:
            if event["kind"] == "record":
                record = capture["calls"][int(event["call_id"])]
                wake = capture["calls"][int(event["source_call_id"])]
                self.assertEqual(event["text"], record["envelope"]["response"]["text"])
                self.assertIn(wake["envelope"]["response"]["text"], record["request"]["prompt"])

    def test_requests_results_and_events_equal_existing_interaction_v3(self):
        capture, _ = self.capture()
        backend = fixtures.ScriptedBackend(self.pin["child_identity"])
        calls = diagnostic.Calls(self.root / "legacy_calls", backend, "formation", backend.identity(), "interaction_v3")
        events = diagnostic.Events()
        expected = diagnostic.run_formation(calls, events)
        self.assertEqual([row["request"] for row in capture["calls"]], backend.requests)
        self.assertEqual(capture["result"], expected)
        self.assertEqual(capture["events"], events.rows)

    def test_teacher_fixed_off_across_birth_treatments(self):
        other = self.root / "DERANGED"
        other.mkdir()
        (other / "adapter_config.json").write_bytes((self.adapter / "adapter_config.json").read_bytes())
        (other / "adapter_model.safetensors").write_bytes(b"different CPU birth adapter")
        pin = dict(self.pin, birth_arm="DERANGED", child_identity=model_backend.configured_generation_identity(str(self.model), str(other)))
        binding = formation.make_binding(pin, expected_birth_pin_sha256=diagnostic.value_hash(pin))
        self.assertEqual(binding["role_identities"]["parent"], self.binding["role_identities"]["parent"])
        self.assertNotEqual(binding["role_identities"]["wake"], self.binding["role_identities"]["wake"])
        captured = formation.capture_formation(RoleBackend(binding), binding,
            expected_binding_sha256=diagnostic.value_hash(binding), cutoff=self.cutoff, clock=lambda: 1)
        self.assertEqual(captured["result"]["calls"], 60)

    def test_public_prompt_visibility_no_birth_or_sealed_scores(self):
        capture, _ = self.capture()
        for row in capture["calls"]:
            request = row["request"]
            for forbidden in (str(self.adapter), self.pin["birth_plan_sha256"], "completion_receipt_sha256", "birth_arm"):
                self.assertNotIn(forbidden, request["prompt"])
            if request["role"] == "parent":
                self.assertTrue(request["eid"].endswith("/pre"))
                self.assertNotIn("Temporary parent restatement", request["prompt"])
                self.assertIn("quiz score:", request["prompt"])
                for task in diagnostic.schedule()["evaluation"]:
                    self.assertNotIn(task, request["prompt"])
            if request["role"] == "record":
                self.assertTrue(request["prompt"].endswith(diagnostic.RECORD + "\n" + diagnostic.RELATION_DEFINITION))
        pin = dict(self.pin, birth_dev_score="SECRET")
        with self.assertRaisesRegex(ValueError, "fields"):
            formation.make_binding(pin, expected_birth_pin_sha256=diagnostic.value_hash(pin))

    def test_unrestricted_child_reflection_and_invalid_raw_records_retained(self):
        capture, _ = self.capture(bad_records=("A",))
        self.assertTrue(self.replay(capture)["ok"])
        records = [event for event in capture["events"] if event["kind"] == "record" and event["arm"] == "A"]
        self.assertEqual(len(records), 6)
        self.assertTrue(all(not event["eligible"] and event["text"] == "not a faithful JSON record" for event in records))
        self.assertEqual(capture["result"]["calls"], 60)
        self.assertIn("spontaneous child reflection is not parent leakage", capture["result"]["main_audit_contract"]["child_criterion"])

    def test_invalid_tasks_retained_without_replacements(self):
        backend = RoleBackend(self.binding)
        original = backend.generate
        def invalid(request):
            envelope = original(request)
            if request["role"] == "wake":
                envelope["response"]["text"] = "unparseable raw child output  \n"
                envelope["response"]["output_token_ids"] = backend.tokenizer.encode(envelope["response"]["text"])
            return envelope
        backend.generate = invalid
        capture, _ = self.capture(backend)
        self.assertTrue(self.replay(capture)["ok"])
        self.assertEqual(capture["result"]["calls"], 16)
        self.assertEqual(len(capture["result"]["tasks"]), 8)
        self.assertTrue(all(task["terminal"] == "protocol_invalid" for task in capture["result"]["tasks"]))

    def test_birth_completion_pin_and_source_mismatch_rejected(self):
        for field, value in (("status", "PARTIAL"), ("schema", "other"), ("birth_arm", "P"),
                             ("completion_receipt_sha256", ""), ("origin", "CLEAN"), ("model_files", {})):
            pin = dict(self.pin, **{field: value})
            with self.subTest(field=field), self.assertRaises(ValueError):
                formation.make_binding(pin, expected_birth_pin_sha256=diagnostic.value_hash(pin))
        with self.assertRaisesRegex(ValueError, "birth pin hash"):
            formation.make_binding(self.pin, expected_birth_pin_sha256="0" * 64)
        for field in ("sources", "protocol", "role_identities"):
            binding = copy.deepcopy(self.binding)
            if field == "sources":
                binding[field]["rulegame.py"] = "0" * 64
            elif field == "protocol":
                binding[field] = "interaction_v2"
            else:
                binding[field]["parent"] = binding[field]["wake"]
            with self.subTest(field=field), self.assertRaises(ValueError):
                formation.RoleCalls(RoleBackend(binding), binding, expected_binding_sha256=diagnostic.value_hash(binding), cutoff=100)

    def test_arbitrary_child_or_parent_identity_rejected_before_generation(self):
        for role in ("wake", "parent"):
            backend = RoleBackend(self.binding)
            backend.binding["role_identities"][role]["adapter_input"] = "/arbitrary/adapter"
            backend.generate = Mock()
            calls = formation.RoleCalls(backend, self.binding, expected_binding_sha256=self.binding_hash, cutoff=100, clock=lambda: 1)
            with self.subTest(role=role), self.assertRaisesRegex(ValueError, "identity"):
                calls.ask(role, "P", diagnostic.task_id(0, "pre"), 1, "task")
            backend.generate.assert_not_called()

    def test_false_actual_loader_or_lora_envelope_rejected_with_partial(self):
        for field in ("loader_identity", "loader_identity_sha256", "lora_request"):
            backend = RoleBackend(self.binding)
            original = backend.generate
            def wrong(request):
                envelope = original(request)
                envelope[field] = None
                return envelope
            backend.generate = wrong
            with self.subTest(field=field), self.assertRaises(formation.FormationFailure) as raised:
                self.capture(backend)
            self.assertEqual(len(raised.exception.partial["calls"]), 1)
            self.assertIsNone(raised.exception.partial["result"])
            self.assertEqual(raised.exception.partial["status"], "FAILED_PARTIAL")

    def test_cutoff_before_call_and_after_generation_and_no_continue(self):
        for clock in (lambda: 1000, Mock(side_effect=[1, 1000])):
            backend = RoleBackend(self.binding)
            calls = formation.RoleCalls(backend, self.binding, expected_binding_sha256=self.binding_hash, cutoff=1000, clock=clock)
            with self.assertRaisesRegex(ValueError, "cutoff"):
                calls.ask("wake", "P", diagnostic.task_id(0, "pre"), 1, "task")
            with self.assertRaisesRegex(ValueError, "cannot continue"):
                calls.ask("wake", "P", diagnostic.task_id(0, "pre"), 1, "task")
        with self.assertRaisesRegex(ValueError, "finite"):
            formation.RoleCalls(backend, self.binding, expected_binding_sha256=self.binding_hash, cutoff=float("nan"))

    def test_all_role_budgets_and_native_output_token_caps(self):
        backend = RoleBackend(self.binding)
        for role, limit in diagnostic.LIMITS["formation"].items():
            calls = formation.RoleCalls(backend, self.binding, expected_binding_sha256=self.binding_hash, cutoff=100, clock=lambda: 1)
            calls.counts[role] = limit
            with self.subTest(role=role), self.assertRaisesRegex(ValueError, "budget"):
                calls.ask(role, "A", diagnostic.task_id(0, "pre"), 1, "task")
        backend.generate = Mock(return_value=dict(response=dict(text="x", prompt_token_ids=[1], output_token_ids=[2] * 401,
            rendered_prompt="task"), loader_identity=self.pin["child_identity"],
            loader_identity_sha256=diagnostic.value_hash(self.pin["child_identity"]), lora_request=formation._route(self.binding, "wake")))
        with self.assertRaisesRegex(formation.FormationFailure, "cap"):
            self.capture(backend)

    def test_replay_rejects_resealed_prompt_seed_role_version_and_events(self):
        capture, _ = self.capture()
        mutations = [lambda item: item["calls"][0]["request"].update(prompt="forged context"),
                     lambda item: item["calls"][0]["request"].update(seed=99),
                     lambda item: item["calls"][0]["request"].update(role="parent"),
                     lambda item: item["calls"][0]["request"].update(protocol="interaction_v2"),
                     lambda item: item.update(protocol="interaction_v2"),
                     lambda item: item["events"][0].update(outcome="forged world"),
                     lambda item: item.update(cutoff=2000)]
        for mutation in mutations:
            changed = copy.deepcopy(capture)
            mutation(changed)
            self.reseal(changed["calls"][0])
            with self.assertRaises(ValueError):
                self.replay(changed)

    def test_replay_rejects_resealed_loader_and_raw_hash_tampering(self):
        capture, _ = self.capture()
        for field in ("identity", "loader_identity", "lora_request", "raw_hash"):
            changed = copy.deepcopy(capture)
            row = next(row for row in changed["calls"] if row["request"]["role"] == "parent")
            if field == "identity":
                row["identity"] = copy.deepcopy(self.pin["child_identity"])
                row["identity_sha256"] = diagnostic.value_hash(row["identity"])
            elif field == "loader_identity":
                row["envelope"][field] = copy.deepcopy(self.pin["child_identity"])
                row["envelope"]["loader_identity_sha256"] = diagnostic.value_hash(row["envelope"][field])
            elif field == "lora_request":
                row["envelope"][field] = formation._route(self.binding, "wake")
            else:
                row["envelope"]["response"]["text"] += "tamper"
            if field != "raw_hash":
                self.reseal(row)
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.replay(changed)

    def test_replay_rejects_missing_extra_ordered_or_partial_calls(self):
        capture, _ = self.capture()
        for operation in ("missing", "extra", "order", "partial"):
            changed = copy.deepcopy(capture)
            if operation == "missing":
                changed["calls"].pop()
            elif operation == "extra":
                changed["calls"].append(copy.deepcopy(changed["calls"][-1]))
            elif operation == "order":
                changed["calls"][0]["ended"] = 2
            else:
                changed["status"] = "FAILED_PARTIAL"
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                self.replay(changed)

    def test_native_construction_requires_opt_in_and_exact_files(self):
        with patch.object(diagnostic, "NativeBackend") as load:
            with self.assertRaisesRegex(ValueError, "allow_gpu"):
                formation.NativeRoleBackend(self.binding, expected_binding_sha256=self.binding_hash)
            load.assert_not_called()
        (self.adapter / "adapter_model.safetensors").write_bytes(b"dirty adapter")
        with patch.object(model_backend, "MODEL", str(self.model)), patch.object(diagnostic, "NativeBackend") as load:
            with self.assertRaisesRegex(ValueError, "adapter files"):
                formation.NativeRoleBackend(self.binding, expected_binding_sha256=self.binding_hash, allow_gpu=True)
            load.assert_not_called()

    def test_real_existing_backend_constructors_enable_one_lora_engine(self):
        tokenizer = fixtures.Tokenizer()
        engine = Mock()
        engine.get_tokenizer.return_value = tokenizer
        llm = Mock(return_value=engine)
        lora = Mock(side_effect=lambda name, number, path: SimpleNamespace(
            lora_name=name, lora_int_id=number, lora_path=path))
        modules = {"vllm": SimpleNamespace(LLM=llm, SamplingParams=Mock()),
                   "vllm.lora.request": SimpleNamespace(LoRARequest=lora)}
        with patch.object(model_backend, "MODEL", str(self.model)), patch.dict(sys.modules, modules):
            backend = formation.NativeRoleBackend(self.binding, expected_binding_sha256=self.binding_hash, allow_gpu=True)
            for role in ("wake", "parent", "restate", "record"):
                request = formation._request(0, role, "A", diagnostic.task_id(0, "pre"), 1, "task")
                self.output(engine, tokenizer, request)
                backend.generate(request)
                self.assertIs(engine.generate.call_args.kwargs["lora_request"], None if role == "parent" else backend.child_lora)
        llm.assert_called_once_with(model=str(self.model), max_model_len=16384, gpu_memory_utilization=.85,
                                   enforce_eager=True, enable_lora=True, max_lora_rank=32)
        lora.assert_called_once_with("born_child", 1, str(self.adapter))

    def test_generation_exception_and_post_call_identity_change_retain_raw_partial(self):
        backend = RoleBackend(self.binding)
        backend.generate = Mock(side_effect=RuntimeError("mock worker failed"))
        with self.assertRaisesRegex(formation.FormationFailure, "worker failed") as raised:
            self.capture(backend)
        self.assertEqual(len(raised.exception.partial["calls"]), 1)
        self.assertNotIn("envelope", raised.exception.partial["calls"][0])
        backend = RoleBackend(self.binding)
        original = backend.generate
        def changed(request):
            envelope = original(request)
            backend.binding["role_identities"]["wake"]["adapter_input"] = "/changed"
            return envelope
        backend.generate = changed
        with self.assertRaisesRegex(formation.FormationFailure, "during call") as raised:
            self.capture(backend)
        self.assertEqual(raised.exception.partial["calls"][0]["envelope"]["response"]["text"], "PREDICT: T\nACT: TRY 0,0,0")
        self.assertIsNone(raised.exception.partial["result"])

    def test_native_one_engine_explicit_parent_none_exact_child_lora_all_roles(self):
        backend, engine, tokenizer = self.native()
        with patch.dict(sys.modules, {"vllm": SimpleNamespace(SamplingParams=Mock(return_value="params"))}):
            for role in ("wake", "parent", "restate", "parent", "record", "wake"):
                request = formation._request(0, role, "P", diagnostic.task_id(0, "pre"), 1, "task")
                self.output(engine, tokenizer, request)
                envelope = backend.generate(request)
                self.assertEqual(envelope["response"]["text"], "unchanged raw  \n")
                self.assertIs(engine.generate.call_args.kwargs["lora_request"], None if role == "parent" else backend.child_lora)
                self.assertEqual(envelope["loader_identity"], self.binding["role_identities"][role])
                self.assertEqual(envelope["loader_identity_sha256"], diagnostic.value_hash(envelope["loader_identity"]))
        self.assertEqual(backend.backend.adapter_path, str(self.adapter))
        backend.backend._LoRARequest.assert_called_once()

    def test_native_version_tokenization_cardinality_and_context_limits_fail_closed(self):
        backend, engine, tokenizer = self.native()
        request = formation._request(0, "wake", "P", diagnostic.task_id(0, "pre"), 1, "task")
        with patch.dict(sys.modules, {"vllm": SimpleNamespace(SamplingParams=Mock())}):
            with self.assertRaisesRegex(ValueError, "version"):
                backend.generate(dict(request, protocol="interaction_v2"))
            engine.generate.assert_not_called()
            with self.assertRaisesRegex(ValueError, "model limit"):
                backend.generate(dict(request, prompt="x" * diagnostic.MAX_MODEL_LEN))
            self.output(engine, tokenizer, request, token_ids=[1])
            with self.assertRaisesRegex(ValueError, "output token"):
                backend.generate(request)
            self.output(engine, tokenizer, request)
            engine.generate.return_value[0].prompt_token_ids = [1]
            with self.assertRaisesRegex(ValueError, "input token"):
                backend.generate(request)
            engine.generate.return_value = []
            with self.assertRaisesRegex(ValueError, "cardinality"):
                backend.generate(request)

    def test_native_stop_receipt_preserves_raw_response_not_imagined_outcome(self):
        backend, engine, tokenizer = self.native()
        request = formation._request(0, "wake", "P", diagnostic.task_id(0, "pre"), 1, "task")
        raw = "PREDICT: F\nTRY: 0,0,0"
        self.output(engine, tokenizer, request, text=raw, token_ids=tokenizer.encode(raw + "\n[OUTCOME]"), stop_reason="\n[OUTCOME]")
        sampling = Mock(return_value="params")
        with patch.dict(sys.modules, {"vllm": SimpleNamespace(SamplingParams=sampling)}):
            envelope = backend.generate(request)
        self.assertEqual(envelope["response"]["text"], raw)
        self.assertEqual(envelope["response"]["output_token_ids"], tokenizer.encode(raw + "\n[OUTCOME]"))
        self.assertEqual(sampling.call_args.kwargs, dict(max_tokens=400, temperature=.7, seed=request["seed"],
                         stop=["\n[OUTCOME]"], include_stop_str_in_output=False))

    def test_native_detects_base_adapter_or_lora_mutation(self):
        backend, _, _ = self.native()
        backend.child_lora.lora_path = "/wrong"
        with self.assertRaisesRegex(ValueError, "LoRA"):
            backend.verify()
        backend.child_lora.lora_path = str(self.adapter)
        (self.model / "weights.fixture").write_bytes(b"dirty base")
        with self.assertRaisesRegex(ValueError, "base files"):
            backend.verify()
        (self.adapter / "adapter_model.safetensors").write_bytes(b"dirty adapter")
        with self.assertRaisesRegex(ValueError, "adapter files"):
            backend.identity("parent")

    def use_projection(self, mode="AUTH"):
        self.binding = formation.make_binding(self.pin, expected_birth_pin_sha256=diagnostic.value_hash(self.pin),
                                              interface=projection.INTERFACE, child_mode=mode)
        self.binding_hash = diagnostic.value_hash(self.binding)

    def projection_backend(self, text_at_tick):
        backend = RoleBackend(self.binding)
        generate = backend.generate
        def generate_projection(request):
            envelope = generate(request)
            if request["role"] == "wake" and request["tick"] in text_at_tick:
                text = text_at_tick[request["tick"]]
                envelope["response"]["text"] = text
                envelope["response"]["output_token_ids"] = backend.tokenizer.encode(text)
            return envelope
        backend.generate = generate_projection
        return backend

    def test_projection_binding_explicit_opt_in_and_original_default_schema(self):
        self.assertEqual(set(self.binding), {"schema", "protocol", "birth", "role_identities", "sources"})
        self.assertEqual(self.binding["schema"], formation.SCHEMA)
        self.assertNotIn("rulegame_action_projection.py", self.binding["sources"])
        with self.assertRaisesRegex(ValueError, "explicit projection"):
            formation.make_binding(self.pin, expected_birth_pin_sha256=diagnostic.value_hash(self.pin), child_mode="OFF")
        for interface, mode in (("other", "AUTH"), (projection.INTERFACE, None), (projection.INTERFACE, "DERANGED")):
            with self.assertRaises(ValueError):
                formation.make_binding(self.pin, expected_birth_pin_sha256=diagnostic.value_hash(self.pin), interface=interface, child_mode=mode)
        other = dict(self.pin, birth_arm="DERANGED")
        with self.assertRaisesRegex(ValueError, "genuine completed AUTH"):
            formation.make_binding(other, expected_birth_pin_sha256=diagnostic.value_hash(other), interface=projection.INTERFACE, child_mode="OFF")
        self.use_projection()
        self.assertEqual(self.binding["schema"], formation.PROJECTION_SCHEMA)
        self.assertEqual(self.binding["sources"]["rulegame_action_projection.py"], diagnostic.digest(projection.__file__))
        self.assertEqual(self.binding["birth"], self.pin)

    def test_projection_auth_off_same_requests_and_complete_replays(self):
        captures = []
        for mode in ("AUTH", "OFF"):
            self.use_projection(mode)
            capture, backend = self.capture()
            self.assertTrue(self.replay(capture)["ok"])
            self.assertEqual(capture["result"]["calls"], 60)
            self.assertEqual(capture["result"]["interface"], projection.INTERFACE)
            self.assertEqual({task["eid"] for task in capture["result"]["tasks"]}, set(projection.schedule()["formation"]))
            for row in capture["calls"]:
                role = row["request"]["role"]
                expected = None if mode == "OFF" or role == "parent" else str(self.adapter)
                self.assertEqual(row["identity"]["adapter_input"], expected)
                self.assertEqual(row["envelope"]["lora_request"], None if expected is None else dict(name="born_child", id=1, path=expected))
            captures.append(capture)
        self.assertEqual([row["request"] for row in captures[0]["calls"]], [row["request"] for row in captures[1]["calls"]])
        with self.assertRaisesRegex(ValueError, "binding mismatch"):
            self.replay(captures[0])

    def test_projection_recovery_raw_budget_execution_and_record_joins(self):
        self.use_projection()
        raw = "ACT: TRY 3,6,9\nACT: TRY 1,3,5"
        capture, backend = self.capture(self.projection_backend({1: raw}))
        self.assertTrue(self.replay(capture)["ok"])
        self.assertEqual(capture["result"]["roles"], dict(wake=40, record=8, parent=4, restate=4))
        for row in capture["calls"]:
            if row["request"]["role"] == "wake":
                self.assertEqual(row["request"]["max_tokens"], 400)
                self.assertIn(row["request"]["tick"], range(1, 6))
                if row["request"]["tick"] == 2:
                    self.assertIn(raw, row["request"]["prompt"])
                    self.assertIn("[ONE ACTION PROJECTION]", row["request"]["prompt"])
        invalid_ids = {row["call_id"] for row in capture["events"] if row["kind"] == "protocol_invalid"}
        executions = [row for row in capture["events"] if row["kind"] == "execution"]
        self.assertFalse(invalid_ids & {row["call_id"] for row in executions})
        self.assertEqual(sum(row["projection_of"] in invalid_ids for row in executions), 8)
        for arm in diagnostic.ARMS:
            self.assertEqual(capture["result"]["interface_metrics"][arm]["projection_recovery"], dict(numerator=4, denominator=4))

    def test_projection_second_invalid_closes_tasks_with_no_world_or_records(self):
        self.use_projection("OFF")
        with patch.object(diagnostic.RuleGame, "evaluate", side_effect=AssertionError("no world dispatch")):
            capture, backend = self.capture(self.projection_backend({1: "COMPARE", 2: "COMPARE:COMPARE"}))
            self.assertTrue(self.replay(capture)["ok"])
        self.assertEqual(capture["result"]["calls"], 24)
        self.assertEqual(capture["result"]["roles"], dict(wake=16, parent=4, restate=4))
        self.assertTrue(all(task["terminal"] == "protocol_invalid" and task["wake_slots_used"] == 2 for task in capture["result"]["tasks"]))
        self.assertFalse(any(row["kind"] in ("execution", "record") for row in capture["events"]))

    def test_projection_parent_visibility_and_no_recap_certification_or_restatement_filter(self):
        self.use_projection()
        backend = self.projection_backend({1: "COMPARE", 2: "COMPARE"})
        original = backend.generate
        def misleading(request):
            envelope = original(request)
            if request["role"] in ("parent", "restate"):
                text = "You executed both proposed TRY actions." if request["role"] == "parent" else "COMPARE:COMPARE:MATCH"
                envelope["response"]["text"] = text
                envelope["response"]["output_token_ids"] = backend.tokenizer.encode(text)
            return envelope
        backend.generate = misleading
        capture, backend = self.capture(backend)
        self.assertTrue(self.replay(capture)["ok"])
        result = capture["result"]
        self.assertFalse(result["semantic_no_answer_certification"])
        self.assertFalse(result["parent_recaps_verified"])
        self.assertTrue(result["parent_semantic_audit_required"])
        for row in capture["calls"]:
            request = row["request"]
            if request["role"] == "parent":
                self.assertIn("UNEXECUTED_PROPOSAL", request["prompt"])
                self.assertIn("NO ACTION OR WORLD RESULT", request["prompt"])
                self.assertNotIn("[OUTCOME] the box", request["prompt"])
                self.assertIsNone(row["envelope"]["lora_request"])
            if request["role"] == "wake" and "/apply" in request["eid"]:
                self.assertIn("Temporary parent restatement:\nCOMPARE:COMPARE:MATCH", request["prompt"])
        self.assertTrue(all(item["parent"] == "You executed both proposed TRY actions." for item in result["interactions"]))

    def test_projection_replay_rejects_forged_execution_and_modified_raw_proposal(self):
        self.use_projection()
        capture, backend = self.capture(self.projection_backend({1: "COMPARE"}))
        forged = copy.deepcopy(capture)
        executed = next(copy.deepcopy(row) for row in forged["events"] if row["kind"] == "execution")
        executed["call_id"] = "0000"
        forged["events"].insert(0, executed)
        with self.assertRaisesRegex(ValueError, "provenance mismatch"):
            self.replay(forged)
        changed = copy.deepcopy(capture)
        row = changed["calls"][0]
        row["envelope"]["response"]["text"] = "ALTERED COMPARE"
        row["envelope"]["response"]["output_token_ids"] = backend.tokenizer.encode("ALTERED COMPARE")
        self.reseal(row)
        with self.assertRaisesRegex(ValueError, "source request"):
            self.replay(changed)
        changed = copy.deepcopy(capture)
        changed["calls"][1]["request"]["tick"] = 1
        self.reseal(changed["calls"][1])
        with self.assertRaisesRegex(ValueError, "source request"):
            self.replay(changed)

    def test_projection_source_schedule_route_and_raw_identity_mismatch_rejected(self):
        self.use_projection()
        for field, value in (("wake_slots", 6), ("child_mode", "OFF"), ("task_schedule", diagnostic.schedule()),
                             ("sources", dict(self.binding["sources"], **{"rulegame_action_projection.py": "0"*64}))):
            binding = dict(self.binding, **{field: value})
            with self.subTest(field=field), self.assertRaises(ValueError):
                formation.RoleCalls(RoleBackend(binding), binding, expected_binding_sha256=diagnostic.value_hash(binding), cutoff=100)
        calls = formation.RoleCalls(RoleBackend(self.binding), self.binding, expected_binding_sha256=self.binding_hash, cutoff=100, clock=lambda: 1)
        with self.assertRaisesRegex(ValueError, "development source"):
            calls.ask("wake", "P", diagnostic.task_id(0, "pre"), 1, "not a fresh source")
        backend = self.projection_backend({1: "COMPARE"})
        generate = backend.generate
        def wrong_route(request):
            envelope = generate(request)
            if request["role"] == "wake" and request["tick"] == 2:
                envelope["lora_request"] = None
            return envelope
        backend.generate = wrong_route
        with self.assertRaisesRegex(formation.FormationFailure, "LoRA request") as failed:
            self.capture(backend)
        self.assertEqual(len(failed.exception.partial["calls"]), 2)
        self.assertFalse(any(row["kind"] == "execution" for row in failed.exception.partial["events"]))

    def test_projection_native_off_has_no_adapter_request_or_engine_switch(self):
        self.use_projection("OFF")
        backend, engine, tokenizer = self.native()
        self.assertIsNone(backend.child_lora)
        self.assertIsNone(backend.backend.adapter_path)
        with patch.dict(sys.modules, {"vllm": SimpleNamespace(SamplingParams=Mock())}):
            for role in ("wake", "parent", "restate", "record", "wake"):
                request = formation._request(0, role, "P", projection.task_id(0, "pre"), 2, "projection public state")
                self.output(engine, tokenizer, request)
                envelope = backend.generate(request)
                self.assertIsNone(engine.generate.call_args.kwargs["lora_request"])
                self.assertIsNone(envelope["loader_identity"]["adapter_input"])
                self.assertIsNone(envelope["lora_request"])
        backend.backend._LoRARequest.assert_not_called()
        backend.child_lora = SimpleNamespace(lora_name="fake", lora_int_id=1, lora_path="/fake")
        with self.assertRaisesRegex(ValueError, "synthetic"):
            backend.verify()

    def test_projection_native_auth_exact_lora_and_missing_handle_rejected_before_call(self):
        self.use_projection()
        backend, engine, tokenizer = self.native()
        request = formation._request(0, "wake", "P", projection.task_id(0, "pre"), 2, "projection public state")
        with patch.dict(sys.modules, {"vllm": SimpleNamespace(SamplingParams=Mock())}):
            self.output(engine, tokenizer, request)
            envelope = backend.generate(request)
            self.assertEqual(envelope["lora_request"], dict(name="born_child", id=1, path=str(self.adapter)))
            engine.generate.reset_mock()
            backend.child_lora = None
            with self.assertRaisesRegex(ValueError, "route mismatch"):
                backend.generate(request)
            engine.generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
