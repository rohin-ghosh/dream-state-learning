import unittest

from report_first_render import render_post


class RenderReporterTests(unittest.TestCase):
    def fixture(self):
        publication = dict(id='a' * 32, path='/TRAIN/inbox.json', sha256='b' * 64)
        row = dict(root='/TRAIN', label='teach_replay', arm='A')
        source = dict(root='/TRAIN', publication=publication, origin='DIRECT_MAIN_AUTHORIZED_ASTRA_B0_NOT_PROVIDER_OUTPUT',
                      observed_unix=1, receipt=dict(path='/PUB', sha256='c' * 64))
        exposure = dict(root='/TRAIN', publication=publication, rendered=True, observed_unix=2,
                        cursor=dict(exposure=dict(record_index=3, record_sha256='d' * 64, filesystem_mtime_ns=1000000000,
                                                  exact_visible_history_and_rendered_message=True)))
        return row, source, exposure, dict(path='/PROOF', sha256='e' * 64)

    def test_exact_proof_and_origin_preserved(self):
        text = render_post(*self.fixture())
        self.assertIn('NOT_PROVIDER_OUTPUT', text)
        self.assertIn('filesystem evidence', text)
        self.assertIn('no behavioral PASS', text)

    def test_unrendered_never_posted(self):
        row, source, exposure, reference = self.fixture()
        exposure['rendered'] = False
        with self.assertRaisesRegex(ValueError, 'verified_REQUEST'):
            render_post(row, source, exposure, reference)

    def test_wrong_life_refused(self):
        row, source, exposure, reference = self.fixture()
        exposure['root'] = '/OTHER'
        with self.assertRaisesRegex(ValueError, 'same_life'):
            render_post(row, source, exposure, reference)


if __name__ == '__main__':
    unittest.main(verbosity=2)
