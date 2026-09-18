"""Freeze and stage authorized source-only generation; never GPU enrollment."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tarfile
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC = importlib.util.spec_from_file_location('pipeline', HERE / 'fleet_source_pipeline.py')
pipeline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pipeline)
protocol = pipeline.protocol
OUTPUT = HERE / 'fleet_generation2'
REMOTE = Path('/localhome/local-rohing/orch_r167_fleet_20260917_generation2')
NODES = ('ovx3', 'ovx2', 'a100', 'a40r')


def pinned_copy(path, directory):
    path = Path(path)
    checksum = protocol.sha(path)
    target = directory / (checksum + path.suffix)
    if not target.exists():
        shutil.copyfile(path, target)
    return dict(path=str(REMOTE / 'control/evidence' / target.name), sha256=checksum)


def ssh(node, command, **kwargs):
    return subprocess.run(['bash', str(REPO / 'gpu' / (node + '_ssh.sh')), command],
        cwd=REPO, check=True, **kwargs)


def build(complete_staging=False):
    OUTPUT.mkdir(mode=0o700, exist_ok=complete_staging)
    evidence_dir = OUTPUT / 'control/evidence'
    evidence_dir.mkdir(parents=True, exist_ok=complete_staging)
    source = OUTPUT / 'source'
    (source / 'gpu').mkdir(parents=True, exist_ok=complete_staging)
    (source / 'tests').mkdir(exist_ok=complete_staging)
    def immutable_copy(origin, target):
        if target.exists():
            protocol.require(protocol.sha(origin) == protocol.sha(target), 'staged_source_cannot_change')
        else:
            shutil.copyfile(origin, target)
    immutable_copy(HERE / 'fleet_source_pipeline.py', source / 'fleet_source_pipeline.py')
    immutable_copy(HERE / 'test_fleet_source_pipeline.py', source / 'test_fleet_source_pipeline.py')
    for name in ('orch_r167_object_probe_queue.py', 'orch_r167_object_survival_eval.py'):
        immutable_copy(REPO / 'gpu' / name, source / 'gpu' / name)
    for directory in ('gpu', 'tests'):
        target = source / directory / '__init__.py'
        if not target.exists():
            target.write_bytes(b'')
    immutable_copy(REPO / 'tests/test_orch_r167_object_probe_queue.py', source / 'tests/test_orch_r167_object_probe_queue.py')
    custody_dir = REPO / 'research_loop/workers/r167_fleet_custody_20260917/train_attempt1'
    immutable_copy(custody_dir / 'native_custody.py', source / 'native_custody.py')
    immutable_copy(custody_dir / 'test_native_custody.py', source / 'test_native_custody.py')
    original_path = HERE / 'fleet_generation1/BATCH_PLAN.json'
    original = protocol.read(original_path)
    galileo_path = REPO / 'research_loop/workers/r167_fleet_custody_20260917/CURRENT_DELIVERY.json'
    galileo_ref = pinned_copy(galileo_path, evidence_dir)
    galileo = {life['life_id']: life for life in protocol.read(galileo_path)['lives']}
    legacy_dir = REPO / 'research_loop/workers/r167_legacy_custody_20260917/observations'
    lives = []
    for original_life in original['lives']:
        life = dict(original_life, status='SOURCE_CANDIDATE', prior_charges=dict(metadata=0, adapter=0))
        life['registry_birth_plan'] = original_life['birth_plan']
        if life['life_id'] in ('C5', 'repo_reader'):
            previous = galileo[life['life_id']].get('cumulative_reads', {})
            life['prior_charges']['metadata'] = previous.get('metadata_bytes', 0) + previous.get('journal_bytes', 0)
            life.update(status='MISSING_CUSTODY_NOT_NEGATIVE', missing_reason='RECOVERY_OR_INITIAL_PATH_CUSTODY_PENDING')
            lives.append(life)
            continue
        if life['node'] == 'ovx3':
            delivery = galileo[life['life_id']]
            previous = delivery['cumulative_reads']
            life['inventory_identity'] = delivery['native_identity']
            life['birth_plan'] = pipeline.reference(delivery.get('matching_original_birth_plan') or life['birth_plan'])
            life['evidence'] = [galileo_ref, pinned_copy(delivery['TRAIN_custody']['path'], evidence_dir)]
            if delivery.get('registration_observation_candidate'):
                life['evidence'].append(pinned_copy(delivery['registration_observation_candidate']['path'], evidence_dir))
        else:
            observed_path = legacy_dir / (life['node'] + '_' + life['life_id'] + '.json')
            observation = protocol.read(observed_path)
            protocol.require(observation['status'] == 'IDENTITY_AND_COMPLETED_FRONTIER_VERIFIED', 'complete_legacy_custody')
            previous = observation['cumulative_reads']
            life['inventory_identity'] = observation['native_identity']
            life['birth_plan'] = pipeline.reference(observation['original_birth_plan'])
            life['evidence'] = [pinned_copy(observed_path, evidence_dir)]
            life['evidence'].extend(pinned_copy(item['path'], evidence_dir) for item in observation['evidence'])
        life['prior_charges']['metadata'] = previous['metadata_bytes'] + previous['journal_bytes']
        lives.append(life)
    for node in NODES:
        request = dict(lives=[life for life in lives if life['node'] == node and life['status'] == 'SOURCE_CANDIDATE'])
        target = OUTPUT / 'control' / (node + '.STAT_REQUEST.json')
        if target.exists():
            protocol.require(protocol.read(target) == request, 'stat_request_unchanged')
        else:
            protocol.write(target, request)
    archive = OUTPUT / ('SOURCE_STAT_STAGE_completion1.tar' if complete_staging else 'SOURCE_STAT_STAGE.tar')
    with tarfile.open(archive, 'w') as bundle:
        bundle.add(source, arcname='source')
        bundle.add(OUTPUT / 'control', arcname='control')
    def stage_stat(node):
        command = f'umask 077; mkdir -p {shlex.quote(str(REMOTE))} && tar --skip-old-files -xf - -C {shlex.quote(str(REMOTE))}'
        with archive.open('rb') as stream:
            ssh(node, command, stdin=stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        command = f'cd {REMOTE}/source && PYTHONPATH={REMOTE}/source python3 -B fleet_source_pipeline.py stat --plan {REMOTE}/control/{node}.STAT_REQUEST.json'
        result = ssh(node, command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
        protocol.write(OUTPUT / (node + '.STAT_RESULT.json'), result.stdout)
        return node, json.loads(result.stdout)
    stats = dict(ThreadPoolExecutor(max_workers=4).map(stage_stat, NODES))
    for life in lives:
        if life['status'] != 'SOURCE_CANDIDATE':
            continue
        node_stats = stats[life['node']]
        observed = next(item for item in node_stats['rows'] if item['life_id'] == life['life_id'])
        if observed.get('status') == 'STAT_REFUSED':
            life.update(status='MISSING_CUSTODY_NOT_NEGATIVE', missing_reason='STAT_REFUSED')
            continue
        life['hostname_sha256'] = node_stats['hostname_sha256']
        life['allocation'] = pipeline.allocation(observed, life['prior_charges'])
    sources = {str(path.relative_to(source)): protocol.sha(path) for path in source.rglob('*.py')}
    plan = dict(schema=pipeline.SCHEMA, original_registry=pinned_copy(original_path, evidence_dir),
        scope=pinned_copy(HERE / 'FLEET_MAIN_SOURCE_SCOPE_20260917.md', evidence_dir),
        amendment=pinned_copy(HERE / 'FLEET_MAIN_METADATA_AMENDMENT_20260917.md', evidence_dir),
        runtime_root=str(REMOTE / 'source'), queue_root=str(REMOTE), sources=sources,
        call_cap=504, token_cap=258048, physical_slots=[0,1], hard_end_unix=1789659000,
        metadata_cap=16*pipeline.GIB, adapter_cap=16*pipeline.GIB, probes=list(pipeline.queue.PROBES),
        conditions=list(pipeline.queue.CONDITIONS), lives=lives, registration_model_calls=0, GPU_authorized=False,
        prepared_unix=time.time(), previous_registry_untouched=True)
    candidates = [life for life in lives if life['status'] == 'SOURCE_CANDIDATE']
    totals = {kind: sum(life['allocation'][kind + '_read_cap'] if life['status'] == 'SOURCE_CANDIDATE'
        else life['prior_charges'][kind] for life in lives) for kind in ('metadata', 'adapter')}
    protocol.require(all(amount <= 16*pipeline.GIB for amount in totals.values()), 'aggregate_budget_before_any_source_read')
    protocol.write(OUTPUT / 'control/PLAN.json', plan)
    with (OUTPUT / 'CPU_TESTS.txt').open('xb') as stream:
        subprocess.run([sys.executable, '-B', '-m', 'unittest', 'tests.test_orch_r167_object_probe_queue',
            'test_fleet_source_pipeline', 'test_native_custody', '-q'], cwd=source,
            stdout=stream, stderr=stream, check=True)
    gate = dict(status='PASS', sources=sources, test_receipt=protocol.ref(OUTPUT / 'CPU_TESTS.txt'),
        source_reads=0, model_calls=0, scope='SOURCE_ONLY_NOT_GPU_GO', candidates=len(candidates),
        missing_lives=[life['life_id'] for life in lives if life['status'] != 'SOURCE_CANDIDATE'],
        allocated_bytes=totals, caps_bytes=dict(metadata=16*pipeline.GIB, adapter=16*pipeline.GIB))
    protocol.write(OUTPUT / 'CPU_GATE.json', gate)
    with tarfile.open(OUTPUT / 'CONTROL_STAGE.tar', 'w') as bundle:
        bundle.add(OUTPUT / 'control', arcname='control')
    for node in NODES:
        with (OUTPUT / 'CONTROL_STAGE.tar').open('rb') as stream:
            ssh(node, f'tar --skip-old-files -xf - -C {REMOTE}', stdin=stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        validation = ssh(node, f'cd {REMOTE}/source && PYTHONPATH={REMOTE}/source python3 -B fleet_source_pipeline.py validate --plan {REMOTE}/control/PLAN.json',
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        protocol.write(OUTPUT / (node + '.VALIDATION.json'), validation.stdout)
    print(json.dumps(dict(status='STAGED_VALIDATED_NO_SOURCE_CONTENT_READ_YET', plan=protocol.ref(OUTPUT / 'control/PLAN.json'),
        CPU_gate=protocol.ref(OUTPUT / 'CPU_GATE.json'), candidates=len(candidates), allocated_bytes=totals)))


if __name__ == '__main__':
    build(complete_staging=sys.argv[1:] == ['--complete-staging'])
