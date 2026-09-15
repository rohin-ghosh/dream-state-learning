"""Focused replay, exactly-once ingestion, and torn-checkpoint regressions."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from organism_v6 import orch_combined_l1_continual as policy
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


def entry(target='FINAL: 4'):
    target_sha = hashlib.sha256(target.encode()).hexdigest()
    source_digest = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return dict(encoding='math', corpus='TEST', index=0, target_sha256=target_sha,
        row=dict(target=target, target_sha256=target_sha, call=dict(raw=target), task_id='train-1',
            student_prefix=[dict(role='user', content='What is 2 + 2?')],
            review=dict(full_text_read=True, status='PASS', neutral_prefix_compatible=True, target_sha256=target_sha,
                raw_call_sha256=source_digest(dict(raw=target)),
                student_prefix_sha256=source_digest([dict(role='user', content='What is 2 + 2?')])),
            admitted=True, semantic_status='PASS', outcome_pass=True, token_contract_pass=True))


def packet(rows=None):
    rows = rows or [entry()]
    return dict(schema='COMBINED_CONTINUAL_ADMITTED_BATCH_V1', batch_id='batch1',
        origin='EXTERNAL_GENERATION', parenting_or_l2_experience=False,
        author_qualified=True, provenance={'manifest_sha256': 'a' * 64}, rows=rows,
        rows_sha256=policy.digest(rows))


def append(state, material, **kwargs):
    return policy.append_batch(state, material, held_math=kwargs.get('held_math', []),
        held_route=kwargs.get('held_route', []), held_question_hashes=kwargs.get('held_question_hashes', []))


@pytest.mark.parametrize('count', [16, 26, 764, 2394, 2470, 2471])
def test_unbounded_layout_retains_original_global_batches(count):
    continual = policy.ContinualLayout(count, 2)
    original = GoalReplayLayout(count, 16)
    for update in range(1, original.updates + 1):
        assert continual.training_indexes(update) == original.training_indexes(update)
        positions = policy.rank_positions(0) + policy.rank_positions(1)
        assert sorted(positions) == [0, 1, 2, 3]
    assert len(continual.training_indexes(original.updates + 1)) == 4


def test_all_legacy_exposures_and_whole_trajectory_cycle():
    layout = policy.ContinualLayout(2394, 2)
    counts = [0] * layout.row_count
    for update in range(1, 2407):
        for index in layout.training_indexes(update):
            counts[index] += 1
    assert counts == list(GoalReplayLayout(2394, 2).presentation_counts())
    assert set(layout.masked_row_indexes('NEW_TRAJECTORY_LOSS_OFF')) == set(range(222, layout.row_count))


def test_exactly_once_and_target_dedup_preserve_initial_multiset():
    original = [entry('same'), entry('same')]
    initial = policy.initial_state(original, 'initial')
    material = packet([entry('same'), entry('new')])
    state = append(initial, material)
    assert state['rows'][:2] == original and len(state['rows']) == 3
    assert state['ingested'][0]['added'] == 1 and len(state['duplicates']) == 1
    assert append(state, material) is state
    altered = deepcopy(material)
    altered['provenance']['manifest_sha256'] = 'different'
    with pytest.raises(ValueError, match='rebound'):
        append(state, altered)


@pytest.mark.parametrize('change', ['admitted', 'semantic_status', 'outcome_pass', 'token_contract_pass',
                                  'raw', 'hash', 'review', 'prefix'])
def test_reject_invalid_admission_without_mutating_state(change):
    material = packet()
    row = material['rows'][0]['row']
    if change in ('admitted', 'outcome_pass', 'token_contract_pass'):
        row[change] = False
    elif change == 'semantic_status':
        row[change] = 'UNREVIEWED'
    elif change == 'raw':
        row['call']['raw'] = 'edited'
    elif change == 'hash':
        row['target_sha256'] = 'bad'
    elif change == 'review':
        row['review']['full_text_read'] = False
    else:
        row['student_prefix'][0]['role'] = 'system'
    material['rows_sha256'] = policy.digest(material['rows'])
    state = policy.initial_state([], 'initial')
    before = deepcopy(state)
    with pytest.raises(ValueError):
        append(state, material)
    assert state == before


def test_held_id_question_hash_and_route_exclusions():
    state, material = policy.initial_state([], 'initial'), packet()
    for kwargs in [dict(held_math=['train-1']), dict(held_route=['What is 2']),
                   dict(held_question_hashes=[hashlib.sha256(b'What is 2 + 2?').hexdigest()])]:
        with pytest.raises(ValueError, match='held_'):
            append(state, material, **kwargs)


def staged_checkpoint(tmp_path):
    staging = tmp_path / '000128.pending'
    (staging / 'adapter').mkdir(parents=True)
    for name in ['optimizer.pt', 'rank0.pt', 'rank1.pt', 'adapter/adapter_config.json',
                 'adapter/adapter_model.safetensors']:
        (staging / name).write_bytes(name.encode())
    return staging


def test_checkpoint_commit_and_corruption_fail_closed(tmp_path):
    staging = staged_checkpoint(tmp_path)
    destination = tmp_path / '000128'
    with pytest.raises(ValueError, match='uncommitted'):
        policy.verify_checkpoint(staging)
    committed = policy.commit_checkpoint(staging, destination, dict(update=128, cursor=256))
    assert policy.verify_checkpoint(destination) == committed
    (destination / 'optimizer.pt').write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='hash_drift'):
        policy.verify_checkpoint(destination)


def test_torn_checkpoint_never_commits(tmp_path):
    staging = staged_checkpoint(tmp_path)
    (staging / 'rank1.pt').unlink()
    with pytest.raises(ValueError, match='missing'):
        policy.commit_checkpoint(staging, tmp_path / '000128', {})
    assert not (tmp_path / '000128').exists()


def test_checkpoint_cannot_replace_existing_evidence(tmp_path):
    staging = staged_checkpoint(tmp_path)
    destination = tmp_path / '000128'
    destination.mkdir()
    with pytest.raises(ValueError, match='already_exists'):
        policy.commit_checkpoint(staging, destination, {})


def test_matched_pair_boundary_requires_same_version_and_exposure():
    full = dict(update=128, corpus_sha256='corpus', corpus_version=1,
                exposure_counts=[1, 2], reference_tokens=500, supervised_tokens=500)
    off = dict(full, supervised_tokens=50)
    assert policy.pair_boundary(full, off) == 128
    for key in ('update', 'corpus_sha256', 'corpus_version', 'exposure_counts', 'reference_tokens'):
        changed = dict(off, **{key: 'changed'})
        with pytest.raises(ValueError, match='drift'):
            policy.pair_boundary(full, changed)


def test_two_rank_gradient_sum_matches_global_token_normalization():
    torch = pytest.importorskip('torch')
    parameter = torch.tensor([0.2, -0.3], requires_grad=True)
    features = torch.tensor([[1., 2.], [2., 1.], [3., 1.], [1., 3.]])
    targets = torch.tensor([1., 0., 2., 0.])
    weights = torch.tensor([3., 2., 7., 5.])
    reference = weights.sum()
    for masked in (False, True):
        active = weights.clone()
        if masked:
            active[2:] = 0
        loss = (((features @ parameter - targets) ** 2) * active).sum() / reference
        expected = torch.autograd.grad(loss, parameter)[0]
        actual = torch.zeros_like(parameter)
        for world_size in (1, 2, 3):
            actual = torch.zeros_like(parameter)
            for rank in range(world_size):
                positions = list(policy.rank_positions(rank, world_size))
                local_loss = (((features[positions] @ parameter - targets[positions]) ** 2)
                              * active[positions]).sum() / reference
                actual += torch.autograd.grad(local_loss, parameter)[0]
            assert torch.allclose(actual, expected)


def test_parenting_and_l2_rows_are_quarantined():
    material = packet()
    material['parenting_or_l2_experience'] = True
    with pytest.raises(ValueError, match='quarantined'):
        append(policy.initial_state([], 'initial'), material)


def test_optimizer_and_rng_resume_matches_uninterrupted_cpu():
    torch = pytest.importorskip('torch')
    torch.manual_seed(8203)
    parameter = torch.nn.Parameter(torch.tensor([1., 2.]))
    optimizer = torch.optim.AdamW([parameter], lr=3e-5)
    def update():
        optimizer.zero_grad()
        (parameter * torch.rand(2)).sum().backward()
        optimizer.step()
    update()
    saved_parameter, saved_optimizer, saved_rng = parameter.detach().clone(), deepcopy(optimizer.state_dict()), torch.get_rng_state()
    update()
    expected = parameter.detach().clone()
    with torch.no_grad():
        parameter.copy_(saved_parameter)
    optimizer.load_state_dict(saved_optimizer)
    torch.set_rng_state(saved_rng)
    update()
    assert torch.equal(parameter, expected)


def require_delta76_fixtures(root):
    paths = (root / 'INBOX/math_final_review_delta76_20260915/BOUND_PACKET.json',
        root / 'PACKET/ADMITTED_ROWS.json',
        root / 'INBOX/math_final_review_delta76_20260915/ROWS.json')
    missing = [str(path.relative_to(root)) for path in paths if not path.is_file()]
    if missing:
        pytest.skip('immutable experiment fixtures not in source-only checkout: ' + ', '.join(missing))
    return paths[0]


@pytest.mark.parametrize('available', range(8))
def test_delta76_fixture_availability_requires_all_inputs(tmp_path, available):
    paths = ('INBOX/math_final_review_delta76_20260915/BOUND_PACKET.json',
        'PACKET/ADMITTED_ROWS.json', 'INBOX/math_final_review_delta76_20260915/ROWS.json')
    for index, name in enumerate(paths):
        if available & (1 << index):
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{}')
    if available == 7:
        assert require_delta76_fixtures(tmp_path) == tmp_path / paths[0]
    else:
        with pytest.raises(pytest.skip.Exception, match='immutable experiment fixtures'):
            require_delta76_fixtures(tmp_path)


def test_real_main_delta76_is_exactly_once_and_preserves_rows():
    repository = Path(__file__).resolve().parents[1]
    root = repository / 'research_notes/analysis/orch_combined_l1_continual_20260915_attempt1'
    path = require_delta76_fixtures(root)
    original = json.loads((root / 'PACKET/ADMITTED_ROWS.json').read_text())
    material = json.loads(path.read_text())
    state = append(policy.initial_state(original, 'initial'), material)
    assert len(state['rows']) == 2470
    assert state['rows'][:2394] == original
    assert [entry['row'] for entry in state['rows'][2394:]] == json.loads((path.parent / 'ROWS.json').read_text())
    assert append(state, material) is state


def test_admission_repeats_full_scan_not_identity_waiver(tmp_path):
    from gpu.orch_combined_l1_continual_guard import admit_devices
    reports = iter([dict(clear=False, blocking_reasons=['process_identity_drift:4583']),
                    dict(clear=True, blocking_reasons=[])])
    calls = []
    def scan(index, service):
        calls.append(index)
        return next(reports)
    admit_devices(tmp_path, [2], 'TEST', scan=scan, pause=lambda seconds: None)
    assert calls == [2, 2]
    assert len(list((tmp_path / 'ADMISSION_ATTEMPTS').glob('*.json'))) == 2
    assert json.loads((tmp_path / 'TEST_2.json').read_text())['clear'] is True


def test_admission_never_waives_owner_or_unknown_visibility(tmp_path):
    from gpu.orch_combined_l1_continual_guard import admit_devices
    for reason in ('open_device_pid:1', 'unknown_minor_process_visibility:1:PermissionError'):
        with pytest.raises(AssertionError, match='fresh_gpu_admission_failed'):
            admit_devices(tmp_path, [2], reason.split(':')[0],
                scan=lambda index, service: dict(clear=False, blocking_reasons=[reason]), pause=lambda unused: None)


def test_admission_instability_is_bounded(tmp_path):
    from gpu.orch_combined_l1_continual_guard import admit_devices
    with pytest.raises(AssertionError, match='unstable_full_process_snapshot'):
        admit_devices(tmp_path, [2], 'BOUNDED', scan=lambda index, service:
            dict(clear=False, blocking_reasons=['process_identity_drift:4583']),
            pause=lambda unused: None, attempts=2)


def test_worker_encoder_respects_fixed1452_entrypoint(monkeypatch):
    from gpu import orch_combined_l1_continual_run as run
    rows = [dict(encoding='terse_route' if index < 1452 else 'math', index=index, row={})
            for index in range(2394)]
    calls = []
    def encode_initial(material, tokenizer):
        assert len(material) == 2394
        calls.append(len(material))
        return tuple(range(2394))
    monkeypatch.setattr(run.combined, 'encode_rows', encode_initial)
    monkeypatch.setattr(run.encoding, 'encode_rows', lambda material, tokenizer: (9999,))
    cache = {}
    assert run.encode_corpus(rows, object(), cache) == tuple(range(2394))
    expanded = rows + [dict(encoding='math', index=2394, row={})]
    assert run.encode_corpus(expanded, object(), cache)[-1] == 9999
    assert calls == [2394]


def gloo_sum_worker(rank, world_size, rendezvous):
    import torch
    torch.distributed.init_process_group('gloo', init_method=rendezvous, rank=rank, world_size=world_size)
    positions = policy.rank_positions(rank, world_size)
    weights = torch.tensor([3., 2., 7., 5.])
    gradient = weights[list(positions)].sum().reshape(1) / weights.sum()
    torch.distributed.all_reduce(gradient, op=torch.distributed.ReduceOp.SUM)
    assert torch.allclose(gradient, torch.tensor([1.]))
    torch.distributed.barrier()
    torch.distributed.destroy_process_group()


def test_actual_three_process_gloo_global_normalization(tmp_path):
    torch = pytest.importorskip('torch')
    torch.multiprocessing.spawn(gloo_sum_worker, args=(3, 'file://' + str(tmp_path / 'rendezvous')), nprocs=3, join=True)
