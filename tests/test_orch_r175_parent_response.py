import json

import pytest

from gpu.orch_r175_parent_response import compatible_parser, normalize_rationale
from gpu.orch_route_parent_campaign_providers import response_schema


def test_structured_rationale_is_lossless_and_private():
    response = dict(speak=True, message='Astra: What did your attempt show?',
                    rationale={'object_id': 'same_object', 'source_records': [123], 'next_task': None})
    parsed = compatible_parser(response_schema)(json.dumps(response))
    assert parsed['message'] == response['message']
    assert json.loads(parsed['rationale']) == response['rationale']


def test_existing_string_is_byte_unchanged():
    raw = json.dumps(dict(speak=True, message='Continue.', rationale='{"object_id":"same"}'))
    assert normalize_rationale(raw) == raw


@pytest.mark.parametrize('changes', [dict(message='word ' * 91), dict(speak='true'),
                                    dict(extra='unknown'), dict(rationale=['not', 'object'])])
def test_original_validator_still_rejects(changes):
    response = dict(speak=True, message='Continue.', rationale={'object_id': 'same'})
    response.update(changes)
    with pytest.raises(ValueError):
        compatible_parser(response_schema)(json.dumps(response))


def test_does_not_change_ids_or_counter_semantics():
    response = dict(speak=True, message='Continue.', rationale={'object_id': 'Invalid_UPPER', 'next_task': 'invalid'})
    parsed = compatible_parser(response_schema)(json.dumps(response))
    assert json.loads(parsed['rationale']) == response['rationale']


def test_bounded_input():
    with pytest.raises(ValueError, match='bounded_parent_wire_text'):
        normalize_rationale('x' * 65537)
