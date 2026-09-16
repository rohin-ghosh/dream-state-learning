from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from gpu import orch_r125_readout_trajectory as reducer
from organism_v6 import orch_r107_capability as policy


def write(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, sort_keys=True, allow_nan=False))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def panel(directory, steps, *, changed=False, prompt_tokens=20, eos=99, context=None):
    root = '/retained-node/child'
    provenance = dict(schema=reducer.READOUT_SCHEMA, pid=100 + steps, ppid=90,
        process=['boot-identity', 100 + steps, 12345], host_sha256='a' * 64,
        plan_path=root + '/plan.json', plan_sha256='b' * 64,
        checkpoint_path=f'{root}/checkpoints/sleep_{steps:04d}/COMMIT.json',
        checkpoint_commit_sha256=policy.digest(['commit', steps]),
        checkpoint_sha256=dict(adapter=policy.digest(['files', steps]), optimizer='c' * 64, rng='c' * 64),
        adapter_state_sha256=policy.digest(['adapter', steps]), optimizer_steps=steps,
        base_sha256=policy.BASE_SHA256, suite_sha256=reducer.SUITE_SHA256, source=policy.SOURCE,
        output_path=f'{root}/readouts/sleep_{steps:04d}', gpu_uuid='GPU-test',
        max_new_tokens=512, decoder=deepcopy(reducer.DECODER), parent_present=False,
        history_present=False, train_ingestion=False, training_updates=0,
        raw_reasoning_preserved=True, started_unix=1.0)
    write(directory / 'REQUEST.json', provenance)
    snapshot = dict(adapter_state_sha256=provenance['adapter_state_sha256'],
        base_sha256=policy.BASE_SHA256, frozen_base_verified=True, checkpoint_files_verified=True,
        gpu_uuid='GPU-test', readonly=True, status='PASS', pid=provenance['pid'], observed_unix=2.0)
    write(directory / 'BEFORE.json', snapshot)
    write(directory / 'AFTER.json', dict(snapshot, unchanged=True, observed_unix=4.0))
    captures, manifest = [], {}
    for position, task in enumerate(policy.tasks()):
        arms = ('ON', 'OFF') if position % 2 == 0 else ('OFF', 'ON')
        for offset, arm in enumerate(arms):
            name = f'CALL_{position * 2 + offset:03d}.json'
            record = dict(provenance, position=position, task_id=task['id'], family=task['family'],
                arm=arm, condition='LORA_' + arm, messages=policy.messages(task),
                status='RESERVED', started_unix=3.0)
            write(directory / 'reservations' / name, record)
            response = dict(raw='not a task answer', messages=policy.messages(task),
                token_ids=[7, eos], prompt_tokens=prompt_tokens, terminal=True,
                truncated=False, max_new_tokens=512, eos_token_id=eos)
            if context is not None:
                response['context'] = context
            if changed and position == 0 and arm == 'ON':
                response.update(raw='source_sha256 one two three one two three one two three',
                    token_ids=[7] * 8 + [eos])
            capture = policy.capture(task, arm, response,
                checkpoint_sha256=provenance['adapter_state_sha256'],
                base_sha256=policy.BASE_SHA256, lora_enabled=arm == 'ON')
            captures.append(capture)
            record.update(status='COMPLETE', response=response, capture=capture, finished_unix=3.5)
            manifest[name] = write(directory / name, record)
    scores = policy.reduce_paired(captures, checkpoint_sha256=provenance['adapter_state_sha256'],
        base_sha256=policy.BASE_SHA256, max_new_tokens=512)
    write(directory / 'COMPLETE.json', dict(provenance, status='COMPLETE', calls=64,
        call_files=manifest, task_count=32, before_after_verified=True,
        paired_scores=scores, finished_unix=5.0))
    return directory


@pytest.fixture
def trajectory(tmp_path):
    return panel(tmp_path / 'zero', 0), panel(tmp_path / 'one', 16, changed=True)


def rewrite_call(directory, mutate, *, rehash=True):
    path = directory / 'CALL_000.json'
    record = read(path)
    mutate(record)
    checksum = write(path, record)
    if rehash:
        complete = read(directory / 'COMPLETE.json')
        complete['call_files'][path.name] = checksum
        write(directory / 'COMPLETE.json', complete)


