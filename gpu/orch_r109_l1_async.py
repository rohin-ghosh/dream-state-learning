"""Independent R109 arm scheduling over an immutable native training archive."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tarfile
import time


ROOT = Path('/localhome/local-rohing/orch_r109_l1_20260915')
END = 1789491360
CUTOFF = END - 300
MAX_SEGMENTS = 512
TOPOLOGY = {'FULL': [0, 1, 2], 'CONTROL': [3]}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def partition(arm, index):
    if index not in TOPOLOGY[arm]:
        raise ValueError('outside_owned_training_topology')
    if arm == 'CONTROL':
        return list(range(32)), True
    return (list(range(index * 16, (index + 1) * 16)), False) if index < 2 else ([], True)


def may_start_fit(now, segment):
    return now < CUTOFF - 600 and 0 <= segment < MAX_SEGMENTS


def alive(expected):
    try:
        directory = Path('/proc') / str(expected['pid'])
        fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
        return (fields[0] != 'Z' and fields[19] == expected['start_ticks']
                and directory.stat().st_uid == expected['uid']
                and Path('/proc/sys/kernel/random/boot_id').read_text().strip() == expected['boot_id'])
    except FileNotFoundError:
        return False


def ready(arm, jobs, occupied):
    return not any(alive(job['identity']) for job in jobs) and not set(TOPOLOGY[arm]).intersection(occupied)


def cpu_binding(cwd, pythonpath, visible_devices):
    return (Path(cwd) in (ROOT / 'source', ROOT.parent)
            and pythonpath == str(ROOT / 'source') and visible_devices == '')


def exit_codes(jobs):
    codes = []
    for job in jobs:
        if job['child'] is None:
            codes.append(None)
            continue
        code = job['child'].poll()
        if code is None:
            return None
        codes.append(code)
    return codes


def verify():
    from gpu import orch_r109_l1_run as original
    directory = Path(__file__).resolve().parent
    receipt = read(directory / 'PRE_GPU.json')
    assert receipt['cpu_passed'] is True and receipt['builder_line'].startswith('[Builder]')
    assert receipt['hard_end_unix'] == END and receipt['native_cutoff_unix'] == CUTOFF
    assert receipt['source_sha256'] == sha(__file__)
    assert receipt['supplement_archive_sha256'] == sha(directory / 'source.tar')
    with tarfile.open(directory / 'source.tar') as archive:
        members = archive.getmembers()
        assert sorted(member.name for member in members) == sorted(receipt['files'])
        for member in members:
            assert member.isfile() and member.name == Path(member.name).name
            assert hashlib.sha256(archive.extractfile(member).read()).hexdigest() == receipt['files'][member.name]
            assert sha(directory / member.name) == receipt['files'][member.name]
    plan = original.verify()
    assert plan['node'] == 'node2' and plan['train_topology'] == TOPOLOGY
    assert receipt['original_plan_sha256'] == sha(ROOT / 'PLAN.json')
    assert receipt['original_archive_sha256'] == plan['source_archive_sha256']
    assert plan['lifetime']['hard_deadline_unix'] == END
    assert plan['lifetime']['native_deadline_unix'] == CUTOFF
    return plan


def split_readout(arm, index, segment, resume):
    from gpu import orch_r109_l1_train as trainer
    from gpu.orch_rich_hot_node2_exhaustion_v3 import Engine
    from gpu.orch_r107_capability_run import readonly_condition
    from organism_v6 import orch_r107_capability as capability
    from organism_v6 import experienced_event_reader_audit_lesson as behavior
    verify()
    task_indexes, include_held = partition(arm, index)
    plan, prepared, commit, adapter, binding, proxy = trainer.load_plan(arm, resume, False)
    uuid = plan['uuid_by_index'][index]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
    loaded = trainer.native.load_stage(binding, model_dir=plan['model_dir'], device='cuda:0',
        gpu_uuid=uuid, context=trainer.native.StageContext(),
        check=lambda label: trainer.previous.common.check_deadline(plan['lifetime'], label), engine_factory=Engine)
    output = ROOT / 'fit' / arm / f'segment{segment:03d}' / 'readout'
    suite = capability.tasks()
    assert len(suite) == 32 and capability.digest(suite) == prepared['fixed32_suite_sha256']
    held = read(ROOT / 'input/prior/LEGACY_READOUT.json')['held']
    assert trainer.policy.digest(held) == prepared['held_behavior_sha256'] and held['split'] == 'HELD'
    for condition in ('ON', 'OFF'):
        directory = output / condition
        directory.mkdir(parents=True, exist_ok=True)
        result = None
        behavior_calls = []
        with readonly_condition(loaded.engine.model, 'LORA_' + condition):
            for task_index in task_indexes:
                destination = directory / f'CAPABILITY_{task_index:03d}.json'
                assert not destination.exists()
                response = loaded.engine.generate(capability.messages(suite[task_index]), max_new_tokens=512)
                trainer.write(destination, capability.capture(suite[task_index], condition, response,
                    checkpoint_sha256=adapter.state_sha256, base_sha256=trainer.policy.BASE,
                    lora_enabled=condition == 'ON'))
            if include_held:
                def generate(messages):
                    destination = directory / f'BEHAVIOR_{len(behavior_calls):03d}.json'
                    assert not destination.exists()
                    response = loaded.engine.generate(messages, max_new_tokens=160)
                    trainer.write(destination, response)
                    behavior_calls.append(response)
                    return response
                result = behavior.collect_cases(held, generate, coached=False)
                assert len(behavior_calls) == 16
        loaded.verify_unchanged()
        trainer.write(directory / f'PART_{index}_COMPLETE.json', dict(condition=condition,
            capability_indexes=task_indexes, capability_calls=len(task_indexes), behavior_calls=len(behavior_calls),
            behavior=result['summary'] if result else None, fixed32_suite_sha256=prepared['fixed32_suite_sha256'],
            checkpoint_state_sha256=adapter.state_sha256, held_behavior_sha256=prepared['held_behavior_sha256'],
            source_sha256=sha(__file__), base_and_adapter_unchanged=True, parent_access=False,
            training_ingestion=False, finished_unix=time.time()))


def finish_readout(arm, segment):
    from gpu import orch_r109_l1_train as trainer
    from organism_v6 import orch_r107_capability as capability
    directory = ROOT / 'fit' / arm / f'segment{segment:03d}'
    checkpoint = Path(read(directory / 'COMPLETE.json')['checkpoint'])
    adapter = trainer.storage.verify_checkpoint(checkpoint)['metadata']['adapter']['state_sha256']
    prepared = read(ROOT / 'PREPARED.json')
    summaries = {}
    for condition in ('ON', 'OFF'):
        output = directory / 'readout' / condition
        complete = output / 'COMPLETE.json'
        if not complete.exists():
            parts = [read(output / f'PART_{index}_COMPLETE.json') for index in TOPOLOGY[arm]]
            assert sorted(position for part in parts for position in part['capability_indexes']) == list(range(32))
            assert sum(part['behavior_calls'] for part in parts) == 16
            assert all(part['checkpoint_state_sha256'] == adapter and part['base_and_adapter_unchanged']
                       and part['fixed32_suite_sha256'] == prepared['fixed32_suite_sha256']
                       and part['held_behavior_sha256'] == prepared['held_behavior_sha256'] for part in parts)
            held_part = next(part for part in parts if part['behavior_calls'])
            trainer.write(complete, dict(status='COMPLETE', condition=condition, capability_calls=32,
                behavior_calls=16, behavior=held_part['behavior'], checkpoint_state_sha256=adapter,
                fixed32_suite_sha256=prepared['fixed32_suite_sha256'], held_behavior_sha256=prepared['held_behavior_sha256'],
                base_and_adapter_unchanged=True, parent_access=False, training_ingestion=False,
                split_execution=True, finished_unix=time.time()))
        summaries[condition] = read(complete)
        assert summaries[condition]['checkpoint_state_sha256'] == adapter
        assert summaries[condition]['capability_calls'] == 32 and summaries[condition]['behavior_calls'] == 16
        assert len(list(output.glob('CAPABILITY_*.json'))) == 32 and len(list(output.glob('BEHAVIOR_*.json'))) == 16
    records = [read(path) for path in sorted((directory / 'readout').glob('*/CAPABILITY_*.json'))]
    summary = capability.reduce_paired(records, checkpoint_sha256=adapter, base_sha256=trainer.policy.BASE, max_new_tokens=512)
    destination = directory / 'PAIRED_FIXED32.json'
    if not destination.exists():
        trainer.write(destination, summary)
    trainer.write(directory / 'ASYNC_READOUT_ACCEPTED.json', dict(update=int(checkpoint.name),
        checkpoint_commit_sha256=sha(checkpoint / 'COMMIT.json'), checkpoint_state_sha256=adapter,
        reduction_sha256=sha(destination), readouts=summaries, finished_unix=time.time(),
        claim='CONTROLLED_DIAGNOSTICS_NOT_ESTABLISHED_RETAINED_LEARNING'))
    return checkpoint


def takeover():
    from gpu import orch_r109_l1_run as original
    from gpu.orch_r109_l1_ops import identity
    candidates = []
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            arguments = (directory / 'cmdline').read_bytes().split(b'\0')
            if b'gpu.orch_r109_l1_run' in arguments and b'fit-supervise' in arguments:
                assert directory.stat().st_uid == os.getuid()
                environment = dict(value.split(b'=', 1) for value in (directory / 'environ').read_bytes().split(b'\0') if b'=' in value)
                assert cpu_binding((directory / 'cwd').resolve(), environment.get(b'PYTHONPATH', b'').decode(),
                                   environment.get(b'CUDA_VISIBLE_DEVICES', b'').decode())
                candidates.append(identity(int(directory.name)))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    assert len(candidates) == 1, 'exactly_one_owned_old_cpu_supervisor'
    expected = candidates[0]
    descriptor = os.pidfd_open(expected['pid'])
    killed = False
    try:
        assert identity(expected['pid']) == expected
        signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
        time.sleep(0.2)
        launches = [(path, read(path)) for path in ROOT.glob('*_LAUNCH.json')
                    if path.name.startswith(('fit_', 'readout_'))]
        segment = max(int(row['arguments'][row['arguments'].index('--segment') + 1]) for path, row in launches)
        latest = [(path, row) for path, row in launches
                  if int(row['arguments'][row['arguments'].index('--segment') + 1]) == segment]
        phase = 'readout' if any(row['arguments'][0] == 'readout' for path, row in latest) else 'train'
        group = [(path, row) for path, row in latest if row['arguments'][0] == phase]
        assert len(group) == 4 and sorted(row['index'] for path, row in group) == list(range(4)), 'complete_dispatch_group_required'
        known = {row['identity']['pid'] for path, row in group}
        for directory in Path('/proc').iterdir():
            if not directory.name.isdigit():
                continue
            try:
                fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
                if int(fields[1]) == expected['pid'] and fields[0] != 'Z':
                    assert int(directory.name) in known, 'unreceipted_child_handoff_rejected'
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                continue
        receipt = dict(old_cpu_identity=expected, guardian_identity=identity(os.getpid()),
            phase=phase, segment=segment, source_sha256=sha(__file__), model_jobs_untouched=True,
            hard_end_unix=END, observed_unix=time.time(),
            inherited=[dict(receipt_sha256=sha(path), **row) for path, row in group])
        assert all(row['source_archive_sha256'] == read(ROOT / 'PLAN.json')['source_archive_sha256']
                   and row['identity']['uid'] == os.getuid() and row['hard_deadline_unix'] == END
                   for path, row in group)
        original.write(Path(__file__).parent / 'CUSTODY.json', receipt)
        signal.pidfd_send_signal(descriptor, signal.SIGKILL)
        killed = True
        return receipt
    finally:
        if not killed and alive(expected):
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


def launch(plan, arm, phase, segment, resume, index, rank):
    from gpu import orch_r109_l1_run as original
    from gpu.orch_r109_l1_ops import identity
    verify()
    report = original.scan('node2', index)
    label = f'async_{phase}_{segment}_{arm}_{index}'
    original.write(ROOT / 'admissions' / f'{label}_{time.time_ns()}.json', report)
    if not report['clear']:
        return None
    assert report['scanner_euid'] == 0 and report['gpu']['uuid'] == plan['uuid_by_index'][index]
    arguments = [phase, '--arm', arm, '--index', str(index), '--segment', str(segment), '--resume', str(resume)]
    module = 'orch_r109_l1_async'
    if phase == 'train':
        module = 'gpu.orch_r109_l1_train'
        arguments += ['--rank', str(rank), '--world-size', str(len(TOPOLOGY[arm]))]
    with (ROOT / (label + '.log')).open('x') as log:
        child = subprocess.Popen([original.PYTHON, '-B', '-u', '-m', module, *arguments],
            cwd=ROOT / 'source', stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True, env=dict(os.environ,
                PYTHONPATH=str(Path(__file__).parent) + ':' + str(ROOT / 'source'),
                CUDA_VISIBLE_DEVICES=plan['uuid_by_index'][index], HF_HUB_OFFLINE='1',
                TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
                MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false'))
    expected = identity(child.pid)
    receipt = dict(identity=expected, index=index, uuid=plan['uuid_by_index'][index], module=module,
        arguments=arguments, source_archive_sha256=plan['source_archive_sha256'],
        async_source_sha256=sha(__file__), hard_deadline_unix=END, started_unix=time.time())
    original.write(ROOT / (label + '_LAUNCH.json'), receipt)
    return dict(**receipt, child=child)


def recovery_custody():
    from gpu import orch_r109_l1_run as original
    from gpu.orch_r109_l1_ops import identity
    prior = ROOT / 'async_v2'
    old_cpu = read(prior / 'CPU_LAUNCH.json')['identity']
    assert not alive(old_cpu) and (prior / 'FAILURE.json').exists()
    inherited = []
    for arm, indexes in TOPOLOGY.items():
        complete_path = ROOT / 'fit' / arm / 'segment004/COMPLETE.json'
        complete = read(complete_path)
        assert complete['update'] == 9572
        from organism_v6 import orch_combined_l1_continual as storage
        assert storage.verify_checkpoint(Path(complete['checkpoint']))['metadata']['update'] == 9572
        for index in indexes:
            path = ROOT / f'async_train_4_{arm}_{index}_LAUNCH.json'
            row = read(path)
            assert not alive(row['identity']) and row['index'] == index
            inherited.append(dict(row, receipt_sha256=sha(path)))
    receipt = dict(old_cpu_identity=old_cpu, guardian_identity=identity(os.getpid()),
        phase='train', segment=4, inherited=inherited, source_sha256=sha(__file__),
        original_failure_sha256=sha(prior / 'FAILURE.json'), observed_unix=time.time(),
        model_jobs_untouched=True, hard_end_unix=END,
        recovery='COMMITTED9572_ONLY_READOUT_NEXT_NO_OPTIMIZER_REPLAY')
    original.write(Path(__file__).parent / 'CUSTODY.json', receipt)
    return receipt


def supervise(recover=False):
    import fcntl
    from gpu import orch_r109_l1_run as original
    plan = verify()
    directory = Path(__file__).parent
    lock = (directory / 'LOCK').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not (directory / 'CUSTODY.json').exists(), 'explicit_recovery_required_no_counter_reset'
    custody = recovery_custody() if recover else takeover()
    states = {}
    for arm in TOPOLOGY:
        jobs = [dict(row, child=None) for row in custody['inherited']
                if row['arguments'][row['arguments'].index('--arm') + 1] == arm]
        states[arm] = dict(phase=custody['phase'], segment=custody['segment'], jobs=jobs,
                          pending=False, resume=None, terminal=False)
    try:
        while not all(state['terminal'] for state in states.values()):
            now = time.time()
            if now >= END - 45:
                break
            jobs = [job for state in states.values() for job in state['jobs']]
            occupied = {job['index'] for job in jobs if alive(job['identity'])}
            for arm, state in states.items():
                if state['terminal']:
                    continue
                if not state['pending']:
                    if not ready(arm, state['jobs'], occupied):
                        continue
                    codes = exit_codes(state['jobs'])
                    if codes is None:
                        continue
                    original.write(directory / f'EXIT_{arm}_{state["segment"]}_{state["phase"]}.json',
                        dict(returncodes=codes, identities=[job['identity'] for job in state['jobs']], observed_unix=time.time()))
                    assert all(code in (None, 0) for code in codes), 'stage_failed_preserve_evidence'
                    if state['phase'] == 'train':
                        complete = read(ROOT / 'fit' / arm / f'segment{state["segment"]:03d}' / 'COMPLETE.json')
                        assert complete['update'] == 8932 + 128 * (state['segment'] + 1)
                        state['resume'] = Path(complete['checkpoint'])
                        state['phase'] = 'readout'
                    else:
                        state['resume'] = finish_readout(arm, state['segment'])
                        state['segment'] += 1
                        state['phase'] = 'train'
                    state['jobs'] = []
                    state['pending'] = True
                if state['phase'] == 'train' and not may_start_fit(now, state['segment']):
                    state['terminal'] = True
                    continue
                if now >= CUTOFF:
                    state['terminal'] = True
                    continue
                for rank, index in enumerate(TOPOLOGY[arm]):
                    if any(job['index'] == index for job in state['jobs']):
                        continue
                    job = launch(plan, arm, state['phase'], state['segment'], state['resume'], index, rank)
                    if job is None:
                        break
                    state['jobs'].append(job)
                state['pending'] = len(state['jobs']) != len(TOPOLOGY[arm])
            original.write(directory / 'HEARTBEAT.json', dict(observed_unix=time.time(), hard_end_unix=END,
                native_cutoff_unix=CUTOFF, maximum_total_segments_per_arm=MAX_SEGMENTS,
                independent_arms=True, compare_only_matched_updates=True, source_sha256=sha(__file__),
                arms={arm:dict(phase=state['phase'], segment=state['segment'], pending=state['pending'],
                    terminal=state['terminal'], resume=str(state['resume']),
                    processes=[dict(identity=job['identity'], index=job['index'], alive=alive(job['identity']))
                               for job in state['jobs']]) for arm, state in states.items()}))
            time.sleep(2)
    except BaseException as failure:
        original.write(directory / 'FAILURE.json', dict(type=type(failure).__name__,
            message=str(failure), observed_unix=time.time(), remaining_jobs_guarded_until_original_end=True))
        raise
    finally:
        while any(alive(job['identity']) for state in states.values() for job in state['jobs']) and time.time() < END - 45:
            time.sleep(2)
        for state in states.values():
            for job in state['jobs']:
                expected = job['identity']
                if alive(expected):
                    descriptor = os.pidfd_open(expected['pid'])
                    try:
                        if alive(expected):
                            original.write(directory / f'HARD_STOP_{expected["pid"]}.json', dict(identity=expected, observed_unix=time.time(), reason='FIXED_R109_HARD_END'))
                            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                            time.sleep(5)
                            if alive(expected):
                                signal.pidfd_send_signal(descriptor, signal.SIGKILL)
                    finally:
                        os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['supervise', 'recover', 'readout', 'verify'])
    parser.add_argument('--arm', choices=list(TOPOLOGY))
    parser.add_argument('--index', type=int)
    parser.add_argument('--segment', type=int)
    parser.add_argument('--resume', type=Path)
    options = parser.parse_args()
    if options.action in ('supervise', 'recover'):
        supervise(options.action == 'recover')
    elif options.action == 'verify':
        plan = verify()
        print(json.dumps(dict(status='PASS', plan_sha256=sha(ROOT / 'PLAN.json'), source_sha256=sha(__file__))))
    else:
        split_readout(options.arm, options.index, options.segment, options.resume)
