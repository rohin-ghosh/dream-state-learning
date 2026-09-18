"""Read-only CODE boundary validation and immutable released-life certificate."""

import argparse
from collections import Counter
from copy import deepcopy
from pathlib import Path
import time

from gpu import orch_r108_code_parent_r116_shared as client


run = client.run
require = client.require


def carry(rows):
    bindings = [row for row in rows if row['kind'] == 'PARENT'
        and row['status'] in ('COMPLETE','SILENT') and row.get('reflection_settings')]
    last = max(bindings,key=lambda row:(row['finished_unix'],row['id'])) if bindings else None
    return dict(schema='R118_CODE_CARRY_V1',
        reflection_settings=deepcopy(last['reflection_settings']) if last else
            dict(effective_max_new_tokens=4096,status='DEFAULT_CAP'),
        reflection_source_id=last['id'] if last else None,
        conversation_carry='NO_CROSS_CYCLE_CONVERSATION_IN_PREDECESSOR',
        old_experience_replayed=False,
        reservation_counts=dict(Counter(row['kind']+'_'+row['status'] for row in rows)))


def validate(root, *, process_exists=lambda pid:(Path('/proc')/str(pid)).exists()):
    root = Path(root).resolve(strict=True)
    plan = run.read(root/'PLAN.json')
    branch = {2:'F3',6:'A3'}.get(plan['physical'])
    require(branch is not None,'own_CODE_pair_only')
    request = run.read(root/'RELEASE_AFTER_CYCLE.json')
    release = run.read(root/'CYCLE_RELEASE_READY.json')
    require(request['receiver_ready'] is True and request['branch'] == branch,
        'explicit_matched_pair_release')
    require(request['predecessor_plan_sha256'] == run.sha(root/'PLAN.json'), 'original_PLAN_binding')
    require(release['request_sha256'] == run.sha(root/'RELEASE_AFTER_CYCLE.json'), 'linked_release_request')
    for key in ('roster','eight_ready'):
        reference = request[key]
        require(run.sha(Path(reference['path'])) == reference['sha256'],'actual_all_eight_bound')
    prepared = run.read(Path(request['eight_ready']['path']))
    require(prepared['branch_specs'][branch]['root'] == str(root), 'same_ready_root')
    bounds = {key:plan[key] for key in client.BOUND_FIELDS}
    require(bounds == prepared['branch_bounds'][branch] == request['bounds'], 'all_original_bounds')
    predecessors = request['predecessors']
    require(predecessors and all(not process_exists(item['pid']) for item in predecessors),
        'native_guard_readouts_must_all_exit')
    cycle = release['cycle']
    require(type(cycle) is int and cycle > 0, 'actual_completed_cycle')
    complete_path = root/'cycles'/f'C{cycle:03d}_COMPLETE.json'
    require(run.read(complete_path)['cycle'] == cycle,'matching_complete_cycle')
    paths = sorted((root/'reservations').glob('*.json'))
    rows = [run.read(path) for path in paths]
    require(rows and all(row['status'] in ('COMPLETE','SILENT','MISSING','FAILED')
        and type(row['cycle']) is int and row['cycle'] <= cycle for row in rows),
        'all_charged_calls_settled_no_later_cycle')
    require(max(row['cycle'] for row in rows) == cycle,'actual_cursor')
    for request_path in (root/'parent_queue').glob('*.request.json'):
        require(request_path.with_name(request_path.name.replace('.request.','.response.')).is_file(),
            'await_original_parent_delivery_no_retry')
    for claim in (root/'parent_claude').glob('*.claim'):
        publication = run.read(claim/'PUBLISHED.json')
        response = root/'parent_queue'/(claim.name.removesuffix('.claim')+'.response.json')
        require(run.sha(response) == publication['response_sha256'],'settled_provider_claim')
    return dict(root=root,branch=branch,bounds=bounds,release=release,
        predecessors=predecessors,rows=rows,next_cycle=cycle+1)


def publish(root):
    validated = validate(root)
    root = validated['root']
    target = root/'R118_SHARED_HANDOFF_BRANCH.json'
    if target.exists():
        document = run.read(target)
        require(all(run.sha(root/name) == expected for name,expected in document['preserved_files'].items()),
            'existing_handoff_unchanged')
        return document
    carry_path = root/'R118_CODE_CARRY.json'
    value = carry(validated['rows'])
    if carry_path.exists():
        require(run.read(carry_path) == value,'existing_carry_unchanged')
    else:
        run.write_new(carry_path,value)
    names = ['PLAN.json','RELEASE_AFTER_CYCLE.json','CYCLE_RELEASE_READY.json',
        'R118_CODE_CARRY.json','COHORT.json','LEGACY_READOUT.json','BROKER_CONFIG.json',
        'SHARED_CLIENT_READY.json','SOURCE_SHA256.json','CONT_SOURCE_SHA256.json',
        'CONTINUATION_BINDING.json','LAUNCH.json','CONT_LAUNCH.json','ADMISSION.json',
        'CONT_ADMISSION.json','COMPLETE.json','CONTINUATION_COMPLETE.json',
        'TERMINAL.json','CONTINUATION_TERMINAL.json','GUARD_TERMINAL.json',
        'CONT_GUARD_TERMINAL.json','CYCLE_ZERO_PROCESS.json']
    paths = [root/name for name in names if (root/name).is_file()]
    for folder in ('reservations','cycles','readouts','triples','environment','parent_queue',
        'parent_transcripts','parent_claude'):
        paths.extend(path for path in (root/folder).rglob('*')
            if path.is_file() and path.suffix not in ('.partial','.tmp'))
    preserved = {str(path.relative_to(root)):run.sha(path) for path in sorted(set(paths))}
    document = dict(schema='R118_CODE_RELEASED_HANDOFF_V1',root=str(root),branch=validated['branch'],
        bounds=validated['bounds'],release=dict(path=str(root/'CYCLE_RELEASE_READY.json'),
            sha256=run.sha(root/'CYCLE_RELEASE_READY.json')),
        predecessors=validated['predecessors'],preserved_files=preserved,
        next_cycle=validated['next_cycle'],carry=dict(path=str(carry_path),sha256=run.sha(carry_path)),
        charged_calls=len(validated['rows']),reservation_counts=value['reservation_counts'],
        original_deadline_unchanged=True,new_model_calls=0,new_provider_calls=0,
        observed_unix=time.time(),raw_on_node_only=True)
    require(all(run.sha(root/name) == expected for name,expected in preserved.items()),'stable_boundary_snapshot')
    run.write_new(target,document)
    return document


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    result=publish(args.root)
    print(result['branch'],str(args.root/'R118_SHARED_HANDOFF_BRANCH.json'),result['next_cycle'])
