"""Evaluation-only recovery of the committed D1; no optimizer or training calls."""

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import time

from gpu import astra_stage2a_native_models as models
from gpu import astra_stage2a_native_prepare as prepare
from gpu import astra_stage2a_native_tokenizer_receipt as tokens
from gpu import astra_stage2a_recovery_load as recovery
from gpu.astra_stage2a_reduced_conductor import _checkpoint_adapter_sha256
from organism_v6 import composition_birth_stage2a_actor as actor_api
from organism_v6 import composition_birth_stage2a_checkpoint as checkpoint_api
from organism_v6 import composition_birth_stage2a_screen as screen
from organism_v6 import composition_birth_stage2a_screen_custody as custody
from organism_v6 import composition_birth_stage2a_screen_reduce as reducer
from organism_v6 import composition_birth_stage2a_screen_runtime as runtime
from organism_v6 import composition_birth_stage2a_training as training
from organism_v6.pcfl_vertical_train import _state_hash


def write(path, value):
    with Path(path).open("xb") as stream:
        stream.write(tokens._encode(value))


def restore_adapter(initialized, checkpoint, *, torch):
    roster = initialized.observation.trainable_roster
    training._require(checkpoint["binding"]["roster"] == [asdict(spec) for spec in roster],
                      "saved_roster_mismatch")
    expected = _checkpoint_adapter_sha256(checkpoint, roster)
    named = dict(initialized.model.named_parameters())
    for spec in roster:
        value = checkpoint["adapter"][spec.name]
        training._require(tuple(value.shape) == spec.shape and str(value.dtype) == spec.dtype
                          and bool(torch.isfinite(value).all()), "invalid_saved_adapter")
    with torch.no_grad():
        for spec in roster:
            named[spec.name].copy_(checkpoint["adapter"][spec.name])
    training._require(training.adapter_sha256(initialized.model, roster) == expected,
                      "restored_adapter_hash_mismatch")
    return expected


