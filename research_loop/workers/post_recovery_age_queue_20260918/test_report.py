import unittest
import xml.etree.ElementTree as ElementTree

from report import render


class ReportTests(unittest.TestCase):
    def test_never_plot_different_judges_as_one_comparison(self):
        with self.assertRaises(ValueError):
            render(dict(rows=[dict(judge_epoch_sha256='old'), dict(judge_epoch_sha256='new')]))

    def test_not_loaded_is_unknown_not_zero(self):
        markdown, svg = render(dict(observed_utc='synthetic', rows=[dict(arm='base', state='LOAD_NOT_OBSERVED')]))
        self.assertIn('unknown | unknown', markdown)
        self.assertNotIn('polyline', svg)

    def test_pinned_c2_age_is_not_mislabeled_age24_or_latest_live_weights(self):
        markdown, unused = render(dict(observed_utc='synthetic', rows=[],
            source_description='C2 sleep51 versus sleep117, selected at a fixed cut.'))
        self.assertIn('C2 sleep51 versus sleep117', markdown)
        self.assertNotIn('Source age24', markdown)

    def test_actual_token_curves_cover_acceptance_and_pixels_separately(self):
        counts = dict(generated_tokens=3072, distinct_scored=50, distinct_accepted=24,
            new_pixels=15, acts_without_scored_strings=2,
            curve=[dict(generated_tokens=3072, distinct_accepted=24, new_pixels=15)])
        row = dict(arm='learner24', state='COMPLETE_FIXED_6144_TOKENS',
            source_optimizer_steps=1152, per_seed={'23201': counts}, judge_epoch_sha256='same')
        markdown, svg = render(dict(observed_utc='synthetic', rows=[row]))
        self.assertIn('| 3072 | 50 | 24 | 15 | 2 | 1152 |', markdown)
        self.assertIn('optimizer steps are not training FLOPs', markdown)
        root = ElementTree.fromstring(svg)
        lines = root.findall('.//{http://www.w3.org/2000/svg}polyline')
        self.assertEqual({line.attrib['data-metric'] for line in lines}, {'distinct_accepted', 'new_pixels'})
        self.assertTrue(all(line.attrib['points'].split()[-1].startswith('730.0,') for line in lines))


if __name__ == '__main__':
    unittest.main()
