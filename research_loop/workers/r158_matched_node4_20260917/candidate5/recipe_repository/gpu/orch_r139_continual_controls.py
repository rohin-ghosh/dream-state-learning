"""R134 frozen continual controls; operator-only launch, no learning or sleep."""

import argparse
from contextlib import contextmanager, nullcontext
from copy import deepcopy
import gc
import json
import os
from pathlib import Path
import random
import re
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

from gpu import orch_r125_continual_native as native
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, digest, require, valid_sha256


SCHEMA = 'R139_CONTINUAL_CONTROLS_V1'
MANIFEST_SCHEMA = 'R139_FROZEN_MODEL_V1'
GATE_SCHEMA = 'R139_CPU_PROVENANCE_GATE_V1'
MODES = ('frozen_rank8_no_sleep', 'frozen_base_no_adapter')
SOURCE_FILES = (
    'gpu/orch_r139_continual_controls.py',
    'tests/test_orch_r139_continual_controls.py',
    'gpu/orch_r125_continual_native.py', 'gpu/orch_r125_stream_journal.py',
    'gpu/orch_r125_continual_readout.py', 'gpu/astra_experienced_event_microloop.py',
    'gpu/astra_pchain2_native.py', 'gpu/orch_guided_native.py',
    'gpu/orch_r107_capability_run.py', 'organism_v6/orch_r107_capability.py',
    'organism_v6/orch_r124_train_history.py', 'organism_v6/orch_r125_continual_stream.py',
    'organism_v6/orch_r125_plain_context.py', 'organism_v6/pcfl_vertical_train.py',
)
NOTICE = (
    'This is a frozen control: no learning, no optimizer updates, no sleep, and no '
    'compaction at sleep. Any learning or sleep description in the startup describes '
    'the comparison learner, not this runtime. Ordinary oldest-context eviction '
    'still applies. Continue generating and receiving parent messages as usual. '
    'Separate scheduled capability checks do not change your weights or provide '
    'their contents or results to this conversation. '
)


def source_inventory(root):
    return {name: native.sha(Path(root) / name) for name in SOURCE_FILES}


def plan_binding(plan):
    return digest({key: value for key, value in plan.items() if key != 'cpu_gate'})


def adapter_files(directory):
    directory = Path(directory)
    require(directory.is_absolute() and directory.is_dir() and not directory.is_symlink(),
            'real_adapter_directory_required')
    files = {}
    for path in sorted(directory.iterdir()):
        require(path.is_file() and not path.is_symlink(), 'regular_adapter_files_only')
        files[path.name] = native.sha(path)
    require({'adapter_config.json', 'adapter_model.safetensors'} <= files.keys(),
            'actual_safetensors_adapter_required')
    from gpu.astra_pchain2_native import TARGET_MODULES
    config = native.read(directory / 'adapter_config.json')
    require(config.get('peft_type') == 'LORA'
        and type(config.get('r')) is int and config['r'] == 8 and config.get('lora_alpha') == 16
        and config.get('lora_dropout') == 0.05 and config.get('bias') == 'none'
        and config.get('task_type') == 'CAUSAL_LM'
        and set(config.get('target_modules', [])) == set(TARGET_MODULES)
        and not config.get('use_dora', False) and not config.get('use_rslora', False)
        and not config.get('modules_to_save') and not config.get('rank_pattern')
        and not config.get('alpha_pattern') and not config.get('fan_in_fan_out', False)
        and not config.get('lora_bias', False) and not config.get('target_parameters')
        and not config.get('trainable_token_indices'), 'exact_native_rank8_recipe')
    return files


