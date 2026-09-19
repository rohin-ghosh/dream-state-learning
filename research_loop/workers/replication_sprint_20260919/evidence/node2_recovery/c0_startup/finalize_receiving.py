"""Bind actual receiving CPU and Main publication receipts; no native dispatch."""

import argparse
import importlib
import json
import os
import re
import sys
import time
from pathlib import Path

import c0_startup as startup
from prepare_receiving import ADDITIONS, HERE, binding, file_sha, require, write


def finalize(cpu_receipt_path, publication_path):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_receiving_environment')
    control, source = Path(startup.CONTROL), Path(startup.STAGED_SOURCE)
    manifest = json.loads((control / 'STARTUP.json').read_bytes())
    delta = json.loads(startup.bound_bytes(manifest['source_delta']))
    config = json.loads((control / 'GUARD_CANDIDATE.json').read_bytes())
    cpu = json.loads(Path(cpu_receipt_path).read_bytes())
    require(cpu['schema'] == 'C0_STARTUP_CPU_TEST_RECEIPT_V1' and cpu['passed'] is True
        and cpu['returncode'] == 0 and cpu['receiving_source_root'] == str(source)
        and cpu['receiving_source_pins'] == config['source_pins']
        and cpu['runtime_additions'] == delta['additions']
        and cpu['originals_unchanged'] is True, 'actual_receiving_CPU_same_source')
    require(file_sha(cpu['output']['path']) == cpu['output']['sha256']
        and file_sha(cpu['synthetic_trace']['path']) == cpu['synthetic_trace']['sha256'],
        'receiving_CPU_trace_bytes')
    require(all(file_sha(HERE / name) == expected for name, expected in cpu['tested_source_files'].items()),
        'tested_bundle_bytes_unchanged')
    publication = json.loads(Path(publication_path).read_bytes())
    require(publication['builder_entry_pushed'] is True
        and re.fullmatch(r'[0-9a-f]{40}', publication['commit_sha'])
        and publication['runtime_additions'] == delta['additions'], 'Main_truthful_published_exact_source_receipt')
    actual = {str(path.relative_to(source)): file_sha(path) for path in source.rglob('*.py')}
    require(actual == config['source_pins'], 'actual_receiving_full_source_closure')
    allocation = dict(plan_sha256=config['plan_sha256'], cpu_tests_passed=True,
        gpu_uuid=json.loads((control / 'PLAN.json').read_bytes())['gpu_uuid'], physical=4,
        builder_entry_pushed=True, declared_unix=time.time(), receiving_cpu=binding(cpu_receipt_path),
        Main_publication=binding(publication_path), no_GPU_execution_by_finalizer=True)
    write(control / 'ALLOCATION.json', allocation)
    config['allocation_sha256'] = file_sha(control / 'ALLOCATION.json')
    startup.validate_guard_binding(config, manifest, (control / 'PLAN.json').read_bytes())
    write(control / 'GUARD.json', config)
    sys.path.insert(0, str(source))
    guard = importlib.import_module('gpu.orch_r125_continual_guard')
    require(Path(guard.__file__).resolve().is_relative_to(source), 'original_guard_from_receiving_source')
    guard.validate(control / 'GUARD.json')
    write(control / 'RECEIVING_CPU.json', dict(passed=True, source_pins=actual,
        tests=binding(cpu_receipt_path), Main_publication=binding(publication_path),
        privileged_admission_performed=False, GPU_or_native_started=False))
    print(json.dumps(dict(status='CPU_RECEIVING_BOUND_NOT_ADMITTED_OR_LAUNCHED', control=str(control))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cpu-receipt', type=Path, required=True)
    parser.add_argument('--publication-receipt', type=Path, required=True)
    arguments = parser.parse_args()
    finalize(arguments.cpu_receipt, arguments.publication_receipt)
