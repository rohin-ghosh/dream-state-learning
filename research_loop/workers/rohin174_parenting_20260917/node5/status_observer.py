"""Read-only process/receipt census; no parent or child control actions."""

import json
from pathlib import Path
import time

from activate_parent import identity, read, reference, write


HERE = Path(__file__).resolve().parent
ROOTS = ('ACTIVATION_A_1789678829928180897', 'ACTIVATION_B_1789678847374158305',
         'ACTIVATION_C_1789678852147451612', 'ACTIVATION_D_1789678856612153632')


def observe():
    rows = []
    current_bindings = {}
    for ready_path in HERE.glob('ACTIVATION_*/READY.json'):
        for binding in read(ready_path)['manifests']:
            started_path = ready_path.parent / (binding['label'] + '_STARTED.json')
            if not started_path.exists() or binding['label'] == 'C2':
                continue
            stamp = read(started_path)['observed_unix']
            previous = current_bindings.get(binding['label'])
            if previous is None or stamp > previous[0]:
                current_bindings[binding['label']] = (stamp, ready_path.parent, binding)
    for unused_stamp, root, binding in sorted(current_bindings.values(), key=lambda entry: entry[2]['label']):
            manifest = read(binding['path'])
            output = Path(manifest['output'])
            started = read(root / (binding['label'] + '_STARTED.json'))
            successors = list(HERE.glob('CONSOLE_' + binding['label'] + '_*/parent/ACTIVE_PARENT.json'))
            predecessor_output = output
            if successors:
                active_path = max(successors, key=lambda path: read(path)['observed_unix'])
                active = read(active_path)
                output = active_path.parent
                started = dict(pid=active['pid'], identity=active['identity'])
            route_successors = list(HERE.glob('ROUTE_' + binding['label'] + '_*/parent/ACTIVE_PARENT.json'))
            if route_successors:
                active_path = max(route_successors, key=lambda path: read(path)['observed_unix'])
                active = read(active_path)
                output = active_path.parent
                started = dict(pid=active['pid'], identity=active['identity'])
            row = dict(label=binding['label'], arm=manifest['arm'], manifest=binding,
                       operator_pid=started['pid'], receipts={}, operator_live=False,
                       current_output=str(output), original_activation_output=str(predecessor_output))
            try:
                actual = identity(started['pid'])
                row['operator_live'] = actual['start_ticks'] == started['identity']['start_ticks'] and actual['state'] not in ('Z', 'X')
                row['operator_state'] = actual['state']
            except FileNotFoundError:
                pass
            for receipt in ('ACTIVE_PARENT', 'PARENT_EXITED', 'FAILED_CLOSED', 'FIRST_PUBLICATION',
                            'FIRST_RENDERED_REQUEST', 'WITHDRAWAL_COMPLETE'):
                path = output / (receipt + '.json')
                if path.exists():
                    row['receipts'][receipt] = reference(path)
            row['current_status'] = 'STARTED_NOT_TAKEOVER'
            if 'FAILED_CLOSED' in row['receipts']:
                failure = read(row['receipts']['FAILED_CLOSED']['path'])
                row.update(current_status='OPERATOR_FAILED_NOT_CHILD_FAILURE', failure=failure)
            elif 'ACTIVE_PARENT' in row['receipts']:
                row['current_status'] = 'R175_ACTIVE_NO_PUBLICATION_VERIFIED'
            if 'FIRST_PUBLICATION' in row['receipts']:
                row['current_status'] = 'PUBLISHED_NOT_RENDERED'
            if 'FIRST_RENDERED_REQUEST' in row['receipts']:
                row['current_status'] = 'RENDERED_REQUEST_VERIFIED'
            latest = sorted(output.glob('STATUS_*.json'))
            if latest:
                row['latest_status'] = read(latest[-1]).get('status')
                row['latest_status_receipt'] = reference(latest[-1])
            polls = sorted(output.glob('POLL_*.json'))
            if polls:
                snapshot = read(polls[-1])['snapshot']
                row['current_snapshot'] = {key: snapshot[key] for key in
                    ('caught_up', 'response_count', 'request_count', 'sleep_count', 'head_sha256')}
                row['current_snapshot_receipt'] = reference(polls[-1])
            row['attempts'] = []
            for path in sorted(output.glob('parent_*/RESULT.json')):
                result = read(path)
                row['attempts'].append(dict(receipt=reference(path), status=result['status'],
                                            error=result.get('error'), model=result.get('model')))
            if route_successors:
                route_binding = read(output.parent / 'BINDING.json')
                eligible = set(route_binding.get('eligible_publication_ids', []))
                for entry in read(output / 'SEED.json')['attempts']:
                    result = entry['result']
                    if result.get('status') == 'PUBLISHED' and result['publication']['id'] in eligible:
                        row['attempts'].append(dict(receipt=entry['refs']['result'],status=result['status'],
                            error=result.get('error'),model=result.get('model'),inherited_reserved_publication=True))
                row['route_binding'] = reference(output.parent / 'BINDING.json')
            rows.append(row)
    receipt = HERE / ('BASELINE_STATUS_' + str(time.time_ns()) + '.json')
    write(receipt, dict(observed_unix=time.time(), rows=rows, C2='EXCLUDED_MAIN_OWNED_NO_ACTION',
        child_signals=0, peers_active=False, GPU_actions=0,
        historical_blockers=dict(reader='Original ambiguous_delivery refusals preserved; exact saved-render identity repair uses new sources',
                                 run1_provider='Prior HTTP404 preserved; console publication must not be retried'),
        builder='[Builder] 2026-09-17: 12 actual-owned-source CPU tests per arm and receiving hash/compile checks PASS; lifecycle and publication evidence remain separate'))
    print(json.dumps(dict(receipt=reference(receipt), rows=[dict(label=row['label'],
        status=row['current_status'], latest=row.get('latest_status'), live=row['operator_live']) for row in rows])))


if __name__ == '__main__':
    observe()