def test_trajectory_reports_exact_descriptive_changes_and_sources(trajectory):
    baseline, later = trajectory
    before = {path: path.read_bytes() for directory in trajectory for path in directory.rglob('*') if path.is_file()}
    result = reducer.reduce_trajectory(baseline, [later])
    zero, one = result['checkpoints']
    assert result['schema'] == reducer.SCHEMA
    assert 'not cognition, retention-success' in result['claim_boundary']
    assert zero['arms']['ON']['changes']['versus_checkpoint0']['exact_response_changes'] == 0
    assert one['arms']['ON']['changes']['versus_OFF'] == dict(exact_response_changes=1,
        generated_tokens_delta=7, cap_hits_delta=0, fixed_task_comparable_outputs=32,
        fixed_task_passes_delta=0)
    assert one['arms']['ON']['changes']['versus_checkpoint0']['exact_response_changes'] == 1
    assert one['arms']['OFF']['changes']['versus_checkpoint0']['exact_response_changes'] == 0
    row = one['outputs'][0]
    assert all('raw' not in output for checkpoint in result['checkpoints'] for output in checkpoint['outputs'])
    assert 'source_sha256 one two three one two three one two three' not in json.dumps(result)
    assert row['generated_tokens'] == 9
    assert row['repeated_token_4gram'] == dict(windows=6, repeated_windows=4, fraction=4 / 6)
    assert row['repeated_whitespace_4gram'] == dict(windows=7, repeated_windows=3, fraction=3 / 7)
    assert row['journal_marker_counts']['source_sha256'] == 1
    assert one['arms']['ON']['journal_marker_output_fraction'] == 1 / 32
    assert one['arms']['ON']['generated_tokens'] == 71
    assert row['source_sha256'] == hashlib.sha256((later / row['source_file']).read_bytes()).hexdigest()
    assert row['response_sha256'] == policy.digest(read(later / row['source_file'])['response'])
    assert len(one['sources']) == 132
    assert before == {path: path.read_bytes() for directory in trajectory for path in directory.rglob('*') if path.is_file()}


@pytest.mark.parametrize('missing', ['COMPLETE.json', 'REQUEST.json', 'BEFORE.json', 'AFTER.json',
    'CALL_001.json', 'reservations/CALL_001.json'])
def test_missing_evidence_is_rejected(trajectory, missing):
    baseline, later = trajectory
    (later / missing).unlink()
    with pytest.raises(ValueError):
        reducer.reduce_trajectory(baseline, [later])


@pytest.mark.parametrize('field,value,reason', [
    ('status', 'FAILED', 'completed_call'),
    ('arm', 'OFF', 'call_pair'),
    ('task_id', 'unknown', 'call_pair'),
    ('condition', 'LORA_OFF', 'call_pair'),
    ('position', 1, 'call_pair'),
    ('messages', [], 'call_pair'),
    ('plan_sha256', 'f' * 64, 'provenance'),
    ('parent_present', True, 'provenance'),
    ('checkpoint_commit_sha256', 'f' * 64, 'provenance'),
    ('adapter_state_sha256', 'f' * 64, 'provenance'),
])
def test_rehashed_call_tampering_is_rejected(trajectory, field, value, reason):
    baseline, later = trajectory
    rewrite_call(later, lambda record: record.update({field: value}))
    with pytest.raises(ValueError, match=reason):
        reducer.reduce_trajectory(baseline, [later])


def test_call_source_hash_is_checked_before_capture(trajectory):
    baseline, later = trajectory
    rewrite_call(later, lambda record: record['response'].update(raw='tampered'), rehash=False)
    with pytest.raises(ValueError, match='call_source_hash'):
        reducer.reduce_trajectory(baseline, [later])


@pytest.mark.parametrize('field,value', [('response_sha256', 'f' * 64), ('prompt_sha256', 'f' * 64),
    ('task_sha256', 'f' * 64), ('lora_enabled', False), ('thinking_metrics', {'success': True})])
def test_capture_provenance_is_recomputed(trajectory, field, value):
    baseline, later = trajectory
    rewrite_call(later, lambda record: record['capture'].update({field: value}))
    with pytest.raises(ValueError, match='capture_hash'):
        reducer.reduce_trajectory(baseline, [later])


