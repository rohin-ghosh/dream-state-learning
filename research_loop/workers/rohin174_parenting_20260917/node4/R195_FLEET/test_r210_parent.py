import os
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import Mock, patch

import r210_parent_endpoint as endpoint


class R210ParentTests(unittest.TestCase):
    def test_verified_prior_cursor_avoids_replaying_the_whole_journal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / 'r210'
            store = target / 'parent_cursor'
            store.mkdir(parents=True)
            refs = []
            for index in (80, 120):
                path = store / (str(index) + '.json')
                path.write_text(json.dumps(dict(root=str((root / 'life').resolve()), journal_id='same', next_index=index)))
                refs.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            marker = target / 'R230_BOOTSTRAP_CURSOR.json'
            marker.write_text(json.dumps(dict(reference=refs[1])))
            self.assertEqual(endpoint.resume_verified_cursor(root, target, refs[0]), refs[1])
            self.assertEqual(endpoint.resume_verified_cursor(root, target, refs[1]), refs[1])
            self.assertEqual(endpoint.resume_verified_cursor(root, target, None), refs[1])
            Path(refs[1]['path']).write_text('{}')
            with self.assertRaisesRegex(ValueError, 'pinned_operator_cursor'):
                endpoint.resume_verified_cursor(root, target, refs[0])

    def publication(self, physical, words, isolated=False):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            if isolated:
                (target / 'R211_ISOLATION.json').write_text('{}')
            console = types.ModuleType('gpu.orch_r127_pilot_console')
            console.publish_parent = Mock(return_value={'id': 'actual-publication'})
            loaded = dict(index=1, kind='LOADED', document=dict(pid=os.getpid()))
            with patch.object(endpoint, 'configure', return_value=(target, target, Path.cwd())), \
                    patch.object(endpoint, 'read', return_value=dict(last_record_index=0)), \
                    patch.object(endpoint, 'records', return_value=[loaded]), \
                    patch.object(endpoint, 'WALL', time.time() + 60), \
                    patch.dict(sys.modules, {'gpu.orch_r127_pilot_console': console}):
                result = endpoint.publish(physical, ' '.join(['word'] * words))
                console.publish_parent.assert_called_once()
                self.assertEqual(console.publish_parent.call_args.args[1], 'Astra')
                return result

    def test_original_style_b_160_word_contract_is_preserved(self):
        for physical in (2, 3, 5):
            with self.subTest(physical=physical):
                self.assertEqual(self.publication(physical, 160), {'id': 'actual-publication'})

    def test_style_b_over_limit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'bounded_Astra_publication'):
            self.publication(5, 161)

    def test_style_c_limit_is_not_weakened(self):
        for physical in (6, 7):
            with self.subTest(physical=physical):
                self.assertEqual(self.publication(physical, 120), {'id': 'actual-publication'})
                with self.assertRaisesRegex(ValueError, 'bounded_Astra_publication'):
                    self.publication(physical, 121)

    def test_reserved_gpu_and_original_kernel_have_no_parent_mutation(self):
        for physical in (0, 1, 4):
            with self.subTest(physical=physical):
                with self.assertRaisesRegex(ValueError, 'only_R210_clone_parents'):
                    endpoint.configure(physical)

    def test_actual_creative_answer_is_bounded_and_not_a_formula_prompt(self):
        text = (Path(__file__).parent / 'R210_CREATIVE_PARENT.txt').read_text()
        self.assertLessEqual(len(text.split()), 120)
        self.assertIn('CREATIVE-OPEN-C', text)
        self.assertIn('lighthouse', text)
        self.assertIn('attributed inbox', text)
        self.assertIsNone(re.search(r'\bV\b', text))

    def test_isolation_blocks_parent_publication(self):
        with self.assertRaisesRegex(ValueError, 'R211_no_inbound_parent_publication'):
            self.publication(7, 20, isolated=True)


if __name__ == '__main__':
    unittest.main()
