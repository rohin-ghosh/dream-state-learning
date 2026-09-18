"""Synthetic CPU-only receipts; no models, private panels, or GPU dispatch."""

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


followup = load_module('r209_followup_test', 'followup_c2.py')
extractor = load_module('r209_literal_extractor_test', 'extract_literal_caption.py')
generator = followup.generator
RAW = '[{"contest_id":"toy-0","text":"Synthetic child caption")]'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(generator.canonical(value))


class Backend:
    def __init__(self, act='[{"contest_id":"toy-1","text":"A synthetic revision."}]', *, stop=None):
        self.act = act
        self.stop = stop
        self.calls = []
        self.frozen_checks = 0
        self.identity = dict(base_sha256=generator.BASE_SHA256, adapter_state_sha256=generator.ADAPTER_STATE_SHA256,
                             all_parameters_frozen=True, tokenizer=dict(test_fixture=True), decoder=dict(do_sample=False))

    def generate(self, messages, max_new_tokens):
        self.calls.append(deepcopy(messages))
        if self.stop == 'overflow':
            raise generator.ProposalError('context_overflow_no_input_truncation')
        phase = 'THINK' if len(self.calls) == 1 else 'ACT'
        return dict(messages=deepcopy(messages), raw='Synthetic new thought.' if phase == 'THINK' else self.act,
                    token_ids=[17, 18], prompt_tokens=110+len(self.calls),
                    terminal=self.stop != phase, truncated=self.stop == phase)

    def verify_unchanged(self):
        self.frozen_checks += 1
        return deepcopy(self.identity)


@pytest.fixture
def receipt_run(tmp_path, monkeypatch):
    manifest = tmp_path/'GAME_MANIFEST.json'
    write(manifest, dict(mode='DEVELOPMENT', development_contest_ids=['toy-0', 'toy-1', 'toy-2'],
                        reserved_final_contest_ids=[], contests=[
                            dict(contest_id=f'toy-{index}', canonical_scene=f'Synthetic scene {index}.',
                                 image=f'opaque-{index}', split='agent_development') for index in range(3)]))
    provenance = dict(source_complete=51, source_optimizer_steps=4908, checkpoint=dict(sha256=generator.COMMIT_SHA256),
                      base_sha256=generator.BASE_SHA256, adapter_state_sha256=generator.ADAPTER_STATE_SHA256)
    monkeypatch.setattr(generator, 'verify_checkpoint', lambda path: deepcopy(provenance))
    monkeypatch.setattr(generator, 'FrozenC2', lambda *args: Backend(RAW))
    previous = tmp_path/'previous'
    assert generator.run(SimpleNamespace(output=str(previous), game_manifest=str(manifest), base_root='unused',
                                        adapter_root='unused', device='cuda:0')) == 1
    extracted = tmp_path/'literal'
    extractor.run(previous, extracted)
    actions = generator.decode((extracted/'actions.json').read_bytes())
    game = tmp_path/'game'
    result = dict(ok=True, accepted=False, status='rejected', rank=55, reference_count=64, top_k=8,
                  raw_score=-6.1875, q=None, pixel_count=0, relevance_score=0.2256, relevance_threshold=-0.002079,
                  contest_id='toy-0', acceptance_mode='relative_rank', scoring_status='relative_rank_development',
                  rejection_reason='outside_top_k', matching_caption=None)
    write(game/'actions/0000.json', dict(action=actions[0], unix=1234.0))
    write(game/'outcomes/0000.json', dict(result=result, unix=1235.0, actor='environment', child_training_target=False))
    write(game/'PUBLIC_RESULT.json', dict(status='COMPLETE_REAL_DEVELOPMENT_GAME',
                                        actions_sha256=generator.file_ref(extracted/'actions.json')['sha256'],
                                        attempts=1, accepted=0, new_pixels=0, completed_unix=1236.0,
                                        per_attempt=[{key: result.get(key) for key in followup.SUMMARY_FIELDS}],
                                        pixel_config=dict(path='/do/not/open/private_config')))
    write(game/'LOADED.json', dict(game_manifest=generator.file_ref(manifest), panel_sha256='not-a-panel'))
    backend = Backend()
    monkeypatch.setattr(generator, 'FrozenC2', lambda *args: backend)
    args = SimpleNamespace(game_manifest=str(manifest), previous_proposals=str(previous),
                           scored_actions=str(extracted/'actions.json'), game_output=str(game),
                           base_root='unused', adapter_root='unused', device='cuda:0', output=str(tmp_path/'followup'))
    return args, backend


