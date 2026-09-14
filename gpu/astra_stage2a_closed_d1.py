"""Fresh CLOSED D1 exploratory arm; execution is explicit, never on import.

Reuse the original paired curriculum and initialization, not its fitted adapter.
Main owns prospective logging and external comparison; this is not admission
under the earlier conditional salvage. No BASE readout, D2, or launch tooling.
Run in an exclusive process with one unused GPU visible. The finite deadline
guards every top-level forward but cannot preempt an in-flight kernel/backward.
"""

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import time

from gpu import astra_stage2a_native_models as models
from gpu import astra_stage2a_native_prepare as prepare
from gpu import astra_stage2a_native_tokenizer_receipt as tokens
from gpu import astra_stage2a_recovery_load as recovery
from gpu.astra_stage2a_recover_readout import write
from gpu.astra_stage2a_reduced_conductor import _checkpoint_adapter_sha256
from organism_v6 import composition_birth_stage2a_actor as actor_api
from organism_v6 import composition_birth_stage2a_checkpoint as checkpoint_api
from organism_v6 import composition_birth_stage2a_screen as screen
from organism_v6 import composition_birth_stage2a_screen_custody as custody
from organism_v6 import composition_birth_stage2a_screen_reduce as reducer
from organism_v6 import composition_birth_stage2a_screen_runtime as runtime
from organism_v6 import composition_birth_stage2a_training as training
from organism_v6.pcfl_vertical_train import _state_hash


MAX_SECONDS = 5400


def validate_pairing(request, original, prepared, initialized, *, master):
    """Use actual masks, tape, recipe and roster validators before any fit."""
    binding = original["binding"]
    training._require(original["completed_updates"] == 256 and original["cursor"] == 1024
                      and len(original["receipts"]) == 256
                      and binding["arm"] == "ATOM_LOCAL"
                      and binding["lineage_id"] == request["lineage_id"], "original_atom_d1_required")
    training.validate_recipe(binding["recipe"])
    fingerprint = training.validate_batches(prepared.batches, master=master)
    training._require(fingerprint == prepared.tape_fingerprint == binding["batches_sha256"],
                      "original_paired_tape_changed")
    observation = initialized.observation
    training.validate_trainable_roster(observation.trainable_roster,
                                      layer_count=observation.layer_count, adapter_name="default")
    training._require(binding["roster"] == [asdict(spec) for spec in observation.trainable_roster],
                      "original_trainable_roster_changed")
    training._require(observation.initial_adapter_sha256 == binding["initial_adapter_sha256"],
                      "original_initial_adapter_changed")
    return fingerprint


