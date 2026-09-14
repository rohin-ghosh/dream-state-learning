"""Caller-bound native entry; importing performs no preparation or execution.

Main owns source/native/lease authorization and external hash/wheel provenance.
CPU preparation is not CUDA qualification. Execution uses the existing reduced
conductor's SAME-PROCESS roundtrip: no fresh-process persistence or G1 claim.
Deadlines include every top-level training forward, not preemption of an ongoing
kernel/backward/update. Handled aborts export training observations, never a
partial checkpoint; process death and storage failure can still prevent export.
Arendt's _source_gates/_Attempt preflight and separation_original_dir relocation
contract are reused verbatim; no alternate source-admission schema is defined.
Invoke the CLI with python -m gpu.astra_stage2a_native_entry, after Main review.
"""

import argparse
from dataclasses import asdict
from hashlib import sha256
from importlib import metadata
import math
import os
from pathlib import Path
import subprocess
import time

from gpu import astra_stage2a_native_models as models
from gpu import astra_stage2a_native_prepare as prepare
from gpu import astra_stage2a_native_tokenizer_receipt as tokens
from gpu import astra_stage2a_reduced_conductor as conductor
from organism_v6 import composition_birth_stage2a_actor as actor_api
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_training as training
from organism_v6 import pcfl_vertical_train as base_hash_api


base_state_hash = base_hash_api._state_hash


class EntryFailure(RuntimeError):
    def __init__(self, error, evidence):
        super().__init__(str(error))
        self.original_error, self.evidence = error, evidence


def _write(path, value):
    with Path(path).open("xb") as stream:
        stream.write(tokens._encode(value))


