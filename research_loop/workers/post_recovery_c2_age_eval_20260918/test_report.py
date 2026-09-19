import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import runpy
import unittest
import xml.etree.ElementTree as ElementTree

from reconcile import HERE, RENDERER, METRICS, reconcile, sha, summarize


class SameBlockReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads((HERE / 'SAME_BLOCK_REMOTE_RECEIPT.json').read_bytes())
        cls.original = json.loads((HERE / 'AGE_BLOCK_REFRESH.json').read_bytes())

    def test_pinned_receipts_not_stale_or_other_block(self):
        self.assertEqual(sha(HERE / 'AGE_BLOCK_REFRESH.json'),
            '980cef105dcf2ff6555a7b86980a79be5f763fe6f7ef46bf694cd14e46d9cae3')
        self.assertEqual(sha(HERE / 'SAME_BLOCK_REMOTE_RECEIPT.json'),
            '8b4b55c187138ffb4378d9d4bbfed13965a3c65d728cc084ca78b738207b5245')
        self.assertEqual(len(self.receipt['files']), 350)
        self.assertEqual(sha(HERE / 'audit_reader.py'), self.receipt['reader_sha256'])

    def test_all_six_raw_and_distinct_counts(self):
        summary = reconcile(self.receipt, self.original)['per_seed']
        expected = {
            'base': [(25, (72, 43, 28), (50, 24, 15)), (24, (75, 54, 40), (51, 36, 24))],
            'c2sleep51': [(29, (98, 66, 35), (94, 62, 34)), (30, (78, 42, 31), (76, 40, 31))],
            'c2sleep117': [(80, (114, 70, 22), (106, 62, 19)), (67, (94, 54, 26), (93, 53, 26))],
        }
        results = (HERE / 'RESULTS.md').read_text()
        for arm, rows in expected.items():
            for seed, (events, raw, distinct) in zip(('23201', '23202'), rows, strict=True):
                counts = summary[arm][seed]
                self.assertEqual(counts['events'], events)
                self.assertEqual(tuple(counts['raw_' + metric] for metric in METRICS), raw)
                self.assertEqual(tuple(counts[metric] for metric in METRICS), distinct)
                raw_text, distinct_text = (' / '.join(map(str, values)) for values in (raw, distinct))
                self.assertIn(f'| {arm} | {seed} | {events} | 3072 | {raw_text} | {distinct_text} |', results)

    def test_replayed_new_pixel_is_not_new_novelty(self):
        scored = dict(caption_sha256='same-caption', result=dict(rank=1, accepted=True,
            status='new_pixel', replayed=False, pixel_id='pixel-one'))
        event = dict(actual_generated_tokens=128, origin=dict(stage='ACT'),
            score=dict(new_pixels=1, results=[scored]))
        replay = deepcopy(event)
        replay['score']['results'][0]['result']['replayed'] = True
        cells = [dict(contest_id='scene-one', seed=23201, events=[event, replay])]
        counts = summarize(cells)['23201']
        self.assertEqual((counts['event_new_pixels'], counts['new_pixels']), (2, 1))
        self.assertEqual((counts['raw_distinct_accepted'], counts['distinct_accepted']), (2, 1))
        self.assertEqual(counts['distinct_new_pixel_ids'], 1)
        cells.append(dict(contest_id='scene-one', seed=23202, events=[event]))
        self.assertEqual(summarize(cells)['23202']['new_pixels'], 1)

    def test_reject_wrong_block_despite_identical_base_counts(self):
        receipt = deepcopy(self.receipt)
        receipt['blocks']['c2']['rows'][0] = receipt['blocks']['earlier']['rows'][0]
        with self.assertRaisesRegex(ValueError, 'same_block_root'):
            reconcile(receipt, self.original)

    def test_reject_mismatched_completion_hash(self):
        receipt = deepcopy(self.receipt)
        row = receipt['blocks']['c2']['rows'][0]
        receipt['files'][row['output'] + '/COMPLETE.json']['sha256'] = 'incorrect'
        with self.assertRaisesRegex(ValueError, 'same_receipt_complete_sha256'):
            reconcile(receipt, self.original)

    def test_reject_unequal_actual_budget(self):
        receipt = deepcopy(self.receipt)
        receipt['blocks']['c2']['rows'][0]['cells'][0]['events'][0]['actual_generated_tokens'] -= 1
        with self.assertRaisesRegex(ValueError, 'equal_actual_tokens'):
            reconcile(receipt, self.original)

    def test_original_facts_stand_without_broad_claim_or_metric_substitution(self):
        summary = reconcile(self.receipt, self.original)
        self.assertTrue(summary['original_distinct_counts_stand'])
        self.assertTrue(summary['within_block_arithmetic_comparison_stands'])
        self.assertTrue(summary['broad_beat_base_claim_retracted'])
        self.assertTrue(summary['raw_event_counts_are_not_distinct_new_pixels'])
        for seed in ('23201', '23202'):
            for arm in ('c2sleep51', 'c2sleep117'):
                self.assertGreater(summary['per_seed'][arm][seed]['new_pixels'],
                    summary['per_seed']['base'][seed]['new_pixels'])
        for name in ('RESULTS.md', 'STATUS.md'):
            text = (HERE / name).read_text()
            self.assertIn('original', text.lower())
            self.assertIn('counts', text)
            self.assertIn('stand', text)
            self.assertIn('broad', text)
            self.assertIn('retracted', text)
        self.assertIn('not corrected distinct-new-pixel counts',
            (HERE / 'RESULTS.md').read_text().replace('**', ''))

    def test_exact_source_pointers_are_bound_to_collected_files(self):
        summary = reconcile(self.receipt, self.original)
        results = (HERE / 'RESULTS.md').read_text()
        for block, rows in summary['source_pointers'].items():
            for arm, pointers in rows.items():
                complete = pointers['complete']
                self.assertIn(complete['path'], results)
                self.assertEqual(len(pointers['cell_results']), 6)
                for pointer in [value for key, value in pointers.items() if key != 'cell_results'] + pointers['cell_results']:
                    self.assertEqual({key: value for key, value in pointer.items() if key != 'path'},
                        self.receipt['files'][pointer['path']])
                if block == 'c2':
                    self.assertIn('/orch_post_recovery_c2_age_eval_20260918/' + arm + '/', complete['path'])

    def test_pinned_source_and_receiving_provenance(self):
        ready_path = HERE.parent / 'post_recovery_c2_age_sources_20260918/READY.json'
        ready = json.loads(ready_path.read_bytes())
        sources = {entry['absolute_sleep']: entry for entry in ready['sources']}
        provenance = json.loads((HERE / 'RECEIVING_PROVENANCE.json').read_bytes())
        prepared = [json.loads(line) for line in (HERE / 'RECEIVING_CPU_PREPARED.log').read_text().splitlines()
            if line.startswith('{')]
        for row, proof, preparation in zip(self.receipt['blocks']['c2']['rows'], provenance['arms'], prepared, strict=True):
            self.assertTrue(proof['verified'])
            self.assertEqual(proof['config_sha256'], preparation['config_sha256'])
            self.assertEqual(preparation['source_readiness_sha256'], sha(ready_path))
            self.assertEqual(proof['config_sha256'], self.receipt['files'][row['root'] + '/CONFIG.json']['sha256'])
            for relative, expected in row['source_manifest'].items():
                if relative.endswith(('ny_caption_game.py', '/runner.py')):
                    self.assertEqual(sha(HERE.parents[2] / relative), expected)
            if row['arm'] != 'base':
                source = sources[row['config']['identity']['absolute_sleep']]
                self.assertEqual(row['loaded']['identity']['adapter_state_sha256'], source['adapter_state_sha256'])
                self.assertEqual(row['loaded']['source_age']['optimizer_steps'], source['optimizer_steps'])

    def test_captured_remote_observer_reproduces_receipt(self):
        receipt = json.loads((HERE / 'REPORTER_SOURCE_RECEIPT.json').read_bytes())
        captured = next(value for name, value in receipt['files'].items() if name.endswith('/observe.py'))
        self.assertEqual(hashlib.sha256(captured['source'].encode()).hexdigest(), captured['sha256'])
        self.assertEqual(sha(RENDERER.with_name('observe.py')), captured['sha256'])
        tree = ast.parse(captured['source'])
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'count_events')
        namespace = {}
        exec(compile(ast.Module(body=[function], type_ignores=[]), 'captured_count_events', 'exec'), namespace)
        for row, prior in zip(self.receipt['blocks']['c2']['rows'], self.original['rows'], strict=True):
            cells = [(cell['contest_id'], cell['seed'], cell['events']) for cell in row['cells']]
            self.assertEqual(namespace['count_events'](cells), prior['per_seed'])

    def test_rendered_completed_independent_seed_curves(self):
        markdown, svg = runpy.run_path(str(RENDERER))['render'](self.original)
        self.assertEqual((HERE / 'TOKEN_CURVES.svg').read_text(),
            svg.replace('New embedding pixels', 'Distinct new embedding pixels'))
        status = (HERE / 'STATUS.md').read_text()
        self.assertTrue(status.startswith(markdown.split('\nThe first operator-protocol failure', 1)[0]))
        self.assertNotIn('LOADED_EVALUATION_INCOMPLETE', status)
        self.assertNotIn('Current chain audit', status)
        self.assertIn('claim remains retracted', status)
        lines = ElementTree.fromstring(svg).findall('.//{http://www.w3.org/2000/svg}polyline')
        self.assertEqual(len(lines), 12)
        self.assertTrue(all(line.attrib['points'].split()[-1].startswith('730.0,') for line in lines))

    def test_artifact_hashes_and_preserved_stale_report(self):
        manifest = json.loads((HERE / 'RECONCILIATION.json').read_bytes())
        for name, expected in manifest['local_sha256'].items():
            self.assertEqual(sha(HERE / name), expected)
        self.assertEqual(sha(HERE / 'STATUS_2212.md'),
            '103a4b30d7f7d583a5004ad01002574e97dd2fa09b143e55433b31dd9f2e3e62')
        self.assertEqual((HERE / 'AGE_BLOCK_REFRESH_0039.json').stat().st_size, 0)


if __name__ == '__main__':
    unittest.main()
