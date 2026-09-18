"""R202 same-life held-context handoff using the existing C2 containment."""

import argparse
from copy import deepcopy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import select
import shutil
import signal
import subprocess
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r202_C2_20260918_resume1')
OLD = Path('/localhome/local-rohing/orch_r153_r194_C2_20260917_console1')
STAGED = Path('/localhome/local-rohing/orch_r201_math_b_node5_20260918_attempt1')
LIFE = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
specification = importlib.util.spec_from_file_location('saved_primitives', ROOT / 'saved_primitives.py')
saved = importlib.util.module_from_spec(specification)
specification.loader.exec_module(saved)
require, read, sha, write = saved.require, saved.read, saved.sha, saved.write


def environment():
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(ROOT / 'source'), OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')


def identities():
    actor = saved.identity(3018395)
    require(actor['start_ticks'] == '23105951' and actor['cwd'] == str(OLD / 'source')
        and actor['argv'][-3:] == ['native', '--config', str(OLD / 'control/GUARD.json')], 'exact_current_C2_native')
    timer = saved.identity(actor['parent'])
    supervisor = saved.identity(timer['parent'])
    require(timer['pid'] == 3018394 and supervisor['pid'] == 3018393
        and supervisor['start_ticks'] == '23105934' and actor['group'] == timer['pid']
        and actor['cgroup'] == supervisor['cgroup'], 'exact_native_timeout_supervisor')
    outer, bridge = saved.identity(3018332), saved.identity(3018251)
    require(outer['start_ticks'] == '23105789' and bridge['start_ticks'] == '23105688', 'exact_outer_and_bridge')
    return dict(actor=actor, timer=timer, supervisor=supervisor, outer=outer, bridge=bridge)


def metadata(path):
    with path.open('rb') as handle:
        handle.seek(max(0, path.stat().st_size - 4096))
        raw = handle.read()
    return json.loads(b'{' + raw[raw.rfind(b',"index":') + 1:])


def held_boundary():
    paths = sorted((LIFE / 'stream/records').glob('[0-9]' * 20 + '.json'))
    head = read(paths[-1])
    if head['kind'] != 'R194_TURN':
        return None
    require(head['document']['act_held'] and head['document']['learn_held'], 'actual_console_hold')
    context_path = paths[-2]
    context = read(context_path)
    require(context['kind'] == 'CONTEXT_COMMITTED' and context['sha256'] == head['previous_sha256'], 'current_committed_console')
    envelope = context['document']['state']
    state = envelope['state']
    require(state['pending'] is None and state['sleep_frontier'] == len(state['rows'])
        and envelope['sha256'] == saved.digest(state), 'saved_model_no_pending_generation_or_training')
    complete_path = next(path for path in reversed(paths) if metadata(path)['kind'] == 'SLEEP_COMPLETE')
    complete = read(complete_path)
    prior = complete['document']['resume_state']['state']
    require(prior['rows'] == state['rows'] and prior['model_state_sha256'] == state['model_state_sha256']
        and state['history']['events'][:len(prior['history']['events'])] == prior['history']['events'],
        'all_console_history_preserved_no_added_training')
    return dict(head=saved.reference(paths[-1]), head_record_sha256=head['sha256'], head_index=head['index'],
        context=saved.reference(context_path), context_index=context['index'], state=envelope,
        complete=saved.reference(complete_path), checkpoint=complete['document']['checkpoint'],
        cycle=complete['document']['cycle'], history_events=len(state['history']['events']))


def state_proof(boundary):
    sys.path.insert(0, str(ROOT / 'source'))
    from gpu import orch_r125_continual_native as native
    from organism_v6.orch_r125_continual_stream import ContinualStream, digest
    import random
    import torch
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_state_proof')
    restored = ContinualStream.restore(boundary['state'], expected_sha256=boundary['state']['sha256'])
    require(restored.checkpoint() == boundary['state'], 'full_CURRENT_context_exact_roundtrip')
    checkpoint = boundary['checkpoint']
    native.NativeChild.verify_checkpoint(checkpoint)
    require(digest(checkpoint['checkpoint_sha256']) == restored.model_state_sha256, 'current_context_saved_model_binding')
    payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'], 'exact_optimizer_steps')
    parameters = [torch.nn.Parameter(torch.zeros_like(payload['optimizer']['state'][index]['exp_avg']))
        for index in range(len(payload['parameter_names']))]
    optimizer = torch.optim.AdamW(parameters)
    optimizer.load_state_dict(payload['optimizer'])
    actual = optimizer.state_dict()
    require(actual['param_groups'] == payload['optimizer']['param_groups'], 'exact_AdamW_groups')
    for index, fields in payload['optimizer']['state'].items():
        for name, expected in fields.items():
            value = actual['state'][index][name]
            require(torch.equal(value, expected) if torch.is_tensor(expected) else value == expected,
                'exact_AdamW_tensor_and_step')
    random.setstate(payload['python_rng'])
    torch.set_rng_state(payload['cpu_rng'])
    require(random.getstate() == payload['python_rng'] and torch.equal(torch.get_rng_state(), payload['cpu_rng'])
        and len(payload['cuda_rng']) == 1 and payload['cuda_rng'][0].device.type == 'cpu'
        and not torch.cuda.is_initialized(), 'saved_Python_CPU_CUDA_RNG_preserved_no_GPU')
    return dict(status='PASS', optimizer_steps=checkpoint['optimizer_steps'], context_index=boundary['context_index'],
        context_sha256=boundary['state']['sha256'], history_events=boundary['history_events'],
        adapter_state_sha256=checkpoint['adapter_state_sha256'], cuda_initialized=False,
        optimizer_restored_exact=True, saved_checkpoint_RNG_restored_exact=True,
        live_console_sampling_RNG_not_separately_checkpointed=True, observed_unix=time.time())


