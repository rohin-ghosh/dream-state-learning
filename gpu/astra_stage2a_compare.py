"""CPU-only comparison of captured BASE D1 and explicitly staged fitted custody.

Only the fresh output file is written. No model, tokenizer, training, tensor
deserialization, qualification or launch path is invoked. FITTED is a neutral
comparison role: using the reducer's atom_local parameter does not establish
that the fitted method is ATOM_LOCAL. In particular CLOSED remains exploratory.
Original and fitted REQUEST metadata are retained separately, never merged or
used to infer an arm. Caller owns method attribution and exclusive input access.
"""

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path

from gpu import astra_stage2a_native_prepare as prepare
from gpu import astra_stage2a_replay_baseline as replay
from organism_v6 import composition_birth_stage2a_checkpoint as checkpoint
from organism_v6 import composition_birth_stage2a_screen_custody as custody
from organism_v6 import composition_birth_stage2a_screen_reduce as reducer
from organism_v6 import composition_birth_stage2a_screen_runtime as runtime


METRICS = ("skill_pairs", "typed_interventions", "whole_chains", "useful_reads", "typed_steps", "canaries")
REQUEST_LIMIT = 1024 * 1024


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _unique_fields(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate_request_field:" + key)
        result[key] = value
    return result


def _request(path, *, optional=False):
    descriptor = os.open(path.parent, checkpoint._directory_flags())
    try:
        try:
            size, digest, snapshot = checkpoint._read_file(descriptor, path.name, REQUEST_LIMIT, snapshot=True)
        except FileNotFoundError:
            if optional:
                return None
            raise
    finally:
        os.close(descriptor)
    values = json.loads(snapshot.getvalue(), object_pairs_hook=_unique_fields)
    _require(type(values) is dict, "request_object_required")
    checkpoint._json_bytes(values)
    return dict(path=str(path), size_bytes=size, sha256=digest, values=values)


def _custody_pin(directory):
    limits = custody.ReceiptLimits()
    descriptor = os.open(directory, checkpoint._directory_flags())
    try:
        names = []
        with os.scandir(descriptor) as entries:
            for entry in entries:
                names.append(entry.name)
                _require(len(names) <= custody.MAX_FILES, "receipt_file_limit_exceeded")
        rows = []
        total = 0
        for name in sorted(names):
            limit = limits.tensor_bytes if name.endswith(".pt") else limits.event_bytes
            size, digest, unused = checkpoint._read_file(descriptor, name, limit)
            total += size
            _require(total <= limits.total_bytes, "receipt_limit_exceeded")
            rows.append(dict(name=name, size_bytes=size, sha256=digest))
    finally:
        os.close(descriptor)
    return dict(path=str(directory), file_count=len(rows), size_bytes=total,
                tree_sha256=sha256(checkpoint._json_bytes(rows)).hexdigest(),
                complete_sha256=next((row["sha256"] for row in rows if row["name"] == "COMPLETE"), None))


def _slim(state):
    return dict(state_id=state.run.state_id, stage=state.run.stage,
                terminal_reason=state.run.terminal_reason, counter_provenance=state.run.counter_provenance,
                reportable=state.reportable, issues=list(state.issues), accounting=asdict(state.accounting),
                metrics=None if state.metrics is None else {
                    name: getattr(state.metrics, name) for name in METRICS})


def compare_captured(*, original_run, fitted_custody, fitted_state_id, stage):
    """Read-only report; explicit D1/D2 stage, original master/BASE/held bindings.

    Complete, exactly replayable custody is mandatory. Optional fitted-side
    REQUEST.json comes from fitted_custody's parent and is provenance only.
    No inference that matching an original state ID authenticates its method.
    Tree hashes cover canonical JSON of sorted name/size_bytes/sha256 rows.
    Recorded context counts are replayed without tokenizer authentication.
    """
    _require(type(stage) is str and stage in ("D1", "D2"), "explicit_D1_or_D2_stage_required")
    _require(reducer._identity(fitted_state_id), "explicit_fitted_state_identity_required")
    original_run = Path(original_run).absolute()
    fitted_custody = Path(fitted_custody).absolute()
    baseline = original_run / "BASE"
    original_request = _request(original_run / "REQUEST.json")
    fitted_request = _request(fitted_custody.parent / "REQUEST.json", optional=True)
    values = original_request["values"]
    _require(reducer._identity(values.get("base_state_id")), "original_base_state_identity_required")
    _require(values["base_state_id"] != fitted_state_id, "distinct_explicit_state_identities_required")
    master_hex = values.get("master_hex")
    _require(type(master_hex) is str and 0 < len(master_hex) <= 8192, "bounded_original_master_required")
    master = bytes.fromhex(master_hex)
    _require(0 < len(master) <= 4096, "bounded_original_master_required")
    paths = dict(BASE=baseline, FITTED=fitted_custody)
    before = {label: _custody_pin(path) for label, path in paths.items()}
    held = prepare.prepare_reduced_held(bound_allocation=prepare.allocate_source(master=master))
    base = replay.replay_state(baseline, state_id=values["base_state_id"], master=master, held=held)
    fitted = replay.replay_state(fitted_custody, state_id=fitted_state_id,
                                 master=master, held=held, stage=stage)
    reduce_state = reducer.reduce_base_d1 if stage == "D1" else reducer.reduce_base_d2
    reduced = reduce_state(base=base, atom_local=fitted, base_state_id=values["base_state_id"],
        atom_local_state_id=fitted_state_id, master=master,
        chains=held.chains, interventions=held.interventions, canaries=held.canaries)
    _require(before == {label: _custody_pin(path) for label, path in paths.items()},
             "custody_changed_during_comparison")
    _require(original_request == _request(original_run / "REQUEST.json")
             and fitted_request == _request(fitted_custody.parent / "REQUEST.json", optional=True),
             "request_changed_during_comparison")
    return dict(
        kind="CAPTURED_REDUCED_COMPARISON", fitted_stage=stage,
        reportable=reduced.reportable, criteria_passed=reduced.criteria_passed,
        criteria=[dict(asdict(item), passed=item.passed) for item in reduced.criteria],
        states=dict(BASE=_slim(reduced.base), FITTED=_slim(reduced.atom_local)),
        evidence=before,
        provenance=dict(original_request=original_request, fitted_request=fitted_request,
                        master_sha256=sha256(master).hexdigest(), held_receipt_sha256=held.receipt_sha256),
        code_sha256={name: sha256(Path(path).read_bytes()).hexdigest() for name, path in (
            ("compare", __file__), ("replay", replay.__file__), ("reducer", reducer.__file__),
            ("prepare", prepare.__file__), ("runtime", runtime.__file__), ("custody", custody.__file__))},
        limitations=[
            "FITTED is a comparison role, not an ATOM_LOCAL method assertion; CLOSED remains exploratory.",
            "Original and fitted REQUEST metadata are separate unauthenticated method provenance.",
            "Retained context counts only; no independent tokenizer, model, checkpoint or training verification.",
            "Custody hashes detect byte changes, not whole-bundle substitution; retain original evidence.",
            "Numerical criteria only; no scientific claim or continuation eligibility is established.",
        ])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-run", required=True, type=Path)
    parser.add_argument("--fitted-custody", required=True, type=Path)
    parser.add_argument("--fitted-state-id", required=True)
    parser.add_argument("--stage", required=True, choices=("D1", "D2"))
    parser.add_argument("--output", required=True, type=Path)
    options = parser.parse_args(argv)
    try:
        output = options.output.absolute()
        _require(not os.path.lexists(output), "fresh_output_required")
        _require(output.parent.is_dir(), "existing_output_parent_required")
        _require(not any(output.resolve().is_relative_to(path.resolve()) for path in (
            options.original_run / "BASE", options.fitted_custody)), "output_must_be_outside_custody")
        report = compare_captured(original_run=options.original_run, fitted_custody=options.fitted_custody,
                                 fitted_state_id=options.fitted_state_id, stage=options.stage)
        raw = checkpoint._json_bytes(report) + b"\n"
        with output.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except (ValueError, OSError, TypeError, KeyError) as error:
        parser.exit(2, f"captured comparison failed: {error}\n")
    print(json.dumps(dict(output=str(output), sha256=sha256(raw).hexdigest(),
        reportable=report["reportable"], criteria_passed=report["criteria_passed"],
        failed_criteria=[row["name"] for row in report["criteria"] if not row["passed"]]), sort_keys=True))
    return 0 if report["reportable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
