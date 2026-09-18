"""Freeze only previously unattempted OFF cells under the existing delegation."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r167_fleet_20260917_generation2')
STAGE = ROOT / 'gpu_unused_off_generation1'


def main():
    os.umask(0o077)
    STAGE.mkdir(mode=0o700, exist_ok=False)
    previous = ROOT / 'gpu_takeover_20260917t1403z'
    source = STAGE / 'source'
    shutil.copytree(previous / 'source', source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    incoming = Path(__file__).resolve().parent
    for name in ('fleet_gpu_controller.py', 'test_fleet_gpu_controller.py', 'test_fleet_unused_off.py'):
        shutil.copyfile(incoming / name, source / name)
    sys.path.insert(0, str(source))
    from gpu import orch_r167_fleet_eval as evaluator
    from gpu import orch_r130_benchmark_sidecar as sidecar
    import fleet_gpu_controller as controller
    protocol = evaluator.protocol
    common = protocol.read(previous / 'RUNTIME.json')['common']
    protocol.require(protocol.sha(source / 'gpu/orch_r167_fleet_eval.py') ==
        common['sources']['gpu/orch_r167_fleet_eval.py'], 'unchanged_tested_evaluator')
    block = protocol.read(ROOT / 'gpu_operation1/PHYSICAL1.BLOCKED.json')
    key = block['key']
    attempt = ROOT / 'attempts' / key
    refusal = protocol.read(attempt / 'REFUSED.json')
    report = protocol.read(attempt / 'ACTUAL_ADMISSION.private.json')
    protocol.require(refusal['calls_charged'] == 0 and not (ROOT / 'ledger' / (key + '.RESERVED.json')).exists(),
        'refusal_never_invoked_but_permanently_excluded')
    protocol.require(report['blocking_reasons'] == ['process_identity_drift:1765193'], 'exact_preserved_refusal')
    released = []
    for name in ('INITIATOR.json', 'WRAPPER.json'):
        path = ROOT / 'launches' / key / name
        identity = protocol.read(path)['identity']
        protocol.require(controller.gone(sidecar, identity), 'refused_wrapper_naturally_released')
        released.append(protocol.ref(path))
    protocol.require(not (Path('/proc') / '1765193').exists(), 'drift_process_naturally_gone')
    protocol.write(STAGE / 'PRIOR_REFUSAL_EXCLUDED.json', dict(status='CONSUMED_REFUSAL_PERMANENTLY_EXCLUDED',
        key=key, refusal=protocol.ref(attempt / 'REFUSED.json'), released=released,
        source_operation='gpu_operation1', new_operation='gpu_operation2', physical_slots=[1],
        observed_unix=time.time(), signals_sent=0, retry=False))
    pins = sidecar.source_inventory(source)
    protocol.write(STAGE / 'SOURCE_PINS.json', pins)
    tests = ['tests.test_orch_r167_fleet_eval', 'tests.test_orch_r167_object_survival_eval',
        'tests.test_orch_r167_object_probe_queue', 'test_fleet_gpu_controller',
        'test_fleet_interpreter_attestation', 'test_fleet_unused_off']
    environment = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
    with (STAGE / 'CPU_TESTS.private.txt').open('xb') as log:
        result = subprocess.run([common['python'], '-B', '-m', 'unittest', '-v', *tests],
            cwd=source, env=environment, stdout=log, stderr=log, timeout=180)
    protocol.require(result.returncode == 0, 'actual_receiving_unused_OFF_CPU_tests')
    common['source_root'] = str(source)
    common['sources'] = pins
    common['cpu_gate'] = protocol.write(STAGE / 'CPU_GATE.json', dict(status='PASS',
        helper_sha256=pins['gpu/orch_r167_fleet_eval.py'], tests_sha256=pins['tests/test_orch_r167_fleet_eval.py'],
        tested_modules=tests, receipt=protocol.ref(STAGE / 'CPU_TESTS.private.txt'), observed_unix=time.time()))
    common['builder'] = protocol.write(STAGE / 'BUILDER_GATE.json', dict(status='CPU_AND_PROVENANCE_PASS',
        cpu_gate=common['cpu_gate'], pipeline=common['pipeline'], authority=common['authority'],
        dated_builder_line='[Builder] '+time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+
            ' — Fresh source/CPU gate for only previously unattempted OFF cells; preserved failed cell excluded; strict admission unchanged.',
        prior_refusal=protocol.ref(STAGE / 'PRIOR_REFUSAL_EXCLUDED.json'), model_calls=0))
    runtime = protocol.write(STAGE / 'RUNTIME.json', dict(common=common, physical_slots=[1]))
    pipeline = protocol.bound(common['pipeline'])
    cells = controller.candidates(pipeline, 1)
    protocol.require(bool(cells) and all(cell['key'] != key for cell in cells), 'only_unconsumed_remaining_OFF')
    cell = cells[0]
    life = ROOT / 'lives' / cell['life_id']
    config = dict(common, life_id=cell['life_id'], sleep=cell['sleep'], condition=cell['condition'],
        capture=protocol.ref(life / 'captures' / f"{cell['sleep']:06d}" / 'COMPLETE.json'),
        registration=protocol.ref(life / 'REGISTERED.json'), TRAIN_freeze=protocol.ref(life / 'TRAIN_FREEZE.json'),
        transfer=cell['transfer'], physical=1, gpu_uuid=sidecar.DEVICES[1])
    config_path = STAGE / 'PREFLIGHT.CONFIG.json'
    protocol.write(config_path, config)
    evaluator.validate(config_path)
    report = sidecar.scan(config)
    protocol.write(STAGE / 'ADMISSION.private.json', report)
    protocol.require(report['clear'] and not report['blocking_reasons'], 'unchanged_strict_admission')
    for name, checksum in pins.items():
        protocol.require(protocol.sha(source / name) == checksum, 'immutable_source_pins')
    protocol.write(STAGE / 'READY.json', dict(status='UNUSED_OFF_ONLY_CPU_PROVENANCE_ADMISSION_PASS',
        runtime=runtime, eligible_cells=len(cells), excluded_refusal=key, observed_unix=time.time(),
        physical_slots=[1], model_calls=0, hard_end_unix=1789659000))
    print(json.dumps(dict(status='READY_UNUSED_OFF_ONLY_NOT_LAUNCHED', runtime=runtime,
        eligible_cells=len(cells), excluded_consumed_cells=1, model_calls=0)))


if __name__ == '__main__':
    main()