def make_plan(reference_plan, *, mode, adapter=None, max_readouts=None):
    """Copy a native PLAN; caller supplies real paths, source snapshot and CPU gate."""
    native.validate_plan(reference_plan)
    require('startup_context' in reference_plan, 'R127_startup_required')
    plan = deepcopy(reference_plan)
    plan.update(schema=SCHEMA, reference_plan_sha256=digest(reference_plan),
        control=dict(mode=mode, adapter=deepcopy(adapter), learning_steps=0,
            optimizer_steps=0, sleep_enabled=False, compaction_at_sleep=False,
            readout_schedule=dict(initial=True, every_segments=reference_plan['segments_per_sleep'],
                reference_presleep_extra_segments=int(reference_plan.get('presleep_variant',
                    'free_distillation') != 'no_distillation'),
                basis='ordinary_committed_segments', max_readouts=max_readouts),
            sampling_rng=dict(seed=reference_plan.get('seed', 0),
                initialization='native_before_lora_then_reset_before_generation',
                generators=['python', 'torch_cpu', 'torch_cuda_all'])),
        source_files=source_inventory(plan['source_root']), cpu_gate=None)
    return validate_plan(plan)


def validate_plan(plan):
    require(plan.get('schema') == SCHEMA, 'control_plan_schema')
    reference = {key: deepcopy(value) for key, value in plan.items()
        if key not in ('control', 'source_files', 'cpu_gate', 'reference_plan_sha256')}
    reference['schema'] = native.SCHEMA
    require(digest(reference) == plan['reference_plan_sha256'], 'exact_reference_plan_binding')
    native.validate_plan(reference)
    require(plan.get('startup_context') is not None, 'R127_startup_required')
    require(plan.get('authorized_wall_extension') is None and plan.get('preupdate_recovery') is None,
            'new_control_life_only')
    control = plan['control']
    require(set(control) == {'mode', 'adapter', 'learning_steps', 'optimizer_steps',
        'sleep_enabled', 'compaction_at_sleep', 'readout_schedule', 'sampling_rng'}, 'exact_control_fields')
    require(control['mode'] in MODES, 'explicit_control_mode')
    require(type(control['learning_steps']) is int and control['learning_steps'] == 0
        and type(control['optimizer_steps']) is int and control['optimizer_steps'] == 0
        and control['sleep_enabled'] is False and control['compaction_at_sleep'] is False,
        'no_learning_sleep_or_compaction')
    schedule = control['readout_schedule']
    require(set(schedule) == {'initial', 'every_segments', 'reference_presleep_extra_segments',
        'basis', 'max_readouts'} and schedule['initial'] is True
        and type(schedule['every_segments']) is int
        and schedule['every_segments'] == plan['segments_per_sleep']
        and type(schedule['reference_presleep_extra_segments']) is int
        and schedule['reference_presleep_extra_segments'] == int(plan.get('presleep_variant',
            'free_distillation') != 'no_distillation')
        and schedule['basis'] == 'ordinary_committed_segments', 'explicit_matched_readout_frontiers')
    require(schedule['max_readouts'] is None or type(schedule['max_readouts']) is int
        and schedule['max_readouts'] > 0, 'explicit_control_smoke_limit')
    seed = plan.get('seed', 0)
    require(control['sampling_rng'] == dict(seed=seed,
        initialization='native_before_lora_then_reset_before_generation',
        generators=['python', 'torch_cpu', 'torch_cuda_all'])
        and type(control['sampling_rng']['seed']) is int, 'exact_sampling_seed_initialization')
    adapter = control['adapter']
    if control['mode'] == MODES[1]:
        require(adapter is None, 'base_control_has_no_adapter')
    else:
        require(type(adapter) is dict, 'explicit_real_adapter_initialization')
        if adapter.get('initialization') == 'seeded_rank8':
            require(set(adapter) == {'initialization'}, 'seeded_not_pretrained')
        else:
            require(set(adapter) == {'initialization', 'path', 'files', 'state_sha256'}
                and adapter['initialization'] == 'pretrained_rank8'
                and valid_sha256(adapter['state_sha256']), 'pinned_pretrained_adapter')
            require(adapter_files(adapter['path']) == adapter['files'], 'pretrained_adapter_files_binding')
    require(set(plan['source_files']) == set(SOURCE_FILES)
        and all(valid_sha256(value) for value in plan['source_files'].values()), 'exact_source_inventory')
    return plan


