"""Read-only gen1 CODE forks with asynchronous parent delivery and no shared sleep."""

import argparse
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

from gpu import orch_r119_code_continuation as custody
from gpu import orch_r108_code_parent_r115_run as run
from gpu import orch_r108_code_parent_r116_shared as loader


MODULE = 'gpu.orch_r119_code_independent'
FINAL_TIME = 1789538400
require = custody.require


def command(service, phase, document):
    arguments = [MODULE, phase, '--service', str(service)]
    script = ('import sys,runpy;sys.path.insert(0,' + repr(document['source_root']) +
        ');import gpu;gpu.__path__.insert(0,' + repr(document['wrapper_directory']) +
        ');sys.argv=' + repr(arguments) + ';runpy.run_module(' + repr(MODULE) + ',run_name="__main__")')
    return [document['interpreter'], '-B', '-c', script]


def configure(service, *, initial=False):
    service = Path(service).resolve(strict=True)
    document = custody.read(service / 'INDEPENDENT.json')
    require(document['schema'] == 'R119_CODE_INDEPENDENT_ELICITATION_V1'
        and document['service'] == str(service) and document['optimizer_updates'] == 0
        and document['shared_barrier'] is False, 'explicit_no_shared_restart')
    for path, pin in document['source_files'].items():
        require(custody.ref(path)['sha256'] == pin, 'frozen_independent_source')
    pointers = custody.checked(document['pointers'])
    root = Path(pointers['root'])
    require(service.parents[1] == root and pointers['branch'] in ('F3', 'A3'), 'own_F3_A3_only')
    plan = custody.checked(pointers['original_plan'])
    require(document['hard_end_unix'] <= plan['lease_end_unix'] - 21600
        and document['train_end_unix'] == document['hard_end_unix'] - 120
        and document['final_unix'] == FINAL_TIME, 'actual_lease_and_new_morning_readout')
    for key in ('native_cap', 'parent_cap', 'cycles'):
        require(document[key] == plan[key], 'no_counter_or_quota_reset')
    if initial:
        require(not (root / 'r119_continuation/service_2/GUARD_ONCE').exists(),
            'shared_campaign_staged_only_never_dispatched')
        fresh = custody.branch_snapshot(root)
        require(fresh['preserved_files'] == pointers['preserved_files']
            and fresh['existing_submission'] == pointers['existing_submission'], 'pending_and_charges_preserved')
        from gpu import orch_r118_code_parallel_handoff as handoff
        proof = custody.checked(custody.checked(pointers['prepared'])['proof'])
        require(all(not handoff.alive(identity) for identity in proof['predecessors']), 'old_actors_exited')
    effective = dict(plan, hard_deadline_unix=document['hard_end_unix'])
    def check(checked_root, phase):
        require(Path(checked_root) == root and custody.ref(root / 'PLAN.json') == pointers['original_plan'],
            'historical_PLAN_unchanged')
        require(time.time() < document['hard_end_unix'] - 10, 'actual_lease_wall:' + phase)
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'exact_CODE_CVD')
        return effective
    run.check = check
    return document, pointers, effective


