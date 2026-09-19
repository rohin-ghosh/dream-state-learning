"""Explicit CPU-only prefix tail probe; no proof production, admission or dispatch."""

import argparse
import contextlib
import json
import os
from pathlib import Path
import sys

import cpu_probe as original


def write_once(path, value):
    path = Path(path)
    content = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('xb') as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        if path.read_bytes() != content:
            raise ValueError('prefix_immutable_output_conflict')
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def probe(request, mode='tail'):
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU_only_prefix_probe_required')
    sys.path.insert(0, request['source'])
    from gpu import checkpoint_tail_runtime as reader
    from gpu import pair_prefix_authority as approval
    specification = request['selection']
    selection = specification['selection']
    approval.load_authority(request['prefix_authority'], request['plan'], request['source_pins'],
        life_binding_sha256=request['life_binding_sha256'], epoch_id=request['epoch_id'])
    if mode == 'prefix-admission':
        output = Path(specification['cpu_path'])
        control = Path(request['source']).parent / 'control'
        approval.require(output.is_absolute() and output.resolve() == output
            and output.is_relative_to(control / 'attempts'), 'own_receiving_attempt_CPU_output_only')
        guard = approval.selection_guard(request['prefix_authority'], request['plan'], request['source_pins'], selection)
        path = Path(request['source']).parent / 'control/prefix_guards' / (approval.digest(guard) + '.json')
        write_once(path, guard)
        binding = dict(schema='PAIR_PREFIX_SELECTION_BINDING_V1', authority=request['prefix_authority'],
            selection_guard=approval.reference(path), selection_sha256=approval.digest(selection))
        cpu = approval.derive_cpu_receipt(specification['cpu_parent'], request['prefix_authority'],
            request['plan'], request['source_pins'], selection, binding)
        write_once(specification['cpu_path'], cpu)
        return dict(prefix_binding=binding, cpu=approval.reference(specification['cpu_path']),
            admission_granted=False, checkpoint_tail_validated=False)
    from gpu.orch_r125_continual_guard import validate
    config, plan = validate(specification['guard_path'])
    approval.require(plan == request['plan'] and config['resume'] is True, 'actual_receiving_guard_and_plan')
    binding = specification['prefix_binding']
    argument = approval.verify_selection_binding(binding, request['prefix_authority'], request['plan'],
        request['source_pins'], selection)
    scan = reader.scan

    token = dict(life_binding_sha256=request['life_binding_sha256'], epoch_id=request['epoch_id'],
        new_source_pins=request['source_pins'], deadline_unix=plan['hard_end_unix'], receiver=dict(
            prefix_binding=binding, guard_path=specification['guard_path'],
            artifact_pins={specification['guard_path']: approval.reference(specification['guard_path'])['sha256']}))

    def selected_scan(journal, selected):
        approval.require(selected == selection, 'exact_selected_CPU_probe')
        with approval.admitted_prefix(config, plan, guard_path=specification['guard_path']):
            approval.require(approval.reader_argument(plan, token, selected) == argument, 'same_admitted_CPU_proof')
            admission = approval.admission_argument(plan, token, selected)
            return scan(journal, selected, prefix_proof=argument, prefix_admission=admission)

    reader.scan = selected_scan
    try:
        result = original.probe(request['source'], request['candidate'], request['plan'], 'tail', selection)
    finally:
        reader.scan = scan
    result['prefix_binding'] = binding
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prefix-admission', 'tail'))
    parser.add_argument('--request', required=True, type=Path)
    arguments = parser.parse_args()
    with contextlib.redirect_stdout(sys.stderr):
        result = probe(json.loads(arguments.request.read_bytes()), arguments.mode)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