def verify_gate(plan):
    require(source_inventory(plan['source_root']) == plan['source_files'], 'source_provenance_drift')
    gate = plan.get('cpu_gate')
    require(type(gate) is dict and set(gate) == {'path', 'sha256'}
        and Path(gate['path']).is_absolute() and native.sha(gate['path']) == gate['sha256'],
        'bound_CPU_gate_required')
    receipt = native.read(gate['path'])
    require(receipt.get('schema') == GATE_SCHEMA and receipt.get('status') == 'PASS'
        and receipt.get('plan_binding') == plan_binding(plan)
        and receipt.get('source_files') == plan['source_files']
        and receipt.get('tests_passed') is True, 'passing_exact_CPU_provenance_gate')
    require(native.sha(receipt['test_log_path']) == receipt['test_log_sha256'], 'CPU_test_log_binding')
    line = receipt['coordination_line']
    require('[Builder]' in line and re.search(r'\b\d{4}-\d{2}-\d{2}\b', line) is not None
        and plan_binding(plan) in line
        and line in (Path(plan['source_root']) / 'research_loop/COORDINATION.md').read_text().splitlines(),
        'operator_Builder_coordination_gate')


def admitted_plan(plan_path):
    plan_path = Path(plan_path).resolve(strict=True)
    require(os.environ.get('R125_ADMISSION_PLAN_SHA256') == native.sha(plan_path),
            'admitted_control_plan_environment')
    plan = validate_plan(native.read(plan_path))
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'one_bound_GPU_environment')
    require(Path(__file__).resolve() == Path(plan['source_root']).resolve() / SOURCE_FILES[0],
            'executing_bound_source_snapshot')
    verify_gate(plan)
    return plan


class FrozenChild:
    count_tokens = native.NativeChild.count_tokens
    check = native.NativeChild.check
    seed_rng = native.NativeChild.seed_rng

    def __init__(self, plan, manifest=None):
        from gpu import astra_experienced_event_microloop as source
        from gpu import orch_guided_native as weights
        self.plan, self.native = plan, weights
        self.experiment = native.experiment_binding(plan)
        adapter = plan['control']['adapter']
        adapter_path = manifest['adapter_path'] if manifest else (
            adapter['path'] if adapter and adapter['initialization'] == 'pretrained_rank8' else None)
        tokenizer = source.native.load_local_tokenizer(plan['model_dir'])
        self.engine = source.Engine(SimpleNamespace(model_dir=plan['model_dir'],
            device='cpu' if adapter and adapter_path is None else 'cuda:0',
            phase='readout', expected_base_sha256=native.BASE_SHA256, adapter_dir=adapter_path),
            tokenizer, check=self.check)
        self.torch, self.tokenizer = self.engine.torch, tokenizer
        if adapter and adapter_path is None:
            native.NativeChild.initialize_adapter(self)
        self.parameters = {name: parameter for name, parameter in self.engine.model.named_parameters()
                           if weights.is_lora(name)}
        require(bool(self.parameters) == (adapter is not None), 'actual_adapter_presence')
        require(all(parameter.dtype == self.torch.float32 for parameter in self.parameters.values()),
                'FP32_frozen_adapter')
        require(plan['context_limit'] <= self.engine.model.config.max_position_embeddings,
                'context_within_local_model_positions')
        self.engine.model.requires_grad_(False)
        self.engine.model.eval()
        if adapter and adapter['initialization'] == 'pretrained_rank8':
            require(self.adapter_hash() == adapter['state_sha256'], 'loaded_pretrained_tensor_identity')
        self.seed_rng()
        self.identity = self.snapshot()
        if manifest:
            require(self.identity == manifest['identity'], 'loaded_frozen_model_identity')

    def adapter_hash(self):
        return self.native.state_hash(self.parameters) if self.parameters else None

    def snapshot(self):
        from gpu.orch_r125_continual_readout import _verify_device
        require(not any(parameter.requires_grad for parameter in self.engine.model.parameters())
            and not self.engine.model.training, 'frozen_readonly_eval')
        self.engine.verify_base()
        return dict(base_sha256=native.BASE_SHA256, base_fingerprint_verified=True,
            adapter_state_sha256=self.adapter_hash(), gpu_uuid=_verify_device(self.engine, self.plan),
            mode=self.plan['control']['mode'], learning_steps=0, optimizer_steps=0)

    def generate(self, messages, *, max_new_tokens, deadline_unix):
        response = native.NativeChild.generate(self, messages, max_new_tokens=max_new_tokens,
                                               deadline_unix=deadline_unix)
        require(response['adapter_state_sha256'] == self.identity['adapter_state_sha256'],
                'frozen_generation_adapter_identity')
        response.update(control_mode=self.plan['control']['mode'], learning_steps=0, optimizer_steps=0)
        return response

    def offload_for_readout(self):
        self.torch.cuda.synchronize()
        state = dict(cpu_rng=self.torch.get_rng_state(), cuda_rng=self.torch.cuda.get_rng_state_all(),
                     python_rng=random.getstate(), identity=self.snapshot())
        self.engine.model.to('cpu')
        gc.collect()
        self.torch.cuda.empty_cache()
        return state

    def restore_after_readout(self, state):
        self.engine.model.to('cuda:0')
        self.engine.model.requires_grad_(False)
        self.engine.model.eval()
        self.torch.set_rng_state(state['cpu_rng'])
        self.torch.cuda.set_rng_state_all(state['cuda_rng'])
        random.setstate(state['python_rng'])
        require(self.snapshot() == state['identity'] == self.identity, 'readout_preserves_frozen_resident')