def bind(args):
    scenes, reference = generator.load_scenes(args.game_manifest)
    return followup.bind_previous(args.previous_proposals, args.scored_actions, args.game_output, scenes, reference)


def test_delivers_exact_own_raw_and_receipt_feedback_in_next_think(receipt_run):
    args, backend = receipt_run
    assert followup.run(args) == 0
    assert len(backend.calls) == 2 and backend.frozen_checks == 1
    messages = backend.calls[0]
    original = generator.decode((Path(args.previous_proposals)/'ACT_INPUT.json').read_bytes())['messages']
    assert messages[:len(original)] == original
    assert messages[len(original)] == dict(role='assistant', content=RAW)
    feedback = generator.decode(messages[-2]['content'].split('\n', 1)[1])
    assert feedback == bind(args)['feedback']
    assert feedback['attempts'][0]['original_wire_format_valid'] is False
    assert feedback['attempts'][0]['result']['rank'] == 55
    assert feedback['attempts'][0]['result']['raw_score'] == -6.1875
    assert feedback['attempts'][0]['result']['relevance_score'] == 0.2256
    assert feedback['attempts'][0]['result']['q'] is None
    assert messages[-1]['content'] == followup.PARENT_FOLLOWUP
    assert backend.calls[1][:-2] == messages
    assert backend.calls[1][-2]['content'] == 'Synthetic new thought.'
    output = Path(args.output)
    actions = generator.decode((output/'actions.json').read_bytes())
    assert actions[0]['text'] == 'A synthetic revision.'
    assert actions[0]['origin']['text_repaired'] is False
    assert actions[0]['origin']['original_wire_format_valid'] is True
    result = generator.decode((output/'RESULT.json').read_bytes())
    assert result['training_updates'] == 0 and result['judge_calls'] == 0
    assert result['exact_state_continuation_claim'] is False
    assert result['previous_context_truncated'] is False
    assert result['total_generated_tokens'] == 4
    assert generator.decode((output/'CONTEXT_BEFORE.json').read_bytes())[-1]['content'] == RAW
    assert generator.decode((output/'CONTEXT_AFTER.json').read_bytes())[-1]['content'] == backend.act
    rows = [generator.decode(line) for line in (output/'DATASET.jsonl').read_bytes().splitlines()]
    assert [row['phase'] for row in rows][-3:] == ['THINK', 'ACT_INPUT', 'ACT']
    assert all(row['training_applied'] is False and row['child_training_target'] is False for row in rows)
    assert all(row['external_text_masked'] for row in rows if row['actor'] != 'C2')
    assert next(row for row in rows if row['actor'] == 'environment')['source']['sha256'] == result['feedback']['sha256']


def test_never_reads_private_files_or_forwards_extra_result_fields(receipt_run, monkeypatch):
    args, backend = receipt_run
    path = Path(args.game_output)/'outcomes/0000.json'
    outcome = generator.decode(path.read_bytes())
    outcome['result']['reference_panel'] = ['FORBIDDEN_PRIVATE_SENTINEL']
    outcome['result']['matching_caption'] = 'FORBIDDEN_PRIVATE_SENTINEL'
    write(path, outcome)
    original_read = Path.read_bytes

    def guarded_read(path):
        assert path.name not in {'REFERENCE_PANELS.private.json', 'private_config'}
        assert 'snapshots' not in path.parts
        return original_read(path)

    monkeypatch.setattr(Path, 'read_bytes', guarded_read)
    assert followup.run(args) == 0
    assert 'FORBIDDEN_PRIVATE_SENTINEL' not in json.dumps(backend.calls)
    assert all('FORBIDDEN_PRIVATE_SENTINEL' not in path.read_text() for path in Path(args.output).iterdir())


@pytest.mark.parametrize('filename,mutation', [
    ('ACT_GENERATION.json', lambda value: value.update(raw='altered original ACT')),
    ('ACT_INPUT.json', lambda value: value['messages'].append(dict(role='user', content='extra'))),
    ('FROZEN_AFTER.json', lambda value: value.update(adapter_state_sha256='judge adapter')),
    ('INPUT.json', lambda value: value['game_manifest'].update(sha256='different game')),
    ('FAILED.json', lambda value: value.update(status='not the retained failure')),
])
def test_changed_proposal_receipts_block_before_model_load(receipt_run, filename, mutation):
    args, backend = receipt_run
    path = Path(args.previous_proposals)/filename
    value = generator.decode(path.read_bytes())
    mutation(value)
    write(path, value)
    assert followup.run(args) == 1 and backend.calls == []
    assert not (Path(args.output)/'LOADED.json').exists()


