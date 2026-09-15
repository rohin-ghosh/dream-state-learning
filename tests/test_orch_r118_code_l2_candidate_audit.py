from copy import deepcopy
import hashlib
import json

import pytest

from gpu import orch_r118_code_l2_candidate_audit as audit


class Tokenizer:
    eos_token_id = 0

    def apply_chat_template(self, messages, **unused):
        return [ord(character) for character in json.dumps(messages, ensure_ascii=False)]

    def decode(self, tokens, **unused):
        return ''.join(chr(token) for token in tokens)


def response(raw, messages, terminal=True):
    return dict(raw=raw, messages=messages, prompt_tokens=len(Tokenizer().apply_chat_template(messages)),
        token_ids=[ord(character) for character in raw] + ([0] if terminal else []), terminal=terminal,
        truncated=not terminal, input_truncated=False)


def span(source, text, fragment):
    start = text.index(fragment)
    return dict(source=source, start=start, end=start + len(fragment), sha256=audit.text_sha(fragment))


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    root = tmp_path / 'F3'
    prefix = 'C001_E0'
    task = dict(task_id='SYNTHETIC_TRAIN_1', split='TRAIN', content_sha256='a' * 64,
        prompt='Sum the entries of values; no additional constant.',
        tests=[dict(arguments=dict(values=[1, 2]), expected=3), dict(arguments=dict(values=[]), expected=0)])
    monkeypatch.setattr(audit.policy, 'tasks', lambda split: [task] if split == 'TRAIN' else pytest.fail('sealed_read'))
    before_raw = 'sum(values) + 1'
    child_raw = 'The extra one was wrong. The correction is sum(values).'
    guidance = 'Compare the requested quantity with your extra term; réfléchir.'
    feedback = '{"child_received": true, "status": "COMPLETE", "passed": false}'

    def event(actor, text):
        return dict(actor=actor, text=text, split='TRAIN', task_id=task['task_id'],
            task_sha256=task['content_sha256'], visibility='CHILD_VISIBLE', child_received=True,
            source_sha256=audit.text_sha(text))

    events = [event('environment', task['prompt']), event('child', before_raw), event('checker', feedback),
        event('parent', guidance), event('child', child_raw)]
    messages = [dict(role='system', content='Reflect freely.')]
    messages += [dict(role='assistant' if item['actor'] == 'child' else 'user', content=item['text'])
        for item in events[:-1]]
    request = dict(id=prefix + '_PARENT', payload=dict(task_id=task['task_id'],
        task_provenance=dict(split='TRAIN', task_sha256=task['content_sha256']), events=events[:3]),
        payload_sha256='b' * 64)
    wire = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    parent_response = dict(status='COMPLETE', actual_model='SYNTHETIC_PARENT', id=prefix + '_PARENT',
        request_sha256=wire, payload_sha256=request['payload_sha256'])
    audit.write_new(root / 'parent_queue' / (prefix + '_PARENT.request.json'), request)
    response_path = root / 'parent_queue' / (prefix + '_PARENT.response.json')
    audit.write_new(response_path, parent_response)
    rows = {}
    for name, kind, phase, start, finish in (('ORIGINAL', 'NATIVE', 'episode', 1, 2),
            ('PARENT', 'PARENT', 'experience', 3, 4), ('REFLECTION', 'NATIVE', 'reflection', 5, 6)):
        row = dict(id=prefix + '_' + name, kind=kind, phase=phase, split='TRAIN', status='COMPLETE',
            cycle=1, routes=dict(evaluation_origin=None), evaluation_origin=None,
            started_unix=start, finished_unix=finish)
        if name == 'PARENT':
            row.update(guidance=guidance, actual_model='SYNTHETIC_PARENT', response_sha256=audit.sha(response_path))
        else:
            row['response'] = response(before_raw if name == 'ORIGINAL' else child_raw,
                [dict(role='user', content=task['prompt'])] if name == 'ORIGINAL' else messages)
        rows[name] = row
        audit.write_new(root / 'reservations' / (row['id'] + '.json'), row)
    audit.write_new(root / 'triples' / (prefix + '.json'), dict(task_id=task['task_id'],
        cycle=1, parent_present=True, events=events))
    audit.write_new(root / 'PLAN.json', dict(parent_model='SYNTHETIC_PARENT'))
    audit.write_new(root / 'SOURCE_SHA256.json', dict(synthetic='c' * 64))
    selection = dict(roots=dict(F3=str(root)), pairs=[dict(branch='F3', prefix=prefix)])
    snapshot = audit.freeze(selection, tmp_path / 'audit')
    annotation = dict(method='AUTHOR_READ_ONLY_SEMANTIC_REVIEW_NO_MODEL_CALL',
        child_call_sha256=snapshot['pairs'][0]['files']['child']['sha256'],
        reviewed_whole_target=dict(sha256=audit.text_sha(child_raw), characters=len(child_raw)),
        grounding='PASS', all_endorsed_claims_supported=True, rationale='Synthetic correction of an unrequested constant.',
        findings=[dict(status='SUPPORTED', claim_role='SUPPORTED_OBSERVATION', explanation='Task forbids extra constant.',
            target=span('child', child_raw, 'The extra one was wrong.'),
            evidence=span('environment', task['prompt'], 'no additional constant'))],
        functional_witness=dict(before=span('before', before_raw, before_raw),
            after=span('child', child_raw, 'sum(values)')))
    return dict(root=root, snapshot=snapshot, annotations={'F3:' + prefix: annotation},
        rows=rows, task=task, tokenizer=Tokenizer(), selection=selection)


