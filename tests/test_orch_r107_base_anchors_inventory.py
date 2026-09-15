"""CPU-only native-token joins; fixtures never snapshot a live source tree."""

from copy import deepcopy
import json

import pytest

from gpu import orch_r107_base_anchors_inventory as inventory
from gpu import orch_r107_base_anchors_run as runner
from gpu.orch_r108_guided_native import validate_anchor_inventory
from organism_v6 import orch_r107_base_anchors as policy


class Tokenizer:
    eos_token_id = 1

    def __init__(self):
        self.all_special_ids = [1]

    def apply_chat_template(self, messages, **kwargs):
        return [ord(letter) + 10 for letter in messages[0]['content']]

    def decode(self, tokens, **kwargs):
        return ''.join(chr(token - 10) for token in tokens)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True))


@pytest.fixture
def prepared(tmp_path):
    tokenizer = Tokenizer()
    suite = policy.tasks()
    sources = {'organism_v6/orch_r107_base_anchors.py': inventory.sha(policy.__file__),
        'gpu/orch_r107_base_anchors_run.py': inventory.sha(runner.__file__)}
    plan = dict(base_sha256=policy.BASE_SHA, adapter=None, parent_calls=0, training_updates=0,
        call_cap=64, max_new_tokens=512, suite_sha256=policy.digest(suite), sources=sources,
        exclusions=policy.exclusions(suite))
    write(tmp_path / 'PLAN.json', plan)
    write(tmp_path / 'TASKS_PRIVATE.json', suite)
    write(tmp_path / 'RESERVATIONS.json', [row['id'] for row in suite])
    calls, tokenization = [], []
    for position, task in enumerate(suite):
        if task['family'] == 'code':
            raw = json.dumps(dict(expression=task['oracle']['reference_expression']))
        elif task['family'] == 'simulated_tools':
            raw = json.dumps(task['oracle'])
        else:
            raw = task['oracle']['answer']
        messages = policy.messages(task)
        prefix = tokenizer.apply_chat_template(messages)
        response = dict(messages=messages, raw=raw, token_ids=[ord(letter)+10 for letter in raw]+[1],
            prompt_tokens=len(prefix), terminal=True, truncated=False)
        call = dict(position=position, task_id=task['id'], family=task['family'], status='COMPLETE',
            messages=messages, max_new_tokens=512, base_sha256=policy.BASE_SHA, adapter=None,
            response=response, outcome=policy.outcome(task, response, 1))
        calls.append(call)
        write(tmp_path / 'readout' / f'CALL_{position:03d}.json', call)
        tokenization.append(dict(task_id=task['id'], prompt_tokens=len(prefix), encoded_sha256=policy.digest(prefix)))
    write(tmp_path / 'READY.json', dict(status='PASS', plan_sha256=inventory.sha(tmp_path / 'PLAN.json'),
        suite_sha256=policy.digest(suite), tokenization=tokenization,
        task_file_sha256=inventory.sha(tmp_path / 'TASKS_PRIVATE.json'),
        reservations_sha256=inventory.sha(tmp_path / 'RESERVATIONS.json')))
    write(tmp_path / 'PUBLICATION.json', dict(ready_sha256=inventory.sha(tmp_path / 'READY.json'), own_cpu_tests_passed=True))
    for stage in ('BEFORE', 'AFTER'):
        write(tmp_path / 'readout' / (stage+'.json'), dict(base_sha256=policy.BASE_SHA,
            frozen_base_verified=True, no_adapter_verified=True, parent_calls=0, training_updates=0, status='PASS'))
    write(tmp_path / 'LAUNCH.json', {})
    write(tmp_path / 'ADMISSION.json', {})
    runner.publish_anchors(tmp_path, calls, True)
    seal(tmp_path)
    return tmp_path, tokenizer


def seal(root):
    manifest = inventory.read(root / 'ANCHOR_MANIFEST.json')
    manifest['anchors_sha256'] = inventory.sha(root / 'ANCHOR_ROWS.json')
    write(root / 'ANCHOR_MANIFEST.json', manifest)
    write(root / 'readout/COMPLETE.json', dict(status='COMPLETE', calls=64, finished_unix=1,
        manifest_sha256=inventory.sha(root / 'ANCHOR_MANIFEST.json')))
    return inventory.sha(root / 'ANCHOR_MANIFEST.json')


def build(prepared):
    root, tokenizer = prepared
    return inventory.build_inventory(root, tokenizer, 16384,
        expected_manifest_sha256=inventory.sha(root / 'ANCHOR_MANIFEST.json'))


