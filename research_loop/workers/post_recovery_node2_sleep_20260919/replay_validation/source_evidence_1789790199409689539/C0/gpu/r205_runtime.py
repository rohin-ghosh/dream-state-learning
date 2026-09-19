"""Scoped R205 entrypoint: unchanged R204 learner, explicit frozen-C2 control."""

import argparse
from copy import deepcopy
from dataclasses import replace
import errno
import hashlib
import inspect
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
from types import FunctionType

from gpu import orch_r125_continual_native as native
from gpu import orch_r125_stream_journal as journal_module
from organism_v6.orch_r125_continual_stream import ContinualStream, digest, require
from organism_v6.orch_r124_train_history import TrainEvent


MODULE = 'gpu.r205_runtime'
POLICY = 'R205_INHERITED_C2_NO_WEIGHT_UPDATES_V1'
DEVICES = {
    0: ('GPU-0ee6f753-c61e-e18a-8aea-acccd3042939', '0000:4f:00.0'),
    1: ('GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821', '0000:52:00.0'),
    2: ('GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1', '0000:56:00.0'),
    3: ('GPU-e1277146-04f2-c38f-d1ae-1a98132f907e', '0000:57:00.0'),
    4: ('GPU-f484c608-a2d4-0c26-dee1-a06cc5ae69e4', '0000:ce:00.0'),
    5: ('GPU-bc211959-642d-664b-3581-42a0dbe434e9', '0000:d1:00.0'),
    6: ('GPU-1a83d900-1e95-c7b4-9b12-8117399697f8', '0000:d5:00.0'),
    7: ('GPU-319224de-e668-1822-d80b-4b24d15968ae', '0000:d6:00.0'),
}
TRIALS = ('R205_PARENTED_NO_WEIGHT_UPDATES', 'R205_FRESH_MATH_FIRST_PRINCIPLES',
    'R205_PEER_MATH', 'R205_PEER_REPO', 'R205_P4', 'R205_P32', 'R205_LR03', 'R205_LR3',
    'R206_NODE3_CONVERSATIONAL', 'R213_MATH_A', 'R213_MATH_C',
    'R213_NEW_MATH_B', 'R213_NEW_SIEGE_SCOUT', 'R213_NEW_SIEGE_NEGOTIATOR',
    'R213_NEW_SIEGE_QUARTERMASTER', 'R213_NEW_SIEGE_CHALLENGER', 'R213_NEW_CONVERSATIONAL_ENVOY')
CONTEXT_SHA = '3c8c45a6bfef9bb7d5a36dd9ddaf1e0a2293c6a83c718cbe2bca8e0ed6d16b48'
MANIFEST_SHA = '29ca04c2c51671c7df922a4b05448586e74eec35da45b03009877baccbccce84'


def optimizer_digest(optimizer, torch):
    result = hashlib.sha256()

    def visit(value):
        if torch.is_tensor(value):
            tensor = value.detach().cpu().contiguous()
            result.update(str((str(tensor.dtype), tuple(tensor.shape))).encode())
            result.update(tensor.numpy().tobytes())
        elif isinstance(value, dict):
            result.update(b'dict')
            for key in sorted(value, key=repr):
                visit(key)
                visit(value[key])
        elif isinstance(value, (tuple, list)):
            result.update(type(value).__name__.encode())
            for item in value:
                visit(item)
        else:
            result.update(repr((type(value).__name__, value)).encode())

    visit(optimizer.state_dict())
    return result.hexdigest()


def validate_frozen(receipt, previous):
    require(receipt.get('control_policy') == POLICY, 'explicit_frozen_control_policy')
    require(receipt.get('optimizer_steps') == 0
        and receipt.get('total_optimizer_steps') == previous['optimizer_steps'] == 4908
        and receipt.get('cumulative_optimizer_steps') == 4908,
        'preserve_inherited_optimizer4908_zero_new_updates')
    require(receipt.get('weight_updates_enabled') is False
        and receipt.get('no_update_reason') == 'parented_no_weight_updates_control'
        and receipt.get('presentations') == []
        and receipt.get('child_token_exposures') == receipt.get('anchor_token_exposures') == 0
        and receipt.get('frozen_base_verified') is True, 'honest_zero_exposure_control')
    require(receipt['before_adapter_sha256'] == receipt['after_adapter_sha256']
        == previous['adapter_state_sha256'], 'inherited_adapter_never_changed')
    require(receipt['before_optimizer_state_sha256'] == receipt['after_optimizer_state_sha256']
        and len(receipt['before_optimizer_state_sha256']) == 64, 'optimizer_state_never_changed')
    if 'checkpoint' in receipt:
        checkpoint = receipt['checkpoint']
        require(checkpoint['optimizer_steps'] == 4908
            and checkpoint['adapter_state_sha256'] == previous['adapter_state_sha256']
            and checkpoint['experiment'] == previous['experiment']
            and checkpoint['checkpoint_sha256'] == receipt['checkpoint_sha256'],
            'actual_saved_frozen_checkpoint')


