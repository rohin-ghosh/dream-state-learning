"""Exact-slot, new-context BASE forks; preparation never invokes a model or parent."""

import argparse
import fcntl
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from types import SimpleNamespace


LANE = 'node1_7'
VERSION = 'overflow_r135_v2'
LABEL = 'R135_CHANGED_CONTEXT_FORK_V1'
HOST_SHA = 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
DEPENDENCY = Path('/localhome/local-rohing/orch_r118_node1_route_source')
SOURCE_TREE = Path('/localhome/local-rohing/orch_r109_route_20260915_node1_7_attempt2/source')
MANIFEST_SHA = '4a6a50b6b7594bdeabd541bef1e963c48fbd1deb21fd032bc13db630a51dec67'
MODEL = '/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28'
DEPENDENCY_PINS = {
    'gpu/orch_r111_route_recovery.py': '2b96471dbb7dbfde4ca749250a21828b04643257eae217a9aa9a49b5649102c4',
    'gpu/orch_r109_route_run.py': '95b7be9f76e5a31549264b11c16ff84561e237d6d30ddf94d10138fe34341496',
    'gpu/orch_r109_route_engine.py': '84c8963dea72183549a12662de69874f25345819bc78f9ed5b7bd4634a4667bd',
    'gpu/orch_r109_route_scan.py': '3e88ae5dc3ac7e0bede7200c59b969fa7682a7fad391ca993d91cccaaad65f34',
    'gpu/orch_math_pipeline_l2_run.py': '552701099e3fe4fe4994a13a0f52ce71a112f32a858a382b51c66468c55acaa3',
    'organism_v6/orch_r109_route.py': '8727c558770bf8b2afbd27b88277cd8291a4607cade7f6e1b9491bc207a41555',
}
SLOTS = {
    0: dict(root='/localhome/local-rohing/orch_r109_route_20260915_node1_7_attempt2',
        prior_version='overflow_r129_v1', uuid='GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d',
        cycle=53, native=2047, parent=112, disposition='COMPLETE', checkpoint=52,
        ready_sha='d0769d1863a7a62d76ef003635e065d49cacbf9a6ff0af8d3691f88236d47e60',
        failed_sha='a444489a8a101a9e0770f5617c59643b445b0d227d209ba7ffd4f26211fe01ad',
        terminal_sha='ff246b289d8545025db73c04190dc8de25b7b70bd5f12e9cb96260f624196447',
        ledger_sha='8687dd2a77cbabc0a34f6a9cca9fb6b8d62b483731155e2b281ca70112de3b85',
        call_sha='3df2ad19cb98d4fd519f9b9e31e07bfd908d078325c6c920dfbccebb0f397ba2',
        relocation_sha='2822202db4dec37c41b8d23aec3a08ad48e9e5fa04ae9193e42a76e3713e97d1'),
    2: dict(root='/localhome/local-rohing/orch_r109_route_20260915_r120_C39_fork_a40r2_attempt1',
        prior_version='lease_r120_v2', uuid='GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8',
        cycle=60, native=2328, parent=127, disposition='MISSING', checkpoint=59,
        ready_sha='494343a40016af7c82ba75b502b3bb10472393620e08b361aa71d6075db31342',
        failed_sha='bb1ebd18cf3b247beaa38da02e3333c53eb09d8063e5383a34b20bc97ee8fbc4',
        terminal_sha='10df8537935186b5e9226b5c9d58df056edf22a2341e98dde0d5268a5564e03c',
        ledger_sha='526a7bb2f9e763ccdee2e5843d32a69a4bd61afec0946d9c3c704ce8e72c0e9d',
        call_sha='cd13679ed408347bcda97d70982f6b07869a3037432d1ad36c777cd2aa075abe',
        relocation_sha='4aaea73fa64cb35d26430fc45c00716bfb356f27cd9b714a14b73257e6106759'),
}
COUNTERS = ('native_completed', 'parent_completed', 'parent_missing', 'train_segments',
    'train_episodes', 'held_episodes', 'sleeps', 'optimizer_updates', 'triples', 'semantic_verified_changes')
NOTICE = ('R135 CHANGED-CONTEXT FORK: The complete latest actual child reflection follows verbatim. '
    'All preceding context is archived node-local, not summarized or tail-clipped. '
    'This is not an exact-context continuation. The final user message preserves the actual '
    'parent disposition, including empty advice after a missing parent.\nPending reflection instruction:\n')


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def ref(path):
    return dict(path=str(path), sha256=sha(path))


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def slot(physical):
    require(type(physical) is int and physical in SLOTS, 'exact_physical_0_or_2')
    return SLOTS[physical]


