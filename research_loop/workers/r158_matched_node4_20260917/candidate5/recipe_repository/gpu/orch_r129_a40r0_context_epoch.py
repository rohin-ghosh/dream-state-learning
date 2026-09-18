"""Explicit changed-context BASE epoch; never replay the completed C52 prefix."""

import argparse
import fcntl
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace


ROOT = Path('/localhome/local-rohing/orch_r109_route_20260915_node1_7_attempt2')
LANE = 'node1_7'
VERSION = 'overflow_r129_v1'
UUID = 'GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d'
NOTICE = ('R129 OVERFLOW_CONTEXT_DISTILLATION: This is an explicitly changed-context epoch. '
    'Your complete most recent child-authored reflection is retained verbatim in the assistant message. '
    'The full earlier context remains archived but is not included here. No compiler summary replaces it. '
    'Continue the pending reflection with the already-delivered parent guidance. '
    'This is not an identical-context continuation.\nPending reflection instruction:\n')


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    return dict(path=str(path), sha256=sha(path))


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def directory(root=ROOT, lane=LANE):
    require(Path(root) == ROOT and lane == LANE, 'only_a40r0')
    return Path(root) / VERSION / ('campaign_' + lane)


def compact_context(call, request, response):
    payload = request['payload']
    require(call['status'] == 'COMPLETE' and call['purpose'] == 'reflection' and call['cycle'] == 52,
        'actual_completed_C52_child_reflection')
    require(payload['split'] == 'TRAIN' and payload['cycle'] == 52 and payload['turn'] == 2
        and payload['mode'] == 'METACOGNITION_CONVERSATION', 'exact_pending_TRAIN_reflection')
    messages = payload['messages']
    require(messages[-1] == dict(role='assistant', content=call['response']['raw']), 'full_actual_child_carry')
    require(messages[:-1] == call['response']['messages'], 'actual_causal_prefix')
    require(response['status'] == 'COMPLETE', 'already_delivered_parent_only')
    instruction = json.loads(messages[1]['content'])['focus']
    require(isinstance(instruction, str) and instruction, 'pending_instruction')
    plan = response['plan']
    task = payload['episodes'][0]['task_id']
    advice = plan['guidance'] + '\n' + plan['episode_guidance'][task]
    compact = [dict(messages[0]), dict(role='user', content=NOTICE + instruction),
        dict(role='assistant', content=call['response']['raw']), dict(role='user', content=advice)]
    require(compact[2]['content'] == call['response']['raw'], 'no_child_truncation')
    return dict(messages=compact, full_pending_messages=messages + [dict(role='user', content=advice)],
        advice=advice, instruction=instruction, context_changed=True, compiler_summary=False)


def validate_cursor(rows, failed):
    require(failed['native_completed'] == 2005 and failed['optimizer_updates'] == 0, 'actual_BASE_counter_carry')
    native = [row['number'] for row in rows if row['kind'] == 'NATIVE']
    parents = [row['number'] for row in rows if row['kind'] == 'PARENT']
    require(native == list(range(1, 2006)) and parents == list(range(1, 111)), 'exact_original_charges_no_2006')
    require(max(row['cycle'] for row in rows) == 52, 'same_pending_cycle')
    return {key: failed[key] for key in ('native_completed', 'parent_completed', 'parent_missing',
        'train_segments', 'train_episodes', 'held_episodes', 'sleeps', 'optimizer_updates', 'triples',
        'semantic_verified_changes')}


def replace_once(source, old, new):
    require(source.count(old) == 1, 'exact_native_source_seam')
    return source.replace(old, new)


def native_source(source):
    source = replace_once(source, "campaign=root/('campaign_'+lane)", 'campaign=epoch_directory(root,lane)')
    source = replace_once(source, '    def status(phase):', '    epoch_restore(counters,state)\n    def status(phase):')
    source = replace_once(source, "counters['parent_completed']+=1", "counters['parent_completed' if receipt['status']=='COMPLETE' else 'parent_missing']+=1")
    source = replace_once(source, 'for cycle in range(1,policy.CYCLES+1):', 'for cycle in range(52,policy.CYCLES+1):')
    start = source.index("            group=frozen['train'][cycle-1]")
    end = source.index("            status('SLEEP')", start)
    original = source[start:end]
    pending = """            if cycle == 52:
                pending = epoch_carry()
                state['pending_parent'] = pending['parent_receipt']
                state['advice'] = pending['advice']
                response = generate(pending['messages'],'reflection','TRAIN-REFLECTION-52-2',52,2)
                state['memory'] = response['raw']
                write(output/'CONVERSATION_C52.json',dict(messages=pending['messages']+[dict(role='assistant',content=response['raw'])],
                    turns=2,completed_prior_turn_replayed=False,context_epoch='R129_OVERFLOW_CONTEXT_DISTILLATION',
                    identical_context_claim=False,original_full_context=epoch_carry_reference()))
            else:
"""
    source = source[:start] + pending + ''.join('    ' + line if line.strip() else line for line in original.splitlines(True)) + source[end:]
    source = replace_once(source, "started_unix=time.time(),phase_version=policy.VERSION,base_sha256=policy.BASE_SHA,",
        "started_unix=time.time(),phase_version=policy.VERSION,base_sha256=policy.BASE_SHA,context_epoch='R129_OVERFLOW_CONTEXT_DISTILLATION',identical_context_claim=False,")
    return source


