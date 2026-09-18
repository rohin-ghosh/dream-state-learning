"""Focused CPU-only private adaptation and THINK-only external input tests."""

import importlib.util
from pathlib import Path
import tarfile
from types import SimpleNamespace


def imported(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_r210_parent_peer_introduction_only_at_think():
    helper = imported('r210_inbox')
    peer = SimpleNamespace(text='Astra: [R210_PEER] attributed own state')
    parent = SimpleNamespace(text='Astra: [R210_PARENT] actual new environment')
    human = SimpleNamespace(text='Rohin: question')
    tool = SimpleNamespace(text='Tool: exact receipt')
    values = [peer, parent, human, tool]
    assert helper.think_incoming(values, 'THINK') == values
    assert helper.think_incoming(values, 'ACT') == [human, tool]
    assert helper.think_incoming(values, 'LEARN') == [human, tool]
    assert helper.think_incoming(values, 'ACT') == helper.think_incoming(values, 'ACT')


def test_released_AST_changes_only_private_executor_and_R210_inbox_route():
    prepare = imported('prepare_r210')
    with tarfile.open(prepare.BUNDLE/'runtime_overlay.tar.gz') as archive:
        released = archive.extractfile('gpu/orch_r184_think_act_learn.py').read().decode()
    private = (prepare.OWN/'r206_receiving/gpu/orch_r184_think_act_learn.py').read_text()
    result = prepare.adapted_driver(released, private)
    assert 'R209_ENGLISH_PROSE_TARGET_QUARANTINE_V1' not in result or 'prose_target_filter' in result
    assert 'R203_MATH_COMM_B_node1_clone1' in result
    assert 'R202_CREATIVE_B_node1_clone1' in result
    assert 'incoming = think_incoming(incoming, stage)' in result


def test_parent_opening_bounds_V_repair_without_supplying_V():
    parent = imported('r210_parent')
    arm = dict(previous_ACT=dict(text='V = unknown; syntax error'), task='Write a new scene.', excerpt=None)
    text, stalled = parent.opening(arm)
    assert stalled and 'n=3' in text and 'exact formula' in text and 'two repair turns' in text
    assert 'V =' not in text and text.startswith('[R210_PARENT]') and 'not a withdrawn' in text
    assert 'Write a new scene.' in text
    arm['previous_ACT']['text'] = 'Here is my actual scene draft.'
    text, stalled = parent.opening(arm)
    assert not stalled and 'exact formula' not in text


def test_peer_state_requires_new_phase_source_hash_not_matching_inherited_text():
    parent = imported('r210_parent')
    assert "if event['source_sha256'] in new_sources" in parent.OBSERVE
    assert 'new_texts' not in parent.OBSERVE


def test_english_parent_rejects_raw_drift_but_accepts_lossless_escaped_quote():
    parent = imported('r210_parent')
    assert parent.parent_language_violations('你写到') == ['U+4F60', 'U+5199', 'U+5230']
    assert parent.parent_language_violations('Your value is ３') == ['U+FF13']
    assert parent.parent_language_violations('English with hidden\u200btext') == ['U+200B']
    parent.validate_parent_response(dict(speak=True, message='Escaped own excerpt: "\\u4f60". '
                                        'Choose a LANGUAGE CHECK; continue your scene.', rationale='English feedback.'))
    try:
        parent.validate_parent_response(dict(speak=True, message='你写到', rationale='English feedback.'))
    except AssertionError as error:
        assert str(error) == 'R212_PARENT_ENGLISH_SCRIPT_REQUIRED'
    else:
        raise AssertionError('Non-English parent output was accepted')


def test_parent_script_rejection_and_isolation_happen_before_transport():
    parent = imported('r210_parent')
    parent.remote = lambda code: (_ for _ in ()).throw(AssertionError('TRANSPORT_MUST_NOT_RUN'))
    for physical, text, expected in ((4, '[R210_PARENT] 你写到', 'R212_PARENT_ENGLISH_SCRIPT_REQUIRED'),
                                      (7, '[R210_PARENT] English.', 'R211_isolation_no_parent_or_peer_input')):
        try:
            parent.publish(physical, text, 'TEST_ONLY')
        except AssertionError as error:
            assert str(error) == expected
        else:
            raise AssertionError('Invalid publication was accepted')


def test_parent_observer_reads_actual_action_receipt_kind():
    parent = imported('r210_parent')
    assert "kind in ('R184_ACT','R184_ACT_OUTCOME')" in parent.OBSERVE


def test_r213_parent_judgment_preserves_human_priority_and_forbids_solutions():
    parent = imported('r210_parent')
    instruction = parent.R213_JUDGMENT_POLICY
    for phrase in ('at most two real attempts or clarification turns', 'without new evidence',
                   'a repeated plan or declaration is not an executed attempt',
                   'do not assign competing homework', 'No solutions.', 'P7 remains fully isolated'):
        assert phrase in instruction
    assert parent.policy()['legacy_v_closed'] is True
    assert parent.policy()['competing_homework'] is False
    assert "document['message'].get('speaker')=='Rohin'" in parent.OBSERVE
