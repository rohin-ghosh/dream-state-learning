"""Successor CODE lifecycle using the existing life ledger and shared F1 barrier."""

import argparse
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys
import time

from gpu import orch_r108_code_parent_r116_shared as client
from gpu import orch_r108_code_parent_r115_continue as continuation


run = client.run
require = client.require
MODULE = 'gpu.orch_r108_code_parent_r116_shared_run'


def activation_plan(root):
    plan = run.check(root, 'shared_activation')
    activation = run.read(root/'SHARED_ACTIVATION.json')
    require(activation['predecessor_plan_sha256'] == run.sha(root/'PLAN.json'), 'original_PLAN_unchanged')
    require(activation['inherited_bounds'] == {key:plan[key] for key in client.BOUND_FIELDS},
        'original_lifetime_and_caps')
    require(run.policy.digest(run.read(root/'COHORT.json')) == plan['cohort_sha256'], 'original_cohort')
    return dict(plan, shared_learner=activation['shared_learner'])


def verify_boundary(root):
    activation = run.read(root/'SHARED_ACTIVATION.json')
    release = run.read(root/'CYCLE_RELEASE_READY.json')
    require(not (Path('/proc')/str(activation['predecessor_identity']['pid'])).exists(),
        'predecessor_must_naturally_exit')
    for name, expected in activation['previous_reservations'].items():
        require(run.sha(root/'reservations'/name) == expected, 'historical_capture_unchanged')
    rows = [run.read(path) for path in (root/'reservations').glob('*.json')]
    require(set(activation['previous_reservations']) == {path.name for path in (root/'reservations').glob('*.json')},
        'all_original_reservations_preserved')
    require(all(row['status'] != 'STARTED' for row in rows), 'no_unresolved_previous_calls')
    next_cycle = continuation.resume_cycle(root)
    require(next_cycle == release['cycle']+1, 'exact_completed_cycle_successor')
    return next_cycle


def cycle(driver, tasks, ordinal):
    require(len(tasks) == 2 and len({task['task_id'] for task in tasks}) == 2,
        'two_original_scheduled_episodes')
    combined = []
    for index, task in enumerate(tasks):
        combined.extend(run.episode(driver, task, ordinal, index))
    task = tasks[-1]
    messages = [dict(role='assistant' if event['actor']=='child' else 'user',content=event['text'])
        for event in combined]
    messages.append(dict(role='user',content=run.policy.previous.PROMPTS['presleep']))
    before = driver.capture(f'C{ordinal:03d}_META', task, 'presleep', ordinal, messages,
        driver.settings['effective_max_new_tokens'])
    if before['status'] == 'COMPLETE':
        combined.append(run.environment.event(task,'child',before['response']['raw'],completed=True))
        guidance = driver.parent(f'C{ordinal:03d}_META_PARENT',task,combined,ordinal,1,'presleep_metacognition')
        if guidance:
            messages += [dict(role='assistant',content=before['response']['raw']),dict(role='user',content=guidance)]
            driver.reflection(f'C{ordinal:03d}_META_REFLECTION',task,ordinal,messages)
    return driver.finish_cycle(ordinal,[task['task_id'] for task in tasks],
        lambda phase:run.forward_check(driver.root,phase))


class ReadoutDriver(run.Driver):
    def __init__(self, root, engine, session):
        super().__init__(root,engine,evaluation=True)
        self.session = session

    def status(self):
        pass

    def reserve(self, identifier, kind, **kwargs):
        require(kind == 'NATIVE' and kwargs.get('split') != 'TRAIN', 'parent_free_evaluation_only')
        path, row = super().reserve(identifier,kind,**kwargs)
        row.update(self.session.capture_metadata())
        require(not row['routes']['sleep'] and not row['routes']['parent'], 'evaluation_never_experience')
        run.write(path,row)
        return path,row