def stage():
    require(Path(__file__).resolve().parent == ROOT and not (ROOT / 'source').exists(), 'new_owned_R202_control')
    main = read(STAGED / 'main_ready/READY.json')
    require(main['schema'] == 'R201_MAIN_TESTED_SOURCE_OVERLAY_V1' and main['status'] == 'CPU_TESTED_NOT_LIVE'
        and len(main['files']) == 33 and sha(STAGED / 'main_ready/runtime_overlay.tar.gz')
        == main['archive_sha256'] == '599f44f1a39bc0a312a180963feef8affc62748cec20721a79112bfc5a0540b1', 'frozen_Main_overlay')
    owners = identities()
    source = ROOT / 'source'
    shutil.copytree(STAGED / 'source', source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pytest_cache'))
    for path in (ROOT / 'test_wrappers').iterdir():
        shutil.copy2(path, source / 'gpu' / path.name)
    assembly = read(STAGED / 'ASSEMBLY.json')
    for name, expected in main['files'].items():
        if name == 'gpu/orch_r184_think_act_learn.py':
            expected = assembly['Main_adapter_only_delta']['driver_sha256']
        require(sha(source / name) == expected, 'exact_R201_source_plus_existing_CPU_adapter:' + name)
    original_guard = read(OLD / 'control/GUARD.json')
    original_plan = read(original_guard['plan_path'])
    plan = deepcopy(original_plan)
    plan.update(main['required_native_options'])
    plan['source_root'] = str(source)
    plan['startup_context']['path'] = str(source / 'context/R153_STARTUP.md')
    plan['think_act_learn'] = dict(main['required_driver_options'], trial_id='C2_R202_current_context_creative_resume',
        cpu_gate_root=original_plan['think_act_learn']['cpu_gate_root'],
        cpu_gate_sha256=original_plan['think_act_learn']['cpu_gate_sha256'],
        environment_facts=original_plan['think_act_learn']['environment_facts'])
    require(plan['root'] == str(LIFE) and plan['physical'] == 1 and plan['new_presentations'] == 16
        and plan['rehearsal_presentations'] == 0 and plan['anchor_lambda'] == 0.25
        and plan['hard_end_unix'] == 1789776000, 'same_C2_root_recipe_and_wall')
    control = ROOT / 'control'
    control.mkdir()
    write(control / 'PLAN.json', plan)
    tests = [str(source / name) for name in main['files'] if name.startswith('tests/')]
    test_environment = dict(environment(), PYTHONPATH=os.pathsep.join(map(str,
        (STAGED / 'cpu_test_deps', source, source / 'tests'))), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    with (ROOT / 'CPU.log').open('x') as log:
        result = subprocess.run([PYTHON, '-B', '-m', 'pytest', '-q', '-o',
            'cache_dir=' + str(ROOT / 'pytest_cache'), *tests], cwd=source,
            env=test_environment, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    text = (ROOT / 'CPU.log').read_text()
    require(result.returncode == 0 and ' skipped' not in text, 'actual_R202_receiving_CPU_tests')
    counts = re.findall(r'(\d+) passed', text)
    require(counts, 'actual_test_count')
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_guard as guard
    from gpu.orch_r125_cpu_experiment import digest, verify_gate
    require(digest(verify_gate(plan['think_act_learn']['cpu_gate_root']))
        == plan['think_act_learn']['cpu_gate_sha256'], 'actual_same_boot_math_gate')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    cpu = dict(passed=True, source_pins=pins, tests_run=int(counts[-1]), log_sha256=sha(ROOT / 'CPU.log'),
        Main_ready_sha256=sha(STAGED / 'main_ready/READY.json'), observed_unix=time.time())
    write(control / 'RECEIVING_CPU.json', cpu)
    allocation = dict(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        physical=1, gpu_uuid=plan['gpu_uuid'], builder_entry_logged=True, declared_unix=time.time(),
        cpu_receipt_path=str(control / 'RECEIVING_CPU.json'), cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'),
        authority='Rohin202 explicit original-C2 release/current-context reload; Main frozen tested runtime')
    write(control / 'ALLOCATION.json', allocation)
    config = deepcopy(original_guard)
    config.update(plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'), source_pins=pins,
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'),
        attempt_dir=str(control), copy_raw=str(LIFE), resume=True)
    write(control / 'GUARD.json', config)
    guard.validate(control / 'GUARD.json')
    bridge = dict(raw_root=str(LIFE), journal_id=read(LIFE / 'stream/JOURNAL.json')['journal_id'],
        socket='/tmp/r202_node5_c2_resume1.sock', cpu_source=str(source), native_source=str(source),
        gate_root=plan['think_act_learn']['cpu_gate_root'], gate_sha256=plan['think_act_learn']['cpu_gate_sha256'],
        code_policy=plan['think_act_learn']['code_policy'], guard_path=str(control / 'GUARD.json'),
        guard_sha256=sha(control / 'GUARD.json'), stop_unix=plan['hard_end_unix'])
    write(ROOT / 'BRIDGE.json', bridge)
    boundary = held_boundary()
    require(boundary is not None, 'currently_idle_committed_console_boundary')
    write(ROOT / 'STAGE_STATE_CPU.json', state_proof(boundary))
    write(ROOT / 'READY.json', dict(status='RECEIVING_READY_CURRENT_CONTEXT_NOT_RELEASED', owners=owners,
        guard=saved.reference(control / 'GUARD.json'), cpu=saved.reference(control / 'RECEIVING_CPU.json'),
        main_ready=saved.reference(STAGED / 'main_ready/READY.json'), source_pins=pins,
        source_files=saved.files(source), boundary_context_index=boundary['context_index'],
        hold_release='Explicit operator-authorized R194 runtime RUN event, never a Rohin inbox message',
        prepared_unix=time.time()))
    print(json.dumps(dict(status='R202_RECEIVING_READY_NOT_RELEASED', tests=cpu['tests_run'],
        current_context=boundary['context_index'], current_root=str(LIFE), new_plan=str(control / 'PLAN.json'))))


def execute():
    ready = read(ROOT / 'READY.json')
    owners = identities()
    require(owners == ready['owners'] and saved.files(ROOT / 'source') == ready['source_files'], 'unchanged_ready_inputs')
    sys.path.insert(0, str(ROOT / 'source'))
    from gpu import orch_r125_continual_guard as guard
    guard.validate(ROOT / 'control/GUARD.json')
    descriptor = os.open('/localhome/local-rohing/orch_r157_C2_HANDOFF.lock', os.O_RDWR | os.O_NOFOLLOW)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    handles = {}
    try:
        (ROOT / 'EXECUTE_ONCE').mkdir()
        for role, identity in owners.items():
            saved.same(identity)
            handles[role] = os.pidfd_open(identity['pid'])
            saved.same(identity)
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            boundary = held_boundary()
            if boundary is None:
                time.sleep(.2)
                continue
            with saved.pause_watchdog(handles['actor'], 480):
                saved.pause_exact(owners['actor'], handles['actor'])
                if held_boundary() != boundary:
                    continue
                saved.check_children({role: owners[role] for role in ('actor', 'timer', 'supervisor')})
                require(not saved.live_children(owners['bridge']['pid']), 'idle_original_tool_bridge')
                proof = state_proof(boundary)
                write(ROOT / 'ACTUAL_STATE_CPU.json', proof)
                write(ROOT / 'CURRENT_BOUNDARY.json', boundary)
                checkpoint = Path(boundary['checkpoint']['adapter_path']).parent
                shutil.copytree(checkpoint, ROOT / 'preserved_checkpoint')
                stream = ROOT / 'preserved_stream'
                stream.mkdir()
                shutil.copy2(LIFE / 'stream/JOURNAL.json', stream / 'JOURNAL.json')
                shutil.copytree(LIFE / 'stream/records', stream / 'records')
                shutil.copytree(LIFE / 'stream/inbox', stream / 'inbox')
                saved.verify_snapshot(stream, LIFE, dict(reference=boundary['head']))
                inbox = saved.files(LIFE / 'stream/inbox')
                require(held_boundary() == boundary and saved.files(checkpoint) == saved.files(ROOT / 'preserved_checkpoint'),
                    'complete_exact_preservation_before_stop')
                write(ROOT / 'PRESERVED.json', dict(observed_unix=time.time(), context_index=boundary['context_index'],
                    context_sha256=boundary['state']['sha256'], head=boundary['head'], checkpoint=saved.files(checkpoint),
                    inbox=inbox, history_events=boundary['history_events'], cycle=boundary['cycle'],
                    old_root_kept=True, no_history_rollback=True, no_rows_rewritten=True))
                write(ROOT / 'TERMINATION_INTENT.json', dict(owners=owners, observed_unix=time.time(),
                    authorization='ROHIN202_EXPLICIT_CURRENT_CONTEXT_RELEASE', preserved=saved.reference(ROOT / 'PRESERVED.json')))
                signal.pidfd_send_signal(handles['actor'], signal.SIGTERM)
                signal.pidfd_send_signal(handles['actor'], signal.SIGCONT)
                for role in ('actor', 'timer', 'supervisor', 'outer'):
                    require(bool(select.select([handles[role]], [], [], 30)[0]), 'owned_exit:' + role)
                require(held_boundary() == boundary and all(sha(LIFE / 'stream/inbox' / name) == expected
                    for name, expected in inbox.items()), 'no_context_or_human_inbox_rollback')
                write(ROOT / 'OLD_NATIVE_RETIRED.json', dict(observed_unix=time.time(), owners=owners,
                    current_context_index=boundary['context_index'], same_root=str(LIFE), reset=False))
            from gpu.orch_r125_stream_journal import StreamJournal
            from gpu.orch_r194_console_reflection import ConsoleReflection
            from organism_v6.orch_r125_continual_stream import ContinualStream
            old_plan = read(OLD / 'control/PLAN.json')
            with StreamJournal(LIFE / 'stream') as journal:
                context = journal.latest_checkpoint()['document']
                require(context == boundary['state'], 'release_at_exact_CURRENT_context')
                current = ContinualStream.restore(context, expected_sha256=context['sha256'])
                release = journal.record('R202_OPERATOR_RELEASE', dict(authority='ROHIN202_EXPLICIT_OPERATOR_AUTHORIZATION',
                    source='operator', attributed_as_Rohin_inbox=False, observed_unix=time.time(),
                    preserved_context=boundary['context'], new_plan=saved.reference(ROOT / 'control/PLAN.json')))
                ConsoleReflection(None, current, journal, old_plan['think_act_learn']['console_reflection'])._control('RUN')
                require(current.checkpoint()['state']['history']['events'][:-1] == context['state']['history']['events'],
                    'all_prior_console_events_preserved_in_order')
                write(ROOT / 'RELEASED.json', dict(observed_unix=time.time(), release=release, act_held=False,
                    learn_held=False, Rohin_inbox_messages_created=0, prior_context=boundary['context'],
                    released_context_sha256=current.checkpoint()['sha256'], source='operator_authorized_runtime_mode_change'))
            saved.same(owners['bridge'])
            signal.pidfd_send_signal(handles['bridge'], signal.SIGTERM)
            require(bool(select.select([handles['bridge']], [], [], 15)[0]), 'old_idle_bridge_exited')
            processes = {}
            for name, command in (
                ('bridge', [PYTHON, '-B', str(ROOT / 'math_bridge.py'), '--config', str(ROOT / 'BRIDGE.json')]),
                ('supervisor', [PYTHON, '-B', '-m', 'gpu.r188_node5_confinement', 'dispatch', '--config', str(ROOT / 'control/GUARD.json')]),
            ):
                with (ROOT / (name + '.log')).open('x') as log:
                    process = subprocess.Popen(command, cwd=ROOT / 'source', env=environment(), stdin=subprocess.DEVNULL,
                        stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                processes[name] = saved.identity(process.pid)
                if name == 'bridge':
                    bridge_deadline = time.monotonic() + 30
                    while not list((ROOT / 'bridge_receipts').glob('READY*')):
                        require(process.poll() is None and time.monotonic() < bridge_deadline, 'new_bridge_READY')
                        time.sleep(.1)
            write(ROOT / 'STARTED.json', dict(observed_unix=time.time(), processes=processes,
                same_root=str(LIFE), prior_context_index=boundary['context_index'], loaded=False))
            print(json.dumps(dict(status='R202_RELEASED_WRAPPERS_STARTED_NOT_YET_LOADED',
                released=read(ROOT / 'RELEASED.json'), processes=processes)))
            break
        else:
            raise TimeoutError('no_idle_CURRENT_console_boundary_original_left_running')
    except BaseException as error:
        write(ROOT / ('FAILURE_' + str(time.time_ns()) + '.json'), dict(error_type=type(error).__name__,
            reason=str(error), observed_unix=time.time(), retired=(ROOT / 'OLD_NATIVE_RETIRED.json').exists(),
            released=(ROOT / 'RELEASED.json').exists(), no_implicit_retry=True))
        raise
    finally:
        for handle in handles.values():
            os.close(handle)
        os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('stage', 'execute'))
    globals()[parser.parse_args().action]()