def directory(physical, root=None, lane=LANE):
    expected = Path(slot(physical)['root'])
    require((root is None or Path(root) == expected) and lane == LANE, 'exact_slot_root_lane')
    return expected / VERSION / ('campaign_' + LANE)


def validate_scope(physical, host_sha, inventory, relocation):
    config = slot(physical)
    require(host_sha == HOST_SHA, 'exact_a40r_host_hash')
    require(inventory == dict(physical=physical, uuid=config['uuid']), 'exact_physical_uuid_join')
    require(relocation['target_physical'] == physical and relocation['target_uuid'] == config['uuid']
        and relocation['target_wrapper'] == 'gpu/a40r_ssh.sh', 'exact_slot_relocation')


def scope(physical):
    config = slot(physical)
    root = Path(config['root'])
    require(root.resolve() == root, 'canonical_slot_root')
    require(directory(physical).resolve() == directory(physical), 'canonical_output_no_symlink')
    host_sha = hashlib.sha256(socket.gethostname().encode()).hexdigest()
    require(host_sha == HOST_SHA, 'exact_a40r_host_hash')
    path = root / 'lease_r120_v2/RELOCATION.json'
    require(sha(path) == config['relocation_sha'], 'frozen_slot_relocation')
    lines = subprocess.check_output(['nvidia-smi', '--id=' + str(physical),
        '--query-gpu=index,uuid', '--format=csv,noheader,nounits'], text=True).strip().splitlines()
    require(len(lines) == 1, 'single_slot_inventory')
    index, uuid = [part.strip() for part in lines[0].split(',')]
    validate_scope(physical, host_sha, dict(physical=int(index), uuid=uuid), read(path))
    return config


def validate_cursor(physical, rows, failed):
    config = slot(physical)
    require(failed['native_completed'] == config['native'] and failed['optimizer_updates'] == 0,
        'exact_failed_BASE_counters')
    require(all(row['kind'] in ('NATIVE', 'PARENT') and row['lane'] == LANE for row in rows),
        'only_original_lane_reservations')
    for kind, last in [('NATIVE', config['native']), ('PARENT', config['parent'])]:
        selected = [row for row in rows if row['kind'] == kind]
        require([row['number'] for row in selected] == list(range(1, last + 1)),
            'exact_charged_sequence_no_new_intent')
        require(selected[-1]['cycle'] == config['cycle'], 'exact_pending_cycle')
    require(max(row['cycle'] for row in rows) == config['cycle'], 'no_later_cycle')
    return {key: failed[key] for key in COUNTERS}


def validate_ready(ready, now):
    require(ready['learned'] is False and ready['base']['verified'] is True
        and ready['base']['expected_base_sha256'] == BASE_SHA and ready['model_dir'] == MODEL
        and ready['base']['model_dir'] == MODEL, 'original_frozen_BASE_no_adapter')
    require((ready['context'], ready['output_cap'], ready['native_cap'], ready['parent_cap'],
        ready['cycles'], ready['reflection_turns']) == (32768, 8192, 16384, 640, 256, 2),
        'original_context_caps_cycles_turns')
    require((ready['native_deadline_unix'], ready['hard_deadline_unix'], ready['lease_end_unix'])
        == (1789754280.0, 1789754400.0, 1789776000.0), 'original_absolute_deadlines')
    require(now < ready['native_deadline_unix'], 'unexpired_native_deadline')


