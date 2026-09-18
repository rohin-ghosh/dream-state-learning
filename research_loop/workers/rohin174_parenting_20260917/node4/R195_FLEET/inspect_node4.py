"""Read node4 learner metadata; no writes, signals, model calls or readouts."""

import importlib.util
import json
import os
from pathlib import Path
import time


BASE = Path('/localhome/local-rohing')
HELPERS = BASE / 'orch_r179_node4_r181journal_20260917t2220z/r144_helpers.py'
LEASE = BASE / 'orch_r132_kernel_child_20260916_attempt1/control1/LEASE_BUDGET.json'
LIVES = {
    'orch_r132_kernel_child_20260916_attempt1': 'kernel0',
    'orch_r136_raw_unparented_a40r1_20260916_attempt1': 'raw_unparented',
    'orch_r136_raw_parented_seed1_a40r3_20260916_attempt1': 'raw_parented',
    'orch_r136_kernel_parented_a40r4_20260916_attempt1': 'kernel_parented',
    'orch_r133_brain_free_20260916_attempt1': 'brain_free',
    'orch_r133_node3_brain_guided_20260916_attempt1': 'brain_guided',
    'orch_r133_support_free_20260916_attempt1': 'support_free',
}
SOURCE_FILES = (
    'gpu/orch_r125_continual_native.py', 'gpu/orch_r125_stream_journal.py',
    'organism_v6/orch_r125_continual_stream.py', 'gpu/orch_r184_think_act_learn.py',
    'gpu/orch_r193_continuity.py', 'organism_v6/orch_r194_code_target_filter.py',
    'gpu/orch_r153_code_blocks.py', 'gpu/orch_r132_kernel_bridge.py',
    'gpu/orch_r125_cpu_experiment.py', 'gpu/orch_r125_cpu_confinement_probe.py',
    'gpu/orch_r153_community_transport.py', 'gpu/orch_r161_native_executor.py',
)
PLAN_FIELDS = (
    'physical', 'gpu_uuid', 'root', 'source_root', 'hard_end_unix', 'lease_end_unix',
    'rehearsal_presentations', 'new_presentations', 'new_row_presentations',
    'think_act_learn', 'code_target_filter', 'code_policy', 'readout_every',
    'readout_every_sleeps', 'max_sleep_updates', 'wall_seconds',
)


def process_metadata(process):
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    return dict(pid=int(process.name), start_ticks=fields[19], parent=int(fields[1]),
                state=fields[0], cwd=str((process / 'cwd').resolve()),
                cgroup=(process / 'cgroup').read_text().strip())


def record_metadata(record):
    document = record['document']
    keys = ('pid', 'cycle', 'optimizer_steps', 'loaded_unix', 'stage', 'trial_id',
            'started_unix', 'finished_unix', 'new_rows', 'selected_old_rows',
            'new_presentations', 'policy', 'status')
    return dict(index=record['index'], kind=record['kind'], sha256=record['sha256'],
                metadata={key: document[key] for key in keys if key in document})


def native_leaves(candidates):
    timer_pids = {metadata['parent'] for _, _, metadata in candidates}
    return [candidate for candidate in candidates if candidate[2]['pid'] not in timer_pids]


def inspect_life(process, argv, helpers):
    guard_path = Path(argv[argv.index('--config') + 1])
    guard = helpers.read(guard_path)
    plan = helpers.read(guard['plan_path'])
    root = Path(plan['root'])
    if root.parent.name not in LIVES:
        return None
    helpers.require(helpers.sha(guard['plan_path']) == guard['plan_sha256'], 'plan_binding')
    source = Path(plan['source_root'])
    row = dict(life=LIVES[root.parent.name], native=process_metadata(process),
               guard_path=str(guard_path), guard_sha256=helpers.sha(guard_path),
               plan={key: plan[key] for key in PLAN_FIELDS if key in plan},
               backing_root=str(root.resolve()),
               containment=guard.get('device_containment'),
               guard_keys=sorted(guard), source_files={})
    for relative in SOURCE_FILES:
        path = source / relative
        row['source_files'][relative] = dict(present=path.is_file())
        if path.is_file():
            text = path.read_text()
            row['source_files'][relative].update(sha256=helpers.sha(path),
                mentions_code_policy='code_policy' in text,
                mentions_nfkc='NFKC' in text,
                mentions_r193='orch_r193_continuity' in text)
    backing_root = root.resolve(strict=True)
    paths = helpers.records(backing_root)
    row['head_index'] = int(paths[-1].stem)
    row['scan_from_index'] = int(paths[max(0, len(paths) - 320)].stem)
    latest = {}
    for path in reversed(paths[-320:]):
        record = helpers.read(path)
        kind = record['kind']
        if kind not in ('SLEEP_COMPLETE', 'SLEEP_RECIPE', 'LOADED', 'R184_STAGE') or kind in latest:
            continue
        latest[kind] = record_metadata(record)
        if kind == 'SLEEP_COMPLETE':
            envelope = record['document']['resume_state']
            state = envelope['state']
            latest[kind]['saved'] = dict(state_sha256=envelope['sha256'],
                state_digest_valid=helpers.digest(state) == envelope['sha256'],
                no_pending=state['pending'] is None, rows=len(state['rows']),
                sleep_frontier=state['sleep_frontier'], deadline_unix=state['deadline_unix'],
                state_keys=sorted(state))
    row['latest_metadata_in_bounded_window'] = latest
    boundary = helpers.sleep_boundary(backing_root)
    row['at_exact_saved_boundary_now'] = boundary is not None
    if boundary is not None:
        row['boundary_cycle_now'] = boundary['cycle']
    return row


def main():
    specification = importlib.util.spec_from_file_location('existing_r181_helpers', HELPERS)
    helpers = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(helpers)
    helpers.current_node('a40r')
    lease = helpers.read(LEASE)
    result = dict(observed_unix=time.time(), helpers_path=str(HELPERS),
        helpers_sha256=helpers.sha(HELPERS), mutation_count=0,
        lease={key: lease[key] for key in ('hard_end_unix', 'lease_end_unix',
            'safety_margin_seconds') if key in lease}, learners=[], bridges=[], errors=[])
    native_candidates = []
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            argv = (process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
            module = (argv[argv.index('-m') + 1] if '-m' in argv
                else next((Path(argument).name for argument in argv[1:]
                    if argument.endswith('.py')), ''))
            if module == 'gpu.orch_r125_continual_guard' and 'native' in argv and '--config' in argv:
                native_candidates.append((process, argv, process_metadata(process)))
            elif any(word in module for word in ('bridge', 'service')):
                row = dict(module=module, process=process_metadata(process))
                row['selected_options'] = {key: argv[argv.index(key) + 1]
                    for key in ('--root', '--config', '--code-policy', '--runtime-root')
                    if key in argv and argv.index(key) + 1 < len(argv)}
                result['bridges'].append(row)
        except (FileNotFoundError, ProcessLookupError):
            continue
        except Exception as error:
            result['errors'].append(dict(pid=int(process.name), error_type=type(error).__name__,
                message=str(error)))
    for process, argv, metadata in native_leaves(native_candidates):
        try:
            row = inspect_life(process, argv, helpers)
            if row is not None:
                result['learners'].append(row)
        except Exception as error:
            result['errors'].append(dict(pid=int(process.name), error_type=type(error).__name__,
                message=str(error)))
    result['learners'].sort(key=lambda row: row['plan']['physical'])
    result['missing_lives'] = sorted(set(LIVES.values()) - {row['life'] for row in result['learners']})
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
