"""Bounded actual no-adapter BASE64 and independent paired-default scheduling."""

import argparse
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_combined_l1_continual_run as run
from gpu.orch_combined_l1_dev_repair import admit as admit_devices
from organism_v6 import orch_combined_l1_base as policy
from organism_v6 import orch_combined_l1_dev as dev
from organism_v6 import orch_combined_l1_behavior as behavior


def live(identity):
    try:
        return run.common.process_identity(identity['pid']) == identity
    except (FileNotFoundError, ProcessLookupError):
        return False


def readout(root):
    plan = policy.validate(run.read(root / 'BASE_PLAN.json'))
    assert run.sha(root / 'COHORT.json') == plan['cohort_sha256']
    prepared = run.validate(root)
    uuid = run.DEVICES[1]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
    assert not any(live(run.read(root / 'P64_HISTORICAL_REPAIR' / f'{arm}_START.json')['identity']) for arm in ('OFF',))
    output = root / 'P64_DEFAULT/BASE/readout'
    output.mkdir(parents=True, exist_ok=False)
    lifetime = run.read(root / 'LIFETIME.json')
    assert lifetime['hard_deadline_unix'] == plan['hard_deadline_unix']
    count = 0
    try:
        base_files = run.common.portable.verify_base_files(prepared['bundle'], prepared['model_dir'],
            expected_manifest_sha256=run.BUNDLE_SHA)
        assert base_files['expected_base_sha256'] == policy.BASE_SHA
        tokenizer = run.native.source.native.load_local_tokenizer(prepared['model_dir'])
        engine = run.common.ReadoutEngine(policy.options(prepared['model_dir'], uuid), tokenizer,
            check=lambda label: run.common.check_deadline(lifetime, label))
        parameters = policy.verify_no_adapter(engine.model.named_parameters(), getattr(engine.model, 'peft_config', None))
        run.write(output / 'LOADED.json', dict(parent_present=False, adapter=None, active_lora=False,
            base_sha256=policy.BASE_SHA, training_updates=0, process=run.common.process_identity(os.getpid()),
            loaded_unix=time.time(), parameters=parameters, prompt_condition='MINIMAL_DEFAULT_ADDON_BASE',
            not_initial37ec=True, exact_engine_source=run.sha(run.common.portable.source.__file__)))
        outcomes = []
        for task in run.read(root / 'COHORT.json')['tasks']:
            assert count < 64
            run.common.check_deadline(lifetime, 'base_default_reserve')
            path = output / f'CALL_{count:03d}.json'
            record = dict(position=count, messages=dev.default_math_messages(task), max_new_tokens=1536,
                metadata=dict(purpose='math_held', task_id=task['id']), status='RESERVED',
                prompt_condition='MINIMAL_DEFAULT_ADDON_BASE', parent_present=False, started_unix=time.time())
            assert not path.exists()
            run.write(path, record)
            count += 1
            try:
                response = engine.generate(record['messages'], max_new_tokens=1536)
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
                    run.write(output / 'FIRST_CALL.json', dict(status=record['status'], sha256=run.sha(path), finished_unix=record['finished_unix']))
        engine.verify_base()
        policy.verify_no_adapter(engine.model.named_parameters(), getattr(engine.model, 'peft_config', None))
        run.write(output / 'COMPLETE.json', dict(status='COMPLETE', calls=count, base_sha256=policy.BASE_SHA,
            unchanged=True, adapter=None, training_updates=0, parent_calls=0, no_promotion_claim=True))
    except BaseException as error:
        run.write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error), calls=count))
        raise


def watch(root):
    policy.validate(run.read(root / 'BASE_PLAN.json'))
    ready = run.read(root / 'BASE_READY.json')
    assert ready['status'] == 'PASS' and ready['plan_sha256'] == run.sha(root / 'BASE_PLAN.json')
    assert ready['source_sha256'] == run.sha(root / 'source_base_aux.tar')
    assert ready['source_files'] == run.verify_archive(root / 'source_base_aux.tar', root / 'source_base_aux')
    assert run.read(root / 'BASE_PUBLICATION.json')['ready_sha256'] == run.sha(root / 'BASE_READY.json')
    assert not (root / 'P64_DEFAULT/FULL_START.json').exists() and not (root / 'P64_DEFAULT/OFF_START.json').exists()
    output = root / 'P64_DEFAULT'
    pending = {'OFF': 1, 'FULL': 0}
    running, completed = {}, {}
    base_started = False
    try:
        while pending or running or not base_started:
            assert time.time() < run.read(root / 'LIFETIME.json')['native_deadline_unix']
            for arm in list(running):
                child, identity, stream = running[arm]
                if child.poll() is None:
                    continue
                stream.close()
                completed[arm] = child.returncode
                del running[arm]
            candidates = []
            for arm, index in pending.items():
                historical = run.read(root / 'P64_HISTORICAL_REPAIR' / f'{arm}_START.json')
                if not live(historical['identity']):
                    calls = run.MATH_ROOT / ('SCALE764_' + arm) / 'readout'
                    assert (calls / 'AFTER.json').exists() or (calls / 'FAILED.json').exists()
                    candidates.append((arm, index))
            if 'OFF' in completed and not base_started:
                candidates.append(('BASE', 1))
            for arm, index in candidates:
                admit_devices(root, (index,), f'P64_DEFAULT_WITH_BASE_{arm}')
                stream = (output / f'{arm}.log').open('x')
                if arm == 'BASE':
                    command = [run.PYTHON, '-B', '-m', 'gpu.orch_combined_l1_base', '--root', str(root), '--readout']
                    source = root / 'source_base_aux'
                    base_started = True
                else:
                    command = [run.PYTHON, '-B', '-m', 'gpu.orch_combined_l1_p64_default', '--root', str(root), '--arm', arm, '--index', str(index)]
                    source = root / 'source'
                    del pending[arm]
                child = subprocess.Popen(command, cwd=source, env=dict(os.environ,
                    PYTHONPATH=str(source), CUDA_VISIBLE_DEVICES=run.DEVICES[index], PYTHONDONTWRITEBYTECODE='1'),
                    stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
                identity = run.common.process_identity(child.pid)
                running[arm] = (child, identity, stream)
                run.write(output / f'{arm}_START.json', dict(pid=child.pid, identity=identity, index=index,
                    command=command, source_sha256=run.sha(root / ('source_base_aux.tar' if arm == 'BASE' else 'source.tar')),
                    started_unix=time.time()))
            time.sleep(1)
    except BaseException as error:
        run.write(output / 'BASE_WATCH_FAILED.json', dict(type=type(error).__name__, message=str(error)))
    finally:
        for arm, (child, identity, stream) in running.items():
            run.common.stop_owned(child, identity)
            stream.close()
            completed[arm] = child.returncode
        if not pending:
            admit_devices(root, (0, 1), 'P64_DEFAULT_BASE_RELEASE')
            calls = {arm: len(list((output / arm / 'readout').glob('CALL_*.json'))) for arm in ('FULL', 'OFF', 'BASE')}
            assert calls['FULL'] <= 64 and calls['OFF'] <= 64 and calls['BASE'] <= 64
            run.write(output / 'RELEASED.json', dict(returncodes=[completed.get(arm) for arm in ('FULL', 'OFF')],
                base_returncode=completed.get('BASE'), actual_reserved_calls=calls['FULL'] + calls['OFF'],
                additional_base_calls=calls['BASE'], new_total_ceiling=1824, released_unix=time.time(), failures_preserved=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--readout', action='store_true')
    arguments = parser.parse_args()
    if arguments.readout:
        readout(arguments.root)
    else:
        watch(arguments.root)