class FrozenChild(native.NativeChild):
    def __init__(self, plan, checkpoint=None):
        require(checkpoint is not None and checkpoint['optimizer_steps'] == 4908,
            'control_requires_inherited_fixed_C2_not_fresh_LoRA')
        super().__init__(plan, checkpoint)
        self.frozen_checkpoint = deepcopy(checkpoint)
        self.frozen_optimizer_digest = optimizer_digest(self.optimizer, self.torch)

        def reject_step(*args, **kwargs):
            raise ValueError('R205_control_optimizer_step_forbidden')

        self.optimizer.step = reject_step

    def sleep(self, new_rows, old_rows, anchors, record):
        require(new_rows and self.optimizer_steps == 4908, 'nonempty_control_boundary')
        require(not any(parameter.requires_grad for parameter in self.engine.model.parameters()),
            'all_control_weights_readonly')
        self.engine.verify_base()
        adapter = self.adapter_hash()
        optimizer = optimizer_digest(self.optimizer, self.torch)
        require(optimizer == self.frozen_optimizer_digest, 'actual_inherited_optimizer_unchanged')
        receipt = dict(control_policy=POLICY, optimizer_steps=0, total_optimizer_steps=4908,
            cumulative_optimizer_steps=4908, weight_updates_enabled=False,
            no_update_reason='parented_no_weight_updates_control', presentations=[],
            child_token_exposures=0, anchor_token_exposures=0, frozen_base_verified=True,
            before_adapter_sha256=adapter, after_adapter_sha256=self.adapter_hash(),
            before_optimizer_state_sha256=optimizer,
            after_optimizer_state_sha256=optimizer_digest(self.optimizer, self.torch))
        validate_frozen(receipt, self.frozen_checkpoint)
        return receipt


class FrozenStream(ContinualStream):
    def commit_sleep(self, receipt, record):
        require(self.pending is None and self.sleep_frontier < len(self.rows), 'clean_control_frontier')
        previous = self.sleep_receipts[-1]['checkpoint']
        validate_frozen(receipt, previous)
        require(receipt['status'] == 'COMPLETE' and receipt['new_row_sha256'] ==
            [row['source_sha256'] for row in self.pending_rows()], 'exact_control_new_rows')
        self.sleep_frontier = len(self.rows)
        self.sleep_receipts.append(deepcopy(receipt))
        self.model_state_sha256 = digest(receipt['checkpoint_sha256'])
        try:
            record('SLEEP_COMPLETE', dict(deepcopy(receipt), resume_state=self.checkpoint()))
        except BaseException:
            self.pending = 'sleep:' + digest(receipt)
            raise
        return self.checkpoint()


