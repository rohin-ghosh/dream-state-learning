"""CPU-only source-closure validation before publishing distinct route READY_V2."""

import argparse
import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as xml

from gpu import orch_r111_route_boundary as boundary
from gpu import orch_r111_route_shared_ready as ready


TESTS = (
    'tests/test_orch_r111_route_pair.py',
    'tests/test_orch_r111_route_v4.py',
    'tests/test_orch_r111_route_shared.py',
    'tests/test_orch_r111_route_shared_ready.py',
    'tests/test_orch_r111_route_shared_native.py',
    'tests/test_orch_r111_route_boundary.py',
    'tests/test_orch_r116_shared_learner.py',
)


def summarize_junit(path):
    document = xml.parse(path).getroot()
    suites = [document] if document.tag == 'testsuite' else list(document.findall('testsuite'))
    boundary.require(bool(suites), 'actual_test_suites')
    totals = {name: sum(int(suite.attrib.get(name, 0)) for suite in suites)
              for name in ('tests', 'failures', 'errors', 'skipped')}
    boundary.require(totals['tests'] > 0 and totals['failures'] == totals['errors'] == totals['skipped'] == 0,
                     'all_native_CPU_tests_pass_no_skips')
    return totals


def validate(source):
    source = Path(source).resolve(strict=True)
    boundary.require(Path(__file__).resolve().parents[1] == source, 'execute_frozen_validator')
    boundary.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_visible_devices')
    for name in TESTS + ready.V2_SOURCE_FILES:
        boundary.require((source / name).is_file(), 'complete_test_and_runtime_closure')
    manifest_path = source / 'SOURCE_CLOSURE_V2.json'
    files = {str(path.relative_to(source)): boundary.sha(path)
             for path in source.rglob('*.py') if path.is_file()}
    boundary.write_new(manifest_path, dict(schema='R118_ROUTE_SOURCE_CLOSURE_V2', root=str(source),
        files=files, frozen_unix=time.time(), raw_files_included=False))
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
                       HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    started = time.time()
    help_command = [sys.executable, '-B', '-m', 'gpu.orch_r111_route_pair_shared', '--help']
    with (source / 'ENTRYPOINT_HELP_V2.log').open('x') as stream:
        help_result = subprocess.run(help_command, cwd=source, env=environment,
                                     stdout=stream, stderr=subprocess.STDOUT, timeout=60)
    boundary.require(help_result.returncode == 0, 'actual_shared_entrypoint_import_and_parser')
    junit = source / 'CPU_SHARED_V2.junit.xml'
    command = [sys.executable, '-B', '-m', 'pytest', '-q', *TESTS, '--junitxml=' + str(junit)]
    with (source / 'CPU_SHARED_V2.log').open('x') as stream:
        result = subprocess.run(command, cwd=source, env=environment,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=600)
    boundary.require(result.returncode == 0, 'native_CPU_suite_failed_preserve_log')
    totals = summarize_junit(junit)
    import torch

    boundary.require(not torch.cuda.is_initialized(), 'CPU_validator_no_CUDA')
    receipt = dict(schema='R118_ROUTE_SHARED_CPU_V2', passed=True, native_cpu=True,
        cuda_initialized=False, source_files={name: boundary.sha(source / name) for name in ready.V2_SOURCE_FILES},
        closure_manifest=boundary.reference(manifest_path),
        entrypoint=dict(module='gpu.orch_r111_route_pair_shared', help_exit_code=help_result.returncode,
                        sha256=boundary.sha(source / 'gpu/orch_r111_route_pair_shared.py')),
        tests_passed=totals['tests'], tests_failed=totals['failures'] + totals['errors'], tests_skipped=totals['skipped'],
        junit=boundary.reference(junit), log=boundary.reference(source / 'CPU_SHARED_V2.log'),
        tests=list(TESTS), command=command, started_unix=started, completed_unix=time.time(),
        packages={name: importlib.metadata.version(name) for name in ('torch', 'transformers', 'peft', 'pytest')},
        GPU_calls=0, provider_calls=0, live_lanes_changed=False)
    ready.verify_closure(source, receipt)
    boundary.write_new(source / 'CPU_SHARED_V2.json', receipt)
    return dict(path=str(source / 'CPU_SHARED_V2.json'), sha256=boundary.sha(source / 'CPU_SHARED_V2.json'),
                tests_passed=totals['tests'], source_files=len(files), passed=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    arguments = parser.parse_args()
    print(boundary.json.dumps(validate(arguments.source), sort_keys=True))
