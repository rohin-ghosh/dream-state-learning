"""Original C2: tested interactive-console mode at one exact complete boundary."""

import argparse
import ast
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import time

import saved_primitives as saved


OLD = Path('/localhome/local-rohing/orch_r153_r193_C2_20260917_recovery1')
NEW = Path('/localhome/local-rohing/orch_r153_r194_C2_20260917_console1')
LIFE = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
MAIN_SHA = 'dd2f413ed8617b819400306dd966a636d0ed0b5cee6209096fab4601c41b9def'
SUFFIX_SHA = 'd5e69655fd30f3317d114bd4aab2025024fdfb1521664b536d54ad61069bf026'
SOCKET = '/tmp/r194_node5_c2_console1.sock'
PHASE = 'R194_C2_CONSOLE_REFLECTION_V1'
require, read, sha, write = saved.require, saved.read, saved.sha, saved.write


def replace_once(text, before, after):
    require(text.count(before) == 1, 'unique_actual_source_anchor:' + before[:70])
    return text.replace(before, after, 1)


def patch_native(original, canonical):
    require(hashlib.sha256(canonical.encode()).hexdigest() == MAIN_SHA, 'Main_exact_memory_payload')
    nodes = {node.name: node for node in ast.parse(canonical).body if isinstance(node, ast.FunctionDef)}
    lines = canonical.splitlines(keepends=True)
    functions = '\n\n'.join(''.join(lines[nodes[name].lineno - 1:nodes[name].end_lineno])
                            for name in ('sleep_loss_implementation', 'masked_causal_mean_loss', 'sleep_causal_loss'))
    changed = replace_once(original, '\n\ndef sha(path):',
        "\n\nMODEL_DEFAULT = 'MODEL_DEFAULT'\nMASKED_CAUSAL_CE_V1 = 'MASKED_CAUSAL_CE_V1'\n\n\n"
        + functions + '\n\ndef sha(path):')
    changed = replace_once(changed, 'def validate_plan(plan):\n',
        'def validate_plan(plan):\n    sleep_loss_implementation(plan)\n')
    changed = replace_once(changed, '    def sleep(self, new_rows, old_rows, anchors, record):\n',
        '    def sleep(self, new_rows, old_rows, anchors, record):\n'
        '        loss_implementation = sleep_loss_implementation(self.plan)\n')
    changed = replace_once(changed,
        '            available_old_rows=available_old_rows, selected_old_rows=len(old_rows), anchor_lambda=0.25))',
        '            available_old_rows=available_old_rows, selected_old_rows=len(old_rows), anchor_lambda=0.25,\n'
        '            **(dict(sleep_loss_impl=loss_implementation) if loss_implementation != MODEL_DEFAULT else {})))')
    changed = replace_once(changed,
        '                        loss = self.engine.model(input_ids=inputs, labels=labels,\n'
        '                            attention_mask=self.torch.ones_like(inputs), use_cache=False).loss',
        '                        loss = sleep_causal_loss(self.engine.model, inputs, labels,\n'
        '                            self.torch.ones_like(inputs), implementation=loss_implementation, sample=sample)')
    ast.parse(changed)
    return changed


def complete_boundary(root):
    paths = sorted((Path(root) / 'stream/records').glob('[0-9]' * 20 + '.json'))
    head = read(paths[-1])
    require(head['sha256'] == saved.digest({key: value for key, value in head.items() if key != 'sha256'}), 'head_hash')
    complete_path = paths[-1]
    if head['kind'] == 'R184_LEARN_COMPLETE':
        require(len(paths) >= 2, 'preceding_complete_required')
        complete_path = paths[-2]
        complete = read(complete_path)
        require(complete['kind'] == 'SLEEP_COMPLETE' and head['previous_sha256'] == complete['sha256']
                and head['document']['cycle'] == complete['document']['cycle']
                and head['document']['checkpoint'] == complete['document']['checkpoint'], 'exact_R184_postlearn_boundary')
    elif head['kind'] != 'SLEEP_COMPLETE':
        return None
    complete = read(complete_path)
    require(complete['sha256'] == saved.digest({key: value for key, value in complete.items() if key != 'sha256'}), 'complete_hash')
    document = complete['document']
    state = document['resume_state']['state']
    require(document['status'] == 'COMPLETE' and state['pending'] is None
            and state['sleep_frontier'] == len(state['rows'])
            and document['resume_state']['sha256'] == saved.digest(state), 'complete_history_no_unsaved_suffix')
    return dict(record=complete, reference=saved.reference(complete_path), state_sha256=saved.digest(state),
                cycle=document['cycle'], index=complete['index'], head=saved.reference(paths[-1]))


