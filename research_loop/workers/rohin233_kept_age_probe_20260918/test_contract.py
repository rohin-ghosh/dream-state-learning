from copy import deepcopy
import json
import os
from pathlib import Path
import socket
import socketserver
import threading
import time

import pytest

from research_loop.workers.rohin233_kept_age_probe_20260918 import enroll, parent_bridge as parent
from research_loop.workers.rohin233_kept_age_probe_20260918 import source_exposure


def source_request():
    generated = dict(stage='ACT', opportunity=7, messages=[dict(role='user', content='synthetic scene')])
    identifier = parent.sha(parent.canonical(generated))
    request = dict(origin=dict(kind='STANDALONE_GENERATION', request_id=identifier,
        request_sha256=identifier, response_sha256='a' * 64))
    config = dict(condition='synthetic', rule_sha256='b' * 64)
    response = dict(request_id=identifier, **config, receipt_sha256='c' * 64,
        report=dict(instruction='Actual scorer instruction.', feedback=[dict(accepted=False, rank=65)]))
    return generated, request, config, response


def test_parent_preserves_scorer_receipt_and_feedback():
    generated, request, config, response = source_request()
    original = deepcopy(response)
    modified, evidence = parent.envelope(request, response, generated, config)
    assert response == original
    assert modified['receipt_sha256'] == original['receipt_sha256']
    assert modified['report']['feedback'] == original['report']['feedback']
    assert modified['report']['instruction'].startswith(original['report']['instruction'])
    assert evidence['model_weights_changed'] is False and evidence['unmatched_guidance'] is True
    assert parent.EPOCH in modified['report']['instruction']


def test_bad_origin_cannot_be_parented():
    generated, request, config, response = source_request()
    generated['stage'] = 'THINK'
    with pytest.raises(ValueError, match='actual_generation_request_binding'):
        parent.envelope(request, response, generated, config)


def test_curriculum_diversity_has_no_count_or_private_answers():
    assert len({parent.guidance(number) for number in range(1, 7)}) == 6
    assert all('no mandatory fields or count' in parent.guidance(number) for number in range(1, 7))


def test_atomic_exchange_retains_both_live_sockets(tmp_path):
    first, second = tmp_path / 'first.sock', tmp_path / 'second.sock'
    with socket.socket(socket.AF_UNIX) as old, socket.socket(socket.AF_UNIX) as new:
        old.bind(str(first))
        new.bind(str(second))
        identities = first.stat().st_ino, second.stat().st_ino
        parent.exchange(first, second)
        assert (first.stat().st_ino, second.stat().st_ino) == identities[::-1]
        parent.exchange(first, second)
        assert (first.stat().st_ino, second.stat().st_ino) == identities


