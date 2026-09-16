"""Exact F4 C112 CPU rehydration and publication-gated same-life continuation."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from types import FunctionType, SimpleNamespace


ROOT = Path('/localhome/local-rohing/orch_r115_grid_pair_20260915/F4')
OUTPUT = ROOT / 'r140_continuation_v1'
TIMER_OUTPUT = ROOT / 'r140_timer_custody_v1'
TIMER_SOURCE = Path('/localhome/local-rohing/orch_r139_F4_timer_source_v1/gpu/orch_r139_grid_timer_custody.py')
TIMER_SHA = '8dd31979a4ca1cafbf2a3dc9d7724adf2cb5ccb4c25610480d0add2730ebc10a'
BASE_PLAN_SHA = 'e09bd25ca7bca2089526a966ce1a34e678d350793911e3ea32ef262d0727d6b3'
NORMALIZER = Path('/localhome/local-rohing/orch_r140_grid_repair_20260916/gpu/orch_r140_grid_json.py')
NORMALIZER_SHA = '7a9d95d996fc6854b1a8cf19819850fc7d36d836cc857c9bdf3286245bb251e6'
FAILED_SHA = 'd4a7f4885084c8ca56d3770a45d0c67d80c8f4a94ad1168260a5ec6e7ade00dd'
CYCLE, FAILED, FIRST_PARENT = 112, 4456, 325


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return dict(path=str(Path(path).resolve(strict=True)), sha256=sha(path))


def checked(reference):
    path = Path(reference['path'])
    require(path.resolve() == path and sha(path) == reference['sha256'], 'immutable_reference')
    return read(path)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dependencies():
    require(sha(TIMER_SOURCE) == TIMER_SHA and sha(NORMALIZER) == NORMALIZER_SHA, 'pinned_dependencies')
    timer = load(TIMER_SOURCE, 'r140_previous_timer')
    handoff, legacy, native_path = timer.dependencies()
    return timer, handoff, legacy, load(NORMALIZER, 'r140_published_json')


def frozen_state(grid, root):
    rows = [json.loads(line) for line in (root / 'LEDGER.jsonl').read_text().splitlines() if line]
    require({kind: sum(row['kind'] == kind for row in rows) for kind in ('NATIVE', 'PARENT')}
            == dict(NATIVE=FAILED, PARENT=324), 'exact_failed_counters')
    for kind in ('NATIVE', 'PARENT'):
        require([row['number'] for row in rows if row['kind'] == kind]
                == list(range(1, 1 + sum(row['kind'] == kind for row in rows))), 'contiguous_counters')
    cached = [row for row in rows if row.get('cycle') == CYCLE]
    require(len(cached) == 33 and all(row['kind'] == 'NATIVE' and row['split'] == 'TRAIN'
            and not row['attached_readout'] for row in cached), 'C112_only_33_native_no_parent_charges')
    require([row['number'] for row in cached] == list(range(4424, FAILED + 1)), 'exact_C112_charge_order')
    failed_path = root / 'calls' / f'N{FAILED:05d}.json'
    require(sha(failed_path) == FAILED_SHA and read(failed_path)['status'] == 'STARTED', 'immutable_predispatch_frontier')
    require(read(root / 'CARRY.json') == read(root / 'cycles/0111/TRAIN_COMPLETE.json')['carry'], 'old_C111_carry')
    require(not (root / 'cycles/0112/TRAIN_COMPLETE.json').exists(), 'unfinished_C112')
    applications = sorted((root / 'independent_r119_v1/parent_applied').glob('*.json'))
    for path in applications:
        require(not any(4424 <= int(Path(item['path']).stem[1:]) <= FAILED
                        for item in read(path).get('applied_to', [])), 'no_C112_parent_application')
    paths = [root / name for name in ('LEDGER.jsonl', 'CARRY.json', 'TRAIN.json', 'CONFIG.json',
                                      'cycles/0111/TRAIN_COMPLETE.json', 'independent_r119_v1/LEASE_BUDGET.json')]
    paths += [root / 'calls' / f'N{row["number"]:05d}.json' for row in cached]
    paths += sorted((root / 'cycles/0112').rglob('*.json'))
    paths += sorted((root / 'triples').glob('C0112_*.json'))
    paths += applications
    return cached, {str(path): sha(path) for path in paths}


class FrontierReached(BaseException):
    pass


def reconstruction_writer(grid, root, *, dry):
    original = grid.write
    def write(path, value, replace=False):
        path = Path(path)
        if path.exists() and not replace:
            require(path.is_relative_to(root) and grid.read(path) == value, 'exact_existing_rehydrated_receipt')
            return
        require(not dry, 'CPU_history_cannot_write')
        if path.parent == root / 'calls':
            require(int(path.stem[1:]) > FAILED, 'old_native_records_immutable')
        return original(path, value, replace=replace)
    return write


def replay_class(grid, parent_type, cached, *, dry, frontier_calls=None):
    class RehydratedLife(parent_type):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.cursor, self.rehydrating = 0, True
            self.cached_environments, self.cached_asks = 0, []
            self.last_cached_raw = None
            self.frontier = None

        def calls(self, tasks, purpose, messages, cap, *, attached_readout=False):
            if not self.rehydrating:
                return super().calls(tasks, purpose, messages, cap, attached_readout=attached_readout)
            require(len(tasks) == len(messages) == 1 and not attached_readout, 'single_TRAIN_history')
            row = cached[self.cursor]
            require(row['task_id'] == tasks[0]['id'] and row['purpose'] == purpose
                    and tasks[0]['split'] == 'TRAIN', 'exact_cached_call_order')
            path = self.root / 'calls' / f'N{row["number"]:05d}.json'
            record = grid.read(path)
            require(record['messages'] == messages[0] and record['cap'] == cap, 'exact_cached_messages_and_cap')
            if row['number'] == FAILED:
                require(record['status'] == 'STARTED' and self.cursor == len(cached) - 1, 'single_started_frontier')
                self.frontier = dict(failed_call=ref(path), messages_sha256=digest(messages[0]), cap=cap,
                    task_id=tasks[0]['id'], purpose=purpose, completed_native_reused=self.cursor,
                    environment_receipts_reused=self.cached_environments, ask_projections=self.cached_asks,
                    frozen_messages_exact=True, no_cached_model_env_parent_calls=True)
                if dry:
                    raise FrontierReached()
                self.rehydrating = False
                require(frontier_calls is not None, 'published_frontier_generator')
                return frontier_calls(self, tasks, purpose, messages, cap, attached_readout=False)
            require(record['status'] == 'COMPLETE', 'only_COMPLETE_response_reuse')
            self.cursor += 1
            response = deepcopy(record['response'])
            response['reference'] = grid.ref(path)
            self.last_cached_raw = response['raw']
            self.event('child', response['raw'], grid.sha(path))
            return [response]

        def ask(self, task, episode, phase):
            if not self.rehydrating:
                return super().ask(task, episode, phase)
            require(phase in ('experience', 'open_turn'), 'only_observed_cached_ask_sites')
            if phase == 'experience':
                path = self.root / 'triples' / f'C{self.cycle:04d}_E{episode}.json'
                result = deepcopy(grid.read(path)['intervention'])
                require(result['request'] is None and result['response'] is None
                        and result['disposition']['status'] == 'PENDING'
                        and result['disposition']['guidance'] is None, 'cached_nonblocking_no_dispatch')
                self.cached_asks.append(dict(phase=phase, episode=episode, source=ref(path)))
                return result
            require(episode == 0, 'only_completed_first_open_ask')
            self.cached_asks.append(dict(phase=phase, episode=episode,
                proof='pinned_AsyncLife.ask_always_returns_null_direct_guidance; no_C112_parent_charge',
                timestamp_reconstructed=False))
            return dict(disposition=dict(guidance=None))

        def environment(self, task, state, raw, purpose, sequence, *, open_turn=False, attached_readout=False):
            if not self.rehydrating:
                return super().environment(task, state, raw, purpose, sequence,
                    open_turn=open_turn, attached_readout=attached_readout)
            require(not attached_readout and task['split'] == 'TRAIN' and raw == self.last_cached_raw,
                    'cached_action_bound_to_actual_child_response')
            path = self.root / 'cycles' / f'{self.cycle:04d}' / purpose / f'{task["id"]}_{sequence:02d}.json'
            document = grid.read(path)
            feedback, after = document['environment_call'], document['resulting_state']
            require(document['task_id'] == task['id'] and document['split'] == 'TRAIN'
                    and document['attached_readout'] is False, 'saved_environment_task_join')
            if feedback.get('operation') == 'NO_ENVIRONMENT_REQUEST':
                require(open_turn and after == state and feedback == dict(operation='NO_ENVIRONMENT_REQUEST',
                    enacted=False, semantic_initiative='UNASSESSED', child_received=True), 'cached_open_noop')
            else:
                require(feedback['before_observation'] == grid.policy.public_observation(task, state)
                        and feedback['after_observation'] == grid.policy.public_observation(task, after)
                        and feedback['post_task_exploration'] == open_turn, 'saved_environment_state_join')
            self.cached_environments += 1
            self.event('environment', json.dumps(feedback, sort_keys=True), grid.sha(path))
            return deepcopy(after), deepcopy(feedback), grid.ref(path)
    return RehydratedLife


def cpu_rehydrate(grid, prior, root, config):
    cached, references = frozen_state(grid, root)
    parent_type = prior.mailbox.life_class(grid, 'independent_r119_v1', first_parent=FIRST_PARENT)
    life = replay_class(grid, parent_type, cached, dry=True)(root, None, config, CYCLE)
    roster, memory = read(root / 'TRAIN.json'), read(root / 'CARRY.json')
    writer = grid.write
    grid.write = reconstruction_writer(grid, root, dry=True)
    try:
        grid.train_cycle(life, [roster[7], roster[15]], memory)
        raise ValueError('expected_missing_native_frontier')
    except FrontierReached:
        require(life.frontier is not None and life.cursor == 32 and life.cached_environments == 32,
                'complete_exact_cached_prefix')
    finally:
        grid.write = writer
    require(references == {path: sha(path) for path in references}, 'CPU_inputs_unchanged')
    return dict(frontier=life.frontier, input_hashes=references, counts=dict(NATIVE=4456, PARENT=324),
                cycle=112, CPU_only=True, native_calls=0, environment_calls=0, parent_calls=0, charges=0)


def normalized_life(grid, normalizer):
    if getattr(grid.Life, '_r140_normalized', False):
        return grid.Life
    base = grid.Life
    class NormalizedLife(base):
        _r140_normalized = True
        def calls(self, tasks, purpose, messages, cap, *, attached_readout=False):
            require(not attached_readout and len(tasks) == len(messages) == 1
                    and tasks[0]['split'] == 'TRAIN', 'TRAIN_only_single_normalized_generation')
            actual, metadata = normalizer.normalize_messages(self.engine.tokenizer, messages[0], cap, limit=16384)
            require(normalizer.recover_original_messages(actual, metadata) == messages[0], 'lossless_originals')
            original = grid.write
            def annotated(path, value, replace=False):
                if isinstance(value, dict) and 'messages' in value and 'status' in value:
                    require(value['number'] > FAILED, 'fresh_native_reservation_only')
                    if metadata['applied']:
                        value = dict(value, lossless_json_normalization=metadata, normalizer_sha256=NORMALIZER_SHA)
                return original(path, value, replace=replace)
            grid.write = annotated
            try:
                return super().calls(tasks, purpose, [actual], cap, attached_readout=False)
            finally:
                grid.write = original
    return NormalizedLife


def cpu_dispatch_record_proof(grid, normalizer, root, tokenizer):
    from unittest.mock import patch
    failed_path = root / 'calls' / f'N{FAILED:05d}.json'
    before = sha(failed_path)
    failed = read(failed_path)
    records, sent, reservations = {}, [], []
    def reserve(unused_root, kind, detail):
        require(kind == 'NATIVE', 'CPU_integration_no_parent')
        reservations.append(detail)
        return FAILED + len(reservations)
    def write(path, value, replace=False):
        require(Path(path) == root / 'calls' / 'N04457.json', 'CPU_memory_only_fresh_record')
        records[str(path)] = deepcopy(value)
    def batch(messages, cap):
        require(records[str(root / 'calls/N04457.json')]['messages'] == messages[0], 'STARTED_equals_dispatch')
        sent.append((deepcopy(messages), cap))
        return [dict(raw='CPU_STUB_NOT_A_MODEL_RESPONSE', token_ids=[])]
    with (patch.object(grid, 'reserve', reserve), patch.object(grid, 'write', write),
          patch.object(grid, 'ref', lambda path: dict(path=str(path), sha256=digest(records[str(path)]))),
          patch.object(grid.Life, 'event', lambda *args: None)):
        life = normalized_life(grid, normalizer)(root, SimpleNamespace(tokenizer=tokenizer, batch=batch), {}, CYCLE)
        life.calls([dict(id=failed['task_id'], split='TRAIN')], failed['purpose'], [failed['messages']], failed['cap'])
    record = records[str(root / 'calls/N04457.json')]
    require(len(sent) == len(reservations) == 1 and record['messages'] == sent[0][0][0]
            and record['status'] == 'COMPLETE' and record['cap'] == sent[0][1] == failed['cap'], 'COMPLETE_equals_dispatch')
    metadata = record['lossless_json_normalization']
    require(normalizer.recover_original_messages(record['messages'], metadata) == failed['messages']
            and before == sha(failed_path), 'exact_original_and_FAILED_unchanged')
    return dict(CPU_only=True, dispatch_stub=True, production_Life_calls_used=True,
        actual_tokenizer=True, recorded_equals_dispatched=True, STARTED_and_COMPLETE_verified=True,
        original_messages_reconstructed=True, failed_call=ref(failed_path), failed_status_unchanged='STARTED',
        original_prompt_tokens=metadata['original_prompt_tokens'], actual_prompt_tokens=metadata['actual_prompt_tokens'],
        generation_cap=failed['cap'], would_reserve_native=FAILED + 1, real_reservations=0,
        native_calls=0, environment_calls=0, parent_calls=0, disk_writes=0)


def prepare():
    timer, handoff, legacy, normalizer = dependencies()
    prior = legacy.original()
    grid, unused, root, config, checkpoint = prior.configure('F4')
    initial = read(ROOT / 'r139_astra_handoff_v1/RESUMED.json')
    require(not legacy.same_process(initial['identity']), 'failed_actor_must_be_gone')
    proof = cpu_rehydrate(grid, prior, root, dict(config, parent_model=handoff.ASTRA))
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(config['model_dir'], local_files_only=True)
    integration = cpu_dispatch_record_proof(grid, normalizer, root, tokenizer)
    base_path = TIMER_SOURCE.parent.parent / 'F4_TIMER_PLAN.json'
    require(sha(base_path) == BASE_PLAN_SHA, 'frozen_original_timer_plan')
    base = read(base_path)
    old_custody = ref(ROOT / 'r139_timer_custody_v1/ARMED.json')
    controller = checked(old_custody)['controller_identity']
    require(legacy.same_process(controller) and legacy.no_attempt(Path(checked(base['old_final_plan'])['output'])),
            'live_old_timer_and_unattempted_FINAL')
    require(not OUTPUT.exists() and not TIMER_OUTPUT.exists(), 'new_continuation_namespaces')
    return dict(base, schema='R140_F4_C112_CONTINUATION_V1', output=str(TIMER_OUTPUT),
        controller_source=ref(__file__), base_timer_plan=ref(base_path), previous_custody=old_custody,
        normalizer=ref(NORMALIZER), predecessor=initial['identity'], old_timers={'previous_R139_controller': controller},
        initial_successor_receipt=str(OUTPUT / 'RESUMED.json'), original_initial=ref(ROOT / 'r139_astra_handoff_v1/RESUMED.json'),
        reconstruction=proof, normalization_integration=integration,
        first_parent=FIRST_PARENT, failed_predispatch=ref(ROOT / 'calls/N04456.json'),
        status='STAGED_NOT_AUTHORIZED', normalizer_exact_proof=ref(NORMALIZER.parent.parent / 'EXACT_FAILED_CALL_PROOF.json'))


def validate(plan):
    timer, handoff, legacy, normalizer = dependencies()
    base = checked(plan['base_timer_plan'])
    require(plan['base_timer_plan']['sha256'] == BASE_PLAN_SHA, 'frozen_original_timer_plan')
    timer.validate(base)
    require(plan['schema'] == 'R140_F4_C112_CONTINUATION_V1' and plan['root'] == str(ROOT)
            and plan['output'] == str(TIMER_OUTPUT) and plan['controller_source'] == ref(__file__)
            and plan['normalizer'] == ref(NORMALIZER) and plan['first_parent'] == FIRST_PARENT
            and plan['initial_successor_receipt'] == str(OUTPUT / 'RESUMED.json'), 'exact_R140_scope')
    for name in ('morning_unix', 'evaluation_end_unix', 'train_end_unix', 'hard_end_unix',
                 'existing_FINAL_quota', 'additional_FINAL_calls', 'parent_FINAL_calls', 'sealed_inputs_to_parent',
                 'empty_readout_context', 'actions', 'approved_intake', 'requested_scope', 'old_final_plan',
                 'morning_successor_receipt', 'checkpoint', 'handoff_source', 'handoff_plan', 'legacy_source', 'native_source'):
        require(plan[name] == base[name], 'unchanged_custody_' + name)
    initial = checked(plan['original_initial'])
    require(plan['predecessor'] == initial['identity'] and plan['old_timers'] ==
            {'previous_R139_controller': checked(plan['previous_custody'])['controller_identity']}, 'exact_predecessor_custody')
    require(plan['failed_predispatch']['sha256'] == FAILED_SHA, 'immutable_failed_source')
    checked(plan['normalizer_exact_proof'])
    return handoff, legacy, checked(plan['old_final_plan'])


def completed_boundary(root, legacy):
    rows = [json.loads(line) for line in (root / 'LEDGER.jsonl').read_text().splitlines() if line]
    cycle = max(row.get('cycle', 0) for row in rows)
    path = root / 'cycles' / f'{cycle:04d}' / 'TRAIN_COMPLETE.json'
    document = read(path)
    require(len(document['outcomes']) == 2 and document['optimizer_steps'] == 0
            and document['carry'] == read(root / 'CARRY.json'), 'two_episodes_durable_carry')
    for row in rows:
        if row.get('cycle') == cycle and row['kind'] == 'NATIVE':
            require(row['split'] == 'TRAIN' and not row.get('attached_readout'), 'TRAIN_cursor_only')
            call = root / 'calls' / f'N{row["number"]:05d}.json'
            if row['number'] == FAILED:
                retirement = read(OUTPUT / 'FAILED_PREDISPATCH.json')
                require(retirement['failed_call'] == ref(call) and sha(call) == FAILED_SHA
                        and retirement['status'] == 'FAILED_PREDISPATCH_CONTEXT_OVERFLOW', 'explicit_failed_charge_preserved')
            else:
                require(read(call)['status'] == 'COMPLETE', 'no_unfinished_model_input')
    return dict(cycle=cycle, next_cycle=cycle + 1, ledger=ref(root / 'LEDGER.jsonl'), carry=ref(root / 'CARRY.json'),
        train_complete=ref(path), counts={kind: sum(row['kind'] == kind for row in rows) for kind in ('NATIVE', 'PARENT')},
        pending_parent_claims_preserved=True, optimizer_used=False, no_replay=True, retired_predispatch_charges=[FAILED])


def timer_namespace(plan):
    timer, handoff, legacy, normalizer = dependencies()
    namespace = dict(vars(timer), __file__=__file__, OUTPUT=TIMER_OUTPUT)
    for name, value in vars(timer).items():
        if isinstance(value, FunctionType) and value.__globals__ is vars(timer):
            bound = FunctionType(value.__code__, namespace, value.__name__, value.__defaults__, value.__closure__)
            bound.__kwdefaults__ = value.__kwdefaults__
            namespace[name] = bound
    def timer_validate(candidate):
        current_handoff, current_legacy, old = validate(candidate)
        legacy_view = SimpleNamespace(**dict(vars(current_legacy),
            completed_boundary=lambda root: completed_boundary(root, current_legacy)))
        handoff_view = SimpleNamespace(**dict(vars(current_handoff),
            boundary_snapshot=lambda root, ignored: current_handoff.boundary_snapshot(root, legacy_view)))
        return handoff_view, current_legacy, old
    namespace['validate'] = timer_validate
    original_receipt = namespace['custody_receipt']
    def custody_receipt(candidate, identity, publication_ref):
        return dict(original_receipt(candidate, identity, publication_ref), initial_resume_entrypoint='continue',
            rehydration_cycle=CYCLE, historical_failed_charge=FAILED, first_parent=FIRST_PARENT,
            normalizer=candidate['normalizer'])
    namespace['custody_receipt'] = custody_receipt
    original_adapter = namespace['adapted_native']
    def adapted_native(candidate, current_legacy, old, derived):
        callbacks = original_adapter(candidate, current_legacy, old, derived)
        resume = callbacks['resume']
        view = SimpleNamespace(**vars(resume.__globals__['custody']))
        original_validate = view.validate
        def validated_resume(actual):
            prior, grid, config, checkpoint = original_validate(actual)
            grid.Life = normalized_life(grid, normalizer)
            mailbox = current_legacy.original().mailbox
            prior.mailbox = SimpleNamespace(life_class=lambda module, era:
                mailbox.life_class(module, era, first_parent=FIRST_PARENT))
            return prior, grid, config, checkpoint
        view.validate = validated_resume
        require_released = timer.bind(resume.__globals__['require_released'], custody=view)
        callbacks['resume'] = timer.bind(resume, custody=view, require_released=require_released)
        return callbacks
    namespace['adapted_native'] = adapted_native
    return namespace


def continue_native(plan, publication_path):
    timer, handoff, legacy, normalizer = dependencies()
    validate(plan)
    namespace = timer_namespace(plan)
    namespace['live_custody'](plan, legacy, ref(publication_path))
    require(not legacy.same_process(plan['predecessor']), 'old_actor_gone')
    for path, expected in plan['reconstruction']['input_hashes'].items():
        require(sha(path) == expected, 'unchanged_rehydration_inputs')
    prior = legacy.original()
    grid, unused, root, config, checkpoint = prior.configure('F4')
    require(cpu_rehydrate(grid, prior, root, dict(config, parent_model=handoff.ASTRA)) == plan['reconstruction'], 'exact_published_CPU_proof')
    publication = read(publication_path)
    admission = checked(publication['continuation_admission'])
    require(admission['clear'] is True and admission['scanner_euid'] == 0 and not admission['blocking_reasons']
            and admission['gpu']['uuid'] == config['uuid'] and 0 <= time.time() - publication['admission_observed_unix'] <= 120,
            'fresh_same_GPU_admission')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == config['uuid'] and time.time() < timer.TRAIN_END, 'same_GPU_and_wall')
    OUTPUT.mkdir(mode=0o700)
    namespace['register'](plan, legacy, 'initial')
    with (OUTPUT / 'OLD_CARRY.json').open('xb') as stream:
        stream.write((root / 'CARRY.json').read_bytes())
    legacy.write(OUTPUT / 'FAILED_PREDISPATCH.json', dict(status='FAILED_PREDISPATCH_CONTEXT_OVERFLOW',
        failed_call=plan['failed_predispatch'], exact_proof=plan['normalizer_exact_proof'],
        original_status_unchanged='STARTED', old_charge_preserved=True, fresh_reservation_required=True))
    from peft import PeftModel
    from gpu import orch_guided_native as native
    engine = grid.load_engine(config)
    identity = native.bridge.AdapterIdentity.from_document(checkpoint['adapter'])
    engine.model = PeftModel.from_pretrained(engine.model, identity.path, is_trainable=False,
        local_files_only=True, autocast_adapter_dtype=True)
    engine.model.requires_grad_(False)
    engine.model.eval()
    require(native.observe_adapter(engine, identity) == identity, 'same_frozen_LoRA')
    for path, expected in plan['reconstruction']['input_hashes'].items():
        require(sha(path) == expected, 'unchanged_history_after_model_load')
    caps = read(ROOT / 'independent_r119_v1/LEASE_BUDGET.json')['prospective_caps']
    grid.MAX_NATIVE, grid.MAX_PARENT = caps['NATIVE'], caps['PARENT']
    config = dict(config, parent_model=handoff.ASTRA)
    writer = grid.write
    def provenance(path, value, replace=False):
        if isinstance(value, dict) and 'messages' in value and 'status' in value:
            require(value['split'] == 'TRAIN' and not value['attached_readout'], 'TRAIN_only')
            value = dict(value, adapter=identity.document(), fork_checkpoint_sha256=prior.CHECKPOINT_SHA,
                parent_nonblocking=True, local_optimizer_steps=0, parent_segment=handoff.ERA,
                continuation_source_sha256=sha(__file__))
        return writer(path, value, replace=replace)
    grid.write = provenance
    grid.Life = normalized_life(grid, normalizer)
    parent_type = prior.mailbox.life_class(grid, 'independent_r119_v1', first_parent=FIRST_PARENT)
    cached, ignored = frozen_state(grid, root)
    replay = replay_class(grid, parent_type, cached, dry=False, frontier_calls=grid.Life.calls)
    grid.write = reconstruction_writer(grid, root, dry=False)
    initial = checked(plan['original_initial'])
    legacy.write(OUTPUT / 'RESUMED.json', dict(identity=legacy.process(os.getpid()), checkpoint=plan['checkpoint'],
        parent_model=handoff.ASTRA, parent_segment=handoff.ERA, counter_reset=False, next_cycle=CYCLE,
        counts=plan['reconstruction']['counts'], boundary=initial['boundary'], after_parent=initial['after_parent'],
        rehydration_frontier=plan['reconstruction']['frontier'], first_parent=FIRST_PARENT,
        source=ref(__file__), normalizer=plan['normalizer'], optimizer_steps=0, live_rng_restored=False))
    roster, memory, cycle = read(root / 'TRAIN.json'), read(root / 'CARRY.json'), CYCLE
    while time.time() < timer.TRAIN_END:
        life = (replay if cycle == CYCLE else parent_type)(root, engine, config, cycle)
        tasks = [roster[(cycle - 1) % 8], roster[8 + (cycle - 1) % 8]]
        try:
            grid.train_cycle(life, tasks, memory)
        except grid.TrainWindowClosed:
            break
        memory = read(root / 'CARRY.json')
        cycle += 1
    legacy.write(OUTPUT / 'TRAIN_ENDED.json', dict(next_cycle=cycle, counter_reset=False, extra_FINAL_calls=0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'timer', 'continue', 'current', 'morning', 'evaluate', 'resume'))
    parser.add_argument('--expected-self-sha256', required=True)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--plan-sha256')
    parser.add_argument('--publication', type=Path)
    args = parser.parse_args()
    require(sha(__file__) == args.expected_self_sha256 and sys.dont_write_bytecode, 'immutable_no_bytecode_command')
    if args.mode == 'prepare':
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_proof_only')
        print(json.dumps(prepare(), sort_keys=True, indent=2))
        return
    require(args.plan is not None and args.publication is not None and sha(args.plan) == args.plan_sha256, 'exact_Main_plan')
    plan, publication = read(args.plan), read(args.publication)
    timer, handoff, legacy, normalizer = dependencies()
    validate(plan)
    timer.authorize(plan, publication, ref(args.plan), time.time())
    require(publication.get('R140_C112_continuation') is True and publication.get('normalizer') == plan['normalizer'],
            'Main_published_frontier_and_normalizer')
    namespace = timer_namespace(plan)
    if args.mode == 'timer':
        namespace['arm'](plan, args.plan, args.publication)
    elif args.mode == 'continue':
        continue_native(plan, args.publication)
    elif args.mode == 'current':
        namespace['live_custody'](plan, legacy, ref(args.publication))
        print(json.dumps(namespace['current_native'](plan, legacy), sort_keys=True))
    elif args.mode == 'morning':
        namespace['morning'](plan, args.plan, args.publication)
    else:
        namespace['native_phase'](plan, args.mode, args.plan, args.publication)


if __name__ == '__main__':
    main()
