import copy
import json
from pathlib import Path
import shutil
import signal
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kernel4_prospective as kernel


@pytest.fixture
def fixture_output(tmp_path):
    output = tmp_path / 'old'
    output.mkdir()
    shutil.copyfile(kernel.OLD_OUTPUT / 'STARTED.json', output / 'STARTED.json')
    for name in ('parent_000000', 'parent_000004', 'parent_000052'):
        shutil.copytree(kernel.OLD_OUTPUT / name, output / name)
    return output


def update(path, **fields):
    document = json.loads(path.read_text())
    document.update(fields)
    path.write_text(json.dumps(document))


def test_settled_old_schema_without_schedule_count(fixture_output):
    ledger = kernel.terminal_ledger(fixture_output)
    assert ledger['reserved'] == 106
    assert ledger['statuses'] == {'PUBLISHED': 1, 'SILENT': 1, 'MISSING': 1}
    assert ledger['terminal_denials'][0]['disposition'] == 'TERMINAL_PROVIDER_DENIAL_RESERVED_NEVER_REPLAY'
    assert len(ledger['files']) > 10


@pytest.mark.parametrize('code', [429, '429'])
def test_evidenced_budget_denial_code_forms(fixture_output, code):
    path = fixture_output / 'parent_000052/http_error_response.txt'
    payload = json.loads(path.read_text())
    payload['error']['code'] = code
    path.write_text(json.dumps(payload))
    assert kernel.terminal_ledger(fixture_output)['reserved'] == 106


@pytest.mark.parametrize('fields', [
    {'sent_unix': 1}, {'inbox_publication': {}}, {'response': {}}, {'usage': {}},
    {'error_type': 'TimeoutError'}, {'status': 'UNKNOWN'}, {'retry': True},
])
def test_ambiguous_failure_never_terminable(fixture_output, fields):
    update(fixture_output / 'parent_000052/RESULT.json', **fields)
    with pytest.raises(ValueError):
        kernel.terminal_ledger(fixture_output)


def test_missing_terminal_result_refused(fixture_output):
    (fixture_output / 'parent_000052/RESULT.json').unlink()
    with pytest.raises(FileNotFoundError):
        kernel.terminal_ledger(fixture_output)


def test_stdout_on_missing_result_is_uncertain(fixture_output):
    (fixture_output / 'parent_000052/stdout.json').write_text('{}')
    with pytest.raises(ValueError, match='unknown_publication'):
        kernel.terminal_ledger(fixture_output)


def test_unbound_reserved_intent_refused(fixture_output):
    update(fixture_output / 'parent_000052/DISPATCH_INTENT.json', source_sha256='0' * 64)
    with pytest.raises(ValueError, match='bound_reserved_intent'):
        kernel.terminal_ledger(fixture_output)


def test_other_provider_error_is_not_assumed_safe(fixture_output):
    path = fixture_output / 'parent_000052/http_error_response.txt'
    path.write_text(json.dumps({'error': {'code': 500, 'type': 'server_error'}}))
    with pytest.raises(ValueError, match='only_evidenced_terminal'):
        kernel.terminal_ledger(fixture_output)


def test_exact_inbox_preserved_tool_receipts_not_parent_calls(fixture_output):
    ledger = kernel.terminal_ledger(fixture_output)
    rows = [dict(publication, actor='parent', speaker='Astra', split='TRAIN')
            for publication in ledger['publications'].values()]
    rows.append(dict(id='tool-id', actor='tool', speaker='Tool', split='TRAIN'))
    kernel.verify_inbox(rows, ledger)
    rows.append(dict(id='unknown', actor='parent', speaker='Astra', split='TRAIN'))
    with pytest.raises(ValueError, match='unknown_or_missing'):
        kernel.verify_inbox(rows, ledger)


