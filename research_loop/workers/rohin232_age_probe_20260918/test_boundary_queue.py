import json

import pytest

from research_loop.workers.rohin232_age_probe_20260918 import boundary_queue as queue


def record(life, index, kind, document):
    value=dict(index=index,journal_id='synthetic_journal',kind=kind,document=document)
    value['sha256']=queue.digest(value)
    path=life/'stream/records'/f'{index:020d}.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(queue.canonical(value))
    return value


def fixture(root):
    life=root/'life'
    initial=record(life,1,'LOADED',dict(base_sha256=queue.BASE_SHA))
    for cycle in (1,2,3):
        directory=life/'checkpoints'/f'sleep_{cycle:06d}'
        (directory/'adapter').mkdir(parents=True)
        for name in ('README.md','adapter_config.json','adapter_model.safetensors'):
            (directory/'adapter'/name).write_bytes(f'synthetic-{cycle}-{name}'.encode())
        commit=dict(base_sha256=queue.BASE_SHA,adapter_state_sha256=str(cycle)*64,
            optimizer_steps=cycle*32,created_unix=cycle,
            adapter_files={path.name:queue.file_hash(path) for path in (directory/'adapter').iterdir()})
        (directory/'COMMIT.json').write_bytes(queue.canonical(commit))
        (directory/'optimizer_rng.pt').write_bytes(b'synthetic-not-a-real-model')
        record(life,cycle+1,'SLEEP_COMPLETE',dict(status='COMPLETE',cycle=cycle,
            after_adapter_sha256=commit['adapter_state_sha256'],total_optimizer_steps=cycle*32,
            resume_state=dict(never_in_probe_context=True)))
    record(life,5,'UPDATE',dict(optimizer_step=97))
    registration=dict(life_root=str(life),journal_id='synthetic_journal',source_name='test',
        initial_loaded=dict(index=1,sha256=initial['sha256']),baseline_cycle=0,baseline_optimizer_steps=0,
        runtime_epochs=[dict(name='initial',after_record_index=0,record_index=1,record_sha256=initial['sha256'])])
    return life,registration


def test_every_sleep_includes_non_power_two_and_preserves_source(tmp_path):
    life,registration=fixture(tmp_path)
    original={str(path.relative_to(life)):queue.file_hash(path) for path in life.rglob('*') if path.is_file()}
    output=tmp_path/'queue'
    status=queue.scan(registration,output)
    assert status['captured_ages']==[1,2,3] and status['pending_ages']==[1,2,3]
    assert status['launched_ages']==[] and status['learner_signals']==[]
    assert not list(output.rglob('optimizer_rng.pt'))
    assert original=={str(path.relative_to(life)):queue.file_hash(path) for path in life.rglob('*') if path.is_file()}
    assert queue.scan(registration,output)['captured_ages']==[1,2,3]


def test_latest_completed_ignores_inflight_update(tmp_path):
    _,registration=fixture(tmp_path)
    output=tmp_path/'queue'
    assert queue.scan(registration,output,latest=True)['captured_ages']==[3]


def test_wrong_journal_or_tampered_commit_fails(tmp_path):
    life,registration=fixture(tmp_path)
    with pytest.raises(ValueError,match='source_record_binding'):
        queue.scan(dict(registration,journal_id='wrong'),tmp_path/'wrong')
    (life/'checkpoints/sleep_000003/adapter/adapter_model.safetensors').write_bytes(b'changed')
    with pytest.raises(ValueError,match='adapter_bytes_not_committed'):
        queue.scan(registration,tmp_path/'queue',latest=True)


def test_new_runtime_epoch_is_pending_not_silently_same_source(tmp_path):
    life,registration=fixture(tmp_path)
    record(life,3,'R232_RECOVERY_CONTEXT',dict(state_sha256='a'*64))
    output=tmp_path/'queue'
    result=queue.scan(registration,output)
    assert result['captured_ages']==[1]
    assert result['pending_ages']==[1,3] and result['pending_epoch_ages']==[3]
    assert result['unknown_epoch_markers']==[3] and result['source_binding_verified'] is False
