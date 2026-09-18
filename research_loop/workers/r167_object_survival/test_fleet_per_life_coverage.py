import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fleet_per_life_coverage as observer


class PerLifeTests(unittest.TestCase):
    def test_registration_not_completion_and_no_sealed_data_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            queue_path = root / 'QUEUE_PLAN.json'
            queue_path.write_text(json.dumps(dict(life_id='example', first_sleep=20, sleep_count=3)))
            registration = root / 'lives/example/REGISTERED.json'
            registration.parent.mkdir(parents=True)
            registration.write_text(json.dumps(dict(plan=dict(path=str(queue_path),
                sha256=hashlib.sha256(queue_path.read_bytes()).hexdigest()))))
            sealed = root / 'attempts/unrelated/sealed'
            sealed.mkdir(parents=True)
            (sealed / '0.RAW.private.json').write_text('never read')
            plan = dict(lives=[dict(life_id='example', node='ovx3', status='SOURCE_CANDIDATE'),
                dict(life_id='missing', node='ovx3', status='MISSING_CUSTODY_NOT_NEGATIVE', hold='CUSTODY')])
            original = observer.read
            def metadata_only(path):
                self.assertNotIn('sealed', path.parts)
                self.assertNotIn('.private.', path.name)
                return original(path)
            with patch.object(observer, 'read', side_effect=metadata_only):
                result = observer.coverage(root, plan)
            self.assertEqual(result['scope_count'], 2)
            self.assertEqual(result['source_admitted_count'], 1)
            self.assertEqual(result['completed_calls'], 0)
            self.assertEqual(result['lives'][0]['fixed_checkpoints'], [0, 20, 21, 22])
            self.assertEqual(result['lives'][0]['missing_captures'], [0, 20, 21, 22])
            self.assertEqual(result['lives'][1]['fixed_checkpoints'], [])


if __name__ == '__main__':
    unittest.main()
