import pytest

from research_loop.workers.rohin183_repo_learning_20260917 import safe_snapshot as snapshot


@pytest.mark.parametrize('path',['gpu/native.py','organism_v6/history.py','research_notes/method.md',
    'research_loop/architecture_intake.py','analysis/methods.md','tests/test_runtime.py'])
def test_broad_safe_sources(path):
    assert snapshot.permitted_path(path)


@pytest.mark.parametrize('path',['gpu/hosts.env','../outside.py','/etc/passwd','research_loop/private/rows.txt',
    'research_loop/workers/r176_probe/runner.py','research_loop/workers/r177_game/data_judge/model.py',
    'research_notes/analysis/evaluation/key.py','research_notes/analysis/report.md','research_loop/COORDINATION.md',
    'research_notes/FINAL/items.txt','research_notes/answer_keys.py','research_notes/scores.json',
    'research_loop/workers/rohin183_repo_learning_20260917/snapshot/foo.py'])
def test_exclusions_before_read(path):
    assert not snapshot.permitted_path(path)


def test_snapshot_preserves_exact_safe_files_without_opening_private_or_links(tmp_path,monkeypatch):
    root=tmp_path/'repo'
    for directory in ('gpu','organism_v6','research_notes','research_loop'):
        (root/directory).mkdir(parents=True)
        (root/directory/'safe.py').write_text('value = 1\n')
    private=root/'research_loop/private'
    private.mkdir()
    (private/'hidden.py').write_text('DO_NOT_READ')
    (root/'gpu/link.py').symlink_to(private/'hidden.py')
    original=snapshot.os.open
    def guarded(path,*args,**kwargs):
        assert 'private' not in str(path)
        return original(path,*args,**kwargs)
    monkeypatch.setattr(snapshot.os,'open',guarded)
    reference=snapshot.build(root,tmp_path/'output')
    assert reference['bytes']>0
    assert (tmp_path/'output/gpu/safe.py').read_bytes()==b'value = 1\n'
    assert not (tmp_path/'output/gpu/link.py').exists()
    assert not (tmp_path/'output/research_loop/private').exists()


def test_resume_preserves_captured_bytes_and_refuses_finalized_snapshot(tmp_path):
    root=tmp_path/'repo'
    for directory in ('gpu','organism_v6','research_notes','research_loop'):
        (root/directory).mkdir(parents=True)
        (root/directory/'safe.py').write_text('current = 2\n')
    destination=tmp_path/'snapshot'
    (destination/'gpu').mkdir(parents=True)
    (destination/'gpu/safe.py').write_text('captured = 1\n')
    snapshot.build(root,destination,resume=True)
    assert (destination/'gpu/safe.py').read_text()=='captured = 1\n'
    with pytest.raises(ValueError,match='immutable_new_snapshot'):
        snapshot.build(root,destination,resume=True)