def save_manifest(child, plan):
    directory = Path(plan['root']) / 'frozen_model'
    directory.mkdir(mode=0o700, exist_ok=False)
    identity = child.snapshot()
    require(identity == child.identity, 'unchanged_initial_frozen_identity')
    adapter_path, files = None, {}
    if child.parameters:
        adapter_path = str(directory / 'adapter')
        child.engine.model.save_pretrained(adapter_path, safe_serialization=True, save_embedding_layers=False)
        files = adapter_files(adapter_path)
    manifest = dict(schema=MANIFEST_SCHEMA, identity=identity, adapter_path=adapter_path,
        adapter_files=files, initialization=deepcopy(plan['control']['adapter']),
        model_state_sha256=digest(identity), plan_binding=plan_binding(plan),
        sampling_rng=deepcopy(plan['control']['sampling_rng']), runtime=child.engine.runtime,
        artifact_kind='immutable_frozen_model_not_learning_checkpoint', optimizer_checkpoint=None)
    path = directory / 'MANIFEST.json'
    native.write_once(path, manifest)
    return path, manifest


def verify_manifest(plan, path):
    path = Path(path).resolve(strict=True)
    require(path == Path(plan['root']).resolve() / 'frozen_model/MANIFEST.json', 'local_frozen_manifest')
    manifest = native.read(path)
    identity = manifest['identity']
    require(manifest['schema'] == MANIFEST_SCHEMA and manifest['plan_binding'] == plan_binding(plan)
        and manifest['model_state_sha256'] == digest(identity)
        and identity['base_sha256'] == native.BASE_SHA256 and identity['base_fingerprint_verified'] is True
        and identity['gpu_uuid'] == plan['gpu_uuid'] and identity['mode'] == plan['control']['mode']
        and identity['learning_steps'] == identity['optimizer_steps'] == 0
        and manifest['initialization'] == plan['control']['adapter']
        and manifest['sampling_rng'] == plan['control']['sampling_rng']
        and manifest['artifact_kind'] == 'immutable_frozen_model_not_learning_checkpoint'
        and manifest['optimizer_checkpoint'] is None, 'frozen_manifest_contract')
    if plan['control']['adapter'] is None:
        require(manifest['adapter_path'] is None and not manifest['adapter_files']
            and identity['adapter_state_sha256'] is None, 'no_fake_base_adapter')
    else:
        require(Path(manifest['adapter_path']).resolve() == path.parent / 'adapter'
            and adapter_files(manifest['adapter_path']) == manifest['adapter_files']
            and valid_sha256(identity['adapter_state_sha256']), 'frozen_adapter_manifest_binding')
    return manifest


