"""Bounded existing-parent evidence; writes only this new receipt directory."""

import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'r167_legacy_parent_rollout'
sys.path.insert(0, str(OLD))
import legacy_takeover as legacy


def observe():
    rows = []
    probe = legacy.read(OLD / 'render_probe.py').decode().replace(
        '128 * 1024 * 1024', "request['read_cap']").replace(
        "request['start_index'] + 64", "request['start_index'] + request['record_cap']")
    for receipt in sorted(OLD.glob('*/RUNNING.json')):
        running = json.loads(legacy.read(receipt))
        config = json.loads(legacy.read(receipt.parent / 'CONFIG.json'))
        current = legacy.identity(running['parent']['pid'])
        assert all(current[key] == running['parent'][key] for key in ('pid', 'start_ticks', 'argv', 'uid'))
        row = dict(candidate=receipt.parent.name, parent=current, running=legacy.ref(receipt), attempts=[])
        budget, records = 64 * 1024 * 1024, 256
        paths = sorted((receipt.parent / 'parent').glob('parent_*/RESULT.json'))
        assert len(paths) <= 1000
        for path in paths:
            result = json.loads(legacy.read(path))
            item = dict(result=legacy.ref(path), status=result['status'], finished_unix=result['finished_unix'])
            if result['status'] == 'PUBLISHED':
                publication = result['inbox_publication']
                source = json.loads(legacy.read(path.parent / 'SOURCE.json'))
                start, anchor = source['record_count'] - 1, source['head_sha256']
                delivered = path.parent / 'DELIVERED.json'
                if delivered.exists():
                    delivery = json.loads(legacy.read(delivered))
                    assert delivery['inbox_id'] == publication['id']
                    start = delivery['consumption']['record_index']
                    anchor = delivery['consumption']['record_sha256']
                    item['delivery_receipt'] = legacy.ref(delivered)
                request = dict(root=config['root'], source_root=config['source_root'],
                    inbox_id=publication['id'], publication_sha256=publication['sha256'],
                    start_index=start, start_record_sha256=anchor, read_cap=budget, record_cap=min(64, records))
                item['publication'] = publication
                if budget > 0 and records > 0:
                    result_remote = subprocess.run(['bash', str(legacy.REPOSITORY / 'gpu' / (config['node'] + '_ssh.sh')),
                        'python3 - ' + shlex.quote(json.dumps(request))], input=probe.encode(),
                        capture_output=True, timeout=45)
                    records -= min(64, records)
                    if result_remote.returncode == 0:
                        item['render'] = json.loads(result_remote.stdout)
                        budget -= item['render']['bytes_read']
                    else:
                        budget = 0
                        item['render'] = dict(status='READ_FAILED_BUDGET_CLOSED',
                            stderr_sha256=legacy.digest(result_remote.stderr))
                else:
                    item['render'] = dict(status='CAP_REACHED_NOT_VERIFIED')
            row['attempts'].append(item)
        row['remaining_read_budget'] = budget
        rows.append(row)
    receipt = HERE / ('DELIVERY_' + str(time.time_ns()) + '.json')
    counts = dict(successors_alive=len(rows), published=sum(item['status'] == 'PUBLISHED'
        for row in rows for item in row['attempts']), rendered=sum(
        item.get('render', {}).get('status') == 'RENDERED_TEXT_VERIFIED'
        for row in rows for item in row['attempts']))
    legacy.write(receipt, dict(observed_unix=time.time(), parents=rows, counts=counts,
        kernel4=dict(status='PROVENANCE_BLOCKED_ORIGINAL_CONTINUES', parent=legacy.identity(716608)),
        no_signals=True, no_remote_writes=True, no_retention_claim=True))
    print(json.dumps(dict(receipt=legacy.ref(receipt), counts=counts)))


if __name__ == '__main__':
    observe()
