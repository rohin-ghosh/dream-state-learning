"""Reuse exact R181/R144 preservation for the four R203 reassigned lives."""

import argparse
import json
import os
from pathlib import Path
import time

import retire_brain_guided6 as existing
from math_c import HOME, HELPER_BUNDLE, WALL, PYTHON, host, read, require, sha, write


def prepare_binding(physical, capture=False, reload_context=None):
    allowed = (0, 1, 2, 3, 5, 6, 7) if reload_context is not None else (0, 1, 3, 5, 6)
    require(physical in allowed, 'only_Main_named_reallocations_or_same_life_reload')
    host()
    root = HOME if physical == 6 else HOME.parent / f'SCALE_physical{physical}'
    if reload_context is None:
        census = read(HOME / ('RELOAD6_CENSUS.json' if physical == 6 else 'R203_INVENTORY_20260918T0312Z.json'))
        selected = next(row for row in census['learners'] if row['plan']['physical'] == physical)
    else:
        selected = reload_context['selected']
        require(selected['plan']['root'] == str(root / 'life'), 'same_current_clone_root_only')
    rollout = existing.module('existing_node4_rollout', HELPER_BUNDLE / 'node4_rollout.py')
    helpers = rollout.helper_module(HELPER_BUNDLE)
    logical = Path(selected['plan']['root'])
    backing = Path(selected['backing_root'])
    require(logical.resolve() == backing, 'exact_existing_logical_backing_binding')
    strict_regular = helpers.regular

    def exact_alias(path):
        path = Path(path)
        if path == logical or logical in path.parents:
            expected = backing / path.relative_to(logical)
            require(logical.resolve() == backing and path.resolve() == expected, 'no_nested_alias_or_backing_substitution')
            return strict_regular(expected)
        return strict_regular(path)

    helpers.regular = exact_alias
    if physical == 6 or reload_context is not None:
        original_boundary, original_records = helpers.sleep_boundary, helpers.records

        def receipt_boundary(path):
            paths = original_records(path)
            if not paths or read(paths[-1])['kind'] != 'R184_LEARN_COMPLETE':
                return original_boundary(path)
            require(len(paths) >= 2, 'complete_receipt_requires_saved_predecessor')
            receipt, complete = read(paths[-1]), read(paths[-2])
            if complete['kind'] != 'SLEEP_COMPLETE':
                return None
            require(receipt['sha256'] == helpers.digest({key: value for key, value in receipt.items() if key != 'sha256'})
                and receipt['previous_sha256'] == complete['sha256']
                and receipt['journal_id'] == complete['journal_id']
                and receipt['index'] == complete['index'] + 1
                and receipt['document']['cycle'] == complete['document']['cycle']
                and receipt['document']['checkpoint'] == complete['document']['checkpoint'],
                'strict_same_checkpoint_receipt_tail')
            helpers.records = lambda unused: paths[:-1]
            try:
                saved = original_boundary(path)
            finally:
                helpers.records = original_records
            saved['trailing_receipt_sha256'] = receipt['sha256']
            return saved

        helpers.sleep_boundary = receipt_boundary
    guard_path = Path(selected['guard_path'])
    require(sha(guard_path) == selected['guard_sha256'], 'same_actual_original_guard')
    config, plan, original = helpers.originals(guard_path)
    require(plan['physical'] == physical and plan['gpu_uuid'] == selected['plan']['gpu_uuid']
        and plan['root'] == str(logical) and plan['source_root'] == selected['plan']['source_root']
        and plan['hard_end_unix'] == WALL, 'same_selected_life_source_device_wall')
    actor = helpers.identity(selected['native']['pid'])
    require(actor['start_ticks'] == selected['native']['start_ticks'], 'selected_native_start_ticks')
    timer = helpers.identity(actor['parent'])
    supervisor = helpers.identity(timer['parent'])
    pair = dict(actor=actor, timer=timer, supervisor=supervisor)
    expected = [str(PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(guard_path)]
    require(actor['argv'] == expected and timer['argv'][:3] == ['timeout','--signal=TERM','--kill-after=5s']
        and timer['argv'][4:] == expected and actor['group'] == timer['group'] == timer['pid'], 'exact_native_timeout_ancestry')
    require(supervisor['argv'][-3:] == ['contained-native','--config',str(guard_path)]
        and supervisor['argv'][:3] == [str(PYTHON),'-B','-m'], 'exact_contained_supervisor')
    launch = read(Path(config['attempt_dir']) / 'LAUNCH.json')
    require(launch['pid'] == timer['pid'] and str(launch['parent_start_ticks']) == timer['start_ticks']
        and launch['guard_sha256'] == sha(guard_path) and launch['plan_sha256'] == config['plan_sha256'], 'original_launch_binding')
    for process in pair.values():
        require(process['uid'] == 2524 and process['cwd'] == plan['source_root']
            and process['cgroup'] == actor['cgroup'] and process['boot_id'] == actor['boot_id']
            and process['environment'] == ['CUDA_VISIBLE_DEVICES='+plan['gpu_uuid']], 'same_owned_GPU_cgroup_source')
    require(actor['cgroup'] == '0::/system.slice/'+config['device_containment']['unit']+'.service', 'original_device_containment')
    selection = (Path(reload_context['selection']) if reload_context is not None
        else root / ('RELOAD_SELECTION.json' if physical == 6 else 'RETIRE_SELECTION.json'))
    if capture:
        write(selection, dict(physical=physical, processes=pair, logical_root=str(logical), backing_root=str(backing),
            guard_path=str(guard_path), guard_sha256=sha(guard_path), captured_unix=time.time(),
            reason='R203 useful-but-reallocated; no failure claim', no_signals=True))
    else:
        require(read(selection)['processes'] == pair, 'same_captured_exact_processes')
    existing.HOME, existing.OLD_ROOT, existing.OLD = root, logical, backing.parent
    existing.OLD_GUARD, existing.GPU = guard_path, plan['gpu_uuid']
    existing.RETIREMENT = (Path(reload_context['retirement']) if reload_context is not None
        else root / ('reload_r204_boundary' if physical == 6 else 'retirement'))
    return rollout, helpers, config, plan, original, pair, existing.neighbor_observations(helpers)


def run(physical):
    root = HOME if physical == 6 else HOME.parent / f'SCALE_physical{physical}'
    def ready():
        receiving = root / 'reload_r204' if physical == 6 else root
        receipt = read(receiving / 'RECEIVING_READY.json')
        require(receipt['status'] == 'CPU_TESTED_NOT_LIVE' and receipt['guard_sha256'] == sha(receiving / 'control/GUARD.json'), 'receiving_source_ready')
        parent = 'PARENT_QUIESCED_R204.json' if physical == 6 else 'PARENT_QUIESCED.json'
        require(read(root / parent)['no_future_old_parent_writes'], 'old_parent_quiesced')
    existing.HOME = root
    existing.prepare = lambda: prepare_binding(physical)
    existing.run(wait_seconds=5400, check_ready=ready)
    if physical == 6:
        import reload_math_c
        reload_math_c.launch()
    else:
        import r203_receive
        r203_receive.launch(physical)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('capture','retire_launch'))
    parser.add_argument('--physical', type=int, choices=(0,1,3,5,6), required=True)
    options = parser.parse_args()
    if options.action == 'capture':
        prepare_binding(options.physical, capture=True)
        print(json.dumps(dict(status='EXACT_NATIVE_SELECTION_CAPTURED_NO_SIGNALS',physical=options.physical)))
    else:
        run(options.physical)
