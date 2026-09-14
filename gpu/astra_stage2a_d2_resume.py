"""Source-only, caller-invoked D1 full-state continuation; never launch authority.

Non-material glue preserving the prospective protocol: Main alone adjudicates
actual D1 criteria before calling. Acquisition or autonomous-chain shortfalls
with finite loss, intact custody and canaries may justify continuation; an
arbitrary numerical miss (notably BASE-ceiling/gain-only) does not. No automatic
eligibility, qualification, promotion, retry, BASE readout or changed seed rule.

The existing restore interface is StatefulTrainer(..., checkpoint=...), not a
restore() method. Callers provide an initialized matching native ATOM model,
its actor, all constructor options and the expected D1 binding/hash. No model,
tokenizer, device or batch loader is constructed here. Imports perform no I/O
or torch import. Explicit invocation uses existing local checkpoint/custody I/O.

This is same-process restore/readout evidence only, NOT fresh-process persistence
qualification. Main retains responsibility for provenance and scientific gates.
Callers exclusively own the model, actor, options, held bindings and paths during
the call. Failures retain original exceptions, live trainer/screens and partial
files; process death is outside this boundary. Never overwrite failed attempts.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass
from hashlib import sha256
import os

from gpu.astra_stage2a_reduced_conductor import (
    ConductorFailure, ReducedConductorRun, _checkpoint_adapter_sha256, _require,
)
from organism_v6 import composition_birth_stage2a_checkpoint as checkpoint_api
from organism_v6 import composition_birth_stage2a_screen as screen
from organism_v6 import composition_birth_stage2a_screen_custody as custody
from organism_v6 import composition_birth_stage2a_screen_runtime as runtime
from organism_v6 import composition_birth_stage2a_training as training


STATUS = "SOURCE_ONLY_D2_RESUME"
REMAINING_SEAMS = (
    "reduce_base_d1 accepts only D1 live ScreenRuns, not D2 slots/seeds; "
    "stage-aware reduction against the prior bound BASE remains external.",
    "Persisted BASE receipt verification does not reconstruct a reducer-compatible "
    "live ScreenRun. Retain the original BASE evidence; do not rerun or relabel it.",
)


@dataclass(repr=False)
class D2ResumeRun(ReducedConductorRun):
    trainer: object = None
    d1_manifest: object = None
    d1_checkpoint: object = None
    restored_checkpoint: object = None
    remaining_seams: tuple = REMAINING_SEAMS
    status: str = STATUS


def run_d2_resume(*, model, atom_local_actor, trainer_options, trainer_binding,
                  d1_checkpoint_dir, d1_checkpoint_sha256, checkpoint_dir,
                  atom_custody_dir, atom_local_state_id, base_state_id,
                  base_evidence, master, chains, interventions, canaries,
                  counter_provenance, torch=None):
    """Restore once, train D2 once (updates 257..512), save, read out once.

    trainer_options are the existing StatefulTrainer constructor keyword args,
    excluding model/checkpoint; their master must match the readout master.
    trainer_binding and d1_checkpoint_sha256 come from Main's saved D1 evidence,
    not from an unverified manifest. The native constructor validates complete
    optimizer, RNG, receipts, roster, recipe and lineage before restoring them.

    The readout reserves the existing D2 280-slot subset with its existing seed
    mapping (unused chain slots are not forced calls). BASE evidence is retained
    opaquely, never replayed through a native actor or reconstructed. The current
    reducer cannot accept D2; reduction stays None and remaining_seams explains
    why. completed_unreduced is NOT an eligibility or scientific pass decision.
    torch is forwarded only to the custody sink, as in the reduced conductor.
    """
    result = D2ResumeRun(inputs=dict(
        model=model, atom_local_actor=atom_local_actor, trainer_options=trainer_options,
        trainer_binding=trainer_binding, d1_checkpoint_dir=d1_checkpoint_dir,
        d1_checkpoint_sha256=d1_checkpoint_sha256, checkpoint_dir=checkpoint_dir,
        atom_custody_dir=atom_custody_dir, atom_local_state_id=atom_local_state_id,
        base_state_id=base_state_id, base_evidence=base_evidence, master=master,
        chains=chains, interventions=interventions, canaries=canaries,
        counter_provenance=counter_provenance, torch=torch,
    ))
    phase, sink = "bindings", None
    try:
        _require(all(type(value) is str and value.strip() and value.isascii() and "\0" not in value
                     for value in (base_state_id, atom_local_state_id))
                 and base_state_id != atom_local_state_id, "distinct_explicit_state_identities_required")
        _require(atom_local_actor.model is model and callable(atom_local_actor)
                 and callable(atom_local_actor.count_context) and type(atom_local_actor.calls) is list,
                 "matching_prepared_actor_required")
        options = dict(trainer_options)
        _require(not {"model", "checkpoint"}.intersection(options)
                 and options["arm"] == "ATOM_LOCAL" and options["master"] == master,
                 "atom_restore_options_or_master_mismatch")
        expected_binding = deepcopy(trainer_binding)
        _require(expected_binding["arm"] == "ATOM_LOCAL" and training._sha(d1_checkpoint_sha256),
                 "bound_atom_d1_checkpoint_required")
        chains, interventions, canaries = runtime._bindings(
            screen.reduced_screen("D2"), chains, interventions, canaries)
        _require(type(counter_provenance) is str and counter_provenance.strip(),
                 "explicit_counter_provenance_required")
        paths = tuple(checkpoint_api._path(path) for path in
                      (d1_checkpoint_dir, checkpoint_dir, atom_custody_dir))
        resolved = tuple(os.path.realpath(path) for path in paths)
        _require(len(set(resolved)) == 3 and all(
            os.path.commonpath((left, right)) not in (left, right)
            for index, left in enumerate(resolved) for right in resolved[index + 1:]),
            "distinct_non_nested_artifact_paths_required")
        _require(all(not os.path.lexists(path) and os.path.isdir(os.path.dirname(path))
                     for path in paths[1:]), "fresh_artifact_directories_with_existing_parents_required")

        phase = "load_D1"
        result.d1_manifest = checkpoint_api.inspect_checkpoint(paths[0])
        result.d1_checkpoint = checkpoint_api.load_checkpoint(paths[0])
        state = result.d1_checkpoint
        _require(state["sha256"] == d1_checkpoint_sha256 == result.d1_manifest["state_sha256"]
                 and state["binding"] == expected_binding
                 and (state["completed_updates"], state["cursor"]) == (256, 1024),
                 "checkpoint_d1_binding_mismatch")

        phase = "restore_D1"
        result.trainer = training.StatefulTrainer(model, checkpoint=state, **options)
        trainer = result.trainer
        roster = tuple(trainer.roster)
        _require([asdict(spec) for spec in roster] == expected_binding["roster"],
                 "trainer_roster_binding_mismatch")

        def check_live_binding(completed):
            _require(trainer.model is model and atom_local_actor.model is model
                     and trainer.binding == expected_binding and trainer.arm == "ATOM_LOCAL"
                     and trainer.batches is options["batches"] and tuple(trainer.roster) == roster
                     and (trainer.completed_updates, trainer.cursor) == (completed, completed * 4),
                     "live_trainer_binding_or_boundary_changed")

        check_live_binding(256)
        result.restored_checkpoint = trainer.checkpoint()
        _require(result.restored_checkpoint["sha256"] == d1_checkpoint_sha256,
                 "full_state_restore_boundary_mismatch")
        result.hashes["d1_checkpoint"] = d1_checkpoint_sha256
        result.hashes["d1_adapter"] = _checkpoint_adapter_sha256(state, roster)
        _require(training.adapter_sha256(model, roster) == result.hashes["d1_adapter"],
                 "restored_live_adapter_mismatch")

        phase = "train_D2"
        result.training_receipts = trainer.train_stage("D2")
        check_live_binding(512)
        _require(len(result.training_receipts) == 256 and len(trainer.receipts) == 512,
                 "exact_d2_update_receipts_required")

        phase = "checkpoint_D2"
        result.checkpoint = trainer.checkpoint()
        state = result.checkpoint
        _require(state["binding"] == expected_binding
                 and (state["completed_updates"], state["cursor"]) == (512, 2048),
                 "checkpoint_d2_binding_mismatch")
        adapter_hash = _checkpoint_adapter_sha256(state, roster)
        result.hashes["d2_adapter"] = adapter_hash
        _require(training.adapter_sha256(model, roster) == adapter_hash, "checkpoint_live_adapter_mismatch")
        result.saved_manifest = checkpoint_api.save_checkpoint(paths[1], state)
        result.inspected_manifest = checkpoint_api.inspect_checkpoint(paths[1])
        _require(result.saved_manifest == result.inspected_manifest, "checkpoint_manifest_roundtrip_mismatch")
        result.loaded_checkpoint = checkpoint_api.load_checkpoint(paths[1])
        loaded = result.loaded_checkpoint
        _require(loaded["sha256"] == state["sha256"] == result.inspected_manifest["state_sha256"]
                 and loaded["binding"] == expected_binding
                 and (loaded["completed_updates"], loaded["cursor"]) == (512, 2048)
                 and result.inspected_manifest["binding_sha256"]
                 == sha256(checkpoint_api._json_bytes(expected_binding)).hexdigest(),
                 "full_checkpoint_roundtrip_binding_mismatch")
        _require(_checkpoint_adapter_sha256(loaded, roster) == adapter_hash,
                 "checkpoint_adapter_roundtrip_mismatch")
        result.hashes["d2_checkpoint"] = loaded["sha256"]

        phase = "ATOM_LOCAL_D2"
        check_live_binding(512)
        _require(training.adapter_sha256(model, roster) == adapter_hash, "adapter_changed_before_readout")
        sink = custody.ScreenCustodySink(paths[2], torch=torch)
        result.sinks["ATOM_LOCAL"] = sink
        run = runtime.run_reduced_state(
            stage="D2", state_id=atom_local_state_id, master=master, chains=chains,
            interventions=interventions, canaries=canaries, actor=atom_local_actor,
            actor_calls=atom_local_actor.calls, count_context=atom_local_actor.count_context,
            counter_provenance=counter_provenance, custody_sink=sink,
        )
        result.screens["ATOM_LOCAL"] = run
        result.failures.extend(ConductorFailure(phase + "." + fault.phase, fault.error)
                               for fault in run.failures)
        check_live_binding(512)
        _require(training.adapter_sha256(model, roster) == adapter_hash, "adapter_changed_during_readout")
        result.receipts["ATOM_LOCAL"] = receipt = custody.verify_receipt(paths[2])
        _require((run.state_id, run.stage, len(run.reservations)) == (atom_local_state_id, "D2", 280)
                 and (receipt.state_id, receipt.stage, receipt.terminal_reason)
                 == (atom_local_state_id, "D2", run.terminal_reason), "receipt_live_run_binding_mismatch")
        _require(run.terminal_reason == "completed_unscored" and not run.failures,
                 "infrastructure_incomplete_screen")
        result.terminal_reason = "completed_unreduced"
    except BaseException as error:
        result.failures.append(ConductorFailure(phase, error))
        result.terminal_reason = "aborted"
    finally:
        if sink is not None:
            try:
                sink.close()
            except BaseException as error:
                result.failures.append(ConductorFailure("ATOM_LOCAL_D2.close", error))
                result.terminal_reason = "aborted"
    return result
