"""Read-only native monitoring, owned evidence archival, and terminal handoff."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time


REPO = Path(__file__).resolve().parents[1]
REMOTE = '/tmp/orch_terse_breadth_20260914_attempt1'
REMOTE_BY_HOST = dict(a100='/tmp/orch_terse_breadth_20260914_attempt2', node3=REMOTE)
LOCAL = REPO / 'gpu_artifacts_local/orch_terse_breadth_20260914_attempt1'
ANALYSIS = REPO / 'research_notes/analysis/orch_terse_breadth_20260914_attempt1'
WORKER = REPO / 'research_loop/workers/TERSE_BREADTH.md'
NOTEBOOK = REPO / 'research_notes/analysis/orch_terse_breadth_20260914_notebook.md'
HOSTS = (('a100', 'gpu/a100_ssh.sh', (0, 1, 2, 3)), ('node3', 'gpu/ovx2_ssh.sh', (4, 5)))


def utc():
    return datetime.now(timezone.utc).isoformat()


def remote(wrapper, command, **kwargs):
    return subprocess.run(['bash', str(REPO / wrapper), command], check=True, timeout=300, **kwargs)


def snapshot():
    result = dict(utc=utc(), lanes=[])
    for host, wrapper, lanes in HOSTS:
        script = f'''import json
from pathlib import Path
root=Path({REMOTE_BY_HOST[host]!r})
for lane in {lanes!r}:
    stages={{}}
    for phase in ('train','after','baseline'):
        directory=root/f'{{phase}}{{lane}}'
        path=directory/'RESULT.json'
        failed=directory/'FAILED.json'
        if path.exists() or failed.exists():
            data=json.loads((path if path.exists() else failed).read_text())
            stages[phase]={{key:data.get(key) for key in ('status','updates','model_calls','error','wall_seconds')}}
            if 'summary' in data: stages[phase]['primary']=data['summary']['primary']
        losses=directory/'LOSSES.jsonl'
        if phase=='train' and losses.exists() and phase not in stages:
            with losses.open('rb') as stream:
                stream.seek(max(0,losses.stat().st_size-4096))
                lines=stream.read().splitlines()
            try: stages[phase]={{'status':'RUNNING','last_loss':json.loads(lines[-1])}}
            except (ValueError,IndexError): stages[phase]={{'status':'RUNNING_PARTIAL_LINE'}}
    print(json.dumps(dict(lane=lane,done=(root/f'chain{{lane}}.done').exists(),stages=stages)))
'''
        response = remote(wrapper, 'python3 -c ' + shlex.quote(script), capture_output=True, text=True)
        result['lanes'].extend(dict(host=host, **json.loads(line)) for line in response.stdout.splitlines())
    return result


def archive():
    receipts = {}
    for host, wrapper, unused_lanes in HOSTS:
        partial = LOCAL / f'terminal_{host}_{time.time_ns()}.tar.gz.partial'
        final = LOCAL / f'terminal_{host}.tar.gz'
        if not final.exists():
            with partial.open('xb') as output:
                remote(wrapper, f'tar -czf - -C {shlex.quote(REMOTE_BY_HOST[host])} .', stdout=output)
            subprocess.run(['tar', '-tzf', str(partial)], check=True, stdout=subprocess.DEVNULL, timeout=120)
            partial.rename(final)
        extracted = LOCAL / f'terminal_{host}'
        if not extracted.exists():
            extracted.mkdir()
            subprocess.run(['tar', '--no-same-owner', '-xzf', str(final), '-C', str(extracted)], check=True, timeout=120)
        receipts[host] = dict(path=str(final), sha256=hashlib.sha256(final.read_bytes()).hexdigest())
    return receipts


def reduce_terminal(archives):
    roots = {host: LOCAL / f'terminal_{host}' for host, unused_wrapper, unused_lanes in HOSTS}
    summaries, failures = {}, []
    for host, unused_wrapper, lanes in HOSTS:
        for lane in lanes:
            for phase in ('train', 'after') + (('baseline',) if lane == 0 else ()):
                directory = roots[host] / f'{phase}{lane}'
                result = directory / 'RESULT.json'
                if not result.exists():
                    failed = directory / 'FAILED.json'
                    failures.append(dict(lane=lane, phase=phase,
                        failure=json.loads(failed.read_text()) if failed.exists() else 'MISSING_RESULT_SEE_GUARDIAN'))
                    continue
                data = json.loads(result.read_text())
                if data.get('status') != 'COMPLETE':
                    failures.append(dict(lane=lane, phase=phase, failure=data))
                summaries[f'{phase}{lane}'] = data
    report = dict(utc=utc(), archives=archives, failures=failures,
        reader_verified=False, promotion=False, old266_gate='FAIL_UNCHANGED',
        conclusion='INCOMPLETE_NATIVE_EVIDENCE' if failures else 'AUTHOR_COMPARISON_PENDING',
        caveats=['Only two independent training seeds', 'Shared cohort, corpus, and37ec ancestry',
                 'Sixteen-doseA40 versus four-doseA100 crosses hardware',
                 'Dose changes legacy rehearsal as well as new-target exposure',
                 'Not rich-data admission, loop evidence, or H1/H2'])
    if not failures:
        baseline = summaries['baseline0']['summary']['primary']['correct']
        pairs = []
        for full_lane, off_lane in ((0, 1), (2, 3), (4, 5)):
            full, off = summaries[f'after{full_lane}'], summaries[f'after{off_lane}']
            train_full, train_off = summaries[f'train{full_lane}'], summaries[f'train{off_lane}']
            assert full['batch_sha256'] == off['batch_sha256'] == train_full['batch_sha256'] == train_off['batch_sha256']
            assert full['batch_sha256'] == summaries['baseline0']['batch_sha256']
            assert full['seed'] == off['seed'] and full['trajectory_presentations'] == off['trajectory_presentations']
            assert train_full['row_presentations'] == train_off['row_presentations']
            assert train_full['reference_supervised_tokens'] == train_off['reference_supervised_tokens']
            assert full['loaded_adapter_state_sha256'] == train_full['adapter_state_after']
            assert off['loaded_adapter_state_sha256'] == train_off['adapter_state_after']
            assert full['pid'] != train_full['pid'] and off['pid'] != train_off['pid']
            assert all(entry['frozen_base_unchanged'] for entry in (full, off, train_full, train_off, summaries['baseline0']))
            full_score, off_score = (entry['summary']['primary']['correct'] for entry in (full, off))
            reference = sum(entry['summary']['paired']['correct'] for entry in full['summary']['deterministic_first_port'])
            survived = full['summary']['engineering_target_met'] and full_score > max(off_score, baseline, reference)
            pairs.append(dict(seed=full['seed'], dose=full['trajectory_presentations'], full=full_score,
                loss_off=off_score, baseline=baseline, deterministic=reference, denominator=64,
                difference=full_score-off_score, full_goals=full['summary']['primary']['goals'],
                goal_denominator=128, checks=full['summary']['checks'], conjunction_survived=survived,
                full_state=train_full['adapter_state_after'], control_state=train_off['adapter_state_after']))
        report.update(pairs=pairs, conclusion='TWO_SEED_FOUR_DOSE_SURVIVAL_AUTHOR_ONLY'
            if all(pair['conjunction_survived'] for pair in pairs[:2]) else 'FOUR_DOSE_BREADTH_CONJUNCTION_NOT_REPLICATED')
    return report


def publish(report):
    path = ANALYSIS / 'TERMINAL_AUTHOR_RESULT.json'
    with path.open('x') as stream:
        json.dump(report, stream, sort_keys=True, indent=2)
        stream.write('\n')
    text = (f"\n{utc()} [Builder] TERMINAL_READY: {report['conclusion']}. "
            'Own six fit/readout chains ended; terminal archives and author summary are preserved in '
            '`research_notes/analysis/orch_terse_breadth_20260914_attempt1/TERMINAL_AUTHOR_RESULT.json`. '
            'Request ordered SEQ now, and independent reader verification; no promotion or extra256. '
            'Independent blind cohort worker was not contacted. '
            'Publication failure, if any, is recorded in terminal_publish.json.\n')
    for journal in (WORKER, NOTEBOOK):
        with journal.open('a') as stream:
            stream.write(text)
    paths = [str(item.relative_to(REPO)) for item in (path, WORKER, NOTEBOOK)]
    publication = dict(utc=utc(), paths=paths)
    try:
        if (REPO / '.git/MERGE_HEAD').exists():
            raise RuntimeError('SHARED_MERGE_ACTIVE_MAIN_RECONCILIATION_REQUIRED')
        subprocess.run(['git', 'add', '--', *paths], cwd=REPO, check=True, timeout=30)
        subprocess.run(['git', 'commit', '--only', '-m', 'TERSE-BREADTH terminal author result and reader handoff', '--', *paths],
                       cwd=REPO, check=True, timeout=60)
        publication['commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
        subprocess.run(['git', 'push', 'origin', 'HEAD:main'], cwd=REPO, check=True, timeout=90)
        publication['status'] = 'PUBLISHED'
    except Exception as error:
        publication.update(status='PRESERVED_NEEDS_MAIN_PUBLICATION', error=repr(error))
    (ANALYSIS / 'terminal_publish.json').write_text(json.dumps(publication, indent=2) + '\n')


def main():
    deadline = json.loads((ANALYSIS / 'COLLECTION_LAUNCH.json').read_text())[0]['allocation_deadline_epoch']
    while time.time() < deadline + 600:
        try:
            current = snapshot()
            with (LOCAL / 'native_monitor.jsonl').open('a') as stream:
                stream.write(json.dumps(current) + '\n')
            if len(current['lanes']) == 6 and all(lane['done'] for lane in current['lanes']):
                archives = archive()
                try:
                    report = reduce_terminal(archives)
                except Exception as error:
                    report = dict(utc=utc(), archives=archives, conclusion='AUTHOR_VERIFICATION_FAILED',
                                  error=repr(error), reader_verified=False, promotion=False, old266_gate='FAIL_UNCHANGED')
                publish(report)
                return
        except Exception as error:
            with (LOCAL / 'monitor_errors.jsonl').open('a') as stream:
                stream.write(json.dumps(dict(utc=utc(), error=repr(error))) + '\n')
            if (ANALYSIS / 'TERMINAL_AUTHOR_RESULT.json').exists():
                return
        time.sleep(90)
    (LOCAL / 'MONITOR_DEADLINE.txt').write_text(utc() + ' native guardians remain independently bounded\n')


if __name__ == '__main__':
    main()
