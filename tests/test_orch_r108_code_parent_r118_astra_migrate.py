import pytest
import json
import subprocess
from pathlib import Path

from gpu import orch_r108_code_parent_r118_astra_migrate as migration


def test_only_published_claims_allow_broker_boundary():
    snapshot = dict(config_sha256='bound', lock_present=True, unpublished=[], partial=[], claims=3)
    assert migration.settled(snapshot, 'bound')
    assert not migration.settled(snapshot, 'changed_config')


@pytest.mark.parametrize('change', [dict(unpublished=['active.claim']),
    dict(partial=['response.partial']), dict(lock_present=False), dict(claims=True), dict(claims=-1)])
def test_unfinished_delivery_or_unknown_ownership_never_migrates(change):
    snapshot = dict(config_sha256='bound', lock_present=True, unpublished=[], partial=[], claims=3)
    assert not migration.settled(dict(snapshot, **change), 'bound')


def test_boundary_binds_canonical_config_and_actual_publication(tmp_path, monkeypatch):
    class LocalStore:
        def shell(self, script):
            return subprocess.run(['bash', '-c', script], text=True, capture_output=True, check=True)

    monkeypatch.setattr(migration, 'REMOTE_ROOT', str(tmp_path))
    ledger = tmp_path/'parent_claude'
    (ledger/'RUNNER.lock').mkdir(parents=True)
    (tmp_path/'parent_queue').mkdir()
    config = {'family':'code', 'deadline':100}
    (ledger/'CONFIG.json').write_text(json.dumps(config, indent=2))
    snapshot = migration.boundary(LocalStore())
    assert migration.settled(snapshot, migration.astra.transport.digest(config))
    (ledger/'CALL.claim').mkdir()
    assert not migration.settled(migration.boundary(LocalStore()), migration.astra.transport.digest(config))


def test_exact_script_or_module_entry_and_exact_config():
    root = Path('/tmp/owned')
    assert migration.owned_command(['python3', '-B', str(root/'source/gpu/orch_r108_code_parent_r115_astra.py'),
        '--config', str(root/'CONFIG.json')], root)
    assert migration.owned_command(['python3', '-m', 'gpu.orch_r108_code_parent_r115_astra',
        '--config', str(root/'CONFIG.json')], root)
    assert not migration.owned_command(['other.py', '--config', str(root/'CONFIG.json')], root)
    assert not migration.owned_command(['gpu.orch_r108_code_parent_r115_astra', '--config', '/tmp/foreign/CONFIG.json'], root)
