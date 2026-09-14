"""Explicit CPU initialization of a supplied base; not native admission.

The caller authenticates and loads the frozen Qwen base, qualifies source and
tokenization, pins the runtime, and owns process/device exclusivity. This module
loads no pretrained weights and makes no forward calls. It retains original
base tensor references before PEFT wrapping, exact initial adapter tensors and
CPU RNG states. A later CLOSED arm must copy this artifact, not reseed a fit.
"""

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import time

from organism_v6 import composition_birth_stage2a_initial_adapter as initial
from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_training as training


@dataclass(repr=False)
class InitializedAtom:
    model: object
    observation: object
    base_references: dict
    receipt: dict
    directory: Path


def _write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def _file_hash(path):
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def initialize_atom_cpu(base_model, *, torch, peft, master, initial_directory,
                        expected_base_sha256, base_state_hash):
    """Initialize once from CPU Kaiming-A/zero-B and retain failure evidence.

    base_state_hash must be the same reference-map hash used by the existing
    authenticated base-state receipt. Agreement is checked before wrapping and
    after initialization. It is not a substitute for file/runtime provenance.
    No CUDA context may exist; GPU initialization/seeds are later caller duties.
    """
    training._require(training._sha(expected_base_sha256), "explicit_base_digest_required")
    seed = primitives.adapter_seed(master)
    training._require(not torch.cuda.is_initialized(), "cpu_initialization_before_cuda_required")
    training._require(not hasattr(base_model, "peft_config"), "unwrapped_base_required")
    training._require(base_model.config.model_type == "qwen2", "qwen2_base_required")
    references = {name: value for name, value in base_model.named_parameters()}
    references.update(dict(base_model.named_buffers()))
    training._require(bool(references), "nonempty_base_required")
    training._require(all(value.device.type == "cpu" for value in references.values()),
                      "cpu_base_required")
    training._require(all(not value.is_floating_point() or value.dtype == torch.bfloat16
                          for value in references.values()), "exact_bfloat16_base_required")
    training._require(base_state_hash(references) == expected_base_sha256, "base_digest_mismatch")
    directory = Path(initial_directory)
    directory.mkdir(parents=False, exist_ok=False)
    receipt = dict(schema="ASTRA_STAGE2A_CPU_INITIALIZATION_V1", status="STARTED",
                   master_sha256=sha256(master).hexdigest(), seed=seed,
                   expected_base_sha256=expected_base_sha256,
                   started_unix=time.time(), cuda_initialized=False,
                   native_admission=False, fresh_process_persistence=False)
    _write(directory / "STARTED.json", receipt)
    try:
        base_model.requires_grad_(False)
        base_model.config.use_cache = False
        torch.manual_seed(seed)
        rng_before = torch.get_rng_state().clone()
        config = peft.LoraConfig(
            r=8, lora_alpha=16, lora_dropout=0.05,
            target_modules=list(training.TARGET_MODULES), bias="none",
            task_type="CAUSAL_LM", init_lora_weights=True,
            use_rslora=False, use_dora=False,
        )
        model = peft.get_peft_model(base_model, config, adapter_name="default",
                                    autocast_adapter_dtype=True)
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        rng_after = torch.get_rng_state().clone()
        observation = initial.inspect_initial_adapter(
            model, torch=torch, layer_count=model.config.num_hidden_layers,
            adapter_name="default")
        training._require(base_state_hash(references) == expected_base_sha256,
                          "base_changed_during_initialization")
        named = dict(model.named_parameters())
        tensors = {spec.name: named[spec.name].detach().cpu().clone()
                   for spec in observation.trainable_roster}
        payload = dict(adapter=tensors, rng_before=rng_before, rng_after=rng_after, seed=seed)
        with (directory / "initial_state.pt").open("xb") as stream:
            torch.save(payload, stream)
        loaded = torch.load(directory / "initial_state.pt", weights_only=True, map_location="cpu")
        training._require(training._tree_hash(loaded) == training._tree_hash(payload),
                          "initial_artifact_roundtrip_changed_bytes")
        receipt.update(status="INITIALIZED_CPU_ONLY", finished_unix=time.time(),
                       observation=asdict(observation), torch_version=str(torch.__version__),
                       base_state_sha256=base_state_hash(references),
                       state_file_sha256=_file_hash(directory / "initial_state.pt"),
                       rng_before_sha256=training.tensor_sha256(rng_before),
                       rng_after_sha256=training.tensor_sha256(rng_after),
                       gradient_checkpointing_use_reentrant=False,
                       initialized_arms=["ATOM_LOCAL"], closed_copy_executed=False)
        _write(directory / "receipt.json", receipt)
        return InitializedAtom(model, observation, references, receipt, directory)
    except BaseException as error:
        _write(directory / "FAILED.json", dict(receipt, status="FAILED",
                                               error_type=type(error).__name__, error=str(error),
                                               finished_unix=time.time()))
        raise


def verify_retained_base(initialized, *, base_state_hash):
    """Rehash original tensor references, including after PEFT name rewriting."""
    actual = base_state_hash(initialized.base_references)
    training._require(actual == initialized.receipt["expected_base_sha256"],
                      "retained_frozen_base_changed")
    return actual
