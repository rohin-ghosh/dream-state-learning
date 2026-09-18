import copy
import importlib.util
import json
from pathlib import Path

import native_custody
import pytest


def module():
    spec = importlib.util.spec_from_file_location('isolated_c5_metadata', Path(__file__).with_name('recovery_metadata.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    value.digest = native_custody.digest
    value.require = native_custody.require
    return value


def fixture():
    digest = native_custody.digest
    request = dict(split='TRAIN', segment=0, messages=[dict(role='user', content='private TRAIN fixture')],
                   render_receipt=dict(all_history_tokens_masked=True))
    before = dict(pending=digest(request), rows=[], sleep_frontier=0, sleep_receipts=[], model_state_sha256='model')
    response = dict(request_sha256=digest(request), response=dict(raw='private child fixture', token_ids=[1, 2]))
    row = dict(prefix=request['messages'], target=response['response']['raw'], token_ids=[1, 2], actor='child',
               split='TRAIN', prefix_loss=False, target_loss=True, source_sha256=digest(response))
    after = dict(before, pending=None, rows=[row])
    return [dict(kind='REQUEST', index=1, document=dict(request, resume_state=dict(state=before, sha256=digest(before)))),
            dict(kind='RESPONSE', index=2, document=response),
            dict(kind='COMMITTED', index=3, document=dict(segment=0, source_sha256=digest(response),
                state=dict(state=after, sha256=digest(after))))]


def test_real_row_binding_returns_only_metadata():
    result = module().committed_triple(*fixture())
    assert result['original_target_binding'] and result['prefix_masked']
    assert 'private' not in json.dumps(result)
    assert result['semantic_correctness_or_learning_claim'] is False


@pytest.mark.parametrize('field,value', [('target', 'substitute'), ('prefix_loss', True)])
def test_wrong_original_target_or_mask_refuses(field, value):
    records = copy.deepcopy(fixture())
    wrapped = records[-1]['document']['state']
    wrapped['state']['rows'][-1][field] = value
    wrapped['sha256'] = native_custody.digest(wrapped['state'])
    with pytest.raises(ValueError, match='exact_own_child_target_and_mask'):
        module().committed_triple(*records)