def test_missing_or_changed_publication_refused(fixture_output):
    ledger = kernel.terminal_ledger(fixture_output)
    with pytest.raises(ValueError, match='unknown_or_missing'):
        kernel.verify_inbox([], ledger)
    rows = [dict(publication, actor='parent', speaker='Astra', split='TRAIN')
            for publication in ledger['publications'].values()]
    rows[0]['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='exact_published'):
        kernel.verify_inbox(rows, ledger)


def test_only_exact_preexisting_Main_nudge_reconciles_external_id(fixture_output):
    ledger = kernel.terminal_ledger(fixture_output)
    external = kernel.external_publications()
    rows = [dict(publication, actor='parent', speaker='Astra', split='TRAIN')
            for publication in list(ledger['publications'].values()) + list(external.values())]
    with pytest.raises(ValueError, match='unknown_or_missing'):
        kernel.verify_inbox(rows, ledger)
    kernel.verify_inbox(rows, ledger, external)
    rows[-1]['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='exact_published'):
        kernel.verify_inbox(rows, ledger, external)


def test_only_prospective_source_policy_cursor_config_fields(fixture_output):
    old = json.loads(kernel.OLD_CONFIG.read_text())
    ledger = kernel.terminal_ledger(fixture_output)
    candidate = kernel.candidate_config(old, ledger)
    assert {key for key in candidate if candidate[key] != old.get(key)} == {
        'parent_module_sha256', 'principles_path', 'principles_sha256',
        'predecessor_output', 'predecessor_started_sha256', 'start_after_response_count'}
    assert candidate['start_after_response_count'] == 106
    assert candidate['root'] == old['root']
    assert candidate['source_root'] == old['source_root']
    assert candidate['hard_end_unix'] == old['hard_end_unix']
    assert candidate['cadence_responses'] == 2


@pytest.mark.parametrize('field,value', [
    ('root', '/wrong'), ('node', 'ovx2'), ('physical', 0), ('cadence_responses', 1),
    ('parent_style', 'other'), ('programme', 'raw_parented'), ('hard_end_unix', 0),
])
def test_invariant_config_changes_refused(field, value):
    old = json.loads(kernel.OLD_CONFIG.read_text())
    old[field] = value
    with pytest.raises(ValueError, match='exact_original_life'):
        kernel.candidate_config(old, {})


@pytest.mark.parametrize('pid', [2278329, 601818, 601954, 447695, 448014, 508091, 508573])
def test_no_other_parent_or_child_identity(pid):
    observed = copy.deepcopy(kernel.EXPECTED)
    observed['pid'] = pid
    with pytest.raises(ValueError, match='exact_kernel4'):
        kernel.verify(observed)


class FakeOperations:
    def __init__(self, children=False, race=False):
        self.signals = []
        self.children = children
        self.race = race

    def identity(self, pid):
        result = copy.deepcopy(kernel.EXPECTED)
        result['state'] = 'T' if self.signals else 'S'
        return result

    def children_absent(self, pid):
        return not self.children

    def open(self, pid):
        assert pid == 716608
        return 321

    def signal(self, descriptor, number):
        assert descriptor == 321
        self.signals.append(number)

    def childless_stopped(self, pid):
        if self.race:
            raise ValueError('child_race')

    def close(self, descriptor):
        assert descriptor == 321


def test_child_present_means_no_signal():
    operations = FakeOperations(children=True)
    with pytest.raises(ValueError):
        with kernel.paused(operations):
            pytest.fail('must_not_enter')
    assert not operations.signals


def test_child_race_resumes_parent_without_termination():
    operations = FakeOperations(race=True)
    with pytest.raises(ValueError):
        with kernel.paused(operations):
            pytest.fail('must_not_enter')
    assert operations.signals == [signal.SIGSTOP, signal.SIGCONT]


def test_uncertain_ledger_always_resumes_parent_without_termination():
    operations = FakeOperations()
    with pytest.raises(ValueError):
        with kernel.paused(operations):
            raise ValueError('uncertain_ledger')
    assert operations.signals == [signal.SIGSTOP, signal.SIGCONT]