def run(options):
    root = Path(options.output_dir)
    root.mkdir(exist_ok=False)
    receipt = dict(status="INCOMPLETE", started_unix=time.time(),
                   recovery="D1_EVALUATION_ONLY", new_updates=0, baseline_model_calls=0,
                   original_run=options.original_run, checkpoint_sha256=options.checkpoint_sha256,
                   limits="DEV text-memory controller readout; no autonomous parenting or H1/H2 claim. "
                          "Only adapter tensors restored; optimizer/RNG continuation not exercised.")
    write(root / "REQUEST.json", vars(options))

    def check():
        training._require(time.time() < options.deadline_unix, "recovery_deadline")

    def progress(stage):
        check()
        print(json.dumps(dict(stage=stage, utc_unix=time.time())), flush=True)

    try:
        import torch
        import peft
        import transformers

        training._require(os.environ.get("CUDA_VISIBLE_DEVICES") == options.gpu_uuid,
                          "single_gpu_binding_required")
        training._require(torch.__version__ == "2.13.0+cu130" and peft.__version__ == "0.20.0"
                          and transformers.__version__ == "5.5.3", "runtime_changed")
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        original = Path(options.original_run)
        request_bytes = (original / "REQUEST.json").read_bytes()
        request = json.loads(request_bytes)
        receipt["original_request_sha256"] = sha256(request_bytes).hexdigest()
        master = bytes.fromhex(request["master_hex"])
        progress("strict_checkpoint_load")
        checkpoint_dir = original / "D1"
        receipt["manifest"] = checkpoint_api.inspect_checkpoint(checkpoint_dir)
        training._require(receipt["manifest"]["blob"]["sha256"] == options.checkpoint_sha256,
                          "checkpoint_blob_binding_mismatch")
        state = recovery.load_exclusive(checkpoint_dir, torch=torch)
        training._require(state["sha256"] == options.state_sha256
                          and state["completed_updates"] == 256 and state["cursor"] == 1024
                          and len(state["receipts"]) == 256
                          and state["binding"]["lineage_id"] == request["lineage_id"],
                          "saved_d1_binding_mismatch")
        receipt["state_sha256"] = state["sha256"]
        progress("tokenizer_and_held")
        official = json.loads(Path(request["official_manifest"]).read_bytes())
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            request["model_dir"], local_files_only=True, trust_remote_code=False,
            use_fast=True, padding_side="right")
        receipt["tokenizer"] = tokens.restore_official_backend(
            tokenizer, request["model_dir"], official["files"], root / "backend")
        allocation = prepare.allocate_source(master=master)
        held = prepare.prepare_reduced_held(bound_allocation=allocation)
        receipt["held_sha256"] = held.receipt_sha256
        progress("base_load_and_adapter_restore")
        base = transformers.AutoModelForCausalLM.from_pretrained(
            request["model_dir"], local_files_only=True, trust_remote_code=False,
            torch_dtype=torch.bfloat16, device_map=None, attn_implementation="sdpa",
            use_safetensors=True)
        initialized = models.initialize_atom_cpu(
            base, torch=torch, peft=peft, master=master, initial_directory=root / "initial",
            expected_base_sha256=request["base_state_sha256"], base_state_hash=_state_hash)
        training._require(initialized.observation.initial_adapter_sha256
                          == state["binding"]["initial_adapter_sha256"], "initial_lineage_mismatch")
        receipt["adapter_sha256"] = restore_adapter(initialized, state, torch=torch)
        initialized.model.to("cuda:0")
        receipt["base_pre"] = models.verify_retained_base(initialized, base_state_hash=_state_hash)

        class BoundedActor(actor_api.ReadoutActor):
            def __call__(self, request):
                check()
                return super().__call__(request)

        actor = BoundedActor(model=initialized.model, tokenizer=tokenizer, torch=torch,
                             device="cuda:0", count_basis=prepare.COUNT_BASIS)
        progress("atom_readout")
        sink = custody.ScreenCustodySink(root / "ATOM_LOCAL", torch=torch)
        try:
            observed = runtime.run_reduced_state(
                state_id=request["atom_state_id"], stage="D1", master=master,
                chains=held.chains, interventions=held.interventions, canaries=held.canaries,
                actor=actor, actor_calls=actor.calls, count_context=actor.count_context,
                counter_provenance=prepare.COUNT_BASIS, custody_sink=sink)
        finally:
            sink.close()
        receipt["terminal_reason"] = observed.terminal_reason
        receipt["physical_calls"] = len(actor.calls)
        receipt["failures"] = [dict(phase=failure.phase, error=str(failure.error))
                               for failure in observed.failures]
        receipt["adapter_post"] = training.adapter_sha256(
            initialized.model, initialized.observation.trainable_roster)
        receipt["base_post"] = models.verify_retained_base(initialized, base_state_hash=_state_hash)
        training._require(receipt["adapter_post"] == receipt["adapter_sha256"], "readout_changed_adapter")
        training._require(observed.terminal_reason == "completed_unscored" and not observed.failures,
                          "incomplete_readout")
        verification = custody.verify_receipt(root / "ATOM_LOCAL")
        receipt["custody"] = dict(state_id=verification.state_id, stage=verification.stage,
                                  terminal_reason=verification.terminal_reason,
                                  event_count=len(verification.events), export_status=verification.export_status)
        reduced = reducer._reduce_state(
            observed, request["atom_state_id"], screen.reduced_decode_seeds("D1", master=master), set(),
            master=master, chains=held.chains, interventions=held.interventions, canaries=held.canaries)
        training._require(reduced.reportable, "nonreportable_atom:" + repr(reduced.issues))
        receipt["metrics"] = asdict(reduced.metrics)
        receipt["accounting"] = asdict(reduced.accounting)
        receipt["status"] = "ATOM_READOUT_COMPLETE_BASE_COMPARISON_PENDING"
        receipt["finished_unix"] = time.time()
        write(root / "RESULT.json", receipt)
        progress("finished")
        return receipt
    except BaseException as error:
        receipt.update(status="FAILED", error_type=type(error).__name__, error=str(error),
                       finished_unix=time.time())
        write(root / "FAILED.json", receipt)
        raise


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("original-run", "output-dir", "checkpoint-sha256", "state-sha256", "gpu-uuid"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--deadline-unix", required=True, type=float)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
