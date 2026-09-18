"""Node4 physical6 only: prepare a new MATH-C without modifying the old life."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tarfile
import time
import uuid


HOME = Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/MATH_C')
SOURCE = HOME / 'source'
SNAPSHOT = HOME / 'snapshot'
BASE = Path('/localhome/local-rohing')
PYTHON = BASE / 'v2/venv/bin/python'
OLD = BASE / 'orch_r188_node4_relocated_20260917t2349z/receiving3v2'
OLD_ROOT = BASE / 'orch_r133_node3_brain_guided_20260916_attempt1/run1'
OLD_GUARD = OLD / 'control_admission2/GUARD.json'
LEASE = BASE / 'orch_r132_kernel_child_20260916_attempt1/control1/LEASE_BUDGET.json'
HELPER_BUNDLE = BASE / 'orch_r179_node4_r181journal_20260917t2220z'
HOST_SHA = 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'
MANIFEST_SHA = '29ca04c2c51671c7df922a4b05448586e74eec35da45b03009877baccbccce84'
ARCHIVE_SHA = '9beaf7a79063c5cf4af2868e1f3122dfea7f4fa5ce3f7d3f2f51716676cdee34'
OVERLAY_SHA = '599f44f1a39bc0a312a180963feef8affc62748cec20721a79112bfc5a0540b1'
WALL = 1789754400
GPU = 'GPU-06b31c8f-7a96-d812-23f3-df3444d95397'
GATE = BASE / 'orch_r153_cpu_smoke_20260918t0238z/gate'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)


def host():
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA, 'node4_only')
    require(os.getuid() == 2524 and read(LEASE)['hard_end_unix'] == WALL and time.time() + 180 < WALL,
        'same_user_existing_hard_wall')


def extract_exact(archive_path, target, expected):
    with tarfile.open(archive_path) as archive:
        members = archive.getmembers()
        require(len(members) == len(expected) and {member.name for member in members} == set(expected),
            'exact_archive_members')
        for member in members:
            require(member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts,
                'regular_owned_members_only')
            destination = target / member.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as incoming, destination.open('xb') as outgoing:
                shutil.copyfileobj(incoming, outgoing)
            require(sha(destination) == expected[member.name], 'archive_member_digest:' + member.name)


def stage():
    host()
    require(sha(SNAPSHOT / 'MANIFEST.json') == MANIFEST_SHA and sha(SNAPSHOT / 'SNAPSHOT.tar') == ARCHIVE_SHA,
        'Main_named_source_capture')
    require(sha(HOME / 'main_ready/runtime_overlay.tar.gz') == OVERLAY_SHA, 'Main_tested_overlay')
    manifest = read(SNAPSHOT / 'MANIFEST.json')
    expected = {item['relative']: item['sha256'] for item in manifest['files']}
    extract_exact(SNAPSHOT / 'SNAPSHOT.tar', SNAPSHOT, expected)
    shutil.copytree(SNAPSHOT / 'source', SOURCE)
    ready = read(HOME / 'main_ready/READY.json')
    overlay = HOME / 'overlay'
    overlay.mkdir()
    extract_exact(HOME / 'main_ready/runtime_overlay.tar.gz', overlay, ready['files'])
    for relative in ready['files']:
        destination = SOURCE / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(overlay / relative, destination)
    old_source = OLD / 'source'
    for relative in ('gpu/orch_r188_node4_rehome_containment.py', 'gpu/orch_r133_retire_old_lanes.py',
                     'gpu/orch_r179_busy_preflight.py'):
        if (old_source / relative).exists():
            shutil.copyfile(old_source / relative, SOURCE / relative)
    write(HOME / 'STAGED.json', dict(status='SOURCE_STAGED_NO_RETIREMENT', manifest_sha256=MANIFEST_SHA,
        overlay_sha256=OVERLAY_SHA, source_root=str(SOURCE), observed_unix=time.time(), signals=0))


def sandbox_probe():
    host()
    sys.path.insert(0, str(GATE.parent / 'source'))
    from gpu import orch_r125_cpu_confinement_probe as profile
    from gpu.orch_r125_cpu_experiment import digest, verify_gate
    gate_digest = digest(verify_gate(GATE))
    root = HOME / 'sandbox_probe'
    root.mkdir(mode=0o755)
    (root / 'empty').mkdir(mode=0o755)
    (root / 'readonly.txt').write_text('No external mathematical inputs.\n')
    filesystem = root / 'rootfs'
    filesystem.mkdir(mode=0o755)
    for name in ('usr', 'etc', 'proc', 'dev', 'sys', 'run', 'tmp', 'work'):
        (filesystem / name).mkdir(mode=0o755)
    for name in ('bin', 'lib', 'lib64'):
        (filesystem / name).symlink_to('usr/' + name)
    payload = ('import importlib.util,json,os,sys\n'
        'facts=dict(python=sys.version,uid=os.getuid(),torch_present=importlib.util.find_spec("torch") is not None)\n'
        'for name in ("sympy","mpmath"):\n'
        ' try:\n'
        '  package=__import__(name);facts[name]=package.__version__\n'
        ' except ImportError: facts[name]=None\n'
        'if facts["sympy"]:\n'
        ' import sympy\n'
        ' facts["calculation"]=str(sympy.factorint(91))\n'
        'print(json.dumps(facts))\n')
    (root / 'payload.py').write_text(payload)
    command = profile.command(root, 'orch-r125-cpu-r201-math-c-probe')
    completed = subprocess.run(command, capture_output=True, text=True, timeout=35)
    evidence = dict(command=command, gate_root=str(GATE), gate_sha256=gate_digest,
        profile_sha256=sha(profile.__file__), returncode=completed.returncode,
        stdout=completed.stdout, stderr=completed.stderr, observed_unix=time.time(),
        child_tool_request=False, original_life_changed=False)
    write(HOME / 'CPU_SANDBOX.json', evidence)
    require(completed.returncode == 0, 'actual_CPU_sandbox_math_dependencies_missing')
    facts = json.loads(completed.stdout)
    require(facts['uid'] != 0 and not facts['torch_present'], 'CPU_sandbox_safety')
    print(json.dumps(evidence))
    return evidence


def math_prepare():
    host()
    import c2_math_environment as helper
    helper.ORIGINAL_SOURCE = SOURCE
    helper.prepare(GATE.parent)


def math_test():
    host()
    import c2_math_environment as helper
    helper.ORIGINAL_SOURCE = SOURCE
    helper.test_candidate(GATE.parent)


def clone_state(physical=6, trial_id='R201_MATH_C_node4_6', arm='MATH-C'):
    host()
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r125_continual_stream import ContinualStream, digest
    ready = read(HOME / 'main_ready/READY.json')
    sandbox = read(HOME / 'CPU_SANDBOX.json')
    require(sandbox['returncode'] == 0, 'actual_sandbox_passed')
    facts = json.loads(sandbox['stdout'])
    require(not facts['torch_present'], 'no_torch_in_CPU_sandbox')
    source_complete = read(SNAPSHOT / 'complete/SLEEP_COMPLETE.json')
    context_record = read(SNAPSHOT / 'console/CONTEXT_COMMITTED.json')
    learned = source_complete['document']['resume_state']
    context = context_record['document']['state']
    require(source_complete['index'] == 5823 and context_record['index'] == 5846
        and source_complete['document']['cycle'] == 51, 'exact_source_and_console_cut')
    require(context['state']['rows'] == learned['state']['rows']
        and context['state']['sleep_frontier'] == learned['state']['sleep_frontier']
        and context['state']['model_state_sha256'] == learned['state']['model_state_sha256'],
        'console_not_learned_weights_or_new_training_rows')
    life = HOME / 'life'
    checkpoint_dir = life / 'checkpoints/sleep_000051'
    checkpoint_dir.mkdir(parents=True)
    shutil.copytree(SNAPSHOT / 'complete/adapter', checkpoint_dir / 'adapter')
    shutil.copyfile(SNAPSHOT / 'complete/optimizer_rng.pt', checkpoint_dir / 'optimizer_rng.pt')
    checkpoint = read(SNAPSHOT / 'complete/COMMIT.json')
    checkpoint.update(adapter_path=str(checkpoint_dir / 'adapter'),
                      optimizer_rng_path=str(checkpoint_dir / 'optimizer_rng.pt'))
    write(checkpoint_dir / 'COMMIT.json', checkpoint)
    require(checkpoint['optimizer_steps'] == 4908 and sha(checkpoint['optimizer_rng_path'])
        == checkpoint['checkpoint_sha256']['optimizer'] == checkpoint['checkpoint_sha256']['rng'],
        'copied_complete51_optimizer_RNG_exact')
    plan = read(SNAPSHOT / 'source_binding/PLAN.json')
    source_before = plan['source_root']
    plan.update(root=str(life), source_root=str(SOURCE), physical=physical, gpu_uuid=GPU,
                hard_end_unix=WALL, lease_end_unix=read(LEASE)['lease_end_unix'], max_sleeps=57,
                **ready['required_native_options'])
    if plan.get('startup_context'):
        relative = Path(plan['startup_context']['path']).relative_to(source_before)
        plan['startup_context']['path'] = str(SOURCE / relative)
        startup = SOURCE / relative
        if not startup.exists():
            startup.parent.mkdir(parents=True, exist_ok=True)
            require(hashlib.sha256(plan['birth_prompt'].encode()).hexdigest() == plan['startup_context']['sha256'],
                'source_bound_startup_context')
            with startup.open('x') as output:
                output.write(plan['birth_prompt'])
    driver = dict(ready['required_driver_options'], trial_id=trial_id,
        cpu_gate_root=str(GATE), cpu_gate_sha256=sandbox['gate_sha256'],
        environment_facts=f'This actual confined Python tool reports SymPy {facts["sympy"]} and mpmath {facts["mpmath"]}. '
        'It has no Torch, GPU, network, or home access. '
        'A proposed computation is not a verified result; use the actual returned receipt.')
    plan['think_act_learn'] = driver
    for key in ('community_agent_id', 'community_profile'):
        plan.pop(key, None)
    target = deepcopy(context)
    target['state']['deadline_unix'] = WALL
    target['sha256'] = digest(target['state'])
    with StreamJournal(life / 'stream', create=True) as journal:
        journal.record('R201_CLONE_SOURCE', dict(arm=arm, source_manifest_sha256=MANIFEST_SHA,
            complete_record_index=5823, console_record_index=5846, console_state_sha256=context['sha256'],
            imported_context_not_new_generation=True, live_inbox_replication=False,
            source_deadline_unix=context['state']['deadline_unix'], clone_deadline_unix=WALL))
        for index in (5844, 5845, 5846):
            record = read(SNAPSHOT / 'console/records' / f'{index:020d}.json')
            document = deepcopy(record['document'])
            key = 'resume_state' if record['kind'] == 'REQUEST' else 'state'
            if key in document:
                document[key]['state']['deadline_unix'] = WALL
                document[key]['sha256'] = digest(document[key]['state'])
            journal.record(record['kind'], document)
        restored = journal.latest_checkpoint()
        require(restored['document'] == target and restored['expected_sha256'] == target['sha256'],
            'exact_common_masked_context_only_deadline_rebound')
        stream = ContinualStream.restore(restored['document'], expected_sha256=restored['expected_sha256'])
        require(stream.checkpoint() == target and len(stream.rows) == 153 and stream.pending is None
            and stream.sleep_frontier == 153, 'full_same_source_state_roundtrip')
        require(not list((life / 'stream/inbox').iterdir()), 'no_source_inbox_messages_replayed')
        journal_id = journal._manifest['journal_id']
    import torch
    payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == 4908 and payload['optimizer']['state']
        and all(group['lr'] == 3e-5 for group in payload['optimizer']['param_groups'])
        and payload['python_rng'] and payload['cpu_rng'] is not None and len(payload['cuda_rng']) == 1,
        'source_AdamW_RNG_and_LR_preserved')
    require(not torch.cuda.is_initialized(), 'CPU_restore_only')
    (HOME / 'control').mkdir()
    write(HOME / 'control/PLAN.json', plan)
    write(HOME / 'CLONE_RESTORED.json', dict(status='CPU_RESTORED_NOT_LAUNCHED',
        source_manifest_sha256=MANIFEST_SHA, source_console_state_sha256=context['sha256'],
        clone_state_sha256=target['sha256'], checkpoint_sha256=sha(checkpoint_dir / 'COMMIT.json'),
        optimizer_steps=4908, optimizer_restored_exact=True, learning_rate=3e-5,
        console_masking_preserved=True, rows=153, journal_id=journal_id, first_new_record=4,
        original_source_unchanged=True, live_inbox_copied=False, torch_cuda_initialized=False,
        source_cut_imported_as_historical_records=[5844, 5845, 5846], observed_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('stage', 'sandbox', 'clone', 'math_prepare', 'math_test'))
    arguments = parser.parse_args()
    {'stage': stage, 'sandbox': sandbox_probe, 'clone': clone_state,
     'math_prepare': math_prepare, 'math_test': math_test}[arguments.action]()