class ControlJournal(journal_module.StreamJournal):
    def _advance(self, state, kind, document):
        if kind == 'R205_FIXED_C2_FORK':
            require(state['latest'] is None and state['index'] == 0, 'single_new_clone_genesis')
            require(native.sha(document['manifest_path']) == MANIFEST_SHA, 'fixed_C2_manifest')
            source = native.read(document['source_context_path'])
            require(source['sha256'] == CONTEXT_SHA
                and digest({key: value for key, value in source.items() if key != 'sha256'}) == CONTEXT_SHA,
                'exact_C2_console5846_record')
            expected = deepcopy(source['document']['state'])
            expected['state']['deadline_unix'] = document['hard_end_unix']
            expected['sha256'] = digest(expected['state'])
            require(expected == document['state'], 'only_new_clone_deadline_delta')
            require(expected['state']['pending'] is None
                and expected['state']['sleep_frontier'] == len(expected['state']['rows']) == 153
                and len(expected['state']['sleep_receipts']) == 51, 'complete51_context5846_no_pending')
            require(expected['state']['sleep_receipts'][-1]['checkpoint']['optimizer_steps'] == 4908,
                'source_optimizer4908')
            state['latest'] = self._checkpoint(document['state'])
            return
        if kind == 'SLEEP_COMPLETE' and document.get('control_policy') == POLICY:
            require(state['latest'] is not None and state['sleep_request'] is not None
                and state['request'] is None and state['response'] is None,
                'control_requires_actual_sleep_request')
            previous = state['latest']['document']['state']
            checkpoint = self._checkpoint(document['resume_state'])
            current = checkpoint['document']['state']
            self._unchanged(previous, current, {'pending', 'sleep_frontier', 'sleep_receipts', 'model_state_sha256'})
            receipt = {key: value for key, value in document.items() if key != 'resume_state'}
            validate_frozen(receipt, previous['sleep_receipts'][-1]['checkpoint'])
            rows = previous['rows'][previous['sleep_frontier']:]
            require(rows and current['pending'] is None
                and current['sleep_frontier'] == len(current['rows'])
                and current['sleep_receipts'] == previous['sleep_receipts'] + [receipt]
                and receipt['new_row_sha256'] == [row['source_sha256'] for row in rows]
                and receipt['status'] == 'COMPLETE'
                and receipt['cycle'] == state['sleep_request']['cycle']
                and current['model_state_sha256'] == digest(receipt['checkpoint_sha256']),
                'source_bound_zero_update_control_commit')
            state['latest'], state['sleep_request'] = checkpoint, None
            return
        return super()._advance(state, kind, document)


def compact_birth(stream, journal):
    before = stream.checkpoint()
    candidates = [operation for operation in stream.history.operations if operation['kind'] == 'compaction']
    if candidates:
        summary = TrainEvent.restore(candidates[-1]['summary'])
    else:
        children = [event for event in stream.history.events if event.actor == 'child' and event.text.strip()]
        summary = children[-1] if children else None
    if summary is None:
        journal.record('R205_BIRTH_CONTEXT', dict(action='FRESH_EMPTY_NO_INHERITED_CONTEXT_TO_COMPACT',
            state_sha256=before['sha256'], new_training_rows=0))
        return
    summary = replace(summary, event_id='r205:birth-carry:' + before['sha256'], phase='compaction')
    stream.history.compact(summary, through=stream.history.frontier(len(stream.history.events)))
    require(stream.rows == before['state']['rows'], 'birth_compaction_never_changes_raw_targets')
    journal.record('COMPACTION', dict(kind='R205_BIRTH_PRIOR_CHILD_CARRY',
        source_sha256=summary.source_sha256, new_child_distillation=False, raw_history_preserved=True,
        state=stream.checkpoint()))


def no_executor(driver, origin):
    require(driver.config['trial_id'] in TRIALS,
        'only_assigned_R205_arms')
    return dict(status='PROSE_REASONING_NO_EXECUTOR_CONNECTED', executed=False, origin=origin,
        reason='This first-principles screen has no CPU/GPU code executor; outputs are unexecuted reasoning.')


def peer_capsule(sender, record):
    require(sender in ('peer_math', 'peer_repo') and record['kind'] == 'R184_LEARN_COMPLETE'
        and record['document']['cycle'] > 51, 'new_actual_peer_state_only')
    require(digest({key: value for key, value in record.items() if key != 'sha256'}) == record['sha256'],
        'peer_record_content_binding')
    lines = ['Peer state from ' + sender + ', after completed cycle ' + str(record['document']['cycle']) + '.',
        'This is a different-environment peer treatment, not parent guidance or your own verified result.',
        'The following carried assertions can include inherited entries; they are not all new discoveries.']
    for entry in record['document']['working_state']['entries']:
        lines.append(entry['kind'] + ': ' + entry['text'])
    lines.append('During THINK, predict what transfers to your task, then check a concrete case or inspect the supplied source. '
        'No code executor is connected: label a reasoning check honestly. Only your own restatement can become your training target.')
    text = '\n'.join(lines)
    require(len(text.encode()) <= 6000, 'bounded_peer_state_no_truncation_or_normalization')
    return text


