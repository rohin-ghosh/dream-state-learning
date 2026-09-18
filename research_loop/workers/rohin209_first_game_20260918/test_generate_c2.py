"""CPU-only fixtures: these tests do not load C2, Torch, or any GPU model."""

from copy import deepcopy
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import struct
import subprocess
from types import SimpleNamespace

import pytest


SPEC = importlib.util.spec_from_file_location('r209_generate_c2', Path(__file__).with_name('generate_c2.py'))
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


@pytest.fixture
def manifest(tmp_path):
    document = dict(mode='DEVELOPMENT', development_contest_ids=['toy-0', 'toy-1', 'toy-2'],
                    reserved_final_contest_ids=['unused-final'], contests=[
        dict(contest_id=f'toy-{index}', canonical_scene=f'Synthetic factual scene {index}.',
             image=f'opaque-image-{index}', split='agent_development') for index in range(3)])
    path = tmp_path/'GAME_MANIFEST.json'
    path.write_text(json.dumps(document))
    return path


class FakeBackend:
    def __init__(self, act, *, terminal=True, truncated=False):
        self.act, self.terminal, self.truncated = act, terminal, truncated
        self.calls = []
        self.frozen_checks = 0
        self.identity = dict(test_double=True, GPU_calls=0)

    def generate(self, messages, max_new_tokens):
        self.calls.append((deepcopy(messages), max_new_tokens))
        raw = 'Synthetic THINK: choose one direction without inventing feedback.' if len(self.calls) == 1 else self.act
        return dict(messages=deepcopy(messages), prompt_tokens=100+len(self.calls), token_ids=[11, 12, 13],
                    raw=raw, terminal=True if len(self.calls) == 1 else self.terminal,
                    truncated=False if len(self.calls) == 1 else self.truncated)

    def verify_unchanged(self):
        self.frozen_checks += 1
        return dict(test_double=True, GPU_calls=0, weights_unchanged=True)


def fixture_provenance():
    return dict(checkpoint=dict(sha256='synthetic-test-checkpoint-not-a-live-receipt'))


def test_manifest_projects_only_three_scene_facts_and_never_opens_image_handles(manifest):
    scenes, reference = generator.load_scenes(manifest)
    assert len(scenes) == 3
    assert all(set(scene) == {'contest_id', 'canonical_scene'} for scene in scenes)
    assert reference['sha256'] == hashlib.sha256(manifest.read_bytes()).hexdigest()


@pytest.mark.parametrize('mutation', ['raw_captions', 'score', 'panel', 'final', 'duplicates', 'four_scenes'])
def test_private_or_non_development_manifest_is_rejected_before_model_load(manifest, mutation):
    document = json.loads(manifest.read_bytes())
    if mutation == 'raw_captions':
        document['human_captions'] = ['synthetic forbidden fixture']
    elif mutation == 'score':
        document['contests'][0]['score'] = 0.9
    elif mutation == 'panel':
        document['contests'][0]['reference_panel'] = ['synthetic forbidden fixture']
    elif mutation == 'final':
        document['contests'][0]['split'] = 'final_evaluation'
    elif mutation == 'duplicates':
        document['development_contest_ids'][1] = 'toy-0'
    else:
        document['contests'].append(document['contests'][0])
    manifest.write_text(json.dumps(document))
    with pytest.raises(generator.ProposalError):
        generator.load_scenes(manifest)


def test_snapshot51_declared_format_and_checkpoint_pins_match_actual_source_manifest():
    repo = Path(__file__).resolve().parents[3]
    source = repo/'research_loop/workers/rohin174_parenting_20260917/node5/R195_FLEET/MSG201/C2_SNAPSHOT_20260918T021847Z/MANIFEST.json'
    document = json.loads(source.read_bytes())
    assert document['cycle'] == 51
    assert document['checkpoint']['adapter_state_sha256'] == generator.ADAPTER_STATE_SHA256
    assert document['checkpoint']['adapter_files'] == generator.ADAPTER_FILES
    assert next(row['sha256'] for row in document['files'] if row['relative'] == 'complete/COMMIT.json') == generator.COMMIT_SHA256
    assert not any(row['relative'].startswith('complete/adapter/') and row['relative'].endswith('.pt') for row in document['files'])