def test_all_families_native_ids_and_r108_interface(prepared):
    root, tokenizer = prepared
    anchors, receipt = build(prepared)
    validate_anchor_inventory(anchors)
    assert receipt['families'] == dict.fromkeys(policy.FAMILIES, 16)
    assert receipt['completed_calls'] == receipt['encoded_anchors'] == 64
    assert receipt['shortfalls'] == dict.fromkeys(policy.FAMILIES, 0)
    first = anchors['code'][0]
    response = inventory.read(root / 'readout/CALL_000.json')['response']
    assert first['encoded'].target_ids == tuple(response['token_ids'])
    assert first['encoded'].labels[:response['prompt_tokens']] == (-100,) * response['prompt_tokens']
    assert first['encoded'].labels[response['prompt_tokens']:] == tuple(response['token_ids'])
    assert receipt['new_model_calls'] == receipt['training_updates'] == receipt['parent_calls'] == 0
    assert receipt['automatic_fit'] is False
    assert inventory.load_inventory(root, tokenizer, expected_manifest_sha256=inventory.sha(root / 'ANCHOR_MANIFEST.json')) == anchors


@pytest.mark.parametrize('field,value', [('split', 'HELD'), ('cohort', 'other'), ('trainingAllowed', True),
    ('automatic_fit', True), ('family', 'math'), ('target', 'rewritten'), ('call_sha256', '0'*64)])
def test_anchor_boundary_mutations_rejected(prepared, field, value):
    root, _ = prepared
    rows = inventory.read(root / 'ANCHOR_ROWS.json')
    rows[0][field] = value
    write(root / 'ANCHOR_ROWS.json', rows)
    seal(root)
    with pytest.raises(ValueError):
        build(prepared)


@pytest.mark.parametrize('mutation', ['duplicate', 'omit', 'adapter', 'teacher', 'after', 'call_hash', 'prompt_ids'])
def test_evidence_and_inventory_tampering_rejected(prepared, mutation):
    root, tokenizer = prepared
    rows = inventory.read(root / 'ANCHOR_ROWS.json')
    if mutation == 'duplicate':
        rows[-1] = deepcopy(rows[0])
    elif mutation == 'omit':
        rows.pop()
    elif mutation == 'adapter':
        rows[0]['source_actor']['adapter'] = 'not_base'
    elif mutation == 'teacher':
        manifest = inventory.read(root / 'ANCHOR_MANIFEST.json')
        manifest['teacher_targets'] = True
        write(root / 'ANCHOR_MANIFEST.json', manifest)
    elif mutation == 'after':
        after = inventory.read(root / 'readout/AFTER.json')
        after['no_adapter_verified'] = False
        write(root / 'readout/AFTER.json', after)
    elif mutation == 'call_hash':
        call = inventory.read(root / 'readout/CALL_000.json')
        call['response']['raw'] = 'other'
        write(root / 'readout/CALL_000.json', call)
    elif mutation == 'prompt_ids':
        tokenizer.apply_chat_template = lambda *args, **kwargs: [17]
    write(root / 'ANCHOR_ROWS.json', rows)
    seal(root)
    with pytest.raises(ValueError):
        build(prepared)


@pytest.mark.parametrize('mutation', ['token_roundtrip', 'special_token', 'no_eos', 'truncated', 'context'])
def test_encoding_never_rescues_or_truncates(prepared, mutation):
    root, tokenizer = prepared
    task = policy.tasks()[0]
    row = inventory.read(root / 'ANCHOR_ROWS.json')[0]
    call = inventory.read(root / 'readout/CALL_000.json')
    ready = inventory.read(root / 'READY.json')['tokenization'][0]
    context = 16384
    if mutation == 'token_roundtrip':
        call['response']['token_ids'][0] += 1
    elif mutation == 'special_token':
        tokenizer.all_special_ids.append(call['response']['token_ids'][0])
    elif mutation == 'no_eos':
        call['response']['token_ids'][-1] += 1
    elif mutation == 'truncated':
        call['response']['truncated'] = True
    else:
        context = 1
    with pytest.raises(ValueError):
        inventory.encode_anchor(task, row, call, ready, tokenizer, context)


def test_default_pin_rejects_different_source(prepared):
    root, tokenizer = prepared
    with pytest.raises(ValueError, match='bound_native_file'):
        inventory.load_inventory(root, tokenizer)


def test_source_files_are_read_only(prepared):
    root, _ = prepared
    before = {str(path): inventory.sha(path) for path in root.rglob('*.json')}
    build(prepared)
    assert before == {str(path): inventory.sha(path) for path in root.rglob('*.json')}
