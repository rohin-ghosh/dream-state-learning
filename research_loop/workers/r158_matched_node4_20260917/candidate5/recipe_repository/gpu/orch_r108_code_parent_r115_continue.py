"""No-replay continuation after the captured pre-forward guard return failure."""

import argparse
from pathlib import Path
import subprocess
import time

from gpu import orch_r108_code_parent_r115_run as run


def resume_cycle(root):
    rows = [run.read(path) for path in (root / 'reservations').glob('*.json')]
    return max([row['cycle'] for row in rows] + [0]) + 1


def native(root):
    plan = run.check(root, 'operational_continuation')
    receipt = run.read(root / 'CONTINUATION_BINDING.json')
    run.policy.require(run.sha(root / 'PLAN.json') == receipt['plan_sha256'], 'original_lifetime_unchanged')
    for name, expected in receipt['previous_reservations'].items():
        run.policy.require(run.sha(root / 'reservations' / name) == expected, 'preserved_failed_reservations')
    start = resume_cycle(root)
    run.policy.require(start == receipt['next_cycle'], 'no_replayed_stage')
    engine = run.load_engine(root)
    driver = run.Driver(root, engine)
    run.write_new(root / 'CONTINUATION_ACTOR_READY.json', dict(base_sha256=engine.loaded_base_sha256,
        no_adapter=engine.no_adapter, started_unix=time.time(), next_cycle=start,
        initial_readout_repeated=False, previous_cells=len(receipt['previous_reservations'])))
    pending = []
    final_started = False
    try:
        for cycle in range(start, plan['cycles'] + 1):
            if time.time() >= plan['hard_deadline_unix'] - 120:
                break
            if time.time() >= run.FINAL_CUT and not final_started:
                for child in pending:
                    child.wait()
                pending = [run.readout_process(root, cycle, 'FINAL')]
                final_started = True
            tasks = run.policy.tasks('TRAIN')[(cycle - 1) * 2:cycle * 2]
            combined = []
            for index, task in enumerate(tasks):
                combined.extend(run.episode(driver, task, cycle, index))
            task = tasks[-1]
            messages = [dict(role='assistant' if event['actor'] == 'child' else 'user',
                content=event['text']) for event in combined]
            messages.append(dict(role='user', content=run.policy.previous.PROMPTS['presleep']))
            before = driver.capture(f'C{cycle:03d}_PRESLEEP', task, 'presleep', cycle,
                messages, driver.settings['effective_max_new_tokens'])
            if before['status'] == 'COMPLETE':
                combined.append(run.environment.event(task, 'child', before['response']['raw'], completed=True))
                guidance = driver.parent(f'C{cycle:03d}_META_PARENT', task, combined, cycle, 1,
                    'presleep_metacognition')
                if guidance:
                    messages += [dict(role='assistant', content=before['response']['raw']),
                        dict(role='user', content=guidance)]
                    driver.reflection(f'C{cycle:03d}_META_REFLECTION', task, cycle, messages)
            run.write_new(root / 'cycles' / f'C{cycle:03d}_COMPLETE.json', dict(cycle=cycle,
                completed_unix=time.time(), optimizer_steps=0, sleep_buffer_rows=0,
                lambda_actual='NOT_APPLIED', continuation=True))
            driver.status()
            if (root / 'RELEASE_AFTER_CYCLE.json').exists():
                request = run.read(root / 'RELEASE_AFTER_CYCLE.json')
                if request.get('receiver_ready') is True:
                    run.write_new(root / 'CYCLE_RELEASE_READY.json', dict(cycle=cycle,
                        request_sha256=run.sha(root / 'RELEASE_AFTER_CYCLE.json')))
                    break
            for child in pending:
                child.wait()
            pending = [run.readout_process(root, cycle, 'DEV')]
        for child in pending:
            child.wait()
        engine.verify_base()
        run.write_new(root / 'CONTINUATION_COMPLETE.json', dict(finished_unix=time.time(),
            optimizer_steps=0, unchanged_base=True))
    finally:
        for child in pending:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
        run.write_new(root / 'CONTINUATION_TERMINAL.json', dict(finished_unix=time.time(), optimizer_steps=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    native(parser.parse_args().root)
