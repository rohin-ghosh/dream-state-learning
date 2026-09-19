"""Original-node CPU evidence only; no lock creation, publication or provider calls."""

from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from binding_candidate import BoundHelper, MEMBERS, TARGET, digest, provider_disposition, require


ROOT = Path('/localhome/local-rohing/orch_r205_node3_20260918')
PARENT = ROOT / 'r233_recovery_parents_v4'
CONTROL = ROOT / TARGET / 'control_ws6_pending_math_b_20260919T144429Z'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def process(pid):
    root = Path('/proc') / str(pid)
    if not root.exists():
        return None
    stat = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    arguments = (root / 'cmdline').read_bytes()
    return dict(pid=pid, start_ticks=stat[19], status=stat[0], uid=root.stat().st_uid,
        command_sha256=hashlib.sha256(arguments).hexdigest(), args=arguments.decode().rstrip('\0').split('\0'),
        cwd=str((root / 'cwd').resolve()))


def main():
    require(os.uname().nodename == 'ipp2-ovx-p6-09' and os.getuid() == 2524, 'original_node_owner')
    sys.path[:0] = [str(PARENT), str(ROOT / 'r231_parent_operator_v1'), str(ROOT)]
    classroom = importlib.import_module('classroom')
    helper = importlib.import_module('r230_curriculum')
    config_path = ROOT / 'r233_classroom_operator_v2/CONFIG_PRIVATE.json'
    config = json.loads(config_path.read_bytes())
    for relative, expected in config['helper_pins'].items():
        require(sha(ROOT / relative) == expected, 'original_helper_source_' + relative)
    require(tuple(classroom.MEMBERS) == MEMBERS, 'unchanged_original_classroom_members')
    old_bindings = {name: helper.bind(ROOT, name) for name in MEMBERS}
    guard_path = CONTROL / 'GUARD_BUILDER1450.json'
    require(sha(guard_path) == 'd51e90bfea4306030ece342db7fc3d9d03790679a1ef1b7517bdac26b7e90ba0', 'actual_admitted_guard')
    guard = json.loads(guard_path.read_bytes())
    plan_path = CONTROL / 'PLAN.json'
    plan = json.loads(plan_path.read_bytes())
    require(sha(plan_path) == guard['plan_sha256'] == '82704f31ed7cc3b816dc1feea1205423bedd0e0fd4d92c477dea9f95ce21b70d', 'unchanged_V3_plan')
    source = Path(plan['source_root'])
    require(digest(guard['source_pins']) == '7a5a7d7fe44b1053a90d1c7b18a5eabf3ed3d63409844e3f56071f84fcefb88a', 'published_V3_closure')
    for relative, expected in guard['source_pins'].items():
        require(sha(source / relative) == expected, 'unchanged_runtime_source_' + relative)
    loaded = json.loads((ROOT / TARGET / 'raw/stream/records/00000000000000009609.json').read_bytes())
    require(loaded['kind'] == 'LOADED' and loaded['sha256'] == '2917ea7daf9a16defadf3b065aa196fd8959a16259853b2c16dd7c887835dac7'
        and loaded['sha256'] == digest({key: value for key, value in loaded.items() if key != 'sha256'}), 'actual_LOADED')
    pid = loaded['document']['pid']
    binding = dict(old_bindings[TARGET], source=str(source), control=str(CONTROL),
        guard_path=str(guard_path), native_pid=pid, loaded=dict(index=9609, sha256=loaded['sha256']),
        deadline=plan['hard_end_unix'], writer_sha256=sha(source / 'gpu/orch_r127_pilot_console.py'),
        plan_learning_policy=plan.get('learn_row_policy'), think_learning_policy=plan['think_act_learn'].get('learn_row_policy'),
        resident_selectors={key: value for key, value in plan['think_act_learn'].items() if 'filter' in key})
    require(binding['writer_sha256'] == guard['source_pins']['gpu/orch_r127_pilot_console.py']
        == old_bindings[TARGET]['writer_sha256'], 'same_pinned_parent_writer')
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()

    def observe():
        compute_text = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid', '--format=csv,noheader'],
            check=True, capture_output=True, text=True, timeout=20).stdout
        compute = [(int(line.split(',')[0]), line.split(',')[1].strip()) for line in compute_text.splitlines() if line.strip()]
        natives = []
        for directory in Path('/proc').iterdir():
            if not directory.name.isdigit():
                continue
            try:
                if directory.stat().st_uid != os.getuid():
                    continue
                arguments = (directory / 'cmdline').read_bytes().decode(errors='replace').split('\0')
                if 'native' in arguments and '--config' in arguments:
                    native_guard = arguments[arguments.index('--config') + 1]
                    if str(ROOT) + '/' in native_guard and 'timeout' not in Path(arguments[0]).name:
                        natives.append((int(directory.name), native_guard))
            except FileNotFoundError:
                continue
        current = process(pid)
        require(current is not None and current['cwd'] == str(source)
            and current['args'] == ['/localhome/local-rohing/v2/venv/bin/python', '-B', '-m',
                'gpu.ws6_math_b_pending_entry', 'native', '--config', str(guard_path)], 'actual_native_command_and_cwd')
        observations = {}
        for name in MEMBERS:
            active_path = ROOT / name / 'ACTIVE_RUNTIME.json'
            active = json.loads(active_path.read_bytes())
            old_plan = json.loads((Path(active['control']) / 'PLAN.json').read_bytes())
            matches = [number for number, path in natives if path.startswith(str(ROOT / name) + '/')]
            compute_pids = [number for number, gpu in compute if gpu == old_plan['gpu_uuid']]
            if name == TARGET:
                observations[name] = dict(state='LOADED_ALIVE', pid=pid, start_ticks=current['start_ticks'], boot_id=boot,
                    uid=current['uid'], status=current['status'], command_sha256=current['command_sha256'], source=str(source),
                    guard_path=str(guard_path), guard_sha256=sha(guard_path), plan_sha256=sha(plan_path),
                    loaded_index=9609, loaded_sha256=loaded['sha256'], physical=2, gpu_uuid=plan['gpu_uuid'],
                    native_matches=matches, compute_pids=compute_pids)
            else:
                observations[name] = dict(state='EXPECTED_DOWN', native_matches=matches, compute_pids=compute_pids,
                    legacy_pid_exists=Path('/proc', str(old_bindings[name]['native_pid'])).exists(),
                    old_binding_sha256=digest(old_bindings[name]), active_sha256=sha(active_path))
        return observations

    initial = observe()
    proxy = BoundHelper(helper, ROOT, initial, old_bindings, binding, observe)
    with patch.object(classroom.importlib, 'import_module', return_value=proxy):
        try:
            classroom.load_helpers(ROOT, config)
        except ValueError as error:
            require(str(error) == 'all seven protected parented natives must be alive', 'original_default_guard_reason')
        else:
            raise ValueError('default_guard_must_not_accept_partial_cohort')
        unused, bindings = classroom.load_helpers(ROOT, config, recovering=True)
    live = [name for name, descriptor in bindings.items() if proxy.alive(descriptor)]
    require(live == [TARGET], 'original_recovering_guard_exact_MathB_only')
    output = ROOT / 'r233_classroom_handoff_v1/live'
    current = {name: classroom.inherited(helper, ROOT, ROOT / 'r230_curriculum_live_v1', name) for name in MEMBERS}
    restored = classroom.restore(helper, ROOT, output, current)
    rows, usage = {}, Counter()
    usage_complete = True
    reservations = []
    ledger_pins = {}
    adaptive = importlib.import_module('adaptive_parent')
    for name in MEMBERS:
        turns = sorted((output / name).glob('turn_*'))
        rows[name] = dict(turns=len(turns), published=0, authenticated_results=0, pending=[])
        for directory in turns:
            for path in sorted(directory.iterdir()):
                require(path.is_file() and not path.is_symlink(), 'known_regular_parent_ledger_member')
                ledger_pins[str(path.relative_to(output))] = sha(path)
            request = directory / 'PROVIDER_REQUEST.json'
            result = directory / 'PROVIDER_RESULT.json'
            published = directory / 'PUBLISHED.json'
            if published.exists():
                rows[name]['published'] += 1
            if result.exists():
                content = json.loads(result.read_bytes())
                adaptive.message(content, sha(request))
                rows[name]['authenticated_results'] += 1
                require(isinstance(content['usage'], dict), 'preserve_actual_usage')
                for key, value in content['usage'].items():
                    if type(value) in (int, float):
                        usage[key] += value
            elif request.exists():
                reservation = dict(life=name, directory=str(directory), request_sha256=sha(request),
                    dispatch_state='UNKNOWN_NOT_A_NEW_BUDGET', reserved=True, retry_allowed=False)
                rows[name]['pending'].append(reservation)
                reservations.append(reservation)
                usage_complete = False
    ledger_pins['STARTED.json'] = sha(output / 'STARTED.json')
    for name in MEMBERS:
        old = current[name]
        require(sha(Path(old['directory']) / 'PREPARED.json') == old['publication']['prepared_sha256']
            and sha(old['publication']['path']) == old['publication']['sha256'], 'preserved_last_published_turn')
    pending = output / TARGET / 'turn_0032/PROVIDER_REQUEST.json'
    require(sha(pending) == 'bfcfa905da08d97323ab95c3c4482ebd36559109bc1b4929aaf6a23b955b6d16', 'original_ambiguous_turn0032')
    require(not pending.with_name('PROVIDER_RESULT.json').exists() and restored[3][TARGET] == 32, 'pending_turn_not_reset_or_resolved')
    ledger = dict(cumulative_usage=dict(usage), cumulative_usage_complete=usage_complete,
        pending_request_sha256=sha(pending), pending_result_authenticated=False, next_turn=restored[3][TARGET],
        ledger_sha256=digest(ledger_pins), service_end_unix=plan['hard_end_unix'])
    old_publishers = {str(number): process(number) for number in (1973233, 1973234)}
    lock_path = ROOT / 'R230_CURRICULUM_WRITER.lock'
    with lock_path.open('rb') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock_free = False
        else:
            lock_free = True
            fcntl.flock(lock, fcntl.LOCK_UN)
    source_pins = {str(path): sha(path) for path in (Path(classroom.__file__), Path(helper.__file__),
        Path(adaptive.__file__), PARENT / 'model_parent.py', PARENT / 'service_horizon.py', config_path)}
    require(all(sha(output / relative) == expected for relative, expected in ledger_pins.items()), 'ledger_changed_during_CPU_read')
    proxy.check()
    print(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(), status='REAL_NODE_CPU_BINDING_AND_ORIGINAL_RECOVERING_GUARD_PASS_NO_LAUNCH',
        default_all_seven_guard_rejects_partial=True, recovering_original_guard_pass=True,
        original_classroom_source_unmodified=True, all_bound_names=list(bindings), actual_live_names=live,
        cohort=initial, target_binding=binding, source_pins=source_pins, original_config=config,
        current_parent_ledgers=rows, preserved_ledger_files=ledger_pins, restored_round=restored[0],
        restored_math_round=restored[1], restored_sequence=restored[3],
        pending_reserved=reservations, provider_disposition=provider_disposition(ledger),
        old_publishers=old_publishers, original_classroom_lock_available=lock_free,
        no_parent_launch=True, no_provider_request=True, no_native_signal=True,
        receiving_method='real_node_data_original_guard_with_CPU_only_binding_adapter_not_publication_admission'), sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
