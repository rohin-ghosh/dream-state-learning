"""One-shot, no-signal custody after R127; exact unfinished gen7 continuation."""

import argparse
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import sys
import time


BASE = Path('/localhome/local-rohing')
PRIOR = BASE/'orch_r119_l1_gen7_continuation_20260915_attempt1'
RELEASE = BASE/'orch_r119_l1_gen7_r127_handover_20260915_attempt1/RELEASED.json'
RELEASE_SHA = '07ca220976b1fa7d7fa7fd41cebe9a3e5891735987e82435e13c9735a25f02ae'
ASSAY = BASE/'orch_r127_route_transfer_20260915'
PLAN_SHA = '12710e14684045bd5e5b31187bac6094ac4e00e65e318a2b6a11d724d0139846'
READY_SHA = 'e99f4ce44ce8ae5c9534ae4de45b1935f12f797439fafec382a3caeceaa3b5df'
CONTINUE_SHA = 'a4544a3f989b2a3e70b7f979867c0424fd2aec613d708fe34062abdbcce741b3'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    temporary = path.with_suffix(path.suffix+'.pending')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    assert not path.exists(), 'one_shot_receipt_exists'
    temporary.rename(path)


def cursor(release):
    assert release['status'] == 'RELEASED' and release['no_replay']
    progress = release['boundary']['progress']
    assert (progress['calls'], progress['inherited_calls'], progress['batch'], progress['position']) == (21259,15842,302,17)
    assert release['boundary']['next_call'] == 21260
    assert release['boundary']['next_cursor'] == dict(batch=302,position=19)
    assert 16384-(progress['calls']-progress['inherited_calls']) == 10967
    return progress