def new_stream(plan, manifest):
    history = TrainHistory(system_prompt=plan['system_prompt'], birth_prompt=plan['birth_prompt'])
    adapter = plan['control']['adapter']
    label = ('A seed-initialized, never-trained rank-8 LoRA is mounted.'
        if adapter and adapter['initialization'] == 'seeded_rank8' else
        'A real pretrained frozen rank-8 LoRA is mounted.' if adapter else 'No adapter is mounted.')
    history.append(TrainEvent(event_id='runtime:r139_control', actor='environment', split='TRAIN',
        phase='feedback', episode_id='continual_stream', source_id=SCHEMA,
        source_sha256=digest(plan['control']), origin='TRAIN_COLLECTION', text=NOTICE + label))
    initial_budget = dict(context_limit=plan['context_limit'], segment_tokens=plan['segment_tokens'],
        total_generated_tokens=0, segments_per_readout=plan['control']['readout_schedule']['every_segments'],
        learning_steps=0, sleep_enabled=False)
    history.append(TrainEvent(event_id='runtime:birth_budget', actor='environment', split='TRAIN',
        phase='feedback', episode_id='continual_stream', source_id='R125_RUNTIME_BUDGET',
        source_sha256=digest(initial_budget), origin='TRAIN_COLLECTION',
        text='[budget] ' + json.dumps(initial_budget, sort_keys=True)))
    stream = ContinualStream(history, context_limit=plan['context_limit'],
        segment_tokens=plan['segment_tokens'], segments_per_sleep=plan['segments_per_sleep'],
        deadline_unix=plan['hard_end_unix'], model_state_sha256=manifest['model_state_sha256'],
        allow_eviction=True, experiment=native.experiment_binding(plan))
    if plan.get('presentation_version'):
        stream.set_presentation(dict(version=plan['presentation_version'],
            system_prompt=plan['system_prompt'], birth_prompt=plan['birth_prompt']), plan['context_limit'])
    return stream


def drive(child, stream, journal, dispatch):
    """Continuous ordinary generations; dispatch receives only cycle/frontier integers."""
    schedule = child.plan['control']['readout_schedule']
    dispatch(0, 0)
    cycles = 0
    while time.time() < child.plan['hard_end_unix']:
        stream.step(child.generate, child.count_tokens, journal.record, incoming=journal.read_inbox())
        require(stream.sleep_frontier == 0 and not stream.sleep_receipts, 'no_control_sleep_receipts')
        if len(stream.rows) % schedule['every_segments']:
            continue
        cycles += 1
        dispatch(cycles, len(stream.rows))
        if schedule['max_readouts'] is not None and cycles >= schedule['max_readouts']:
            journal.record('TERMINAL', dict(status='CONTROL_ENGINEERING_SMOKE_COMPLETE',
                scheduled_readouts=cycles, generated_segments=len(stream.rows), learning_steps=0,
                optimizer_steps=0, sleeps=0, retained_learning_claim=False))
            return


def fresh_readout(child, plan_path, manifest_path, cycle, frontier):
    plan = child.plan
    name = f'control_{cycle:06d}'
    output = Path(plan['root']) / 'readouts' / name
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    require(not output.exists(), 'readout_no_implicit_replay')
    command = [sys.executable, '-B', '-m', 'gpu.orch_r139_continual_controls', '--plan', str(plan_path),
               '--readout-manifest', str(manifest_path), '--output', str(output)]
    native.write_once(output.parent / (name + '_DISPATCH.json'), dict(cycle=cycle,
        ordinary_segment_frontier=frontier, schedule=plan['control']['readout_schedule'],
        command_sha256=digest(command), manifest_sha256=native.sha(manifest_path),
        resident_pid=os.getpid(), history_shared=False, parent_present=False,
        learning_steps=0, started_unix=time.time()))
    state = child.offload_for_readout()
    process = None
    try:
        with (output.parent / (name + '.log')).open('x') as log:
            process = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            status = process.wait(timeout=max(1, plan['hard_end_unix'] - time.time() - 15))
        require(status == 0 and (output / 'COMPLETE.json').is_file(), 'fresh_control_readout_incomplete')
    except Exception as error:
        native.write_once(output.parent / (name + '_FAILED.json'), dict(error_type=type(error).__name__,
            error=str(error), retry_allowed=False, failed_unix=time.time()))
    finally:
        try:
            if process is not None and process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
        finally:
            child.restore_after_readout(state)