class Driver(run.Driver):
    def __init__(self, root, engine, document, pointers):
        super().__init__(root, engine)
        self.plan = dict(self.plan, hard_deadline_unix=document['hard_end_unix'])
        self.document = document
        self.service = Path(document['service'])
        self.settings = deepcopy(pointers['carry']['reflection_settings'])
        self.pending = {}
        self.guidance = []
        self.injected = []
        self.model_binding = dict(source_condition='FORK_OF_COMMITTED_SHARED_GEN1_READONLY',
            checkpoint=pointers['checkpoint'], generation=pointers['generation'], optimizer_updates=0,
            shared_sleep=False, parented_derived=True)

    def poll_parent(self, now=None):
        now = time.time() if now is None else now
        for identifier, entry in list(self.pending.items()):
            response_path = self.root / 'parent_queue' / (identifier + '.response.json')
            if not response_path.exists() and now < entry['deadline']:
                continue
            record = entry['record']
            record.update(status='MISSING', late=now >= entry['deadline'], no_retry=True)
            if response_path.exists():
                response = run.read(response_path)
                request = entry['request']
                archive = response.get('transcript_receipt', {})
                archive_root = Path(archive.get('remote_root', '/nonexistent'))
                files = archive.get('files', {})
                valid = response.get('id') == identifier and response.get('request_sha256') == run.broker.digest(request)
                valid = valid and response.get('payload_sha256') == request['payload_sha256']
                valid = valid and archive_root.is_absolute() and archive_root.is_relative_to(self.root)
                valid = valid and bool(files) and all(Path(name).name == name and (archive_root / name).is_file()
                    and run.sha(archive_root / name) == pin for name, pin in files.items())
                valid = valid and response.get('actual_model') in self.document['allowed_parent_models']
                record.update(response_sha256=run.sha(response_path), provider_dispatched=response.get('provider_dispatched'),
                    provider_actual_model=response.get('actual_model'), delivered_unix=now,
                    delivery_latency_seconds=now - record['started_unix'])
                if valid and now < entry['deadline'] and response.get('status') in ('COMPLETE', 'SILENT'):
                    record.update(status=response['status'], late=False)
                    plan = response.get('plan') or {}
                    guidance = plan.get('guidance', plan.get('message', ''))
                    record['guidance'] = guidance if response['status'] == 'COMPLETE' else ''
                    record['parent_metadata'] = response.get('parent_metadata')
                    if record['guidance']:
                        self.guidance.append((identifier, record['guidance']))
                    try:
                        self.settings = run.broker.reflection_call_settings(response, request, 4096,
                            config=run.read(self.root / 'BROKER_CONFIG.json'))
                        record['reflection_settings'] = self.settings
                    except (ValueError, KeyError, TypeError):
                        record['reflection_setting_status'] = 'UNCHANGED_UNUSABLE_ASYNC_SETTINGS'
            record['finished_unix'] = now
            run.write(entry['path'], record)
            del self.pending[identifier]

    def parent(self, identifier, task, events, cycle, episode, phase):
        require(task['split'] == 'TRAIN' and not self.evaluation, 'TRAIN_only_async_parent')
        self.poll_parent()
        path, record = self.reserve(identifier, 'PARENT', split='TRAIN', phase=phase, cycle=cycle)
        deadline = min(time.time() + 600, self.document['train_end_unix'])
        request = run.adapter.request(task, events, phase=phase, identifier=identifier,
            life_id=self.plan['life_id'], cycle=cycle, episode=episode, lane_deadline_unix=deadline)
        request['payload_sha256'] = run.broker.digest(request['payload'])
        run.write_new(self.root / 'parent_queue' / (identifier + '.request.json'), request)
        record.update(status='PENDING', asynchronous=True, wait_seconds=0, deadline_unix=deadline)
        run.write(path, record)
        self.pending[identifier] = dict(path=path, record=record, request=request, deadline=deadline)
        self.status()
        return ''

    def capture(self, identifier, task, phase, cycle, messages, cap, *, evaluation_origin=None):
        self.poll_parent()
        applied = []
        if task['split'] == 'TRAIN' and evaluation_origin is None and self.guidance:
            applied, self.guidance = self.guidance, []
            messages = deepcopy(messages) + [dict(role='user', content='Parent guidance received since your previous turn:\n'
                + '\n\n'.join(text for unused, text in applied))]
        row = super().capture(identifier, task, phase, cycle, messages, cap, evaluation_origin=evaluation_origin)
        row.update(model_binding=self.model_binding, injected_parent_ids=[key for key, unused in applied],
            parent_wait_seconds=0)
        run.write(self.root / 'reservations' / (identifier + '.json'), row)
        return row

    def batch(self, identifiers, tasks, phase, cycle, messages, cap):
        require(all(task['split'] != 'TRAIN' for task in tasks), 'parent_free_diagnostic_batch')
        rows = super().batch(identifiers, tasks, phase, cycle, messages, cap)
        for identifier, row in zip(identifiers, rows):
            row.update(model_binding=self.model_binding, injected_parent_ids=[])
            run.write(self.root / 'reservations' / (identifier + '.json'), row)
        return rows


def load_engine(root, pointers, plan):
    session = SimpleNamespace(root=Path(root), state=dict(generation=pointers['generation']),
        loaded_reference=pointers['checkpoint'], loaded=False)
    return loader.Session.load_engine(session, plan, lambda phase:run.check(root, phase))


def diagnostic(driver, ordinal, split, namespace):
    require(split in ('DEV', 'FINAL'), 'fixed_diagnostic_scope')
    if split == 'FINAL':
        require(time.time() >= FINAL_TIME and namespace == 'R119_FINAL_20260916_0600', 'no_early_or_old_FINAL_replay')
    output = driver.service / namespace / f'C{ordinal:03d}'
    output.mkdir(parents=True, exist_ok=False)
    tasks = run.policy.tasks(split)
    rows = driver.batch([f'{namespace}_C{ordinal:03d}_{index}' for index in range(8)], tasks,
        'readout', ordinal, [run.policy.previous.messages(task, 'readout') for task in tasks], 2048)
    run.write_new(output / 'COMPLETE.json', dict(split=split, calls=len(rows), cycle=ordinal,
        full_continuation_saved_in_reservations=True, parent_visible=False, head_visible=split == 'DEV',
        sleep_eligible=False, optimizer_steps=0, fresh_process=False, evaluation_only_model_calls=True))


