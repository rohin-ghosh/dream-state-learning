import importlib.util
import io
from pathlib import Path
import tarfile

import pytest

from gpu import ny_caption_data as data


def exporter():
    path = Path(__file__).resolve().with_name('portable_judge.py')
    spec = importlib.util.spec_from_file_location('portable_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_portable_rebase_preserves_weights_and_omits_private_cases(tmp_path):
    root = tmp_path.resolve()
    weight = data.private_write(root/'checkpoint/humor/model.safetensors', b'synthetic-not-model')
    training = data.private_write(root/'training_config.json', {'synthetic': True})
    original = dict(schema='NY_TRAINED_JUDGE_CONFIG_V1', tau=dict(threshold=None),
        checkpoint={'humor/model.safetensors': dict(weight, path='/old/model.safetensors')},
        private_errors={'caption': 'DO_NOT_EXPORT'}, blind_comparator_input={'caption': 'DO_NOT_EXPORT'})
    result = exporter().portable_config(original, training, root/'checkpoint')
    assert result['checkpoint']['humor/model.safetensors'] == weight
    assert result['tau']['threshold'] is None
    assert result['training_config'] == training
    assert 'private_errors' not in result and 'blind_comparator_input' not in result


def test_portable_rejects_changed_weight_or_path_escape(tmp_path):
    root = tmp_path.resolve()
    weight = data.private_write(root/'checkpoint/model.safetensors', b'synthetic')
    original = dict(checkpoint={'model.safetensors': dict(weight, sha256='0'*64)})
    with pytest.raises(ValueError, match='portable_weights_unchanged'):
        exporter().portable_config(original, {}, root/'checkpoint')
    with pytest.raises(ValueError, match='portable_checkpoint_whitelist'):
        exporter().portable_config(dict(checkpoint={'../escape': weight}), {}, root/'checkpoint')


def test_resume_extracts_existing_archive_without_overwriting_partial(tmp_path):
    root = tmp_path.resolve()
    module = exporter()
    original = data.private_write(root/'checkpoint/model.safetensors', b'partial')
    raw = b'synthetic-complete'
    planned = {'model.safetensors': dict(bytes=len(raw), sha256=module.hashlib.sha256(raw).hexdigest())}
    archive = root/'CHECKPOINT.tar'
    with tarfile.open(archive, 'w:') as stream:
        member = tarfile.TarInfo('model.safetensors')
        member.size = len(raw)
        stream.addfile(member, io.BytesIO(raw))
    archive_ref = data.file_ref(archive)
    with pytest.raises(ValueError, match='preserves_partial_export'):
        module.extract_checkpoint(archive, planned, root/'checkpoint')
    module.extract_checkpoint(archive, planned, root/'checkpoint_resumed_v1')
    assert (root/'checkpoint_resumed_v1/model.safetensors').read_bytes() == raw
    assert data.file_ref(root/'checkpoint/model.safetensors') == original
    assert data.file_ref(archive) == archive_ref


def test_archive_content_hash_is_required(tmp_path):
    root = tmp_path.resolve()
    archive = root/'CHECKPOINT.tar'
    with tarfile.open(archive, 'w:') as stream:
        member = tarfile.TarInfo('model.safetensors')
        member.size = 3
        stream.addfile(member, io.BytesIO(b'bad'))
    with pytest.raises(ValueError, match='portable_checkpoint_transport_hash'):
        exporter().extract_checkpoint(archive, {'model.safetensors': dict(bytes=3, sha256='0'*64)}, root/'new')
