"""Receiver-only assembly and CPU gates; never touches old lives or leases."""

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tarfile
import time


ROOT = Path(__file__).resolve().parent
RELEASE = ROOT / 'r206_ready'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
SNAPSHOT_SHA = '9beaf7a79063c5cf4af2868e1f3122dfea7f4fa5ce3f7d3f2f51716676cdee34'
OVERLAY_SHA = 'ab7c3ada0780d8414aba30e59721df1bb8c51fdee747105359682bae3c144f84'
REFERENCE_SHA = '3d0d9dc7fbdefc7ccc24c2625b56b05a6a8c07baea41e3753038813f86da541d'
ARMS = {
    'fresh_math': (1, 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821', 'R205_FRESH_MATH_FIRST_PRINCIPLES'),
    'frozen_c2': (0, 'GPU-0ee6f753-c61e-e18a-8aea-acccd3042939', 'R205_PARENTED_NO_WEIGHT_UPDATES'),
    'peer_math': (2, 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1', 'R205_PEER_MATH'),
    'peer_repo': (3, 'GPU-e1277146-04f2-c38f-d1ae-1a98132f907e', 'R205_PEER_REPO'),
    'p4': (4, 'GPU-f484c608-a2d4-0c26-dee1-a06cc5ae69e4', 'R205_P4'),
    'p32': (5, 'GPU-bc211959-642d-664b-3581-42a0dbe434e9', 'R205_P32'),
    'lr03': (6, 'GPU-1a83d900-1e95-c7b4-9b12-8117399697f8', 'R205_LR03'),
    'lr3': (7, 'GPU-319224de-e668-1822-d80b-4b24d15968ae', 'R205_LR3'),
    'conversational': (0, 'GPU-0ee6f753-c61e-e18a-8aea-acccd3042939', 'R206_NODE3_CONVERSATIONAL'),
    'r213_math_a': (1, 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821', 'R213_MATH_A'),
    'r213_math_c': (4, 'GPU-f484c608-a2d4-0c26-dee1-a06cc5ae69e4', 'R213_MATH_C'),
    'r213_math_b_fork': (2, 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1', 'R213_NEW_MATH_B'),
    'r213_siege_scout_fork': (3, 'GPU-e1277146-04f2-c38f-d1ae-1a98132f907e', 'R213_NEW_SIEGE_SCOUT'),
    'r213_siege_negotiator_fork': (5, 'GPU-bc211959-642d-664b-3581-42a0dbe434e9', 'R213_NEW_SIEGE_NEGOTIATOR'),
    'r213_siege_quartermaster_fork': (6, 'GPU-1a83d900-1e95-c7b4-9b12-8117399697f8', 'R213_NEW_SIEGE_QUARTERMASTER'),
    'r213_siege_challenger_fork': (7, 'GPU-319224de-e668-1822-d80b-4b24d15968ae', 'R213_NEW_SIEGE_CHALLENGER'),
}


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def extract(archive_path, destination, expected):
    with tarfile.open(archive_path) as archive:
        members = archive.getmembers()
        require(len(members) == len(expected) and len({member.name for member in members}) == len(members)
            and all(member.isfile() and member.name in expected and not Path(member.name).is_absolute()
                and '..' not in Path(member.name).parts for member in members), 'exact_regular_archive_members')
        archive.extractall(destination, filter='data')
    require(all(sha(destination / name) == expected_sha for name, expected_sha in expected.items()), 'receiving_all_file_hashes')


def prepare(name):
    require(socket.gethostname() == '[REDACTED_HOST]' and ROOT.name == 'orch_r205_node3_20260918', 'owned_node3_receiver')
    snapshot = ROOT / 'snapshot'
    manifest = read(ROOT / 'MANIFEST.json')
    require(sha(ROOT / 'MANIFEST.json') == '29ca04c2c51671c7df922a4b05448586e74eec35da45b03009877baccbccce84', 'fixed_manifest')
    if not snapshot.exists():
        require(sha(ROOT / 'SNAPSHOT.tar') == SNAPSHOT_SHA, 'fixed_C2_archive')
        snapshot.mkdir(mode=0o700)
        extract(ROOT / 'SNAPSHOT.tar', snapshot, {item['relative']: item['sha256'] for item in manifest['files']})
    ready = read(RELEASE / 'READY.json')
    require(sha(RELEASE / 'runtime_overlay.tar.gz') == ready['archive_sha256'] == OVERLAY_SHA
        and ready['schema'] == 'R206_MAIN_TESTED_SOURCE_OVERLAY_V1'
        and len(ready['files']) == 42, 'Main_frozen_R206_new_starts_only')
    require(sha(ROOT / 'PARENT_REFERENCE.md') == REFERENCE_SHA, 'clean_C2_parent_reference')
    arm = ROOT / name
    arm.mkdir(mode=0o700)
    source = arm / 'source'
    shutil.copytree(snapshot / 'source', source)
    extract(RELEASE / 'runtime_overlay.tar.gz', source, ready['files'])
    shutil.copy2(ROOT / 'r205_runtime.py', source / 'gpu/r205_runtime.py')
    (source / 'tests').mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'test_r205_runtime.py', source / 'tests/test_r205_runtime.py')
    if name.startswith('r213_'):
        from r209_filter_resume import REPAIR_FILES, POLICY
        repair = read(ROOT / 'r209_repair/READY.json')
        require(repair['files'] == REPAIR_FILES and repair['tests']['passed']
            and repair['base_archive_sha256'] == OVERLAY_SHA
            and repair['prose_target_filter'] == POLICY, 'exact_R209_release')
        for relative, expected in REPAIR_FILES.items():
            require(sha(ROOT / 'r209_repair/source' / relative) == expected, 'R209_file_hash')
            shutil.copy2(ROOT / 'r209_repair/source' / relative, source / relative)
        for filename in ('r213_node3_runtime.py', 'r213_policy.py', 'r209_node3_audit.py'):
            shutil.copy2(ROOT / filename, source / 'gpu' / filename)
        for path in (ROOT / 'r209_repair/tests').glob('test_*.py'):
            shutil.copy2(path, source / 'tests' / path.name)
        shutil.copy2(ROOT / 'test_r213_node3.py', source / 'tests/test_r213_node3.py')
        if name.endswith('_fork'):
            for filename in ('r213_fork_runtime.py', 'r213_fork_policy.py'):
                shutil.copy2(ROOT / filename, source / 'gpu' / filename)
            shutil.copy2(ROOT / 'test_r213_forks.py', source / 'tests/test_r213_forks.py')
    physical, device, trial = ARMS[name]
    plan = deepcopy(read(snapshot / 'source_binding/PLAN.json'))
    lease_end = datetime.fromisoformat('2026-09-26T03:03:00+00:00').timestamp()
    operator_budget = 21600 if name.endswith('_fork') else 7200
    hard_end = min(time.time() + operator_budget, lease_end - 21600)
    plan.update(source_root=str(source), physical=physical, gpu_uuid=device,
        hard_end_unix=hard_end, lease_end_unix=lease_end, max_sleeps=6 if name == 'fresh_math' else 57)
    plan.update(ready['required_native_options'])
    if name == 'conversational':
        plan['max_sleeps'] = None
    if name.startswith('r213_'):
        plan['max_sleeps'] = None
    for key in ('authorized_wall_extension', 'preupdate_recovery', 'plasticity'):
        plan.pop(key, None)
    if name in ('p4', 'p32', 'lr03', 'lr3'):
        plan['plasticity'] = dict(schema='R186_PLASTICITY_V1',
            learning_rate_multiplier={'lr03': 0.3, 'lr3': 3}.get(name, 1))
        plan['new_presentations'] = {'p4': 4, 'p32': 32}.get(name, 16)
    facts = ('This R205 first-principles screen has no connected code executor, GPU experiments, network, '
        'unrestricted repository browser. Mathematical calculations are your own unexecuted reasoning. '
        'Do not claim tool verification. Parent messages are masked inputs, not training targets. ')
    if name == 'frozen_c2':
        facts += 'You retain C2 checkpoint51 and its adapter; no subsequent weight updates are performed. Only your context and own carried notes evolve.'
    elif name == 'fresh_math':
        facts += 'You start from frozen Qwen2.5-7B-Instruct with a newly initialized LoRA, no C2 weights, optimizer, or conversation history.'
        plan['root'] = str(arm / 'logical')
        plan['seed'] = 20501
        plan['birth_prompt'] = ('You are a language-model learner investigating mathematics from first principles. '
            'Choose a small mathematical question, state definitions, derive an argument, and check concrete cases by reasoning. '
            'Distinguish conjecture, example, and proof. Revise a claim when a counterexample defeats it. '
            'Only your own newly generated eligible words are learning targets; the base weights stay frozen. '
            'Astra offers sparse questions for three cycles and then withdraws for three. ' + facts)
    else:
        facts += 'You inherit the same fixed C2 checkpoint51/context5846. Only newly generated eligible own words train your LoRA.'
    if name in ('peer_math', 'peer_repo'):
        facts += ' A source-bound peer state may arrive during THINK; predict then reason-check it, never adopt a peer report as your own verified result.'
    if name == 'peer_repo':
        facts += ' Your repository task uses an actual read-only pinned source excerpt delivered by Astra; proposals are not applied or executed.'
    if name == 'conversational':
        facts = ('You are a conversational C2 copy from fixed checkpoint51 and its genuine context5846. '
            'Actual new Rohin messages receive direct prose ACT replies; their exact attributed words stay '
            'masked and pinned across sleep and compaction. Do not claim the human has read your reply. '
            'Astra is not Rohin. There is no code executor, network, or peer exchange in this branch. '
            'Keep your own views, questions, and conclusions; do not invent human messages or prior experiences.')
    (source / 'context').mkdir(exist_ok=True)
    startup = source / 'context/R205_STARTUP.md'
    startup.write_text(plan['birth_prompt'])
    plan['startup_context'] = dict(version='R127_STARTUP_V1', path=str(startup), sha256=sha(startup))
    gate = arm / 'NO_EXECUTOR.json'
    write(gate, dict(schema='R205_NO_EXECUTOR_V1', executed=False, reason=facts))
    plan['think_act_learn'] = dict(ready['required_driver_options'], trial_id=trial,
        cpu_gate_root=str(arm), cpu_gate_sha256=sha(gate), environment_facts=facts)
    if name.startswith('r213_'):
        plan['think_act_learn']['prose_target_filter'] = POLICY
        plan['think_act_learn']['environment_facts'] = (
            'R213 math trio, fixed C2 checkpoint51/context5846; new clone with inherited history, '
            'not a fresh base or matched comparison to the reused Math B. No code executor, '
            'network or host-action tools are connected. Parent and peer words remain masked '
            'context; only eligible own new English words train. Peer inputs enter only during THINK.')
        if name.endswith('_fork'):
            from r213_fork_policy import ASSIGNMENTS, GROUPS
            require(plan['new_presentations'] == 16 and 'plasticity' not in plan,
                'new_baseline16_no_inherited_P32_or_LR_treatment')
            plan['think_act_learn']['environment_facts'] = (
                'R213 NEW fixed C2 checkpoint51/context5846 fork, baseline sixteen presentations and '
                'LR0.00003. This is NOT a continuation of an interrupted node3 trial and inherits '
                'none of its partial updates. All interactions are closed text-only reasoning or '
                'fictional roleplay, no execution, real-world tools, network or host privileges. '
                'Only own eligible English targets train; parent/peer input remains masked. '
                'Native peer reception is only in THINK and restricted to the named R213 group.')
            write(arm / 'LINEAGE.json', dict(schema='R213_NEW_C2_51_FORK_V1',
                source_manifest_sha256=sha(ROOT / 'MANIFEST.json'), source_checkpoint=51,
                source_optimizer_steps=4908, source_context=5846, assignment=ASSIGNMENTS[name],
                named_peers=GROUPS[name], new_presentations=16, learning_rate=3e-5,
                interrupted_tail_inherited=False, resident_continuity_claimed=False,
                old_roots_untouched=True, operator_budget_seconds=operator_budget,
                hard_end_unix=hard_end, physical_lease_unchanged=True))
    control = arm / 'control'
    write(control / 'PLAN.json', plan)
    raw = arm / 'raw'
    raw.mkdir(mode=0o700)
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_native as native
    from gpu.r205_runtime import ControlJournal
    native.validate_plan(plan)
    require(Path(plan['model_dir']).is_dir() and Path(plan['anchors']).is_dir(), 'actual_local_base_and_anchors')
    if name != 'fresh_math':
        shutil.copytree(snapshot / 'complete', raw / 'checkpoints/sleep_000051')
        state = deepcopy(read(snapshot / 'console/CONTEXT_COMMITTED.json')['document']['state'])
        state['state']['deadline_unix'] = hard_end
        state['sha256'] = native.digest(state['state'])
        with ControlJournal(raw / 'stream', create=True) as journal:
            journal.record('R205_FIXED_C2_FORK', dict(manifest_path=str(ROOT / 'MANIFEST.json'),
                source_context_path=str(snapshot / 'console/CONTEXT_COMMITTED.json'),
                hard_end_unix=hard_end, state=state))
            require(journal.latest_checkpoint()['expected_sha256'] == state['sha256'], 'actual_source_bound_restore')
        import torch
        payload = torch.load(snapshot / 'complete/optimizer_rng.pt', map_location='cpu', weights_only=False)
        require(payload['optimizer_steps'] == 4908 and not torch.cuda.is_initialized(), 'actual_optimizer4908_CPU_restore')
        if name == 'conversational':
            archive_path = ROOT / 'FIXED_CONTEXT_INBOX.tar.gz'
            require(sha(archive_path) == '271a13510cb0d9b14d8696efac9eb19d6ac5e29ba549a6a4d368b3ac27307aa0',
                'exact_fixed_capture_inbox_archive')
            copied = []
            known_events = state['state']['history']['events']
            with tarfile.open(archive_path) as archive:
                for event in known_events:
                    if event['actor'] != 'parent' or not event['text'].startswith('Rohin: '):
                        continue
                    path = Path(event['source_id'])
                    require(path.parent == Path(plan['root']) / 'stream/inbox', 'original_Rohin_inbox_path')
                    member = archive.getmember('inbox/' + path.name)
                    require(member.isfile() and member.size < 1024 * 1024, 'bounded_original_inbox_file')
                    original = archive.extractfile(member).read()
                    require(hashlib.sha256(original).hexdigest() == event['source_sha256']
                        == manifest['inbox_hashes'][path.name], 'exact_original_Rohin_bytes')
                    message = json.loads(original)
                    require(message['speaker'] == 'Rohin' and message['actor'] == 'parent'
                        and event['text'] == 'Rohin: ' + message['text']
                        and event['event_id'] == 'parent:inbox:' + message['id'], 'genuine_known_Rohin_input_only')
                    with (raw / 'stream/inbox' / path.name).open('xb') as output:
                        output.write(original)
                    copied.append(dict(event_id=event['event_id'], source_sha256=event['source_sha256'], filename=path.name))
            write(arm / 'R206_HISTORICAL_ROHIN_INPUTS.json', dict(copied=copied,
                new_human_messages_created=0, new_human_targets=0, original_context_unchanged=True))
    write(arm / 'LEASE.json', dict(lease_end_unix=lease_end, hard_end_unix=hard_end,
        evidence=read(ROOT / 'LEASE_AND_CAPACITY.json'), actual_physical_lease_changed=False,
        operator_screen_cap_seconds=operator_budget, physical_lease_margin_seconds=21600))
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=os.pathsep.join((str(source), str(source / 'tests'))), OMP_NUM_THREADS='1')
    tests = ['tests/test_r205_runtime.py', 'tests/test_orch_r203_prose_target_filter.py',
        'tests/test_orch_r195_learn_review_filter.py',
        'tests/test_orch_r184_think_act_learn.py', 'tests/test_orch_r125_stream_journal.py']
    if name.startswith('r213_'):
        tests.remove('tests/test_orch_r203_prose_target_filter.py')
        tests += ['tests/test_existing_prose.py', 'tests/test_orch_r194_code_target_filter.py',
            'tests/test_r213_node3.py']
        if name.endswith('_fork'):
            tests += ['tests/test_r213_forks.py']
    with (arm / 'CPU.log').open('x') as output:
        result = subprocess.run([PYTHON, '-B', '-m', 'unittest', '-q', *[Path(test).stem for test in tests]],
            cwd=source, env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=150)
    require(result.returncode == 0, 'receiving_CPU_tests_must_pass_see_CPU.log')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    cpu = dict(passed=True, source_pins=pins, tests=tests, observed_unix=time.time(),
        log_sha256=sha(arm / 'CPU.log'), Main_overlay_sha256=OVERLAY_SHA, cuda_visible_devices='',
        parent_reference_sha256=REFERENCE_SHA, fixed_C2_manifest_sha256=sha(ROOT / 'MANIFEST.json'))
    write(arm / 'CPU.json', cpu)
    write(control / 'RECEIVING_CPU.json', cpu)
    write(arm / 'BUILDER.json', dict(actor='Builder', recorded_unix=time.time(),
        scope='R205_node3_only_user_authorized', cpu_sha256=sha(arm / 'CPU.json'),
        source_pins=pins, no_shared_coordination_edit_per_direct_instruction=True))
    write(control / 'ALLOCATION.json', dict(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        gpu_uuid=device, physical=physical, builder_entry_logged=True,
        cpu_receipt_path=str(arm / 'CPU.json'), cpu_receipt_sha256=sha(arm / 'CPU.json'), declared_unix=time.time()))
    config = dict(schema='R125_CONTINUAL_GUARD_V1', source_pins=pins, resume=name != 'fresh_math',
        copy_raw=str(raw), plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        attempt_dir=str(control), host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),
        hard_end_unix=hard_end, lease_path=str(arm / 'LEASE.json'), lease_sha256=sha(arm / 'LEASE.json'),
        next_reserved_unix=lease_end, allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', config)
    from gpu.orch_r125_continual_guard import validate
    validate(control / 'GUARD.json')
    write(arm / 'READY.json', dict(status='RECEIVING_CPU_PASS_NOT_DISPATCHED', physical=physical,
        source_pins=pins, plan_sha256=sha(control / 'PLAN.json'), captured_unix=time.time()))
    print(json.dumps(dict(arm=name, status='RECEIVING_CPU_PASS', physical=physical, cpu_log=str(arm / 'CPU.log'))))


def launch(name):
    arm = ROOT / name
    require(read(arm / 'CPU.json')['passed'] and not (arm / 'DISPATCHED.json').exists(), 'ready_once_only')
    source = arm / 'source'
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(source))
    processes = {}
    parent = ([PYTHON, '-B', str(ROOT / 'r213_parent.py'), name] if name.startswith('r213_')
        else [PYTHON, '-B', str(ROOT / 'r205_parent.py'), '--arm', str(arm)])
    module = 'gpu.r213_node3_runtime' if name.startswith('r213_') else 'gpu.r205_runtime'
    if name.endswith('_fork'):
        parent = [PYTHON, '-B', str(ROOT / 'r213_fork_parent.py'), name]
        module = 'gpu.r213_fork_runtime'
    for label, command in (
        ('parent', parent),
        ('supervisor', [PYTHON, '-B', '-m', module, 'dispatch', '--config', str(arm / 'control/GUARD.json')])):
        with (arm / (label + '.log')).open('x') as output:
            process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        processes[label] = dict(pid=process.pid, start_ticks=Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19])
    receipt = dict(status='DISPATCHED_NOT_LOADED_PROOF', observed_unix=time.time(), arm=name, processes=processes)
    write(arm / 'DISPATCHED.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'launch'))
    parser.add_argument('arm', choices=tuple(ARMS))
    args = parser.parse_args()
    globals()[args.mode](args.arm)
