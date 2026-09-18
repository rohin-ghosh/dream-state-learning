"""One bounded metadata observation of owned successors and deferred parents."""

import datetime
import json
from pathlib import Path
import shlex
import subprocess
import time

import legacy_takeover as legacy


def observe():
    rows = []
    replacements = {}
    for receipt in legacy.HERE.glob('*/RUNNING.json'):
        binding = json.loads(legacy.read(receipt.parent / 'BINDING.json'))
        replacements[binding['root']] = json.loads(legacy.read(receipt))
    for directory in sorted(legacy.HERE.iterdir()):
        if not (directory / 'DISPATCH_RESULT.json').exists():
            continue
        binding = json.loads(legacy.read(directory / 'BINDING.json'))
        row = dict(candidate=directory.name)
        if not (directory / 'RUNNING.json').exists():
            if binding['root'] in replacements:
                successor = replacements[binding['root']]
                row.update(status='PRESERVED_REFUSAL_SUPERSEDED_BY_SUCCESSOR',
                    successor_pid=successor['parent']['pid'])
                rows.append(row)
                continue
            try:
                original = legacy.identity(binding['parent']['pid'])
                row.update(status='DEFERRED_ORIGINAL_ALIVE', pid=original['pid'], state=original['state'],
                    same_identity=all(original[key] == binding['parent'][key]
                        for key in ('pid', 'start_ticks', 'argv', 'uid')))
            except OSError:
                row.update(status='ORIGINAL_ABSENT_NO_ACTION')
            rows.append(row)
            continue
        running = json.loads(legacy.read(directory / 'RUNNING.json'))
        try:
            current = legacy.identity(running['parent']['pid'])
            row.update(status='SUCCESSOR_ALIVE', pid=current['pid'], state=current['state'],
                same_identity=all(current[key] == running['parent'][key]
                    for key in ('pid', 'start_ticks', 'argv', 'uid')))
        except OSError:
            row.update(status='SUCCESSOR_ABSENT_NO_RETRY')
        config = json.loads(legacy.read(directory / 'CONFIG.json'))
        principles = legacy.read(config['principles_path'])
        attempts = []
        for attempt in sorted((directory / 'parent').glob('parent_*'))[:3]:
            projected = dict(attempt=attempt.name)
            if (attempt / 'SYSTEM.txt').exists():
                projected.update(system=legacy.ref(attempt / 'SYSTEM.txt'),
                    exact_policy_principles_present=principles in legacy.read(attempt / 'SYSTEM.txt'))
            if (attempt / 'RESULT.json').exists():
                result = json.loads(legacy.read(attempt / 'RESULT.json'))
                projected.update(status=result['status'], result=legacy.ref(attempt / 'RESULT.json'),
                    finished_unix=result['finished_unix'])
                if result['status'] == 'PUBLISHED':
                    publication = result['inbox_publication']
                    projected['publication'] = publication
                    source = json.loads(legacy.read(attempt / 'SOURCE.json'))
                    request = dict(root=config['root'], source_root=config['source_root'],
                        inbox_id=publication['id'], publication_sha256=publication['sha256'],
                        start_index=source['record_count'] - 1, start_record_sha256=source['head_sha256'])
                    remote = subprocess.run(['bash', str(legacy.REPOSITORY / 'gpu' / (config['node'] + '_ssh.sh')),
                        'python3 - ' + shlex.quote(json.dumps(request))],
                        input=legacy.read(legacy.HERE / 'render_probe.py'), capture_output=True, timeout=45)
                    if remote.returncode == 0:
                        projected['render'] = json.loads(remote.stdout)
                    else:
                        projected['render'] = dict(status='READ_ONLY_RENDER_CHECK_FAILED',
                            stderr_sha256=legacy.digest(remote.stderr), returncode=remote.returncode)
            attempts.append(projected)
        row['attempts'] = attempts
        rows.append(row)
    now = datetime.datetime.now(datetime.timezone.utc)
    path = legacy.HERE / ('MONITOR_' + now.strftime('%Y%m%dT%H%M%S') + '_' + str(time.time_ns()) + '.json')
    legacy.write(path, dict(observed_unix=now.timestamp(), candidates=rows, no_process_signals=True,
        no_readout_contents=True, no_claim_of_scientific_gain=True))
    print(json.dumps(dict(receipt=legacy.ref(path), candidates=[dict(candidate=row['candidate'],
        status=row['status'], pid=row.get('pid'), attempts=[dict(attempt=item['attempt'],status=item.get('status'),
        policy=item.get('exact_policy_principles_present'),render=item.get('render',{}).get('status'))
        for item in row.get('attempts',[])]) for row in rows]), indent=2))


if __name__ == '__main__':
    observe()