@contextmanager
def bounded_wall(plan):
    remaining = plan['hard_end_unix'] - time.time()
    require(remaining > 0, 'control_wall_expired')
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    require(previous_timer == (0.0, 0.0), 'control_requires_unshared_wall_timer')
    previous_handler = signal.signal(signal.SIGALRM,
        lambda signum, frame: (_ for _ in ()).throw(TimeoutError('control_wall')))
    signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def run(plan_path):
    plan_path = Path(plan_path).resolve(strict=True)
    plan = admitted_plan(plan_path)
    with bounded_wall(plan):
        return _run(plan_path, plan)


def _run(plan_path, plan):
    from gpu.orch_r125_stream_journal import StreamJournal
    root = Path(plan['root'])
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    require(not (root / 'stream').exists() and not (root / 'frozen_model').exists(), 'new_control_no_resume')
    with StreamJournal(root / 'stream', create=True) as journal:
        child = FrozenChild(plan)
        manifest_path, manifest = save_manifest(child, plan)
        stream = new_stream(plan, manifest)
        journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
        journal.record('LOADED', dict(control=plan['control'], identity=child.identity,
            runtime=child.engine.runtime, plan_binding=plan_binding(plan), pid=os.getpid(),
            learning_steps=0, optimizer_steps=0, resume=False))
        drive(child, stream, journal, lambda cycle, frontier:
            fresh_readout(child, plan_path, manifest_path, cycle, frontier))


def run_readout(plan_path, manifest_path, output_path):
    plan = admitted_plan(plan_path)
    with bounded_wall(plan):
        return _run_readout(plan_path, manifest_path, output_path, plan)


