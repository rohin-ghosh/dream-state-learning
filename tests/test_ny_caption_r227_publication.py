import copy
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from research_loop.workers.rohin221_continuous_caption_20260918 import publish_hourly as publisher


@pytest.fixture
def reference():
    return json.loads((publisher.ROOT / 'R227_HOURLY_20260918T090004Z.json').read_bytes())


def write_cut(source, document, stamp='20260918T100000Z'):
    source.mkdir(parents=True, exist_ok=True)
    document = copy.deepcopy(document)
    document['observed_cut_utc'] = '2026-09-18T10:00:00+00:00'
    filename = 'R227_HOURLY_' + stamp + '.json'
    payload = publisher.encode(document)
    (source / filename).write_bytes(payload)
    (source / filename).with_suffix('.md').write_text(publisher.render_markdown(document))
    (source / 'R227_HOURLY_LATEST.json').write_text(json.dumps(dict(json=str(source / filename),
        sha256=hashlib.sha256(payload).hexdigest())))
    return filename


@pytest.fixture
def cut(tmp_path, reference):
    source = tmp_path / 'reports'
    filename = write_cut(source, reference)
    return publisher.load_cut(source, filename)


@pytest.fixture
def repositories(tmp_path):
    remote, seed, worktree = [tmp_path / name for name in ('remote.git', 'seed', 'publication')]
    subprocess.run(['git', 'init', '--bare', '--initial-branch=main', str(remote)], check=True, capture_output=True)
    seed.mkdir()
    publisher.git(seed, 'init', '--initial-branch=main')
    publisher.git(seed, 'config', 'user.name', 'PublicationTest')
    publisher.git(seed, 'config', 'user.email', 'test@example.invalid')
    coordination = seed / publisher.COORDINATION
    coordination.parent.mkdir(parents=True)
    coordination.write_text('Existing coordination.\n')
    publisher.git(seed, 'add', '--', publisher.COORDINATION)
    publisher.git(seed, 'commit', '-m', 'Synthetic initial publication fixture')
    publisher.git(seed, 'remote', 'add', 'origin', str(remote))
    publisher.git(seed, 'push', '-u', 'origin', 'main')
    publisher.ensure_worktree(seed, worktree)
    return remote, seed, worktree


def test_exact_safe_cut_and_relative_reference(cut):
    assert cut['document']['source_receipt']['path'].startswith(publisher.WORKER.as_posix())
    assert not cut['document']['source_receipt']['path'].startswith('/')
    assert cut['document']['players'][1]['cumulative']['accepted_before_novelty'] == 192


@pytest.mark.parametrize('payload', ['synthetic.example.invalid', '192.0.2.10', '2001:db8::1',
    '-----BEGIN OPENSSH PRIVATE KEY-----', 'ghp_' + 'x' * 32])
def test_privacy_scan_rejects_host_ip_or_key(payload):
    with pytest.raises(publisher.PublicationError, match='privacy_scan_rejected'):
        publisher.privacy_scan(payload)


def test_timestamp_not_mistaken_for_ipv6():
    publisher.privacy_scan('2026-09-18T09:00:04.900572+00:00')


def test_raw_transcript_and_unknown_strings_fail_closed(reference):
    reference['raw_act'] = 'An actual child transcript must never be public here.'
    with pytest.raises(publisher.PublicationError, match='unknown_report_field'):
        publisher.normalized_report(reference)
    reference.pop('raw_act')
    reference['definitions']['accepted'] = 'A transcript hidden in an allowed field.'
    with pytest.raises(publisher.PublicationError, match='nonaggregate_or_unknown_report_text'):
        publisher.normalized_report(reference)


def test_error_report_is_not_published(reference):
    reference['errors'] = {'frozen_base': 'synthetic-private-host'}
    with pytest.raises(publisher.PublicationError, match='wrong_schema_or_collection_error'):
        publisher.normalized_report(reference)


def test_markdown_injection_and_symlink_rejected(tmp_path, reference):
    source = tmp_path / 'reports'
    filename = write_cut(source, reference)
    markdown = (source / filename).with_suffix('.md')
    markdown.write_text(markdown.read_text() + '\nRaw child transcript.\n')
    with pytest.raises(publisher.PublicationError, match='markdown_not_exact'):
        publisher.load_cut(source, filename)
    markdown.unlink()
    markdown.symlink_to(source / filename)
    with pytest.raises(publisher.PublicationError, match='cut_incomplete_symlink'):
        publisher.load_cut(source, filename)


