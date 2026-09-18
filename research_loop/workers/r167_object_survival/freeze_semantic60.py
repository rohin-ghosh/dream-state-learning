import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

from gpu import orch_r167_object_survival_eval as protocol
from gpu import orch_route_parent_campaign_providers as providers


def build(generation):
    repository = Path.cwd().resolve()
    worker = Path(__file__).resolve().parent
    protocol.require(type(generation) is int and 1 <= generation <= 99, 'explicit_new_generation')
    destination = worker / f'semantic60_generation{generation}'
    source = destination / 'source'
    source.mkdir(parents=True, mode=0o700, exist_ok=False)
    files = {Path(module.__file__).resolve() for module in tuple(sys.modules.values())
        if getattr(module, '__file__', None) and Path(module.__file__).is_file()
        and Path(module.__file__).resolve().is_relative_to(repository)
        and module.__name__ != '__main__'}
    for path in sorted(files):
        target = source / path.relative_to(repository)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    for name in ('semantic_judge.py', 'test_semantic_judge.py'):
        shutil.copyfile(worker / name, source / name)
    pins = {str(path.relative_to(source)):protocol.sha(path) for path in sorted(source.rglob('*.py'))}
    pins_ref = protocol.write(destination / 'SOURCE_PINS.json', pins)
    with (destination / 'CPU_TESTS.txt').open('wb') as log:
        completed = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'test_semantic_judge', '-v'],
            cwd=source, env=dict(os.environ, PYTHONPATH=str(source)), stdout=log, stderr=log, timeout=60)
    protocol.require(completed.returncode == 0 and b'Ran 15 tests' in (destination / 'CPU_TESTS.txt').read_bytes(),
                     'actual_frozen_source_CPU_PASS')
    gate = protocol.write(destination / 'CPU_GATE.json', dict(status='PASS', tests=15, provider_calls=0,
        source_pins_sha256=protocol.digest(pins), source_pins=pins_ref,
        test_receipt=protocol.ref(destination / 'CPU_TESTS.txt')))
    inventory_ref = protocol.ref(worker / 'SEMANTIC60_PACKET_REFS.json')
    inventory = protocol.bound(inventory_ref)
    config_path = (Path.home() / '.codex/nvidia-astra.config.toml').resolve()
    plan = dict(schema='R167_STATELESS_SEMANTIC60_V1', source_pins=pins, source_root=str(source),
        packet_inventory=inventory_ref, rubric=inventory['rubric'], provider_config=protocol.ref(config_path),
        transport=protocol.ref(repository / 'gpu/ovx_ssh.sh'),
        transport_environment=protocol.ref(repository / 'gpu/hosts.env'),
        model=providers.STRONG, effort='high', max_output_tokens=4096, call_cap=60, packet_count=60,
        timeout_seconds=120, concurrency=2, maximum_wall_seconds=5400,
        private_vm_root=f'/tmp/orch_r167_semantic_60_generation{generation}_private',
        private_remote_root=str(protocol.CAMPAIGN / f'private_appendices/semantic60_generation{generation}'),
        visibility='PRIVATE_VM_AND_NODE2_EXCLUDED_FROM_ALL_PARENTS_AND_REPO_READER', CPU_gate=gate)
    plan_ref = protocol.write(destination / 'PLAN.json', plan)
    validation = subprocess.run([sys.executable, '-B', str(source / 'semantic_judge.py'), 'validate',
        '--plan', str(destination / 'PLAN.json')], cwd=source, env=dict(os.environ,PYTHONPATH=str(source)),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    protocol.require(validation.returncode == 0, 'receiving_config_and_existing_key_gate')
    protocol.write(destination / 'VALIDATION.json', validation.stdout)
    template = dict(schema=plan['schema'], status='PREPARATION_ONLY_REPLACE_WITH_EXPLICIT_MAIN_GO',
        plan=plan_ref, calls=60, provider_model=providers.STRONG, max_concurrent=2, no_retries=True)
    protocol.write(destination / 'MAIN_GO.template.json', template)
    receipt = dict(status='CPU_FROZEN_READY_AWAITING_NEW_MAIN_EXECUTION_GO', plan=plan_ref, CPU_gate=gate,
        runner=protocol.ref(source / 'semantic_judge.py'), tests=protocol.ref(source / 'test_semantic_judge.py'),
        provider=protocol.ref(source / 'gpu/orch_route_parent_campaign_providers.py'), source_pins=pins_ref,
        configuration_sha256=plan['provider_config']['sha256'], model=providers.STRONG, effort='high',
        registered_packets=60, provider_calls=0, provider_call_cap=60, per_call_output_token_cap=4096,
        aggregate_provider_output_token_cap=245760, concurrency_cap=2, provider_timeout_seconds=120,
        batch_wall_seconds=5400, private_VM_root=plan['private_vm_root'], private_node2_root=plan['private_remote_root'],
        new_service=False, credential_copy=False, actual_parent_publication=False, GPU_calls=0,
        runtime_source_files=len(pins), rubric_sha256=plan['rubric']['sha256'])
    protocol.write(destination / 'READINESS.json', receipt)
    print(protocol.json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--generation', required=True, type=int)
    build(parser.parse_args().generation)
