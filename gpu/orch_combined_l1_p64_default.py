"""Additional128 minimal-prompt calls after historical P64 releases its GPUs."""

import argparse
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_combined_l1_continual_run as run
from gpu.orch_combined_l1_continual_guard import admit_devices
from organism_v6 import orch_combined_l1_dev as policy
from organism_v6 import orch_combined_l1_behavior as behavior


def readout(root, arm, index):
    plan = policy.validate_plan(run.read(root / 'DEV_PLAN.json'))
    prepared = run.validate(root)
    assert run.sha(root / 'COHORT.json') == plan['cohort_sha256']['COHORT.json']
    source = run.MATH_ROOT / ('SCALE764_' + arm) / 'fit/COMPLETE.json'
    fit = run.read(source)
    assert fit['status'] == 'COMPLETE' and fit['updates'] == 6208
    assert run.read(run.MATH_ROOT / 'COHORT.json')['tasks'] == run.read(root / 'COHORT.json')['tasks']
    output = root / 'P64_DEFAULT' / arm / 'readout'
    output.mkdir(parents=True, exist_ok=False)
    lifetime = run.read(root / 'LIFETIME.json')
    uuid = run.DEVICES[index]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid and index == (0 if arm == 'FULL' else 1)
    count = 0
    try:
        identity = run.common.bridge.AdapterIdentity.from_document(fit['output_adapter'])
        binding = run.common.bridge.StageBinding(root.name + '_P64_DEFAULT', run.common.bridge.ARMS[1], 0,
            'sealed_readout', identity, False, True, run.sha(root / 'DEV_PLAN.json'))
        loaded = run.native.load_stage(binding, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
            context=run.native.StageContext(), check=lambda label: run.common.check_deadline(lifetime, label),
            predecessor_processes=(tuple(fit['process']),), engine_factory=run.common.ReadoutEngine)
        run.write(output / 'LOADED.json', dict(process=loaded.process, observed=loaded.observed.document(),
            parent_present=False, fit_sha256=run.sha(source), historical_prompted_P64_unchanged=True,
            prompt_condition='MINIMAL_DEFAULT_ADDON', loaded_unix=time.time()))
        outcomes = []
        for task in run.read(root / 'COHORT.json')['tasks']:
            assert count < 64
            run.common.check_deadline(lifetime, 'p64_default_reserve')
            path = output / f'CALL_{count:03d}.json'
            record = dict(position=count, messages=policy.default_math_messages(task), max_new_tokens=1536,
                metadata=dict(purpose='math_held', task_id=task['id']), status='RESERVED',
                prompt_condition='MINIMAL_DEFAULT_ADDON', started_unix=time.time(), parent_present=False)
            assert not path.exists()
            run.write(path, record)
            count += 1
            try:
                response = loaded.engine.generate(record['messages'], max_new_tokens=1536)
                record.update(status='COMPLETE', response=response,
                    richness=dict(behavior.describe(response['raw']), tokens=behavior.token_metrics(response, 1536)))
                outcomes.append(dict(task_id=task['id'], family=task['family'], **run.common.transfer.score(task, response)))
                run.write(output / 'MATH_ROWS.json', outcomes)
            except BaseException as error:
                record.update(status='FAILED', error=dict(type=type(error).__name__, message=str(error)))
                raise
            finally:
                record['finished_unix'] = time.time()
                run.write(path, record)
                if count == 1:
                    run.write(output / 'FIRST_CALL.json', dict(path=path.name, sha256=run.sha(path), status=record['status']))
        observed = loaded.verify_unchanged()
        run.write(output / 'COMPLETE.json', dict(status='COMPLETE', calls=count, observed=observed.document(),
            parent_calls=0, training_updates=0, no_promotion_claim=True, report_order=['richness', 'accuracy']))
    except BaseException as error:
        run.write(output / 'FAILED.json', dict(status='FAILED', calls=count, type=type(error).__name__, message=str(error)))
        raise


def watch(root):
    policy.validate_plan(run.read(root / 'DEV_PLAN.json'))
    output = root / 'P64_DEFAULT'
    output.mkdir(exist_ok=False)
    run.write(output / 'REGISTERED.json', dict(calls=128, cohort_sha256=run.sha(root / 'COHORT.json'),
        plan_sha256=run.sha(root / 'DEV_PLAN.json'), parent_present=False, registered_unix=time.time(),
        historical_prompted_readout_first=True, devices=[0, 1]))
    children = []
    try:
        for arm, index in (('OFF', 1), ('FULL', 0)):
            historical = run.MATH_ROOT / ('SCALE764_' + arm) / 'readout'
            start = run.read(root / 'P64_HISTORICAL_REPAIR' / f'{arm}_START.json')
            while True:
                assert time.time() < run.read(root / 'LIFETIME.json')['native_deadline_unix']
                try:
                    live = run.common.process_identity(start['pid']) == start['identity']
                except (FileNotFoundError, ProcessLookupError):
                    live = False
                if not live:
                    break
                time.sleep(2)
            assert (historical / 'AFTER.json').exists() or (historical / 'FAILED.json').exists(), 'historical_exit_evidence_missing'
            assert run.read(run.MATH_ROOT / ('SCALE764_' + arm) / 'fit/COMPLETE.json')['status'] == 'COMPLETE'
            admit_devices(root, (index,), f'P64_DEFAULT_{index}')
            stream = (output / f'{arm}.log').open('x')
            command = [run.PYTHON, '-B', '-m', 'gpu.orch_combined_l1_p64_default', '--root', str(root),
                       '--arm', arm, '--index', str(index)]
            child = subprocess.Popen(command, cwd=root / 'source', env=dict(os.environ,
                CUDA_VISIBLE_DEVICES=run.DEVICES[index], PYTHONDONTWRITEBYTECODE='1'),
                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            identity = run.common.process_identity(child.pid)
            children.append((child, identity, stream))
            run.write(output / f'{arm}_START.json', dict(pid=child.pid, identity=identity, index=index, command=command))
        while any(child.poll() is None for child, _, _ in children):
            assert time.time() < run.read(root / 'LIFETIME.json')['native_deadline_unix']
            time.sleep(1)
    except BaseException as error:
        run.write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error), time_unix=time.time()))
    finally:
        for child, identity, stream in children:
            run.common.stop_owned(child, identity)
            stream.close()
        if children:
            admit_devices(root, (0, 1), 'P64_DEFAULT_RELEASE')
            run.write(output / 'RELEASED.json', dict(returncodes=[child.returncode for child, _, _ in children],
                actual_reserved_calls=len(list(output.glob('*/readout/CALL_*.json'))), released_unix=time.time(),
                failures_preserved=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--arm', choices=('FULL', 'OFF'))
    parser.add_argument('--index', type=int, choices=(0, 1))
    options = parser.parse_args()
    if options.arm:
        readout(options.root, options.arm, options.index)
    else:
        watch(options.root)
