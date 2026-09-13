"""CPU-only actual-corpus fixtures; scripted receipts are not native evidence."""
from collections import Counter
import copy
import importlib.util
import json
from pathlib import Path
import re
import sys
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zlib


sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("repair_core_test", "/tmp/astra_own_replay_repair_core_20260913.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
ARCHIVE = Path("/data/home/rohing/dream-state/gpu_artifacts_local/actual_record_memory_20260913_attempt1/evidence.tar")
ARCHIVE_PIN = "3ed6579e7e885139d78faf3457eb3bec254215d36b533558ef22f8199ff6a003"


class Tokenizer:
    chat_template = "CPU_FIXTURE_NOT_NATIVE"
    eos_token, eos_token_id, pad_token_id = "<|im_end|>", 1, 0

    def encode(self, text, add_special_tokens=False):
        pieces = re.findall(r"<\|im_start\|>|<\|im_end\|>|[A-Za-z_]+|[0-9]+|[^\w\s]|\s", text)
        assert "".join(pieces) == text
        return [1 if piece == self.eos_token else 2 if piece == "<|im_start|>" else zlib.crc32(piece.encode()) + 3 for piece in pieces]

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False):
        messages = copy.deepcopy(messages)
        if messages[0]["role"] != "system":
            messages.insert(0, dict(role="system", content="You are a helpful assistant."))
        text = "".join(f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n" for message in messages)
        if add_generation_prompt:
            text += "<|im_start|>assistant\n"
        return self.encode(text) if tokenize else text


class RepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capture = core.load_capture(core.CAPTURE_RUNTIME_PATH)
        cls.memory = cls.capture.lifecycle()
        def load(path, pin, name):
            return cls.memory.load(dict(path=path, sha256=pin), name, pin)
        cls.replay = load("/tmp/astra_own_source_replay_core_20260913.py", cls.capture.CORE_PIN, "repair_test_replay")
        cls.native = load("/tmp/astra_level1_real_record_run_20260913.py", cls.capture.NATIVE_PIN, "repair_test_native")
        cls.probe = load("/tmp/astra_birth_skill_probe_run_20260913.py", core.PROBE_PIN, "repair_test_probe")
        cls.helper = load("/tmp/astra_level1_skill_run_20260913.py", core.HELPER_PIN, "repair_test_helper")
        cls.trainer = load("/tmp/astra_level1_real_record_source_20260913_attempt1/organism_v6/train_adapter_v3.py", core.TRAINER_PIN, "repair_test_trainer")
        cls.bundles = {str(seed): cls.replay.build(seed) for seed in range(3)}
        _, cls.corpus = cls.replay.dependencies()
        if core.digest(ARCHIVE) != ARCHIVE_PIN:
            raise AssertionError("original actual-memory archive pin differs")
        cls.originals = []
        with tarfile.open(ARCHIVE, "r:") as archive:
            for seed in range(3):
                prefix = f"real_record_memory_seed{seed}_20260913_attempt1/"
                original = {name: json.loads(archive.extractfile(prefix+name+".json").read()) for name in ("plan", "dataset", "capture", "retention")}
                original["parent"] = original["plan"]["parent"]
                cls.originals.append(original)
        cls.raw_responses, cls.admissions = {}, {}
        for key, bundle in cls.bundles.items():
            responses = []
            observations = {row["row_id"]: row for row in bundle["training_observations"]}
            for index, request in enumerate(bundle["requests"]):
                execution = cls.corpus.assess_source(observations[request["row_id"]]["source"])["execution"]
                predicted, observed = execution["predicted"], execution["observed"]
                fields = dict(relation="unavailable" if predicted is None else "matched" if predicted == observed else "mismatched",
                              predicted=predicted, observed=observed, **{"try": execution["values"]})
                raw = " \n" + json.dumps(fields, indent=2) + "\t\n"
                if index >= (24, 12, 0)[int(key)]:
                    raw = "CPU fixture rejected output"
                responses.append(dict(request_id=request["request_id"], input_sha256=request["input_sha256"],
                                      producer_sha256=request["producer_sha256"], raw=raw, finish_reason="stop"))
            cls.raw_responses[key] = responses
            cls.admissions[key] = cls.replay.admit(bundle, responses)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="own_replay_repair_cpu_")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.root, self.out = self.home / "capture", self.home / "collected"
        self.root.mkdir()
        self.out.mkdir()
        self.spec = dict(runner_sha256=core.CAPTURE_RUNTIME_PIN,
            core=dict(path=self.replay.__file__, sha256=self.capture.CORE_PIN),
            native=dict(path=self.native.__file__, sha256=self.capture.NATIVE_PIN),
            public=dict(path=self.probe.__file__, sha256=self.capture.PUBLIC_PIN),
            lifecycle=dict(path=self.memory.__file__, sha256=self.capture.LIFECYCLE_PIN),
            archive=dict(path=self.replay.ARCHIVE, sha256=self.replay.ARCHIVE_PIN), source_root=self.replay.SOURCE_ROOT,
            protocol=dict(path="/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_OWN_SOURCE_REPLAY_CAPTURE_2026-09-13.md", sha256=self.capture.PROTOCOL_PIN),
            gpu_index=6, gpu_uuid="GPU-CPU-NOT-NATIVE", expected_boot_id="0"*36, lease_end=1e10)
        self.reference = dict(self.originals[0]["plan"], chat_template=Tokenizer.chat_template)
        self.runtime = SimpleNamespace(tree=self.tree, validate_response=self.native.validate_response)
        self.bound = dict(memory=self.memory, core=self.replay, runtime=self.runtime, probe=self.probe,
                          bundles=self.bundles, reference=self.reference, parents={})
        self.write(self.root / "spec.json", self.spec)
        inputs = {}
        for key, bundle in self.bundles.items():
            for name, value in ((f"bundle_seed{key}.json", bundle), (f"calls_seed{key}.json", self.capture.make_calls(bundle, Tokenizer(), self.probe))):
                self.write(self.root / name, value)
                inputs[name] = core.digest(self.root / name)
        self.plan = self.capture.expected_plan(self.root, self.spec, core.digest(self.root / "spec.json"), self.bound, inputs)
        self.write(self.root / "plan.json", self.plan)
        self.plan_hash = core.digest(self.root / "plan.json")
        self.write(self.root / "prepare_started.json", dict(spec_sha256=self.plan["spec_sha256"]))
        costs, joins = {}, {}
        for key, bundle in self.bundles.items():
            seed = int(key)
            directory = self.root / "run" / f"seed{key}"
            directory.mkdir(parents=True)
            route = self.capture.route_for(self.plan, seed, self.runtime)
            producer = self.plan["producers"][key]
            self.write(directory / "identity.json", dict(scope=self.capture.SCOPE, seed=seed, producer=producer,
                producer_sha256=bundle["producer_sha256"], lora_request=route, model_files=self.plan["model_files"], engine=self.plan["engine"], params=self.plan["params"]))
            calls = self.memory.read(self.root / f"calls_seed{key}.json")
            names, native_responses, joins[key] = ["identity.json"], [], []
            for call, raw in zip(calls, self.raw_responses[key], strict=True):
                request = dict(call, params=self.plan["params"], lora_request=route)
                response = dict(call["native"], text=raw["raw"], decoded_output=raw["raw"], actual_prompt_token_ids=call["native"]["prompt_token_ids"],
                    output_token_ids=Tokenizer().encode(raw["raw"]), finish_reason=raw["finish_reason"], stop_reason=None, lora_request=route, started=1., ended=1.5)
                for suffix, value in ((".request.json", request), (".response.json", response)):
                    name = call["call_id"] + suffix
                    self.write(directory / name, value)
                    names.append(name)
                native_responses.append(response)
                joins[key].append(dict(request_id=raw["request_id"], call_id=call["call_id"],
                    native_request_sha256=core.digest(directory / (call["call_id"] + ".request.json")),
                    native_response_sha256=core.digest(directory / (call["call_id"] + ".response.json")), core_response_sha256=core.value_hash(raw)))
            costs[key] = dict(calls=24, fits=0, updates=0, teacher_calls=0,
                prompt_tokens=sum(len(response["actual_prompt_token_ids"]) for response in native_responses),
                output_tokens=sum(len(response["output_token_ids"]) for response in native_responses), generation_seconds=12.)
            self.write(directory / "closed.json", dict(costs[key], seed=seed, files={name: core.digest(directory / name) for name in names}, adapter_files_after=producer["adapter_files"]))
            identity = dict(pid=9000+seed, pgid=9000+seed, start_ticks=100+seed)
            command = [self.plan["python"], "-B", str(self.capture.SELF), "worker", "--root", str(self.root), "--plan-sha256", self.plan_hash, "--seed", key, "--allow-gpu"]
            self.write(directory / "launch.json", dict(identity=identity, seed=seed, plan_sha256=self.plan_hash, command=command, started=10.*seed+1))
            self.write(directory / "started.json", dict(seed=seed, plan_sha256=self.plan_hash, pid=identity["pid"], pgid=identity["pgid"], time=10.*seed+2))
            self.write(directory / "released.json", dict(identity=identity, seed=seed, ended=10.*seed+3, elapsed_seconds=2.))
            self.write(self.out / f"seed{key}_admission.json", self.admissions[key])
        inventory = self.capture.validate_completed(self.plan, self.plan_hash, self.bound)
        self.write(self.root / "capture_complete.json", dict(scope=self.capture.SCOPE, plan_sha256=self.plan_hash, stages=inventory,
            calls=72, fits=0, updates=0, teacher_calls=0, admitted=False, elapsed_seconds=30.))
        self.report = dict(scope=self.capture.SCOPE, claim=self.capture.CLAIM, plan_sha256=self.plan_hash,
            completion_sha256=core.digest(self.root / "capture_complete.json"), protocol=self.spec["protocol"],
            source_pins={key: self.spec[key] for key in ("core", "native", "public", "lifecycle", "archive")}, seed_reports={},
            counts={key: self.capture.admission_counts(admission) for key, admission in self.admissions.items()}, native_source_joins=joins,
            costs_per_seed=costs, costs=dict({field: sum(cost[field] for cost in costs.values()) for field in costs["0"]}, controller_seconds=30.),
            native_capture_receipts_checked=True, core_native_identity_verified=False, automatic_pass=False, fit_decision=None)
        self.repin_collection()
        self.write(self.root.with_name(self.root.name + ".collection_claim.json"), dict(plan_sha256=self.plan_hash, out=str(self.out), retry=False))
        self.addCleanup(patch.stopall)
        patch.object(core, "load_capture", return_value=self.capture).start()
        patch.object(self.capture, "bind", return_value=self.bound).start()
        self.no_admit = patch.object(self.replay, "admit", side_effect=AssertionError("build must not recollect/re-admit")).start()
        self.no_collect = patch.object(self.capture, "collect", side_effect=AssertionError("no second collection")).start()

    def write(self, path, value):
        Path(path).write_bytes(core.encoded(value))

    def tree(self, path):
        for bundle in self.bundles.values():
            if str(path) == bundle["producer"]["adapter"]:
                return copy.deepcopy(bundle["producer"]["adapter_files"])
        return {str(entry.relative_to(path)): core.digest(entry) for entry in sorted(Path(path).rglob("*")) if entry.is_file()}

    def repin_collection(self):
        self.report["seed_reports"] = {str(seed): dict(path=f"seed{seed}_admission.json", sha256=core.digest(self.out / f"seed{seed}_admission.json")) for seed in range(3)}
        self.write(self.out / "replay_report.json", self.report)
        self.write(self.out / "collection.json", dict(replay_report_sha256=core.digest(self.out / "replay_report.json"), completion_sha256=self.report["completion_sha256"]))

    def build(self, seed=0, supplied=None, original=None):
        original = self.originals[seed] if original is None else original
        return core.build(original["plan"], original, self.plan, self.report if supplied is None else supplied, seed)

    def encode(self, material, arm="REPLAY", tokenizer=None):
        return core.encode(material, arm, Tokenizer() if tokenizer is None else tokenizer, self.trainer, self.helper, self.probe, material["seed"])

    def test_all_seed_counts_original_order_and_maximum_budget(self):
        for seed, replay_count in enumerate((24, 12, 0)):
            material = self.build(seed)
            self.assertEqual(material["memory_rows"], self.originals[seed]["dataset"]["rows"])
            self.assertEqual(material["counts"]["replay"], replay_count)
            self.assertEqual(material["counts"]["updates_per_arm"], 8*(core.MEMORY_COUNTS[seed]+replay_count) if replay_count else 0)
            self.assertEqual(material["parent"], self.originals[seed]["parent"])
        self.assertEqual(sum(2*8*(count+24) for count in core.MEMORY_COUNTS), 1632)
        self.no_admit.assert_not_called()
        self.no_collect.assert_not_called()

    def test_seed_admission_and_summary_api_equal(self):
        self.assertEqual(self.build(supplied=self.admissions["0"]), self.build())

    def test_distinct_duplicates_exact_cycling_and_raw_roundtrip(self):
        material = self.build()
        memory = material["memory_rows"]
        ids = []
        for arm in core.ARMS:
            rows = material["arms"][arm]["rows"]
            ids.extend(row["row_id"] for row in rows)
            for index, row in enumerate(rows):
                original = (memory[index] if index < len(memory) else material["replay_rows"][index-len(memory)] if arm == "REPLAY" else memory[(index-len(memory)) % len(memory)])
                self.assertEqual(row["raw_target"].encode(), original["raw_target"].encode())
                self.assertEqual(row["source_row_id"], original["row_id"])
                self.assertEqual(row["input_messages"], original["input_messages"])
                self.assertEqual(row["source"], original["source"])
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(json.loads(core.encoded(material)), material)
        self.assertTrue(material["replay_rows"][0]["raw_target"].startswith(" \n"))

    def test_frozen_encoder_masks_eos_orders_dose_and_costs(self):
        material = self.build()
        encodings = [self.encode(material, arm) for arm in core.ARMS]
        for arm, result in zip(core.ARMS, encodings, strict=True):
            self.assertEqual(result, self.encode(material, arm))
            self.assertEqual(result["updates"], 304)
            self.assertEqual(result["rows"], 38)
            self.assertEqual(result["presentations"], 304)
            self.assertEqual(result["padding_tokens"], 0)
            self.assertEqual(Counter(name for order in result["epoch_order"] for name in order), Counter({row["row_id"]: 8 for row in material["arms"][arm]["rows"]}))
            for audit, item, row in zip(result["encoding"], result["items"], material["arms"][arm]["rows"], strict=True):
                labels = audit["labels"]
                self.assertEqual([label for label in labels if label != -100], Tokenizer().encode(row["raw_target"])+[1])
                prefix_count = len(audit["native_prompt"]["prompt_token_ids"])
                self.assertEqual(labels[:prefix_count], [-100]*prefix_count)
                self.assertEqual(labels[-1], -100)
                self.assertEqual(item["spans"][0][0], audit["native_prompt"]["rendered_prompt"])
                self.assertEqual(item["spans"][1][0], row["raw_target"])
                self.assertNotIn("source_proof", audit["full_assistant_text"])
            for field in ("rows", "presentations", "total_tokens", "target_tokens", "context_tokens", "train_tokens_seen", "actual_supervised_tokens", "actual_context_tokens"):
                self.assertEqual(result[field], sum(cost[field] for cost in result["per_kind"].values()))
            self.assertEqual(result["actual_padded_tokens"], result["train_tokens_seen"])
            self.assertEqual(result["encoding_sha256"], core.value_hash({key: value for key, value in result.items() if key != "encoding_sha256"}))
        self.assertEqual(encodings[0]["per_kind"]["memory"]["presentations"], 112)
        self.assertEqual(encodings[1]["per_kind"]["extra_memory"]["presentations"], 192)
        self.assertNotEqual(encodings[0]["total_tokens"], encodings[1]["total_tokens"])
        positions = [[[name.rsplit(":", 1)[1] for name in order] for order in result["epoch_order"]] for result in encodings]
        self.assertEqual(positions[0], positions[1])

    def test_zero_replay_neither_arm_calls_encoder(self):
        material = self.build(2)
        self.assertEqual(material["status"], "REPLAY_UNAVAILABLE")
        for arm in core.ARMS:
            result = core.encode(material, arm, None, None, None, None, 2)
            self.assertEqual(result["items"], [])
            self.assertEqual(result["updates"], 0)
            self.assertEqual(result["train_tokens_seen"], 0)
            self.assertEqual(result["epoch_order"], [])

    def test_memory_raw_prompt_source_and_parent_tamper(self):
        for field in ("raw_target", "input_messages", "source", "source_proof"):
            original = copy.deepcopy(self.originals[0])
            original["dataset"]["rows"][0][field] = "tamper"
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.build(original=original)
        original = copy.deepcopy(self.originals[0])
        original["plan"]["parent"]["adapter"] = "/CPU_DESCENDANT_NOT_ORIGINAL"
        with self.assertRaises(ValueError):
            self.build(original=original)

    def test_saved_teacher_held_source_id_prompt_and_omission_tamper(self):
        for field, value in (("raw_target", "TEACHER_REWRITE"), ("row_id", "held_00"), ("source", {"source_id": "wrong"}),
                             ("input_messages", [{"role": "user", "content": "parent lesson"}]), ("source_proof", {"target_origin": "TEACHER"})):
            admission = copy.deepcopy(self.admissions["0"])
            admission["admitted"][0][field] = value
            self.write(self.out / "seed0_admission.json", admission)
            self.repin_collection()
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.build()
        admission = copy.deepcopy(self.admissions["0"])
        admission["admitted"].pop()
        admission["admitted_count"] -= 1
        self.write(self.out / "seed0_admission.json", admission)
        self.report["counts"]["0"] = self.capture.admission_counts(admission)
        self.repin_collection()
        with self.assertRaises(ValueError):
            self.build()

    def test_native_raw_prompt_adapter_and_release_tamper(self):
        directory = self.root / "run" / "seed0"
        for name, field, value in (("train_00.response.json", "text", "teacher"), ("train_00.request.json", "messages", []),
                                   ("released.json", "identity", dict(pid=99, pgid=99, start_ticks=1))):
            path = directory / name
            original = self.memory.read(path)
            self.write(path, dict(original, **{field: value}))
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.build()
            self.write(path, original)

    def test_collection_failure_claim_and_join_tamper(self):
        self.write(self.out / "collection_failure.json", dict(error="CPU fixture failure"))
        with self.assertRaises(ValueError):
            self.build()
        (self.out / "collection_failure.json").unlink()
        self.report["native_source_joins"]["0"][0]["core_response_sha256"] = "bad"
        self.repin_collection()
        with self.assertRaises(ValueError):
            self.build()

    def test_prepared_inventory_completion_and_once_claim_tamper(self):
        paths = (self.root / "calls_seed0.json", self.root / "capture_complete.json",
                 self.root.with_name(self.root.name + ".collection_claim.json"))
        for path in paths:
            original = self.memory.read(path)
            changed = copy.deepcopy(original)
            if path.name == "calls_seed0.json":
                changed[0]["messages"][0]["content"] = "HELD_OR_TEACHER_PROMPT"
            elif path.name == "capture_complete.json":
                changed["stages"]["0"] = {}
            else:
                changed["retry"] = True
            self.write(path, changed)
            with self.subTest(path=path.name), self.assertRaises(ValueError):
                self.build()
            self.write(path, original)

    def test_source_judge_audit_rejects_rehashed_eligibility_forgery(self):
        admission = copy.deepcopy(self.admissions["1"])
        admission["responses"][-1]["eligible"] = True
        admission["responses"][-1]["errors"] = []
        self.write(self.out / "seed1_admission.json", admission)
        self.repin_collection()
        with self.assertRaises(ValueError):
            self.build(1)

    def test_capture_route_and_producer_tamper(self):
        original = self.plan["producers"]["0"]["adapter"]
        self.plan["producers"]["0"]["adapter"] = "/CPU_WRONG_OR_DESCENDANT_ADAPTER"
        try:
            with self.assertRaises(ValueError):
                self.build()
        finally:
            self.plan["producers"]["0"]["adapter"] = original

    def test_wrong_seed_protocol_and_unknown_arm(self):
        for seed in (True, -1, 3):
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                core.validate_memory(self.originals[0]["plan"], self.originals[0], seed)
        with self.assertRaises(ValueError):
            core.build(self.originals[0]["plan"], self.originals[0], self.plan, self.report, 0, protocol_path=__file__)
        material = self.build()
        with self.assertRaises(ValueError):
            core.encode(material, "LR0", None, None, None, None, 0)
        with self.assertRaises(ValueError):
            core.encode(material, "REPLAY", None, None, None, None, 1)

    def test_material_hash_lineage_and_no_input_mutation(self):
        original_hash = core.value_hash(self.originals)
        report_hash = core.value_hash(self.report)
        material = self.build()
        before = core.value_hash(material)
        self.encode(material)
        self.assertEqual(before, core.value_hash(material))
        self.assertEqual(original_hash, core.value_hash(self.originals))
        self.assertEqual(report_hash, core.value_hash(self.report))
        material["arms"]["REPLAY"]["rows"][0]["raw_target"] = "changed"
        with self.assertRaises(ValueError):
            self.encode(material)
        material["material_sha256"] = core.value_hash({key: value for key, value in material.items() if key != "material_sha256"})
        with self.assertRaises(ValueError):
            self.encode(material)

    def test_encoding_rejects_eos_pad_and_truncation(self):
        material = self.build()
        tokenizer = Tokenizer()
        tokenizer.pad_token_id = tokenizer.eos_token_id
        with self.assertRaises(ValueError):
            self.encode(material, tokenizer=tokenizer)
        class LongTokenizer(Tokenizer):
            def encode(self, text, add_special_tokens=False):
                return [token for token in super().encode(text, add_special_tokens) for repeat in range(1 if token == 1 else 50)]
        with self.assertRaises(ValueError):
            self.encode(material, tokenizer=LongTokenizer())


if __name__ == "__main__":
    unittest.main(verbosity=2)