@pytest.mark.parametrize('kind', ['incomplete', 'error'])
def test_noncomplete_responses_even_with_valid_capture_are_rejected(trajectory, kind):
    baseline, later = trajectory

    def mutate(record):
        response = record['response']
        if kind == 'incomplete':
            response.update(token_ids=[7], terminal=False)
        else:
            response['error'] = 'RuntimeError'
        record['capture'] = policy.capture(policy.tasks()[0], 'ON', response,
            checkpoint_sha256=record['adapter_state_sha256'], base_sha256=policy.BASE_SHA256,
            lora_enabled=True)

    rewrite_call(later, mutate)
    with pytest.raises(ValueError, match='incomplete_response'):
        reducer.reduce_trajectory(baseline, [later])


@pytest.mark.parametrize('which', ['zero', 'later', 'both'])
def test_valid_cap_hits_are_retained_with_explicit_score_denominators(trajectory, which):
    baseline, later = trajectory

    def truncate(record):
        record['response'].update(token_ids=[7] * 512, terminal=False, truncated=True)
        record['capture'] = policy.capture(policy.tasks()[0], 'ON', record['response'],
            checkpoint_sha256=record['adapter_state_sha256'], base_sha256=policy.BASE_SHA256,
            lora_enabled=True)

    directories = trajectory if which == 'both' else [baseline if which == 'zero' else later]
    for directory in directories:
        rewrite_call(directory, truncate)
        complete = read(directory / 'COMPLETE.json')
        captures = [read(directory / f'CALL_{index:03d}.json')['capture'] for index in range(64)]
        complete['paired_scores'] = policy.reduce_paired(captures,
            checkpoint_sha256=complete['adapter_state_sha256'],
            base_sha256=policy.BASE_SHA256, max_new_tokens=512)
        assert not complete['paired_scores']['all_pairs_complete']
        write(directory / 'COMPLETE.json', complete)
    result = reducer.reduce_trajectory(baseline, [later])
    for checkpoint in result['checkpoints']:
        is_cap_hit = Path(checkpoint['directory']) in directories
        row = checkpoint['outputs'][0]
        assert row['cap_hit'] is is_cap_hit
        assert row['generated_tokens'] == (512 if is_cap_hit else 2 if checkpoint['directory'] == str(baseline) else 9)
        assert row['completion'] == ('truncated' if is_cap_hit else 'complete')
        assert checkpoint['arms']['ON']['cap_hit_outputs'] == int(is_cap_hit)
        assert checkpoint['arms']['ON']['fixed_task_scored_outputs'] == 32 - int(is_cap_hit)
        assert checkpoint['arms']['ON']['outputs'] == 32
        if is_cap_hit:
            assert row['fixed_task_pass'] is None
            assert row['versus_OFF']['fixed_task_pass_delta'] is None
    assert result['checkpoints'][1]['outputs'][0]['versus_checkpoint0']['fixed_task_pass_delta'] is None
    assert result['checkpoints'][1]['arms']['ON']['changes']['versus_checkpoint0']['fixed_task_comparable_outputs'] == 31


@pytest.mark.parametrize('tokens,truncated', [([7] * 511, True), ([7] * 512, False), ([7] * 513, True)])
def test_malformed_cap_flags_or_lengths_are_rejected(trajectory, tokens, truncated):
    baseline, later = trajectory
    rewrite_call(later, lambda record: record['response'].update(
        token_ids=tokens, terminal=False, truncated=truncated))
    with pytest.raises(ValueError, match='truncation_cap_mismatch|truncation_flag_mismatch|native_cap_violation'):
        reducer.reduce_trajectory(baseline, [later])


@pytest.mark.parametrize('kwargs', [dict(prompt_tokens=21), dict(eos=100), dict(context=4096)])
def test_cross_checkpoint_decoder_or_prompt_token_drift(tmp_path, kwargs):
    baseline = panel(tmp_path / 'zero', 0)
    later = panel(tmp_path / 'later', 16, **kwargs)
    with pytest.raises(ValueError, match='cross_checkpoint_prompt_or_decoder'):
        reducer.reduce_trajectory(baseline, [later])