def schedule_readout(root, session, ordinal, scope):
    require(scope in ('DEV','FINAL'), 'no_initial_readout_repetition')
    reference = root/'shared_readout_bindings'/f'C{ordinal:03d}_{scope}.json'
    run.write_new(reference,dict(state=deepcopy(session.state),checkpoint=deepcopy(session.loaded_reference),
        scope=scope,cycle=ordinal,config_sha256=client.coordinator.sha(session.shared_root/'CONFIG.json')))
    log = root/'shared_readout_bindings'/f'C{ordinal:03d}_{scope}.log'
    with log.open('x') as stream:
        child = subprocess.Popen([sys.executable,'-B','-m',MODULE,'readout','--root',str(root),
            '--binding',str(reference)],stdout=stream,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
    return child


def readout(root, binding_path):
    plan = activation_plan(root)
    binding = run.read(binding_path)
    require(Path(binding_path).resolve().is_relative_to((root/'shared_readout_bindings').resolve()),
        'own_pinned_readout_binding')
    session = client.Session(root,plan,readout=True)
    require(binding['config_sha256'] == client.coordinator.sha(session.shared_root/'CONFIG.json')
        and binding['state']['config_sha256'] == binding['config_sha256']
        and binding['state']['checkpoint'] == binding['checkpoint'], 'pinned_common_readout_state')
    require(type(binding['state']['generation']) is int
        and binding['state']['generation'] <= session.state['generation'], 'real_readout_generation')
    session.state = binding['state']
    session.loaded_reference = client.coordinator.checked_checkpoint(binding['checkpoint'])
    engine = session.load_engine(plan,lambda phase:run.forward_check(root,phase),readout=True)
    run.readouts(ReadoutDriver(root,engine,session),binding['cycle'],binding['scope'])
    engine.verify_base()


def native(root):
    plan = activation_plan(root)
    start = verify_boundary(root)
    session = client.Session(root,plan)
    engine = session.load_engine(plan,lambda phase:run.forward_check(root,phase))
    driver = client.Driver(root,engine,session)
    run.write_new(root/'SHARED_ACTOR_READY.json',dict(pid=os.getpid(),next_cycle=start,
        capture_binding=session.capture_metadata(),original_plan_sha256=run.sha(root/'PLAN.json'),
        local_optimizer_steps=0,optimizer_owner='F1',initial_readout_repeated=False,started_unix=time.time()))
    pending=[]
    final_started=any((root/'readouts').glob('*_FINAL/COMPLETE.json'))
    try:
        cohort = run.read(root/'COHORT.json')['TRAIN']
        for ordinal in range(start,plan['cycles']+1):
            if time.time() >= plan['hard_deadline_unix']-120:
                break
            if time.time() >= run.FINAL_CUT and not final_started:
                for child in pending:
                    child.wait()
                pending=[schedule_readout(root,session,ordinal,'FINAL')]
                final_started=True
            result = cycle(driver,cohort[(ordinal-1)*2:ordinal*2],ordinal)
            run.write_new(root/'cycles'/f'C{ordinal:03d}_COMPLETE.json',dict(cycle=ordinal,
                completed_unix=time.time(),optimizer_owner='F1',local_optimizer_steps=0,
                shared_generation=session.state['generation'],shared_sleep=result,
                sleep_buffer_rows=len(driver.cycle_sources.get(ordinal,[]))))
            for child in pending:
                child.wait()
            pending=[schedule_readout(root,session,ordinal,'DEV')]
        for child in pending:
            child.wait()
        engine.verify_base()
        run.write_new(root/'SHARED_COMPLETE.json',dict(completed_unix=time.time(),local_optimizer_steps=0,
            generation=session.state['generation'],no_lifetime_reset=True))
    finally:
        run.write_new(root/'SHARED_TERMINAL.json',dict(finished_unix=time.time(),local_optimizer_steps=0))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entry',choices=('native','readout'))
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--binding',type=Path)
    args=parser.parse_args()
    if args.entry == 'native':
        native(args.root)
    else:
        require(args.binding is not None,'readout_binding_required')
        readout(args.root,args.binding)
