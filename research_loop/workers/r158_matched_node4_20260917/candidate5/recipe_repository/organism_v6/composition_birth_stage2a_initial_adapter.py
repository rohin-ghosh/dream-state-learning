"""Non-material, source-only initial-adapter observation, not preparation.

The caller supplies an already constructed CPU model and the installed torch
dependency used by training. No loading, initialization, forward, placement,
mode/config/tensor/RNG mutation, files or network operations occur. The caller
must exclude concurrent model changes during inspection and trainer handoff.
Hash agreement cannot establish authentication or native preparation readiness.
"""

from dataclasses import dataclass

from organism_v6 import composition_birth_stage2a_training as training


STATUS = training.STATUS
SCIENCE_GATES = training.SCIENCE_GATES
OUTSIDE_VERIFICATION = (
    "Kaiming-A sampling provenance and distribution",
    "actual adapter-init seed, RNG history and initialization/copy history",
    "authentication of model, tokenizer, revision, runtime or caller-provided hashes",
    "full native preparation, route/core semantics, execution readiness and science claims",
)


@dataclass(frozen=True)
class InitialAdapterObservation:
    trainable_roster: tuple[training.ParameterSpec, ...]
    initial_adapter_sha256: str
    layer_count: int
    adapter_name: str
    initialization_observations: tuple[str, ...] = (
        "trainer-validated default Kaiming-A/zero-B policy metadata",
        "finite A and B values; every A tensor nonzero; every B tensor zero",
    )
    outside_verification: tuple[str, ...] = OUTSIDE_VERIFICATION


def inspect_initial_adapter(model, *, torch, layer_count, adapter_name,
                            expected_initial_adapter_sha256=None):
    """Derive trainer-ordered specs and hash exact fp32/bf16 initial storage.

    Feed result.trainable_roster and result.initial_adapter_sha256 directly to
    StatefulTrainer, retaining layer_count/adapter_name and supplying the plan,
    arm, lineage and preparation binding separately. This does not create or
    authenticate those caller bindings. An optional expected digest checks only
    byte agreement with another observed/saved initialization.

    Required trainer metadata must be present and valid; missing metadata is
    rejected rather than inferred. Default-policy metadata is not proof that
    Kaiming sampling occurred. Nonzero finite A/zero B does not prove history.
    No tensor references are returned and no storage dtype is cast or promoted.
    """
    training._require(expected_initial_adapter_sha256 is None
                      or training._sha(expected_initial_adapter_sha256),
                      "invalid_expected_initial_adapter_sha256")
    named = tuple(model.named_parameters())
    for name, value in named + tuple(model.named_buffers()):
        training._require(isinstance(value, torch.Tensor) and value.device.type == "cpu",
                          "cpu_tensor_required:" + name)
    roster = tuple(training.ParameterSpec(name, tuple(value.shape), str(value.dtype))
                   for name, value in named if value.requires_grad)
    training.validate_trainable_roster(roster, layer_count=layer_count, adapter_name=adapter_name)
    training._require(training._torch() is torch, "training_torch_dependency_mismatch")
    selected, _ = training._validate_model(model, roster, layer_count, adapter_name)
    for name, value in selected:
        if ".lora_B." in name:
            training._require(bool((value == 0).all()), "nonzero_initial_lora_B:" + name)
        else:
            training._require(bool((value != 0).any()), "zero_initial_lora_A:" + name)
    digest = training.adapter_sha256(model, roster)
    training._require(expected_initial_adapter_sha256 is None or digest == expected_initial_adapter_sha256,
                      "initial_adapter_bytes_differ_from_caller_binding")
    return InitialAdapterObservation(roster, digest, layer_count, adapter_name)
