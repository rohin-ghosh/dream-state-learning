"""Score-blind readout lifecycle receipts for prospective matched lives."""

import os
from pathlib import Path
import time

from gpu import orch_r125_continual_native as native


SCHEMA = 'R150_MATCHED_READOUT_CUSTODY_V1'


def paths(plan, cycle):
    name = native.readout_name(plan, cycle)
    directory = Path(plan['root'])/'readouts'
    return dict(output=directory/name, dispatch=directory/f'{name}_DISPATCH.json',
        failure=directory/f'{name}_FAILED.json', log=directory/f'{name}.log',
        opened=directory/f'{name}_R150_OPEN.json', closed=directory/f'{name}_R150_CLOSED.json')


def binding(plan_path, plan, checkpoint, cycle):
    return dict(schema=SCHEMA, plan_sha256=native.sha(plan_path), cycle=cycle,
        matched_arm=plan['matched_arm'], cohort_sha256=plan['matched_cohort']['sha256'],
        checkpoint_commit_sha256=native.sha(Path(checkpoint['adapter_path']).parent/'COMMIT.json'),
        output_path=str(paths(plan, cycle)['output']), parent_present=False, history_shared=False)


def disposition(plan_path, plan, checkpoint, cycle):
    locations = paths(plan, cycle)
    for path in locations.values():
        native.require(not any(item.is_symlink() for item in (path, *path.parents)), 'readout_custody_no_symlinks')
    present = {name for name, path in locations.items() if path.exists()}
    if not present:
        return 'NOT_STARTED'
    native.require({'opened', 'closed', 'dispatch'} <= present,
                   'readout_custody_unresolved_before_model_load')
    expected = binding(plan_path, plan, checkpoint, cycle)
    opened, closed, dispatch = [native.read(locations[name]) for name in ('opened', 'closed', 'dispatch')]
    native.require(opened.get('binding') == closed.get('binding') == expected, 'exact_readout_custody_binding')
    native.require(closed.get('open_sha256') == native.sha(locations['opened'])
        and closed.get('dispatch_sha256') == native.sha(locations['dispatch']), 'bound_readout_lifecycle_files')
    native.require(closed.get('status') == 'DISPATCHER_RETURNED_AFTER_CLEANUP'
        and closed.get('resident_pid') == opened.get('resident_pid')
        and closed.get('resident_start_ticks') == opened.get('resident_start_ticks')
        and closed.get('native_dispatcher_sha256') == opened.get('native_dispatcher_sha256')
        == native.sha(native.__file__), 'original_dispatcher_completed_cleanup')
    native.require(dispatch.get('cycle') == cycle
        and dispatch.get('checkpoint_sha256') == expected['checkpoint_commit_sha256']
        and dispatch.get('parent_present') is False and dispatch.get('history_shared') is False,
        'native_readout_dispatch_binding')
    return 'CLOSED'


def fresh_readout(child, plan_path, checkpoint, cycle):
    plan = child.plan
    native.require(disposition(plan_path, plan, checkpoint, cycle) == 'NOT_STARTED', 'readout_no_implicit_replay')
    locations = paths(plan, cycle)
    locations['opened'].parent.mkdir(parents=True, exist_ok=True)
    process_id = os.getpid()
    start_ticks = Path('/proc', str(process_id), 'stat').read_text().rsplit(')', 1)[1].split()[19]
    expected = binding(plan_path, plan, checkpoint, cycle)
    resident = dict(resident_pid=process_id, resident_start_ticks=start_ticks,
                    native_dispatcher_sha256=native.sha(native.__file__))
    native.write_once(locations['opened'], dict(binding=expected, opened_unix=time.time(), **resident))
    native.fresh_readout(child, plan_path, checkpoint, cycle)
    native.require(locations['dispatch'].is_file(), 'native_dispatch_receipt_required')
    native.write_once(locations['closed'], dict(binding=expected, **resident,
        status='DISPATCHER_RETURNED_AFTER_CLEANUP', closed_unix=time.time(),
        open_sha256=native.sha(locations['opened']), dispatch_sha256=native.sha(locations['dispatch']),
        evaluation_completion_marker_present=(locations['output']/'COMPLETE.json').is_file(),
        evaluation_failure_marker_present=locations['failure'].is_file(),
        evaluation_contents_read=False, evaluations_gate_continuation=False))
    native.require(disposition(plan_path, plan, checkpoint, cycle) == 'CLOSED', 'readout_custody_closed')