def compact_context(physical, call, request, receipt, response=None):
    config = slot(physical)
    require(call['status'] == 'COMPLETE' and call['purpose'] == 'reflection'
        and call['cycle'] == config['cycle'] and call['number'] == config['native']
        and call['task_id'] == f"TRAIN-REFLECTION-{config['cycle']}-1"
        and call['adapter_state'] is None and call['base_sha256'] == BASE_SHA,
        'actual_latest_completed_BASE_reflection')
    require(call['response']['input_truncated'] is False
        and call['response']['full_prompt_prefix_verified'] is True, 'actual_full_child_prefix')
    payload = request['payload']
    require(payload['split'] == 'TRAIN' and payload['cycle'] == config['cycle']
        and payload['turn'] == 2 and payload['mode'] == 'METACOGNITION_CONVERSATION',
        'exact_pending_TRAIN_turn_two')
    require(receipt['number'] == config['parent'] and receipt['cycle'] == config['cycle']
        and receipt['turn'] == 2 and receipt['status'] == config['disposition'], 'actual_parent_disposition')
    messages = payload['messages']
    raw = call['response']['raw']
    require(isinstance(raw, str) and raw, 'whole_actual_child_reflection')
    require(messages[-1] == dict(role='assistant', content=raw)
        and messages[:-1] == call['response']['messages'], 'exact_causal_prefix_join')
    require(messages[0]['role'] == 'system' and messages[1]['role'] == 'user', 'original_system_instruction')
    instruction = json.loads(messages[1]['content'])['focus']
    require(isinstance(instruction, str) and instruction, 'original_pending_instruction')
    advice = ''
    if config['disposition'] == 'COMPLETE':
        require(response is not None and response['status'] == 'COMPLETE', 'consumed_parent_only')
        task = payload['episodes'][0]['task_id']
        advice = response['plan']['guidance'] + '\n' + response['plan']['episode_guidance'][task]
    compact = [dict(messages[0]), dict(role='user', content=NOTICE + instruction),
        dict(role='assistant', content=raw), dict(role='user', content=advice)]
    return dict(messages=compact, full_pending_messages=messages + [dict(role='user', content=advice)],
        advice=advice, parent_receipt=receipt, context_changed=True, compiler_summary=False,
        identical_context_claim=False, full_child_retained=True, late_parent_consumed=False)


def token_fit(tokenizer, carry):
    tokens = tokenizer.apply_chat_template(carry['messages'], tokenize=True,
        add_generation_prompt=True, return_dict=False)
    require(0 < len(tokens) < 32768, 'whole_compact_prompt_must_fit_no_clipping')
    return dict(prompt_tokens=len(tokens), context_limit=32768,
        effective_output_cap=min(8192, 32768 - len(tokens)), input_truncated=False,
        full_child_retained=True, model_calls=0, parent_calls=0)


def dependencies():
    require(DEPENDENCY.resolve() == DEPENDENCY, 'canonical_frozen_dependency')
    for relative, expected in DEPENDENCY_PINS.items():
        require(sha(DEPENDENCY / relative) == expected, 'unchanged_dependency_policy_source')


def original_source_tree(root):
    require((root / 'source').resolve() == SOURCE_TREE and SOURCE_TREE.resolve() == SOURCE_TREE,
        'exact_original_shared_source_target')
    for relative, expected in read(root / 'SOURCE_SHA256.json').items():
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts,
            'relative_original_source_file')
        path = root / 'source' / relative
        require(path.resolve() == SOURCE_TREE / relative and sha(path) == expected,
            'original_source_unchanged')