def runtime(dependency_root, relocation_path=None):
    source = Path(dependency_root) / 'gpu/orch_r111_route_recovery.py'
    sys.path.insert(0, str(Path(dependency_root)))
    import gpu
    gpu.__path__ = [str(source.parent)] + list(gpu.__path__)
    spec = importlib.util.spec_from_file_location('r129_frozen_route_recovery', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    relocation = read(relocation_path or ROOT / 'lease_r120_v2/RELOCATION.json')
    require(relocation['target_physical'] == 0 and relocation['target_uuid'] == UUID
        and relocation['target_wrapper'] == 'gpu/a40r_ssh.sh', 'exact_owned_relocation')
    policy = module.old.policy
    policy.LANES[LANE] = dict(policy.LANES[LANE], host='node1', physical=0, uuid=UUID)
    policy.DEVICES[LANE] = UUID
    require(not policy.LANES[LANE]['learned'] and policy.CONTEXT == 32768, 'unchanged_BASE_context')
    module.directory = directory
    return module


def verify(module):
    module.old.verify(ROOT, LANE)
    epoch = read(directory() / 'EPOCH.json')
    require(epoch['source'] == ref(Path(__file__).resolve()), 'frozen_epoch_source')
    for pointer in epoch['frozen_references']:
        require(ref(Path(pointer['path'])) == pointer, 'frozen_epoch_provenance')
    require(ref(directory() / 'CARRY.json') == epoch['carry'], 'full_carry_unchanged')
    require(sha(ROOT / 'RESERVATIONS.jsonl') == epoch['ledger_sha256'] or
        hashlib.sha256((ROOT / 'RESERVATIONS.jsonl').read_bytes()[:epoch['ledger_bytes']]).hexdigest() == epoch['ledger_sha256'],
        'unchanged_inherited_ledger_prefix')
    return epoch


def prepare(dependency_root):
    module = runtime(dependency_root)
    module.old.verify(ROOT, LANE)
    prior = ROOT / 'lease_r120_v2/campaign_node1_7'
    require(not Path('/proc/774742').exists() and not Path('/proc/774733').exists(), 'predecessors_exited')
    failed = read(prior / 'FAILED.json')
    require(failed['error'] == dict(type='ValueError', message='uncropped_context_fit'), 'exact_original_failure')
    ledger = (ROOT / 'RESERVATIONS.jsonl').read_bytes()
    rows = [json.loads(line) for line in ledger.splitlines() if line.strip()]
    counters = validate_cursor(rows, failed)
    require(not (prior / 'native/CALL_002006.json').exists(), 'unreserved_turn_not_replayed')
    child_path = prior / 'native/CALL_002005.json'
    request_path = prior / 'parent_queue/GUIDED_SLEEP_C52_P110.request.json'
    response_path = prior / 'parent_queue/GUIDED_SLEEP_C52_P110.response.json'
    call, request, response = read(child_path), read(request_path), read(response_path)
    require(response['request_sha256'] == sha(request_path), 'parent110_original_join')
    archive = Path(response['archive']['remote_root'])
    require(archive.is_relative_to(ROOT / 'parent_transcripts'), 'own_original_parent_archive')
    for name, pin in response['archive']['files'].items():
        require(Path(name).name == name and sha(archive / name) == pin, 'original_parent_archive')
    require(response['plan'] == read(archive / 'PLAN.json'), 'same_delivered_plan')
    carry = compact_context(call, request, response)
    carry['parent_receipt'] = read(prior / 'PARENT_00110.json')
    require(carry['parent_receipt']['status'] == 'COMPLETE', 'original_parent_received')
    ready = read(prior / 'READY.json')
    require(ready['learned'] is False and ready['native_cap'] == 16384 and ready['parent_cap'] == 640
        and time.time() < ready['native_deadline_unix'], 'same_mode_caps_lease')
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(ready['model_dir'], local_files_only=True, trust_remote_code=False)
    tokens = tokenizer.apply_chat_template(carry['messages'], tokenize=True, add_generation_prompt=True, return_dict=False)
    require(0 < len(tokens) < ready['context'], 'complete_compact_carry_fits')
    output = directory()
    output.mkdir(parents=True, exist_ok=False)
    (output / 'parent_queue').mkdir()
    write(output / 'READY.json', ready)
    write(output / 'CARRY.json', carry)
    frozen = [ref(prior / name) for name in ('FAILED.json', 'GUARDIAN_FAILED.json', 'TERMINAL.json',
        'READY.json', 'RECOVERY.json', 'CHECKPOINT_C51.json', 'PARENT_00110.json')]
    frozen.extend(ref(path) for path in (child_path, request_path, response_path, archive / 'PLAN.json'))
    frozen.extend(ref(path) for path in Path(dependency_root).rglob('*.py'))
    epoch = dict(schema='R129_OVERFLOW_CONTEXT_DISTILLATION_V1', source=ref(Path(__file__).resolve()),
        dependency_root=str(dependency_root), frozen_references=frozen, carry=ref(output / 'CARRY.json'),
        counters=counters, ledger_sha256=hashlib.sha256(ledger).hexdigest(), ledger_bytes=len(ledger),
        first_unreserved_native=2006, next_parent_number=111, pending_cycle=52, pending_reflection_turn=2,
        compact_prompt_tokens=len(tokens), context_limit=ready['context'],
        no_adapter=True, optimizer_updates=0, rng_restoration='NOT_AVAILABLE_NEW_DECLARED_CONTEXT_FORK',
        greedy_original_decoder=True, identical_context_claim=False, parent110_calls=0, created_unix=time.time())
    write(output / 'EPOCH.json', epoch)
    return dict(epoch=ref(output / 'EPOCH.json'), carry=epoch['carry'], compact_prompt_tokens=len(tokens),
        first_unreserved_native=2006, optimizer_updates=0)


def native(dependency_root):
    module = runtime(dependency_root)
    epoch = verify(module)
    require(sha(ROOT / 'RESERVATIONS.jsonl') == epoch['ledger_sha256'], 'no_intervening_reservations')
    carry = read(directory() / 'CARRY.json')

    def restore(counters, state):
        counters.update(epoch['counters'])
        state.update(memory=carry['messages'][2]['content'], old_rows=[])

    namespace = dict(module.old.native.__globals__, parent=module.parent,
        verify=lambda root, lane: verify(module), epoch_directory=directory, epoch_restore=restore,
        epoch_carry=lambda: carry, epoch_carry_reference=lambda: epoch['carry'])
    exec(compile(native_source(inspect.getsource(module.old.native)), __file__ + ':epoch_native', 'exec'), namespace)
    namespace['native'](ROOT, LANE)


def scan(dependency_root):
    module = runtime(dependency_root)
    verify(module)
    require(os.geteuid() == 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'privileged_cpu_scan')
    service = directory() / 'SERVICE_IDENTITY.json'
    if not service.exists():
        module.old.admission.node1.service(service)
    return module.old.admission.scan(LANE, service)


def guard(dependency_root):
    module = runtime(dependency_root)
    verify(module)
    source = inspect.getsource(module.old.guard)
    source = replace_once(source, "campaign=root/('campaign_'+lane)", 'campaign=epoch_directory(root,lane)')
    source = source.replace("root/'ALLOCATION.md'", "campaign/'ALLOCATION.md'")
    source = replace_once(source, "'gpu.orch_r109_route_run','native','--root',str(root),'--lane',lane",
        "'gpu.orch_r129_a40r0_context_epoch','native','--dependency-root',str(epoch_dependency)")
    source = source.replace("root/'source'", 'epoch_source_root')

    def admission(lane, service):
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            sys.executable, '-B', str(Path(__file__).resolve()), 'scan', '--dependency-root', str(dependency_root)]
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=100)
        return json.loads(result.stdout)

    namespace = dict(module.old.guard.__globals__, verify=lambda root, lane: verify(module),
        epoch_directory=directory, epoch_dependency=Path(dependency_root),
        epoch_source_root=Path(__file__).resolve().parents[1], admission=SimpleNamespace(scan=admission))
    with (directory() / 'OWNER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (directory() / 'GUARD_ONCE').mkdir()
        exec(compile(source, __file__ + ':epoch_guard', 'exec'), namespace)
        namespace['guard'](ROOT, LANE)


def broker(dependency_root, repository, buffer, receipts, relocation):
    require(not Path('/proc/3137150').exists(), 'original_parent_broker_exited')
    module = runtime(dependency_root, relocation)
    with buffer.with_suffix('.owner.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        module.broker(repository, ROOT, LANE, buffer, receipts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'native', 'scan', 'guard', 'broker'))
    parser.add_argument('--dependency-root', type=Path, required=True)
    for name in ('repository', 'buffer', 'receipts', 'relocation'):
        parser.add_argument('--' + name, type=Path)
    arguments = parser.parse_args()
    if arguments.phase == 'broker':
        broker(arguments.dependency_root, arguments.repository, arguments.buffer, arguments.receipts, arguments.relocation)
    else:
        result = globals()[arguments.phase](arguments.dependency_root)
        if result is not None:
            print(json.dumps(result, sort_keys=True))