def receive_peer(driver):
    from gpu.orch_r127_pilot_console import _inbox
    receiver = {'R205_PEER_MATH': 'peer_math', 'R205_PEER_REPO': 'peer_repo'}.get(driver.config['trial_id'])
    if receiver is None:
        return None
    root = Path(driver.child.plan['source_root']).parent
    sender = 'peer_repo' if receiver == 'peer_math' else 'peer_math'
    paths = sorted((root.parent / sender / 'peer_state').glob('*.json'))
    if not paths:
        return None
    path = paths[-1]
    require(not path.is_symlink() and path.stat().st_size <= 1024 * 1024, 'bounded_peer_record_file')
    record = native.read(path)
    text = peer_capsule(sender, record)
    seen = getattr(driver, '_r205_peer_seen', set())
    if record['sha256'] in seen:
        return None
    publication = _inbox(Path(driver.child.plan['root']), 'Tool', text,
        dict(path=str(path), sha256=native.sha(path)))
    seen.add(record['sha256'])
    driver._r205_peer_seen = seen
    return dict(sender=sender, receiver=receiver, source_record_sha256=record['sha256'],
        publication=publication, text=text, imported_training_rows=0)


def install_runtime(plan):
    from gpu import orch_r184_think_act_learn as driver
    require(plan['physical'] in DEVICES and plan['gpu_uuid'] == DEVICES[plan['physical']][0], 'only_R205_node3_slots')
    trial = plan['think_act_learn']['trial_id']
    if trial != 'R205_FRESH_MATH_FIRST_PRINCIPLES':
        journal_module.StreamJournal = ControlJournal
    if trial == 'R205_PARENTED_NO_WEIGHT_UPDATES':
        native.NativeChild = FrozenChild
        native.ContinualStream = FrozenStream
    driver.ThinkActLearn._cpu = no_executor
    original_loop = driver.run_loop
    original_stage = driver.ThinkActLearn.generate_stage

    def peer_stage(self, stage, **kwargs):
        publication = receive_peer(self) if stage == 'THINK' else None
        if publication is None:
            return original_stage(self, stage, **kwargs)
        record_original = self.journal.record
        rendered = []

        def record_peer(kind, document):
            if kind == 'REQUEST' and any(message.get('role') == 'user'
                    and message.get('content') == 'Tool: ' + publication['text'] for message in document['messages']):
                require(document['render_receipt']['all_history_tokens_masked'], 'peer_tokens_never_training_targets')
                rendered.append(dict(segment=document['segment'], request_sha256=digest(document),
                    all_history_tokens_masked=True))
            return record_original(kind, document)

        self.journal.record = record_peer
        try:
            result = original_stage(self, stage, **kwargs)
        finally:
            self.journal.record = record_original
        record_original('R205_PEER_THINK_INPUT', dict(publication, rendered_requests=rendered,
            actual_THINK_render_verified=bool(rendered), observed_unix=time.time()))
        return result

    def birth_loop(child, stream, journal, anchors, plan, root, plan_path, completed_sleeps):
        compact_birth(stream, journal)
        return original_loop(child, stream, journal, anchors, plan, root, plan_path, completed_sleeps)

    driver.run_loop = birth_loop
    driver.ThinkActLearn.generate_stage = peer_stage


def contained_command(config_path, mode):
    from gpu import r184_node2_confinement as template
    from gpu import orch_r125_continual_guard as guard
    config, plan = guard.validate(config_path)
    require(plan['physical'] in DEVICES and plan['gpu_uuid'] == DEVICES[plan['physical']][0], 'priority_slots_only')
    namespace = dict(template.command.__globals__, DEVICE=plan['gpu_uuid'], MODULE=MODULE)
    argv = FunctionType(template.command.__code__, namespace, argdefs=template.command.__defaults__)(config_path, mode)
    require(argv.count('--property=DeviceAllow=/dev/nvidia3 rw') == 1, 'exact_tested_device_seam')
    argv[argv.index('--property=DeviceAllow=/dev/nvidia3 rw')] = '--property=DeviceAllow=/dev/nvidia' + str(plan['physical']) + ' rw'
    require('--property=DevicePolicy=strict' in argv and '--property=NoNewPrivileges=yes' in argv,
        'strict_existing_confinement_retained')
    return argv