def _run_readout(plan_path, manifest_path, output_path, plan):
    import torch
    from organism_v6 import orch_r107_capability as policy
    from gpu.orch_r107_capability_run import readonly_condition
    from gpu.orch_r125_continual_readout import SUITE_SHA256, MAX_NEW_TOKENS
    require(not torch.cuda.is_initialized(), 'fresh_process_without_resident_CUDA')
    manifest = verify_manifest(plan, manifest_path)
    manifest_sha256 = native.sha(manifest_path)
    output = Path(output_path).resolve()
    readouts = Path(plan['root']).resolve() / 'readouts'
    require(output != readouts and output.is_relative_to(readouts)
        and not output.is_relative_to(Path(plan['source_root']).resolve()), 'separate_private_readout_output')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    provenance = dict(schema=SCHEMA, mode=plan['control']['mode'], pid=os.getpid(),
        plan_sha256=native.sha(plan_path), manifest_sha256=manifest_sha256,
        model_state_sha256=manifest['model_state_sha256'], identity=manifest['identity'],
        learning_steps=0, optimizer_steps=0, history_present=False, parent_present=False,
        train_ingestion=False, suite_sha256=SUITE_SHA256, max_new_tokens=MAX_NEW_TOKENS,
        decoder=dict(do_sample=False, num_beams=1, repetition_penalty=1.0),
        policy_checkpoint_field_meaning='frozen_adapter_tensor_hash_or_actual_base_fingerprint',
        started_unix=time.time())
    native.write_once(output / 'REQUEST.json', provenance)
    call_files = {}
    child = None
    before = None
    try:
        tasks = policy.tasks()
        require(len(tasks) == 32 and policy.digest(tasks) == SUITE_SHA256, 'unchanged_held_registry')
        child = FrozenChild(plan, manifest)
        before = child.snapshot()
        native.write_once(output / 'BEFORE.json', before)
        identity_hash = before['adapter_state_sha256'] or before['base_sha256']
        captures = []
        for position, task in enumerate(tasks):
            arms = (('ON', 'OFF') if position % 2 == 0 else ('OFF', 'ON')) if child.parameters else ('OFF',)
            for arm in arms:
                child.check('readout_call')
                messages = policy.messages(task)
                name = f'CALL_{len(call_files):03d}.json'
                record = dict(task_id=task['id'], arm=arm, messages=deepcopy(messages), status='RESERVED')
                native.write_once(output / 'reservations' / name, record)
                try:
                    context = readonly_condition(child.engine.model, 'LORA_' + arm) if child.parameters else nullcontext()
                    with context:
                        response = child.engine.generate(messages, max_new_tokens=MAX_NEW_TOKENS)
                    record['response'] = deepcopy(response)
                    require(messages == policy.messages(task), 'public_messages_mutated')
                    require(response.get('max_new_tokens', MAX_NEW_TOKENS) == MAX_NEW_TOKENS, 'fixed_readout_cap')
                    response = dict(response, max_new_tokens=MAX_NEW_TOKENS,
                                    eos_token_id=child.tokenizer.eos_token_id)
                    capture = policy.capture(task, arm, response, checkpoint_sha256=identity_hash,
                        base_sha256=before['base_sha256'], lora_enabled=arm == 'ON')
                    captures.append(capture)
                    record.update(status='COMPLETE', capture=capture)
                except BaseException as error:
                    record.update(status='FAILED', error_type=type(error).__name__, error=str(error))
                    raise
                finally:
                    native.write_once(output / name, record)
                    call_files[name] = native.sha(output / name)
        after = child.snapshot()
        require(after == before == manifest['identity'], 'readout_frozen_identity_unchanged')
        require(native.sha(manifest_path) == manifest_sha256
            and verify_manifest(plan, manifest_path) == manifest, 'readout_manifest_unchanged')
        require(admitted_plan(plan_path) == plan, 'readout_plan_unchanged')
        native.write_once(output / 'AFTER.json', dict(after, unchanged=True))
        scores = (policy.reduce_paired(captures, checkpoint_sha256=identity_hash,
            base_sha256=before['base_sha256'], max_new_tokens=MAX_NEW_TOKENS) if child.parameters else None)
        require(len(call_files) == (64 if child.parameters else 32), 'all_actual_readout_cells')
        complete = dict(provenance, status='COMPLETE', calls=len(call_files), call_files=call_files,
            actual_arms=['ON', 'OFF'] if child.parameters else ['OFF'], paired_scores=scores,
            paired_comparison_available=bool(child.parameters), before_after_verified=True,
            finished_unix=time.time())
        native.write_once(output / 'COMPLETE.json', complete)
        return complete
    except BaseException as error:
        identity_check = dict(status='UNAVAILABLE', unchanged=False)
        if child is not None and before is not None:
            try:
                after = child.snapshot()
                identity_check = dict(status='PASS' if after == before else 'FAILED',
                    unchanged=after == before, identity=after)
            except BaseException as verification_error:
                identity_check = dict(status='FAILED', unchanged=False,
                    error_type=type(verification_error).__name__, error=str(verification_error))
        if not (output / 'AFTER.json').exists():
            native.write_once(output / 'AFTER.json', identity_check)
        native.write_once(output / 'FAILED.json', dict(provenance, status='FAILED',
            error_type=type(error).__name__, error=str(error), call_files=call_files,
            before_after_verified=identity_check['unchanged'], retry_allowed=False, finished_unix=time.time()))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--validate-only', action='store_true')
    parser.add_argument('--readout-manifest', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    require(bool(args.readout_manifest) == bool(args.output), 'readout_manifest_and_output_together')
    if args.validate_only:
        plan = validate_plan(native.read(args.plan))
        require(source_inventory(plan['source_root']) == plan['source_files'], 'source_provenance_drift')
        print(json.dumps(dict(status='CPU_PLAN_VALID_ONLY_NOT_LAUNCH_ADMISSION', plan_binding=plan_binding(plan))))
        return
    if args.readout_manifest:
        run_readout(args.plan, args.readout_manifest, args.output)
    else:
        run(args.plan)


if __name__ == '__main__':
    main()
