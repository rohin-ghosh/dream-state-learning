"""Freeze the unchanged receiving evaluator; no model calls or learner reads."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r167_fleet_20260917_generation2')
STAGE = ROOT / 'gpu_takeover_20260917t1403z'


def main():
    os.umask(0o077)
    STAGE.mkdir(mode=0o700, exist_ok=False)
    source = STAGE / 'source'
    previous = ROOT / 'receiving_generation1' / 'source'
    shutil.copytree(previous, source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    incoming = Path(__file__).resolve().parent
    for name in ('fleet_gpu_controller.py', 'test_fleet_gpu_controller.py', 'test_fleet_interpreter_attestation.py'):
        if (source / name).exists():
            raise FileExistsError(name)
        shutil.copyfile(incoming / name, source / name)
    shutil.copyfile(incoming / 'gpu/orch_r167_fleet_eval.py', source / 'gpu/orch_r167_fleet_eval.py')
    sys.path.insert(0, str(source))
    from gpu import orch_r167_fleet_eval as evaluator
    from gpu import orch_r130_benchmark_sidecar as sidecar
    import fleet_gpu_controller as controller

    protocol = evaluator.protocol
    pins = sidecar.source_inventory(source)
    protocol.write(STAGE / 'SOURCE_PINS.json', pins)
    resource = protocol.read(ROOT / 'RECEIVING_RESOURCE.json')
    pipeline_path = ROOT / 'control2' / 'PLAN.json'
    pipeline = protocol.read(pipeline_path)
    protocol.require(protocol.sha(pipeline_path) == '1b3e26dc333de5201d4f1f943726f44a5d44652ccc69d3b8872497acfa1282fc', 'original_generation2_plan')
    original = (previous / 'gpu/orch_r167_fleet_eval.py').read_text()
    repaired = original.replace('def expected_go(config_path, authority):',
        'def interpreter_sha(path):\n    return protocol.sha(Path(path).resolve(strict=True))\n\n\ndef expected_go(config_path, authority):')
    repaired = repaired.replace("require(protocol.sha(config['python']) == config['python_sha256'], 'exact_existing_interpreter')",
        "require(interpreter_sha(config['python']) == config['python_sha256'], 'exact_existing_interpreter')")
    protocol.require((source / 'gpu/orch_r167_fleet_eval.py').read_text() == repaired,
        'only_authenticated_virtualenv_interpreter_attestation_repair')
    protocol.write(STAGE / 'NON_MATERIAL_REPAIR.json', dict(status='VIRTUALENV_SYMLINK_ATTESTATION_ONLY',
        previous=protocol.ref(previous / 'gpu/orch_r167_fleet_eval.py'),
        repaired=protocol.ref(source / 'gpu/orch_r167_fleet_eval.py'),
        preserved_failed_preflight=str(ROOT / 'gpu_takeover_20260917t1357z'),
        failed_gpu_jobs=0, model_calls=0, source_registry_unchanged=True))
    authority_path = ROOT / 'control2' / 'MAIN_CONDITIONAL_EXECUTION.md'
    release = protocol.bound(resource['release'])
    protocol.require(len(release['identities']) == 114 and all(
        entry['gone'] and controller.gone(sidecar, entry['identity']) for entry in release['identities']),
        'fresh_exact114_previous_processes_released')
    protocol.write(STAGE / 'FRESH_RELEASE.json', dict(status='ALL114_EXACT_IDENTITIES_GONE',
        release=resource['release'], observed_unix=time.time(), model_calls=0))
    environment = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
    tests = ['tests.test_orch_r167_fleet_eval', 'tests.test_orch_r167_object_survival_eval',
        'tests.test_orch_r167_object_probe_queue', 'test_fleet_gpu_controller', 'test_fleet_interpreter_attestation']
    with (STAGE / 'CPU_TESTS.private.txt').open('xb') as log:
        result = subprocess.run([resource['python'], '-B', '-m', 'unittest', '-v', *tests],
            cwd=source, env=environment, stdout=log, stderr=log, timeout=180)
    protocol.require(result.returncode == 0, 'actual_receiving_CPU_tests_failed_preserved')
    gate = protocol.write(STAGE / 'CPU_GATE.json', dict(status='PASS',
        helper_sha256=pins['gpu/orch_r167_fleet_eval.py'], tests_sha256=pins['tests/test_orch_r167_fleet_eval.py'],
        tested_modules=tests, receipt=protocol.ref(STAGE / 'CPU_TESTS.private.txt'),
        sources=protocol.ref(STAGE / 'SOURCE_PINS.json'), observed_unix=time.time(), model_calls=0))
    authority = protocol.ref(authority_path)
    builder = protocol.write(STAGE / 'BUILDER_GATE.json', dict(status='CPU_AND_PROVENANCE_PASS',
        cpu_gate=gate, pipeline=protocol.ref(pipeline_path), authority=authority,
        dated_builder_line='[Builder] ' + time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) +
            ' — R167 takeover: actual unchanged receiving-source CPU/provenance gate; exact per-cell validation before GO; no provider or parent calls.',
        release=protocol.ref(STAGE / 'FRESH_RELEASE.json'), model_calls=0))
    methods = protocol.write(STAGE / 'METHODS.json', evaluator.METHODS)
    common = dict(schema=evaluator.SCHEMA, pipeline=protocol.ref(pipeline_path), root=str(ROOT), methods=methods,
        source_root=str(source), sources=pins, python=resource['python'], python_sha256=resource['python_sha256'],
        model_dir=resource['model_dir'], service_path=resource['service_path'],
        service_sha256=protocol.sha(resource['service_path']), lease=resource['lease'], cpu_gate=gate,
        builder=builder, release=resource['release'], authority=authority, max_job_seconds=900)
    runtime = protocol.write(STAGE / 'RUNTIME.json', dict(common=common))
    preflight = STAGE / 'preflight'
    preflight.mkdir(mode=0o700)
    ready = []
    for physical in (0, 1):
        cells = controller.candidates(pipeline, physical)
        protocol.require(bool(cells), 'at_least_one_eligible_fixed_cell_each_condition')
        cell = cells[0]
        life = ROOT / 'lives' / cell['life_id']
        config = dict(common, life_id=cell['life_id'], sleep=cell['sleep'], condition=cell['condition'],
            capture=protocol.ref(life / 'captures' / f"{cell['sleep']:06d}" / 'COMPLETE.json'),
            registration=protocol.ref(life / 'REGISTERED.json'), TRAIN_freeze=protocol.ref(life / 'TRAIN_FREEZE.json'),
            transfer=cell['transfer'], physical=physical, gpu_uuid=sidecar.DEVICES[physical])
        config_path = preflight / (cell['key'] + '.CONFIG.json')
        protocol.write(config_path, config)
        evaluator.validate(config_path)
        report = sidecar.scan(config)
        scan_ref = protocol.write(preflight / f'PHYSICAL{physical}.ADMISSION.private.json', report)
        protocol.require(report['clear'] and not report['blocking_reasons'], 'strict_fresh_admission_not_clear')
        ready.append(dict(physical=physical, condition=cell['condition'], eligible_cells=len(cells),
            config=protocol.ref(config_path), admission=scan_ref))
    for name, checksum in pins.items():
        protocol.require(protocol.sha(source / name) == checksum, 'post_CPU_source_unchanged')
    protocol.require(time.time() + 915 < pipeline['hard_end_unix'], 'full_job_within_original_wall')
    protocol.write(STAGE / 'READY.json', dict(status='ACTUAL_RECEIVING_CPU_PROVENANCE_AND_ADMISSION_PASS',
        runtime=runtime, slots=ready, model_calls=0, observed_unix=time.time(), authority=authority,
        original_wall_unix=pipeline['hard_end_unix'], calls_cap=504, tokens_cap=258048))
    print(json.dumps(dict(status='READY_NOT_LAUNCHED', stage=str(STAGE), runtime=runtime,
        eligible_condition_cells=sum(row['eligible_cells'] for row in ready), model_calls=0)))


if __name__ == '__main__':
    main()