def fixture(tmp_path):
    life = tmp_path / 'life'
    target = dict(root=str(life), label='synthetic', journal_id='journal')
    previous = None
    for index in range(7):
        kind = 'LOADED' if index == 0 else ('SLEEP_COMPLETE' if index in (1, 3, 5) else 'UPDATE')
        document = (dict(base_sha256=enroll.BASE) if index == 0 else dict(status='COMPLETE',
            cycle=(index + 1) // 2, total_optimizer_steps=0, after_adapter_sha256='d' * 64))
        record = dict(index=index, journal_id='journal', previous_sha256=previous, kind=kind, document=document)
        record['sha256'] = enroll.digest(record)
        enroll.put(life / 'stream/records' / f'{index:020d}.json', record)
        previous = record['sha256']
        if index == 0:
            target['initial_loaded'] = dict(index=0, sha256=previous)
    return target


def test_every_completed_sleep_paged_no_hidden_subsample(tmp_path):
    target = fixture(tmp_path)
    cursor, entries = {}, []
    while True:
        result = enroll.page(target, cursor, limit=2)
        entries.extend(result['entries'])
        cursor = result['cursor']
        if result['caught_up']:
            break
    assert [entry['sleep'] for entry in entries] == [1, 2, 3]
    assert all(not entry['captured'] and not entry['evaluated'] for entry in entries)
    assert all(entry['checkpoint_status'] == 'MISSING' for entry in entries)
    assert enroll.page(target, cursor)['entries'] == []


def test_journal_tamper_and_inflight_never_admitted(tmp_path):
    target = fixture(tmp_path)
    path = Path(target['root']) / 'stream/records/00000000000000000003.json'
    row = json.loads(path.read_bytes())
    row['document']['cycle'] = 100
    path.write_text(json.dumps(row))
    with pytest.raises(ValueError, match='journal_record_identity'):
        enroll.page(target, {})


def test_no_parent_text_in_queue_entries(tmp_path):
    target = fixture(tmp_path)
    result = enroll.page(target, {})
    assert 'messages' not in json.dumps(result)
    assert all(entry['context_into_probe'] is False for entry in result['entries'])


def test_remote_module_prefix_is_compilable():
    source = Path(enroll.__file__).read_text().rsplit("if __name__ == '__main__':", 1)[0]
    compile(source, '<read-only-remote-page>', 'exec')


def test_live_handover_forwards_once_and_keeps_original_receipt(tmp_path):
    generated, request, binding, response = source_request()
    identifier = request['origin']['request_id']
    generations = tmp_path / 'generations'
    generations.mkdir()
    (generations / (identifier + '.json')).write_text(json.dumps(dict(request=generated)))
    endpoint = tmp_path / 'base.sock'
    received = []

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            received.append(self.rfile.readline())
            self.wfile.write(parent.canonical(response) + b'\n')

    with socketserver.UnixStreamServer(str(endpoint), Handler) as server:
        backend = threading.Thread(target=server.handle_request)
        backend.start()
        config = dict(endpoint=str(endpoint), endpoint_inode=endpoint.stat().st_ino,
            scorer_pid=os.getpid(), scorer_start_ticks=parent.proc_start(os.getpid()),
            player_pid=os.getpid(), player_start_ticks=parent.proc_start(os.getpid()),
            generation_root=str(generations), deadline_unix=time.time() + 1.5, **binding)
        root = tmp_path / 'bridge'
        root.mkdir()
        bridge = threading.Thread(target=parent.serve, args=(config, root))
        bridge.start()
        deadline = time.monotonic() + 1
        while not (root / 'ACTIVE.json').exists() and time.monotonic() < deadline:
            time.sleep(.01)
        assert (root / 'ACTIVE.json').exists()
        raw = parent.canonical(request) + b'\n'
        result = json.loads(parent.forward(raw, endpoint))
        assert received == [raw]
        assert result['receipt_sha256'] == response['receipt_sha256']
        assert result['report']['feedback'] == response['report']['feedback']
        assert parent.EPOCH in result['report']['instruction']
        bridge.join(3)
        backend.join(1)
        assert not bridge.is_alive()
        assert endpoint.stat().st_ino == config['endpoint_inode']
        assert json.loads((root / 'private' / identifier / 'SOURCE.json').read_bytes())['original_response'] == response


def test_exposure_rejects_previously_rendered_scene_without_exporting_text(tmp_path):
    life = tmp_path / 'life'
    records = life / 'stream/records'
    records.mkdir(parents=True)
    scene = 'An invented synthetic astronaut balances a wooden chair beside a giant clock.'
    records.joinpath('00000000000000000000.json').write_text(json.dumps(dict(index=0,
        kind='REQUEST', document=dict(messages=[dict(role='user', content=scene)]))))
    capture = dict(head_index=0, head_sha256='a' * 64, sources=[dict(sleep_complete_index=1)],
        exposure=dict(complete=True))
    result = source_exposure.audit(life, dict(contests=[dict(contest_id='synthetic', canonical_scene=scene)]), capture)
    assert result['eligible'] is False and result['matched_record_indices']['synthetic'] == [0]
    assert scene not in json.dumps(result)


def test_probe_does_not_load_source_parent_or_optimizer():
    from research_loop.workers.rohin233_kept_age_probe_20260918 import probe
    source = Path(probe.__file__).read_text()
    assert 'parent_tokens=0,source_parent_text_loaded=False' in source
    assert "source['sleep_complete_sha256']==identity['sleep_complete_sha256']" in source
    assert 'contract.run_cell(backend,scene,seed,score,emit)' in source


def test_readonly_parent_receipt_observers_compile():
    from research_loop.workers.rohin233_kept_age_probe_20260918 import observe_parent, observe_pair
    compile(observe_parent.CODE, '<parent-render>', 'exec')
    compile(observe_pair.CODE, '<pair-render>', 'exec')


def test_retained_capture_is_not_eligibility_and_does_not_copy_context(tmp_path):
    from research_loop.workers.rohin233_kept_age_probe_20260918 import capture_retained
    target = fixture(tmp_path)
    checkpoint = Path(target['root']) / 'checkpoints/sleep_000001'
    (checkpoint / 'adapter').mkdir(parents=True)
    names = ['README.md', 'adapter_config.json', 'adapter_model.safetensors']
    for name in names:
        (checkpoint / 'adapter' / name).write_bytes(b'synthetic-not-model')
    (checkpoint / 'COMMIT.json').write_text(json.dumps(dict(base_sha256=enroll.BASE,
        adapter_state_sha256='d' * 64, optimizer_steps=0,
        adapter_files={name:capture_retained.sha(checkpoint / 'adapter' / name) for name in names})))
    entry = enroll.page(target, {})['entries'][0]
    source = capture_retained.capture(target, entry, tmp_path / 'custody')
    assert source['eligibility'].startswith('PENDING') and source['relative_sleep'] is None
    assert source['source_context_copied_or_loaded'] is False and source['learner_signals'] == []
    assert capture_retained.capture(target, entry, tmp_path / 'custody') == source
    (checkpoint / 'adapter/adapter_model.safetensors').write_bytes(b'tamper')
    with pytest.raises(ValueError, match='retained_adapter_commit_hashes'):
        capture_retained.capture(target, entry, tmp_path / 'bad')
