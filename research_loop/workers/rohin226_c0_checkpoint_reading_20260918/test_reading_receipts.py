from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location('reading_receipts', Path(__file__).with_name('reading_receipts.py'))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProjectionTests(unittest.TestCase):
    def fixture(self):
        return dict(observed_utc='2026-09-18T08:20:40Z', service=dict(pid=123, private='do-not-export'),
            state=dict(completed_cycle=64, pending=None), identities=[], publications=[], turns=[], cycles=[], failures=[])

    def test_pending_is_not_render_claim(self):
        source = self.fixture()
        source['publications'] = [dict(path='private-path', document=dict(number=0, action='reading',
            text='private-text', render=None, publication=dict(id='actual-id', sha256='a' * 64, path='private-path')))]
        result = MODULE.project(source)
        self.assertIsNone(result['publications'][0]['render'])
        self.assertEqual(result['publications'][0]['publication']['id'], 'actual-id')
        self.assertNotIn('private-', json.dumps(result))
        self.assertNotIn('do-not-export', json.dumps(result))

    def test_cycle_keeps_source_hash_not_raw_child_text(self):
        source = self.fixture()
        source['cycles'] = [dict(document=dict(cycle=65, reading_rendered=True,
            events=[dict(kind='actual_ACT', index=100, sha256='b' * 64, raw='secret-like-child-text', raw_sha256='c' * 64)]))]
        before = deepcopy(source)
        result = MODULE.project(source)
        self.assertEqual(result['cycles'][0]['events'][0]['index'], 100)
        self.assertNotIn('secret-like-child-text', json.dumps(result))
        self.assertEqual(source, before)

    def test_actual_render_evidence_survives_projection(self):
        source = self.fixture()
        source['state']['pending'] = dict(number=1, action='memory', text='do-not-export',
            render=dict(index=110, sha256='d' * 64, all_history_tokens_masked=True,
                story_verbatim_in_request=True, adapter_memory_claim=False, raw='do-not-export'))
        result = MODULE.project(source)
        self.assertTrue(result['state']['pending']['render']['all_history_tokens_masked'])
        self.assertFalse(result['adapter_retention_claim'])
        self.assertNotIn('do-not-export', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