def identities():
    actor = saved.identity(2930123)
    require(actor['start_ticks'] == '22768040' and actor['cwd'] == str(OLD / 'source')
            and actor['argv'][-3:] == ['native', '--config', str(OLD / 'control/GUARD.json')], 'exact_original_C2_native')
    timer = saved.identity(actor['parent'])
    supervisor = saved.identity(timer['parent'])
    require(timer['argv'][0] == 'timeout' and actor['group'] == timer['pid']
            and supervisor['cwd'] == str(OLD / 'source') and actor['cgroup'] == supervisor['cgroup'], 'same_contained_native_tree')
    outer = saved.identity(2930061)
    bridge = saved.identity(2930020)
    require(outer['start_ticks'] == '22767888' and bridge['start_ticks'] == '22767768', 'original_outer_and_math_bridge')
    return dict(actor=actor, timer=timer, supervisor=supervisor), outer, bridge


def stage():
    require(Path(__file__).resolve().parent == NEW, 'owned_remote_phase')
    main_pass = read(NEW / 'MAIN_PASS.json')
    require(main_pass['status'] == 'PASS' and main_pass['scope'] == 'original_C2_R194_console', 'explicit_Main_test_PASS_before_stage')
    old_config = read(OLD / 'control/GUARD.json')
    old_plan = read(old_config['plan_path'])
    require(sha(NEW / 'main/gpu/orch_r125_continual_native.py') == MAIN_SHA, 'Main_memory_pin')
    require(sha(NEW / 'main/gpu/orch_r145_suffix_loss.py') == SUFFIX_SHA, 'unchanged_suffix_dependency')
    pair, outer, bridge = identities()
    source = NEW / 'source'
    shutil.copytree(OLD / 'source', source)
    actual_old = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    require(actual_old == old_config['source_pins'], 'actual_running_source_closure')
    native = source / 'gpu/orch_r125_continual_native.py'
    require(sha(native) == sha(NEW / 'ORIGINAL_NATIVE.py'), 'actual_native_snapshot')
    native.chmod(0o644)
    native.write_text(patch_native(native.read_text(), (NEW / 'main/gpu/orch_r125_continual_native.py').read_text()))
    for relative in ('gpu/orch_r145_suffix_loss.py', 'tests/test_orch_r125_masked_causal_loss.py',
                     'tests/test_orch_r125_masked_causal_loss_qwen_cpu.py'):
        target = source / relative
        if target.exists():
            if relative.startswith('gpu/'):
                require(sha(target) == SUFFIX_SHA, 'existing_suffix_dependency_unchanged')
            target.chmod(0o644)
        shutil.copyfile(NEW / 'main' / relative, target)
    closure = read(NEW / 'MAIN_CLOSURE.json')
    require(main_pass['source_closure'] == closure, 'Main_PASS_bound_closure')
    for relative, expected in closure.items():
        require(sha(NEW / 'main' / relative) == expected, 'pinned_Main_dataset_closure')
        target = source / relative
        if target.exists():
            target.chmod(0o644)
        shutil.copyfile(NEW / 'main' / relative, target)
    driver = source / 'gpu/orch_r184_think_act_learn.py'
    prior = (OLD / 'source/gpu/orch_r184_think_act_learn.py').read_text()
    current = driver.read_text()
    begin, end = current.index('    def _cpu(self, origin):'), current.index('    def act(self):')
    old_begin, old_end = prior.index('    def _cpu(self, origin):'), prior.index('    def act(self):')
    driver.write_text(current[:begin] + prior[old_begin:old_end] + current[end:])
    compile(driver.read_text(), str(driver), 'exec')
    environment = saved.environment(source)
    result = subprocess.run([str(saved.PYTHON), '-B', '-m', 'unittest',
        'tests.test_orch_r125_masked_causal_loss', 'tests.test_orch_r125_masked_causal_loss_qwen_cpu',
        'tests.test_orch_r184_think_act_learn', 'tests.test_orch_r194_console_reflection',
        'tests.test_orch_r125_stream_journal', 'tests.test_orch_r125_continual_stream', '-v'],
        cwd=source, env=environment, capture_output=True, text=True, timeout=180)
    (NEW / 'CPU.log').write_text(result.stdout + result.stderr)
    require(result.returncode == 0 and 'skipped=' not in result.stderr, 'actual_source_loss_and_installed_Qwen_CPU_tests')
    control = NEW / 'control'
    control.mkdir()
    plan = dict(old_plan, source_root=str(source), sleep_loss_impl='MASKED_CAUSAL_CE_V1')
    plan['think_act_learn'] = dict(old_plan['think_act_learn'], console_reflection=dict(
        schema='R194_CONSOLE_REFLECTION_V1', session_id='rohin194_C2_20260917'))
    plan['startup_context'] = dict(old_plan['startup_context'], path=str(source / 'context/R153_STARTUP.md'))
    require({key: value for key, value in plan['think_act_learn'].items() if key != 'console_reflection'} == old_plan['think_act_learn'] and plan['new_presentations'] == 16
            and plan['rehearsal_presentations'] == 0, 'no_other_experimental_factor')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    changes = {name: checksum for name, checksum in pins.items() if actual_old.get(name) != checksum}
    require(set(changes) <= set(closure) | {'gpu/orch_r125_continual_native.py', 'gpu/orch_r145_suffix_loss.py',
            'tests/test_orch_r125_masked_causal_loss.py', 'tests/test_orch_r125_masked_causal_loss_qwen_cpu.py'}, 'authorized_memory_dataset_closure_only')
    cpu = dict(passed=True, source_pins=pins, log_sha256=sha(NEW / 'CPU.log'), phase=PHASE,
               numerical_equivalence='within_tested_tolerance_not_bit_exact', whole_history_preserved=True)
    write(control / 'RECEIVING_CPU.json', cpu)
    write(control / 'PLAN.json', plan)
    allocation = dict(read(old_config['allocation_path']), plan_sha256=sha(control / 'PLAN.json'),
        cpu_tests_passed=True, declared_unix=time.time(), builder_entry_logged=True,
        builder_entry_pushed=True, builder_entry_pushed_semantics='LOCAL_POSTING_NOT_GIT_PUSH', phase=PHASE)
    write(control / 'ALLOCATION.json', allocation)
    config = dict(old_config, source_pins=pins, attempt_dir=str(control), plan_path=str(control / 'PLAN.json'),
        plan_sha256=sha(control / 'PLAN.json'), allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', config)
    old_bridge = read(OLD / 'BRIDGE.json')
    write(NEW / 'BRIDGE.json', dict(old_bridge, native_source=str(source), socket=SOCKET,
        guard_path=str(control / 'GUARD.json'), guard_sha256=sha(control / 'GUARD.json')))
    bridge_text = (NEW / 'bridge_template.py').read_text().replace('R193_C2_RECOVERY45_MATH_ENV', PHASE)
    bridge_text = replace_once(bridge_text, "'/tmp/r193_node5_c2_recovery1.sock'", repr(SOCKET))
    (NEW / 'math_bridge.py').write_text(bridge_text)
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_guard as guard
    from gpu import r188_node5_confinement as confinement
    guard.validate(control / 'GUARD.json')
    probe = NEW / 'preflight'
    probe.mkdir()
    write(probe / 'GUARD.json', dict(config, attempt_dir=str(probe)))
    subprocess.run(confinement.command(probe / 'GUARD.json', 'probe'), check=True, timeout=100)
    saved.freeze(source)
    write(NEW / 'READY.json', dict(phase=PHASE, pair=pair, outer=outer, bridge=bridge, source_changes=changes,
        source_pins=pins, guard=saved.reference(control / 'GUARD.json'), cpu=saved.reference(control / 'RECEIVING_CPU.json'),
        device=saved.reference(probe / 'CONFINEMENT_CPU.json'), wall=plan['hard_end_unix'], staged_unix=time.time()))
    print(json.dumps(dict(status='READY', ready=saved.reference(NEW / 'READY.json'), changes=changes)))


def execute():
    require(read(NEW / 'MAIN_PASS.json')['status'] == 'PASS', 'Main_test_PASS_required')
    ready = read(NEW / 'READY.json')
    pair, outer, bridge = identities()
    require(pair == ready['pair'] and outer == ready['outer'] and bridge == ready['bridge'], 'unchanged_staged_owners')
    old_config = read(OLD / 'control/GUARD.json')
    old_plan = read(old_config['plan_path'])
    control = NEW / 'control'
    lock = os.open('/localhome/local-rohing/orch_r157_C2_HANDOFF.lock', os.O_RDWR | os.O_NOFOLLOW)
    descriptors = {}
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (NEW / 'EXECUTE_ONCE').mkdir()
        for role, process in dict(pair, outer=outer, bridge=bridge).items():
            saved.same(process)
            descriptors[role] = os.pidfd_open(process['pid'])
            saved.same(process)
        write(NEW / 'ARMED.json', dict(phase=PHASE, pid=os.getpid(), time=time.time(), signals=0, wait_seconds=1200))
        deadline = min(time.monotonic() + 1200, time.monotonic() + old_plan['hard_end_unix'] - time.time() - 600)
        while time.monotonic() < deadline:
            saved.same(pair['actor'])
            boundary = complete_boundary(LIFE)
            metadata = saved.readout(LIFE, old_config, old_plan, boundary, pair['actor']) if boundary else None
            if metadata is None:
                time.sleep(.25)
                continue
            with saved.pause_watchdog(descriptors['actor'], 480) as pause_deadline:
                saved.pause_exact(pair['actor'], descriptors['actor'])
                if complete_boundary(LIFE) != boundary:
                    continue
                completion = saved.wait_readout(metadata, pause_deadline - 180)
                saved.check_children(pair)
                require(not saved.live_children(bridge['pid']), 'no_inflight_math_request_at_complete_boundary')
                write(NEW / 'BOUNDARY.json', boundary)
                proof = saved.boundary_cpu(control / 'PLAN.json', NEW / 'BOUNDARY.json')
                write(NEW / 'STATE_CPU.json', proof)
                checkpoint = LIFE / 'checkpoints' / ('sleep_%06d' % boundary['cycle'])
                inventory = saved.files(checkpoint)
                shutil.copytree(checkpoint, NEW / 'preserved_checkpoint')
                require(saved.files(NEW / 'preserved_checkpoint') == inventory, 'adapter_optimizer_RNG_preserved')
                inbox = {path.name: sha(path) for path in (LIFE / 'stream/inbox').glob('*.json')}
                require('311ae25be2484fccbcd8af839c4fa025.json' in inbox, 'queued_or_consumed_parent_preserved')
                write(NEW / 'READY_AT_BOUNDARY.json', dict(cycle=boundary['cycle'], state_sha256=boundary['state_sha256'],
                    boundary=saved.reference(NEW / 'BOUNDARY.json'), readout_completion=completion, checkpoint_files=inventory,
                    inbox=inbox, no_history_cut=True, no_discarded_updates=True, time=time.time()))
                require(complete_boundary(LIFE) == boundary and time.monotonic() + 100 < pause_deadline, 'same_boundary_before_retirement')
                for process in dict(pair, outer=outer, bridge=bridge).values():
                    saved.same(process)
                write(NEW / 'TERMINATION_INTENT.json', dict(pair=pair, phase=PHASE, time=time.time(), native_only=True))
                signal.pidfd_send_signal(descriptors['actor'], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors['actor'], signal.SIGCONT)
                for role in ('actor', 'timer', 'supervisor', 'outer'):
                    require(bool(select.select([descriptors[role]], [], [], 30)[0]), 'natural_old_exit:' + role)
                require(complete_boundary(LIFE) == boundary and saved.files(checkpoint) == inventory, 'no_unsaved_suffix_or_model_change')
                require(all(sha(LIFE / 'stream/inbox' / name) == checksum for name, checksum in inbox.items()), 'inbox_unchanged')
                write(NEW / 'RETIRED.json', dict(cycle=boundary['cycle'], optimizer_steps=proof['optimizer_steps'],
                    phase=PHASE, time=time.time(), no_reset=True, no_discarded_updates=True, same_root=str(LIFE)))
            require(not saved.live_children(bridge['pid']), 'old_math_bridge_idle')
            saved.same(bridge)
            write(NEW / 'OLD_BRIDGE_STOP_INTENT.json', dict(identity=bridge, time=time.time(), in_flight=False))
            signal.pidfd_send_signal(descriptors['bridge'], signal.SIGTERM)
            require(bool(select.select([descriptors['bridge']], [], [], 10)[0]), 'old_idle_bridge_exited')
            write(NEW / 'OLD_BRIDGE_EXITED.json', dict(time=time.time()))
            break
        else:
            raise TimeoutError('bounded_wait_expired_original_left_running')
        processes = {}
        for name, command, cwd in (
            ('bridge', [str(saved.PYTHON), '-B', str(NEW / 'math_bridge.py'), '--config', str(NEW / 'BRIDGE.json')], NEW),
            ('supervisor', [str(saved.PYTHON), '-B', '-m', 'gpu.r188_node5_confinement', 'dispatch', '--config', str(control / 'GUARD.json')], NEW / 'source')):
            with (NEW / (name + '.log')).open('x') as log:
                process = subprocess.Popen(command, cwd=cwd, env=saved.environment(NEW / 'source'),
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            processes[name] = saved.identity(process.pid)
            if name == 'bridge':
                ready_deadline = time.monotonic() + 30
                while not list((NEW / 'bridge_receipts').glob('READY*')):
                    require(process.poll() is None and time.monotonic() < ready_deadline, 'new_exact_math_bridge_ready')
                    time.sleep(.1)
        write(NEW / 'STARTED.json', dict(phase=PHASE, processes=processes, cycle=boundary['cycle'],
            optimizer_steps=proof['optimizer_steps'], time=time.time(), loaded=False))
    except BaseException as error:
        write(NEW / 'FAILED.json', dict(error_type=type(error).__name__, reason=str(error), time=time.time(),
            native_stop_intent=(NEW / 'TERMINATION_INTENT.json').exists(), retired=(NEW / 'RETIRED.json').exists(), no_retry=True))
        raise
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(lock)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('stage', 'execute'))
    arguments = parser.parse_args()
    stage() if arguments.action == 'stage' else execute()
