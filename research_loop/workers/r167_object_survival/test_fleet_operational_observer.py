import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fleet_operational_observer as observer


class ObserverTests(unittest.TestCase):
    def test_hashed_job_keys_use_config_condition_without_sealed_reads(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ledger = root / 'ledger'
            ledger.mkdir()
            config = root / 'CONFIG.json'
            config.write_text(json.dumps(dict(condition='LORA_OFF', life_id='synthetic', sleep=0)))
            key = 'a' * 64
            (ledger / (key + '.RESERVED.json')).write_text(json.dumps(dict(key=key,
                execution=dict(path=str(config)), calls_charged=3, tokens_charged=1536)))
            sealed = root / 'attempts' / key / 'sealed'
            sealed.mkdir(parents=True)
            (sealed / '0.RAW.private.json').write_text('sealed-not-json-do-not-open')
            original = observer.read
            def metadata_only(path):
                self.assertNotIn('sealed', path.parts)
                self.assertNotIn('.private.', path.name)
                return original(path)
            with patch.object(observer, 'read', side_effect=metadata_only):
                report = observer.observe(root)
            self.assertEqual(report['conditions']['LORA_OFF']['reserved_jobs'], 1)
            self.assertEqual(report['conditions']['LORA_OFF']['response_files'], 1)
            self.assertEqual(report['conditions']['LORA_ON']['reserved_jobs'], 0)
            self.assertEqual(report['calls_charged'], 3)
            self.assertFalse(report['sealed_content_read'])


if __name__ == '__main__':
    unittest.main()