def run(fixture):
    return audit.audit(fixture['snapshot'], fixture['annotations'], fixture['tokenizer'])


def test_actual_whole_child_correction_not_final_format_gate(fixture):
    report, corpus = run(fixture)
    assert report['counts'] == {'ELIGIBLE': 1} and len(corpus) == 1
    assert corpus[0]['arm'] == audit.ARM and corpus[0]['automatic_ingestion'] is False
    assert corpus[0]['target_origin'] == 'ACTUAL_NATIVE_CHILD_NOT_PARENT'
    assert report['results'][0]['functional']['changed_cases'] == 2


def test_unicode_parent_all_prefix_masked_exact_native_target(fixture):
    report, corpus = run(fixture)
    encoded = corpus[0]['encoded']
    prefix = report['results'][0]['masking']['prompt_tokens']
    assert encoded['labels'][:prefix] == [-100] * prefix
    assert encoded['labels'][prefix:] == fixture['rows']['REFLECTION']['response']['token_ids']
    assert report['results'][0]['masking']['parent_prompt_labels_unmasked'] == 0


@pytest.mark.parametrize('field,value', [('prompt_tokens', 1), ('raw', 'replacement'),
    ('token_ids', [9, 0]), ('terminal', False), ('input_truncated', True)])
def test_native_token_or_prefix_changes_rejected(fixture, field, value):
    changed = deepcopy(fixture['rows']['REFLECTION']['response'])
    changed[field] = value
    with pytest.raises(ValueError):
        audit.masked_tokens(changed, fixture['tokenizer'])


def test_nonterminal_preserved_without_invented_eos_or_length_gate(fixture):
    raw = 'A grounded observation. ' * 300
    source = response(raw, [dict(role='user', content='Parent context')], terminal=False)
    encoded, compact = audit.masked_tokens(source, fixture['tokenizer'])
    assert encoded['target_ids'] == source['token_ids'] and 0 not in encoded['target_ids']
    assert compact['truncated'] and compact['child_tokens'] > 400


def test_partial_support_does_not_override_endorsed_contradiction(fixture):
    annotation = fixture['annotations']['F3:C001_E0']
    annotation['grounding'] = 'FAIL'
    annotation['findings'].append(dict(annotation['findings'][0], status='CONTRADICTED',
        claim_role='ENDORSED_ASSERTION', explanation='Synthetic separately labelled contradictory assertion.'))
    report, corpus = run(fixture)
    assert report['counts'] == {'REJECTED': 1} and not corpus
    assert report['results'][0]['functional']['status'] == 'PASS'


def test_oracle_success_or_token_mask_alone_never_admits(fixture):
    fixture['annotations'] = {}
    report, corpus = run(fixture)
    assert report['counts'] == {'UNKNOWN': 1} and not corpus
    assert report['results'][0]['masking']['status'] == 'PASS'


def test_no_functional_witness_is_unknown_not_format_failure(fixture):
    fixture['annotations']['F3:C001_E0'].pop('functional_witness')
    report, corpus = run(fixture)
    assert report['counts'] == {'UNKNOWN': 1} and not corpus


@pytest.mark.parametrize('field,value', [('split', 'FINAL'), ('evaluation_origin', 'DEV'),
    ('status', 'MISSING'), ('phase', 'readout')])
def test_nontrain_unreceived_or_readout_pair_retained_unknown(fixture, field, value):
    entry = fixture['snapshot']['pairs'][0]
    path = entry['files']['parent']['path']
    row = audit.read(path)
    row[field] = value
    with open(path, 'w') as stream:
        json.dump(row, stream)
    entry['files']['parent']['sha256'] = audit.sha(path)
    report, corpus = run(fixture)
    assert report['counts'] == {'UNKNOWN': 1} and not corpus


def test_source_tampering_detected_and_not_rewritten(fixture):
    path = fixture['snapshot']['pairs'][0]['files']['child']['path']
    with open(path, 'a') as stream:
        stream.write(' ')
    changed = audit.sha(path)
    report, corpus = run(fixture)
    assert report['counts'] == {'UNKNOWN': 1} and not corpus
    assert audit.sha(path) == changed


def test_whole_target_hash_and_evidence_offsets_bound(fixture):
    fixture['annotations']['F3:C001_E0']['findings'][0]['target']['start'] += 1
    report, corpus = run(fixture)
    assert report['counts'] == {'UNKNOWN': 1} and not corpus


def test_no_admission_on_unsupported_generated_code(fixture):
    texts = dict(before='sum(values)', child='__import__("os").system("false")')
    witness = {name: span(name, text, text) for name, text in texts.items()}
    witness['after'] = witness.pop('child')
    result = audit.functional_witness(witness, texts, fixture['task'])
    assert result['status'] == 'UNKNOWN'


def test_duplicate_and_oversized_pair_rosters_rejected(fixture, tmp_path):
    selection = deepcopy(fixture['selection'])
    selection['pairs'] *= 2
    with pytest.raises(ValueError, match='unique'):
        audit.freeze(selection, tmp_path / 'duplicate')
    selection['pairs'] *= 9
    with pytest.raises(ValueError, match='bounded'):
        audit.freeze(selection, tmp_path / 'too_many')


def test_old_roots_never_receive_audit_outputs(fixture):
    before = {str(path): audit.sha(path) for path in fixture['root'].rglob('*') if path.is_file()}
    run(fixture)
    after = {str(path): audit.sha(path) for path in fixture['root'].rglob('*') if path.is_file()}
    assert before == after
