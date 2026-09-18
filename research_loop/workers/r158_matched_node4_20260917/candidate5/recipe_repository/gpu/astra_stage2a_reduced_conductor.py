"""Source-only BASE -> ATOM_LOCAL D1 -> reduced-criteria orchestration.

This non-material glue grants no source/native/device/model/provenance/deadline
authorization. Main owns those gates, real launches, roots and admission. There
is no CLI, preparation, loader, new trainer/scorer, D2, CLOSED fit or retry.
Importing this module does not import torch or execute any collaborator.

Only explicitly calling run_reduced_conductor invokes the caller's already
prepared actors/trainer and existing storage APIs. Callers must own exclusive
access to models (including storage aliases), bindings and fresh local paths.
State IDs and hashes bind this attempt, not authenticity or launch permission.
The same-process checkpoint roundtrip and live-adapter checks are NOT evidence
of fresh-process persistence. Main owns the later separate native load/eval
wrapper and any persistence promotion; this module adds no RPC or model loader.
The trainer_binding argument is the caller's expected existing trainer.binding
dictionary, not a new provenance schema or a collection of native green flags.

Every failure, including interruption, is returned with original exceptions,
live screens, actors, trainer and partial storage evidence. No files are removed
or overwritten. Retain the result even on failure: serialized error diagnostics
are not the original exception objects. Process death is outside this boundary.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import os

from organism_v6 import composition_birth_stage2a_checkpoint as checkpoint_api
from organism_v6 import composition_birth_stage2a_screen_custody as custody
from organism_v6 import composition_birth_stage2a_screen_reduce as reducer
from organism_v6 import composition_birth_stage2a_screen_runtime as runtime
from organism_v6 import composition_birth_stage2a_training as training


STATUS = "SOURCE_ONLY_REDUCED_CONDUCTOR"


@dataclass(frozen=True)
class ConductorFailure:
    phase: str
    error: BaseException


@dataclass(repr=False)
class ReducedConductorRun:
    """Attempt evidence, never a scientific admission decision."""

    inputs: dict
    screens: dict = field(default_factory=dict)
    sinks: dict = field(default_factory=dict)
    receipts: dict = field(default_factory=dict)
    training_receipts: object = None
    checkpoint: object = None
    saved_manifest: object = None
    inspected_manifest: object = None
    loaded_checkpoint: object = None
    hashes: dict = field(default_factory=dict)
    reduction: object = None
    failures: list = field(default_factory=list)
    terminal_reason: str = "incomplete"
    status: str = STATUS


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _checkpoint_adapter_sha256(state, roster):
    _require(set(state["adapter"]) == {spec.name for spec in roster},
             "checkpoint_adapter_roster_mismatch")
    return training._digest([(spec.name, training.tensor_sha256(state["adapter"][spec.name]))
                             for spec in roster])


def run_reduced_conductor(*, base_state_id, atom_local_state_id, base_actor,
                          atom_local_actor, trainer, trainer_binding, batches,
                          master, chains, interventions, canaries,
                          counter_provenance, base_custody_dir, atom_custody_dir,
                          checkpoint_dir, torch=None):
    """Join prepared interfaces once; return numerical criteria to Main.

    Both readouts reserve the existing 280 D1 slots (not 280 forced calls).
    Only infrastructure/binding/custody faults stop progression; BASE performance
    is not a veto. train_stage('D1') is called exactly once after BASE custody.
    Full checkpoint save/inspect/load precedes ATOM readout; loading verifies a
    same-process CPU storage roundtrip, not restoration into another model or
    fresh-process/native reload evidence. Returned artifacts can bind Main's
    later wrapper; they do not promote a persistence claim.
    torch is forwarded only to ScreenCustodySink; checkpoint I/O owns its usual
    lazy torch import. This function must not be called natively without Main's
    separate authorization. Tests use only bounded fakes/mocks.
    """
    result = ReducedConductorRun(inputs=dict(
        base_state_id=base_state_id, atom_local_state_id=atom_local_state_id,
        base_actor=base_actor, atom_local_actor=atom_local_actor, trainer=trainer,
        trainer_binding=trainer_binding, batches=batches, master=master,
        chains=chains, interventions=interventions, canaries=canaries,
        counter_provenance=counter_provenance, base_custody_dir=base_custody_dir,
        atom_custody_dir=atom_custody_dir, checkpoint_dir=checkpoint_dir, torch=torch,
    ))
    phase = "bindings"
    try:
        _require(all(type(value) is str and value.strip() and value.isascii() and "\0" not in value
                     for value in (base_state_id, atom_local_state_id))
                 and base_state_id != atom_local_state_id, "distinct_state_ids_required")
        _require(base_actor is not atom_local_actor and base_actor.model is not atom_local_actor.model
                 and base_actor.calls is not atom_local_actor.calls, "distinct_actor_states_required")
        _require(trainer.model is atom_local_actor.model, "atom_actor_trainer_model_mismatch")
        _require(all(callable(actor) and callable(actor.count_context) and type(actor.calls) is list
                     for actor in (base_actor, atom_local_actor)), "prepared_actor_interfaces_required")
        _require(trainer.arm == "ATOM_LOCAL" and type(trainer.completed_updates) is int
                 and trainer.completed_updates == 0, "fresh_atom_local_trainer_required")
        expected_binding = deepcopy(trainer_binding)
        _require(trainer.binding == expected_binding and expected_binding["arm"] == "ATOM_LOCAL",
                 "trainer_binding_mismatch")
        _require(trainer.batches is batches, "prepared_batch_identity_mismatch")
        _require(training.validate_batches(batches, master=master) == expected_binding["batches_sha256"],
                 "prepared_batch_master_binding_mismatch")
        roster = tuple(trainer.roster)
        _require([asdict(spec) for spec in roster] == expected_binding["roster"],
                 "trainer_roster_binding_mismatch")
        model = trainer.model
        baseline_model = base_actor.model
        paths = tuple(checkpoint_api._path(path) for path in
                      (base_custody_dir, atom_custody_dir, checkpoint_dir))
        resolved = tuple(os.path.realpath(path) for path in paths)
        _require(len(set(resolved)) == 3 and all(
            os.path.commonpath((left, right)) not in (left, right)
            for index, left in enumerate(resolved) for right in resolved[index + 1:]),
            "distinct_non_nested_artifact_paths_required")
        _require(all(not os.path.lexists(path) and os.path.isdir(os.path.dirname(path)) for path in paths),
                 "fresh_artifact_directories_with_existing_parents_required")

        def check_live_binding():
            _require(trainer.model is model and atom_local_actor.model is model
                     and base_actor.model is baseline_model, "live_model_identity_changed")
            _require(trainer.binding == expected_binding and trainer.batches is batches
                     and tuple(trainer.roster) == roster and trainer.arm == "ATOM_LOCAL",
                     "live_trainer_binding_changed")

        def readout(label, state_id, actor, directory, expected_hash):
            sink = None
            try:
                check_live_binding()
                result.hashes[label + "_atom_before"] = training.adapter_sha256(model, roster)
                _require(result.hashes[label + "_atom_before"] == expected_hash,
                         "adapter_changed_before_readout")
                sink = custody.ScreenCustodySink(directory, torch=torch)
                result.sinks[label] = sink
                run = runtime.run_reduced_state(
                    stage="D1", state_id=state_id, master=master, chains=chains,
                    interventions=interventions, canaries=canaries, actor=actor,
                    actor_calls=actor.calls, count_context=actor.count_context,
                    counter_provenance=counter_provenance, custody_sink=sink,
                )
                result.screens[label] = run
                result.failures.extend(ConductorFailure(label + "." + fault.phase, fault.error)
                                       for fault in run.failures)
                check_live_binding()
                result.hashes[label + "_atom_after"] = training.adapter_sha256(model, roster)
                _require(result.hashes[label + "_atom_after"] == expected_hash,
                         "adapter_changed_during_readout")
                receipt = custody.verify_receipt(directory)
                result.receipts[label] = receipt
                _require((run.state_id, run.stage, len(run.reservations)) == (state_id, "D1", 280),
                         "screen_identity_or_reservation_mismatch")
                _require((receipt.state_id, receipt.stage, receipt.terminal_reason)
                         == (state_id, "D1", run.terminal_reason), "receipt_live_run_binding_mismatch")
                _require(run.terminal_reason == "completed_unscored" and not run.failures,
                         "infrastructure_incomplete_screen")
            except BaseException as error:
                result.failures.append(ConductorFailure(label, error))
            finally:
                if sink is not None:
                    try:
                        sink.close()
                    except BaseException as error:
                        result.failures.append(ConductorFailure(label + ".close", error))

        phase = "BASE"
        initial_hash = training.adapter_sha256(model, roster)
        result.hashes["initial_atom_adapter"] = initial_hash
        _require(initial_hash == expected_binding["initial_adapter_sha256"],
                 "initial_adapter_binding_mismatch")
        readout("BASE", base_state_id, base_actor, paths[0], initial_hash)
        if result.failures:
            result.terminal_reason = "aborted"
            return result

        phase = "D1_train"
        check_live_binding()
        result.training_receipts = trainer.train_stage("D1")
        _require(type(trainer.completed_updates) is int and trainer.completed_updates == 256
                 and trainer.cursor == 1024 and len(result.training_receipts) == 256,
                 "exact_d1_256_updates_required")
        check_live_binding()
        phase = "D1_checkpoint"
        result.checkpoint = trainer.checkpoint()
        state = result.checkpoint
        _require(state["binding"] == expected_binding and state["completed_updates"] == 256
                 and state["cursor"] == 1024, "checkpoint_d1_binding_mismatch")
        saved_adapter_hash = _checkpoint_adapter_sha256(state, roster)
        result.hashes["d1_adapter"] = saved_adapter_hash
        _require(training.adapter_sha256(model, roster) == saved_adapter_hash,
                 "checkpoint_live_adapter_mismatch")
        result.saved_manifest = checkpoint_api.save_checkpoint(paths[2], state)
        result.inspected_manifest = checkpoint_api.inspect_checkpoint(paths[2])
        _require(result.saved_manifest == result.inspected_manifest, "checkpoint_manifest_roundtrip_mismatch")
        result.loaded_checkpoint = checkpoint_api.load_checkpoint(paths[2])
        loaded = result.loaded_checkpoint
        _require(loaded["sha256"] == state["sha256"] == result.inspected_manifest["state_sha256"]
                 and loaded["binding"] == expected_binding and loaded["completed_updates"] == 256
                 and loaded["cursor"] == 1024
                 and result.inspected_manifest["binding_sha256"]
                 == sha256(checkpoint_api._json_bytes(expected_binding)).hexdigest(),
                 "full_checkpoint_roundtrip_binding_mismatch")
        _require(_checkpoint_adapter_sha256(loaded, roster) == saved_adapter_hash,
                 "checkpoint_adapter_roundtrip_mismatch")
        result.hashes["d1_checkpoint"] = loaded["sha256"]

        phase = "ATOM_LOCAL"
        readout("ATOM_LOCAL", atom_local_state_id, atom_local_actor, paths[1], saved_adapter_hash)
        if result.failures:
            result.terminal_reason = "aborted"
            return result
        phase = "reduce"
        result.reduction = reducer.reduce_base_d1(
            base=result.screens["BASE"], atom_local=result.screens["ATOM_LOCAL"],
            base_state_id=base_state_id, atom_local_state_id=atom_local_state_id,
            master=master, chains=chains, interventions=interventions, canaries=canaries,
        )
        result.terminal_reason = "reduced"
    except BaseException as error:
        result.failures.append(ConductorFailure(phase, error))
        result.terminal_reason = "aborted"
    return result