def runtime(physical):
    config = scope(physical)
    dependencies()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(DEPENDENCY))
    for package_name in ('gpu', 'organism_v6'):
        package = __import__(package_name)
        package.__path__ = [str(DEPENDENCY / package_name)] + list(package.__path__)
    source = DEPENDENCY / 'gpu/orch_r111_route_recovery.py'
    spec = importlib.util.spec_from_file_location('r135_frozen_route_recovery', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for relative in DEPENDENCY_PINS:
        module_name = relative[:-3].replace('/', '.')
        if module_name in sys.modules:
            require(Path(sys.modules[module_name].__file__).resolve() == DEPENDENCY / relative,
                'no_import_shadowing')
    policy = module.old.policy
    require(policy.HOSTS['node1']['sha256'] == HOST_SHA and policy.BASE_SHA == BASE_SHA
        and not policy.LANES[LANE]['learned'] and policy.CONTEXT == 32768,
        'unchanged_host_BASE_policy')
    policy.LANES[LANE] = dict(policy.LANES[LANE], host='node1', physical=physical, uuid=config['uuid'])
    policy.DEVICES[LANE] = config['uuid']
    module.directory = lambda root, lane: directory(physical, root, lane)
    return module


def fresh_evidence(physical):
    config = scope(physical)
    root = Path(config['root'])
    prior = root / config['prior_version'] / ('campaign_' + LANE)
    require(prior.resolve() == prior, 'canonical_failed_campaign')
    paths = []
    for name, expected in [('READY.json', config['ready_sha']), ('FAILED.json', config['failed_sha']),
            ('TERMINAL.json', config['terminal_sha']),
            (f"native/CALL_{config['native']:06d}.json", config['call_sha'])]:
        path = prior / name
        require(sha(path) == expected, 'exact_diagnosed_failed_artifact')
        paths.append(path)
    require(read(prior / 'FAILED.json')['error'] == dict(type='ValueError', message='uncropped_context_fit')
        and read(prior / 'TERMINAL.json')['status'] == 'FAILED', 'exact_failed_context_boundary')
    require(read(prior / f"CHECKPOINT_C{config['checkpoint']}.json")['adapter'] is None,
        'prior_checkpoint_no_adapter')
    for name in ('LAUNCH.json', 'GUARD_LAUNCH.json'):
        launch = read(prior / name)
        require(not Path('/proc', str(launch['pid'])).exists(), 'prior_receipt_owner_absent')
        paths.append(prior / name)
    require(read(prior / 'LAUNCH.json')['uuid'] == config['uuid'], 'prior_native_slot_join')
    ledger = (root / 'RESERVATIONS.jsonl').read_bytes()
    require(hashlib.sha256(ledger).hexdigest() == config['ledger_sha'], 'no_intervening_reservations')
    rows = [json.loads(line) for line in ledger.splitlines() if line.strip()]
    counters = validate_cursor(physical, rows, read(prior / 'FAILED.json'))
    require(not list(root.glob(f"**/native/CALL_{config['native'] + 1:06d}.json")),
        'no_prior_next_call_any_campaign')
    ready = read(prior / 'READY.json')
    validate_ready(ready, time.time())
    require(sha(root / 'SOURCE_SHA256.json') == MANIFEST_SHA, 'original_source_manifest')
    original_source_tree(root)
    for relative, expected in ready['files'].items():
        path = root / relative
        require(path.resolve().is_relative_to(root) and sha(path) == expected, 'original_ready_file_binding')
        paths.append(path)
    request_path = prior / 'parent_queue' / f"GUIDED_SLEEP_C{config['cycle']}_P{config['parent']}.request.json"
    receipt_path = prior / f"PARENT_{config['parent']:05d}.json"
    request, receipt = read(request_path), read(receipt_path)
    require(receipt['request_sha256'] == sha(request_path), 'actual_parent_request_join')
    response = None
    paths += [request_path, receipt_path, prior / f"CHECKPOINT_C{config['checkpoint']}.json",
        root / 'SOURCE_SHA256.json', root / 'lease_r120_v2/RELOCATION.json']
    if config['disposition'] == 'COMPLETE':
        response_path = request_path.with_name(request_path.name.replace('.request.', '.response.'))
        response = read(response_path)
        require(receipt['response_sha256'] == sha(response_path)
            and response['request_sha256'] == sha(request_path) and receipt['archive'] == response['archive'],
            'consumed_parent_response_join')
        archive = Path(response['archive']['remote_root'])
        require(archive.resolve() == archive and archive.is_relative_to(root / 'parent_transcripts'),
            'own_consumed_parent_archive')
        for name, expected in response['archive']['files'].items():
            require(Path(name).name == name and sha(archive / name) == expected, 'consumed_parent_archive_hash')
            paths.append(archive / name)
        require(response['plan'] == read(archive / 'PLAN.json'), 'actual_delivered_plan')
        paths += [response_path, archive / 'PLAN.json']
    call = read(prior / f"native/CALL_{config['native']:06d}.json")
    carry = compact_context(physical, call, request, receipt, response)
    for pattern in (f"native/TRAIN*C{config['cycle']}*.json", 'CARRY.json', 'EPOCH.json', 'RECOVERY.json'):
        paths.extend(prior.glob(pattern))
    return dict(prior=prior, ready=ready, carry=carry, counters=counters, ledger_bytes=len(ledger),
        references=[ref(path) for path in sorted(set(paths))])


def prepare(physical):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_prepare')
    output = directory(physical)
    require(not output.exists(), 'new_epoch_only_no_overwrite')
    source_root = Path(__file__).resolve().parents[1]
    test_receipt = source_root / 'CPU_TESTS.json'
    tested = read(test_receipt)
    require(tested['exit_code'] == 0 and tested['source_sha256'] == sha(Path(__file__).resolve())
        and tested['tests_sha256'] == sha(source_root / 'tests/test_orch_r135_a40r_context_epoch.py'),
        'current_source_CPU_regression_tests_required')
    module = runtime(physical)
    compile(native_source(inspect.getsource(module.old.native), physical), 'R135_CPU_native_seam', 'exec')
    evidence = fresh_evidence(physical)
    module.old.verify(Path(slot(physical)['root']), LANE)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(evidence['ready']['model_dir'], local_files_only=True,
        trust_remote_code=False)
    fit = token_fit(tokenizer, evidence['carry'])
    tokenizer_files = [ref(path) for path in sorted(Path(MODEL).glob('*'))
        if path.name in ('tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json',
            'vocab.json', 'merges.txt', 'added_tokens.json')]
    require(tokenizer_files, 'local_tokenizer_provenance')
    frozen = evidence['references'] + [ref(path) for path in sorted(DEPENDENCY.rglob('*.py'))]
    frozen += [ref(test_receipt), ref(source_root / 'tests/test_orch_r135_a40r_context_epoch.py')]
    require(sha(Path(slot(physical)['root']) / 'RESERVATIONS.jsonl') == slot(physical)['ledger_sha'],
        'no_intervening_reservations_during_prepare')
    output.mkdir(parents=True, exist_ok=False)
    (output / 'parent_queue').mkdir()
    with (output / 'READY.json').open('xb') as stream:
        stream.write((evidence['prior'] / 'READY.json').read_bytes())
    archive = dict(full_pending_messages=evidence['carry'].pop('full_pending_messages'),
        original_evidence=evidence['references'], prior_campaign=str(evidence['prior']),
        all_previous_context_preserved_node_local=True)
    write(output / 'ARCHIVE_CONTEXT.json', archive)
    write(output / 'CARRY.json', evidence['carry'])
    config = slot(physical)
    epoch = dict(schema=LABEL, physical=physical, uuid=config['uuid'], host_sha256=HOST_SHA,
        root=config['root'], source=ref(Path(__file__).resolve()), dependency_root=str(DEPENDENCY),
        frozen_references=frozen, tokenizer_files=tokenizer_files, ready=ref(output / 'READY.json'),
        carry=ref(output / 'CARRY.json'), archive=ref(output / 'ARCHIVE_CONTEXT.json'),
        counters=evidence['counters'], ledger_sha256=config['ledger_sha'], ledger_bytes=evidence['ledger_bytes'],
        first_unreserved_native=config['native'] + 1, next_parent_number=config['parent'] + 1,
        pending_cycle=config['cycle'], pending_turn=2, parent_disposition=config['disposition'],
        no_adapter=True, optimizer_updates=0, identical_context_claim=False, context_changed=True,
        previous_policy_unchanged=True, rng_restoration='NOT_AVAILABLE_DECLARED_NEW_CONTEXT_FORK',
        token_fit=fit, created_unix=time.time())
    write(output / 'EPOCH.json', epoch)
    receipt = dict(schema=LABEL, physical=physical, uuid=config['uuid'], host_sha256=HOST_SHA,
        epoch=ref(output / 'EPOCH.json'), ready=epoch['ready'], carry_sha256=epoch['carry']['sha256'],
        archive_sha256=epoch['archive']['sha256'], first_unreserved_native=epoch['first_unreserved_native'],
        next_parent_number=epoch['next_parent_number'], pending_cycle=config['cycle'], pending_turn=2,
        parent_disposition=config['disposition'], counters=epoch['counters'], token_fit=fit,
        context_changed=True, identical_context_claim=False, launch_authorized=False)
    write(output / 'CPU_PREPARATION.json', receipt)
    verify(physical)
    return receipt


def verify(physical, pristine=False):
    config = scope(physical)
    dependencies()
    output = directory(physical)
    epoch = read(output / 'EPOCH.json')
    require(epoch['schema'] == LABEL and epoch['physical'] == physical and epoch['uuid'] == config['uuid']
        and epoch['host_sha256'] == HOST_SHA and epoch['root'] == config['root'], 'exact_epoch_slot')
    prior = Path(config['root']) / config['prior_version'] / ('campaign_' + LANE)
    require(sha(prior / 'FAILED.json') == config['failed_sha'], 'exact_failed_counter_source')
    failed = read(prior / 'FAILED.json')
    require(epoch['counters'] == {key: failed[key] for key in COUNTERS}
        and epoch['first_unreserved_native'] == config['native'] + 1
        and epoch['next_parent_number'] == config['parent'] + 1
        and epoch['pending_cycle'] == config['cycle'] and epoch['pending_turn'] == 2
        and epoch['parent_disposition'] == config['disposition']
        and epoch['ledger_sha256'] == config['ledger_sha'] and epoch['no_adapter'] is True
        and epoch['optimizer_updates'] == 0 and epoch['identical_context_claim'] is False
        and epoch['context_changed'] is True, 'unchanged_failed_cursor_and_fork_contract')
    prepared = read(output / 'CPU_PREPARATION.json')
    require(prepared['epoch'] == ref(output / 'EPOCH.json') and prepared['token_fit'] == epoch['token_fit'],
        'CPU_preparation_epoch_binding')
    require(epoch['source'] == ref(Path(__file__).resolve()), 'frozen_epoch_source')
    for pointer in epoch['frozen_references'] + epoch['tokenizer_files'] + [epoch['ready'], epoch['carry'], epoch['archive']]:
        require(ref(pointer['path']) == pointer, 'frozen_provenance_changed')
    require(sha(output / 'READY.json') == config['ready_sha'], 'original_ready_bytes')
    validate_ready(read(output / 'READY.json'), time.time())
    ledger = (Path(config['root']) / 'RESERVATIONS.jsonl').read_bytes()
    require(hashlib.sha256(ledger[:epoch['ledger_bytes']]).hexdigest() == config['ledger_sha'],
        'unchanged_charged_ledger_prefix')
    if pristine:
        require(hashlib.sha256(ledger).hexdigest() == config['ledger_sha'], 'no_intervening_reservations')
        fresh_evidence(physical)
    return epoch


def replace_once(source, old, new):
    require(source.count(old) == 1, 'exact_frozen_native_seam')
    return source.replace(old, new)


def native_source(source, physical):
    cycle = slot(physical)['cycle']
    source = replace_once(source, "campaign=root/('campaign_'+lane)", 'campaign=epoch_directory(root,lane)')
    source = replace_once(source, '    def status(phase):', '    epoch_restore(counters,state)\n    def status(phase):')
    source = replace_once(source, "counters['parent_completed']+=1",
        "counters['parent_completed' if receipt['status']=='COMPLETE' else 'parent_missing']+=1")
    source = replace_once(source, 'for cycle in range(1,policy.CYCLES+1):', f'for cycle in range({cycle},policy.CYCLES+1):')
    start_marker = "            group=frozen['train'][cycle-1]"
    end_marker = "            status('SLEEP')"
    require(source.count(start_marker) == source.count(end_marker) == 1, 'exact_pending_cycle_seam')
    start, end = source.index(start_marker), source.index(end_marker)
    require(start < end, 'ordered_pending_cycle_seam')
    original = source[start:end]
    pending = f"""            if cycle == {cycle}:
                pending = epoch_carry()
                state['pending_parent'] = pending['parent_receipt']
                state['advice'] = pending['advice']
                response = generate(pending['messages'],'reflection','TRAIN-REFLECTION-{cycle}-2',{cycle},2)
                state['memory'] = response['raw']
                write(output/'CONVERSATION_C{cycle}.json',dict(messages=pending['messages']+[dict(role='assistant',content=response['raw'])],
                    turns=2,completed_prior_turn_replayed=False,context_epoch='{LABEL}',
                    identical_context_claim=False,original_full_context=epoch_archive_reference()))
            else:
"""
    source = source[:start] + pending + ''.join('    ' + line if line.strip() else line
        for line in original.splitlines(True)) + source[end:]
    return replace_once(source, 'started_unix=time.time(),phase_version=policy.VERSION,base_sha256=policy.BASE_SHA,',
        f"started_unix=time.time(),phase_version=policy.VERSION,base_sha256=policy.BASE_SHA,context_epoch='{LABEL}',identical_context_claim=False,")


def publication(physical):
    epoch = verify(physical)
    output = directory(physical)
    document = read(output / 'PUBLICATION.json')
    require(document['epoch_sha256'] == sha(output / 'EPOCH.json')
        and document['ready_sha256'] == sha(output / 'READY.json')
        and document['allocation_sha256'] == sha(output / 'ALLOCATION.md')
        and document['dated_builder_publication'] is True
        and document['source_sha256'] == epoch['source']['sha256'], 'Main_publication_required')
    return epoch


def first_native_reserver(module, physical):
    config = slot(physical)
    first = True

    def reserve(root, lane, kind, detail):
        nonlocal first
        directory(physical, root, lane)
        if not first:
            return module.old.reserve(root, lane, kind, detail)
        require(kind == 'NATIVE' and detail == dict(cycle=config['cycle'], purpose='reflection',
            task_id=f"TRAIN-REFLECTION-{config['cycle']}-2"), 'only_unreserved_pending_turn_first')
        with (root / 'RESERVATIONS.jsonl').open('r+') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            stream.seek(0)
            require(hashlib.sha256(stream.read().encode()).hexdigest() == config['ledger_sha'],
                'first_reservation_atomic_unchanged_ledger')
            require(not list(root.glob(f"**/native/CALL_{config['native'] + 1:06d}.json")),
                'first_reservation_no_existing_call')
            require(config['native'] < module.old.policy.NATIVE_CAP, 'original_native_cap')
            intent = dict(lane=lane, kind=kind, number=config['native'] + 1,
                reserved_unix=time.time(), **detail)
            stream.write(json.dumps(intent, sort_keys=True) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        first = False
        return intent

    return reserve


def native(physical):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == slot(physical)['uuid'], 'exact_native_uuid_cvd')
    module = runtime(physical)
    epoch = verify(physical, pristine=True)
    publication(physical)
    carry = read(directory(physical) / 'CARRY.json')

    def restore(counters, state):
        counters.update(epoch['counters'])
        state.update(memory=carry['messages'][2]['content'], old_rows=[])

    namespace = dict(module.old.native.__globals__, parent=module.parent,
        verify=lambda root, lane: verify(physical), epoch_directory=module.directory,
        epoch_restore=restore, epoch_carry=lambda: carry, epoch_archive_reference=lambda: epoch['archive'],
        reserve=first_native_reserver(module, physical))
    with (directory(physical) / 'NATIVE_ONCE').open('x'):
        exec(compile(native_source(inspect.getsource(module.old.native), physical),
            __file__ + ':epoch_native', 'exec'), namespace)
        namespace['native'](Path(slot(physical)['root']), LANE)


def scan(physical):
    require(os.geteuid() == 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'privileged_CPU_scan')
    module = runtime(physical)
    verify(physical)
    service = directory(physical) / 'SERVICE_IDENTITY.json'
    if not service.exists():
        module.old.admission.node1.service(service)
    result = module.old.admission.scan(LANE, service)
    require(result['host_sha256'] == HOST_SHA and result['gpu']['index'] == physical
        and result['gpu']['uuid'] == slot(physical)['uuid'], 'exact_scanner_slot_join')
    return result


def guard(physical):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_guard_only')
    module = runtime(physical)
    verify(physical, pristine=True)
    publication(physical)
    source = replace_once(inspect.getsource(module.old.guard),
        "campaign=root/('campaign_'+lane)", 'campaign=epoch_directory(root,lane)')
    source = source.replace("root/'ALLOCATION.md'", "campaign/'ALLOCATION.md'")
    source = replace_once(source, "'gpu.orch_r109_route_run','native','--root',str(root),'--lane',lane",
        f"'gpu.orch_r135_a40r_context_epoch','native','--physical','{physical}'")
    source = source.replace("root/'source'", 'epoch_source_root')

    def admission(lane, service):
        result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            sys.executable, '-B', str(Path(__file__).resolve()), 'scan', '--physical', str(physical)],
            capture_output=True, text=True, check=True, timeout=100)
        return json.loads(result.stdout)

    namespace = dict(module.old.guard.__globals__, verify=lambda root, lane: verify(physical),
        epoch_directory=module.directory, epoch_source_root=Path(__file__).resolve().parents[1],
        admission=SimpleNamespace(scan=admission))
    with (directory(physical) / 'OWNER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (directory(physical) / 'GUARD_ONCE').mkdir()
        exec(compile(source, __file__ + ':epoch_guard', 'exec'), namespace)
        namespace['guard'](Path(slot(physical)['root']), LANE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'verify', 'native', 'guard', 'scan'))
    parser.add_argument('--physical', type=int, choices=tuple(SLOTS), required=True)
    arguments = parser.parse_args()
    if arguments.phase == 'verify':
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_verify')
        epoch = verify(arguments.physical, pristine=True)
        print(json.dumps(dict(schema=LABEL, physical=arguments.physical, verified=True,
            epoch=ref(directory(arguments.physical) / 'EPOCH.json'), token_fit=epoch['token_fit']), sort_keys=True))
    else:
        result = globals()[arguments.phase](arguments.physical)
        if result is not None:
            print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
