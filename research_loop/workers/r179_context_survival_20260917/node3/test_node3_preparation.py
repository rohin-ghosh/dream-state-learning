"""CPU-only tests for the metadata collector; no live or remote actions."""

import ast
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parent


@pytest.fixture
def collector():
    specification = importlib.util.spec_from_file_location('node3_readonly', HERE / 'inspect_node3.py')
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_collector_has_no_process_creation_signal_or_runtime_import():
    tree = ast.parse(HERE.joinpath('inspect_node3.py').read_bytes())
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    assert imports == {'hashlib', 'json', 'os', 're', 'socket', 'stat', 'time'}
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert not attributes.intersection({'kill', 'killpg', 'pidfd_open', 'pidfd_send_signal',
        'Popen', 'run', 'system', 'mkdir', 'write_text', 'write_bytes', 'load_model', 'from_pretrained'})


def test_bound_metadata_is_verified_and_source_symlinks_refuse(collector, tmp_path):
    path = tmp_path / 'metadata.json'
    path.write_text('{"fixture":true}')
    reader = collector.Reader()
    reference = dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    assert reader.bound_json(reference) == {'fixture': True}
    with pytest.raises(ValueError, match='reference_hash'):
        reader.bound_json(dict(reference, sha256='0' * 64))
    link = tmp_path / 'link.json'
    link.symlink_to(path)
    with pytest.raises(ValueError, match='canonical_read'):
        reader.raw(link)


@pytest.mark.parametrize('relative', ['readouts/sleep_000001/COMPLETE.json', 'optimizer_rng.pt', 'adapter/model.safetensors'])
def test_sealed_readouts_and_model_payloads_are_not_opened(collector, tmp_path, relative):
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('must_not_be_read')
    with pytest.raises(ValueError, match='no_sealed_or_model_payload'):
        collector.Reader().raw(path)


def test_update_head_does_not_become_saved_boundary(collector, tmp_path):
    directory = tmp_path / 'stream/records'
    directory.mkdir(parents=True)
    record = dict(index=1, kind='UPDATE', document=dict(fixture=True))
    record['sha256'] = collector.digest(record)
    path = directory / '00000000000000000001.json'
    path.write_text(json.dumps(record))
    result = collector.current_head(collector.Reader(), tmp_path)
    assert result['kind'] == 'UPDATE' and result['clean_saved_boundary'] is False
    assert result['reference']['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_scope_refuses_before_any_host_reads(collector):
    with pytest.raises(ValueError, match='six_scoped_lives'):
        collector.collect(dict(schema='R179_NODE3_READONLY_SEED_V1', lanes=[]))
