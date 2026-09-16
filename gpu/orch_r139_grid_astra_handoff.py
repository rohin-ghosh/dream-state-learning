"""F4 saved-cycle Astra handoff adapter; stage by default, Main publishes execution."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import re
import shlex
import sys
import time
from types import FunctionType


ROOT = Path('/localhome/local-rohing/orch_r115_grid_pair_20260915/F4')
ERA = 'r139_astra_handoff_v1'
OLD_ERA = 'independent_r119_v1'
ASTRA = 'openai/openai/gpt-6-astra'
HARD_END = 1789596240
TRAIN_END = 1789596120
MORNING = 1789538400
DIRECTIVE = 'bb2f2eb9716c97f13697dadb804fdedc6626f470'
CUSTODY = Path('/localhome/local-rohing/orch_r119_grid_final_source_20260915_v1/gpu/orch_r119_grid_final_lifecycle.py')
CUSTODY_SHA = '28c8d5d052d289ec8f3feaa0095e083f0945b1f0829dc3dec1b8ce19f15913bd'
BROKER_RUNTIME = Path('/tmp/orch_r118_grid_http_source_20260915_v1')
BROKER_PINS = {
    'gpu/orch_r110_claude_broker.py': '6d2dc623cf1e7000175de78160d6f791ac040ad3679bbd6ae852529b8db1cb99',
    'gpu/orch_r118_astra_slots.py': '2c0e63311dac814044234c1fc48d4650aab4947f560620bbc79ccbbbd67d7a4d',
    'gpu/orch_r118_node3_6_grid_broker_http.py': '7ca44f23b83b334f91b539c22944814602577970b892fef85e09ef75ce0e9d18',
    'gpu/orch_r115_grid_astra.py': 'a9afab32f2b15c2c1fdf420122c908c08bd185b467b2f1677eddab3a9d6d06d7',
    'gpu/orch_route_parent_campaign_providers.py': 'b0f76da0d2037aa8dd5b922cc57942ba4f9ac7ec9249c4367380a9b5791ffc14',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    path = Path(path)
    require(path.resolve() == path and path.stat().st_size <= 16 * 1024 * 1024, 'bounded_regular_document')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate_key')
            result[key] = value
        return result
    return json.loads(path.read_bytes(), object_pairs_hook=unique)


def reference(path):
    return dict(path=str(Path(path).resolve(strict=True)), sha256=sha(path))


def checked(reference_value):
    path = check_hash(reference_value)
    return read(path)


def check_hash(reference_value):
    path = Path(reference_value['path'])
    require(path.resolve() == path and sha(path) == reference_value['sha256'], 'immutable_reference')
    return path


def custody():
    require(sha(CUSTODY) == CUSTODY_SHA, 'pinned_existing_boundary_seam')
    specification = importlib.util.spec_from_file_location('r139_existing_custody', CUSTODY)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def stage():
    legacy = custody()
    old_final = read(ROOT / legacy.EVENT / 'PLAN.json')
    loaded = read(ROOT / OLD_ERA / 'LOADED.json')
    ready = read(ROOT / OLD_ERA / 'READY.json')
    budget = read(ROOT / OLD_ERA / 'LEASE_BUDGET.json')
    config = read(ROOT / 'CONFIG.json')
    require(legacy.same_process(old_final['predecessor'])
            and loaded['pid'] == old_final['predecessor']['pid'], 'exact_live_F4_predecessor')
    require(config['life_id'] == 'F4_FABLE' and config['parent_model'] == 'claude-fable-5-1'
            and ready['mode'] == 'GEN1_FROZEN_LORA_ELICITATION_ONLY'
            and loaded['optimizer_steps'] == ready['local_optimizer_steps'] == 0, 'frozen_elicitation_only')
    require(budget['hard_end_unix'] == HARD_END and ready['train_end_unix'] == TRAIN_END,
            'original_wall')
    rows = [json.loads(line) for line in (ROOT / 'LEDGER.jsonl').read_text().splitlines() if line]
    return dict(schema='R139_F4_SAVED_STATE_HANDOFF_V1', root=str(ROOT), output=str(ROOT / ERA),
        status='STAGED_NOT_AUTHORIZED', approved_intake=DIRECTIVE + ':COORDINATION_2026-09-16T02:35Z',
        requested_scope='R121_LEVEL1_F4_PROSPECTIVE_PARENT_CHOICE_NO_RESET',
        source_sha256=sha(__file__), custody_sha256=CUSTODY_SHA,
        predecessor=old_final['predecessor'],
        observed_counts={kind: sum(row['kind'] == kind for row in rows) for kind in ('NATIVE', 'PARENT')},
        observed_cycle=max(row['cycle'] for row in rows), observed_unix=time.time(),
        references={name: reference(path) for name, path in {
            'config': ROOT / 'CONFIG.json', 'broker_config': ROOT / 'BROKER_CONFIG.json',
            'old_Claude_config': ROOT / 'parent_claude/CONFIG.json',
            'budget': ROOT / OLD_ERA / 'LEASE_BUDGET.json', 'loaded': ROOT / OLD_ERA / 'LOADED.json',
            'ready': ROOT / OLD_ERA / 'READY.json', 'checkpoint': Path(old_final['checkpoint']['path']),
            'old_final_plan': ROOT / legacy.EVENT / 'PLAN.json',
            'old_morning_timer': ROOT / legacy.EVENT / 'ARMED.json',
            'old_wall_timer': ROOT / legacy.EVENT / 'WALL_ARMED.json'}.items()},
        hard_end_unix=HARD_END, train_end_unix=TRAIN_END, morning_unix=MORNING,
        cumulative_caps=budget['prospective_caps'], old_Claude_cap=298, requested_model=ASTRA,
        new_segment_cap='existing cumulative PARENT ceiling minus ACTUAL boundary PARENT high-water',
        broker_runtime=str(BROKER_RUNTIME), broker_pins=BROKER_PINS,
        optimizer_mode='NO_ACTIVE_OPTIMIZER_ARCHIVED_ADAMW_RNG_BYTES_PRESERVED',
        runtime_rng_mode='GREEDY_NO_SAMPLING_NO_LIVE_RNG_CHECKPOINT_AVAILABLE',
        release_condition='NEXT_DURABLE_COMPLETE_TWO_EPISODE_CYCLE_NO_INFLIGHT_CALLS',
        provider_calls=0, signals_sent=0, child_launches=0, counter_reset=False,
        required_Main_publication=['exact plan hash and approved scope',
            'live successor-aware morning and hard-wall custody receipt',
            'exact stopped-and-released durable boundary', 'fresh strict GPU admission before resume'])


def authorize(plan, publication, plan_sha256, mode, now):
    require(plan['schema'] == 'R139_F4_SAVED_STATE_HANDOFF_V1' and plan['root'] == str(ROOT)
            and plan['output'] == str(ROOT / ERA) and plan['requested_model'] == ASTRA,
            'only_F4_saved_state_handoff')
    require(plan['source_sha256'] == sha(__file__) and plan['custody_sha256'] == CUSTODY_SHA,
            'exact_handoff_source')
    require(plan['hard_end_unix'] == HARD_END and plan['train_end_unix'] == TRAIN_END
            and plan['morning_unix'] == MORNING, 'no_clock_expansion')
    require(publication.get('authorized') is True and publication.get('published_by') == 'Main'
            and publication.get('plan_sha256') == plan_sha256
            and publication.get('approved_intake') == plan['approved_intake']
            and publication.get('requested_scope') == plan['requested_scope']
            and mode in publication.get('modes', [])
            and publication.get('not_before_unix', now + 1) <= now < TRAIN_END,
            'Main_exact_publication_required')
    require(publication.get('new_parent_model') == ASTRA
            and publication.get('no_reset') is True and publication.get('no_historical_redispatch') is True,
            'truthful_prospective_only')


def validate_native(plan, publication):
    legacy = custody()
    for item in plan['references'].values():
        checked(item)
    budget = checked(plan['references']['budget'])
    require(plan['cumulative_caps'] == budget['prospective_caps'], 'no_cap_expansion')
    timers = checked(publication['timer_custody'])
    require(timers['root'] == str(ROOT) and timers['status'] == 'ARMED_SUCCESSOR_AWARE'
            and timers['train_end_unix'] == TRAIN_END and timers['hard_end_unix'] == HARD_END
            and timers['morning_unix'] == MORNING and timers['existing_FINAL_quota'] == 8
            and timers['additional_FINAL_calls'] == 0 and timers['sealed_inputs_to_parent'] is False
            and timers['old_final_plan'] == plan['references']['old_final_plan']
            and timers['successor_receipt_path'] == str(ROOT / ERA / 'RESUMED.json')
            and timers['resume_preserves_R139_parent_binding'] is True,
            'preserve_morning_and_wall_custody')
    require(sha(timers['controller_source']['path']) == timers['controller_source']['sha256']
            and legacy.same_process(timers['controller_identity']), 'actual_live_timer_custody')
    return legacy


def boundary_snapshot(root, legacy):
    root = Path(root)
    boundary = legacy.completed_boundary(root)
    rows = [json.loads(line) for line in (root / 'LEDGER.jsonl').read_text().splitlines() if line]
    for kind in ('NATIVE', 'PARENT'):
        numbers = [row['number'] for row in rows if row['kind'] == kind]
        require(numbers == list(range(1, len(numbers) + 1)), 'cumulative_counters_no_reset')
    old_claims = sorted(path.name for path in (root / 'parent_claude').glob('P*.claim'))
    require(old_claims == [f'P{number:04d}.claim' for number in range(1, 299)], 'preserve_all_298_Claude_claims')
    require(not (root / 'parent_claude/RUNNER.lock').exists(), 'old_broker_must_be_released')
    high_water = boundary['counts']['PARENT']
    queue_numbers = [int(path.name[1:].split('.')[0]) for path in (root / 'parent_queue').glob('P*.request.json')]
    require(max(queue_numbers, default=0) <= high_water, 'queue_ledger_boundary_join')
    boundary.update(after_parent=high_water, first_new_parent=high_water + 1,
                    old_claims_sha256=hashlib.sha256('\n'.join(old_claims).encode()).hexdigest(),
                    original_Claude_claims=298, skip_historical_pending=True,
                    parent_model_before='claude-fable-5-1', parent_model_after=ASTRA,
                    full_episodes_preserved=True, no_live_episode_abandoned=True)
    return boundary


def release(plan, publication):
    legacy = validate_native(plan, publication)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_release_controller_only')
    require(not (ROOT / ERA / 'BOUNDARY.json').exists(), 'no_release_retry')
    namespace = dict(legacy.release_at_boundary.__globals__, MORNING=publication['not_before_unix'],
        BOUNDARY_END=min(publication['not_before_unix'] + 600, TRAIN_END), EVENT=ERA,
        event_paths=lambda branch: (ROOT, ROOT / ERA),
        completed_boundary=lambda root: boundary_snapshot(root, legacy))
    bound = FunctionType(legacy.release_at_boundary.__code__, namespace)
    return bound(dict(plan, branch='F4'))


def consumer_config(config, boundary):
    require(config['life_id'] == 'F4_FABLE' and config['parent_model'] == 'claude-fable-5-1', 'original_identity')
    require(boundary['first_new_parent'] == boundary['after_parent'] + 1
            and boundary['next_cycle'] == boundary['cycle'] + 1, 'exact_next_boundary')
    return dict(deepcopy(config), parent_model=ASTRA)


def resume(plan, publication):
    legacy = validate_native(plan, publication)
    released = read(ROOT / ERA / 'RELEASED.json')
    require(released['status'] == 'RELEASED' and released['predecessor'] == plan['predecessor']
            and not legacy.same_process(plan['predecessor']), 'old_actor_gone_before_GPU_load')
    boundary = checked(released['boundary'])
    for name in ('carry', 'ledger', 'train_complete'):
        check_hash(boundary[name])
    admission = checked(publication['resume_admission'])
    require(admission['clear'] is True and admission['scanner_euid'] == 0
            and not admission['blocking_reasons'], 'fresh_strict_admission')
    require(0 <= time.time() - publication['admission_observed_unix'] <= 120,
            'admission_freshness')
    prior = legacy.original()
    grid, unused_admission, root, config, checkpoint = prior.configure('F4')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == config['uuid'], 'same_GPU')
    require(admission['gpu']['uuid'] == config['uuid'], 'admission_same_GPU')
    require(checked(plan['references']['loaded'])['adapter'] == checkpoint['adapter'], 'same_loaded_LoRA')
    require(sha(prior.CHECKPOINT.parent / 'optimizer_rng.pt') == checkpoint['optimizer_rng_sha256'], 'preserve_AdamW_RNG_archive')
    require(not (ROOT / ERA / 'RESUME_ONCE').exists(), 'no_duplicate_native_resume')
    (ROOT / ERA / 'RESUME_ONCE').mkdir()
    from peft import PeftModel
    from gpu import orch_guided_native as native
    engine = grid.load_engine(config)
    identity = native.bridge.AdapterIdentity.from_document(checkpoint['adapter'])
    engine.model = PeftModel.from_pretrained(engine.model, identity.path, is_trainable=False,
        local_files_only=True, autocast_adapter_dtype=True)
    engine.model.requires_grad_(False)
    engine.model.eval()
    require(native.observe_adapter(engine, identity) == identity, 'same_frozen_gen1_LoRA')
    for name in ('carry', 'ledger', 'train_complete'):
        check_hash(boundary[name])
    config = consumer_config(config, boundary)
    caps = checked(plan['references']['budget'])['prospective_caps']
    grid.MAX_NATIVE, grid.MAX_PARENT = caps['NATIVE'], caps['PARENT']
    writer = grid.write
    def train_only(path, value, replace=False):
        if isinstance(value, dict) and 'messages' in value and 'status' in value:
            require(value['split'] == 'TRAIN' and not value['attached_readout'], 'TRAIN_only')
            value = dict(value, adapter=identity.document(), fork_checkpoint_sha256=prior.CHECKPOINT_SHA,
                         parent_nonblocking=True, local_optimizer_steps=0, parent_segment=ERA)
        return writer(path, value, replace=replace)
    grid.write = train_only
    life_type = prior.mailbox.life_class(grid, OLD_ERA, first_parent=boundary['first_new_parent'])
    memory, roster, cycle = grid.read(root / 'CARRY.json'), grid.read(root / 'TRAIN.json'), boundary['next_cycle']
    legacy.write(ROOT / ERA / 'RESUMED.json', dict(identity=legacy.process(os.getpid()),
        boundary=released['boundary'], next_cycle=cycle, after_parent=boundary['after_parent'],
        counts=boundary['counts'], checkpoint=plan['references']['checkpoint'], parent_model=ASTRA,
        parent_segment=ERA, old_mailbox_era=OLD_ERA, optimizer_steps=0, counter_reset=False,
        live_rng_restored=False, greedy_no_sampling=True, archived_optimizer_rng_preserved=True,
        hard_end_unix=HARD_END, observed_unix=time.time()))
    while time.time() < TRAIN_END:
        life = life_type(root, engine, config, cycle)
        tasks = [roster[(cycle - 1) % 8], roster[8 + (cycle - 1) % 8]]
        try:
            grid.train_cycle(life, tasks, memory)
        except grid.TrainWindowClosed:
            break
        memory = grid.read(root / 'CARRY.json')
        legacy.write(ROOT / ERA / f'C{cycle:04d}.json', dict(cycle=cycle, carry=grid.ref(root / 'CARRY.json'),
            ledger=grid.ref(root / 'LEDGER.jsonl'), optimizer_steps=0, parent_segment=ERA))
        cycle += 1
    legacy.write(ROOT / ERA / 'LIFE_TERMINAL.json', dict(status='TRAIN_WINDOW_ENDED', observed_unix=time.time()))


def replace_one(source, before, after):
    require(source.count(before) == 1, 'exact_existing_A4_source_site')
    return source.replace(before, after, 1)


def prospective(request, boundary, *, now, disposed=False):
    if not isinstance(request, dict) or not re.fullmatch(r'P[0-9]{4,}', request.get('id', '')):
        return False
    payload = request.get('payload', {})
    return (not disposed and int(request['id'][1:]) > boundary['after_parent']
        and payload.get('cycle', -1) >= boundary['next_cycle']
        and payload.get('phase') == 'experience' and payload.get('life_id') == 'F4_FABLE'
        and payload.get('game') == 'grid' and payload.get('task_provenance', {}).get('split') == 'TRAIN'
        and type(request.get('lane_deadline_unix')) in (int, float)
        and now < min(request['lane_deadline_unix'] - 30, TRAIN_END))


def broker_functions(http, boundary, plan, publication, plan_sha256):
    transport, astra = http.astra.transport, http.astra
    def authorized(config, receipt, now):
        authorize(plan, receipt, plan_sha256, 'broker', now)
        require(config['life_id'] == 'F4_FABLE' and config['remote_root'] == str(ROOT)
                and config['deadline_unix'] == HARD_END
                and config['max_parent_calls'] == plan['cumulative_caps']['PARENT'] - boundary['after_parent'],
                'F4_broker_identity_and_original_cap')
    strong_source = inspect.getsource(astra.existing.strong)
    for before, after in [("config['model_reasoning_effort']", "'low'"),
                          ('max_output_tokens=4096', 'max_output_tokens=1024'),
                          ('maximum_output_tokens=4096', 'maximum_output_tokens=1024'),
                          ('timeout_seconds=120', 'timeout_seconds=570'),
                          ('min(120, deadline - time.time())', 'min(570, deadline - time.time())')]:
        strong_source = replace_one(strong_source, before, after)
    runner_namespace = dict(astra.existing.strong.__globals__, parse_strong=astra.parse)
    exec(compile(strong_source, __file__ + ':existing_A4_low1024', 'exec'), runner_namespace)
    evaluator = FunctionType(http.evaluate.__code__, dict(http.evaluate.__globals__, authorize=authorized),
                             argdefs=http.evaluate.__defaults__)
    evaluator.__kwdefaults__ = http.evaluate.__kwdefaults__
    def evaluate(request, directory, deadline, **kwargs):
        transport.validate_request(request, kwargs['config'])
        require(prospective(request, boundary, now=time.time()), 'new_live_TRAIN_episode_only')
        result = evaluator(request, directory, deadline, **kwargs, runner=runner_namespace['strong'])
        result['parent_segment'] = ERA
        require(result.get('actual_model') in (None, ASTRA), 'truthful_Astra_only')
        transport.write(Path(directory) / 'SEGMENT.json', dict(segment=ERA, requested_model=ASTRA,
            actual_model=result.get('actual_model'), boundary_after_parent=boundary['after_parent'],
            historical_Claude_cap=298, historical_replay=False))
        return result
    namespace = dict(transport.process_request.__globals__, evaluate=evaluate, validate_launch=authorized)
    process_source = replace_one(inspect.getsource(transport.process_request), "root / 'parent_claude'", "root / 'parent_astra_r139'")
    exec(compile(process_source, __file__ + ':new_segment_ledger', 'exec'), namespace)
    original_process = namespace['process_request']
    def process_request(store, config, launch, name, buffer, prompt_root, principles_path):
        require(re.fullmatch(r'P[0-9]{4,}\.request\.json', name), 'numbered_request')
        identifier = name.removesuffix('.request.json')
        if int(identifier[1:]) <= boundary['after_parent']:
            return 'HISTORICAL_NO_REDISPATCH'
        if int(identifier[1:]) > plan['cumulative_caps']['PARENT']:
            return 'CUMULATIVE_CAP_EXHAUSTED'
        paths = [ROOT / folder / (identifier + suffix) for folder, suffix in (
            ('parent_claude', '.claim'), ('parent_astra_r139', '.claim'), ('parent_received', '.json'),
            ('parent_queue', '.response.json'))]
        if any(store.exists(path) for path in paths) or not store.exists(ROOT / 'parent_queue' / name):
            return 'DISPOSED_OR_MISSING_NO_REDISPATCH'
        packet = buffer / 'eligibility.json'
        try:
            require(int(store.shell('stat -c %s ' + str(ROOT / 'parent_queue' / name)).stdout) <= transport.PACKET_CAP,
                    'bounded_request_packet')
            store.copy('NODE:' + str(ROOT / 'parent_queue' / name), packet)
            require(store.hash(ROOT / 'parent_queue' / name) == sha(packet), 'immutable_request')
            request = transport.loads(packet.read_text())
            if not prospective(request, boundary, now=time.time()):
                return 'EXPIRED_OR_NON_EPISODE_NO_REDISPATCH'
        finally:
            if packet.exists():
                packet.unlink()
        return original_process(store, config, launch, name, buffer, prompt_root, principles_path)
    namespace.update(process_request=process_request)
    serve_source = replace_one(inspect.getsource(transport.serve), "root / 'parent_claude'", "root / 'parent_astra_r139'")
    serve_source = replace_one(serve_source, "root / 'TERMINAL.json'", "root / 'r139_astra_handoff_v1/LIFE_TERMINAL.json'")
    exec(compile(serve_source, __file__ + ':existing_A4_serve', 'exec'), namespace)
    return namespace['serve']


def broker_config(old, boundary, caps, source_pins):
    require(old['branch'] == 'F4' and old['family'] == 'grid' and old['life_id'] == 'F4_FABLE'
            and old['max_parent_calls'] == 298, 'original_F4_Claude_config')
    remaining = caps['PARENT'] - boundary['after_parent']
    require(boundary['after_parent'] >= 298 and remaining > 0, 'bounded_remaining_segment')
    config = deepcopy(old)
    for key in ('queue_transport', 'provider_lock_scope', 'terminal_filename'):
        config.pop(key, None)
    config.update(deadline_unix=HARD_END, max_parent_calls=remaining, source_files=source_pins)
    return config


def load_broker_runtime():
    for relative, expected in BROKER_PINS.items():
        require(sha(BROKER_RUNTIME / relative) == expected, 'pinned_A4_broker_source')
    sys.path.insert(0, str(BROKER_RUNTIME))
    from gpu import orch_r118_node3_6_grid_broker_http as http
    require(Path(http.__file__).resolve() == BROKER_RUNTIME / 'gpu/orch_r118_node3_6_grid_broker_http.py',
            'isolated_A4_import')
    return http


def broker(plan, publication, plan_sha256, publication_path):
    require(Path(plan['broker_runtime']) == BROKER_RUNTIME and plan['broker_pins'] == BROKER_PINS,
            'existing_A4_runtime')
    http = load_broker_runtime()
    transport = http.astra.transport
    store = transport.Store(BROKER_RUNTIME)
    def remote(reference_value):
        path = Path(reference_value['path'])
        require(str(path).startswith(str(ROOT) + '/') and '..' not in path.parts, 'F4_remote_reference')
        require(store.hash(path) == reference_value['sha256'], 'remote_reference_hash')
        require(int(store.shell('stat -c %s ' + shlex.quote(str(path))).stdout) <= 4 * 1024 * 1024,
                'bounded_remote_metadata')
        return transport.loads(store.shell('cat ' + shlex.quote(str(path))).stdout)
    resumed = remote(publication['resumed'])
    require(resumed['parent_model'] == ASTRA and resumed['parent_segment'] == ERA
            and resumed['counter_reset'] is False and resumed['checkpoint'] == plan['references']['checkpoint'],
            'honest_actual_consumer_ready')
    boundary = remote(resumed['boundary'])
    require(resumed['after_parent'] == boundary['after_parent'], 'boundary_consumer_join')
    old = remote(plan['references']['broker_config'])
    budget = remote(plan['references']['budget'])
    require(plan['cumulative_caps'] == budget['prospective_caps'], 'same_lease_caps')
    require(not store.exists(ROOT / 'parent_claude/RUNNER.lock'), 'old_Claude_broker_absent')
    config = broker_config(old, boundary, plan['cumulative_caps'], transport.source_pins())
    transport.validate_config(config)
    folder = Path(publication_path).parent
    config_path = folder / 'F4_ASTRA_CONFIG.json'
    if config_path.exists():
        require(read(config_path) == config, 'immutable_staged_broker_config')
    else:
        transport.write(config_path, config)
    serving = broker_functions(http, boundary, plan, publication, plan_sha256)
    serving(config_path, publication_path, Path('/data/home/rohing/courier/swarm/prompts'),
            BROKER_RUNTIME / 'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('stage', 'check-broker', 'release', 'resume', 'broker'))
    parser.add_argument('--expected-self-sha256', required=True)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--plan-sha256')
    parser.add_argument('--publication', type=Path)
    args = parser.parse_args()
    require(sha(__file__) == args.expected_self_sha256, 'immutable_command')
    if args.mode == 'stage':
        print(json.dumps(stage(), sort_keys=True, indent=2))
        return
    if args.mode == 'check-broker':
        http = load_broker_runtime()
        bound = broker_functions(http, dict(after_parent=319, next_cycle=106),
                                 dict(cumulative_caps=dict(PARENT=404430)), {}, 'CPU_ONLY')
        require(callable(bound) and callable(bound.__globals__['process_request']), 'A4_adapter_compiles')
        print(json.dumps(dict(status='CPU_COMPILED_NO_DISPATCH', source_sha256=sha(__file__),
            original_A4_pins=BROKER_PINS, provider_calls=0, claims_created=0, runtime_mutated=False), sort_keys=True))
        return
    require(args.plan is not None and args.publication is not None and sha(args.plan) == args.plan_sha256,
            'explicit_plan_and_Main_publication')
    plan, publication = read(args.plan), read(args.publication)
    authorize(plan, publication, args.plan_sha256, args.mode, time.time())
    if args.mode == 'broker':
        broker(plan, publication, args.plan_sha256, args.publication)
    else:
        globals()[args.mode](plan, publication)


if __name__ == '__main__':
    main()
