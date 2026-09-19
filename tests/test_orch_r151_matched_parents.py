"""Local CPU fixtures check configuration/custody, not successful real parenting."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import time
from unittest.mock import patch

import pytest

from gpu import orch_r151_matched_parents as setup
from gpu.orch_r150_matched_journal import MatchedJournal
from organism_v6.orch_r125_plain_context import VERSION
from test_orch_r125_continual_native import make_plan
from test_orch_r150_matched_stream import COHORT, FakeChild, make_stream


REPOSITORY = Path(__file__).resolve().parents[1]


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True))
    return path


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    wrapper = tmp_path/'ovx3_ssh.sh'
    wrapper.write_text('exit 97\n')
    original_pin = setup.pin

    def fixture_pin(path):
        if Path(path) == REPOSITORY/'gpu/ovx3_ssh.sh':
            return original_pin(wrapper)
        return original_pin(path)

    monkeypatch.setattr(setup, 'pin', fixture_pin)
    root = Path('/localhome/local-rohing/orch_r151_cpu_fixture')
    plan = make_plan(root)
    plan.update(context_limit=16384, hard_end_unix=time.time()+7200,
        lease_end_unix=time.time()+7800, startup_context=None, presentation_version=VERSION,
        presleep_variant='free_distillation', readout_revision=1)
    plans = {arm: dict(deepcopy(plan), root=str(root/arm), matched_arm=arm,
        physical=index, gpu_uuid=f'GPU-CPU-fixture-{index}',
        parent_enabled=arm != 'unparented_learning') for index, arm in enumerate(setup.matched.ARMS)}
    cohort = setup.matched.cohort_document(list(plans.values()), root/'common_initial')
    cohort_path = save(tmp_path/'COHORT.json', cohort)
    plan_paths = {}
    for arm, plan in plans.items():
        plan['matched_cohort'] = dict(path=str(root/'COHORT.json'), sha256=setup.parent.sha(cohort_path))
        plan_paths[arm] = save(tmp_path/(arm+'.PLAN.json'), plan)
    programme = tmp_path/'programme.md'
    principles = tmp_path/'principles.md'
    programme.write_text('Attend to actual TRAIN activity, without hidden answers.')
    principles.write_text('Ask useful questions; do not impose a thought template.')
    template = dict(schema='R133_PROGRAMME_PARENT_V1', programme='raw_parented',
        programme_path=str(programme), programme_sha256=setup.parent.sha(programme),
        principles_path=str(principles), principles_sha256=setup.parent.sha(principles),
        parent_style='Socratic', parent_reasoning_effort='low', branch='OLD_FROZEN_LABEL',
        node='ovx2', schedule_on='response', start_after_request_count=99,
        cadence_label='SPARSE', cadence_responses=3)
    template_path = save(tmp_path/'TEMPLATE.json', template)
    return dict(cohort=cohort_path, cohort_sha256=setup.parent.sha(cohort_path), plans=plan_paths,
        template=template_path, output=tmp_path/'parents', programme=programme, wrapper=wrapper)


def prepare(fixture):
    return setup.prepare(REPOSITORY, fixture['cohort'], fixture['cohort_sha256'],
        fixture['plans'], fixture['template'], fixture['output'])


def test_preparation_pins_two_identical_parent_contracts_without_execution(fixture):
    with patch.object(setup.parent, 'strong', side_effect=AssertionError('provider forbidden')), \
            patch.object(setup.parent, 'remote', side_effect=AssertionError('remote forbidden')), \
            patch.object(setup.matched, 'run', side_effect=AssertionError('launch forbidden')), \
            patch('subprocess.run', side_effect=AssertionError('subprocess forbidden')):
        reference = prepare(fixture)
        result = setup.verify(reference['path'], reference['sha256'])
    assert result['status'] == 'VERIFIED_CPU_ONLY_NOT_REGISTERED'
    document = setup.read_pinned(reference)
    assert document['provider_calls'] == document['GPU_calls'] == document['remote_writes'] == 0
    assert document['parent_contract']['parenting_success_claim'] is False
    assert document['registration']['runtime_verified'] is False
    assert document['parent_contract']['model'] == setup.parent.STRONG
    configs = {arm: setup.read_pinned(pin) for arm, pin in document['configs'].items()}
    learned, frozen = (configs[arm] for arm in ('parented_learning', 'parented_frozen'))
    assert {key for key in learned if learned[key] != frozen[key]} == {'root'}
    assert learned['branch'] == frozen['branch'] == setup.BRANCH
    assert learned['parent_style'] == 'Socratic'
    assert learned['schedule_on'] == 'request'
    assert learned['cadence_responses'] == 1 and learned['cadence_label'] == 'PERSISTENT'
    assert learned['start_after_request_count'] == learned['start_after_response_count'] == 0
    assert learned['node'] == 'ovx3'
    state = dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=[
        dict(actor='child', text='What might I try next?')])
    assert setup.parent.prompt(learned, state) == setup.parent.prompt(frozen, state)
    assert 'OLD_FROZEN_LABEL' not in str(setup.parent.prompt(learned, state))
    assert 'parented_frozen' not in str(setup.parent.prompt(frozen, state))
    unparented = document['arms']['unparented_learning']
    assert unparented['config_file'] is None and unparented['parent_enabled'] is False
    assert not (fixture['output']/'unparented_learning.PARENT.json').exists()
    for arm in setup.matched.ARMS:
        assert document['arms'][arm]['learning_enabled'] is (arm != 'parented_frozen')
    assert set(document['source_pins']) == set(setup.SOURCE_FILES)
    assert document['source_pins']['gpu/ovx3_ssh.sh'] == setup.pin(fixture['wrapper'])
    for path in fixture['output'].iterdir():
        assert path.stat().st_mode & 0o222 == 0
    with pytest.raises(ValueError, match='new_canonical_local_output'):
        prepare(fixture)


@pytest.mark.parametrize('field,value', [('seed', 33), ('extra_parent_instruction', 'frozen only')])
def test_rejects_unmatched_plan_knobs(fixture, field, value):
    path = fixture['plans']['parented_frozen']
    plan = json.loads(path.read_text())
    plan[field] = value
    save(path, plan)
    with pytest.raises(ValueError, match='identical_common|only_matched_condition'):
        prepare(fixture)
    assert not fixture['output'].exists()


def test_external_cohort_pin_and_missing_arm_fail_closed(fixture):
    fixture['cohort_sha256'] = '0'*64
    with pytest.raises(ValueError, match='expected_cohort_pin'):
        prepare(fixture)
    fixture['cohort_sha256'] = setup.parent.sha(fixture['cohort'])
    del fixture['plans']['unparented_learning']
    with pytest.raises(ValueError, match='exact_three_matched_plans'):
        prepare(fixture)


def test_matched_plan_reference_is_not_rewritten_to_local_copy(fixture):
    reference = prepare(fixture)
    document = setup.read_pinned(reference)
    assert document['runtime_cohort_path'].startswith('/localhome/')
    assert document['cohort']['path'] == str(fixture['cohort'])
    path = fixture['plans']['parented_learning']
    plan = json.loads(path.read_text())
    plan['matched_cohort']['sha256'] = 'f'*64
    save(path, plan)
    with pytest.raises(ValueError, match='immutable_input_pin'):
        setup.verify(reference['path'], reference['sha256'])


@pytest.mark.parametrize('target', ['programme', 'template', 'cohort', 'config'])
def test_verify_rejects_changed_bytes(fixture, target):
    reference = prepare(fixture)
    path = (fixture['output']/'parented_learning.PARENT.json') if target == 'config' else fixture[target]
    path.chmod(0o600)
    path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ValueError, match='immutable_input_pin|fixed_parent_source'):
        setup.verify(reference['path'], reference['sha256'])


def test_verify_checks_source_drift_and_manifest_digest(fixture):
    reference = prepare(fixture)
    with pytest.raises(ValueError, match='expected_manifest_pin'):
        setup.verify(reference['path'], '0'*64)
    original = setup.pin

    def changed_source(path):
        result = original(path)
        if str(path).endswith('/gpu/orch_r133_programme_parent.py'):
            result['sha256'] = '0'*64
        return result

    with patch.object(setup, 'pin', side_effect=changed_source), \
            pytest.raises(ValueError, match='exact_prepared_contract'):
        setup.verify(reference['path'], reference['sha256'])


def test_transport_pin_is_checked_without_a_staged_shell_wrapper(fixture):
    reference = prepare(fixture)
    fixture['wrapper'].write_text('exit 98\n')
    with pytest.raises(ValueError, match='exact_prepared_contract'):
        setup.verify(reference['path'], reference['sha256'])


def test_explicit_effort_and_pinned_sources_required(fixture):
    template = json.loads(fixture['template'].read_text())
    template['parent_reasoning_effort'] = None
    save(fixture['template'], template)
    with pytest.raises(ValueError, match='explicit_shared_effort'):
        prepare(fixture)
    template['parent_reasoning_effort'] = 'low'
    template['principles_sha256'] = '0'*64
    save(fixture['template'], template)
    with pytest.raises(ValueError, match='fixed_parent_source'):
        prepare(fixture)


@pytest.mark.parametrize('name', ['HELD.json', 'FINAL.json', 'sealed_scores.json', 'readout.json'])
def test_evaluation_paths_rejected_before_read(tmp_path, name):
    with patch.object(Path, 'read_bytes', side_effect=AssertionError('must not read')), \
            pytest.raises(ValueError, match='no_evaluation_input'):
        setup.pin(tmp_path/name)


def test_symlink_inputs_rejected(tmp_path):
    original = save(tmp_path/'original.json', {})
    link = tmp_path/'link.json'
    link.symlink_to(original)
    with pytest.raises(ValueError, match='regular_local_input'):
        setup.pin(link)


def local_script(repository, config, script):
    output = io.StringIO()
    with redirect_stdout(output):
        exec(compile(script, '<R133-local-CPU-transport-test>', 'exec'), {})
    return json.loads(output.getvalue())


@pytest.mark.parametrize('arm', ['parented_learning', 'parented_frozen'])
def test_actual_r133_publication_and_snapshot_use_matched_registration(tmp_path, arm):
    root = tmp_path/arm
    root.mkdir()
    stream = make_stream(arm)
    with MatchedJournal(root/'stream', arm=arm, cohort_sha256=COHORT, create=True) as journal:
        journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
        with patch.object(setup.parent, 'remote', side_effect=local_script), \
                patch.object(setup.parent, 'strong', side_effect=AssertionError('no provider')):
            publication = setup.parent.publish(REPOSITORY, dict(root=str(root)), 'What did you notice?')
            incoming = journal.read_inbox()
            assert incoming[0].text == 'Astra: What did you notice?'
            assert incoming[0].actor == 'parent' and incoming[0].split == 'TRAIN'
            child = FakeChild(arm)
            stream.step(child.generate, child.count_tokens, journal.record, incoming=incoming, now=lambda: 100)
            state = setup.parent.snapshot(REPOSITORY, dict(root=str(root)))
        assert publication['id'] in state['consumed_inbox']
        assert state['parent_consumptions'][0]['speaker'] == 'Astra'
        assert [event['actor'] for event in state['events']] == ['parent', 'child']
        assert all(row['actor'] == 'child' for row in stream.rows)
        assert state['response_count'] == state['request_count'] == 1


def test_unparented_matched_consumer_rejects_even_attributed_astra(tmp_path):
    root = tmp_path/'unparented_learning'
    root.mkdir()
    stream = make_stream('unparented_learning')
    with MatchedJournal(root/'stream', arm=stream.arm, cohort_sha256=COHORT, create=True) as journal:
        journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
        with patch.object(setup.parent, 'remote', side_effect=local_script):
            publication = setup.parent.publish(REPOSITORY, dict(root=str(root)), 'CPU rejection fixture')
        with pytest.raises(ValueError, match='unparented_parent_channel_forbidden'):
            journal.read_inbox()
        assert Path(publication['path']).is_file()
        assert journal.latest_checkpoint()['document'] == stream.checkpoint()


def test_cli_only_offers_prepare_and_verify(capsys):
    with pytest.raises(SystemExit) as result:
        setup.main(['--help'])
    assert result.value.code == 0
    assert '{prepare,verify}' in capsys.readouterr().out
    with pytest.raises(SystemExit):
        setup.main(['serve'])
