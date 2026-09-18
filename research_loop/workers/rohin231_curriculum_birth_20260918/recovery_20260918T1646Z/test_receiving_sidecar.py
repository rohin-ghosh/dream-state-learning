from copy import deepcopy
import unittest

from extension_spec import digest
from repair_receiving_sidecar import preservation


class PreservationTests(unittest.TestCase):
    def binding(self):
        checkpoint = dict(checkpoint_sha256={'adapter':'a', 'optimizer':'b', 'rng':'c'})
        state = dict(model_state_sha256=digest(checkpoint['checkpoint_sha256']), pending=None,
            sleep_frontier=1, rows=[{}])
        complete = dict(kind='SLEEP_COMPLETE', index=12, sha256='record', document=dict(
            checkpoint=checkpoint, resume_state=dict(state=state, sha256=digest(state))))
        return dict(complete=complete, journal_id='same', head=dict(index=13, sha256='head')), checkpoint

    def test_required_checkpoint_and_state_sidecar(self):
        bound, checkpoint = self.binding()
        actual = preservation(bound, checkpoint)
        self.assertEqual(actual['checkpoint'], checkpoint)
        self.assertEqual(actual['coherent_state'], bound['complete']['document']['resume_state'])
        self.assertFalse(actual['resident_after_checkpoint_RNG_captured'])

    def test_other_checkpoint_cannot_be_substituted(self):
        bound, checkpoint = self.binding()
        other = deepcopy(checkpoint)
        other['checkpoint_sha256']['adapter'] = 'older'
        with self.assertRaises(ValueError):
            preservation(bound, other)

    def test_pending_work_cannot_be_discarded(self):
        bound, checkpoint = self.binding()
        saved = bound['complete']['document']['resume_state']
        saved['state']['pending'] = 'request'
        saved['sha256'] = digest(saved['state'])
        with self.assertRaises(ValueError):
            preservation(bound, checkpoint)


if __name__ == '__main__':
    unittest.main()
