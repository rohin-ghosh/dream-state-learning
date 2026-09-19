import hashlib
import unittest
from unittest.mock import patch

import trace_remote


class TraceTests(unittest.TestCase):
    def test_attributed_prefix_is_part_of_exact_render_not_provider_message(self):
        digest = lambda value: hashlib.sha256(value.encode()).hexdigest()
        item = dict(publication_id='receipt', publication_sha256='canonical_inbox')
        event = dict(actor='parent', event_id='parent:inbox:receipt', source_sha256='canonical_inbox', text='Astra: Exact provider message.')
        with patch.object(trace_remote, 'text_sha', digest, create=True):
            self.assertTrue(trace_remote.exact_event(event,item,digest('Astra: Exact provider message.')))
            self.assertFalse(trace_remote.exact_event(event,item,digest('Exact provider message.')))
            self.assertFalse(trace_remote.exact_event(dict(event,source_sha256='wrong'),item,digest(event['text'])))
            self.assertFalse(trace_remote.exact_event(dict(event,event_id='parent:inbox:static'),item,digest(event['text'])))
            self.assertFalse(trace_remote.exact_event(dict(event,text='quoted '+event['text']),item,digest(event['text'])))


if __name__ == '__main__':
    unittest.main()