def continuation(root):
    path = root/'orch_r119_l1_gen7_continue.py'
    assert sha(path) == CONTINUE_SHA
    spec = importlib.util.spec_from_file_location('pinned_continue',path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    context = dict(module.__dict__, __file__=str(Path(__file__).resolve()))
    source = inspect.getsource(module.configuration)
    assert source.count('== 20286') == 1
    source = source.replace('== 20286','== 21259')
    exec(compile(source,__file__,'exec'),context)
    for name in ('generate','supervise'):
        exec(compile(inspect.getsource(getattr(module,name)),__file__,'exec'),context)
    return context


def metadata(run, plan_path):
    if not (run/'TERMINAL.json').exists():
        return None
    start = read(run/'START.json')
    assert start['plan'] == dict(path=str(plan_path),sha256=PLAN_SHA)
    terminal = read(run/'TERMINAL.json')
    assert terminal['status'] in ('COMPLETE','INCOMPLETE')
    assert terminal['optimizer_steps'] == terminal['training_rows'] == terminal['parent_calls'] == 0
    launches = sorted(run.glob('*_LAUNCH.json'))
    files = [run/'START.json',run/'TERMINAL.json']
    pids = [start['pid']]
    outcomes = []
    for path in launches:
        launch = read(path)
        condition = launch['condition']
        assert path.name == condition+'_LAUNCH.json'
        exit_path = run/(condition+'_EXIT.json')
        assert exit_path.exists(), 'terminal_without_child_exit'
        outcome = read(exit_path)
        assert outcome['condition'] == condition and outcome['no_retry'] is True
        assert launch['started_unix'] <= outcome['finished_unix'] <= terminal['finished_unix']
        outcomes.append(outcome)
        pids.append(launch['pid'])
        files.extend((path,exit_path))
    assert sorted(outcomes,key=lambda item:item['condition']) == sorted(terminal['results'],key=lambda item:item['condition'])
    assert len(pids) == len(set(pids))
    return dict(files={str(path):sha(path) for path in files},pids=pids,status=terminal['status'])


def absent(pids):
    return all(not (Path('/proc')/str(pid)).exists() for pid in pids)


def validate(root):
    pins = read(root/'SOURCE_PINS.json')
    for path, expected in pins.items():
        assert sha(root/path) == expected, 'source_pin_changed'
    assert sha(RELEASE) == RELEASE_SHA
    assert sha(ASSAY/'PLAN.json') == PLAN_SHA and sha(ASSAY/'READY.json') == READY_SHA
    release = read(RELEASE)
    cursor(release)
    assert sha(release['capture_manifest']['path']) == release['capture_manifest']['sha256']
    config = read(root/'FORKS.json')
    assert config == read(PRIOR/'FORKS.json'), 'original_bounds_and_seed_unchanged'
    assert config['hard_deadline_unix'] == config['lease_end_unix']-21600 == release['hard_deadline_unix']
    assert sha(config['service_identity']) == release['service_identity_sha256']
    assert config['uuid_by_index'][7] == release['uuid']
    plan = read(ASSAY/'PLAN.json')
    assert plan['uuid'] == release['uuid'] and plan['service_identity'] == config['service_identity']
    return release,config,Path(plan['output'])


def watch(root):
    release,config,run = validate(root)
    ready = read(root/'CUSTODY_PRE_GPU.json')
    assert ready['cpu_passed'] and ready['builder_line'].startswith('[Builder]')
    assert ready['source_pins_sha256'] == sha(root/'SOURCE_PINS.json')
    write(root/'ARMED.json',dict(pid=os.getpid(),observed_unix=time.time(),gpu_launched=False,
        release_sha256=RELEASE_SHA,next_call=21260,remaining_original_segment_allowance=10967))
    from gpu.orch_rich_hot_node2_scan import scan
    while time.time() < config['hard_deadline_unix']:
        before = metadata(run,ASSAY/'PLAN.json')
        if before is None or not absent(before['pids']):
            time.sleep(5)
            continue
        report = scan(7,Path(config['service_identity']))
        report.pop('host',None)
        scan_path = root/('ADMISSION_%d.json'%time.time_ns())
        write(scan_path,report)
        time.sleep(2)
        after = metadata(run,ASSAY/'PLAN.json')
        if before != after or not absent(after['pids']):
            continue
        if not report['clear']:
            time.sleep(5)
            continue
        assert report['scanner_euid'] == 0 and report['gpu']['uuid'] == release['uuid']
        validate(root)
        terminal = run/'TERMINAL.json'
        write(root/'ASSAY_RELEASED.json',dict(status='RELEASED',observed_unix=time.time(),
            metadata=after,all_recorded_pids_absent=True,no_signals=True,
            admission=dict(path=str(scan_path),sha256=sha(scan_path)),physical=7,uuid=release['uuid']))
        receipt = dict(physical=7,progress=cursor(release),source_sha256=sha(__file__),
            release_path=str(RELEASE),release_sha256=RELEASE_SHA,
            assay_terminal_path=str(terminal),assay_terminal_sha256=sha(terminal),
            capture_manifest=release['capture_manifest']['path'],capture_manifest_sha256=release['capture_manifest']['sha256'],
            prior_root=str(PRIOR),prior_stage=str(PRIOR/'segment0000'))
        write(root/'CURSOR_RESUME.json',receipt)
        write(root/'PRE_GPU.json',dict(ready,cursor_resume_sha256=sha(root/'CURSOR_RESUME.json')))
        continuation(root)['supervise'](root)
        return
    write(root/'EXPIRED.json',dict(status='ORIGINAL_LEASE_WALL',observed_unix=time.time()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('check','watch','generate'))
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--segment',type=int,default=0)
    options = parser.parse_args()
    if options.action == 'check':
        validate(options.root)
        context = continuation(options.root)
        module = context['worker'](options.root)
        module.config(options.root)
        compile(context['resumed_source'](inspect.getsource(module.generation.generate)),__file__,'exec')
        print(json.dumps(dict(status='CPU_PROVENANCE_PASS',next_call=21260,next_cursor='B302/P19',remaining=10967)))
    elif options.action == 'generate':
        continuation(options.root)['generate'](options.root,options.segment)
    else:
        try:
            watch(options.root)
        except BaseException as error:
            write(options.root/'FAILED.json',dict(error_type=type(error).__name__,error=str(error),no_retry=True,observed_unix=time.time()))
            raise


if __name__ == '__main__':
    main()