def test_checkpoint_verifier_rejects_judge_weights_and_native_pt(tmp_path, monkeypatch):
    adapter = tmp_path/'adapter'
    adapter.mkdir()
    files = {}
    for name in generator.ADAPTER_FILES:
        payload = ('synthetic fixture '+name).encode()
        (adapter/name).write_bytes(payload)
        files[name] = hashlib.sha256(payload).hexdigest()
    checkpoint = dict(base_sha256=generator.BASE_SHA256, adapter_state_sha256=generator.ADAPTER_STATE_SHA256,
                      optimizer_steps=4908, adapter_files=files)
    commit = tmp_path/'COMMIT.json'
    commit.write_text(json.dumps(checkpoint))
    monkeypatch.setattr(generator, 'ADAPTER_FILES', files)
    monkeypatch.setattr(generator, 'COMMIT_SHA256', hashlib.sha256(commit.read_bytes()).hexdigest())
    assert generator.verify_checkpoint(adapter)['source_complete'] == 51
    (adapter/'adapter_model.safetensors').write_bytes(b'different synthetic judge weights')
    with pytest.raises(generator.ProposalError, match='adapter_bytes_changed'):
        generator.verify_checkpoint(adapter)
    (adapter/'native.pt').write_bytes(b'not loaded or unpickled')
    with pytest.raises(generator.ProposalError, match='native_pt'):
        generator.verify_checkpoint(adapter)


@pytest.mark.parametrize('raw', [
    'prose before []', '```json\n[]\n```', '[{"contest_id":"toy-0","text":"unfinished"}',
    '[{"contest_id":"toy-0","text":"first","text":"second"}]',
    '[{"contest_id":"toy-0","text":"caption","origin":{"actor":"C2"}}]',
    '[{"contest_id":"unused-final","text":"caption"}]',
    '[{"contest_id":"toy-0","text":""}]', '[NaN]',
    json.dumps([dict(contest_id='toy-0', text='word '*51)]),
    json.dumps([dict(contest_id='toy-0', text='synthetic caption')]*11),
])
def test_caption_parser_never_repairs_slices_relabels_or_truncates(raw):
    with pytest.raises((generator.ProposalError, json.JSONDecodeError)):
        generator.parse_captions(raw, {'toy-0', 'toy-1', 'toy-2'})


def test_actual_decoded_caption_text_is_preserved_exactly():
    text = '  Synthetic punctuation: naïve — café.  '
    assert generator.parse_captions(json.dumps([dict(contest_id='toy-1', text=text)]), {'toy-1'})[0]['text'] == text


def test_one_think_act_opportunity_records_hashes_tokens_and_unmodified_actions(manifest, tmp_path):
    scenes, unused_reference = generator.load_scenes(manifest)
    backend = FakeBackend(json.dumps([dict(contest_id='toy-1', text='  A synthetic caption.  ')]))
    output = tmp_path/'proposal'
    output.mkdir()
    result = generator.opportunity(backend, scenes, fixture_provenance(), output)
    assert result['status'] == 'CAPTIONS_GENERATED' and result['generation_calls'] == 2
    assert result['total_prompt_tokens'] == 203 and result['total_generated_tokens'] == 6
    assert backend.frozen_checks == 1 and len(backend.calls) == 2
    assert [call[1] for call in backend.calls] == [generator.THINK_TOKENS, generator.ACT_TOKENS]
    assert len(backend.calls[0][0]) == 3 and len(backend.calls[1][0]) == 5
    assert backend.calls[1][0][-2]['content'] == json.loads((output/'THINK_GENERATION.json').read_bytes())['raw']
    for phase in ('THINK', 'ACT'):
        receipt = json.loads((output/(phase+'_RECEIPT.json')).read_bytes())
        assert receipt['input']['sha256'] == hashlib.sha256((output/(phase+'_INPUT.json')).read_bytes()).hexdigest()
        assert receipt['generation']['sha256'] == hashlib.sha256((output/(phase+'_GENERATION.json')).read_bytes()).hexdigest()
    actions = json.loads((output/'actions.json').read_bytes())
    assert set(actions[0]) == {'contest_id', 'text', 'origin'}
    assert actions[0]['text'] == '  A synthetic caption.  '
    assert actions[0]['origin']['stage'] == 'ACT' and actions[0]['origin']['action_index'] == 0
    assert actions[0]['origin']['generation_sha256'] == hashlib.sha256((output/'ACT_GENERATION.json').read_bytes()).hexdigest()
    assert not actions[0]['origin']['text_repaired'] and not result['learning_or_retention_demonstrated']
    assert 'opaque-image' not in json.dumps(backend.calls) and 'unused-final' not in json.dumps(backend.calls)


