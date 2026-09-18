import copy
import hashlib
import json
from types import SimpleNamespace

import pytest

from r184_parent_effort import SCHEMA, TEXT, install, publication_refs


def fixture(tmp_path, label='C1'):
    plan = (TEXT + '\n').encode()
    (tmp_path / 'R184_FIXED_FIRST_COMPARISON.md').write_bytes(plan)
    (tmp_path / 'R184_EFFORT_PHASE.json').write_text(json.dumps(dict(schema=SCHEMA,
        label=label, fixed_plan_sha256=hashlib.sha256(plan).hexdigest())))
    return SimpleNamespace(prompt=lambda config, state, memory: ('unchanged arm', state))


def test_exact_both_directions_only_and_no_state_changes(tmp_path):
    policy = fixture(tmp_path)
    config = dict(cadence_responses=2, r175_word_limit=90, r175_arm='B')
    state = dict(request_count=20, delivered={'existing': 'unchanged'})
    memory = dict(awaiting_render=True, last_response_count=19)
    before = copy.deepcopy((config, state, memory))
    proof = install(policy, tmp_path)
    text, payload = policy.prompt(config, state, memory)
    assert text == 'unchanged arm\n\n' + SCHEMA + '\n' + TEXT
    assert payload is state and (config, state, memory) == before
    assert proof['cadence_word_limits_clocks_pending_and_child_unchanged']


def test_C2_excluded_before_install(tmp_path):
    policy = fixture(tmp_path, 'C2')
    original = policy.prompt
    with pytest.raises(ValueError, match='nonC2'):
        install(policy, tmp_path)
    assert policy.prompt is original


def test_changed_plan_rejected(tmp_path):
    policy = fixture(tmp_path)
    (tmp_path / 'R184_FIXED_FIRST_COMPARISON.md').write_text('changed')
    with pytest.raises(ValueError, match='fixed_plan_pin'):
        install(policy, tmp_path)


def test_existing_nonphase_sources_unchanged(tmp_path):
    policy = SimpleNamespace(prompt=lambda *args: ('old', {}))
    original = policy.prompt
    assert install(policy, tmp_path) is None and policy.prompt is original


def test_actual_retry_publication_prompt_and_paths(tmp_path):
    directory = tmp_path / 'parent_000123_prepub_retry1'
    directory.mkdir()
    result = dict(status='PUBLISHED', publication=dict(id='actual'))
    (directory / 'RESULT.json').write_text(json.dumps(result))
    (directory / 'SOURCE.json').write_text('{}')
    (directory / 'PROMPT.json').write_text(json.dumps(dict(instruction=SCHEMA + TEXT)))
    assert publication_refs(tmp_path, result)['result']['path'] == str(directory / 'RESULT.json')
    (directory / 'PROMPT.json').write_text(json.dumps(dict(instruction='old')))
    with pytest.raises(ValueError, match='actual_outbound'):
        publication_refs(tmp_path, result)


def test_examples_append_without_payload_or_clock_change(tmp_path):
    policy = fixture(tmp_path)
    module = tmp_path / 'gpu/orch_r188_parent_examples.py'
    module.parent.mkdir()
    module.write_text("MARKER='R188_REPORTED_WORKED_EXAMPLES_V1'\nPROVENANCE='Rohin188 relayed by Fable'\ndef parent_policy_suffix():\n    return '\\nReported example; not the recipient transcript.'\n")
    (tmp_path/'R188_EXAMPLES_PHASE.json').write_text(json.dumps(dict(main_module_sha256=hashlib.sha256(module.read_bytes()).hexdigest())))
    proof = install(policy, tmp_path)
    state = dict(request_count=123)
    text,payload = policy.prompt({},state,{})
    assert payload is state and state == dict(request_count=123)
    assert text.endswith('Reported example; not the recipient transcript.')
    assert proof['examples']['provenance'] == 'Rohin188 relayed by Fable'
