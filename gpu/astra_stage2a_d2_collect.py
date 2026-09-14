"""Fresh training collection with a frozen saved DEV controller, not clean birth."""

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from gpu import astra_stage2a_native_models as models
from gpu import astra_stage2a_outcome_collect as collector
from gpu import astra_stage2a_recover_readout as readout
from gpu import astra_stage2a_recovery_load as recovery
from organism_v6 import composition_birth_stage2a_checkpoint as checkpoint_api
from organism_v6 import composition_birth_stage2a_training as training
from organism_v6.pcfl_vertical_train import _state_hash


MASTER = b"ASTRA-OUTCOME-COLLECT-TRAIN-20260914-A3"
D2_STATE = "2ce34dced3b9c55335d4bdf195b870ecdef69a2bc94de641cb1ccbf151aee2bf"
D2_ADAPTER = "5e96317f732aed604691d93f98c02f21dbb0621501381d416f552fe7694bb394"


def validate_source(state, request):
    collector.require(state["sha256"] == D2_STATE and state["completed_updates"] == 512
                      and state["cursor"] == 2048 and len(state["receipts"]) == 512,
                      "exact_saved_D2_required")
    collector.require(state["binding"]["lineage_id"] == request["lineage_id"]
                      and state["binding"]["arm"] == "ATOM_LOCAL", "D2_source_lineage_mismatch")
    original_master = bytes.fromhex(request["master_hex"])
    collector.require(original_master != MASTER, "fresh_collection_master_required")
    return original_master


def make_factory(options):
    def factory(base, root, check):
        import peft
        import torch

        check("D2_checkpoint_load")
        collector.require(peft.__version__ == collector.tokens.RUNTIME_VERSIONS["peft"], "peft_runtime_changed")
        checkpoint_dir = Path(options.checkpoint)
        manifest = checkpoint_api.inspect_checkpoint(checkpoint_dir)
        state = recovery.load_exclusive(checkpoint_dir, torch=torch)
        request_raw = Path(options.original_request).read_bytes()
        request = json.loads(request_raw)
        original_master = validate_source(state, request)
        collector.require(request["base_state_sha256"] == options.expected_base_sha256, "D2_base_pin_changed")
        initialized = models.initialize_atom_cpu(base, torch=torch, peft=peft, master=original_master,
            initial_directory=root / "initial", expected_base_sha256=options.expected_base_sha256,
            base_state_hash=_state_hash)
        collector.require(initialized.observation.initial_adapter_sha256 == state["binding"]["initial_adapter_sha256"],
                          "initial_lineage_changed")
        adapter_hash = readout.restore_adapter(initialized, state, torch=torch)
        collector.require(adapter_hash == D2_ADAPTER, "D2_adapter_changed")
        receipt = dict(kind="FROZEN_DEV_D2_CONTROLLER_NOT_AUTHENTIC_BIRTH", new_updates=0,
            checkpoint_path=str(checkpoint_dir), checkpoint_manifest=manifest,
            checkpoint_state_sha256=state["sha256"], adapter_sha256=adapter_hash,
            original_request_sha256=sha256(request_raw).hexdigest(),
            original_master_sha256=sha256(original_master).hexdigest(),
            roster=[asdict(spec) for spec in initialized.observation.trainable_roster])
        collector.write_json(root / "LEARNER.json", receipt)

        def verify():
            collector.require(training.adapter_sha256(initialized.model, initialized.observation.trainable_roster)
                              == adapter_hash, "collection_changed_D2_adapter")
            return models.verify_retained_base(initialized, base_state_hash=_state_hash)

        return initialized.model, receipt, verify

    return factory


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("model-dir", "output", "gpu-uuid", "expected-base-sha256", "checkpoint", "original-request"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--deadline-unix", type=float, required=True)
    options = parser.parse_args(argv)
    collector.MASTER = MASTER
    collector.run(options, learner_factory=make_factory(options))


if __name__ == "__main__":
    main()