def run(options, *, libraries=None, clock=time.time):
    original_root, root = Path(options.original_run).resolve(), Path(options.output_dir).resolve()
    training._require(root != original_root and original_root not in root.parents,
                      "output_must_not_modify_original_run")
    root.mkdir(exist_ok=False)
    report = dict(status="INCOMPLETE", started_unix=clock(), arm="CLOSED", stage="D1",
                  original_run=str(original_root), expected_updates=256, baseline_model_calls=0,
                  comparison="EXTERNAL_PENDING", initialization="FRESH_MATCHED_INITIAL_NOT_D1_ADAPTER",
                  claim="EARLY_EXPLORATORY_COMPLETE_HISTORY_COMPARISON_NOT_CONDITIONAL_SALVAGE",
                  rng_topology="SINGLE_GPU_NOT_ORIGINAL_TWO_GPU_TOPOLOGY",
                  max_seconds=MAX_SECONDS, reserved_A40_hours=1.5,
                  limits="DEV controller only; no autonomous parenting, H1/H2, or exact dropout-mask claim.")
    trainer, hook = None, None
    train_export_attempted = False

    def check(stage):
        training._require(type(options.deadline_unix) in (int, float)
                          and math.isfinite(options.deadline_unix) and clock() < options.deadline_unix,
                          "finite_unexpired_deadline_required:" + stage)
        training._require(options.deadline_unix <= report["started_unix"] + MAX_SECONDS,
                          "maximum_5400_second_budget_exceeded")

    def progress(stage):
        check(stage)
        report["phase"] = stage
        print(json.dumps(dict(stage=stage, utc_unix=clock())), flush=True)

    def export_train():
        nonlocal train_export_attempted
        if train_export_attempted:
            return
        train_export_attempted = True
        write(root / "TRAIN.json", dict(
            kind="TRAINING_OBSERVATIONS_NOT_A_CHECKPOINT", arm="CLOSED", stage="D1",
            completed_updates=trainer.completed_updates if trainer is not None else 0,
            cursor=trainer.cursor if trainer is not None else 0,
            receipts=tokens.retain(trainer.receipts if trainer is not None else []),
            binding=tokens.retain(trainer.binding if trainer is not None else {}),
            lineage_failed=getattr(trainer, "_failed", None),
            limit="A failed update may be partially applied; observations are not resumable."))

    try:
        check("request")
        write(root / "REQUEST.json", vars(options))
        raw = (original_root / "REQUEST.json").read_bytes()
        request = json.loads(raw)
        report["original_request_sha256"] = sha256(raw).hexdigest()
        master = bytes.fromhex(request["master_hex"])
        identities = {request["atom_state_id"], request["base_state_id"], request["lineage_id"]}
        training._require(all(type(value) is str and value.strip() and value.isascii()
                              and "\0" not in value and value not in identities
                              for value in (options.closed_state_id, options.lineage_id)),
                          "distinct_closed_identity_required")
        training._require(type(options.gpu_uuid) is str and options.gpu_uuid.startswith("GPU-")
                          and "," not in options.gpu_uuid
                          and os.environ.get("CUDA_VISIBLE_DEVICES") == options.gpu_uuid,
                          "single_gpu_binding_required")
        training._require(options.gpu_uuid not in request["gpu_uuids"], "original_gpus_reserved_for_main")
        if libraries is None:
            import torch
            import peft
            import transformers
        else:
            torch, peft, transformers = libraries
        training._require(torch.__version__ == "2.13.0+cu130" and peft.__version__ == "0.20.0"
                          and transformers.__version__ == "5.5.3", "runtime_changed")
        training._require(not torch.cuda.is_initialized(), "exclusive_fresh_cpu_process_required")
        torch.set_num_threads(request["threads"])
        torch.set_num_interop_threads(request["interop_threads"])
        progress("original_checkpoint_binding_only")
        manifest = checkpoint_api.inspect_checkpoint(original_root / "D1")
        training._require(manifest["blob"]["sha256"] == options.checkpoint_sha256,
                          "original_checkpoint_blob_changed")
        original = recovery.load_exclusive(original_root / "D1", torch=torch)
        training._require(original["sha256"] == options.state_sha256 == manifest["state_sha256"],
                          "original_checkpoint_state_changed")
        report["original_state_sha256"] = original["sha256"]
        progress("existing_paired_curriculum")
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
        progress("fresh_initialization")
        base = transformers.AutoModelForCausalLM.from_pretrained(
            request["model_dir"], local_files_only=True, trust_remote_code=False,
            torch_dtype=torch.bfloat16, device_map=None, attn_implementation="sdpa", use_safetensors=True)
        initialized = models.initialize_atom_cpu(
            base, torch=torch, peft=peft, master=master, initial_directory=root / "initial",
            expected_base_sha256=request["base_state_sha256"], base_state_hash=_state_hash)
        report["paired_tape_sha256"] = validate_pairing(request, original, prepared, initialized, master=master)
        report["initial_adapter_sha256"] = initialized.observation.initial_adapter_sha256
        report["preparation_sha256"] = prepared.receipt_sha256
        del original
        held = prepare.prepare_reduced_held(bound_allocation=allocation)
        report["held_sha256"] = held.receipt_sha256
        progress("single_gpu_placement")
        torch.cuda.init()
        training._require(torch.cuda.device_count() == 1, "exactly_one_visible_gpu_required")
        initialized.model.to("cuda:0")
        report["base_pre"] = models.verify_retained_base(initialized, base_state_hash=_state_hash)
        hook = initialized.model.register_forward_pre_hook(lambda module, inputs: check("forward"))
        trainer = training.StatefulTrainer(
            initialized.model, arm="CLOSED", master=master, batches=prepared.batches,
            trainable_roster=initialized.observation.trainable_roster,
            layer_count=initialized.observation.layer_count, adapter_name="default",
            lineage_id=options.lineage_id, preparation_sha256=prepared.receipt_sha256,
            initial_adapter_sha256=initialized.observation.initial_adapter_sha256)
        progress("CLOSED_D1_train")
        trainer.train_stage("D1")
        export_train()
        training._require(trainer.completed_updates == 256 and trainer.cursor == 1024
                          and len(trainer.receipts) == 256, "exact_d1_256_updates_required")
        progress("full_checkpoint_before_readout")
        state = trainer.checkpoint()
        report["manifest"] = checkpoint_api.save_checkpoint(root / "D1", state)
        inspected = checkpoint_api.inspect_checkpoint(root / "D1")
        training._require(inspected == report["manifest"], "checkpoint_manifest_roundtrip_changed")
        loaded = recovery.load_exclusive(root / "D1", torch=torch)
        trainer._validate_checkpoint(loaded)
        training._require(loaded["sha256"] == state["sha256"] == inspected["state_sha256"]
                          and training._tree_hash(loaded) == training._tree_hash(state),
                          "full_checkpoint_roundtrip_changed")
        roster = initialized.observation.trainable_roster
        saved_adapter = _checkpoint_adapter_sha256(loaded, roster)
        training._require(training.adapter_sha256(initialized.model, roster) == saved_adapter,
                          "checkpoint_live_adapter_changed")
        report["state_sha256"], report["adapter_sha256"] = loaded["sha256"], saved_adapter
        del loaded, state

        class BoundedActor(actor_api.ReadoutActor):
            def count_context(self, prefix):
                check("readout_context")
                return super().count_context(prefix)

            def __call__(self, request):
                check("readout_call")
                return super().__call__(request)

        progress("CLOSED_D1_readout")
        actor = BoundedActor(model=initialized.model, tokenizer=tokenizer, torch=torch,
                             device="cuda:0", count_basis=prepare.COUNT_BASIS)
        sink = custody.ScreenCustodySink(root / "CLOSED", torch=torch)
        try:
            observed = runtime.run_reduced_state(
                state_id=options.closed_state_id, stage="D1", master=master,
                chains=held.chains, interventions=held.interventions, canaries=held.canaries,
                actor=actor, actor_calls=actor.calls, count_context=actor.count_context,
                counter_provenance=prepare.COUNT_BASIS, custody_sink=sink)
        finally:
            sink.close()
        report.update(terminal_reason=observed.terminal_reason, physical_calls=len(actor.calls),
                      failures=[dict(phase=fault.phase, error=str(fault.error)) for fault in observed.failures])
        report["adapter_post"] = training.adapter_sha256(initialized.model, roster)
        report["base_post"] = models.verify_retained_base(initialized, base_state_hash=_state_hash)
        training._require(report["adapter_post"] == saved_adapter, "readout_changed_adapter")
        training._require(observed.terminal_reason == "completed_unscored" and not observed.failures,
                          "incomplete_closed_readout")
        verification = custody.verify_receipt(root / "CLOSED")
        training._require((verification.state_id, verification.stage, verification.terminal_reason)
                          == (options.closed_state_id, "D1", "completed_unscored"), "closed_custody_mismatch")
        progress("CLOSED_D1_reduce")
        reduced = reducer._reduce_state(
            observed, options.closed_state_id, screen.reduced_decode_seeds("D1", master=master), set(),
            master=master, chains=held.chains, interventions=held.interventions, canaries=held.canaries)
        training._require(reduced.reportable, "nonreportable_closed:" + repr(reduced.issues))
        report.update(metrics=asdict(reduced.metrics), accounting=asdict(reduced.accounting),
                      closed_state_id=options.closed_state_id, lineage_id=options.lineage_id,
                      status="CLOSED_D1_COMPLETE_EXTERNAL_COMPARISON_PENDING", finished_unix=clock())
        check("result")
        write(root / "RESULT.json", report)
        return report
    except BaseException as error:
        report.update(status="FAILED", error_type=type(error).__name__, error=str(error), finished_unix=clock())
        try:
            export_train()
        except BaseException as export_error:
            report["train_export_error"] = str(export_error)
        write(root / "FAILED.json", report)
        raise
    finally:
        if hook is not None:
            hook.remove()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("original-run", "output-dir", "checkpoint-sha256", "state-sha256",
                 "gpu-uuid", "closed-state-id", "lineage-id"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--deadline-unix", required=True, type=float)
    return parser.parse_args(argv)


if __name__ == "__main__":
    run(parse_args())