def test_zero_chosen_captions_is_not_filled_with_operator_fixtures(manifest, tmp_path):
    scenes, unused_reference = generator.load_scenes(manifest)
    result = generator.opportunity(FakeBackend('[]'), scenes, fixture_provenance(), tmp_path)
    assert result['status'] == 'NO_PROPOSALS' and result['action_count'] == 0
    assert json.loads((tmp_path/'actions.json').read_bytes()) == []


@pytest.mark.parametrize('raw,terminal,truncated', [('not JSON', True, False), ('[]', False, True)])
def test_failed_generation_preserves_actual_input_and_raw_without_retry(manifest, tmp_path, monkeypatch, raw, terminal, truncated):
    backend = FakeBackend(raw, terminal=terminal, truncated=truncated)
    monkeypatch.setattr(generator, 'verify_checkpoint', lambda root: fixture_provenance())
    monkeypatch.setattr(generator, 'FrozenC2', lambda *args: backend)
    output = tmp_path/'failed-proposal'
    args = SimpleNamespace(game_manifest=str(manifest), base_root='not-read', adapter_root='not-read', output=str(output), device='cuda:0')
    assert generator.run(args) == 1
    assert len(backend.calls) == 2
    assert json.loads((output/'ACT_GENERATION.json').read_bytes())['raw'] == raw
    assert (output/'THINK_INPUT.json').exists() and (output/'ACT_INPUT.json').exists()
    assert (output/'FAILED.json').exists() and not (output/'actions.json').exists()
    with pytest.raises(FileExistsError):
        generator.run(args)


def test_no_model_load_with_unassigned_device(monkeypatch):
    monkeypatch.delenv('CUDA_VISIBLE_DEVICES', raising=False)
    with pytest.raises(generator.ProposalError, match='assigned_single_GPU'):
        generator.FrozenC2('not-read', 'not-read', 'cuda:0')


def test_standalone_tensor_hash_matches_existing_native_algorithm_without_torch(monkeypatch):
    class TensorFixture:
        dtype = 'torch.float32'

        def __init__(self, values):
            self.shape = (len(values),)
            self.payload = struct.pack('<'+'f'*len(values), *values)

        def detach(self):
            return self

        cpu = contiguous = detach

        def reshape(self, size):
            assert size == -1
            return self

        def view(self, dtype):
            assert dtype == 'fixture-uint8'
            return self

        def numpy(self):
            return SimpleNamespace(tobytes=lambda: self.payload)

    fake_torch = SimpleNamespace(is_tensor=lambda value: isinstance(value, TensorFixture), uint8='fixture-uint8')
    monkeypatch.setitem(sys.modules, 'torch', fake_torch)
    repo = Path(__file__).resolve().parents[3]
    tree = ast.parse((repo/'organism_v6/pcfl_vertical_train.py').read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_state_hash')
    namespace = dict(hashlib=hashlib, canonical=generator.canonical)
    exec(compile(ast.Module(body=[function], type_ignores=[]), '<existing-native-hash-only>', 'exec'), namespace)
    state = {'z.lora_A.default.weight': TensorFixture([1.25, -3.5]), 'a.weight': TensorFixture([0.0])}
    assert generator.tensor_state_hash(state, fake_torch) == namespace['_state_hash'](state)
    changed = dict(state, **{'a.weight': TensorFixture([1.0])})
    assert generator.tensor_state_hash(changed, fake_torch) != generator.tensor_state_hash(state, fake_torch)


def test_help_is_standalone_without_model_dependencies_or_gpu_calls(tmp_path):
    script = Path(__file__).with_name('generate_c2.py').resolve()
    result = subprocess.run([sys.executable, '-I', str(script), '--help'], cwd=tmp_path,
                            capture_output=True, text=True, check=True)
    assert all('--'+name in result.stdout for name in ('game-manifest', 'base-root', 'adapter-root', 'output', 'device'))
    assert list(tmp_path.iterdir()) == []