def verify_devices(config, plan, unit):
    require(plan['physical'] in DEVICES and plan['gpu_uuid'] == DEVICES[plan['physical']][0], 'bound_node3_GPU')
    require(os.getuid() == os.getgid() == 2524, 'nonroot_service')
    require(Path('/proc/self/cgroup').read_text().strip() == '0::/system.slice/' + unit + '.service', 'device_cgroup')
    status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    require(int(status['CapEff'].strip(), 16) == 0 and status['NoNewPrivs'].strip() == '1', 'no_capabilities')
    fields = dict(line.split(':', 1) for line in Path('/proc/driver/nvidia/gpus', DEVICES[plan['physical']][1],
        'information').read_text().splitlines() if ':' in line)
    require(fields['GPU UUID'].strip() == plan['gpu_uuid'] and int(fields['Device Minor']) == plan['physical'], 'kernel_device_identity')
    metadata = Path('/dev/nvidia' + str(plan['physical'])).lstat()
    require(stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev) == 195
        and os.minor(metadata.st_rdev) == plan['physical'], 'actual_character_device')
    for descriptor in Path('/proc/self/fd').iterdir():
        try:
            require(not os.readlink(descriptor).startswith('/dev/nvidia'), 'no_inherited_GPU_descriptor')
        except FileNotFoundError:
            pass
    denied = []
    for minor in range(8):
        try:
            descriptor = os.open('/dev/nvidia' + str(minor), os.O_RDWR | os.O_CLOEXEC)
        except OSError as error:
            require(minor != plan['physical'] and error.errno in (errno.EPERM, errno.EACCES), 'foreign_device_denied')
            denied.append(minor)
        else:
            os.close(descriptor)
            require(minor == plan['physical'], 'foreign_device_open_abort')
    for path in ('/dev/nvidiactl', '/dev/nvidia-uvm'):
        os.close(os.open(path, os.O_RDWR | os.O_CLOEXEC))
    require(len(denied) == 7 and os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'seven_foreign_devices_denied')
    return dict(observed_unix=time.time(), physical=plan['physical'], gpu_uuid=plan['gpu_uuid'],
        denied_foreign_minors=denied, unit=unit, pid=os.getpid(), model_calls=0)


def supervise_owned(config_path):
    from gpu import orch_r125_continual_guard as guard
    source = inspect.getsource(guard.supervise)
    require(source.count("'gpu.orch_r125_continual_guard'") == 2, 'two_exact_guard_entrypoint_literals')
    source = source.replace("'gpu.orch_r125_continual_guard'", repr(MODULE))
    namespace = dict(guard.supervise.__globals__)
    exec(compile(source, __file__ + ':owned_entrypoint', 'exec'), namespace)
    return namespace['supervise'](config_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('dispatch', 'probe', 'child', 'native', 'scan'))
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--unit')
    args = parser.parse_args()
    from gpu import orch_r125_continual_guard as guard
    config, plan = guard.validate(args.config)
    attempt = Path(config['attempt_dir'])
    if args.mode == 'scan':
        print(json.dumps(guard.scan(args.config)))
    elif args.mode == 'native':
        install_runtime(plan)
        guard.native_entry(args.config)
    elif args.mode == 'dispatch':
        require(not (attempt / 'OUTER_STARTED.json').exists(), 'one_dispatch_only')
        cpu = native.read(attempt / 'RECEIVING_CPU.json')
        require(cpu['passed'] and cpu['source_pins'] == config['source_pins'], 'receiving_CPU_exact_source')
        native.write_once(attempt / 'OUTER_STARTED.json', dict(pid=os.getpid(), started_unix=time.time()))
        try:
            subprocess.run(contained_command(args.config, 'probe'), check=True, timeout=100)
            scan = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                'PYTHONPATH=' + plan['source_root'], sys.executable, '-B', '-m', MODULE, 'scan', '--config', str(args.config)]
            report = json.loads(subprocess.check_output(scan, text=True, timeout=100))
            require(report['scanner_euid'] == 0 and report['clear'] and not report['blocking_reasons'], 'fresh_privileged_admission')
            native.write_once(attempt / 'PRE_SERVICE_ADMISSION.json', dict(report=report,
                verified_unix=time.time(), guard_sha256=native.sha(args.config)))
            status = subprocess.run(contained_command(args.config, 'child'), check=False).returncode
            native.write_once(attempt / 'OUTER_EXIT.json', dict(status=status, finished_unix=time.time()))
        except BaseException as error:
            native.write_once(attempt / 'OUTER_FAILED.json', dict(error=str(error), error_type=type(error).__name__, finished_unix=time.time()))
            raise
    else:
        native.write_once(attempt / ('CONFINEMENT_CPU.json' if args.mode == 'probe' else 'CONFINEMENT_CHILD.json'),
            verify_devices(config, plan, args.unit))
        if args.mode == 'child':
            supervise_owned(args.config)


if __name__ == '__main__':
    main()
