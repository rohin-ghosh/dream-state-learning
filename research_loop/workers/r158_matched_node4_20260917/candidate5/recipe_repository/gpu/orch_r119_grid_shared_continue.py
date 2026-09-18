"""Prospective shared GRID clock and custody; never re-arm completed FINAL."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


SOURCE = Path(__file__).resolve().parents[1]
CLOCK_SOURCE = Path('/localhome/local-rohing/orch_r119_lease_continuation_20260915/source')
CLOCK = dict(path='/localhome/local-rohing/orch_r119_lease_continuation_20260915/CLOCK.json',
             sha256='a1aa51349c1784ec9f78e6411912576be43b55942c5fcdf1858ca391fd81c510')
BACKEND_SHA = '33a30aa1793a053ca603a9c3e2c4e5fde477b35b99d858af87dfa980036a065c'
TERMINAL = 'R119_GRID_SHARED_TERMINAL.json'
FINAL_SHAS = {'F4':'6385075a2ff37d4e820a443606924dd7e80b7c1ca7175bf2a64401e4db345cd7',
              'A4':'b653284f13b3fe61cbd12f0671d32788c8aa8df56dd46136efce7320e12de091'}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def ref(path):
    path = Path(path)
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def read(reference):
    require(ref(reference['path']) == reference, 'immutable_reference')
    return json.loads(Path(reference['path']).read_text())


def write(path, document):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as output:
        json.dump(document, output, indent=2, sort_keys=True)
        output.write('\n')
    return ref(path)


def overlay(bounds, clock):
    result = dict(bounds, hard_end_unix=clock['hard_end_unix'],
                  train_end_unix=clock['train_end_unix'], parent_wait_seconds=600)
    require(all(result[key] == value for key, value in bounds.items()
                if key not in ('hard_end_unix', 'train_end_unix', 'parent_wait_seconds')),
            'no_counter_quota_reset')
    return result


def final_metadata(branch):
    root = Path('/localhome/local-rohing/orch_r118_grid_final_parallel_20260915_attempt1') / branch
    complete = dict(path=str(root / 'COMPLETE.json'), sha256=FINAL_SHAS[branch])
    read(complete)
    terminal = ref(root / 'TERMINAL.json')
    document = read(terminal)
    require(document['status'] == 'COMPLETE' and document['exit_code'] == 0 and document['no_retry'] is True,
            'original_FINAL_COMPLETE_never_rearm')
    return dict(complete=complete, terminal=terminal, ledger=ref(root / 'EVAL_LEDGER.json'),
                completed_calls=8, retry=False, evaluator_calls=0)


def modules(plan):
    require(ref(CLOCK_SOURCE / 'gpu/orch_r118_parallel_consolidation.py')['sha256'] == BACKEND_SHA,
            'Main_exact_continuation_backend')
    os.environ['ORCH_R119_LEASE_CLOCK'] = CLOCK['path']
    os.environ['ORCH_R119_LEASE_CLOCK_SHA256'] = CLOCK['sha256']
    sys.path.insert(0, plan['runtime'])
    import gpu
    gpu.__path__.insert(0, str(CLOCK_SOURCE / 'gpu'))
    from gpu import orch_r119_lease_clock as clock_module
    clock = clock_module.validate(CLOCK, backend_path=CLOCK_SOURCE / 'gpu/orch_r118_parallel_consolidation.py')
    path = SOURCE / 'gpu/orch_r118_grid_parallel_run.py'
    spec = importlib.util.spec_from_file_location('r119_private_grid_runner', path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runner.__file__ = __file__
    runner.TERMINAL = TERMINAL
    handoff, loop = runner.modules(plan)
    require(Path(handoff.parallel.__file__).resolve() == CLOCK_SOURCE / 'gpu/orch_r118_parallel_consolidation.py',
            'actual_backend_is_clock_bound')
    run = handoff.run
    old_end, old_train = run.grid.END, run.grid.TRAIN_END

    def inherited(config):
        require(config['hard_end_unix'] == old_end and config['train_end_unix'] == old_train,
                'historical_CONFIG_walls_unchanged')
        return dict(hard_end_unix=old_end, train_end_unix=old_train, final_unix=run.grid.policy.FINAL_UNIX,
            max_native_calls=run.grid.MAX_NATIVE, max_parent_calls=run.grid.MAX_PARENT, physical=config['physical'],
            parent_wait_seconds=600 if run.branch_for(config) == 'F4' else 120)

    run.inherited_bounds = inherited
    run.grid.END, run.grid.TRAIN_END = clock['hard_end_unix'], clock['train_end_unix']
    run.grid.policy.HARD_END_UNIX = clock['hard_end_unix']
    run.life_class = lambda branch: run.F4SharedLife if branch in ('F4', 'A4') else fail('owned_branch')
    require(plan['bounds'] == overlay(read(plan['boundary'])['bounds'], clock), 'explicit_new_branch_clock')
    validator = inspect.getsource(runner.validate)
    before = "plan['bounds'] == boundary['bounds'] == handoff.run.inherited_bounds(config)"
    require(validator.count(before) == 1, 'exact_original_bound_validation')
    validator = validator.replace(before,
        "boundary['bounds'] == handoff.run.inherited_bounds(config) and plan['bounds'] == overlay(boundary['bounds'], clock)")
    namespace = dict(runner.__dict__, overlay=overlay, clock=clock)
    exec(compile(validator, __file__ + ':clock_validate', 'exec'), namespace)
    runner.validate = namespace['validate']

    def supervision(certificate, **unused):
        retained = certificate['retained_supervision']
        require(retained['native_identity'] == certificate['identity']
                and retained['owner_verified_safe_for_parallel'] is True, 'same_actual_native')
        for identity in (certificate['identity'], retained['guard_identity']):
            handoff.parallel.live_identity(identity)
        binding = read(retained['guard_binding'])
        require(binding['native_identity'] == certificate['identity'] and binding['terminal_filename'] == TERMINAL,
                'actual_continuation_guard')
        require(len(retained['final_identity_bindings']) == 1, 'one_completed_FINAL_custodian')
        item = retained['final_identity_bindings'][0]
        handoff.parallel.live_identity(item['identity'])
        evidence = read(item['evidence'])
        require(evidence['role'] == 'COMPLETED_FINAL_CUSTODIAN_NO_EVALUATION'
                and evidence['custodian_identity'] == item['identity']
                and evidence['completed_final'] == final_metadata(certificate['branch'])
                and evidence['native_identity'] == certificate['identity'], 'completed_FINAL_not_new_timer')
        return retained

    handoff.supervision = supervision

    def scan(root):
        config, unused_activation, unused_boundary = run.validate(root)
        if os.geteuid() != 0:
            command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                'python3', '-B', str(Path(__file__).resolve()), 'scan', '--plan', plan['_reference']['path'],
                '--sha256', plan['_reference']['sha256']]
            return json.loads(subprocess.check_output(command, text=True, timeout=100))
        from types import SimpleNamespace
        run.grid.admission.minor.pinned.policy = SimpleNamespace(DEVICES={config['physical']: config['uuid']},
            HOST_SHA=run.grid.HOST_SHA, require=require,
            allocation=lambda physical: require(physical == config['physical'], 'assigned_GRID_only'))
        return run.admission.scan(config['physical'], Path(root) / 'SERVICE_IDENTITY.json')

    run.scan = scan

    def spawn_readout(root, cycle, scope, session):
        require(scope == 'dev', 'completed_FINAL_never_dispatched_again')
        folder = Path(root) / 'shared_readout_bindings'
        binding = folder / f'{cycle:04d}_{scope}.json'
        write(binding, dict(cycle=cycle, scope=scope, session=deepcopy(session),
            predecessor_processes=[list(run.client.native.process_identity())], parent_calls=0, carry_access=False))
        command = [run.grid.PYTHON, '-B', str(Path(__file__).resolve()), 'readout', '--plan',
            plan['_reference']['path'], '--sha256', plan['_reference']['sha256'], '--binding', str(binding)]
        with (folder / f'{cycle:04d}_{scope}.log').open('x') as log:
            result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                timeout=max(1, run.grid.END-time.time()-3))
        require(result.returncode == 0, 'fresh_DEV_failure_preserved_no_retry')

    run.spawn_readout = spawn_readout
    loop.fresh_dev.__kwdefaults__['readout'] = spawn_readout
    return runner, handoff, loop


def fail(reason):
    raise ValueError(reason)


def guard(plan, runner, handoff, loop):
    root, config, boundary = runner.validate(plan, handoff)
    directory = Path(plan['directory'])
    (directory / 'GUARD_ONCE').mkdir()
    identity = handoff.parallel.process_identity()
    write(directory / 'CPU_LAUNCH.json', dict(identity=identity, terminal_filename=TERMINAL,
                                             plan=plan['_reference']))
    child = None
    try:
        for attempt in range(120):
            report = handoff.run.scan(root)
            write(directory / 'admission' / f'{attempt:03d}.json', report)
            if report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']:
                require(report['gpu']['uuid'] == config['uuid'], 'actual_assigned_UUID')
                break
            time.sleep(2)
        else:
            raise ValueError('strict_admission_failed')
        runner.validate(plan, handoff)
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'native', '--plan',
                   plan['_reference']['path'], '--sha256', plan['_reference']['sha256']]
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=config['uuid'])
        with (directory / 'NATIVE.log').open('x') as log:
            child = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        write(directory / 'CHILD_LAUNCH.json', dict(pid=child.pid, command=command, observed_unix=time.time()))
        runner.wait_file(directory / 'NATIVE_IDENTITY.json', time.time()+120, handoff.run.check_deadline)
        native = json.loads((directory / 'NATIVE_IDENTITY.json').read_text())['identity']
        binding = write(directory / 'GUARD_BINDING.json', dict(native_identity=native,
            guard_identity=identity, root=str(root), terminal_filename=TERMINAL))
        custody_command = [sys.executable, '-B', str(Path(__file__).resolve()), 'custody', '--plan',
            plan['_reference']['path'], '--sha256', plan['_reference']['sha256']]
        with (directory / 'CUSTODY.log').open('x') as log:
            custody = subprocess.Popen(custody_command, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''),
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        runner.wait_file(directory / 'CUSTODY_IDENTITY.json', time.time()+60, handoff.run.check_deadline)
        custodian = json.loads((directory / 'CUSTODY_IDENTITY.json').read_text())
        evidence = write(directory / 'COMPLETED_FINAL_CUSTODY.json', dict(root=str(root),
            role='COMPLETED_FINAL_CUSTODIAN_NO_EVALUATION', native_identity=native,
            custodian_identity=custodian, completed_final=final_metadata(plan['branch']), evaluator_calls=0))
        support = dict(branch=plan['branch'], root=str(root), identity=native,
            retained_supervision=dict(native_identity=native, guard_identity=identity, guard_binding=binding,
                owner_verified_safe_for_parallel=True,
                final_identity_bindings=[dict(identity=custodian, evidence=evidence)]))
        handoff.supervision(support)
        write(directory / 'SUPERVISION.json', support)
        code = child.wait(timeout=max(1, plan['bounds']['hard_end_unix']-time.time()))
        write(root / TERMINAL, dict(status='COMPLETE' if code == 0 else 'FAILED', exit_code=code,
                                    no_retry=True, finished_unix=time.time()))
    except BaseException as error:
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            child.wait(timeout=15)
        if not (root / TERMINAL).exists():
            write(root / TERMINAL, dict(status='FAILED', error=str(error), no_retry=True, finished_unix=time.time()))
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('validate', 'scan', 'guard', 'native', 'custody', 'readout'))
    parser.add_argument('--plan', required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--binding')
    args = parser.parse_args()
    reference = dict(path=args.plan, sha256=args.sha256)
    plan = read(reference)
    plan['_reference'] = reference
    runner, handoff, loop = modules(plan)
    if args.mode == 'guard':
        guard(plan, runner, handoff, loop)
    elif args.mode == 'native':
        runner.native(plan, handoff, loop)
    elif args.mode == 'scan':
        print(json.dumps(handoff.run.scan(Path(plan['root']))))
    elif args.mode == 'readout':
        require(json.loads(Path(args.binding).read_text())['scope'] == 'dev', 'no_FINAL_retry')
        handoff.run.readout(Path(plan['root']), Path(args.binding))
    elif args.mode == 'custody':
        write(Path(plan['directory']) / 'CUSTODY_IDENTITY.json', handoff.parallel.process_identity())
        while time.time() < plan['bounds']['hard_end_unix']:
            final_metadata(plan['branch'])
            if (Path(plan['root']) / TERMINAL).exists():
                break
            time.sleep(10)
    else:
        handoff.validate_snapshot(read(plan['boundary']))
        final_metadata(plan['branch'])
        print(json.dumps(dict(status='CPU_READY_NO_DISPATCH', branch=plan['branch'], clock=CLOCK)))


if __name__ == '__main__':
    main()
