"""CPU fixtures only; no native model, tokenizer, GPU query or process launch."""
import copy
from contextlib import contextmanager
import json
from pathlib import Path
import subprocess
import tempfile
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import astra_q0_readout_supplement as supplement
from gpu import astra_pairwise_q0_fulldose as q0
from tests.test_astra_pairwise_q0_fulldose import TokenizerFixture, evidence_fixture, readout_fixture, raw_output, torch


def put(root, relative, value):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(q0.canonical(value))


def seal_original(root):
    for name in ("SEAL.json", "FINALIZED.json"):
        (root / name).unlink(missing_ok=True)
    put(root, "SEAL.json", dict(version=q0.VERSION, evidence_kind=q0.NATIVE_KIND,
                                classification="PENDING_DURABLE_FINALIZATION", files=q0.inventory(root)))
    put(root, "FINALIZED.json", dict(seal_sha256=q0.file_hash(root / "SEAL.json"), evidence_durable_unix=1100., elapsed_seconds=100.))


def build_original(root, prepared, config):
    root.mkdir()
    evidence = evidence_fixture(prepared, TokenizerFixture(), auth=False, deranged=False)
    def binary(value):
        if isinstance(value, dict):
            if set(value) == {"shape", "dtype", "values", "sha256"}:
                return q0.tensor_payload(q0.payload_tensor(value))
            return {key: binary(item) for key, item in value.items()}
        if isinstance(value, list):
            return [binary(item) for item in value]
        return value
    with q0.tensor_store(root, writable=True):
        evidence = binary(evidence)
    diagnostic, _, _ = q0.historical_helpers()
    manifest = dict(version=q0.VERSION, config=config, allocation=prepared["allocation"], recipe=prepared["recipe"],
                    prepared_sha256=q0.digest(prepared), source_pins={"fixture": "NOT_NATIVE"}, inputs={"fixture": True},
                    public_binding=None)
    put(root, "manifest.json", manifest)
    put(root, "prepared.json", prepared)
    put(root, "PREPARED.json", dict(manifest_sha256=q0.file_hash(root / "manifest.json"), prepared_sha256=q0.file_hash(root / "prepared.json")))
    started = dict(started=1000., deadline=11800., controller=dict(pid=50, start_ticks=1))
    put(root, "STARTED.json", started)
    prior = {}
    for index, stage in enumerate(supplement.STAGES):
        arm = None if index == 0 else "OFF" if index == 1 else "P_AUTH" if index <= 5 else "P_DERANGED"
        kind = "audit" if index == 0 else "fit" if index in (2, 6) else "eval"
        snapshot = None if kind != "eval" else 0 if index == 1 else int(stage.rsplit("_", 1)[1])
        ticket = dict(sequence=index, kind=kind, arm=arm, snapshot=snapshot, evidence_kind=q0.NATIVE_KIND,
                      prepared_sha256=q0.digest(prepared), deadline=11800.)
        if kind == "fit":
            ticket["diagnostic_only"] = False
        ticket["ticket_sha256"] = q0.digest(ticket)
        job = dict(ticket=ticket, prior_receipts=dict(prior), manifest_sha256=q0.file_hash(root / "manifest.json"),
                   started_sha256=q0.file_hash(root / "STARTED.json"), deadline=11755.)
        if kind == "audit":
            result = evidence["audit"]
        elif kind == "fit":
            result = next(fit for fit in evidence["fits"] if fit["arm"] == arm)
            for update in q0.SNAPSHOTS:
                path = f"stages/{stage}/snapshots/{update}"
                put(root, path + "/adapter_config.json", {"fixture_only": True, "r": 8})
                put(root, path + "/adapter_model.safetensors", {"NOT_REAL_TENSORS": update})
                result["snapshots"][str(update)] = dict(path=path, adapter_sha256=diagnostic.w0.tree_hash(root / path), lora_sha256=q0.digest([arm, update]))
        else:
            result = evidence["readouts"][arm + "/" + str(snapshot)]
            if arm != "OFF":
                job["adapter"] = next(fit for fit in evidence["fits"] if fit["arm"] == arm)["snapshots"][str(snapshot)]
        put(root, "jobs/" + stage + ".json", job)
        identity = dict(pid=100 + index, start_ticks=10 + index, ppid=50, pgid=100 + index, session=100 + index)
        load = dict(identity=identity, load_id=str(index), allocation=prepared["allocation"], recipe=prepared["recipe"],
                    source_pins=manifest["source_pins"], inputs=manifest["inputs"], adapter=job.get("adapter"),
                    job_sha256=q0.file_hash(root / "jobs" / (stage + ".json")), ticket_sha256=ticket["ticket_sha256"])
        events = []
        def event(name, value):
            path = f"{len(events):04d}_{name}.json"
            put(root, "stages/" + stage + "/events/" + path, value)
            events.append(dict(path=path, sha256=q0.file_hash(root / "stages" / stage / "events" / path)))
        if kind == "fit":
            event("initial", result["initial"])
            event("canary_after", dict(result=result["canary"], delta=result["canary_raw"]["delta"]))
            for step in result["steps"]:
                event("step", step)
            natural = calls = 656
        elif kind == "eval":
            for record in result:
                event("readout", record)
            natural = sum(record["operation"] == "prefix" for record in result)
            calls = natural + sum(len(record["output"]["generated_ids"]) for record in result if record["operation"] == "generate")
        else:
            natural = calls = 128
        done = dict(result=result, load=load, events=events, counters=dict(natural_prefix_forwards=natural, model_forward_calls=calls),
                    finished=1001. + index * 2)
        put(root, "stages/" + stage + "/DONE.json", done)
        put(root, "stages/" + stage + "/LOAD.json", load)
        put(root, "logs/" + stage + ".log", {"CPU_FIXTURE_ONLY": True})
        cleanup = dict(pid=identity["pid"], device=config["gpu_uuid"], owned_group_empty=True, gpu_processes_absent=True,
                       reservation_release_verified=True)
        put(root, "logs/" + stage + ".cleanup.json", cleanup)
        receipt = dict(pid=identity["pid"], process_start=identity["start_ticks"], load_id=load["load_id"], attempts=1,
                       start=1000. + index * 2, finish=1001. + index * 2, status="FINISHED", cleanup="COMPLETE",
                       ticket_sha256=ticket["ticket_sha256"], adapter=job.get("adapter"),
                       done_sha256=q0.file_hash(root / "stages" / stage / "DONE.json"),
                       cleanup_sha256=q0.file_hash(root / "logs" / (stage + ".cleanup.json")),
                       log_sha256=q0.file_hash(root / "logs" / (stage + ".log")))
        put(root, "receipts/" + stage + ".json", receipt)
        prior[stage + ".json"] = q0.file_hash(root / "receipts" / (stage + ".json"))
    ticket = dict(sequence=9, kind="eval", arm=supplement.STATE, snapshot=128, prepared_sha256=q0.digest(prepared),
                  evidence_kind=q0.NATIVE_KIND, deadline=11800.)
    ticket["ticket_sha256"] = q0.digest(ticket)
    job = dict(ticket=ticket, prior_receipts=prior, adapter=evidence["fits"][1]["snapshots"]["128"],
               manifest_sha256=q0.file_hash(root / "manifest.json"), started_sha256=q0.file_hash(root / "STARTED.json"))
    put(root, "jobs/" + supplement.FAILED_STAGE + ".json", job)
    put(root, "stages/" + supplement.FAILED_STAGE + "/CLAIMED.json", dict(identity=dict(pid=109)))
    put(root, "logs/" + supplement.FAILED_STAGE + ".cleanup.json", dict(cleanup, pid=109))
    (root / "logs" / (supplement.FAILED_STAGE + ".log")).write_text("gpu_identity subprocess.TimeoutExpired --query-gpu=uuid,name,driver_version timed out after 15 seconds\n")
    put(root, "FAILED.json", {"fixture_failure": "identity timeout; NOT NATIVE"})
    put(root, "RESOURCE.json", dict(stages=list(supplement.STAGES), gpu_release_verified=True, version=q0.VERSION,
                                   allocation=prepared["allocation"]))
    put(root, "reduction.json", dict(candidate=dict(label="NONREPORTABLE_RUNTIME_ABORT"), scientific_claim=False))
    seal_original(root)
    return manifest


class SupplementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = TokenizerFixture()
        cls.prepared = q0.build_prepared(cls.tokenizer, replica="R1")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.original = self.folder / "old"
        self.config = q0.native_config_template("R1")
        self.config.update(node=q0.hashlib.sha256(b"fixture-node").hexdigest(), environment={"fixture": True},
                           gpu_uuid="GPU-11111111-1111-1111-1111-111111111111", driver_version="580.1",
                           lease_end_unix=20000000000., lease_cutoff_unix=19999970000.,
                           approved_intake="Main-supplement", builder_preflight_reference="CPU-only test")
        self.original_manifest = build_original(self.original, self.prepared, self.config)
        self.custody = self.folder / "custody.json"
        put(self.folder, "custody.json", {"Noether_schema_not_assumed": "CPU_FIXTURE_ONLY"})
        self.custody_sha = q0.file_hash(self.custody)
        self.pins = dict(seal_sha256=q0.file_hash(self.original / "SEAL.json"), finalized_sha256=q0.file_hash(self.original / "FINALIZED.json"))
        self.old_before = q0.inventory(self.original)
        self.out = self.folder / "supplement"

    def admit(self):
        return supplement.admit_original(self.original, self.custody, self.custody_sha, **self.pins)

    def fake_verify(self, root):
        self.assertEqual(Path(root), self.original)
        return self.original_manifest, self.prepared, self.tokenizer

    def prepare(self, joined=False):
        with patch.object(q0, "native_verify", side_effect=self.fake_verify), patch.object(q0, "native_input_pins", return_value={}):
            return supplement.prepare(self.out, self.original, self.custody, self.custody_sha, self.config, joined=joined, **self.pins)

    def test_admission_binds_original_without_writing_it(self):
        admitted = self.admit()
        self.assertEqual(admitted["allocation"], q0.allocation_spec("R1"))
        self.assertEqual(admitted["adapter"]["path"], "stages/06_fit_P_DERANGED/snapshots/128")
        self.assertEqual(q0.inventory(self.original), self.old_before)

    def test_changed_original_or_external_witness_pin_rejected(self):
        with self.assertRaises(q0.IntegrityError):
            supplement.admit_original(self.original, self.custody, "0" * 64, **self.pins)
        put(self.original, "extra.json", {})
        with self.assertRaises(q0.IntegrityError):
            self.admit()
        seal_original(self.original)
        with self.assertRaisesRegex(q0.IntegrityError, "Main-pinned"):
            self.admit()

    def test_loaded_failed_stage_rejects_even_resealed_fixture(self):
        put(self.original, "stages/" + supplement.FAILED_STAGE + "/LOAD.json", {})
        seal_original(self.original)
        self.pins.update(seal_sha256=q0.file_hash(self.original / "SEAL.json"), finalized_sha256=q0.file_hash(self.original / "FINALIZED.json"))
        with self.assertRaisesRegex(q0.IntegrityError, "no load"):
            self.admit()

    def test_wrong_failure_or_release_rejects(self):
        path = self.original / "logs" / (supplement.FAILED_STAGE + ".log")
        path.write_text("gpu_identity TimeoutExpired --query-gpu=uuid,name,driver_version timed out after 7 seconds")
        seal_original(self.original)
        self.pins.update(seal_sha256=q0.file_hash(self.original / "SEAL.json"), finalized_sha256=q0.file_hash(self.original / "FINALIZED.json"))
        with self.assertRaisesRegex(q0.IntegrityError, "chronology"):
            self.admit()

    def test_prepare_is_disjoint_write_once_and_replayable(self):
        plan = self.prepare()
        self.assertFalse(plan["joined_diagnostic"])
        self.assertEqual(plan["attempts"], 1)
        with self.assertRaises(q0.IntegrityError):
            self.prepare()
        with patch.object(q0, "native_verify", side_effect=self.fake_verify), patch.object(q0, "native_input_pins", return_value={}):
            actual, prepared, _ = supplement.verify(self.out)
        self.assertEqual(actual, plan)
        self.assertEqual(prepared, self.prepared)
        self.assertEqual(q0.inventory(self.original), self.old_before)

    def test_source_and_plan_mutation_reject_before_load(self):
        plan = self.prepare()
        plan["updates"] = 1
        put(self.out, "manifest.json", plan)
        put(self.out, "PREPARED.json", {name: q0.file_hash(self.out / name) for name in
                                       ("manifest.json", "prepared.json", "requests.json", "custody.json")})
        with self.assertRaises(q0.IntegrityError):
            supplement.verify(self.out)

    def test_gpu_entrypoints_require_opt_in_before_reads(self):
        with patch.object(supplement, "verify", side_effect=AssertionError("must not read")):
            for call in (supplement.execute, supplement.worker):
                with self.assertRaises(q0.IntegrityError):
                    call("/nonexistent")

    def test_direct_worker_uses_original_evaluate_frozen_and_no_training(self):
        plan = self.prepare()
        now = supplement.time.time()
        controller = dict(pid=222, start_ticks=1)
        worker_identity = dict(pid=333, pgid=333, session=333, ppid=222, start_ticks=2)
        put(self.out, "STARTED.json", dict(started=now, deadline=now + 3600, controller=controller))
        put(self.out, "job.json", dict(started_sha256=q0.file_hash(self.out / "STARTED.json"),
                                      manifest_sha256=q0.file_hash(self.out / "manifest.json"),
                                      controller=controller, deadline=now + 3555))
        counts = dict(natural_prefix_forwards=0, model_forward_calls=0)
        class Frozen(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.anchor = torch.nn.Parameter(torch.zeros(1), requires_grad=False)
            def forward(self, input_ids, use_cache=False, output_hidden_states=False):
                self.assert_frozen()
                counts["natural_prefix_forwards"] += 1
                counts["model_forward_calls"] += 1
                return SimpleNamespace(logits=torch.zeros(1, 1, 21405))
            def assert_frozen(self):
                assert not self.training and not self.anchor.requires_grad
        model = Frozen().eval()
        @contextmanager
        def counter(current):
            self.assertIs(current, model)
            yield counts
        def generate(current, tokenizer, row, *, max_new_tokens, do_sample):
            self.assertEqual((max_new_tokens, do_sample), (32, False))
            output = raw_output(row.get("expected", "ACT: -mem2reg"), tokenizer)
            counts["model_forward_calls"] += len(output["generated_ids"])
            return output
        diagnostic, _, _ = q0.historical_helpers()
        with patch.object(supplement, "verify", return_value=(plan, self.prepared, self.tokenizer)), \
                patch.object(supplement, "source_pins", return_value=plan["source_pins"]), \
                patch.object(supplement, "gpu_identity_30s", return_value={"fixture": True}) as query, \
                patch.object(supplement, "load_snapshot", return_value=(model, plan["admission"]["adapter"]["lora_sha256"])), \
                patch.object(q0, "process_identity", side_effect=lambda pid: controller if pid == supplement.os.getppid() else worker_identity), \
                patch.object(q0, "native_forward_counter", side_effect=counter), \
                patch.object(q0, "native_generate", side_effect=generate), \
                patch.object(q0, "evaluate", wraps=q0.evaluate) as evaluate, \
                patch.object(q0, "train_fit", side_effect=AssertionError("no fitting")), \
                patch.object(diagnostic.w0, "gpu_identity", side_effect=AssertionError("no old identity query")):
            result = supplement.worker(self.out, allow_gpu=True)
        self.assertEqual(result["records"], 584)
        query.assert_called_once()
        self.assertEqual(evaluate.call_args.args[2:4], ("P_DERANGED", 128))
        done = supplement.read_json(self.out / "DONE.json")
        self.assertEqual(done["counters"]["natural_prefix_forwards"], 288)
        self.assertEqual((done["updates"], done["training_forwards"]), (0, 0))
        self.assertEqual(q0.inventory(self.original), self.old_before)

    def test_snapshot_loader_uses_exact128_readonly_and_tensor_check(self):
        plan = self.prepare()
        base, loaded = Mock(), Mock()
        diagnostic = SimpleNamespace(w0=SimpleNamespace(assert_gpu_idle=Mock(), load_hf_model=Mock(return_value=base),
            lora_tensors=Mock(side_effect=[{}, {"fixture": True}]), tree_hash=Mock(return_value=plan["admission"]["adapter"]["adapter_sha256"]),
            tensor_digest=Mock(return_value=plan["admission"]["adapter"]["lora_sha256"])))
        peft = SimpleNamespace(PeftModel=SimpleNamespace(from_pretrained=Mock(return_value=loaded)))
        with patch.object(q0, "historical_helpers", return_value=(diagnostic, None, {})), \
                patch.object(q0, "configure_worker_torch", return_value="CPU_FIXTURE") as configured, \
                patch.dict(sys.modules, peft=peft):
            actual, digest = supplement.load_snapshot(plan, self.prepared)
        self.assertIs(actual, loaded)
        self.assertEqual(digest, plan["admission"]["adapter"]["lora_sha256"])
        configured.assert_called_once_with(diagnostic, self.config, self.prepared)
        peft.PeftModel.from_pretrained.assert_called_once_with(base, str(self.original / plan["admission"]["adapter"]["path"]),
                                                             is_trainable=False, local_files_only=True)
        loaded.requires_grad_.assert_called_once_with(False)
        loaded.eval.assert_called_once()

    def mock_controller(self, *, fail=False, bad_release=False, corrupt=None, joined=False):
        plan = self.prepare(joined)
        commands = []
        actual_diagnostic, _, _ = q0.historical_helpers()

        def run(command, *, log_path, timeout, device):
            commands.append(command)
            self.assertEqual(command[3], "gpu.astra_q0_readout_supplement")
            self.assertGreater(timeout, 30)
            self.assertLessEqual(timeout, 3555)
            job = supplement.read_json(self.out / "job.json")
            now = supplement.time.time()
            identity = dict(pid=5555, pgid=5555, session=5555, ppid=job["controller"]["pid"], start_ticks=123)
            put(self.out, "worker.process.json", dict(pid=5555, pgid=5555, device=device))
            put(self.out, "worker.cleanup.json", dict(pid=5555, device=device, owned_group_empty=not bad_release,
                                                       gpu_processes_absent=not bad_release, reservation_release_verified=not bad_release))
            log_path.write_text("CPU FIXTURE WORKER, NO PROCESS LAUNCHED")
            if fail:
                raise subprocess.TimeoutExpired(command, timeout)
            hardware = dict(node=self.config["node"], gpu_uuid=device, driver_version=self.config["driver_version"],
                            gpu_name="A40", timeout_seconds=30, started=now, finished=now)
            load = dict(identity=identity, job_sha256=q0.file_hash(self.out / "job.json"), manifest_sha256=q0.file_hash(self.out / "manifest.json"),
                        source_pins=plan["source_pins"], prepared_sha256=plan["prepared_sha256"], requests_sha256=plan["requests_sha256"],
                        adapter=plan["admission"]["adapter"], actual_lora_sha256=plan["admission"]["adapter"]["lora_sha256"],
                        allocation=self.prepared["allocation"], hardware=hardware, loaded=now)
            put(self.out, "CLAIMED.json", dict(identity=identity, timestamp=now))
            put(self.out, "LOAD.json", load)
            records = readout_fixture(self.prepared, self.tokenizer, supplement.STATE, 128)
            if corrupt == "missing":
                records.pop()
            if corrupt == "decode":
                next(record for record in records if record["operation"] == "generate")["output"]["text"] = "bad"
            if corrupt == "order":
                records[0], records[1] = records[1], records[0]
            events = []
            for index, record in enumerate(records):
                path = f"{index:04d}.json"
                put(self.out, "events/" + path, record)
                events.append(dict(path=path, sha256=q0.file_hash(self.out / "events" / path)))
            tokens = sum(len(record["output"]["generated_ids"]) for record in records if record["operation"] == "generate")
            counters = dict(natural_prefix_forwards=288, model_forward_calls=288 + tokens + (corrupt == "counter"))
            put(self.out, "DONE.json", dict(version=supplement.VERSION, load=load, records=records, events=events,
                                           counters=counters, updates=0, training_forwards=0, finished=supplement.time.time()))
            return 5555

        supervisor = SimpleNamespace(run_worker=run, gpu_processes_absent=Mock(return_value=not bad_release))
        diagnostic = SimpleNamespace(w0=SimpleNamespace(assert_output_fds_outside_run=Mock(), tree_hash=actual_diagnostic.w0.tree_hash))
        def helpers():
            return diagnostic, supervisor, {}
        with patch.object(supplement, "verify", return_value=(plan, self.prepared, self.tokenizer)), \
                patch.object(q0, "historical_helpers", side_effect=helpers), \
                patch.dict(supplement.os.environ, CUDA_VISIBLE_DEVICES=self.config["gpu_uuid"], CUBLAS_WORKSPACE_CONFIG=":4096:8"):
            result = supplement.execute(self.out, allow_gpu=True)
            self.assertEqual(supplement.replay(self.out), result)
            with self.assertRaises(q0.IntegrityError):
                supplement.execute(self.out, allow_gpu=True)
        self.assertEqual(q0.inventory(self.original), self.old_before)
        self.assertEqual(len(commands), 1)
        return result

    def test_complete584_readout_is_supplement_not_primary(self):
        result = self.mock_controller(joined=True)["report"]
        self.assertEqual(result["status"], "SUPPLEMENT_READOUT_COMPLETE")
        self.assertEqual((result["prefix_readouts"], result["generations"], result["updates"]), (288, 296, 0))
        self.assertEqual(result["original_primary_label"], "NONREPORTABLE_RUNTIME_ABORT")
        self.assertFalse(result["original_primary_changed"])
        self.assertFalse(result["primary_three_root_complete"])
        self.assertEqual(result["joined_diagnostic"]["scope"], "POST_ABORT_JOINED_DIAGNOSTIC_ENDPOINT_NOT_ORIGINAL_PRIMARY")
        self.assertTrue(result["joined_diagnostic"]["endpoint_passed"])

    def test_worker_failure_preserves_abort_and_no_retry(self):
        self.assertEqual(self.mock_controller(fail=True)["report"]["status"], "SUPPLEMENT_ABORT")

    def test_missing_release_cannot_be_complete(self):
        self.assertEqual(self.mock_controller(bad_release=True)["report"]["status"], "SUPPLEMENT_ABORT")

    def test_missing_capture_cannot_be_complete(self):
        self.assertEqual(self.mock_controller(corrupt="missing")["report"]["status"], "SUPPLEMENT_ABORT")

    def test_decoder_drift_cannot_be_complete(self):
        self.assertEqual(self.mock_controller(corrupt="decode")["report"]["status"], "SUPPLEMENT_ABORT")

    def test_counter_drift_cannot_be_complete(self):
        self.assertEqual(self.mock_controller(corrupt="counter")["report"]["status"], "SUPPLEMENT_ABORT")

    def test_request_order_cannot_change(self):
        self.assertEqual(self.mock_controller(corrupt="order")["report"]["status"], "SUPPLEMENT_ABORT")


class IdentityTests(unittest.TestCase):
    def config(self):
        return dict(node=q0.hashlib.sha256(b"fixture-node").hexdigest(), gpu_uuid="GPU-fixture", driver_version="580.1")

    def test_one_exact30s_identity_query(self):
        with patch.object(supplement.platform, "node", return_value="fixture-node"), \
                patch.object(supplement.subprocess, "run", return_value=SimpleNamespace(stdout="GPU-fixture, NVIDIA A40, 580.1\n")) as run:
            result = supplement.gpu_identity_30s(self.config())
        self.assertEqual(result["timeout_seconds"], 30)
        run.assert_called_once_with(["nvidia-smi", "-i", "GPU-fixture", "--query-gpu=uuid,name,driver_version", "--format=csv,noheader,nounits"],
                                    capture_output=True, text=True, check=True, timeout=30)

    def test_query_timeout_has_no_retry(self):
        with patch.object(supplement.platform, "node", return_value="fixture-node"), \
                patch.object(supplement.subprocess, "run", side_effect=subprocess.TimeoutExpired("fixture", 30)) as run:
            with self.assertRaises(subprocess.TimeoutExpired):
                supplement.gpu_identity_30s(self.config())
        self.assertEqual(run.call_count, 1)

    def test_identity_mismatch_rejects(self):
        for output in ("", "GPU-other,A40,580.1", "GPU-fixture,A100,580.1", "GPU-fixture,A40,999", "GPU-fixture,A40,580.1\nGPU-fixture,A40,580.1"):
            with patch.object(supplement.platform, "node", return_value="fixture-node"), \
                    patch.object(supplement.subprocess, "run", return_value=SimpleNamespace(stdout=output)), \
                    self.assertRaises(q0.IntegrityError):
                supplement.gpu_identity_30s(self.config())

    def test_finalization_deadline_cannot_promote_candidate(self):
        report = dict(status="SUPPLEMENT_READOUT_COMPLETE", joined_diagnostic={"endpoint_passed": True})
        result = supplement.effective_report(report, dict(finished=4000., elapsed_seconds=3600.), dict(deadline=4000.))
        self.assertEqual(result["report"]["status"], "SUPPLEMENT_ABORT")
        self.assertIsNone(result["report"]["joined_diagnostic"])

    def test_post_fsync_overrun_cannot_promote_candidate(self):
        report = dict(status="SUPPLEMENT_READOUT_COMPLETE", joined_diagnostic={"endpoint_passed": True})
        result = supplement.effective_report(report, dict(finished=3999., elapsed_seconds=3599.), dict(deadline=4000.),
                                             dict(observed=4001., elapsed_seconds=3601.))
        self.assertEqual(result["report"]["status"], "SUPPLEMENT_ABORT")


if __name__ == "__main__":
    unittest.main()