def native(service):
    service = Path(service)
    document, pointers, plan = configure(service, initial=True)
    root = Path(pointers['root'])
    (service / 'NATIVE_ONCE').mkdir()
    from gpu import orch_r118_code_parallel_handoff as handoff
    identity = handoff.identities.identity(os.getpid())
    custody.write(service / 'NATIVE_REQUEST.json', dict(identity=identity, definition=custody.ref(service / 'INDEPENDENT.json')))
    engine, driver, error = None, None, None
    try:
        engine = load_engine(root, pointers, plan)
        driver = Driver(root, engine, document, pointers)
        custody.write(service / 'ACTOR_READY.json', dict(identity=identity, loaded_unix=time.time(),
            model_binding=driver.model_binding, pending_submission_preserved=pointers['existing_submission'],
            pending_experience_not_fitted=True, prior_counters=pointers['cumulative_counts'],
            reflection_carry=driver.settings, shared_barrier=False, optimizer=None))
        tasks = run.policy.tasks('TRAIN')
        for ordinal in range(pointers['next_cycle'], document['cycles'] + 1):
            if time.time() >= document['train_end_unix'] - 120:
                break
            require(not any((root / 'reservations').glob(f'C{ordinal:03d}_*.json')), 'no_charged_cycle_replay')
            events = []
            selected = tasks[(ordinal - 1) * 2:ordinal * 2]
            require(len(selected) == 2, 'fixed_two_episode_schedule')
            for index, task in enumerate(selected):
                events.extend(run.episode(driver, task, ordinal, index))
            messages = [dict(role='assistant' if event['actor'] == 'child' else 'user',content=event['text']) for event in events]
            messages.append(dict(role='user',content=run.policy.previous.PROMPTS['presleep']))
            reflected = driver.capture(f'C{ordinal:03d}_META', selected[-1], 'presleep', ordinal,
                messages, driver.settings['effective_max_new_tokens'])
            if reflected['status'] == 'COMPLETE':
                events.append(run.environment.event(selected[-1], 'child', reflected['response']['raw'], completed=True))
                driver.parent(f'C{ordinal:03d}_META_PARENT', selected[-1], events, ordinal, 1, 'presleep_metacognition')
            driver.poll_parent()
            custody.write(service / f'C{ordinal:03d}_COMPLETE.json', dict(cycle=ordinal, train_episodes=2,
                optimizer_updates=0, shared_barrier=False, pending_parents=len(driver.pending), finished_unix=time.time()))
            if time.time() >= FINAL_TIME and not (service / 'FINAL_ONCE').exists():
                (service / 'FINAL_ONCE').mkdir()
                diagnostic(driver, ordinal, 'FINAL', 'R119_FINAL_20260916_0600')
            diagnostic(driver, ordinal, 'DEV', 'R119_DEV')
            engine.verify_base()
    except BaseException as failure:
        error = failure
    finally:
        if driver is not None:
            driver.poll_parent()
            custody.write(service / 'PENDING_PARENT_CUSTODY.json', dict(ids=list(driver.pending),
                no_retry=True, stop_reason=type(error).__name__ if error else 'SCHEDULE_OR_LEASE_END'))
        custody.write(service / 'TERMINAL.json', dict(status='FAILED' if error else 'COMPLETE',
            error_type=type(error).__name__ if error else None, observed_unix=time.time(), optimizer_updates=0))
    if error:
        raise error


def guard(service):
    service = Path(service)
    document, pointers, plan = configure(service, initial=True)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_guard')
    from gpu import orch_r118_code_parallel_handoff as handoff
    (service / 'GUARD_ONCE').mkdir()
    identity = handoff.identities.identity(os.getpid())
    custody.write(service / 'GUARD_IDENTITY.json', dict(identity=identity))
    result = subprocess.run(document['admission_command'], capture_output=True, text=True, timeout=120, check=True)
    report = __import__('json').loads(result.stdout)
    custody.write(service / 'ADMISSION.json', report)
    require(handoff.previous.admitted(report, plan), 'fresh_privileged_original_full_admission')
    with (service / 'NATIVE.log').open('x') as log:
        child = subprocess.Popen(command(service, 'native', document), env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid']),
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    native_identity = handoff.identities.identity(child.pid)
    custody.write(service / 'LAUNCH.json', dict(identity=native_identity, guardian=identity,
        admission=custody.ref(service / 'ADMISSION.json'), launched_unix=time.time(), independent=True))
    try:
        child.wait(timeout=max(1, document['hard_end_unix'] - time.time() - 5))
    finally:
        if child.poll() is None:
            from gpu import orch_r118_code_parallel_loop as old
            old.cleanup_native(native_identity, Path(pointers['root']))
        custody.write(service / 'GUARD_TERMINAL.json', dict(identity=native_identity,
            returncode=child.poll(), observed_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('guard', 'native'))
    parser.add_argument('--service', type=Path, required=True)
    arguments = parser.parse_args()
    globals()[arguments.phase](arguments.service)
