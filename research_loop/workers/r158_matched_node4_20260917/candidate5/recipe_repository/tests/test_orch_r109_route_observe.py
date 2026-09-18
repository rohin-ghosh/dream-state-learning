"""Compact observer never exports native text or fabricates quality rates."""

import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from gpu import orch_r109_route_observe as observe


class CompactTests(unittest.TestCase):
    def test_raw_text_excluded_and_protocol_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            campaign=root/'campaign_test'
            (campaign/'native').mkdir(parents=True)
            value=dict(status='COMPLETE',started_unix=time.time()-30,finished_unix=time.time()-10,purpose='train_episode',
                response=dict(raw='ROUTE SECRET_IDENTIFIER',token_ids=[1,2],truncated=False,
                    full_prompt_prefix_verified=True,input_truncated=False))
            (campaign/'native/CALL_1.json').write_text(json.dumps(value))
            with patch.object(observe.subprocess,'check_output',return_value=''):
                result=observe.collect(root,'test')
            self.assertNotIn('SECRET_IDENTIFIER',json.dumps(result))
            self.assertEqual(result['native_counts']['protocol_only_structural'],1)
            self.assertIsNone(result['throughput_600s']['qualified_functional_count'])
            self.assertFalse(result['throughput_600s']['full_600s_available'])
            self.assertEqual(result['throughput_600s']['semantic_sample_denominator'],0)


if __name__=='__main__':
    unittest.main()