def test_real_push_append_only_allowlist_root_dirty_and_duplicate_safe(repositories, cut):
    remote, seed, worktree = repositories
    (seed / 'DO_NOT_STAGE').write_text('Unrelated dirty checkout.')
    index = Path(publisher.git(seed, 'rev-parse', '--git-path', 'index').stdout.decode().strip())
    index = seed / index if not index.is_absolute() else index
    original_index = index.read_bytes()
    result = publisher.publish_cut(worktree, cut)
    assert result['status'] == 'pushed'
    assert publisher.git(remote, 'rev-parse', 'main').stdout.decode().strip() == result['commit']
    assert index.read_bytes() == original_index
    changed = publisher.git(worktree, 'show', '--format=', '--name-only', 'HEAD').stdout.decode().splitlines()
    assert set(changed) == {publisher.COORDINATION.as_posix(),
        (publisher.WORKER / cut['filename']).as_posix(), (publisher.WORKER / cut['filename']).with_suffix('.md').as_posix()}
    coordination = (worktree / publisher.COORDINATION).read_text()
    assert coordination.startswith('Existing coordination.\n')
    duplicate = publisher.publish_cut(worktree, cut)
    assert duplicate['status'] == 'already_published'
    assert duplicate['commit'] == result['commit']
    assert (worktree / publisher.COORDINATION).read_text() == coordination


@pytest.mark.parametrize('conflict', [False, True])
def test_nonfastforward_fetch_rebase_retry_or_skip_preserving_commit(repositories, cut, monkeypatch, conflict):
    remote, seed, worktree = repositories
    actual_git = publisher.git
    raced = []

    def race(directory, *arguments, **options):
        assert '--force' not in arguments and '--force-with-lease' not in arguments
        if Path(directory) == worktree and arguments[0] == 'push' and not raced:
            raced.append(True)
            relative = publisher.COORDINATION if conflict else Path('parallel-report.txt')
            target = seed / relative
            if conflict:
                target.write_text(target.read_text() + '\nConcurrent Main append.\n')
            else:
                target.write_text('Independent synthetic publication.\n')
            actual_git(seed, 'add', '--', relative)
            actual_git(seed, 'commit', '-m', 'Parallel publication fixture')
            actual_git(seed, 'push', 'origin', 'main')
        return actual_git(directory, *arguments, **options)

    monkeypatch.setattr(publisher, 'git', race)
    result = publisher.publish_cut(worktree, cut)
    assert result['status'] == ('skipped_rebase_conflict' if conflict else 'pushed')
    assert raced
    publisher.ensure_clean(worktree)
    if conflict:
        assert result['preserved_commit']
        assert b'Concurrent Main append.' in actual_git(remote, 'show', 'main:' + publisher.COORDINATION.as_posix()).stdout
    else:
        assert result['push_attempts'] == 2


def test_foreign_stage_or_root_worktree_rejected(repositories, cut):
    remote, seed, worktree = repositories
    with pytest.raises(publisher.PublicationError, match='refuse_root_dirty_worktree'):
        publisher.ensure_worktree(seed, seed)
    (worktree / 'foreign').write_text('Unrelated work.')
    publisher.git(worktree, 'add', 'foreign')
    with pytest.raises(publisher.PublicationError, match='isolated_worktree_not_clean'):
        publisher.publish_cut(worktree, cut)


def test_completed_pointer_and_state_are_idempotent(tmp_path, reference, monkeypatch):
    source = tmp_path / 'reports'
    write_cut(source, reference)
    calls = []

    def published(worktree, cut):
        calls.append(cut['stamp'])
        return dict(status='already_published', commit='a' * 40, pushed_by_this_companion=False)

    monkeypatch.setattr(publisher, 'publish_cut', published)
    state = {}
    events = tmp_path / 'events.jsonl'
    for unused in range(2):
        publisher.publication_cycle(source, tmp_path / 'worktree', state, events, '20260918T090004Z')
    assert calls == ['20260918T100000Z']
    assert len(events.read_text().splitlines()) == 1
    assert state['20260918T100000Z']['commit'] == 'a' * 40
