"""Fresh-process, parent-blind intermediate and terminal checkpoint readouts."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace

from gpu import orch_combined_l1_continual_run as run
from gpu import orch_combined_l1_run as combined
from organism_v6 import orch_combined_l1_continual as state
from organism_v6 import orch_combined_l1_dev as policy


def evaluation_root(root, phase, update):
    return root / 'ADAPTIVE_DEV' / f'{phase}_{update:09d}'


def readout(root, phase, update, arm, family, index):
    plan = policy.validate_plan(run.read(root / 'DEV_PLAN.json'))
    assert all(run.sha(root / name) == expected for name, expected in plan['cohort_sha256'].items())
    prepared = run.validate(root)
    checkpoint = root / arm / 'checkpoints' / f'{update:09d}'
    metadata = state.verify_checkpoint(checkpoint)['metadata']
    evaluation = evaluation_root(root, phase, update)
    allocation = run.read(evaluation / 'ALLOCATION.json')
    output = evaluation / arm / family / 'readout'
    output.mkdir(parents=True, exist_ok=False)
    uuid = run.DEVICES[index]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
    cap, count = policy.call_cap(phase, family), 0
    lifetime = dict(run.read(root / 'LIFETIME.json'), native_deadline_unix=allocation['deadline_unix'])
    try:
        identity = run.common.bridge.AdapterIdentity.from_document(metadata['adapter'])
        binding = run.common.bridge.StageBinding(root.name, run.common.bridge.ARMS[1], 0,
            'sealed_readout', identity, False, True, run.sha(root / 'DEV_PLAN.json'))
        loaded = run.native.load_stage(binding, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
            context=run.native.StageContext(), check=lambda label: run.common.check_deadline(lifetime, label),
            predecessor_processes=(tuple(metadata['process']),), engine_factory=run.common.ReadoutEngine)
        run.write(output / 'LOADED.json', dict(process=loaded.process, observed=loaded.observed.document(),
            parent_present=False, checkpoint_sha256=run.sha(checkpoint / 'COMMIT.json'),
            phase=phase, family=family, claim=plan['claim'], loaded_unix=time.time()))

        def generate(messages, **details):
            nonlocal count
            run.common.check_deadline(lifetime, 'adaptive_dev_reserve')
            assert count < cap, 'prospective_dev_family_call_cap'
            tokens = plan['math_tokens'] if family == 'math' else plan['route_tokens'] if family == 'route' else plan['other_tokens']
            path = output / f'CALL_{count:03d}.json'
            record = dict(position=count, messages=messages, metadata=details, max_new_tokens=tokens,
                started_unix=time.time(), status='RESERVED', parent_present=False,
                prompt_condition='MINIMAL_DEFAULT' if family == 'math' else 'EXISTING_ACTION_PROTOCOL_NO_RICHNESS_HINTS' if family == 'route' else 'ORIGINAL_LEGACY',
                claim=plan['claim'], checkpoint_sha256=run.sha(checkpoint / 'COMMIT.json'))
            assert not path.exists()
            run.write(path, record)
            count += 1
            try:
                response = loaded.engine.generate(messages, max_new_tokens=tokens)
                from organism_v6 import orch_combined_l1_behavior as behavior
                text = response['raw'] if isinstance(response, dict) else response
                record.update(status='COMPLETE', response=response,
                    richness=dict(behavior.describe(text), tokens=behavior.token_metrics(response, tokens)))
                return response
            except BaseException as error:
                record.update(status='FAILED', error=dict(type=type(error).__name__, message=str(error)))
                raise
            finally:
                record['finished_unix'] = time.time()
                run.write(path, record)
                if count == 1:
                    run.write(output / 'FIRST_CALL.json', dict(path=path.name, sha256=run.sha(path),
                        status=record['status'], finished_unix=record['finished_unix']))

        result = {}
        if family == 'math':
            cohort = run.read(root / 'COHORT.json')
            rows = []
            for task in cohort['tasks']:
                messages = policy.default_math_messages(task)
                response = generate(messages, purpose='math_held', task_id=task['id'])
                rows.append(dict(task_id=task['id'], family=task['family'], **run.common.transfer.score(task, response)))
                run.write(output / 'MATH_ROWS.json', rows)
            assert count == len(rows) == 64
            result = dict(correct=sum(row['outcome_pass'] for row in rows), denominator=64)
            from gpu.orch_combined_l1_behavior import analyze
            analyze(output, evaluation / 'SEALED_DESCRIPTIVES' / arm)
        elif family == 'route':
            probes = run.read(root / 'ROUTE_COHORT.json')['probes'][:policy.ROUTE_WORLDS[phase]]
            panels = []
            for position, probe in enumerate(probes):
                runtime = SimpleNamespace(**combined.route.goal.runtime(probe['shard']))
                panel = combined.route.evaluate_goal_world(probe['collection'], plan['route_condition'],
                    generate, output, 'ADAPTIVE_DEV', position, runtime)
                panels.append(panel)
                run.write(output / 'ROUTE_PANELS.json', panels)
            result = dict(correct=sum(panel['summary']['individual']['correct'] for panel in panels),
                denominator=4 * len(panels), paired_correct=sum(panel['summary']['paired']['correct'] for panel in panels),
                paired_denominator=2 * len(panels), condition=plan['route_condition'])
        else:
            legacy = run.read(root / 'LEGACY_READOUT.json')
            events = [dict(event=fact['event'], raw=episode['event']['raw'])
                for fact, episode in zip(legacy['old_bank'], legacy['old_episodes'])]
            retention = combined.route.memory.recall(events, generate, output, 'OLD')
            audit = combined.route.memory.audit.collect_cases(legacy['held'],
                lambda messages: generate(messages, purpose='legacy_audit'), coached=False)
            run.write(output / 'AUDIT.json', audit)
            assert count == 48
            result = dict(retention=retention, audit=audit['summary'])
        observed = loaded.verify_unchanged()
        run.write(output / 'COMPLETE.json', dict(status='COMPLETE', result=result, calls=count,
            observed=observed.document(), process=loaded.process, updates=0, fits=0, parent_calls=0,
            claim=plan['claim'], finished_unix=time.time(), no_promotion_claim=True))
    except BaseException as error:
        run.write(output / 'FAILED.json', dict(status='FAILED', calls=count,
            type=type(error).__name__, message=str(error), finished_unix=time.time(), no_retry=True))
        raise


def launch(root, phase, update, lifetime):
    from gpu.orch_combined_l1_continual_guard import admit_devices
    plan = policy.validate_plan(run.read(root / 'DEV_PLAN.json'))
    evaluation = evaluation_root(root, phase, update)
    evaluation.mkdir(parents=True, exist_ok=False)
    checkpoint_hashes = {arm: run.sha(root / arm / 'checkpoints' / f'{update:09d}/COMMIT.json') for arm in state.ARMS}
    deadline = min(lifetime['native_deadline_unix'], time.time() + plan['maximum_diagnostic_seconds'])
    if phase == 'INTERMEDIATE':
        deadline = min(deadline, plan['intermediate_finish_before_unix'])
    run.write(evaluation / 'ALLOCATION.json', dict(update=update, phase=phase, devices=plan['temporary_devices'],
        jobs=policy.jobs(phase), checkpoint_sha256=checkpoint_hashes, deadline_unix=deadline,
        allocated_unix=time.time(), maximum_calls=sum(2 * policy.call_cap(phase, family) for family in policy.FAMILIES),
        own_training_suspended_at_durable_checkpoint=True, math0_1_untouched=True,
        queue_policy='mathFULL,mathOFF,routeFULL,routeOFF,legacyFULL,legacyOFF; next free identical A100'))
    pending, running, results = list(policy.jobs(phase)), {}, []
    try:
        while pending or running:
            for index in plan['temporary_devices']:
                if index in running:
                    child, identity, arm, family, stream = running[index]
                    if child.poll() is None:
                        continue
                    stream.close()
                    results.append(dict(arm=arm, family=family, index=index, returncode=child.returncode))
                    del running[index]
                if pending and time.time() < deadline:
                    admit_devices(root, (index,), f'DEV_{phase}_{update}_{len(results)}_{index}')
                    arm, family = pending.pop(0)
                    log = (evaluation / f'{arm}_{family}.log').open('x')
                    command = [run.PYTHON, '-B', '-m', 'gpu.orch_combined_l1_dev', '--root', str(root),
                        '--phase', phase, '--update', str(update), '--arm', arm, '--family', family, '--index', str(index)]
                    child = subprocess.Popen(command, cwd=root / 'source', env=dict(os.environ,
                        CUDA_VISIBLE_DEVICES=run.DEVICES[index], PYTHONDONTWRITEBYTECODE='1'),
                        stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    identity = run.common.process_identity(child.pid)
                    running[index] = (child, identity, arm, family, log)
                    run.write(evaluation / f'{arm}_{family}_START.json', dict(pid=child.pid, identity=identity,
                        command=command, index=index, started_unix=time.time()))
            if time.time() >= deadline:
                break
            time.sleep(1)
    except BaseException as error:
        run.write(evaluation / 'DISPATCH_FAILED.json', dict(type=type(error).__name__, message=str(error)))
    finally:
        for index, (child, identity, arm, family, stream) in running.items():
            run.common.stop_owned(child, identity)
            stream.close()
            results.append(dict(arm=arm, family=family, index=index, returncode=child.poll(), stopped_at_deadline=True))
        calls = list(evaluation.glob('*/*/readout/CALL_*.json'))
        assert len(calls) <= sum(2 * policy.call_cap(phase, family) for family in policy.FAMILIES)
        assert checkpoint_hashes == {arm: run.sha(root / arm / 'checkpoints' / f'{update:09d}/COMMIT.json') for arm in state.ARMS}
        for index in plan['temporary_devices']:
            admit_devices(root, (index,), f'DEV_RELEASE_{phase}_{update}_{index}')
        run.write(evaluation / 'RESULT.json', dict(status='COMPLETE' if len(results) == 6 and
            all(result['returncode'] == 0 for result in results) else 'PARTIAL_OR_FAILED_PRESERVED',
            jobs=results, unstarted=pending, actual_reserved_calls=len(calls), checkpoint_sha256=checkpoint_hashes,
            checkpoint_unchanged=True, optimizer_rng_cursor_preserved=True, claim=plan['claim'],
            parent_access=False, no_promotion_claim=True, finished_unix=time.time()))
    return evaluation


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--phase', choices=policy.PHASES, required=True)
    parser.add_argument('--update', type=int, required=True)
    parser.add_argument('--arm', choices=state.ARMS, required=True)
    parser.add_argument('--family', choices=policy.FAMILIES, required=True)
    parser.add_argument('--index', type=int, choices=(2, 3, 6), required=True)
    options = parser.parse_args()
    readout(options.root, options.phase, options.update, options.arm, options.family, options.index)
