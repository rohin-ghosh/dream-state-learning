import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))
from render_probe import visible_kind


def fixture():
    return dict(message=dict(schema='R127_ATTRIBUTED_INBOX_V1', speaker='Astra', text='fixture', id='id'),
        source_id='source', source_sha256='a' * 64)


def messages(content, role='user'):
    return [dict(role='system', content='system'), dict(role='user', content='startup'), dict(role=role, content=content)]


def test_plain_match_is_not_claimed_unique_id():
    assert visible_kind(messages('Astra: fixture'), fixture()) == 'EXACT_PLAIN_TEXT_MATCH_NOT_UNIQUE_ID_ATTRIBUTION'
    assert visible_kind(messages('Astra: fixture', role='assistant'), fixture()) is None


def test_exact_structured_match_and_source_binding():
    metadata = dict(event_id='parent:inbox:id', actor='parent', split='TRAIN', source_id='source', source_sha256='a' * 64)
    content = 'Parent advice (not an observed fact)\n' + json.dumps(metadata) + '\nAstra: fixture'
    assert visible_kind(messages(content), fixture()) == 'EXACT_STRUCTURED_ID_AND_TEXT_MATCH'
    assert visible_kind(messages(content.replace('source', 'wrong')), fixture()) is None


def test_no_substring_or_system_prompt_matching():
    assert visible_kind(messages('Astra: fixture extra'), fixture()) is None
    assert visible_kind(messages('Astra: fixture', role='system'), fixture()) is None