@pytest.mark.parametrize('name,field,value', [
    ('COMPLETE.json', 'before_after_verified', False),
    ('COMPLETE.json', 'calls', 63),
    ('COMPLETE.json', 'paired_scores', {}),
    ('AFTER.json', 'unchanged', False),
    ('AFTER.json', 'adapter_state_sha256', 'f' * 64),
    ('BEFORE.json', 'readonly', 1),
    ('REQUEST.json', 'suite_sha256', 'f' * 64),
    ('REQUEST.json', 'decoder', dict(do_sample=True)),
    ('REQUEST.json', 'base_sha256', 'f' * 64),
    ('REQUEST.json', 'raw_reasoning_preserved', False),
    ('REQUEST.json', 'plan_sha256', 'not-a-hash'),
    ('REQUEST.json', 'process', ['boot', 999, 0]),
])
def test_panel_receipt_tampering(trajectory, name, field, value):
    baseline, later = trajectory
    receipt = read(later / name)
    receipt[field] = value
    write(later / name, receipt)
    with pytest.raises(ValueError):
        reducer.reduce_trajectory(baseline, [later])


@pytest.mark.parametrize('name', ['FAILED.json', 'CALL_064.json', 'reservations/CALL_064.json'])
def test_failed_or_extra_evidence_is_rejected(trajectory, name):
    baseline, later = trajectory
    write(later / name, {})
    with pytest.raises(ValueError):
        reducer.reduce_trajectory(baseline, [later])


def test_checkpoint0_and_unique_steps_required(trajectory, tmp_path):
    baseline, later = trajectory
    with pytest.raises(ValueError, match='checkpoint0_zero_steps'):
        reducer.reduce_trajectory(later)
    with pytest.raises(ValueError, match='duplicate_checkpoint_steps'):
        reducer.reduce_trajectory(baseline, [later, later])
    newest = panel(tmp_path / 'newest', 32)
    result = reducer.reduce_trajectory(baseline, [newest, later])
    assert [item['provenance']['optimizer_steps'] for item in result['checkpoints']] == [0, 16, 32]


@pytest.mark.parametrize('raw', ['{"schema":1,"schema":2}', '{"value":NaN}', '[]'])
def test_malformed_json_rejected(trajectory, raw):
    baseline, later = trajectory
    (later / 'REQUEST.json').write_text(raw)
    with pytest.raises(ValueError):
        reducer.reduce_trajectory(baseline, [later])


def test_short_grams_and_literal_markers():
    assert reducer._repetition([]) == dict(windows=0, repeated_windows=0, fraction=0.0)
    assert reducer._repetition([1, 1, 1, 1, 1])['fraction'] == 0.5
    assert reducer._repetition('a b c d a b c d'.split())['fraction'] == 1 / 5


def test_cli_is_cpu_only_readonly_and_emits_no_partial_report(trajectory):
    baseline, later = trajectory
    source = """
import sys
from gpu import orch_r125_readout_trajectory as reducer
reducer.main(sys.argv[1:])
assert 'torch' not in sys.modules
assert 'gpu.orch_r125_continual_native' not in sys.modules
assert 'gpu.orch_r125_stream_journal' not in sys.modules
"""
    command = [sys.executable, '-B', '-c', source, '--checkpoint0', str(baseline), '--readout', str(later)]
    result = subprocess.run(command, cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['schema'] == reducer.SCHEMA
    (later / 'CALL_001.json').unlink()
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 2
    assert result.stdout == ''


def test_cli_requires_explicit_baseline():
    with pytest.raises(SystemExit) as error:
        reducer.main([])
    assert error.value.code == 2


def test_compact_cli_is_raw_free_and_keeps_source_hashes(trajectory, capsys):
    baseline, later = trajectory
    reducer.main(['--checkpoint0', str(baseline), '--readout', str(later), '--compact'])
    stdout = capsys.readouterr().out
    result = json.loads(stdout)
    assert len(stdout.splitlines()) == 1
    assert all('outputs' not in checkpoint for checkpoint in result['checkpoints'])
    assert all(len(checkpoint['sources']) == 132 for checkpoint in result['checkpoints'])
    assert result['checkpoints'][1]['arms']['ON']['changes']['versus_checkpoint0']['exact_response_changes'] == 1
    assert 'source_sha256 one two three one two three one two three' not in stdout
    assert 'not a task answer' not in stdout


def test_suite_fingerprint_is_fixed(trajectory, monkeypatch):
    baseline, later = trajectory
    tasks = policy.tasks()
    tasks[0]['prompt'] += ' changed'
    monkeypatch.setattr(policy, 'tasks', lambda: tasks)
    with pytest.raises(ValueError, match='fixed_synthetic32_suite'):
        reducer.reduce_trajectory(baseline, [later])