def _hash_file(path, check):
    training._require(Path(path).is_file(), "regular_file_required")
    digest, length = sha256(), 0
    with Path(path).open("rb") as stream:
        before = os.fstat(stream.fileno())
        while True:
            check("file_hash:" + Path(path).name)
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            length += len(chunk)
        after = os.fstat(stream.fileno())
    training._require((before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                      == (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                      and length == before.st_size, "file_changed_during_hash")
    return {"sha256": digest.hexdigest(), "size": length}


def verify_official_files(model_dir, official_manifest, check):
    check("official_manifest")
    training._require(Path(official_manifest).stat().st_size <= tokens.MAX_FILE_BYTES,
                      "bounded_official_manifest_required")
    raw = Path(official_manifest).read_bytes()
    training._require(sha256(raw).hexdigest() == tokens.OFFICIAL_RECEIPT_SHA256,
                      "official_manifest_authentication_mismatch")
    official = tokens._json(raw)
    training._require(official.get("repository") == tokens.REPOSITORY
                      and official.get("revision") == tokens.REVISION
                      and official.get("status") == "PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING"
                      and official.get("file_count") == 14 and len(official["files"]) == 14,
                      "complete_official_14_file_binding_required")
    observed = {}
    for name, expected in official["files"].items():
        tokens._relative(name)
        training._require("/" not in name, "flat_official_file_roster_required")
        observed[name] = _hash_file(Path(model_dir) / name, check)
        training._require(observed[name] == {key: expected[key] for key in ("sha256", "size")},
                          "official_file_mismatch:" + name)
    return observed


def _device_receipt(options, check, clock):
    rows = []
    for uuid in options.gpu_uuids:
        check("device_identity")
        reply = subprocess.run(["nvidia-smi", "-i", uuid, "--query-gpu=uuid,name,driver_version",
                                "--format=csv,noheader,nounits"], check=True, capture_output=True,
                               text=True, timeout=options.deadline_unix - clock())
        actual, name, driver = (part.strip() for part in reply.stdout.strip().split(","))
        training._require(actual == uuid and driver == options.driver_version, "gpu_or_driver_pin_mismatch")
        rows.append(dict(uuid=actual, name=name, driver_version=driver))
    return rows


def _references(model):
    return dict(model.named_parameters()) | dict(model.named_buffers())


def _active_atom(initialized):
    model = initialized.model
    training._require(set(model.peft_config) == {"default"} and list(model.active_adapters) == ["default"],
                      "default_atom_adapter_must_be_active")
    for spec in initialized.observation.trainable_roster:
        if ".lora_A." in spec.name:
            module = model.get_submodule(spec.name.split(".lora_A.")[0])
            training._require(not module.disable_adapters and not module.merged
                              and list(module.active_adapters) == ["default"], "atom_adapter_disabled_or_merged")


def run_entry(options, *, libraries=None, clock=time.time, device_probe=_device_receipt,
              actor_factory=actor_api.ReadoutActor, trainer_factory=training.StatefulTrainer,
              emit_progress=False):
    """Run only after Main's review; injected libraries/factories are trusted code.

    Return all live objects, including failure-inclusive conductor evidence.
    EntryFailure retains those same objects and the original exception. Partial
    files are never removed. Missing runtime wheels are recorded as unverified,
    not silently authenticated. No numerical pass criterion is required.
    """
    evidence = {"objects": {}, "receipt": {"mode": options.mode, "stages": [], "hashes": {},
                "claim_scope": "SAME_PROCESS_ONLY_NOT_FRESH_PROCESS_OR_G1",
                "wheel_attestation": "MAIN_OWNED_NOT_VERIFIED_HERE"}, "errors": []}
    receipt, objects = evidence["receipt"], evidence["objects"]
    root = None
    training_export_attempted = False

    def export_training():
        nonlocal training_export_attempted
        trainer = objects.get("trainer")
        if trainer is None:
            return True
        if training_export_attempted:
            return receipt["training_observations"]["export"] == "COMPLETE"
        training_export_attempted = True
        record = receipt["training_observations"] = {"path": "TRAINING_OBSERVATIONS.json", "export": "INCOMPLETE"}
        try:
            faults = getattr(objects.get("conductor"), "failures", ())
            snapshot = dict(kind="TRAINING_OBSERVATIONS_NOT_A_CHECKPOINT_NOT_RESUMABLE",
                completed_updates=trainer.completed_updates, cursor=trainer.cursor,
                receipt_count=len(trainer.receipts), receipts=tokens.retain(trainer.receipts),
                binding=tokens.retain(trainer.binding), lineage_failed=getattr(trainer, "_failed", None),
                errors=[dict(error_type=type(error).__name__, error=str(error)) for error in
                        evidence["errors"] + [getattr(fault, "error", fault) for fault in faults]],
                limit="Trainer-reported counters only; the failing update may be partially applied. No optimizer/adapter/RNG restoration evidence.")
            objects["training_observations"] = snapshot
            _write(root / record["path"], snapshot)
            record.update(export="COMPLETE", sha256=sha256(tokens._encode(snapshot)).hexdigest(),
                          completed_updates=trainer.completed_updates, receipt_count=len(trainer.receipts))
            return True
        except BaseException as error:
            evidence["errors"].append(error)
            return False

    def check(stage):
        training._require(type(options.deadline_unix) in (int, float)
                          and math.isfinite(options.deadline_unix) and clock() < options.deadline_unix,
                          "finite_unexpired_deadline_required:" + stage)

    def stage(name, callback):
        check(name)
        timing = {"stage": name, "started_unix": clock(), "status": "RUNNING"}
        receipt["stages"].append(timing)
        if emit_progress:
            print(tokens._encode(timing).decode("ascii"), end="", flush=True)
        try:
            result = callback()
            timing["status"] = "RETURNED"
            return result
        except BaseException:
            timing["status"] = "ERROR"
            raise
        finally:
            timing["finished_unix"] = clock()
            timing["elapsed_seconds"] = timing["finished_unix"] - timing["started_unix"]
            if emit_progress:
                print(tokens._encode(timing).decode("ascii"), end="", flush=True)

    try:
        check("entry")
        training._require(options.mode in ("prepare-only", "reduced") and training._sha(options.base_state_sha256),
                          "explicit_mode_and_base_state_binding_required")
        training._require(all(type(value) is str and value.strip() and value.isascii() and "\0" not in value
                              for value in (options.lineage_id, options.base_state_id, options.atom_state_id))
                          and options.base_state_id != options.atom_state_id, "distinct_explicit_state_bindings_required")
        training._require(type(options.threads) is int and options.threads > 0
                          and type(options.interop_threads) is int and options.interop_threads > 0,
                          "positive_explicit_thread_pins_required")
        visible = "" if options.mode == "prepare-only" else ",".join(options.gpu_uuids)
        training._require(os.environ.get("CUDA_VISIBLE_DEVICES") == visible, "visible_device_pin_mismatch")
        if options.mode == "reduced":
            training._require(len(options.gpu_uuids) == len(set(options.gpu_uuids)) == 2
                              and all(value.startswith("GPU-") for value in options.gpu_uuids)
                              and {options.base_device, options.atom_device} == {"cuda:0", "cuda:1"}
                              and bool(options.driver_version), "explicit_distinct_two_gpu_bindings_required")
        master = bytes.fromhex(options.master_hex)
        training._require(0 < len(master) <= 4096, "bounded_preselected_master_required")
        destination = Path(options.output_dir).absolute()
        destination.mkdir(parents=False, exist_ok=False)
        root = destination
        _write(root / "REQUEST.json", vars(options))
        allocation = objects["allocation"] = stage("allocation", lambda: prepare.allocate_source(master=master))
        compiled = objects["curriculum"] = stage("compile", lambda: prepare.compile_source_curriculum(
            bound_allocation=allocation, master=master))
        attempt = tokens._Attempt(root / "source_preflight")
        try:
            receipt["source_gates"] = stage("source_gates", lambda: tokens._source_gates(
                attempt, options.qualification_dir, options.separation_dir, allocation, compiled, master,
                options.separation_original_dir))
        finally:
            attempt.freeze()
        source_paths = [Path(__file__)] + [Path(module.__file__) for module in (models, tokens, conductor, base_hash_api)]
        receipt["implementation_pins"] = {str(path): _hash_file(path, check) for path in source_paths}
        receipt["official_files"] = stage("official_files", lambda: verify_official_files(
            options.model_dir, options.official_manifest, check))
        receipt["runtime"] = stage("runtime_versions", lambda: {
            name: metadata.version(name) for name in tokens.RUNTIME_VERSIONS})
        training._require(all(receipt["runtime"][name] == version.split("+")[0]
                              or receipt["runtime"][name] == version
                              for name, version in tokens.RUNTIME_VERSIONS.items() if version is not None),
                          "runtime_distribution_version_mismatch")
        os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = str(options.threads)
        if libraries is None:
            check("native_imports")
            import torch
            import peft
            import transformers
        else:
            torch, peft, transformers = libraries
        check("runtime_setup")
        training._require(torch.__version__ == "2.13.0+cu130" and torch.version.cuda == "13.0"
                          and transformers.__version__ == "5.5.3" and peft.__version__ == "0.20.0"
                          and not torch.cuda.is_initialized(), "exact_runtime_and_uninitialized_cuda_required")
        torch.set_num_threads(options.threads)
        torch.set_num_interop_threads(options.interop_threads)
        receipt["loaded_runtime"] = dict(torch=torch.__version__, transformers=transformers.__version__,
                                         peft=peft.__version__, cuda_runtime=torch.version.cuda)
        receipt["thread_environment"] = {name: os.environ[name] for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS")}
        receipt["threads"] = {"intra": torch.get_num_threads(), "interop": torch.get_num_interop_threads()}
        training._require(receipt["threads"] == {"intra": options.threads, "interop": options.interop_threads},
                          "effective_thread_pin_mismatch")
        tokenizer = objects["tokenizer"] = stage("tokenizer_load", lambda: transformers.AutoTokenizer.from_pretrained(
            options.model_dir, local_files_only=True, trust_remote_code=False, use_fast=True, padding_side="right"))
        receipt["tokenizer_backend_restoration"] = stage("tokenizer_backend_restoration", lambda: tokens.restore_official_backend(
            tokenizer, options.model_dir, receipt["official_files"], root / "backend_restoration"))
        token_receipt = objects["tokenizer_receipt"] = stage("tokenizer_receipt", lambda: tokens.prepare_tokenizer_receipt(
            bound_allocation=allocation, compiled_curriculum=compiled, master=master, tokenizer=tokenizer,
            model_dir=options.model_dir, official_manifest=options.official_manifest, loaded_files=tokens.REQUIRED_FILES,
            qualification_dir=options.qualification_dir, separation_dir=options.separation_dir,
            separation_original_dir=options.separation_original_dir, output_dir=root / "tokenizer"))
        receipt["tokenizer_receipt_sha256"] = token_receipt.receipt_sha256

        def load_cpu():
            model = transformers.AutoModelForCausalLM.from_pretrained(
                options.model_dir, local_files_only=True, trust_remote_code=False, torch_dtype=torch.bfloat16,
                device_map=None, attn_implementation="sdpa", use_safetensors=True)
            training._require(model.config._attn_implementation == "sdpa"
                              and all(value.device.type == "cpu" for value in _references(model).values()),
                              "cpu_sdpa_model_required")
            return model

        raw_atom = objects["raw_atom"] = stage("atom_cpu_load", load_cpu)
        initialized = objects["initialized"] = stage("atom_initialize", lambda: models.initialize_atom_cpu(
            raw_atom, torch=torch, peft=peft, master=master, initial_directory=root / "initial",
            expected_base_sha256=options.base_state_sha256, base_state_hash=base_state_hash))
        receipt["initial"] = initialized.receipt
        receipt["hashes"]["atom_cpu_base"] = stage("atom_cpu_base_hash", lambda: models.verify_retained_base(
            initialized, base_state_hash=base_state_hash))
        training._require(not torch.cuda.is_initialized(), "cpu_preparation_initialized_cuda")
        if options.mode == "prepare-only":
            receipt["status"] = "PREPARED_CPU_ONLY"
        else:
            base = objects["base"] = stage("base_cpu_load", load_cpu)
            training._require(base is not initialized.model and base is not raw_atom, "distinct_base_atom_models_required")
            receipt["hashes"]["base_cpu"] = stage("base_cpu_hash", lambda: base_state_hash(_references(base)))
            training._require(receipt["hashes"]["base_cpu"] == options.base_state_sha256, "base_tensor_pin_mismatch")
            receipt["devices"] = stage("devices", lambda: device_probe(options, check, clock))
            training._require(os.environ.get("CUDA_VISIBLE_DEVICES") == visible and not torch.cuda.is_initialized(),
                              "cuda_visibility_or_initialization_changed_before_placement")
            stage("cuda_initialize", torch.cuda.init)
            training._require(torch.cuda.device_count() == 2, "exactly_two_visible_devices_required")
            torch.cuda.manual_seed_all(primitives.adapter_seed(master))
            base.requires_grad_(False)
            stage("base_place", lambda: base.to(device=options.base_device))
            stage("atom_place", lambda: initialized.model.to(device=options.atom_device))
            for model, device in ((base, options.base_device), (initialized.model, options.atom_device)):
                training._require(all(str(value.device) == device for value in _references(model).values()),
                                  "complete_single_device_placement_required")

            class GuardedActor(actor_factory):
                def count_context(self, prefix):
                    check("readout_context")
                    return super().count_context(prefix)

                def __call__(self, request):
                    check("readout_call")
                    if self.model is initialized.model:
                        _active_atom(initialized)
                    return super().__call__(request)

            class GuardedTrainer(trainer_factory):
                def train_stage(self, selected):
                    check("D1_train")

                    def before_forward(module, inputs):
                        check("D1_training_forward")

                    handle = self.model.register_forward_pre_hook(before_forward)
                    try:
                        return super().train_stage(selected)
                    finally:
                        handle.remove()

                def checkpoint(self):
                    check("D1_checkpoint_roundtrip")
                    return super().checkpoint()

            trainer = objects["trainer"] = stage("trainer", lambda: GuardedTrainer(
                initialized.model, arm="ATOM_LOCAL", master=master, batches=token_receipt.prepared_birth.batches,
                trainable_roster=initialized.observation.trainable_roster, layer_count=initialized.observation.layer_count,
                adapter_name="default", lineage_id=options.lineage_id, preparation_sha256=token_receipt.receipt_sha256,
                initial_adapter_sha256=initialized.observation.initial_adapter_sha256))
            actors = [GuardedActor(model=model, tokenizer=tokenizer, torch=torch, device=device,
                                  count_basis=prepare.COUNT_BASIS) for model, device in
                      ((base, options.base_device), (initialized.model, options.atom_device))]
            objects["actors"] = actors
            held = objects["held"] = stage("held", lambda: prepare.prepare_reduced_held(bound_allocation=allocation))
            for label, verify in (("base", lambda: base_state_hash(_references(base))),
                                  ("atom_base", lambda: models.verify_retained_base(initialized, base_state_hash=base_state_hash))):
                receipt["hashes"][label + "_pre"] = stage(label + "_pre", verify)
                training._require(receipt["hashes"][label + "_pre"] == options.base_state_sha256, "pre_base_drift")
            try:
                objects["conductor"] = stage("conductor", lambda: conductor.run_reduced_conductor(
                    base_state_id=options.base_state_id, atom_local_state_id=options.atom_state_id,
                    base_actor=actors[0], atom_local_actor=actors[1], trainer=trainer, trainer_binding=dict(trainer.binding),
                    batches=trainer.batches, master=master, chains=held.chains, interventions=held.interventions,
                    canaries=held.canaries, counter_provenance="TOKENIZER_RECEIPT_SHA256:" + token_receipt.receipt_sha256,
                    base_custody_dir=root / "BASE", atom_custody_dir=root / "ATOM_LOCAL", checkpoint_dir=root / "D1", torch=torch))
            finally:
                for label, verify in (("base", lambda: base_state_hash(_references(base))),
                                      ("atom_base", lambda: models.verify_retained_base(initialized, base_state_hash=base_state_hash))):
                    try:
                        receipt["hashes"][label + "_post"] = stage(label + "_post", verify)
                        training._require(receipt["hashes"][label + "_post"] == options.base_state_sha256, "post_base_drift")
                    except BaseException as error:
                        evidence["errors"].append(error)
            run = objects["conductor"]
            training._require(run.terminal_reason == "reduced" and not run.failures and not evidence["errors"],
                              "conductor_or_base_audit_incomplete")
            receipt.update(status="REDUCED_NUMERICAL_DATA", conductor_hashes=run.hashes,
                           criteria=[asdict(item) for item in run.reduction.criteria])
        training._require(export_training(), "training_observations_export_failed")
        check("finish")
        training._require(receipt["implementation_pins"] == {str(path): _hash_file(path, check) for path in source_paths},
                          "implementation_changed_during_entry")
        _write(root / "RESULT.json", receipt)
        return evidence
    except BaseException as error:
        evidence["errors"].append(error)
        export_training()
        if root is not None and root.is_dir() and not (root / "RESULT.json").exists():
            try:
                _write(root / "FAILED.json", dict(receipt, error_type=type(error).__name__, error=str(error)))
            except BaseException as storage_error:
                evidence["errors"].append(storage_error)
        raise EntryFailure(error, evidence) from error


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare-only", "reduced"))
    for name in ("model-dir", "official-manifest", "qualification-dir", "separation-dir", "output-dir",
                 "master-hex", "base-state-sha256", "lineage-id", "base-state-id", "atom-state-id"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--separation-original-dir")
    parser.add_argument("--deadline-unix", required=True, type=float)
    parser.add_argument("--threads", required=True, type=int)
    parser.add_argument("--interop-threads", required=True, type=int)
    parser.add_argument("--gpu-uuids", nargs=2, default=[])
    parser.add_argument("--base-device")
    parser.add_argument("--atom-device")
    parser.add_argument("--driver-version")
    return parser.parse_args(argv)


if __name__ == "__main__":
    run_entry(parse_args(), emit_progress=True)