@pytest.mark.parametrize('filename,mutation', [
    ('PUBLIC_RESULT.json', lambda value: value.update(status='LAUNCHED')),
    ('PUBLIC_RESULT.json', lambda value: value.update(actions_sha256='not scored')),
    ('PUBLIC_RESULT.json', lambda value: value.update(new_pixels=1)),
    ('PUBLIC_RESULT.json', lambda value: value['per_attempt'][0].update(rank=1)),
    ('LOADED.json', lambda value: value['game_manifest'].update(sha256='wrong manifest')),
    ('actions/0000.json', lambda value: value['action'].update(text='rewritten caption')),
    ('outcomes/0000.json', lambda value: value.update(actor='parent')),
    ('outcomes/0000.json', lambda value: value['result'].update(contest_id='toy-1')),
    ('outcomes/0000.json', lambda value: value['result'].update(q=0.7)),
    ('outcomes/0000.json', lambda value: value['result'].update(raw_score=True)),
    ('outcomes/0000.json', lambda value: value['result'].update(rank=66)),
])
def test_changed_game_or_nonactual_feedback_blocks_before_model_load(receipt_run, filename, mutation):
    args, backend = receipt_run
    path = Path(args.game_output)/filename
    value = generator.decode(path.read_bytes())
    mutation(value)
    write(path, value)
    assert followup.run(args) == 1 and backend.calls == []
    assert not (Path(args.output)/'LOADED.json').exists()


def test_rewritten_literal_is_rejected_even_with_rehashed_action_file(receipt_run):
    args, backend = receipt_run
    actions_path = Path(args.scored_actions)
    actions = generator.decode(actions_path.read_bytes())
    actions[0]['text'] = 'Invented repair'
    write(actions_path, actions)
    summary_path = Path(args.game_output)/'PUBLIC_RESULT.json'
    summary = generator.decode(summary_path.read_bytes())
    summary['actions_sha256'] = generator.file_ref(actions_path)['sha256']
    write(summary_path, summary)
    assert followup.run(args) == 1 and backend.calls == []
    failed = generator.decode((Path(args.output)/'FAILED.json').read_bytes())
    assert failed['reason'] == 'literal_text_changed'


@pytest.mark.parametrize('raw,stop,calls', [(RAW, None, 2), ('[]', 'THINK', 1), ('[]', 'ACT', 2), ('[]', 'overflow', 1)])
def test_failure_preserves_context_raw_dataset_and_frozen_check_no_retry(receipt_run, raw, stop, calls):
    args, backend = receipt_run
    backend.act, backend.stop = raw, stop
    assert followup.run(args) == 1
    output = Path(args.output)
    assert len(backend.calls) == calls and backend.frozen_checks == 1
    assert (output/'DATASET.jsonl').is_file() and (output/'CONTEXT_BEFORE.json').is_file()
    assert (output/'CONTEXT_AFTER.json').is_file() and (output/'FROZEN_AFTER.json').is_file()
    assert (output/'FAILED.json').is_file() and not (output/'actions.json').exists()
    if calls == 2:
        assert generator.decode((output/'ACT_GENERATION.json').read_bytes())['raw'] == raw
    with pytest.raises(FileExistsError):
        followup.run(args)


def test_no_substitute_when_child_chooses_no_captions(receipt_run):
    args, backend = receipt_run
    backend.act = '[]'
    assert followup.run(args) == 2
    assert generator.decode((Path(args.output)/'actions.json').read_bytes()) == []


def test_different_loaded_tokenizer_cannot_generate(receipt_run):
    args, backend = receipt_run
    backend.identity['tokenizer'] = dict(different=True)
    assert followup.run(args) == 1 and backend.calls == []


def test_cli_help_requires_no_model_dependencies_and_frozen_generator_is_untouched(tmp_path):
    script = Path(__file__).with_name('followup_c2.py').resolve()
    result = subprocess.run([sys.executable, '-I', str(script), '--help'], cwd=tmp_path,
                            capture_output=True, text=True, check=True)
    assert '--previous-proposals' in result.stdout and '--scored-actions' in result.stdout
    assert hashlib.sha256(script.with_name('generate_c2.py').read_bytes()).hexdigest() == followup.FROZEN_GENERATOR_SHA256
