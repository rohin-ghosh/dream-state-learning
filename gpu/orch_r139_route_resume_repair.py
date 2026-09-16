"""F1 attempt3: preserve uncharged signal metadata and resume saved C55."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import time
from types import FunctionType


OLD = Path('/localhome/local-rohing/orch_r139_F1_astra_handoff_20260916_attempt2')
STAGE = Path('/localhome/local-rohing/orch_r139_F1_astra_handoff_20260916_attempt3')
ROOT = Path('/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1')
HANDOFF_SHA = '22b251d95498fa946d79aed690284c20fc5a2b9f70bb1f2597dde70944ab7fba'
BOUNDARY_SHA = '86faf1b2a4cde016ebf18b86f0441f3224c91169c4a9854cd3db83c625c6839b'
LEDGER_SHA = 'cc6e032e5b7ee569e6d841c77fb9a0e1fa4c6f32097de5b791f900a72d689ae1'
METADATA = {'START.json':'292312c9effcc417efbb986f66a68daf07436e6ea4a103d765ff71baf0ba4035',
    'EPISODE_0.json':'9c212191c5b30158665b9ccabdb431e164421b7afa218d323d1664fe613e3e0a'}
FAILED_READY_SHA = 'f7145810e67e0e16fc827112da7a0605087d39d9bf2bb37837dadbf83b13cabc'
READY_NAME = 'R139B_INDEPENDENT_ACTOR_READY.json'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value,stream,sort_keys=True,indent=2)
        stream.write('\n')


def ref(path):
    return dict(path=str(path),sha256=sha(path))


def legacy():
    require(sha(OLD/'handoff.py') == HANDOFF_SHA, 'frozen_attempt2_source')
    spec = importlib.util.spec_from_file_location('r139_frozen_attempt2',OLD/'handoff.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def metadata_contract(episode, rows):
    require(not any(row.get('cycle',55)>55 or row.get('sleep',55)>55 for row in rows), 'no_charged_C56_call')
    require(episode['terminal_reason']=='generation_failure' and episode['actor_calls']==1,
        'one_aborted_metadata_capture')
    require(episode['reads']==[] and episode['routes']==[] and len(episode['captures'])==1,
        'no_executed_environment_action')
    capture = episode['captures'][0]
    require(capture['turn']==0 and capture['response'] is None and capture['command'] is None
        and capture['prior_reads']==[], 'no_native_response_or_command')
    require(capture['error']==dict(type='TimeoutError',message='owned_lifetime_signal'), 'original_signal_only')
    require(episode['current']==episode['task']['node'] and episode['messages']==capture['messages'],
        'unchanged_initial_episode_context')


def proof():
    old = legacy()
    require(sha(OLD/'BOUNDARY.json')==BOUNDARY_SHA and sha(ROOT/'RESERVATIONS.jsonl')==LEDGER_SHA,
        'exact_C55_boundary_uncharged_ledger')
    boundary = read(OLD/'BOUNDARY.json')
    require(boundary['completed_cycle']==55 and boundary['next_cycle']==56 and boundary['sleeps']==55,
        'only_saved_C55_resume')
    release = read(OLD/'RELEASED.json')
    require(release['status']=='RELEASED' and release['boundary']==ref(OLD/'BOUNDARY.json'), 'actual_old_release')
    require(all(not Path('/proc',str(pid)).exists() for pid in (3356570,2608950,2608951)),
        'original_timeout_and_failed_successor_absent')
    for path, expected in boundary['preserved'].items():
        require(sha(path)==expected, 'preserved_C55_state')
    output = ROOT/'cycle_0056'
    require({path.name for path in output.iterdir()}==set(METADATA), 'only_two_uncharged_metadata_files')
    for name, expected in METADATA.items():
        require(sha(output/name)==expected, 'original_metadata_unchanged')
    require(sha(ROOT/'R139_INDEPENDENT_ACTOR_READY.json')==FAILED_READY_SHA, 'failed_ready_preserved')
    failed = read(ROOT/'R139_INDEPENDENT_ACTOR_READY.json')
    require(failed['pid']==2608951 and failed['optimizer_restored'] is True and failed['next_cycle']==56,
        'exact_failed_load_receipt')
    require(failed['adapter']==read(boundary['checkpoint']['path'])['adapter'], 'failed_attempt_same_saved_adapter')
    rows = [json.loads(line) for line in (ROOT/'RESERVATIONS.jsonl').read_text().splitlines() if line.strip()]
    require(len(rows)==3175, 'all_3175_charges_preserved')
    metadata_contract(read(output/'EPISODE_0.json'),rows)
    for path in (ROOT/'R121_PARENT_DELIVERY').glob('*.applied.json'):
        require(str(path) in boundary['preserved'], 'no_unrecorded_parent_consumption')
    native = old.load_native()
    native.verify(ROOT)
    cohort = read(ROOT/'COHORT.json')
    task = cohort['train'][110 % len(cohort['train'])]
    attempts = []
    def no_dispatch(messages):
        attempts.append(messages)
        raise TimeoutError('owned_lifetime_signal')
    simulated = native.episode(task['world'],task['task'],no_dispatch,cohort['store'])
    require(len(attempts)==1 and simulated==read(output/'EPISODE_0.json'), 'exact_CPU_reconstructed_uncharged_episode')
    require(not (ROOT/READY_NAME).exists(), 'new_attempt_not_started')
    return old, boundary


def repair_run(source, original_transform):
    source = original_transform(source)
    changes = {
        'R139_INDEPENDENT_ACTOR_READY.json':('R139B_INDEPENDENT_ACTOR_READY.json',2),
        'R139_INDEPENDENT_ANCHOR_INVENTORY.json':('R139B_INDEPENDENT_ANCHOR_INVENTORY.json',1),
        "output/f'EPISODE_{episode_index}.json'":('episode_path(output, episode_index)',2),
    }
    for before,(after,count) in changes.items():
        require(source.count(before)==count, 'exact_R139B_native_patch_seam')
        source = source.replace(before,after)
    return source


def episode_path(output, episode_index):
    output = Path(output)
    if output==ROOT/'cycle_0056' and episode_index==0:
        require(sha(output/'EPISODE_0.json')==METADATA['EPISODE_0.json'], 'aborted_metadata_preserved')
        return output/'EPISODE_0_R139B.json'
    return output/f'EPISODE_{episode_index}.json'


def adoptable_start(output, plan):
    output = Path(output)
    reference = plan['adopt_start']
    return bool(output==ROOT/'cycle_0056' and reference and reference==ref(output/'START.json')
        and {path.name for path in output.iterdir()}==set(METADATA)
        and all(sha(output/name)==expected for name,expected in METADATA.items()))


def repair_resume(source):
    before = 'adoptable_start=adoptable_start)'
    require(source.count(before)==1, 'exact_resume_namespace')
    return source.replace(before,'adoptable_start=adoptable_start, episode_path=episode_path)')


def prepare():
    require(Path(__file__).resolve()==STAGE/'handoff.py', 'immutable_attempt3_source')
    old, prior = proof()
    native = old.load_native()
    compile(repair_run(inspect.getsource(native.run),old.resume_source),'<CPU_R139B_resume>','exec')
    compile(repair_resume(inspect.getsource(old.resume)),'<CPU_R139B_resume_namespace>','exec')
    require(read(STAGE/'CPU_TESTS.json')['passed'] is True, 'own_CPU_tests')
    boundary = deepcopy(prior)
    for name in METADATA:
        boundary['preserved'][str(ROOT/'cycle_0056'/name)] = sha(ROOT/'cycle_0056'/name)
    for path in (ROOT/'R139_INDEPENDENT_ACTOR_READY.json',OLD/'READY.json',OLD/'RELEASED.json',
                 OLD/'RESUME_PLAN.json',OLD/'HISTORY.json',OLD/'LAUNCH.json',OLD/'ADMISSION_PROCESS.json'):
        boundary['preserved'][str(path)] = sha(path)
    boundary['repair'] = dict(original_boundary=ref(OLD/'BOUNDARY.json'), metadata_only=True,
        no_charged_call_replayed=True, episode_metadata=ref(ROOT/'cycle_0056/EPISODE_0.json'),
        new_episode_path=str(ROOT/'cycle_0056/EPISODE_0_R139B.json'))
    write(STAGE/'BOUNDARY.json',boundary)
    (STAGE/'RELEASED.json').symlink_to(OLD/'RELEASED.json')
    ready = dict(schema='R139B_METADATA_ONLY_RESUME_REPAIR_V1',root=str(ROOT),
        source_sha256=sha(__file__),original_handoff=ref(OLD/'handoff.py'),
        original_plan_sha256=old.PLAN_SHA,boundary=ref(STAGE/'BOUNDARY.json'),tests=ref(STAGE/'CPU_TESTS.json'),
        hard_end_unix=read(OLD/'READY.json')['hard_end_unix'],provider=old.MODEL,
        preserved_old_files=len(prior['preserved']),ledger_rows=3175,ledger_sha256=LEDGER_SHA,
        actor_ready_filename=READY_NAME,observed_unix=time.time(),no_reset=True,no_dispatch=True)
    ready.update(original_release=ref(OLD/'RELEASED.json'),release_reused_unchanged=True,new_signals=0)
    write(STAGE/'READY.json',ready)
    write(STAGE/'GO_TEMPLATE.json',dict(authorized=False,ready_sha256=sha(STAGE/'READY.json'),
        published_commit='',logical_life_reset=False,expires_unix=ready['hard_end_unix']))
    return dict(status='CPU_PREPARED_NOT_LAUNCHED',source_sha256=sha(__file__),ready=ref(STAGE/'READY.json'),
        boundary_sha256=sha(STAGE/'BOUNDARY.json'),preserved_old_files=len(prior['preserved']),
        ledger_rows=3175,uncharged_episode_metadata_verified=True)


def verify_stage(stage):
    require(Path(stage)==STAGE and Path(__file__).resolve()==STAGE/'handoff.py', 'exact_attempt3')
    ready = read(STAGE/'READY.json')
    require(ready['source_sha256']==sha(__file__) and sha(ready['tests']['path'])==ready['tests']['sha256'],
        'published_repair_source_tests')
    require(sha(STAGE/'BOUNDARY.json')==ready['boundary']['sha256'], 'prepared_boundary')
    proof()
    return ready


def authorize(stage):
    ready = verify_stage(stage)
    go = read(STAGE/'GO.json')
    require(go['authorized'] is True and go['ready_sha256']==sha(STAGE/'READY.json')
        and bool(go['published_commit']) and go['logical_life_reset'] is False, 'Main_exact_publication_required')
    require(time.time()<go['expires_unix']<=ready['hard_end_unix'], 'original_wall')
    return ready,go


def resume():
    authorize(STAGE)
    old = legacy()
    values = dict(old.resume.__globals__,verify_stage=verify_stage,
        resume_source=lambda source:repair_run(source,old.resume_source),
        adoptable_start=adoptable_start,episode_path=episode_path)
    exec(compile(repair_resume(inspect.getsource(old.resume)),__file__+':saved_resume','exec'),values)
    values['resume'](STAGE)


def supervise(python):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='', 'CPU_supervisor_only')
    authorize(STAGE)
    require(not (STAGE/'LAUNCH.json').exists(), 'one_attempt3_launch')
    old = legacy()
    values = dict(old.supervise.__globals__,__file__=__file__,authorize=authorize,
        release=lambda stage:dict(status='RELEASED',release=ref(STAGE/'RELEASED.json')))
    return FunctionType(old.supervise.__code__,values,'supervise',old.supervise.__defaults__)(STAGE,python)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase',choices=('prepare','check','resume','supervise'))
    parser.add_argument('--stage',type=Path,default=STAGE)
    parser.add_argument('--python')
    args = parser.parse_args()
    require(args.stage==STAGE, 'attempt3_only')
    if args.phase=='supervise':
        require(args.python=='/localhome/local-rohing/v2/venv/bin/python', 'original_native_venv')
        result = supervise(args.python)
    elif args.phase=='check':
        verify_stage(STAGE)
        result = dict(status='CPU_CHECK_PASS',ready=ref(STAGE/'READY.json'),signals=0,calls=0)
    else:
        result = globals()[args.phase]()
    if result is not None:
        print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()
