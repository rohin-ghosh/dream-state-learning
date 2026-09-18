"""One caller-authorized full-state D1→D2 continuation, preserving the old root."""

import argparse
import json
import os
from pathlib import Path
import time

from gpu import astra_stage2a_d2_resume as resume
from gpu import astra_stage2a_native_models as models
from gpu import astra_stage2a_native_prepare as prepare
from gpu import astra_stage2a_native_tokenizer_receipt as tokens
from gpu import astra_stage2a_recovery_load as recovery
from gpu.astra_stage2a_recover_readout import write
from organism_v6 import composition_birth_stage2a_actor as actor_api
from organism_v6 import composition_birth_stage2a_checkpoint as checkpoint_api
from organism_v6 import composition_birth_stage2a_training as training
from organism_v6.pcfl_vertical_train import _state_hash


def run(options):
    root = Path(options.output_dir)
    root.mkdir(exist_ok=False)
    write(root / "REQUEST.json", vars(options))
    report = dict(status="INCOMPLETE", started_unix=time.time(),
                  original_run=options.original_run, expected_new_updates=256,
                  expected_cumulative_updates=512, baseline_model_calls=0,
                  claim="DEV_CONTROLLER_D2_NOT_AUTONOMOUS_PARENTING")
    run_result = None

    def check(stage):
        training._require(time.time() < options.deadline_unix, "D2_deadline:" + stage)

    def progress(stage):
        check(stage)
        print(json.dumps(dict(stage=stage, utc_unix=time.time())), flush=True)

    try:
        import torch
        import peft
        import transformers

        training._require(os.environ.get("CUDA_VISIBLE_DEVICES") == ",".join(options.gpu_uuids),
                          "original_two_device_topology_required")
        training._require(torch.__version__ == "2.13.0+cu130" and peft.__version__ == "0.20.0"
                          and transformers.__version__ == "5.5.3", "runtime_changed")
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        original = Path(options.original_run)
        request = json.loads((original / "REQUEST.json").read_bytes())
        master = bytes.fromhex(request["master_hex"])
        progress("load_saved_D1")
        manifest = checkpoint_api.inspect_checkpoint(original / "D1")
        training._require(manifest["blob"]["sha256"] == options.checkpoint_sha256,
                          "D1_blob_changed")
        state = recovery.load_exclusive(original / "D1", torch=torch)
        training._require(state["sha256"] == options.state_sha256
                          and state["completed_updates"] == 256 and state["cursor"] == 1024,
                          "D1_state_changed")
        report["D1_state_sha256"] = state["sha256"]
        report["binding"] = state["binding"]
        progress("prepare_existing_tape")
        official = json.loads(Path(request["official_manifest"]).read_bytes())
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            request["model_dir"], local_files_only=True, trust_remote_code=False,
            use_fast=True, padding_side="right")
        report["tokenizer"] = tokens.restore_official_backend(
            tokenizer, request["model_dir"], official["files"], root / "backend")
        allocation = prepare.allocate_source(master=master)
        compiled = prepare.compile_source_curriculum(bound_allocation=allocation, master=master)
        prepared = prepare.prepare_birth(validated_curriculum=compiled, tokenizer=tokenizer,
                                         master=master, padding_policy=tokens.PADDING_POLICY)
        training._require(training.validate_batches(prepared.batches, master=master)
                          == state["binding"]["batches_sha256"], "saved_training_tape_changed")
        held = prepare.prepare_reduced_held(bound_allocation=allocation)
        report["held_sha256"] = held.receipt_sha256
        progress("model_and_original_rng_topology")
        base = transformers.AutoModelForCausalLM.from_pretrained(
            request["model_dir"], local_files_only=True, trust_remote_code=False,
            torch_dtype=torch.bfloat16, device_map=None, attn_implementation="sdpa",
            use_safetensors=True)
        initialized = models.initialize_atom_cpu(
            base, torch=torch, peft=peft, master=master, initial_directory=root / "initial",
            expected_base_sha256=request["base_state_sha256"], base_state_hash=_state_hash)
        training._require(initialized.observation.initial_adapter_sha256
                          == state["binding"]["initial_adapter_sha256"], "initial_lineage_changed")
        torch.cuda.init()
        training._require(torch.cuda.device_count() == 2, "original_cuda_rng_topology_required")
        initialized.model.to("cuda:1")
        report["base_pre"] = models.verify_retained_base(initialized, base_state_hash=_state_hash)

        class BoundedActor(actor_api.ReadoutActor):
            def __call__(self, request):
                check("readout")
                return super().__call__(request)

        actor = BoundedActor(model=initialized.model, tokenizer=tokenizer, torch=torch,
                             device="cuda:1", count_basis=prepare.COUNT_BASIS)
        trainer_options = dict(
            arm="ATOM_LOCAL", master=master, batches=prepared.batches,
            trainable_roster=initialized.observation.trainable_roster,
            layer_count=initialized.observation.layer_count, adapter_name="default",
            lineage_id=request["lineage_id"], preparation_sha256=state["binding"]["preparation_sha256"],
            initial_adapter_sha256=state["binding"]["initial_adapter_sha256"])
        progress("restore_then_updates257_to512_then_D2_readout")

        def before_forward(module, inputs):
            check("forward")

        hook = initialized.model.register_forward_pre_hook(before_forward)
        try:
            run_result = resume.run_d2_resume(
                model=initialized.model, atom_local_actor=actor, trainer_options=trainer_options,
                trainer_binding=state["binding"], d1_checkpoint_dir=original / "D1",
                d1_checkpoint_sha256=state["sha256"], checkpoint_dir=root / "D2",
                atom_custody_dir=root / "ATOM_LOCAL", atom_local_state_id=request["atom_state_id"],
                base_state_id=request["base_state_id"], base_evidence=str(original / "BASE"),
                master=master, chains=held.chains, interventions=held.interventions, canaries=held.canaries,
                counter_provenance="TOKENIZER_RECEIPT_SHA256:" + state["binding"]["preparation_sha256"],
                torch=torch, checkpoint_loader=lambda directory: recovery.load_exclusive(directory, torch=torch))
        finally:
            hook.remove()
        report["base_post"] = models.verify_retained_base(initialized, base_state_hash=_state_hash)
        report["terminal_reason"] = run_result.terminal_reason
        report["failures"] = [dict(phase=fault.phase, error=str(fault.error)) for fault in run_result.failures]
        report["hashes"] = run_result.hashes
        if run_result.trainer is not None:
            report["completed_updates"] = run_result.trainer.completed_updates
            report["cursor"] = run_result.trainer.cursor
            write(root / "TRAINING_OBSERVATIONS.json", dict(
                completed_updates=run_result.trainer.completed_updates,
                cursor=run_result.trainer.cursor, receipts=tokens.retain(run_result.trainer.receipts)))
        training._require(not run_result.failures and run_result.terminal_reason == "completed_unreduced",
                          "incomplete_D2:" + repr(report["failures"]))
        report["status"] = "D2_COMPLETE_REDUCTION_PENDING"
        report["finished_unix"] = time.time()
        write(root / "RESULT.json", report)
        progress("finished")
        return report
    except BaseException as error:
        report.update(status="FAILED", error=str(error), error_type=type(error).__name__,
                      finished_unix=time.time())
        write(root / "FAILED.json", report)
        raise


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("original-run", "output-dir", "checkpoint-sha256", "state-sha256"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--gpu-uuids", nargs=2, required=True)
    parser.add_argument("--deadline-unix", required=True, type=float)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
